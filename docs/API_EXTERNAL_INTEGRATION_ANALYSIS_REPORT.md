# API・外部連携解析レポート

**プロジェクト**: MangaAnime-Info-delivery-system
**解析日時**: 2025-12-06
**解析者**: Backend Developer Agent

---

## 📋 目次

1. [エグゼクティブサマリー](#エグゼクティブサマリー)
2. [AniList GraphQL API解析](#anilist-graphql-api解析)
3. [しょぼいカレンダーAPI解析](#しょぼいカレンダーapi解析)
4. [マンガRSSフィード解析](#マンガrssフィード解析)
5. [Gmail API連携解析](#gmail-api連携解析)
6. [Google Calendar API連携解析](#google-calendar-api連携解析)
7. [設定ファイル解析](#設定ファイル解析)
8. [総合評価と推奨事項](#総合評価と推奨事項)

---

## エグゼクティブサマリー

### 解析対象モジュール
- `modules/anime_anilist.py` - AniList GraphQL API
- `modules/anime_syoboi.py` - しょぼいカレンダーAPI
- `modules/manga_rss.py` - マンガRSSフィード
- `modules/mailer.py` - Gmail API
- `modules/calendar_integration.py` - Google Calendar API
- `config.json` - システム設定

### 主要な発見事項

#### ✅ 強み
- モジュール化された設計
- エラーハンドリングの実装
- ログ記録の一貫性

#### ⚠️ 改善点
- レート制限対応の不足
- リトライロジックの不完全性
- 設定の外部化不足
- タイムアウト設定の欠如

---

## AniList GraphQL API解析

### ファイル: `modules/anime_anilist.py`

#### 接続状態

**エンドポイント**:
```python
ANILIST_API_URL = "https://graphql.anilist.co"
```

**認証**: 不要（パブリックAPI）

#### レート制限

**公式制限**: 90リクエスト/分

**現在の実装**:
```python
# レート制限対応: 未実装
# ⚠️ 問題: バースト的なリクエストで制限に到達する可能性
```

**推奨実装**:
```python
import time
from functools import wraps

def rate_limit(calls=90, period=60):
    """レート制限デコレータ"""
    def decorator(func):
        timestamps = []
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            timestamps[:] = [t for t in timestamps if now - t < period]
            if len(timestamps) >= calls:
                sleep_time = period - (now - timestamps[0])
                time.sleep(sleep_time)
            timestamps.append(time.time())
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

#### GraphQLクエリ品質

**現在のクエリ例**:
```graphql
query ($page: Int, $perPage: Int, $season: MediaSeason, $seasonYear: Int) {
  Page(page: $page, perPage: $perPage) {
    media(season: $season, seasonYear: $seasonYear, type: ANIME) {
      id
      title { romaji native english }
      startDate { year month day }
      episodes
      genres
      coverImage { large }
    }
  }
}
```

**評価**: ✅ 適切な最小フィールド取得

#### エラーハンドリング

**現在の実装**:
```python
try:
    response = requests.post(ANILIST_API_URL, json=payload)
    response.raise_for_status()
except requests.RequestException as e:
    logging.error(f"AniList API error: {e}")
    return []
```

**問題点**:
- タイムアウト設定なし
- リトライなし
- GraphQLエラー（200ステータスでもエラー）の未処理

**推奨実装**:
```python
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

def get_session_with_retry():
    session = requests.Session()
    retry = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    return session

@rate_limit(calls=90, period=60)
def fetch_anilist_data(query, variables):
    session = get_session_with_retry()
    try:
        response = session.post(
            ANILIST_API_URL,
            json={'query': query, 'variables': variables},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        # GraphQLエラーチェック
        if 'errors' in data:
            logging.error(f"GraphQL errors: {data['errors']}")
            return None

        return data.get('data')
    except requests.Timeout:
        logging.error("AniList API timeout")
        return None
    except requests.RequestException as e:
        logging.error(f"AniList API error: {e}")
        return None
```

---

## しょぼいカレンダーAPI解析

### ファイル: `modules/anime_syoboi.py`

#### 接続状態

**エンドポイント**:
```python
SYOBOI_API_URL = "https://cal.syoboi.jp/db.php"
```

**認証**: 不要

#### パラメータ設計

**現在の実装**:
```python
params = {
    'Command': 'ProgLookup',
    'Range': f'{start_date}-{end_date}',
    'Fields': 'TID,Title,StTime,ChName'
}
```

**評価**: ✅ 必要十分なフィールド取得

#### レート制限

**公式情報**: 明示的な制限なし（非公式APIのため配慮必要）

**推奨対応**:
```python
import time

# 1リクエスト/秒の控えめな制限
@rate_limit(calls=1, period=1)
def fetch_syoboi_data(start_date, end_date):
    # 実装
    pass
```

#### エラーハンドリング

**現在の問題**:
- XML/JSONパースエラーの未処理
- 文字エンコーディング問題（Shift_JIS）の不完全な処理

**推奨実装**:
```python
def fetch_syoboi_data(start_date, end_date):
    try:
        response = requests.get(
            SYOBOI_API_URL,
            params=params,
            timeout=10
        )
        response.encoding = 'shift_jis'  # 明示的に設定
        response.raise_for_status()

        # XMLパース
        import xml.etree.ElementTree as ET
        try:
            root = ET.fromstring(response.content)
        except ET.ParseError as e:
            logging.error(f"XML parse error: {e}")
            return []

        return parse_syoboi_xml(root)
    except Exception as e:
        logging.error(f"Syoboi API error: {e}")
        return []
```

---

## マンガRSSフィード解析

### ファイル: `modules/manga_rss.py`

#### 対応RSSソース

**現在の設定**:
```python
RSS_SOURCES = {
    "bookwalker": {
        "url": "https://bookwalker.jp/rss/",
        "enabled": True
    },
    "magapoke": {
        "url": "https://pocket.shonenmagazine.com/rss",
        "enabled": True
    },
    "jump_bookstore": {
        "url": "https://jumpbookstore.com/rss/new",
        "enabled": False  # エンドポイント廃止により無効化
    },
    "rakuten_kobo": {
        "url": "https://books.rakuten.co.jp/rss/new-comics/",
        "enabled": True
    }
}
```

#### フィード取得ロジック

**feedparserライブラリ使用**:
```python
import feedparser

def fetch_rss_feed(url):
    try:
        feed = feedparser.parse(url)
        if feed.bozo:  # パースエラー
            logging.warning(f"RSS parse warning: {feed.bozo_exception}")
        return feed.entries
    except Exception as e:
        logging.error(f"RSS fetch error: {e}")
        return []
```

**評価**: ✅ feedparserは堅牢なライブラリ

#### 問題点と推奨対応

**現在の問題**:
1. タイムアウトなし（feedparserは内部でurllibを使用）
2. User-Agent未設定（一部サイトでブロックされる可能性）
3. ETags/Last-Modified非対応（無駄な帯域消費）

**推奨実装**:
```python
import feedparser
import requests

def fetch_rss_feed_improved(url, etag=None, modified=None):
    """
    ETags/Last-Modifiedに対応したRSSフィード取得
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

        if response.status_code == 304:
            logging.info(f"RSS not modified: {url}")
            return None, etag, modified

        response.raise_for_status()

        feed = feedparser.parse(response.content)
        new_etag = response.headers.get('ETag')
        new_modified = response.headers.get('Last-Modified')

        return feed.entries, new_etag, new_modified
    except Exception as e:
        logging.error(f"RSS fetch error for {url}: {e}")
        return [], None, None
```

#### RSSソース管理

**データベーススキーマ追加推奨**:
```sql
CREATE TABLE rss_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    url TEXT NOT NULL,
    enabled INTEGER DEFAULT 1,
    etag TEXT,
    last_modified TEXT,
    last_fetch DATETIME,
    error_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## Gmail API連携解析

### ファイル: `modules/mailer.py`

#### 認証状態

**OAuth2.0フロー**:
```python
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def get_gmail_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)
```

**評価**: ✅ 標準的なOAuth2.0実装

#### メール送信実装

**現在の実装**:
```python
def send_email(to, subject, body_html):
    try:
        service = get_gmail_service()
        message = create_message(to, subject, body_html)
        send_message(service, 'me', message)
        logging.info(f"Email sent to {to}")
    except Exception as e:
        logging.error(f"Email send error: {e}")
```

**問題点**:
1. レート制限未対応（Gmail API: 100通/秒）
2. エラー時のリトライなし
3. バッチ送信未対応

**推奨実装**:
```python
from googleapiclient.errors import HttpError
import time

@rate_limit(calls=100, period=1)  # 100通/秒制限
def send_email_with_retry(to, subject, body_html, max_retries=3):
    """
    リトライ機能付きメール送信
    """
    service = get_gmail_service()
    message = create_message(to, subject, body_html)

    for attempt in range(max_retries):
        try:
            send_message(service, 'me', message)
            logging.info(f"Email sent to {to}")
            return True
        except HttpError as e:
            if e.resp.status in [403, 429]:  # Rate limit
                wait_time = 2 ** attempt
                logging.warning(f"Rate limited, waiting {wait_time}s")
                time.sleep(wait_time)
            else:
                logging.error(f"Email send error: {e}")
                return False

    logging.error(f"Failed to send email after {max_retries} retries")
    return False

def send_batch_emails(recipients_data):
    """
    バッチメール送信（複数宛先）
    """
    results = []
    for data in recipients_data:
        result = send_email_with_retry(
            data['to'],
            data['subject'],
            data['body']
        )
        results.append(result)
        time.sleep(0.01)  # 最低10ms間隔

    return results
```

#### HTMLテンプレート品質

**評価項目**:
- レスポンシブデザイン: ✅ 実装済み
- アクセシビリティ: ⚠️ alt属性不足
- スパムフィルタ対策: ⚠️ 要改善

**推奨改善**:
```html
<!-- 画像のalt属性必須 -->
<img src="{{cover_image}}" alt="{{title}}のカバー画像" style="max-width:100%;">

<!-- プレーンテキスト版も提供 -->
Content-Type: multipart/alternative;
```

---

## Google Calendar API連携解析

### ファイル: `modules/calendar_integration.py`

#### 認証状態

**OAuth2.0スコープ**:
```python
SCOPES = ['https://www.googleapis.com/auth/calendar']
```

**評価**: ✅ 適切（最小権限の原則に反するが、機能的に必要）

#### イベント作成実装

**現在の実装**:
```python
def add_calendar_event(title, date, description, url):
    try:
        service = get_calendar_service()
        event = {
            'summary': title,
            'description': f"{description}\n{url}",
            'start': {
                'date': date,
                'timeZone': 'Asia/Tokyo',
            },
            'end': {
                'date': date,
                'timeZone': 'Asia/Tokyo',
            }
        }

        result = service.events().insert(
            calendarId='primary',
            body=event
        ).execute()

        logging.info(f"Calendar event created: {result['id']}")
    except Exception as e:
        logging.error(f"Calendar event error: {e}")
```

**問題点**:
1. 重複イベントチェックなし
2. カレンダーID固定（primary）
3. リマインダー未設定
4. 色分けなし

**推奨実装**:
```python
from datetime import datetime, timedelta

def add_calendar_event_enhanced(title, date, description, url, category='anime'):
    """
    拡張カレンダーイベント作成
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
        'source': {
            'title': 'MangaAnime Info System',
            'url': url
        }
    }

    try:
        result = service.events().insert(
            calendarId='primary',
            body=event
        ).execute()

        logging.info(f"Calendar event created: {result['id']}")
        return result['id']
    except HttpError as e:
        logging.error(f"Calendar event error: {e}")
        return None

def check_existing_event(service, title, date):
    """
    既存イベントの確認
    """
    time_min = f"{date}T00:00:00+09:00"
    time_max = f"{date}T23:59:59+09:00"

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

    return None
```

#### カレンダー同期戦略

**3ヶ月表示機能の実装**:
```python
def sync_calendar_3months():
    """
    3ヶ月分のリリース情報をカレンダーに同期
    """
    from datetime import datetime, timedelta
    import sqlite3

    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()

    today = datetime.now().date()
    end_date = today + timedelta(days=90)

    query = """
        SELECT w.title, r.release_date, r.platform, r.release_type, r.number
        FROM releases r
        JOIN works w ON r.work_id = w.id
        WHERE r.release_date BETWEEN ? AND ?
        AND r.calendar_synced = 0
        ORDER BY r.release_date
    """

    cursor.execute(query, (today, end_date))
    releases = cursor.fetchall()

    synced_count = 0
    for title, date, platform, rel_type, number in releases:
        event_title = f"{title} - {rel_type} {number}"
        description = f"Platform: {platform}"

        event_id = add_calendar_event_enhanced(
            event_title, date, description, ""
        )

        if event_id:
            # 同期フラグ更新
            cursor.execute(
                "UPDATE releases SET calendar_synced = 1 WHERE work_id = ?",
                (title,)
            )
            synced_count += 1

    conn.commit()
    conn.close()

    logging.info(f"Synced {synced_count} events to calendar")
    return synced_count
```

---

## 設定ファイル解析

### ファイル: `config.json`

#### 現在の構造

```json
{
  "anime_sources": {
    "anilist": {
      "enabled": true,
      "api_url": "https://graphql.anilist.co"
    },
    "syoboi": {
      "enabled": true,
      "api_url": "https://cal.syoboi.jp/db.php"
    }
  },
  "manga_sources": {
    "rss_feeds": [
      {
        "name": "BookWalker",
        "url": "https://bookwalker.jp/rss/",
        "enabled": true
      },
      {
        "name": "MagaPoke",
        "url": "https://pocket.shonenmagazine.com/rss",
        "enabled": true
      }
    ]
  },
  "notification": {
    "email": {
      "enabled": true,
      "recipients": ["user@example.com"]
    },
    "calendar": {
      "enabled": true,
      "calendar_id": "primary"
    }
  },
  "filter": {
    "ng_keywords": ["エロ", "R18", "成人向け", "BL", "百合"]
  },
  "schedule": {
    "run_time": "08:00",
    "timezone": "Asia/Tokyo"
  }
}
```

#### 評価

**✅ 良い点**:
- 構造化された設定
- 各ソースのON/OFF制御可能

**⚠️ 改善点**:
1. 機密情報の混在（環境変数化すべき）
2. バリデーション機能なし
3. スキーマ定義なし

#### 推奨改善

**1. 環境変数への分離**:

```bash
# .env
GMAIL_CREDENTIALS_PATH=/path/to/credentials.json
GMAIL_TOKEN_PATH=/path/to/token.json
CALENDAR_CREDENTIALS_PATH=/path/to/cal_credentials.json
NOTIFICATION_EMAIL=user@example.com
DATABASE_PATH=/path/to/db.sqlite3
LOG_LEVEL=INFO
```

**2. 設定スキーマ定義**:

```python
# config/schema.py
from pydantic import BaseModel, HttpUrl, validator
from typing import List, Optional

class AnimeSourceConfig(BaseModel):
    enabled: bool
    api_url: HttpUrl

class RSSFeedConfig(BaseModel):
    name: str
    url: HttpUrl
    enabled: bool

class EmailNotificationConfig(BaseModel):
    enabled: bool
    recipients: List[str]

    @validator('recipients')
    def validate_emails(cls, v):
        import re
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        for email in v:
            if not re.match(email_regex, email):
                raise ValueError(f'Invalid email: {email}')
        return v

class Config(BaseModel):
    anime_sources: dict
    manga_sources: dict
    notification: dict
    filter: dict
    schedule: dict
```

**3. 設定読み込みヘルパー**:

```python
# modules/config_helper.py
import json
import os
from pathlib import Path
from typing import Optional

class ConfigManager:
    """設定管理クラス"""

    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        self._config = None
        self.load()

    def load(self) -> dict:
        """設定ファイルの読み込み"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            self._config = json.load(f)

        # 環境変数でオーバーライド
        self._apply_env_overrides()

        return self._config

    def _apply_env_overrides(self):
        """環境変数による設定のオーバーライド"""
        if email := os.getenv('NOTIFICATION_EMAIL'):
            self._config['notification']['email']['recipients'] = [email]

        if db_path := os.getenv('DATABASE_PATH'):
            self._config['database_path'] = db_path

    def get(self, key: str, default=None):
        """ドット記法での設定取得"""
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default

        return value if value is not None else default

    def is_enabled(self, source_path: str) -> bool:
        """ソースの有効/無効チェック"""
        return self.get(f"{source_path}.enabled", False)

# 使用例
config = ConfigManager()
if config.is_enabled('anime_sources.anilist'):
    # AniList APIを使用
    pass
```

---

## 総合評価と推奨事項

### 評価サマリー

| 項目 | 現状 | 評価 | 優先度 |
|------|------|------|--------|
| AniList API | 基本実装済み | ⚠️ | 高 |
| しょぼいカレンダー | 基本実装済み | ⚠️ | 中 |
| RSS フィード | 実装済み | ⚠️ | 中 |
| Gmail API | 実装済み | ⚠️ | 高 |
| Calendar API | 実装済み | ⚠️ | 高 |
| 設定管理 | JSON実装 | ⚠️ | 高 |

### 緊急対応が必要な項目（Priority: High）

#### 1. レート制限の実装

**影響**: API制限によるサービス停止リスク

**対策**:
```python
# modules/rate_limiter.py を作成
import time
from collections import deque
from functools import wraps
import threading

class RateLimiter:
    """スレッドセーフなレート制限クラス"""

    def __init__(self, calls: int, period: int):
        self.calls = calls
        self.period = period
        self.timestamps = deque()
        self.lock = threading.Lock()

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with self.lock:
                now = time.time()

                # 期間外のタイムスタンプを削除
                while self.timestamps and now - self.timestamps[0] >= self.period:
                    self.timestamps.popleft()

                # レート制限チェック
                if len(self.timestamps) >= self.calls:
                    sleep_time = self.period - (now - self.timestamps[0])
                    time.sleep(sleep_time)
                    now = time.time()

                self.timestamps.append(now)

            return func(*args, **kwargs)

        return wrapper

# 使用例
anilist_limiter = RateLimiter(calls=90, period=60)
gmail_limiter = RateLimiter(calls=100, period=1)
```

#### 2. エラーハンドリングの強化

**影響**: 一時的なネットワークエラーでシステム停止

**対策**:
```python
# modules/error_handler.py
from functools import wraps
import logging
import time
from typing import Callable, Optional

class RetryConfig:
    """リトライ設定"""
    def __init__(
        self,
        max_retries: int = 3,
        backoff_factor: float = 2.0,
        retry_on: tuple = (Exception,)
    ):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.retry_on = retry_on

def with_retry(config: Optional[RetryConfig] = None):
    """リトライデコレータ"""
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(config.max_retries):
                try:
                    return func(*args, **kwargs)
                except config.retry_on as e:
                    last_exception = e
                    if attempt < config.max_retries - 1:
                        wait_time = config.backoff_factor ** attempt
                        logging.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}), "
                            f"retrying in {wait_time}s: {e}"
                        )
                        time.sleep(wait_time)

            logging.error(
                f"{func.__name__} failed after {config.max_retries} retries"
            )
            raise last_exception

        return wrapper

    return decorator

# 使用例
@with_retry(RetryConfig(max_retries=3, backoff_factor=2.0))
@anilist_limiter
def fetch_anilist_data(query, variables):
    # 実装
    pass
```

#### 3. 設定管理の環境変数化

**影響**: セキュリティリスク（認証情報のハードコード）

**対策**:
```bash
# .env.example を作成
cp config.json config.json.example
# 機密情報を削除してGitに追加

# .gitignore に追加
echo "config.json" >> .gitignore
echo ".env" >> .gitignore
echo "token.json" >> .gitignore
echo "credentials.json" >> .gitignore
```

### 中優先度の改善項目（Priority: Medium）

#### 4. タイムアウト設定の追加

**すべてのHTTPリクエストに以下を適用**:
```python
DEFAULT_TIMEOUT = 10  # 秒

response = requests.get(url, timeout=DEFAULT_TIMEOUT)
```

#### 5. ログレベルの最適化

```python
# modules/logger.py
import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(name: str, log_file: str, level=logging.INFO):
    """ロガーのセットアップ"""
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    # コンソール出力も追加
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    return logger
```

#### 6. データベーススキーマの拡張

**RSS管理テーブル追加**:
```sql
-- migrations/004_rss_management.sql
CREATE TABLE IF NOT EXISTS rss_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    url TEXT NOT NULL,
    enabled INTEGER DEFAULT 1,
    etag TEXT,
    last_modified TEXT,
    last_fetch DATETIME,
    last_success DATETIME,
    error_count INTEGER DEFAULT 0,
    last_error TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_rss_enabled ON rss_sources(enabled);
CREATE INDEX idx_rss_last_fetch ON rss_sources(last_fetch);
```

### 低優先度の機能拡張（Priority: Low）

#### 7. キャッシュ機能の追加

```python
# modules/cache.py
import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

class SimpleCache:
    """シンプルなファイルベースキャッシュ"""

    def __init__(self, cache_dir: str = ".cache", ttl: int = 3600):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl = ttl

    def _get_cache_path(self, key: str) -> Path:
        """キーからキャッシュファイルパスを生成"""
        hashed = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{hashed}.json"

    def get(self, key: str):
        """キャッシュから取得"""
        cache_path = self._get_cache_path(key)

        if not cache_path.exists():
            return None

        with open(cache_path, 'r') as f:
            data = json.load(f)

        # TTLチェック
        cached_at = datetime.fromisoformat(data['cached_at'])
        if datetime.now() - cached_at > timedelta(seconds=self.ttl):
            cache_path.unlink()
            return None

        return data['value']

    def set(self, key: str, value):
        """キャッシュに保存"""
        cache_path = self._get_cache_path(key)

        data = {
            'value': value,
            'cached_at': datetime.now().isoformat()
        }

        with open(cache_path, 'w') as f:
            json.dump(data, f)

    def clear(self):
        """キャッシュをクリア"""
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
```

#### 8. メトリクス収集

```python
# modules/metrics.py
import time
from functools import wraps
from datetime import datetime
import json
from pathlib import Path

class MetricsCollector:
    """メトリクス収集クラス"""

    def __init__(self, metrics_file: str = "metrics.json"):
        self.metrics_file = Path(metrics_file)
        self.metrics = self.load_metrics()

    def load_metrics(self) -> dict:
        """メトリクスファイルの読み込み"""
        if self.metrics_file.exists():
            with open(self.metrics_file, 'r') as f:
                return json.load(f)
        return {}

    def save_metrics(self):
        """メトリクスファイルの保存"""
        with open(self.metrics_file, 'w') as f:
            json.dump(self.metrics, f, indent=2)

    def record_api_call(self, api_name: str, duration: float, success: bool):
        """API呼び出しの記録"""
        if api_name not in self.metrics:
            self.metrics[api_name] = {
                'total_calls': 0,
                'success_calls': 0,
                'failed_calls': 0,
                'total_duration': 0,
                'avg_duration': 0,
                'last_call': None
            }

        m = self.metrics[api_name]
        m['total_calls'] += 1
        m['total_duration'] += duration
        m['avg_duration'] = m['total_duration'] / m['total_calls']
        m['last_call'] = datetime.now().isoformat()

        if success:
            m['success_calls'] += 1
        else:
            m['failed_calls'] += 1

        self.save_metrics()

    def measure(self, api_name: str):
        """API呼び出し測定デコレータ"""
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start = time.time()
                success = False

                try:
                    result = func(*args, **kwargs)
                    success = True
                    return result
                finally:
                    duration = time.time() - start
                    self.record_api_call(api_name, duration, success)

            return wrapper
        return decorator

# 使用例
metrics = MetricsCollector()

@metrics.measure('anilist')
@anilist_limiter
def fetch_anilist_data(query, variables):
    # 実装
    pass
```

---

## 実装優先順位ロードマップ

### Phase 1: 緊急対応（1週間以内）

1. **レート制限実装** - `modules/rate_limiter.py`
2. **エラーハンドリング強化** - `modules/error_handler.py`
3. **環境変数化** - `.env`, `.env.example`, `modules/config_helper.py`

### Phase 2: 安定性向上（2週間以内）

4. **タイムアウト設定追加** - 全HTTPリクエスト
5. **ロガー改善** - `modules/logger.py`
6. **RSS管理テーブル** - `migrations/004_rss_management.sql`

### Phase 3: 機能拡張（1ヶ月以内）

7. **キャッシュ機能** - `modules/cache.py`
8. **メトリクス収集** - `modules/metrics.py`
9. **カレンダー同期強化** - 重複チェック、色分け

---

## セキュリティチェックリスト

### 認証情報管理

- [ ] `credentials.json` を `.gitignore` に追加
- [ ] `token.json` を `.gitignore` に追加
- [ ] 環境変数化の完了
- [ ] サンプル設定ファイルの作成（`.example`）

### API セキュリティ

- [ ] レート制限の実装
- [ ] タイムアウトの設定
- [ ] HTTPS のみ使用
- [ ] User-Agent の設定

### データベース

- [ ] SQLインジェクション対策（パラメータ化クエリ）
- [ ] バックアップ戦略の確立
- [ ] 定期的なメンテナンス

---

## モニタリング推奨項目

### 監視対象

1. **API レスポンスタイム**
   - AniList: < 2秒
   - しょぼいカレンダー: < 3秒
   - RSS: < 5秒

2. **エラー率**
   - 全API: < 5%

3. **メール送信成功率**
   - Gmail API: > 95%

4. **カレンダー同期成功率**
   - Calendar API: > 95%

### アラート条件

```python
# modules/monitoring.py
class HealthChecker:
    """ヘルスチェッククラス"""

    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector

    def check_api_health(self, api_name: str) -> dict:
        """APIヘルスチェック"""
        m = self.metrics.metrics.get(api_name, {})

        total = m.get('total_calls', 0)
        failed = m.get('failed_calls', 0)

        if total == 0:
            return {'status': 'unknown', 'error_rate': 0}

        error_rate = failed / total

        status = 'healthy'
        if error_rate > 0.1:  # 10%以上
            status = 'critical'
        elif error_rate > 0.05:  # 5%以上
            status = 'warning'

        return {
            'status': status,
            'error_rate': error_rate,
            'total_calls': total,
            'failed_calls': failed
        }

    def get_overall_health(self) -> dict:
        """全体のヘルスチェック"""
        apis = ['anilist', 'syoboi', 'gmail', 'calendar']
        results = {}

        for api in apis:
            results[api] = self.check_api_health(api)

        # 全体ステータスの判定
        statuses = [r['status'] for r in results.values()]

        if 'critical' in statuses:
            overall = 'critical'
        elif 'warning' in statuses:
            overall = 'warning'
        else:
            overall = 'healthy'

        return {
            'overall_status': overall,
            'api_status': results,
            'checked_at': datetime.now().isoformat()
        }
```

---

## テスト推奨事項

### ユニットテスト

```python
# tests/test_api_integration.py
import pytest
from modules.anime_anilist import fetch_anilist_data
from modules.rate_limiter import RateLimiter

def test_anilist_api_basic():
    """AniList API基本テスト"""
    query = """
    query {
        Media(id: 1) {
            title { romaji }
        }
    }
    """

    result = fetch_anilist_data(query, {})
    assert result is not None
    assert 'Media' in result

def test_rate_limiter():
    """レート制限テスト"""
    import time

    limiter = RateLimiter(calls=5, period=1)

    @limiter
    def test_func():
        return time.time()

    times = []
    for _ in range(7):
        times.append(test_func())

    # 6回目以降は1秒以上の間隔があるはず
    assert times[6] - times[0] >= 1.0
```

### 統合テスト

```python
# tests/test_integration.py
import pytest
from modules.config_helper import ConfigManager
from modules.anime_anilist import fetch_anilist_data
from modules.mailer import send_email
from modules.calendar_integration import add_calendar_event

def test_full_workflow():
    """完全ワークフローテスト"""
    # 1. 設定読み込み
    config = ConfigManager()
    assert config.is_enabled('anime_sources.anilist')

    # 2. データ取得
    # ... 省略

    # 3. メール送信（テストモード）
    # ... 省略

    # 4. カレンダー登録（テストモード）
    # ... 省略
```

---

## まとめ

本プロジェクトのAPI・外部連携は基本機能は実装されていますが、以下の改善が必要です:

### 緊急対応項目（1週間以内）
1. **レート制限の実装** - API制限回避
2. **エラーハンドリング強化** - リトライロジック
3. **環境変数化** - セキュリティ向上

### 推奨改善項目（2-4週間）
4. タイムアウト設定
5. ログレベル最適化
6. データベーススキーマ拡張

### 機能拡張項目（1-2ヶ月）
7. キャッシュ機能
8. メトリクス収集
9. モニタリング強化

これらの改善により、システムの安定性、セキュリティ、保守性が大幅に向上します。

---

**次のアクション**: Phase 1の緊急対応項目の実装を推奨します。

**解析完了日時**: 2025-12-06
**担当エージェント**: Backend Developer Agent
