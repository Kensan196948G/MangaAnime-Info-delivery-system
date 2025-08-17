#!/usr/bin/env python3
"""
Unit tests for content filtering logic
"""

import pytest
from unittest.mock import Mock, patch


class TestContentFiltering:
    """Test content filtering logic for NG keywords and genres."""

    @pytest.mark.unit
    def test_ng_keyword_filtering_title(self, test_config):
        """Test NG keyword filtering in titles."""
        ng_keywords = test_config["filtering"]["ng_keywords"]

        test_cases = [
            # (title, should_be_filtered)
            ("普通のアニメタイトル", False),
            ("エロアニメタイトル", True),
            ("R18作品", True),
            ("成人向け漫画", True),
            ("BL作品集", True),
            ("百合姫", True),
            ("ボーイズラブストーリー", True),
            ("アダルト向け", True),
            ("18禁コンテンツ", True),
            ("官能小説", True),
            ("ハーレクインロマンス", True),
            ("進撃の巨人", False),  # Normal title
            ("鬼滅の刃", False),  # Normal title
        ]

        for title, should_be_filtered in test_cases:
            is_filtered = self._contains_ng_keywords(title, ng_keywords)
            assert (
                is_filtered == should_be_filtered
            ), f"Title '{title}' filtering result mismatch"

    @pytest.mark.unit
    def test_ng_keyword_filtering_description(self, test_config):
        """Test NG keyword filtering in descriptions."""
        ng_keywords = test_config["filtering"]["ng_keywords"]

        test_cases = [
            ("普通のアニメの説明です。冒険とファンタジーの物語。", False),
            ("この作品にはエロティックな要素が含まれています。", True),
            ("R18指定の作品です。大人向けの内容となっています。", True),
            ("成人向けコンテンツのため、視聴にご注意ください。", True),
            ("BLジャンルの代表的な作品です。", True),
            ("百合要素を含む日常系アニメ。", True),
            ("学園もので友情と青春を描いた作品。", False),
            ("ファンタジー世界での冒険譚。", False),
        ]

        for description, should_be_filtered in test_cases:
            is_filtered = self._contains_ng_keywords(description, ng_keywords)
            assert (
                is_filtered == should_be_filtered
            ), f"Description filtering result mismatch"

    @pytest.mark.unit
    def test_ng_genre_filtering(self, test_config):
        """Test NG genre filtering for AniList data."""
        ng_genres = test_config["filtering"]["ng_genres"]

        test_cases = [
            # (genres_list, should_be_filtered)
            (["Action", "Adventure", "Comedy"], False),
            (["Drama", "Romance", "School"], False),
            (["Hentai"], True),
            (["Ecchi", "Comedy"], True),
            (["Action", "Hentai", "Adventure"], True),
            (["Fantasy", "Magic"], False),
            (["Sci-Fi", "Mecha"], False),
        ]

        for genres, should_be_filtered in test_cases:
            is_filtered = self._contains_ng_genres(genres, ng_genres)
            assert (
                is_filtered == should_be_filtered
            ), f"Genres {genres} filtering result mismatch"

    @pytest.mark.unit
    def test_combined_filtering_logic(self, test_config):
        """Test combined filtering logic (keywords + genres + tags)."""
        ng_keywords = test_config["filtering"]["ng_keywords"]
        ng_genres = test_config["filtering"]["ng_genres"]

        # Simulate AniList media data
        test_media = [
            {
                "title": {"romaji": "Normal Anime"},
                "description": "A normal adventure story",
                "genres": ["Action", "Adventure"],
                "tags": [{"name": "Shounen"}, {"name": "Fantasy"}],
                "expected_filtered": False,
            },
            {
                "title": {"romaji": "Ecchi Anime"},
                "description": "Comedy with some ecchi elements",
                "genres": ["Comedy", "Ecchi"],
                "tags": [{"name": "School"}, {"name": "Harem"}],
                "expected_filtered": True,
            },
            {
                "title": {"romaji": "R18 Manga"},
                "description": "Adult content warning",
                "genres": ["Drama"],
                "tags": [{"name": "Adult Cast"}],
                "expected_filtered": True,
            },
            {
                "title": {"romaji": "Shounen Battle"},
                "description": "Epic battles and friendship",
                "genres": ["Action", "Shounen"],
                "tags": [{"name": "Battle"}, {"name": "Power"}],
                "expected_filtered": False,
            },
        ]

        for media in test_media:
            is_filtered = self._should_filter_media(media, ng_keywords, ng_genres)
            expected = media["expected_filtered"]
            title = media["title"]["romaji"]
            assert is_filtered == expected, f"Media '{title}' filtering result mismatch"

    @pytest.mark.unit
    def test_case_insensitive_filtering(self, test_config):
        """Test case-insensitive filtering."""
        ng_keywords = test_config["filtering"]["ng_keywords"]

        test_cases = [
            ("エロアニメ", True),
            ("エロアニメ", True),  # Full-width
            ("ero anime", True),  # Lowercase English
            ("ERO ANIME", True),  # Uppercase English
            ("Ero Anime", True),  # Mixed case
            ("r18作品", True),
            ("R18作品", True),
        ]

        for text, should_be_filtered in test_cases:
            # Case-insensitive check
            is_filtered = any(
                keyword.lower() in text.lower()
                or keyword in text  # For Japanese characters
                for keyword in ng_keywords
            )
            assert (
                is_filtered == should_be_filtered
            ), f"Text '{text}' case-insensitive filtering failed"

    @pytest.mark.unit
    def test_partial_keyword_matching(self, test_config):
        """Test partial keyword matching behavior."""
        ng_keywords = test_config["filtering"]["ng_keywords"]

        # Test that partial matches work correctly
        test_cases = [
            ("エロい表情", True),  # Contains "エロ"
            ("アダルトチルドレン", True),  # Contains "アダルト"
            ("成人向けゲーム", True),  # Contains "成人向け"
            ("大人の事情", False),  # Does not contain exact NG keywords
            ("エピソード", False),  # Contains "エ" but not "エロ"
            ("登録", False),  # Contains "R" but not "R18"
        ]

        for text, should_be_filtered in test_cases:
            is_filtered = self._contains_ng_keywords(text, ng_keywords)
            assert (
                is_filtered == should_be_filtered
            ), f"Partial matching for '{text}' failed"

    @pytest.mark.unit
    def test_tag_filtering(self, test_config):
        """Test filtering based on AniList tags."""
        ng_keywords = test_config["filtering"]["ng_keywords"]
        exclude_tags = test_config["filtering"].get("exclude_tags", [])

        test_tags_data = [
            {
                "tags": [{"name": "Shounen"}, {"name": "Battle"}],
                "expected_filtered": False,
            },
            {
                "tags": [{"name": "Adult Cast"}, {"name": "Mature Themes"}],
                "expected_filtered": any("Adult Cast" in tag for tag in exclude_tags),
            },
            {
                "tags": [{"name": "Ecchi"}, {"name": "Fanservice"}],
                "expected_filtered": True,  # Should be caught by genre filtering
            },
            {
                "tags": [{"name": "School"}, {"name": "Comedy"}],
                "expected_filtered": False,
            },
        ]

        for tag_data in test_tags_data:
            tags = [tag["name"] for tag in tag_data["tags"]]

            # Check if any tag contains NG keywords
            is_filtered = any(
                any(keyword.lower() in tag.lower() for keyword in ng_keywords)
                for tag in tags
            )

            # For exclude_tags, check exact matches
            if exclude_tags:
                is_filtered = is_filtered or any(tag in exclude_tags for tag in tags)

            expected = tag_data["expected_filtered"]
            assert is_filtered == expected, f"Tag filtering for {tags} failed"

    def _contains_ng_keywords(self, text, ng_keywords):
        """Helper method to check if text contains NG keywords."""
        if not text:
            return False

        text_lower = text.lower()
        return any(
            keyword.lower() in text_lower or keyword in text for keyword in ng_keywords
        )

    def _contains_ng_genres(self, genres, ng_genres):
        """Helper method to check if genres contain NG genres."""
        if not genres:
            return False

        return any(genre in ng_genres for genre in genres)

    def _should_filter_media(self, media, ng_keywords, ng_genres):
        """Helper method to determine if media should be filtered."""
        # Check title
        title = media.get("title", {}).get("romaji", "")
        if self._contains_ng_keywords(title, ng_keywords):
            return True

        # Check description
        description = media.get("description", "")
        if self._contains_ng_keywords(description, ng_keywords):
            return True

        # Check genres
        genres = media.get("genres", [])
        if self._contains_ng_genres(genres, ng_genres):
            return True

        # Check tags
        tags = [tag.get("name", "") for tag in media.get("tags", [])]
        if any(self._contains_ng_keywords(tag, ng_keywords) for tag in tags):
            return True

        return False


