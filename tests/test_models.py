"""
データモデルのテスト
modules/models.py のデータクラスとバリデーションロジックをテスト
"""
import pytest
import sys
from datetime import datetime, date
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.models import (
    Work,
    Release,
    AniListWork,
    RSSFeedItem,
    WorkType,
    ReleaseType,
    DataSource,
    DataValidator,
    DataNormalizer,
)


class TestWorkType:
    """WorkType Enumのテスト"""

    def test_work_type_values(self):
        """WorkTypeの値が正しいことを確認"""
        assert WorkType.ANIME.value == "anime"
        assert WorkType.MANGA.value == "manga"

    def test_work_type_from_string(self):
        """文字列からWorkTypeを取得"""
        assert WorkType("anime") == WorkType.ANIME
        assert WorkType("manga") == WorkType.MANGA

    def test_work_type_invalid(self):
        """無効な値でエラーになることを確認"""
        with pytest.raises(ValueError):
            WorkType("invalid")


class TestReleaseType:
    """ReleaseType Enumのテスト"""

    def test_release_type_values(self):
        """ReleaseTypeの値が正しいことを確認"""
        assert ReleaseType.EPISODE.value == "episode"
        assert ReleaseType.VOLUME.value == "volume"

    def test_release_type_from_string(self):
        """文字列からReleaseTypeを取得"""
        assert ReleaseType("episode") == ReleaseType.EPISODE
        assert ReleaseType("volume") == ReleaseType.VOLUME


class TestDataSource:
    """DataSource Enumのテスト"""

    def test_data_source_values(self):
        """DataSourceの主要な値が正しいことを確認"""
        assert DataSource.ANILIST.value == "anilist"
        assert DataSource.SYOBOI.value == "syoboi_calendar"
        assert DataSource.RSS_DANIME.value == "danime_rss"
        assert DataSource.RSS_BOOKWALKER.value == "bookwalker_rss"

    def test_all_sources_unique(self):
        """すべてのデータソースが一意であることを確認"""
        values = [source.value for source in DataSource]
        assert len(values) == len(set(values))


class TestWorkModel:
    """Workデータモデルのテスト"""

    def test_create_work_anime(self):
        """アニメ作品の作成"""
        work = Work(
            title="進撃の巨人",
            work_type=WorkType.ANIME,
            title_kana="しんげきのきょじん",
            title_en="Attack on Titan",
            official_url="https://example.com",
        )

        assert work.title == "進撃の巨人"
        assert work.work_type == WorkType.ANIME
        assert work.title_kana == "しんげきのきょじん"
        assert work.title_en == "Attack on Titan"
        assert work.official_url == "https://example.com"

    def test_create_work_manga(self):
        """マンガ作品の作成"""
        work = Work(title="ワンピース", work_type=WorkType.MANGA)

        assert work.title == "ワンピース"
        assert work.work_type == WorkType.MANGA

    def test_work_title_required(self):
        """タイトルが必須であることを確認"""
        with pytest.raises(ValueError, match="Title is required"):
            Work(title="", work_type=WorkType.ANIME)

    def test_work_title_empty_after_strip(self):
        """空白文字のみのタイトルでエラーになることを確認"""
        with pytest.raises(ValueError, match="Title is required"):
            Work(title="   ", work_type=WorkType.ANIME)

    def test_work_title_stripped(self):
        """タイトルの前後の空白が削除されることを確認"""
        work = Work(title="  テストタイトル  ", work_type=WorkType.ANIME)
        assert work.title == "テストタイトル"

    def test_work_type_string_conversion(self):
        """文字列のwork_typeが自動変換されることを確認"""
        work = Work(title="テスト", work_type="anime")
        assert work.work_type == WorkType.ANIME

        work = Work(title="テスト", work_type="manga")
        assert work.work_type == WorkType.MANGA

    def test_work_type_invalid_string(self):
        """無効なwork_type文字列でエラーになることを確認"""
        with pytest.raises(ValueError, match="Invalid work_type"):
            Work(title="テスト", work_type="invalid")

    def test_work_invalid_url(self):
        """無効なURLがNoneに変換されることを確認"""
        work = Work(
            title="テスト", work_type=WorkType.ANIME, official_url="not_a_valid_url"
        )
        assert work.official_url is None

    def test_work_valid_url(self):
        """有効なURLが保持されることを確認"""
        url = "https://example.com/anime"
        work = Work(title="テスト", work_type=WorkType.ANIME, official_url=url)
        assert work.official_url == url

    def test_work_to_dict(self):
        """Work.to_dict()が正しい辞書を返すことを確認"""
        work = Work(
            id=1,
            title="テストアニメ",
            work_type=WorkType.ANIME,
            title_kana="てすとあにめ",
            title_en="Test Anime",
            official_url="https://example.com",
        )

        result = work.to_dict()

        assert result["id"] == 1
        assert result["title"] == "テストアニメ"
        assert result["type"] == "anime"
        assert result["title_kana"] == "てすとあにめ"
        assert result["title_en"] == "Test Anime"
        assert result["official_url"] == "https://example.com"

    def test_work_from_dict(self):
        """Work.from_dict()が正しくインスタンスを作成することを確認"""
        data = {
            "id": 1,
            "title": "テストアニメ",
            "type": "anime",
            "title_kana": "てすとあにめ",
            "title_en": "Test Anime",
            "official_url": "https://example.com",
            "created_at": datetime.now(),
        }

        work = Work.from_dict(data)

        assert work.id == 1
        assert work.title == "テストアニメ"
        assert work.work_type == WorkType.ANIME
        assert work.title_kana == "てすとあにめ"
        assert work.title_en == "Test Anime"

    def test_work_metadata(self):
        """metadataが正しく保存されることを確認"""
        work = Work(
            title="テスト",
            work_type=WorkType.ANIME,
            metadata={"anilist_id": 12345, "genres": ["Action", "Adventure"]},
        )

        assert work.metadata["anilist_id"] == 12345
        assert "Action" in work.metadata["genres"]


