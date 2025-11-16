#!/usr/bin/env python3
"""
Gmail接続とRSSフィード設定の検証スクリプト
"""

import os
import sys
import json
import logging
from datetime import datetime
from dotenv import load_dotenv

# プロジェクトルートをPythonパスに追加
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# .envファイル読み込み
load_dotenv()

def test_config_loading():
    """config.json読み込みテスト"""
    print("\n" + "="*60)
    print("📋 config.json 設定確認")
    print("="*60)
    
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Gmail設定確認
        gmail_config = config.get('google', {}).get('gmail', {})
        print(f"\n✅ Gmail設定:")
        print(f"  - from_email: {gmail_config.get('from_email', '未設定')}")
        print(f"  - to_email: {gmail_config.get('to_email', '未設定')}")
        print(f"  - subject_prefix: {gmail_config.get('subject_prefix', '未設定')}")
        
        # .env設定確認
        print(f"\n✅ .env設定:")
        print(f"  - GMAIL_SENDER_EMAIL: {os.getenv('GMAIL_SENDER_EMAIL', '未設定')}")
        print(f"  - GMAIL_RECIPIENT_EMAIL: {os.getenv('GMAIL_RECIPIENT_EMAIL', '未設定')}")
        print(f"  - GMAIL_APP_PASSWORD: {'設定済み' if os.getenv('GMAIL_APP_PASSWORD') else '未設定'}")
        
        # RSS設定確認
        rss_config = config.get('apis', {}).get('rss_feeds', {})
        feeds = rss_config.get('feeds', [])
        print(f"\n✅ RSSフィード設定: {len(feeds)}件")
        for feed in feeds:
            status = "有効" if feed.get('enabled', True) else "無効"
            print(f"  - {feed.get('name')}: {status}")
            print(f"    URL: {feed.get('url')}")
        
        return True, config
        
    except Exception as e:
        print(f"\n❌ 設定ファイル読み込みエラー: {e}")
        return False, None

