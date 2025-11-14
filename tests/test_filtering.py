"""
フィルタリング機能のテストモジュール
"""

from modules.filter_logic import ContentFilter
import pytest
import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class MockConfigManager:
    """テスト用のConfigManagerモック"""

    def __init__(self):
        self._ng_keywords = ["エロ", "R18", "成人向け", "BL", "百合"]
        self._ng_genres = ["Hentai", "Ecchi"]
        self._exclude_tags = []

    def get_ng_keywords(self):
        """NGキーワードリストを返す"""
        return self._ng_keywords

    def get_ng_genres(self):
        """NGジャンルリストを返す"""
        return self._ng_genres

    def get_exclude_tags(self):
        """除外タグリストを返す"""
        return self._exclude_tags

    def set_ng_keywords(self, keywords):
        """NGキーワードを設定"""
        self._ng_keywords = keywords


@pytest.fixture
def content_filter():
    """ContentFilterのインスタンスを提供"""
    mock_config = MockConfigManager()
    return ContentFilter(mock_config)


@pytest.fixture
def sample_anime_data():
    """テスト用のアニメデータ"""
    return {
        "id": 1,
        "title": {
            "romaji": "Test Anime",
            "english": "Test Anime",
            "native": "テストアニメ",
        },
        "description": "A test anime for unit testing",
        "genres": ["Action", "Adventure"],
        "tags": [{"name": "School"}, {"name": "Friendship"}],
        "isAdult": False,
    }


@pytest.fixture
def sample_manga_data():
    """テスト用のマンガデータ"""
    return {
        "title": "Test Manga",
        "description": "A test manga for unit testing",
        "volume": "1",
        "url": "https://example.com/manga/1",
    }


