#!/usr/bin/env python3
"""
スマートバッチ通知スクリプト
Gmailレート制限を回避しながら段階的に全件送信

Gmailの制限:
- 1日500通まで
- 連続送信でSMTP接続切断される可能性あり
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
from datetime import datetime

# Gmail制限対策の設定
DAILY_LIMIT = 500  # 1日の送信上限
BATCH_SIZE = 20    # 1バッチあたりの送信数
DELAY_BETWEEN_EMAILS = 2.0  # メール間の待機時間（秒）
DELAY_BETWEEN_BATCHES = 60.0  # バッチ間の待機時間（秒）

def get_unnotified_count():
    """未通知件数取得"""
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM releases WHERE notified = 0")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_unnotified_releases(limit):
    """未通知リリース取得"""
    conn = sqlite3.connect('db.sqlite3')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
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
        LIMIT ?
    """, (limit,))

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

def send_batch(releases):
    """1バッチ送信"""
    sender = SMTPGmailSender()
    success_ids = []
    failed_count = 0

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
                print(f"  ✅ [{i}/{len(releases)}] {title[:50]}...")
            else:
                failed_count += 1
                print(f"  ❌ [{i}/{len(releases)}] {title[:50]}... - 送信失敗")

            # メール間待機
            if i < len(releases):
                time.sleep(DELAY_BETWEEN_EMAILS)

        except Exception as e:
            failed_count += 1
            print(f"  ❌ [{i}/{len(releases)}] エラー: {e}")
            continue

    # 成功した分を通知済みにマーク
    if success_ids:
        marked = mark_as_notified(success_ids)

    return len(success_ids), failed_count

def main():
    print("="*70)
    print("🚀 スマートバッチ通知送信（Gmailレート制限対策版）")
    print("="*70)
    print(f"📊 設定:")
    print(f"  - 1バッチ: {BATCH_SIZE}通")
    print(f"  - メール間隔: {DELAY_BETWEEN_EMAILS}秒")
    print(f"  - バッチ間隔: {DELAY_BETWEEN_BATCHES}秒")
    print(f"  - 1日上限: {DAILY_LIMIT}通")
    print("="*70)

    # 未通知件数確認
    total_unnotified = get_unnotified_count()
    print(f"\n📦 未通知リリース: {total_unnotified}件")

    if total_unnotified == 0:
        print("✅ 送信すべき通知はありません")
        return

    # 本日送信可能な最大数
    today_max = min(total_unnotified, DAILY_LIMIT)
    print(f"📅 本日送信予定: {today_max}件（Gmail1日制限: {DAILY_LIMIT}通）")

    # バッチ数計算
    total_batches = (today_max + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"📨 バッチ数: {total_batches}バッチ")

    # 推定時間
    estimated_time = (
        (BATCH_SIZE * DELAY_BETWEEN_EMAILS) * total_batches +
        (DELAY_BETWEEN_BATCHES * (total_batches - 1))
    ) / 60
    print(f"⏱️  推定時間: 約{estimated_time:.1f}分")

    input(f"\n▶️  {today_max}件の送信を開始します。Enter を押してください...")

    # バッチ送信開始
    total_success = 0
    total_failed = 0
    start_time = datetime.now()

    for batch_num in range(1, total_batches + 1):
        print(f"\n{'='*70}")
        print(f"📨 バッチ {batch_num}/{total_batches} 開始")
        print(f"{'='*70}")

        # バッチ取得
        batch_releases = get_unnotified_releases(BATCH_SIZE)

        if not batch_releases:
            print("⚠️ 未通知リリースがなくなりました")
            break

        # 送信
        success, failed = send_batch(batch_releases)

        total_success += success
        total_failed += failed

        print(f"\n📊 バッチ {batch_num} 完了:")
        print(f"  ✅ 成功: {success}件")
        print(f"  ❌ 失敗: {failed}件")
        print(f"  📈 累計: {total_success}件送信済み")

        # バッチ間待機
        if batch_num < total_batches:
            remaining_unnotified = get_unnotified_count()
            if remaining_unnotified == 0:
                print("\n🎉 全ての通知を送信しました！")
                break

            print(f"\n⏳ 次のバッチまで{DELAY_BETWEEN_BATCHES}秒待機...")
            print(f"   （残り: {remaining_unnotified}件）")
            time.sleep(DELAY_BETWEEN_BATCHES)

    # 終了サマリー
    end_time = datetime.now()
    elapsed = (end_time - start_time).total_seconds() / 60

    print("\n" + "="*70)
    print("🎊 送信完了！")
    print("="*70)
    print(f"✅ 成功: {total_success}件")
    print(f"❌ 失敗: {total_failed}件")
    print(f"⏱️  所要時間: {elapsed:.1f}分")
    print(f"📦 残り未通知: {get_unnotified_count()}件")
    print("="*70)

    if total_failed > 0:
        print("\n⚠️ 失敗した通知について:")
        print("  - 後ほど再実行することで再送信できます")
        print("  - 実行コマンド: python3 scripts/smart_batch_notify.py")

    if get_unnotified_count() > 0:
        print("\n📅 残りの通知について:")
        print(f"  - Gmail 1日制限({DAILY_LIMIT}通)のため、明日以降に送信してください")
        print("  - または cron により自動送信されます（毎日8:00）")

if __name__ == "__main__":
    main()
