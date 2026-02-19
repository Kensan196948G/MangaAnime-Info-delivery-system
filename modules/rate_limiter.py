#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
レート制限モジュール

各種APIのレート制限を管理するモジュール。
スレッドセーフな実装により、並列実行環境でも正確な制限を実現。

使用例:
    from modules.rate_limiter import RateLimiter

    # AniList API用（90リクエスト/分）
    anilist_limiter = RateLimiter(calls=90, period=60)

    @anilist_limiter
    def fetch_anilist_data():
        # API呼び出し
        pass
"""

import logging
import time
from collections import deque

logger = logging.getLogger(__name__)
from functools import wraps
from threading import Lock
from typing import Callable, Optional


class RateLimiter:
    """
    スレッドセーフなレート制限クラス

    指定された期間内の呼び出し回数を制限します。
    制限を超える場合、自動的に待機します。

    Attributes:
        calls (int): 期間内の最大呼び出し回数
        period (int): 期間（秒）
        timestamps (deque): 呼び出しタイムスタンプの履歴
        lock (Lock): スレッドセーフ用のロック
    """

    def __init__(self, calls: int, period: int, name: Optional[str] = None):
        """
        Args:
            calls: 期間内の最大呼び出し回数
            period: 期間（秒）
            name: レート制限の識別名（ログ出力用）
        """
        self.calls = calls
        self.period = period
        self.name = name or "RateLimiter"
        self.timestamps = deque()
        self.lock = Lock()

        logger.info(f"{self.name} initialized: {calls} calls per {period} seconds")

    def __call__(self, func: Callable) -> Callable:
        """
        デコレータとして使用するための__call__メソッド

        Args:
            func: レート制限を適用する関数

        Returns:
            ラップされた関数
        """

        @wraps(func)
        def wrapper(*args, **kwargs):
            with self.lock:
                now = time.time()

                # 期間外のタイムスタンプを削除
                while self.timestamps and now - self.timestamps[0] >= self.period:
                    self.timestamps.popleft()

                # レート制限チェック
                if len(self.timestamps) >= self.calls:
                    sleep_time = self.period - (now - self.timestamps[0]) + 0.1
                    logger.warning(
                        f"{self.name}: Rate limit reached. "
                        f"Sleeping for {sleep_time:.2f} seconds"
                    )
                    time.sleep(sleep_time)
                    now = time.time()

                    # 再度クリーンアップ
                    while self.timestamps and now - self.timestamps[0] >= self.period:
                        self.timestamps.popleft()

                self.timestamps.append(now)
                logger.debug(f"{self.name}: {len(self.timestamps)}/{self.calls} calls used")

            return func(*args, **kwargs)

        return wrapper

    def get_remaining_calls(self) -> int:
        """
        現在の期間内で残りの呼び出し可能回数を返す

        Returns:
            残りの呼び出し可能回数
        """
        with self.lock:
            now = time.time()

            # 期間外のタイムスタンプを削除
            while self.timestamps and now - self.timestamps[0] >= self.period:
                self.timestamps.popleft()

            return max(0, self.calls - len(self.timestamps))

    def get_time_until_next_call(self) -> float:
        """
        次の呼び出しが可能になるまでの時間（秒）を返す

        Returns:
            待機時間（秒）。即座に呼び出し可能な場合は0.0
        """
        with self.lock:
            now = time.time()

            # 期間外のタイムスタンプを削除
            while self.timestamps and now - self.timestamps[0] >= self.period:
                self.timestamps.popleft()

            if len(self.timestamps) < self.calls:
                return 0.0

            return self.period - (now - self.timestamps[0])

    def reset(self):
        """レート制限の履歴をリセット"""
        with self.lock:
            self.timestamps.clear()
            logger.info(f"{self.name}: Rate limiter reset")


# 各API用のレート制限インスタンス
# AniList GraphQL API: 90リクエスト/分
anilist_limiter = RateLimiter(calls=90, period=60, name="AniList")

# Gmail API: 100通/秒（実際には控えめに50通/秒に設定）
gmail_limiter = RateLimiter(calls=50, period=1, name="Gmail")

# Google Calendar API: 5リクエスト/秒（公式制限は10/秒）
calendar_limiter = RateLimiter(calls=5, period=1, name="GoogleCalendar")

# しょぼいカレンダーAPI: 1リクエスト/秒（非公式のため控えめ）
syoboi_limiter = RateLimiter(calls=1, period=1, name="Syoboi")

# RSS フィード: 10リクエスト/秒（各ソース個別に管理）
rss_limiter = RateLimiter(calls=10, period=1, name="RSS")


if __name__ == "__main__":
    # テスト実行
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # テスト用のレート制限（5呼び出し/秒）
    test_limiter = RateLimiter(calls=5, period=1, name="Test")

    @test_limiter
    def test_function(n: int):
        logger.info(f"Call {n} at {time.time():.2f}")
        return n

    logger.info("Testing rate limiter with 10 calls (should take ~2 seconds)...")
    start = time.time()

    for i in range(10):
        test_function(i)

    elapsed = time.time() - start
    logger.info(f"\nCompleted in {elapsed:.2f} seconds")
    logger.info(f"Remaining calls: {test_limiter.get_remaining_calls()}")
    logger.info(f"Time until next call: {test_limiter.get_time_until_next_call():.2f}s")