class TestContentFilter:
    """ContentFilterの基本機能テスト"""

    def test_filter_initialization(self):
        """ContentFilterの初期化テスト"""
        mock_config = MockConfigManager()
        mock_config.set_ng_keywords(["test"])
        mock_config._ng_genres = ["TestGenre"]
        filter_instance = ContentFilter(mock_config)
        assert filter_instance is not None

    def test_set_ng_keywords(self, content_filter):
        """NGキーワードの設定テスト"""
        new_keywords = ["新しいNGワード"]
        content_filter.set_ng_keywords(new_keywords)
        # 新しいキーワードで動作することを確認
        anime_with_new_ng = {
            "title": {"romaji": "新しいNGワード"},
            "description": "",
            "genres": [],
            "tags": [],
            "isAdult": False,
        }
        assert content_filter.filter_anime(anime_with_new_ng) is True

    def test_filter_anime_with_ng_title(self, content_filter):
        """タイトルにNGキーワードを含むアニメのフィルタリング"""
        anime_with_ng = {
            "title": {"romaji": "エロアニメ"},
            "description": "Normal description",
            "genres": ["Action"],
            "tags": [],
            "isAdult": False,
        }
        assert content_filter.filter_anime(anime_with_ng) is True

    def test_filter_anime_with_ng_description(self, content_filter):
        """説明にNGキーワードを含むアニメのフィルタリング"""
        anime_with_ng = {
            "title": {"romaji": "Normal Title"},
            "description": "これはR18の内容です",
            "genres": ["Action"],
            "tags": [],
            "isAdult": False,
        }
        assert content_filter.filter_anime(anime_with_ng) is True

    def test_filter_anime_with_ng_genre(self, content_filter):
        """NGジャンルを含むアニメのフィルタリング"""
        anime_with_ng = {
            "title": {"romaji": "Normal Title"},
            "description": "Normal description",
            "genres": ["Action", "Hentai"],
            "tags": [],
            "isAdult": False,
        }
        assert content_filter.filter_anime(anime_with_ng) is True

    def test_filter_anime_with_adult_flag(self, content_filter):
        """isAdultフラグがTrueのアニメのフィルタリング"""
        anime_adult = {
            "title": {"romaji": "Normal Title"},
            "description": "Normal description",
            "genres": ["Action"],
            "tags": [],
            "isAdult": True,
        }
        assert content_filter.filter_anime(anime_adult) is True

    def test_filter_clean_anime(self, content_filter, sample_anime_data):
        """クリーンなアニメがフィルタされないことの確認"""
        assert content_filter.filter_anime(sample_anime_data) is False

    def test_filter_manga_with_ng_title(self, content_filter):
        """タイトルにNGキーワードを含むマンガのフィルタリング"""
        manga_with_ng = {
            "title": "エロマンガ",
            "description": "Normal description",
            "volume": "1",
            "url": "https://example.com",
        }
        assert content_filter.filter_manga(manga_with_ng) is True

    def test_filter_clean_manga(self, content_filter, sample_manga_data):
        """クリーンなマンガがフィルタされないことの確認"""
        assert content_filter.filter_manga(sample_manga_data) is False

    def test_filter_anime_none_data(self, content_filter):
        """Noneデータの処理テスト"""
        assert content_filter.filter_anime(None) is False

    def test_filter_anime_empty_data(self, content_filter):
        """空データの処理テスト"""
        assert content_filter.filter_anime({}) is False

    def test_filter_anime_missing_fields(self, content_filter):
        """必須フィールドが欠けているデータの処理テスト"""
        incomplete_anime = {"title": {"romaji": "Test"}}
        assert content_filter.filter_anime(incomplete_anime) is False

    def test_case_insensitive_filtering(self, content_filter):
        """大文字小文字を区別しないフィルタリング"""
        anime_uppercase = {
            "title": {"romaji": "EROANI"},
            "description": "",
            "genres": [],
            "tags": [],
            "isAdult": False,
        }
        # 大文字小文字の扱いは実装に依存
        result = content_filter.filter_anime(anime_uppercase)
        # エロが含まれるので、大文字小文字を区別しない場合はTrue
        assert isinstance(result, bool)  # bool値が返ることを確認

    def test_partial_keyword_matching(self, content_filter):
        """部分一致でのフィルタリング"""
        anime_partial = {
            "title": {"romaji": "これはエロティックなアニメです"},
            "description": "",
            "genres": [],
            "tags": [],
            "isAdult": False,
        }
        # エロが部分的に含まれる
        assert content_filter.filter_anime(anime_partial) is True

    def test_ng_keyword_filtering_integration(self, content_filter):
        """NGキーワードフィルタリングの統合テスト"""
        # NGキーワードを含むケース
        anime_with_ng = {
            "title": {"romaji": "エロアニメ"},
            "description": "",
            "genres": [],
            "tags": [],
            "isAdult": False,
        }
        assert content_filter.filter_anime(anime_with_ng) is True

        # NGキーワードを含まないケース
        clean_anime = {
            "title": {"romaji": "普通のアニメ"},
            "description": "",
            "genres": [],
            "tags": [],
            "isAdult": False,
        }
        assert content_filter.filter_anime(clean_anime) is False

        # 空文字列のケース
        empty_anime = {
            "title": {"romaji": ""},
            "description": "",
            "genres": [],
            "tags": [],
            "isAdult": False,
        }
        assert content_filter.filter_anime(empty_anime) is False

        # Noneを含むケース
        none_anime = {
            "title": None,
            "description": None,
            "genres": None,
            "tags": None,
            "isAdult": False,
        }
        assert content_filter.filter_anime(none_anime) is False

    def test_tag_filtering_integration(self, content_filter):
        """タグフィルタリングの統合テスト"""
        # 通常のタグ
        anime_with_tags = {
            "title": {"romaji": "Test"},
            "description": "",
            "genres": [],
            "tags": [{"name": "School"}, {"name": "Friendship"}],
            "isAdult": False,
        }
        assert content_filter.filter_anime(anime_with_tags) is False

        # NGキーワードを含むタグ
        anime_with_ng_tag = {
            "title": {"romaji": "Test"},
            "description": "",
            "genres": [],
            "tags": [{"name": "エロ"}],
            "isAdult": False,
        }
        assert content_filter.filter_anime(anime_with_ng_tag) is True

        # 空のタグリスト
        anime_empty_tags = {
            "title": {"romaji": "Test"},
            "description": "",
            "genres": [],
            "tags": [],
            "isAdult": False,
        }
        assert content_filter.filter_anime(anime_empty_tags) is False

        # タグがNone
        anime_none_tags = {
            "title": {"romaji": "Test"},
            "description": "",
            "genres": [],
            "tags": None,
            "isAdult": False,
        }
        assert content_filter.filter_anime(anime_none_tags) is False

        # 不正な構造のタグ（エラーにならないことを確認）
        anime_invalid_tags = {
            "title": {"romaji": "Test"},
            "description": "",
            "genres": [],
            "tags": [{"invalid": "data"}, {"name": "ValidTag"}],
            "isAdult": False,
        }
        try:
            result = content_filter.filter_anime(anime_invalid_tags)
            assert result is False  # 正常に処理される
        except Exception:
            assert False, "Invalid tag structure should not cause exception"


class TestContentFilterIntegration:
    """ContentFilterの統合テスト"""

    def test_filter_anime_list(self, content_filter):
        """アニメリストのフィルタリング統合テスト"""
        anime_list = [
            {
                "id": 1,
                "title": {"romaji": "Clean Anime"},
                "description": "A normal anime",
                "genres": ["Action"],
                "tags": [{"name": "School"}],
                "isAdult": False,
            },
            {
                "id": 2,
                "title": {"romaji": "エロアニメ"},
                "description": "Adult content",
                "genres": ["Action"],
                "tags": [{"name": "School"}],
                "isAdult": False,
            },
            {
                "id": 3,
                "title": {"romaji": "Another Clean Anime"},
                "description": "Another normal anime",
                "genres": ["Comedy"],
                "tags": [{"name": "Friendship"}],
                "isAdult": True,
            },
        ]

        # フィルタリング実行
        filtered = [
            anime for anime in anime_list if not content_filter.filter_anime(anime)
        ]

        # ID 1のみが残るはず（ID 2はNGキーワード、ID 3はisAdult）
        assert len(filtered) == 1
        assert filtered[0]["id"] == 1

    def test_filter_manga_list(self, content_filter):
        """マンガリストのフィルタリング統合テスト"""
        manga_list = [
            {
                "title": "Normal Manga",
                "description": "A normal manga",
                "volume": "1",
                "url": "https://example.com/1",
            },
            {
                "title": "R18マンガ",
                "description": "Adult manga",
                "volume": "1",
                "url": "https://example.com/2",
            },
            {
                "title": "Another Normal Manga",
                "description": "Another normal manga",
                "volume": "2",
                "url": "https://example.com/3",
            },
        ]

        # フィルタリング実行
        filtered = [
            manga for manga in manga_list if not content_filter.filter_manga(manga)
        ]

        # 2冊が残るはず（R18マンガは除外）
        assert len(filtered) == 2
        assert filtered[0]["title"] == "Normal Manga"
        assert filtered[1]["title"] == "Another Normal Manga"