def test_gmail_connection():
    """Gmail接続テスト"""
    print("\n" + "="*60)
    print("📧 Gmail接続テスト")
    print("="*60)
    
    try:
        from modules.config import ConfigManager
        from modules.mailer import GmailNotifier, EmailNotification
        
        # 設定マネージャー初期化
        config_manager = ConfigManager()
        config = config_manager.get_all()

        # Gmail通知器初期化
        notifier = GmailNotifier(config)
        
        # 認証テスト
        print("\n🔐 Gmail認証を試行中...")
        if notifier.authenticate():
            print("✅ Gmail認証成功!")
            
            # 認証状態の詳細表示
            auth_state = notifier.auth_state
            print(f"\n📊 認証状態:")
            print(f"  - 認証済み: {auth_state.is_authenticated}")
            print(f"  - 最終認証時刻: {auth_state.last_auth_time}")
            print(f"  - トークン有効期限: {auth_state.token_expires_at}")
            print(f"  - 連続認証失敗: {auth_state.consecutive_auth_failures}回")
            
            # パフォーマンス統計
            stats = notifier.get_performance_stats()
            print(f"\n📈 パフォーマンス統計:")
            print(f"  - 送信成功: {stats['total_emails_sent']}件")
            print(f"  - 送信失敗: {stats['total_send_failures']}件")
            print(f"  - 認証試行: {stats['total_auth_attempts']}回")
            print(f"  - 成功率: {stats['success_rate']*100:.1f}%")
            
            # テストメール送信確認
            response = input("\n📮 テストメールを送信しますか? (y/N): ")
            if response.lower() == 'y':
                test_notification = EmailNotification(
                    subject="[テスト] Gmail接続確認",
                    html_content=f"""
                    <html>
                    <body>
                        <h2>Gmail接続テスト成功</h2>
                        <p>このメールは、MangaAnime情報配信システムのGmail接続テストです。</p>
                        <p>送信時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    </body>
                    </html>
                    """,
                    text_content="Gmail接続テスト成功"
                )
                
                if notifier.send_notification(test_notification):
                    print("✅ テストメール送信成功!")
                else:
                    print("❌ テストメール送信失敗")
            
            return True
        else:
            print("❌ Gmail認証失敗")
            if notifier.auth_state.last_auth_error:
                print(f"   エラー: {notifier.auth_state.last_auth_error}")
            return False
            
    except ImportError as e:
        print(f"❌ モジュールインポートエラー: {e}")
        print("   必要なライブラリをインストールしてください:")
        print("   pip install google-auth google-auth-oauthlib google-api-python-client")
        return False
    except Exception as e:
        print(f"❌ Gmail接続テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_rss_feeds():
    """RSSフィード取得テスト"""
    print("\n" + "="*60)
    print("📡 RSSフィード取得テスト")
    print("="*60)
    
    try:
        import feedparser
        import requests

        # config.jsonから直接読み込み
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)

        rss_config = config.get('apis', {}).get('rss_feeds', {})
        feeds = rss_config.get('feeds', [])
        timeout = rss_config.get('timeout_seconds', 20)
        user_agent = rss_config.get('user_agent', 'MangaAnime-Info-delivery-system/1.0')
        
        success_count = 0
        total_count = len([f for f in feeds if f.get('enabled', True)])
        
        print(f"\n🔍 {total_count}件のRSSフィードをテスト中...\n")
        
        for feed in feeds:
            if not feed.get('enabled', True):
                continue
                
            name = feed.get('name', 'Unknown')
            url = feed.get('url', '')
            feed_type = feed.get('type', 'unknown')
            
            print(f"📰 {name} ({feed_type})")
            print(f"   URL: {url}")
            
            try:
                # HTTP headers設定
                headers = {
                    'User-Agent': user_agent,
                    'Accept': 'application/rss+xml, application/xml, text/xml'
                }
                
                # フィード取得
                response = requests.get(url, headers=headers, timeout=timeout)
                response.raise_for_status()
                
                # フィードパース
                parsed = feedparser.parse(response.content)
                
                if parsed.bozo:
                    print(f"   ⚠️  警告: フィードパースにエラーがあります")
                    if hasattr(parsed, 'bozo_exception'):
                        print(f"       {parsed.bozo_exception}")
                
                entries_count = len(parsed.entries)
                
                if entries_count > 0:
                    print(f"   ✅ 成功: {entries_count}件のエントリを取得")
                    
                    # 最新3件のタイトルを表示
                    print(f"   📝 最新エントリ (最大3件):")
                    for i, entry in enumerate(parsed.entries[:3], 1):
                        title = entry.get('title', 'タイトルなし')[:50]
                        published = entry.get('published', '日付不明')
                        print(f"      {i}. {title}... ({published})")
                    
                    success_count += 1
                else:
                    print(f"   ⚠️  警告: エントリが0件です")
                
            except requests.Timeout:
                print(f"   ❌ タイムアウト: {timeout}秒以内に応答がありませんでした")
            except requests.HTTPError as e:
                print(f"   ❌ HTTPエラー: {e.response.status_code} - {e}")
            except Exception as e:
                print(f"   ❌ エラー: {e}")
            
            print()  # 空行
        
        # 結果サマリー
        print("="*60)
        print(f"📊 テスト結果サマリー")
        print("="*60)
        print(f"成功: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
        
        if success_count == total_count:
            print("✅ すべてのRSSフィードが正常に取得できました!")
            return True
        elif success_count > 0:
            print(f"⚠️  一部のRSSフィードに問題があります")
            return False
        else:
            print("❌ すべてのRSSフィードが取得できませんでした")
            return False
            
    except ImportError as e:
        print(f"❌ モジュールインポートエラー: {e}")
        print("   必要なライブラリをインストールしてください:")
        print("   pip install feedparser requests")
        return False
    except Exception as e:
        print(f"❌ RSSフィードテストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """メイン処理"""
    print("\n" + "="*60)
    print("🔧 Gmail接続 & RSSフィード設定検証ツール")
    print("="*60)
    
    # 1. 設定ファイル確認
    config_ok, config = test_config_loading()
    if not config_ok:
        print("\n❌ 設定ファイルの読み込みに失敗しました")
        return 1
    
    # 2. Gmail接続テスト
    gmail_ok = test_gmail_connection()
    
    # 3. RSSフィードテスト
    rss_ok = test_rss_feeds()
    
    # 最終結果
    print("\n" + "="*60)
    print("🎯 総合結果")
    print("="*60)
    print(f"設定ファイル: {'✅ OK' if config_ok else '❌ NG'}")
    print(f"Gmail接続: {'✅ OK' if gmail_ok else '❌ NG'}")
    print(f"RSSフィード: {'✅ OK' if rss_ok else '❌ NG'}")
    
    if config_ok and gmail_ok and rss_ok:
        print("\n🎉 すべてのテストが成功しました!")
        return 0
    else:
        print("\n⚠️  一部のテストに失敗しました。上記のエラーを確認してください。")
        return 1

if __name__ == '__main__':
    sys.exit(main())
