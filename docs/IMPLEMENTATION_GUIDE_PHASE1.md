# Phase 1 実装ガイド - 緊急対応項目

**作成日**: 2025-12-06
**対象**: Backend Developer
**期限**: 1週間以内

---

## 📋 目次

1. [実装概要](#実装概要)
2. [レート制限実装](#レート制限実装)
3. [エラーハンドリング強化](#エラーハンドリング強化)
4. [環境変数化](#環境変数化)
5. [データベースマイグレーション](#データベースマイグレーション)
6. [テスト実装](#テスト実装)
7. [デプロイ手順](#デプロイ手順)

---

## 実装概要

### 作成済みファイル

```
MangaAnime-Info-delivery-system/
├── modules/
│   ├── rate_limiter.py          ✅ 作成済み
│   ├── error_handler.py         ✅ 作成済み
│   └── config_loader.py         ✅ 作成済み
├── migrations/
│   └── 004_rss_management.sql   ✅ 作成済み
├── config.env.example           ✅ 作成済み
└── docs/
    ├── API_EXTERNAL_INTEGRATION_ANALYSIS_REPORT.md  ✅ 作成済み
    └── IMPLEMENTATION_GUIDE_PHASE1.md               ✅ 本ファイル
```

### 実装タスク

- [x] レート制限モジュール作成
- [x] エラーハンドリングモジュール作成
- [x] 設定管理モジュール作成
- [x] 環境変数テンプレート作成
- [x] データベースマイグレーションSQL作成
- [ ] 既存モジュールの修正
- [ ] テストコード作成
- [ ] ドキュメント更新
- [ ] デプロイ

---

## レート制限実装

### Step 1: 既存モジュールの修正

#### 1.1 `modules/anime_anilist.py` の修正

**Before**:
```python
import requests
import logging

def fetch_anilist_data(query, variables):
    response = requests.post(ANILIST_API_URL, json={'query': query, 'variables': variables})
    response.raise_for_status()
    return response.json()
```

**After**:
```python
import requests
import logging
from modules.rate_limiter import anilist_limiter
from modules.error_handler import with_retry, RetryConfig

@with_retry(RetryConfig(max_retries=3, backoff_factor=2.0))
@anilist_limiter
def fetch_anilist_data(query, variables):
    """
    AniList GraphQL API からデータを取得

    Args:
        query: GraphQLクエリ
        variables: クエリ変数

    Returns:
        APIレスポンスのdataフィールド

    Raises:
        requests.RequestException: API呼び出しエラー
    """
    try:
        response = requests.post(
            ANILIST_API_URL,
            json={'query': query, 'variables': variables},
            timeout=10,  # タイムアウト追加
            headers={'User-Agent': 'MangaAnime-Info-Bot/1.0'}
        )
        response.raise_for_status()
        data = response.json()

        # GraphQLエラーチェック
        if 'errors' in data:
            error_msg = ', '.join([e.get('message', 'Unknown error') for e in data['errors']])
            logging.error(f"GraphQL errors: {error_msg}")
            raise ValueError(f"GraphQL errors: {error_msg}")

        return data.get('data')

    except requests.Timeout:
        logging.error("AniList API timeout")
        raise
    except requests.RequestException as e:
        logging.error(f"AniList API error: {e}")
        raise
```

#### 1.2 `modules/anime_syoboi.py` の修正

**修正箇所**:
```python
from modules.rate_limiter import syoboi_limiter
from modules.error_handler import with_retry, RetryConfig

@with_retry(RetryConfig(max_retries=3, backoff_factor=2.0))
@syoboi_limiter
def fetch_syoboi_data(start_date, end_date):
    """
    しょぼいカレンダーAPIからデータを取得

    Args:
        start_date: 開始日（YYYY-MM-DD）
        end_date: 終了日（YYYY-MM-DD）

    Returns:
        番組情報のリスト
    """
    params = {
        'Command': 'ProgLookup',
        'Range': f'{start_date}-{end_date}',
        'Fields': 'TID,Title,StTime,ChName'
    }

    try:
        response = requests.get(
            SYOBOI_API_URL,
            params=params,
            timeout=10,
            headers={'User-Agent': 'MangaAnime-Info-Bot/1.0'}
        )
        response.encoding = 'shift_jis'  # 明示的に設定
        response.raise_for_status()

        # XMLパース
        import xml.etree.ElementTree as ET
        try:
            root = ET.fromstring(response.content)
            return parse_syoboi_xml(root)
        except ET.ParseError as e:
            logging.error(f"XML parse error: {e}")
            raise

    except Exception as e:
        logging.error(f"Syoboi API error: {e}")
        raise
```

#### 1.3 `modules/manga_rss.py` の修正

**修正箇所**:
```python
import feedparser
import requests
from modules.rate_limiter import rss_limiter
from modules.error_handler import with_retry, RetryConfig
from modules.config_loader import get_config

@with_retry(RetryConfig(max_retries=3, backoff_factor=1.5))
@rss_limiter
def fetch_rss_feed(url, etag=None, modified=None):
    """
    RSS フィードを取得（ETag/Last-Modified対応）

    Args:
        url: RSS Feed URL
        etag: 前回取得時のETag
        modified: 前回取得時のLast-Modified

    Returns:
        (entries, new_etag, new_modified) のタプル
    """
    headers = {
        'User-Agent': 'MangaAnime-Info-Bot/1.0 (+https://example.com/bot)'
    }

    if etag:
        headers['If-None-Match'] = etag
    if modified:
        headers['If-Modified-Since'] = modified

    try:
        response = requests.get(url, headers=headers, timeout=15)

        # 304 Not Modified
        if response.status_code == 304:
            logging.info(f"RSS not modified: {url}")
            return [], etag, modified

        response.raise_for_status()

        feed = feedparser.parse(response.content)

        if feed.bozo and feed.bozo_exception:
            logging.warning(f"RSS parse warning for {url}: {feed.bozo_exception}")

        new_etag = response.headers.get('ETag')
        new_modified = response.headers.get('Last-Modified')

        return feed.entries, new_etag, new_modified

    except Exception as e:
        logging.error(f"RSS fetch error for {url}: {e}")
        raise
```

#### 1.4 `modules/mailer.py` の修正

**修正箇所**:
```python
from googleapiclient.errors import HttpError
from modules.rate_limiter import gmail_limiter
from modules.error_handler import with_retry, RetryConfig, gmail_breaker

@with_retry(RetryConfig(max_retries=3, backoff_factor=2.0))
@gmail_limiter
@gmail_breaker
def send_email(to, subject, body_html):
    """
    Gmailでメールを送信

    Args:
        to: 送信先メールアドレス
        subject: 件名
        body_html: HTML本文

    Returns:
        成功時True、失敗時False
    """
    try:
        service = get_gmail_service()
        message = create_message(to, subject, body_html)
        result = send_message(service, 'me', message)

        logging.info(f"Email sent to {to}: {result['id']}")
        return True

    except HttpError as e:
        if e.resp.status in [403, 429]:
            logging.error(f"Gmail rate limit exceeded: {e}")
        else:
            logging.error(f"Gmail API error: {e}")
        raise

    except Exception as e:
        logging.error(f"Email send error: {e}")
        raise
```

#### 1.5 `modules/calendar_integration.py` の修正

**修正箇所**:
```python
from googleapiclient.errors import HttpError
from modules.rate_limiter import calendar_limiter
from modules.error_handler import with_retry, RetryConfig, calendar_breaker
import sqlite3

@with_retry(RetryConfig(max_retries=3, backoff_factor=2.0))
@calendar_limiter
@calendar_breaker
def add_calendar_event(title, date, description, url, category='anime'):
    """
    Google カレンダーにイベントを追加

    Args:
        title: イベントタイトル
        date: 日付（YYYY-MM-DD）
        description: 説明
        url: URL
        category: カテゴリ（anime, manga, movie）

    Returns:
        イベントID、失敗時None
    """
    service = get_calendar_service()

    # 重複チェック
    existing = check_existing_event(service, title, date)
    if existing:
        logging.info(f"Event already exists: {existing['id']}")
        return existing['id']

    # カテゴリ別色設定
    color_map = {
        'anime': '9',      # 青
        'manga': '10',     # 緑
        'movie': '11',     # 赤
    }

    event = {
        'summary': title,
        'description': f"{description}\n\nURL: {url}",
        'start': {
            'date': date,
            'timeZone': 'Asia/Tokyo',
        },
        'end': {
            'date': date,
            'timeZone': 'Asia/Tokyo',
        },
        'colorId': color_map.get(category, '1'),
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'popup', 'minutes': 60},
                {'method': 'popup', 'minutes': 1440},  # 1日前
            ],
        },
    }

    try:
        result = service.events().insert(
            calendarId='primary',
            body=event
        ).execute()

        event_id = result['id']
        logging.info(f"Calendar event created: {event_id}")

        # データベースに記録
        save_calendar_event_to_db(title, date, event_id, category)

        return event_id

    except HttpError as e:
        logging.error(f"Calendar API error: {e}")
        raise

def check_existing_event(service, title, date):
    """既存イベントの確認"""
    time_min = f"{date}T00:00:00+09:00"
    time_max = f"{date}T23:59:59+09:00"

    try:
        events_result = service.events().list(
            calendarId='primary',
            timeMin=time_min,
            timeMax=time_max,
            q=title,
            singleEvents=True
        ).execute()

        events = events_result.get('items', [])
        for event in events:
            if event.get('summary') == title:
                return event

    except HttpError as e:
        logging.error(f"Error checking existing event: {e}")

    return None

def save_calendar_event_to_db(title, date, event_id, category):
    """カレンダーイベントをデータベースに保存"""
    from modules.config_loader import get_config

    config = get_config()
    db_path = config.get_database_path()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO calendar_events (title, event_date, event_id, category)
            VALUES (?, ?, ?, ?)
        """, (title, date, event_id, category))

        conn.commit()
        logging.debug(f"Saved calendar event to database: {event_id}")

    except sqlite3.IntegrityError:
        logging.warning(f"Calendar event already exists in database: {event_id}")

    finally:
        conn.close()
```

---

## エラーハンドリング強化

### Step 2: 共通エラーハンドラの追加

**新規ファイル**: `modules/common_utils.py`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
共通ユーティリティモジュール
"""

import logging
from typing import Optional, Dict, Any
import time

logger = logging.getLogger(__name__)


def log_api_call(
    api_name: str,
    endpoint: str,
    method: str,
    status_code: Optional[int],
    success: bool,
    response_time: float,
    error_message: Optional[str] = None
):
    """
    API呼び出しをデータベースに記録

    Args:
        api_name: API名
        endpoint: エンドポイント
        method: HTTPメソッド
        status_code: ステータスコード
        success: 成功/失敗
        response_time: レスポンス時間
        error_message: エラーメッセージ
    """
    import sqlite3
    from modules.config_loader import get_config

    config = get_config()
    db_path = config.get_database_path()

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO api_call_logs (
                api_name, endpoint, method, status_code,
                success, response_time, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            api_name, endpoint, method, status_code,
            1 if success else 0, response_time, error_message
        ))

        conn.commit()
        conn.close()

    except Exception as e:
        logger.error(f"Failed to log API call: {e}")


def measure_time(func):
    """実行時間測定デコレータ"""
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start
            logger.debug(f"{func.__name__} completed in {elapsed:.3f}s")
            return result
        except Exception as e:
            elapsed = time.time() - start
            logger.error(f"{func.__name__} failed after {elapsed:.3f}s: {e}")
            raise
    return wrapper
```

---

## 環境変数化

### Step 3: 環境設定のセットアップ

#### 3.1 `.gitignore` の更新

```bash
# プロジェクトルートで実行
cat >> .gitignore << 'EOF'

# Environment variables
.env
.env.local
.env.*.local

# Google API credentials
credentials.json
token.json
calendar_credentials.json
calendar_token.json

# Sensitive config
config.json
EOF
```

#### 3.2 環境変数ファイルの作成

```bash
# サンプルファイルから.envを作成
cp config.env.example .env

# エディタで.envを編集
nano .env
```

**必須設定項目**:
```bash
# .env
NOTIFICATION_EMAIL=your-email@example.com
DATABASE_PATH=db.sqlite3
LOG_LEVEL=INFO
GMAIL_CREDENTIALS_PATH=credentials.json
GMAIL_TOKEN_PATH=token.json
```

#### 3.3 既存スクリプトの修正

**すべてのPythonスクリプトの冒頭に追加**:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# 環境変数の読み込み（最優先）
from dotenv import load_dotenv
load_dotenv()

import logging
from modules.config_loader import get_config

# 設定の読み込み
config = get_config()

# ロギング設定
logging.basicConfig(
    level=getattr(logging, config.get_log_level()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config.get('log_file', 'logs/app.log')),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
```

---

## データベースマイグレーション

### Step 4: マイグレーションの実行

#### 4.1 マイグレーション実行スクリプト

**新規ファイル**: `scripts/run_migration.py`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
データベースマイグレーション実行スクリプト
"""

import sqlite3
import logging
from pathlib import Path
from dotenv import load_dotenv
from modules.config_loader import get_config

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migration(db_path: str, migration_file: Path):
    """
    マイグレーションを実行

    Args:
        db_path: データベースファイルパス
        migration_file: マイグレーションSQLファイル
    """
    logger.info(f"Running migration: {migration_file.name}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # マイグレーションSQLの読み込み
        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()

        # 実行
        cursor.executescript(migration_sql)
        conn.commit()

        logger.info(f"Migration completed: {migration_file.name}")

    except Exception as e:
        conn.rollback()
        logger.error(f"Migration failed: {e}")
        raise

    finally:
        conn.close()


def main():
    config = get_config()
    db_path = config.get_database_path()

    migrations_dir = Path('migrations')
    migration_files = sorted(migrations_dir.glob('*.sql'))

    logger.info(f"Found {len(migration_files)} migration files")

    for migration_file in migration_files:
        run_migration(db_path, migration_file)

    logger.info("All migrations completed successfully")


if __name__ == '__main__':
    main()
```

#### 4.2 マイグレーションの実行

```bash
# 実行権限付与
chmod +x scripts/run_migration.py

# マイグレーション実行
python3 scripts/run_migration.py
```

#### 4.3 マイグレーション確認

```bash
# SQLite CLIで確認
sqlite3 db.sqlite3

# テーブル一覧
.tables

# rss_sourcesテーブルの確認
.schema rss_sources

# 初期データの確認
SELECT * FROM rss_sources;

# ビューの確認
SELECT * FROM api_call_summary;

# 終了
.quit
```

---

## テスト実装

### Step 5: ユニットテストの作成

**新規ファイル**: `tests/test_rate_limiter.py`

```python
import pytest
import time
from modules.rate_limiter import RateLimiter


def test_rate_limiter_basic():
    """基本的なレート制限のテスト"""
    limiter = RateLimiter(calls=5, period=1, name="Test")

    @limiter
    def test_func():
        return time.time()

    # 5回は即座に実行可能
    times = []
    for _ in range(5):
        times.append(test_func())

    # 5回とも1秒以内に完了
    assert times[4] - times[0] < 1.0

    # 6回目は待機が発生
    start = time.time()
    test_func()
    elapsed = time.time() - start

    # 待機時間が発生したはず
    assert elapsed > 0.0


def test_rate_limiter_remaining_calls():
    """残り呼び出し数のテスト"""
    limiter = RateLimiter(calls=10, period=1, name="Test")

    assert limiter.get_remaining_calls() == 10

    @limiter
    def test_func():
        pass

    # 3回呼び出し
    for _ in range(3):
        test_func()

    assert limiter.get_remaining_calls() == 7


def test_rate_limiter_reset():
    """リセット機能のテスト"""
    limiter = RateLimiter(calls=5, period=1, name="Test")

    @limiter
    def test_func():
        pass

    # 5回呼び出し
    for _ in range(5):
        test_func()

    assert limiter.get_remaining_calls() == 0

    # リセット
    limiter.reset()

    assert limiter.get_remaining_calls() == 5
```

**新規ファイル**: `tests/test_error_handler.py`

```python
import pytest
from modules.error_handler import with_retry, RetryConfig, CircuitBreaker


def test_retry_success():
    """リトライ成功のテスト"""
    attempt_count = 0

    @with_retry(RetryConfig(max_retries=3, backoff_factor=0.1))
    def test_func():
        nonlocal attempt_count
        attempt_count += 1

        if attempt_count < 3:
            raise Exception("Fail")

        return "Success"

    result = test_func()
    assert result == "Success"
    assert attempt_count == 3


def test_retry_failure():
    """リトライ失敗のテスト"""
    @with_retry(RetryConfig(max_retries=3, backoff_factor=0.1))
    def test_func():
        raise ValueError("Always fail")

    with pytest.raises(ValueError):
        test_func()


def test_circuit_breaker():
    """サーキットブレーカーのテスト"""
    breaker = CircuitBreaker(failure_threshold=3, timeout=1, name="Test")

    @breaker
    def test_func(should_fail):
        if should_fail:
            raise Exception("Fail")
        return "Success"

    # 3回失敗させる
    for _ in range(3):
        with pytest.raises(Exception):
            test_func(True)

    # OPEN状態になっているはず
    with pytest.raises(Exception, match="Circuit breaker"):
        test_func(False)

    # タイムアウト待機
    time.sleep(1.1)

    # 回復するはず
    result = test_func(False)
    assert result == "Success"
```

**新規ファイル**: `tests/test_config_loader.py`

```python
import pytest
import os
from pathlib import Path
from modules.config_loader import ConfigLoader


def test_config_loader_basic(tmp_path):
    """基本的な設定読み込みのテスト"""
    config_file = tmp_path / "config.json"
    config_file.write_text("""
    {
        "anime_sources": {
            "anilist": {
                "enabled": true,
                "api_url": "https://example.com"
            }
        },
        "notification": {
            "email": {
                "recipients": ["test@example.com"]
            }
        }
    }
    """)

    config = ConfigLoader(str(config_file), env_file=None)

    assert config.is_enabled('anime_sources.anilist')
    assert config.get('anime_sources.anilist.api_url') == "https://example.com"
    assert config.get_notification_emails() == ["test@example.com"]


def test_env_override(tmp_path, monkeypatch):
    """環境変数オーバーライドのテスト"""
    config_file = tmp_path / "config.json"
    config_file.write_text("""
    {
        "notification": {
            "email": {
                "recipients": ["default@example.com"]
            }
        }
    }
    """)

    # 環境変数設定
    monkeypatch.setenv('NOTIFICATION_EMAIL', 'override@example.com')

    config = ConfigLoader(str(config_file), env_file=None)

    assert config.get_notification_emails() == ["override@example.com"]
```

### テストの実行

```bash
# すべてのテストを実行
pytest tests/ -v

# カバレッジ付きで実行
pytest tests/ --cov=modules --cov-report=html

# 特定のテストのみ
pytest tests/test_rate_limiter.py -v
```

---

## デプロイ手順

### Step 6: 本番環境への適用

#### 6.1 バックアップ

```bash
# データベースバックアップ
cp db.sqlite3 backups/db.sqlite3.backup.$(date +%Y%m%d_%H%M%S)

# 設定ファイルバックアップ
cp config.json backups/config.json.backup.$(date +%Y%m%d_%H%M%S)
```

#### 6.2 依存パッケージのインストール

```bash
# requirements.txtに追加
cat >> requirements.txt << 'EOF'
python-dotenv==1.0.0
pydantic==2.5.0
EOF

# インストール
pip install -r requirements.txt
```

#### 6.3 マイグレーション実行

```bash
python3 scripts/run_migration.py
```

#### 6.4 動作確認

```bash
# Pythonインタラクティブシェルで確認
python3

>>> from modules.rate_limiter import anilist_limiter
>>> from modules.error_handler import with_retry
>>> from modules.config_loader import get_config
>>>
>>> config = get_config()
>>> print(config.get_notification_emails())
>>>
>>> # レート制限のテスト
>>> @anilist_limiter
... def test():
...     print("Called!")
...
>>> test()
>>> test()
>>>
>>> exit()
```

#### 6.5 ログ確認

```bash
# アプリケーションログ
tail -f logs/app.log

# エラーのみ表示
tail -f logs/app.log | grep ERROR
```

---

## トラブルシューティング

### よくある問題

#### 1. インポートエラー

**エラー**:
```
ModuleNotFoundError: No module named 'modules.rate_limiter'
```

**解決策**:
```bash
# PYTHONPATHの設定
export PYTHONPATH=/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system:$PYTHONPATH

# または、スクリプト内で設定
import sys
sys.path.insert(0, '/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system')
```

#### 2. データベースエラー

**エラー**:
```
sqlite3.OperationalError: table rss_sources already exists
```

**解決策**:
```sql
-- SQLiteで確認
sqlite3 db.sqlite3

-- テーブル削除（必要な場合のみ）
DROP TABLE IF EXISTS rss_sources;

-- マイグレーション再実行
.quit
python3 scripts/run_migration.py
```

#### 3. レート制限が効かない

**原因**: デコレータの順序が間違っている

**正しい順序**:
```python
@with_retry(...)      # 外側
@rate_limiter         # 内側
@circuit_breaker      # 最内側
def api_call():
    pass
```

---

## チェックリスト

### 実装前

- [ ] 既存コードのバックアップ
- [ ] データベースのバックアップ
- [ ] 依存パッケージの確認

### 実装中

- [ ] rate_limiter.py の動作確認
- [ ] error_handler.py の動作確認
- [ ] config_loader.py の動作確認
- [ ] 各モジュールへの適用完了
- [ ] マイグレーション実行完了

### 実装後

- [ ] ユニットテストの実行
- [ ] 統合テストの実行
- [ ] ログの確認
- [ ] パフォーマンステスト
- [ ] ドキュメント更新

### デプロイ後

- [ ] モニタリング設定
- [ ] アラート設定
- [ ] バックアップスケジュール確認
- [ ] ロールバック手順の確認

---

## 次のステップ（Phase 2）

Phase 1完了後、以下のPhase 2実装に進みます:

1. タイムアウト設定の統一
2. ログレベル最適化
3. キャッシュ機能追加
4. メトリクス収集強化
5. モニタリングダッシュボード構築

詳細は `docs/IMPLEMENTATION_GUIDE_PHASE2.md` を参照。

---

**作成者**: Backend Developer Agent
**最終更新**: 2025-12-06
