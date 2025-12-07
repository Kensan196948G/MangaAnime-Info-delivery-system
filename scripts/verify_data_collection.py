#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
データ収集検証スクリプト
作成日: 2025-12-06
目的: データ収集後の品質チェックと統計情報出力
"""

import sqlite3
import json
import os
import sys
from datetime import datetime
from collections import defaultdict

PROJECT_ROOT = "/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system"
DB_PATH = os.path.join(PROJECT_ROOT, "db.sqlite3")

def connect_db():
    """データベース接続"""
    if not os.path.exists(DB_PATH):
        logger.info(f"✗ データベースが見つかりません: {DB_PATH}")
        sys.exit(1)
    return sqlite3.connect(DB_PATH)

def get_statistics(conn):
    """統計情報取得"""
    cursor = conn.cursor()

    stats = {
        "works": {},
        "releases": {},
        "data_quality": {}
    }

    # Works統計
    cursor.execute("SELECT COUNT(*) FROM works")
    stats["works"]["total_count"] = cursor.fetchone()[0]

    cursor.execute("SELECT type, COUNT(*) FROM works GROUP BY type")
    stats["works"]["by_type"] = dict(cursor.fetchall())

    cursor.execute("SELECT COUNT(*) FROM works WHERE title_kana IS NOT NULL")
    stats["works"]["with_kana"] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM works WHERE official_url IS NOT NULL")
    stats["works"]["with_url"] = cursor.fetchone()[0]

    # Releases統計
    cursor.execute("SELECT COUNT(*) FROM releases")
    stats["releases"]["total_count"] = cursor.fetchone()[0]

    cursor.execute("SELECT release_type, COUNT(*) FROM releases GROUP BY release_type")
    stats["releases"]["by_type"] = dict(cursor.fetchall())

    cursor.execute("SELECT platform, COUNT(*) FROM releases GROUP BY platform")
    stats["releases"]["by_platform"] = dict(cursor.fetchall())

    cursor.execute("SELECT source, COUNT(*) FROM releases GROUP BY source")
    stats["releases"]["by_source"] = dict(cursor.fetchall())

    cursor.execute("SELECT COUNT(*) FROM releases WHERE notified = 1")
    stats["releases"]["notified_count"] = cursor.fetchone()[0]

    # データ品質チェック
    cursor.execute("SELECT COUNT(*) FROM works WHERE title IS NULL OR title = ''")
    stats["data_quality"]["works_without_title"] = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM releases WHERE release_date IS NULL")
    stats["data_quality"]["releases_without_date"] = cursor.fetchone()[0]

    cursor.execute("""
        SELECT work_id, COUNT(*) as dup_count
        FROM releases
        GROUP BY work_id, release_type, number, platform, release_date
        HAVING COUNT(*) > 1
    """)
    stats["data_quality"]["duplicate_releases"] = len(cursor.fetchall())

    return stats

def get_recent_data(conn, limit=10):
    """最近追加されたデータ取得"""
    cursor = conn.cursor()

    recent = {
        "works": [],
        "releases": []
    }

    cursor.execute("""
        SELECT id, title, type, official_url, created_at
        FROM works
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))
    recent["works"] = cursor.fetchall()

    cursor.execute("""
        SELECT r.id, w.title, r.release_type, r.number, r.platform, r.release_date, r.created_at
        FROM releases r
        JOIN works w ON r.work_id = w.id
        ORDER BY r.created_at DESC
        LIMIT ?
    """, (limit,))
    recent["releases"] = cursor.fetchall()

    return recent

