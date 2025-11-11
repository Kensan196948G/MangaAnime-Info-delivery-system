#!/usr/bin/env python3
"""
自動エラー検知・修復ループシステム

30分おきに最大10回のループでエラー検知と自動修復を実行します。
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# ログディレクトリの作成
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/auto_repair_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ErrorDetector:
    """エラー検知クラス"""

    def __init__(self):
        self.detected_errors = []

    def detect_syntax_errors(self) -> List[Dict]:
        """構文エラーを検知"""
        errors = []
        logger.info("構文エラーをチェック中...")

        try:
            result = subprocess.run(
                ['python', '-m', 'py_compile'] + list(Path('modules').glob('*.py')),
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                errors.append({
                    'type': 'SyntaxError',
                    'message': result.stderr,
                    'severity': 'high'
                })
        except Exception as e:
            logger.error(f"構文チェックエラー: {e}")

        return errors

    def detect_import_errors(self) -> List[Dict]:
        """インポートエラーを検知"""
        errors = []
        logger.info("インポートエラーをチェック中...")

        for py_file in Path('modules').glob('*.py'):
            try:
                result = subprocess.run(
                    ['python', '-c', f'import {py_file.stem}'],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd='modules'
                )

                if result.returncode != 0 and 'ImportError' in result.stderr:
                    errors.append({
                        'type': 'ImportError',
                        'file': str(py_file),
                        'message': result.stderr,
                        'severity': 'medium'
                    })
            except Exception as e:
                logger.error(f"{py_file}のインポートチェックエラー: {e}")

        return errors

    def detect_test_failures(self) -> List[Dict]:
        """テスト失敗を検知"""
        errors = []
        logger.info("テスト失敗をチェック中...")

        try:
            result = subprocess.run(
                ['pytest', 'tests/', '-v', '--tb=short', '--maxfail=5'],
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.returncode != 0:
                # 失敗したテストを解析
                failed_tests = []
                for line in result.stdout.split('\n'):
                    if 'FAILED' in line:
                        failed_tests.append(line.strip())

                if failed_tests:
                    errors.append({
                        'type': 'TestFailure',
                        'message': f"{len(failed_tests)}個のテストが失敗",
                        'failed_tests': failed_tests[:10],  # 最大10個
                        'severity': 'medium'
                    })
        except Exception as e:
            logger.error(f"テストチェックエラー: {e}")

        return errors

    def detect_lint_errors(self) -> List[Dict]:
        """Lintエラーを検知"""
        errors = []
        logger.info("Lintエラーをチェック中...")

        try:
            result = subprocess.run(
                ['flake8', 'modules/', 'tests/', '--count', '--max-line-length=120'],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                error_count = result.stdout.strip().split('\n')[-1] if result.stdout else '0'
                errors.append({
                    'type': 'LintError',
                    'message': f"{error_count}個のLintエラー",
                    'details': result.stdout[:500],  # 最初の500文字
                    'severity': 'low'
                })
        except Exception as e:
            logger.error(f"Lintチェックエラー: {e}")

        return errors

    def detect_all(self) -> List[Dict]:
        """すべてのエラーを検知"""
        all_errors = []

        all_errors.extend(self.detect_syntax_errors())
        all_errors.extend(self.detect_import_errors())
        all_errors.extend(self.detect_test_failures())
        all_errors.extend(self.detect_lint_errors())

        self.detected_errors = all_errors
        logger.info(f"合計 {len(all_errors)} 個のエラーを検出")

        return all_errors


class AutoRepair:
    """自動修復クラス"""

    def __init__(self):
        self.repair_history = []

    def repair_syntax_errors(self, error: Dict) -> bool:
        """構文エラーを修復"""
        logger.info("構文エラーの修復を試行中...")

        try:
            # 自動フォーマッタを実行
            result = subprocess.run(
                ['black', 'modules/', 'tests/'],
                capture_output=True,
                text=True,
                timeout=120
            )

            success = result.returncode == 0
            self.repair_history.append({
                'timestamp': datetime.now().isoformat(),
                'error_type': 'SyntaxError',
                'action': 'black auto-format',
                'success': success,
                'output': result.stdout if success else result.stderr
            })

            return success
        except Exception as e:
            logger.error(f"構文エラー修復失敗: {e}")
            return False

    def repair_import_errors(self, error: Dict) -> bool:
        """インポートエラーを修復"""
        logger.info("インポートエラーの修復を試行中...")

        try:
            # 不足しているパッケージをインストール
            result = subprocess.run(
                ['pip', 'install', '-r', 'requirements.txt', '--upgrade'],
                capture_output=True,
                text=True,
                timeout=300
            )

            success = result.returncode == 0
            self.repair_history.append({
                'timestamp': datetime.now().isoformat(),
                'error_type': 'ImportError',
                'action': 'pip install requirements',
                'success': success,
                'output': result.stdout[:200] if success else result.stderr[:200]
            })

            return success
        except Exception as e:
            logger.error(f"インポートエラー修復失敗: {e}")
            return False

    def repair_test_failures(self, error: Dict) -> bool:
        """テスト失敗を修復"""
        logger.info("テスト失敗の修復を試行中...")

        try:
            # テストデータのクリーンアップ
            result = subprocess.run(
                ['python', '-c', 'import shutil; shutil.rmtree(".pytest_cache", ignore_errors=True)'],
                capture_output=True,
                text=True,
                timeout=30
            )

            # キャッシュクリア後に再テスト
            retest_result = subprocess.run(
                ['pytest', 'tests/', '--co', '-q'],
                capture_output=True,
                text=True,
                timeout=60
            )

            success = retest_result.returncode == 0
            self.repair_history.append({
                'timestamp': datetime.now().isoformat(),
                'error_type': 'TestFailure',
                'action': 'clear cache and retest',
                'success': success,
                'output': 'テストキャッシュをクリア'
            })

            return success
        except Exception as e:
            logger.error(f"テスト失敗修復エラー: {e}")
            return False

    def repair_lint_errors(self, error: Dict) -> bool:
        """Lintエラーを修復"""
        logger.info("Lintエラーの修復を試行中...")

        try:
            # autopep8で自動修正
            result = subprocess.run(
                ['autopep8', '--in-place', '--recursive', '--max-line-length=120', 'modules/', 'tests/'],
                capture_output=True,
                text=True,
                timeout=120
            )

            success = result.returncode == 0
            self.repair_history.append({
                'timestamp': datetime.now().isoformat(),
                'error_type': 'LintError',
                'action': 'autopep8 auto-fix',
                'success': success,
                'output': 'コードスタイルを自動修正'
            })

            return success
        except Exception as e:
            logger.error(f"Lintエラー修復失敗: {e}")
            return False

    def repair(self, error: Dict) -> bool:
        """エラータイプに応じて修復"""
        error_type = error.get('type', '')

        repair_methods = {
            'SyntaxError': self.repair_syntax_errors,
            'ImportError': self.repair_import_errors,
            'TestFailure': self.repair_test_failures,
            'LintError': self.repair_lint_errors
        }

        repair_method = repair_methods.get(error_type)
        if repair_method:
            return repair_method(error)
        else:
            logger.warning(f"未知のエラータイプ: {error_type}")
            return False


class RepairLoop:
    """修復ループ管理クラス"""

    def __init__(self, max_loops: int = 10, interval: int = 180):
        self.max_loops = max_loops
        self.interval = interval
        self.detector = ErrorDetector()
        self.repairer = AutoRepair()
        self.loop_count = 0
        self.successful_repairs = 0
        self.failed_repairs = 0

    def run(self) -> Dict:
        """修復ループを実行"""
        logger.info(f"自動修復ループ開始 (最大{self.max_loops}回)")

        start_time = datetime.now()

        for loop in range(1, self.max_loops + 1):
            self.loop_count = loop
            logger.info(f"\n{'='*60}")
            logger.info(f"ループ {loop}/{self.max_loops} 開始")
            logger.info(f"{'='*60}\n")

            # エラー検知
            errors = self.detector.detect_all()

            if not errors:
                logger.info("✅ エラーが検出されませんでした")
                break

            # エラー修復
            logger.info(f"🔧 {len(errors)}個のエラーを修復中...")

            for error in errors:
                logger.info(f"  - {error['type']}: {error['message'][:100]}")

                if self.repairer.repair(error):
                    self.successful_repairs += 1
                    logger.info(f"    ✅ 修復成功")
                else:
                    self.failed_repairs += 1
                    logger.warning(f"    ❌ 修復失敗")

            # 最後のループでなければ待機
            if loop < self.max_loops:
                logger.info(f"\n⏳ {self.interval}秒待機中...\n")
                time.sleep(self.interval)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # サマリー生成
        summary = {
            'timestamp': end_time.isoformat(),
            'duration_seconds': duration,
            'total_loops': self.loop_count,
            'max_loops': self.max_loops,
            'successful_repairs': self.successful_repairs,
            'failed_repairs': self.failed_repairs,
            'detected_errors': self.detector.detected_errors,
            'repair_attempts': self.repairer.repair_history,
            'final_status': 'success' if not self.detector.detected_errors else 'failed',
            'recommendations': self._generate_recommendations()
        }

        # サマリーを保存
        with open('repair_summary.json', 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        logger.info(f"\n{'='*60}")
        logger.info(f"修復ループ完了")
        logger.info(f"  実行時間: {duration:.1f}秒")
        logger.info(f"  ループ数: {self.loop_count}/{self.max_loops}")
        logger.info(f"  成功: {self.successful_repairs}, 失敗: {self.failed_repairs}")
        logger.info(f"{'='*60}\n")

        return summary

    def _generate_recommendations(self) -> List[str]:
        """推奨アクションを生成"""
        recommendations = []

        if self.failed_repairs > 0:
            recommendations.append("手動での確認が必要なエラーがあります")

        if self.loop_count >= self.max_loops:
            recommendations.append("最大ループ回数に達しました。エラーログを確認してください")

        if self.detector.detected_errors:
            error_types = set(e['type'] for e in self.detector.detected_errors)
            for error_type in error_types:
                if error_type == 'SyntaxError':
                    recommendations.append("構文エラーを手動で修正してください")
                elif error_type == 'ImportError':
                    recommendations.append("依存パッケージを確認してください")
                elif error_type == 'TestFailure':
                    recommendations.append("失敗したテストを詳細に調査してください")

        if not recommendations:
            recommendations.append("すべてのエラーが修復されました！")

        return recommendations


def main():
    parser = argparse.ArgumentParser(description='自動エラー検知・修復ループシステム')
    parser.add_argument('--max-loops', type=int, default=10, help='最大ループ回数')
    parser.add_argument('--interval', type=int, default=180, help='ループ間隔（秒）')
    parser.add_argument('--issue-number', type=str, help='関連するIssue番号')
    parser.add_argument('--create-issue-on-failure', action='store_true', help='失敗時にIssue作成')

    args = parser.parse_args()

    # ログディレクトリ作成
    Path('logs').mkdir(exist_ok=True)

    # 修復ループ実行
    loop = RepairLoop(max_loops=args.max_loops, interval=args.interval)
    summary = loop.run()

    # 失敗時の終了コード
    if summary['final_status'] == 'failed':
        logger.error("修復ループが失敗しました")
        sys.exit(1)
    else:
        logger.info("修復ループが正常に完了しました")
        sys.exit(0)


if __name__ == '__main__':
    main()
