#!/usr/bin/env python3
"""
WebUI E2Eエラーチェックスクリプト
全ページにアクセスしてHTTPステータスとエラーを確認
"""
import sys
import requests
from typing import Dict, List, Tuple

BASE_URL = "http://192.168.3.135:3030"

# チェックするページ一覧
PAGES_TO_CHECK = [
    ('/', 'ダッシュボード'),
    ('/releases', 'リリース一覧'),
    ('/calendar', 'カレンダー'),
    ('/config', '設定'),
    ('/watchlist', 'ウォッチリスト'),
    ('/works', '作品一覧'),
    ('/logs', 'ログ'),
    ('/users', 'ユーザー管理'),
    ('/api-keys', 'APIキー管理'),
    ('/admin/audit-logs', '監査ログ'),
    ('/admin/dashboard', '管理者ダッシュボード'),
    ('/api/stats', 'API統計'),
    ('/api/sources', 'APIソース'),
    ('/health', 'ヘルスチェック'),
]

def check_page(url: str, name: str) -> Tuple[bool, str, int]:
    """
    ページをチェック
    Returns: (成功, メッセージ, ステータスコード)
    """
    try:
        response = requests.get(url, timeout=10)
        status_code = response.status_code
        
        if status_code == 200:
            # HTMLにエラーメッセージが含まれているかチェック
            content = response.text.lower()
            if 'error' in content or 'exception' in content or 'traceback' in content:
                return False, f"ページ内にエラーメッセージ検出", status_code
            return True, "OK", status_code
        elif status_code == 302 or status_code == 301:
            return True, f"リダイレクト", status_code
        elif status_code == 404:
            return False, "ページが見つかりません", status_code
        elif status_code == 500:
            return False, "サーバーエラー", status_code
        else:
            return False, f"予期しないステータス", status_code
            
    except requests.exceptions.ConnectionError:
        return False, "接続エラー（サーバー起動していない可能性）", 0
    except requests.exceptions.Timeout:
        return False, "タイムアウト", 0
    except Exception as e:
        return False, f"例外: {str(e)}", 0


def main():
    print("=" * 60)
    print("WebUI E2Eエラーチェック")
    print("=" * 60)
    print(f"ベースURL: {BASE_URL}")
    print()
    
    results = []
    success_count = 0
    error_count = 0
    
    for path, name in PAGES_TO_CHECK:
        url = BASE_URL + path
        success, message, status_code = check_page(url, name)
        
        results.append({
            'name': name,
            'path': path,
            'success': success,
            'message': message,
            'status_code': status_code
        })
        
        if success:
            success_count += 1
            print(f"✅ {name:20s} [{status_code}] {message}")
        else:
            error_count += 1
            print(f"❌ {name:20s} [{status_code}] {message}")
    
    print()
    print("=" * 60)
    print("テスト結果サマリー")
    print("=" * 60)
    print(f"総ページ数: {len(PAGES_TO_CHECK)}")
    print(f"成功: {success_count}")
    print(f"失敗: {error_count}")
    print(f"成功率: {success_count / len(PAGES_TO_CHECK) * 100:.1f}%")
    print()
    
    if error_count > 0:
        print("❌ エラーが検出されました")
        print()
        print("エラーページ:")
        for result in results:
            if not result['success']:
                print(f"  - {result['name']}: {result['path']}")
                print(f"    理由: {result['message']}")
        sys.exit(1)
    else:
        print("✅ すべてのページが正常に動作しています")
        sys.exit(0)


if __name__ == '__main__':
    main()
