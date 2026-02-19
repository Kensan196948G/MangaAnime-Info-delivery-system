"""
Redis Cache Module with Memory Fallback

Redis接続が利用できない場合は自動的にメモリキャッシュにフォールバックします。
デコレータパターンで簡単にキャッシュを適用できます。

Features:
- Redis接続管理
- メモリキャッシュフォールバック
- デコレータパターン
- TTL設定（1時間〜24時間）
- キャッシュ統計
- 非同期対応
"""

import asyncio
import functools
import hashlib
import json
import logging
import pickle

logger = logging.getLogger(__name__)
import time
from collections import OrderedDict
from typing import Any, Callable, Dict, Optional

try:
    import redis.asyncio as aioredis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("redis package not installed. Using memory cache fallback.")


class MemoryCache:
    """
    メモリベースのLRUキャッシュ（Redis未接続時のフォールバック）
    """

    def __init__(self, max_size: int = 1000):
        """
        初期化

        Args:
            max_size: 最大キャッシュサイズ
        """
        self.cache: OrderedDict = OrderedDict()
        self.max_size = max_size
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        """キャッシュから取得"""
        if key not in self.cache:
            self.misses += 1
            return None

        value, expire_time = self.cache[key]

        # TTL チェック
        if expire_time and time.time() > expire_time:
            del self.cache[key]
            self.misses += 1
            return None

        # LRU: 最近使用したものを末尾に移動
        self.cache.move_to_end(key)
        self.hits += 1
        return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """キャッシュに設定"""
        expire_time = time.time() + ttl if ttl else None

        if key in self.cache:
            self.cache.move_to_end(key)

        self.cache[key] = (value, expire_time)

        # 最大サイズを超えたら最も古いものを削除
        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)

    def delete(self, key: str):
        """キャッシュから削除"""
        if key in self.cache:
            del self.cache[key]

    def clear(self):
        """全キャッシュクリア"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0

    def get_stats(self) -> Dict[str, Any]:
        """キャッシュ統計"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0

        return {
            "type": "memory",
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.2f}%",
        }


class CacheManager:
    """
    統合キャッシュマネージャー（Redis + メモリフォールバック）
    """

    # TTL定義
    TTL_1_HOUR = 3600
    TTL_6_HOURS = 21600
    TTL_12_HOURS = 43200
    TTL_24_HOURS = 86400

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        memory_fallback: bool = True,
        memory_max_size: int = 1000,
    ):
        """
        初期化

        Args:
            redis_url: Redis接続URL
            memory_fallback: メモリキャッシュフォールバック有効化
            memory_max_size: メモリキャッシュ最大サイズ
        """
        self.redis_url = redis_url
        self.redis_client: Optional[aioredis.Redis] = None
        self.use_redis = False

        # メモリキャッシュ（フォールバック）
        self.memory_cache = MemoryCache(max_size=memory_max_size) if memory_fallback else None

    async def connect(self):
        """Redis接続"""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available. Using memory cache only.")
            return

        try:
            self.redis_client = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=False,  # バイナリデータ対応
                socket_connect_timeout=5,
            )

            # 接続テスト
            await self.redis_client.ping()
            self.use_redis = True
            logger.info("Redis connection established successfully")

        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Using memory cache fallback.")
            self.redis_client = None
            self.use_redis = False

    async def disconnect(self):
        """Redis切断"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")

    async def __aenter__(self):
        """非同期コンテキストマネージャー（入場）"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャー（退場）"""
        await self.disconnect()

    def _make_key(self, prefix: str, *args, **kwargs) -> str:
        """
        キャッシュキー生成

        Args:
            prefix: キープレフィックス
            *args: 位置引数
            **kwargs: キーワード引数

        Returns:
            ハッシュ化されたキー
        """
        key_parts = [prefix]

        if args:
            key_parts.append(str(args))

        if kwargs:
            # 辞書を決定的な順序でソート
            sorted_kwargs = json.dumps(kwargs, sort_keys=True)
            key_parts.append(sorted_kwargs)

        key_string = ":".join(key_parts)

        # SHA256でハッシュ化（長いキーを避ける）
        key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:16]
        return f"{prefix}:{key_hash}"

    async def get(self, key: str) -> Optional[Any]:
        """
        キャッシュから取得

        Args:
            key: キャッシュキー

        Returns:
            キャッシュされた値、または None
        """
        # Redis優先
        if self.use_redis and self.redis_client:
            try:
                value = await self.redis_client.get(key)
                if value:
                    return pickle.loads(value)
            except Exception as e:
                logger.warning(f"Redis get failed: {e}. Trying memory cache...")

        # メモリキャッシュフォールバック
        if self.memory_cache:
            return self.memory_cache.get(key)

        return None

    async def set(self, key: str, value: Any, ttl: int = TTL_1_HOUR):
        """
        キャッシュに設定

        Args:
            key: キャッシュキー
            value: 保存する値
            ttl: 有効期限（秒）
        """
        serialized_value = pickle.dumps(value)

        # Redis優先
        if self.use_redis and self.redis_client:
            try:
                await self.redis_client.setex(key, ttl, serialized_value)
                return
            except Exception as e:
                logger.warning(f"Redis set failed: {e}. Falling back to memory cache...")

        # メモリキャッシュフォールバック
        if self.memory_cache:
            self.memory_cache.set(key, value, ttl)

    async def delete(self, key: str):
        """
        キャッシュから削除

        Args:
            key: キャッシュキー
        """
        # Redis
        if self.use_redis and self.redis_client:
            try:
                await self.redis_client.delete(key)
            except Exception as e:
                logger.warning(f"Redis delete failed: {e}")

        # メモリキャッシュ
        if self.memory_cache:
            self.memory_cache.delete(key)

    async def clear(self, pattern: Optional[str] = None):
        """
        キャッシュクリア

        Args:
            pattern: パターン指定（例: "anime:*"）
        """
        # Redis
        if self.use_redis and self.redis_client:
            try:
                if pattern:
                    keys = await self.redis_client.keys(pattern)
                    if keys:
                        await self.redis_client.delete(*keys)
                else:
                    await self.redis_client.flushdb()
            except Exception as e:
                logger.warning(f"Redis clear failed: {e}")

        # メモリキャッシュ
        if self.memory_cache:
            self.memory_cache.clear()

    async def get_stats(self) -> Dict[str, Any]:
        """キャッシュ統計取得"""
        stats = {
            "redis_enabled": self.use_redis,
        }

        # Redis統計
        if self.use_redis and self.redis_client:
            try:
                info = await self.redis_client.info("stats")
                stats["redis"] = {
                    "keyspace_hits": info.get("keyspace_hits", 0),
                    "keyspace_misses": info.get("keyspace_misses", 0),
                }
            except Exception as e:
                logger.warning(f"Failed to get Redis stats: {e}")

        # メモリキャッシュ統計
        if self.memory_cache:
            stats["memory"] = self.memory_cache.get_stats()

        return stats


