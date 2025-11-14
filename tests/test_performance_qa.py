"""
Performance QA Test Suite
パフォーマンス品質保証テスト
"""

import pytest
import time
import json
import sqlite3
import sys
import concurrent.futures
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestPerformanceQA:
    """パフォーマンス品質保証テストクラス"""

    def test_api_response_time_stats(self, client):
        """統計APIのレスポンスタイムテスト"""
        start_time = time.time()
        response = client.get('/api/stats')
        end_time = time.time()

        elapsed = end_time - start_time

        assert response.status_code == 200
        assert elapsed < 2.0, f"レスポンスタイムが遅い: {elapsed:.2f}秒"


    def test_api_response_time_works(self, client):
        """作品一覧APIのレスポンスタイムテスト"""
        start_time = time.time()
        response = client.get('/api/works')
        end_time = time.time()

        elapsed = end_time - start_time

        assert response.status_code == 200
        assert elapsed < 3.0, f"レスポンスタイムが遅い: {elapsed:.2f}秒"


    def test_api_response_time_recent_releases(self, client):
        """最近のリリースAPIのレスポンスタイムテスト"""
        start_time = time.time()
        response = client.get('/api/releases/recent')
        end_time = time.time()

        elapsed = end_time - start_time

        assert response.status_code == 200
        assert elapsed < 2.0, f"レスポンスタイムが遅い: {elapsed:.2f}秒"


    def test_database_query_performance(self, test_db):
        """データベースクエリのパフォーマンステスト"""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        # 大量のデータを挿入
        start_time = time.time()

        for i in range(1000):
            cursor.execute("""
                INSERT INTO works (title, type)
                VALUES (?, ?)
            """, (f'テスト作品{i}', 'anime'))

        conn.commit()
        insert_time = time.time() - start_time

        # 検索クエリのパフォーマンス
        start_time = time.time()
        cursor.execute("SELECT * FROM works WHERE type = 'anime'")
        results = cursor.fetchall()
        query_time = time.time() - start_time

        conn.close()

        assert insert_time < 10.0, f"挿入が遅い: {insert_time:.2f}秒"
        assert query_time < 1.0, f"検索が遅い: {query_time:.2f}秒"
        assert len(results) == 1000


    def test_concurrent_api_requests(self, client):
        """並列APIリクエストのパフォーマンステスト"""
        def make_request():
            start = time.time()
            response = client.get('/api/stats')
            elapsed = time.time() - start
            return response.status_code, elapsed

        # 20並列でリクエスト
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request) for _ in range(20)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # 全てのリクエストが成功
        assert all(status == 200 for status, _ in results)

        # 平均レスポンスタイム
        avg_time = sum(elapsed for _, elapsed in results) / len(results)
        assert avg_time < 3.0, f"平均レスポンスタイムが遅い: {avg_time:.2f}秒"


    def test_large_dataset_pagination(self, client, test_db):
        """大量データのページネーションパフォーマンステスト"""
        # 大量データを挿入
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        for i in range(500):
            cursor.execute("""
                INSERT INTO works (title, type)
                VALUES (?, ?)
            """, (f'大量データテスト{i}', 'manga'))

        conn.commit()
        conn.close()

        # ページネーションのパフォーマンス
        start_time = time.time()
        response = client.get('/api/works?page=1&per_page=50')
        elapsed = time.time() - start_time

        assert response.status_code == 200
        assert elapsed < 2.0, f"ページネーションが遅い: {elapsed:.2f}秒"


    def test_search_performance(self, client, test_db):
        """検索機能のパフォーマンステスト"""
        # テストデータを挿入
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        for i in range(200):
            cursor.execute("""
                INSERT INTO works (title, type)
                VALUES (?, ?)
            """, (f'検索テスト作品{i}', 'anime'))

        conn.commit()
        conn.close()

        # 検索のパフォーマンス
        start_time = time.time()
        response = client.get('/api/works?search=検索テスト')
        elapsed = time.time() - start_time

        assert response.status_code == 200
        assert elapsed < 2.0, f"検索が遅い: {elapsed:.2f}秒"


    def test_data_update_performance(self, test_db):
        """データ更新のパフォーマンステスト"""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        # 既存データを挿入
        cursor.execute("""
            INSERT INTO works (title, type)
            VALUES (?, ?)
        """, ('更新テスト作品', 'anime'))

        work_id = cursor.lastrowid
        conn.commit()

        # 更新のパフォーマンス
        start_time = time.time()

        for i in range(100):
            cursor.execute("""
                UPDATE works
                SET title = ?
                WHERE id = ?
            """, (f'更新後のタイトル{i}', work_id))

        conn.commit()
        update_time = time.time() - start_time

        conn.close()

        assert update_time < 2.0, f"更新が遅い: {update_time:.2f}秒"


    def test_join_query_performance(self, test_db):
        """結合クエリのパフォーマンステスト"""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        # テストデータを挿入
        for i in range(100):
            cursor.execute("""
                INSERT INTO works (title, type)
                VALUES (?, ?)
            """, (f'結合テスト作品{i}', 'anime'))

            work_id = cursor.lastrowid

            # 各作品に3つのリリースを追加
            for j in range(3):
                cursor.execute("""
                    INSERT INTO releases (work_id, release_type, number, release_date)
                    VALUES (?, ?, ?, ?)
                """, (work_id, 'episode', str(j+1), '2025-12-01'))

        conn.commit()

        # 結合クエリのパフォーマンス
        start_time = time.time()

        cursor.execute("""
            SELECT w.*, r.release_type, r.number, r.release_date
            FROM works w
            LEFT JOIN releases r ON w.id = r.work_id
            WHERE w.type = 'anime'
        """)

        results = cursor.fetchall()
        query_time = time.time() - start_time

        conn.close()

        assert query_time < 1.0, f"結合クエリが遅い: {query_time:.2f}秒"
        assert len(results) == 300  # 100作品 × 3リリース


    def test_stress_concurrent_write(self, test_db):
        """並列書き込みストレステスト"""
        def insert_data(db_path, start_id):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            for i in range(10):
                cursor.execute("""
                    INSERT INTO works (title, type)
                    VALUES (?, ?)
                """, (f'並列テスト{start_id}_{i}', 'anime'))

            conn.commit()
            conn.close()

        # 10スレッドで並列書き込み
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(insert_data, test_db, i) for i in range(10)]
            concurrent.futures.wait(futures)

        # データが正しく挿入されたか確認
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM works")
        count = cursor.fetchone()[0]
        conn.close()

        assert count >= 100


    def test_index_usage(self, test_db):
        """データベースインデックス使用のテスト"""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        # インデックスを作成
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_works_type ON works(type)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_releases_work_id ON releases(work_id)
        """)

        conn.commit()

        # 大量データを挿入
        for i in range(1000):
            cursor.execute("""
                INSERT INTO works (title, type)
                VALUES (?, ?)
            """, (f'インデックステスト{i}', 'anime'))

        conn.commit()

        # インデックスを使用したクエリのパフォーマンス
        start_time = time.time()
        cursor.execute("SELECT * FROM works WHERE type = 'anime'")
        results = cursor.fetchall()
        query_time = time.time() - start_time

        conn.close()

        assert query_time < 0.5, f"インデックスが効いていない可能性: {query_time:.2f}秒"


    def test_batch_insert_performance(self, test_db):
        """バッチ挿入のパフォーマンステスト"""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()

        # バッチデータ準備
        batch_data = [(f'バッチテスト{i}', 'anime') for i in range(1000)]

        # バッチ挿入
        start_time = time.time()
        cursor.executemany("""
            INSERT INTO works (title, type)
            VALUES (?, ?)
        """, batch_data)
        conn.commit()
        batch_time = time.time() - start_time

        conn.close()

        assert batch_time < 5.0, f"バッチ挿入が遅い: {batch_time:.2f}秒"


@pytest.fixture
def client():
    """Flaskテストクライアントのフィクスチャ"""
    try:
        from app.web_app import app
        app.config['TESTING'] = True

        with app.test_client() as client:
            yield client
    except ImportError:
        pytest.skip("web_app.pyが見つかりません")


@pytest.fixture
def test_db(tmp_path):
    """テスト用データベースのフィクスチャ"""
    db_path = tmp_path / "performance_qa_test.db"

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
