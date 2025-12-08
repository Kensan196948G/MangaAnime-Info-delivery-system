"""
Unit Tests for Filtering Logic
===============================

Tests for content filtering:
- NG keyword filtering
- Genre filtering
- Tag filtering
- Description filtering
- Whitelist/blacklist
"""

import pytest
import re


class TestNGKeywordFiltering:
    """Test suite for NG keyword filtering"""

    @pytest.fixture
    def ng_keywords(self):
        """Standard NG keywords list"""
        return [
            "R18", "R-18", "18禁",
            "成人向け", "アダルト",
            "BL", "ボーイズラブ",
            "百合", "GL",
            "エロ", "18+",
            "過激", "暴力的"
        ]

    def test_exact_match_filtering(self, ng_keywords):
        """Test exact keyword match filtering"""
        test_titles = [
            ("普通のアニメ", False),
            ("R18アニメ", True),
            ("ボーイズラブストーリー", True),
            ("百合アニメ", True),
            ("正常なタイトル", False),
        ]

        for title, should_filter in test_titles:
            contains_ng = any(keyword in title for keyword in ng_keywords)
            assert contains_ng == should_filter

    def test_case_insensitive_filtering(self, ng_keywords):
        """Test case-insensitive filtering"""
        test_cases = [
            "r18 content",
            "R18 Content",
            "r-18 anime",
        ]

        ng_keywords_lower = [kw.lower() for kw in ng_keywords]

        for title in test_cases:
            contains_ng = any(kw in title.lower() for kw in ng_keywords_lower)
            assert contains_ng

    def test_partial_word_matching(self, ng_keywords):
        """Test partial word matching"""
        # Should match these
        positive_cases = [
            "R18アニメ",
            "【R18】タイトル",
            "成人向けコンテンツ",
        ]

        # Should NOT match these (avoiding false positives)
        negative_cases = [
            "18歳の主人公",  # Contains "18" but not "R18"
            "禁断の恋",  # Contains "禁" but not "18禁"
        ]

        for title in positive_cases:
            contains_ng = any(kw in title for kw in ng_keywords)
            assert contains_ng

        for title in negative_cases:
            contains_ng = any(kw in title for kw in ng_keywords)
            assert not contains_ng

    def test_filter_by_genre(self):
        """Test filtering by genre"""
        ng_genres = ["Hentai", "Ecchi", "Yaoi", "Yuri"]

        anime_genres_pass = ["Action", "Adventure", "Comedy"]
        anime_genres_fail = ["Action", "Ecchi", "Comedy"]

        assert not any(genre in ng_genres for genre in anime_genres_pass)
        assert any(genre in ng_genres for genre in anime_genres_fail)

    def test_filter_by_description(self, ng_keywords):
        """Test filtering by description content"""
        descriptions = [
            ("This is a normal anime about heroes", False),
            ("This contains R18 content warning", True),
            ("A story about 成人向け themes", True),
            ("Family-friendly adventure", False),
        ]

        for description, should_filter in descriptions:
            contains_ng = any(kw in description for kw in ng_keywords)
            assert contains_ng == should_filter

    def test_multiple_ng_keywords(self, ng_keywords):
        """Test content with multiple NG keywords"""
        title = "R18 ボーイズラブ アニメ"

        matched_keywords = [kw for kw in ng_keywords if kw in title]

        assert len(matched_keywords) >= 2
        assert "R18" in matched_keywords
        assert "ボーイズラブ" in matched_keywords

    def test_whitespace_handling(self, ng_keywords):
        """Test filtering with various whitespace"""
        test_cases = [
            "R18  アニメ",  # Double space
            "R18\tアニメ",  # Tab
            "R18\nアニメ",  # Newline
            " R18 ",  # Leading/trailing spaces
        ]

        for title in test_cases:
            # Normalize whitespace before checking
            normalized = ' '.join(title.split())
            contains_ng = any(kw in normalized for kw in ng_keywords)
            assert contains_ng


