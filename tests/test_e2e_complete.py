#!/usr/bin/env python3
"""
完全E2Eテストスイート
全階層の統合テスト
"""

import sys
import os
import time
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import pytest

# プロジェクトルート
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'scripts'))

# アプリとレポート生成器インポート
try:
    from app.web_app import app, init_db
    from generate_e2e_report import E2EReportGenerator
except ImportError as e:
    pytest.skip(f"Required modules not available: {e}", allow_module_level=True)


class CompleteE2ETester:
    """完全E2Eテスター"""

    def __init__(self):
        self.app = app
        self.client = app.test_client()
        self.report = E2EReportGenerator()

        # データベース初期化
        with app.app_context():
            init_db()

        # テスト結果
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0

    def run_all_tests(self):
        """全テスト実行"""
        print("=" * 80)
        print("🧪 完全E2Eテストスイート実行")
        print("=" * 80)

        # 1. HTMLページテスト
        print("\n1️⃣ HTMLページテスト...")
        self.test_html_pages()

        # 2. APIエンドポイントテスト
        print("\n2️⃣ APIエンドポイントテスト...")
        self.test_api_endpoints()

        # 3. 認証フローテスト
        print("\n3️⃣ 認証フローテスト...")
        self.test_authentication()

        # 4. データベーステスト
        print("\n4️⃣ データベーステスト...")
        self.test_database_operations()

        # 5. エラーハンドリングテスト
        print("\n5️⃣ エラーハンドリングテスト...")
        self.test_error_handling()

        # 6. パフォーマンステスト
        print("\n6️⃣ パフォーマンステスト...")
        self.test_performance()

        # レポート生成
        print("\n" + "=" * 80)
        print("📊 テスト結果サマリー")
        print("=" * 80)
        self.print_summary()

        # HTMLレポート生成
        report_path = self.report.generate_html_report()
        print(f"\n📄 HTMLレポート: {report_path}")

        return self.failed_tests == 0

    def test_html_pages(self):
        """HTMLページテスト"""
        pages = [
            ('/', 'トップページ', 200),
            ('/releases', 'リリース一覧', 200),
            ('/calendar', 'カレンダー', 200),
            ('/config', '設定', 200),
            ('/watchlist', 'ウォッチリスト', 200),
            ('/logs', 'ログ', 200),
            ('/users', 'ユーザー管理', 200),
            ('/api-keys', 'APIキー管理', 200),
            ('/admin/audit-logs', '監査ログ', 200),
            ('/admin/dashboard', '管理ダッシュボード', 200),
            ('/auth/login', 'ログイン', 200),
        ]

        for path, name, expected_status in pages:
            self._test_page(path, name, expected_status)

    def test_api_endpoints(self):
        """APIエンドポイントテスト"""
        endpoints = [
            ('/api/stats', 'GET', '統計情報', 200),
            ('/api/sources', 'GET', 'ソース一覧', 200),
            ('/api/releases/recent', 'GET', '最新リリース', 200),
            ('/api/releases/upcoming', 'GET', '今後のリリース', 200),
            ('/api/works', 'GET', '作品一覧', 200),
            ('/api/calendar/events', 'GET', 'カレンダーイベント', 200),
            ('/api/collection-status', 'GET', 'コレクション状態', 200),
            ('/health', 'GET', 'ヘルスチェック', 200),
            ('/ready', 'GET', 'レディネスチェック', 200),
            ('/metrics', 'GET', 'メトリクス', 200),
        ]

        for path, method, name, expected_status in endpoints:
            self._test_api(path, method, name, expected_status)

    def test_authentication(self):
        """認証テスト"""
        # ログインページアクセス
        self._test_page('/auth/login', 'ログインページ', 200)

        # ログアウト
        response = self.client.get('/auth/logout', follow_redirects=False)
        self._record_test(
            'ログアウト処理',
            response.status_code in [200, 302],
            f"Status: {response.status_code}"
        )

    def test_database_operations(self):
        """データベース操作テスト"""
        db_path = project_root / 'db.sqlite3'

        if not db_path.exists():
            self._record_test(
                'データベースファイル存在',
                False,
                f"ファイルが見つかりません: {db_path}"
            )
            return

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # テーブル存在確認
            required_tables = ['works', 'releases', 'users', 'api_keys', 'audit_logs']
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row[0] for row in cursor.fetchall()]

            for table in required_tables:
                exists = table in existing_tables
                self._record_test(
                    f'テーブル存在: {table}',
                    exists,
                    f"テーブル '{table}' が見つかりません" if not exists else "OK"
                )

                if exists:
                    # レコード数確認
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"    ├─ レコード数: {count}件")

            conn.close()

        except Exception as e:
            self._record_test('データベース接続', False, str(e))

    def test_error_handling(self):
        """エラーハンドリングテスト"""
        # 404エラー
        response = self.client.get('/nonexistent-page')
        self._record_test(
            '404エラーハンドリング',
            response.status_code == 404,
            f"Status: {response.status_code}"
        )

        # 無効なAPIリクエスト
        response = self.client.post('/api/invalid', json={'invalid': 'data'})
        self._record_test(
            '無効なAPIリクエスト処理',
            response.status_code in [404, 405],
            f"Status: {response.status_code}"
        )

    def test_performance(self):
        """パフォーマンステスト"""
        # ページロード時間
        start_time = time.time()
        response = self.client.get('/')
        end_time = time.time()

        load_time = end_time - start_time
        self._record_test(
            'ページロード時間',
            load_time < 1.0,
            f"{load_time:.3f}秒"
        )

        # API応答時間
        start_time = time.time()
        response = self.client.get('/api/stats')
        end_time = time.time()

        api_time = end_time - start_time
        self._record_test(
            'API応答時間',
            api_time < 0.5,
            f"{api_time:.3f}秒"
        )

    def _test_page(self, path: str, name: str, expected_status: int):
        """個別ページテスト"""
        start_time = time.time()
        response = self.client.get(path, follow_redirects=False)
        end_time = time.time()

        response_time = end_time - start_time
        data = response.data.decode('utf-8')

        # ステータスコードチェック
        status_ok = response.status_code == expected_status

        # エラー検出
        has_error = 'Traceback' in data or 'Error' in data[:500]

        # 結果記録
        success = status_ok and not has_error

        if success:
            print(f"  ✓ {name} ({path})")
        else:
            print(f"  ✗ {name} ({path}) - Status: {response.status_code}")
            if has_error:
                print(f"    └─ エラー検出")
                self.report.add_error(f'{name} エラー', f'{path} でエラーが検出されました')

        self._record_test(name, success, f"Status: {response.status_code}")
        self.report.add_page_result(name, path, response.status_code, response_time)

    def _test_api(self, path: str, method: str, name: str, expected_status: int):
        """個別APIテスト"""
        if method == 'GET':
            response = self.client.get(path)
        elif method == 'POST':
            response = self.client.post(path, json={})
        else:
            response = self.client.get(path)

        success = response.status_code == expected_status
        result = 'OK' if success else f'Status: {response.status_code}'

        if success:
            print(f"  ✓ {name} ({method} {path})")
        else:
            print(f"  ✗ {name} ({method} {path}) - {result}")

        self._record_test(f'{name} API', success, result)
        self.report.add_api_result(path, method, response.status_code, result)

    def _record_test(self, test_name: str, passed: bool, detail: str = ""):
        """テスト結果記録"""
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
        else:
            self.failed_tests += 1

    def print_summary(self):
        """サマリー出力"""
        print(f"\n総テスト数: {self.total_tests}")
        print(f"✅ 成功: {self.passed_tests}")
        print(f"❌ 失敗: {self.failed_tests}")

        if self.failed_tests == 0:
            print("\n🎉 すべてのテストに合格しました！")
        else:
            print(f"\n⚠️  {self.failed_tests}件のテストが失敗しました")

        # 成功率
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        print(f"成功率: {success_rate:.1f}%")


def main():
    """メイン実行"""
    tester = CompleteE2ETester()
    success = tester.run_all_tests()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
