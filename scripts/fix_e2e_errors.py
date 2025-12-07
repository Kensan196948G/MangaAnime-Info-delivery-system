#!/usr/bin/env python3
"""
E2Eエラー自動修復スクリプト
検出されたエラーを自動的に修正します
"""

import sys
import os
import re
import shutil
from pathlib import Path
from datetime import datetime

project_root = Path(__file__).parent.parent


class E2EErrorFixer:
    """E2Eエラー自動修復"""

    def __init__(self):
        self.fixes_applied = []
        self.backup_dir = project_root / 'backups' / datetime.now().strftime('%Y%m%d_%H%M%S')

    def fix_all(self):
        """全修復実行"""
        print("=" * 80)
        print("🔧 E2Eエラー自動修復開始")
        print("=" * 80)

        # バックアップディレクトリ作成
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        print(f"\n📦 バックアップディレクトリ: {self.backup_dir}")

        # 1. 未実装エンドポイント追加
        print("\n1️⃣ 未実装エンドポイント追加...")
        self.add_missing_endpoints()

        # 2. テンプレートエラー修正
        print("\n2️⃣ テンプレートエラー修正...")
        self.fix_template_errors()

        # 3. データベーススキーマ修正
        print("\n3️⃣ データベーススキーマ確認...")
        self.verify_database_schema()

        # 4. ルーティングエラー修正
        print("\n4️⃣ ルーティングエラー修正...")
        self.fix_routing_errors()

        # レポート出力
        self.print_report()

    def add_missing_endpoints(self):
        """未実装エンドポイント追加"""
        web_app_path = project_root / 'app' / 'web_app.py'

        if not web_app_path.exists():
            print(f"❌ web_app.pyが見つかりません: {web_app_path}")
            return

        # バックアップ
        backup_path = self.backup_dir / 'web_app.py.bak'
        shutil.copy(web_app_path, backup_path)
        print(f"  ✓ バックアップ作成: {backup_path}")

        content = web_app_path.read_text(encoding='utf-8')

        # /health エンドポイント追加
        if '@app.route("/health")' not in content:
            health_endpoint = '''

@app.route('/health')
def health_check():
    """ヘルスチェックエンドポイント"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })
'''
            content += health_endpoint
            self.fixes_applied.append("✓ /health エンドポイント追加")

        # /ready エンドポイント追加
        if '@app.route("/ready")' not in content:
            ready_endpoint = '''

@app.route('/ready')
def readiness_check():
    """レディネスチェックエンドポイント"""
    try:
        # データベース接続確認
        db = get_db()
        db.execute('SELECT 1').fetchone()
        return jsonify({
            'status': 'ready',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'not ready',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 503
'''
            content += ready_endpoint
            self.fixes_applied.append("✓ /ready エンドポイント追加")

        # /metrics エンドポイント追加
        if '@app.route("/metrics")' not in content:
            metrics_endpoint = '''

@app.route('/metrics')
def metrics():
    """メトリクスエンドポイント"""
    db = get_db()

    # 基本統計
    stats = {
        'works_total': db.execute('SELECT COUNT(*) FROM works').fetchone()[0],
        'releases_total': db.execute('SELECT COUNT(*) FROM releases').fetchone()[0],
        'users_total': db.execute('SELECT COUNT(*) FROM users').fetchone()[0],
        'api_keys_total': db.execute('SELECT COUNT(*) FROM api_keys').fetchone()[0],
        'timestamp': datetime.now().isoformat()
    }

    # Prometheus形式
    prometheus_format = f"""# TYPE works_total counter
works_total {stats['works_total']}
# TYPE releases_total counter
releases_total {stats['releases_total']}
# TYPE users_total counter
users_total {stats['users_total']}
# TYPE api_keys_total counter
api_keys_total {stats['api_keys_total']}
"""

    return prometheus_format, 200, {'Content-Type': 'text/plain; charset=utf-8'}
'''
            content += metrics_endpoint
            self.fixes_applied.append("✓ /metrics エンドポイント追加")

        # /api/collection-status エンドポイント追加
        if '@app.route("/api/collection-status")' not in content:
            collection_status_endpoint = '''

@app.route('/api/collection-status')
def api_collection_status():
    """コレクション状態API"""
    db = get_db()

    # ステータス別集計
    status_counts = {}
    rows = db.execute('''
        SELECT status, COUNT(*) as count
        FROM collection
        GROUP BY status
    ''').fetchall()

    for row in rows:
        status_counts[row['status']] = row['count']

    return jsonify({
        'total': sum(status_counts.values()),
        'by_status': status_counts,
        'timestamp': datetime.now().isoformat()
    })
'''
            content += collection_status_endpoint
            self.fixes_applied.append("✓ /api/collection-status エンドポイント追加")

        # 保存
        web_app_path.write_text(content, encoding='utf-8')
        print(f"  ✓ web_app.py更新完了")

    def fix_template_errors(self):
        """テンプレートエラー修正"""
        templates_dir = project_root / 'app' / 'templates'

        if not templates_dir.exists():
            print(f"❌ テンプレートディレクトリが見つかりません: {templates_dir}")
            return

        # base.htmlチェック
        base_template = templates_dir / 'base.html'
        if not base_template.exists():
            # base.html作成
            base_content = '''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}MangaAnime Info Delivery{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    {% block extra_css %}{% endblock %}
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="{{ url_for('index') }}">MangaAnime Info</a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav">
                    <li class="nav-item"><a class="nav-link" href="{{ url_for('index') }}">ホーム</a></li>
                    <li class="nav-item"><a class="nav-link" href="{{ url_for('releases') }}">リリース</a></li>
                    <li class="nav-item"><a class="nav-link" href="{{ url_for('calendar') }}">カレンダー</a></li>
                    <li class="nav-item"><a class="nav-link" href="{{ url_for('watchlist') }}">ウォッチリスト</a></li>
                </ul>
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item"><a class="nav-link" href="{{ url_for('auth_login') }}">ログイン</a></li>
                </ul>
            </div>
        </div>
    </nav>

    <main class="container mt-4">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }} alert-dismissible fade show" role="alert">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        {% block content %}{% endblock %}
    </main>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    {% block extra_js %}{% endblock %}
</body>
</html>
'''
            base_template.write_text(base_content, encoding='utf-8')
            self.fixes_applied.append("✓ base.html作成")

        # auth/login.htmlチェック
        auth_dir = templates_dir / 'auth'
        auth_dir.mkdir(exist_ok=True)

        login_template = auth_dir / 'login.html'
        if not login_template.exists():
            login_content = '''{% extends "base.html" %}

{% block title %}ログイン - MangaAnime Info Delivery{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header">
                <h4>ログイン</h4>
            </div>
            <div class="card-body">
                <form method="POST" action="{{ url_for('auth_login') }}">
                    <div class="mb-3">
                        <label for="username" class="form-label">ユーザー名</label>
                        <input type="text" class="form-control" id="username" name="username" required>
                    </div>
                    <div class="mb-3">
                        <label for="password" class="form-label">パスワード</label>
                        <input type="password" class="form-control" id="password" name="password" required>
                    </div>
                    <button type="submit" class="btn btn-primary">ログイン</button>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
'''
            login_template.write_text(login_content, encoding='utf-8')
            self.fixes_applied.append("✓ auth/login.html作成")

    def verify_database_schema(self):
        """データベーススキーマ確認"""
        import sqlite3

        db_path = project_root / 'db.sqlite3'

        if not db_path.exists():
            print(f"  ℹ データベースファイルが存在しません（初回起動時に作成されます）")
            return

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # テーブル一覧取得
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            print(f"  ✓ 既存テーブル: {', '.join(tables)}")

            conn.close()

        except Exception as e:
            print(f"  ❌ データベースエラー: {e}")

    def fix_routing_errors(self):
        """ルーティングエラー修正"""
        # url_for()のエンドポイント名チェック
        routes_init = project_root / 'app' / 'routes' / '__init__.py'

        if not routes_init.exists():
            # routes/__init__.py作成
            routes_dir = project_root / 'app' / 'routes'
            routes_dir.mkdir(parents=True, exist_ok=True)

            init_content = '''"""
Routes package
すべてのルート定義をここで管理
"""

from . import auth
from . import api
from . import admin

__all__ = ['auth', 'api', 'admin']
'''
            routes_init.write_text(init_content, encoding='utf-8')
            self.fixes_applied.append("✓ routes/__init__.py作成")

    def print_report(self):
        """レポート出力"""
        print("\n" + "=" * 80)
        print("📊 修復結果")
        print("=" * 80)

        if len(self.fixes_applied) > 0:
            print(f"\n✅ 適用された修正: {len(self.fixes_applied)}件")
            for fix in self.fixes_applied:
                print(f"  {fix}")
        else:
            print("\nℹ️  修正が必要な項目は見つかりませんでした")

        print("\n" + "=" * 80)


def main():
    """メイン実行"""
    fixer = E2EErrorFixer()
    fixer.fix_all()


if __name__ == '__main__':
    main()
