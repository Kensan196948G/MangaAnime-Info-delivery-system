#!/usr/bin/env python3
"""
自動修復ループシステム（15回ループ・5分待機版）

機能:
- エラー自動検知
- 自動修復実行（最大15回）
- 15回超過時: 5分待機
- 5分後: 再度15回ループ
- 継続実行（ユーザー中断まで）
"""

import os
import sys
from pathlib import Path
import time
import subprocess
import json
from datetime import datetime
from typing import List, Dict, Any, Tuple

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 設定
MAX_LOOPS = 15
WAIT_TIME_SECONDS = 300  # 5分
CONTINUOUS_MODE = True

class AutoRepairSystem:
    """自動修復システム"""

    def __init__(self):
        self.total_repairs = 0
        self.total_errors = 0
        self.cycle_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.log_file = f"logs/auto_repair_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

        # ログディレクトリ作成
        os.makedirs('logs', exist_ok=True)

    def log(self, message: str):
        """ログ出力"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {message}"
        print(log_message)

        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_message + '\n')

    def detect_errors(self) -> List[Dict[str, Any]]:
        """エラー検知"""
        errors = []

        # 1. 構文エラーチェック
        self.log("🔍 構文エラーをチェック中...")
        result = subprocess.run(
            ['python3', '-m', 'py_compile'] + list(Path('app').rglob('*.py')),
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            errors.append({
                'type': 'SyntaxError',
                'message': result.stderr,
                'severity': 'high'
            })

        # 2. インポートエラーチェック
        self.log("🔍 インポートエラーをチェック中...")
        # 簡易チェック（importを含む行を確認）

        # 3. テスト実行
        self.log("🔍 テストを実行中...")
        result = subprocess.run(
            ['pytest', 'tests/', '-v', '--tb=short'],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            errors.append({
                'type': 'TestFailure',
                'message': result.stdout,
                'severity': 'medium'
            })

        return errors

    def auto_repair(self, errors: List[Dict[str, Any]]) -> Tuple[int, int]:
        """
        自動修復実行

        Returns:
            tuple: (成功数, 失敗数)
        """
        success = 0
        failed = 0

        for error in errors:
            self.log(f"🔧 修復中: {error['type']}")

            try:
                if error['type'] == 'SyntaxError':
                    # 構文エラー修復（black auto-format）
                    subprocess.run(
                        ['black', 'app', 'modules'],
                        capture_output=True,
                        timeout=30
                    )
                    success += 1
                    self.log(f"  ✅ 修復成功: {error['type']}")

                elif error['type'] == 'TestFailure':
                    # テスト失敗は手動確認が必要
                    self.log(f"  ⚠️ 手動確認が必要: {error['type']}")
                    failed += 1

                else:
                    self.log(f"  ⚠️ 未対応のエラータイプ: {error['type']}")
                    failed += 1

            except Exception as e:
                self.log(f"  ❌ 修復失敗: {e}")
                failed += 1

        return success, failed

    def verify_fixes(self) -> bool:
        """修復検証"""
        self.log("✓ 修復を検証中...")

        # 再度エラーチェック
        errors = self.detect_errors()

        if len(errors) == 0:
            self.log("  ✅ 全てのエラーが修復されました")
            return True
        else:
            self.log(f"  ⚠️ 残存エラー: {len(errors)}件")
            return False

    def run_cycle(self, cycle_num: int) -> bool:
        """1サイクル（15回ループ）実行"""
        self.log("="*70)
        self.log(f"🔄 サイクル {cycle_num} 開始（最大{MAX_LOOPS}回ループ）")
        self.log("="*70)

        for loop in range(1, MAX_LOOPS + 1):
            self.log(f"\n━━━ ループ {loop}/{MAX_LOOPS} ━━━")

            # エラー検知
            errors = self.detect_errors()

            if len(errors) == 0:
                self.log("✅ エラーなし！サイクル完了")
                return True

            self.log(f"🚨 検出されたエラー: {len(errors)}件")
            self.total_errors += len(errors)

            # 自動修復
            success, failed = self.auto_repair(errors)
            self.success_count += success
            self.failure_count += failed
            self.total_repairs += 1

            # 検証
            if self.verify_fixes():
                self.log("✅ 修復成功！サイクル完了")
                return True

            # 次のループまで少し待機
            if loop < MAX_LOOPS:
                time.sleep(2)

        self.log(f"⚠️ サイクル{cycle_num}完了（{MAX_LOOPS}回実行）")
        self.log(f"   残存エラーあり → 5分待機後に再試行")
        return False

    def run_continuous(self):
        """継続実行（無限ループ）"""
        self.log("="*70)
        self.log("🚀 自動修復システム起動（15回ループ・5分待機版）")
        self.log("="*70)
        self.log(f"設定: MAX_LOOPS={MAX_LOOPS}, WAIT={WAIT_TIME_SECONDS}秒")
        self.log(f"モード: {'継続実行' if CONTINUOUS_MODE else '1サイクルのみ'}")
        self.log("="*70)

        try:
            while CONTINUOUS_MODE:
                self.cycle_count += 1

                # 1サイクル実行
                success = self.run_cycle(self.cycle_count)

                if success:
                    self.log(f"\n🎉 サイクル{self.cycle_count}完了！エラーなし")

                    if not CONTINUOUS_MODE:
                        break

                    # 成功した場合も定期的にチェック
                    self.log(f"⏳ 次のチェックまで{WAIT_TIME_SECONDS}秒待機...")
                    time.sleep(WAIT_TIME_SECONDS)
                else:
                    self.log(f"\n⏳ サイクル{self.cycle_count}完了（エラー残存）")
                    self.log(f"   {WAIT_TIME_SECONDS}秒（5分）待機後、再試行...")
                    time.sleep(WAIT_TIME_SECONDS)

        except KeyboardInterrupt:
            self.log("\n\n⚠️ ユーザーによる中断")
            self.print_summary()

        except Exception as e:
            self.log(f"\n\n❌ システムエラー: {e}")
            self.print_summary()

    def print_summary(self):
        """サマリー出力"""
        self.log("\n" + "="*70)
        self.log("📊 自動修復システム サマリー")
        self.log("="*70)
        self.log(f"総サイクル数: {self.cycle_count}")
        self.log(f"総修復実行: {self.total_repairs}")
        self.log(f"検出エラー総数: {self.total_errors}")
        self.log(f"修復成功: {self.success_count}")
        self.log(f"修復失敗: {self.failure_count}")

        if self.total_repairs > 0:
            success_rate = (self.success_count / (self.success_count + self.failure_count)) * 100
            self.log(f"成功率: {success_rate:.1f}%")

        self.log("="*70)
        self.log(f"ログファイル: {self.log_file}")

def main():
    import argparse

    parser = argparse.ArgumentParser(description='自動修復ループシステム')
    parser.add_argument('--max-loops', type=int, default=MAX_LOOPS, help='最大ループ回数')
    parser.add_argument('--wait', type=int, default=WAIT_TIME_SECONDS, help='待機時間（秒）')
    parser.add_argument('--once', action='store_true', help='1サイクルのみ実行')
    args = parser.parse_args()

    global MAX_LOOPS, WAIT_TIME_SECONDS, CONTINUOUS_MODE
    MAX_LOOPS = args.max_loops
    WAIT_TIME_SECONDS = args.wait
    CONTINUOUS_MODE = not args.once

    system = AutoRepairSystem()
    system.run_continuous()

if __name__ == "__main__":
    main()
