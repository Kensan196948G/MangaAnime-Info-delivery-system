#!/usr/bin/env python3
"""
ユーザー管理機能 自動統合スクリプト
既存のapp/routes/auth.py、app/web_app.py、templates/base.htmlに
必要なコードを自動追加します
"""

import os
import sys
import re
from pathlib import Path

# プロジェクトルートディレクトリ
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def backup_file(file_path: Path) -> Path:
    """ファイルのバックアップを作成"""
    backup_path = file_path.with_suffix(file_path.suffix + '.bak')
    backup_path.write_text(file_path.read_text(encoding='utf-8'), encoding='utf-8')
    print(f"✅ バックアップ作成: {backup_path}")
    return backup_path


def integrate_auth_py():
    """app/routes/auth.pyにUserStoreメソッドを追加"""
    auth_file = PROJECT_ROOT / 'app' / 'routes' / 'auth.py'

    if not auth_file.exists():
        print(f"❌ ファイルが見つかりません: {auth_file}")
        return False

    content = auth_file.read_text(encoding='utf-8')

    # すでに統合済みかチェック
    if 'def get_all_users(self)' in content:
        print("⚠️  auth.py: すでに統合済みです")
        return True

    # バックアップ
    backup_file(auth_file)

    # UserStoreクラスの終わりを見つけて追加
    methods_to_add = '''
    def get_all_users(self) -> list:
        """全ユーザーを取得"""
        return list(self._users.values())

    def delete_user(self, user_id: str) -> bool:
        """ユーザーを削除"""
        if user_id in self._users:
            del self._users[user_id]
            return True
        return False

    def get_user_count(self) -> int:
        """ユーザー数を取得"""
        return len(self._users)
'''

    # get_user_by_usernameメソッドの後に追加
    pattern = r'(def get_user_by_username\(self, username: str\).*?return None)'
    replacement = r'\1' + methods_to_add

    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    if new_content == content:
        print("❌ auth.py: パターンマッチに失敗しました")
        return False

    auth_file.write_text(new_content, encoding='utf-8')
    print("✅ auth.py: UserStoreメソッドを追加しました")
    return True


def integrate_web_app_py():
    """app/web_app.pyにusers_bpを登録"""
    web_app_file = PROJECT_ROOT / 'app' / 'web_app.py'

    if not web_app_file.exists():
        print(f"❌ ファイルが見つかりません: {web_app_file}")
        return False

    content = web_app_file.read_text(encoding='utf-8')

    # すでに統合済みかチェック
    if 'from app.routes.users import users_bp' in content:
        print("⚠️  web_app.py: すでに統合済みです")
        return True

    # バックアップ
    backup_file(web_app_file)

    # インポート追加
    import_pattern = r'(from app\.routes\.auth import auth_bp, login_manager)'
    import_replacement = r'\1\nfrom app.routes.users import users_bp'

    content = re.sub(import_pattern, import_replacement, content)

    # Blueprint登録
    register_pattern = r'(app\.register_blueprint\(auth_bp\))'
    register_replacement = r'\1\napp.register_blueprint(users_bp)'

    content = re.sub(register_pattern, register_replacement, content)

    web_app_file.write_text(content, encoding='utf-8')
    print("✅ web_app.py: users_bpを登録しました")
    return True


def integrate_base_html():
    """templates/base.htmlにナビゲーションリンクを追加"""
    base_file = PROJECT_ROOT / 'templates' / 'base.html'

    if not base_file.exists():
        print(f"❌ ファイルが見つかりません: {base_file}")
        return False

    content = base_file.read_text(encoding='utf-8')

    # すでに統合済みかチェック
    if 'users.user_list' in content:
        print("⚠️  base.html: すでに統合済みです")
        return True

    # バックアップ
    backup_file(base_file)

    # ナビゲーションメニュー追加
    nav_addition = '''                        {% if current_user.is_admin %}
                        <li class="nav-item">
                            <a class="nav-link" href="{{ url_for('users.user_list') }}">
                                <i class="bi bi-people-fill"></i> ユーザー管理
                            </a>
                        </li>
                        {% endif %}
'''

    # ログアウトリンクの前に挿入
    pattern = r'(\s+<li class="nav-item">\s+<a class="nav-link" href="{{ url_for\(\'auth\.logout\'\) }}">'
    replacement = nav_addition + r'\1'

    new_content = re.sub(pattern, replacement, content)

    if new_content == content:
        print("❌ base.html: パターンマッチに失敗しました")
        return False

    base_file.write_text(new_content, encoding='utf-8')
    print("✅ base.html: ナビゲーションリンクを追加しました")
    return True


def verify_integration():
    """統合結果の検証"""
    print("\n" + "=" * 60)
    print("統合結果の検証")
    print("=" * 60)

    checks = [
        (PROJECT_ROOT / 'app' / 'routes' / 'users.py', "users.py"),
        (PROJECT_ROOT / 'templates' / 'users' / 'list.html', "users/list.html"),
        (PROJECT_ROOT / 'app' / 'routes' / 'auth.py', "auth.py (get_all_users)"),
        (PROJECT_ROOT / 'app' / 'web_app.py', "web_app.py (users_bp)"),
        (PROJECT_ROOT / 'templates' / 'base.html', "base.html (nav)"),
    ]

    all_ok = True
    for file_path, name in checks:
        if file_path.exists():
            content = file_path.read_text(encoding='utf-8')
            if 'users' in name.lower() and 'list.html' in name:
                ok = 'ユーザー管理' in content
            elif 'auth.py' in name:
                ok = 'get_all_users' in content
            elif 'web_app.py' in name:
                ok = 'users_bp' in content
            elif 'base.html' in name:
                ok = 'users.user_list' in content
            else:
                ok = True

            status = "✅" if ok else "❌"
            print(f"{status} {name}")
            all_ok = all_ok and ok
        else:
            print(f"❌ {name} (ファイルが存在しません)")
            all_ok = False

    return all_ok


def main():
    """メイン処理"""
    print("=" * 60)
    print("ユーザー管理機能 自動統合スクリプト")
    print("=" * 60)
    print()

    # 各ファイルの統合
    results = []

    print("1. auth.pyへのUserStoreメソッド追加...")
    results.append(integrate_auth_py())

    print("\n2. web_app.pyへのBlueprint登録...")
    results.append(integrate_web_app_py())

    print("\n3. base.htmlへのナビゲーション追加...")
    results.append(integrate_base_html())

    # 検証
    verify_ok = verify_integration()
    results.append(verify_ok)

    # 結果サマリー
    print("\n" + "=" * 60)
    print("統合完了サマリー")
    print("=" * 60)

    if all(results):
        print("✅ すべての統合が正常に完了しました")
        print()
        print("次のステップ:")
        print("  1. アプリケーションを起動: python app/web_app.py")
        print("  2. 管理者でログイン")
        print("  3. ナビゲーションバーの「ユーザー管理」をクリック")
        print()
        print("詳細な使用方法: docs/USER_MANAGEMENT_INTEGRATION.md")
        return 0
    else:
        print("❌ 一部の統合に失敗しました")
        print()
        print("トラブルシューティング:")
        print("  1. バックアップファイル(.bak)から復元")
        print("  2. 手動統合ガイドを参照: docs/USER_MANAGEMENT_INTEGRATION.md")
        return 1


if __name__ == '__main__':
    sys.exit(main())
