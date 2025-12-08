# Google Calendar API ラッパー 使用ガイド

## 概要

`modules/calendar_api.py` は Google Calendar API の Python ラッパーモジュールです。
OAuth2.0認証、イベントのCRUD操作、バッチ処理、エラーハンドリングを提供します。

## 目次

1. [セットアップ](#セットアップ)
2. [基本的な使い方](#基本的な使い方)
3. [イベント操作](#イベント操作)
4. [バッチ処理](#バッチ処理)
5. [エラーハンドリング](#エラーハンドリング)
6. [ベストプラクティス](#ベストプラクティス)

---

## セットアップ

### 1. 必要なライブラリのインストール

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### 2. OAuth2.0認証情報の取得

1. [Google Cloud Console](https://console.cloud.google.com/) でプロジェクトを作成
2. Google Calendar API を有効化
3. OAuth2.0クライアントIDを作成（デスクトップアプリ）
4. 認証情報JSONファイルをダウンロード

### 3. 初回認証の実行

```python
from modules.calendar_api import GoogleCalendarAPI

# 初回実行時、ブラウザで認証が必要
calendar = GoogleCalendarAPI(
    token_file='auth/calendar_token.json',
    calendar_id='primary'
)
```

認証成功後、`auth/calendar_token.json` にトークンが保存されます。

---

## 基本的な使い方

### インスタンスの作成

```python
from modules.calendar_api import GoogleCalendarAPI

# デフォルト設定（プライマリカレンダー）
calendar = GoogleCalendarAPI()

# カスタム設定
calendar = GoogleCalendarAPI(
    token_file='path/to/token.json',
    calendar_id='your_calendar_id@group.calendar.google.com'
)
```

### カレンダー情報の取得

```python
# カレンダー情報を表示
info = calendar.get_calendar_info()
print(f"カレンダー: {info['summary']}")
print(f"タイムゾーン: {info['timeZone']}")
```

---

## イベント操作

### イベントの作成

#### シンプルな作成

```python
from datetime import datetime

event = calendar.create_event(
    summary='呪術廻戦 第10話配信',
    start_time=datetime(2025, 12, 10, 23, 0),
    duration_minutes=30
)

print(f"イベント作成: {event['id']}")
```

#### 詳細設定付き作成

```python
from modules.calendar_api import create_reminder

# リマインダーを設定
reminders = [
    create_reminder('popup', 60),   # 1時間前にポップアップ
    create_reminder('email', 1440)  # 1日前にメール
]

event = calendar.create_event(
    summary='呪術廻戦 第10話配信',
    start_time=datetime(2025, 12, 10, 23, 0),
    duration_minutes=30,
    description='dアニメストアで配信開始',
    location='https://anime.dmkt-sp.jp/',
    color_id='9',  # ブルー
    reminders=reminders
)
```

#### カラーID一覧

| ID | 色 |
|----|---|
| 1 | ラベンダー |
| 2 | セージ |
| 3 | グレープ |
| 4 | フラミンゴ |
| 5 | バナナ |
| 6 | タンジェリン |
| 7 | ピーコック |
| 8 | グラファイト |
| 9 | ブルーベリー |
| 10 | バジル |
| 11 | トマト |

### イベントの取得

```python
# IDで取得
event = calendar.get_event('event_id_here')
print(f"タイトル: {event['summary']}")
print(f"開始: {event['start']['dateTime']}")

# 存在しない場合はEventNotFoundError
try:
    event = calendar.get_event('invalid_id')
except EventNotFoundError:
    print("イベントが見つかりません")
```

### イベントの更新

```python
# タイトルを変更
updated_event = calendar.update_event(
    event_id='event_id_here',
    updates={
        'summary': '呪術廻戦 第10話配信（更新）',
        'description': '配信時間が変更されました'
    }
)
```

### イベントの削除

```python
# イベントを削除
result = calendar.delete_event('event_id_here')

if result:
    print("削除成功")
```

---

## イベント検索・一覧取得

### 日付範囲で取得

```python
from datetime import datetime, timedelta

# 今月のイベントを取得
start_date = datetime.now().replace(day=1, hour=0, minute=0, second=0)
end_date = (start_date + timedelta(days=32)).replace(day=1)

events = calendar.get_events_by_date_range(start_date, end_date)

for event in events:
    print(f"{event['summary']} - {event['start']['dateTime']}")
```

### イベント一覧の取得

```python
# 今後1週間のイベント
events = calendar.list_events(
    time_min=datetime.now(),
    time_max=datetime.now() + timedelta(days=7),
    max_results=50
)

print(f"取得件数: {len(events)}")
```

### キーワード検索

```python
# "呪術廻戦"を含むイベントを検索
events = calendar.search_events('呪術廻戦')

for event in events:
    print(f"- {event['summary']}")
```

---

## バッチ処理

### 複数イベントの一括作成

```python
from datetime import datetime, timedelta

# 作成するイベントのデータ
events_data = [
    {
        'summary': '呪術廻戦 第10話',
        'start_time': datetime(2025, 12, 10, 23, 0),
        'duration_minutes': 30,
        'description': 'dアニメストア'
    },
    {
        'summary': 'SPY×FAMILY 第5話',
        'start_time': datetime(2025, 12, 11, 22, 30),
        'duration_minutes': 30,
        'description': 'dアニメストア'
    },
    {
        'summary': 'チェンソーマン 第8話',
        'start_time': datetime(2025, 12, 12, 23, 30),
        'duration_minutes': 30,
        'description': 'dアニメストア'
    }
]

# バッチ作成（50件ずつ処理）
success, failed, errors = calendar.batch_create_events(
    events_data,
    batch_size=50
)

print(f"成功: {success}件")
print(f"失敗: {failed}件")

if errors:
    print("エラー詳細:")
    for error in errors:
        print(f"  - {error}")
```

### 複数イベントの一括更新

```python
# 更新データのリスト（event_id, updates のタプル）
updates_data = [
    ('event_id_1', {'summary': '更新後タイトル1'}),
    ('event_id_2', {'summary': '更新後タイトル2'}),
    ('event_id_3', {'description': '詳細を追加'})
]

success, failed = calendar.batch_update_events(updates_data)
print(f"更新成功: {success}件, 失敗: {failed}件")
```

### 複数イベントの一括削除

```python
# 削除するイベントIDのリスト
event_ids = ['event_id_1', 'event_id_2', 'event_id_3']

success, failed = calendar.batch_delete_events(event_ids)
print(f"削除成功: {success}件, 失敗: {failed}件")
```

---

## エラーハンドリング

### 例外の種類

```python
from modules.calendar_api import (
    GoogleCalendarAPIError,      # 基底例外
    AuthenticationError,          # 認証エラー
    QuotaExceededError,           # クォータ超過
    EventNotFoundError            # イベント未検出
)
```

### エラーハンドリングの実装例

```python
try:
    event = calendar.create_event(
        summary='新しいイベント',
        start_time=datetime.now(),
        duration_minutes=60
    )

except AuthenticationError as e:
    print(f"認証エラー: {e}")
    print("再認証が必要です")

except QuotaExceededError as e:
    print(f"API制限超過: {e}")
    print("しばらく待ってから再試行してください")

except EventNotFoundError as e:
    print(f"イベントが見つかりません: {e}")

except GoogleCalendarAPIError as e:
    print(f"APIエラー: {e}")
```

### 自動リトライ

APIエラー時、自動的に3回までリトライされます（指数バックオフ）：

- 1回目: 1秒待機
- 2回目: 2秒待機
- 3回目: 4秒待機

```python
# 自動リトライが有効
# 一時的なネットワークエラーやレート制限は自動で対処
event = calendar.create_event(
    summary='イベント',
    start_time=datetime.now()
)
```

---

## ベストプラクティス

### 1. ロギングの設定

```python
import logging

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

calendar = GoogleCalendarAPI()
```

### 2. トークンの管理

```python
import os
from pathlib import Path

# トークンファイルを安全な場所に保存
token_dir = Path.home() / '.config' / 'calendar_app'
token_dir.mkdir(parents=True, exist_ok=True)

calendar = GoogleCalendarAPI(
    token_file=str(token_dir / 'token.json')
)
```

### 3. レート制限対策

```python
# 大量のイベントを作成する場合はバッチ処理を使用
events_data = [...]  # 大量のイベントデータ

# 50件ずつバッチ処理（推奨）
success, failed, errors = calendar.batch_create_events(
    events_data,
    batch_size=50
)
```

### 4. エラー時の詳細ログ

```python
import logging

logger = logging.getLogger(__name__)

try:
    event = calendar.create_event(...)

except GoogleCalendarAPIError as e:
    logger.error(f"イベント作成失敗: {e}", exc_info=True)
    # エラーをDBに記録するなど
```

### 5. 環境変数での設定管理

```python
import os

calendar = GoogleCalendarAPI(
    token_file=os.getenv('CALENDAR_TOKEN_FILE', 'auth/calendar_token.json'),
    calendar_id=os.getenv('CALENDAR_ID', 'primary')
)
```

---

## 実用例

### アニメ配信スケジュールの登録

```python
from datetime import datetime
from modules.calendar_api import GoogleCalendarAPI, create_reminder, format_event_summary

def register_anime_schedule(anime_data):
    """アニメ配信スケジュールをカレンダーに登録"""
    calendar = GoogleCalendarAPI()

    events_data = []

    for anime in anime_data:
        # イベントデータを作成
        event_data = {
            'summary': format_event_summary(
                anime['title'],
                f"第{anime['episode']}話"
            ),
            'start_time': anime['broadcast_time'],
            'duration_minutes': 30,
            'description': (
                f"配信プラットフォーム: {anime['platform']}\n"
                f"URL: {anime['url']}"
            ),
            'color_id': '9',  # ブルー
            'reminders': [
                create_reminder('popup', 30)  # 30分前に通知
            ]
        }
        events_data.append(event_data)

    # バッチ登録
    success, failed, errors = calendar.batch_create_events(events_data)

    print(f"登録完了: {success}件")
    if failed > 0:
        print(f"登録失敗: {failed}件")
        for error in errors:
            print(f"  - {error}")

# 使用例
anime_schedule = [
    {
        'title': '呪術廻戦',
        'episode': 10,
        'broadcast_time': datetime(2025, 12, 10, 23, 0),
        'platform': 'dアニメストア',
        'url': 'https://anime.dmkt-sp.jp/'
    },
    # ... 他のアニメ
]

register_anime_schedule(anime_schedule)
```

---

## トラブルシューティング

### Q1. 認証エラーが発生する

**A:** トークンファイルを削除して再認証してください。

```bash
rm auth/calendar_token.json
python your_script.py  # 再認証が実行されます
```

### Q2. レート制限エラーが頻発する

**A:** バッチ処理を使用し、`batch_size` を小さくしてください。

```python
# batch_sizeを減らす
success, failed, errors = calendar.batch_create_events(
    events_data,
    batch_size=25  # デフォルト50から減らす
)
```

### Q3. イベントが作成されない

**A:** イベントデータの検証を確認してください。

```python
# デバッグログを有効化
import logging
logging.basicConfig(level=logging.DEBUG)

# イベント作成を試行
event = calendar.create_event(...)
```

---

## 参考リンク

- [Google Calendar API ドキュメント](https://developers.google.com/calendar/api)
- [Python クイックスタート](https://developers.google.com/calendar/api/quickstart/python)
- [OAuth 2.0 ガイド](https://developers.google.com/identity/protocols/oauth2)

---

**作成日**: 2025-12-08
**Phase**: 17 - Google Calendar API統合
**バージョン**: 1.0.0
