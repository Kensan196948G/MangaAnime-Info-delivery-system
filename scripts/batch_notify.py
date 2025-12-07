#!/usr/bin/env python3
"""
バッチ通知スクリプト
全未通知リリースをGmailで通知（バッチサイズで分割）
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
from modules.smtp_mailer import SMTPGmailSender
import time
import argparse

def get_unnotified_releases(limit=None):
    """未通知リリース取得"""
    conn = sqlite3.connect('db.sqlite3')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
        SELECT
            r.id,
            w.title,
            w.title_kana,
            r.release_type,
            r.number,
            r.platform,
            r.release_date
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
    """通知済みにマーク"""
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()

    placeholders = ','.join(['?' for _ in release_ids])
    cursor.execute(
        f"UPDATE releases SET notified = 1 WHERE id IN ({placeholders})",
        release_ids
    )

    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected

def send_notifications(releases, delay=1):
    """
    バッチ通知送信

    Args:
        releases: リリースリスト
        delay: 各送信の間隔（秒）

    Returns:
        (success_count, failed_count)
    """
    sender = SMTPGmailSender()
    success_ids = []
    failed_count = 0

    total = len(releases)

    for i, release in enumerate(releases, 1):
        try:
            title = release['title_kana'] or release['title']
            release_type = '話' if release['release_type'] == 'episode' else '巻'
            number = release['number'] or '不明'

            subject = f"【MangaAnime配信】{title} 第{number}{release_type}"

            html_content = f"""
<html>
<body>
<h2>{title}</h2>
<p><strong>第{number}{release_type}</strong> が配信されます</p>
<p>📅 配信日: {release['release_date']}</p>
<p>📺 プラットフォーム: {release['platform']}</p>
</body>
</html>
"""

            success = sender.send_email(
                subject=subject,
                html_content=html_content,
                to_email=os.getenv('GMAIL_TO_EMAIL', 'kensan1969@gmail.com')
            )

            if success:
                success_ids.append(release['id'])
                print(f"✅ [{i}/{total}] {title} - 送信完了")
            else:
                failed_count += 1
                print(f"❌ [{i}/{total}] {title} - 送信失敗")

            # レート制限対策
            if i < total:
                time.sleep(delay)

        except Exception as e:
            failed_count += 1
            print(f"❌ [{i}/{total}] エラー: {e}")
            continue

    # 成功した分を通知済みにマーク
    if success_ids:
        marked = mark_as_notified(success_ids)
        print(f"📝 {marked}件を通知済みにマーク")

    return len(success_ids), failed_count

def main():
    parser = argparse.ArgumentParser(description='バッチ通知送信')
    parser.add_argument('--limit', type=int, help='送信件数制限')
    parser.add_argument('--delay', type=float, default=2.0, help='送信間隔（秒）')
    parser.add_argument('--batch-size', type=int, default=20, help='バッチサイズ')
    parser.add_argument('--batch-delay', type=float, default=30.0, help='バッチ間待機時間（秒）')
    args = parser.parse_args()

    print("="*60)
    print("🚀 バッチ通知送信スクリプト 開始")
    print("="*60)

    # 未通知件数確認
    all_releases = get_unnotified_releases()
    total_unnotified = len(all_releases)
    print(f"📦 未通知リリース: {total_unnotified}件")

    if total_unnotified == 0:
        print("✅ 送信すべき通知はありません")
        return

    # 送信件数決定
    if args.limit:
        to_send = min(args.limit, total_unnotified)
        print(f"⚠️ 送信制限: {to_send}件")
    else:
        to_send = total_unnotified

    # バッチ処理
    batch_size = args.batch_size
    total_success = 0
    total_failed = 0

    for batch_start in range(0, to_send, batch_size):
        batch_end = min(batch_start + batch_size, to_send)
        batch_releases = get_unnotified_releases(limit=batch_size)

        print(f"\n📨 バッチ {batch_start//batch_size + 1}: {len(batch_releases)}件送信中...")

        success, failed = send_notifications(batch_releases, delay=args.delay)

        total_success += success
        total_failed += failed

        print(f"✅ バッチ完了: 成功 {success}件 / 失敗 {failed}件")

        # バッチ間の待機（Gmailレート制限対策）
        if batch_end < to_send:
            wait_time = args.batch_delay
            print(f"⏳ 次のバッチまで{wait_time}秒待機（Gmailレート制限対策）...")
            time.sleep(wait_time)

    print("\n" + "="*60)
    print("📊 最終結果")
    print(f"✅ 成功: {total_success}件")
    print(f"❌ 失敗: {total_failed}件")
    print("="*60)

if __name__ == "__main__":
    main()
