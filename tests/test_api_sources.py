#!/usr/bin/env python3
"""
API Sources Testing Script
Tests all the new API endpoints for source testing and configuration
"""

from app.web_app import app
import json
import sys


def print_section(title):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def test_get_sources():
    """Test GET /api/sources"""
    print_section("GET /api/sources - すべてのソース一覧")
    
    with app.test_client() as client:
        response = client.get('/api/sources')
        data = json.loads(response.data)
        
        print(f"Status: {response.status_code}")
        print(f"\n【API】")
        for api in data.get('apis', []):
            status = "✓" if api['enabled'] else "✗"
            print(f"  {status} {api['name']}: {api['url']}")
            print(f"     Rate Limit: {api.get("rate_limit", "N/A")}/min | Timeout: {api.get("timeout", "N/A")}s")
        
        print(f"\n【RSS Feeds】")
        for feed in data.get('rss_feeds', []):
            status = "✓" if feed['enabled'] else "✗"
            verified = "✓" if feed.get('verified') else "?"
            print(f"  {status} {feed['name']} (verified: {verified})")
            print(f"     URL: {feed['url']}")
        
        summary = data.get('summary', {})
        print(f"\n【サマリー】")
        print(f"  Total: {summary['total_sources']}")
        print(f"  Enabled: {summary['enabled_sources']}")
        print(f"  Disabled: {summary['disabled_sources']}")
        
        return response.status_code == 200


def test_anilist():
    """Test POST /api/sources/anilist/test"""
    print_section("POST /api/sources/anilist/test - AniList接続テスト")
    
    with app.test_client() as client:
        response = client.post('/api/sources/anilist/test')
        data = json.loads(response.data)
        
        print(f"Status: {response.status_code}")
        print(f"Overall Status: {data.get('overall_status')}")
        print(f"Success Rate: {data.get('success_rate')}")
        print(f"Total Time: {data.get('total_time_ms')}ms")
        
        print(f"\n【テスト結果】")
        for test in data.get('tests', []):
            status_icon = {"success": "✓", "failed": "✗", "error": "✗", "info": "ℹ", "warning": "⚠"}.get(test['status'], "?")
            print(f"  {status_icon} {test['name']}")
            print(f"     Status: {test['status']}")
            if 'response_time_ms' in test:
                print(f"     Response Time: {test['response_time_ms']}ms")
            if 'details' in test:
                print(f"     Details: {test['details']}")
            if 'error' in test:
                print(f"     Error: {test['error']}")
        
        return data.get('overall_status') == 'success'


def test_syoboi():
    """Test POST /api/sources/syoboi/test"""
    print_section("POST /api/sources/syoboi/test - しょぼいカレンダーテスト")
    
    with app.test_client() as client:
        response = client.post('/api/sources/syoboi/test')
        data = json.loads(response.data)
        
        print(f"Status: {response.status_code}")
        print(f"Overall Status: {data.get('overall_status')}")
        print(f"Success Rate: {data.get('success_rate')}")
        print(f"Total Time: {data.get('total_time_ms')}ms")
        
        print(f"\n【テスト結果】")
        for test in data.get('tests', []):
            status_icon = {"success": "✓", "failed": "✗", "error": "✗", "info": "ℹ", "warning": "⚠"}.get(test['status'], "?")
            print(f"  {status_icon} {test['name']}")
            print(f"     Status: {test['status']}")
            if 'response_time_ms' in test:
                print(f"     Response Time: {test['response_time_ms']}ms")
            if 'details' in test:
                print(f"     Details: {test['details']}")
        
        return data.get('overall_status') == 'success'


def test_rss_feed():
    """Test POST /api/sources/rss/test"""
    print_section("POST /api/sources/rss/test - RSSフィードテスト")
    
    with app.test_client() as client:
        # Test with Shonen Jump+
        feed_id = '少年ジャンプ＋'.lower().replace(' ', '_').replace('＋', 'plus')
        response = client.post('/api/sources/rss/test', json={'feed_id': feed_id})
        data = json.loads(response.data)
        
        print(f"Feed: {data.get('source')}")
        print(f"URL: {data.get('url')}")
        print(f"Status: {response.status_code}")
        print(f"Overall Status: {data.get('overall_status')}")
        print(f"Success Rate: {data.get('success_rate')}")
        print(f"Total Time: {data.get('total_time_ms')}ms")
        
        print(f"\n【テスト結果】")
        for test in data.get('tests', []):
            status_icon = {"success": "✓", "failed": "✗", "error": "✗", "info": "ℹ", "warning": "⚠"}.get(test['status'], "?")
            print(f"  {status_icon} {test['name']}")
            print(f"     Status: {test['status']}")
            if 'response_time_ms' in test:
                print(f"     Response Time: {test['response_time_ms']}ms")
            if 'entries_count' in test:
                print(f"     Entries: {test['entries_count']}件")
            if 'details' in test:
                print(f"     Details: {test['details']}")
        
        if 'sample_entry' in data:
            print(f"\n【サンプルエントリー】")
            print(f"  Title: {data['sample_entry'].get('title')}")
            print(f"  Link: {data['sample_entry'].get('link')}")
            print(f"  Published: {data['sample_entry'].get('published')}")
        
        return data.get('overall_status') == 'success'


def test_toggle_source():
    """Test POST /api/sources/toggle"""
    print_section("POST /api/sources/toggle - ソース有効/無効切り替え")
    
    with app.test_client() as client:
        # Test disable
        print("【しょぼいカレンダーを無効化】")
        response = client.post('/api/sources/toggle', 
                              json={'source_type': 'syoboi', 'enabled': False})
        data = json.loads(response.data)
        print(f"  Status: {response.status_code}")
        print(f"  Success: {data.get('success')}")
        print(f"  Message: {data.get('message')}")
        
        # Test enable
        print("\n【しょぼいカレンダーを有効化】")
        response = client.post('/api/sources/toggle', 
                              json={'source_type': 'syoboi', 'enabled': True})
        data = json.loads(response.data)
        print(f"  Status: {response.status_code}")
        print(f"  Success: {data.get('success')}")
        print(f"  Message: {data.get('message')}")
        
        # Test RSS toggle
        print("\n【RSSフィード(となりのヤングジャンプ)を有効化】")
        response = client.post('/api/sources/toggle', 
                              json={'source_type': 'rss_feed', 
                                    'source_id': 'となりのヤングジャンプ'.lower().replace(' ', '_'),
                                    'enabled': True})
        data = json.loads(response.data)
        print(f"  Status: {response.status_code}")
        print(f"  Success: {data.get('success')}")
        print(f"  Message: {data.get('message')}")
        
        return True


def main():
    """Run all tests"""
    print("="*60)
    print("  API Sources Testing - すべてのエンドポイントテスト")
    print("="*60)
    
    tests = [
        ("ソース一覧取得", test_get_sources),
        ("AniListテスト", test_anilist),
        ("しょぼいカレンダーテスト", test_syoboi),
        ("RSSフィードテスト", test_rss_feed),
        ("ソース切り替えテスト", test_toggle_source),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n✗ エラー: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Print summary
    print_section("テスト結果サマリー")
    passed = 0
    for name, success in results:
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"  {status}: {name}")
        if success:
            passed += 1
    
    print(f"\n{passed}/{len(results)} tests passed")
    
    return 0 if passed == len(results) else 1


if __name__ == '__main__':
    sys.exit(main())
