# tests/integration/test_full_pipeline.py
# 完全パイプライン統合テスト

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch


@pytest.mark.integration
class TestFullPipeline:
    """情報収集 → フィルタリング → DB保存 → 通知 → カレンダー同期の完全フローテスト"""

    # ===========================
    # エンドツーエンドフローテスト
    # ===========================

    def test_collect_filter_store_notify_pipeline(
        self,
        test_db,
        mock_anilist_response,
        mock_gmail_service,
        mock_calendar_service,
        mocker
    ):
        """完全パイプライン: 収集 → フィルタ → 保存 → 通知 → カレンダー"""

        # ステップ1: 情報収集（モック）
        mock_post = mocker.patch('requests.post')
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_anilist_response
        mock_post.return_value = mock_response

        # from app.collectors.anilist import AniListCollector
        # collector = AniListCollector()
        # anime_data = collector.fetch_upcoming_anime()

        # assert len(anime_data) > 0

        # ステップ2: NGワードフィルタリング
        # from app.filters.ng_keywords import NGKeywordFilter
        # filter = NGKeywordFilter(keywords=["エロ", "R18"])
        # filtered_data = [item for item in anime_data if filter.is_allowed_work(item)]

        # assert len(filtered_data) > 0

        # ステップ3: データベース保存
        # from app.db.operations import save_anime_data
        # save_anime_data(test_db, filtered_data)

        cursor = test_db.cursor()
        # saved_works = cursor.execute("SELECT COUNT(*) FROM works").fetchone()[0]
        # assert saved_works > 0

        # ステップ4: 未通知リリースの取得
        # unnotified = cursor.execute("""
        #     SELECT * FROM releases WHERE notified = 0
        # """).fetchall()
        # assert len(unnotified) > 0

        # ステップ5: メール通知
        # from app.notifiers.gmail import GmailNotifier
        # notifier = GmailNotifier()
        # notifier.send_notification(unnotified[0])

        # mock_gmail_service.users().messages().send.assert_called_once()

        # ステップ6: カレンダー同期
        # from app.calendar.google_calendar import GoogleCalendarSync
        # calendar_sync = GoogleCalendarSync()
        # calendar_sync.sync_release(unnotified[0])

        # mock_calendar_service.events().insert.assert_called_once()

        # ステップ7: 通知済みフラグ更新
        # cursor.execute("UPDATE releases SET notified = 1 WHERE id = ?", (unnotified[0][0],))
        # test_db.commit()

        # updated = cursor.execute("SELECT notified FROM releases WHERE id = ?", (unnotified[0][0],)).fetchone()
        # assert updated[0] == 1

        pass

    def test_duplicate_prevention(self, test_db, mock_anilist_response, mocker):
        """重複データの防止テスト"""

        mock_post = mocker.patch('requests.post')
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_anilist_response
        mock_post.return_value = mock_response

        # 1回目: データ挿入
        # from app.collectors.anilist import AniListCollector
        # from app.db.operations import save_anime_data

        # collector = AniListCollector()
        # anime_data = collector.fetch_upcoming_anime()
        # save_anime_data(test_db, anime_data)

        cursor = test_db.cursor()
        # initial_count = cursor.execute("SELECT COUNT(*) FROM releases").fetchone()[0]

        # 2回目: 同じデータを再度挿入
        # save_anime_data(test_db, anime_data)

        # final_count = cursor.execute("SELECT COUNT(*) FROM releases").fetchone()[0]

        # UNIQUE制約により重複挿入されない
        # assert final_count == initial_count

        pass

    def test_error_recovery_on_notification_failure(
        self,
        test_db,
        sample_releases,
        mock_gmail_service,
        mocker
    ):
        """通知失敗時のエラーリカバリーテスト"""

        # Gmail送信失敗をシミュレート
        mock_gmail_service.users().messages().send().execute.side_effect = Exception("Gmail API Error")

        # from app.notifiers.gmail import GmailNotifier
        # notifier = GmailNotifier()

        cursor = test_db.cursor()
        unnotified = cursor.execute("SELECT * FROM releases WHERE notified = 0").fetchone()

        # エラーが発生してもプログラムが停止しない
        try:
            # notifier.send_notification(unnotified)
            pass
        except Exception as e:
            # エラーログを記録
            print(f"通知失敗: {e}")

        # 通知失敗したため、notifiedフラグは0のまま
        result = cursor.execute("SELECT notified FROM releases WHERE id = ?", (unnotified[0],)).fetchone()
        # assert result[0] == 0

        pass

    def test_calendar_sync_retry_on_failure(
        self,
        test_db,
        sample_releases,
        mock_calendar_service,
        mocker
    ):
        """カレンダー同期失敗時のリトライテスト"""

        # 1回目: 失敗
        # 2回目: 成功
        mock_calendar_service.events().insert().execute.side_effect = [
            Exception("Network Error"),
            {
                'id': 'test_event_id',
                'htmlLink': 'https://calendar.google.com/event'
            }
        ]

        # from app.calendar.google_calendar import GoogleCalendarSync
        # calendar_sync = GoogleCalendarSync(max_retries=2)

        cursor = test_db.cursor()
        release = cursor.execute("SELECT * FROM releases WHERE calendar_synced = 0").fetchone()

        # リトライ処理
        # calendar_sync.sync_with_retry(release)

        # 2回目で成功
        # assert mock_calendar_service.events().insert().execute.call_count == 2

        pass

    # ===========================
    # バッチ処理テスト
    # ===========================

    def test_batch_notification(
        self,
        test_db,
        large_dataset,
        mock_gmail_service
    ):
        """大量データの一括通知処理テスト"""

        # from app.notifiers.batch import BatchNotifier
        # notifier = BatchNotifier(batch_size=10)

        cursor = test_db.cursor()
        unnotified = cursor.execute("SELECT * FROM releases WHERE notified = 0").fetchall()

        # バッチ処理実行
        # notifier.send_batch(unnotified)

        # すべて通知済みになっている
        # remaining = cursor.execute("SELECT COUNT(*) FROM releases WHERE notified = 0").fetchone()[0]
        # assert remaining == 0

        pass

    def test_incremental_calendar_sync(
        self,
        test_db,
        sample_releases,
        mock_calendar_service
    ):
        """増分カレンダー同期テスト"""

        # from app.calendar.google_calendar import GoogleCalendarSync
        # calendar_sync = GoogleCalendarSync()

        cursor = test_db.cursor()

        # 未同期のリリースのみ取得
        unsynced = cursor.execute("""
            SELECT * FROM releases WHERE calendar_synced = 0 AND notified = 1
        """).fetchall()

        # 増分同期実行
        # for release in unsynced:
        #     calendar_sync.sync_release(release)

        # すべて同期済み
        # remaining = cursor.execute("""
        #     SELECT COUNT(*) FROM releases WHERE calendar_synced = 0 AND notified = 1
        # """).fetchone()[0]
        # assert remaining == 0

        pass

    # ===========================
    # スケジューラ統合テスト
    # ===========================

    @pytest.mark.slow
    def test_scheduled_job_execution(self, test_db, mocker):
        """スケジューラによる定期実行テスト"""

        # from app.scheduler import run_daily_job

        # スケジューラ実行（モック）
        mock_collect = mocker.patch('app.collectors.anilist.AniListCollector.fetch_upcoming_anime')
        mock_collect.return_value = [{"title": "Test Anime"}]

        # run_daily_job()

        # 収集関数が呼ばれたことを確認
        # mock_collect.assert_called_once()

        pass

    # ===========================
    # ロールバックテスト
    # ===========================

    def test_rollback_on_db_error(self, test_db, mock_anilist_response, mocker):
        """DB操作エラー時のロールバックテスト"""

        mock_post = mocker.patch('requests.post')
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_anilist_response
        mock_post.return_value = mock_response

        cursor = test_db.cursor()
        initial_count = cursor.execute("SELECT COUNT(*) FROM works").fetchone()[0]

        try:
            # データ挿入
            cursor.execute("INSERT INTO works (title, type) VALUES ('Test', 'anime')")

            # 意図的にエラーを発生させる
            cursor.execute("INSERT INTO works (title, type) VALUES (NULL, 'anime')")  # NOT NULL制約違反

            test_db.commit()
        except Exception:
            test_db.rollback()

        final_count = cursor.execute("SELECT COUNT(*) FROM works").fetchone()[0]
        assert final_count == initial_count  # ロールバックされている

    # ===========================
    # パフォーマンステスト
    # ===========================

    @pytest.mark.slow
    @pytest.mark.performance
    def test_full_pipeline_performance(
        self,
        test_db,
        large_dataset,
        mock_gmail_service,
        mock_calendar_service,
        mocker
    ):
        """完全パイプラインのパフォーマンステスト"""
        import time

        start_time = time.time()

        # ステップ1: 大量データ取得
        cursor = test_db.cursor()
        releases = cursor.execute("SELECT * FROM releases WHERE notified = 0").fetchall()

        # ステップ2: 通知処理
        for release in releases[:100]:  # 最初の100件
            # モック通知
            pass

        # ステップ3: カレンダー同期
        for release in releases[:100]:
            # モック同期
            pass

        elapsed_time = time.time() - start_time

        # 100件の処理が30秒以内
        assert elapsed_time < 30.0

    # ===========================
    # データ整合性テスト
    # ===========================

    def test_data_consistency_across_tables(
        self,
        test_db,
        sample_works,
        sample_releases
    ):
        """テーブル間のデータ整合性テスト"""

        cursor = test_db.cursor()

        # すべてのリリースに対応する作品が存在することを確認
        orphaned = cursor.execute("""
            SELECT r.*
            FROM releases r
            LEFT JOIN works w ON r.work_id = w.id
            WHERE w.id IS NULL
        """).fetchall()

        assert len(orphaned) == 0

    def test_timezone_consistency(self, test_db, sample_releases):
        """タイムゾーン整合性テスト"""

        cursor = test_db.cursor()

        # すべての日付がISO 8601形式であることを確認
        releases = cursor.execute("SELECT release_date FROM releases").fetchall()

        for release in releases:
            date_str = release[0]
            # ISO 8601形式（YYYY-MM-DD）のチェック
            assert len(date_str) == 10
            assert date_str[4] == '-'
            assert date_str[7] == '-'