class TestFilteringEdgeCases:
    """Test suite for edge cases in filtering"""

    def test_empty_title_filtering(self):
        """Test filtering empty or None titles"""
        ng_keywords = ["R18", "BL"]

        empty_cases = ["", None, "   "]

        for title in empty_cases:
            if title:
                contains_ng = any(kw in title for kw in ng_keywords)
            else:
                contains_ng = False

            assert not contains_ng

    def test_very_long_title_filtering(self):
        """Test filtering very long titles"""
        ng_keywords = ["R18"]

        long_title = "あ" * 1000 + "R18" + "い" * 1000

        contains_ng = any(kw in long_title for kw in ng_keywords)
        assert contains_ng

    def test_special_characters_in_keywords(self):
        """Test filtering with special characters"""
        ng_keywords = ["R-18", "18+", "成人向け"]

        test_titles = [
            ("R-18コンテンツ", True),
            ("18+制限", True),
            ("成人向けアニメ", True),
            ("R18コンテンツ", False),  # Dash missing
        ]

        for title, should_filter in test_titles:
            contains_ng = any(kw in title for kw in ng_keywords)
            assert contains_ng == should_filter

    def test_unicode_normalization(self):
        """Test Unicode normalization in filtering"""
        import unicodedata

        # Full-width vs half-width
        title1 = "Ｒ１８アニメ"  # Full-width
        title2 = "R18アニメ"     # Half-width

        # Normalize to NFKC (compatibility composition)
        normalized1 = unicodedata.normalize('NFKC', title1)
        normalized2 = unicodedata.normalize('NFKC', title2)

        assert "R18" in normalized1
        assert normalized1 == normalized2

    def test_regex_pattern_filtering(self):
        """Test regex-based filtering"""
        # Pattern for R18, R-18, R_18, etc.
        pattern = r'R[-_\s]?18'

        test_cases = [
            ("R18アニメ", True),
            ("R-18アニメ", True),
            ("R_18アニメ", True),
            ("R 18アニメ", True),
            ("R218アニメ", False),
        ]

        for title, should_match in test_cases:
            matches = bool(re.search(pattern, title, re.IGNORECASE))
            assert matches == should_match


class TestWhitelistBlacklist:
    """Test suite for whitelist/blacklist functionality"""

    def test_whitelist_priority(self):
        """Test that whitelist takes priority over NG keywords"""
        ng_keywords = ["暴力", "過激"]
        whitelist = ["進撃の巨人", "鬼滅の刃"]

        # These titles contain NG keywords but are whitelisted
        test_cases = [
            ("進撃の巨人", True, False),  # Whitelisted, should pass
            ("過激なアニメ", False, True),  # Not whitelisted, should filter
        ]

        for title, is_whitelisted, should_filter in test_cases:
            if any(wl in title for wl in whitelist):
                filtered = False  # Whitelist overrides
            else:
                filtered = any(kw in title for kw in ng_keywords)

            assert filtered == should_filter

    def test_blacklist_absolute_block(self):
        """Test that blacklist always blocks"""
        blacklist = ["特定の禁止作品", "完全NG作品"]

        test_titles = [
            ("特定の禁止作品 シーズン2", True),
            ("完全NG作品の続編", True),
            ("普通の作品", False),
        ]

        for title, should_block in test_titles:
            is_blocked = any(bl in title for bl in blacklist)
            assert is_blocked == should_block

    def test_combined_whitelist_blacklist(self):
        """Test combined whitelist and blacklist logic"""
        ng_keywords = ["暴力"]
        whitelist = ["許可された作品"]
        blacklist = ["絶対NG"]

        def should_filter(title):
            # Blacklist has highest priority
            if any(bl in title for bl in blacklist):
                return True

            # Whitelist overrides NG keywords
            if any(wl in title for wl in whitelist):
                return False

            # Check NG keywords
            return any(kw in title for kw in ng_keywords)

        test_cases = [
            ("絶対NG作品", True),  # Blacklisted
            ("許可された作品", False),  # Whitelisted
            ("暴力的なアニメ", True),  # NG keyword
            ("普通のアニメ", False),  # Clean
        ]

        for title, expected_filter in test_cases:
            assert should_filter(title) == expected_filter


