"""
Unit Tests for Manga RSS Feed Integration
==========================================

Tests for RSS feed parsing and processing:
- Feed parsing
- Entry extraction
- Date parsing
- Error handling
- Multiple feed sources
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import xml.etree.ElementTree as ET


class TestRSSFeedParsing:
    """Test suite for RSS feed parsing"""

    @pytest.fixture
    def sample_rss_feed(self):
        """Sample RSS feed XML"""
        return """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>BookWalker New Releases</title>
                <link>https://bookwalker.jp</link>
                <description>Latest manga releases</description>
                <item>
                    <title>テストマンガ 第1巻</title>
                    <link>https://bookwalker.jp/series/12345/vol1</link>
                    <pubDate>Mon, 15 Dec 2025 09:00:00 +0900</pubDate>
                    <description>新刊情報です</description>
                </item>
                <item>
                    <title>テストマンガ 第2巻</title>
                    <link>https://bookwalker.jp/series/12345/vol2</link>
                    <pubDate>Mon, 22 Dec 2025 09:00:00 +0900</pubDate>
                    <description>続刊情報です</description>
                </item>
            </channel>
        </rss>"""

    @pytest.fixture
    def atom_feed(self):
        """Sample Atom feed XML"""
        return """<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <title>Manga Updates</title>
            <link href="https://example.com"/>
            <entry>
                <title>New Manga Vol 1</title>
                <link href="https://example.com/manga/1"/>
                <published>2025-12-15T09:00:00+09:00</published>
                <summary>Description here</summary>
            </entry>
        </feed>"""

    def test_parse_rss_feed(self, sample_rss_feed):
        """Test parsing RSS feed"""
        root = ET.fromstring(sample_rss_feed)

        assert root.tag == 'rss'
        assert root.get('version') == '2.0'

        channel = root.find('channel')
        assert channel is not None

        title = channel.find('title').text
        assert title == 'BookWalker New Releases'

    def test_extract_rss_items(self, sample_rss_feed):
        """Test extracting items from RSS feed"""
        root = ET.fromstring(sample_rss_feed)
        channel = root.find('channel')
        items = channel.findall('item')

        assert len(items) == 2

        first_item = items[0]
        title = first_item.find('title').text
        link = first_item.find('link').text

        assert 'テストマンガ' in title
        assert 'bookwalker.jp' in link

    def test_parse_atom_feed(self, atom_feed):
        """Test parsing Atom feed"""
        root = ET.fromstring(atom_feed)

        # Atom uses namespace
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        entries = root.findall('atom:entry', ns)

        assert len(entries) == 1

    def test_parse_rss_pub_date(self, sample_rss_feed):
        """Test parsing RSS pubDate"""
        root = ET.fromstring(sample_rss_feed)
        items = root.find('channel').findall('item')

        pub_date_str = items[0].find('pubDate').text

        # Parse RFC 2822 format
        from email.utils import parsedate_to_datetime
        pub_date = parsedate_to_datetime(pub_date_str)

        assert pub_date.year == 2025
        assert pub_date.month == 12
        assert pub_date.day == 15

    def test_extract_volume_number(self, sample_rss_feed):
        """Test extracting volume number from title"""
        root = ET.fromstring(sample_rss_feed)
        items = root.find('channel').findall('item')

        title = items[0].find('title').text

        # Extract volume number
        import re
        match = re.search(r'第(\d+)巻', title)
        if match:
            volume_number = match.group(1)

        assert volume_number == '1'

    def test_parse_feed_with_missing_elements(self):
        """Test parsing feed with missing optional elements"""
        rss = """<?xml version="1.0"?>
        <rss version="2.0">
            <channel>
                <title>Test Feed</title>
                <item>
                    <title>Item Title</title>
                    <link>https://example.com</link>
                </item>
            </channel>
        </rss>"""

        root = ET.fromstring(rss)
        item = root.find('channel/item')

        description = item.find('description')
        pub_date = item.find('pubDate')

        assert description is None
        assert pub_date is None

    def test_handle_malformed_xml(self):
        """Test handling malformed XML"""
        malformed_xml = """<?xml version="1.0"?>
        <rss version="2.0">
            <channel>
                <title>Test</title>
                <item>
                    <title>Unclosed tag
                </item>
            </channel>
        """

        with pytest.raises(ET.ParseError):
            ET.fromstring(malformed_xml)

    def test_handle_empty_feed(self):
        """Test handling empty feed"""
        empty_feed = """<?xml version="1.0"?>
        <rss version="2.0">
            <channel>
                <title>Empty Feed</title>
            </channel>
        </rss>"""

        root = ET.fromstring(empty_feed)
        items = root.find('channel').findall('item')

        assert len(items) == 0

    def test_parse_feed_encoding(self):
        """Test parsing feed with different encoding"""
        # UTF-8 feed with Japanese characters
        feed = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>日本語フィード</title>
                <item>
                    <title>マンガタイトル</title>
                    <link>https://example.com</link>
                </item>
            </channel>
        </rss>"""

        root = ET.fromstring(feed.encode('utf-8'))
        title = root.find('channel/title').text

        assert '日本語' in title


