"""
マンガRSSフィード収集モジュール（型ヒント付き）
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import feedparser

logger = logging.getLogger(__name__)


class RSSFeedParser:
    """RSSフィードパーサー"""

    def __init__(self, feed_url: str, source_name: str = "RSS") -> None:
        """
        初期化

        Args:
            feed_url: RSSフィードのURL
            source_name: ソース名
        """
        self.feed_url = feed_url
        self.source_name = source_name

    def fetch_feed(self) -> Optional[feedparser.FeedParserDict]:
        """
        RSSフィードを取得

        Returns:
            Optional[feedparser.FeedParserDict]: フィードデータ（エラー時はNone）
        """
        try:
            feed = feedparser.parse(self.feed_url)

            if feed.bozo:
                logger.warning(f"フィード解析警告: {self.feed_url} - {feed.bozo_exception}")

            return feed

        except Exception as e:
            logger.error(f"フィード取得エラー: {self.feed_url} - {e}")
            return None

    def parse_entries(self) -> List[Dict[str, Any]]:
        """
        フィードエントリーを解析

        Returns:
            List[Dict[str, Any]]: 解析されたエントリーのリスト
        """
        feed = self.fetch_feed()

        if not feed or not hasattr(feed, "entries"):
            return []

        entries: List[Dict[str, Any]] = []

        for entry in feed.entries:
            parsed_entry = self._parse_entry(entry)
            if parsed_entry:
                entries.append(parsed_entry)

        logger.info(f"{self.source_name}: {len(entries)}件取得")
        return entries

    def _parse_entry(self, entry: Any) -> Optional[Dict[str, Any]]:
        """
        個別エントリーを解析

        Args:
            entry: フィードエントリー

        Returns:
            Optional[Dict[str, Any]]: 解析されたエントリー（解析失敗時はNone）
        """
        try:
            title = entry.get("title", "不明")
            link = entry.get("link", "")
            published = self._parse_date(entry)
            description = entry.get("description", "") or entry.get("summary", "")

            # タイトルから巻数を抽出
            volume_number = self._extract_volume_number(title)

            return {
                "title": title,
                "link": link,
                "published": published,
                "description": description,
                "volume_number": volume_number,
                "source": self.source_name,
                "raw_entry": entry,
            }

        except Exception as e:
            logger.error(f"エントリー解析エラー: {e}")
            return None

    def _parse_date(self, entry: Any) -> Optional[str]:
        """
        エントリーから日付を解析

        Args:
            entry: フィードエントリー

        Returns:
            Optional[str]: 日付（YYYY-MM-DD形式、不明な場合はNone）
        """
        # published_parsedを優先
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                dt = datetime(*entry.published_parsed[:6])
                return dt.strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                pass

        # updated_parsedを試行
        if hasattr(entry, "updated_parsed") and entry.updated_parsed:
            try:
                dt = datetime(*entry.updated_parsed[:6])
                return dt.strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                pass

        # 文字列から解析を試みる
        date_str = entry.get("published", "") or entry.get("updated", "")
        if date_str:
            return self._parse_date_string(date_str)

        return None

    def _parse_date_string(self, date_str: str) -> Optional[str]:
        """
        日付文字列を解析

        Args:
            date_str: 日付文字列

        Returns:
            Optional[str]: 日付（YYYY-MM-DD形式、解析失敗時はNone）
        """
        # よくある日付フォーマットを試行
        formats = [
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%Y年%m月%d日",
            "%a, %d %b %Y %H:%M:%S %z",
            "%a, %d %b %Y %H:%M:%S %Z",
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue

        return None

    def _extract_volume_number(self, title: str) -> Optional[str]:
        """
        タイトルから巻数を抽出

        Args:
            title: タイトル文字列

        Returns:
            Optional[str]: 巻数（抽出できない場合はNone）
        """
        # パターン: "第X巻", "X巻", "(X)", "[X]", "Vol.X", "Volume X"
        patterns = [
            r"第(\d+)巻",
            r"(\d+)巻",
            r"\((\d+)\)",
            r"\[(\d+)\]",
            r"[Vv]ol\.?\s*(\d+)",
            r"[Vv]olume\s+(\d+)",
            r"#(\d+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, title)
            if match:
                return match.group(1)

        return None


def parse_bookwalker_feed(feed_url: str) -> List[Dict[str, Any]]:
    """
    BookWalkerのRSSフィードを解析

    Args:
        feed_url: RSSフィードのURL

    Returns:
        List[Dict[str, Any]]: 解析されたエントリーのリスト
    """
    parser = RSSFeedParser(feed_url, "BookWalker")
    return parser.parse_entries()


def parse_magapoke_feed(feed_url: str) -> List[Dict[str, Any]]:
    """
    マガポケのRSSフィードを解析

    Args:
        feed_url: RSSフィードのURL

    Returns:
        List[Dict[str, Any]]: 解析されたエントリーのリスト
    """
    parser = RSSFeedParser(feed_url, "マガポケ")
    return parser.parse_entries()


def parse_danime_feed(feed_url: str) -> List[Dict[str, Any]]:
    """
    dアニメストアのRSSフィードを解析

    Args:
        feed_url: RSSフィードのURL

    Returns:
        List[Dict[str, Any]]: 解析されたエントリーのリスト
    """
    parser = RSSFeedParser(feed_url, "dアニメストア")
    return parser.parse_entries()


def parse_generic_feed(feed_url: str, source_name: str = "RSS") -> List[Dict[str, Any]]:
    """
    汎用RSSフィードを解析

    Args:
        feed_url: RSSフィードのURL
        source_name: ソース名

    Returns:
        List[Dict[str, Any]]: 解析されたエントリーのリスト
    """
    parser = RSSFeedParser(feed_url, source_name)
    return parser.parse_entries()


def extract_work_title(entry_title: str) -> str:
    """
    エントリータイトルから作品タイトルを抽出

    Args:
        entry_title: エントリータイトル

    Returns:
        str: 作品タイトル
    """
    # 巻数表記を削除
    title = re.sub(r"第?\d+巻", "", entry_title)
    title = re.sub(r"\(\d+\)", "", title)
    title = re.sub(r"\[\d+\]", "", title)
    title = re.sub(r"[Vv]ol\.?\s*\d+", "", title)
    title = re.sub(r"[Vv]olume\s+\d+", "", title)
    title = re.sub(r"#\d+", "", title)

    # 記号を削除
    title = re.sub(r"[【】『』「」\[\]()（）]", "", title)

    # 余分な空白を削除
    title = re.sub(r"\s+", " ", title).strip()

    return title


def check_ng_keywords_in_entry(
    entry: Dict[str, Any], ng_keywords: List[str]
) -> Tuple[bool, List[str]]:
    """
    エントリー内のNGキーワードをチェック

    Args:
        entry: エントリー情報
        ng_keywords: NGキーワードのリスト

    Returns:
        Tuple[bool, List[str]]: (NGキーワードが含まれるか, マッチしたキーワードのリスト)
    """
    matched_keywords: List[str] = []

    # タイトルをチェック
    title = entry.get("title", "")
    for keyword in ng_keywords:
        if keyword.lower() in title.lower():
            matched_keywords.append(keyword)

    # 説明をチェック
    description = entry.get("description", "")
    if description:
        for keyword in ng_keywords:
            if keyword.lower() in description.lower():
                matched_keywords.append(keyword)

    # 重複を削除
    matched_keywords = list(set(matched_keywords))

    return len(matched_keywords) > 0, matched_keywords


def parse_multiple_feeds(feed_urls: Dict[str, str]) -> Dict[str, List[Dict[str, Any]]]:
    """
    複数のRSSフィードを解析

    Args:
        feed_urls: フィード名とURLの辞書

    Returns:
        Dict[str, List[Dict[str, Any]]]: フィード名ごとのエントリーリスト
    """
    results: Dict[str, List[Dict[str, Any]]] = {}

    for source_name, feed_url in feed_urls.items():
        try:
            parser = RSSFeedParser(feed_url, source_name)
            entries = parser.parse_entries()
            results[source_name] = entries

            logger.info(f"{source_name}: {len(entries)}件取得")

        except Exception as e:
            logger.error(f"{source_name} 取得エラー: {e}")
            results[source_name] = []

    return results


def validate_feed_url(url: str) -> bool:
    """
    RSSフィードURLの妥当性を検証

    Args:
        url: RSSフィードのURL

    Returns:
        bool: 妥当なURLかどうか
    """
    try:
        result = urlparse(url)
        return all([result.scheme in ["http", "https"], result.netloc])
    except Exception:
        return False


def get_feed_info(feed_url: str) -> Optional[Dict[str, Any]]:
    """
    フィード情報を取得

    Args:
        feed_url: RSSフィードのURL

    Returns:
        Optional[Dict[str, Any]]: フィード情報（エラー時はNone）
    """
    try:
        feed = feedparser.parse(feed_url)

        if feed.bozo:
            logger.warning(f"フィード解析警告: {feed.bozo_exception}")

        return {
            "title": feed.feed.get("title", "不明"),
            "link": feed.feed.get("link", ""),
            "description": feed.feed.get("description", ""),
            "language": feed.feed.get("language", ""),
            "updated": feed.feed.get("updated", ""),
            "entry_count": len(feed.entries),
        }

    except Exception as e:
        logger.error(f"フィード情報取得エラー: {e}")
        return None
