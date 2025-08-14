"""
Data normalization and integration module for Anime/Manga information system.

This module provides:
- Title normalization with multiple language support
- Duplicate work detection and merging
- Data quality scoring and validation
- Hash-based unique ID generation
- Multi-source data integration
- Fuzzy matching for similar titles

Requirements:
- Handle Japanese, English, and Romaji titles
- Detect variations and alternate titles
- Merge data from multiple sources (AniList, RSS feeds)
- Maintain data integrity and consistency
"""

import hashlib
import re
import logging
import unicodedata
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Set
from difflib import SequenceMatcher
from dataclasses import dataclass
from enum import Enum

from .models import Work, Release, WorkType, ReleaseType, DataSource


class NormalizationLevel(Enum):
    """Normalization level enumeration."""
    BASIC = "basic"
    ADVANCED = "advanced"
    STRICT = "strict"


class MatchConfidence(Enum):
    """Match confidence levels."""
    EXACT = "exact"          # 100% match
    HIGH = "high"            # 90-99% match
    MEDIUM = "medium"        # 70-89% match
    LOW = "low"              # 50-69% match
    NONE = "none"            # <50% match


@dataclass
class TitleVariation:
    """Title variation data structure."""
    original: str
    normalized: str
    language: str  # 'ja', 'en', 'romaji'
    confidence: float
    source: str


@dataclass
class MatchResult:
    """Work matching result."""
    target_id: Optional[int]
    confidence: MatchConfidence
    similarity_score: float
    matched_fields: List[str]
    differences: List[str]


@dataclass
class DataQualityScore:
    """Data quality scoring."""
    overall_score: float
    completeness: float
    accuracy: float
    consistency: float
    freshness: float
    details: Dict[str, Any]