class TestReleaseModel:
    """Releaseデータモデルのテスト"""

    def test_create_release_episode(self):
        """エピソードリリースの作成"""
        release = Release(
            work_id=1,
            release_type=ReleaseType.EPISODE,
            number="1",
            platform="Netflix",
            release_date=date(2025, 12, 15),
            source="anilist",
            source_url="https://example.com",
        )

        assert release.work_id == 1
        assert release.release_type == ReleaseType.EPISODE
        assert release.number == "1"
        assert release.platform == "Netflix"
        assert release.release_date == date(2025, 12, 15)
        assert release.notified is False

    def test_create_release_volume(self):
        """巻数リリースの作成"""
        release = Release(
            work_id=2, release_type=ReleaseType.VOLUME, number="5", platform="BookWalker"
        )

        assert release.work_id == 2
        assert release.release_type == ReleaseType.VOLUME
        assert release.number == "5"

    def test_release_work_id_required(self):
        """work_idが必須であることを確認"""
        with pytest.raises(ValueError, match="Valid work_id is required"):
            Release(work_id=0, release_type=ReleaseType.EPISODE)

    def test_release_work_id_negative(self):
        """負のwork_idでエラーになることを確認"""
        with pytest.raises(ValueError, match="Valid work_id is required"):
            Release(work_id=-1, release_type=ReleaseType.EPISODE)

    def test_release_type_string_conversion(self):
        """文字列のrelease_typeが自動変換されることを確認"""
        release = Release(work_id=1, release_type="episode")
        assert release.release_type == ReleaseType.EPISODE

        release = Release(work_id=1, release_type="volume")
        assert release.release_type == ReleaseType.VOLUME

    def test_release_type_invalid_string(self):
        """無効なrelease_type文字列でエラーになることを確認"""
        with pytest.raises(ValueError, match="Invalid release_type"):
            Release(work_id=1, release_type="invalid")

    def test_release_number_normalization(self):
        """numberフィールドが正規化されることを確認"""
        release = Release(work_id=1, release_type=ReleaseType.EPISODE, number="  12  ")
        assert release.number == "12"

    def test_release_number_integer_conversion(self):
        """整数のnumberが文字列に変換されることを確認"""
        release = Release(work_id=1, release_type=ReleaseType.EPISODE, number=5)
        assert release.number == "5"

    def test_release_date_string_parsing(self):
        """日付文字列がdate型に変換されることを確認"""
        # ISO format
        release = Release(
            work_id=1, release_type=ReleaseType.EPISODE, release_date="2025-12-15"
        )
        assert release.release_date == date(2025, 12, 15)

        # Slash format
        release = Release(
            work_id=1, release_type=ReleaseType.EPISODE, release_date="2025/12/15"
        )
        assert release.release_date == date(2025, 12, 15)

    def test_release_date_japanese_format(self):
        """日本語形式の日付がパースされることを確認"""
        release = Release(
            work_id=1, release_type=ReleaseType.EPISODE, release_date="2025年12月15日"
        )
        assert release.release_date == date(2025, 12, 15)

    def test_release_date_invalid_string(self):
        """無効な日付文字列がNoneになることを確認"""
        release = Release(
            work_id=1,
            release_type=ReleaseType.EPISODE,
            release_date="invalid date string",
        )
        assert release.release_date is None

    def test_release_to_dict(self):
        """Release.to_dict()が正しい辞書を返すことを確認"""
        release = Release(
            id=1,
            work_id=10,
            release_type=ReleaseType.EPISODE,
            number="3",
            platform="dアニメストア",
            release_date=date(2025, 12, 20),
            source="anilist",
            source_url="https://example.com",
            notified=True,
        )

        result = release.to_dict()

        assert result["id"] == 1
        assert result["work_id"] == 10
        assert result["release_type"] == "episode"
        assert result["number"] == "3"
        assert result["platform"] == "dアニメストア"
        assert result["release_date"] == "2025-12-20"
        assert result["source"] == "anilist"
        assert result["notified"] == 1

    def test_release_from_dict(self):
        """Release.from_dict()が正しくインスタンスを作成することを確認"""
        data = {
            "id": 1,
            "work_id": 10,
            "release_type": "episode",
            "number": "3",
            "platform": "Netflix",
            "release_date": date(2025, 12, 20),
            "source": "anilist",
            "source_url": "https://example.com",
            "notified": 1,
            "created_at": datetime.now(),
        }

        release = Release.from_dict(data)

        assert release.id == 1
        assert release.work_id == 10
        assert release.release_type == ReleaseType.EPISODE
        assert release.number == "3"
        assert release.notified is True

    def test_release_notified_false(self):
        """notifiedフィールドがFalseになることを確認"""
        data = {
            "work_id": 1,
            "release_type": "episode",
            "notified": 0,
        }

        release = Release.from_dict(data)
        assert release.notified is False


