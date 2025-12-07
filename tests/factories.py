"""
Test Data Factories

factory_boyを使用したテストデータ生成ファクトリー
"""

import factory
from factory import fuzzy
from datetime import datetime, timedelta
import random


class WorkFactory(factory.Factory):
    """作品データのファクトリー"""

    class Meta:
        model = dict

    id = factory.Sequence(lambda n: n + 1)
    title = factory.Faker('sentence', nb_words=3, locale='ja_JP')
    title_kana = factory.Faker('sentence', nb_words=3, locale='ja_JP')
    title_en = factory.Faker('sentence', nb_words=3)
    type = factory.Iterator(['anime', 'manga'])
    official_url = factory.Faker('url')
    created_at = factory.LazyFunction(datetime.now)


class AnimeWorkFactory(WorkFactory):
    """アニメ作品専用ファクトリー"""

    type = 'anime'
    genre = factory.List([
        factory.Faker('random_element', elements=['アクション', 'コメディ', 'ドラマ', 'SF', 'ファンタジー'])
        for _ in range(random.randint(1, 3))
    ])
    studio = factory.Faker('company', locale='ja_JP')
    season = factory.Faker('random_element', elements=['春', '夏', '秋', '冬'])
    year = factory.Faker('random_int', min=2020, max=2025)


class MangaWorkFactory(WorkFactory):
    """マンガ作品専用ファクトリー"""

    type = 'manga'
    genre = factory.List([
        factory.Faker('random_element', elements=['少年', '少女', '青年', '女性', 'BL'])
        for _ in range(random.randint(1, 2))
    ])
    publisher = factory.Faker('company', locale='ja_JP')
    author = factory.Faker('name', locale='ja_JP')


class ReleaseFactory(factory.Factory):
    """リリース情報のファクトリー"""

    class Meta:
        model = dict

    id = factory.Sequence(lambda n: n + 1)
    work_id = factory.Faker('random_int', min=1, max=1000)
    release_type = factory.Iterator(['episode', 'volume'])
    number = factory.Sequence(lambda n: str(n))
    platform = factory.Faker('random_element', elements=[
        'dアニメストア',
        'Netflix',
        'Amazon Prime Video',
        'BookWalker',
        '楽天Kobo'
    ])
    release_date = factory.LazyFunction(
        lambda: datetime.now() + timedelta(days=random.randint(0, 90))
    )
    source = factory.Faker('random_element', elements=[
        'anilist',
        'syobocal',
        'rss',
        'danime',
        'netflix',
        'prime'
    ])
    source_url = factory.Faker('url')
    notified = False
    created_at = factory.LazyFunction(datetime.now)


class EpisodeReleaseFactory(ReleaseFactory):
    """エピソードリリース専用ファクトリー"""

    release_type = 'episode'
    platform = factory.Faker('random_element', elements=[
        'dアニメストア',
        'Netflix',
        'Amazon Prime Video',
        'ABEMA',
        'U-NEXT'
    ])


class VolumeReleaseFactory(ReleaseFactory):
    """巻数リリース専用ファクトリー"""

    release_type = 'volume'
    platform = factory.Faker('random_element', elements=[
        'BookWalker',
        '楽天Kobo',
        'Kindle',
        'マガポケ',
        'ジャンプBOOKストア'
    ])


class UserFactory(factory.Factory):
    """ユーザーデータのファクトリー"""

    class Meta:
        model = dict

    id = factory.Sequence(lambda n: n + 1)
    email = factory.Faker('email')
    username = factory.Faker('user_name')
    is_active = True
    created_at = factory.LazyFunction(datetime.now)


class NotificationFactory(factory.Factory):
    """通知データのファクトリー"""

    class Meta:
        model = dict

    id = factory.Sequence(lambda n: n + 1)
    user_id = factory.Faker('random_int', min=1, max=100)
    release_id = factory.Faker('random_int', min=1, max=1000)
    notification_type = factory.Iterator(['email', 'calendar', 'both'])
    status = factory.Iterator(['pending', 'sent', 'failed'])
    sent_at = factory.Maybe(
        'status',
        yes_declaration=factory.LazyFunction(datetime.now),
        no_declaration=None
    )
    created_at = factory.LazyFunction(datetime.now)


class SettingsFactory(factory.Factory):
    """設定データのファクトリー"""

    class Meta:
        model = dict

    id = factory.Sequence(lambda n: n + 1)
    user_id = factory.Faker('random_int', min=1, max=100)
    notification_enabled = True
    email_enabled = True
    calendar_enabled = True
    ng_keywords = factory.List([
        factory.Faker('word')
        for _ in range(random.randint(0, 5))
    ])
    platforms = factory.List([
        factory.Faker('random_element', elements=[
            'dアニメストア',
            'Netflix',
            'Amazon Prime Video',
            'BookWalker'
        ])
        for _ in range(random.randint(1, 3))
    ])
    updated_at = factory.LazyFunction(datetime.now)


class APIResponseFactory(factory.Factory):
    """API レスポンスのファクトリー"""

    class Meta:
        model = dict

    status = 'success'
    data = factory.Dict({})
    message = None
    timestamp = factory.LazyFunction(datetime.now)


class ErrorResponseFactory(APIResponseFactory):
    """エラーレスポンス専用ファクトリー"""

    status = 'error'
    data = None
    message = factory.Faker('sentence')
    error_code = factory.Faker('random_element', elements=[
        'VALIDATION_ERROR',
        'NOT_FOUND',
        'INTERNAL_ERROR',
        'UNAUTHORIZED',
        'FORBIDDEN'
    ])


# ファクトリー使用例
def create_test_work(**kwargs):
    """テスト用作品データを生成"""
    return WorkFactory(**kwargs)


def create_test_anime(**kwargs):
    """テスト用アニメデータを生成"""
    return AnimeWorkFactory(**kwargs)


def create_test_manga(**kwargs):
    """テスト用マンガデータを生成"""
    return MangaWorkFactory(**kwargs)


def create_test_release(**kwargs):
    """テスト用リリースデータを生成"""
    return ReleaseFactory(**kwargs)


def create_test_episode(**kwargs):
    """テスト用エピソードデータを生成"""
    return EpisodeReleaseFactory(**kwargs)


def create_test_volume(**kwargs):
    """テスト用巻数データを生成"""
    return VolumeReleaseFactory(**kwargs)


def create_batch_works(count=10, work_type=None):
    """複数の作品データを一括生成"""
    if work_type == 'anime':
        return [AnimeWorkFactory() for _ in range(count)]
    elif work_type == 'manga':
        return [MangaWorkFactory() for _ in range(count)]
    else:
        return [WorkFactory() for _ in range(count)]


def create_batch_releases(count=10, release_type=None):
    """複数のリリースデータを一括生成"""
    if release_type == 'episode':
        return [EpisodeReleaseFactory() for _ in range(count)]
    elif release_type == 'volume':
        return [VolumeReleaseFactory() for _ in range(count)]
    else:
        return [ReleaseFactory() for _ in range(count)]