class TitleNormalizer:
    """
    Advanced title normalization with multi-language support.
    
    Handles Japanese, English, and Romaji titles with various
    formatting conventions and alternate representations.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Unicode normalization patterns
        self.katakana_pattern = re.compile(r'[ァ-ヾ]')
        self.hiragana_pattern = re.compile(r'[ぁ-ゖ]')
        self.kanji_pattern = re.compile(r'[一-龯]')
        self.ascii_pattern = re.compile(r'[A-Za-z0-9]')
        
        # Common title prefixes/suffixes to remove
        self.noise_patterns = [
            r'^\[.*?\]\s*',          # [Tag] prefix
            r'^\【.*?】\s*',         # 【Tag】 prefix
            r'\s*\(.*?\)$',          # (Info) suffix
            r'\s*（.*?）$',          # （Info） suffix
            r'^\s*新刊[：:]\s*',      # 新刊: prefix
            r'^\s*new[：:]\s*',       # new: prefix (case insensitive)
            r'^\s*最新[：:]\s*',      # 最新: prefix
            r'^\s*update[：:]\s*',    # update: prefix
        ]
        
        # Season/series indicators
        self.season_patterns = [
            (r'第(\d+)期', r'Season \1'),
            (r'(\d+)期', r'Season \1'),
            (r'season\s*(\d+)', r'Season \1'),
            (r'シーズン(\d+)', r'Season \1'),
        ]
        
        # Episode/Volume patterns
        self.episode_patterns = [
            r'第(\d+)話',
            r'#(\d+)',
            r'Episode\s*(\d+)',
            r'ep\.?\s*(\d+)',
            r'(\d+)話'
        ]
        
        self.volume_patterns = [
            r'第(\d+)巻',
            r'Vol\.?\s*(\d+)',
            r'Volume\s*(\d+)',
            r'(\d+)巻'
        ]
    
    def normalize_title(self, title: str, level: NormalizationLevel = NormalizationLevel.ADVANCED) -> str:
        """
        Normalize title for consistent comparison and storage.
        
        Args:
            title: Raw title string
            level: Normalization level
            
        Returns:
            Normalized title
        """
        if not title or not title.strip():
            return ""
        
        normalized = title.strip()
        
        # Unicode normalization
        normalized = unicodedata.normalize('NFKC', normalized)
        
        # Remove noise patterns
        for pattern in self.noise_patterns:
            normalized = re.sub(pattern, '', normalized, flags=re.IGNORECASE)
        
        if level == NormalizationLevel.BASIC:
            # Basic cleanup only
            normalized = re.sub(r'\s+', ' ', normalized).strip()
            
        elif level == NormalizationLevel.ADVANCED:
            # Advanced normalization
            normalized = self._advanced_normalize(normalized)
            
        elif level == NormalizationLevel.STRICT:
            # Strict normalization for exact matching
            normalized = self._strict_normalize(normalized)
        
        return normalized.strip()
    
    def _advanced_normalize(self, title: str) -> str:
        """Advanced normalization with language-specific handling."""
        # Convert fullwidth to halfwidth characters
        title = self._convert_fullwidth(title)
        
        # Normalize punctuation
        title = self._normalize_punctuation(title)
        
        # Handle season indicators
        for pattern, replacement in self.season_patterns:
            title = re.sub(pattern, replacement, title, flags=re.IGNORECASE)
        
        # Clean up whitespace
        title = re.sub(r'\s+', ' ', title)
        
        return title
    
    def _strict_normalize(self, title: str) -> str:
        """Strict normalization for exact matching."""
        title = self._advanced_normalize(title)
        
        # Convert to lowercase for ASCII characters
        title = ''.join(c.lower() if c.isascii() else c for c in title)
        
        # Remove all non-alphanumeric characters except spaces
        title = re.sub(r'[^\w\s\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', '', title)
        
        # Normalize spaces
        title = re.sub(r'\s+', ' ', title)
        
        return title
    
    def _convert_fullwidth(self, text: str) -> str:
        """Convert fullwidth characters to halfwidth."""
        # Fullwidth ASCII to halfwidth
        text = text.translate(str.maketrans(
            'ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ'
            'ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ'
            '０１２３４５６７８９',
            'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            'abcdefghijklmnopqrstuvwxyz'
            '0123456789'
        ))
        
        return text
    
    def _normalize_punctuation(self, text: str) -> str:
        """Normalize punctuation marks."""
        # Common punctuation normalizations
        punctuation_map = {
            '！': '!',
            '？': '?',
            '：': ':',
            '；': ';',
            '，': ',',
            '．': '.',
            '（': '(',
            '）': ')',
            '「': '"',
            '」': '"',
            '『': '"',
            '』': '"',
            '〜': '~',
            '～': '~',
        }
        
        for jp, en in punctuation_map.items():
            text = text.replace(jp, en)
        
        return text
    
    def extract_variations(self, title: str) -> List[TitleVariation]:
        """
        Extract different variations of a title.
        
        Args:
            title: Original title
            
        Returns:
            List of title variations
        """
        variations = []
        
        # Original
        variations.append(TitleVariation(
            original=title,
            normalized=self.normalize_title(title, NormalizationLevel.BASIC),
            language=self._detect_language(title),
            confidence=1.0,
            source="original"
        ))
        
        # Advanced normalized
        advanced_norm = self.normalize_title(title, NormalizationLevel.ADVANCED)
        if advanced_norm != variations[0].normalized:
            variations.append(TitleVariation(
                original=title,
                normalized=advanced_norm,
                language=self._detect_language(title),
                confidence=0.9,
                source="advanced_normalized"
            ))
        
        # Strict normalized
        strict_norm = self.normalize_title(title, NormalizationLevel.STRICT)
        if strict_norm not in [v.normalized for v in variations]:
            variations.append(TitleVariation(
                original=title,
                normalized=strict_norm,
                language=self._detect_language(title),
                confidence=0.8,
                source="strict_normalized"
            ))
        
        return variations
    
    def _detect_language(self, text: str) -> str:
        """
        Detect the primary language of the text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Language code ('ja', 'en', 'romaji')
        """
        if not text:
            return "unknown"
        
        # Count character types
        katakana_count = len(self.katakana_pattern.findall(text))
        hiragana_count = len(self.hiragana_pattern.findall(text))
        kanji_count = len(self.kanji_pattern.findall(text))
        ascii_count = len(self.ascii_pattern.findall(text))
        
        total_chars = len(text.replace(' ', ''))
        
        if total_chars == 0:
            return "unknown"
        
        # Calculate ratios
        japanese_ratio = (katakana_count + hiragana_count + kanji_count) / total_chars
        ascii_ratio = ascii_count / total_chars
        
        if japanese_ratio > 0.3:
            return "ja"
        elif ascii_ratio > 0.7:
            # Distinguish between English and Romaji
            if self._is_likely_romaji(text):
                return "romaji"
            else:
                return "en"
        else:
            return "mixed"
    
    def _is_likely_romaji(self, text: str) -> bool:
        """Check if text is likely to be Romaji."""
        # Simple heuristics for Romaji detection
        romaji_indicators = [
            r'\b(no|wa|ga|wo|ni|de|to|kara|made|yo|ne|ka)\b',  # Common particles
            r'[aiueo]{2,}',  # Vowel sequences common in Romaji
            r'(tsu|chi|shi|cha|cho|kyo|gyo)',  # Common Romaji combinations
        ]
        
        for pattern in romaji_indicators:
            if re.search(pattern, text.lower()):
                return True
        
        return False


class WorkMatcher:
    """
    Advanced work matching with fuzzy matching capabilities.
    
    Provides methods to find duplicate or similar works across
    different data sources using various matching strategies.
    """
    
    def __init__(self, title_normalizer: TitleNormalizer):
        self.title_normalizer = title_normalizer
        self.logger = logging.getLogger(__name__)
    
    def find_matches(self, target_work: Work, candidates: List[Work], 
                    min_confidence: MatchConfidence = MatchConfidence.MEDIUM) -> List[MatchResult]:
        """
        Find matching works from candidates.
        
        Args:
            target_work: Work to find matches for
            candidates: List of candidate works
            min_confidence: Minimum confidence level for matches
            
        Returns:
            List of match results sorted by confidence
        """
        matches = []
        
        for candidate in candidates:
            if candidate.id == target_work.id:
                continue  # Skip self
            
            match_result = self._compare_works(target_work, candidate)
            
            if self._confidence_level_value(match_result.confidence) >= self._confidence_level_value(min_confidence):
                matches.append(match_result)
        
        # Sort by similarity score (descending)
        matches.sort(key=lambda x: x.similarity_score, reverse=True)
        
        return matches
    
    def _compare_works(self, work1: Work, work2: Work) -> MatchResult:
        """Compare two works and return match result."""
        matched_fields = []
        differences = []
        scores = []
        
        # Title comparison (most important)
        title_score = self._compare_titles(work1, work2)
        scores.append(title_score * 0.6)  # 60% weight
        
        if title_score > 0.8:
            matched_fields.append("title")
        else:
            differences.append(f"title: {work1.title} vs {work2.title}")
        
        # Work type comparison
        if work1.work_type == work2.work_type:
            scores.append(1.0 * 0.2)  # 20% weight
            matched_fields.append("work_type")
        else:
            scores.append(0.0 * 0.2)
            differences.append(f"work_type: {work1.work_type} vs {work2.work_type}")
        
        # URL comparison (if available)
        url_score = self._compare_urls(work1.official_url, work2.official_url)
        scores.append(url_score * 0.1)  # 10% weight
        
        if url_score > 0.5:
            matched_fields.append("official_url")
        elif work1.official_url and work2.official_url:
            differences.append("official_url: different URLs")
        
        # Metadata comparison (if available)
        metadata_score = self._compare_metadata(
            getattr(work1, 'metadata', {}), 
            getattr(work2, 'metadata', {})
        )
        scores.append(metadata_score * 0.1)  # 10% weight
        
        # Calculate overall similarity
        overall_score = sum(scores)
        confidence = self._score_to_confidence(overall_score)
        
        return MatchResult(
            target_id=work2.id,
            confidence=confidence,
            similarity_score=overall_score,
            matched_fields=matched_fields,
            differences=differences
        )
    
    def _compare_titles(self, work1: Work, work2: Work) -> float:
        """Compare titles of two works."""
        # Get all title variations for both works
        titles1 = self._get_all_titles(work1)
        titles2 = self._get_all_titles(work2)
        
        max_similarity = 0.0
        
        for title1 in titles1:
            for title2 in titles2:
                # Exact match
                if title1.normalized == title2.normalized:
                    return 1.0
                
                # Fuzzy match
                similarity = SequenceMatcher(None, title1.normalized, title2.normalized).ratio()
                max_similarity = max(max_similarity, similarity)
                
                # Also check with strict normalization
                strict1 = self.title_normalizer.normalize_title(title1.original, NormalizationLevel.STRICT)
                strict2 = self.title_normalizer.normalize_title(title2.original, NormalizationLevel.STRICT)
                
                if strict1 == strict2:
                    return 0.95
                
                strict_similarity = SequenceMatcher(None, strict1, strict2).ratio()
                max_similarity = max(max_similarity, strict_similarity * 0.9)
        
        return max_similarity
    
    def _get_all_titles(self, work: Work) -> List[TitleVariation]:
        """Get all available titles for a work."""
        titles = []
        
        # Main title
        if work.title:
            titles.extend(self.title_normalizer.extract_variations(work.title))
        
        # English title
        if work.title_en:
            titles.extend(self.title_normalizer.extract_variations(work.title_en))
        
        # Kana title
        if work.title_kana:
            titles.extend(self.title_normalizer.extract_variations(work.title_kana))
        
        # Metadata titles (if available)
        metadata = getattr(work, 'metadata', {})
        if 'anilist_titles' in metadata:
            anilist_titles = metadata['anilist_titles']
            for title_type, title_value in anilist_titles.items():
                if title_value:
                    titles.extend(self.title_normalizer.extract_variations(title_value))
        
        return titles
    
    def _compare_urls(self, url1: Optional[str], url2: Optional[str]) -> float:
        """Compare URLs."""
        if not url1 or not url2:
            return 0.0
        
        if url1 == url2:
            return 1.0
        
        # Extract domains for comparison
        try:
            from urllib.parse import urlparse
            domain1 = urlparse(url1).netloc.lower()
            domain2 = urlparse(url2).netloc.lower()
            
            if domain1 == domain2:
                return 0.7  # Same domain, different paths
            
            # Check for similar domains
            similarity = SequenceMatcher(None, domain1, domain2).ratio()
            return similarity * 0.5
            
        except:
            return 0.0
    
    def _compare_metadata(self, meta1: Dict[str, Any], meta2: Dict[str, Any]) -> float:
        """Compare metadata fields."""
        if not meta1 or not meta2:
            return 0.0
        
        common_keys = set(meta1.keys()) & set(meta2.keys())
        if not common_keys:
            return 0.0
        
        matches = 0
        total = len(common_keys)
        
        for key in common_keys:
            if meta1[key] == meta2[key]:
                matches += 1
            elif isinstance(meta1[key], str) and isinstance(meta2[key], str):
                # Fuzzy string comparison
                similarity = SequenceMatcher(None, str(meta1[key]), str(meta2[key])).ratio()
                if similarity > 0.8:
                    matches += 0.8
        
        return matches / total if total > 0 else 0.0
    
    def _confidence_level_value(self, confidence: MatchConfidence) -> float:
        """Convert confidence level to numeric value."""
        mapping = {
            MatchConfidence.EXACT: 1.0,
            MatchConfidence.HIGH: 0.9,
            MatchConfidence.MEDIUM: 0.7,
            MatchConfidence.LOW: 0.5,
            MatchConfidence.NONE: 0.0
        }
        return mapping.get(confidence, 0.0)
    
    def _score_to_confidence(self, score: float) -> MatchConfidence:
        """Convert similarity score to confidence level."""
        if score >= 0.98:
            return MatchConfidence.EXACT
        elif score >= 0.9:
            return MatchConfidence.HIGH
        elif score >= 0.7:
            return MatchConfidence.MEDIUM
        elif score >= 0.5:
            return MatchConfidence.LOW
        else:
            return MatchConfidence.NONE


class DataQualityAnalyzer:
    """
    Data quality analysis and scoring.
    
    Evaluates the completeness, accuracy, consistency, and freshness
    of work and release data across multiple dimensions.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def analyze_work(self, work: Work) -> DataQualityScore:
        """
        Analyze data quality for a work.
        
        Args:
            work: Work to analyze
            
        Returns:
            Data quality score
        """
        completeness = self._calculate_completeness(work)
        accuracy = self._calculate_accuracy(work)
        consistency = self._calculate_consistency(work)
        freshness = self._calculate_freshness(work)
        
        # Overall score (weighted average)
        overall = (
            completeness * 0.3 +
            accuracy * 0.3 +
            consistency * 0.2 +
            freshness * 0.2
        )
        
        return DataQualityScore(
            overall_score=overall,
            completeness=completeness,
            accuracy=accuracy,
            consistency=consistency,
            freshness=freshness,
            details={
                'has_title': bool(work.title),
                'has_english_title': bool(work.title_en),
                'has_kana_title': bool(work.title_kana),
                'has_official_url': bool(work.official_url),
                'has_metadata': bool(getattr(work, 'metadata', {})),
                'creation_date': work.created_at.isoformat() if work.created_at else None
            }
        )
    
    def _calculate_completeness(self, work: Work) -> float:
        """Calculate completeness score (0.0 to 1.0)."""
        fields = [
            work.title,           # Required
            work.title_en,        # Optional but valuable
            work.title_kana,      # Optional but valuable
            work.official_url,    # Optional but valuable
        ]
        
        # Basic completeness
        filled_basic = sum(1 for field in fields[:1] if field)  # Title is required
        basic_score = filled_basic / 1
        
        # Extended completeness
        filled_extended = sum(1 for field in fields[1:] if field)
        extended_score = filled_extended / 3
        
        # Metadata completeness
        metadata = getattr(work, 'metadata', {})
        metadata_fields = ['description', 'genres', 'tags', 'status']
        filled_metadata = sum(1 for field in metadata_fields if field in metadata and metadata[field])
        metadata_score = filled_metadata / len(metadata_fields)
        
        # Weighted completeness
        return basic_score * 0.6 + extended_score * 0.3 + metadata_score * 0.1
    
    def _calculate_accuracy(self, work: Work) -> float:
        """Calculate accuracy score based on data validation."""
        score = 1.0
        
        # Title validation
        if work.title:
            if len(work.title.strip()) < 2:
                score -= 0.3
            if work.title.strip() != work.title:
                score -= 0.1
        
        # URL validation
        if work.official_url:
            if not self._is_valid_url(work.official_url):
                score -= 0.2
        
        # Work type validation
        if not isinstance(work.work_type, (WorkType, str)):
            score -= 0.2
        
        return max(0.0, score)
    
    def _calculate_consistency(self, work: Work) -> float:
        """Calculate consistency score."""
        score = 1.0
        
        # Check title consistency
        titles = [work.title, work.title_en, work.title_kana]
        non_empty_titles = [t for t in titles if t]
        
        if len(non_empty_titles) > 1:
            # Basic consistency checks
            normalizer = TitleNormalizer()
            normalized_titles = [normalizer.normalize_title(t, NormalizationLevel.STRICT) for t in non_empty_titles]
            
            # Check if normalized titles are too different
            max_similarity = 0.0
            for i in range(len(normalized_titles)):
                for j in range(i + 1, len(normalized_titles)):
                    similarity = SequenceMatcher(None, normalized_titles[i], normalized_titles[j]).ratio()
                    max_similarity = max(max_similarity, similarity)
            
            if max_similarity < 0.3:  # Titles are very different
                score -= 0.2
        
        return max(0.0, score)
    
    def _calculate_freshness(self, work: Work) -> float:
        """Calculate freshness score based on data age."""
        if not work.created_at:
            return 0.5  # Unknown, assume medium freshness
        
        age_days = (datetime.now() - work.created_at).days
        
        # Freshness scoring
        if age_days <= 1:
            return 1.0
        elif age_days <= 7:
            return 0.9
        elif age_days <= 30:
            return 0.7
        elif age_days <= 90:
            return 0.5
        elif age_days <= 180:
            return 0.3
        else:
            return 0.1
    
    def _is_valid_url(self, url: str) -> bool:
        """Basic URL validation."""
        try:
            from urllib.parse import urlparse
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False


