# Googleカレンダー統合設計書

**バージョン**: 1.0
**作成日**: 2025-12-07
**ステータス**: 設計フェーズ

---

## 1. 概要

このドキュメントは、Googleカレンダー統合機能の実装設計を定義しています。アニメ・マンガのリリース情報をGoogleカレンダーに自動登録し、ユーザーのスケジュール管理を支援します。

### 1.1 目的
- リリース情報をカレンダーイベントとして自動作成
- ユーザーのGoogleカレンダーに統合
- 更新・削除時の同期管理
- 同期状態の追跡とエラーハンドリング

### 1.2 スコープ
```
In Scope:
  - 新規リリースの自動カレンダー登録
  - リリース情報更新時のカレンダー更新
  - キャンセル/削除されたリリースの処理
  - 同期状態の記録と監視
  - リトライロジックとエラーハンドリング

Out of Scope:
  - ユーザーが手動で追加したイベントの管理
  - カレンダーの権限管理
  - マルチアカウント対応（将来実装）
```

---

## 2. システムアーキテクチャ

### 2.1 データベーススキーマ

#### releases テーブルへの追加カラム
```sql
calendar_synced INTEGER DEFAULT 0          -- 0: 未同期, 1: 同期済み
calendar_event_id TEXT                     -- Google Calendar Event ID
calendar_synced_at DATETIME                -- 同期実行日時
```

#### calendar_sync_log テーブル
同期操作の完全な監査証跡を記録
```
columns:
  - id: プライマリキー
  - release_id: リリースID（外部キー）
  - work_id: 作品ID（外部キー）
  - google_event_id: GoogleイベントID
  - sync_status: pending|synced|failed|updated|deleted
  - sync_type: create|update|delete
  - error_message: エラー詳細
  - retry_count: リトライ回数
  - max_retries: 最大リトライ回数
  - synced_at: 同期完了日時
  - created_at: レコード作成日時
  - updated_at: レコード更新日時
```

#### calendar_metadata テーブル
カレンダーイベント固有のメタデータ
```
columns:
  - id: プライマリキー
  - release_id: リリースID（一意キー）
  - calendar_title: カレンダータイトル
  - calendar_description: 説明文
  - calendar_location: 場所（配信プラットフォーム等）
  - event_color: イベント色（アニメ/マンガで分類）
  - reminder_minutes_before: リマインダー時間（デフォルト: 1440分=1日前）
  - calendar_id: ターゲットカレンダーID
  - is_all_day: 終日イベント設定
  - created_at: レコード作成日時
  - updated_at: レコード更新日時
```

### 2.2 処理フロー

```
┌─────────────────────────────────────────┐
│  定期実行: release_notifier.py          │
│  (毎朝08:00 via cron)                   │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ 1. 新規リリース取得                       │
│    SELECT * FROM releases               │
│    WHERE calendar_synced = 0            │
│    AND release_date >= TODAY            │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ 2. フィルタリング                         │
│    - NGキーワード確認                    │
│    - ユーザー設定フィルタ確認              │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│ 3. Googleカレンダーイベント作成            │
│    - Google Calendar API呼び出し         │
│    - タイトル・説明・日時設定              │
│    - リマインダー設定                     │
└──────────────┬──────────────────────────┘
               │
      ┌────────┴─────────┐
      │                  │
      ▼ Success          ▼ Error
    ┌──────────┐     ┌──────────────┐
    │ 4a成功   │     │ 4b失敗/リトライ│
    └────┬─────┘     └──────┬───────┘
         │                  │
         ▼                  ▼
    更新: releases      記録: calendar_sync_log
    - calendar_synced=1 - sync_status=failed
    - calendar_event_id - retry_count++
    - calendar_synced_at - error_message
                      (max_retries 超えたら終了)
```

---

## 3. 実装仕様

### 3.1 sync_calendar.py（カレンダー同期メインスクリプト）

