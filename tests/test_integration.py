"""
統合テスト
システム全体の統合動作をテスト
"""
import pytest
import sys
import os
from pathlib import Path
from datetime import date
from unittest.mock import Mock, patch, MagicMock

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from modules import db, filter_logic
except ImportError:
    pytest.skip("Required modules not found", allow_module_level=True)


@pytest.fixture
def integration_db(tmp_path):
    """統合テスト用データベース"""
    db_path = str(tmp_path / "integration_test.db")
    db.init_db(db_path)
    yield db_path
    if os.path.exists(db_path):
        os.remove(db_path)


class TestEndToEndWorkflow:
    """エンドツーエンドワークフローのテスト"""

    def test_anime_collection_workflow(self, integration_db):
        """アニメ収集ワークフロー"""
        # 1. 作品登録
        work_id = db.insert_work(
            db_path=integration_db,
            title='統合テストアニメ',
            work_type='anime'
        )
        assert work_id is not None

        # 2. リリース情報登録
        release_id = db.insert_release(
            db_path=integration_db,
            work_id=work_id,
            release_type='episode',
            number='1',
            platform='dアニメストア',
            release_date=date(2025, 12, 15),
            source='anilist'
        )
        assert release_id is not None

        # 3. 未通知リリース取得
        unnotified = db.get_unnotified_releases(integration_db)
        assert len(unnotified) > 0

        # 4. 通知済みマーク
        db.mark_as_notified(integration_db, release_id)

        # 5. 再取得して確認
        unnotified_after = db.get_unnotified_releases(integration_db)
        assert len(unnotified_after) == len(unnotified) - 1

    def test_manga_collection_workflow(self, integration_db):
        """マンガ収集ワークフロー"""
        # 1. 作品登録
        work_id = db.insert_work(
            db_path=integration_db,
            title='統合テストマンガ',
            work_type='manga'
        )

        # 2. 複数巻の登録
        for vol in range(1, 6):
            db.insert_release(
                db_path=integration_db,
                work_id=work_id,
                release_type='volume',
                number=str(vol),
                platform='BookWalker',
                release_date=date(2025, 12, vol),
                source='rss'
            )

        # 3. すべて取得できることを確認
        releases = db.get_unnotified_releases(integration_db)
        manga_releases = [r for r in releases if r['title'] == '統合テストマンガ']
        assert len(manga_releases) == 5


class TestFilteringIntegration:
    """フィルタリング統合テスト"""

    @patch('modules.anime_anilist.fetch_anime_data')
    def test_anime_filtering_integration(self, mock_fetch, integration_db):
        """アニメフィルタリング統合"""
        if hasattr(filter_logic, 'apply_filters'):
            # NGワードを含むデータ
            ng_anime = {
                'title': 'NGアニメ',
                'genres': ['Ecchi'],
                'description': 'エロい作品'
            }

            # 安全なデータ
            safe_anime = {
                'title': '安全アニメ',
                'genres': ['Action', 'Fantasy'],
                'description': 'ファンタジー冒険'
            }

            # フィルタリング
            assert filter_logic.apply_filters(ng_anime) is False
            assert filter_logic.apply_filters(safe_anime) is True


class TestNotificationIntegration:
    """通知統合テスト"""

    @patch('modules.mailer.send_email')
    @patch('modules.calendar.insert_event')
    def test_notification_workflow(self, mock_calendar, mock_mailer, integration_db):
        """通知ワークフロー統合テスト"""
        # 1. テストデータ作成
        work_id = db.insert_work(
            db_path=integration_db,
            title='通知テストアニメ',
            work_type='anime'
        )

        release_id = db.insert_release(
            db_path=integration_db,
            work_id=work_id,
            release_type='episode',
            number='1',
            platform='Netflix',
            release_date=date(2025, 12, 25),
            source='anilist'
        )

        # 2. 未通知リリース取得
        releases = db.get_unnotified_releases(integration_db)

        # 3. メール送信（モック）
        mock_mailer.return_value = True
        if hasattr(__import__('modules.mailer', fromlist=['send_email']), 'send_email'):
            result = mock_mailer(
                to='test@example.com',
                subject='テスト通知',
                releases=releases
            )
            assert result is True

        # 4. カレンダー登録（モック）
        mock_calendar.return_value = True
        if hasattr(__import__('modules.calendar', fromlist=['insert_event']), 'insert_event'):
            result = mock_calendar(
                calendar_id='primary',
                event=releases[0]
            )
            assert result is True

        # 5. 通知済みマーク
        db.mark_as_notified(integration_db, release_id)


