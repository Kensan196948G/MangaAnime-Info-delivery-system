#!/usr/bin/env python3
"""
エラー復旧機能とスケジューラ最適化 - Phase 2 Implementation

このモジュールは以下の機能を提供します：
- 自動エラー復旧システム
- 適応的リトライ機能
- スケジューラの最適化
- エラー分析と学習機能
"""

import time
import logging
import asyncio
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import json
import sqlite3


class ErrorSeverity(Enum):
    """エラーの重要度レベル"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecoveryStrategy(Enum):
    """復旧戦略の種類"""

    IMMEDIATE_RETRY = "immediate_retry"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    CIRCUIT_BREAKER = "circuit_breaker"
    FALLBACK_SERVICE = "fallback_service"
    SKIP_AND_CONTINUE = "skip_and_continue"
    MANUAL_INTERVENTION = "manual_intervention"


@dataclass
class ErrorContext:
    """エラーコンテキスト情報"""

    timestamp: float
    error_type: str
    error_message: str
    service_name: str
    operation: str
    severity: ErrorSeverity
    recovery_attempts: int = 0
    context_data: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        data = asdict(self)
        data["severity"] = self.severity.value
        return data


@dataclass
class RecoveryAction:
    """復旧アクション定義"""

    strategy: RecoveryStrategy
    max_attempts: int
    delay_seconds: float
    success_threshold: float
    fallback_function: Optional[Callable] = None

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換（シリアライズ用）"""
        return {
            "strategy": self.strategy.value,
            "max_attempts": self.max_attempts,
            "delay_seconds": self.delay_seconds,
            "success_threshold": self.success_threshold,
        }


