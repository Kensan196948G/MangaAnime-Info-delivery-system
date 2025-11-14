#!/usr/bin/env python3
"""
Integration tests for enhanced backend modules.

Tests:
- Syoboi Calendar API integration
- Enhanced Manga RSS collector
- Streaming platform enhanced collector
- Enhanced data normalizer
- Enhanced content filter
"""

from modules.models import Work, WorkType
from modules.filter_logic_enhanced import (
    ConfigBasedFilterManager,
    EnhancedContentFilter,
    FilterAction,
)
from modules.data_normalizer_enhanced import (
    EnhancedDuplicateDetector,
    EnhancedDataMerger,
)
from modules.streaming_platform_enhanced import (
    EnhancedStreamingCollector,
    StreamingPlatform,
)
from modules.manga_rss_enhanced import (
    EnhancedMangaRSSCollector,
)
from modules.anime_syoboi import (
    SyoboiCalendarClient,
    fetch_syoboi_programs_sync,
)
import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestSyoboiCalendarIntegration:
    """Test Syoboi Calendar API integration."""

    def test_client_initialization(self):
        """Test client initialization."""
        client = SyoboiCalendarClient(timeout=15)
        assert client is not None
        assert client.timeout == 15
        assert client.requests_per_minute == 60

    @pytest.mark.asyncio
    async def test_fetch_recent_programs(self):
        """Test fetching recent programs."""
        client = SyoboiCalendarClient(timeout=15)

        try:
            programs = await client.get_recent_programs(days_ahead=3)
            assert isinstance(programs, list)
            print(f"Fetched {len(programs)} programs from Syoboi Calendar")

            if programs:
                program = programs[0]
                assert hasattr(program, "title")
                assert hasattr(program, "program_id")
                print(f"Sample program: {program.title}")

        except Exception as e:
            pytest.skip(f"Syoboi Calendar API unavailable: {e}")

    def test_synchronous_fetch(self):
        """Test synchronous wrapper."""
        try:
            programs = fetch_syoboi_programs_sync(days_ahead=2)
            assert isinstance(programs, list)
            print(f"Sync fetch: {len(programs)} programs")

        except Exception as e:
            pytest.skip(f"Syoboi Calendar API unavailable: {e}")

    @pytest.mark.asyncio
    async def test_fetch_and_convert(self):
        """Test fetching and converting to Work/Release models."""
        client = SyoboiCalendarClient()

        try:
            works, releases = await client.fetch_and_convert(days_ahead=3)
            assert isinstance(works, list)
            assert isinstance(releases, list)
            print(f"Converted: {len(works)} works, {len(releases)} releases")

        except Exception as e:
            pytest.skip(f"Syoboi Calendar API unavailable: {e}")


class TestEnhancedMangaRSSCollector:
    """Test enhanced manga RSS collector."""

    def test_collector_initialization(self):
        """Test collector initialization."""
        collector = EnhancedMangaRSSCollector()
        assert collector is not None
        assert len(collector.MANGA_SOURCES) > 0
        print(f"Available manga sources: {len(collector.MANGA_SOURCES)}")

    def test_get_all_sources(self):
        """Test getting all sources."""
        collector = EnhancedMangaRSSCollector()
        sources = collector.get_all_sources()
        assert isinstance(sources, list)
        print(f"Enabled sources: {len(sources)}")

        for source in sources:
            print(f"  - {source.name}: {source.url}")

    @pytest.mark.asyncio
    async def test_fetch_single_feed(self):
        """Test fetching a single feed."""
        collector = EnhancedMangaRSSCollector()

        # Try BookWalker feed
        bookwalker_source = collector.get_source_by_name("bookwalker")

        if bookwalker_source:
            try:
                items = await collector.fetch_feed_async(bookwalker_source)
                assert isinstance(items, list)
                print(f"Fetched {len(items)} items from {bookwalker_source.name}")

            except Exception as e:
                pytest.skip(f"Feed unavailable: {e}")

    def test_statistics(self):
        """Test statistics retrieval."""
        collector = EnhancedMangaRSSCollector()
        stats = collector.get_statistics()
        assert isinstance(stats, dict)
        assert "available_sources" in stats
        print(f"Collector stats: {stats}")