#### ファイル構成
```
scripts/
├── sync_calendar.py              # メインスクリプト
├── modules/
│   ├── calendar_api.py           # Google Calendar API ラッパー
│   ├── calendar_sync_manager.py  # 同期ロジック管理
│   └── calendar_event_builder.py # イベント構築ユーティリティ
```

#### 3.1.1 sync_calendar.py - メイン処理

```python
#!/usr/bin/env python3
"""
Googleカレンダー同期メインスクリプト
毎日定期実行される中心モジュール
"""

import logging
from datetime import datetime, timedelta
from modules.db import Database
from modules.calendar_sync_manager import CalendarSyncManager
from modules.calendar_api import GoogleCalendarAPI
from config import load_config

def main():
    """
    Main execution flow:
    1. 未同期リリース取得
    2. カレンダーメタデータ作成
    3. Googleカレンダー同期
    4. DB更新
    5. エラーハンドリング・リトライ
    """

    # 初期化
    config = load_config()
    db = Database()
    logger = setup_logger('sync_calendar')

    try:
        # 1. Google Calendar API初期化
        api = GoogleCalendarAPI(credentials_path=config['google_credentials_path'])
        manager = CalendarSyncManager(db, api, config)

        # 2. 未同期かつ明日以降のリリースを取得
        unsynced_releases = db.get_unsynced_releases(
            days_ahead=config['calendar_sync_days_ahead']
        )

        logger.info(f"Found {len(unsynced_releases)} releases to sync")

        # 3. 各リリースをカレンダー同期
        sync_results = {
            'created': 0,
            'updated': 0,
            'failed': 0,
            'skipped': 0
        }

        for release in unsynced_releases:
            try:
                result = manager.sync_release(release)
                sync_results[result['status']] += 1
                logger.info(f"Sync {result['status']}: {release['id']}")

            except Exception as e:
                sync_results['failed'] += 1
                logger.error(f"Error syncing release {release['id']}: {str(e)}")
                # エラーハンドリングはmanagerで実施

        # 4. 結果ログ
        logger.info(f"Sync complete: {sync_results}")

        # 5. 同期統計をDBに記録
        db.record_sync_statistics(sync_results)

    except Exception as e:
        logger.critical(f"Fatal error in calendar sync: {str(e)}")
        raise

    finally:
        db.close()

def setup_logger(name):
    """ロギング設定"""
    logger = logging.getLogger(name)
    handler = logging.FileHandler('logs/calendar_sync.log')
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger

if __name__ == '__main__':
    main()
```

#### 3.1.2 calendar_sync_manager.py - 同期ロジック

