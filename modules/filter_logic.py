#!/usr/bin/env python3
"""
フィルタリングロジックモジュール
アニメ・マンガ情報配信システムのコンテンツフィルタリング機能

Enhanced features (統合版):
- Dynamic config.json-based NG keyword management
- Genre-based filtering with flexible rules
- Tag-based filtering with priority levels
- User-defined custom filter rules
- Filter performance optimization
- Audit logging for filtered content
"""

import difflib
import hashlib
import json
import logging
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .models import AniListWork, RSSFeedItem, Work

# === Enhanced Filter Classes (統合: filter_logic_enhanced.py より移植) ===


class FilterAction(Enum):
    """Filter action enumeration."""

    ALLOW = "allow"
    BLOCK = "block"
    WARN = "warn"
    REVIEW = "review"


class FilterPriority(Enum):
    """Filter priority levels."""

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class FilterRule:
    """Custom filter rule definition."""

    rule_id: str
    name: str
    pattern: str  # Regex pattern
    action: FilterAction
    priority: FilterPriority
    targets: List[str] = field(default_factory=lambda: ["title", "description"])
    case_sensitive: bool = False
    enabled: bool = True
    reason: str = ""


@dataclass
class EnhancedFilterResult:
    """Enhanced filter result with detailed information."""

    is_filtered: bool
    action: FilterAction = FilterAction.ALLOW
    confidence: float = 0.0  # 0.0 to 1.0
    matched_rules: List[FilterRule] = field(default_factory=list)
    matched_keywords: List[str] = field(default_factory=list)
    matched_genres: List[str] = field(default_factory=list)
    matched_tags: List[str] = field(default_factory=list)
    reason: str = ""
    review_notes: str = ""


@dataclass
class FilterResult:
    """フィルタリング結果"""

    is_filtered: bool
    reason: Optional[str] = None
    matched_keywords: List[str] = None
    matched_genres: List[str] = None
    matched_tags: List[str] = None

    def __post_init__(self):
        if self.matched_keywords is None:
            self.matched_keywords = []
        if self.matched_genres is None:
            self.matched_genres = []
        if self.matched_tags is None:
            self.matched_tags = []


