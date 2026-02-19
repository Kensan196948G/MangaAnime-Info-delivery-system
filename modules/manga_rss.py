#!/usr/bin/env python3
"""
マンガRSS収集モジュール
各種マンガサイトのRSSフィードから新刊情報を収集
"""

import asyncio
import hashlib
import json
import logging
import re

logger = logging.getLogger(__name__)


class _SimpleCache:
    """シンプルなメモリキャッシュ（モジュールレベルキャッシュ用）"""

    def __init__(self):
        self._store = {}

    def get(self, key):
        return self._store.get(key)

    def set(self, key, value, ttl=None):
        self._store[key] = value

    def delete(self, key):
        self._store.pop(key, None)

    def clear(self):
        self._store.clear()


# モジュールレベルキャッシュ（テストでのパッチ対象）
cache = _SimpleCache()


# モジュールレベルDBオブジェクト（テストでのパッチ対象）
class _NullDB:
    """DBが未初期化の場合のプレースホルダー"""

    def __getattr__(self, name):
        def _noop(*args, **kwargs):
            return None

        return _noop


db = _NullDB()


import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

import aiohttp
import feedparser
import requests

from .models import DataSource, ReleaseType, RSSFeedItem, WorkType


@dataclass
class FeedHealth:
    """RSS フィードの健全性を追跡するクラス"""

    url: str
    success_count: int = 0
    failure_count: int = 0
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    last_response_time: float = 0.0
    average_response_time: float = 0.0
    consecutive_failures: int = 0
    is_healthy: bool = True

    def record_success(self, response_time: float):
        """成功を記録"""
        self.success_count += 1
        self.consecutive_failures = 0
        self.last_success = datetime.now()
        self.last_response_time = response_time

        # 平均応答時間を更新
        if self.average_response_time == 0:
            self.average_response_time = response_time
        else:
            self.average_response_time = (self.average_response_time + response_time) / 2

        self.is_healthy = True

    def record_failure(self):
        """失敗を記録"""
        self.failure_count += 1
        self.consecutive_failures += 1
        self.last_failure = datetime.now()

        # 連続失敗が3回以上で不健全とみなす
        if self.consecutive_failures >= 3:
            self.is_healthy = False

    def get_success_rate(self) -> float:
        """成功率を取得"""
        total = self.success_count + self.failure_count
        if total == 0:
            return 1.0
        return self.success_count / total

    def get_health_score(self) -> float:
        """ヘルススコアを計算 (0.0-1.0)"""
        if not self.is_healthy:
            return 0.0

        success_rate = self.get_success_rate()
        response_penalty = min(self.average_response_time / 10.0, 0.5)  # 10秒で50%ペナルティ
        consecutive_failure_penalty = min(self.consecutive_failures * 0.1, 0.3)

        score = success_rate - response_penalty - consecutive_failure_penalty
        return max(0.0, min(1.0, score))