```python
"""
同期管理・オーケストレーション
複雑なビジネスロジックをカプセル化
"""

class CalendarSyncManager:

    def __init__(self, db, api, config):
        self.db = db
        self.api = api
        self.config = config
        self.logger = logging.getLogger(__name__)

    def sync_release(self, release):
        """
        単一リリースの同期処理

        Args:
            release: リリース情報辞書

        Returns:
            {'status': 'created'|'updated'|'failed'|'skipped',
             'event_id': str,
             'error': str}
        """

        # 1. リリース情報をカレンダーイベントに変換
        event_data = self._build_event_data(release)

        # 2. カレンダーメタデータがあるか確認
        metadata = self.db.get_calendar_metadata(release['id'])

        # 3. 既にカレンダーイベントが存在するか確認
        if release['calendar_event_id']:
            return self._update_event(release, event_data)
        else:
            return self._create_event(release, event_data)

    def _create_event(self, release, event_data):
        """新規イベント作成"""
        try:
            # Google Calendar APIでイベント作成
            event_id = self.api.create_event(event_data)

            # DB更新
            self.db.update_release_calendar_sync(
                release_id=release['id'],
                calendar_event_id=event_id,
                calendar_synced=1,
                calendar_synced_at=datetime.now()
            )

            # ログ記録
            self.db.log_calendar_sync(
                release_id=release['id'],
                work_id=release['work_id'],
                google_event_id=event_id,
                sync_status='synced',
                sync_type='create',
                synced_at=datetime.now()
            )

            return {
                'status': 'created',
                'event_id': event_id,
                'error': None
            }

        except Exception as e:
            # エラー記録・リトライ判定
            return self._handle_sync_error(
                release, 'create', str(e)
            )

    def _update_event(self, release, event_data):
        """既存イベント更新"""
        try:
            event_id = release['calendar_event_id']
            self.api.update_event(event_id, event_data)

            # DB更新
            self.db.update_release_calendar_sync(
                release_id=release['id'],
                calendar_synced=1,
                calendar_synced_at=datetime.now()
            )

            # ログ記録
            self.db.log_calendar_sync(
                release_id=release['id'],
                work_id=release['work_id'],
                google_event_id=event_id,
                sync_status='synced',
                sync_type='update',
                synced_at=datetime.now()
            )

            return {
                'status': 'updated',
                'event_id': event_id,
                'error': None
            }

        except Exception as e:
            return self._handle_sync_error(
                release, 'update', str(e)
            )

    def _build_event_data(self, release):
        """
        リリース情報をGoogle Calendarイベント形式に変換

        Returns:
            {
                'summary': str,           # イベントタイトル
                'description': str,       # 説明文
                'start': datetime,        # 開始日時
                'end': datetime,          # 終了日時
                'location': str,          # 場所
                'colorId': str,           # 色ID
                'reminders': [...]        # リマインダー設定
            }
        """
        # 作品情報取得
        work = self.db.get_work(release['work_id'])

        # タイトル構築
        title = self._build_title(work, release)

        # 説明文構築
        description = self._build_description(work, release)

        # 日時設定
        start_date = datetime.strptime(
            release['release_date'], '%Y-%m-%d'
        )

        event_data = {
            'summary': title,
            'description': description,
            'start': {
                'date': start_date.isoformat(),  # 終日イベント
                'timeZone': 'Asia/Tokyo'
            },
            'end': {
                'date': (start_date + timedelta(days=1)).isoformat(),
                'timeZone': 'Asia/Tokyo'
            },
            'location': self._get_location(release),
            'colorId': self._get_color_id(work),
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {
                        'method': 'notification',
                        'minutes': 1440  # 1日前
                    }
                ]
            }
        }

        return event_data

    def _build_title(self, work, release):
        """イベントタイトル構築"""
        if release['release_type'] == 'episode':
            return f"{work['title']} 第{release['number']}話配信"
        elif release['release_type'] == 'volume':
            return f"{work['title']} 第{release['number']}巻発売"
        else:
            return f"{work['title']} {release['number']}"

    def _build_description(self, work, release):
        """説明文構築"""
        lines = [
            f"作品: {work['title']}",
            f"タイプ: {work['type'].upper()}",
            f"プラットフォーム: {release['platform']}",
            f"配信日: {release['release_date']}",
            ""
        ]

        if work['official_url']:
            lines.append(f"公式URL: {work['official_url']}")

        return "\n".join(lines)

    def _get_location(self, release):
        """場所（プラットフォーム）"""
        platform_names = {
            'netflix': 'Netflix',
            'prime': 'Amazon Prime Video',
            'dアニメ': 'dアニメストア',
            'crunchyroll': 'Crunchyroll',
            'unknown': '配信予定'
        }
        return platform_names.get(release['platform'], release['platform'])

    def _get_color_id(self, work):
        """イベント色ID"""
        color_map = {
            'anime': '1',      # 青
            'manga': '2'       # 緑
        }
        return color_map.get(work['type'], '0')

    def _handle_sync_error(self, release, sync_type, error_msg):
        """エラーハンドリング・リトライ管理"""
        retry_record = self.db.get_calendar_sync_log(release['id'])

        # リトライ回数チェック
        if retry_record and retry_record['retry_count'] >= 3:
            # 最大リトライ回数に達した
            self.db.log_calendar_sync(
                release_id=release['id'],
                work_id=release['work_id'],
                sync_status='failed',
                sync_type=sync_type,
                error_message=error_msg,
                retry_count=3
            )
            self.logger.error(f"Max retries exceeded for release {release['id']}")
            return {
                'status': 'failed',
                'event_id': None,
                'error': error_msg
            }

        # リトライ記録
        retry_count = (retry_record['retry_count'] if retry_record else 0) + 1
        self.db.log_calendar_sync(
            release_id=release['id'],
            work_id=release['work_id'],
            sync_status='pending',
            sync_type=sync_type,
            error_message=error_msg,
            retry_count=retry_count
        )

        return {
            'status': 'failed',
            'event_id': None,
            'error': error_msg
        }
```