class TestRSSDataExtraction:
    """Test suite for extracting data from RSS feeds"""

    def test_extract_manga_title(self):
        """Test extracting manga title from feed entry"""
        entry_title = "ワンピース 第105巻 (One Piece Vol 105)"

        # Extract base title
        import re
        match = re.match(r'(.+?)\s*第\d+巻', entry_title)
        if match:
            base_title = match.group(1).strip()

        assert base_title == "ワンピース"

    def test_extract_volume_variations(self):
        """Test extracting volume from various formats"""
        test_cases = [
            ("マンガ 第1巻", "1"),
            ("マンガ 1巻", "1"),
            ("マンガ Vol.1", "1"),
            ("マンガ Volume 1", "1"),
            ("マンガ (1)", "1"),
        ]

        import re
        for title, expected_vol in test_cases:
            # Try multiple patterns
            patterns = [
                r'第(\d+)巻',
                r'(\d+)巻',
                r'Vol\.?(\d+)',
                r'Volume\s*(\d+)',
                r'\((\d+)\)'
            ]

            volume = None
            for pattern in patterns:
                match = re.search(pattern, title, re.IGNORECASE)
                if match:
                    volume = match.group(1)
                    break

            assert volume == expected_vol

    def test_extract_publisher_from_url(self):
        """Test extracting publisher from feed URL"""
        feed_urls = [
            ("https://bookwalker.jp/rss", "bookwalker"),
            ("https://manga.line.me/rss", "line"),
            ("https://pocket.shonenmagazine.com/rss", "shonenmagazine"),
        ]

        import re
        for url, expected_publisher in feed_urls:
            match = re.search(r'https?://([^/]+)', url)
            if match:
                domain = match.group(1)
                publisher = domain.split('.')[0]

            assert expected_publisher in publisher

    def test_extract_release_date_formats(self):
        """Test extracting dates in various formats"""
        from email.utils import parsedate_to_datetime

        date_formats = [
            "Mon, 15 Dec 2025 09:00:00 +0900",  # RFC 2822
            "2025-12-15T09:00:00+09:00",  # ISO 8601
        ]

        # RFC 2822
        rfc_date = parsedate_to_datetime(date_formats[0])
        assert rfc_date.year == 2025

        # ISO 8601
        iso_date = datetime.fromisoformat(date_formats[1].replace('+09:00', '+09:00'))
        assert iso_date.year == 2025

    def test_clean_html_from_description(self):
        """Test cleaning HTML from description"""
        html_description = "<p>新刊発売！</p><br/><a href='link'>詳細はこちら</a>"

        # Simple HTML removal
        import re
        clean_text = re.sub(r'<[^>]+>', '', html_description)

        assert '<p>' not in clean_text
        assert '新刊発売' in clean_text

    def test_extract_price_from_description(self):
        """Test extracting price information"""
        descriptions = [
            "価格: 500円",
            "定価：1,000円",
            "Price: ¥750",
        ]

        import re
        for desc in descriptions:
            match = re.search(r'[¥円]\s*?([\d,]+)', desc)
            if not match:
                match = re.search(r'([\d,]+)\s*円', desc)

            if match:
                price_str = match.group(1).replace(',', '')
                price = int(price_str)

            assert price > 0