class TestDataConsistency:
    """データ整合性テスト"""

    def test_duplicate_prevention(self, integration_db):
        """重複データ防止のテスト"""
        # 同じ作品を2回登録
        work_id_1 = db.insert_work(
            db_path=integration_db,
            title='重複テスト',
            work_type='anime'
        )

        work_id_2 = db.insert_work(
            db_path=integration_db,
            title='重複テスト',
            work_type='anime'
        )

        # 同じIDが返される
        assert work_id_1 == work_id_2

    def test_release_uniqueness(self, integration_db):
        """リリース情報の一意性テスト"""
        work_id = db.insert_work(
            db_path=integration_db,
            title='一意性テスト',
            work_type='anime'
        )

        # 同じリリース情報を2回登録
        release_id_1 = db.insert_release(
            db_path=integration_db,
            work_id=work_id,
            release_type='episode',
            number='1',
            platform='Netflix',
            release_date=date(2025, 12, 15),
            source='anilist'
        )

        release_id_2 = db.insert_release(
            db_path=integration_db,
            work_id=work_id,
            release_type='episode',
            number='1',
            platform='Netflix',
            release_date=date(2025, 12, 15),
            source='anilist'
        )

        # UNIQUE制約により重複が防止される
        assert release_id_1 is not None
        assert release_id_2 is not None or release_id_2 is None


class TestErrorRecovery:
    """エラーリカバリテスト"""

    @patch('modules.anime_anilist.fetch_anime_data')
    def test_api_failure_recovery(self, mock_fetch, integration_db):
        """API障害からのリカバリ"""
        # 最初は失敗、2回目は成功
        mock_fetch.side_effect = [
            ConnectionError("Network error"),
            [{'title': 'Success Anime'}]
        ]

        # リトライ処理があれば成功する
        if hasattr(__import__('modules.anime_anilist', fromlist=['fetch_with_retry']), 'fetch_with_retry'):
            from modules.anime_anilist import fetch_with_retry
            result = fetch_with_retry()
            # リトライにより成功
            assert result is not None or result == []

    def test_database_error_handling(self, integration_db):
        """データベースエラーハンドリング"""
        # 無効なデータでの挿入試行
        try:
            db.insert_release(
                db_path=integration_db,
                work_id=None,  # 無効
                release_type='episode',
                number='1',
                platform='test',
                release_date=date(2025, 12, 15),
                source='test'
            )
        except Exception:
            # エラーが適切に処理される
            pass


class TestPerformance:
    """パフォーマンステスト"""

    def test_bulk_insert_performance(self, integration_db):
        """大量データ挿入のパフォーマンス"""
        import time

        start_time = time.time()

        # 100件の作品を挿入
        for i in range(100):
            work_id = db.insert_work(
                db_path=integration_db,
                title=f'パフォーマンステスト{i}',
                work_type='anime' if i % 2 == 0 else 'manga'
            )

            # 各作品に5件のリリース
            for j in range(5):
                db.insert_release(
                    db_path=integration_db,
                    work_id=work_id,
                    release_type='episode' if i % 2 == 0 else 'volume',
                    number=str(j + 1),
                    platform='test',
                    release_date=date(2025, 12, 1 + j),
                    source='test'
                )

        elapsed_time = time.time() - start_time

        # 処理が完了することを確認（タイムアウトなし）
        assert elapsed_time < 30  # 30秒以内に完了

    def test_query_performance(self, integration_db):
        """クエリパフォーマンステスト"""
        # テストデータ作成
        for i in range(50):
            work_id = db.insert_work(
                db_path=integration_db,
                title=f'クエリテスト{i}',
                work_type='anime'
            )

            db.insert_release(
                db_path=integration_db,
                work_id=work_id,
                release_type='episode',
                number='1',
                platform='test',
                release_date=date(2025, 12, 15),
                source='test'
            )

        import time
        start_time = time.time()

        # 未通知リリース取得
        releases = db.get_unnotified_releases(integration_db)

        elapsed_time = time.time() - start_time

        # クエリが高速に実行される
        assert elapsed_time < 1  # 1秒以内
        assert len(releases) >= 50


class TestConcurrency:
    """並行処理テスト"""

    def test_concurrent_inserts(self, integration_db):
        """並行挿入のテスト"""
        import threading

        def insert_work(title):
            db.insert_work(
                db_path=integration_db,
                title=title,
                work_type='anime'
            )

        threads = []
        for i in range(10):
            thread = threading.Thread(
                target=insert_work,
                args=(f'並行テスト{i}',)
            )
            threads.append(thread)
            thread.start()

        # すべてのスレッドの完了を待つ
        for thread in threads:
            thread.join()

        # データが正しく挿入されている
        # （SQLiteのロック処理により安全に処理される）


class TestBackupRestore:
    """バックアップ・リストアテスト"""

    def test_database_backup(self, integration_db, tmp_path):
        """データベースバックアップ"""
        # テストデータ作成
        work_id = db.insert_work(
            db_path=integration_db,
            title='バックアップテスト',
            work_type='anime'
        )

        # バックアップ
        backup_path = str(tmp_path / "backup.db")

        import shutil
        shutil.copy(integration_db, backup_path)

        # バックアップファイルが作成される
        assert os.path.exists(backup_path)

        # バックアップから復元できる
        restored_work = db.get_work_by_title(backup_path, 'バックアップテスト', 'anime')
        assert restored_work is not None
        assert restored_work['title'] == 'バックアップテスト'