class TestAniListWork:
    """AniListWorkデータモデルのテスト"""

    def test_create_anilist_work(self):
        """AniListWork作成テスト"""
        work = AniListWork(
            id=12345,
            title_romaji="Shingeki no Kyojin",
            title_english="Attack on Titan",
            title_native="進撃の巨人",
            description="A story about titans",
            genres=["Action", "Drama"],
            tags=["Military", "Survival"],
            status="FINISHED",
            site_url="https://anilist.co/anime/12345",
        )

        assert work.id == 12345
        assert work.title_romaji == "Shingeki no Kyojin"
        assert work.title_english == "Attack on Titan"
        assert "Action" in work.genres

    def test_anilist_work_to_work_with_english(self):
        """英語タイトルがある場合のWork変換"""
        anilist_work = AniListWork(
            id=1,
            title_romaji="Romaji Title",
            title_english="English Title",
            title_native="日本語タイトル",
        )

        work = anilist_work.to_work()

        # 英語タイトルが優先される
        assert work.title == "English Title"
        assert work.work_type == WorkType.ANIME
        assert work.title_en == "English Title"
        assert work.title_kana == "日本語タイトル"

    def test_anilist_work_to_work_without_english(self):
        """英語タイトルがない場合のWork変換"""
        anilist_work = AniListWork(
            id=1, title_romaji="Romaji Title", title_native="日本語タイトル"
        )

        work = anilist_work.to_work()

        # ローマ字タイトルが使われる
        assert work.title == "Romaji Title"

    def test_anilist_work_metadata(self):
        """AniListWorkのメタデータがWorkに保存されることを確認"""
        anilist_work = AniListWork(
            id=1,
            title_romaji="Test",
            description="Test description",
            genres=["Action"],
            tags=["Military"],
            status="RELEASING",
        )

        work = anilist_work.to_work()

        assert work.metadata["anilist_id"] == 1
        assert work.metadata["description"] == "Test description"
        assert "Action" in work.metadata["genres"]
        assert work.metadata["status"] == "RELEASING"


