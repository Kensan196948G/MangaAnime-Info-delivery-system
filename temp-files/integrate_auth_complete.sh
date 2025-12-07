#!/bin/bash
#
# 認証機構統合スクリプト
# web_app.py, routes/__init__.py, templates/base.html を更新
#

set -e  # エラーで停止

BASE_DIR="/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system"
cd "$BASE_DIR"

echo "========================================================================"
echo "認証機構統合スクリプト"
echo "========================================================================"

# バックアップディレクトリ作成
BACKUP_DIR="backups/auth_integration_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
echo "✓ Backup directory: $BACKUP_DIR"

# ============================================================================
# Task 1: app/routes/__init__.py の作成/更新
# ============================================================================
echo ""
echo "[Task 1] Creating/Updating app/routes/__init__.py"
echo "------------------------------------------------------------------------"

ROUTES_INIT="app/routes/__init__.py"

if [ -f "$ROUTES_INIT" ]; then
    cp "$ROUTES_INIT" "$BACKUP_DIR/$(basename $ROUTES_INIT).bak"
    echo "✓ Backed up existing file"

    if grep -q "from app.routes.auth import" "$ROUTES_INIT"; then
        echo "ℹ  auth already exported in __init__.py"
    else
        echo "Adding auth export..."
        cat >> "$ROUTES_INIT" << 'EOF'

from app.routes.auth import auth_bp, init_login_manager

__all__ = ['auth_bp', 'init_login_manager']
EOF
        echo "✓ Added auth export"
    fi
else
    echo "Creating new __init__.py..."
    cat > "$ROUTES_INIT" << 'EOF'
"""
Routes package
Contains all route blueprints for the application
"""
from app.routes.auth import auth_bp, init_login_manager

__all__ = ['auth_bp', 'init_login_manager']
EOF
    echo "✓ Created $ROUTES_INIT"
fi

# ============================================================================
# Task 2: app/web_app.py の更新
# ============================================================================
echo ""
echo "[Task 2] Updating app/web_app.py"
echo "------------------------------------------------------------------------"

WEB_APP="app/web_app.py"
cp "$WEB_APP" "$BACKUP_DIR/$(basename $WEB_APP).bak"
echo "✓ Backed up $WEB_APP"

# Python スクリプトで編集
python3 << 'PYTHON_SCRIPT'
import re

WEB_APP = 'app/web_app.py'

with open(WEB_APP, 'r', encoding='utf-8') as f:
    content = f.read()

original_content = content
changes = []

# Step 1: flask_login インポート追加
if 'from flask_login import' not in content:
    # Flask インポートの直後に追加
    content = re.sub(
        r'(from flask import [^\n]+\n)',
        r'\1from flask_login import login_required, current_user\n',
        content,
        count=1
    )
    changes.append("Added flask_login import")

# Step 2: auth モジュールインポート追加
if 'from app.routes.auth import' not in content:
    # import sqlite3 の直後に追加
    content = re.sub(
        r'(import sqlite3\n)',
        r'\1from app.routes.auth import auth_bp, init_login_manager\n',
        content,
        count=1
    )
    changes.append("Added auth module import")

# Step 3: SECRET_KEY 設定追加
if "app.config['SECRET_KEY']" not in content:
    # app = Flask(__name__) の直後に追加
    content = re.sub(
        r"(app = Flask\(__name__\)\n)",
        r"\1app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')\n\n" +
        r"# Initialize login manager\n" +
        r"init_login_manager(app)\n\n" +
        r"# Register authentication blueprint\n" +
        r"app.register_blueprint(auth_bp, url_prefix='/auth')\n\n",
        content,
        count=1
    )
    changes.append("Added SECRET_KEY and auth initialization")

# Step 4: 保護が必要なルートに @login_required を追加
protected_routes = [
    (r"(@app\.route\('/settings'[^\)]*\)\n)(def settings\(\):)", "settings"),
    (r"(@app\.route\('/api/settings/update'[^\)]*\)\n)(def update_settings\(\):)", "update_settings"),
    (r"(@app\.route\('/api/clear-history'[^\)]*\)\n)(def clear_history\(\):)", "clear_history"),
    (r"(@app\.route\('/api/delete-work/<int:work_id>'[^\)]*\)\n)(def delete_work\([^\)]*\):)", "delete_work"),
]

for pattern, name in protected_routes:
    # @login_required が既にあるかチェック
    route_match = re.search(pattern, content)
    if route_match:
        # 前後100文字で @login_required があるかチェック
        start = max(0, route_match.start() - 100)
        end = min(len(content), route_match.end() + 50)
        context = content[start:end]

        if '@login_required' not in context:
            content = re.sub(pattern, r'\1@login_required\n\2', content)
            changes.append(f"Protected route: {name}")

# ファイルに書き込み
if content != original_content:
    with open(WEB_APP, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✓ Updated web_app.py")
    for change in changes:
        print(f"  - {change}")
else:
    print("ℹ  No changes needed in web_app.py")

PYTHON_SCRIPT

# ============================================================================
# Task 3: templates/base.html の更新
# ============================================================================
echo ""
echo "[Task 3] Updating templates/base.html"
echo "------------------------------------------------------------------------"

BASE_HTML="templates/base.html"
cp "$BASE_HTML" "$BACKUP_DIR/$(basename $BASE_HTML).bak"
echo "✓ Backed up $BASE_HTML"

# Python スクリプトで編集
python3 << 'PYTHON_SCRIPT'
BASE_HTML = 'templates/base.html'

with open(BASE_HTML, 'r', encoding='utf-8') as f:
    content = f.read()

if 'current_user.is_authenticated' in content:
    print("ℹ  Login status already present in template")
else:
    # </nav> の前にログイン状態表示を追加
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

        with open(BASE_HTML, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✓ Added login status display to template")
    else:
        print("⚠  </nav> tag not found, skipping template update")

PYTHON_SCRIPT

# ============================================================================
# Summary
# ============================================================================
echo ""
echo "========================================================================"
echo "✓ 認証機構の統合が完了しました"
echo "========================================================================"
echo ""
echo "変更されたファイル:"
echo "  - app/routes/__init__.py (認証モジュールのエクスポート)"
echo "  - app/web_app.py (認証統合とルート保護)"
echo "  - templates/base.html (ログイン状態表示)"
echo ""
echo "バックアップ:"
echo "  $BACKUP_DIR"
echo ""
echo "次のステップ:"
echo "  1. アプリケーションを再起動"
echo "  2. /auth/register でユーザー登録"
echo "  3. /auth/login でログイン"
echo "  4. /settings などの保護されたルートにアクセステスト"
echo ""
echo "保護されたルート:"
echo "  - /settings"
echo "  - /api/settings/update"
echo "  - /api/clear-history"
echo "  - /api/delete-work/<id>"
echo ""
echo "========================================================================"
