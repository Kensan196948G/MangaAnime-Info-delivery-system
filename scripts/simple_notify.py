#!/usr/bin/env python3
"""
最もシンプルな通知スクリプト
SMTPGmailSenderクラスを直接使用
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

def main():
    # 未通知リリースを1件取得
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
        LIMIT 1
    """)

    release = cursor.fetchone()

    if not release:
        print("✅ 未通知のリリースはありません")
        conn.close()
        return

    # メール送信
    sender = SMTPGmailSender()
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
</body>
</html>
"""

    print(f"📧 送信中: {subject}")

    sender.send_email(
        subject=subject,
        html_content=body,
        to_email=os.getenv('GMAIL_TO_EMAIL', 'kensan1969@gmail.com')
    )

    # 通知済みにマーク
    cursor.execute("UPDATE releases SET notified = 1 WHERE id = ?", (release['id'],))
    conn.commit()
    conn.close()

    print(f"✅ 通知送信完了: {title}")

if __name__ == "__main__":
    main()
