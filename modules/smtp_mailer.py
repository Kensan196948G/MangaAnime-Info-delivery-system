#!/usr/bin/env python3
"""
SMTPベースのGmail送信モジュール (App Passwordを使用)
OAuth2不要で動作する代替実装
"""

import logging
import os
import smtplib

logger = logging.getLogger(__name__)
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict

from dotenv import load_dotenv

load_dotenv()


class SMTPGmailSender:
    """SMTP経由でGmailを送信するクラス"""

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize SMTP Gmail sender.

        Args:
            config: Configuration dictionary (optional, uses .env if not provided)
        """
        self.config = config or {}

        # .envまたはconfig.jsonから設定を取得
        gmail_config = self.config.get("google", {}).get("gmail", {})

        self.sender_email = (
            os.getenv("GMAIL_SENDER_EMAIL")
            or gmail_config.get("from_email")
            or os.getenv("GMAIL_ADDRESS")
        )
        self.recipient_email = (
            os.getenv("GMAIL_RECIPIENT_EMAIL") or gmail_config.get("to_email") or self.sender_email
        )
        self.app_password = os.getenv("GMAIL_APP_PASSWORD")

        # Gmail SMTP設定
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587  # TLS

        # 送信統計
        self.total_sent = 0
        self.total_failed = 0

        logger.info(f"SMTP Gmail Sender initialized for {self.sender_email}")

    def validate_config(self) -> bool:
        """設定の検証"""
        if not self.sender_email:
            logger.error("Sender email not configured")
            return False

        if not self.recipient_email:
            logger.error("Recipient email not configured")
            return False

        if not self.app_password:
            logger.error("Gmail App Password not configured")
            return False

        return True

    def send_email(
        self,
        subject: str,
        html_content: str,
        text_content: str = None,
        to_email: str = None,
    ) -> bool:
        """
        Send email via SMTP.

        Args:
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text email body (optional)
            to_email: Recipient email (optional, uses default if not provided)

        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.validate_config():
            return False

        recipient = to_email or self.recipient_email

        try:
            # メッセージ作成
            message = MIMEMultipart("alternative")
            message["From"] = self.sender_email
            message["To"] = recipient
            message["Subject"] = subject

            # テキスト部分
            if text_content:
                text_part = MIMEText(text_content, "plain", "utf-8")
                message.attach(text_part)

            # HTML部分
            html_part = MIMEText(html_content, "html", "utf-8")
            message.attach(html_part)

            # SMTP接続と送信
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # TLS暗号化
                server.login(self.sender_email, self.app_password)
                server.send_message(message)

            self.total_sent += 1
            logger.info(f"Email sent successfully to {recipient}: {subject}")
            return True

        except smtplib.SMTPAuthenticationError as e:
            self.total_failed += 1
            logger.error(f"SMTP Authentication failed: {e}")
            logger.error("Please check GMAIL_APP_PASSWORD in .env file")
            return False

        except smtplib.SMTPException as e:
            self.total_failed += 1
            logger.error(f"SMTP error occurred: {e}")
            return False

        except Exception as e:
            self.total_failed += 1
            logger.error(f"Failed to send email: {e}")
            return False

    def send_test_email(self) -> bool:
        """テストメールを送信"""
        subject = "[テスト] Gmail SMTP接続確認"

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #4CAF50;">Gmail SMTP接続テスト成功</h2>
            <p>このメールは、MangaAnime情報配信システムのGmail SMTP接続テストです。</p>
            <div style="background-color: #f0f0f0; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h3>送信情報:</h3>
                <ul>
                    <li><strong>送信元:</strong> {self.sender_email}</li>
                    <li><strong>送信先:</strong> {self.recipient_email}</li>
                    <li><strong>送信時刻:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                    <li><strong>方式:</strong> SMTP (TLS)</li>
                </ul>
            </div>
            <p style="color: #666; font-size: 0.9em;">
                ※ このメールが正常に届いていれば、Gmail送信機能が正常に動作しています。
            </p>
        </body>
        </html>
        """

        text_content = f"""
        Gmail SMTP接続テスト成功
        
        このメールは、MangaAnime情報配信システムのGmail SMTP接続テストです。
        
        送信元: {self.sender_email}
        送信先: {self.recipient_email}
        送信時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        方式: SMTP (TLS)
        
        ※ このメールが正常に届いていれば、Gmail送信機能が正常に動作しています。
        """

        return self.send_email(subject, html_content, text_content)

    def get_stats(self) -> Dict[str, Any]:
        """送信統計を取得"""
        total = self.total_sent + self.total_failed
        success_rate = (self.total_sent / total * 100) if total > 0 else 0

        return {
            "total_sent": self.total_sent,
            "total_failed": self.total_failed,
            "success_rate": f"{success_rate:.1f}%",
            "is_configured": self.validate_config(),
        }


# スタンドアロンテスト用
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger.info("=" * 60)
    logger.info("Gmail SMTP送信テスト")
    logger.info("=" * 60)

    sender = SMTPGmailSender()

    logger.info(f"\n設定情報:")
    logger.info(f"  送信元: {sender.sender_email}")
    logger.info(f"  送信先: {sender.recipient_email}")
    logger.info(f"  App Password: {'設定済み' if sender.app_password else '未設定'}")

    if sender.validate_config():
        logger.info("\n✅ 設定OK - テストメールを送信します...")
        if sender.send_test_email():
            logger.info("✅ テストメール送信成功!")
            logger.info(f"\n統計: {sender.get_stats()}")
        else:
            logger.info("❌ テストメール送信失敗")
    else:
        logger.info("\n❌ 設定エラー - .envファイルを確認してください")
