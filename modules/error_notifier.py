#!/usr/bin/env python3
"""
エラー通知メール送信モジュール
配信エラーやシステムエラー発生時にkensan1969@gmail.comに通知を送信
"""

import json
import logging
import os

logger = logging.getLogger(__name__)
import smtplib
import sys
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Optional


class ErrorNotifier:
    """エラー通知メール送信クラス"""

    def __init__(self, config_path: str = "./config.json"):
        """
        初期化

        Args:
            config_path: 設定ファイルのパス
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.error_config = self.config.get("error_notifications", {})
        self.cooldown_file = "./logs/error_notification_cooldown.json"

        # ログ設定
        self.logger = logging.getLogger(__name__)

    def _load_config(self) -> Dict:
        """設定ファイルを読み込む"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logging.getLogger(__name__).error(f"設定ファイル読み込みエラー: {e}")
            return {}

    def _load_cooldown_data(self) -> Dict:
        """クールダウンデータを読み込む"""
        try:
            if os.path.exists(self.cooldown_file):
                with open(self.cooldown_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return {"last_sent": None, "hourly_count": 0, "hourly_reset": None}

    def _save_cooldown_data(self, data: Dict):
        """クールダウンデータを保存"""
        try:
            os.makedirs(os.path.dirname(self.cooldown_file), exist_ok=True)
            with open(self.cooldown_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"クールダウンデータ保存エラー: {e}")

    def _is_rate_limited(self) -> tuple[bool, str]:
        """レート制限チェック"""
        if not self.error_config.get("enabled", False):
            return True, "エラー通知機能が無効です"

        cooldown_data = self._load_cooldown_data()
        now = datetime.now()

        # クールダウンチェック
        cooldown_minutes = self.error_config.get("cooldown_minutes", 30)
        if cooldown_data.get("last_sent"):
            last_sent = datetime.fromisoformat(cooldown_data["last_sent"])
            time_diff = now - last_sent
            if time_diff < timedelta(minutes=cooldown_minutes):
                remaining = cooldown_minutes - int(time_diff.total_seconds() / 60)
                return True, f"クールダウン中 (残り{remaining}分)"

        # 時間あたりの制限チェック
        max_per_hour = self.error_config.get("max_emails_per_hour", 5)
        hourly_reset = cooldown_data.get("hourly_reset")
        hourly_count = cooldown_data.get("hourly_count", 0)

        if hourly_reset:
            reset_time = datetime.fromisoformat(hourly_reset)
            if now - reset_time >= timedelta(hours=1):
                hourly_count = 0
                cooldown_data["hourly_reset"] = now.isoformat()
        else:
            cooldown_data["hourly_reset"] = now.isoformat()

        if hourly_count >= max_per_hour:
            return (
                True,
                f"時間あたりの送信制限に達しました ({hourly_count}/{max_per_hour})",
            )

        return False, ""

    def send_error_notification(
        self,
        error_type: str,
        error_message: str,
        error_details: Optional[str] = None,
        log_file_path: Optional[str] = None,
    ) -> bool:
        """
        エラー通知メールを送信

        Args:
            error_type: エラータイプ (例: "配信エラー", "システムエラー")
            error_message: エラーメッセージ
            error_details: 詳細情報
            log_file_path: ログファイルパス

        Returns:
            bool: 送信成功かどうか
        """
        # レート制限チェック
        is_limited, limit_reason = self._is_rate_limited()
        if is_limited:
            self.logger.warning(f"エラー通知送信スキップ: {limit_reason}")
            return False

        try:
            # メール作成
            msg = self._create_error_email(error_type, error_message, error_details, log_file_path)
            if not msg:
                return False

            # メール送信
            success = self._send_email(msg)

            if success:
                # クールダウンデータ更新
                cooldown_data = self._load_cooldown_data()
                cooldown_data["last_sent"] = datetime.now().isoformat()
                cooldown_data["hourly_count"] = cooldown_data.get("hourly_count", 0) + 1
                self._save_cooldown_data(cooldown_data)

                self.logger.info(f"エラー通知メール送信成功: {error_type}")

            return success

        except Exception as e:
            self.logger.error(f"エラー通知送信中にエラー: {e}")
            return False

    def _create_error_email(
        self,
        error_type: str,
        error_message: str,
        error_details: Optional[str],
        log_file_path: Optional[str],
    ) -> Optional[MIMEMultipart]:
        """エラー通知メールを作成"""
        try:
            msg = MIMEMultipart()

            # ヘッダー設定
            subject_prefix = self.error_config.get("subject_prefix", "🚨 システムエラー")
            msg["Subject"] = f"{subject_prefix} - {error_type}"
            msg["From"] = (
                f"{self.error_config.get('sender_name', 'MangaAnime監視システム')} <{self.error_config.get('sender_email')}>"
            )
            msg["To"] = self.error_config.get("recipient_email")

            # メール本文作成
            body = self._create_error_email_body(
                error_type, error_message, error_details, log_file_path
            )
            msg.attach(MIMEText(body, "html", "utf-8"))

            return msg

        except Exception as e:
            self.logger.error(f"エラーメール作成エラー: {e}")
            return None

    def _create_error_email_body(
        self,
        error_type: str,
        error_message: str,
        error_details: Optional[str],
        log_file_path: Optional[str],
    ) -> str:
        """エラーメール本文を作成"""
        now = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")

        # ログファイルの最新エラーを取得
        recent_logs = ""
        if log_file_path and os.path.exists(log_file_path):
            try:
                with open(log_file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    recent_logs = "".join(lines[-20:])  # 最新20行
            except Exception:
                recent_logs = "ログファイル読み込みエラー"

        html_body = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: 'Hiragino Sans', 'Yu Gothic', sans-serif; margin: 20px; }}
                .header {{ background-color: #dc3545; color: white; padding: 15px; border-radius: 5px; }}
                .content {{ background-color: #f8f9fa; padding: 20px; margin: 10px 0; border-radius: 5px; }}
                .error-box {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                .logs {{ background-color: #343a40; color: #ffffff; padding: 15px; margin: 10px 0; border-radius: 5px; font-family: monospace; font-size: 12px; max-height: 300px; overflow-y: auto; }}
                .footer {{ color: #6c757d; font-size: 12px; margin-top: 20px; }}
                .status {{ font-weight: bold; color: #dc3545; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>🚨 MangaAnime システムエラー通知</h2>
            </div>

            <div class="content">
                <h3>エラー概要</h3>
                <p><strong>エラータイプ:</strong> <span class="status">{error_type}</span></p>
                <p><strong>発生時刻:</strong> {now}</p>
                <p><strong>システム:</strong> MangaAnime情報配信システム</p>
            </div>

            <div class="error-box">
                <h3>🔍 エラー詳細</h3>
                <p><strong>メッセージ:</strong></p>
                <pre>{error_message}</pre>

                {f'<p><strong>詳細情報:</strong></p><pre>{error_details}</pre>' if error_details else ''}
            </div>

            {'<div class="logs"><h3>📋 最新ログ (直近20行)</h3><pre>' + recent_logs + '</pre></div>' if recent_logs else ''}

            <div class="content">
                <h3>🔧 推奨対応</h3>
                <ul>
                    <li>システムログを確認してください</li>
                    <li>Web UI (http://192.168.3.135:3030) で状態を確認してください</li>
                    <li>必要に応じてシステムを再起動してください</li>
                    <li>問題が継続する場合は、設定ファイルを確認してください</li>
                </ul>
            </div>

            <div class="footer">
                <p>このメールはMangaAnime情報配信システムから自動送信されました。</p>
                <p>システム監視: kensan1969@gmail.com</p>
                <p>送信時刻: {now}</p>
            </div>
        </body>
        </html>
        """

        return html_body

    def _send_email(self, msg: MIMEMultipart) -> bool:
        """メールを送信"""
        try:
            smtp_server = self.error_config.get("smtp_server")
            smtp_port = self.error_config.get("smtp_port", 587)
            sender_email = self.error_config.get("sender_email")
            sender_password = self.error_config.get("sender_password")
            use_tls = self.error_config.get("use_tls", True)

            if not all([smtp_server, sender_email, sender_password]):
                self.logger.error("SMTP設定が不完全です")
                return False

            with smtplib.SMTP(smtp_server, smtp_port) as server:
                if use_tls:
                    server.starttls()

                server.login(sender_email, sender_password)
                text = msg.as_string()
                server.sendmail(sender_email, self.error_config.get("recipient_email"), text)

            return True

        except Exception as e:
            self.logger.error(f"メール送信エラー: {e}")
            return False

    def test_notification(self) -> bool:
        """テスト通知を送信"""
        return self.send_error_notification(
            error_type="テスト通知",
            error_message="エラー通知システムのテストメールです。",
            error_details="システムが正常に動作しています。",
        )


def main():
    """コマンドライン実行用のメイン関数"""
    if len(sys.argv) < 3:
        logger.info(
            "使用方法: python error_notifier.py <error_type> <error_message> [error_details] [log_file_path]"
        )
        logger.info(
            "例: python error_notifier.py '配信エラー' 'メール送信に失敗しました' '詳細情報' './logs/app.log'"
        )
        sys.exit(1)

    error_type = sys.argv[1]
    error_message = sys.argv[2]
    error_details = sys.argv[3] if len(sys.argv) > 3 else None
    log_file_path = sys.argv[4] if len(sys.argv) > 4 else None

    notifier = ErrorNotifier()
    success = notifier.send_error_notification(
        error_type, error_message, error_details, log_file_path
    )

    if success:
        logger.info("✅ エラー通知メール送信完了")
        sys.exit(0)
    else:
        logger.info("❌ エラー通知メール送信失敗")
        sys.exit(1)


if __name__ == "__main__":
    main()