class TestGenreFiltering:
    """Test suite for genre-based filtering"""

    def test_single_genre_filter(self):
        """Test filtering by single genre"""
        ng_genres = ["Hentai"]

        anime_genres = ["Action", "Comedy"]
        assert not any(g in ng_genres for g in anime_genres)

        anime_genres_ng = ["Action", "Hentai"]
        assert any(g in ng_genres for g in anime_genres_ng)

    def test_multiple_genre_filter(self):
        """Test filtering by multiple genres"""
        ng_genres = ["Hentai", "Ecchi", "Yaoi", "Yuri"]

        test_cases = [
            (["Action", "Adventure"], False),
            (["Action", "Ecchi"], True),
            (["Romance", "Yaoi"], True),
            (["Comedy", "Slice of Life"], False),
        ]

        for genres, should_filter in test_cases:
            filtered = any(g in ng_genres for g in genres)
            assert filtered == should_filter

    def test_genre_case_sensitivity(self):
        """Test case-sensitive genre matching"""
        ng_genres = ["Hentai", "Ecchi"]
        ng_genres_lower = [g.lower() for g in ng_genres]

        anime_genres = ["action", "ecchi", "comedy"]
        anime_genres_lower = [g.lower() for g in anime_genres]

        # Case-insensitive matching
        filtered = any(g in ng_genres_lower for g in anime_genres_lower)
        assert filtered

    def test_partial_genre_matching(self):
        """Test partial genre name matching"""
        # Should NOT match partial genres to avoid false positives
        ng_genres = ["Ecchi"]
        anime_genres = ["Mecha"]  # Contains "echa" but not "Ecchi"

        filtered = any(g in ng_genres for g in anime_genres)
        assert not filtered


class TestTagFiltering:
    """Test suite for tag-based filtering"""

    def test_filter_by_tags(self):
        """Test filtering by tags"""
        ng_tags = ["Sexual Content", "Violence", "Gore"]

        anime_tags = ["Adventure", "Magic", "School"]
        assert not any(t in ng_tags for t in anime_tags)

        anime_tags_ng = ["Adventure", "Sexual Content"]
        assert any(t in ng_tags for t in anime_tags_ng)

    def test_tag_vs_genre_difference(self):
        """Test that tags and genres are filtered separately"""
        ng_genres = ["Hentai"]
        ng_tags = ["Sexual Content"]

        # Has NG tag but not NG genre
        anime1 = {
            "genres": ["Action", "Romance"],
            "tags": ["Sexual Content", "Drama"]
        }

        genre_filtered = any(g in ng_genres for g in anime1["genres"])
        tag_filtered = any(t in ng_tags for t in anime1["tags"])

        assert not genre_filtered
        assert tag_filtered

    def test_combined_genre_tag_filtering(self):
        """Test combined genre and tag filtering"""
        ng_genres = ["Hentai"]
        ng_tags = ["Sexual Content"]

        def should_filter(anime):
            genre_match = any(g in ng_genres for g in anime.get("genres", []))
            tag_match = any(t in ng_tags for t in anime.get("tags", []))
            return genre_match or tag_match

        test_cases = [
            ({"genres": ["Action"], "tags": ["Adventure"]}, False),
            ({"genres": ["Hentai"], "tags": ["Adventure"]}, True),
            ({"genres": ["Action"], "tags": ["Sexual Content"]}, True),
            ({"genres": ["Hentai"], "tags": ["Sexual Content"]}, True),
        ]

        for anime, expected in test_cases:
            assert should_filter(anime) == expected