class TestFilteringPerformance:
    """Test filtering performance with large datasets."""

    @pytest.mark.performance
    def test_bulk_filtering_performance(self, test_config, test_data_generator):
        """Test filtering performance with large anime datasets."""
        import time

        ng_keywords = test_config["filtering"]["ng_keywords"]
        ng_genres = test_config["filtering"]["ng_genres"]

        # Generate large dataset
        large_dataset = test_data_generator.generate_anime_data(1000)

        # Add some NG content to test filtering
        for i in range(0, len(large_dataset), 10):  # Every 10th item
            if i < len(large_dataset):
                large_dataset[i]["genres"].append("Ecchi")  # Add NG genre

        start_time = time.time()

        filtered_count = 0
        for media in large_dataset:
            if self._should_filter_media_fast(media, ng_keywords, ng_genres):
                filtered_count += 1

        end_time = time.time()
        filtering_time = end_time - start_time

        # Verify performance
        assert (
            filtering_time < 2.0
        ), f"Filtering 1000 items took {filtering_time:.2f}s, should be under 2.0s"

        # Verify some items were filtered
        expected_filtered = len(large_dataset) // 10  # Every 10th item
        assert filtered_count >= expected_filtered * 0.8  # Allow some variance

    def _should_filter_media_fast(self, media, ng_keywords, ng_genres):
        """Optimized version of media filtering for performance testing."""
        # Quick genre check first (most efficient)
        genres = media.get("genres", [])
        if any(genre in ng_genres for genre in genres):
            return True

        # Then check title
        title = media.get("title", {}).get("romaji", "").lower()
        if any(keyword.lower() in title for keyword in ng_keywords):
            return True

        # Description check last (most expensive)
        description = media.get("description", "")
        if description and any(
            keyword.lower() in description.lower() for keyword in ng_keywords
        ):
            return True

        return False

    @pytest.mark.performance
    def test_regex_vs_string_matching_performance(self, test_config):
        """Compare regex vs simple string matching for filtering."""
        import time
        import re

        ng_keywords = test_config["filtering"]["ng_keywords"]

        # Create regex pattern
        pattern = re.compile(
            "|".join(re.escape(keyword.lower()) for keyword in ng_keywords),
            re.IGNORECASE,
        )

        test_texts = [
            "普通のアニメタイトル",
            "エロアニメタイトル",
            "R18作品です",
            "成人向けコンテンツ",
            "学園コメディ",
            "ファンタジー冒険譚",
        ] * 1000  # 6000 total tests

        # Test string matching approach
        start_time = time.time()
        string_results = []
        for text in test_texts:
            result = any(keyword.lower() in text.lower() for keyword in ng_keywords)
            string_results.append(result)
        string_time = time.time() - start_time

        # Test regex approach
        start_time = time.time()
        regex_results = []
        for text in test_texts:
            result = bool(pattern.search(text))
            regex_results.append(result)
        regex_time = time.time() - start_time

        # Verify results are the same
        assert (
            string_results == regex_results
        ), "String matching and regex should produce same results"

        # Performance comparison (string matching should generally be faster for small keyword sets)
        print(f"String matching: {string_time:.4f}s, Regex matching: {regex_time:.4f}s")

        # Both should complete within reasonable time
        assert string_time < 1.0, "String matching should complete within 1 second"
        assert regex_time < 2.0, "Regex matching should complete within 2 seconds"


