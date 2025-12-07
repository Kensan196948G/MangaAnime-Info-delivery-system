#!/usr/bin/env python3
"""
WebUI E2Eチェック（修正版）
実際のサーバーエラーのみ検出
"""
import requests

BASE_URL = "http://192.168.3.135:3030"

PAGES = [
    ('/', 'ダッシュボード'),
    ('/releases', 'リリース一覧'),
    ('/calendar', 'カレンダー'),
    ('/config', '設定'),
    ('/watchlist', 'ウォッチリスト'),
    ('/logs', 'ログ'),
    ('/users', 'ユーザー管理'),
    ('/api-keys', 'APIキー管理'),
    ('/admin/audit-logs', '監査ログ'),
    ('/api/stats', 'API統計'),
    ('/health', 'ヘルスチェック'),
]

print("=" * 60)
print("WebUI E2Eチェック")
print("=" * 60)
print()

success = 0
errors = []

for path, name in PAGES:
    url = BASE_URL + path
    try:
        r = requests.get(url, timeout=5)
        
        # 500エラーまたはTraceback検出のみエラー扱い
        if r.status_code == 500:
            errors.append(f"{name}: サーバーエラー（500）")
            print(f"❌ {name:25s} [500] サーバーエラー")
        elif 'Traceback' in r.text and 'werkzeug' in r.text:
            errors.append(f"{name}: Python例外検出")
            print(f"❌ {name:25s} [200] Python例外")
        elif r.status_code in [200, 302]:
            success += 1
            print(f"✅ {name:25s} [{r.status_code}] OK")
        else:
            print(f"⚠️  {name:25s} [{r.status_code}] 警告")
            
    except Exception as e:
        errors.append(f"{name}: {e}")
        print(f"❌ {name:25s} 接続エラー")

print()
print(f"成功: {success}/{len(PAGES)} ({success/len(PAGES)*100:.1f}%)")

if errors:
    print()
    print("検出されたエラー:")
    for e in errors:
        print(f"  - {e}")
else:
    print()
    print("✅ すべて正常")
