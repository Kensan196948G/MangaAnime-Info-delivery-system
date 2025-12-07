#!/usr/bin/env python3
"""
認証機構統合の実装スクリプト
web_app.py に段階的に認証を統合します
"""
import os
import re
import shutil
from datetime import datetime

BASE_DIR = '/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system'
WEB_APP_PATH = os.path.join(BASE_DIR, 'app/web_app.py')
AUTH_PATH = os.path.join(BASE_DIR, 'app/routes/auth.py')
ROUTES_INIT_PATH = os.path.join(BASE_DIR, 'app/routes/__init__.py')
BASE_TEMPLATE_PATH = os.path.join(BASE_DIR, 'templates/base.html')

def backup_file(filepath):
    """ファイルをバックアップ"""
    backup_path = f"{filepath}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(filepath, backup_path)
    print(f"✓ Backup created: {backup_path}")
    return backup_path

def read_file(filepath):
    """ファイルを読み込み"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(filepath, content):
    """ファイルに書き込み"""
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✓ Updated: {filepath}")

def integrate_step1_imports(web_app_content):
    """Step 1: flask_login のインポート追加"""
    print("\n[Step 1] Adding flask_login imports...")

    # 既にインポートされているか確認
    if 'from flask_login import' in web_app_content:
        print("  ℹ flask_login already imported")
        return web_app_content

    # Flask のインポート行を探して、その直後に追加
    flask_import_pattern = r'(from flask import [^\n]+)'
    match = re.search(flask_import_pattern, web_app_content)

    if match:
        flask_import = match.group(1)
        # Flask インポートに login_required, current_user を追加
        new_import = flask_import.replace(
            'from flask import',
            'from flask import'
        )
        if 'login_required' not in new_import:
            # 既存のインポートの後に追加
            replacement = f"{flask_import}\nfrom flask_login import login_required, current_user"
            web_app_content = web_app_content.replace(flask_import, replacement)
            print("  ✓ Added: from flask_login import login_required, current_user")

    return web_app_content

def integrate_step2_app_config(web_app_content):
    """Step 2: app.config['SECRET_KEY'] と Blueprint登録"""
    print("\n[Step 2] Adding app configuration and Blueprint registration...")

    # app = Flask(__name__) の直後に設定を追加
    app_creation_pattern = r"(app = Flask\(__name__\))"

    if "app.config['SECRET_KEY']" in web_app_content:
        print("  ℹ SECRET_KEY already configured")
    else:
        replacement = """app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')"""
        web_app_content = re.sub(app_creation_pattern, replacement, web_app_content)
        print("  ✓ Added: app.config['SECRET_KEY']")

    # Blueprint登録（ファイルの適切な場所に挿入）
    if 'from app.routes.auth import auth_bp, init_login_manager' not in web_app_content:
        # インポートセクションの最後に追加
        last_import_pattern = r'(import sqlite3\n)'
        replacement = r'\1from app.routes.auth import auth_bp, init_login_manager\n'
        web_app_content = re.sub(last_import_pattern, replacement, web_app_content)
        print("  ✓ Added: from app.routes.auth import auth_bp, init_login_manager")

    # init_login_manager と Blueprint登録を app 作成直後に追加
    if 'init_login_manager(app)' not in web_app_content:
        app_config_pattern = r"(app\.config\['SECRET_KEY'\][^\n]+\n)"
        replacement = r"\1\n# Initialize login manager\ninit_login_manager(app)\n\n# Register authentication blueprint\napp.register_blueprint(auth_bp, url_prefix='/auth')\n"
        web_app_content = re.sub(app_config_pattern, replacement, web_app_content)
        print("  ✓ Added: init_login_manager(app) and auth_bp registration")

    return web_app_content

def integrate_step3_protected_routes(web_app_content):
    """Step 3: 保護が必要なルートに @login_required を追加"""
    print("\n[Step 3] Adding @login_required to protected routes...")

    # 保護が必要なルートのパターン
    protected_patterns = [
        (r"(@app\.route\('/settings'[^\)]*\)\n)(def settings\(\):)", r"\1@login_required\n\2"),
        (r"(@app\.route\('/api/settings/update'[^\)]*\)\n)(def update_settings\(\):)", r"\1@login_required\n\2"),
        (r"(@app\.route\('/api/clear-history'[^\)]*\)\n)(def clear_history\(\):)", r"\1@login_required\n\2"),
        (r"(@app\.route\('/api/delete-work/<int:work_id>'[^\)]*\)\n)(def delete_work\([^\)]*\):)", r"\1@login_required\n\2"),
    ]

    count = 0
    for pattern, replacement in protected_patterns:
        if re.search(pattern, web_app_content):
            # @login_required が既にあるかチェック
            route_match = re.search(pattern, web_app_content)
            if route_match:
                route_section = web_app_content[max(0, route_match.start()-100):route_match.end()+50]
                if '@login_required' not in route_section:
                    web_app_content = re.sub(pattern, replacement, web_app_content)
                    count += 1
                    print(f"  ✓ Protected route: {route_match.group(2)}")

    print(f"  Total protected routes: {count}")
    return web_app_content

