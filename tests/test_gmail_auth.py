#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gmail認証・送信統合テストスクリプト
- OAuth2認証（Gmail API）とApp Password（SMTP）の両方をテスト
- 実際のメール送信テスト機能
- 認証設定の詳細診断
"""

import argparse
import base64
import json
import smtplib
import sys
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict, Optional, Tuple

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'auth'))
try:
    from auth_config import AuthConfig
except ImportError:
    # Fallback: create a mock AuthConfig
    class AuthConfig:
        def __init__(self):
            pass


class GmailAuthTester:
    """Gmail認証テスト統合クラス"""
    
    def __init__(self):
        self.auth_config = AuthConfig()
    
    def test_oauth2_auth(self, send_test_email: bool = False) -> Tuple[bool, str]:
        """OAuth2認証をテスト"""
        try:
            # token.json の存在確認
            if not self.auth_config.token_file.exists():
                return False, "token.json が見つかりません。create_token.py を実行してください"
            
            # トークン読み込み
            with open(self.auth_config.token_file, 'r', encoding='utf-8') as f:
                token_data = json.load(f)
            
            # 認証情報の作成
            creds = Credentials.from_authorized_user_info(token_data)
            
            # Gmail APIサービス作成
            service = build('gmail', 'v1', credentials=creds)
            
            # プロフィール情報取得テスト
            profile = service.users().getProfile(userId='me').execute()
            email_address = profile.get('emailAddress')
            
            result_msg = f"✅ OAuth2認証成功: {email_address}"
            
            # テストメール送信（オプション）
            if send_test_email:
                try:
                    test_result = self._send_test_email_oauth2(service, email_address)
                    result_msg += f"\n{test_result}"
                except Exception as e:
                    result_msg += f"\n⚠️ テストメール送信に失敗: {e}"
            
            return True, result_msg
            
        except FileNotFoundError:
            return False, "token.json または credentials.json が見つかりません"
        except HttpError as e:
            return False, f"Gmail API エラー: {e}"
        except Exception as e:
            return False, f"OAuth2認証エラー: {e}"
    
    def test_app_password_auth(self, send_test_email: bool = False) -> Tuple[bool, str]:
        """Gmail App Password認証をテスト"""
        try:
            # Gmail設定の読み込み
            gmail_config = self.auth_config.load_gmail_config()
            if not gmail_config:
                return False, "gmail_config.json の読み込みに失敗しました"
            
            email_address = gmail_config['email_address']
            app_password = gmail_config['app_password']
            smtp_server = gmail_config.get('smtp_server', 'smtp.gmail.com')
            smtp_port = gmail_config.get('smtp_port', 587)
            
            # SMTP接続テスト
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(email_address, app_password)
            
            result_msg = f"✅ App Password認証成功: {email_address}"
            
            # テストメール送信（オプション）
            if send_test_email:
                try:
                    test_result = self._send_test_email_smtp(server, email_address, gmail_config)
                    result_msg += f"\n{test_result}"
                except Exception as e:
                    result_msg += f"\n⚠️ テストメール送信に失敗: {e}"
            
            server.quit()
            return True, result_msg
            
        except smtplib.SMTPAuthenticationError:
            return False, "認証に失敗しました。App Passwordが正しいか確認してください"
        except smtplib.SMTPConnectError:
            return False, "SMTPサーバーに接続できませんでした"
        except Exception as e:
            return False, f"App Password認証エラー: {e}"
    
    def _send_test_email_oauth2(self, service, email_address: str) -> str:
        """OAuth2を使用してテストメールを送信"""
        try:
            # メール内容作成
            message = MIMEMultipart('alternative')
            message['to'] = email_address
            message['from'] = email_address
            message['subject'] = 'アニメ・マンガ通知システム - OAuth2テスト'
            
            # HTML本文
            html_body = """
            <html>
                <body>
                    <h2>🎉 OAuth2認証テスト成功！</h2>
                    <p>MangaAnime-Info-delivery-systemのGmail API認証が正常に動作しています。</p>
                    <ul>
                        <li>📧 認証方式: OAuth2 (Gmail API)</li>
                        <li>🕒 送信日時: {}</li>
                        <li>⚡ システム状態: 正常</li>
                    </ul>
                    <p>システムの準備が完了しました！</p>
                </body>
            </html>
            """.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            message.attach(MIMEText(html_body, 'html'))
            
            # Base64エンコード
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # メール送信
            send_result = service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            return f"✅ テストメール送信成功 (ID: {send_result['id']})"
            
        except Exception as e:
            raise Exception(f"OAuth2メール送信エラー: {e}")
    
    def _send_test_email_smtp(self, server: smtplib.SMTP, email_address: str, config: Dict) -> str:
        """SMTPを使用してテストメールを送信"""
        try:
            # メール内容作成
            message = MIMEMultipart('alternative')
            message['To'] = email_address
            message['From'] = f"{config.get('sender_name', 'システム')} <{email_address}>"
            message['Subject'] = 'アニメ・マンガ通知システム - App Passwordテスト'
            
            # HTML本文
            html_body = """
            <html>
                <body>
                    <h2>🎉 App Password認証テスト成功！</h2>
                    <p>MangaAnime-Info-delivery-systemのSMTP認証が正常に動作しています。</p>
                    <ul>
                        <li>📧 認証方式: App Password (SMTP)</li>
                        <li>🕒 送信日時: {}</li>
                        <li>🔒 セキュリティ: 2段階認証 + App Password</li>
                        <li>⚡ システム状態: 正常</li>
                    </ul>
                    <p>システムの準備が完了しました！</p>
                </body>
            </html>
            """.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            message.attach(MIMEText(html_body, 'html'))
            
            # メール送信
            server.send_message(message)
            
            return "✅ テストメール送信成功 (SMTP)"
            
        except Exception as e:
            raise Exception(f"SMTPメール送信エラー: {e}")
    
    def run_comprehensive_test(self, send_emails: bool = False) -> Dict[str, Tuple[bool, str]]:
        """包括的な認証テストを実行"""
        print("🚀 Gmail認証の包括的テストを開始します...\n")
        
        results = {}
        
        # 1. 設定ファイルの検証
        print("📋 1. 認証設定ファイルの検証...")
        config_results = self.auth_config.validate_all_configs()
        results.update(config_results)
        
        # 2. OAuth2認証テスト
        print("\n🔐 2. OAuth2認証テスト...")
        oauth2_result = self.test_oauth2_auth(send_emails)
        results['oauth2_auth'] = oauth2_result
        print(f"   {oauth2_result[1]}")
        
        # 3. App Password認証テスト
        print("\n🔑 3. App Password認証テスト...")
        app_password_result = self.test_app_password_auth(send_emails)
        results['app_password_auth'] = app_password_result
        print(f"   {app_password_result[1]}")
        
        # 結果サマリー
        print("\n" + "="*50)
        print("📊 テスト結果サマリー:")
        
        success_count = sum(1 for is_success, _ in results.values() if is_success)
        total_count = len(results)
        
        for test_name, (is_success, message) in results.items():
            status = "✅" if is_success else "❌"
            print(f"  {status} {test_name}: {message.split('.')[0] if '.' in message else message}")
        
        print(f"\n🎯 成功率: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
        
        if success_count == total_count:
            print("🎉 全てのテストが成功しました！システムは正常に動作します。")
        else:
            print("⚠️ 一部のテストが失敗しました。上記のエラーを確認してください。")
        
        return results


def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(
        description="Gmail認証の統合テストスクリプト",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python test_gmail_auth.py                    # 基本的な認証テスト
  python test_gmail_auth.py --send-emails     # テストメール送信も実行
  python test_gmail_auth.py --oauth2-only     # OAuth2認証のみテスト
  python test_gmail_auth.py --smtp-only       # App Password認証のみテスト
        """
    )
    
    parser.add_argument('--send-emails', action='store_true',
                       help='実際にテストメールを送信する')
    parser.add_argument('--oauth2-only', action='store_true',
                       help='OAuth2認証のみテスト')
    parser.add_argument('--smtp-only', action='store_true',
                       help='App Password認証のみテスト')
    
    args = parser.parse_args()
    
    tester = GmailAuthTester()
    
    if args.oauth2_only:
        print("🔐 OAuth2認証テストを実行中...")
        is_success, message = tester.test_oauth2_auth(args.send_emails)
        status = "✅" if is_success else "❌"
        print(f"{status} {message}")
        return 0 if is_success else 1
    
    elif args.smtp_only:
        print("🔑 App Password認証テストを実行中...")
        is_success, message = tester.test_app_password_auth(args.send_emails)
        status = "✅" if is_success else "❌"
        print(f"{status} {message}")
        return 0 if is_success else 1
    
    else:
        # 包括的テスト実行
        results = tester.run_comprehensive_test(args.send_emails)
        
        # 全体的な成功判定
        all_success = all(is_success for is_success, _ in results.values())
        return 0 if all_success else 1


if __name__ == "__main__":
    sys.exit(main())