#!/usr/bin/env python3
"""
7回ループ自動修復システムの状態管理スクリプト
30分のクールダウン期間を管理
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path


class RepairLoopManager:
    def __init__(self):
        self.state_dir = Path(".repair-state")
        self.state_dir.mkdir(exist_ok=True)
        self.state_file = self.state_dir / "loop_state.json"
        self.max_attempts_per_cycle = 7
        self.cooldown_minutes = 30
        self.max_cycles_before_escalation = 3

    def load_state(self):
        """現在の状態を読み込み"""
        if self.state_file.exists():
            with open(self.state_file, "r") as f:
                return json.load(f)
        return self.get_initial_state()

    def get_initial_state(self):
        """初期状態を作成"""
        return {
            "current_cycle": 1,
            "attempts_in_cycle": 0,
            "total_attempts": 0,
            "last_attempt_time": None,
            "cycle_end_time": None,
            "in_cooldown": False,
            "issues_processed": [],
            "repair_history": [],
        }

    def save_state(self, state):
        """状態を保存"""
        with open(self.state_file, "w") as f:
            json.dump(state, f, indent=2, default=str)

    def can_attempt_repair(self):
        """修復試行が可能かチェック"""
        state = self.load_state()

        # クールダウン中かチェック
        if state["in_cooldown"] and state["cycle_end_time"]:
            cycle_end = datetime.fromisoformat(state["cycle_end_time"])
            cooldown_end = cycle_end + timedelta(minutes=self.cooldown_minutes)

            if datetime.now() < cooldown_end:
                remaining = (cooldown_end - datetime.now()).total_seconds()
                logger.info(
                    f"⏸️  Cooldown active. Remaining: {int(remaining / 60)} minutes {int(remaining % 60)} seconds"
                )
                return False, state
            else:
                # クールダウン終了、次のサイクルへ
                state["in_cooldown"] = False
                state["current_cycle"] += 1
                state["attempts_in_cycle"] = 0
                self.save_state(state)
                logger.info(f"🔄 Starting new cycle {state['current_cycle']}")

        # 現在のサイクルで試行可能かチェック
        if state["attempts_in_cycle"] >= self.max_attempts_per_cycle:
            # サイクル終了、クールダウンへ
            state["in_cooldown"] = True
            state["cycle_end_time"] = datetime.now().isoformat()
            self.save_state(state)
            logger.info(
                f"💤 Cycle {state['current_cycle']} complete. Entering {self.cooldown_minutes} minute cooldown..."
            )
            return False, state

        return True, state

    def record_attempt(self, success=False, error_details=None):
        """修復試行を記録"""
        state = self.load_state()

        state["attempts_in_cycle"] += 1
        state["total_attempts"] += 1
        state["last_attempt_time"] = datetime.now().isoformat()

        # 履歴に追加
        state["repair_history"].append(
            {
                "cycle": state["current_cycle"],
                "attempt": state["attempts_in_cycle"],
                "total_attempt": state["total_attempts"],
                "timestamp": datetime.now().isoformat(),
                "success": success,
                "error": error_details,
            }
        )

        # 履歴は最新100件のみ保持
        if len(state["repair_history"]) > 100:
            state["repair_history"] = state["repair_history"][-100:]

        self.save_state(state)

        logger.info(
            f"📊 Cycle {state['current_cycle']}, Attempt {state['attempts_in_cycle']}/{self.max_attempts_per_cycle}"
        )
        logger.info(f"   Total attempts: {state['total_attempts']}")
        logger.info(f"   Result: {'✅ Success' if success else '❌ Failed'}")

        return state

    def check_escalation_needed(self):
        """エスカレーションが必要かチェック"""
        state = self.load_state()

        if state["current_cycle"] > self.max_cycles_before_escalation:
            logger.info(f"⚠️  Escalation needed! {state['current_cycle']} cycles attempted.")
            return True

        return False

    def get_status_summary(self):
        """現在の状態サマリーを取得"""
        state = self.load_state()

        summary = {
            "current_cycle": state["current_cycle"],
            "attempts_in_cycle": state["attempts_in_cycle"],
            "max_attempts_per_cycle": self.max_attempts_per_cycle,
            "total_attempts": state["total_attempts"],
            "in_cooldown": state["in_cooldown"],
            "needs_escalation": self.check_escalation_needed(),
        }

        if state["in_cooldown"] and state["cycle_end_time"]:
            cycle_end = datetime.fromisoformat(state["cycle_end_time"])
            cooldown_end = cycle_end + timedelta(minutes=self.cooldown_minutes)
            remaining = max(0, (cooldown_end - datetime.now()).total_seconds())
            summary["cooldown_remaining_seconds"] = int(remaining)

        # 成功率を計算
        if state["repair_history"]:
            successful = sum(1 for h in state["repair_history"] if h["success"])
            summary[
                "success_rate"
            ] = f"{(successful / len(state['repair_history']) * 100):.1f}%"

        return summary

    def reset_state(self):
        """状態をリセット"""
        initial_state = self.get_initial_state()

        self.save_state(initial_state)
        logger.info("🔄 Repair loop state reset")
        return initial_state


def main():
    """CLIエントリーポイント"""
    import argparse

    parser = argparse.ArgumentParser(description="Repair Loop Manager")
    parser.add_argument(
        "action",
        choices=["check", "attempt", "status", "reset"],
        help="Action to perform",
    )
    parser.add_argument(
        "--success", action="store_true", help="Mark attempt as successful"
    )
    parser.add_argument("--error", type=str, help="Error details for failed attempt")

    args = parser.parse_args()

    manager = RepairLoopManager()

    if args.action == "check":
        can_repair, state = manager.can_attempt_repair()
        sys.exit(0 if can_repair else 1)

    elif args.action == "attempt":
        can_repair, state = manager.can_attempt_repair()
        if can_repair:
            manager.record_attempt(success=args.success, error_details=args.error)
        else:
            logger.info("Cannot attempt repair at this time")
            sys.exit(1)

    elif args.action == "status":
        summary = manager.get_status_summary()
        logger.info("\n📊 Repair Loop Status")
        logger.info("=" * 50)
        for key, value in summary.items():
            logger.info(f"{key}: {value}")

    elif args.action == "reset":
        manager.reset_state()


if __name__ == "__main__":
    main()
