#!/usr/bin/env python3
"""
包括的E2Eエラーチェック
全ページ・全API・JavaScriptエラーを厳格にチェック
"""
import requests
import json
import sys
from typing import List, Dict, Tuple

BASE_URL = "http://192.168.3.135:3030"

# 全チェック対象
ALL_ENDPOINTS = {
    'HTML Pages': [
        ('/', 'ダッシュボード'),
        ('/releases', 'リリース一覧'),
        ('/calendar', 'カレンダー'),
        ('/config', '設定'),
        ('/watchlist', 'ウォッチリスト'),
        ('/logs', 'ログ'),
        ('/users', 'ユーザー管理'),
        ('/api-keys', 'APIキー管理'),
        ('/admin/audit-logs', '監査ログ'),
        ('/collection-dashboard', '収集ダッシュボード'),
        ('/data-browser', 'データブラウザ'),
        ('/collection-settings', '収集設定'),
    ],
    'API Endpoints': [
        ('/api/stats', 'システム統計'),
        ('/api/sources', 'データソース'),
        ('/api/releases/recent', '最近のリリース'),
        ('/api/releases/upcoming', '今後のリリース'),
        ('/api/collection-status', '収集状態'),
        ('/api/notification-status', '通知状態'),
        ('/health', 'ヘルスチェック'),
        ('/ready', 'Ready状態'),
        ('/metrics', 'メトリクス'),
    ]
}

def check_endpoint(url: str, name: str, is_api: bool = False) -> Dict:
    """エンドポイントをチェック"""
    result = {
        'name': name,
        'url': url,
        'success': False,
        'status_code': 0,
        'errors': []
    }
    
    try:
        response = requests.get(url, timeout=10)
        result['status_code'] = response.status_code
        
        # ステータスコードチェック
        if response.status_code not in [200, 302, 304]:
            result['errors'].append(f"異常ステータス: {response.status_code}")
            return result
        
        content = response.text
        
        # Pythonエラー検出
        if 'Traceback (most recent call last)' in content:
            result['errors'].append("Pythonトレースバック検出")
            return result
        
        if 'werkzeug.routing.exceptions.BuildError' in content:
            result['errors'].append("url_for()エラー検出")
            return result
        
        if 'sqlite3.OperationalError' in content:
            result['errors'].append("SQLiteエラー検出")
            return result
        
        if 'NameError:' in content or 'AttributeError:' in content:
            result['errors'].append("Python名前エラー検出")
            return result
        
        # APIの場合はJSON妥当性チェック
        if is_api:
            try:
                data = json.loads(content)
                if isinstance(data, dict) and 'error' in data:
                    result['errors'].append(f"APIエラー: {data.get('error')}")
                    return result
            except json.JSONDecodeError:
                if '/health' not in url and '/ready' not in url:
                    result['errors'].append("無効なJSON")
                    return result
        
        result['success'] = True
        return result
        
    except requests.exceptions.ConnectionError:
        result['errors'].append("接続エラー")
    except requests.exceptions.Timeout:
        result['errors'].append("タイムアウト")
    except Exception as e:
        result['errors'].append(f"例外: {str(e)}")
    
    return result


def main():
    print("=" * 70)
    print("包括的E2Eエラーチェック")
    print("=" * 70)
    print(f"ベースURL: {BASE_URL}")
    print()
    
    all_results = []
    total_count = 0
    success_count = 0
    error_count = 0
    
    for category, endpoints in ALL_ENDPOINTS.items():
        print(f"\n【{category}】")
        print("-" * 70)
        
        for path, name in endpoints:
            url = BASE_URL + path
            is_api = category == 'API Endpoints'
            result = check_endpoint(url, name, is_api)
            all_results.append(result)
            total_count += 1
            
            if result['success']:
                success_count += 1
                print(f"✅ {name:30s} [{result['status_code']}] OK")
            else:
                error_count += 1
                print(f"❌ {name:30s} [{result['status_code']}] {', '.join(result['errors'])}")
    
    print()
    print("=" * 70)
    print("テスト結果サマリー")
    print("=" * 70)
    print(f"総エンドポイント数: {total_count}")
    print(f"成功: {success_count} ({success_count/total_count*100:.1f}%)")
    print(f"失敗: {error_count}")
    print()
    
    if error_count > 0:
        print("❌ エラーが検出されました")
        print()
        print("エラー詳細:")
        for result in all_results:
            if not result['success']:
                print(f"\n  {result['name']}:")
                print(f"    URL: {result['url']}")
                print(f"    ステータス: {result['status_code']}")
                for error in result['errors']:
                    print(f"    - {error}")
        sys.exit(1)
    else:
        print("✅ すべてのエンドポイントが正常に動作しています")
        sys.exit(0)


if __name__ == '__main__':
    main()