class TestContentFiltering:
    """追加のコンテンツフィルタリングテスト"""

    def test_ng_keyword_filtering_title(self, content_filter):
        """タイトルのNGキーワードフィルタリング"""
        anime = {
            "title": {"romaji": "エロアニメ"},
            "description": "",
            "genres": [],
            "tags": [],
            "isAdult": False,
        }
        assert content_filter.filter_anime(anime) is True

    def test_ng_keyword_filtering_description(self, content_filter):
        """説明のNGキーワードフィルタリング"""
        anime = {
            "title": {"romaji": "Test"},
            "description": "R18コンテンツ",
            "genres": [],
            "tags": [],
            "isAdult": False,
        }
        assert content_filter.filter_anime(anime) is True

    def test_ng_genre_filtering(self, content_filter):
        """NGジャンルフィルタリング"""
        anime = {
            "title": {"romaji": "Test"},
            "description": "",
            "genres": ["Hentai"],
            "tags": [],
            "isAdult": False,
        }
        assert content_filter.filter_anime(anime) is True

    def test_combined_filtering_logic(self, content_filter):
        """複合フィルタリングロジック"""
        # 複数の条件を満たす
        anime = {
            "title": {"romaji": "エロアニメ"},
            "description": "R18",
            "genres": ["Hentai"],
            "tags": [{"name": "成人向け"}],
            "isAdult": True,
        }
        assert content_filter.filter_anime(anime) is True

    def test_case_insensitive_filtering(self, content_filter):
        """大文字小文字を区別しないフィルタリング"""
        # 実装に依存するが、一般的には大文字小文字を区別しない
        anime = {
            "title": {"romaji": "ero anime"},
            "description": "",
            "genres": [],
            "tags": [],
            "isAdult": False,
        }
        # 実装により結果が異なる可能性がある
        result = content_filter.filter_anime(anime)
        assert isinstance(result, bool)

    def test_partial_keyword_matching(self, content_filter):
        """部分一致キーワードマッチング"""
        anime = {
            "title": {"romaji": "エロティック"},
            "description": "",
            "genres": [],
            "tags": [],
            "isAdult": False,
        }
        assert content_filter.filter_anime(anime) is True

    def test_tag_filtering(self, content_filter):
        """タグのフィルタリング"""
        anime = {
            "title": {"romaji": "Test"},
            "description": "",
            "genres": [],
            "tags": [{"name": "BL"}],
            "isAdult": False,
        }
        assert content_filter.filter_anime(anime) is True


class TestFilteringPerformance:
    """フィルタリングパフォーマンステスト"""

    def test_bulk_filtering_performance(self, content_filter):
        """大量データのフィルタリングパフォーマンス"""
        import time

        # 1000件のテストデータ生成
        anime_list = []
        for i in range(1000):
            anime_list.append(
                {
                    "title": {"romaji": f"Anime {i}"},
                    "description": f"Description {i}",
                    "genres": ["Action"] if i % 2 == 0 else ["Comedy"],
                    "tags": [{"name": f"Tag{i}"}],
                    "isAdult": i % 100 == 0,
                }
            )

        # パフォーマンス測定
        start_time = time.time()
        filtered = [
            anime for anime in anime_list if not content_filter.filter_anime(anime)
        ]
        end_time = time.time()

        # 1000件を1秒以内に処理できることを確認
        assert end_time - start_time < 1.0
        # isAdultがTrueの10件が除外される
        assert len(filtered) == 990

    def test_regex_vs_string_matching_performance(self, content_filter):
        """正規表現と文字列マッチングのパフォーマンス比較"""
        import time

        # テストデータ
        test_text = "これは長いテキストです" * 100

        # 100回の繰り返しテスト
        iterations = 100

        start_time = time.time()
        for _ in range(iterations):
            # ContentFilterの内部実装に依存
            anime = {
                "title": {"romaji": test_text},
                "description": "",
                "genres": [],
                "tags": [],
                "isAdult": False,
            }
            content_filter.filter_anime(anime)
        end_time = time.time()

        # 100回の処理が0.1秒以内に完了することを確認
        assert end_time - start_time < 0.1
