#!/usr/bin/env python3
"""
簡易通知送信スクリプト
全未通知リリースに対してGmail通知とGoogleカレンダー登録を実行
"""

import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 環境変数読み込み
from dotenv import load_dotenv
load_dotenv()

import sqlite3
from datetime import datetime
from modules.smtp_mailer import sender as gmail_sender
import logging

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_unnotified_releases(limit=None):
    """未通知のリリース情報を取得"""
    conn = sqlite3.connect('db.sqlite3')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
        SELECT
            r.id,
            r.work_id,
            w.title,
            w.title_kana,
            r.release_type,
            r.number,
            r.platform,
            r.release_date,
            r.source_url
        FROM releases r
        JOIN works w ON r.work_id = w.id
        WHERE r.notified = 0
        ORDER BY r.release_date ASC
    """

    if limit:
        query += f" LIMIT {limit}"

    cursor.execute(query)
    releases = cursor.fetchall()
    conn.close()

    return releases

def mark_as_notified(release_ids):
    """リリースを通知済みにマーク"""
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()

    placeholders = ','.join(['?' for _ in release_ids])
    cursor.execute(
        f"UPDATE releases SET notified = 1 WHERE id IN ({placeholders})",
        release_ids
    )

    conn.commit()
    conn.close()
    logger.info(f"✅ {len(release_ids)}件を通知済みにマーク")

def send_batch_notifications(releases, dry_run=False):
    """バッチ通知送信"""
    logger.info(f"📧 {len(releases)}件の通知を送信開始...")

    success_ids = []
    failed_count = 0

    for i, release in enumerate(releases, 1):
        try:
            title = release['title_kana'] or release['title']
            release_type = '話' if release['release_type'] == 'episode' else '巻'
            subject = f"【MangaAnime配信】{title} 第{release['number']}{release_type}"

            body = f"""
<html>
<body>
<h2>{title}</h2>
<p><strong>第{release['number']}{release_type}</strong> が配信されます</p>
<p>📅 配信日: {release['release_date']}</p>
<p>📺 プラットフォーム: {release['platform']}</p>
<p>🔗 <a href="{release['source_url']}">詳細を見る</a></p>
</body>
</html>
"""

            if not dry_run:
                # Gmail送信
                to_email = os.getenv('GMAIL_TO_EMAIL', 'kensan1969@gmail.com')
                gmail_sender.send_email(
                    to_email=to_email,
                    subject=subject,
                    body=body
                )

                # Googleカレンダー登録は後で実装
                # add_to_calendar(...)

                success_ids.append(release['id'])
                logger.info(f"✅ [{i}/{len(releases)}] {title} - 通知送信完了")
            else:
                logger.info(f"🔄 [DRY-RUN] [{i}/{len(releases)}] {title}")
                success_ids.append(release['id'])

        except Exception as e:
            logger.error(f"❌ [{i}/{len(releases)}] 通知送信失敗: {e}")
            failed_count += 1
            continue

    if success_ids and not dry_run:
        mark_as_notified(success_ids)

    logger.info(f"""
📊 通知送信完了
✅ 成功: {len(success_ids)}件
❌ 失敗: {failed_count}件
    """)

    return len(success_ids), failed_count

def main():
    import argparse

    parser = argparse.ArgumentParser(description='MangaAnime通知送信')
    parser.add_argument('--limit', type=int, help='送信件数制限')
    parser.add_argument('--dry-run', action='store_true', help='ドライラン（実際には送信しない）')
    args = parser.parse_args()

    logger.info("="*60)
    logger.info("🚀 MangaAnime通知送信スクリプト 開始")
    if args.dry_run:
        logger.info("⚠️ ドライランモード")
    logger.info("="*60)

    # 未通知リリース取得
    releases = get_unnotified_releases(limit=args.limit)
    logger.info(f"📦 未通知リリース: {len(releases)}件")

    if not releases:
        logger.info("✅ 送信すべき通知はありません")
        return

    # バッチ通知送信
    success, failed = send_batch_notifications(releases, dry_run=args.dry_run)

    logger.info("="*60)
    logger.info("✅ 処理完了")
    logger.info("="*60)

if __name__ == "__main__":
    main()
