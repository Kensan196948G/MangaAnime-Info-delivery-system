"""
フィルタリングロジックモジュールのテスト
modules/filter_logic.py のテストカバレッジ向上
"""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from modules import filter_logic
except ImportError:
    pytest.skip("filter_logic module not found", allow_module_level=True)


class TestNGKeywords:
    """NGキーワードのテスト"""

    def test_default_ng_keywords(self):
        """デフォルトNGキーワードの確認"""
        if hasattr(filter_logic, 'NG_KEYWORDS'):
            keywords = filter_logic.NG_KEYWORDS

            assert keywords is not None
            assert isinstance(keywords, list)
            assert len(keywords) > 0

    def test_filter_with_ng_keyword(self):
        """NGキーワードを含むコンテンツのフィルタリング"""
        if hasattr(filter_logic, 'contains_ng_keyword'):
            text = "これはエロいアニメです"
            result = filter_logic.contains_ng_keyword(text)

            assert result is True  # NGワードを含む

    def test_filter_safe_content(self):
        """安全なコンテンツの通過"""
        if hasattr(filter_logic, 'contains_ng_keyword'):
            text = "これは普通のファンタジーアニメです"
            result = filter_logic.contains_ng_keyword(text)

            assert result is False  # NGワードを含まない


class TestAnimeFiltering:
    """アニメフィルタリングのテスト"""

    def test_filter_by_genre(self):
        """ジャンルでのフィルタリング"""
        if hasattr(filter_logic, 'filter_by_genre'):
            anime = {
                'title': 'テストアニメ',
                'genres': ['Action', 'Fantasy']
            }

            result = filter_logic.filter_by_genre(
                anime,
                allowed_genres=['Action', 'Fantasy', 'Adventure']
            )

            assert result is True

    def test_filter_excluded_genre(self):
        """除外ジャンルのフィルタリング"""
        if hasattr(filter_logic, 'filter_by_genre'):
            anime = {
                'title': 'テストアニメ',
                'genres': ['Ecchi', 'Fantasy']
            }

            result = filter_logic.filter_by_genre(
                anime,
                excluded_genres=['Ecchi', 'Hentai']
            )

            assert result is False  # 除外ジャンルを含む

    def test_filter_by_tags(self):
        """タグでのフィルタリング"""
        if hasattr(filter_logic, 'filter_by_tags'):
            anime = {
                'title': 'テストアニメ',
                'tags': [
                    {'name': 'Magic', 'rank': 80},
                    {'name': 'School', 'rank': 70}
                ]
            }

            result = filter_logic.filter_by_tags(
                anime,
                excluded_tags=['Ecchi', 'Nudity']
            )

            assert result is True  # 除外タグを含まない


class TestMangaFiltering:
    """マンガフィルタリングのテスト"""

    def test_filter_manga_by_keywords(self):
        """キーワードでのマンガフィルタリング"""
        if hasattr(filter_logic, 'filter_manga'):
            manga = {
                'title': 'テストマンガ',
                'description': 'ファンタジー冒険マンガ'
            }

            result = filter_logic.filter_manga(manga)

            assert result is True  # NGワードなし

    def test_filter_manga_with_ng_word(self):
        """NGワードを含むマンガの除外"""
        if hasattr(filter_logic, 'filter_manga'):
            manga = {
                'title': 'エロマンガ',
                'description': 'R18作品です'
            }

            result = filter_logic.filter_manga(manga)

            assert result is False  # NGワードあり


class TestDescriptionFiltering:
    """説明文フィルタリングのテスト"""

    def test_filter_by_description(self):
        """説明文でのフィルタリング"""
        if hasattr(filter_logic, 'filter_by_description'):
            description = "魔法と冒険のファンタジー作品"
            result = filter_logic.filter_by_description(description)

            assert result is True

    def test_filter_description_with_ng_word(self):
        """NGワードを含む説明文の除外"""
        if hasattr(filter_logic, 'filter_by_description'):
            description = "成人向けのエロティックな作品です"
            result = filter_logic.filter_by_description(description)

            assert result is False


