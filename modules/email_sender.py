#!/usr/bin/env python3
"""
Simple Email Sender Module for MangaAnime Info System
Provides basic email notification functionality for testing purposes.
"""

import smtplib
import ssl
import json
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailSender:
    def __init__(self, config_path: str = "config.json"):
        """Initialize email sender with configuration"""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)

            self.email_config = config.get("email", {})
            self.notification_email = config.get("notification_email", "")
            self.test_mode = self.email_config.get("test_mode", True)

            logger.info(
                f"Email sender initialized in {'test' if self.test_mode else 'production'} mode"
            )
        except Exception as e:
            logger.error(f"Failed to load email configuration: {e}")
            self.email_config = {}
            self.notification_email = ""
            self.test_mode = True

    def send_test_notification(self, message: str = "テスト通知") -> dict:
        """Send a test notification email"""
        try:
            if not self.notification_email:
                return {
                    "success": False,
                    "error": "通知先メールアドレスが設定されていません",
                }

            # In test mode, simulate email sending without actually sending
            if self.test_mode:
                logger.info(f"TEST MODE: Would send email to {self.notification_email}")
                logger.info(f"TEST MODE: Message content: {message}")

                return {
                    "success": True,
                    "message": f"テスト通知を{self.notification_email}に送信しました（テストモード）",
                    "details": {
                        "recipient": self.notification_email,
                        "timestamp": datetime.now().isoformat(),
                        "mode": "test",
                    },
                }

            # Production mode - actual email sending
            current_time = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")

            email_body = f"""
MangaAnime情報配信システムからのテスト通知です。

{message}

送信日時: {current_time}
システム状態: 正常稼働中

本メールは自動送信されています。
システムが正常に動作していることを確認できました。

---
MangaAnime情報配信システム
            """.strip()

            return self._send_actual_email(
                to_email=self.notification_email,
                subject="🔔 MangaAnime配信システム - テスト通知",
                body=email_body,
            )

        except Exception as e:
            logger.error(f"Failed to send test notification: {e}")
            return {"success": False, "error": f"メール送信エラー: {str(e)}"}

    def _send_actual_email(self, to_email: str, subject: str, body: str) -> dict:
        """Actually send email via SMTP (production mode) with Gmail authentication"""
        try:
            # Create message
            msg = MIMEMultipart()
            sender_email = self.email_config.get("sender_email", "system@localhost")
            sender_name = self.email_config.get("sender_name", "System")

            msg["From"] = f"{sender_name} <{sender_email}>"
            msg["To"] = to_email
            msg["Subject"] = subject

            # Add body
            msg.attach(MIMEText(body, "plain", "utf-8"))

            # SMTP configuration
            smtp_server = self.email_config.get("smtp_server", "localhost")
            smtp_port = self.email_config.get("smtp_port", 587)
            use_tls = self.email_config.get("use_tls", True)
            sender_password = self.email_config.get("sender_password", "")

            if not sender_password:
                return {
                    "success": False,
                    "error": "メール送信用のパスワードが設定されていません",
                }

            logger.info(
                f"Attempting to send email to {to_email} via {smtp_server}:{smtp_port}"
            )

            # Create secure connection and send
            context = ssl.create_default_context()

            with smtplib.SMTP(smtp_server, smtp_port) as server:
                # server.set_debuglevel(1)  # Disable debug output for production

                if use_tls:
                    logger.info("Starting TLS...")
                    server.starttls(context=context)

                # Gmail authentication with app password
                logger.info(f"Logging in as {sender_email}...")
                server.login(sender_email, sender_password)

                # Send the message
                logger.info("Sending message...")
                server.send_message(msg)

            logger.info(f"Email sent successfully to {to_email}")
            return {
                "success": True,
                "message": f"メールを{to_email}に送信しました",
                "details": {
                    "recipient": to_email,
                    "sender": sender_email,
                    "timestamp": datetime.now().isoformat(),
                    "mode": "production",
                },
            }

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP Authentication failed: {e}")
            return {
                "success": False,
                "error": f"Gmail認証エラー: アプリパスワードを確認してください ({str(e)})",
            }
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            return {"success": False, "error": f"SMTP送信エラー: {str(e)}"}
        except Exception as e:
            logger.error(f"General email error: {e}")
            return {"success": False, "error": f"メール送信エラー: {str(e)}"}

    def send_release_notification(self, releases: list) -> dict:
        """Send notification about new releases"""
        try:
            if not releases:
                return {"success": False, "error": "送信する新着情報がありません"}

            # Create email content
            subject = f"MangaAnime配信システム - 新着情報 ({len(releases)}件)"

            body_lines = [
                "新しいアニメ・マンガの配信情報をお知らせします。\n",
                f"取得日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
            ]

            for release in releases[:10]:  # Limit to first 10
                title = release.get("title", "不明な作品")
                episode = release.get("number", "不明")
                platform = release.get("platform", "不明")
                release_date = release.get("release_date", "不明")

                body_lines.append(
                    f"• {title} - 第{episode}話/巻 ({platform}) - {release_date}"
                )

            if len(releases) > 10:
                body_lines.append(f"\n他{len(releases) - 10}件の更新があります。")

            body_lines.append("\n---")
            body_lines.append("MangaAnime情報配信システム")

            body = "\n".join(body_lines)

            if self.test_mode:
                logger.info(
                    f"TEST MODE: Would send release notification with {len(releases)} releases"
                )
                return {
                    "success": True,
                    "message": f"新着情報通知を送信しました（テストモード）- {len(releases)}件",
                    "details": {
                        "recipient": self.notification_email,
                        "release_count": len(releases),
                        "mode": "test",
                    },
                }
            else:
                return self._send_actual_email(self.notification_email, subject, body)

        except Exception as e:
            logger.error(f"Failed to send release notification: {e}")
            return {"success": False, "error": f"新着情報通知エラー: {str(e)}"}


def test_email_functionality():
    """Test function to verify email functionality"""
    sender = EmailSender()
    result = sender.send_test_notification(
        "システムテスト - メール機能が正常に動作しています"
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    test_email_functionality()
