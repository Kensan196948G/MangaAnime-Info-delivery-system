#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
エラーハンドリングモジュール

API呼び出しやネットワーク処理のエラー処理とリトライロジックを提供。

使用例:
    from modules.error_handler import with_retry, RetryConfig

    @with_retry(RetryConfig(max_retries=3))
    def fetch_data():
        # API呼び出し
        pass
"""

import time
import logging
from functools import wraps
from typing import Callable, Optional, Tuple, Type
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RetryConfig:
    """
    リトライ設定

    Attributes:
        max_retries: 最大リトライ回数
        backoff_factor: バックオフ係数（指数バックオフ）
        retry_on: リトライ対象の例外タプル
        retry_on_status: リトライ対象のHTTPステータスコード
        max_backoff: 最大待機時間（秒）
    """
    max_retries: int = 3
    backoff_factor: float = 2.0
    retry_on: Tuple[Type[Exception], ...] = (Exception,)
    retry_on_status: Tuple[int, ...] = (500, 502, 503, 504, 429)
    max_backoff: float = 60.0  # 最大1分


def calculate_backoff(attempt: int, backoff_factor: float, max_backoff: float) -> float:
    """
    エクスポネンシャルバックオフの計算

    Args:
        attempt: 現在の試行回数（0から始まる）
        backoff_factor: バックオフ係数
        max_backoff: 最大待機時間

    Returns:
        待機時間（秒）
    """
    wait_time = backoff_factor ** attempt
    return min(wait_time, max_backoff)


def with_retry(config: Optional[RetryConfig] = None):
    """
    リトライデコレータ

    関数実行時のエラーを自動的にリトライします。
    エクスポネンシャルバックオフによる待機時間の増加により、
    一時的なネットワークエラーやサーバー過負荷に対応します。

    Args:
        config: リトライ設定（省略時はデフォルト設定）

    Returns:
        デコレータ関数

    使用例:
        @with_retry(RetryConfig(max_retries=5, backoff_factor=1.5))
        def api_call():
            response = requests.get("https://api.example.com")
            return response.json()
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(config.max_retries):
                try:
                    result = func(*args, **kwargs)

                    # 成功した場合、リトライがあったことをログに記録
                    if attempt > 0:
                        logger.info(
                            f"{func.__name__} succeeded after {attempt + 1} attempts"
                        )

                    return result

                except config.retry_on as e:
                    last_exception = e

                    # HTTPステータスコードをチェック（requestsライブラリの場合）
                    if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                        status_code = e.response.status_code

                        # リトライ対象外のステータスコードの場合は即座に失敗
                        if status_code not in config.retry_on_status and status_code >= 400:
                            logger.error(
                                f"{func.__name__} failed with non-retryable status "
                                f"{status_code}: {e}"
                            )
                            raise

                    # 最後の試行の場合はリトライしない
                    if attempt >= config.max_retries - 1:
                        break

                    # バックオフ時間の計算
                    wait_time = calculate_backoff(
                        attempt,
                        config.backoff_factor,
                        config.max_backoff
                    )

                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt + 1}/{config.max_retries}), "
                        f"retrying in {wait_time:.2f}s: {type(e).__name__}: {e}"
                    )

                    time.sleep(wait_time)

            # 全てのリトライが失敗した場合
            logger.error(
                f"{func.__name__} failed after {config.max_retries} retries"
            )
            raise last_exception

        return wrapper

    return decorator


