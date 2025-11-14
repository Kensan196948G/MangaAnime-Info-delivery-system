#!/usr/bin/env python3
"""
メール配信機能のテストスクリプト
Gmail送信機能が正しく動作するか確認します
"""

import sys
import os
from pathlib import Path

# プロジェクトのルートディレクトリをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from modules.config import ConfigManager
from modules.mailer import GmailNotifier, EmailTemplateGenerator
from modules.db import DatabaseManager
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_email_configuration():
    """メール設定の確認"""
    print("=" * 60)
    print("📧 メール配信機能テスト")
    print("=" * 60)
    
    # 設定読み込み
    config = ConfigManager()
    
    print("\n1️⃣ 設定確認:")
    print(f"  SMTP Server: {config.get_value('notification.email.smtp_server')}")
    print(f"  Port: {config.get_value('notification.email.smtp_port')}")
    print(f"  Sender: {config.get_value('notification.email.sender')}")
    print(f"  Recipients: {config.get_value('notification.email.recipients')}")
    print(f"  Auth Type: {config.get_value('notification.email.auth_type')}")
    
    # App Passwordファイル確認
    app_password_file = config.get_value('notification.email.app_password_file', 'gmail_app_password.txt')
    if os.path.exists(app_password_file):
        print(f"  ✅ App Password File: {app_password_file} (存在)")
        with open(app_password_file, 'r') as f:
            password = f.read().strip()
            if password:
                print(f"  ✅ App Password: 設定済み (長さ: {len(password)}文字)")
            else:
                print("  ❌ App Password: ファイルが空です")
                return False
    else:
        print(f"  ❌ App Password File: {app_password_file} (存在しない)")
        print("\n⚠️  Gmail App Passwordの設定が必要です:")
        print("  1. Googleアカウントで2段階認証を有効化")
        print("  2. https://myaccount.google.com/apppasswords でアプリパスワードを生成")
        print(f"  3. 生成されたパスワードを {app_password_file} に保存")
        print(f"     echo 'your-app-password' > {app_password_file}")
        print(f"     chmod 600 {app_password_file}")
        return False
    
    return True

def test_email_sending():
    """実際のメール送信テスト"""
    config = ConfigManager()
    
    print("\n2️⃣ メール送信テスト:")
    
    # GmailNotifierの初期化
    try:
        mailer = GmailNotifier(config)
        print("  ✅ GmailNotifier初期化成功")
    except Exception as e:
        print(f"  ❌ GmailNotifier初期化失敗: {e}")
        return False
    
    # 認証テスト
    try:
        if mailer.authenticate():
            print("  ✅ Gmail認証成功")
        else:
            print("  ❌ Gmail認証失敗")
            return False
    except Exception as e:
        print(f"  ❌ 認証エラー: {e}")
        return False
    
    # テストメール送信
    try:
        # テストデータ作成
        test_releases = [
            {
                'title': 'テスト作品',
                'number': '第1話',
                'platform': 'テストプラットフォーム',
                'release_date': '2025-09-03',
                'url': 'https://example.com'
            }
        ]
        
        # メールテンプレート生成
        template_gen = EmailTemplateGenerator(config)
        notification = template_gen.generate_release_notification(
            test_releases,
            subject_prefix="[テスト] "
        )
        
        print(f"  送信先: {notification['to']}")
        print(f"  件名: {notification['subject']}")
        
        # 実際の送信
        if mailer.send_notification(notification):
            print("  ✅ テストメール送信成功！")
            print("  メールボックスを確認してください。")
            return True
        else:
            print("  ❌ テストメール送信失敗")
            return False
            
    except Exception as e:
        print(f"  ❌ 送信エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """メインテスト実行"""
    # 設定確認
    if not test_email_configuration():
        print("\n❌ メール設定が不完全です。上記の指示に従って設定してください。")
        sys.exit(1)
    
    # 送信テスト
    print("\n📮 実際にテストメールを送信しますか？ (y/n): ", end="")
    if input().lower() == 'y':
        if test_email_sending():
            print("\n✅ メール配信機能は正常に動作しています！")
        else:
            print("\n❌ メール送信に問題があります。設定を確認してください。")
            sys.exit(1)
    else:
        print("\nテストをスキップしました。")
    
    print("\n" + "=" * 60)
    print("テスト完了")
    print("=" * 60)

if __name__ == "__main__":
    main()