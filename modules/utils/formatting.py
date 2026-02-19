"""
Data formatting utilities for MangaAnime Info Delivery System.

Provides common formatting functions to eliminate code duplication.
"""

import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def format_date(
    date_obj: Optional[datetime | date | str], format: str = "%Y-%m-%d", default: str = ""
) -> str:
    """
    Format date object to string.

    Args:
        date_obj: Date object or string
        format: Output format
        default: Default value if formatting fails

    Returns:
        Formatted date string
    """
    if not date_obj:
        return default

    try:
        if isinstance(date_obj, str):
            # Try to parse string to datetime
            date_obj = datetime.fromisoformat(date_obj.replace("Z", "+00:00"))

        if isinstance(date_obj, datetime):
            return date_obj.strftime(format)
        elif isinstance(date_obj, date):
            return date_obj.strftime(format)

    except (ValueError, AttributeError) as e:
        logger.warning(f"Date formatting error: {e}")

    return default


def format_datetime(
    dt: Optional[datetime | str], format: str = "%Y-%m-%d %H:%M:%S", default: str = ""
) -> str:
    """
    Format datetime object to string.

    Args:
        dt: Datetime object or string
        format: Output format
        default: Default value if formatting fails

    Returns:
        Formatted datetime string
    """
    return format_date(dt, format, default)


def format_japanese_date(date_obj: Optional[datetime | date | str]) -> str:
    """
    Format date in Japanese style.

    Args:
        date_obj: Date object or string

    Returns:
        Japanese formatted date (e.g., "2025年12月8日")
    """
    formatted = format_date(date_obj, "%Y年%m月%d日")
    if formatted:
        # Remove leading zeros from month and day
        formatted = formatted.replace("年0", "年").replace("月0", "月")
    return formatted


def format_relative_time(dt: datetime | str, reference: Optional[datetime] = None) -> str:
    """
    Format datetime as relative time (e.g., "2 hours ago").

    Args:
        dt: Datetime object or string
        reference: Reference datetime (defaults to now)

    Returns:
        Relative time string
    """
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        except ValueError:
            return ""

    if not isinstance(dt, datetime):
        return ""

    if reference is None:
        reference = datetime.now()

    diff = reference - dt

    if diff.total_seconds() < 60:
        return "たった今"
    elif diff.total_seconds() < 3600:
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes}分前"
    elif diff.total_seconds() < 86400:
        hours = int(diff.total_seconds() / 3600)
        return f"{hours}時間前"
    elif diff.days < 7:
        return f"{diff.days}日前"
    elif diff.days < 30:
        weeks = diff.days // 7
        return f"{weeks}週間前"
    elif diff.days < 365:
        months = diff.days // 30
        return f"{months}ヶ月前"
    else:
        years = diff.days // 365
        return f"{years}年前"


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string (e.g., "1.5 MB")
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024**2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024**3:
        return f"{size_bytes / (1024 ** 2):.1f} MB"
    else:
        return f"{size_bytes / (1024 ** 3):.1f} GB"


def format_number(number: int | float, locale: str = "ja") -> str:
    """
    Format number with thousand separators.

    Args:
        number: Number to format
        locale: Locale for formatting ('ja' or 'en')

    Returns:
        Formatted number string
    """
    if locale == "ja":
        return f"{number:,}"
    else:
        return f"{number:,}"


def format_percentage(value: float, decimals: int = 1) -> str:
    """
    Format value as percentage.

    Args:
        value: Value between 0 and 1 (or 0 and 100)
        decimals: Number of decimal places

    Returns:
        Formatted percentage string
    """
    # Assume value is 0-1 if less than 1, otherwise 0-100
    if value <= 1.0:
        percentage = value * 100
    else:
        percentage = value

    return f"{percentage:.{decimals}f}%"


def format_work_title(
    title: str,
    title_kana: Optional[str] = None,
    title_en: Optional[str] = None,
    include_all: bool = False,
) -> str:
    """
    Format work title with optional readings.

    Args:
        title: Main title
        title_kana: Kana reading
        title_en: English title
        include_all: Include all available titles

    Returns:
        Formatted title string
    """
    if not include_all:
        return title

    parts = [title]

    if title_kana:
        parts.append(f"({title_kana})")

    if title_en:
        parts.append(f"[{title_en}]")

    return " ".join(parts)


