#!/usr/bin/env python3
"""
データクレンジングスクリプト
Phase 18: データ品質向上

処理内容:
1. 空タイトルの修正（"[" のみなど）
2. 不完全タイトルの修正
3. 重複作品の統合
4. 欠損値の補完
"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

import sqlite3
import re
from datetime import datetime
import shutil

def backup_database():
    """データベースバックアップ"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f"db.sqlite3.backup_before_cleaning_{timestamp}"

    shutil.copy('db.sqlite3', backup_file)
    print(f"📝 バックアップ作成: {backup_file}")
    return backup_file

def analyze_data_quality():
    """データ品質分析"""
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()

    # 空タイトル
    cursor.execute("""
        SELECT COUNT(*) FROM works
        WHERE title = '[' OR title = '' OR title IS NULL OR title LIKE '[%' AND title NOT LIKE '%]%'
    """)
    empty_titles = cursor.fetchone()[0]

    # title_kana 欠損
    cursor.execute("SELECT COUNT(*) FROM works WHERE title_kana IS NULL OR title_kana = ''")
    missing_kana = cursor.fetchone()[0]

    # number 欠損
    cursor.execute("SELECT COUNT(*) FROM releases WHERE number IS NULL OR number = ''")
    missing_number = cursor.fetchone()[0]

    # platform 欠損
    cursor.execute("SELECT COUNT(*) FROM releases WHERE platform IS NULL OR platform = ''")
    missing_platform = cursor.fetchone()[0]

    # 重複タイトル
    cursor.execute("""
        SELECT COUNT(*) FROM (
            SELECT title, COUNT(*) as count
            FROM works
            GROUP BY title
            HAVING count > 1
        )
    """)
    duplicates = cursor.fetchone()[0]

    conn.close()

    return {
        'empty_titles': empty_titles,
        'missing_kana': missing_kana,
        'missing_number': missing_number,
        'missing_platform': missing_platform,
        'duplicates': duplicates
    }

def clean_empty_titles():
    """空タイトルの修正"""
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()

    # パターン1: "[" のみ
    cursor.execute("""
        UPDATE works
        SET title = 'タイトル不明_' || id,
            title_kana = 'タイトル不明_' || id
        WHERE title = '['
    """)
    pattern1 = cursor.rowcount

    # パターン2: 空文字列
    cursor.execute("""
        UPDATE works
        SET title = 'タイトル不明_' || id,
            title_kana = 'タイトル不明_' || id
        WHERE title = '' OR title IS NULL
    """)
    pattern2 = cursor.rowcount

    # パターン3: "[" で始まり "]" で終わらない（不完全）
    cursor.execute("""
        UPDATE works
        SET title = REPLACE(title, '[', ''),
            title_kana = REPLACE(COALESCE(title_kana, title), '[', '')
        WHERE title LIKE '[%' AND title NOT LIKE '%]%' AND title != '['
    """)
    pattern3 = cursor.rowcount

    conn.commit()
    conn.close()

    total = pattern1 + pattern2 + pattern3
    print(f"  ✅ 空タイトル修正: {total}件")
    print(f"     - '['のみ: {pattern1}件")
    print(f"     - 空文字列: {pattern2}件")
    print(f"     - 不完全: {pattern3}件")

    return total

