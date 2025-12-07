#!/usr/bin/env python3
"""
認証統合を実行
確実性を高めるため、ファイルを読み取ってから編集
"""
import os
import shutil
from datetime import datetime

BASE = '/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system'

def backup(path):
    """バックアップ作成"""
    backup_path = f"{path}.bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if os.path.exists(path):
        shutil.copy2(path, backup_path)
        print(f"✓ Backed up: {os.path.basename(backup_path)}")
    return backup_path

def read_lines(path):
    """ファイルを行単位で読み込み"""
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return f.readlines()

def write_lines(path, lines):
    """ファイルに行単位で書き込み"""
    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print(f"✓ Updated: {os.path.basename(path)}")

def show_context(lines, line_num, context=5):
    """指定行の前後を表示"""
    start = max(0, line_num - context)
    end = min(len(lines), line_num + context + 1)
    print(f"\n  Context around line {line_num + 1}:")
    for i in range(start, end):
        marker = " >>>" if i == line_num else "    "
        print(f"  {marker} {i+1:4d}: {lines[i]}", end='')

# =============================================================================
# Task 1: app/web_app.py の編集
# =============================================================================
print("\n" + "="*80)
print("Task 1: Integrating authentication into app/web_app.py")
print("="*80)

web_app_path = f'{BASE}/app/web_app.py'
backup(web_app_path)
lines = read_lines(web_app_path)

print(f"\nOriginal file: {len(lines)} lines")

# 現在の状態を確認
print("\n--- Checking current state ---")
has_flask_login = any('from flask_login import' in line for line in lines)
has_secret_key = any("app.config['SECRET_KEY']" in line for line in lines)
has_auth_import = any('from app.routes.auth import' in line for line in lines)

print(f"  flask_login imported: {has_flask_login}")
print(f"  SECRET_KEY configured: {has_secret_key}")
print(f"  auth module imported: {has_auth_import}")

# Step 1: flask_login インポート追加
if not has_flask_login:
    print("\n[Step 1.1] Adding flask_login import...")
    for i, line in enumerate(lines):
        if line.strip().startswith('from flask import '):
            # この行の直後に追加
            lines.insert(i + 1, 'from flask_login import login_required, current_user\n')
            print(f"  ✓ Inserted at line {i + 2}")
            show_context(lines, i + 1)
            break

# Step 2: auth モジュールのインポート追加
if not has_auth_import:
    print("\n[Step 1.2] Adding auth module import...")
    for i, line in enumerate(lines):
        if 'import sqlite3' in line:
            # この行の直後に追加
            lines.insert(i + 1, 'from app.routes.auth import auth_bp, init_login_manager\n')
            print(f"  ✓ Inserted at line {i + 2}")
            show_context(lines, i + 1)
            break

# Step 3: SECRET_KEY と LoginManager 初期化
if not has_secret_key:
    print("\n[Step 1.3] Adding SECRET_KEY and LoginManager initialization...")
    for i, line in enumerate(lines):
        if line.strip() == 'app = Flask(__name__)':
            # この行の直後に設定を追加
            insert_lines = [
                "app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')\n",
                "\n",
                "# Initialize login manager\n",
                "init_login_manager(app)\n",
                "\n",
                "# Register authentication blueprint\n",
                "app.register_blueprint(auth_bp, url_prefix='/auth')\n",
                "\n"
            ]
            for j, insert_line in enumerate(insert_lines):
                lines.insert(i + 1 + j, insert_line)
            print(f"  ✓ Inserted configuration block after line {i + 1}")
            show_context(lines, i + 4, context=10)
            break

# Step 4: 保護が必要なルートに @login_required を追加
print("\n[Step 1.4] Adding @login_required to protected routes...")
protected_routes = [
    'def settings():',
    'def update_settings():',
    'def clear_history():',
    'def delete_work('
]

protected_count = 0
i = 0
while i < len(lines):
    line = lines[i]
    # ルート定義を探す
    for route_def in protected_routes:
        if route_def in line:
            # 直前の行が @app.route かチェック
            if i > 0 and '@app.route' in lines[i-1]:
                # さらにその前に @login_required があるかチェック
                if i < 2 or '@login_required' not in lines[i-2]:
                    # @app.route と def の間に @login_required を挿入
                    lines.insert(i, '@login_required\n')
                    protected_count += 1
                    print(f"  ✓ Protected: {route_def.strip()} at line {i + 1}")
                    show_context(lines, i, context=3)
                    i += 1  # 挿入した分スキップ
    i += 1

print(f"\n  Total protected routes: {protected_count}")

# ファイルに書き込み
write_lines(web_app_path, lines)

# =============================================================================
# Task 2: app/routes/__init__.py の作成/更新
# =============================================================================
print("\n" + "="*80)
print("Task 2: Creating/Updating app/routes/__init__.py")
print("="*80)

routes_init_path = f'{BASE}/app/routes/__init__.py'

if os.path.exists(routes_init_path):
    backup(routes_init_path)
    init_lines = read_lines(routes_init_path)
else:
    init_lines = []
    print("  Creating new file...")

# authの export が既にあるかチェック
has_auth_export = any('from app.routes.auth import' in line for line in init_lines)

if not has_auth_export:
    # 新しい内容を追加
    new_content = '''"""
Routes package
Contains all route blueprints
"""
from app.routes.auth import auth_bp, init_login_manager

__all__ = ['auth_bp', 'init_login_manager']
'''
    if init_lines:
        # 既存の内容に追加
        init_lines.append('\nfrom app.routes.auth import auth_bp, init_login_manager\n')
    else:
        init_lines = new_content.splitlines(keepends=True)

    write_lines(routes_init_path, init_lines)
else:
    print("  ℹ auth already exported")

# =============================================================================
# Task 3: templates/base.html の更新
# =============================================================================
print("\n" + "="*80)
print("Task 3: Updating templates/base.html with login status")
print("="*80)

base_html_path = f'{BASE}/templates/base.html'

if os.path.exists(base_html_path):
    backup(base_html_path)
    html_content = ''
    with open(base_html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    has_login_status = 'current_user.is_authenticated' in html_content

    if not has_login_status:
        print("  Adding login status display...")

        # </nav> の前に追加
        login_status_html = '''
          <!-- ログイン状態表示 -->
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
'''

        # </ul> の直後、</nav> の前に挿入
        # より安全な方法: 最後の </ul> の後に追加
        if '</nav>' in html_content:
            html_content = html_content.replace('</nav>', login_status_html + '\n        </nav>')
            with open(base_html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print("  ✓ Added login status display")
        else:
            print("  ⚠ </nav> tag not found, skipping template update")
    else:
        print("  ℹ Login status already present")
else:
    print("  ⚠ base.html not found, skipping")

# =============================================================================
# Summary
# =============================================================================
print("\n" + "="*80)
print("✓ Authentication Integration Complete!")
print("="*80)
print("""
Next Steps:
1. Restart the application
2. Visit /auth/register to create a user
3. Visit /auth/login to log in
4. Try accessing protected routes like /settings

Protected Routes:
- /settings (settings page)
- /api/settings/update (update settings)
- /api/clear-history (clear notification history)
- /api/delete-work/<id> (delete work)
""")
