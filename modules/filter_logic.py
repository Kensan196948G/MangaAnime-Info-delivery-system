#!/usr/bin/env python3
"""
フィルタリングロジックモジュール
アニメ・マンガ情報配信システムのコンテンツフィルタリング機能
"""

import logging
import re
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass
from .models import Work, AniListWork, RSSFeedItem, WorkType
import difflib
import time
from functools import lru_cache
import hashlib


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
    
    def __init__(self, config_manager, enable_fuzzy_matching: bool = True, similarity_threshold: float = 0.8):
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
        
        self.logger.info(f"Enhanced filter initialized: NGキーワード {len(self.ng_keywords)} 件、"
                        f"NGジャンル {len(self.ng_genres)} 件、"
                        f"除外タグ {len(self.exclude_tags)} 件、"
                        f"fuzzy matching: {enable_fuzzy_matching}")
    
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
            r'(?i)r[-_]?18',  # R-18, R18, R_18
            r'(?i)adult[-_]?only',  # Adult only, adult-only
            r'(?i)18[-_]?禁',  # 18禁
            r'(?i)成人[-_]?向け',  # 成人向け
            r'(?i)エロ[-_]?(ゲーム|マンガ|アニメ)?',  # エロ related
            r'(?i)(xxx|porn|hentai)',  # English adult terms
            r'(?i)official[-_]?art[-_]?book',  # Filter art books that might contain adult content
            r'(?i)gravure',  # Gravure content
            r'(?i)成年コミック',  # Adult comics
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
                pattern = re.compile(f'\\b{escaped}\\b', re.IGNORECASE | re.UNICODE)
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
        if hasattr(work, 'metadata') and work.metadata:
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
            (anilist_work.title_native, "原語タイトル")
        ]
        
        for title, context in titles_to_check:
            if title:
                result = self._check_text_content_optimized(title, context)
                if result.is_filtered:
                    return result
        
        # 説明文チェック (truncate long descriptions for performance)
        if anilist_work.description:
            # Limit description length for performance
            desc_text = anilist_work.description[:500] if len(anilist_work.description) > 500 else anilist_work.description
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
            desc_text = rss_item.description[:300] if len(rss_item.description) > 300 else rss_item.description
            desc_result = self._check_text_content_optimized(desc_text, "RSS説明文")
            if desc_result.is_filtered:
                return desc_result
        
        return FilterResult(is_filtered=False)
    
    @lru_cache(maxsize=1000)
    def _get_text_hash(self, text: str) -> str:
        """Generate hash for text caching."""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
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
        cached_result = getattr(self, '_filter_cache', {}).get(text_hash)
        if cached_result:
            self.cache_hits += 1
            return cached_result
        
        result = self._check_text_content(text, context)
        
        # Cache the result
        if not hasattr(self, '_filter_cache'):
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
            return FilterResult(
                is_filtered=True,
                reason=reason,
                matched_keywords=matched_keywords
            )
        
        # カスタムパターンチェック (optimized)
        for pattern in self.custom_patterns:
            match = pattern.search(text)
            if match:
                reason = f"{context}で危険パターンに一致: {pattern.pattern} (matched: '{match.group()}')"
                self.logger.debug(f"フィルタリング: {reason} - '{text[:50]}...'")
                return FilterResult(
                    is_filtered=True,
                    reason=reason
                )
        
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
                        self.logger.debug(f"Fuzzy match: '{word}' ~ '{keyword}' (similarity: {similarity:.2f})")
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
            return FilterResult(
                is_filtered=True,
                reason=reason,
                matched_genres=matched_genres
            )
        
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
            return FilterResult(
                is_filtered=True,
                reason=reason,
                matched_tags=matched_tags
            )
        
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
        if 'description' in metadata and metadata['description']:
            desc_result = self._check_text_content(metadata['description'], "メタデータ説明文")
            if desc_result.is_filtered:
                return desc_result
        
        # ジャンルチェック
        if 'genres' in metadata and isinstance(metadata['genres'], list):
            genre_result = self._check_genres(metadata['genres'])
            if genre_result.is_filtered:
                return genre_result
        
        # タグチェック
        if 'tags' in metadata and isinstance(metadata['tags'], list):
            tag_result = self._check_tags(metadata['tags'])
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
            self.total_filter_time / self.filter_call_count 
            if self.filter_call_count > 0 else 0
        )
        
        cache_hit_rate = (
            self.cache_hits / self.filter_call_count 
            if self.filter_call_count > 0 else 0
        )
        
        return {
            'ng_keywords_count': len(self.ng_keywords),
            'ng_genres_count': len(self.ng_genres),
            'exclude_tags_count': len(self.exclude_tags),
            'custom_patterns_count': len(self.custom_patterns),
            'compiled_patterns_count': len(self.compiled_keyword_patterns),
            'fuzzy_matching_enabled': self.enable_fuzzy_matching,
            'similarity_threshold': self.similarity_threshold,
            'performance': {
                'total_filter_calls': self.filter_call_count,
                'total_filter_time': self.total_filter_time,
                'average_filter_time': avg_filter_time,
                'cache_hits': self.cache_hits,
                'cache_hit_rate': cache_hit_rate,
                'cache_size': len(getattr(self, '_filter_cache', {}))
            }
        }
    
    def optimize_performance(self):
        """
        Optimize filter performance by recompiling patterns and clearing old cache.
        """
        # Clear old cache
        if hasattr(self, '_filter_cache'):
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
                pattern = re.compile(f'\\b{escaped}\\b', re.IGNORECASE | re.UNICODE)
                self.compiled_keyword_patterns[keyword.lower().strip()] = pattern
                
                # Clear cache to ensure new keyword takes effect
                if hasattr(self, '_filter_cache'):
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
            if hasattr(self, '_filter_cache'):
                self._filter_cache.clear()
            
            self.logger.info(f"Removed dynamic NG keyword: '{keyword}'")


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


def filter_work_list(works: List[Work], content_filter: ContentFilter) -> tuple[List[Work], List[FilterResult]]:
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