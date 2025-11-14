#!/usr/bin/env python3
"""
サンプルデータ投入スクリプト
"""

import logging
from datetime import datetime, timedelta
import random

# モジュールのインポート
from modules import get_db

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# サンプルアニメデータ
SAMPLE_ANIME = [
    {
        'title': '葬送のフリーレン',
        'title_kana': 'そうそうのふりーれん',
        'title_en': 'Frieren: Beyond Journey\'s End',
        'type': 'anime',
        'official_url': 'https://frieren-anime.jp/',
        'releases': [
            {'release_type': 'episode', 'number': '29', 'platform': 'dアニメストア', 'release_date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')},
            {'release_type': 'episode', 'number': '30', 'platform': 'dアニメストア', 'release_date': (datetime.now() + timedelta(days=8)).strftime('%Y-%m-%d')},
        ]
    },
    {
        'title': '薬屋のひとりごと',
        'title_kana': 'くすりやのひとりごと',
        'title_en': 'The Apothecary Diaries',
        'type': 'anime',
        'official_url': 'https://kusuriyanohitorigoto.jp/',
        'releases': [
            {'release_type': 'episode', 'number': '25', 'platform': 'Netflix', 'release_date': (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')},
            {'release_type': 'episode', 'number': '26', 'platform': 'Netflix', 'release_date': (datetime.now() + timedelta(days=9)).strftime('%Y-%m-%d')},
        ]
    },
    {
        'title': '僕のヒーローアカデミア',
        'title_kana': 'ぼくのひーろーあかでみあ',
        'title_en': 'My Hero Academia',
        'type': 'anime',
        'official_url': 'https://heroaca.com/',
        'releases': [
            {'release_type': 'episode', 'number': '151', 'platform': 'dアニメストア', 'release_date': (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')},
            {'release_type': 'episode', 'number': '152', 'platform': 'dアニメストア', 'release_date': (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d')},
        ]
    },
    {
        'title': 'SPY×FAMILY',
        'title_kana': 'すぱいふぁみりー',
        'title_en': 'Spy x Family',
        'type': 'anime',
        'official_url': 'https://spy-family.net/',
        'releases': [
            {'release_type': 'episode', 'number': '38', 'platform': 'Amazon Prime', 'release_date': (datetime.now() + timedelta(days=4)).strftime('%Y-%m-%d')},
        ]
    },
    {
        'title': '【推しの子】',
        'title_kana': 'おしのこ',
        'title_en': 'Oshi no Ko',
        'type': 'anime',
        'official_url': 'https://ichigoproduction.com/',
        'releases': [
            {'release_type': 'episode', 'number': '25', 'platform': 'dアニメストア', 'release_date': (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d')},
        ]
    },
    {
        'title': 'ダンジョン飯',
        'title_kana': 'だんじょんめし',
        'title_en': 'Delicious in Dungeon',
        'type': 'anime',
        'official_url': 'https://delicious-in-dungeon.com/',
        'releases': [
            {'release_type': 'episode', 'number': '25', 'platform': 'Netflix', 'release_date': (datetime.now() + timedelta(days=6)).strftime('%Y-%m-%d')},
        ]
    },
    {
        'title': '呪術廻戦',
        'title_kana': 'じゅじゅつかいせん',
        'title_en': 'Jujutsu Kaisen',
        'type': 'anime',
        'official_url': 'https://jujutsukaisen.jp/',
        'releases': [
            {'release_type': 'episode', 'number': '48', 'platform': 'dアニメストア', 'release_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')},
        ]
    },
]

# サンプルマンガデータ
SAMPLE_MANGA = [
    {
        'title': 'ワンピース',
        'title_kana': 'わんぴーす',
        'title_en': 'One Piece',
        'type': 'manga',
        'official_url': 'https://one-piece.com/',
        'releases': [
            {'release_type': 'volume', 'number': '108', 'platform': 'BookWalker', 'release_date': (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')},
            {'release_type': 'volume', 'number': '108', 'platform': 'Kindle', 'release_date': (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d')},
        ]
    },
    {
        'title': 'チェンソーマン',
        'title_kana': 'ちぇんそーまん',
        'title_en': 'Chainsaw Man',
        'type': 'manga',
        'official_url': 'https://chainsawman.net/',
        'releases': [
            {'release_type': 'volume', 'number': '17', 'platform': 'BookWalker', 'release_date': (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d')},
        ]
    },
    {
        'title': 'スパイファミリー',
        'title_kana': 'すぱいふぁみりー',
        'title_en': 'Spy x Family',
        'type': 'manga',
        'official_url': 'https://spy-family.net/',
        'releases': [
            {'release_type': 'volume', 'number': '14', 'platform': 'Kindle', 'release_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')},
        ]
    },
    {
        'title': '僕のヒーローアカデミア',
        'title_kana': 'ぼくのひーろーあかでみあ',
        'title_en': 'My Hero Academia',
        'type': 'manga',
        'official_url': 'https://heroaca.com/',
        'releases': [
            {'release_type': 'volume', 'number': '40', 'platform': 'BookWalker', 'release_date': (datetime.now() + timedelta(days=10)).strftime('%Y-%m-%d')},
        ]
    },
    {
        'title': '怪獣8号',
        'title_kana': 'かいじゅうはちごう',
        'title_en': 'Kaiju No.8',
        'type': 'manga',
        'official_url': 'https://kj8.jp/',
        'releases': [
            {'release_type': 'volume', 'number': '13', 'platform': 'BookWalker', 'release_date': (datetime.now() + timedelta(days=12)).strftime('%Y-%m-%d')},
        ]
    },
]


def main():
    """メイン処理"""
    try:
        logger.info("=" * 60)
        logger.info("🚀 サンプルデータ投入を開始します")
        logger.info("=" * 60)

        # DBの初期化
        logger.info("データベースを初期化中...")
        db = get_db()

        # 既存データをクリア
        logger.info("既存データをクリア中...")
        with db.get_connection() as conn:
            conn.execute("DELETE FROM releases")
            conn.execute("DELETE FROM works")
            conn.commit()
        logger.info("✅ 既存データをクリアしました")

        # アニメデータを投入
        logger.info("\n📺 アニメデータを投入中...")
        anime_count = 0
        anime_release_count = 0

        for anime in SAMPLE_ANIME:
            try:
                # 作品情報を投入
                work_id = db.create_work(
                    title=anime['title'],
                    work_type=anime['type'],
                    title_kana=anime.get('title_kana'),
                    title_en=anime.get('title_en'),
                    official_url=anime.get('official_url')
                )

                if work_id:
                    anime_count += 1
                    logger.info(f"  ✅ {anime['title']} (ID: {work_id})")

                    # リリース情報を投入
                    for release in anime.get('releases', []):
                        release_id = db.create_release(
                            work_id=work_id,
                            release_type=release['release_type'],
                            number=release['number'],
                            platform=release['platform'],
                            release_date=release['release_date'],
                            source='sample_data',
                            source_url=anime.get('official_url')
                        )
                        if release_id:
                            anime_release_count += 1

            except Exception as e:
                logger.error(f"  ❌ {anime['title']}: {e}")
                continue

        logger.info(f"✅ アニメ: {anime_count}作品、{anime_release_count}リリースを登録")

        # マンガデータを投入
        logger.info("\n📚 マンガデータを投入中...")
        manga_count = 0
        manga_release_count = 0

        for manga in SAMPLE_MANGA:
            try:
                # 作品情報を投入
                work_id = db.create_work(
                    title=manga['title'],
                    work_type=manga['type'],
                    title_kana=manga.get('title_kana'),
                    title_en=manga.get('title_en'),
                    official_url=manga.get('official_url')
                )

                if work_id:
                    manga_count += 1
                    logger.info(f"  ✅ {manga['title']} (ID: {work_id})")

                    # リリース情報を投入
                    for release in manga.get('releases', []):
                        release_id = db.create_release(
                            work_id=work_id,
                            release_type=release['release_type'],
                            number=release['number'],
                            platform=release['platform'],
                            release_date=release['release_date'],
                            source='sample_data',
                            source_url=manga.get('official_url')
                        )
                        if release_id:
                            manga_release_count += 1

            except Exception as e:
                logger.error(f"  ❌ {manga['title']}: {e}")
                continue

        logger.info(f"✅ マンガ: {manga_count}作品、{manga_release_count}リリースを登録")

        # 統計情報を表示
        logger.info("\n📊 データベース統計:")
        stats = db.get_work_stats()
        total_works = stats.get('anime_works', 0) + stats.get('manga_works', 0)
        logger.info(f"  - 総作品数: {total_works}件")
        logger.info(f"  - アニメ: {stats.get('anime_works', 0)}件")
        logger.info(f"  - マンガ: {stats.get('manga_works', 0)}件")
        logger.info(f"  - 総リリース数: {stats.get('total_releases', 0)}件")

        logger.info("\n" + "=" * 60)
        logger.info("✅ サンプルデータ投入が完了しました")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
