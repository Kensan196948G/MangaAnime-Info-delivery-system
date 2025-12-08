"""
Async Utilities Module

非同期処理のベストプラクティスを提供します。

Features:
- 並列API呼び出し
- タイムアウト管理
- リトライ機構（指数バックオフ）
- セマフォによる同時実行数制御
- エラーハンドリング
- プログレストラッキング
"""

import asyncio
import functools
import logging
import time
from typing import Any, Callable, Coroutine, List, Optional, TypeVar, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryStrategy(Enum):
    """リトライ戦略"""
    EXPONENTIAL = "exponential"  # 指数バックオフ
    LINEAR = "linear"  # 線形バックオフ
    CONSTANT = "constant"  # 固定間隔


@dataclass
class RetryConfig:
    """リトライ設定"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    exceptions: tuple = (Exception,)
    on_retry: Optional[Callable[[int, Exception], None]] = None


@dataclass
class TaskResult:
    """タスク実行結果"""
    success: bool
    result: Any = None
    error: Optional[Exception] = None
    duration: float = 0.0
    attempts: int = 1


async def retry_async(
    config: RetryConfig,
    func: Callable[..., Coroutine[Any, Any, T]],
    *args,
    **kwargs
) -> T:
    """
    非同期関数のリトライ実行

    Args:
        config: リトライ設定
        func: 実行する非同期関数
        *args: 関数の位置引数
        **kwargs: 関数のキーワード引数

    Returns:
        関数の実行結果

    Raises:
        最後のエラー（全リトライ失敗時）
    """
    last_exception = None

    for attempt in range(1, config.max_attempts + 1):
        try:
            result = await func(*args, **kwargs)
            if attempt > 1:
                logger.info(f"Success on attempt {attempt}/{config.max_attempts}")
            return result

        except config.exceptions as e:
            last_exception = e
            logger.warning(
                f"Attempt {attempt}/{config.max_attempts} failed: {type(e).__name__}: {e}"
            )

            # コールバック実行
            if config.on_retry:
                config.on_retry(attempt, e)

            # 最後の試行でない場合は待機
            if attempt < config.max_attempts:
                delay = _calculate_delay(attempt, config)
                logger.info(f"Retrying in {delay:.2f} seconds...")
                await asyncio.sleep(delay)

    # 全リトライ失敗
    logger.error(f"All {config.max_attempts} attempts failed")
    raise last_exception


def _calculate_delay(attempt: int, config: RetryConfig) -> float:
    """
    バックオフ遅延時間を計算

    Args:
        attempt: 試行回数
        config: リトライ設定

    Returns:
        待機時間（秒）
    """
    if config.strategy == RetryStrategy.EXPONENTIAL:
        delay = config.base_delay * (2 ** (attempt - 1))
    elif config.strategy == RetryStrategy.LINEAR:
        delay = config.base_delay * attempt
    else:  # CONSTANT
        delay = config.base_delay

    return min(delay, config.max_delay)


def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
    exceptions: tuple = (Exception,)
):
    """
    リトライデコレータ

    Usage:
        @with_retry(max_attempts=5, base_delay=2.0)
        async def fetch_data():
            return await api_call()
    """
    def decorator(func: Callable[..., Coroutine[Any, Any, T]]):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            config = RetryConfig(
                max_attempts=max_attempts,
                base_delay=base_delay,
                strategy=strategy,
                exceptions=exceptions
            )
            return await retry_async(config, func, *args, **kwargs)
        return wrapper
    return decorator


async def with_timeout(
    coro: Coroutine[Any, Any, T],
    timeout: float,
    default: Optional[T] = None
) -> T:
    """
    タイムアウト付き実行

    Args:
        coro: コルーチン
        timeout: タイムアウト時間（秒）
        default: タイムアウト時のデフォルト値

    Returns:
        実行結果またはデフォルト値

    Raises:
        asyncio.TimeoutError: タイムアウト（defaultが未指定の場合）
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        if default is not None:
            logger.warning(f"Operation timed out after {timeout}s, returning default value")
            return default
        raise


async def run_parallel(
    tasks: List[Coroutine[Any, Any, T]],
    max_concurrent: Optional[int] = None,
    timeout: Optional[float] = None,
    return_exceptions: bool = True
) -> List[Union[T, Exception]]:
    """
    並列タスク実行（同時実行数制限付き）

    Args:
        tasks: 実行するコルーチンリスト
        max_concurrent: 最大同時実行数（Noneの場合は無制限）
        timeout: 全体のタイムアウト（秒）
        return_exceptions: 例外を結果に含めるか

    Returns:
        実行結果リスト
    """
    if not tasks:
        return []

    if max_concurrent:
        semaphore = asyncio.Semaphore(max_concurrent)

        async def bounded_task(coro):
            async with semaphore:
                return await coro

        bounded_tasks = [bounded_task(task) for task in tasks]
    else:
        bounded_tasks = tasks

    # タイムアウト付き実行
    if timeout:
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*bounded_tasks, return_exceptions=return_exceptions),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.error(f"Parallel execution timed out after {timeout}s")
            raise
    else:
        results = await asyncio.gather(*bounded_tasks, return_exceptions=return_exceptions)

    return results