class TestRSSFeedItem:
    """RSSFeedItemデータモデルのテスト"""

    def test_create_rss_feed_item(self):
        """RSSFeedItemの作成"""
        item = RSSFeedItem(
            title="「進撃の巨人」第1話",
            link="https://example.com/episode1",
            description="第1話の配信開始",
            published=datetime(2025, 12, 15, 12, 0, 0),
            category="anime",
        )

        assert item.title == "「進撃の巨人」第1話"
        assert item.link == "https://example.com/episode1"
        assert item.published.year == 2025

    def test_extract_work_info_japanese_brackets(self):
        """日本語括弧からタイトルを抽出"""
        item = RSSFeedItem(title="「進撃の巨人」第1話配信開始")
        info = item.extract_work_info()

        assert info is not None
        assert info["title"] == "進撃の巨人"

    def test_extract_work_info_english_quotes(self):
        """英語引用符からタイトルを抽出"""
        item = RSSFeedItem(title='"Attack on Titan" Episode 1')
        info = item.extract_work_info()

        assert info is not None
        assert info["title"] == "Attack on Titan"

    def test_extract_episode_number_japanese(self):
        """日本語形式のエピソード番号を抽出"""
        item = RSSFeedItem(title="「テストアニメ」第5話")
        info = item.extract_work_info()

        assert info["number"] == "5"
        assert info["release_type"] == ReleaseType.EPISODE

    def test_extract_episode_number_english(self):
        """英語形式のエピソード番号を抽出"""
        item = RSSFeedItem(title='"Test Anime" Episode 12')
        info = item.extract_work_info()

        assert info["number"] == "12"
        assert info["release_type"] == ReleaseType.EPISODE

    def test_extract_volume_number_japanese(self):
        """日本語形式の巻数を抽出"""
        item = RSSFeedItem(title="「テストマンガ」第3巻発売")
        info = item.extract_work_info()

        assert info["number"] == "3"
        assert info["release_type"] == ReleaseType.VOLUME

    def test_extract_volume_number_english(self):
        """英語形式の巻数を抽出"""
        item = RSSFeedItem(title='"Test Manga" Vol. 8')
        info = item.extract_work_info()

        assert info["number"] == "8"
        assert info["release_type"] == ReleaseType.VOLUME

    def test_extract_work_info_with_published_date(self):
        """公開日が含まれることを確認"""
        published = datetime(2025, 12, 25, 10, 30, 0)
        item = RSSFeedItem(title="「テスト」第1話", published=published)
        info = item.extract_work_info()

        assert info["release_date"] == date(2025, 12, 25)

    def test_extract_work_info_no_title(self):
        """タイトルがない場合Noneを返すことを確認"""
        item = RSSFeedItem(title=None)
        info = item.extract_work_info()

        assert info is None


class TestDataValidator:
    """DataValidatorのテスト"""

    def test_validate_work_valid(self):
        """有効な作品データの検証"""
        work_data = {"title": "テストアニメ", "type": "anime"}

        errors = DataValidator.validate_work(work_data)

        assert len(errors) == 0

    def test_validate_work_missing_title(self):
        """タイトルが欠けている場合のエラー"""
        work_data = {"type": "anime"}

        errors = DataValidator.validate_work(work_data)

        assert len(errors) > 0
        assert any("Title is required" in error for error in errors)

    def test_validate_work_empty_title(self):
        """空のタイトルの場合のエラー"""
        work_data = {"title": "", "type": "anime"}

        errors = DataValidator.validate_work(work_data)

        assert len(errors) > 0
        assert any("Title is required" in error for error in errors)

    def test_validate_work_invalid_type(self):
        """無効なwork_typeの場合のエラー"""
        work_data = {"title": "テスト", "type": "invalid"}

        errors = DataValidator.validate_work(work_data)

        assert len(errors) > 0
        assert any("work_type" in error for error in errors)

    def test_validate_work_missing_type(self):
        """work_typeが欠けている場合のエラー"""
        work_data = {"title": "テスト"}

        errors = DataValidator.validate_work(work_data)

        assert len(errors) > 0

    def test_validate_release_valid(self):
        """有効なリリースデータの検証"""
        release_data = {"work_id": 1, "release_type": "episode"}

        errors = DataValidator.validate_release(release_data)

        assert len(errors) == 0

    def test_validate_release_missing_work_id(self):
        """work_idが欠けている場合のエラー"""
        release_data = {"release_type": "episode"}

        errors = DataValidator.validate_release(release_data)

        assert len(errors) > 0
        assert any("work_id is required" in error for error in errors)

    def test_validate_release_invalid_type(self):
        """無効なrelease_typeの場合のエラー"""
        release_data = {"work_id": 1, "release_type": "invalid"}

        errors = DataValidator.validate_release(release_data)

        assert len(errors) > 0
        assert any("release_type" in error for error in errors)