#### 3.1.3 calendar_api.py - Google Calendar API ラッパー

```python
"""
Google Calendar API ラッパー
認証・通信を隠蔽
"""

from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from google.oauth2 import service_account
from google.auth.oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging

class GoogleCalendarAPI:

    SCOPES = ['https://www.googleapis.com/auth/calendar']

    def __init__(self, credentials_path='credentials/token.json'):
        self.logger = logging.getLogger(__name__)
        self.service = self._authenticate(credentials_path)

    def _authenticate(self, credentials_path):
        """OAuth2認証"""
        try:
            creds = self._get_credentials(credentials_path)
            return build('calendar', 'v3', credentials=creds)
        except Exception as e:
            self.logger.error(f"Authentication failed: {str(e)}")
            raise

    def _get_credentials(self, token_path):
        """認証情報取得・更新"""
        # 実装詳細は既存のmailer.py参照
        pass

    def create_event(self, event_data):
        """
        カレンダーイベント作成

        Args:
            event_data: イベント情報辞書

        Returns:
            str: イベントID

        Raises:
            HttpError: API呼び出しエラー
        """
        try:
            event = self.service.events().insert(
                calendarId='primary',
                body=event_data,
                sendNotifications=True
            ).execute()

            self.logger.info(f"Event created: {event['id']}")
            return event['id']

        except HttpError as e:
            self.logger.error(f"Create event error: {str(e)}")
            raise

    def update_event(self, event_id, event_data):
        """
        カレンダーイベント更新

        Args:
            event_id: イベントID
            event_data: 更新情報

        Returns:
            dict: 更新後のイベント情報
        """
        try:
            event = self.service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event_data,
                sendNotifications=True
            ).execute()

            self.logger.info(f"Event updated: {event_id}")
            return event

        except HttpError as e:
            self.logger.error(f"Update event error: {str(e)}")
            raise

    def delete_event(self, event_id):
        """
        カレンダーイベント削除

        Args:
            event_id: イベントID
        """
        try:
            self.service.events().delete(
                calendarId='primary',
                eventId=event_id,
                sendNotifications=True
            ).execute()

            self.logger.info(f"Event deleted: {event_id}")

        except HttpError as e:
            self.logger.error(f"Delete event error: {str(e)}")
            raise

    def get_event(self, event_id):
        """
        カレンダーイベント取得

        Args:
            event_id: イベントID

        Returns:
            dict: イベント情報
        """
        try:
            event = self.service.events().get(
                calendarId='primary',
                eventId=event_id
            ).execute()

            return event

        except HttpError as e:
            self.logger.error(f"Get event error: {str(e)}")
            raise
```

---

## 4. インテグレーションポイント

### 4.1 既存スクリプトとの連携

#### release_notifier.py との連携
```python
# release_notifier.py内で呼び出し
from scripts.sync_calendar import sync_calendar_events

def main():
    # ... 既存の通知処理 ...

    # カレンダー同期実行
    sync_calendar_events()
```

#### config.json への追加設定
```json
{
  "calendar": {
    "sync_enabled": true,
    "sync_days_ahead": 30,
    "credentials_path": "credentials/calendar_token.json",
    "calendar_id": "primary",
    "reminder_minutes": 1440,
    "event_colors": {
      "anime": "1",
      "manga": "2"
    },
    "max_retries": 3,
    "retry_interval_hours": 6
  }
}
```

