#!/usr/bin/env python3
"""
認証機構統合 - 最終実行スクリプト
このスクリプトを実行すると、認証機構がメインアプリに統合されます
"""
import os
import shutil
import re
from datetime import datetime

BASE_DIR = '/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system'
os.chdir(BASE_DIR)

# バックアップディレクトリ
BACKUP_DIR = f'backups/auth_integration_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
os.makedirs(BACKUP_DIR, exist_ok=True)

print("="*80)
print("認証機構統合スクリプト - 実行開始")
print("="*80)
print(f"Backup directory: {BACKUP_DIR}")
print()

# ============================================================================
# Task 1: app/routes/__init__.py
# ============================================================================
print("[Task 1] app/routes/__init__.py")
print("-"*80)

routes_init = 'app/routes/__init__.py'

if os.path.exists(routes_init):
    shutil.copy2(routes_init, f'{BACKUP_DIR}/__init__.py.bak')
    with open(routes_init, 'r') as f:
        content = f.read()

    if 'from app.routes.auth import' in content:
        print("✓ auth already exported")
    else:
        content += '\nfrom app.routes.auth import auth_bp, init_login_manager\n'
        content += "\n__all__ = ['auth_bp', 'init_login_manager']\n"
        with open(routes_init, 'w') as f:
            f.write(content)
        print("✓ Added auth export")
else:
    # 新規作成
    with open(routes_init, 'w') as f:
        f.write('''"""
Routes package
Contains all route blueprints for the application
"""
from app.routes.auth import auth_bp, init_login_manager

__all__ = ['auth_bp', 'init_login_manager']
''')
    print("✓ Created new file")

# ============================================================================
# Task 2: app/web_app.py
# ============================================================================
print("\n[Task 2] app/web_app.py")
print("-"*80)

web_app = 'app/web_app.py'
shutil.copy2(web_app, f'{BACKUP_DIR}/web_app.py.bak')

with open(web_app, 'r') as f:
    content = f.read()

original_content = content
changes = []

# 2.1: flask_login インポート
if 'from flask_login import' not in content:
    pattern = r'(from flask import [^\n]+\n)'
    replacement = r'\1from flask_login import login_required, current_user\n'
    content = re.sub(pattern, replacement, content, count=1)
    changes.append("Added: from flask_login import login_required, current_user")

# 2.2: auth モジュールインポート
if 'from app.routes.auth import' not in content:
    pattern = r'(import sqlite3\n)'
    replacement = r'\1from app.routes.auth import auth_bp, init_login_manager\n'
    content = re.sub(pattern, replacement, content, count=1)
    changes.append("Added: from app.routes.auth import auth_bp, init_login_manager")

# 2.3: SECRET_KEY と認証初期化
if "app.config['SECRET_KEY']" not in content:
    pattern = r"(app = Flask\(__name__\)\n)"
    replacement = (
        r"\1"
        r"app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')\n"
        r"\n"
        r"# Initialize login manager\n"
        r"init_login_manager(app)\n"
        r"\n"
        r"# Register authentication blueprint\n"
        r"app.register_blueprint(auth_bp, url_prefix='/auth')\n"
        r"\n"
    )
    content = re.sub(pattern, replacement, content, count=1)
    changes.append("Added: SECRET_KEY and auth initialization")

# 2.4: 保護ルートに @login_required 追加
protected_routes = [
    (r"(@app\.route\('/settings'[^\)]*\)\s*\n)(def settings\(\):)", "settings"),
    (r"(@app\.route\('/api/settings/update'[^\)]*\)\s*\n)(def update_settings\(\):)", "update_settings"),
    (r"(@app\.route\('/api/clear-history'[^\)]*\)\s*\n)(def clear_history\(\):)", "clear_history"),
    (r"(@app\.route\('/api/delete-work/<int:work_id>'[^\)]*\)\s*\n)(def delete_work\([^\)]*\):)", "delete_work"),
]

for pattern, name in protected_routes:
    match = re.search(pattern, content)
    if match:
        # 前後をチェックして @login_required が既にあるか確認
        start = max(0, match.start() - 200)
        end = min(len(content), match.end() + 100)
        context = content[start:end]

        if '@login_required' not in context:
            replacement = r'\1@login_required\n\2'
            content = re.sub(pattern, replacement, content, count=1)
            changes.append(f"Protected: {name}")

# ファイルに書き込み
if content != original_content:
    with open(web_app, 'w') as f:
        f.write(content)
    print("✓ Updated web_app.py:")
    for change in changes:
        print(f"  - {change}")
else:
    print("ℹ No changes needed")

# ============================================================================
# Task 3: templates/base.html
# ============================================================================
print("\n[Task 3] templates/base.html")
print("-"*80)

base_html = 'templates/base.html'
shutil.copy2(base_html, f'{BACKUP_DIR}/base.html.bak')

with open(base_html, 'r') as f:
    content = f.read()

if 'current_user.is_authenticated' in content:
    print("ℹ Login status already present")
else:
    # </nav> の前にログイン状態を追加
    login_status = '''
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

    if '</nav>' in content:
        content = content.replace('</nav>', login_status + '\n        </nav>', 1)
        with open(base_html, 'w') as f:
            f.write(content)
        print("✓ Added login status display")
    else:
        print("⚠ </nav> tag not found")

# ============================================================================
# Summary
# ============================================================================
print("\n" + "="*80)
print("✓ 統合完了!")
print("="*80)
print(f"\nBackup location: {BACKUP_DIR}/")
print("\nModified files:")
print("  - app/routes/__init__.py")
print("  - app/web_app.py")
print("  - templates/base.html")
print("\nProtected routes:")
print("  - /settings")
print("  - /api/settings/update")
print("  - /api/clear-history")
print("  - /api/delete-work/<id>")
print("\nNext steps:")
print("  1. Restart the application: python3 app/web_app.py")
print("  2. Register a user: http://localhost:5000/auth/register")
print("  3. Login: http://localhost:5000/auth/login")
print("  4. Test protected routes")
print("="*80)
