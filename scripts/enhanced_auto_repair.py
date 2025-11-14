#!/usr/bin/env python3
"""
改善版自動エラー検知・修復ループシステム

アーキテクチャ検証レポートの推奨事項を実装した改善版
"""

import argparse
import json
import logging
import sqlite3
import subprocess
import sys
import time
import psutil
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum


# ========================================
# データクラス定義
# ========================================

class ErrorSeverity(Enum):
    """エラー重大度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CircuitState(Enum):
    """サーキットブレーカー状態"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class ErrorInfo:
    """エラー情報"""
    type: str
    severity: ErrorSeverity
    message: str
    file: Optional[str] = None
    line: Optional[int] = None
    details: Optional[str] = None


@dataclass
class RepairResult:
    """修復結果"""
    success: bool
    method: str
    duration: float
    error_message: Optional[str] = None


@dataclass
class ResourceMetrics:
    """リソースメトリクス"""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    warnings: List[str]


# ========================================
# 設定管理
# ========================================

class ConfigManager:
    """設定管理クラス"""

    def __init__(self, config_path: str = "config/auto-repair-recommended.yml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """設定ファイルを読み込み"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logging.warning(f"設定ファイル {self.config_path} が見つかりません。デフォルト設定を使用します。")
            return self._default_config()

    def _default_config(self) -> Dict:
        """デフォルト設定"""
        return {
            'loop_control': {
                'max_loops': {'normal': 7},
                'interval': {'normal': 60},
                'timeout': {'normal': 1200}
            },
            'resource_management': {
                'monitoring': {
                    'enabled': True,
                    'cpu': {'threshold_warning': 70, 'threshold_critical': 85},
                    'memory': {'threshold_warning': 70, 'threshold_critical': 85},
                    'disk': {'threshold_warning': 80, 'threshold_critical': 90}
                }
            },
            'advanced': {
                'circuit_breaker': {
                    'enabled': True,
                    'failure_threshold': 3,
                    'timeout': 300
                }
            }
        }

    def get(self, path: str, default: Any = None) -> Any:
        """ドット記法で設定値を取得"""
        keys = path.split('.')
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value


# ========================================
# リソース監視
# ========================================

class ResourceMonitor:
    """リソース監視クラス"""

    def __init__(self, config: ConfigManager):
        self.config = config
        self.cpu_threshold_warning = config.get('resource_management.monitoring.cpu.threshold_warning', 70)
        self.cpu_threshold_critical = config.get('resource_management.monitoring.cpu.threshold_critical', 85)
        self.memory_threshold_warning = config.get('resource_management.monitoring.memory.threshold_warning', 70)
        self.memory_threshold_critical = config.get('resource_management.monitoring.memory.threshold_critical', 85)
        self.disk_threshold_warning = config.get('resource_management.monitoring.disk.threshold_warning', 80)
        self.disk_threshold_critical = config.get('resource_management.monitoring.disk.threshold_critical', 90)

        self.logger = logging.getLogger(__name__)

    def check_resources(self) -> ResourceMetrics:
        """リソース使用状況をチェック"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            warnings = self._generate_warnings(cpu_percent, memory.percent, disk.percent)

            return ResourceMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                disk_percent=disk.percent,
                warnings=warnings
            )
        except Exception as e:
            self.logger.error(f"リソース監視エラー: {e}")
            return ResourceMetrics(
                cpu_percent=0.0,
                memory_percent=0.0,
                disk_percent=0.0,
                warnings=[f"リソース監視エラー: {e}"]
            )

    def _generate_warnings(self, cpu: float, memory: float, disk: float) -> List[str]:
        """警告メッセージを生成"""
        warnings = []

        if cpu >= self.cpu_threshold_critical:
            warnings.append(f"🚨 CPU使用率が危険レベル: {cpu:.1f}%")
        elif cpu >= self.cpu_threshold_warning:
            warnings.append(f"⚠️ CPU使用率が高い: {cpu:.1f}%")

        if memory >= self.memory_threshold_critical:
            warnings.append(f"🚨 メモリ使用率が危険レベル: {memory:.1f}%")
        elif memory >= self.memory_threshold_warning:
            warnings.append(f"⚠️ メモリ使用率が高い: {memory:.1f}%")

        if disk >= self.disk_threshold_critical:
            warnings.append(f"🚨 ディスク使用率が危険レベル: {disk:.1f}%")
        elif disk >= self.disk_threshold_warning:
            warnings.append(f"⚠️ ディスク使用率が高い: {disk:.1f}%")

        return warnings

    def is_safe_to_continue(self, metrics: ResourceMetrics) -> bool:
        """処理続行が安全かチェック"""
        # クリティカル警告がある場合は停止
        return not any("🚨" in w for w in metrics.warnings)


# ========================================
# Circuit Breaker
# ========================================

class CircuitBreaker:
    """サーキットブレーカーパターン実装"""

    def __init__(self, failure_threshold: int = 3, timeout: int = 300):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        self.logger = logging.getLogger(__name__)

    def call(self, func, *args, **kwargs):
        """サーキットブレーカー経由で関数を実行"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.logger.info("Circuit breaker: HALF_OPEN状態に移行")
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerOpenError("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _on_success(self):
        """成功時の処理"""
        self.failures = 0
        if self.state == CircuitState.HALF_OPEN:
            self.logger.info("Circuit breaker: CLOSED状態に復帰")
        self.state = CircuitState.CLOSED

    def _on_failure(self):
        """失敗時の処理"""
        self.failures += 1
        self.last_failure_time = time.time()

        if self.failures >= self.failure_threshold:
            self.logger.error(f"Circuit breaker opened after {self.failures} failures")
            self.state = CircuitState.OPEN

    def _should_attempt_reset(self) -> bool:
        """リセット試行判定"""
        if self.last_failure_time is None:
            return False
        return (time.time() - self.last_failure_time) > self.timeout

    def reset(self):
        """手動リセット"""
        self.failures = 0
        self.state = CircuitState.CLOSED
        self.logger.info("Circuit breaker manually reset")


class CircuitBreakerOpenError(Exception):
    """サーキットブレーカーがオープン状態の例外"""
    pass


# ========================================
# メトリクス収集
# ========================================

class MetricsCollector:
    """メトリクス収集クラス"""

    def __init__(self, db_path: str = 'repair_metrics.db'):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.init_db()

    def init_db(self):
        """メトリクスDB初期化"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS repair_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        error_type TEXT NOT NULL,
                        severity TEXT NOT NULL,
                        repair_method TEXT NOT NULL,
                        success INTEGER NOT NULL,
                        duration_seconds REAL,
                        error_message TEXT,
                        repair_details TEXT
                    )
                ''')

                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_error_type
                    ON repair_history(error_type, success)
                ''')

                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_timestamp
                    ON repair_history(timestamp DESC)
                ''')

                conn.commit()
        except Exception as e:
            self.logger.error(f"メトリクスDB初期化エラー: {e}")

    def record_repair(self, error: ErrorInfo, result: RepairResult):
        """修復結果を記録"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO repair_history
                    (error_type, severity, repair_method, success, duration_seconds, error_message)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    error.type,
                    error.severity.value,
                    result.method,
                    1 if result.success else 0,
                    result.duration,
                    result.error_message
                ))
                conn.commit()
        except Exception as e:
            self.logger.error(f"メトリクス記録エラー: {e}")

    def get_success_rate(self, error_type: str = None, days: int = 30) -> float:
        """成功率を計算"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if error_type:
                    result = conn.execute('''
                        SELECT AVG(success) * 100 FROM repair_history
                        WHERE error_type = ?
                        AND timestamp > datetime('now', '-' || ? || ' days')
                    ''', (error_type, days)).fetchone()
                else:
                    result = conn.execute('''
                        SELECT AVG(success) * 100 FROM repair_history
                        WHERE timestamp > datetime('now', '-' || ? || ' days')
                    ''', (days,)).fetchone()

                return result[0] if result[0] else 0.0
        except Exception as e:
            self.logger.error(f"成功率計算エラー: {e}")
            return 0.0

    def get_trending_errors(self, limit: int = 10, days: int = 7) -> List[Dict]:
        """頻出エラーパターンを取得"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                results = conn.execute('''
                    SELECT
                        error_type,
                        COUNT(*) as frequency,
                        AVG(success) * 100 as success_rate,
                        AVG(duration_seconds) as avg_duration
                    FROM repair_history
                    WHERE timestamp > datetime('now', '-' || ? || ' days')
                    GROUP BY error_type
                    ORDER BY frequency DESC
                    LIMIT ?
                ''', (days, limit)).fetchall()

                return [
                    {
                        'error_type': r[0],
                        'frequency': r[1],
                        'success_rate': r[2],
                        'avg_duration': r[3]
                    }
                    for r in results
                ]
        except Exception as e:
            self.logger.error(f"トレンド分析エラー: {e}")
            return []


# ========================================
# エラー検知 (改善版)
# ========================================

class EnhancedErrorDetector:
    """改善版エラー検知クラス"""

    def __init__(self, config: ConfigManager, resource_monitor: ResourceMonitor):
        self.config = config
        self.resource_monitor = resource_monitor
        self.detected_errors = []
        self.logger = logging.getLogger(__name__)

    def detect_all(self) -> List[ErrorInfo]:
        """すべてのエラーを検知 (リソースチェック付き)"""
        all_errors = []

        # リソースチェック
        metrics = self.resource_monitor.check_resources()
        if not self.resource_monitor.is_safe_to_continue(metrics):
            self.logger.error("リソース使用率が危険レベル。検知を中断します。")
            for warning in metrics.warnings:
                self.logger.error(warning)
            return all_errors

        # 各種エラー検知
        if self.config.get('error_detection.syntax.enabled', True):
            all_errors.extend(self.detect_syntax_errors())

        if self.config.get('error_detection.import.enabled', True):
            all_errors.extend(self.detect_import_errors())

        if self.config.get('error_detection.test.enabled', True):
            all_errors.extend(self.detect_test_failures())

        if self.config.get('error_detection.lint.enabled', True):
            all_errors.extend(self.detect_lint_errors())

        self.detected_errors = all_errors
        self.logger.info(f"合計 {len(all_errors)} 個のエラーを検出")

        return all_errors

    def detect_syntax_errors(self) -> List[ErrorInfo]:
        """構文エラーを検知"""
        errors = []
        self.logger.info("構文エラーをチェック中...")

        directories = self.config.get('error_detection.syntax.directories', ['modules', 'tests'])

        for check_dir in directories:
            dir_path = Path(check_dir)
            if not dir_path.exists():
                continue

            for py_file in dir_path.rglob('*.py'):
                try:
                    result = subprocess.run(
                        ['python', '-m', 'py_compile', str(py_file)],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )

                    if result.returncode != 0:
                        errors.append(ErrorInfo(
                            type='SyntaxError',
                            severity=ErrorSeverity.HIGH,
                            message=result.stderr[:500],
                            file=str(py_file)
                        ))
                        self.logger.warning(f"構文エラー検出: {py_file}")
                except subprocess.TimeoutExpired:
                    self.logger.error(f"{py_file}の構文チェックがタイムアウト")
                except Exception as e:
                    self.logger.error(f"{py_file}の構文チェックエラー: {e}")

        return errors

    def detect_import_errors(self) -> List[ErrorInfo]:
        """インポートエラーを検知 (改善版)"""
        errors = []
        self.logger.info("インポートエラーをチェック中...")

        exclude_patterns = self.config.get('error_detection.import.exclude_patterns', [
            'attempted relative import',
            'DeprecationWarning'
        ])

        for py_file in Path('modules').glob('*.py'):
            if py_file.stem.startswith('_'):
                continue

            try:
                module_name = f'modules.{py_file.stem}'
                result = subprocess.run(
                    ['python', '-c', f'import {module_name}'],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    env={'PYTHONPATH': str(Path.cwd())}
                )

                if result.returncode != 0:
                    # 除外パターンのチェック
                    if not any(pattern in result.stderr for pattern in exclude_patterns):
                        # 実際のインポートエラーのみ
                        if any(err in result.stderr for err in [
                            'ModuleNotFoundError',
                            'ImportError: cannot import',
                            'No module named'
                        ]):
                            errors.append(ErrorInfo(
                                type='ImportError',
                                severity=ErrorSeverity.HIGH,
                                message=result.stderr[:200],
                                file=str(py_file)
                            ))
            except subprocess.TimeoutExpired:
                self.logger.error(f"{py_file}のインポートチェックがタイムアウト")
            except Exception as e:
                self.logger.error(f"{py_file}のインポートチェックエラー: {e}")

        return errors

    def detect_test_failures(self) -> List[ErrorInfo]:
        """テスト失敗を検知"""
        errors = []
        self.logger.info("テスト失敗をチェック中...")

        try:
            options = self.config.get('error_detection.test.options', [
                '-v', '--tb=short', '--maxfail=5', '-x', '--timeout=60'
            ])

            result = subprocess.run(
                ['pytest', 'tests/'] + options,
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode != 0:
                failed_tests = []
                for line in result.stdout.split('\n'):
                    if 'FAILED' in line:
                        failed_tests.append(line.strip())

                if failed_tests:
                    errors.append(ErrorInfo(
                        type='TestFailure',
                        severity=ErrorSeverity.MEDIUM,
                        message=f"{len(failed_tests)}個のテストが失敗",
                        details='\n'.join(failed_tests[:10])
                    ))
        except subprocess.TimeoutExpired:
            self.logger.error("テストチェックがタイムアウト")
        except Exception as e:
            self.logger.error(f"テストチェックエラー: {e}")

        return errors

    def detect_lint_errors(self) -> List[ErrorInfo]:
        """Lintエラーを検知"""
        errors = []
        self.logger.info("Lintエラーをチェック中...")

        try:
            options = self.config.get('error_detection.lint.options', [
                '--count', '--max-line-length=120'
            ])

            result = subprocess.run(
                ['flake8', 'modules/', 'tests/'] + options,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                error_count = result.stdout.strip().split('\n')[-1] if result.stdout else '0'

                # warning_onlyの場合は低重大度
                severity = ErrorSeverity.LOW if self.config.get('error_detection.lint.warning_only', True) else ErrorSeverity.MEDIUM

                errors.append(ErrorInfo(
                    type='LintError',
                    severity=severity,
                    message=f"{error_count}個のLintエラー",
                    details=result.stdout[:500]
                ))
        except subprocess.TimeoutExpired:
            self.logger.error("Lintチェックがタイムアウト")
        except Exception as e:
            self.logger.error(f"Lintチェックエラー: {e}")

        return errors


# ========================================
# 自動修復 (改善版)
# ========================================

class EnhancedAutoRepair:
    """改善版自動修復クラス"""

    def __init__(self, config: ConfigManager, metrics: MetricsCollector, circuit_breaker: CircuitBreaker):
        self.config = config
        self.metrics = metrics
        self.circuit_breaker = circuit_breaker
        self.repair_history = []
        self.logger = logging.getLogger(__name__)

    def repair(self, error: ErrorInfo) -> RepairResult:
        """エラーを修復 (フォールバック戦略付き)"""
        start_time = time.time()

        try:
            # Circuit Breaker経由で修復実行
            success = self.circuit_breaker.call(self._repair_with_fallback, error)

            duration = time.time() - start_time

            result = RepairResult(
                success=success,
                method=self._get_repair_method(error.type),
                duration=duration
            )

            # メトリクス記録
            self.metrics.record_repair(error, result)

            return result

        except CircuitBreakerOpenError as e:
            self.logger.error(f"Circuit Breaker開放中: {e}")
            return RepairResult(
                success=False,
                method="circuit_breaker_blocked",
                duration=time.time() - start_time,
                error_message=str(e)
            )
        except Exception as e:
            self.logger.error(f"修復エラー: {e}")
            return RepairResult(
                success=False,
                method=self._get_repair_method(error.type),
                duration=time.time() - start_time,
                error_message=str(e)
            )

    def _repair_with_fallback(self, error: ErrorInfo) -> bool:
        """フォールバック戦略で修復"""
        error_type = error.type

        # プライマリ修復
        primary_method = self._get_primary_repair_method(error_type)
        if primary_method:
            self.logger.info(f"プライマリ修復試行: {error_type}")
            if primary_method(error):
                return True

        # フォールバック修復
        fallback_methods = self._get_fallback_repair_methods(error_type)
        for i, method in enumerate(fallback_methods):
            self.logger.info(f"フォールバック試行 {i+1}/{len(fallback_methods)}: {error_type}")
            try:
                if method(error):
                    return True
            except Exception as e:
                self.logger.warning(f"フォールバック失敗: {e}")
                continue

        self.logger.error(f"すべての修復戦略が失敗: {error_type}")
        return False

    def _get_primary_repair_method(self, error_type: str):
        """プライマリ修復メソッドを取得"""
        methods = {
            'SyntaxError': self.repair_syntax_with_black,
            'ImportError': self.repair_import_with_pip,
            'TestFailure': self.repair_test_with_cache_clear,
            'LintError': self.repair_lint_with_autopep8
        }
        return methods.get(error_type)

    def _get_fallback_repair_methods(self, error_type: str) -> List:
        """フォールバックメソッドを取得"""
        fallbacks = {
            'SyntaxError': [self.repair_syntax_with_autopep8],
            'ImportError': [
                self.repair_import_with_force_reinstall,
                self.repair_import_with_requirements_reset
            ],
            'TestFailure': [
                self.repair_test_with_dependency_reinstall
            ],
            'LintError': []
        }
        return fallbacks.get(error_type, [])

    def _get_repair_method(self, error_type: str) -> str:
        """修復メソッド名を取得"""
        methods = {
            'SyntaxError': 'black',
            'ImportError': 'pip_install',
            'TestFailure': 'cache_clear',
            'LintError': 'autopep8'
        }
        return methods.get(error_type, 'unknown')

    # 修復メソッド実装
    def repair_syntax_with_black(self, error: ErrorInfo) -> bool:
        """Blackで構文エラーを修復"""
        try:
            result = subprocess.run(
                ['black', 'modules/', 'tests/', '--line-length=120'],
                capture_output=True,
                text=True,
                timeout=120
            )
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"Black修復エラー: {e}")
            return False

    def repair_syntax_with_autopep8(self, error: ErrorInfo) -> bool:
        """autopep8で構文エラーを修復"""
        try:
            result = subprocess.run(
                ['autopep8', '--in-place', '--recursive', '--max-line-length=120', 'modules/', 'tests/'],
                capture_output=True,
                text=True,
                timeout=120
            )
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"autopep8修復エラー: {e}")
            return False

    def repair_import_with_pip(self, error: ErrorInfo) -> bool:
        """pipでインポートエラーを修復"""
        try:
            result = subprocess.run(
                ['pip', 'install', '-r', 'requirements.txt', '--upgrade'],
                capture_output=True,
                text=True,
                timeout=300
            )
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"pip修復エラー: {e}")
            return False

    def repair_import_with_force_reinstall(self, error: ErrorInfo) -> bool:
        """強制再インストール"""
        try:
            result = subprocess.run(
                ['pip', 'install', '-r', 'requirements.txt', '--force-reinstall'],
                capture_output=True,
                text=True,
                timeout=300
            )
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"強制再インストールエラー: {e}")
            return False

    def repair_import_with_requirements_reset(self, error: ErrorInfo) -> bool:
        """requirements.txtをリセット"""
        try:
            # Gitから最後の安定版を復元
            subprocess.run(
                ['git', 'checkout', 'HEAD~1', 'requirements.txt'],
                check=True
            )
            # 再インストール
            result = subprocess.run(
                ['pip', 'install', '-r', 'requirements.txt'],
                capture_output=True,
                text=True,
                timeout=300
            )
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"requirements.txtリセットエラー: {e}")
            return False

    def repair_test_with_cache_clear(self, error: ErrorInfo) -> bool:
        """キャッシュクリアでテスト失敗を修復"""
        try:
            subprocess.run(
                ['python', '-c', 'import shutil; shutil.rmtree(".pytest_cache", ignore_errors=True)'],
                timeout=30
            )
            return True
        except Exception as e:
            self.logger.error(f"キャッシュクリアエラー: {e}")
            return False

    def repair_test_with_dependency_reinstall(self, error: ErrorInfo) -> bool:
        """依存関係再インストール"""
        try:
            result = subprocess.run(
                ['pip', 'install', '-r', 'requirements-test.txt', '--force-reinstall'],
                capture_output=True,
                text=True,
                timeout=300
            )
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"依存関係再インストールエラー: {e}")
            return False

    def repair_lint_with_autopep8(self, error: ErrorInfo) -> bool:
        """autopep8でLintエラーを修復"""
        try:
            result = subprocess.run(
                ['autopep8', '--in-place', '--recursive', '--max-line-length=120', 'modules/', 'tests/'],
                capture_output=True,
                text=True,
                timeout=120
            )
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"autopep8修復エラー: {e}")
            return False


# ========================================
# 修復ループ (改善版)
# ========================================

class EnhancedRepairLoop:
    """改善版修復ループ"""

    def __init__(self, config: ConfigManager, max_loops: int = None):
        self.config = config
        self.max_loops = max_loops or config.get('loop_control.max_loops.normal', 7)

        # コンポーネント初期化
        self.resource_monitor = ResourceMonitor(config)
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=config.get('advanced.circuit_breaker.failure_threshold', 3),
            timeout=config.get('advanced.circuit_breaker.timeout', 300)
        )
        self.metrics = MetricsCollector()
        self.detector = EnhancedErrorDetector(config, self.resource_monitor)
        self.repairer = EnhancedAutoRepair(config, self.metrics, self.circuit_breaker)

        self.loop_count = 0
        self.successful_repairs = 0
        self.failed_repairs = 0
        self.initial_error_count = 0
        self.critical_errors = []
        self.warning_errors = []

        self.logger = logging.getLogger(__name__)

    def run(self) -> Dict:
        """修復ループを実行"""
        self.logger.info(f"改善版自動修復ループ開始 (最大{self.max_loops}回)")

        start_time = datetime.now()

        # 初期エラー数を記録
        initial_errors = self.detector.detect_all()
        self.initial_error_count = len(initial_errors)
        self.logger.info(f"初期エラー数: {self.initial_error_count}")

        for loop in range(1, self.max_loops + 1):
            self.loop_count = loop
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"ループ {loop}/{self.max_loops} 開始")
            self.logger.info(f"{'='*60}\n")

            # リソースチェック
            metrics = self.resource_monitor.check_resources()
            self.logger.info(f"リソース: CPU={metrics.cpu_percent:.1f}%, "
                           f"Memory={metrics.memory_percent:.1f}%, "
                           f"Disk={metrics.disk_percent:.1f}%")

            if not self.resource_monitor.is_safe_to_continue(metrics):
                self.logger.error("リソース不足のためループを中断")
                break

            # エラー検知
            errors = self.detector.detect_all()
            self._categorize_errors(errors)

            if not errors:
                self.logger.info("✅ エラーが検出されませんでした")
                break

            self.logger.info(f"検出: クリティカル={len(self.critical_errors)}, "
                           f"警告={len(self.warning_errors)}")

            # クリティカルエラーがなければ部分的成功
            if len(self.critical_errors) == 0 and len(self.warning_errors) > 0:
                self.logger.info("⚠️ 警告レベルのエラーのみです。部分的成功として扱います")
                break

            # エラー修復
            self.logger.info(f"🔧 {len(errors)}個のエラーを修復中...")

            for error in errors:
                self.logger.info(f"  - {error.type}: {error.message[:100]}")

                result = self.repairer.repair(error)

                if result.success:
                    self.successful_repairs += 1
                    self.logger.info(f"    ✅ 修復成功 ({result.duration:.2f}秒)")
                else:
                    self.failed_repairs += 1
                    self.logger.warning(f"    ❌ 修復失敗")

            # 改善が見られたらループを短縮
            current_error_count = len(self.detector.detect_all())
            if current_error_count < self.initial_error_count * 0.3:
                self.logger.info("✅ エラー数が大幅に減少しました。ループを終了します")
                break

            # 最後のループでなければ待機
            if loop < self.max_loops:
                interval = self.config.get('loop_control.interval.normal', 60)
                self.logger.info(f"\n⏳ {interval}秒待機中...\n")
                time.sleep(interval)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # 最終ステータス計算
        final_status = self._calculate_success_status()

        # サマリー生成
        summary = {
            'timestamp': end_time.isoformat(),
            'duration_seconds': duration,
            'total_loops': self.loop_count,
            'max_loops': self.max_loops,
            'successful_repairs': self.successful_repairs,
            'failed_repairs': self.failed_repairs,
            'initial_error_count': self.initial_error_count,
            'final_error_count': len(self.detector.detected_errors),
            'critical_errors': len(self.critical_errors),
            'warning_errors': len(self.warning_errors),
            'error_reduction_rate': self._calculate_error_reduction_rate(),
            'detected_errors': [asdict(e) for e in self.detector.detected_errors],
            'repair_attempts': self.repairer.repair_history,
            'final_status': final_status,
            'recommendations': self._generate_recommendations(),
            'metrics': {
                'success_rate_30d': self.metrics.get_success_rate(days=30),
                'trending_errors': self.metrics.get_trending_errors()
            }
        }

        # サマリーを保存
        with open('repair_summary.json', 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"修復ループ完了: {final_status.upper()}")
        self.logger.info(f"  実行時間: {duration:.1f}秒")
        self.logger.info(f"  ループ数: {self.loop_count}/{self.max_loops}")
        self.logger.info(f"  成功: {self.successful_repairs}, 失敗: {self.failed_repairs}")
        self.logger.info(f"  エラー削減率: {summary['error_reduction_rate']:.1f}%")
        self.logger.info(f"{'='*60}\n")

        return summary

    def _categorize_errors(self, errors: List[ErrorInfo]) -> None:
        """エラーを重大度別に分類"""
        self.critical_errors = []
        self.warning_errors = []

        for error in errors:
            if error.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
                self.critical_errors.append(error)
            else:
                self.warning_errors.append(error)

    def _calculate_success_status(self) -> str:
        """段階的な成功判定"""
        current_errors = self.detector.detect_all()
        self._categorize_errors(current_errors)

        total_errors = len(current_errors)
        critical_count = len(self.critical_errors)
        warning_count = len(self.warning_errors)

        # 完全成功
        if total_errors == 0:
            return 'success'

        # 部分的成功
        if critical_count == 0 and warning_count > 0:
            return 'partial_success'

        # 改善
        if self.initial_error_count > 0:
            reduction_rate = (self.initial_error_count - total_errors) / self.initial_error_count
            if reduction_rate >= 0.5:
                return 'improved'

        # 修復試行あり
        if self.successful_repairs > 0:
            return 'attempted'

        # 失敗
        return 'failed'

    def _calculate_error_reduction_rate(self) -> float:
        """エラー削減率を計算"""
        if self.initial_error_count == 0:
            return 0.0

        final_count = len(self.detector.detected_errors)
        reduction = self.initial_error_count - final_count

        return (reduction / self.initial_error_count) * 100

    def _generate_recommendations(self) -> List[str]:
        """推奨アクションを生成"""
        recommendations = []

        if self.failed_repairs > 0:
            recommendations.append("手動での確認が必要なエラーがあります")

        if self.loop_count >= self.max_loops:
            recommendations.append("最大ループ回数に達しました。エラーログを確認してください")

        if len(self.critical_errors) > 0:
            error_types = set(e.type for e in self.critical_errors)
            for error_type in error_types:
                if error_type == 'SyntaxError':
                    recommendations.append("構文エラーを手動で修正してください")
                elif error_type == 'ImportError':
                    recommendations.append("依存パッケージを確認してください")
                elif error_type == 'TestFailure':
                    recommendations.append("失敗したテストを詳細に調査してください")

        # メトリクスベースの推奨
        success_rate = self.metrics.get_success_rate(days=7)
        if success_rate < 50:
            recommendations.append(f"過去7日間の成功率が低い ({success_rate:.1f}%)。修復戦略の見直しを推奨します")

        if not recommendations:
            recommendations.append("すべてのエラーが修復されました！")

        return recommendations


# ========================================
# メイン処理
# ========================================

def setup_logging(log_level: str = "INFO"):
    """ログ設定"""
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'logs/enhanced_auto_repair_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
            logging.StreamHandler()
        ]
    )


def main():
    parser = argparse.ArgumentParser(description='改善版自動エラー検知・修復ループシステム')
    parser.add_argument('--max-loops', type=int, help='最大ループ回数')
    parser.add_argument('--config', type=str, default='config/auto-repair-recommended.yml',
                       help='設定ファイルパス')
    parser.add_argument('--log-level', type=str, default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                       help='ログレベル')
    parser.add_argument('--dry-run', action='store_true',
                       help='dry-runモード (検知のみ、修復なし)')

    args = parser.parse_args()

    # ログ設定
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    logger.info("="*60)
    logger.info("改善版自動エラー修復システム起動")
    logger.info("="*60)

    try:
        # 設定読み込み
        config = ConfigManager(args.config)

        # 修復ループ実行
        loop = EnhancedRepairLoop(config, max_loops=args.max_loops)

        if args.dry_run:
            logger.info("🔍 Dry-runモード: 検知のみ実行")
            errors = loop.detector.detect_all()
            logger.info(f"検出されたエラー: {len(errors)}個")
            for error in errors:
                logger.info(f"  - {error.type}: {error.message}")
            sys.exit(0)

        summary = loop.run()

        # 終了コード判定
        final_status = summary['final_status']

        if final_status in ['success', 'partial_success', 'improved']:
            logger.info(f"✅ 修復ループが成功しました: {final_status}")
            sys.exit(0)
        elif final_status == 'attempted':
            logger.warning("⚠️ 修復は部分的に行われましたが、完全には解決していません")
            sys.exit(0)
        else:
            logger.error("❌ 修復ループが失敗しました")
            sys.exit(1)

    except Exception as e:
        logger.error(f"予期しないエラー: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