def print_report(stats, recent):
    """レポート出力"""
    logger.info("\n" + "="*60)
    logger.info("データ収集検証レポート")
    logger.info("="*60)
    logger.info(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")

    # Works統計
    logger.info("📊 Works統計")
    logger.info("-" * 60)
    logger.info(f"  総作品数: {stats['works']['total_count']}")
    logger.info(f"  タイプ別:")
    for work_type, count in stats['works']['by_type'].items():
        logger.info(f"    - {work_type}: {count}")
    logger.info(f"  読み仮名あり: {stats['works']['with_kana']} ({stats['works']['with_kana']/max(stats['works']['total_count'],1)*100:.1f}%)")
    logger.info(f"  公式URLあり: {stats['works']['with_url']} ({stats['works']['with_url']/max(stats['works']['total_count'],1)*100:.1f}%)")
    logger.info("")

    # Releases統計
    logger.info("📅 Releases統計")
    logger.info("-" * 60)
    logger.info(f"  総リリース数: {stats['releases']['total_count']}")
    logger.info(f"  リリースタイプ別:")
    for release_type, count in stats['releases']['by_type'].items():
        logger.info(f"    - {release_type}: {count}")
    logger.info(f"  プラットフォーム別:")
    for platform, count in sorted(stats['releases']['by_platform'].items(), key=lambda x: x[1], reverse=True)[:10]:
        logger.info(f"    - {platform}: {count}")
    logger.info(f"  ソース別:")
    for source, count in stats['releases']['by_source'].items():
        logger.info(f"    - {source}: {count}")
    logger.info(f"  通知済み: {stats['releases']['notified_count']}")
    logger.info("")

    # データ品質
    logger.info("🔍 データ品質チェック")
    logger.info("-" * 60)
    quality_issues = 0
    if stats['data_quality']['works_without_title'] > 0:
        logger.info(f"  ⚠ タイトルなしの作品: {stats['data_quality']['works_without_title']}")
        quality_issues += 1
    if stats['data_quality']['releases_without_date'] > 0:
        logger.info(f"  ⚠ 配信日なしのリリース: {stats['data_quality']['releases_without_date']}")
        quality_issues += 1
    if stats['data_quality']['duplicate_releases'] > 0:
        logger.info(f"  ⚠ 重複リリース: {stats['data_quality']['duplicate_releases']}")
        quality_issues += 1

    if quality_issues == 0:
        logger.info("  ✓ データ品質に問題なし")
    logger.info("")

    # 最近追加されたデータ
    logger.info("🆕 最近追加された作品 (上位5件)")
    logger.info("-" * 60)
    for work in recent['works'][:5]:
        work_id, title, work_type, url, created_at = work
        logger.info(f"  [{work_id}] {title} ({work_type})")
        logger.info(f"      URL: {url if url else 'N/A'}")
        logger.info(f"      追加日時: {created_at}")
    logger.info("")

    logger.info("🆕 最近追加されたリリース (上位5件)")
    logger.info("-" * 60)
    for release in recent['releases'][:5]:
        rel_id, title, rel_type, number, platform, rel_date, created_at = release
        logger.info(f"  [{rel_id}] {title}")
        logger.info(f"      {rel_type} #{number if number else 'N/A'} on {platform}")
        logger.info(f"      配信日: {rel_date if rel_date else 'N/A'}")
        logger.info(f"      追加日時: {created_at}")
    logger.info("")

    logger.info("="*60)
    logger.info("検証完了")
    logger.info("="*60)

def export_json_report(stats, output_path):
    """JSON形式でレポート出力"""
    report = {
        "generated_at": datetime.now().isoformat(),
        "statistics": stats
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    logger.info(f"\n📄 JSON レポート出力: {output_path}")

def main():
    """メイン処理"""
import logging

logger = logging.getLogger(__name__)

    logger.info("データ収集検証を開始します...")

logger = logging.getLogger(__name__)


    conn = connect_db()

    try:
        stats = get_statistics(conn)
        recent = get_recent_data(conn, limit=10)

        print_report(stats, recent)

        # JSONレポート出力
        json_path = os.path.join(PROJECT_ROOT, "logs", "data_collection_report.json")
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        export_json_report(stats, json_path)

    finally:
        conn.close()

if __name__ == "__main__":
    main()