### 4.2 データベース連携

#### 新しいDB メソッド
```python
class Database:

    def get_unsynced_releases(self, days_ahead=30):
        """未同期リリース取得"""
        pass

    def update_release_calendar_sync(self, release_id, **kwargs):
        """releases テーブルのカレンダー関連カラム更新"""
        pass

    def get_calendar_metadata(self, release_id):
        """カレンダーメタデータ取得"""
        pass

    def log_calendar_sync(self, **kwargs):
        """同期ログ記録"""
        pass

    def get_calendar_sync_log(self, release_id):
        """同期ログ取得"""
        pass

    def record_sync_statistics(self, stats):
        """同期統計記録"""
        pass
```

---

## 5. エラーハンドリング戦略

### 5.1 エラー分類

| エラー種別 | 原因 | リトライ | 対応 |
|---------|------|--------|------|
| 認証エラー | 認証失敗・期限切れ | 可 | トークン更新 |
| ネットワークエラー | 接続失敗 | 可 | 指数バックオフ |
| API限度超過 | レート制限 | 可 | 待機・再試行 |
| データエラー | 無効なイベント情報 | 不可 | スキップ・ログ記録 |
| システムエラー | DB接続失敗 | 可 | 再起動待機 |

### 5.2 リトライ戦略

```python
# 指数バックオフ
retry_delays = [60, 300, 900, 3600]  # 1分, 5分, 15分, 1時間

def should_retry(error_type, retry_count):
    """リトライ可否判定"""
    if error_type in ['auth', 'network', 'rate_limit']:
        return retry_count < 3
    return False
```

---

## 6. テスト戦略

### 6.1 ユニットテスト

```python
# tests/test_calendar_sync_manager.py
class TestCalendarSyncManager(unittest.TestCase):

    def test_build_event_data(self):
        """イベントデータ構築テスト"""
        pass

    def test_create_event_success(self):
        """イベント作成成功テスト"""
        pass

    def test_create_event_failure(self):
        """イベント作成失敗・リトライテスト"""
        pass

    def test_update_event(self):
        """イベント更新テスト"""
        pass
```

### 6.2 統合テスト

```python
# tests/test_calendar_integration.py
class TestCalendarIntegration(unittest.TestCase):

    def test_full_sync_flow(self):
        """完全同期フロー"""
        pass

    def test_sync_with_filtering(self):
        """フィルタリング付き同期"""
        pass
```

---

## 7. デプロイメントチェックリスト

- [ ] マイグレーション006実行
- [ ] Google Calendar API有効化
- [ ] OAuth2認証情報配置
- [ ] config.json更新
- [ ] DB.pyへのメソッド追加実装
- [ ] sync_calendar.py実装・テスト
- [ ] crontab設定（release_notifier.pyから呼び出し）
- [ ] ログディレクトリ作成
- [ ] 本番環境での動作確認

---

## 8. パフォーマンス最適化

### 8.1 バッチ処理

```python
# 大量イベント作成時はバッチモードを使用
batch_size = 50
for i in range(0, len(releases), batch_size):
    batch = releases[i:i+batch_size]
    # 各バッチを処理
```

### 8.2 キャッシング

```python
# メタデータのキャッシング
cache = {}
for release in releases:
    if release['work_id'] not in cache:
        cache[release['work_id']] = db.get_work(release['work_id'])
```

---

## 9. 監視・メトリクス

### 9.1 記録すべきメトリクス

- 同期成功率 (created/total)
- エラー発生率
- リトライ回数
- API呼び出し総数
- 処理時間（開始～完了）

### 9.2 アラート閾値

- 成功率 < 90%: WARNING
- エラーレート > 5%: CRITICAL
- API超過: CRITICAL

---

## 10. 今後の拡張

- 複数カレンダーサポート
- ジャンル別色分け自動化
- ユーザー設定カスタマイズUI
- スマートリマインダー（配信1時間前）
- 削除イベント自動クリーンアップ
