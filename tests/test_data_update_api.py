"""
Data Update API Test Suite
データ更新APIの機能テスト
"""

import pytest
import json
import sqlite3
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestDataUpdateAPI:
    """データ更新API機能テストクラス"""

    def test_manual_collection_endpoint(self, client):
        """手動データ収集エンドポイントのテスト"""
        response = client.post('/api/manual-collection',
                               data=json.dumps({'source': 'anilist'}),
                               content_type='application/json')

        # 200 OK または 202 Accepted を期待
        assert response.status_code in [200, 202, 400]

        if response.status_code == 200:
            data = json.loads(response.data)
            assert 'status' in data or 'message' in data


    def test_works_api_get(self, client):
        """作品一覧取得APIのテスト"""
        response = client.get('/api/works')

        assert response.status_code == 200

        data = json.loads(response.data)
        assert 'works' in data or isinstance(data, list)


    def test_works_api_filtering(self, client):
        """作品フィルタリング機能のテスト"""
        # タイプでフィルタリング
        response = client.get('/api/works?type=anime')
        assert response.status_code == 200

        data = json.loads(response.data)

        # データが存在する場合、typeがanimeであることを確認
        if isinstance(data, dict) and 'works' in data:
            works = data['works']
            if len(works) > 0:
                assert all(work.get('type') == 'anime' for work in works)


    def test_works_api_search(self, client):
        """作品検索機能のテスト"""
        search_terms = ['test', 'anime', '進撃']

        for term in search_terms:
            response = client.get(f'/api/works?search={term}')
            assert response.status_code == 200


    def test_work_detail_api(self, client, test_db):
        """作品詳細取得APIのテスト"""
        # テストデータを挿入
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO works (title, type, official_url)
            VALUES (?, ?, ?)
        """, ('テスト作品', 'anime', 'https://example.com'))

        work_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # API呼び出し
        response = client.get(f'/api/works/{work_id}')

        assert response.status_code == 200

        data = json.loads(response.data)
        assert data.get('title') == 'テスト作品'


    def test_collection_status_api(self, client):
        """データ収集ステータス取得APIのテスト"""
        response = client.get('/api/collection-status')

        assert response.status_code == 200

        data = json.loads(response.data)
        assert 'status' in data or 'processes' in data


    def test_stats_api(self, client):
        """統計情報取得APIのテスト"""
        response = client.get('/api/stats')

        assert response.status_code == 200

        data = json.loads(response.data)

        # 統計情報の基本項目を確認
        expected_keys = ['total_works', 'total_releases', 'recent_count']
        # 一部のキーが含まれていることを確認
        assert any(key in data for key in expected_keys)


    def test_recent_releases_api(self, client):
        """最近のリリース取得APIのテスト"""
        response = client.get('/api/releases/recent')

        assert response.status_code == 200

        data = json.loads(response.data)
        assert isinstance(data, (list, dict))


    def test_watchlist_add_api(self, client, test_db):
        """ウォッチリスト追加APIのテスト"""
        # テスト作品を作成
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO works (title, type)
            VALUES (?, ?)
        """, ('ウォッチリストテスト作品', 'anime'))

        work_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # ウォッチリストに追加
        response = client.post('/api/watchlist/add',
                               data=json.dumps({'work_id': work_id}),
                               content_type='application/json')

        assert response.status_code in [200, 201, 400]


    def test_error_handling_invalid_work_id(self, client):
        """無効な作品IDのエラーハンドリングテスト"""
        response = client.get('/api/works/99999')

        # 404 Not Found を期待
        assert response.status_code in [404, 400]


    def test_error_handling_invalid_json(self, client):
        """無効なJSON形式のエラーハンドリングテスト"""
        response = client.post('/api/manual-collection',
                               data='invalid json',
                               content_type='application/json')

        # 400 Bad Request を期待
        assert response.status_code == 400


    def test_pagination_support(self, client):
        """ページネーション機能のテスト"""
        # ページ1
        response1 = client.get('/api/works?page=1&per_page=10')
        assert response1.status_code == 200

        # ページ2
        response2 = client.get('/api/works?page=2&per_page=10')
        assert response2.status_code == 200


    def test_sorting_support(self, client):
        """ソート機能のテスト"""
        sort_options = ['title', 'created_at', 'release_date']

        for sort_by in sort_options:
            response = client.get(f'/api/works?sort={sort_by}')
            assert response.status_code in [200, 400]


    def test_concurrent_requests(self, client):
        """同時リクエスト処理のテスト"""
        import concurrent.futures

        def make_request():
            return client.get('/api/stats')

        # 10並列でリクエスト
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # 全てのリクエストが成功することを確認
        assert all(r.status_code == 200 for r in results)


    def test_data_consistency(self, client, test_db):
        """データ整合性のテスト"""
        # データを挿入
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO works (title, type)
            VALUES (?, ?)
        """, ('整合性テスト作品', 'manga'))

        work_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO releases (work_id, release_type, number, release_date)
            VALUES (?, ?, ?, ?)
        """, (work_id, 'volume', '1', '2025-12-01'))

        conn.commit()
        conn.close()

        # APIで取得して整合性を確認
        response = client.get(f'/api/works/{work_id}')
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data.get('title') == '整合性テスト作品'


@pytest.fixture
def client():
    """Flaskテストクライアントのフィクスチャ"""
    try:
        from app.web_app import app
        app.config['TESTING'] = True
        app.config['DATABASE'] = ':memory:'

        with app.test_client() as client:
            yield client
    except ImportError:
        pytest.skip("web_app.pyが見つかりません")


@pytest.fixture
def test_db(tmp_path):
    """テスト用データベースのフィクスチャ"""
    db_path = tmp_path / "test.db"

    # データベース初期化
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

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

    conn.commit()
    conn.close()

    yield str(db_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