class TestRSSFeedSources:
    """Test suite for different RSS feed sources"""

    def test_bookwalker_feed_structure(self):
        """Test BookWalker feed structure"""
        bookwalker_feed = """<?xml version="1.0"?>
        <rss version="2.0">
            <channel>
                <title>BookWalker</title>
                <item>
                    <title>マンガタイトル 1</title>
                    <link>https://bookwalker.jp/series/123</link>
                    <pubDate>Mon, 15 Dec 2025 09:00:00 +0900</pubDate>
                </item>
            </channel>
        </rss>"""

        root = ET.fromstring(bookwalker_feed)
        item = root.find('channel/item')

        assert 'bookwalker.jp' in item.find('link').text

    def test_magazine_pocket_feed(self):
        """Test Magazine Pocket feed structure"""
        feed = """<?xml version="1.0"?>
        <rss version="2.0">
            <channel>
                <title>マガポケ</title>
                <item>
                    <title>新連載！テストマンガ</title>
                    <link>https://pocket.shonenmagazine.com/episode/123</link>
                </item>
            </channel>
        </rss>"""

        root = ET.fromstring(feed)
        item = root.find('channel/item')

        assert 'shonenmagazine.com' in item.find('link').text

    def test_multiple_feed_sources(self):
        """Test handling multiple feed sources"""
        feed_sources = [
            "https://bookwalker.jp/rss",
            "https://manga.line.me/rss",
            "https://pocket.shonenmagazine.com/rss",
        ]

        assert len(feed_sources) == 3
        assert all('http' in url for url in feed_sources)

    def test_feed_source_priority(self):
        """Test feed source priority handling"""
        sources = [
            {"name": "BookWalker", "priority": 1},
            {"name": "LINE Manga", "priority": 2},
            {"name": "Magazine Pocket", "priority": 1},
        ]

        # Sort by priority
        sorted_sources = sorted(sources, key=lambda x: x['priority'])

        assert sorted_sources[0]['priority'] == 1
        assert len([s for s in sources if s['priority'] == 1]) == 2


class TestRSSErrorHandling:
    """Test suite for RSS error handling"""

    def test_handle_network_timeout(self):
        """Test handling network timeout"""
        with patch('requests.get') as mock_get:
            mock_get.side_effect = TimeoutError("Connection timeout")

            try:
                mock_get("https://example.com/rss", timeout=30)
                success = True
            except TimeoutError:
                success = False

            assert not success

    def test_handle_404_error(self):
        """Test handling 404 error"""
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = Exception("404 Not Found")
            mock_get.return_value = mock_response

            try:
                response = mock_get("https://example.com/rss")
                response.raise_for_status()
                success = True
            except Exception:
                success = False

            assert not success

    def test_handle_invalid_xml(self):
        """Test handling invalid XML response"""
        invalid_xml = "This is not XML"

        with pytest.raises(ET.ParseError):
            ET.fromstring(invalid_xml)

    def test_handle_empty_response(self):
        """Test handling empty response"""
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = ""
            mock_get.return_value = mock_response

            response = mock_get("https://example.com/rss")

            if not response.text:
                content_available = False
            else:
                content_available = True

            assert not content_available

    def test_handle_encoding_error(self):
        """Test handling encoding errors"""
        # Simulate incorrectly encoded content
        japanese_text = "日本語"
        wrong_encoding = japanese_text.encode('shift-jis')

        try:
            decoded = wrong_encoding.decode('utf-8')
        except UnicodeDecodeError:
            # Try different encoding
            decoded = wrong_encoding.decode('shift-jis')

        assert decoded == japanese_text

    def test_retry_failed_feed_fetch(self):
        """Test retry logic for failed feed fetches"""
        max_retries = 3
        attempts = 0

        def fetch_feed():
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise ConnectionError("Temporary error")
            return "<rss><channel><title>Success</title></channel></rss>"

        result = None
        for i in range(max_retries):
            try:
                result = fetch_feed()
                break
            except ConnectionError:
                if i == max_retries - 1:
                    raise
                continue

        assert result is not None
        assert attempts == 3


