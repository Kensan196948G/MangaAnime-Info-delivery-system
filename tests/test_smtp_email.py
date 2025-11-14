#!/usr/bin/env python3
"""
SMTP経由でのメール送信テスト（App Password使用）
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os

def send_test_email():
    """App Passwordを使用したSMTP送信テスト"""
    
    # 設定
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = "kensan1969@gmail.com"
    receiver_email = "kensan1969@gmail.com"
    
    # App Password読み込み
    try:
        with open('gmail_app_password.txt', 'r') as f:
            app_password = f.read().strip()
        print(f"✅ App Password読み込み成功（長さ: {len(app_password)}文字）")
    except FileNotFoundError:
        print("❌ gmail_app_password.txtが見つかりません")
        return False
    
    # メール作成
    message = MIMEMultipart("alternative")
    message["Subject"] = f"[テスト] MangaAnime配信システム - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    message["From"] = sender_email
    message["To"] = receiver_email
    
    # HTML本文
    html_body = """
    <html>
      <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h2 style="color: #333;">🎉 メール送信テスト成功！</h2>
        <p>MangaAnime-Info-delivery-systemからのテストメールです。</p>
        
        <h3>📊 システム状態</h3>
        <ul>
          <li>✅ SMTP接続: 成功</li>
          <li>✅ App Password認証: 成功</li>
          <li>✅ メール送信: 成功</li>
        </ul>
        
        <h3>📺 テストデータ（サンプル）</h3>
        <table border="1" cellpadding="10" cellspacing="0" style="border-collapse: collapse;">
          <tr style="background-color: #f0f0f0;">
            <th>作品名</th>
            <th>エピソード</th>
            <th>配信日</th>
          </tr>
          <tr>
            <td>呪術廻戦</td>
            <td>第3期 第1話</td>
            <td>2025-09-03</td>
          </tr>
          <tr>
            <td>ワンピース</td>
            <td>第1125話</td>
            <td>2025-09-03</td>
          </tr>
        </table>
        
        <hr style="margin: 20px 0;">
        <p style="color: #666; font-size: 12px;">
          このメールは自動配信システムのテストです。<br>
          送信時刻: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """
        </p>
      </body>
    </html>
    """
    
    # テキスト本文（フォールバック）
    text_body = """
    メール送信テスト成功！
    
    MangaAnime-Info-delivery-systemからのテストメールです。
    
    システム状態:
    - SMTP接続: 成功
    - App Password認証: 成功
    - メール送信: 成功
    
    送信時刻: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # MIMEパート追加
    part1 = MIMEText(text_body, "plain")
    part2 = MIMEText(html_body, "html")
    message.attach(part1)
    message.attach(part2)
    
    # SMTP送信
    try:
        print("📧 SMTP接続開始...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # TLS暗号化
        
        print("🔐 認証中...")
        server.login(sender_email, app_password)
        
        print("📮 メール送信中...")
        text = message.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()
        
        print("✅ メール送信成功！")
        print(f"📬 {receiver_email} のメールボックスを確認してください")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ 認証エラー: {e}")
        print("App Passwordが正しいか確認してください")
        return False
    except Exception as e:
        print(f"❌ 送信エラー: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("📧 SMTP メール送信テスト（App Password使用）")
    print("=" * 60)
    
    if send_test_email():
        print("\n✅ テスト完了: メール配信機能は正常に動作しています")
    else:
        print("\n❌ テスト失敗: 設定を確認してください")