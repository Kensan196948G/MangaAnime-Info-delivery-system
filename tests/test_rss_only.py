#!/usr/bin/env python3
"""RSSフィード接続テスト"""

import json
import feedparser
import requests
from datetime import datetime

def test_rss_feeds():
    """RSSフィード取得テスト"""
    print("\n" + "="*60)
    print("📡 RSSフィード取得テスト")
    print("="*60)
    
    # config.jsonから読み込み
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
        description = feed.get('description', '')
        
        print(f"📰 {name} ({feed_type})")
        print(f"   {description}")
        print(f"   URL: {url}")
        
        try:
            # HTTP headers設定
            headers = {
                'User-Agent': user_agent,
                'Accept': 'application/rss+xml, application/xml, text/xml, application/atom+xml'
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
                    title = entry.get('title', 'タイトルなし')[:60]
                    published = entry.get('published', entry.get('updated', '日付不明'))
                    print(f"      {i}. {title}...")
                    print(f"         ({published})")
                
                success_count += 1
            else:
                print(f"   ⚠️  警告: エントリが0件です")
            
        except requests.Timeout:
            print(f"   ❌ タイムアウト: {timeout}秒以内に応答がありませんでした")
        except requests.HTTPError as e:
            print(f"   ❌ HTTPエラー: {e.response.status_code}")
            print(f"       {e}")
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
        print(f"⚠️  一部のRSSフィードに問題があります ({total_count - success_count}件失敗)")
        return True  # 1件でも成功していればOK
    else:
        print("❌ すべてのRSSフィードが取得できませんでした")
        return False

if __name__ == '__main__':
    test_rss_feeds()
