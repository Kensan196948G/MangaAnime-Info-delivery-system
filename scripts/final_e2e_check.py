#!/usr/bin/env python3
"""
最終E2Eチェック（厳格版）
"""
import requests

BASE_URL = "http://192.168.3.135:3030"

ENDPOINTS = [
    # HTML Pages
    ('/', 'ダッシュボード', 'html'),
    ('/releases', 'リリース一覧', 'html'),
    ('/calendar', 'カレンダー', 'html'),
    ('/config', '設定', 'html'),
    ('/watchlist', 'ウォッチリスト', 'html'),
    ('/logs', 'ログ', 'html'),
    ('/users', 'ユーザー管理', 'html'),
    ('/api-keys', 'APIキー管理', 'html'),
    ('/admin/audit-logs', '監査ログ', 'html'),
    ('/collection-dashboard', '収集ダッシュボード', 'html'),
    ('/data-browser', 'データブラウザ', 'html'),
    # APIs
    ('/api/stats', 'API統計', 'json'),
    ('/api/sources', 'データソース', 'json'),
    ('/health', 'ヘルスチェック', 'text'),
    ('/metrics', 'メトリクス', 'prometheus'),
]

print("=" * 60)
print("最終E2Eチェック")
print("=" * 60)
print()

success = 0
errors = []

for path, name, response_type in ENDPOINTS:
    url = BASE_URL + path
    try:
        r = requests.get(url, timeout=5)
        
        # Python例外チェック
        if 'Traceback (most recent call last)' in r.text:
            errors.append(f"{name}: Pythonエラー")
            print(f"❌ {name:25s} [500] Pythonエラー")
        elif r.status_code in [200, 302, 304]:
            success += 1
            print(f"✅ {name:25s} [{r.status_code}] OK")
        else:
            errors.append(f"{name}: HTTP {r.status_code}")
            print(f"❌ {name:25s} [{r.status_code}]")
    except Exception as e:
        errors.append(f"{name}: {e}")
        print(f"❌ {name:25s} 接続エラー")

print()
print(f"成功: {success}/{len(ENDPOINTS)} ({success/len(ENDPOINTS)*100:.1f}%)")

if errors:
    print()
    print("検出されたエラー:")
    for e in errors:
        print(f"  - {e}")
else:
    print()
    print("✅ すべて正常")