# グローバルキャッシュインスタンス
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """グローバルキャッシュマネージャー取得"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def cached(prefix: str, ttl: int = CacheManager.TTL_1_HOUR, key_builder: Optional[Callable] = None):
    """
    キャッシュデコレータ

    Args:
        prefix: キャッシュキープレフィックス
        ttl: 有効期限（秒）
        key_builder: カスタムキー生成関数

    Usage:
        @cached("anime_info", ttl=CacheManager.TTL_6_HOURS)
        async def get_anime_info(anime_id: int):
            return await fetch_from_api(anime_id)
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache_manager()

            # キャッシュキー生成
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                cache_key = cache._make_key(prefix, *args, **kwargs)

            # キャッシュチェック
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache HIT: {cache_key}")
                return cached_value

            # キャッシュミス: 関数実行
            logger.debug(f"Cache MISS: {cache_key}")
            result = await func(*args, **kwargs)

            # キャッシュに保存
            if result is not None:
                await cache.set(cache_key, result, ttl)

            return result

        return wrapper

    return decorator


# 使用例
async def example_usage():
    """使用例"""
    # 1. 明示的なキャッシュ操作
    async with CacheManager() as cache:
        # 設定
        await cache.set("anime:123", {"title": "Attack on Titan"}, ttl=CacheManager.TTL_6_HOURS)

        # 取得
        data = await cache.get("anime:123")
        print(f"Cached data: {data}")

        # 削除
        await cache.delete("anime:123")

        # 統計
        stats = await cache.get_stats()
        print(f"Cache stats: {stats}")

    # 2. デコレータ使用
    @cached("anime_search", ttl=CacheManager.TTL_12_HOURS)
    async def search_anime(query: str, limit: int = 10):
        """アニメ検索（キャッシュ付き）"""
        await asyncio.sleep(1)  # API呼び出しをシミュレート
        return [{"title": f"Result for {query}", "limit": limit}]

    # 初回: キャッシュミス
    result1 = await search_anime("naruto", limit=20)
    print(f"First call: {result1}")

    # 2回目: キャッシュヒット
    result2 = await search_anime("naruto", limit=20)
    print(f"Second call (cached): {result2}")


if __name__ == "__main__":
    # テスト実行
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(example_usage())