class ErrorAnalyzer:
    """エラー分析・学習システム"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.error_patterns: Dict[str, List[ErrorContext]] = {}
        self.recovery_success_rates: Dict[str, Dict[str, float]] = {}

    def analyze_error(self, error_context: ErrorContext) -> RecoveryAction:
        """
        エラーを分析し、最適な復旧戦略を決定

        Args:
            error_context: エラーコンテキスト

        Returns:
            最適な復旧アクション
        """
        error_key = f"{error_context.service_name}:{error_context.error_type}"

        # エラーパターンの記録
        if error_key not in self.error_patterns:
            self.error_patterns[error_key] = []
        self.error_patterns[error_key].append(error_context)

        # エラーの頻度と傾向を分析
        recent_errors = self._get_recent_errors(error_key, hours=1)
        error_frequency = len(recent_errors)

        # 復旧戦略の決定
        if error_frequency >= 5:
            # 高頻度エラー - サーキットブレーカー
            return RecoveryAction(
                strategy=RecoveryStrategy.CIRCUIT_BREAKER,
                max_attempts=1,
                delay_seconds=300,  # 5分待機
                success_threshold=0.8,
            )
        elif "timeout" in error_context.error_message.lower():
            # タイムアウトエラー - 指数バックオフ
            return RecoveryAction(
                strategy=RecoveryStrategy.EXPONENTIAL_BACKOFF,
                max_attempts=3,
                delay_seconds=2.0,
                success_threshold=0.7,
            )
        elif "rate limit" in error_context.error_message.lower():
            # レート制限エラー - 長い待機
            return RecoveryAction(
                strategy=RecoveryStrategy.EXPONENTIAL_BACKOFF,
                max_attempts=2,
                delay_seconds=60.0,  # 1分待機
                success_threshold=0.9,
            )
        elif error_context.severity == ErrorSeverity.CRITICAL:
            # 重要なエラー - 手動介入
            return RecoveryAction(
                strategy=RecoveryStrategy.MANUAL_INTERVENTION,
                max_attempts=0,
                delay_seconds=0.0,
                success_threshold=1.0,
            )
        else:
            # 一般的なエラー - 即座にリトライ
            return RecoveryAction(
                strategy=RecoveryStrategy.IMMEDIATE_RETRY,
                max_attempts=2,
                delay_seconds=1.0,
                success_threshold=0.6,
            )

    def _get_recent_errors(self, error_key: str, hours: int = 1) -> List[ErrorContext]:
        """指定時間内の最近のエラーを取得"""
        if error_key not in self.error_patterns:
            return []

        cutoff_time = time.time() - (hours * 3600)
        return [
            error
            for error in self.error_patterns[error_key]
            if error.timestamp > cutoff_time
        ]

    def record_recovery_success(
        self,
        error_context: ErrorContext,
        recovery_action: RecoveryAction,
        success: bool,
    ):
        """復旧の成功/失敗を記録"""
        key = f"{error_context.service_name}:{error_context.error_type}"
        strategy = recovery_action.strategy.value

        if key not in self.recovery_success_rates:
            self.recovery_success_rates[key] = {}

        if strategy not in self.recovery_success_rates[key]:
            self.recovery_success_rates[key][strategy] = 0.5  # 初期値

        # 成功率の更新（移動平均）
        current_rate = self.recovery_success_rates[key][strategy]
        new_rate = current_rate * 0.8 + (1.0 if success else 0.0) * 0.2
        self.recovery_success_rates[key][strategy] = new_rate

        self.logger.debug(
            f"Recovery success rate updated: {key}:{strategy} = {new_rate:.2f}"
        )

    def get_error_statistics(self) -> Dict[str, Any]:
        """エラー統計情報を取得"""
        total_errors = sum(len(errors) for errors in self.error_patterns.values())

        return {
            "total_error_patterns": len(self.error_patterns),
            "total_errors_recorded": total_errors,
            "error_patterns": {
                key: len(errors) for key, errors in self.error_patterns.items()
            },
            "recovery_success_rates": self.recovery_success_rates.copy(),
            "most_common_errors": self._get_most_common_errors(5),
        }

    def _get_most_common_errors(self, limit: int = 5) -> List[Dict[str, Any]]:
        """最も頻繁に発生するエラーを取得"""
        error_counts = [
            {"error_pattern": key, "count": len(errors)}
            for key, errors in self.error_patterns.items()
        ]

        error_counts.sort(key=lambda x: x["count"], reverse=True)
        return error_counts[:limit]


class RecoveryExecutor:
    """復旧処理実行器"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.active_recoveries: Dict[str, threading.Thread] = {}

    async def execute_recovery(
        self,
        error_context: ErrorContext,
        recovery_action: RecoveryAction,
        target_function: Callable,
    ) -> bool:
        """
        復旧処理を実行

        Args:
            error_context: エラーコンテキスト
            recovery_action: 復旧アクション
            target_function: 復旧対象の関数

        Returns:
            復旧成功の場合True
        """
        recovery_key = f"{error_context.service_name}:{error_context.operation}"

        try:
            if recovery_action.strategy == RecoveryStrategy.IMMEDIATE_RETRY:
                return await self._immediate_retry(
                    target_function, recovery_action, error_context
                )

            elif recovery_action.strategy == RecoveryStrategy.EXPONENTIAL_BACKOFF:
                return await self._exponential_backoff_retry(
                    target_function, recovery_action, error_context
                )

            elif recovery_action.strategy == RecoveryStrategy.CIRCUIT_BREAKER:
                return await self._circuit_breaker_recovery(
                    target_function, recovery_action, error_context
                )

            elif recovery_action.strategy == RecoveryStrategy.SKIP_AND_CONTINUE:
                self.logger.info(f"Skipping failed operation: {recovery_key}")
                return True  # スキップは成功として扱う

            elif recovery_action.strategy == RecoveryStrategy.MANUAL_INTERVENTION:
                self.logger.error(f"Manual intervention required: {recovery_key}")
                return False  # 手動介入が必要

            else:
                self.logger.warning(
                    f"Unknown recovery strategy: {recovery_action.strategy}"
                )
                return False

        except Exception as e:
            self.logger.error(f"Recovery execution failed: {e}")
            return False

    async def _immediate_retry(
        self,
        target_function: Callable,
        recovery_action: RecoveryAction,
        error_context: ErrorContext,
    ) -> bool:
        """即座にリトライ"""
        for attempt in range(recovery_action.max_attempts):
            try:
                self.logger.info(f"Immediate retry attempt {attempt + 1}")

                if recovery_action.delay_seconds > 0:
                    await asyncio.sleep(recovery_action.delay_seconds)

                result = await self._execute_target_function(target_function)

                if result:
                    self.logger.info(f"Recovery successful on attempt {attempt + 1}")
                    return True

            except Exception as e:
                self.logger.warning(f"Retry attempt {attempt + 1} failed: {e}")
                continue

        return False

    async def _exponential_backoff_retry(
        self,
        target_function: Callable,
        recovery_action: RecoveryAction,
        error_context: ErrorContext,
    ) -> bool:
        """指数バックオフリトライ"""
        delay = recovery_action.delay_seconds

        for attempt in range(recovery_action.max_attempts):
            try:
                self.logger.info(
                    f"Exponential backoff retry attempt {attempt + 1}, delay: {delay:.1f}s"
                )

                if delay > 0:
                    await asyncio.sleep(delay)

                result = await self._execute_target_function(target_function)

                if result:
                    self.logger.info(f"Recovery successful after {delay:.1f}s delay")
                    return True

                # 指数的に遅延時間を増加
                delay *= 2

            except Exception as e:
                self.logger.warning(
                    f"Exponential backoff attempt {attempt + 1} failed: {e}"
                )
                delay *= 2
                continue

        return False

    async def _circuit_breaker_recovery(
        self,
        target_function: Callable,
        recovery_action: RecoveryAction,
        error_context: ErrorContext,
    ) -> bool:
        """サーキットブレーカー方式の復旧"""
        self.logger.info(
            f"Circuit breaker activated for {recovery_action.delay_seconds}s"
        )

        # サーキットオープン期間の待機
        await asyncio.sleep(recovery_action.delay_seconds)

        try:
            # ハーフオープン状態でテスト
            result = await self._execute_target_function(target_function)

            if result:
                self.logger.info("Circuit breaker test successful - closing circuit")
                return True
            else:
                self.logger.warning(
                    "Circuit breaker test failed - keeping circuit open"
                )
                return False

        except Exception as e:
            self.logger.warning(f"Circuit breaker test exception: {e}")
            return False

    async def _execute_target_function(self, target_function: Callable) -> bool:
        """対象関数の実行（同期・非同期対応）"""
        try:
            if asyncio.iscoroutinefunction(target_function):
                result = await target_function()
            else:
                result = target_function()

            return result is not None and result is not False

        except Exception as e:
            self.logger.debug(f"Target function execution failed: {e}")
            raise