def integrate_step4_routes_init():
    """Step 4: app/routes/__init__.py を更新"""
    print("\n[Step 4] Updating app/routes/__init__.py...")

    if not os.path.exists(ROUTES_INIT_PATH):
        # ファイルが存在しない場合は作成
        content = """\"\"\"
Routes package
Contains all route blueprints
\"\"\"
from app.routes.auth import auth_bp, init_login_manager

__all__ = ['auth_bp', 'init_login_manager']
"""
        os.makedirs(os.path.dirname(ROUTES_INIT_PATH), exist_ok=True)
        write_file(ROUTES_INIT_PATH, content)
        return

    content = read_file(ROUTES_INIT_PATH)

    if 'from app.routes.auth import' in content:
        print("  ℹ auth already exported in __init__.py")
        return

    # 既存の内容に追加
    new_content = content.rstrip() + '\n\nfrom app.routes.auth import auth_bp, init_login_manager\n'

    # __all__ を更新
    if '__all__' in new_content:
        new_content = re.sub(
            r"__all__ = \[(.*?)\]",
            r"__all__ = [\1, 'auth_bp', 'init_login_manager']",
            new_content
        )
    else:
        new_content += "\n__all__ = ['auth_bp', 'init_login_manager']\n"

    write_file(ROUTES_INIT_PATH, new_content)

def integrate_step5_base_template():
    """Step 5: templates/base.html にログイン状態表示を追加"""
    print("\n[Step 5] Updating templates/base.html...")

    if not os.path.exists(BASE_TEMPLATE_PATH):
        print("  ⚠ base.html not found, skipping")
        return

    backup_file(BASE_TEMPLATE_PATH)
    content = read_file(BASE_TEMPLATE_PATH)

    if 'current_user.is_authenticated' in content:
        print("  ℹ Login status already in template")
        return

    # ナビゲーションバーを探して、ログイン状態表示を追加
    # <nav> セクションの終わりに追加
    nav_pattern = r'(</ul>\s*</nav>)'

    login_status_html = """        <!-- ログイン状態表示 -->
        <ul class="navbar-nav ms-auto">
          {% if current_user.is_authenticated %}
            <li class="nav-item dropdown">
              <a class="nav-link dropdown-toggle" href="#" id="navbarDropdown" role="button" data-bs-toggle="dropdown" aria-expanded="false">
                <i class="bi bi-person-circle"></i> {{ current_user.username }}
              </a>
              <ul class="dropdown-menu dropdown-menu-end" aria-labelledby="navbarDropdown">
                <li><a class="dropdown-item" href="{{ url_for('auth.profile') }}"><i class="bi bi-person"></i> プロフィール</a></li>
                <li><hr class="dropdown-divider"></li>
                <li><a class="dropdown-item" href="{{ url_for('auth.logout') }}"><i class="bi bi-box-arrow-right"></i> ログアウト</a></li>
              </ul>
            </li>
          {% else %}
            <li class="nav-item">
              <a class="nav-link" href="{{ url_for('auth.login') }}"><i class="bi bi-box-arrow-in-right"></i> ログイン</a>
            </li>
            <li class="nav-item">
              <a class="nav-link" href="{{ url_for('auth.register') }}"><i class="bi bi-person-plus"></i> 登録</a>
            </li>
          {% endif %}
        </ul>
      </nav>"""

    replacement = login_status_html
    content = re.sub(nav_pattern, replacement, content)

    write_file(BASE_TEMPLATE_PATH, content)

def main():
    """メイン処理"""
    print("="*80)
    print("認証機構統合スクリプト")
    print("="*80)

    # web_app.py のバックアップと読み込み
    print(f"\nTarget: {WEB_APP_PATH}")
    backup_file(WEB_APP_PATH)
    web_app_content = read_file(WEB_APP_PATH)

    # 段階的に統合
    web_app_content = integrate_step1_imports(web_app_content)
    web_app_content = integrate_step2_app_config(web_app_content)
    web_app_content = integrate_step3_protected_routes(web_app_content)

    # web_app.py を保存
    write_file(WEB_APP_PATH, web_app_content)

    # routes/__init__.py を更新
    integrate_step4_routes_init()

    # base.html を更新
    integrate_step5_base_template()

    print("\n" + "="*80)
    print("✓ 認証機構の統合が完了しました")
    print("="*80)
    print("\n次のステップ:")
    print("1. アプリケーションを再起動してください")
    print("2. /auth/register でユーザー登録")
    print("3. /auth/login でログイン")
    print("4. 保護されたルート（/settings など）にアクセス確認")

if __name__ == '__main__':
    main()