class EnhancedRSSParser:
    """強化版RSSパーサー"""

    def __init__(self):
        self.title_patterns = [
            r"^(.+?)\s*[第#]?\s*(\d+)\s*[話巻]\s*(.*)$",  # タイトル + 話/巻番号
            r"^(.+?)\s*(\d+)\s*巻?\s*(.*)$",  # タイトル + 数字 + 巻
            r"^(.+?)\s*vol\.?\s*(\d+)\s*(.*)$",  # タイトル + vol + 数字
        ]

        self.date_patterns = [
            r"(\d{4})-(\d{2})-(\d{2})",  # YYYY-MM-DD
            r"(\d{4})/(\d{2})/(\d{2})",  # YYYY/MM/DD
            r"(\d{2})/(\d{2})/(\d{4})",  # MM/DD/YYYY
        ]

    def extract_title(self, raw_title: str) -> str:
        """タイトルを抽出・クリーンアップ"""
        if not raw_title:
            return ""

        # HTMLタグ除去
        clean_title = re.sub(r"<[^>]+>", "", raw_title)

        # 余分な空白除去
        clean_title = re.sub(r"\s+", " ", clean_title).strip()

        # 番号部分を除去してメインタイトルを抽出
        for pattern in self.title_patterns:
            match = re.match(pattern, clean_title, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return clean_title

    def extract_number_and_type(
        self, raw_title: str
    ) -> Tuple[Optional[str], Optional[ReleaseType]]:
        """タイトルから番号とリリースタイプを抽出"""
        if not raw_title:
            return None, None

        # 話数パターン
        episode_patterns = [
            r"第(\d+)話",
            r"#(\d+)",
            r"ep\.?(\d+)",
            r"episode\s*(\d+)",
        ]

        # 巻数パターン
        volume_patterns = [
            r"第(\d+)巻",
            r"(\d+)巻",
            r"vol\.?\s*(\d+)",
            r"volume\s*(\d+)",
        ]

        # 話数チェック
        for pattern in episode_patterns:
            match = re.search(pattern, raw_title, re.IGNORECASE)
            if match:
                return match.group(1), ReleaseType.EPISODE

        # 巻数チェック
        for pattern in volume_patterns:
            match = re.search(pattern, raw_title, re.IGNORECASE)
            if match:
                return match.group(1), ReleaseType.VOLUME

        return None, None

    def extract_date(self, date_str: str) -> Optional[datetime]:
        """日時文字列から datetime オブジェクトを抽出"""
        if not date_str:
            return None

        # 日付パターンマッチング
        for pattern in self.date_patterns:
            match = re.search(pattern, date_str)
            if match:
                try:
                    groups = match.groups()
                    if len(groups) == 3:
                        if len(groups[0]) == 4:  # YYYY-MM-DD or YYYY/MM/DD
                            year, month, day = groups
                        else:  # MM/DD/YYYY
                            month, day, year = groups

                        return datetime(int(year), int(month), int(day))
                except ValueError:
                    continue

        return None


class MangaRSSCollector:
    """マンガRSS収集クラス（並列処理対応版）"""

    def __init__(self, config_manager):
        """
        RSS収集器の初期化

        Args:
            config_manager: 設定管理インスタンス
        """
        self.config = config_manager
        self.logger = logging.getLogger(__name__)

        # RSS設定の取得
        try:
            rss_config = self.config.get_rss_config()
            self.timeout = rss_config.get("timeout_seconds", 20)
            self.user_agent = rss_config.get("user_agent", "MangaAnimeNotifier/1.0")
            self.max_workers = rss_config.get("max_parallel_workers", 5)

            # 有効なRSSフィードリストを取得
            self.enabled_feeds = self.config.get_enabled_rss_feeds()
        except AttributeError:
            # 設定オブジェクトが異なる構造の場合のフォールバック
            self.timeout = 20
            self.user_agent = "MangaAnimeNotifier/1.0"
            self.max_workers = 5
            self.enabled_feeds = self._get_default_feeds()

        # Feed health monitoring
        self.feed_health = {}
        for feed in self.enabled_feeds:
            url = feed.get("url")
            if url:
                self.feed_health[url] = FeedHealth(url=url)

        # Enhanced RSS parser
        self.parser = EnhancedRSSParser()

        self.logger.info(f"有効なRSSフィード: {len(self.enabled_feeds)} 件")
        self.logger.info(f"並列処理ワーカー数: {self.max_workers}")

    def _get_default_feeds(self) -> List[Dict[str, Any]]:
        """デフォルトのRSSフィード設定を返す（修正版 - 動作確認済みURL）"""
        return [
            {
                "name": "Yahoo!ニュース - エンタメ",
                "url": "https://news.yahoo.co.jp/rss/categories/entertainment.xml",
                "category": "news",
                "enabled": True,
                "priority": "medium",
                "timeout": 15,
                "retry_count": 2,
                "retry_delay": 1,
            },
            {
                "name": "NHKニュース - エンタメ",
                "url": "https://www3.nhk.or.jp/rss/news/cat7.xml",
                "category": "news",
                "enabled": True,
                "priority": "medium",
                "timeout": 15,
                "retry_count": 2,
                "retry_delay": 1,
            },
            {
                "name": "マガポケ (Mock)",
                "url": "https://httpbin.org/xml",  # テスト用Mock URL
                "category": "manga",
                "enabled": False,  # デフォルトで無効
                "priority": "low",
                "timeout": 30,
                "retry_count": 3,
                "retry_delay": 2,
                "status": "mock_for_testing",
            },
            {
                "name": "Kindle (Mock)",
                "url": "https://httpbin.org/xml",  # テスト用Mock URL
                "category": "manga",
                "enabled": False,  # デフォルトで無効
                "priority": "low",
                "timeout": 25,
                "retry_count": 3,
                "retry_delay": 2,
                "status": "mock_for_testing",
            },
            {
                "name": "ジャンプBOOKストア",
                "url": "https://jumpbookstore.com/rss/new-release",
                "category": "manga",
                "enabled": True,
                "priority": "high",
            },
            {
                "name": "コミックシーモア",
                "url": "https://www.cmoa.jp/rss/",
                "category": "manga",
                "enabled": True,
                "priority": "medium",
            },
            {
                "name": "まんが王国",
                "url": "https://comic.k-manga.jp/rss",
                "category": "manga",
                "enabled": True,
                "priority": "medium",
            },
        ]

    def collect(self) -> List[Dict[str, Any]]:
        """
        RSSフィードから並列で情報を収集（強化版）

        Returns:
            List[Dict[str, Any]]: 収集した情報のリスト
        """
        self.logger.info("マンガRSS情報収集を開始（並列処理）...")

        manga_feeds = [
            feed
            for feed in self.enabled_feeds
            if (feed.get("category") == "manga" or feed.get("type") == "manga")
            and feed.get("enabled", True)
        ]

        if not manga_feeds:
            self.logger.warning("有効なマンガRSSフィードが見つかりません")
            return []

        # ヘルシーなフィードを優先
        healthy_feeds = [
            feed
            for feed in manga_feeds
            if self.feed_health.get(feed.get("url", ""), FeedHealth(url="")).is_healthy
        ]

        if len(healthy_feeds) < len(manga_feeds):
            self.logger.info(f"健全なフィード: {len(healthy_feeds)}/{len(manga_feeds)}")

        # 非同期処理でより効率的に収集
        try:
            all_items = asyncio.run(self._collect_async(manga_feeds))
        except Exception as e:
            self.logger.error(f"非同期収集でエラー、同期処理にフォールバック: {e}")
            all_items = self._collect_sync(manga_feeds)

        # 重複除去
        duplicate_detector = DuplicateDetector()
        unique_items = duplicate_detector.remove_duplicates(all_items)

        # 統計情報をログ出力
        stats = duplicate_detector.get_statistics()
        self.logger.info(
            f"マンガRSS収集完了: {len(all_items)} 件取得, {len(unique_items)} 件（重複除去後）, "
            f"重複検出統計: {stats}"
        )

        return unique_items

    async def _collect_async(self, manga_feeds: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """非同期並列収集"""
        connector = aiohttp.TCPConnector(
            limit=20,  # 全体での同時接続数制限
            limit_per_host=5,  # ホストごとの同時接続数制限
            ttl_dns_cache=300,  # DNS キャッシュ
            use_dns_cache=True,
            keepalive_timeout=30,
            enable_cleanup_closed=True,
        )

        timeout = aiohttp.ClientTimeout(
            total=60,  # 全体タイムアウト
            connect=10,  # 接続タイムアウト
            sock_read=30,  # 読み取りタイムアウト
        )

        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={"User-Agent": self.user_agent},
        ) as session:
            tasks = []
            for feed in manga_feeds:
                task = self._collect_from_feed_async(session, feed)
                tasks.append(task)

            # 並列実行（一部失敗しても続行）
            results = await asyncio.gather(*tasks, return_exceptions=True)

            all_items = []
            for i, result in enumerate(results):
                feed_name = manga_feeds[i].get("name", "Unknown")
                if isinstance(result, Exception):
                    self.logger.error(f"  {feed_name} で非同期処理エラー: {result}")
                    continue

                if result:
                    self.logger.info(f"  {feed_name}: {len(result)} 件取得")
                    all_items.extend(result)
                else:
                    self.logger.info(f"  {feed_name}: データなし")

            return all_items

    def _collect_sync(self, manga_feeds: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """同期並列収集（フォールバック）"""
        all_items = []

        # 並列処理でRSS収集を実行
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_feed = {
                executor.submit(self._collect_from_feed_safe, feed): feed for feed in manga_feeds
            }

            for future in as_completed(future_to_feed):
                feed = future_to_feed[future]
                feed_name = feed.get("name", "Unknown")

                try:
                    items = future.result(timeout=45)  # 45秒タイムアウト
                    if items:
                        self.logger.info(f"  {feed_name}: {len(items)} 件取得")
                        all_items.extend(items)
                    else:
                        self.logger.info(f"  {feed_name}: データなし")

                except Exception as e:
                    self.logger.error(f"  {feed_name} で並列処理エラー: {e}")
                    continue

        return all_items

    async def _collect_from_feed_async(
        self, session: aiohttp.ClientSession, feed_info: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """非同期フィード収集"""
        feed_name = feed_info.get("name", "Unknown")
        feed_url = feed_info.get("url")

        if not feed_url:
            self.logger.warning(f"フィードURL未設定: {feed_name}")
            return []

        try:
            start_time = time.time()

            # フィード固有設定を取得
            feed_config = self._get_feed_config(feed_name)
            feed_config.get("timeout", self.timeout)
            retry_count = feed_config.get("retry_count", 3)
            retry_delay = feed_config.get("retry_delay", 2)

            for attempt in range(retry_count):
                try:
                    self.logger.debug(
                        f"{feed_name}から非同期収集中... (試行 {attempt + 1}/{retry_count})"
                    )

                    async with session.get(feed_url) as response:
                        response.raise_for_status()

                        content = await response.read()
                        response_time = time.time() - start_time

                        # RSS解析
                        feed_data = feedparser.parse(content)

                        if feed_data.bozo:
                            self.logger.warning(
                                f"{feed_name}RSSフィードの解析に問題があります: {feed_data.bozo_exception}"
                            )

                        # 成功時の処理
                        items = self._process_feed_entries(feed_data, feed_name)

                        # フィードヘルス更新
                        if feed_url in self.feed_health:
                            self.feed_health[feed_url].record_success(response_time)

                        self.logger.debug(
                            f"{feed_name}から{len(items)}件のアイテムを非同期収集 ({response_time:.1f}s)"
                        )
                        return items

                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    self.logger.warning(f"{feed_name} 非同期収集試行 {attempt + 1} 失敗: {e}")
                    if attempt < retry_count - 1:
                        await asyncio.sleep(retry_delay)
                        continue
                    else:
                        raise

            return []

        except Exception as e:
            self.logger.error(f"非同期フィード収集エラー ({feed_name}): {e}")
            # Feed health記録
            if feed_url in self.feed_health:
                self.feed_health[feed_url].record_failure()
            return []

    def _collect_from_feed_safe(self, feed_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        並列処理対応のフィード収集（エラーハンドリング強化版）

        Args:
            feed_info: フィード情報辞書

        Returns:
            List[Dict[str, Any]]: 収集したアイテムリスト
        """
        feed_name = feed_info.get("name", "Unknown")
        feed_url = feed_info.get("url")

        if not feed_url:
            self.logger.warning(f"フィードURL未設定: {feed_name}")
            return []

        try:
            return self._collect_from_feed_enhanced(feed_url, feed_name)
        except Exception as e:
            self.logger.error(f"フィード収集エラー ({feed_name}): {e}")
            # Feed health記録
            if feed_url in self.feed_health:
                self.feed_health[feed_url].record_failure()
            return []

    def _deduplicate_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        アイテムの重複を除去

        Args:
            items: 全アイテムリスト

        Returns:
            重複除去後のアイテムリスト
        """
        seen = set()
        unique_items = []

        for item in items:
            # タイトルとURLの組み合わせで重複判定
            key = (item.get("title", ""), item.get("official_url", ""))

            if key not in seen:
                seen.add(key)
                unique_items.append(item)
            else:
                self.logger.debug(f"重複アイテムをスキップ: {item.get('title')}")

        return unique_items

    def _collect_from_feed_enhanced(self, feed_url: str, feed_name: str) -> List[Dict[str, Any]]:
        """
        強化版フィード収集（健全性チェック、日時正規化機能付き）

        Args:
            feed_url: フィードURL
            feed_name: フィード名

        Returns:
            List[Dict[str, Any]]: 収集したアイテムリスト
        """
        start_time = time.time()

        # フィード固有設定を取得
        feed_config = self._get_feed_config(feed_name)
        timeout = feed_config.get("timeout", self.timeout)
        retry_count = feed_config.get("retry_count", 3)
        retry_delay = feed_config.get("retry_delay", 2)

        for attempt in range(retry_count):
            try:
                self.logger.info(f"{feed_name}から情報収集中... (試行 {attempt + 1}/{retry_count})")

                # HTTPリクエスト設定（強化版）
                headers = {
                    "User-Agent": self.user_agent,
                    "Accept": "application/rss+xml, application/xml, text/xml",
                    "Accept-Encoding": "gzip, deflate",
                    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
                    "Connection": "keep-alive",
                    "Cache-Control": "no-cache",
                }

                # タイムアウト警告
                if timeout > 10:
                    self.logger.info(f"{feed_name}のタイムアウトを{timeout}秒に延長")

                response = requests.get(
                    feed_url,
                    headers=headers,
                    timeout=timeout,
                    allow_redirects=True,
                    verify=True,
                )

                response.raise_for_status()

                # レスポンス時間チェック
                response_time = time.time() - start_time
                if response_time > 5.0:
                    self.logger.warning(
                        f"{feed_name}RSSの応答が遅延しています ({response_time:.1f}s)"
                    )

                # RSS解析
                feed_data = feedparser.parse(response.content)

                if feed_data.bozo:
                    self.logger.warning(
                        f"{feed_name}RSSフィードの解析に問題があります: {feed_data.bozo_exception}"
                    )

                # 成功時の処理
                items = self._process_feed_entries(feed_data, feed_name)

                # フィードヘルス更新
                if feed_url in self.feed_health:
                    self.feed_health[feed_url].record_success(response_time)

                self.logger.info(
                    f"{feed_name}から{len(items)}件のアイテムを収集 ({response_time:.1f}s)"
                )
                return items

            except requests.exceptions.Timeout:
                self.logger.error(
                    f"{feed_name} RSS接続がタイムアウトしました (試行 {attempt + 1}/{retry_count})"
                )
                if attempt < retry_count - 1:
                    self.logger.info(f"{retry_delay}秒後に再試行します...")
                    time.sleep(retry_delay)
                    continue

            except requests.exceptions.ConnectionError:
                self.logger.error(
                    f"{feed_name} RSS接続に失敗しました (試行 {attempt + 1}/{retry_count})"
                )
                if attempt < retry_count - 1:
                    self.logger.info(f"{retry_delay}秒後に再試行します...")
                    time.sleep(retry_delay)
                    continue

            except requests.exceptions.HTTPError as e:
                self.logger.error(f"{feed_name} HTTPエラー: {e} (試行 {attempt + 1}/{retry_count})")
                if attempt < retry_count - 1:
                    time.sleep(retry_delay)
                    continue

            except Exception as e:
                self.logger.error(
                    f"{feed_name}で予期しないエラー: {e} (試行 {attempt + 1}/{retry_count})"
                )
                if attempt < retry_count - 1:
                    time.sleep(retry_delay)
                    continue

        # 全ての試行が失敗した場合
        self.logger.error(f"{feed_name}から情報を取得できませんでした（{retry_count}回試行後）")

        # フィードヘルス更新（失敗）
        if feed_url in self.feed_health:
            self.feed_health[feed_url].record_failure()

        return []

    def _get_feed_config(self, feed_name: str) -> Dict[str, Any]:
        """フィード固有設定を取得"""
        for feed in self.enabled_feeds:
            if feed.get("name") == feed_name:
                return feed
        return {}

    def _process_feed_entries(self, feed_data, feed_name: str) -> List[Dict[str, Any]]:
        """フィードエントリーの処理"""
        items = []

        for entry in feed_data.entries:
            try:
                rss_item = self._parse_feed_entry_enhanced(entry, feed_name)
                if rss_item:
                    # 作品情報を抽出
                    work_info = self._extract_work_info_enhanced(rss_item, feed_name)
                    if work_info:
                        # 統一形式に変換
                        normalized_item = self._normalize_manga_item_enhanced(
                            work_info, rss_item, feed_name
                        )
                        if normalized_item:
                            items.append(normalized_item)

            except Exception as e:
                self.logger.warning(f"エントリー処理エラー ({feed_name}): {e}")
                continue

        return items

    def _is_feed_healthy(self, response, feed_name: str) -> bool:
        """フィードの健全性をチェック"""
        try:
            # HTTPステータスコードをチェック
            if response.status_code != 200:
                return False

            # コンテンツタイプをチェック
            content_type = response.headers.get("content-type", "").lower()
            if not any(ct in content_type for ct in ["xml", "rss", "atom"]):
                self.logger.warning(f"予期しないコンテンツタイプ ({feed_name}): {content_type}")

            # レスポンスサイズをチェック（空でないか）
            if len(response.content) < 100:
                self.logger.warning(
                    f"レスポンスサイズが小さすぎます ({feed_name}): {len(response.content)} bytes"
                )
                return False

            return True

        except Exception as e:
            self.logger.error(f"健全性チェックエラー ({feed_name}): {e}")
            return False

    def _is_feed_healthy(self, response: requests.Response, feed_name: str) -> bool:
        """
        フィードの健全性をチェック

        Args:
            response: HTTPレスポンス
            feed_name: フィード名

        Returns:
            健全性チェック結果
        """
        # Content-Typeチェック
        content_type = response.headers.get("content-type", "").lower()
        valid_types = ["xml", "rss", "atom"]

        if not any(t in content_type for t in valid_types):
            self.logger.debug(f"疑わしいContent-Type ({feed_name}): {content_type}")

        # レスポンスサイズチェック
        content_length = len(response.content)
        if content_length < 100:  # 極端に小さいレスポンス
            self.logger.warning(f"レスポンスが小さすぎます ({feed_name}): {content_length} bytes")
            return False

        if content_length > 10 * 1024 * 1024:  # 10MB以上
            self.logger.warning(f"レスポンスが大きすぎます ({feed_name}): {content_length} bytes")
            return False

        # 基本的なXML構造チェック
        content_str = response.content[:1000].decode("utf-8", errors="ignore")
        if "<rss" not in content_str and "<feed" not in content_str and "<?xml" not in content_str:
            self.logger.warning(f"XMLフォーマットではありません ({feed_name})")
            return False

        return True

    def _collect_from_feed(self, feed_url: str, feed_name: str) -> List[Dict[str, Any]]:
        """
        個別フィードから情報収集（後方互換性のため維持）

        Args:
            feed_url: フィードURL
            feed_name: フィード名

        Returns:
            List[Dict[str, Any]]: 収集したアイテムリスト
        """
        return self._collect_from_feed_enhanced(feed_url, feed_name)

    def _parse_feed_entry_enhanced(self, entry, feed_name: str) -> Optional[RSSFeedItem]:
        """
        強化版フィードエントリー解析

        Args:
            entry: feedparserのエントリー
            feed_name: フィード名

        Returns:
            Optional[RSSFeedItem]: パース結果
        """
        try:
            # 公開日時の解析（複数フォーマット対応）
            published = None

            # published_parsedを優先
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                try:
                    published = datetime(*entry.published_parsed[:6])
                except (ValueError, TypeError):
                    pass

            # updated_parsedも試行
            if not published and hasattr(entry, "updated_parsed") and entry.updated_parsed:
                try:
                    published = datetime(*entry.updated_parsed[:6])
                except (ValueError, TypeError):
                    pass

            # 文字列からの日時解析
            if not published:
                date_str = getattr(entry, "published", None) or getattr(entry, "updated", None)
                if date_str:
                    published = self.parser.extract_date(date_str)

            # タイトルとdescriptionのクリーンアップ
            title = self.parser.extract_title(getattr(entry, "title", ""))
            description = getattr(entry, "description", None) or getattr(entry, "summary", None)

            # HTMLタグ除去
            if description:
                description = re.sub(r"<[^>]+>", "", description)
                description = description.strip()

            return RSSFeedItem(
                title=title,
                link=getattr(entry, "link", None),
                description=description,
                published=published,
                guid=getattr(entry, "guid", None) or getattr(entry, "id", None),
                category=getattr(entry, "category", None),
                author=getattr(entry, "author", None),
            )

        except Exception as e:
            self.logger.debug(f"エントリー解析エラー ({feed_name}): {e}")
            return None

    def _parse_feed_entry(self, entry, feed_name: str) -> Optional[RSSFeedItem]:
        """
        フィードエントリーをRSSFeedItemに変換（後方互換性のため維持）

        Args:
            entry: feedparserのエントリー
            feed_name: フィード名

        Returns:
            Optional[RSSFeedItem]: パース結果
        """
        return self._parse_feed_entry_enhanced(entry, feed_name)

    def _extract_work_info_enhanced(
        self, rss_item: RSSFeedItem, source_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        強化版作品情報抽出

        Args:
            rss_item: RSSアイテム
            source_name: ソース名

        Returns:
            抽出した作品情報
        """
        if not rss_item.title:
            return None

        # Enhanced parserを使用
        title = self.parser.extract_title(rss_item.title)
        number, release_type = self.parser.extract_number_and_type(rss_item.title)

        # デフォルトでvolume
        if not release_type:
            release_type = ReleaseType.VOLUME

        # リリース日の解析
        release_date = None
        if rss_item.published:
            release_date = rss_item.published.date()

        return {
            "title": title,
            "number": number,
            "release_type": release_type,
            "release_date": release_date,
            "source_url": rss_item.link,
            "description": rss_item.description,
            "source_name": source_name,
        }

    def _normalize_manga_item_enhanced(
        self, work_info: Dict[str, Any], rss_item: RSSFeedItem, source_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        強化版マンガ情報正規化

        Args:
            work_info: 抽出した作品情報
            rss_item: 元のRSSアイテム
            source_name: ソース名

        Returns:
            Optional[Dict[str, Any]]: 正規化された情報
        """
        if not work_info.get("title"):
            return None

        try:
            # ソース別の特別処理
            source_mapping = {
                "BookWalker": DataSource.RSS_BOOKWALKER,
                "マガポケ": DataSource.RSS_GENERAL,
                "ジャンプBOOKストア": DataSource.RSS_GENERAL,
                "コミックシーモア": DataSource.RSS_GENERAL,
                "まんが王国": DataSource.RSS_GENERAL,
            }

            data_source = source_mapping.get(source_name, DataSource.RSS_GENERAL)

            # リリース情報の構築
            releases = []

            release_info = {
                "type": (
                    work_info.get("release_type", ReleaseType.VOLUME).value
                    if work_info.get("release_type")
                    else "volume"
                ),
                "number": work_info.get("number"),
                "date": work_info.get("release_date"),
                "url": rss_item.link,
                "description": work_info.get("description"),
                "platform": source_name,
            }

            releases.append(release_info)

            # 統一形式の作品情報
            normalized = {
                "title": work_info["title"],
                "type": WorkType.MANGA.value,
                "source": data_source.value,
                "title_kana": "",  # RSSからは通常取得不可
                "title_en": "",
                "official_url": rss_item.link,
                "description": rss_item.description or "",
                "genres": [],
                "tags": [],
                "image_url": None,
                "releases": releases,
                "metadata": {
                    "source_name": source_name,
                    "collection_timestamp": datetime.now().isoformat(),
                    "guid": rss_item.guid,
                    "author": rss_item.author,
                    "category": rss_item.category,
                },
            }

            return normalized

        except Exception as e:
            self.logger.debug(f"マンガアイテム正規化エラー: {e}")
            return None

    def _normalize_manga_item(
        self, work_info: Dict[str, Any], rss_item: RSSFeedItem, source_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        マンガ情報を統一形式に正規化（後方互換性のため維持）

        Args:
            work_info: 抽出した作品情報
            rss_item: 元のRSSアイテム
            source_name: ソース名

        Returns:
            Optional[Dict[str, Any]]: 正規化された情報
        """
        return self._normalize_manga_item_enhanced(work_info, rss_item, source_name)


class DuplicateDetector:
    """
    重複検出・排除システム - Phase 2 Implementation

    複数のアルゴリズムを使用して重複を検出し、データ品質を向上させます。
    """

    def __init__(self):
        self.seen_hashes: Set[str] = set()
        self.title_variations: Dict[str, Set[str]] = {}

    def remove_duplicates(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        重複アイテムを除去

        Args:
            items: 処理対象アイテムリスト

        Returns:
            重複除去済みアイテムリスト
        """
        unique_items = []

        for item in items:
            item_hash = self._calculate_item_hash(item)

            if item_hash not in self.seen_hashes:
                # さらに詳細な重複チェック
                if not self._is_similar_title_duplicate(item):
                    unique_items.append(item)
                    self.seen_hashes.add(item_hash)
                    self._update_title_variations(item)

        return unique_items

    def _calculate_item_hash(self, item: Dict[str, Any]) -> str:
        """
        アイテムの一意ハッシュを計算

        Args:
            item: アイテムデータ

        Returns:
            SHA256ハッシュ
        """
        # 重要なフィールドのみを使用してハッシュを計算
        key_fields = {
            "title": item.get("title", "").strip().lower(),
            "type": item.get("type", ""),
            "source": item.get("source", ""),
            "url": item.get("official_url", "") or item.get("url", ""),
        }

        # リリース情報がある場合は含める
        if "releases" in item and item["releases"]:
            release = item["releases"][0]  # 最初のリリース情報を使用
            release_date = release.get("date", "")
            # date/datetime オブジェクトを文字列に変換
            if hasattr(release_date, "isoformat"):
                release_date = release_date.isoformat()
            elif hasattr(release_date, "strftime"):
                release_date = release_date.strftime("%Y-%m-%d")
            key_fields.update(
                {
                    "release_type": release.get("type", ""),
                    "release_number": release.get("number", ""),
                    "release_date": str(release_date) if release_date else "",
                }
            )

        hash_string = json.dumps(key_fields, sort_keys=True, default=str)
        return hashlib.sha256(hash_string.encode("utf-8")).hexdigest()

    def _is_similar_title_duplicate(self, item: Dict[str, Any]) -> bool:
        """
        タイトルの類似性による重複チェック

        Args:
            item: チェック対象アイテム

        Returns:
            類似重複の場合True
        """
        title = item.get("title", "").strip().lower()
        if not title:
            return False

        # 正規化されたタイトルで類似度チェック
        normalized_title = self._normalize_title(title)

        for existing_normalized in self.title_variations:
            if self._calculate_title_similarity(normalized_title, existing_normalized) > 0.85:
                return True

        return False

    def _normalize_title(self, title: str) -> str:
        """
        タイトルの正規化

        Args:
            title: 元のタイトル

        Returns:
            正規化されたタイトル
        """
        # 一般的な記号や文字の統一
        normalized = title.lower().strip()

        # 全角・半角の統一
        normalized = normalized.replace("　", " ")  # 全角スペース→半角
        normalized = re.sub(
            r"[！-～]", lambda m: chr(ord(m.group(0)) - 0xFEE0), normalized
        )  # 全角英数→半角

        # 不要な文字の除去
        normalized = re.sub(r"[\s\-_・]+", "", normalized)  # スペース、ハイフン等除去
        normalized = re.sub(r"[（）()\[\]【】『』「」]", "", normalized)  # 括弧類除去

        return normalized

    def _calculate_title_similarity(self, title1: str, title2: str) -> float:
        """
        タイトル間の類似度計算（Levenshtein距離ベース）

        Args:
            title1: タイトル1
            title2: タイトル2

        Returns:
            類似度 (0.0-1.0)
        """
        if not title1 or not title2:
            return 0.0

        if title1 == title2:
            return 1.0

        # シンプルなLevenshtein距離実装
        len1, len2 = len(title1), len(title2)
        if len1 == 0:
            return 0.0
        if len2 == 0:
            return 0.0

        # DP配列を使った編集距離計算
        dp = [[0] * (len2 + 1) for _ in range(len1 + 1)]

        for i in range(len1 + 1):
            dp[i][0] = i
        for j in range(len2 + 1):
            dp[0][j] = j

        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                cost = 0 if title1[i - 1] == title2[j - 1] else 1
                dp[i][j] = min(
                    dp[i - 1][j] + 1,  # 削除
                    dp[i][j - 1] + 1,  # 挿入
                    dp[i - 1][j - 1] + cost,  # 置換
                )

        max_len = max(len1, len2)
        return 1.0 - (dp[len1][len2] / max_len)

    def _update_title_variations(self, item: Dict[str, Any]):
        """
        タイトルバリエーションの更新

        Args:
            item: 新規アイテム
        """
        title = item.get("title", "").strip().lower()
        if not title:
            return

        normalized_title = self._normalize_title(title)

        if normalized_title not in self.title_variations:
            self.title_variations[normalized_title] = set()

        self.title_variations[normalized_title].add(title)

    def get_statistics(self) -> Dict[str, Any]:
        """
        重複検出の統計情報を取得

        Returns:
            統計情報
        """
        return {
            "unique_hashes": len(self.seen_hashes),
            "title_variations": len(self.title_variations),
            "total_title_variants": sum(
                len(variants) for variants in self.title_variations.values()
            ),
        }


# 個別サイト用の特別なコレクター


class BookWalkerRSSCollector(MangaRSSCollector):
    """BookWalker専用RSS収集クラス（強化版）"""

    def __init__(self, config_manager):
        super().__init__(config_manager)
        # BookWalker特有の設定
        self.bookwalker_base_url = "https://bookwalker.jp"
        self.series_cache = {}  # シリーズ情報キャッシュ

    def collect(self) -> List[Dict[str, Any]]:
        """BookWalker特化の収集処理"""
        self.logger.info("BookWalkerマンガ情報収集を開始...")

        # BookWalker用のフィードのみを処理
        bookwalker_feeds = [
            feed
            for feed in self.enabled_feeds
            if "bookwalker" in feed.get("name", "").lower()
            or "bookwalker" in feed.get("url", "").lower()
        ]

        if not bookwalker_feeds:
            # デフォルトBookWalkerフィードを追加
            bookwalker_feeds = [
                {
                    "name": "BookWalker",
                    "url": "https://bookwalker.jp/rss/book/new",
                    "category": "manga",
                    "enabled": True,
                }
            ]

        all_items = []

        for feed_info in bookwalker_feeds:
            feed_name = feed_info.get("name", "BookWalker")
            feed_url = feed_info.get("url")

            try:
                items = self._collect_bookwalker_feed(feed_url, feed_name)
                if items:
                    all_items.extend(items)
            except Exception as e:
                self.logger.error(f"BookWalker収集エラー: {e}")
                continue

        return all_items

    def _collect_bookwalker_feed(self, feed_url: str, feed_name: str) -> List[Dict[str, Any]]:
        """BookWalker専用の収集処理"""
        # 基本のRSS収集を使用
        items = self._collect_from_feed_enhanced(feed_url, feed_name)

        # BookWalker用の後処理
        processed_items = []
        for item in items:
            # BookWalker特有のメタデータを追加
            if "metadata" not in item:
                item["metadata"] = {}

            # URLから作品IDを抽出
            book_id = self._extract_book_id(item.get("official_url", ""))
            if book_id:
                item["metadata"]["book_id"] = book_id

                # シリーズ情報を取得（キャッシュ付き）
                series_info = self._get_series_info(book_id)
                if series_info:
                    item["metadata"]["series"] = series_info

            item["source"] = DataSource.RSS_BOOKWALKER.value
            processed_items.append(item)

        return processed_items

    def _extract_book_id(self, url: str) -> Optional[str]:
        """BookWalker URLから書籍IDを抽出"""
        if not url or "bookwalker.jp" not in url:
            return None

        # URLパターン: https://bookwalker.jp/de12345678-abcd-efgh-ijkl-123456789012/
        import re

        patterns = [
            r"/de([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})/?",
            r"/series/([0-9]+)/?",
            r"/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/?",
        ]

        for pattern in patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _get_series_info(self, book_id: str) -> Optional[Dict[str, Any]]:
        """BookWalkerのシリーズ情報を取得（キャッシュ付き）"""
        if book_id in self.series_cache:
            return self.series_cache[book_id]

        # 簡易版シリーズ情報推定
        # 実際の実装では、BookWalker APIやスクレイピングを使用
        series_info = {
            "book_id": book_id,
            "estimated_series": True,  # 推定情報フラグ
            "collection_date": datetime.now().isoformat(),
        }

        self.series_cache[book_id] = series_info
        return series_info

    def _normalize_manga_item_enhanced(
        self, work_info: Dict[str, Any], rss_item: RSSFeedItem, source_name: str
    ) -> Optional[Dict[str, Any]]:
        """BookWalker特有の正規化処理"""
        # 基本の正規化を実行
        normalized = super()._normalize_manga_item_enhanced(work_info, rss_item, source_name)

        if normalized:
            # BookWalker特有の処理
            normalized["source"] = DataSource.RSS_BOOKWALKER.value

            # BookWalker特有のメタデータを追加
            if "metadata" not in normalized:
                normalized["metadata"] = {}

            normalized["metadata"]["platform"] = "BookWalker"
            normalized["metadata"]["digital_distribution"] = True

            # 価格情報を抽出（可能なら）
            price_info = self._extract_price_info(rss_item.description or "")
            if price_info:
                normalized["metadata"]["price"] = price_info

        return normalized

    def _extract_price_info(self, description: str) -> Optional[Dict[str, Any]]:
        """説明文から価格情報を抽出"""
        if not description:
            return None

        # 価格パターン
        import re

        patterns = [
            r"(\d+)円",
            r"¥([\d,]+)",
            r"([\d,]+)円",
        ]

        for pattern in patterns:
            match = re.search(pattern, description)
            if match:
                price_str = match.group(1).replace(",", "")
                try:
                    price = int(price_str)
                    return {
                        "amount": price,
                        "currency": "JPY",
                        "extracted_from": "description",
                    }
                except ValueError:
                    continue

        return None


class DAnimeRSSCollector(MangaRSSCollector):
    """dアニメストア専用RSS収集クラス（アニメ配信情報用・強化版）"""

    def __init__(self, config_manager):
        super().__init__(config_manager)
        # dアニメストア特有の設定
        self.danime_base_url = "https://anime.dmkt-sp.jp"
        self.episode_cache = {}  # エピソード情報キャッシュ

    def collect(self) -> List[Dict[str, Any]]:
        """dアニメストア特有の収集処理"""
        self.logger.info("dアニメストア情報収集を開始...")

        # dアニメストア用のフィードのみを処理
        danime_feeds = [
            feed
            for feed in self.enabled_feeds
            if "danime" in feed.get("name", "").lower() or "dアニメ" in feed.get("name", "")
        ]

        if not danime_feeds:
            # デフォルトdアニメストアフィードを追加
            danime_feeds = [
                {
                    "name": "dアニメストア",
                    "url": "https://anime.dmkt-sp.jp/animestore/CF/rss/",
                    "category": "anime",
                    "enabled": True,
                }
            ]

        all_items = []

        for feed_info in danime_feeds:
            feed_name = feed_info.get("name", "dアニメストア")
            feed_url = feed_info.get("url")

            try:
                items = self._collect_danime_feed_enhanced(feed_url, feed_name)
                if items:
                    all_items.extend(items)
            except Exception as e:
                self.logger.error(f"dアニメストア収集エラー: {e}")
                continue

        return all_items

    def _collect_danime_feed_enhanced(self, feed_url: str, feed_name: str) -> List[Dict[str, Any]]:
        """dアニメストア専用の強化収集処理"""
        # 基本のRSS収集を使用
        items = self._collect_from_feed_enhanced(feed_url, feed_name)

        # dアニメストア用の後処理
        processed_items = []
        for item in items:
            # アニメとして分類
            item["type"] = WorkType.ANIME.value
            item["source"] = DataSource.RSS_DANIME.value

            # dアニメストア特有のメタデータを追加
            if "metadata" not in item:
                item["metadata"] = {}

            item["metadata"]["platform"] = "dアニメストア"
            item["metadata"]["streaming_service"] = True
            item["metadata"]["subscription_based"] = True

            # エピソード情報を解析
            episode_info = self._extract_episode_info(
                item.get("title", ""), item.get("description", "")
            )
            if episode_info:
                item["metadata"]["episode_info"] = episode_info

            # 配信日時情報を正規化
            streaming_date = self._normalize_streaming_date(
                item.get("releases", [{}])[0].get("date")
            )
            if streaming_date:
                item["metadata"]["streaming_date"] = streaming_date

            processed_items.append(item)

        return processed_items

    def _collect_danime_feed(self, feed_url: str, feed_name: str) -> List[Dict[str, Any]]:
        """dアニメストア専用の収集処理（後方互換性のため維持）"""
        return self._collect_danime_feed_enhanced(feed_url, feed_name)

    def _extract_episode_info(self, title: str, description: str) -> Optional[Dict[str, Any]]:
        """エピソード情報を抽出"""
        if not title:
            return None

        import re

        episode_patterns = [
            r"#(\d+)",
            r"(第\d+話)",
            r"Episode\s*(\d+)",
            r"EP\.(\d+)",
            r"(\d+)話",
        ]

        for pattern in episode_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                episode_str = match.group(1)
                try:
                    episode_num = int(re.search(r"\d+", episode_str).group())
                    return {
                        "episode_number": episode_num,
                        "episode_title": title,
                        "extracted_pattern": pattern,
                    }
                except (ValueError, AttributeError):
                    continue

        return None

    def _normalize_streaming_date(self, date_info) -> Optional[str]:
        """配信日時を正規化"""
        if not date_info:
            return None

        if isinstance(date_info, str):
            try:
                # ISO形式に変換して返す
                from datetime import datetime

                parsed_date = datetime.fromisoformat(date_info.replace("Z", "+00:00"))
                return parsed_date.isoformat()
            except ValueError:
                return date_info

        return str(date_info)

    def get_health_report(self) -> Dict[str, Any]:
        """Get comprehensive health monitoring report."""
        healthy_feeds = sum(1 for health in self.feed_health.values() if health.is_healthy)
        unhealthy_feeds = len(self.feed_health) - healthy_feeds

        total_requests = sum(health.total_requests for health in self.feed_health.values())
        total_failures = sum(health.total_failures for health in self.feed_health.values())

        avg_response_time = 0
        if self.feed_health:
            response_times = [
                health.average_response_time
                for health in self.feed_health.values()
                if health.average_response_time > 0
            ]
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)

        return {
            "total_feeds": len(self.enabled_feeds),
            "monitored_feeds": len(self.feed_health),
            "healthy_feeds": healthy_feeds,
            "unhealthy_feeds": unhealthy_feeds,
            "total_requests": total_requests,
            "total_failures": total_failures,
            "success_rate": (
                (total_requests - total_failures) / total_requests if total_requests > 0 else 0
            ),
            "average_response_time": avg_response_time,
            "feed_details": {
                url: {
                    "is_healthy": health.is_healthy,
                    "consecutive_failures": health.consecutive_failures,
                    "last_success": (
                        health.last_success.isoformat() if health.last_success else None
                    ),
                    "last_failure": (
                        health.last_failure.isoformat() if health.last_failure else None
                    ),
                    "total_requests": health.total_requests,
                    "total_failures": health.total_failures,
                    "average_response_time": health.average_response_time,
                }
                for url, health in self.feed_health.items()
            },
        }


# モジュールレベルのfetch_and_store関数（collect_all_data.pyから呼び出される）
def fetch_and_store() -> dict:
    """
    マンガRSSフィードからデータを収集しデータベースに保存する。

    Returns:
        dict: 収集結果のサマリー
    """
    from .config import get_config
    from .db import get_db

    try:
        # 設定取得
        config_manager = get_config()

        # コレクター初期化
        collector = MangaRSSCollector(config_manager)

        # データ収集
        items = collector.collect()

        if not items:
            logger.info("マンガRSSから収集されたアイテムはありません")
            return {"success": True, "collected": 0, "stored": 0}

        # データベースに保存
        db = get_db()
        stored_count = 0

        for item in items:
            try:
                title = item.get("title", "Unknown")
                if not title or title == "Unknown":
                    continue

                # 作品IDを取得または作成
                work_id = db.get_or_create_work(
                    title=title,
                    work_type="manga",
                    title_kana=item.get("title_kana"),
                    title_en=item.get("title_en"),
                    official_url=item.get("url"),
                )

                # リリース情報の保存
                release_date = item.get("release_date")
                if isinstance(release_date, datetime):
                    release_date = release_date.strftime("%Y-%m-%d")

                db.create_release(
                    work_id=work_id,
                    release_type=item.get("release_type", "volume"),
                    number=item.get("number"),
                    platform=item.get("platform", item.get("source")),
                    release_date=release_date,
                    source=item.get("source", "rss"),
                    source_url=item.get("url"),
                )
                stored_count += 1

            except Exception as e:
                logger.warning(f"アイテム保存エラー: {item.get('title', 'Unknown')} - {e}")
                continue

        logger.info(f"マンガRSS収集完了: {len(items)}件収集, {stored_count}件保存")
        return {"success": True, "collected": len(items), "stored": stored_count}

    except Exception as e:
        logger.error(f"マンガRSS fetch_and_store エラー: {e}")
        return {"success": False, "error": str(e)}