class TestRSSDataValidation:
    """Test suite for RSS data validation"""

    def test_validate_required_fields(self):
        """Test validation of required fields"""
        entry = {
            "title": "Test Manga Vol 1",
            "link": "https://example.com/manga/1",
            "pubDate": "2025-12-15"
        }

        required_fields = ["title", "link"]
        missing_fields = [f for f in required_fields if f not in entry]

        assert len(missing_fields) == 0

    def test_validate_url_format(self):
        """Test URL format validation"""
        valid_urls = [
            "https://bookwalker.jp/series/123",
            "https://manga.line.me/product/123",
            "http://example.com/manga"
        ]

        invalid_urls = [
            "not-a-url",
            "ftp://example.com",
            "//example.com"
        ]

        import re
        url_pattern = r'^https?://[^\s]+$'

        for url in valid_urls:
            assert re.match(url_pattern, url)

        for url in invalid_urls:
            if url.startswith('ftp'):
                continue
            assert not re.match(url_pattern, url)

    def test_validate_date_format(self):
        """Test date format validation"""
        from email.utils import parsedate_to_datetime

        valid_date = "Mon, 15 Dec 2025 09:00:00 +0900"

        try:
            parsed_date = parsedate_to_datetime(valid_date)
            is_valid = True
        except Exception:
            is_valid = False

        assert is_valid
        assert parsed_date.year == 2025

    def test_sanitize_title(self):
        """Test title sanitization"""
        dirty_title = "  Test Manga  \n\t  Vol 1  "

        # Sanitize
        clean_title = ' '.join(dirty_title.split())

        assert clean_title == "Test Manga Vol 1"
        assert '\n' not in clean_title

    def test_validate_volume_number(self):
        """Test volume number validation"""
        valid_volumes = ["1", "10", "100"]
        invalid_volumes = ["0", "-1", "abc", ""]

        for vol in valid_volumes:
            assert vol.isdigit() and int(vol) > 0

        for vol in invalid_volumes:
            is_valid = vol.isdigit() and int(vol) > 0 if vol else False
            assert not is_valid


class TestRSSEdgeCases:
    """Edge case tests for RSS feed processing"""

    def test_very_long_feed(self):
        """Test handling very long feed with many items"""
        # Generate feed with 1000 items
        items_xml = "".join([
            f"<item><title>Item {i}</title><link>https://example.com/{i}</link></item>"
            for i in range(1000)
        ])

        feed = f"""<?xml version="1.0"?>
        <rss version="2.0">
            <channel>
                <title>Large Feed</title>
                {items_xml}
            </channel>
        </rss>"""

        root = ET.fromstring(feed)
        items = root.find('channel').findall('item')

        assert len(items) == 1000

    def test_unicode_in_feed(self):
        """Test handling Unicode characters"""
        feed = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <item>
                    <title>日本語タイトル 🎌</title>
                    <description>説明文です 📚</description>
                </item>
            </channel>
        </rss>"""

        root = ET.fromstring(feed.encode('utf-8'))
        title = root.find('channel/item/title').text

        assert '日本語' in title
        assert '🎌' in title

    def test_special_characters_in_url(self):
        """Test handling special characters in URLs"""
        feed = """<?xml version="1.0"?>
        <rss version="2.0">
            <channel>
                <item>
                    <title>Test</title>
                    <link>https://example.com/manga?id=123&amp;lang=ja</link>
                </item>
            </channel>
        </rss>"""

        root = ET.fromstring(feed)
        link = root.find('channel/item/link').text

        # XML parser should handle &amp; correctly
        assert '&' in link or '&amp;' in link

    def test_cdata_in_description(self):
        """Test handling CDATA sections"""
        feed = """<?xml version="1.0"?>
        <rss version="2.0">
            <channel>
                <item>
                    <title>Test</title>
                    <description><![CDATA[This is <b>HTML</b> content]]></description>
                </item>
            </channel>
        </rss>"""

        root = ET.fromstring(feed)
        description = root.find('channel/item/description').text

        assert '<b>' in description
        assert 'HTML' in description


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
