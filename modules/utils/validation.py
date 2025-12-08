"""
Data validation utilities for MangaAnime Info Delivery System.

Provides common validation functions to eliminate code duplication.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional


def is_valid_email(email: str) -> bool:
    """
    Validate email address format.

    Args:
        email: Email address to validate

    Returns:
        True if valid, False otherwise
    """
    if not email:
        return False

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None


def is_valid_url(url: str) -> bool:
    """
    Validate URL format.

    Args:
        url: URL to validate

    Returns:
        True if valid, False otherwise
    """
    if not url:
        return False

    pattern = r"^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$"
    return re.match(pattern, url) is not None


def is_valid_date(date_str: str, format: str = "%Y-%m-%d") -> bool:
    """
    Validate date string.

    Args:
        date_str: Date string to validate
        format: Expected date format

    Returns:
        True if valid, False otherwise
    """
    if not date_str:
        return False

    try:
        datetime.strptime(date_str, format)
        return True
    except ValueError:
        return False


def sanitize_string(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize string input.

    Args:
        text: Text to sanitize
        max_length: Maximum length (truncate if exceeded)

    Returns:
        Sanitized string
    """
    if not text:
        return ""

    # Remove control characters
    sanitized = "".join(char for char in text if ord(char) >= 32 or char in "\n\t")

    # Strip whitespace
    sanitized = sanitized.strip()

    # Truncate if needed
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    return sanitized


def validate_work_type(work_type: str) -> bool:
    """
    Validate work type.

    Args:
        work_type: Work type to validate

    Returns:
        True if valid, False otherwise
    """
    valid_types = ["anime", "manga"]
    return work_type.lower() in valid_types


def validate_release_type(release_type: str) -> bool:
    """
    Validate release type.

    Args:
        release_type: Release type to validate

    Returns:
        True if valid, False otherwise
    """
    valid_types = ["episode", "volume", "chapter"]
    return release_type.lower() in valid_types


def contains_ng_keywords(text: str, ng_keywords: List[str]) -> bool:
    """
    Check if text contains any NG keywords.

    Args:
        text: Text to check
        ng_keywords: List of NG keywords

    Returns:
        True if contains NG keywords, False otherwise
    """
    if not text or not ng_keywords:
        return False

    text_lower = text.lower()
    return any(keyword.lower() in text_lower for keyword in ng_keywords)


def validate_work_data(data: Dict[str, Any]) -> List[str]:
    """
    Validate work data dictionary.

    Args:
        data: Work data dictionary

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Required fields
    if not data.get("title"):
        errors.append("Title is required")

    if not data.get("type"):
        errors.append("Type is required")
    elif not validate_work_type(data["type"]):
        errors.append("Invalid work type")

    # Optional URL validation
    if data.get("official_url") and not is_valid_url(data["official_url"]):
        errors.append("Invalid official URL format")

    return errors


def validate_release_data(data: Dict[str, Any]) -> List[str]:
    """
    Validate release data dictionary.

    Args:
        data: Release data dictionary

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Required fields
    if not data.get("work_id"):
        errors.append("Work ID is required")

    if not data.get("release_type"):
        errors.append("Release type is required")
    elif not validate_release_type(data["release_type"]):
        errors.append("Invalid release type")

    # Date validation
    if data.get("release_date") and not is_valid_date(data["release_date"]):
        errors.append("Invalid release date format")

    # URL validation
    if data.get("source_url") and not is_valid_url(data["source_url"]):
        errors.append("Invalid source URL format")

    return errors


def is_valid_platform(platform: str) -> bool:
    """
    Validate streaming/publication platform.

    Args:
        platform: Platform name

    Returns:
        True if valid, False otherwise
    """
    valid_platforms = [
        "netflix",
        "amazon",
        "prime",
        "crunchyroll",
        "funimation",
        "hulu",
        "danime",
        "abema",
        "niconico",
        "bandai",
        "bookwalker",
        "kindle",
        "kobo",
        "jump",
        "magazine",
        "sunday",
        "weekly",
    ]

    if not platform:
        return False

    platform_lower = platform.lower()
    return any(valid in platform_lower for valid in valid_platforms)


def validate_config_data(config: Dict[str, Any]) -> List[str]:
    """
    Validate configuration data.

    Args:
        config: Configuration dictionary

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Database path
    if not config.get("database", {}).get("path"):
        errors.append("Database path is required")

    # Email configuration
    email_config = config.get("email", {})
    if email_config.get("sender") and not is_valid_email(email_config["sender"]):
        errors.append("Invalid sender email address")

    if email_config.get("recipient") and not is_valid_email(email_config["recipient"]):
        errors.append("Invalid recipient email address")

    # API URLs
    apis = config.get("apis", {})
    if apis.get("anilist_url") and not is_valid_url(apis["anilist_url"]):
        errors.append("Invalid AniList API URL")

    if apis.get("syoboi_url") and not is_valid_url(apis["syoboi_url"]):
        errors.append("Invalid Syoboi API URL")

    return errors


def safe_int(value: Any, default: int = 0) -> int:
    """
    Safely convert value to integer.

    Args:
        value: Value to convert
        default: Default value if conversion fails

    Returns:
        Integer value or default
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Safely convert value to float.

    Args:
        value: Value to convert
        default: Default value if conversion fails

    Returns:
        Float value or default
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_bool(value: Any, default: bool = False) -> bool:
    """
    Safely convert value to boolean.

    Args:
        value: Value to convert
        default: Default value if conversion fails

    Returns:
        Boolean value or default
    """
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")

    if isinstance(value, (int, float)):
        return bool(value)

    return default


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix


def normalize_platform_name(platform: str) -> str:
    """
    Normalize platform name for consistency.

    Args:
        platform: Platform name

    Returns:
        Normalized platform name
    """
    if not platform:
        return ""

    # Common normalizations
    normalizations = {
        "amazon prime": "Amazon Prime",
        "prime video": "Amazon Prime",
        "crunchyroll": "Crunchyroll",
        "funimation": "Funimation",
        "hulu": "Hulu",
        "netflix": "Netflix",
        "d anime": "dアニメストア",
        "danime": "dアニメストア",
        "abematv": "ABEMA",
        "abema": "ABEMA",
        "niconico": "ニコニコ動画",
        "bookwalker": "BookWalker",
        "kindle": "Kindle",
        "kobo": "Kobo",
    }

    platform_lower = platform.lower().strip()

    for key, value in normalizations.items():
        if key in platform_lower:
            return value

    # Default: capitalize first letter
    return platform.strip().title()