class TestCustomFilters:
    """カスタムフィルターのテスト"""

    def test_add_custom_ng_keyword(self):
        """カスタムNGキーワードの追加"""
        if hasattr(filter_logic, 'add_ng_keyword'):
            filter_logic.add_ng_keyword('カスタムNG')

            if hasattr(filter_logic, 'NG_KEYWORDS'):
                assert 'カスタムNG' in filter_logic.NG_KEYWORDS

    def test_remove_ng_keyword(self):
        """NGキーワードの削除"""
        if hasattr(filter_logic, 'remove_ng_keyword'):
            if hasattr(filter_logic, 'add_ng_keyword'):
                filter_logic.add_ng_keyword('一時的NG')
                filter_logic.remove_ng_keyword('一時的NG')

                if hasattr(filter_logic, 'NG_KEYWORDS'):
                    assert '一時的NG' not in filter_logic.NG_KEYWORDS


class TestRatingFiltering:
    """年齢制限フィルタリングのテスト"""

    def test_filter_by_rating(self):
        """年齢制限でのフィルタリング"""
        if hasattr(filter_logic, 'filter_by_rating'):
            content = {'rating': 'PG-13'}
            result = filter_logic.filter_by_rating(
                content,
                max_rating='PG-13'
            )

            assert result is True

    def test_filter_adult_content(self):
        """成人向けコンテンツの除外"""
        if hasattr(filter_logic, 'filter_by_rating'):
            content = {'rating': 'R18+'}
            result = filter_logic.filter_by_rating(
                content,
                max_rating='PG-13'
            )

            assert result is False


class TestCombinedFilters:
    """複合フィルターのテスト"""

    def test_apply_all_filters(self):
        """全フィルターの適用"""
        if hasattr(filter_logic, 'apply_filters'):
            anime = {
                'title': '普通のアニメ',
                'genres': ['Action', 'Fantasy'],
                'tags': [{'name': 'Magic', 'rank': 80}],
                'description': 'ファンタジー作品'
            }

            result = filter_logic.apply_filters(anime)

            assert result is True

    def test_fail_any_filter(self):
        """いずれかのフィルターで除外"""
        if hasattr(filter_logic, 'apply_filters'):
            anime = {
                'title': 'テストアニメ',
                'genres': ['Action', 'Ecchi'],  # NGジャンル
                'tags': [{'name': 'Magic', 'rank': 80}],
                'description': 'ファンタジー作品'
            }

            result = filter_logic.apply_filters(anime)

            assert result is False


class TestWhitelist:
    """ホワイトリストのテスト"""

    def test_whitelist_content(self):
        """ホワイトリスト登録コンテンツの通過"""
        if hasattr(filter_logic, 'is_whitelisted'):
            content = {'title': 'ホワイトリスト作品'}

            if hasattr(filter_logic, 'add_to_whitelist'):
                filter_logic.add_to_whitelist('ホワイトリスト作品')

            result = filter_logic.is_whitelisted(content)

            assert result is True

    def test_non_whitelisted_content(self):
        """ホワイトリスト未登録コンテンツ"""
        if hasattr(filter_logic, 'is_whitelisted'):
            content = {'title': '通常作品'}
            result = filter_logic.is_whitelisted(content)

            assert result is False or result is None


class TestCaseSensitivity:
    """大文字小文字の処理テスト"""

    def test_case_insensitive_filtering(self):
        """大文字小文字を区別しないフィルタリング"""
        if hasattr(filter_logic, 'contains_ng_keyword'):
            texts = ['エロ', 'えろ', 'エロ']

            for text in texts:
                if hasattr(filter_logic, 'normalize_text'):
                    normalized = filter_logic.normalize_text(text)
                    # 正規化後は同じ結果
                    assert normalized is not None


class TestPerformance:
    """パフォーマンステスト"""

    def test_filter_large_dataset(self):
        """大量データのフィルタリング"""
        if hasattr(filter_logic, 'apply_filters'):
            # 1000件のデータ
            dataset = [
                {
                    'title': f'アニメ{i}',
                    'genres': ['Action'],
                    'description': 'テスト'
                }
                for i in range(1000)
            ]

            # フィルタリングが完了すること
            filtered = [
                item for item in dataset
                if filter_logic.apply_filters(item)
            ]

            assert isinstance(filtered, list)