class TestDataNormalizer:
    """DataNormalizerのテスト"""

    def test_normalize_title_trim_whitespace(self):
        """前後の空白が削除されることを確認"""
        result = DataNormalizer.normalize_title("  テストタイトル  ")
        assert result == "テストタイトル"

    def test_normalize_title_collapse_whitespace(self):
        """連続する空白が1つに統合されることを確認"""
        result = DataNormalizer.normalize_title("テスト    タイトル")
        assert result == "テスト タイトル"

    def test_normalize_title_remove_brackets(self):
        """括弧付きプレフィックスが削除されることを確認"""
        result = DataNormalizer.normalize_title("[新作] テストアニメ")
        assert result == "テストアニメ"

        result = DataNormalizer.normalize_title("【速報】テストアニメ")
        assert result == "テストアニメ"

    def test_normalize_title_empty_string(self):
        """空文字列の処理"""
        result = DataNormalizer.normalize_title("")
        assert result == ""

    def test_normalize_title_none(self):
        """Noneの処理"""
        result = DataNormalizer.normalize_title(None)
        assert result == ""

    def test_extract_season_info_season_number(self):
        """シーズン番号の抽出"""
        info = DataNormalizer.extract_season_info("進撃の巨人 第2期")
        assert info["season_number"] == 2

        info = DataNormalizer.extract_season_info("Attack on Titan Season 3")
        assert info["season_number"] == 3

    def test_extract_season_info_sequel(self):
        """続編情報の抽出"""
        info = DataNormalizer.extract_season_info("テストアニメ 続編")
        assert info.get("is_sequel") is True

        info = DataNormalizer.extract_season_info("Test Anime 2nd")
        assert info.get("is_sequel") is True

    def test_extract_season_info_final(self):
        """最終シーズン情報の抽出"""
        info = DataNormalizer.extract_season_info("テストアニメ 完結編")
        assert info.get("is_final") is True

        info = DataNormalizer.extract_season_info("Test Anime Final Season")
        assert info.get("is_final") is True

    def test_extract_season_info_no_match(self):
        """シーズン情報がない場合"""
        info = DataNormalizer.extract_season_info("普通のタイトル")
        assert len(info) == 0


class TestWorkRoundtrip:
    """Work データモデルのラウンドトリップテスト"""

    def test_work_to_dict_from_dict_roundtrip(self):
        """Work → dict → Work の変換が正しく機能することを確認"""
        original = Work(
            id=1,
            title="テストアニメ",
            work_type=WorkType.ANIME,
            title_kana="てすとあにめ",
            title_en="Test Anime",
            official_url="https://example.com",
            created_at=datetime.now(),
        )

        # to_dict() → from_dict()
        data = original.to_dict()
        restored = Work.from_dict(data)

        assert restored.id == original.id
        assert restored.title == original.title
        assert restored.work_type == original.work_type
        assert restored.title_kana == original.title_kana
        assert restored.title_en == original.title_en


class TestReleaseRoundtrip:
    """Release データモデルのラウンドトリップテスト"""

    def test_release_to_dict_from_dict_roundtrip(self):
        """Release → dict → Release の変換が正しく機能することを確認"""
        original = Release(
            id=1,
            work_id=10,
            release_type=ReleaseType.EPISODE,
            number="5",
            platform="Netflix",
            release_date=date(2025, 12, 25),
            source="anilist",
            source_url="https://example.com",
            notified=True,
            created_at=datetime.now(),
        )

        # to_dict() → from_dict()
        data = original.to_dict()
        restored = Release.from_dict(data)

        assert restored.id == original.id
        assert restored.work_id == original.work_id
        assert restored.release_type == original.release_type
        assert restored.number == original.number
        assert restored.platform == original.platform
        assert restored.notified == original.notified


class TestEdgeCases:
    """エッジケースのテスト"""

    def test_work_with_unicode_emoji(self):
        """絵文字を含むタイトルの処理"""
        work = Work(title="テストアニメ 🎬", work_type=WorkType.ANIME)
        assert "🎬" in work.title

    def test_release_with_zero_work_id(self):
        """work_id=0でエラーになることを確認"""
        with pytest.raises(ValueError):
            Release(work_id=0, release_type=ReleaseType.EPISODE)

    def test_release_with_none_work_id(self):
        """work_id=Noneでエラーになることを確認"""
        with pytest.raises((ValueError, TypeError)):
            Release(work_id=None, release_type=ReleaseType.EPISODE)

    def test_work_metadata_default_empty_dict(self):
        """metadataのデフォルトが空の辞書であることを確認"""
        work = Work(title="テスト", work_type=WorkType.ANIME)
        assert work.metadata == {}
        assert isinstance(work.metadata, dict)

    def test_release_metadata_default_empty_dict(self):
        """metadataのデフォルトが空の辞書であることを確認"""
        release = Release(work_id=1, release_type=ReleaseType.EPISODE)
        assert release.metadata == {}
        assert isinstance(release.metadata, dict)