class DataIntegrator:
    """
    Multi-source data integration and merging.
    
    Combines data from multiple sources (AniList, RSS feeds) while
    maintaining data integrity and resolving conflicts intelligently.
    """
    
    def __init__(self):
        self.title_normalizer = TitleNormalizer()
        self.work_matcher = WorkMatcher(self.title_normalizer)
        self.quality_analyzer = DataQualityAnalyzer()
        self.logger = logging.getLogger(__name__)
    
    def generate_work_hash(self, title: str, work_type: str) -> str:
        """
        Generate unique hash ID for work identification.
        
        Args:
            title: Work title
            work_type: Work type ('anime' or 'manga')
            
        Returns:
            SHA-256 hash string (16 characters)
        """
        # Normalize title for consistent hashing
        normalized_title = self.title_normalizer.normalize_title(title, NormalizationLevel.STRICT)
        
        # Create hash input
        hash_input = f"{normalized_title.lower()}_{work_type.lower()}"
        
        # Generate SHA-256 hash and take first 16 characters
        return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()[:16]
    
    def integrate_works(self, works: List[Work]) -> List[Work]:
        """
        Integrate and deduplicate works from multiple sources.
        
        Args:
            works: List of works from various sources
            
        Returns:
            Deduplicated and integrated works
        """
        if not works:
            return []
        
        self.logger.info(f"Integrating {len(works)} works...")
        
        # Group works by potential matches
        work_groups = self._group_similar_works(works)
        
        integrated_works = []
        
        for group in work_groups:
            if len(group) == 1:
                # No duplicates, add as-is
                integrated_works.append(group[0])
            else:
                # Merge similar works
                merged_work = self._merge_works(group)
                integrated_works.append(merged_work)
        
        self.logger.info(f"Integration complete: {len(integrated_works)} unique works")
        
        return integrated_works
    
    def _group_similar_works(self, works: List[Work]) -> List[List[Work]]:
        """Group similar works together."""
        groups = []
        processed = set()
        
        for i, work in enumerate(works):
            if i in processed:
                continue
            
            group = [work]
            processed.add(i)
            
            # Find similar works
            for j, other_work in enumerate(works[i + 1:], i + 1):
                if j in processed:
                    continue
                
                match_result = self.work_matcher._compare_works(work, other_work)
                
                if match_result.confidence in [MatchConfidence.EXACT, MatchConfidence.HIGH]:
                    group.append(other_work)
                    processed.add(j)
            
            groups.append(group)
        
        return groups
    
    def _merge_works(self, works: List[Work]) -> Work:
        """
        Merge multiple similar works into a single work.
        
        Args:
            works: List of similar works to merge
            
        Returns:
            Merged work with best available data
        """
        if not works:
            raise ValueError("Cannot merge empty work list")
        
        if len(works) == 1:
            return works[0]
        
        self.logger.debug(f"Merging {len(works)} similar works")
        
        # Analyze quality of each work
        quality_scores = [(work, self.quality_analyzer.analyze_work(work)) for work in works]
        quality_scores.sort(key=lambda x: x[1].overall_score, reverse=True)
        
        # Use the highest quality work as base
        base_work = quality_scores[0][0]
        merged_work = Work(
            id=base_work.id,
            title=base_work.title,
            work_type=base_work.work_type,
            title_kana=base_work.title_kana,
            title_en=base_work.title_en,
            official_url=base_work.official_url,
            created_at=base_work.created_at,
            metadata=dict(getattr(base_work, 'metadata', {}))
        )
        
        # Merge data from other works
        for work, quality in quality_scores[1:]:
            self._merge_work_fields(merged_work, work, quality)
        
        # Add merge metadata
        if not hasattr(merged_work, 'metadata') or merged_work.metadata is None:
            merged_work.metadata = {}
        
        merged_work.metadata.update({
            'merged_from_sources': [getattr(w, 'metadata', {}).get('source', 'unknown') for w in works],
            'merge_timestamp': datetime.now().isoformat(),
            'merged_work_count': len(works)
        })
        
        return merged_work
    
    def _merge_work_fields(self, target: Work, source: Work, source_quality: DataQualityScore):
        """
        Merge fields from source work into target work.
        
        Args:
            target: Target work to merge into
            source: Source work to merge from
            source_quality: Quality score of source work
        """
        # Only merge if source has better data
        if source_quality.overall_score < 0.5:
            return  # Skip low-quality sources
        
        # Merge titles (prefer non-empty values)
        if not target.title_en and source.title_en:
            target.title_en = source.title_en
        
        if not target.title_kana and source.title_kana:
            target.title_kana = source.title_kana
        
        if not target.official_url and source.official_url:
            target.official_url = source.official_url
        
        # Merge metadata
        source_metadata = getattr(source, 'metadata', {})
        if source_metadata:
            for key, value in source_metadata.items():
                if key not in target.metadata or not target.metadata[key]:
                    target.metadata[key] = value
                elif isinstance(value, list) and isinstance(target.metadata[key], list):
                    # Merge lists (remove duplicates)
                    combined = list(set(target.metadata[key] + value))
                    target.metadata[key] = combined


