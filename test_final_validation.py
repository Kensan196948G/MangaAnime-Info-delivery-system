#!/usr/bin/env python3
"""
最終検証スクリプト - Gmail (SMTP) & RSS
"""

import os
import sys
import json
from datetime import datetime

# プロジェクトルートをPythonパスに追加
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_config():
    """設定ファイルの検証"""
    print("\n" + "="*70)
    print("📋 STEP 1: 設定ファイル検証")
    print("="*70)
    
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    gmail_config = config.get('google', {}).get('gmail', {})
    print(f"✅ Gmail設定:")
    print(f"   from_email: {gmail_config.get('from_email')}")
    print(f"   to_email: {gmail_config.get('to_email')}")
    
    rss_feeds = config.get('apis', {}).get('rss_feeds', {}).get('feeds', [])
    enabled_feeds = [f for f in rss_feeds if f.get('enabled', True)]
    verified_feeds = [f for f in enabled_feeds if f.get('verified', False)]
    
    print(f"\n✅ RSSフィード設定:")
    print(f"   総数: {len(rss_feeds)}件")
    print(f"   有効: {len(enabled_feeds)}件")
    print(f"   検証済み: {len(verified_feeds)}件")
    
    for feed in enabled_feeds:
        status = "✓" if feed.get('verified') else "?"
        print(f"   {status} {feed.get('name')}")
    
    return True

def test_smtp_gmail():
    """SMTP Gmail接続テスト"""
    print("\n" + "="*70)
    print("📧 STEP 2: Gmail SMTP接続テスト")
    print("="*70)
    
    try:
        from modules.smtp_mailer import SMTPGmailSender
        
        sender = SMTPGmailSender()
        
        if not sender.validate_config():
            print("❌ Gmail設定エラー")
            return False
        
        print(f"✅ 設定OK")
        print(f"   送信元: {sender.sender_email}")
        print(f"   送信先: {sender.recipient_email}")
        
        # テストメール送信確認
        response = input("\n📮 テストメールを送信しますか? (Y/n): ")
        if response.lower() != 'n':
            print("   送信中...")
            if sender.send_test_email():
                print("✅ テストメール送信成功!")
                stats = sender.get_stats()
                print(f"   統計: {stats}")
                return True
            else:
                print("❌ テストメール送信失敗")
                return False
        else:
            print("   スキップしました")
            return True
            
    except ImportError as e:
        print(f"❌ モジュールインポートエラー: {e}")
        return False
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_rss_feeds():
    """RSSフィードテスト"""
    print("\n" + "="*70)
    print("📡 STEP 3: RSSフィード取得テスト")
    print("="*70)
    
    try:
        import feedparser
        import requests
        
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)

        rss_config = config.get('apis', {}).get('rss_feeds', {})
        feeds = rss_config.get('feeds', [])
        timeout = rss_config.get('timeout_seconds', 20)
        user_agent = rss_config.get('user_agent')
        
        enabled_feeds = [f for f in feeds if f.get('enabled', True)]
        success_count = 0
        
        for feed in enabled_feeds:
            name = feed.get('name')
            url = feed.get('url')
            verified = feed.get('verified', False)
            
            status_icon = "✓" if verified else "?"
            print(f"\n{status_icon} {name}")
            print(f"  URL: {url}")
            
            try:
                headers = {
                    'User-Agent': user_agent,
                    'Accept': 'application/rss+xml, application/xml, text/xml'
                }
                
                response = requests.get(url, headers=headers, timeout=timeout)
                response.raise_for_status()
                
                parsed = feedparser.parse(response.content)
                entries_count = len(parsed.entries)
                
                if entries_count > 0:
                    print(f"  ✅ 成功: {entries_count}件のエントリ")
                    
                    # 最新エントリのタイトル
                    if parsed.entries:
                        latest = parsed.entries[0].get('title', 'タイトルなし')[:50]
                        print(f"  📝 最新: {latest}...")
                    
                    success_count += 1
                else:
                    print(f"  ⚠️  エントリ0件")
                    
            except requests.Timeout:
                print(f"  ❌ タイムアウト")
            except requests.HTTPError as e:
                print(f"  ❌ HTTPエラー: {e.response.status_code}")
            except Exception as e:
                print(f"  ❌ エラー: {type(e).__name__}")
        
        print(f"\n📊 結果: {success_count}/{len(enabled_feeds)}件成功")
        
        return success_count > 0
        
    except Exception as e:
        print(f"❌ RSSテストエラー: {e}")
        return False

def main():
    """メイン処理"""
    print("\n" + "="*70)
    print("🔧 Gmail & RSSフィード 最終検証ツール")
    print(f"   実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    results = {}
    
    # 1. 設定ファイル検証
    results['config'] = test_config()
    
    # 2. Gmail SMTP接続テスト
    results['gmail'] = test_smtp_gmail()
    
    # 3. RSSフィード取得テスト
    results['rss'] = test_rss_feeds()
    
    # 最終結果
    print("\n" + "="*70)
    print("🎯 最終結果")
    print("="*70)
    print(f"設定ファイル: {'✅ OK' if results['config'] else '❌ NG'}")
    print(f"Gmail (SMTP): {'✅ OK' if results['gmail'] else '❌ NG'}")
    print(f"RSSフィード:  {'✅ OK' if results['rss'] else '❌ NG'}")
    
    all_ok = all(results.values())
    
    if all_ok:
        print("\n🎉 すべてのテストが成功しました!")
        print("\n📝 次のステップ:")
        print("   1. Gmail受信トレイを確認してテストメールを確認")
        print("   2. システムの本格運用を開始")
        return 0
    else:
        print("\n⚠️  一部のテストに失敗しました")
        print("   上記のエラーログを確認してください")
        return 1

if __name__ == '__main__':
    sys.exit(main())
