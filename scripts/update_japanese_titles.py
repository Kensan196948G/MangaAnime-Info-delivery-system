#!/usr/bin/env python3
import sqlite3

titles = {
    "GNOSIA": "グノーシア",
    "Kingdom Season 6": "キングダム シーズン6", 
    "Ranma1/2 (2024) Season 2": "らんま1/2（2024）シーズン2",
    "My Friend's Little Sister Has It In for Me!": "友達の妹が俺にだけウザい",
    "Sai-Kyo-Oh! Zukan: The Ultimate Tournament": "最強王図鑑",
    "Koupen-chan": "コウペンちゃん",
    "You and Idol Precure ♪": "ひろがるスカイ！プリキュア",
    "Princess-Session Orchestra": "プリンセス・セッション・オーケストラ",
    "DIGIMON BEATBREAK": "デジモン ビートブレイク",
    "Himitsu no AiPri: Ring-hen": "ひみつのアイプリ",
    "Ao no Orchestra Season 2": "青のオーケストラ シーズン2",
    "Holo no Graffiti": "ホロのグラフィティ",
    "Sazae-san": "サザエさん",
    "Mechanical Marie": "メカニカル・マリー",
    "Li'l Miss Vampire Can't Suck Right": "吸血姫は夜に啼く",
    "Alma-chan Wants to Be a Family!": "アルマちゃんは家族になりたい！",
    "ONE PIECE": "ワンピース",
    "Dad is a Hero, Mom is a Spirit, I'm a Reincarnator": "お父さんは勇者、お母さんは精霊、僕は転生者",
    "Gachiakuta": "ガチアクタ",
    "One-Punch Man Season 3": "ワンパンマン シーズン3",
    "Tojima Wants to Be a Kamen Rider": "藤間くんは仮面ライダーになりたい"
}

conn = sqlite3.connect('data/db.sqlite3')
for eng, jpn in titles.items():
    conn.execute("UPDATE works SET title_kana = ? WHERE title = ?", (jpn, eng))
    print(f"✅ {eng} → {jpn}")
conn.commit()
conn.close()
print(f"\n✅ {len(titles)}作品更新完了")
