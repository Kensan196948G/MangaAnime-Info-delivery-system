"""
リトライハンドラーモジュール
APIコールやネットワークリクエストのリトライ処理を提供
"""

import logging
import time
from functools import wraps
from typing import Any, Callable

logger = logging.getLogger(__name__)


class RetryException(Exception):
    """リトライ失敗時の例外"""


class RetryHandler:
    """リトライハンドラークラス"""

    def __init__(
        self,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
    ):
        """
        初期化

        Args:
            max_retries: 最大リトライ回数
            backoff_factor: バックオフ係数（指数バックオフ）
            initial_delay: 初期遅延時間（秒）
            max_delay: 最大遅延時間（秒）
        """
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.initial_delay = initial_delay
        self.max_delay = max_delay

    def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """
        リトライ付きで関数を実行

        Args:
            func: 実行する関数
            *args: 関数の位置引数
            **kwargs: 関数のキーワード引数

        Returns:
            関数の実行結果

        Raises:
            RetryException: 最大リトライ回数に達した場合
        """
        last_exception = None
        delay = self.initial_delay

        for attempt in range(self.max_retries + 1):
            try:
                result = func(*args, **kwargs)
                if attempt > 0:
                    logger.info(f"リトライ成功: {attempt}回目の試行で成功")
                return result

            except Exception as e:
                last_exception = e

                if attempt < self.max_retries:
                    logger.warning(
                        f"リトライ {attempt + 1}/{self.max_retries}: "
                        f"{type(e).__name__}: {str(e)} - "
                        f"{delay:.1f}秒後に再試行"
                    )
                    time.sleep(delay)
                    delay = min(delay * self.backoff_factor, self.max_delay)
                else:
                    logger.error(f"最大リトライ回数に達しました: {self.max_retries}回")

        raise RetryException(
            f"最大リトライ回数({self.max_retries})に達しました"
        ) from last_exception


def retry_on_exception(
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    initial_delay: float = 1.0,
    exceptions: tuple = (Exception,),
):
    """
    デコレーター: 指定した例外が発生した場合にリトライ

    Args:
        max_retries: 最大リトライ回数
        backoff_factor: バックオフ係数
        initial_delay: 初期遅延時間
        exceptions: リトライ対象の例外タプル

    Returns:
        デコレートされた関数
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            handler = RetryHandler(
                max_retries=max_retries,
                backoff_factor=backoff_factor,
                initial_delay=initial_delay,
            )

            last_exception = None
            delay = initial_delay

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt < max_retries:
                        logger.warning(
                            f"{func.__name__}() リトライ {attempt + 1}/{max_retries}: "
                            f"{type(e).__name__}: {str(e)} - "
                            f"{delay:.1f}秒後に再試行"
                        )
                        time.sleep(delay)
                        delay = min(delay * backoff_factor, 60.0)
                    else:
                        logger.error(f"{func.__name__}() 最大リトライ回数に達しました")
                        raise

            if last_exception:
                raise last_exception

        return wrapper

    return decorator


class RateLimitedRetryHandler(RetryHandler):
    """レート制限対応のリトライハンドラー"""

    def __init__(
        self,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        initial_delay: float = 1.0,
        rate_limit_delay: float = 60.0,
    ):
        """
        初期化

        Args:
            max_retries: 最大リトライ回数
            backoff_factor: バックオフ係数
            initial_delay: 初期遅延時間
            rate_limit_delay: レート制限時の待機時間
        """
        super().__init__(max_retries, backoff_factor, initial_delay)
        self.rate_limit_delay = rate_limit_delay

    def is_rate_limit_error(self, exception: Exception) -> bool:
        """
        レート制限エラーかどうかを判定

        Args:
            exception: 発生した例外

        Returns:
            レート制限エラーの場合True
        """
        error_msg = str(exception).lower()
        rate_limit_keywords = [
            "rate limit",
            "too many requests",
            "429",
            "quota exceeded",
        ]
        return any(keyword in error_msg for keyword in rate_limit_keywords)

    def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """
        レート制限を考慮したリトライ実行

        Args:
            func: 実行する関数
            *args: 関数の位置引数
            **kwargs: 関数のキーワード引数

        Returns:
            関数の実行結果
        """
        last_exception = None
        delay = self.initial_delay

        for attempt in range(self.max_retries + 1):
            try:
                result = func(*args, **kwargs)
                if attempt > 0:
                    logger.info(f"リトライ成功: {attempt}回目の試行で成功")
                return result

            except Exception as e:
                last_exception = e

                # レート制限エラーの場合は特別な処理
                if self.is_rate_limit_error(e):
                    if attempt < self.max_retries:
                        logger.warning(f"レート制限検出: {self.rate_limit_delay}秒待機")
                        time.sleep(self.rate_limit_delay)
                        continue

                if attempt < self.max_retries:
                    logger.warning(
                        f"リトライ {attempt + 1}/{self.max_retries}: "
                        f"{type(e).__name__}: {str(e)} - "
                        f"{delay:.1f}秒後に再試行"
                    )
                    time.sleep(delay)
                    delay = min(delay * self.backoff_factor, self.max_delay)
                else:
                    logger.error(f"最大リトライ回数に達しました: {self.max_retries}回")

        raise RetryException(
            f"最大リトライ回数({self.max_retries})に達しました"
        ) from last_exception


# 使用例
if __name__ == "__main__":
    # 基本的なリトライ
    handler = RetryHandler(max_retries=3)

    def unstable_function():
        import random

        if random.random() < 0.7:
            raise Exception("一時的なエラー")
        return "成功"

    # result = handler.execute_with_retry(unstable_function)
    # print(f"結果: {result}")

    # デコレーター使用例
    @retry_on_exception(max_retries=3, exceptions=(ValueError, ConnectionError))
    def api_call():
        import random

        if random.random() < 0.5:
            raise ConnectionError("接続エラー")
        return {"status": "ok"}

    # result = api_call()
    # print(f"API結果: {result}")