def format_release_title(
    work_title: str, release_type: str, number: Optional[str] = None, platform: Optional[str] = None
) -> str:
    """
    Format release title for notifications.

    Args:
        work_title: Work title
        release_type: Release type (episode/volume/chapter)
        number: Episode/volume/chapter number
        platform: Platform name

    Returns:
        Formatted release title
    """
    parts = [work_title]

    type_labels = {
        "episode": "第{number}話",
        "volume": "第{number}巻",
        "chapter": "第{number}話",
    }

    if number and release_type in type_labels:
        label = type_labels[release_type].format(number=number)
        parts.append(label)

    if platform:
        parts.append(f"({platform})")

    return " ".join(parts)


def format_email_subject(
    work_title: str,
    release_type: str,
    number: Optional[str] = None,
    prefix: str = "[アニメ・マンガ情報]",
) -> str:
    """
    Format email subject line.

    Args:
        work_title: Work title
        release_type: Release type
        number: Episode/volume number
        prefix: Subject prefix

    Returns:
        Formatted email subject
    """
    release_info = format_release_title(work_title, release_type, number)
    return f"{prefix} {release_info}"


def format_calendar_title(work_title: str, release_type: str, number: Optional[str] = None) -> str:
    """
    Format calendar event title.

    Args:
        work_title: Work title
        release_type: Release type
        number: Episode/volume number

    Returns:
        Formatted calendar title
    """
    return format_release_title(work_title, release_type, number)


def format_platform_list(platforms: List[str]) -> str:
    """
    Format list of platforms.

    Args:
        platforms: List of platform names

    Returns:
        Formatted platform string
    """
    if not platforms:
        return ""

    if len(platforms) == 1:
        return platforms[0]

    return "、".join(platforms)


def format_json_pretty(data: Dict[str, Any], indent: int = 2) -> str:
    """
    Format JSON data for pretty printing.

    Args:
        data: Data dictionary
        indent: Indentation spaces

    Returns:
        Pretty formatted JSON string
    """
    import json

    try:
        return json.dumps(data, ensure_ascii=False, indent=indent)
    except (TypeError, ValueError) as e:
        logger.error(f"JSON formatting error: {e}")
        return str(data)


def format_log_message(level: str, message: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    Format log message with context.

    Args:
        level: Log level
        message: Log message
        context: Additional context data

    Returns:
        Formatted log message
    """
    parts = [f"[{level}]", message]

    if context:
        context_str = " | ".join(f"{k}={v}" for k, v in context.items())
        parts.append(f"({context_str})")

    return " ".join(parts)


def format_error_message(error: Exception, include_type: bool = True) -> str:
    """
    Format error message.

    Args:
        error: Exception object
        include_type: Whether to include error type

    Returns:
        Formatted error message
    """
    if include_type:
        return f"{type(error).__name__}: {str(error)}"
    else:
        return str(error)


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human-readable format.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string
    """
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}秒"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        secs = int(seconds % 60)
        return f"{minutes}分{secs}秒"
    else:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours}時間{minutes}分"


def format_table_row(
    data: Dict[str, Any], columns: List[str], widths: Optional[Dict[str, int]] = None
) -> str:
    """
    Format data as table row.

    Args:
        data: Data dictionary
        columns: Column names
        widths: Column widths

    Returns:
        Formatted table row string
    """
    if widths is None:
        widths = {}

    cells = []
    for col in columns:
        value = str(data.get(col, ""))
        width = widths.get(col, len(value))
        cells.append(value.ljust(width))

    return " | ".join(cells)


def format_success_message(message: str, icon: str = "✓") -> str:
    """
    Format success message.

    Args:
        message: Message text
        icon: Success icon

    Returns:
        Formatted success message
    """
    return f"{icon} {message}"


def format_error_response(error: str, code: Optional[str] = None) -> str:
    """
    Format error response message.

    Args:
        error: Error message
        code: Error code

    Returns:
        Formatted error response
    """
    if code:
        return f"[{code}] {error}"
    else:
        return f"エラー: {error}"