class AdaptiveScheduler:
    """適応的スケジューラー"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.task_performance_history: Dict[str, List[Dict[str, Any]]] = {}
        self.optimal_intervals: Dict[str, float] = {}
        self.load_factors: Dict[str, float] = {}

    def calculate_optimal_interval(
        self,
        task_name: str,
        default_interval: float,
        recent_performance: Dict[str, Any],
    ) -> float:
        """
        最適な実行間隔を計算

        Args:
            task_name: タスク名
            default_interval: デフォルト間隔（秒）
            recent_performance: 最近のパフォーマンス情報

        Returns:
            最適化された実行間隔（秒）
        """
        if task_name not in self.task_performance_history:
            self.task_performance_history[task_name] = []

        # パフォーマンス履歴に追加
        performance_entry = {
            "timestamp": time.time(),
            "execution_time": recent_performance.get("execution_time", 0.0),
            "error_rate": recent_performance.get("error_rate", 0.0),
            "success_rate": recent_performance.get("success_rate", 1.0),
            "load_factor": recent_performance.get("load_factor", 0.5),
        }

        self.task_performance_history[task_name].append(performance_entry)

        # 最新50件の履歴を保持
        if len(self.task_performance_history[task_name]) > 50:
            self.task_performance_history[task_name] = self.task_performance_history[
                task_name
            ][-50:]

        # 統計的分析
        recent_entries = self.task_performance_history[task_name][-10:]  # 最新10件

        if len(recent_entries) < 5:
            return default_interval  # データ不足の場合はデフォルト使用

        avg_execution_time = sum(e["execution_time"] for e in recent_entries) / len(
            recent_entries
        )
        avg_error_rate = sum(e["error_rate"] for e in recent_entries) / len(
            recent_entries
        )
        avg_success_rate = sum(e["success_rate"] for e in recent_entries) / len(
            recent_entries
        )
        avg_load_factor = sum(e["load_factor"] for e in recent_entries) / len(
            recent_entries
        )

        # 最適化計算
        optimal_interval = default_interval

        # 実行時間が長い場合は間隔を延長
        if avg_execution_time > 30:
            optimal_interval *= 1.5
        elif avg_execution_time > 60:
            optimal_interval *= 2.0

        # エラー率が高い場合は間隔を延長
        if avg_error_rate > 0.2:
            optimal_interval *= 1.8
        elif avg_error_rate > 0.1:
            optimal_interval *= 1.3

        # 成功率が低い場合は間隔を延長
        if avg_success_rate < 0.7:
            optimal_interval *= 1.5

        # 負荷が高い場合は間隔を調整
        if avg_load_factor > 0.8:
            optimal_interval *= 1.4
        elif avg_load_factor < 0.3:
            optimal_interval *= 0.8

        # 最小・最大制限
        min_interval = default_interval * 0.5
        max_interval = default_interval * 5.0

        optimal_interval = max(min_interval, min(optimal_interval, max_interval))

        self.optimal_intervals[task_name] = optimal_interval

        self.logger.debug(
            f"Optimal interval for {task_name}: {optimal_interval:.1f}s "
            f"(default: {default_interval}s, "
            f"avg_exec: {avg_execution_time:.1f}s, "
            f"error_rate: {avg_error_rate:.2f})"
        )

        return optimal_interval

    def get_scheduler_statistics(self) -> Dict[str, Any]:
        """スケジューラー統計情報を取得"""
        return {
            "tracked_tasks": list(self.optimal_intervals.keys()),
            "optimal_intervals": self.optimal_intervals.copy(),
            "performance_history_counts": {
                task: len(history)
                for task, history in self.task_performance_history.items()
            },
        }


class SmartErrorRecoverySystem:
    """
    統合エラー復旧システム - Phase 2 Implementation

    エラー分析、復旧実行、スケジューラ最適化を統合したシステム
    """

    def __init__(self, db_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path or "error_recovery.db"

        self.error_analyzer = ErrorAnalyzer()
        self.recovery_executor = RecoveryExecutor()
        self.adaptive_scheduler = AdaptiveScheduler()

        self.recovery_statistics = {
            "total_errors_handled": 0,
            "successful_recoveries": 0,
            "failed_recoveries": 0,
            "manual_interventions": 0,
            "start_time": time.time(),
        }

        self._init_database()

    def _init_database(self):
        """データベース初期化"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS error_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL,
                    error_type TEXT,
                    error_message TEXT,
                    service_name TEXT,
                    operation TEXT,
                    severity TEXT,
                    recovery_attempts INTEGER,
                    context_data TEXT,
                    recovery_success BOOLEAN,
                    recovery_strategy TEXT
                )
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_error_logs_timestamp
                ON error_logs(timestamp)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_error_logs_service
                ON error_logs(service_name)
            """
            )

            conn.commit()
            conn.close()

            self.logger.info(f"Error recovery database initialized: {self.db_path}")

        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")

    async def handle_error(
        self,
        error: Exception,
        service_name: str,
        operation: str,
        target_function: Callable,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        エラーハンドリングと復旧処理

        Args:
            error: 発生したエラー
            service_name: サービス名
            operation: 操作名
            target_function: 復旧対象の関数
            severity: エラーの重要度
            context_data: 追加のコンテキストデータ

        Returns:
            復旧成功の場合True
        """
        # エラーコンテキスト作成
        error_context = ErrorContext(
            timestamp=time.time(),
            error_type=type(error).__name__,
            error_message=str(error),
            service_name=service_name,
            operation=operation,
            severity=severity,
            context_data=context_data or {},
        )

        self.recovery_statistics["total_errors_handled"] += 1

        self.logger.warning(
            f"Error handling started: {service_name}:{operation} - {error}"
        )

        # エラー分析と復旧戦略決定
        recovery_action = self.error_analyzer.analyze_error(error_context)

        # データベースログ記録
        self._log_error_to_db(error_context, recovery_action, None)

        # 復旧処理実行
        recovery_success = False

        if recovery_action.strategy != RecoveryStrategy.MANUAL_INTERVENTION:
            try:
                recovery_success = await self.recovery_executor.execute_recovery(
                    error_context, recovery_action, target_function
                )
            except Exception as recovery_error:
                self.logger.error(f"Recovery execution failed: {recovery_error}")
                recovery_success = False
        else:
            self.recovery_statistics["manual_interventions"] += 1
            self.logger.critical(
                f"Manual intervention required: {service_name}:{operation}"
            )

        # 復旧結果の記録
        self.error_analyzer.record_recovery_success(
            error_context, recovery_action, recovery_success
        )

        if recovery_success:
            self.recovery_statistics["successful_recoveries"] += 1
        else:
            self.recovery_statistics["failed_recoveries"] += 1

        # データベース更新
        self._update_error_log(
            error_context, recovery_success, recovery_action.strategy.value
        )

        self.logger.info(
            f"Error handling completed: {service_name}:{operation} - "
            f"Success: {recovery_success}, Strategy: {recovery_action.strategy.value}"
        )

        return recovery_success

    def _log_error_to_db(
        self,
        error_context: ErrorContext,
        recovery_action: RecoveryAction,
        recovery_success: Optional[bool],
    ):
        """エラーログをデータベースに記録"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO error_logs (
                    timestamp, error_type, error_message, service_name,
                    operation, severity, recovery_attempts, context_data,
                    recovery_success, recovery_strategy
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    error_context.timestamp,
                    error_context.error_type,
                    error_context.error_message,
                    error_context.service_name,
                    error_context.operation,
                    error_context.severity.value,
                    error_context.recovery_attempts,
                    (
                        json.dumps(error_context.context_data)
                        if error_context.context_data
                        else None
                    ),
                    recovery_success,
                    recovery_action.strategy.value,
                ),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"Error logging to database failed: {e}")

    def _update_error_log(
        self, error_context: ErrorContext, recovery_success: bool, strategy: str
    ):
        """エラーログの更新"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                UPDATE error_logs
                SET recovery_success = ?, recovery_strategy = ?
                WHERE timestamp = ? AND service_name = ? AND operation = ?
            """,
                (
                    recovery_success,
                    strategy,
                    error_context.timestamp,
                    error_context.service_name,
                    error_context.operation,
                ),
            )

            conn.commit()
            conn.close()

        except Exception as e:
            self.logger.error(f"Error log update failed: {e}")

    def optimize_schedule(
        self,
        task_name: str,
        default_interval: float,
        execution_time: float,
        error_rate: float,
        success_rate: float,
        load_factor: float = 0.5,
    ) -> float:
        """
        スケジュール最適化

        Args:
            task_name: タスク名
            default_interval: デフォルト実行間隔
            execution_time: 実行時間
            error_rate: エラー率
            success_rate: 成功率
            load_factor: システム負荷率

        Returns:
            最適化された実行間隔
        """
        performance_data = {
            "execution_time": execution_time,
            "error_rate": error_rate,
            "success_rate": success_rate,
            "load_factor": load_factor,
        }

        optimal_interval = self.adaptive_scheduler.calculate_optimal_interval(
            task_name, default_interval, performance_data
        )

        return optimal_interval

    def get_comprehensive_statistics(self) -> Dict[str, Any]:
        """包括的な統計情報を取得"""
        uptime_hours = (time.time() - self.recovery_statistics["start_time"]) / 3600.0

        return {
            "system_uptime_hours": uptime_hours,
            "recovery_statistics": self.recovery_statistics.copy(),
            "error_analysis": self.error_analyzer.get_error_statistics(),
            "scheduler_optimization": self.adaptive_scheduler.get_scheduler_statistics(),
            "recovery_success_rate": (
                self.recovery_statistics["successful_recoveries"]
                / max(self.recovery_statistics["total_errors_handled"], 1)
            ),
        }

    def export_error_report(self, hours: int = 24) -> Dict[str, Any]:
        """エラーレポートをエクスポート"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cutoff_time = time.time() - (hours * 3600)

            cursor.execute(
                """
                SELECT service_name, operation, error_type,
                       COUNT(*) as error_count,
                       AVG(CASE WHEN recovery_success = 1 THEN 1.0 ELSE 0.0 END) as success_rate,
                       recovery_strategy
                FROM error_logs
                WHERE timestamp > ?
                GROUP BY service_name, operation, error_type, recovery_strategy
                ORDER BY error_count DESC
            """,
                (cutoff_time,),
            )

            error_summary = []
            for row in cursor.fetchall():
                error_summary.append(
                    {
                        "service_name": row[0],
                        "operation": row[1],
                        "error_type": row[2],
                        "error_count": row[3],
                        "recovery_success_rate": row[4],
                        "recovery_strategy": row[5],
                    }
                )

            conn.close()

            return {
                "report_period_hours": hours,
                "generated_at": datetime.now().isoformat(),
                "error_summary": error_summary,
                "system_statistics": self.get_comprehensive_statistics(),
            }

        except Exception as e:
            self.logger.error(f"Error report export failed: {e}")
            return {
                "error": str(e),
                "system_statistics": self.get_comprehensive_statistics(),
            }


