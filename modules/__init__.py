"""
Anime/Manga Information Delivery System - Modules Package

This package contains the core backend modules for the anime/manga information
delivery system, including database management, data collection from various
sources, and configuration management.

Main Components:
- db: SQLite database management with CRUD operations
- models: Data models and validation utilities
- config: Configuration management with JSON and environment variable support
- anime_anilist: AniList GraphQL API integration for anime data
- manga_rss: RSS feed processing for manga and anime releases

Usage:
    from modules import get_db, get_config
    from modules.anime_anilist import AniListCollector
    from modules.manga_rss import RSSCollector
    from modules.models import Work, Release, WorkType, ReleaseType
"""

from .config import ConfigManager, get_config, load_config_file
# Import main components for easy access
from .db import DatabaseManager, get_db
from .models import (AniListWork, DataNormalizer, DataSource, DataValidator,
                     Release, ReleaseType, RSSFeedItem, Work, WorkType)

# Version information
__version__ = "1.0.0"
__author__ = "MangaAnime-DevAPI Agent"
__description__ = (
    "Backend API and database functionality for Anime/Manga information delivery system"
)

# Package metadata
__all__ = [
    # Database
    "DatabaseManager",
    "get_db",
    # Configuration
    "ConfigManager",
    "get_config",
    "load_config_file",
    # Models
    "Work",
    "Release",
    "AniListWork",
    "RSSFeedItem",
    "WorkType",
    "ReleaseType",
    "DataSource",
    "DataValidator",
    "DataNormalizer",
    # Version info
    "__version__",
    "__author__",
    "__description__",
]


def initialize_system(config_path=None):
    """
    Initialize the system with configuration and database.

    Args:
        config_path: Optional path to configuration file

    Returns:
        Tuple of (config_manager, database_manager)
    """
    # Initialize configuration
    config = get_config(config_path)

    # Initialize database with config
    config.get_database_config()
    db = get_db()

    # Ensure database is initialized
    db.initialize_database()

    return config, db


def get_system_info():
    """
    Get system information and status.

    Returns:
        Dictionary with system information
    """
    config = get_config()
    db = get_db()

    # Get database statistics
    db_stats = db.get_work_stats()

    # Get configuration info
    system_config = config.get_system_config()

    return {
        "version": __version__,
        "description": __description__,
        "system": {
            "name": system_config.name,
            "version": system_config.version,
            "environment": system_config.environment,
            "timezone": system_config.timezone,
        },
        "database": {"path": config.get("database.path"), "statistics": db_stats},
        "configuration": {
            "loaded_from": config._loaded_from,
            "sections": list(config._config_data.keys()),
        },
    }


# Lazy imports for optional components (to avoid import errors if dependencies are missing)
def get_anilist_collector(config=None):
    """
    Get AniList collector instance (lazy import).

    Args:
        config: Optional configuration dictionary

    Returns:
        AniListCollector instance
    """
    try:
        from .anime_anilist import AniListCollector

        return AniListCollector(config)
    except ImportError as e:
        raise ImportError(f"AniList dependencies not available: {e}")


def get_rss_collector(config=None):
    """
    Get RSS collector instance (lazy import).

    Args:
        config: Optional configuration dictionary

    Returns:
        RSSCollector instance
    """
    try:
        from .manga_rss import RSSCollector

        return RSSCollector(config)
    except ImportError as e:
        raise ImportError(f"RSS dependencies not available: {e}")


# Add lazy import functions to __all__
__all__.extend(
    [
        "initialize_system",
        "get_system_info",
        "get_anilist_collector",
        "get_rss_collector",
    ]
)
