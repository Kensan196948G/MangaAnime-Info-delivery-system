#!/usr/bin/env python3
"""
Enhanced filtering logic module with advanced features.

This module extends filter_logic.py with:
- Dynamic config.json-based NG keyword management
- Genre-based filtering with flexible rules
- Tag-based filtering with priority levels
- User-defined custom filter rules
- Filter performance optimization
- Audit logging for filtered content
"""

import logging
import re
import json
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from functools import lru_cache

from .models import Work


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
    action: FilterAction
    confidence: float  # 0.0 to 1.0
    matched_rules: List[FilterRule] = field(default_factory=list)
    matched_keywords: List[str] = field(default_factory=list)
    matched_genres: List[str] = field(default_factory=list)
    matched_tags: List[str] = field(default_factory=list)
    reason: str = ""
    review_notes: str = ""


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
        """
        Add new NG keyword.

        Args:
            keyword: Keyword to add

        Returns:
            True if added successfully
        """
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
        """
        Remove NG keyword.

        Args:
            keyword: Keyword to remove

        Returns:
            True if removed successfully
        """
        keyword = keyword.lower().strip()

        if keyword in self.ng_keywords:
            self.ng_keywords.remove(keyword)

            # Update config
            filtering_config = self.config.get("filtering", {})
            keywords_list = filtering_config.get("ng_keywords", [])
            filtering_config["ng_keywords"] = [
                k for k in keywords_list if k.lower() != keyword
            ]
            self._save_config()

            self.logger.info(f"Removed NG keyword: {keyword}")
            return True

        return False

    def add_custom_rule(self, rule: FilterRule) -> bool:
        """
        Add custom filter rule.

        Args:
            rule: Filter rule to add

        Returns:
            True if added successfully
        """
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
                    tag_name = (
                        tag.get("name", tag) if isinstance(tag, dict) else str(tag)
                    )
                    if tag_name.lower() in self.config_manager.exclude_tags:
                        matched_tags.append(tag_name)
                        self.filter_stats["tags"] += 1

        # Check custom rules
        for rule in self.config_manager.get_active_rules():
            if self._check_custom_rule(work, rule):
                matched_rules.append(rule)
                self.filter_stats["custom_rules"] += 1

        # Determine filter action
        is_filtered = bool(
            matched_keywords or matched_genres or matched_tags or matched_rules
        )

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
            pattern = re.compile(
                rule.pattern, re.IGNORECASE if not rule.case_sensitive else 0
            )

            for target in rule.targets:
                text = ""

                if target == "title":
                    text = work.title
                elif target == "description":
                    text = (work.metadata or {}).get("description", "")
                elif target in work.metadata:
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


# Convenience functions


def create_enhanced_filter(config_path: Optional[str] = None) -> EnhancedContentFilter:
    """Create enhanced content filter instance."""
    return EnhancedContentFilter(config_path=config_path)


def filter_works(
    works: List[Work], config_path: Optional[str] = None
) -> Tuple[List[Work], List[Work]]:
    """
    Filter list of works.

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