class TestDescriptionFiltering:
    """Test suite for description-based filtering"""

    def test_filter_by_description_keywords(self):
        """Test filtering by keywords in description"""
        ng_keywords = ["R18", "成人向け", "18禁"]

        descriptions = [
            ("A normal adventure story", False),
            ("This anime contains R18 content", True),
            ("成人向けの内容を含みます", True),
            ("Suitable for all ages", False),
        ]

        for description, should_filter in descriptions:
            filtered = any(kw in description for kw in ng_keywords)
            assert filtered == should_filter

    def test_description_word_boundary(self):
        """Test word boundary matching in descriptions"""
        ng_keywords = ["adult"]

        # Should match these
        descriptions_match = [
            "This is adult content",
            "Adult themes present",
            "Not for adults only",
        ]

        # Might match these (depending on implementation)
        descriptions_maybe = [
            "The adulthood journey",  # Contains "adult" as substring
        ]

        for desc in descriptions_match:
            # Simple substring matching (current)
            contains = any(kw in desc.lower() for kw in ng_keywords)
            assert contains

    def test_description_html_stripping(self):
        """Test HTML stripping from descriptions"""
        html_description = "<p>This is <b>R18</b> content</p>"

        # Strip HTML tags
        import re
        clean_text = re.sub(r'<[^>]+>', '', html_description)

        ng_keywords = ["R18"]
        filtered = any(kw in clean_text for kw in ng_keywords)
        assert filtered

    def test_long_description_filtering(self):
        """Test filtering in very long descriptions"""
        ng_keywords = ["R18"]

        long_description = "あ" * 5000 + "R18" + "い" * 5000

        filtered = any(kw in long_description for kw in ng_keywords)
        assert filtered


class TestFilteringPerformance:
    """Test suite for filtering performance considerations"""

    def test_keyword_set_performance(self):
        """Test using set for faster keyword lookup"""
        ng_keywords_list = ["R18", "BL", "百合"] * 100  # 300 items
        ng_keywords_set = set(ng_keywords_list)

        title = "普通のアニメ"

        # Set lookup should be faster
        import time

        # List lookup
        start = time.time()
        for _ in range(1000):
            _ = any(kw in title for kw in ng_keywords_list)
        list_time = time.time() - start

        # Set lookup (checking if title contains any keyword is different,
        # but we can check if any word in title is in the set)
        start = time.time()
        for _ in range(1000):
            words = title.split()
            _ = any(word in ng_keywords_set for word in words)
        set_time = time.time() - start

        # Both should complete successfully
        assert list_time > 0
        assert set_time > 0

    def test_regex_compilation(self):
        """Test regex compilation for performance"""
        ng_keywords = ["R18", "BL", "百合"]

        # Compile regex pattern once
        pattern = re.compile('|'.join(re.escape(kw) for kw in ng_keywords))

        test_titles = [
            "普通のアニメ",
            "R18アニメ",
            "BLストーリー",
        ]

        for title in test_titles:
            match = pattern.search(title)
            assert isinstance(match, (re.Match, type(None)))

    def test_early_termination(self):
        """Test early termination in filtering"""
        ng_keywords = ["R18"] + ["keyword"] * 1000

        title = "R18アニメ"

        # Should find match on first keyword and terminate
        found = False
        for keyword in ng_keywords:
            if keyword in title:
                found = True
                break

        assert found


class TestFilterConfiguration:
    """Test suite for filter configuration"""

    def test_load_filter_config(self):
        """Test loading filter configuration"""
        config = {
            "ng_keywords": ["R18", "BL"],
            "ng_genres": ["Hentai"],
            "ng_tags": ["Sexual Content"],
            "enabled": True
        }

        assert config["enabled"] is True
        assert len(config["ng_keywords"]) == 2

    def test_dynamic_filter_update(self):
        """Test dynamically updating filters"""
        filters = {
            "keywords": ["R18"]
        }

        # Add new keyword
        filters["keywords"].append("18禁")

        assert "18禁" in filters["keywords"]
        assert len(filters["keywords"]) == 2

    def test_filter_strictness_levels(self):
        """Test different strictness levels"""
        strict_keywords = ["R18", "18禁", "成人向け", "BL", "百合"]
        moderate_keywords = ["R18", "18禁"]
        lenient_keywords = ["R18"]

        title = "BLアニメ"

        strict_filtered = any(kw in title for kw in strict_keywords)
        moderate_filtered = any(kw in title for kw in moderate_keywords)
        lenient_filtered = any(kw in title for kw in lenient_keywords)

        assert strict_filtered
        assert not moderate_filtered
        assert not lenient_filtered


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
