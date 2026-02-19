#!/usr/bin/env python3
"""
アニメ・マンガタイトルの日本語化モジュール
英語タイトルを日本語タイトルに変換
"""

import json
import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)


class TitleTranslator:
    def __init__(self):
        self.mapping_file = Path("config/title_mapping.json")
        self.title_map = self.load_mappings()

    def load_mappings(self):
        """タイトルマッピングを読み込み"""
        if self.mapping_file.exists():
            with open(self.mapping_file, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            # デフォルトマッピング
            default_mappings = {
                # 2025年冬アニメ
                "WITCH WATCH": "ウィッチウォッチ",
                "Princess-Session Orchestra": "プリンセスセッション・オーケストラ",
                "Kaiju No. 8 Season 2": "怪獣8号 第2期",
                "Kaiju No. 8": "怪獣8号",
                "Shin Chan": "クレヨンしんちゃん",
                "Crayon Shin-chan": "クレヨンしんちゃん",
                "Ninjala the Animation": "ニンジャラ",
                "Betrothed to My Sister's Ex": "姉の元カレと付き合うことになりました",
                "Secrets of the Silent Witch": "サイレント・ウィッチの秘密",
                "Call of the Night Season 2": "よふかしのうた 第2期",
                "Call of the Night": "よふかしのうた",
                "TOUGEN ANKI": "桃源暗鬼",
                "Busu ni Hanataba wo.": "ブスに花束を。",
                # 人気作品
                "One Piece": "ONE PIECE",
                "Dragon Ball DAIMA": "ドラゴンボールDAIMA",
                "Bleach: Thousand-Year Blood War": "BLEACH 千年血戦篇",
                "Jujutsu Kaisen": "呪術廻戦",
                "Chainsaw Man": "チェンソーマン",
                "Spy x Family": "SPY×FAMILY",
                "Demon Slayer": "鬼滅の刃",
                "Attack on Titan": "進撃の巨人",
                "My Hero Academia": "僕のヒーローアカデミア",
                "Tokyo Revengers": "東京リベンジャーズ",
                "Blue Lock": "ブルーロック",
                "Oshi no Ko": "【推しの子】",
                "Frieren": "葬送のフリーレン",
                "Sousou no Frieren": "葬送のフリーレン",
                "Dr. STONE": "Dr.STONE",
                "Kingdom": "キングダム",
                # 2024-2025年の新作
                "Solo Leveling": "俺だけレベルアップな件",
                "The Apothecary Diaries": "薬屋のひとりごと",
                "Kusuriya no Hitorigoto": "薬屋のひとりごと",
                "Dungeon Meshi": "ダンジョン飯",
                "Delicious in Dungeon": "ダンジョン飯",
                "Wind Breaker": "WIND BREAKER",
                "Mushoku Tensei": "無職転生",
                "Re:Zero": "Re:ゼロから始める異世界生活",
                "Overlord": "オーバーロード",
                "That Time I Got Reincarnated as a Slime": "転生したらスライムだった件",
                "The Rising of the Shield Hero": "盾の勇者の成り上がり",
                # マンガ系
                "Hunter x Hunter": "HUNTER×HUNTER",
                "Berserk": "ベルセルク",
                "Vagabond": "バガボンド",
                "Monster": "MONSTER",
                "20th Century Boys": "20世紀少年",
                "Pluto": "PLUTO",
                "Death Note": "DEATH NOTE",
                "Bakuman": "バクマン。",
                "Haikyu!!": "ハイキュー!!",
                "Kuroko's Basketball": "黒子のバスケ",
                "Blue Giant": "BLUE GIANT",
                "Golden Kamuy": "ゴールデンカムイ",
                "Vinland Saga": "ヴィンランド・サガ",
                "Made in Abyss": "メイドインアビス",
                "The Promised Neverland": "約束のネバーランド",
            }

            # ファイルに保存
            self.mapping_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.mapping_file, "w", encoding="utf-8") as f:
                json.dump(default_mappings, f, ensure_ascii=False, indent=2)

            return default_mappings

    def translate(self, title):
        """英語タイトルを日本語に変換"""
        if not title:
            return title

        # 完全一致を試す
        if title in self.title_map:
            return self.title_map[title]

        # Season番号を除いて検索
        base_title = title.replace(" Season 2", "").replace(" Season 3", "")
        base_title = base_title.replace(" 2nd Season", "").replace(" 3rd Season", "")

        if base_title in self.title_map:
            japanese_title = self.title_map[base_title]
            # Season番号を追加
            if "Season 2" in title or "2nd Season" in title:
                japanese_title += " 第2期"
            elif "Season 3" in title or "3rd Season" in title:
                japanese_title += " 第3期"
            elif "Season 4" in title:
                japanese_title += " 第4期"
            return japanese_title

        # 部分一致を試す（最初の単語で検索）
        for eng, jpn in self.title_map.items():
            if title.lower().startswith(eng.lower()):
                return jpn

        # 変換できない場合は元のタイトルを返す
        return title

    def add_mapping(self, english_title, japanese_title):
        """新しいマッピングを追加"""
        self.title_map[english_title] = japanese_title
        self.save_mappings()

    def save_mappings(self):
        """マッピングをファイルに保存"""
        with open(self.mapping_file, "w", encoding="utf-8") as f:
            json.dump(self.title_map, f, ensure_ascii=False, indent=2)

    def update_database_titles(self):
        """データベース内のタイトルを日本語化"""
        conn = sqlite3.connect("db.sqlite3")
        cursor = conn.cursor()

        # 全作品を取得
        cursor.execute("SELECT id, title FROM works")
        works = cursor.fetchall()

        updated_count = 0
        for work_id, title in works:
            japanese_title = self.translate(title)
            if japanese_title != title:
                # title_nativeフィールドに日本語タイトルを保存
                cursor.execute(
                    """
                    UPDATE works
                    SET title_native = ?
                    WHERE id = ?
                """,
                    (japanese_title, work_id),
                )
                updated_count += 1

        conn.commit()
        conn.close()

        return updated_count


def get_japanese_title(title):
    """便利関数：英語タイトルから日本語タイトルを取得"""
    translator = TitleTranslator()
    return translator.translate(title)


if __name__ == "__main__":
    # テスト実行
    translator = TitleTranslator()

    test_titles = [
        "WITCH WATCH",
        "Kaiju No. 8 Season 2",
        "Shin Chan",
        "Call of the Night Season 2",
        "TOUGEN ANKI",
        "Spy x Family",
        "Unknown Title",
    ]

    logger.info("タイトル変換テスト:")
    logger.info("=" * 50)
    for title in test_titles:
        japanese = translator.translate(title)
        logger.info(f"{title:30} → {japanese}")

    # データベース更新
    logger.info("\nデータベースのタイトルを更新中...")
    updated = translator.update_database_titles()
    logger.info(f"✅ {updated}件のタイトルを日本語化しました")
