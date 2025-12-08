#!/usr/bin/env python3
"""
メール配信機能のテストスクリプト
Gmail SMTPを使用してテストメールを送信
"""

import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()


def load_config():
    """設定ファイルを読み込み"""
    with open("config.json", "r", encoding="utf-8") as f:
        return json.load(f)


def test_email_sending():
    """メール送信テスト"""
    config = load_config()
    email_config = config.get("email", {})

    # 設定値を取得
    smtp_server = email_config.get("smtp_server", "smtp.gmail.com")
    smtp_port = email_config.get("smtp_port", 587)
    sender_email = email_config.get("sender_email")
    sender_password = os.getenv("GMAIL_APP_PASSWORD") or email_config.get(
        "sender_password", ""
    ).replace("${GMAIL_APP_PASSWORD}", "")
    recipient_email = config.get("notification_email")

    logger.info("📧 メール配信テスト開始")
    logger.info(f"   送信元: {sender_email}")
    logger.info(f"   送信先: {recipient_email}")
    logger.info(f"   SMTPサーバー: {smtp_server}:{smtp_port}")

    # パスワードチェック
    if not sender_password or sender_password == "${GMAIL_APP_PASSWORD}":
        logger.info("❌ エラー: Gmail App Passwordが設定されていません")
        logger.info("\n📝 設定方法:")
        logger.info("1. Googleアカウントで2段階認証を有効化")
        logger.info("2. https://myaccount.google.com/apppasswords でアプリパスワードを生成")
        logger.info("3. 以下のコマンドで環境変数を設定:")
        logger.info(f"   export GMAIL_APP_PASSWORD='生成された16文字のパスワード'")
        logger.info("4. または .env ファイルに記載:")
        logger.info("   GMAIL_APP_PASSWORD=生成された16文字のパスワード")
        return False

    # テストメール作成
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg[
        "Subject"
    ] = f"[テスト] MangaAnime配信システム - {datetime.now().strftime('%Y-%m-%d %H:%M')}"

    body = """
    🎉 メール配信テスト成功！

    このメールが届いていれば、MangaAnime情報配信システムの
    メール機能は正常に動作しています。

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    システム情報:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    送信時刻: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}
    SMTPサーバー: {smtp_server}
    送信元: {sender_email}

    ✅ メール配信機能: 正常
    ✅ SMTP認証: 成功
    ✅ TLS暗号化: 有効

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    今後、新しいアニメ・マンガ情報が
    このアドレスに自動配信されます。

    MangaAnime情報配信システム
    """

    msg.attach(MIMEText(body, "plain", "utf-8"))

    # メール送信
    try:
        logger.info("\n🔄 SMTP接続中...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # TLS暗号化

        logger.info("🔐 認証中...")
        server.login(sender_email, sender_password)

        logger.info("📤 メール送信中...")
        text = msg.as_string()
        server.sendmail(sender_email, recipient_email, text)
        server.quit()

        logger.info("✅ メール送信成功！")
        logger.info(f"   {recipient_email} にテストメールを送信しました")
        return True

    except smtplib.SMTPAuthenticationError as e:
        logger.info(f"❌ 認証エラー: {e}")
        logger.info("\n対処法:")
        logger.info("1. Gmail App Passwordが正しいか確認")
        logger.info("2. 2段階認証が有効になっているか確認")
        logger.info("3. アプリパスワードを再生成してみる")
        return False

    except smtplib.SMTPException as e:
        logger.info(f"❌ SMTP エラー: {e}")
        return False

    except Exception as e:
        logger.info(f"❌ 予期しないエラー: {e}")
        return False


def check_pending_notifications():
    """保留中の通知を確認"""
    import sqlite3

    try:
        conn = sqlite3.connect("db.sqlite3")
        cursor = conn.cursor()

        # 未通知のリリースを確認
        cursor.execute(
            """
            SELECT COUNT(*) FROM releases

            WHERE notified = 0
        """
        )
        pending = cursor.fetchone()[0]

        logger.info("\n📊 通知状況:")
        logger.info(f"   保留中の通知: {pending} 件")

        if pending > 100:
            logger.info("   ⚠️  大量の通知が滞留しています")
            logger.info("   メール設定を修正後、手動で通知処理を実行してください")

        conn.close()

    except Exception as e:
        logger.info(f"データベースエラー: {e}")


if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("MangaAnime メール配信機能テスト")
    logger.info("=" * 50)

    # メール送信テスト
    success = test_email_sending()

    # 保留通知の確認
    check_pending_notifications()

    logger.info("\n" + "=" * 50)
    if success:
        logger.info("✅ テスト完了: メール配信は正常に動作しています")
    else:
        logger.info("❌ テスト失敗: 上記のエラーを確認してください")
    logger.info("=" * 50)
