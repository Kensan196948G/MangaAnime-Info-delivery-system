"""
フィルタリングロジックモジュール（型ヒント付き）
"""

import logging
import re
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ContentFilter:
    """コンテンツフィルター"""

    def __init__(self, ng_keywords: List[str]) -> None:
        """
        初期化

        Args:
            ng_keywords: NGキーワードのリスト
        """
        self.ng_keywords = [kw.lower() for kw in ng_keywords]

    def check_text(self, text: str) -> Tuple[bool, List[str]]:
        """
        テキストにNGキーワードが含まれるかチェック

        Args:
            text: チェック対象のテキスト

        Returns:
            Tuple[bool, List[str]]: (NGキーワードが含まれるか, マッチしたキーワードのリスト)
        """
        if not text:
            return False, []

        text_lower = text.lower()
        matched_keywords: List[str] = []

        for keyword in self.ng_keywords:
            if keyword in text_lower:
                matched_keywords.append(keyword)

        return len(matched_keywords) > 0, matched_keywords

    def check_multiple_texts(self, texts: List[str]) -> Tuple[bool, List[str]]:
        """
        複数のテキストにNGキーワードが含まれるかチェック

        Args:
            texts: チェック対象のテキストのリスト

        Returns:
            Tuple[bool, List[str]]: (NGキーワードが含まれるか, マッチしたキーワードのリスト)
        """
        all_matched_keywords: List[str] = []

        for text in texts:
            has_ng, matched = self.check_text(text)
            if has_ng:
                all_matched_keywords.extend(matched)

        # 重複を削除
        all_matched_keywords = list(set(all_matched_keywords))

        return len(all_matched_keywords) > 0, all_matched_keywords

    def filter_anime_media(self, media: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        アニメメディア情報をフィルタリング

        Args:
            media: アニメメディア情報

        Returns:
            Tuple[bool, List[str]]: (フィルタリングすべきか, マッチしたキーワードのリスト)
        """
        texts_to_check: List[str] = []

        # タイトルをチェック
        title_obj = media.get("title", {})
        if isinstance(title_obj, dict):
            texts_to_check.extend(
                [
                    str(title_obj.get("romaji", "")),
                    str(title_obj.get("english", "")),
                    str(title_obj.get("native", "")),
                ]
            )
        elif isinstance(title_obj, str):
            texts_to_check.append(title_obj)

        # ジャンルをチェック
        genres = media.get("genres", [])
        if isinstance(genres, list):
            texts_to_check.extend([str(g) for g in genres])

        # タグをチェック
        tags = media.get("tags", [])
        if isinstance(tags, list):
            for tag in tags:
                if isinstance(tag, dict):
                    tag_name = tag.get("name", "")
                    if tag_name:
                        texts_to_check.append(str(tag_name))

        # 説明をチェック
        description = media.get("description", "")
        if description:
            # HTMLタグを除去
            description_text = re.sub(r"<[^>]+>", "", str(description))
            texts_to_check.append(description_text)

        return self.check_multiple_texts(texts_to_check)

    def filter_manga_entry(self, entry: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        マンガエントリーをフィルタリング

        Args:
            entry: マンガエントリー情報

        Returns:
            Tuple[bool, List[str]]: (フィルタリングすべきか, マッチしたキーワードのリスト)
        """
        texts_to_check: List[str] = []

        # タイトルをチェック
        title = entry.get("title", "")
        if title:
            texts_to_check.append(str(title))

        # 説明をチェック
        description = entry.get("description", "")
        if description:
            # HTMLタグを除去
            description_text = re.sub(r"<[^>]+>", "", str(description))
            texts_to_check.append(description_text)

        return self.check_multiple_texts(texts_to_check)

    def add_keyword(self, keyword: str) -> None:
        """
        NGキーワードを追加

        Args:
            keyword: 追加するキーワード
        """
        keyword_lower = keyword.lower()
        if keyword_lower not in self.ng_keywords:
            self.ng_keywords.append(keyword_lower)
            logger.info(f"NGキーワード追加: {keyword}")

    def remove_keyword(self, keyword: str) -> bool:
        """
        NGキーワードを削除

        Args:
            keyword: 削除するキーワード

        Returns:
            bool: 削除に成功したかどうか
        """
        keyword_lower = keyword.lower()
        if keyword_lower in self.ng_keywords:
            self.ng_keywords.remove(keyword_lower)
            logger.info(f"NGキーワード削除: {keyword}")
            return True
        return False

    def get_keywords(self) -> List[str]:
        """
        NGキーワードのリストを取得

        Returns:
            List[str]: NGキーワードのリスト
        """
        return self.ng_keywords.copy()


def filter_anime_list(
    media_list: List[Dict[str, Any]], ng_keywords: List[str]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    アニメリストをフィルタリング

    Args:
        media_list: アニメメディア情報のリスト
        ng_keywords: NGキーワードのリスト

    Returns:
        Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]: (許可されたリスト, フィルタリングされたリスト)
    """
    content_filter = ContentFilter(ng_keywords)
    allowed: List[Dict[str, Any]] = []
    filtered: List[Dict[str, Any]] = []

    for media in media_list:
        should_filter, matched_keywords = content_filter.filter_anime_media(media)

        if should_filter:
            media["_filtered_keywords"] = matched_keywords
            filtered.append(media)
            logger.debug(f"フィルタリング: {media.get('title')} - {matched_keywords}")
        else:
            allowed.append(media)

    logger.info(f"フィルタリング結果: 許可={len(allowed)}件, 除外={len(filtered)}件")

    return allowed, filtered


def filter_manga_list(
    entry_list: List[Dict[str, Any]], ng_keywords: List[str]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    マンガリストをフィルタリング

    Args:
        entry_list: マンガエントリー情報のリスト
        ng_keywords: NGキーワードのリスト

    Returns:
        Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]: (許可されたリスト, フィルタリングされたリスト)
    """
    content_filter = ContentFilter(ng_keywords)
    allowed: List[Dict[str, Any]] = []
    filtered: List[Dict[str, Any]] = []

    for entry in entry_list:
        should_filter, matched_keywords = content_filter.filter_manga_entry(entry)

        if should_filter:
            entry["_filtered_keywords"] = matched_keywords
            filtered.append(entry)
            logger.debug(f"フィルタリング: {entry.get('title')} - {matched_keywords}")
        else:
            allowed.append(entry)

    logger.info(f"フィルタリング結果: 許可={len(allowed)}件, 除外={len(filtered)}件")

    return allowed, filtered


def create_custom_filter(
    filter_func: Callable[[Dict[str, Any]], bool],
) -> Callable[[List[Dict[str, Any]]], Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]]:
    """
    カスタムフィルターを作成

    Args:
        filter_func: フィルター関数（True=除外, False=許可）

    Returns:
        Callable: リストをフィルタリングする関数
    """

    def filter_list(
        items: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        allowed: List[Dict[str, Any]] = []
        filtered: List[Dict[str, Any]] = []

        for item in items:
            if filter_func(item):
                filtered.append(item)
            else:
                allowed.append(item)

        return allowed, filtered

    return filter_list


def filter_by_rating(
    media_list: List[Dict[str, Any]], min_rating: float = 0.0, max_rating: float = 100.0
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    評価スコアでフィルタリング

    Args:
        media_list: メディア情報のリスト
        min_rating: 最小評価スコア
        max_rating: 最大評価スコア

    Returns:
        Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]: (許可されたリスト, フィルタリングされたリスト)
    """
    allowed: List[Dict[str, Any]] = []
    filtered: List[Dict[str, Any]] = []

    for media in media_list:
        rating = media.get("averageScore", 0)

        if isinstance(rating, (int, float)) and min_rating <= rating <= max_rating:
            allowed.append(media)
        else:
            filtered.append(media)

    logger.info(f"評価フィルタリング結果: 許可={len(allowed)}件, 除外={len(filtered)}件")

    return allowed, filtered


def filter_by_date_range(
    items: List[Dict[str, Any]],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    date_field: str = "release_date",
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    日付範囲でフィルタリング

    Args:
        items: アイテムのリスト
        start_date: 開始日（YYYY-MM-DD形式）
        end_date: 終了日（YYYY-MM-DD形式）
        date_field: 日付フィールド名

    Returns:
        Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]: (許可されたリスト, フィルタリングされたリスト)
    """
    allowed: List[Dict[str, Any]] = []
    filtered: List[Dict[str, Any]] = []

    for item in items:
        item_date = item.get(date_field)

        if not item_date:
            filtered.append(item)
            continue

        try:
            # 日付の範囲チェック
            if start_date and item_date < start_date:
                filtered.append(item)
            elif end_date and item_date > end_date:
                filtered.append(item)
            else:
                allowed.append(item)
        except Exception as e:
            logger.error(f"日付比較エラー: {e}")
            filtered.append(item)

    logger.info(f"日付フィルタリング結果: 許可={len(allowed)}件, 除外={len(filtered)}件")

    return allowed, filtered


def combine_filters(
    items: List[Dict[str, Any]],
    filters: List[
        Callable[[List[Dict[str, Any]]], Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]]
    ],
) -> Tuple[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]:
    """
    複数のフィルターを組み合わせる

    Args:
        items: アイテムのリスト
        filters: フィルター関数のリスト

    Returns:
        Tuple[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]: (最終許可リスト, 各段階の除外リスト)
    """
    current_items = items
    all_filtered: Dict[str, List[Dict[str, Any]]] = {}

    for i, filter_func in enumerate(filters):
        allowed, filtered = filter_func(current_items)
        all_filtered[f"filter_{i}"] = filtered
        current_items = allowed

    logger.info(f"複合フィルタリング結果: 最終許可={len(current_items)}件")

    return current_items, all_filtered
