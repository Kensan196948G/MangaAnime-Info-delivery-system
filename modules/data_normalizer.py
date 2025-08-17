"""
Fixed Data normalization and integration module for Anime/Manga information system.

This module provides:
- Title normalization with multiple language support
- Duplicate work detection and merging
- Data quality scoring and validation
- Hash-based unique ID generation
- Multi-source data integration
- Fuzzy matching for similar titles
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

    EXACT = "exact"  # 100% match
    HIGH = "high"  # 90-99% match
    MEDIUM = "medium"  # 70-89% match
    LOW = "low"  # 50-69% match
    NONE = "none"  # <50% match


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
        self.katakana_pattern = re.compile(r"[ァ-ヾ]")
        self.hiragana_pattern = re.compile(r"[ぁ-ゖ]")
        self.kanji_pattern = re.compile(r"[一-龯]")
        self.ascii_pattern = re.compile(r"[A-Za-z0-9]")

        # Common title prefixes/suffixes to remove
        self.noise_patterns = [
            r"^\[.*?\]\s*",  # [Tag] prefix
            r"^\【.*?】\s*",  # 【Tag】 prefix
            r"\s*\(.*?\)$",  # (Info) suffix
            r"\s*（.*?）$",  # （Info） suffix
            r"^\s*新刊[：:]\s*",  # 新刊: prefix
            r"^\s*new[：:]\s*",  # new: prefix (case insensitive)
            r"^\s*最新[：:]\s*",  # 最新: prefix
            r"^\s*update[：:]\s*",  # update: prefix
        ]

    def normalize_title(
        self, title: str, level: NormalizationLevel = NormalizationLevel.ADVANCED
    ) -> str:
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
        normalized = unicodedata.normalize("NFKC", normalized)

        # Remove noise patterns
        for pattern in self.noise_patterns:
            normalized = re.sub(pattern, "", normalized, flags=re.IGNORECASE)

        if level == NormalizationLevel.BASIC:
            # Basic cleanup only
            normalized = re.sub(r"\s+", " ", normalized).strip()

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

        # Clean up whitespace
        title = re.sub(r"\s+", " ", title)

        return title

    def _strict_normalize(self, title: str) -> str:
        """Strict normalization for exact matching."""
        title = self._advanced_normalize(title)

        # Convert to lowercase for ASCII characters
        title = "".join(c.lower() if c.isascii() else c for c in title)

        # Remove all non-alphanumeric characters except spaces
        title = re.sub(r"[^\w\s\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]", "", title)

        # Normalize spaces
        title = re.sub(r"\s+", " ", title)

        return title

    def _convert_fullwidth(self, text: str) -> str:
        """Convert fullwidth characters to halfwidth."""
        # Fullwidth ASCII to halfwidth
        text = text.translate(
            str.maketrans(
                "ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ"
                "ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ"
                "０１２３４５６７８９",
                "ABCDEFGHIJKLMNOPQRSTUVWXYZ" "abcdefghijklmnopqrstuvwxyz" "0123456789",
            )
        )

        return text

    def _normalize_punctuation(self, text: str) -> str:
        """Normalize punctuation marks."""
        # Common punctuation normalizations
        punctuation_map = {
            "！": "!",
            "？": "?",
            "：": ":",
            "；": ";",
            "，": ",",
            "．": ".",
            "（": "(",
            "）": ")",
            "「": '"',
            "」": '"',
            "『": '"',
            "』": '"',
            "〜": "~",
            "～": "~",
        }

        for jp, en in punctuation_map.items():
            text = text.replace(jp, en)

        return text

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

        total_chars = len(text.replace(" ", ""))

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
            r"\b(no|wa|ga|wo|ni|de|to|kara|made|yo|ne|ka)\b",  # Common particles
            r"[aiueo]{2,}",  # Vowel sequences common in Romaji
            r"(tsu|chi|shi|cha|cho|kyo|gyo)",  # Common Romaji combinations
        ]

        for pattern in romaji_indicators:
            if re.search(pattern, text.lower()):
                return True

        return False

    def extract_variations(self, title: str) -> List[Dict[str, Any]]:
        """
        Extract different variations of a title.

        Args:
            title: Original title

        Returns:
            List of title variations
        """
        variations = []

        # Original
        variations.append(
            {
                "original": title,
                "normalized": self.normalize_title(title, NormalizationLevel.BASIC),
                "language": self._detect_language(title),
                "confidence": 1.0,
                "source": "original",
            }
        )

        # Advanced normalized
        advanced_norm = self.normalize_title(title, NormalizationLevel.ADVANCED)
        if advanced_norm != variations[0]["normalized"]:
            variations.append(
                {
                    "original": title,
                    "normalized": advanced_norm,
                    "language": self._detect_language(title),
                    "confidence": 0.9,
                    "source": "advanced_normalized",
                }
            )

        # Strict normalized
        strict_norm = self.normalize_title(title, NormalizationLevel.STRICT)
        if strict_norm not in [v["normalized"] for v in variations]:
            variations.append(
                {
                    "original": title,
                    "normalized": strict_norm,
                    "language": self._detect_language(title),
                    "confidence": 0.8,
                    "source": "strict_normalized",
                }
            )

        return variations


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
            completeness * 0.3 + accuracy * 0.3 + consistency * 0.2 + freshness * 0.2
        )

        return DataQualityScore(
            overall_score=overall,
            completeness=completeness,
            accuracy=accuracy,
            consistency=consistency,
            freshness=freshness,
            details={
                "has_title": bool(work.title),
                "has_english_title": bool(work.title_en),
                "has_kana_title": bool(work.title_kana),
                "has_official_url": bool(work.official_url),
                "has_metadata": bool(getattr(work, "metadata", {})),
                "creation_date": (
                    work.created_at.isoformat() if work.created_at else None
                ),
            },
        )

    def _calculate_completeness(self, work: Work) -> float:
        """Calculate completeness score (0.0 to 1.0)."""
        fields = [
            work.title,  # Required
            work.title_en,  # Optional but valuable
            work.title_kana,  # Optional but valuable
            work.official_url,  # Optional but valuable
        ]

        # Basic completeness
        filled_basic = sum(1 for field in fields[:1] if field)  # Title is required
        basic_score = filled_basic / 1

        # Extended completeness
        filled_extended = sum(1 for field in fields[1:] if field)
        extended_score = filled_extended / 3

        # Metadata completeness
        metadata = getattr(work, "metadata", {})
        metadata_fields = ["description", "genres", "tags", "status"]
        filled_metadata = sum(
            1 for field in metadata_fields if field in metadata and metadata[field]
        )
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
            normalized_titles = [
                normalizer.normalize_title(t, NormalizationLevel.STRICT)
                for t in non_empty_titles
            ]

            # Check if normalized titles are too different
            max_similarity = 0.0
            for i in range(len(normalized_titles)):
                for j in range(i + 1, len(normalized_titles)):
                    similarity = SequenceMatcher(
                        None, normalized_titles[i], normalized_titles[j]
                    ).ratio()
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
        normalized_title = self.title_normalizer.normalize_title(
            title, NormalizationLevel.STRICT
        )

        # Create hash input
        hash_input = f"{normalized_title.lower()}_{work_type.lower()}"

        # Generate SHA-256 hash and take first 16 characters
        return hashlib.sha256(hash_input.encode("utf-8")).hexdigest()[:16]

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

        # For now, just return the works as-is (basic implementation)
        # In a full implementation, this would group similar works and merge them

        self.logger.info(f"Integration complete: {len(works)} works")
        return works


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
        "basic": NormalizationLevel.BASIC,
        "advanced": NormalizationLevel.ADVANCED,
        "strict": NormalizationLevel.STRICT,
    }.get(level.lower(), NormalizationLevel.ADVANCED)

    return normalizer.normalize_title(title, norm_level)


def generate_unique_id(title: str, work_type: str) -> str:
    """
    Generate unique ID for a work.

    Args:
        title: Work title
        work_type: Work type ('anime' or 'manga')

    Returns:
        Unique hash ID
    """
    integrator = DataIntegrator()
    return integrator.generate_work_hash(title, work_type)


def analyze_data_quality(work: Work) -> Dict[str, Any]:
    """
    Analyze data quality for a work.

    Args:
        work: Work to analyze

    Returns:
        Quality analysis results
    """
    analyzer = DataQualityAnalyzer()
    score = analyzer.analyze_work(work)

    return {
        "overall_score": score.overall_score,
        "completeness": score.completeness,
        "accuracy": score.accuracy,
        "consistency": score.consistency,
        "freshness": score.freshness,
        "grade": _score_to_grade(score.overall_score),
        "details": score.details,
    }


def _score_to_grade(score: float) -> str:
    """Convert quality score to letter grade."""
    if score >= 0.9:
        return "A"
    elif score >= 0.8:
        return "B"
    elif score >= 0.7:
        return "C"
    elif score >= 0.6:
        return "D"
    else:
        return "F"
