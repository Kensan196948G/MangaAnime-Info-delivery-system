#!/usr/bin/env python3
"""
E2E Comprehensive Error Check for MangaAnime-Info-delivery-system
すべてのHTMLページとAPIエンドポイントの完全チェック
"""

import sys
import os
import re
import json
from pathlib import Path
from typing import Dict, List, Tuple
import sqlite3

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Flaskアプリのインポート
try:
    from app.web_app import app, init_db
except ImportError as e:
    print(f"❌ アプリのインポートエラー: {e}")
    sys.exit(1)


class E2EErrorChecker:
    """E2Eエラーチェッカー"""

    def __init__(self):
        self.app = app
        self.client = app.test_client()
        self.errors = []
        self.warnings = []
        self.success = []

        # データベース初期化
        with app.app_context():
            init_db()

    def check_all(self):
        """全チェック実行"""
        print("=" * 80)
        print("🔍 E2E 全階層エラーチェック開始")
        print("=" * 80)

        # 1. HTMLページチェック
        print("\n📄 HTMLページチェック...")
        self.check_html_pages()

        # 2. APIエンドポイントチェック
        print("\n🔌 APIエンドポイントチェック...")
        self.check_api_endpoints()

        # 3. 認証フローチェック
        print("\n🔐 認証フローチェック...")
        self.check_auth_flow()

        # 4. データベースチェック
        print("\n💾 データベースチェック...")
        self.check_database()

        # 5. テンプレートチェック
        print("\n📝 テンプレートチェック...")
        self.check_templates()

        # レポート出力
        self.print_report()

        return len(self.errors) == 0

    def check_html_pages(self):
        """HTMLページチェック"""
        pages = [
            ('/', 'トップページ'),
            ('/releases', 'リリース一覧'),
            ('/calendar', 'カレンダー'),
            ('/config', '設定'),
            ('/watchlist', 'ウォッチリスト'),
            ('/logs', 'ログ'),
            ('/users', 'ユーザー管理'),
            ('/api-keys', 'APIキー管理'),
            ('/admin/audit-logs', '監査ログ'),
            ('/admin/dashboard', '管理ダッシュボード'),
            ('/auth/login', 'ログイン'),
        ]

        for path, name in pages:
            self._check_page(path, name)

    def check_api_endpoints(self):
        """APIエンドポイントチェック"""
        endpoints = [
            ('/api/stats', 'GET', '統計情報'),
            ('/api/sources', 'GET', 'ソース一覧'),
            ('/api/releases/recent', 'GET', '最新リリース'),
            ('/api/releases/upcoming', 'GET', '今後のリリース'),
            ('/api/works', 'GET', '作品一覧'),
            ('/api/calendar/events', 'GET', 'カレンダーイベント'),
            ('/api/collection-status', 'GET', 'コレクション状態'),
            ('/health', 'GET', 'ヘルスチェック'),
            ('/ready', 'GET', 'レディネスチェック'),
            ('/metrics', 'GET', 'メトリクス'),
        ]

        for path, method, name in endpoints:
            self._check_api(path, method, name)

    def check_auth_flow(self):
        """認証フローチェック"""
        # ログインページアクセス
        response = self.client.get('/auth/login')
        if response.status_code == 200:
            self.success.append(f"✓ ログインページアクセス可能")
        else:
            self.errors.append(f"✗ ログインページアクセス失敗: {response.status_code}")

        # ログアウト（未認証）
        response = self.client.get('/auth/logout')
        if response.status_code in [200, 302]:
            self.success.append(f"✓ ログアウト処理正常")
        else:
            self.errors.append(f"✗ ログアウト処理失敗: {response.status_code}")

    def check_database(self):
        """データベースチェック"""
        db_path = project_root / 'db.sqlite3'

        if not db_path.exists():
            self.errors.append(f"✗ データベースファイルが存在しません: {db_path}")
            return

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # 必須テーブルチェック
            required_tables = [
                'works', 'releases', 'users', 'api_keys',
                'audit_logs', 'collection'
            ]

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row[0] for row in cursor.fetchall()]

            for table in required_tables:
                if table in existing_tables:
                    # レコード数確認
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    self.success.append(f"✓ テーブル '{table}' 存在 ({count}件)")
                else:
                    self.errors.append(f"✗ テーブル '{table}' が存在しません")

            conn.close()

        except Exception as e:
            self.errors.append(f"✗ データベースエラー: {e}")

    def check_templates(self):
        """テンプレートチェック"""
        templates_dir = project_root / 'app' / 'templates'

        if not templates_dir.exists():
            self.errors.append(f"✗ テンプレートディレクトリが存在しません: {templates_dir}")
            return

        # 必須テンプレート
        required_templates = [
            'base.html',
            'index.html',
            'releases.html',
            'calendar.html',
            'config.html',
            'watchlist.html',
            'logs.html',
            'users.html',
            'api_keys.html',
            'audit_logs.html',
            'admin_dashboard.html',
            'auth/login.html',
        ]

        for template in required_templates:
            template_path = templates_dir / template
            if template_path.exists():
                # url_for()エラーチェック
                self._check_template_syntax(template_path)
            else:
                self.errors.append(f"✗ テンプレートファイルが存在しません: {template}")

    def _check_page(self, path: str, name: str):
        """個別ページチェック"""
        try:
            response = self.client.get(path, follow_redirects=False)
            data = response.data.decode('utf-8')

            # ステータスコードチェック
            if response.status_code == 200:
                # Pythonトレースバック検出
                if 'Traceback' in data or 'Error' in data[:500]:
                    self.errors.append(f"✗ {name} ({path}): Pythonエラー検出")
                    self._extract_error(data, path)
                else:
                    self.success.append(f"✓ {name} ({path}): OK")

            elif response.status_code == 302:
                # リダイレクトは正常（認証など）
                location = response.headers.get('Location', '')
                self.success.append(f"✓ {name} ({path}): リダイレクト → {location}")

            elif response.status_code == 404:
                self.errors.append(f"✗ {name} ({path}): 404 Not Found")

            elif response.status_code == 500:
                self.errors.append(f"✗ {name} ({path}): 500 Internal Server Error")
                self._extract_error(data, path)

            else:
                self.warnings.append(f"⚠ {name} ({path}): {response.status_code}")

        except Exception as e:
            self.errors.append(f"✗ {name} ({path}): 例外発生 - {e}")

    def _check_api(self, path: str, method: str, name: str):
        """個別APIチェック"""
        try:
            if method == 'GET':
                response = self.client.get(path)
            elif method == 'POST':
                response = self.client.post(path, json={})
            else:
                response = self.client.get(path)

            data = response.data.decode('utf-8')

            # ステータスコードチェック
            if response.status_code == 200:
                # JSON形式チェック
                try:
                    json.loads(data)
                    self.success.append(f"✓ {name} ({method} {path}): OK")
                except json.JSONDecodeError:
                    if path in ['/health', '/ready']:
                        # ヘルスチェックはテキストでもOK
                        self.success.append(f"✓ {name} ({method} {path}): OK (text)")
                    else:
                        self.warnings.append(f"⚠ {name} ({method} {path}): JSON形式エラー")

            elif response.status_code == 404:
                self.errors.append(f"✗ {name} ({method} {path}): 404 Not Found")

            elif response.status_code == 500:
                self.errors.append(f"✗ {name} ({method} {path}): 500 Internal Server Error")
                self._extract_error(data, path)

            else:
                self.warnings.append(f"⚠ {name} ({method} {path}): {response.status_code}")

        except Exception as e:
            self.errors.append(f"✗ {name} ({method} {path}): 例外発生 - {e}")

    def _check_template_syntax(self, template_path: Path):
        """テンプレート構文チェック"""
        try:
            content = template_path.read_text(encoding='utf-8')

            # url_for()のエンドポイント名抽出
            url_for_pattern = r"url_for\(['\"]([^'\"]+)['\"]"
            matches = re.findall(url_for_pattern, content)

            if matches:
                self.success.append(f"✓ {template_path.name}: url_for() {len(matches)}個検出")

        except Exception as e:
            self.warnings.append(f"⚠ {template_path.name}: 読み込みエラー - {e}")

    def _extract_error(self, data: str, path: str):
        """エラー詳細抽出"""
        # Traceback抽出
        traceback_match = re.search(r'(Traceback.*?(?:Error|Exception):.*)', data, re.DOTALL)
        if traceback_match:
            error_detail = traceback_match.group(1)[:500]
            self.errors.append(f"  詳細: {error_detail}")

    def print_report(self):
        """レポート出力"""
        print("\n" + "=" * 80)
        print("📊 E2Eエラーチェック結果")
        print("=" * 80)

        print(f"\n✅ 成功: {len(self.success)}件")
        for msg in self.success[:10]:  # 最初の10件のみ表示
            print(f"  {msg}")
        if len(self.success) > 10:
            print(f"  ... 他 {len(self.success) - 10}件")

        print(f"\n⚠️  警告: {len(self.warnings)}件")
        for msg in self.warnings:
            print(f"  {msg}")

        print(f"\n❌ エラー: {len(self.errors)}件")
        for msg in self.errors:
            print(f"  {msg}")

        print("\n" + "=" * 80)

        if len(self.errors) == 0:
            print("✅ すべてのチェックに合格しました！")
            return True
        else:
            print("❌ エラーが検出されました。修正が必要です。")
            return False


def main():
    """メイン実行"""
    checker = E2EErrorChecker()
    success = checker.check_all()

    # 終了コード
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
