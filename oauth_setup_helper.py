#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
OAuth2認証セットアップヘルパー
自動的にOAuth2トークンを生成し、認証状態を検証します。
"""

import os
import json
import sys
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import logging

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 必要なスコープ
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/calendar.events'
]

class OAuthSetupHelper:
    """OAuth2認証セットアップヘルパークラス"""
    
    def __init__(self):
        self.base_dir = Path('.')
        self.token_file = self.base_dir / 'token.json'
        self.credentials_file = self.base_dir / 'credentials.json'
        
    def check_prerequisites(self) -> bool:
        """前提条件をチェック"""
        if not self.credentials_file.exists():
            logger.error("❌ credentials.json が見つかりません")
            logger.info("💡 Google Cloud Consoleから認証情報をダウンロードしてください:")
            logger.info("   https://console.cloud.google.com/apis/credentials")
            return False
            
        # パーミッションチェック
        try:
            os.chmod(self.credentials_file, 0o600)
            logger.info("✅ credentials.json のパーミッションを600に設定しました")
        except Exception as e:
            logger.warning(f"⚠️ パーミッション設定エラー: {e}")
            
        return True
    
    def convert_web_to_installed(self):
        """Web認証情報をInstalled Appタイプに変換"""
        try:
            with open(self.credentials_file, 'r') as f:
                creds_data = json.load(f)
            
            if 'web' in creds_data:
                logger.info("🔄 Web認証情報をInstalled Appタイプに変換中...")
                
                # Webタイプから必要な情報を抽出
                web_creds = creds_data['web']
                
                # Installed Appタイプとして再構成
                installed_creds = {
                    'installed': {
                        'client_id': web_creds['client_id'],
                        'project_id': web_creds['project_id'],
                        'auth_uri': web_creds['auth_uri'],
                        'token_uri': web_creds['token_uri'],
                        'auth_provider_x509_cert_url': web_creds['auth_provider_x509_cert_url'],
                        'client_secret': web_creds['client_secret'],
                        'redirect_uris': ['http://localhost']
                    }
                }
                
                # バックアップを作成
                backup_file = self.credentials_file.with_suffix('.json.backup')
                with open(backup_file, 'w') as f:
                    json.dump(creds_data, f, indent=2)
                logger.info(f"📁 元のファイルをバックアップ: {backup_file}")
                
                # 変換後のファイルを保存
                with open(self.credentials_file, 'w') as f:
                    json.dump(installed_creds, f, indent=2)
                logger.info("✅ credentials.json を Installed App タイプに変換しました")
                
                # パーミッション設定
                os.chmod(self.credentials_file, 0o600)
                
                return True
            
            elif 'installed' in creds_data:
                logger.info("✅ credentials.json は既に Installed App タイプです")
                return True
            
            else:
                logger.error("❌ 未知の認証情報タイプです")
                return False
                
        except Exception as e:
            logger.error(f"❌ 変換エラー: {e}")
            return False
    
    def generate_token(self) -> bool:
        """OAuth2トークンを生成"""
        try:
            creds = None
            
            # 既存のトークンをチェック
            if self.token_file.exists():
                try:
                    creds = Credentials.from_authorized_user_file(str(self.token_file), SCOPES)
                    logger.info("📄 既存のトークンファイルを読み込みました")
                except Exception as e:
                    logger.warning(f"⚠️ 既存トークンの読み込みエラー: {e}")
                    creds = None
            
            # トークンが無効または存在しない場合
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    logger.info("🔄 トークンを更新中...")
                    creds.refresh(Request())
                else:
                    logger.info("🌐 新規認証フローを開始します...")
                    logger.info("📌 ブラウザが開きます。Googleアカウントでログインして認証を許可してください。")
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.credentials_file), SCOPES
                    )
                    
                    # ローカルサーバーで認証（複数ポートを試行）
                    ports = [8080, 8090, 9090, 0]
                    for port in ports:
                        try:
                            creds = flow.run_local_server(port=port)
                            break
                        except Exception as e:
                            if port == 0:  # 最後の試行
                                raise e
                            logger.warning(f"ポート {port} が使用できません。別のポートを試行...")
                
                # トークンを保存
                with open(self.token_file, 'w') as token:
                    token.write(creds.to_json())
                
                # パーミッション設定
                os.chmod(self.token_file, 0o600)
                logger.info(f"✅ トークンを保存しました: {self.token_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ トークン生成エラー: {e}")
            return False
    
    def verify_authentication(self) -> bool:
        """認証が正常に機能することを確認"""
        try:
            if not self.token_file.exists():
                logger.error("❌ token.json が存在しません")
                return False
            
            # トークンを読み込み
            creds = Credentials.from_authorized_user_file(str(self.token_file), SCOPES)
            
            # Gmail APIに接続テスト
            logger.info("📧 Gmail API接続テスト中...")
            gmail_service = build('gmail', 'v1', credentials=creds)
            profile = gmail_service.users().getProfile(userId='me').execute()
            logger.info(f"✅ Gmail API接続成功: {profile.get('emailAddress')}")
            
            # Calendar APIに接続テスト
            logger.info("📅 Calendar API接続テスト中...")
            calendar_service = build('calendar', 'v3', credentials=creds)
            calendar_list = calendar_service.calendarList().list(maxResults=1).execute()
            logger.info(f"✅ Calendar API接続成功: {len(calendar_list.get('items', []))} カレンダー")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 認証検証エラー: {e}")
            return False
    
    def run_setup(self):
        """完全なセットアップを実行"""
        logger.info("=" * 60)
        logger.info("🚀 OAuth2認証セットアップを開始します")
        logger.info("=" * 60)
        
        # 1. 前提条件チェック
        if not self.check_prerequisites():
            return False
        
        # 2. 認証情報の変換（必要な場合）
        if not self.convert_web_to_installed():
            return False
        
        # 3. トークン生成
        if not self.generate_token():
            return False
        
        # 4. 認証検証
        if not self.verify_authentication():
            return False
        
        logger.info("=" * 60)
        logger.info("🎉 OAuth2認証セットアップが完了しました！")
        logger.info("✅ Gmail APIとGoogle Calendar APIが使用可能です")
        logger.info("=" * 60)
        
        return True

def main():
    """メイン処理"""
    helper = OAuthSetupHelper()
    
    if helper.run_setup():
        sys.exit(0)
    else:
        logger.error("セットアップに失敗しました。上記のエラーメッセージを確認してください。")
        sys.exit(1)

if __name__ == "__main__":
    main()