class ContentFilter:
    """Enhanced コンテンツフィルタリングクラス with performance optimization and fuzzy matching"""

    def __init__(
        self,
        config_manager,
        enable_fuzzy_matching: bool = True,
        similarity_threshold: float = 0.8,
    ):
        """
        Enhanced フィルターの初期化

        Args:
            config_manager: 設定管理インスタンス
            enable_fuzzy_matching: ファジィマッチングを有効にするか
            similarity_threshold: ファジィマッチングの類似度閾値 (0.0-1.0)
        """
        self.config = config_manager
        self.logger = logging.getLogger(__name__)
        self.enable_fuzzy_matching = enable_fuzzy_matching
        self.similarity_threshold = similarity_threshold

        # フィルタリング設定の読み込み
        self.ng_keywords = self._normalize_keywords(self.config.get_ng_keywords())
        self.ng_genres = self._normalize_keywords(self.config.get_ng_genres())
        self.exclude_tags = self._normalize_keywords(self.config.get_exclude_tags())

        # 追加の設定可能パターン
        self.custom_patterns = self._load_custom_patterns()

        # Performance optimization: pre-compile keyword patterns for faster matching
        self.compiled_keyword_patterns = self._compile_keyword_patterns()

        # Performance tracking
        self.filter_call_count = 0
        self.total_filter_time = 0.0
        self.cache_hits = 0

        self.logger.info(
            f"Enhanced filter initialized: NGキーワード {len(self.ng_keywords)} 件、"
            f"NGジャンル {len(self.ng_genres)} 件、"
            f"除外タグ {len(self.exclude_tags)} 件、"
            f"fuzzy matching: {enable_fuzzy_matching}"
        )

    def _normalize_keywords(self, keywords: List[str]) -> Set[str]:
        """キーワードを正規化"""
        normalized = set()
        for keyword in keywords:
            if keyword and isinstance(keyword, str):
                normalized.add(keyword.lower().strip())
        return normalized

    def _load_custom_patterns(self) -> List[re.Pattern]:
        """Enhanced カスタム正規表現パターンを読み込み"""
        patterns = []

        # Expanded set of dangerous patterns
        default_patterns = [
            r"(?i)r[-_]?18",  # R-18, R18, R_18
            r"(?i)adult[-_]?only",  # Adult only, adult-only
            r"(?i)18[-_]?禁",  # 18禁
            r"(?i)成人[-_]?向け",  # 成人向け
            r"(?i)エロ[-_]?(ゲーム|マンガ|アニメ)?",  # エロ related
            r"(?i)(xxx|porn|hentai)",  # English adult terms
            r"(?i)official[-_]?art[-_]?book",  # Filter art books that might contain adult content
            r"(?i)gravure",  # Gravure content
            r"(?i)成年コミック",  # Adult comics
        ]

        for pattern_str in default_patterns:
            try:
                patterns.append(re.compile(pattern_str, re.IGNORECASE | re.UNICODE))
            except re.error as e:
                self.logger.warning(f"無効な正規表現パターン '{pattern_str}': {e}")

        return patterns

    def _compile_keyword_patterns(self) -> Dict[str, re.Pattern]:
        """Compile NG keywords into regex patterns for faster matching."""
        compiled_patterns = {}

        # Compile each keyword as a word boundary pattern for better matching
        for keyword in self.ng_keywords:
            try:
                # Escape special regex characters and create word boundary pattern
                escaped = re.escape(keyword)
                pattern = re.compile(f"\\b{escaped}\\b", re.IGNORECASE | re.UNICODE)
                compiled_patterns[keyword] = pattern
            except re.error as e:
                self.logger.warning(f"Failed to compile keyword pattern '{keyword}': {e}")

        return compiled_patterns

    def filter_work(self, work: Work) -> FilterResult:
        """
        Enhanced 作品をフィルタリング with performance optimization

        Args:
            work: 作品オブジェクト

        Returns:
            FilterResult: フィルタリング結果
        """
        # タイトルチェック (using optimized method)
        title_result = self._check_text_content_optimized(work.title, "タイトル")
        if title_result.is_filtered:
            return title_result

        # 英語タイトルチェック
        if work.title_en:
            en_result = self._check_text_content_optimized(work.title_en, "英語タイトル")
            if en_result.is_filtered:
                return en_result

        # カナタイトルチェック
        if work.title_kana:
            kana_result = self._check_text_content_optimized(work.title_kana, "カナタイトル")
            if kana_result.is_filtered:
                return kana_result

        # メタデータからの追加チェック
        if hasattr(work, "metadata") and work.metadata:
            metadata_result = self._check_metadata(work.metadata)
            if metadata_result.is_filtered:
                return metadata_result

        return FilterResult(is_filtered=False)

    def filter_anilist_work(self, anilist_work: AniListWork) -> FilterResult:
        """
        Enhanced AniList作品をフィルタリング with optimized checking

        Args:
            anilist_work: AniList作品オブジェクト

        Returns:
            FilterResult: フィルタリング結果
        """
        # タイトル群チェック (using optimized method)
        titles_to_check = [
            (anilist_work.title_romaji, "ローマ字タイトル"),
            (anilist_work.title_english, "英語タイトル"),
            (anilist_work.title_native, "原語タイトル"),
        ]

        for title, context in titles_to_check:
            if title:
                result = self._check_text_content_optimized(title, context)
                if result.is_filtered:
                    return result

        # 説明文チェック (truncate long descriptions for performance)
        if anilist_work.description:
            # Limit description length for performance
            desc_text = (
                anilist_work.description[:500]
                if len(anilist_work.description) > 500
                else anilist_work.description
            )
            desc_result = self._check_text_content_optimized(desc_text, "説明文")
            if desc_result.is_filtered:
                return desc_result

        # ジャンルチェック (optimized)
        genre_result = self._check_genres_optimized(anilist_work.genres)
        if genre_result.is_filtered:
            return genre_result

        # タグチェック (optimized)
        tag_result = self._check_tags_optimized(anilist_work.tags)
        if tag_result.is_filtered:
            return tag_result

        return FilterResult(is_filtered=False)

    def filter_rss_item(self, rss_item: RSSFeedItem) -> FilterResult:
        """
        Enhanced RSSアイテムをフィルタリング with optimization

        Args:
            rss_item: RSSアイテムオブジェクト

        Returns:
            FilterResult: フィルタリング結果
        """
        # タイトルチェック (using optimized method)
        if rss_item.title:
            title_result = self._check_text_content_optimized(rss_item.title, "RSSタイトル")
            if title_result.is_filtered:
                return title_result

        # 説明文チェック (truncate for performance)
        if rss_item.description:
            desc_text = (
                rss_item.description[:300]
                if len(rss_item.description) > 300
                else rss_item.description
            )
            desc_result = self._check_text_content_optimized(desc_text, "RSS説明文")
            if desc_result.is_filtered:
                return desc_result

        return FilterResult(is_filtered=False)

    @lru_cache(maxsize=1000)
    def _get_text_hash(self, text: str) -> str:
        """Generate hash for text caching."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _check_text_content_optimized(self, text: str, context: str) -> FilterResult:
        """
        Optimized テキストコンテンツをチェック with caching and performance improvements

        Args:
            text: チェック対象テキスト
            context: コンテキスト（ログ用）

        Returns:
            FilterResult: フィルタリング結果
        """
        if not text:
            return FilterResult(is_filtered=False)

        start_time = time.time()
        self.filter_call_count += 1

        # Check cache first
        text_hash = self._get_text_hash(text + context)
        cached_result = getattr(self, "_filter_cache", {}).get(text_hash)
        if cached_result:
            self.cache_hits += 1
            return cached_result

        result = self._check_text_content(text, context)

        # Cache the result
        if not hasattr(self, "_filter_cache"):
            self._filter_cache = {}
        self._filter_cache[text_hash] = result

        # Limit cache size to prevent memory issues
        if len(self._filter_cache) > 5000:
            # Remove oldest half of cache entries
            cache_items = list(self._filter_cache.items())
            self._filter_cache = dict(cache_items[2500:])

        self.total_filter_time += time.time() - start_time
        return result

    def _check_text_content(self, text: str, context: str) -> FilterResult:
        """
        Enhanced テキストコンテンツをチェック with fuzzy matching

        Args:
            text: チェック対象テキスト
            context: コンテキスト（ログ用）

        Returns:
            FilterResult: フィルタリング結果
        """
        if not text:
            return FilterResult(is_filtered=False)

        # Fast exact matching using compiled patterns
        matched_keywords = []
        for keyword, pattern in self.compiled_keyword_patterns.items():
            if pattern.search(text):
                matched_keywords.append(keyword)

        # If no exact matches and fuzzy matching is enabled, try fuzzy matching
        if not matched_keywords and self.enable_fuzzy_matching:
            fuzzy_matches = self._fuzzy_keyword_matching(text)
            matched_keywords.extend(fuzzy_matches)

        if matched_keywords:
            reason = f"{context}でNGキーワードに一致: {', '.join(matched_keywords)}"
            self.logger.debug(f"フィルタリング: {reason} - '{text[:50]}...'")
            return FilterResult(is_filtered=True, reason=reason, matched_keywords=matched_keywords)

        # カスタムパターンチェック (optimized)
        for pattern in self.custom_patterns:
            match = pattern.search(text)
            if match:
                reason = (
                    f"{context}で危険パターンに一致: {pattern.pattern} (matched: '{match.group()}')"
                )
                self.logger.debug(f"フィルタリング: {reason} - '{text[:50]}...'")
                return FilterResult(is_filtered=True, reason=reason)

        return FilterResult(is_filtered=False)

    def _fuzzy_keyword_matching(self, text: str) -> List[str]:
        """
        Perform fuzzy matching against NG keywords.

        Args:
            text: Text to check

        Returns:
            List of matched keywords
        """
        fuzzy_matches = []
        text_words = text.lower().split()

        for keyword in self.ng_keywords:
            keyword_lower = keyword.lower()

            # Check each word in the text for fuzzy similarity
            for word in text_words:
                if len(word) >= 3:  # Only check words of reasonable length
                    similarity = difflib.SequenceMatcher(None, word, keyword_lower).ratio()
                    if similarity >= self.similarity_threshold:
                        fuzzy_matches.append(f"{keyword} (fuzzy: {similarity:.2f})")
                        self.logger.debug(
                            f"Fuzzy match: '{word}' ~ '{keyword}' (similarity: {similarity:.2f})"
                        )
                        break

        return fuzzy_matches

    def _check_genres_optimized(self, genres: List[str]) -> FilterResult:
        """
        Optimized ジャンルリストをチェック

        Args:
            genres: ジャンルリスト

        Returns:
            FilterResult: フィルタリング結果
        """
        if not genres:
            return FilterResult(is_filtered=False)

        # Convert to set for faster lookup
        genre_set = {genre.lower() for genre in genres if genre}
        matched_genres = list(genre_set.intersection(self.ng_genres))

        if matched_genres:
            reason = f"NGジャンルに一致: {', '.join(matched_genres)}"
            self.logger.debug(f"フィルタリング: {reason}")
            return FilterResult(is_filtered=True, reason=reason, matched_genres=matched_genres)

        return FilterResult(is_filtered=False)

    def _check_genres(self, genres: List[str]) -> FilterResult:
        """Backward compatibility wrapper."""
        return self._check_genres_optimized(genres)

    def _check_tags_optimized(self, tags: List[str]) -> FilterResult:
        """
        Optimized タグリストをチェック

        Args:
            tags: タグリスト

        Returns:
            FilterResult: フィルタリング結果
        """
        if not tags:
            return FilterResult(is_filtered=False)

        # Convert to set for faster lookup
        tag_set = {tag.lower() for tag in tags if tag}
        matched_tags = list(tag_set.intersection(self.exclude_tags))

        if matched_tags:
            reason = f"除外タグに一致: {', '.join(matched_tags)}"
            self.logger.debug(f"フィルタリング: {reason}")
            return FilterResult(is_filtered=True, reason=reason, matched_tags=matched_tags)

        return FilterResult(is_filtered=False)

    def _check_tags(self, tags: List[str]) -> FilterResult:
        """Backward compatibility wrapper."""
        return self._check_tags_optimized(tags)

    def _check_metadata(self, metadata: Dict[str, Any]) -> FilterResult:
        """
        メタデータをチェック

        Args:
            metadata: メタデータ辞書

        Returns:
            FilterResult: フィルタリング結果
        """
        # 説明文チェック
        if "description" in metadata and metadata["description"]:
            desc_result = self._check_text_content(metadata["description"], "メタデータ説明文")
            if desc_result.is_filtered:
                return desc_result

        # ジャンルチェック
        if "genres" in metadata and isinstance(metadata["genres"], list):
            genre_result = self._check_genres(metadata["genres"])
            if genre_result.is_filtered:
                return genre_result

        # タグチェック
        if "tags" in metadata and isinstance(metadata["tags"], list):
            tag_result = self._check_tags(metadata["tags"])
            if tag_result.is_filtered:
                return tag_result

        return FilterResult(is_filtered=False)

    def get_filter_statistics(self) -> Dict[str, Any]:
        """
        Enhanced フィルター統計情報を取得

        Returns:
            Dict[str, Any]: 統計情報 including performance metrics
        """
        avg_filter_time = (
            self.total_filter_time / self.filter_call_count if self.filter_call_count > 0 else 0
        )

        cache_hit_rate = (
            self.cache_hits / self.filter_call_count if self.filter_call_count > 0 else 0
        )

        return {
            "ng_keywords_count": len(self.ng_keywords),
            "ng_genres_count": len(self.ng_genres),
            "exclude_tags_count": len(self.exclude_tags),
            "custom_patterns_count": len(self.custom_patterns),
            "compiled_patterns_count": len(self.compiled_keyword_patterns),
            "fuzzy_matching_enabled": self.enable_fuzzy_matching,
            "similarity_threshold": self.similarity_threshold,
            "performance": {
                "total_filter_calls": self.filter_call_count,
                "total_filter_time": self.total_filter_time,
                "average_filter_time": avg_filter_time,
                "cache_hits": self.cache_hits,
                "cache_hit_rate": cache_hit_rate,
                "cache_size": len(getattr(self, "_filter_cache", {})),
            },
        }

    def optimize_performance(self):
        """
        Optimize filter performance by recompiling patterns and clearing old cache.
        """
        # Clear old cache
        if hasattr(self, "_filter_cache"):
            self._filter_cache.clear()

        # Recompile patterns
        self.compiled_keyword_patterns = self._compile_keyword_patterns()

        # Reset performance counters
        self.filter_call_count = 0
        self.total_filter_time = 0.0
        self.cache_hits = 0

        self.logger.info("Filter performance optimization completed")

    def add_dynamic_keyword(self, keyword: str):
        """
        Dynamically add a new NG keyword.

        Args:
            keyword: Keyword to add
        """
        if keyword and keyword.lower().strip() not in self.ng_keywords:
            self.ng_keywords.add(keyword.lower().strip())

            # Compile pattern for the new keyword
            try:
                escaped = re.escape(keyword.lower().strip())
                pattern = re.compile(f"\\b{escaped}\\b", re.IGNORECASE | re.UNICODE)
                self.compiled_keyword_patterns[keyword.lower().strip()] = pattern

                # Clear cache to ensure new keyword takes effect
                if hasattr(self, "_filter_cache"):
                    self._filter_cache.clear()

                self.logger.info(f"Added dynamic NG keyword: '{keyword}'")
            except re.error as e:
                self.logger.error(f"Failed to add dynamic keyword '{keyword}': {e}")

    def remove_dynamic_keyword(self, keyword: str):
        """
        Dynamically remove an NG keyword.

        Args:
            keyword: Keyword to remove
        """
        keyword_lower = keyword.lower().strip()
        if keyword_lower in self.ng_keywords:
            self.ng_keywords.discard(keyword_lower)
            self.compiled_keyword_patterns.pop(keyword_lower, None)

            # Clear cache
            if hasattr(self, "_filter_cache"):
                self._filter_cache.clear()

            self.logger.info(f"Removed dynamic NG keyword: '{keyword}'")

    # Legacy methods for backward compatibility with tests
    def set_ng_keywords(self, keywords: List[str]):
        """
        Legacy method: Set NG keywords for backward compatibility

        Args:
            keywords: List of NG keywords
        """
        self.ng_keywords = self._normalize_keywords(keywords)
        self.compiled_keyword_patterns = self._compile_keyword_patterns()

        # Clear cache to ensure new keywords take effect
        if hasattr(self, "_filter_cache"):
            self._filter_cache.clear()

        self.logger.info(f"Set NG keywords: {keywords}")

    def filter_anime(self, anime_data: Dict[str, Any]) -> bool:
        """
        Legacy method: Filter anime data for backward compatibility

        Args:
            anime_data: Anime data dictionary

        Returns:
            bool: True if should be filtered (blocked), False if allowed
        """
        if not anime_data:
            return False

        try:
            # Check isAdult flag first
            if anime_data.get("isAdult", False):
                return True

            # Check title
            title = anime_data.get("title", {})
            if isinstance(title, dict):
                for title_key in ["romaji", "english", "native"]:
                    title_text = title.get(title_key)
                    if title_text:
                        result = self._check_text_content_optimized(
                            title_text, f"anime_{title_key}"
                        )
                        if result.is_filtered:
                            return True
            elif isinstance(title, str):
                result = self._check_text_content_optimized(title, "anime_title")
                if result.is_filtered:
                    return True

            # Check description
            description = anime_data.get("description")
            if description:
                result = self._check_text_content_optimized(description, "anime_description")
                if result.is_filtered:
                    return True

            # Check genres
            genres = anime_data.get("genres", [])
            if genres:
                genre_result = self._check_genres_optimized(genres)
                if genre_result.is_filtered:
                    return True

            # Check tags
            tags = anime_data.get("tags", [])
            if tags:
                # Handle both string tags and dict tags
                tag_names = []
                for tag in tags:
                    if isinstance(tag, dict) and "name" in tag:
                        tag_names.append(tag["name"])
                    elif isinstance(tag, str):
                        tag_names.append(tag)

                if tag_names:
                    # Check tags using the tag-specific method
                    tag_result = self._check_tags_optimized(tag_names)
                    if tag_result.is_filtered:
                        return True

                    # Also check tag names against NG keywords
                    for tag_name in tag_names:
                        if tag_name:
                            tag_text_result = self._check_text_content_optimized(
                                tag_name, "tag_name"
                            )
                            if tag_text_result.is_filtered:
                                return True

            return False

        except Exception as e:
            self.logger.error(f"Error filtering anime data: {e}")
            return False

    def filter_manga(self, manga_data: Dict[str, Any]) -> bool:
        """
        Legacy method: Filter manga data for backward compatibility

        Args:
            manga_data: Manga data dictionary

        Returns:
            bool: True if should be filtered (blocked), False if allowed
        """
        if not manga_data:
            return False

        try:
            # Check title
            title = manga_data.get("title")
            if title:
                result = self._check_text_content_optimized(title, "manga_title")
                if result.is_filtered:
                    return True

            # Check description
            description = manga_data.get("description")
            if description:
                result = self._check_text_content_optimized(description, "manga_description")
                if result.is_filtered:
                    return True

            return False

        except Exception as e:
            self.logger.error(f"Error filtering manga data: {e}")
            return False


class FilterCollection:
    """複数のフィルターを管理するコレクション"""

    def __init__(self):
        self.filters = []
        self.logger = logging.getLogger(__name__)

    def add_filter(self, filter_instance: ContentFilter):
        """フィルターを追加"""
        self.filters.append(filter_instance)
        self.logger.debug(f"フィルターを追加しました: {type(filter_instance).__name__}")

    def filter_work(self, work: Work) -> FilterResult:
        """すべてのフィルターで作品をチェック"""
        for filter_instance in self.filters:
            result = filter_instance.filter_work(work)
            if result.is_filtered:
                return result

        return FilterResult(is_filtered=False)

    def filter_anilist_work(self, anilist_work: AniListWork) -> FilterResult:
        """すべてのフィルターでAniList作品をチェック"""
        for filter_instance in self.filters:
            result = filter_instance.filter_anilist_work(anilist_work)
            if result.is_filtered:
                return result

        return FilterResult(is_filtered=False)

    def filter_rss_item(self, rss_item: RSSFeedItem) -> FilterResult:
        """すべてのフィルターでRSSアイテムをチェック"""
        for filter_instance in self.filters:
            result = filter_instance.filter_rss_item(rss_item)
            if result.is_filtered:
                return result

        return FilterResult(is_filtered=False)


# 便利な関数
def create_default_filter(config_manager) -> ContentFilter:
    """
    デフォルト設定でフィルターを作成

    Args:
        config_manager: 設定管理インスタンス

    Returns:
        ContentFilter: フィルターインスタンス
    """
    return ContentFilter(config_manager)


def filter_work_list(
    works: List[Work], content_filter: ContentFilter
) -> tuple[List[Work], List[FilterResult]]:
    """
    作品リストをフィルタリング

    Args:
        works: 作品リスト
        content_filter: フィルターインスタンス

    Returns:
        tuple: (有効な作品リスト, フィルタリング結果リスト)
    """
    valid_works = []
    filter_results = []

    for work in works:
        result = content_filter.filter_work(work)
        filter_results.append(result)

        if not result.is_filtered:
            valid_works.append(work)

    return valid_works, filter_results


# === Enhanced Filter Manager (統合: filter_logic_enhanced.py より移植) ===


class ConfigBasedFilterManager:
    """
    Configuration-based filter management system.

    Features:
    - Load NG keywords from config.json
    - Dynamic filter rule updates
    - Filter rule validation
    - Export/import filter configurations
    - Performance monitoring
    """

    DEFAULT_CONFIG_PATH = "config.json"

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize config-based filter manager.

        Args:
            config_path: Path to config.json file
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.logger = logging.getLogger(__name__)

        # Load configuration
        self.config = self._load_config()

        # Initialize filter sets
        self.ng_keywords = self._load_ng_keywords()
        self.ng_genres = self._load_ng_genres()
        self.exclude_tags = self._load_exclude_tags()
        self.custom_rules = self._load_custom_rules()

        self.logger.info(
            "Config-based Filter Manager initialized: "
            f"{len(self.ng_keywords)} keywords, "
            f"{len(self.ng_genres)} genres, "
            f"{len(self.exclude_tags)} tags, "
            f"{len(self.custom_rules)} custom rules"
        )

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            config_file = Path(self.config_path)

            if not config_file.exists():
                self.logger.warning(f"Config file not found: {self.config_path}")
                return self._get_default_config()

            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)

            self.logger.info(f"Loaded configuration from {self.config_path}")
            return config

        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "filtering": {
                "ng_keywords": [
                    "エロ",
                    "R18",
                    "成人向け",
                    "BL",
                    "百合",
                    "ボーイズラブ",
                    "アダルト",
                    "18禁",
                ],
                "ng_genres": ["Hentai", "Ecchi"],
                "exclude_tags": ["Adult Cast", "Erotica"],
                "custom_rules": [],
            }
        }

    def _load_ng_keywords(self) -> Set[str]:
        """Load NG keywords from config."""
        keywords = self.config.get("filtering", {}).get("ng_keywords", [])
        return set(kw.lower().strip() for kw in keywords if kw)

    def _load_ng_genres(self) -> Set[str]:
        """Load NG genres from config."""
        genres = self.config.get("filtering", {}).get("ng_genres", [])
        return set(g.lower().strip() for g in genres if g)

    def _load_exclude_tags(self) -> Set[str]:
        """Load exclude tags from config."""
        tags = self.config.get("filtering", {}).get("exclude_tags", [])
        return set(t.lower().strip() for t in tags if t)

    def _load_custom_rules(self) -> List[FilterRule]:
        """Load custom filter rules from config."""
        rules_data = self.config.get("filtering", {}).get("custom_rules", [])
        rules = []

        for rule_data in rules_data:
            try:
                rule = FilterRule(
                    rule_id=rule_data.get("id", ""),
                    name=rule_data.get("name", ""),
                    pattern=rule_data.get("pattern", ""),
                    action=FilterAction(rule_data.get("action", "block")),
                    priority=FilterPriority(rule_data.get("priority", 2)),
                    targets=rule_data.get("targets", ["title", "description"]),
                    case_sensitive=rule_data.get("case_sensitive", False),
                    enabled=rule_data.get("enabled", True),
                    reason=rule_data.get("reason", ""),
                )
                rules.append(rule)
            except Exception as e:
                self.logger.error(f"Failed to load rule: {e}")

        return rules

    def add_ng_keyword(self, keyword: str) -> bool:
        """Add new NG keyword."""
        keyword = keyword.lower().strip()

        if not keyword:
            return False

        self.ng_keywords.add(keyword)

        # Update config
        filtering_config = self.config.setdefault("filtering", {})
        keywords_list = filtering_config.setdefault("ng_keywords", [])

        if keyword not in [k.lower() for k in keywords_list]:
            keywords_list.append(keyword)
            self._save_config()

        self.logger.info(f"Added NG keyword: {keyword}")
        return True

    def remove_ng_keyword(self, keyword: str) -> bool:
        """Remove NG keyword."""
        keyword = keyword.lower().strip()

        if keyword in self.ng_keywords:
            self.ng_keywords.remove(keyword)

            # Update config
            filtering_config = self.config.get("filtering", {})
            keywords_list = filtering_config.get("ng_keywords", [])
            filtering_config["ng_keywords"] = [k for k in keywords_list if k.lower() != keyword]
            self._save_config()

            self.logger.info(f"Removed NG keyword: {keyword}")
            return True

        return False

    def add_custom_rule(self, rule: FilterRule) -> bool:
        """Add custom filter rule."""
        # Validate rule
        if not rule.rule_id or not rule.pattern:
            self.logger.error("Invalid rule: missing id or pattern")
            return False

        # Check for duplicates
        if any(r.rule_id == rule.rule_id for r in self.custom_rules):
            self.logger.warning(f"Rule already exists: {rule.rule_id}")
            return False

        self.custom_rules.append(rule)

        # Update config
        filtering_config = self.config.setdefault("filtering", {})
        rules_list = filtering_config.setdefault("custom_rules", [])

        rules_list.append(
            {
                "id": rule.rule_id,
                "name": rule.name,
                "pattern": rule.pattern,
                "action": rule.action.value,
                "priority": rule.priority.value,
                "targets": rule.targets,
                "case_sensitive": rule.case_sensitive,
                "enabled": rule.enabled,
                "reason": rule.reason,
            }
        )

        self._save_config()

        self.logger.info(f"Added custom rule: {rule.name} ({rule.rule_id})")
        return True

    def _save_config(self) -> bool:
        """Save configuration to file."""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)

            self.logger.info(f"Saved configuration to {self.config_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")
            return False

    def get_all_keywords(self) -> List[str]:
        """Get all NG keywords."""
        return sorted(list(self.ng_keywords))

    def get_all_genres(self) -> List[str]:
        """Get all NG genres."""
        return sorted(list(self.ng_genres))

    def get_all_tags(self) -> List[str]:
        """Get all exclude tags."""
        return sorted(list(self.exclude_tags))

    def get_active_rules(self) -> List[FilterRule]:
        """Get all active custom rules."""
        return [rule for rule in self.custom_rules if rule.enabled]

    def export_config(self, output_path: str) -> bool:
        """Export filter configuration to file."""
        try:
            export_data = {
                "ng_keywords": self.get_all_keywords(),
                "ng_genres": self.get_all_genres(),
                "exclude_tags": self.get_all_tags(),
                "custom_rules": [
                    {
                        "id": rule.rule_id,
                        "name": rule.name,
                        "pattern": rule.pattern,
                        "action": rule.action.value,
                        "priority": rule.priority.value,
                        "targets": rule.targets,
                        "case_sensitive": rule.case_sensitive,
                        "enabled": rule.enabled,
                        "reason": rule.reason,
                    }
                    for rule in self.custom_rules
                ],
            }

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            self.logger.info(f"Exported filter config to {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to export config: {e}")
            return False


class EnhancedContentFilter:
    """
    Enhanced content filter with config-based management.

    Features:
    - Dynamic NG keyword management
    - Custom filter rules
    - Confidence scoring
    - Detailed filtering reports
    - Performance optimization
    """

    def __init__(
        self,
        config_manager: Optional[ConfigBasedFilterManager] = None,
        config_path: Optional[str] = None,
    ):
        """
        Initialize enhanced content filter.

        Args:
            config_manager: Filter configuration manager
            config_path: Path to config.json (if config_manager not provided)
        """
        self.config_manager = config_manager or ConfigBasedFilterManager(config_path)
        self.logger = logging.getLogger(__name__)

        # Statistics
        self.total_filtered = 0
        self.filter_stats = {"keywords": 0, "genres": 0, "tags": 0, "custom_rules": 0}

    @lru_cache(maxsize=1000)
    def _match_keyword(self, text: str, keyword: str) -> bool:
        """Check if keyword matches text (cached)."""
        if not text or not keyword:
            return False
        return keyword.lower() in text.lower()

    def filter_work(self, work: Work) -> EnhancedFilterResult:
        """
        Filter a work with enhanced result.

        Args:
            work: Work to filter

        Returns:
            Enhanced filter result
        """
        matched_keywords = []
        matched_genres = []
        matched_tags = []
        matched_rules = []

        # Check title against keywords
        for keyword in self.config_manager.ng_keywords:
            if self._match_keyword(work.title, keyword):
                matched_keywords.append(keyword)
                self.filter_stats["keywords"] += 1

        # Check metadata
        metadata = work.metadata or {}

        # Check genres
        if "genres" in metadata:
            genres = metadata["genres"]
            if isinstance(genres, list):
                for genre in genres:
                    if str(genre).lower() in self.config_manager.ng_genres:
                        matched_genres.append(str(genre))
                        self.filter_stats["genres"] += 1

        # Check tags
        if "tags" in metadata:
            tags = metadata["tags"]
            if isinstance(tags, list):
                for tag in tags:
                    tag_name = tag.get("name", tag) if isinstance(tag, dict) else str(tag)
                    if tag_name.lower() in self.config_manager.exclude_tags:
                        matched_tags.append(tag_name)
                        self.filter_stats["tags"] += 1

        # Check custom rules
        for rule in self.config_manager.get_active_rules():
            if self._check_custom_rule(work, rule):
                matched_rules.append(rule)
                self.filter_stats["custom_rules"] += 1

        # Determine filter action
        is_filtered = bool(matched_keywords or matched_genres or matched_tags or matched_rules)

        if is_filtered:
            self.total_filtered += 1

        # Calculate confidence
        confidence = self._calculate_confidence(
            matched_keywords, matched_genres, matched_tags, matched_rules
        )

        # Determine action
        if matched_rules:
            # Use highest priority rule action
            highest_priority_rule = max(matched_rules, key=lambda r: r.priority.value)
            action = highest_priority_rule.action
        else:
            action = FilterAction.BLOCK if is_filtered else FilterAction.ALLOW

        # Build reason
        reason_parts = []
        if matched_keywords:
            reason_parts.append(f"Keywords: {', '.join(matched_keywords)}")
        if matched_genres:
            reason_parts.append(f"Genres: {', '.join(matched_genres)}")
        if matched_tags:
            reason_parts.append(f"Tags: {', '.join(matched_tags)}")
        if matched_rules:
            reason_parts.append(f"Rules: {', '.join(r.name for r in matched_rules)}")

        reason = "; ".join(reason_parts) if reason_parts else "No matches"

        return EnhancedFilterResult(
            is_filtered=is_filtered,
            action=action,
            confidence=confidence,
            matched_rules=matched_rules,
            matched_keywords=matched_keywords,
            matched_genres=matched_genres,
            matched_tags=matched_tags,
            reason=reason,
        )

    def _check_custom_rule(self, work: Work, rule: FilterRule) -> bool:
        """Check if work matches custom rule."""
        try:
            pattern = re.compile(rule.pattern, re.IGNORECASE if not rule.case_sensitive else 0)

            for target in rule.targets:
                text = ""

                if target == "title":
                    text = work.title
                elif target == "description":
                    text = (work.metadata or {}).get("description", "")
                elif work.metadata and target in work.metadata:
                    text = str(work.metadata[target])

                if text and pattern.search(text):
                    return True

            return False

        except Exception as e:
            self.logger.error(f"Error checking rule {rule.rule_id}: {e}")
            return False

    def _calculate_confidence(
        self,
        keywords: List[str],
        genres: List[str],
        tags: List[str],
        rules: List[FilterRule],
    ) -> float:
        """Calculate filter confidence score."""
        if not any([keywords, genres, tags, rules]):
            return 0.0

        score = 0.0

        # Keyword matches (high weight)
        score += len(keywords) * 0.4

        # Genre matches (medium-high weight)
        score += len(genres) * 0.3

        # Tag matches (medium weight)
        score += len(tags) * 0.2

        # Rule matches (varies by priority)
        for rule in rules:
            score += rule.priority.value * 0.1

        # Normalize to 0.0-1.0
        return min(score / 3.0, 1.0)

    def get_statistics(self) -> Dict[str, Any]:
        """Get filter statistics."""
        return {
            "total_filtered": self.total_filtered,
            "filter_stats": self.filter_stats.copy(),
            "active_keywords": len(self.config_manager.ng_keywords),
            "active_genres": len(self.config_manager.ng_genres),
            "active_tags": len(self.config_manager.exclude_tags),
            "active_rules": len(self.config_manager.get_active_rules()),
        }


# === Convenience functions for enhanced filter ===


def create_enhanced_filter(config_path: Optional[str] = None) -> EnhancedContentFilter:
    """Create enhanced content filter instance."""
    return EnhancedContentFilter(config_path=config_path)


def filter_works(
    works: List[Work], config_path: Optional[str] = None
) -> Tuple[List[Work], List[Work]]:
    """
    Filter list of works using enhanced filter.

    Args:
        works: List of works to filter
        config_path: Path to config.json

    Returns:
        Tuple of (allowed_works, filtered_works)
    """
    filter_instance = create_enhanced_filter(config_path)

    allowed = []
    filtered = []

    for work in works:
        result = filter_instance.filter_work(work)

        if result.action == FilterAction.ALLOW:
            allowed.append(work)
        elif result.action == FilterAction.BLOCK:
            filtered.append(work)
        elif result.action == FilterAction.WARN:
            # Include with warning
            allowed.append(work)
        elif result.action == FilterAction.REVIEW:
            # Include for manual review
            allowed.append(work)

    return allowed, filtered