class CircuitBreaker:
    """
    サーキットブレーカーパターンの実装

    連続したエラーが発生した場合、一定期間APIへのアクセスを停止し、
    システムの負荷を軽減します。

    状態:
        - CLOSED: 正常動作（リクエストを通す）
        - OPEN: 異常検知（リクエストをブロック）
        - HALF_OPEN: 回復試行（1つのリクエストのみ通す）

    Attributes:
        failure_threshold: OPENに移行する連続失敗回数
        timeout: OPEN状態の継続時間（秒）
        failure_count: 現在の連続失敗回数
        state: 現在の状態
        last_failure_time: 最後の失敗時刻
    """

    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: float = 60.0,
        name: Optional[str] = None
    ):
        """
        Args:
            failure_threshold: OPENに移行する連続失敗回数
            timeout: OPEN状態の継続時間（秒）
            name: サーキットブレーカーの識別名
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.name = name or "CircuitBreaker"
        self.failure_count = 0
        self.state = self.CLOSED
        self.last_failure_time = None

        logger.info(
            f"{self.name} initialized: threshold={failure_threshold}, "
            f"timeout={timeout}s"
        )

    def __call__(self, func: Callable) -> Callable:
        """
        デコレータとして使用

        Args:
            func: サーキットブレーカーを適用する関数

        Returns:
            ラップされた関数
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            # OPEN状態のチェック
            if self.state == self.OPEN:
                if time.time() - self.last_failure_time >= self.timeout:
                    logger.info(f"{self.name}: Moving to HALF_OPEN state")
                    self.state = self.HALF_OPEN
                else:
                    raise Exception(
                        f"{self.name} is OPEN. Circuit breaker triggered."
                    )

            try:
                result = func(*args, **kwargs)

                # 成功した場合
                if self.state == self.HALF_OPEN:
                    logger.info(f"{self.name}: Recovering to CLOSED state")
                    self.state = self.CLOSED
                    self.failure_count = 0

                return result

            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()

                logger.warning(
                    f"{self.name}: Failure {self.failure_count}/{self.failure_threshold}"
                )

                # 閾値を超えた場合、OPEN状態に移行
                if self.failure_count >= self.failure_threshold:
                    logger.error(f"{self.name}: Moving to OPEN state")
                    self.state = self.OPEN

                raise

        return wrapper

    def reset(self):
        """サーキットブレーカーをリセット"""
        self.failure_count = 0
        self.state = self.CLOSED
        self.last_failure_time = None
        logger.info(f"{self.name}: Reset to CLOSED state")


# 各API用のサーキットブレーカー
anilist_breaker = CircuitBreaker(
    failure_threshold=5,
    timeout=60,
    name="AniListBreaker"
)

gmail_breaker = CircuitBreaker(
    failure_threshold=3,
    timeout=120,
    name="GmailBreaker"
)

calendar_breaker = CircuitBreaker(
    failure_threshold=3,
    timeout=120,
    name="CalendarBreaker"
)


if __name__ == "__main__":
    # テスト実行
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # リトライのテスト
    attempt_count = 0

    @with_retry(RetryConfig(max_retries=3, backoff_factor=1.5))
    def test_retry_function():
        nonlocal attempt_count
        attempt_count += 1
        print(f"Attempt {attempt_count}")

        if attempt_count < 3:
            raise Exception("Simulated error")

        return "Success!"

    print("Testing retry decorator...")
    try:
        result = test_retry_function()
        print(f"Result: {result}")
    except Exception as e:
        print(f"Failed: {e}")

    # サーキットブレーカーのテスト
    print("\n" + "="*50)
    print("Testing circuit breaker...")

    test_breaker = CircuitBreaker(failure_threshold=3, timeout=5, name="Test")

    @test_breaker
    def test_breaker_function(should_fail: bool):
        if should_fail:
            raise Exception("Simulated error")
        return "Success!"

    # 失敗を繰り返してOPEN状態にする
    for i in range(5):
        try:
            test_breaker_function(should_fail=True)
        except Exception as e:
            print(f"Call {i+1}: {e}")

    # OPEN状態での呼び出し
    print("\nCircuit breaker should be OPEN now:")
    try:
        test_breaker_function(should_fail=False)
    except Exception as e:
        print(f"Blocked: {e}")

    # タイムアウト後の回復
    print("\nWaiting for timeout...")
    time.sleep(6)

    try:
        result = test_breaker_function(should_fail=False)
        print(f"Recovered: {result}")
    except Exception as e:
        print(f"Still failing: {e}")