# Convenience functions for external use

def normalize_title(title: str, level: str = "advanced") -> str:
    """
    Normalize a title using the specified level.
    
    Args:
        title: Title to normalize
        level: Normalization level ('basic', 'advanced', 'strict')
        
    Returns:
        Normalized title
    """
    normalizer = TitleNormalizer()
    norm_level = {
        'basic': NormalizationLevel.BASIC,
        'advanced': NormalizationLevel.ADVANCED,
        'strict': NormalizationLevel.STRICT
    }.get(level.lower(), NormalizationLevel.ADVANCED)
    
    return normalizer.normalize_title(title, norm_level)


def find_duplicate_works(works: List[Work], min_confidence: str = "medium") -> Dict[int, List[MatchResult]]:
    """
    Find duplicate works in a list.
    
    Args:
        works: List of works to check
        min_confidence: Minimum confidence level ('low', 'medium', 'high', 'exact')
        
    Returns:
        Dictionary mapping work IDs to their potential duplicates
    """
    normalizer = TitleNormalizer()
    matcher = WorkMatcher(normalizer)
    
    confidence_map = {
        'low': MatchConfidence.LOW,
        'medium': MatchConfidence.MEDIUM,
        'high': MatchConfidence.HIGH,
        'exact': MatchConfidence.EXACT
    }
    
    min_conf = confidence_map.get(min_confidence.lower(), MatchConfidence.MEDIUM)
    
    duplicates = {}
    
    for work in works:
        if not work.id:
            continue
            
        matches = matcher.find_matches(work, works, min_conf)
        if matches:
            duplicates[work.id] = matches
    
    return duplicates\n\n\ndef integrate_work_data(works: List[Work]) -> List[Work]:\n    \"\"\"\n    Integrate and deduplicate works from multiple sources.\n    \n    Args:\n        works: List of works to integrate\n        \n    Returns:\n        Integrated and deduplicated works\n    \"\"\"\n    integrator = DataIntegrator()\n    return integrator.integrate_works(works)\n\n\ndef generate_unique_id(title: str, work_type: str) -> str:\n    \"\"\"\n    Generate unique ID for a work.\n    \n    Args:\n        title: Work title\n        work_type: Work type ('anime' or 'manga')\n        \n    Returns:\n        Unique hash ID\n    \"\"\"\n    integrator = DataIntegrator()\n    return integrator.generate_work_hash(title, work_type)\n\n\ndef analyze_data_quality(work: Work) -> Dict[str, Any]:\n    \"\"\"\n    Analyze data quality for a work.\n    \n    Args:\n        work: Work to analyze\n        \n    Returns:\n        Quality analysis results\n    \"\"\"\n    analyzer = DataQualityAnalyzer()\n    score = analyzer.analyze_work(work)\n    \n    return {\n        'overall_score': score.overall_score,\n        'completeness': score.completeness,\n        'accuracy': score.accuracy,\n        'consistency': score.consistency,\n        'freshness': score.freshness,\n        'grade': _score_to_grade(score.overall_score),\n        'details': score.details\n    }\n\n\ndef _score_to_grade(score: float) -> str:\n    \"\"\"Convert quality score to letter grade.\"\"\"\n    if score >= 0.9:\n        return "A"\n    elif score >= 0.8:\n        return "B"\n    elif score >= 0.7:\n        return "C"\n    elif score >= 0.6:\n        return "D"\n    else:\n        return "F"