# Global error recovery system instance
_error_recovery_system: Optional[SmartErrorRecoverySystem] = None


def initialize_error_recovery(
    db_path: Optional[str] = None,
) -> SmartErrorRecoverySystem:
    """エラー復旧システムの初期化"""
    global _error_recovery_system
    _error_recovery_system = SmartErrorRecoverySystem(db_path)
    return _error_recovery_system


def get_error_recovery_system() -> Optional[SmartErrorRecoverySystem]:
    """グローバルエラー復旧システムの取得"""
    return _error_recovery_system


async def handle_system_error(
    error: Exception,
    service_name: str,
    operation: str,
    target_function: Callable,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    context_data: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    システムエラーハンドリング関数

    Args:
        error: 発生したエラー
        service_name: サービス名
        operation: 操作名
        target_function: 復旧対象の関数
        severity: エラーの重要度
        context_data: 追加のコンテキストデータ

    Returns:
        復旧成功の場合True
    """
    recovery_system = get_error_recovery_system()
    if recovery_system:
        return await recovery_system.handle_error(
            error, service_name, operation, target_function, severity, context_data
        )
    else:
        logging.getLogger(__name__).error("Error recovery system not initialized")
        return False


def optimize_task_schedule(
    task_name: str,
    default_interval: float,
    execution_time: float,
    error_rate: float,
    success_rate: float,
    load_factor: float = 0.5,
) -> float:
    """
    タスクスケジュール最適化関数

    Args:
        task_name: タスク名
        default_interval: デフォルト実行間隔
        execution_time: 実行時間
        error_rate: エラー率
        success_rate: 成功率
        load_factor: システム負荷率

    Returns:
        最適化された実行間隔
    """
    recovery_system = get_error_recovery_system()
    if recovery_system:
        return recovery_system.optimize_schedule(
            task_name,
            default_interval,
            execution_time,
            error_rate,
            success_rate,
            load_factor,
        )
    else:
        return default_interval
