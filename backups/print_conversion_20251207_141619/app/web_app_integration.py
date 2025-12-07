#!/usr/bin/env python3
"""
認証機構統合スクリプト
web_app.py に認証Blueprintを統合します
"""

import re
import os

def integrate_auth_to_web_app():
    """web_app.py に認証機構を統合"""

    web_app_path = '/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/app/web_app.py'

    # ファイルを読み込み
    with open(web_app_path, 'r', encoding='utf-8') as f:
        content = f.read()

    print("現在のweb_app.pyの構造を分析中...")

    # 1. インポート部分の確認
    import_section = content[:content.find('app = Flask(__name__)')]
    print(f"インポートセクション: {len(import_section)} 文字")

    # 2. login_required が既にインポートされているか確認
    has_login_required = 'from flask_login import' in content
    print(f"flask_login インポート済み: {has_login_required}")

    # 3. auth_bp が登録されているか確認
    has_auth_bp = 'auth_bp' in content
    print(f"auth_bp 登録済み: {has_auth_bp}")

    # 4. ルート関数を検索
    route_pattern = r'@app\.route\([\'"]([^\'"]+)[\'"]\s*(?:,\s*methods\s*=\s*\[[^\]]+\])?\)\s*\ndef\s+(\w+)\('
    routes = re.findall(route_pattern, content)
    print(f"\n検出されたルート数: {len(routes)}")
    for path, func_name in routes[:10]:
        print(f"  {func_name}: {path}")

    # 5. 設定変更・削除系のルートを特定
    protected_routes = []
    for path, func_name in routes:
        if any(keyword in func_name.lower() for keyword in ['settings', 'delete', 'update', 'config', 'remove', 'clear']):
            if not any(api_keyword in path for api_keyword in ['/api/', '/health', '/status']):
                protected_routes.append((path, func_name))

    print(f"\n保護が必要なルート候補: {len(protected_routes)}")
    for path, func_name in protected_routes:
        print(f"  {func_name}: {path}")

    return {
        'has_login_required': has_login_required,
        'has_auth_bp': has_auth_bp,
        'routes': routes,
        'protected_routes': protected_routes
    }

if __name__ == '__main__':
    result = integrate_auth_to_web_app()
    print("\n=== 統合準備完了 ===")
    print(f"Total routes: {len(result['routes'])}")
    print(f"Protected routes needed: {len(result['protected_routes'])}")