class TestFilteringEdgeCases:
    """Test edge cases and special scenarios in filtering."""

    @pytest.mark.unit
    def test_empty_input_filtering(self, test_config):
        """Test filtering behavior with empty or None inputs."""
        ng_keywords = test_config["filtering"]["ng_keywords"]
        ng_genres = test_config["filtering"]["ng_genres"]

        # Test empty/None values
        test_cases = [
            {
                "title": {"romaji": None},
                "description": None,
                "genres": None,
                "tags": None,
            },
            {"title": {"romaji": ""}, "description": "", "genres": [], "tags": []},
            {"title": {}, "description": None, "genres": None},  # Missing romaji
            {},  # Completely empty
        ]

        for media in test_cases:
            # Should not throw exceptions and should not be filtered
            try:
                is_filtered = self._safe_filter_media(media, ng_keywords, ng_genres)
                assert is_filtered is False, "Empty inputs should not be filtered"
            except Exception as e:
                pytest.fail(f"Filtering empty input should not raise exception: {e}")

    @pytest.mark.unit
    def test_unicode_and_special_characters(self, test_config):
        """Test filtering with Unicode and special characters."""
        ng_keywords = test_config["filtering"]["ng_keywords"]

        test_cases = [
            ("エロ🔞アニメ", True),  # With emoji
            ("R18⚠️作品", True),  # With warning emoji
            ("成人向け♥コンテンツ", True),  # With heart symbol
            ("普通のアニメ★", False),  # With star
            ("アニメ・マンガ", False),  # With middle dot
            ("アニメ＆マンガ", False),  # With full-width ampersand
        ]

        for text, should_be_filtered in test_cases:
            is_filtered = self._contains_ng_keywords_safe(text, ng_keywords)
            assert (
                is_filtered == should_be_filtered
            ), f"Unicode filtering for '{text}' failed"

    @pytest.mark.unit
    def test_very_long_text_filtering(self, test_config):
        """Test filtering performance with very long descriptions."""
        ng_keywords = test_config["filtering"]["ng_keywords"]

        # Create very long text (10KB)
        long_text = "普通のアニメの説明です。" * 1000

        # Test without NG keywords
        start_time = time.time()
        is_filtered = self._contains_ng_keywords_safe(long_text, ng_keywords)
        end_time = time.time()

        assert not is_filtered
        assert (end_time - start_time) < 0.1, "Long text filtering should be fast"

        # Test with NG keyword at the end
        long_text_with_ng = long_text + "エロ要素あり"

        start_time = time.time()
        is_filtered = self._contains_ng_keywords_safe(long_text_with_ng, ng_keywords)
        end_time = time.time()

        assert is_filtered
        assert (
            end_time - start_time
        ) < 0.1, "Long text filtering with NG keyword should be fast"

    @pytest.mark.unit
    def test_japanese_text_normalization(self, test_config):
        """Test filtering with different Japanese text representations."""
        ng_keywords = test_config["filtering"]["ng_keywords"]

        # Test different representations of the same text
        test_cases = [
            ("エロ", True),  # Katakana
            ("えろ", True),  # Hiragana (if we handle case conversion)
            ("ero", False),  # Romaji (different word)
            ("エロい", True),  # With suffix
            ("エロゲ", True),  # Compound word
            ("R18", True),  # Alphanumeric
            ("R１８", False),  # Full-width numbers (different representation)
        ]

        for text, should_be_filtered in test_cases:
            # Basic filtering (exact match)
            is_filtered = any(keyword in text for keyword in ng_keywords)

            # For hiragana/katakana conversion, we might need additional logic
            if not is_filtered and any(
                char in "あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをん"
                for char in text
            ):
                # Convert hiragana to katakana for comparison
                katakana_text = self._hiragana_to_katakana(text)
                is_filtered = any(keyword in katakana_text for keyword in ng_keywords)

            if text in ["えろ"]:  # Special case for hiragana that should match
                assert (
                    is_filtered
                ), f"Japanese text filtering for '{text}' should handle hiragana/katakana conversion"
            else:
                assert (
                    is_filtered == should_be_filtered
                ), f"Japanese text filtering for '{text}' failed"

    def _safe_filter_media(self, media, ng_keywords, ng_genres):
        """Safe version of media filtering that handles None/empty values."""
        try:
            # Safely get title
            title = ""
            if media.get("title") and isinstance(media["title"], dict):
                title = media["title"].get("romaji") or ""

            if title and self._contains_ng_keywords_safe(title, ng_keywords):
                return True

            # Safely get description
            description = media.get("description") or ""
            if description and self._contains_ng_keywords_safe(
                description, ng_keywords
            ):
                return True

            # Safely get genres
            genres = media.get("genres") or []
            if isinstance(genres, list) and any(
                genre in ng_genres for genre in genres if genre
            ):
                return True

            return False

        except Exception:
            # If any error occurs, default to not filtering
            return False

    def _contains_ng_keywords_safe(self, text, ng_keywords):
        """Safe version of NG keyword checking."""
        if not text or not isinstance(text, str):
            return False

        try:
            text_lower = text.lower()
            return any(
                keyword.lower() in text_lower or keyword in text
                for keyword in ng_keywords
                if keyword
            )
        except Exception:
            return False

    def _hiragana_to_katakana(self, text):
        """Convert hiragana to katakana for comparison."""
        hiragana = "あいうえおかきくけこがぎぐげござじずぜぞだぢづでどたちつてとなにぬねのばびぶべぼはひふへほまみむめもやゆよらりるれろわをん"
        katakana = "アイウエオカキクケコガギグゲゴザジズゼゾダヂヅデドタチツテトナニヌネノバビブベボハヒフヘホマミムメモヤユヨラリルレロワヲン"

        result = ""
        for char in text:
            if char in hiragana:
                result += katakana[hiragana.index(char)]
            else:
                result += char

        return result