class TestStreamingPlatformEnhanced:
    """Test enhanced streaming platform collector."""

    def test_collector_initialization(self):
        """Test collector initialization."""
        collector = EnhancedStreamingCollector()
        assert collector is not None

    def test_platform_detection(self):
        """Test platform detection."""
        collector = EnhancedStreamingCollector()

        test_cases = [
            ("Netflix", StreamingPlatform.NETFLIX),
            ("Amazon Prime Video", StreamingPlatform.AMAZON_PRIME),
            ("Crunchyroll", StreamingPlatform.CRUNCHYROLL),
            ("Hulu", StreamingPlatform.HULU),
        ]

        for site_name, expected_platform in test_cases:
            platform = collector._detect_platform(site_name)
            assert platform == expected_platform
            print(f"{site_name} -> {platform.value}")

    @pytest.mark.asyncio
    async def test_fetch_streaming_data(self):
        """Test fetching streaming data from AniList."""
        collector = EnhancedStreamingCollector()

        try:
            # Fetch current season
            anime_list = await collector.fetch_streaming_data(
                season="FALL", year=2024, per_page=5
            )

            assert isinstance(anime_list, list)
            print(f"Fetched {len(anime_list)} anime with streaming info")

            if anime_list:
                anime = anime_list[0]
                print(f"Sample anime: {anime.get('title', {})}")

                streaming_info = collector.extract_streaming_info(anime)
                print(f"Streaming platforms: {len(streaming_info)}")

                for info in streaming_info:
                    print(f"  - {info.platform.value}: {info.url}")

        except Exception as e:
            pytest.skip(f"AniList API unavailable: {e}")

    @pytest.mark.asyncio
    async def test_fetch_netflix_prime(self):
        """Test fetching Netflix/Prime anime."""
        collector = EnhancedStreamingCollector()

        try:
            anime_list = await collector.fetch_netflix_prime_anime(
                season="FALL", year=2024
            )

            assert isinstance(anime_list, list)
            print(f"Found {len(anime_list)} anime on Netflix/Amazon Prime")

            if anime_list:
                for anime in anime_list[:3]:
                    title = anime.get("title", {})
                    print(f"  - {title.get('romaji', 'Unknown')}")

        except Exception as e:
            pytest.skip(f"AniList API unavailable: {e}")


class TestEnhancedDuplicateDetection:
    """Test enhanced duplicate detection."""

    def test_detector_initialization(self):
        """Test detector initialization."""
        detector = EnhancedDuplicateDetector(fuzzy_threshold=0.85)
        assert detector is not None
        assert detector.fuzzy_threshold == 0.85

    def test_exact_match(self):
        """Test exact title matching."""
        detector = EnhancedDuplicateDetector()

        work1 = Work(title="進撃の巨人", work_type=WorkType.ANIME, id=1)
        work2 = Work(title="進撃の巨人", work_type=WorkType.ANIME, id=2)

        match = detector.detect_duplicate(work1, work2)
        assert match is not None
        assert match.confidence >= 0.95
        assert match.recommended_action == "merge"
        print(f"Exact match confidence: {match.confidence:.2f}")

    def test_fuzzy_match(self):
        """Test fuzzy title matching."""
        detector = EnhancedDuplicateDetector(fuzzy_threshold=0.80)

        work1 = Work(title="Attack on Titan", work_type=WorkType.ANIME, id=1)
        work2 = Work(title="Attack on Titans", work_type=WorkType.ANIME, id=2)

        match = detector.detect_duplicate(work1, work2)
        assert match is not None
        print(f"Fuzzy match confidence: {match.confidence:.2f}")

    def test_no_match_different_types(self):
        """Test that different work types don't match."""
        detector = EnhancedDuplicateDetector()

        work1 = Work(title="同じタイトル", work_type=WorkType.ANIME, id=1)
        work2 = Work(title="同じタイトル", work_type=WorkType.MANGA, id=2)

        match = detector.detect_duplicate(work1, work2)
        assert match is None

    def test_find_duplicates_in_list(self):
        """Test finding all duplicates in a list."""
        detector = EnhancedDuplicateDetector()

        works = [
            Work(title="鬼滅の刃", work_type=WorkType.ANIME, id=1),
            Work(title="鬼滅の刃", work_type=WorkType.ANIME, id=2),
            Work(title="呪術廻戦", work_type=WorkType.ANIME, id=3),
            Work(title="呪術廻戦", work_type=WorkType.ANIME, id=4),
            Work(title="チェンソーマン", work_type=WorkType.ANIME, id=5),
        ]

        duplicates = detector.find_duplicates_in_list(works)
        assert len(duplicates) >= 2
        print(f"Found {len(duplicates)} duplicate pairs")

        for dup in duplicates:
            print(f"  - Works {dup.work1_id} & {dup.work2_id}: {dup.confidence:.2f}")