def fill_missing_kana():
    """title_kana欠損の補完"""
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE works
        SET title_kana = title
        WHERE title_kana IS NULL OR title_kana = ''
    """)

    affected = cursor.rowcount
    conn.commit()
    conn.close()

    print(f"  ✅ title_kana補完: {affected}件")
    return affected

def fill_missing_number():
    """release number欠損の補完"""
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()

    # UNIQUE制約を回避するため、個別に処理
    cursor.execute("""
        SELECT id FROM releases
        WHERE number IS NULL OR number = ''
    """)

    release_ids = [row[0] for row in cursor.fetchall()]
    affected = 0

    for release_id in release_ids:
        try:
            cursor.execute("""
                UPDATE releases
                SET number = '不明_' || id
                WHERE id = ?
            """, (release_id,))
            affected += 1
        except sqlite3.IntegrityError:
            # UNIQUE制約違反の場合はスキップ
            continue

    conn.commit()
    conn.close()

    print(f"  ✅ release number補完: {affected}件")
    return affected

def fill_missing_platform():
    """platform欠損の補完"""
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()

    # UNIQUE制約を回避するため、個別に処理
    cursor.execute("""
        SELECT id FROM releases
        WHERE platform IS NULL OR platform = ''
    """)

    release_ids = [row[0] for row in cursor.fetchall()]
    affected = 0

    for release_id in release_ids:
        try:
            cursor.execute("""
                UPDATE releases
                SET platform = 'その他_' || id
                WHERE id = ?
            """, (release_id,))
            affected += 1
        except sqlite3.IntegrityError:
            # UNIQUE制約違反の場合はスキップ
            continue

    conn.commit()
    conn.close()

    print(f"  ✅ platform補完: {affected}件")
    return affected

def merge_duplicates():
    """重複作品の統合"""
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()

    # 重複タイトル検出
    cursor.execute("""
        SELECT title, GROUP_CONCAT(id) as ids, COUNT(*) as count
        FROM works
        WHERE title NOT LIKE 'タイトル不明_%'
        GROUP BY title
        HAVING count > 1
    """)

    duplicates = cursor.fetchall()
    merged_count = 0

    for row in duplicates:
        title = row[0]
        ids = row[1].split(',')

        # 最初のIDを残し、他を統合
        keep_id = ids[0]
        merge_ids = ids[1:]

        # releases テーブルの work_id を更新
        for merge_id in merge_ids:
            cursor.execute(
                "UPDATE releases SET work_id = ? WHERE work_id = ?",
                (keep_id, merge_id)
            )

        # 不要な works を削除
        for merge_id in merge_ids:
            cursor.execute("DELETE FROM works WHERE id = ?", (merge_id,))

        merged_count += len(merge_ids)

    conn.commit()
    conn.close()

    print(f"  ✅ 重複作品統合: {merged_count}件")
    return merged_count

def main():
    print("="*70)
    print("🧹 データクレンジング開始 - Phase 18")
    print("="*70)

    # 事前分析
    print("\n【事前分析】")
    before = analyze_data_quality()
    print(f"  空タイトル: {before['empty_titles']}件")
    print(f"  title_kana欠損: {before['missing_kana']}件")
    print(f"  number欠損: {before['missing_number']}件")
    print(f"  platform欠損: {before['missing_platform']}件")
    print(f"  重複作品: {before['duplicates']}件")

    if before['empty_titles'] == 0 and before['missing_kana'] == 0 and \
       before['missing_number'] == 0 and before['missing_platform'] == 0 and \
       before['duplicates'] == 0:
        print("\n✅ データクレンジング不要です（既にクリーンな状態）")
        return

    # バックアップ
    print("\n【バックアップ】")
    backup_database()

    # クレンジング実行
    print("\n【クレンジング実行】")

    print("\n1. 空タイトル修正")
    clean_empty_titles()

    print("\n2. title_kana補完")
    fill_missing_kana()

    print("\n3. release number補完")
    fill_missing_number()

    print("\n4. platform補完")
    fill_missing_platform()

    print("\n5. 重複作品統合")
    merge_duplicates()

    # 事後分析
    print("\n【事後分析】")
    after = analyze_data_quality()
    print(f"  空タイトル: {after['empty_titles']}件")
    print(f"  title_kana欠損: {after['missing_kana']}件")
    print(f"  number欠損: {after['missing_number']}件")
    print(f"  platform欠損: {after['missing_platform']}件")
    print(f"  重複作品: {after['duplicates']}件")

    # 改善率計算
    print("\n【改善サマリー】")
    improvements = {
        '空タイトル': before['empty_titles'] - after['empty_titles'],
        'title_kana': before['missing_kana'] - after['missing_kana'],
        'number': before['missing_number'] - after['missing_number'],
        'platform': before['missing_platform'] - after['missing_platform'],
        '重複': before['duplicates'] - after['duplicates']
    }

    for key, value in improvements.items():
        if value > 0:
            print(f"  ✅ {key}: {value}件改善")

    total_improvements = sum(improvements.values())
    print(f"\n  📊 総改善件数: {total_improvements}件")

    print("\n" + "="*70)
    print("✅ データクレンジング完了")
    print("="*70)

if __name__ == "__main__":
    main()
