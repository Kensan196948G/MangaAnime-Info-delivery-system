"""
Gmail送信モジュール（型ヒント付き）
"""
import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional
import logging

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/gmail.send']


def get_gmail_service(
    credentials_path: str = "config/credentials.json",
    token_path: str = "config/token.json"
) -> Resource:
    """
    Gmail APIサービスを取得

    Args:
        credentials_path: 認証情報ファイルのパス
        token_path: トークンファイルのパス

    Returns:
        Resource: Gmail APIサービスオブジェクト
    """
    creds: Optional[Credentials] = None

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    service: Resource = build('gmail', 'v1', credentials=creds)
    return service


def create_html_message(
    sender: str,
    to: str,
    subject: str,
    html_body: str
) -> Dict[str, Any]:
    """
    HTMLメールメッセージを作成

    Args:
        sender: 送信者アドレス
        to: 受信者アドレス
        subject: 件名
        html_body: HTML本文

    Returns:
        Dict[str, Any]: 送信用メッセージ
    """
    message = MIMEMultipart('alternative')
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject

    html_part = MIMEText(html_body, 'html', 'utf-8')
    message.attach(html_part)

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    return {'raw': raw_message}


def send_email(
    service: Resource,
    message: Dict[str, Any]
) -> Dict[str, Any]:
    """
    メールを送信

    Args:
        service: Gmail APIサービス
        message: 送信メッセージ

    Returns:
        Dict[str, Any]: 送信結果
    """
    try:
        sent_message: Dict[str, Any] = service.users().messages().send(
            userId='me',
            body=message
        ).execute()
        logger.info(f"メール送信成功: Message ID {sent_message['id']}")
        return sent_message
    except Exception as e:
        logger.error(f"メール送信エラー: {e}")
        raise


def generate_release_html(releases: List[Dict[str, Any]]) -> str:
    """
    リリース情報からHTML本文を生成

    Args:
        releases: リリース情報のリスト

    Returns:
        str: HTML本文
    """
    html = """
    <html>
    <head>
        <style>
            body {
                font-family: 'Helvetica Neue', Arial, sans-serif;
                background-color: #f5f5f5;
                margin: 0;
                padding: 20px;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background-color: white;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                overflow: hidden;
            }
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }
            .header h1 {
                margin: 0;
                font-size: 28px;
            }
            .content {
                padding: 30px;
            }
            .release-item {
                border-left: 4px solid #667eea;
                padding: 15px;
                margin-bottom: 20px;
                background-color: #f9f9f9;
                border-radius: 4px;
            }
            .release-title {
                font-size: 20px;
                font-weight: bold;
                color: #333;
                margin-bottom: 10px;
            }
            .release-info {
                color: #666;
                margin: 5px 0;
            }
            .release-link {
                display: inline-block;
                margin-top: 10px;
                padding: 8px 16px;
                background-color: #667eea;
                color: white;
                text-decoration: none;
                border-radius: 4px;
            }
            .release-link:hover {
                background-color: #5568d3;
            }
            .footer {
                text-align: center;
                padding: 20px;
                color: #999;
                font-size: 12px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎬 アニメ・マンガ最新情報</h1>
            </div>
            <div class="content">
    """

    for release in releases:
        work_type_emoji = "🎬" if release.get('work_type') == 'anime' else "📚"
        release_type_text = "話" if release.get('release_type') == 'episode' else "巻"

        html += f"""
                <div class="release-item">
                    <div class="release-title">
                        {work_type_emoji} {release.get('title', '不明')}
                    </div>
                    <div class="release-info">
                        <strong>種別:</strong> {'アニメ' if release.get('work_type') == 'anime' else 'マンガ'}
                    </div>
                    <div class="release-info">
                        <strong>内容:</strong> 第{release.get('number', '?')}{release_type_text}
                    </div>
        """

        if release.get('platform'):
            html += f"""
                    <div class="release-info">
                        <strong>配信:</strong> {release['platform']}
                    </div>
            """

        if release.get('release_date'):
            html += f"""
                    <div class="release-info">
                        <strong>公開日:</strong> {release['release_date']}
                    </div>
            """

        if release.get('source_url'):
            html += f"""
                    <a href="{release['source_url']}" class="release-link">詳細を見る</a>
            """

        html += """
                </div>
        """

    html += """
            </div>
            <div class="footer">
                このメールはアニメ・マンガ最新情報配信システムから自動送信されました
            </div>
        </div>
    </body>
    </html>
    """

    return html


def send_release_notification(
    releases: List[Dict[str, Any]],
    recipient: str,
    credentials_path: str = "config/credentials.json",
    token_path: str = "config/token.json"
) -> Optional[Dict[str, Any]]:
    """
    リリース通知メールを送信

    Args:
        releases: リリース情報のリスト
        recipient: 受信者アドレス
        credentials_path: 認証情報ファイルのパス
        token_path: トークンファイルのパス

    Returns:
        Optional[Dict[str, Any]]: 送信結果（エラー時はNone）
    """
    if not releases:
        logger.info("送信するリリース情報がありません")
        return None

    try:
        service = get_gmail_service(credentials_path, token_path)
        html_body = generate_release_html(releases)

        count = len(releases)
        subject = f"【新着{count}件】アニメ・マンガ最新情報"

        message = create_html_message(
            sender='me',
            to=recipient,
            subject=subject,
            html_body=html_body
        )

        result = send_email(service, message)
        logger.info(f"{count}件のリリース通知を送信しました")

        return result

    except Exception as e:
        logger.error(f"通知送信エラー: {e}")
        return None