class TestEnhancedDataMerger:
    """Test enhanced data merger."""

    def test_merger_initialization(self):
        """Test merger initialization."""
        merger = EnhancedDataMerger()
        assert merger is not None

    def test_merge_two_works(self):
        """Test merging two works."""
        merger = EnhancedDataMerger()

        work1 = Work(
            title="ワンピース",
            work_type=WorkType.MANGA,
            id=1,
            title_en="One Piece",
            metadata={"genres": ["Adventure", "Action"]},
        )

        work2 = Work(
            title="ワンピース",
            work_type=WorkType.MANGA,
            id=2,
            title_kana="ワンピース",
            official_url="https://one-piece.com",
            metadata={"genres": ["Fantasy"], "status": "ongoing"},
        )

        merged = merger.merge_works(work1, work2)

        assert merged.title == "ワンピース"
        assert merged.title_en == "One Piece"
        assert merged.title_kana == "ワンピース"
        assert merged.official_url == "https://one-piece.com"

        print(f"Merged work: {merged.title}")
        print(f"  - English: {merged.title_en}")
        print(f"  - Kana: {merged.title_kana}")
        print(f"  - URL: {merged.official_url}")

    def test_deduplicate_works(self):
        """Test deduplicating a list of works."""
        detector = EnhancedDuplicateDetector()
        merger = EnhancedDataMerger()

        works = [
            Work(title="鬼滅の刃", work_type=WorkType.ANIME, id=1),
            Work(
                title="鬼滅の刃",
                work_type=WorkType.ANIME,
                id=2,
                title_en="Demon Slayer",
            ),
            Work(title="呪術廻戦", work_type=WorkType.ANIME, id=3),
        ]

        deduplicated = merger.deduplicate_works(works, detector)

        assert len(deduplicated) == 2
        print(f"Deduplicated {len(works)} works to {len(deduplicated)} unique works")


class TestEnhancedContentFilter:
    """Test enhanced content filter."""

    def test_filter_manager_initialization(self):
        """Test filter manager initialization."""
        manager = ConfigBasedFilterManager()
        assert manager is not None
        assert len(manager.ng_keywords) > 0
        print(f"Loaded {len(manager.ng_keywords)} NG keywords")

    def test_add_ng_keyword(self):
        """Test adding NG keyword."""
        manager = ConfigBasedFilterManager()
        initial_count = len(manager.ng_keywords)

        manager.add_ng_keyword("テストキーワード")

        assert len(manager.ng_keywords) == initial_count + 1
        assert "テストキーワード" in manager.get_all_keywords()

    def test_enhanced_filter_initialization(self):
        """Test enhanced filter initialization."""
        filter_instance = EnhancedContentFilter()
        assert filter_instance is not None

    def test_filter_work_with_ng_keyword(self):
        """Test filtering work with NG keyword."""
        filter_instance = EnhancedContentFilter()

        # Create work with NG keyword
        work = Work(
            title="エロいアニメ",
            work_type=WorkType.ANIME,
            metadata={"description": "18禁コンテンツ"},
        )

        result = filter_instance.filter_work(work)

        assert result.is_filtered == True
        assert result.action == FilterAction.BLOCK
        assert len(result.matched_keywords) > 0
        print(f"Filtered: {result.reason}")

    def test_filter_work_allowed(self):
        """Test allowing clean work."""
        filter_instance = EnhancedContentFilter()

        work = Work(
            title="進撃の巨人",
            work_type=WorkType.ANIME,
            metadata={"description": "人類と巨人の戦いを描いた作品"},
        )

        result = filter_instance.filter_work(work)

        assert result.is_filtered == False
        assert result.action == FilterAction.ALLOW
        print(f"Allowed: {work.title}")

    def test_filter_statistics(self):
        """Test filter statistics."""
        filter_instance = EnhancedContentFilter()

        # Filter some works
        works = [
            Work(title="進撃の巨人", work_type=WorkType.ANIME),
            Work(title="エロアニメ", work_type=WorkType.ANIME),
            Work(title="呪術廻戦", work_type=WorkType.ANIME),
        ]

        for work in works:
            filter_instance.filter_work(work)

        stats = filter_instance.get_statistics()
        assert isinstance(stats, dict)
        assert "total_filtered" in stats
        print(f"Filter stats: {stats}")


def run_integration_tests():
    """Run all integration tests."""
    print("=" * 80)
    print("Running Enhanced Backend Integration Tests")
    print("=" * 80)

    # Run pytest
    pytest.main([__file__, "-v", "-s"])


if __name__ == "__main__":
    run_integration_tests()
