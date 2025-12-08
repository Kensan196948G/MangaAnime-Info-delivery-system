#!/usr/bin/env python3
"""
メール配信スケジューラー

大量通知の自動分散機能：
- 100件以上: 2回分散（朝8時、夜20時）
- 200件以上: 3回分散（朝8時、昼12時、夜20時）
- 日本時間（Asia/Tokyo）対応
"""

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import pytz

logger = logging.getLogger(__name__)

# 日本時間タイムゾーン
JST = pytz.timezone("Asia/Tokyo")


@dataclass
class DeliverySchedule:
    """配信スケジュール情報"""

    hour: int
    minute: int = 0
    description: str = ""

    def to_time_str(self) -> str:
        return f"{self.hour:02d}:{self.minute:02d}"


@dataclass
class EmailBatch:
    """メール配信バッチ"""

    schedule: DeliverySchedule
    releases: List[Dict[str, Any]]
    batch_id: str
    total_batches: int
    current_batch: int

    def get_subject_prefix(self) -> str:
        """件名のプレフィックスを取得"""
        if self.total_batches == 1:
            return "[アニメ・マンガ情報]"
        else:
            return f"[アニメ・マンガ情報 {self.current_batch}/{self.total_batches}]"


class EmailScheduler:
    """メール配信スケジューラー"""

    # デフォルト配信スケジュール
    DEFAULT_SCHEDULES = [
        DeliverySchedule(8, 0, "朝の配信"),
        DeliverySchedule(12, 0, "昼の配信"),
        DeliverySchedule(20, 0, "夜の配信"),
    ]

    def __init__(self, config: Any, state_file_path: Optional[str] = None):
        """
        初期化

        Args:
            config: システム設定
            state_file_path: 配信状態ファイルのパス
        """
        self.config = config
        self.state_file_path = state_file_path or "data/email_scheduler_state.json"

        # 配信閾値の設定
        self.thresholds = {
            "single_delivery": 99,  # 99件以下は1回配信
            "dual_delivery": 199,  # 100-199件は2回配信
            "triple_delivery": float("inf"),  # 200件以上は3回配信
        }

        # 状態ファイルのディレクトリ作成
        os.makedirs(os.path.dirname(self.state_file_path), exist_ok=True)

        logger.info("EmailScheduler initialized")
        logger.info(f"State file: {self.state_file_path}")
        logger.info(f"Thresholds: {self.thresholds}")

    def get_current_jst_time(self) -> datetime:
        """現在の日本時間を取得"""
        return datetime.now(JST)

    def determine_delivery_schedule(self, release_count: int) -> List[DeliverySchedule]:
        """
        リリース数に基づいて配信スケジュールを決定

        Args:
            release_count: リリース件数

        Returns:
            配信スケジュールのリスト
        """
        if release_count <= self.thresholds["single_delivery"]:
            # 99件以下: 朝8時のみ
            schedules = [self.DEFAULT_SCHEDULES[0]]
            logger.info(f"Single delivery scheduled: {release_count} releases")

        elif release_count <= self.thresholds["dual_delivery"]:
            # 100-199件: 朝8時、夜20時
            schedules = [self.DEFAULT_SCHEDULES[0], self.DEFAULT_SCHEDULES[2]]
            logger.info(f"Dual delivery scheduled: {release_count} releases")

        else:
            # 200件以上: 朝8時、昼12時、夜20時
            schedules = self.DEFAULT_SCHEDULES.copy()
            logger.info(f"Triple delivery scheduled: {release_count} releases")

        return schedules

    def split_releases_into_batches(
        self, releases: List[Dict[str, Any]], schedules: List[DeliverySchedule]
    ) -> List[EmailBatch]:
        """
        リリース情報を配信バッチに分割

        Args:
            releases: リリース情報リスト
            schedules: 配信スケジュールリスト

        Returns:
            メール配信バッチのリスト
        """
        total_releases = len(releases)
        total_batches = len(schedules)

        if total_batches == 0:
            return []

        batch_size = total_releases // total_batches
        remainder = total_releases % total_batches

        batches = []
        start_idx = 0

        for i, schedule in enumerate(schedules):
            # 余りを最初のバッチから順番に配分
            current_batch_size = batch_size + (1 if i < remainder else 0)
            end_idx = start_idx + current_batch_size

            batch_releases = releases[start_idx:end_idx]

            batch = EmailBatch(
                schedule=schedule,
                releases=batch_releases,
                batch_id=f"{datetime.now(JST).strftime('%Y%m%d')}_{i+1}",
                total_batches=total_batches,
                current_batch=i + 1,
            )

            batches.append(batch)
            start_idx = end_idx

            logger.info(
                f"Batch {i+1}/{total_batches}: {len(batch_releases)} releases "
                f"scheduled for {schedule.to_time_str()} ({schedule.description})"
            )

        return batches

    def should_send_now(self, schedule: DeliverySchedule, tolerance_minutes: int = 5) -> bool:
        """
        現在時刻が配信時刻かチェック

        Args:
            schedule: 配信スケジュール
            tolerance_minutes: 許容誤差（分）

        Returns:
            配信すべき時刻の場合True
        """
        now = self.get_current_jst_time()
        target_time = now.replace(
            hour=schedule.hour, minute=schedule.minute, second=0, microsecond=0
        )

        # 許容誤差内かチェック
        time_diff = abs((now - target_time).total_seconds())
        return time_diff <= tolerance_minutes * 60

    def get_next_delivery_time(self, schedule: DeliverySchedule) -> datetime:
        """
        次回配信時刻を取得

        Args:
            schedule: 配信スケジュール

        Returns:
            次回配信時刻（日本時間）
        """
        now = self.get_current_jst_time()
        next_delivery = now.replace(
            hour=schedule.hour, minute=schedule.minute, second=0, microsecond=0
        )

        # 既に配信時刻を過ぎている場合は翌日
        if next_delivery <= now:
            next_delivery += timedelta(days=1)

        return next_delivery

    def save_state(self, batches: List[EmailBatch], sent_batch_ids: List[str] = None):
        """
        配信状態をファイルに保存

        Args:
            batches: 配信バッチリスト
            sent_batch_ids: 送信済みバッチIDリスト
        """
        state = {
            "timestamp": datetime.now(JST).isoformat(),
            "batches": [],
            "sent_batch_ids": sent_batch_ids or [],
        }

        for batch in batches:
            batch_data = {
                "batch_id": batch.batch_id,
                "schedule_hour": batch.schedule.hour,
                "schedule_minute": batch.schedule.minute,
                "release_count": len(batch.releases),
                "total_batches": batch.total_batches,
                "current_batch": batch.current_batch,
            }
            state["batches"].append(batch_data)

        try:
            with open(self.state_file_path, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            logger.info(f"State saved to {self.state_file_path}")
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def load_state(self) -> Dict[str, Any]:
        """
        配信状態をファイルから読み込み

        Returns:
            配信状態辞書
        """
        try:
            if os.path.exists(self.state_file_path):
                with open(self.state_file_path, "r", encoding="utf-8") as f:
                    state = json.load(f)
                logger.info(f"State loaded from {self.state_file_path}")
                return state
        except Exception as e:
            logger.error(f"Failed to load state: {e}")

        return {"batches": [], "sent_batch_ids": []}

    def plan_delivery(self, releases: List[Dict[str, Any]]) -> List[EmailBatch]:
        """
        配信計画を作成

        Args:
            releases: 配信対象のリリース情報

        Returns:
            配信バッチリスト
        """
        if not releases:
            logger.info("No releases to deliver")
            return []

        # 配信スケジュール決定
        schedules = self.determine_delivery_schedule(len(releases))

        # バッチ分割
        batches = self.split_releases_into_batches(releases, schedules)

        # 状態保存
        self.save_state(batches)

        return batches

    def get_pending_batches(self) -> List[EmailBatch]:
        """
        送信待ちのバッチを取得

        Returns:
            送信待ちバッチリスト
        """
        state = self.load_state()
        sent_batch_ids = set(state.get("sent_batch_ids", []))

        pending_batches = []

        for batch_data in state.get("batches", []):
            batch_id = batch_data["batch_id"]

            if batch_id not in sent_batch_ids:
                # バッチデータから EmailBatch オブジェクトを再構築
                # 実際のリリースデータは別途取得が必要
                schedule = DeliverySchedule(
                    hour=batch_data["schedule_hour"],
                    minute=batch_data["schedule_minute"],
                )

                # プレースホルダーバッチ（実際の使用時はDBから再取得）
                batch = EmailBatch(
                    schedule=schedule,
                    releases=[],  # 実際のデータは別途設定
                    batch_id=batch_id,
                    total_batches=batch_data["total_batches"],
                    current_batch=batch_data["current_batch"],
                )
                pending_batches.append(batch)

        return pending_batches

    def mark_batch_sent(self, batch_id: str):
        """
        バッチを送信済みとしてマーク

        Args:
            batch_id: バッチID
        """
        state = self.load_state()
        sent_batch_ids = state.get("sent_batch_ids", [])

        if batch_id not in sent_batch_ids:
            sent_batch_ids.append(batch_id)
            state["sent_batch_ids"] = sent_batch_ids

            # 状態保存
            try:
                with open(self.state_file_path, "w", encoding="utf-8") as f:
                    json.dump(state, f, ensure_ascii=False, indent=2)
                logger.info(f"Batch {batch_id} marked as sent")
            except Exception as e:
                logger.error(f"Failed to save state after marking batch sent: {e}")

    def cleanup_old_state(self, days: int = 7):
        """
        古い配信状態をクリーンアップ

        Args:
            days: 保持日数
        """
        try:
            state = self.load_state()
            timestamp_str = state.get("timestamp")

            if timestamp_str:
                state_timestamp = datetime.fromisoformat(timestamp_str)
                cutoff_time = datetime.now(JST) - timedelta(days=days)

                if state_timestamp < cutoff_time:
                    logger.info(f"Cleaning up old state from {timestamp_str}")
                    # 空の状態で上書き
                    self.save_state([], [])

        except Exception as e:
            logger.error(f"Failed to cleanup old state: {e}")

    def get_delivery_stats(self) -> Dict[str, Any]:
        """
        配信統計を取得

        Returns:
            配信統計辞書
        """
        state = self.load_state()
        total_batches = len(state.get("batches", []))
        sent_batches = len(state.get("sent_batch_ids", []))
        pending_batches = total_batches - sent_batches

        stats = {
            "total_batches": total_batches,
            "sent_batches": sent_batches,
            "pending_batches": pending_batches,
            "completion_rate": ((sent_batches / total_batches * 100) if total_batches > 0 else 0),
            "last_update": state.get("timestamp", "N/A"),
        }

        return stats
