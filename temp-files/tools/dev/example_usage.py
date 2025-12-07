#!/usr/bin/env python3
"""
Backend API Usage Example

This script demonstrates how to use the implemented backend functionality
for the Anime/Manga information delivery system.

Features demonstrated:
- System initialization
- Configuration management
- Database operations
- Data collection simulation
- Work and release management
"""

import sys
import os

# Add modules to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules import (
    initialize_system,
    get_config,
    get_db,
    get_system_info,
    Work,
    Release,
    WorkType,
    ReleaseType,
    DataSource,
    get_anilist_collector,
    get_rss_collector,
)


def demo_system_initialization():
    """Demonstrate system initialization."""
    print("=== System Initialization ===")

    # Initialize the system
    config, db = initialize_system()
    print("✓ System initialized")
    print(f"  - Config loaded from: {config._loaded_from}")
    print(f"  - Database path: {config.get('database.path')}")

    # Get system information
    system_info = get_system_info()
    print("✓ System info:")
    print(f"  - Name: {system_info['system']['name']}")
    print(f"  - Version: {system_info['version']}")
    print(f"  - Environment: {system_info['system']['environment']}")

    return config, db


def demo_database_operations(db):
    """Demonstrate database CRUD operations."""
    print("\n=== Database Operations ===")

    # Create anime works
    anime_works = [
        {
            "title": "Attack on Titan Final Season",
            "work_type": "anime",
            "title_en": "Attack on Titan Final Season",
            "title_kana": "シンゲキノキョジン",
            "official_url": "https://shingeki.tv/",
        },
        {
            "title": "Demon Slayer Season 3",
            "work_type": "anime",
            "title_en": "Demon Slayer: Kimetsu no Yaiba",
            "title_kana": "キメツノヤイバ",
        },
    ]

    anime_work_ids = []
    for work_data in anime_works:
        work_id = db.create_work(**work_data)
        anime_work_ids.append(work_id)
        print(f"✓ Created anime: {work_data['title']} (ID: {work_id})")

    # Create manga works
    manga_works = [
        {
            "title": "One Piece",
            "work_type": "manga",
            "title_en": "One Piece",
            "official_url": "https://one-piece.com/",
        },
        {
            "title": "My Hero Academia",
            "work_type": "manga",
            "title_en": "My Hero Academia",
            "title_kana": "ボクノヒーローアカデミア",
        },
    ]

    manga_work_ids = []
    for work_data in manga_works:
        work_id = db.create_work(**work_data)
        manga_work_ids.append(work_id)
        print(f"✓ Created manga: {work_data['title']} (ID: {work_id})")

    # Create releases for anime (episodes)
    for i, work_id in enumerate(anime_work_ids):
        for episode_num in range(1, 4):  # 3 episodes each
            release_id = db.create_release(
                work_id=work_id,
                release_type="episode",
                number=str(episode_num),
                platform="Crunchyroll" if i == 0 else "Funimation",
                release_date=date.today().isoformat(),
                source="demo_data",
                source_url=f"https://example.com/episode/{episode_num}",
            )
            print(f"  - Added episode {episode_num} (Release ID: {release_id})")

    # Create releases for manga (volumes)
    for i, work_id in enumerate(manga_work_ids):
        for volume_num in range(1, 3):  # 2 volumes each
            release_id = db.create_release(
                work_id=work_id,
                release_type="volume",
                number=str(volume_num),
                platform="BookWalker" if i == 0 else "Amazon Kindle",
                release_date=date.today().isoformat(),
                source="demo_data",
                source_url=f"https://example.com/volume/{volume_num}",
            )
            print(f"  - Added volume {volume_num} (Release ID: {release_id})")

    return anime_work_ids, manga_work_ids


def demo_data_models():
    """Demonstrate data model usage."""
    print("\n=== Data Models ===")

    # Create Work models
    work1 = Work(
        title="Jujutsu Kaisen",
        work_type=WorkType.ANIME,
        title_en="Jujutsu Kaisen",
        title_kana="ジュジュツカイセン",
        official_url="https://jujutsukaisen.jp/",
    )
    print(f"✓ Work model: {work1.title} ({work1.work_type.value})")

    # Create Release models
    release1 = Release(
        work_id=1,
        release_type=ReleaseType.EPISODE,
        number="12",
        platform="Netflix",
        release_date=date.today(),
        source=DataSource.ANILIST.value,
    )
    print(
        f"✓ Release model: {release1.release_type.value} {release1.number} on {release1.platform}"
    )

    # Convert to dict for database operations
    work_dict = work1.to_dict()
    release_dict = release1.to_dict()
    print("✓ Converted models to dict format for database storage")

    return work1, release1


def demo_configuration_management(config):
    """Demonstrate configuration management."""
    print("\n=== Configuration Management ===")

    # Access different configuration sections
    db_config = config.get_database_config()
    print(f"✓ Database config: {db_config.path}")

    filtering_config = config.get_filtering_config()
    print(f"✓ NG keywords: {len(filtering_config.ng_keywords)} items")

    system_config = config.get_system_config()
    print(f"✓ System timezone: {system_config.timezone}")

    # Runtime configuration update
    config.update_config("system.log_level", "DEBUG")
    print(f"✓ Updated log level to: {config.get('system.log_level')}")

    # Access nested configuration values
    anilist_url = config.get("apis.anilist.graphql_url")
    rate_limit = config.get("apis.anilist.rate_limit.requests_per_minute", 90)
    print(f"✓ AniList API: {anilist_url} (rate limit: {rate_limit}/min)")


