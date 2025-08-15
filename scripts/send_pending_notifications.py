#!/usr/bin/env python3
"""
滞留している通知を段階的に送信するスクリプト
Gmailのレート制限を考慮して、バッチ処理で送信
"""

import os
import json
import time
import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv
import sys
sys.path.append('.')
from modules.title_translator import TitleTranslator

# 環境変数を読み込み
load_dotenv()

# タイトル翻訳機能を初期化
translator = TitleTranslator()

# 設定
BATCH_SIZE = 20  # 一度に送信する通知数
DELAY_BETWEEN_BATCHES = 60  # バッチ間の待機時間（秒）
MAX_NOTIFICATIONS = 100  # 1回の実行で送信する最大数

def load_config():
    """設定ファイルを読み込み"""
    with open('config.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def get_pending_releases(limit=20):
    """未通知のリリースを取得"""
    conn = sqlite3.connect('db.sqlite3')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT r.*, w.title, w.type
        FROM releases r
        JOIN works w ON r.work_id = w.id
        WHERE r.notified = 0
        ORDER BY r.release_date DESC
        LIMIT ?
    """, (limit,))
    
    releases = cursor.fetchall()
    conn.close()
    return releases

def mark_as_notified(release_ids):
    """通知済みとしてマーク"""
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    for release_id in release_ids:
        cursor.execute("""
            UPDATE releases 
            SET notified = 1 
            WHERE id = ?
        """, (release_id,))
    
    conn.commit()
    conn.close()

def send_notification_email(releases, config):
    """通知メールを送信"""
    email_config = config.get('email', {})
    
    smtp_server = email_config.get('smtp_server', 'smtp.gmail.com')
    smtp_port = email_config.get('smtp_port', 587)
    sender_email = email_config.get('sender_email')
    sender_password = os.getenv('GMAIL_APP_PASSWORD')
    recipient_email = config.get('notification_email')
    
    if not sender_password:
        print("❌ Gmail App Passwordが設定されていません")
        return False
    
    # メール本文を作成
    anime_releases = [r for r in releases if r['type'] == 'anime']
    manga_releases = [r for r in releases if r['type'] == 'manga']
    
    body = "📅 MangaAnime 新着情報\n"
    body += f"配信日: {datetime.now().strftime('%Y年%m月%d日')}\n"
    body += "=" * 50 + "\n\n"
    
    if anime_releases:
        body += "🎬 アニメ新着情報\n"
        body += "-" * 30 + "\n"
        for r in anime_releases[:10]:  # 最大10件
            # タイトルを日本語化
            japanese_title = translator.translate(r['title'])
            body += f"• {japanese_title}\n"
            if r['number']:
                body += f"  第{r['number']}話\n"
            if r['platform']:
                body += f"  配信: {r['platform']}\n"
            body += f"  日付: {r['release_date']}\n\n"
    
    if manga_releases:
        body += "\n📚 マンガ新着情報\n"
        body += "-" * 30 + "\n"
        for r in manga_releases[:10]:  # 最大10件
            # タイトルを日本語化
            japanese_title = translator.translate(r['title'])
            body += f"• {japanese_title}\n"
            if r['number']:
                body += f"  第{r['number']}巻\n"
            if r['platform']:
                body += f"  配信: {r['platform']}\n"
            body += f"  日付: {r['release_date']}\n\n"
    
    body += "\n" + "=" * 50 + "\n"
    body += "MangaAnime情報配信システム\n"
    body += f"通知数: {len(releases)}件\n"
    
    # メール送信
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg['Subject'] = f"[MangaAnime] 新着 {len(releases)}件 - {datetime.now().strftime('%m/%d')}"
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"❌ メール送信エラー: {e}")
        return False

def main():
    """メイン処理"""
    print("=" * 60)
    print("📧 滞留通知送信スクリプト")
    print("=" * 60)
    
    config = load_config()
    
    # 未通知の総数を確認
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM releases WHERE notified = 0")
    total_pending = cursor.fetchone()[0]
    conn.close()
    
    print(f"\n📊 現在の状況:")
    print(f"   未通知リリース: {total_pending} 件")
    print(f"   バッチサイズ: {BATCH_SIZE} 件/回")
    print(f"   最大送信数: {MAX_NOTIFICATIONS} 件")
    print()
    
    if total_pending == 0:
        print("✅ 送信待ちの通知はありません")
        return
    
    sent_count = 0
    batch_count = 0
    
    while sent_count < MAX_NOTIFICATIONS and sent_count < total_pending:
        batch_count += 1
        print(f"\n🔄 バッチ {batch_count} 処理中...")
        
        # 未通知のリリースを取得
        releases = get_pending_releases(BATCH_SIZE)
        
        if not releases:
            break
        
        print(f"   {len(releases)} 件を送信...")
        
        # メール送信
        if send_notification_email(releases, config):
            # 成功したら通知済みにマーク
            release_ids = [r['id'] for r in releases]
            mark_as_notified(release_ids)
            sent_count += len(releases)
            print(f"   ✅ 送信成功 (累計: {sent_count} 件)")
        else:
            print(f"   ❌ 送信失敗")
            break
        
        # 次のバッチまで待機
        if sent_count < MAX_NOTIFICATIONS and sent_count < total_pending:
            print(f"   ⏸️  {DELAY_BETWEEN_BATCHES}秒待機中...")
            time.sleep(DELAY_BETWEEN_BATCHES)
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("📊 送信結果:")
    print(f"   送信済み: {sent_count} 件")
    print(f"   残り: {total_pending - sent_count} 件")
    
    if total_pending - sent_count > 0:
        print(f"\n💡 ヒント: 残りの通知を送信するには、再度このスクリプトを実行してください")
    else:
        print("\n✅ すべての通知を送信しました！")
    
    print("=" * 60)

if __name__ == "__main__":
    main()