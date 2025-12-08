#!/usr/bin/env python3
"""
Enhanced data normalization and integration module.

This module extends data_normalizer.py with:
- Advanced duplicate detection using fuzzy matching
- Improved title normalization with language detection
- Multi-source data merging strategies
- Confidence scoring for matches
- Database-backed deduplication
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from difflib import SequenceMatcher
from enum import Enum
from typing import Any, Dict, List, Optional, Set

import jellyfish  # For phonetic matching (install: pip install jellyfish)

from .data_normalizer import DataQualityAnalyzer, NormalizationLevel, TitleNormalizer
from .models import DataSource, Work


class MatchAlgorithm(Enum):
    """Match algorithm types."""

    EXACT = "exact"
    NORMALIZED = "normalized"
    FUZZY = "fuzzy"
    PHONETIC = "phonetic"
    HYBRID = "hybrid"


@dataclass
class DuplicateMatch:
    """Duplicate detection match result."""

    work1_id: int
    work2_id: int
    confidence: float  # 0.0 to 1.0
    match_type: MatchAlgorithm
    title_similarity: float
    metadata_similarity: float
    recommended_action: str  # "merge", "keep_separate", "review"
    reason: str


@dataclass
class MergeStrategy:
    """Data merging strategy."""

    prefer_source: Optional[DataSource] = None
    prefer_newer: bool = True
    prefer_more_complete: bool = True
    merge_metadata: bool = True


class EnhancedDuplicateDetector:
    """
    Enhanced duplicate work detection with multiple algorithms.

    Features:
    - Exact title matching
    - Normalized title matching
    - Fuzzy string matching (Levenshtein distance)
    - Phonetic matching (Metaphone, Soundex)
    - Hybrid multi-algorithm approach
    - Confidence scoring
    """

    def __init__(
        self,
        exact_threshold: float = 1.0,
        fuzzy_threshold: float = 0.85,
        phonetic_threshold: float = 0.80,
    ):
        """
        Initialize duplicate detector.

        Args:
            exact_threshold: Threshold for exact matches (1.0 = perfect match)
            fuzzy_threshold: Threshold for fuzzy matches (0.0-1.0)
            phonetic_threshold: Threshold for phonetic matches (0.0-1.0)
        """
        self.exact_threshold = exact_threshold
        self.fuzzy_threshold = fuzzy_threshold
        self.phonetic_threshold = phonetic_threshold

        self.title_normalizer = TitleNormalizer()
        self.quality_analyzer = DataQualityAnalyzer()
        self.logger = logging.getLogger(__name__)

        self.logger.info(
            "Enhanced Duplicate Detector initialized: "
            f"fuzzy={fuzzy_threshold}, phonetic={phonetic_threshold}"
        )

    def calculate_title_similarity(
        self,
        title1: str,
        title2: str,
        algorithm: MatchAlgorithm = MatchAlgorithm.HYBRID,
    ) -> float:
        """
        Calculate similarity between two titles.

        Args:
            title1: First title
            title2: Second title
            algorithm: Matching algorithm to use

        Returns:
            Similarity score (0.0 to 1.0)
        """
        if not title1 or not title2:
            return 0.0

        if algorithm == MatchAlgorithm.EXACT:
            return 1.0 if title1 == title2 else 0.0

        elif algorithm == MatchAlgorithm.NORMALIZED:
            norm1 = self.title_normalizer.normalize_title(title1, NormalizationLevel.STRICT)
            norm2 = self.title_normalizer.normalize_title(title2, NormalizationLevel.STRICT)
            return 1.0 if norm1 == norm2 else 0.0

        elif algorithm == MatchAlgorithm.FUZZY:
            # Use Levenshtein distance ratio
            return SequenceMatcher(None, title1.lower(), title2.lower()).ratio()

        elif algorithm == MatchAlgorithm.PHONETIC:
            # Use phonetic matching (for English/Romaji)
            try:
                metaphone1 = jellyfish.metaphone(title1)
                metaphone2 = jellyfish.metaphone(title2)
                return 1.0 if metaphone1 == metaphone2 else 0.0
            except:
                return 0.0

        elif algorithm == MatchAlgorithm.HYBRID:
            # Combine multiple algorithms
            scores = []

            # Exact match
            if title1 == title2:
                return 1.0

            # Normalized match
            norm1 = self.title_normalizer.normalize_title(title1, NormalizationLevel.STRICT)
            norm2 = self.title_normalizer.normalize_title(title2, NormalizationLevel.STRICT)
            if norm1 == norm2:
                scores.append(1.0)
            else:
                # Fuzzy on normalized
                scores.append(SequenceMatcher(None, norm1.lower(), norm2.lower()).ratio())

            # Fuzzy on original
            scores.append(SequenceMatcher(None, title1.lower(), title2.lower()).ratio())

            # Phonetic (if applicable)
            try:
                if self._is_latin_script(title1) and self._is_latin_script(title2):
                    metaphone1 = jellyfish.metaphone(title1)
                    metaphone2 = jellyfish.metaphone(title2)
                    if metaphone1 == metaphone2:
                        scores.append(1.0)
            except:
                pass

            # Return weighted average
            if scores:
                return sum(scores) / len(scores)
            else:
                return 0.0

        return 0.0

    def _is_latin_script(self, text: str) -> bool:
        """Check if text is primarily Latin script."""
        if not text:
            return False

        latin_chars = sum(1 for c in text if ord(c) < 128)
        return latin_chars / len(text) > 0.7

    def detect_duplicate(
        self,
        work1: Work,
        work2: Work,
        algorithm: MatchAlgorithm = MatchAlgorithm.HYBRID,
    ) -> Optional[DuplicateMatch]:
        """
        Detect if two works are duplicates.

        Args:
            work1: First work
            work2: Second work
            algorithm: Matching algorithm

        Returns:
            DuplicateMatch if duplicate detected, None otherwise
        """
        # Skip if different types
        if work1.work_type != work2.work_type:
            return None

        # Calculate title similarity
        title_sim = self.calculate_title_similarity(work1.title, work2.title, algorithm)

        # Check alternate titles if available
        max_title_sim = title_sim

        if work1.title_en and work2.title_en:
            en_sim = self.calculate_title_similarity(work1.title_en, work2.title_en, algorithm)
            max_title_sim = max(max_title_sim, en_sim)

        if work1.title_kana and work2.title_kana:
            kana_sim = self.calculate_title_similarity(
                work1.title_kana, work2.title_kana, algorithm
            )
            max_title_sim = max(max_title_sim, kana_sim)

        # Calculate metadata similarity
        metadata_sim = self._calculate_metadata_similarity(work1, work2)

        # Compute overall confidence
        confidence = (max_title_sim * 0.7) + (metadata_sim * 0.3)

        # Determine if duplicate
        if confidence >= self.fuzzy_threshold:
            match_type = algorithm
            if confidence >= self.exact_threshold:
                match_type = MatchAlgorithm.EXACT

            # Recommend action
            if confidence >= 0.95:
                action = "merge"
                reason = "High confidence duplicate"
            elif confidence >= 0.85:
                action = "review"
                reason = "Likely duplicate, manual review recommended"
            else:
                action = "keep_separate"
                reason = "Low confidence, likely different works"

            return DuplicateMatch(
                work1_id=work1.id or 0,
                work2_id=work2.id or 0,
                confidence=confidence,
                match_type=match_type,
                title_similarity=max_title_sim,
                metadata_similarity=metadata_sim,
                recommended_action=action,
                reason=reason,
            )

        return None

    def _calculate_metadata_similarity(self, work1: Work, work2: Work) -> float:
        """Calculate similarity based on metadata."""
        similarity_score = 0.0
        factors = 0

        # Official URL similarity
        if work1.official_url and work2.official_url:
            factors += 1
            if work1.official_url == work2.official_url:
                similarity_score += 1.0

        # Work type (should already match, but check anyway)
        if work1.work_type == work2.work_type:
            factors += 1
            similarity_score += 1.0

        # Metadata comparison
        meta1 = work1.metadata or {}
        meta2 = work2.metadata or {}

        # Compare specific metadata fields
        comparable_fields = ["anilist_id", "description", "genres", "status"]

        for field in comparable_fields:
            if field in meta1 and field in meta2:
                factors += 1
                if meta1[field] == meta2[field]:
                    similarity_score += 1.0

        return similarity_score / factors if factors > 0 else 0.0

    def find_duplicates_in_list(
        self, works: List[Work], algorithm: MatchAlgorithm = MatchAlgorithm.HYBRID
    ) -> List[DuplicateMatch]:
        """
        Find all duplicates in a list of works.

        Args:
            works: List of works to check
            algorithm: Matching algorithm

        Returns:
            List of duplicate matches
        """
        duplicates = []

        for i in range(len(works)):
            for j in range(i + 1, len(works)):
                match = self.detect_duplicate(works[i], works[j], algorithm)
                if match:
                    duplicates.append(match)

        self.logger.info(f"Found {len(duplicates)} duplicate pairs in {len(works)} works")
        return duplicates


class EnhancedDataMerger:
    """
    Enhanced data merger with intelligent conflict resolution.

    Features:
    - Source preference handling
    - Completeness-based selection
    - Timestamp-based selection
    - Metadata merging with conflict resolution
    """

    def __init__(self, strategy: Optional[MergeStrategy] = None):
        """
        Initialize data merger.

        Args:
            strategy: Merge strategy configuration
        """
        self.strategy = strategy or MergeStrategy()
        self.quality_analyzer = DataQualityAnalyzer()
        self.logger = logging.getLogger(__name__)

    def merge_works(self, work1: Work, work2: Work) -> Work:
        """
        Merge two duplicate works into one.

        Args:
            work1: First work
            work2: Second work

        Returns:
            Merged work
        """
        # Analyze quality of both works
        quality1 = self.quality_analyzer.analyze_work(work1)
        quality2 = self.quality_analyzer.analyze_work(work2)

        # Determine primary work based on strategy
        if self.strategy.prefer_more_complete:
            primary = work1 if quality1.completeness >= quality2.completeness else work2
            secondary = work2 if primary == work1 else work1
        elif self.strategy.prefer_newer:
            primary = (
                work1
                if (work1.created_at or datetime.min) >= (work2.created_at or datetime.min)
                else work2
            )
            secondary = work2 if primary == work1 else work1
        else:
            primary = work1
            secondary = work2

        # Merge fields
        merged = Work(
            title=primary.title,
            work_type=primary.work_type,
            id=primary.id or secondary.id,
            title_kana=primary.title_kana or secondary.title_kana,
            title_en=primary.title_en or secondary.title_en,
            official_url=primary.official_url or secondary.official_url,
            created_at=primary.created_at or secondary.created_at,
            metadata=(
                self._merge_metadata(primary.metadata or {}, secondary.metadata or {})
                if self.strategy.merge_metadata
                else primary.metadata
            ),
        )

        self.logger.debug(f"Merged works: '{primary.title}' + '{secondary.title}'")
        return merged

    def _merge_metadata(self, meta1: Dict[str, Any], meta2: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge metadata dictionaries with conflict resolution.

        Args:
            meta1: First metadata dict
            meta2: Second metadata dict

        Returns:
            Merged metadata
        """
        merged = meta1.copy()

        for key, value in meta2.items():
            if key not in merged:
                # Add missing key
                merged[key] = value
            elif isinstance(value, list) and isinstance(merged[key], list):
                # Merge lists (remove duplicates)
                merged[key] = list(set(merged[key] + value))
            elif isinstance(value, dict) and isinstance(merged[key], dict):
                # Recursively merge dicts
                merged[key] = self._merge_metadata(merged[key], value)
            # For other types, keep existing value (meta1 has priority)

        return merged

    def deduplicate_works(
        self, works: List[Work], detector: EnhancedDuplicateDetector
    ) -> List[Work]:
        """
        Deduplicate a list of works by detecting and merging duplicates.

        Args:
            works: List of works
            detector: Duplicate detector instance

        Returns:
            Deduplicated list of works
        """
        if not works:
            return []

        # Find duplicates
        duplicates = detector.find_duplicates_in_list(works)

        # Build merge groups
        merge_groups: Dict[int, Set[int]] = {}

        for dup in duplicates:
            if dup.recommended_action == "merge":
                idx1 = dup.work1_id
                idx2 = dup.work2_id

                # Find existing groups
                group1 = merge_groups.get(idx1, {idx1})
                group2 = merge_groups.get(idx2, {idx2})

                # Merge groups
                merged_group = group1 | group2

                for idx in merged_group:
                    merge_groups[idx] = merged_group

        # Merge works in each group
        deduplicated = []
        processed = set()

        for i, work in enumerate(works):
            if i in processed:
                continue

            group = merge_groups.get(i, {i})

            if len(group) == 1:
                # No duplicates
                deduplicated.append(work)
            else:
                # Merge all works in group
                group_works = [works[j] for j in group if j < len(works)]
                merged = group_works[0]

                for other_work in group_works[1:]:
                    merged = self.merge_works(merged, other_work)

                deduplicated.append(merged)

            processed.update(group)

        self.logger.info(f"Deduplicated {len(works)} works to {len(deduplicated)} unique works")

        return deduplicated


# Convenience functions


def detect_duplicates(works: List[Work], threshold: float = 0.85) -> List[DuplicateMatch]:
    """
    Detect duplicates in a list of works.

    Args:
        works: List of works
        threshold: Fuzzy match threshold

    Returns:
        List of duplicate matches
    """
    detector = EnhancedDuplicateDetector(fuzzy_threshold=threshold)
    return detector.find_duplicates_in_list(works)


def deduplicate_works(
    works: List[Work],
    threshold: float = 0.85,
    merge_strategy: Optional[MergeStrategy] = None,
) -> List[Work]:
    """
    Deduplicate and merge works.

    Args:
        works: List of works
        threshold: Fuzzy match threshold
        merge_strategy: Merge strategy

    Returns:
        Deduplicated works
    """
    detector = EnhancedDuplicateDetector(fuzzy_threshold=threshold)
    merger = EnhancedDataMerger(merge_strategy)
    return merger.deduplicate_works(works, detector)


def merge_two_works(work1: Work, work2: Work) -> Work:
    """
    Merge two works into one.

    Args:
        work1: First work
        work2: Second work

    Returns:
        Merged work
    """
    merger = EnhancedDataMerger()
    return merger.merge_works(work1, work2)