async def run_parallel_with_progress(
    tasks: List[Coroutine[Any, Any, T]],
    max_concurrent: int = 10,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> List[TaskResult]:
    """
    並列タスク実行（プログレス付き）

    Args:
        tasks: 実行するコルーチンリスト
        max_concurrent: 最大同時実行数
        progress_callback: 進捗コールバック(completed, total)

    Returns:
        TaskResultリスト
    """
    if not tasks:
        return []

    total = len(tasks)
    completed = 0
    results = []
    semaphore = asyncio.Semaphore(max_concurrent)

    async def execute_with_tracking(coro: Coroutine) -> TaskResult:
        nonlocal completed

        start_time = time.time()
        attempts = 1

        async with semaphore:
            try:
                result = await coro
                duration = time.time() - start_time

                completed += 1
                if progress_callback:
                    progress_callback(completed, total)

                return TaskResult(
                    success=True,
                    result=result,
                    duration=duration,
                    attempts=attempts
                )

            except Exception as e:
                duration = time.time() - start_time

                completed += 1
                if progress_callback:
                    progress_callback(completed, total)

                return TaskResult(
                    success=False,
                    error=e,
                    duration=duration,
                    attempts=attempts
                )

    # 全タスクを追跡付きで実行
    tracked_tasks = [execute_with_tracking(task) for task in tasks]
    results = await asyncio.gather(*tracked_tasks)

    return results


async def batch_process(
    items: List[Any],
    process_func: Callable[[Any], Coroutine[Any, Any, T]],
    batch_size: int = 10,
    max_concurrent: int = 5,
    delay_between_batches: float = 0.0
) -> List[T]:
    """
    バッチ処理（大量データの段階的処理）

    Args:
        items: 処理対象アイテムリスト
        process_func: 各アイテムに適用する非同期関数
        batch_size: バッチサイズ
        max_concurrent: バッチ内の最大同時実行数
        delay_between_batches: バッチ間の待機時間（秒）

    Returns:
        処理結果リスト
    """
    all_results = []

    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(items) + batch_size - 1) // batch_size

        logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} items)")

        # バッチ内で並列処理
        tasks = [process_func(item) for item in batch]
        batch_results = await run_parallel(tasks, max_concurrent=max_concurrent)

        all_results.extend(batch_results)

        # バッチ間の待機
        if delay_between_batches > 0 and i + batch_size < len(items):
            await asyncio.sleep(delay_between_batches)

    return all_results


class AsyncRateLimiter:
    """
    非同期レート制限

    Usage:
        limiter = AsyncRateLimiter(rate=10, per=1.0)  # 1秒あたり10リクエスト
        async with limiter:
            await api_call()
    """

    def __init__(self, rate: int, per: float = 1.0):
        """
        初期化

        Args:
            rate: 期間内の最大実行回数
            per: 期間（秒）
        """
        self.rate = rate
        self.per = per
        self.allowance = rate
        self.last_check = time.time()
        self.lock = asyncio.Lock()

    async def __aenter__(self):
        """レート制限チェック"""
        async with self.lock:
            current = time.time()
            time_passed = current - self.last_check
            self.last_check = current

            # 許可量を回復
            self.allowance += time_passed * (self.rate / self.per)
            if self.allowance > self.rate:
                self.allowance = self.rate

            # 許可量が不足している場合は待機
            if self.allowance < 1.0:
                sleep_time = (1.0 - self.allowance) * (self.per / self.rate)
                logger.debug(f"Rate limit reached. Sleeping {sleep_time:.2f}s")
                await asyncio.sleep(sleep_time)
                self.allowance = 1.0

            self.allowance -= 1.0

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """終了処理"""
        pass


# 使用例
async def example_usage():
    """使用例"""
    # 1. リトライ付き関数
    @with_retry(max_attempts=5, base_delay=2.0, strategy=RetryStrategy.EXPONENTIAL)
    async def flaky_api_call():
        """失敗する可能性のあるAPI呼び出し"""
        import random
        if random.random() < 0.7:  # 70%の確率で失敗
            raise ConnectionError("API unreachable")
        return {"status": "success"}

    try:
        result = await flaky_api_call()
        print(f"API call succeeded: {result}")
    except Exception as e:
        print(f"API call failed: {e}")

    # 2. 並列処理
    async def fetch_anime(anime_id: int):
        await asyncio.sleep(0.5)  # API呼び出しをシミュレート
        return {"id": anime_id, "title": f"Anime {anime_id}"}

    anime_ids = list(range(1, 21))
    tasks = [fetch_anime(aid) for aid in anime_ids]

    # 最大5並列で実行
    results = await run_parallel(tasks, max_concurrent=5)
    print(f"Fetched {len(results)} anime")

    # 3. バッチ処理
    items = list(range(1, 101))

    async def process_item(item: int):
        await asyncio.sleep(0.1)
        return item * 2

    batch_results = await batch_process(
        items,
        process_item,
        batch_size=20,
        max_concurrent=5,
        delay_between_batches=1.0
    )
    print(f"Processed {len(batch_results)} items")

    # 4. レート制限
    limiter = AsyncRateLimiter(rate=10, per=1.0)

    for i in range(15):
        async with limiter:
            print(f"Request {i + 1}")

    # 5. タイムアウト
    async def slow_operation():
        await asyncio.sleep(5)
        return "completed"

    try:
        result = await with_timeout(slow_operation(), timeout=2.0)
        print(f"Result: {result}")
    except asyncio.TimeoutError:
        print("Operation timed out")


if __name__ == "__main__":
    # テスト実行
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    asyncio.run(example_usage())
