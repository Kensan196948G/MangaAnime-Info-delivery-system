#!/usr/bin/env python3
"""
分散通知スクリプト - Gmailレート制限完全対策版

戦略:
- 1日を3回に分散（朝8時、昼12時、夜20時）
- 各回: 約67通送信
- 小バッチ: 15通/バッチ
- 長待機: 90秒/バッチ間隔
- 1日合計: 200通（安全マージン）
- 5日間で865件完全送信

Gmailレート制限:
- 公式: 500通/日
- 実測: 連続送信で40-70通で接続切断
- 対策: 時間分散 + 小バッチ + 長待機
"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

import sqlite3
from modules.smtp_mailer import SMTPGmailSender
import time
from datetime import datetime, timedelta
import argparse

# 最適化設定（Gmail制限回避）
BATCH_SIZE = 15              # 小バッチ（15通/バッチ）
EMAIL_DELAY = 2.0            # メール間隔（2秒）
BATCH_DELAY = 90.0           # バッチ間待機（90秒）
SESSION_MAX = 67             # 1セッション最大送信数
DAILY_SESSIONS = 3           # 1日のセッション数（朝・昼・夜）
DAILY_MAX = SESSION_MAX * DAILY_SESSIONS  # 1日最大201通

def get_current_session():
    """
    現在の時刻から送信セッションを判定

    Returns:
        str: 'morning' | 'noon' | 'evening' | None
    """
    now = datetime.now()
    hour = now.hour

    if 7 <= hour < 11:
        return 'morning'
    elif 12 <= hour < 16:
        return 'noon'
    elif 19 <= hour < 22:
        return 'evening'
    else:
        return None

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
    if not release_ids:
        return 0

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
    """1バッチ送信（15通）"""
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
                print(f"    ✅ [{i}/{len(releases)}] {title[:40]}...")
            else:
                failed_count += 1
                print(f"    ❌ [{i}/{len(releases)}] 送信失敗")

            # メール間待機
            if i < len(releases):
                time.sleep(EMAIL_DELAY)

        except Exception as e:
            failed_count += 1
            print(f"    ❌ [{i}/{len(releases)}] エラー: {e}")
            continue

    return success_ids, failed_count

def run_session(session_name, max_count=SESSION_MAX):
    """1セッション実行（約67通）"""
    print(f"\n{'='*70}")
    print(f"📨 {session_name}セッション開始")
    print(f"{'='*70}")
    print(f"  最大送信数: {max_count}通")
    print(f"  バッチサイズ: {BATCH_SIZE}通")
    print(f"  バッチ数: {max_count // BATCH_SIZE}バッチ")
    print(f"  推定時間: 約{(max_count // BATCH_SIZE) * (BATCH_SIZE * EMAIL_DELAY + BATCH_DELAY) / 60:.1f}分")
    print(f"{'='*70}\n")

    total_success = 0
    total_failed = 0
    all_success_ids = []

    batch_count = (max_count + BATCH_SIZE - 1) // BATCH_SIZE

    for batch_num in range(1, batch_count + 1):
        print(f"  📦 バッチ {batch_num}/{batch_count}")

        # バッチ取得
        batch_releases = get_unnotified_releases(BATCH_SIZE)

        if not batch_releases:
            print(f"  ⚠️ 未通知リリースがなくなりました")
            break

        # 送信
        success_ids, failed = send_batch(batch_releases)

        total_success += len(success_ids)
        total_failed += failed
        all_success_ids.extend(success_ids)

        print(f"  📊 成功: {len(success_ids)}件 / 失敗: {failed}件")

        # バッチ間待機
        if batch_num < batch_count:
            remaining = max_count - total_success
            if remaining <= 0:
                break

            next_batch = get_unnotified_releases(1)
            if not next_batch:
                print(f"  🎉 全ての通知を送信しました！")
                break

            print(f"  ⏳ 次のバッチまで{BATCH_DELAY}秒待機...")
            time.sleep(BATCH_DELAY)

    # 成功分を通知済みにマーク
    if all_success_ids:
        marked = mark_as_notified(all_success_ids)
        print(f"\n  📝 {marked}件を通知済みにマーク")

    return total_success, total_failed

def main():
    parser = argparse.ArgumentParser(description='分散通知送信（Gmailレート制限完全対策）')
    parser.add_argument('--session', choices=['morning', 'noon', 'evening', 'auto'],
                        default='auto', help='送信セッション')
    parser.add_argument('--limit', type=int, help='送信数上限（デフォルト: セッション最大値）')
    parser.add_argument('--force', action='store_true', help='時間外でも強制実行')
    args = parser.parse_args()

    print("="*70)
    print("🚀 分散通知送信システム（Gmailレート制限完全対策版）")
    print("="*70)
    print(f"📊 システム設定:")
    print(f"  - バッチサイズ: {BATCH_SIZE}通")
    print(f"  - メール間隔: {EMAIL_DELAY}秒")
    print(f"  - バッチ間隔: {BATCH_DELAY}秒")
    print(f"  - セッション最大: {SESSION_MAX}通")
    print(f"  - 1日最大: {DAILY_MAX}通（{DAILY_SESSIONS}セッション）")
    print("="*70)

    # 未通知件数確認
    unnotified = get_unnotified_releases(1000)
    total_unnotified = len(unnotified)
    print(f"\n📦 未通知リリース: {total_unnotified}件")

    if total_unnotified == 0:
        print("✅ 送信すべき通知はありません")
        return

    # セッション決定
    if args.session == 'auto':
        session = get_current_session()
        if session is None and not args.force:
            print("\n⚠️ 現在は送信時間外です")
            print("   推奨時間帯:")
            print("   - 朝: 07:00-11:00")
            print("   - 昼: 12:00-16:00")
            print("   - 夜: 19:00-22:00")
            print("\n   強制実行する場合は --force オプションを使用してください")
            return
    else:
        session = args.session

    # 送信数決定
    session_limit = args.limit if args.limit else SESSION_MAX
    to_send = min(session_limit, total_unnotified)

    print(f"\n📅 セッション: {session or '手動実行'}")
    print(f"📧 送信予定: {to_send}通")

    # cron実行時は自動開始、手動実行時のみ確認
    if not args.force and sys.stdin.isatty():
        input("\n▶️  送信を開始します。Enter を押してください...")
    else:
        print("\n▶️  自動実行モード: 送信を開始します...")

    # セッション実行
    start_time = datetime.now()
    success, failed = run_session(session or '手動', max_count=to_send)
    end_time = datetime.now()
    elapsed = (end_time - start_time).total_seconds() / 60

    # 最終サマリー
    remaining = len(get_unnotified_releases(1000))

    print(f"\n{'='*70}")
    print(f"🎊 セッション完了")
    print(f"{'='*70}")
    print(f"✅ 成功: {success}通")
    print(f"❌ 失敗: {failed}通")
    print(f"⏱️  所要時間: {elapsed:.1f}分")
    print(f"📦 残り未通知: {remaining}件")
    print(f"{'='*70}")

    if remaining > 0:
        # 次回セッション予測
        next_sessions_needed = (remaining + SESSION_MAX - 1) // SESSION_MAX
        days_needed = (next_sessions_needed + DAILY_SESSIONS - 1) // DAILY_SESSIONS

        print(f"\n📅 残りの送信スケジュール:")
        print(f"  - 必要セッション数: {next_sessions_needed}回")
        print(f"  - 推定完了日数: {days_needed}日")
        print(f"  - 推定完了日: {(datetime.now() + timedelta(days=days_needed)).strftime('%Y-%m-%d')}")

if __name__ == "__main__":
    main()