def demo_query_operations(db):
    """Demonstrate database query operations."""
    print("\n=== Query Operations ===")

    # Get statistics
    stats = db.get_work_stats()
    print("✓ Database statistics:")
    for key, value in stats.items():
        print(f"  - {key}: {value}")

    # Get unnotified releases
    unnotified = db.get_unnotified_releases(limit=10)
    print(f"✓ Unnotified releases: {len(unnotified)}")

    if unnotified:
        sample_release = unnotified[0]
        print(
            f"  - Sample: {sample_release['title']} - {sample_release['release_type']} {sample_release.get('number', 'N/A')}"
        )

        # Mark one as notified
        db.mark_release_notified(sample_release["id"])
        print(f"  - Marked release {sample_release['id']} as notified")

    # Search works
    attack_on_titan = db.get_work_by_title("Attack on Titan Final Season", "anime")
    if attack_on_titan:
        print(f"✓ Found work: {attack_on_titan['title']} (ID: {attack_on_titan['id']})")


def demo_data_collection_concepts(config):
    """Demonstrate data collection concepts (without actual API calls)."""
    print("\n=== Data Collection Concepts ===")

    try:
        # Initialize collectors (simulation - no actual API calls)
        config_dict = config.get_all()

        # AniList collector setup
        anilist_collector = get_anilist_collector(config_dict)
        print("✓ AniList collector ready for anime data collection")
        print(f"  - API endpoint: {config.get('apis.anilist.graphql_url')}")
        print(
            f"  - Rate limit: {config.get('apis.anilist.rate_limit.requests_per_minute')}/min"
        )

        # RSS collector setup
        try:
            rss_collector = get_rss_collector(config_dict)
            print("✓ RSS collector ready for manga data collection")
        except ImportError:
            print("⚠ RSS collector needs feedparser dependency")

        # Filtering setup
        filtering_config = config.get_filtering_config()
        print("✓ Content filtering configured:")
        print(f"  - NG keywords: {len(filtering_config.ng_keywords)}")
        print(f"  - NG genres: {len(filtering_config.ng_genres)}")

    except Exception as e:
        print(f"⚠ Data collection setup: {e}")


def demo_work_management_workflow(db):
    """Demonstrate a complete work management workflow."""
    print("\n=== Work Management Workflow ===")

    # Simulate receiving new anime information
    new_anime = {
        "title": "Chainsaw Man",
        "work_type": "anime",
        "title_en": "Chainsaw Man",
        "title_kana": "チェンソーマン",
        "official_url": "https://chainsawman.dog/",
    }

    # Get or create work (avoids duplicates)
    work_id = db.get_or_create_work(**new_anime)
    print(f"✓ Work managed: {new_anime['title']} (ID: {work_id})")

    # Add multiple episodes
    episodes = [
        {"number": "1", "platform": "Crunchyroll", "date": "2024-10-11"},
        {"number": "2", "platform": "Crunchyroll", "date": "2024-10-18"},
        {"number": "3", "platform": "Crunchyroll", "date": "2024-10-25"},
    ]

    for episode in episodes:
        release_id = db.create_release(
            work_id=work_id,
            release_type="episode",
            number=episode["number"],
            platform=episode["platform"],
            release_date=episode["date"],
            source="demo_workflow",
        )
        if release_id:
            print(
                f"  - Episode {episode['number']}: {episode['date']} on {episode['platform']}"
            )

    # Check for new content to notify
    new_releases = db.get_unnotified_releases(limit=5)
    if new_releases:
        print(f"✓ Ready to notify: {len(new_releases)} new releases")
        # In a real system, this would trigger email/calendar notifications


def main():
    """Main demonstration function."""
    print("Backend API Usage Demonstration")
    print("=" * 50)

    try:
        # Initialize system
        config, db = demo_system_initialization()

        # Demonstrate core functionality
        demo_configuration_management(config)
        anime_ids, manga_ids = demo_database_operations(db)
        demo_data_models()
        demo_query_operations(db)
        demo_data_collection_concepts(config)
        demo_work_management_workflow(db)

        # Final statistics
        print("\n=== Final System Status ===")
        stats = db.get_work_stats()
        print(
            f"Total works in database: {sum(v for k, v in stats.items() if k.endswith('_works'))}"
        )
        print(f"Total releases: {stats.get('total_releases', 0)}")
        print(f"Unnotified releases: {stats.get('unnotified_releases', 0)}")

        print("\n🎉 Backend demonstration completed successfully!")
        print("\nNext steps:")
        print("- Install missing dependencies (feedparser, aiohttp, gql)")
        print("- Configure Google API credentials for notifications")
        print("- Set up cron job for automated data collection")
        print("- Implement email and calendar notification modules")

    except Exception as e:
        print(f"\n❌ Demonstration failed: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
