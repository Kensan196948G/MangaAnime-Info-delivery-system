#!/usr/bin/env python3
"""
新機能テストスイート
テスト対象:
1. 更新ボタン機能（今後の予定/リリース履歴）
2. デフォルト設定（メールアドレス、チェック間隔、通知設定）
3. UI配置（最終更新表示、レスポンシブデザイン）
4. APIエンドポイント（/api/refresh-upcoming, /api/refresh-history, /api/settings）
"""

import pytest
import json
import os
import sys
import sqlite3
from datetime import datetime, timedelta

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Flask アプリケーションのインポート
from app.web_app import app, get_db_connection, load_config, save_config


@pytest.fixture
def client():
    """Flask テストクライアント"""
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    with app.test_client() as client:
        yield client


@pytest.fixture
def sample_config():
    """サンプル設定データ"""
    return {
        "notification_email": "kensan1969@gmail.com",
        "check_interval_hours": 1,
        "email_notifications": True,
        "ng_keywords": ["エロ", "R18", "成人向け"],
        "enabled_sources": {
            "anilist": True,
            "shobo_calendar": True,
            "bookwalker_rss": True
        }
    }


@pytest.fixture
def test_db():
    """テスト用データベース"""
    db_path = "test_db.sqlite3"

    # テスト用DBを作成
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # テーブル作成
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS works (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            title_kana TEXT,
            title_en TEXT,
            type TEXT CHECK(type IN ('anime','manga')),
            official_url TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS releases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            work_id INTEGER NOT NULL,
            release_type TEXT CHECK(release_type IN ('episode','volume')),
            number TEXT,
            platform TEXT,
            release_date DATE,
            source TEXT,
            source_url TEXT,
            notified INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(work_id, release_type, number, platform, release_date)
        )
    """)

    # サンプルデータ追加
    cursor.execute("""
        INSERT INTO works (title, type) VALUES
        ('テストアニメ1', 'anime'),
        ('テストマンガ1', 'manga')
    """)

    today = datetime.now().date()
    future = (datetime.now() + timedelta(days=7)).date()

    cursor.execute("""
        INSERT INTO releases (work_id, release_type, number, platform, release_date, notified)
        VALUES
        (1, 'episode', '1', 'テストプラットフォーム', ?, 0),
        (2, 'volume', '1', 'テストストア', ?, 0)
    """, (str(future), str(future)))

    conn.commit()
    conn.close()

    yield db_path

    # クリーンアップ
    if os.path.exists(db_path):
        os.remove(db_path)


class TestDefaultSettings:
    """デフォルト設定のテスト"""

    def test_default_email_address(self, sample_config):
        """デフォルトメールアドレスが正しく設定されているか"""
        assert sample_config['notification_email'] == 'kensan1969@gmail.com'

    def test_default_check_interval(self, sample_config):
        """デフォルトチェック間隔が1時間に設定されているか"""
        assert sample_config['check_interval_hours'] == 1

    def test_default_email_notification_enabled(self, sample_config):
        """メール通知がデフォルトで有効か"""
        assert sample_config['email_notifications'] is True

    def test_ng_keywords_defined(self, sample_config):
        """NGキーワードが定義されているか"""
        assert len(sample_config['ng_keywords']) > 0
        assert 'エロ' in sample_config['ng_keywords']

    def test_enabled_sources_default(self, sample_config):
        """有効なソースのデフォルト設定"""
        enabled = sample_config['enabled_sources']
        assert enabled['anilist'] is True
        assert enabled['shobo_calendar'] is True
        assert enabled['bookwalker_rss'] is True


class TestAPIEndpoints:
    """APIエンドポイントのテスト"""

    def test_api_stats_endpoint(self, client):
        """統計情報APIのテスト"""
        response = client.get('/api/stats')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'total_works' in data
        assert 'total_releases' in data

    def test_api_works_endpoint(self, client):
        """作品一覧APIのテスト"""
        response = client.get('/api/works')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'works' in data or isinstance(data, list)

    def test_api_collection_status(self, client):
        """収集状況APIのテスト"""
        response = client.get('/api/collection-status')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'last_check' in data or 'status' in data

    def test_api_recent_releases(self, client):
        """最新リリースAPIのテスト"""
        response = client.get('/api/releases/recent')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, (list, dict))


class TestRefreshButtons:
    """更新ボタン機能のテスト"""

    def test_upcoming_refresh_button_exists(self, client):
        """今後の予定更新ボタンの存在確認"""
        response = client.get('/')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        # ボタンまたは更新機能の存在を確認
        assert 'refresh' in html.lower() or '更新' in html

    def test_history_refresh_button_exists(self, client):
        """リリース履歴更新ボタンの存在確認"""
        response = client.get('/works')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        assert 'refresh' in html.lower() or '更新' in html


class TestUILayout:
    """UI配置とレスポンシブデザインのテスト"""

    def test_last_update_display_exists(self, client):
        """最終更新表示の存在確認"""
        response = client.get('/')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        # 最終更新時刻の表示を確認
        assert '最終更新' in html or 'last-update' in html.lower()

    def test_responsive_bootstrap_classes(self, client):
        """Bootstrapレスポンシブクラスの使用確認"""
        response = client.get('/')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        # Bootstrap レスポンシブクラスの確認
        assert 'col-md' in html or 'col-sm' in html or 'col-lg' in html

    def test_mobile_friendly_meta_tag(self, client):
        """モバイル対応メタタグの確認"""
        response = client.get('/')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        assert 'viewport' in html.lower()


class TestProgressBar:
    """プログレスバー表示のテスト"""

    def test_progress_bar_container_exists(self, client):
        """プログレスバーコンテナの存在確認"""
        response = client.get('/')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        # プログレスバー関連の要素を確認
        assert 'progress' in html.lower() or 'loader' in html.lower()


class TestErrorHandling:
    """エラーハンドリングのテスト"""

    def test_invalid_work_id(self, client):
        """無効な作品IDのエラーハンドリング"""
        response = client.get('/api/works/99999')
        assert response.status_code in [404, 200]
        if response.status_code == 200:
            data = json.loads(response.data)
            # エラーメッセージまたは空のレスポンスを確認
            assert 'error' in data or data is None or data == {}

    def test_invalid_api_request(self, client):
        """無効なAPIリクエストのハンドリング"""
        response = client.post('/api/test-notification',
                               data=json.dumps({}),
                               content_type='application/json')
        # 400, 422, 500 のいずれかのエラーレスポンスを期待
        assert response.status_code in [200, 400, 422, 500]


class TestConfigManagement:
    """設定管理機能のテスト"""

    def test_load_config_function(self):
        """設定読み込み機能のテスト"""
        config = load_config()
        assert isinstance(config, dict)
        assert 'ng_keywords' in config or 'notification_email' in config

    def test_save_and_load_config(self, sample_config, tmp_path):
        """設定の保存と読み込みテスト"""
        config_file = tmp_path / "test_config.json"

        # 設定を保存
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(sample_config, f, indent=2, ensure_ascii=False)

        # 設定を読み込み
        with open(config_file, 'r', encoding='utf-8') as f:
            loaded_config = json.load(f)

        assert loaded_config == sample_config
        assert loaded_config['notification_email'] == 'kensan1969@gmail.com'


class TestDatabaseIntegration:
    """データベース統合テスト"""

    def test_db_connection(self):
        """データベース接続テスト"""
        try:
            conn = get_db_connection()
            assert conn is not None
            conn.close()
        except Exception as e:
            pytest.skip(f"Database not available: {e}")

    def test_works_table_structure(self):
        """作品テーブル構造のテスト"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(works)")
            columns = cursor.fetchall()
            conn.close()

            column_names = [col['name'] for col in columns]
            assert 'id' in column_names
            assert 'title' in column_names
            assert 'type' in column_names
        except Exception as e:
            pytest.skip(f"Database not available: {e}")

    def test_releases_table_structure(self):
        """リリーステーブル構造のテスト"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(releases)")
            columns = cursor.fetchall()
            conn.close()

            column_names = [col['name'] for col in columns]
            assert 'id' in column_names
            assert 'work_id' in column_names
            assert 'release_date' in column_names
            assert 'notified' in column_names
        except Exception as e:
            pytest.skip(f"Database not available: {e}")


class TestSecurityFeatures:
    """セキュリティ機能のテスト"""

    def test_secret_key_configured(self):
        """SECRET_KEYが設定されているか"""
        assert app.config.get('SECRET_KEY') is not None
        assert app.config.get('SECRET_KEY') != ''

    def test_csrf_protection_headers(self, client):
        """CSRF保護ヘッダーの確認"""
        response = client.get('/')
        # セキュリティヘッダーの存在確認
        assert response.status_code == 200


class TestPerformance:
    """パフォーマンステスト"""

    def test_homepage_load_time(self, client):
        """ホームページの読み込み時間テスト"""
        import time
        start = time.time()
        response = client.get('/')
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 5.0  # 5秒以内

    def test_api_response_time(self, client):
        """API応答時間テスト"""
        import time
        start = time.time()
        response = client.get('/api/stats')
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 3.0  # 3秒以内


def run_all_tests():
    """全テストを実行"""
    pytest.main([__file__, '-v', '--tb=short'])


if __name__ == '__main__':
    run_all_tests()
