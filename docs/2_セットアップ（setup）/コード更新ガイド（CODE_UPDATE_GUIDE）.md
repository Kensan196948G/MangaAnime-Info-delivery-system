# コード更新ガイド - Config.json構造変更対応

## 概要
config.jsonの構造を整理したため、既存のPythonコードも更新が必要です。
このガイドでは、変更前後の対応表と更新例を示します。

---

## 変更対応表

### 1. メール通知設定

#### 変更前
```python
# 複数の場所に分散
config['email_notifications_enabled']  # bool
config['notification_email']            # str
config['settings']['notification_email']  # str
config['notifications']['email']['enabled']  # bool
config['notifications']['email']['to']  # str
```

#### 変更後
```python
# notifications.email配下に統一
config['notifications']['email']['enabled']  # bool
config['notifications']['email']['to']  # str
config['notifications']['email']['subject_prefix']  # str
config['notifications']['email']['send_time']  # str
```

#### 更新例
```python
# 修正前
if config.get('email_notifications_enabled'):
    send_email(config['notification_email'], content)

# 修正後
if config['notifications']['email']['enabled']:
    send_email(
        config['notifications']['email']['to'],
        content,
        subject_prefix=config['notifications']['email']['subject_prefix']
    )
```

---

### 2. カレンダー設定

#### 変更前
```python
config['calendar_enabled']  # bool
config['calendar_id']  # str
config['settings']['calendar_enabled']  # bool
config['settings']['calendar_id']  # str
config['notifications']['calendar']['enabled']  # bool
config['notifications']['calendar']['calendar_id']  # str
```

#### 変更後
```python
config['notifications']['calendar']['enabled']  # bool
config['notifications']['calendar']['calendar_id']  # str
config['notifications']['calendar']['event_title_format']  # str
config['notifications']['calendar']['color_by_genre']  # bool
config['notifications']['calendar']['reminder_minutes']  # list[int]
```

#### 更新例
```python
# 修正前
if config.get('calendar_enabled'):
    add_to_calendar(config['calendar_id'], event)

# 修正後
calendar_config = config['notifications']['calendar']
if calendar_config['enabled']:
    add_to_calendar(
        calendar_config['calendar_id'],
        event,
        title_format=calendar_config['event_title_format'],
        reminders=calendar_config['reminder_minutes']
    )
```

---

### 3. NGキーワード設定

#### 変更前
```python
config['ng_keywords']  # list[str]
```

#### 変更後
```python
config['filters']['ng_keywords']  # list[str]
config['filters']['min_rating']  # float | None
config['filters']['excluded_genres']  # list[str]
```

#### 更新例
```python
# 修正前
ng_keywords = config.get('ng_keywords', [])
if any(keyword in title for keyword in ng_keywords):
    return False

# 修正後
filter_config = config['filters']
ng_keywords = filter_config['ng_keywords']
min_rating = filter_config.get('min_rating')

if any(keyword in title for keyword in ng_keywords):
    return False
if min_rating and rating < min_rating:
    return False
```

---

### 4. データソース設定

#### 変更前
```python
config['anime_sources']  # list[str]
config['manga_sources']  # list[str]
config['streaming_sources']  # list[str]
```

#### 変更後
```python
config['sources']['anime']  # list[str]
config['sources']['manga']  # list[str]
config['sources']['streaming']  # list[str]
config['sources']['retry_on_failure']  # bool
config['sources']['max_retries']  # int
config['sources']['timeout_seconds']  # int
```

#### 更新例
```python
# 修正前
for source in config['anime_sources']:
    fetch_anime_data(source)

# 修正後
source_config = config['sources']
for source in source_config['anime']:
    try:
        fetch_anime_data(
            source,
            timeout=source_config.get('timeout_seconds', 30)
        )
    except Exception as e:
        if source_config.get('retry_on_failure', True):
            retry_with_backoff(source, source_config['max_retries'])
```

---

### 5. スケジューリング設定

#### 変更前
```python
config['notification_time']  # str
config['settings']['notification_time']  # str
```

#### 変更後
```python
config['scheduling']['cron_expression']  # str
config['scheduling']['timezone']  # str
config['scheduling']['max_execution_time_minutes']  # int
config['scheduling']['concurrent_workers']  # int
```

#### 更新例
```python
# 修正前
notification_time = config.get('notification_time', '08:00')

# 修正後
scheduling = config['scheduling']
cron_expr = scheduling['cron_expression']
timezone = scheduling['timezone']
```

---

## ヘルパー関数の実装

### config_helper.py

```python
"""
config.json アクセス用ヘルパー関数
"""

from typing import Any, Optional
from pathlib import Path
import json


class ConfigHelper:
    """設定ファイル読み込みヘルパー"""

    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        self._config = None
        self.load()

    def load(self):
        """設定ファイルを読み込み"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self._config = json.load(f)

    def reload(self):
        """設定ファイルを再読み込み"""
        self.load()

    @property
    def config(self) -> dict:
        """設定全体を取得"""
        return self._config

    # Email設定
    @property
    def email_enabled(self) -> bool:
        return self._config['notifications']['email']['enabled']

    @property
    def email_to(self) -> str:
        return self._config['notifications']['email']['to']

    @property
    def email_subject_prefix(self) -> str:
        return self._config['notifications']['email']['subject_prefix']

    @property
    def email_send_time(self) -> str:
        return self._config['notifications']['email']['send_time']

    # Calendar設定
    @property
    def calendar_enabled(self) -> bool:
        return self._config['notifications']['calendar']['enabled']

    @property
    def calendar_id(self) -> str:
        return self._config['notifications']['calendar']['calendar_id']

    @property
    def calendar_title_format(self) -> str:
        return self._config['notifications']['calendar']['event_title_format']

    @property
    def calendar_reminders(self) -> list:
        return self._config['notifications']['calendar']['reminder_minutes']

    # Filters設定
    @property
    def ng_keywords(self) -> list:
        return self._config['filters']['ng_keywords']

    @property
    def min_rating(self) -> Optional[float]:
        return self._config['filters'].get('min_rating')

    @property
    def excluded_genres(self) -> list:
        return self._config['filters']['excluded_genres']

    # Sources設定
    @property
    def anime_sources(self) -> list:
        return self._config['sources']['anime']

    @property
    def manga_sources(self) -> list:
        return self._config['sources']['manga']

    @property
    def streaming_sources(self) -> list:
        return self._config['sources']['streaming']

    # Database設定
    @property
    def db_path(self) -> str:
        return self._config.get('database', {}).get('path', 'db.sqlite3')

    # Logging設定
    @property
    def log_level(self) -> str:
        return self._config.get('logging', {}).get('level', 'INFO')

    @property
    def log_file(self) -> str:
        return self._config.get('logging', {}).get('file', 'logs/system.log')


# グローバルインスタンス
_config_helper = None


def get_config() -> ConfigHelper:
    """設定ヘルパーのシングルトンインスタンスを取得"""
    global _config_helper
    if _config_helper is None:
        _config_helper = ConfigHelper()
    return _config_helper
```

---

## 使用例

### 既存コードの更新

#### Before (modules/mailer.py)
```python
import json

with open('config.json') as f:
    config = json.load(f)

if config['email_notifications_enabled']:
    send_mail(
        to=config['notification_email'],
        subject="New Release",
        body=body
    )
```

#### After (modules/mailer.py)
```python
from config_helper import get_config

config = get_config()

if config.email_enabled:
    send_mail(
        to=config.email_to,
        subject=f"{config.email_subject_prefix} New Release",
        body=body
    )
```

---

### 新規実装での使用

```python
from config_helper import get_config

def check_filters(title: str, rating: float, genres: list) -> bool:
    """フィルタリングチェック"""
    config = get_config()

    # NGキーワードチェック
    for keyword in config.ng_keywords:
        if keyword in title:
            return False

    # 最低評価チェック
    if config.min_rating and rating < config.min_rating:
        return False

    # 除外ジャンルチェック
    if any(genre in config.excluded_genres for genre in genres):
        return False

    return True
```

---

## マイグレーションチェックリスト

更新が必要なファイルと確認項目:

### 必須更新ファイル
- [ ] `release_notifier.py` - メイン実行スクリプト
- [ ] `modules/mailer.py` - メール送信処理
- [ ] `modules/calendar.py` - カレンダー処理
- [ ] `modules/filter_logic.py` - フィルタリング処理
- [ ] `modules/db.py` - データベース処理

### 確認項目
- [ ] `config['email_notifications_enabled']` の使用箇所
- [ ] `config['notification_email']` の使用箇所
- [ ] `config['calendar_enabled']` の使用箇所
- [ ] `config['calendar_id']` の使用箇所
- [ ] `config['ng_keywords']` の使用箇所
- [ ] `config['*_sources']` の使用箇所
- [ ] `config['settings']` の使用箇所

### grep コマンド例
```bash
# 古い設定キーの使用箇所を検索
grep -r "email_notifications_enabled" .
grep -r "notification_email" .
grep -r "calendar_enabled" .
grep -r "ng_keywords" .
grep -r "\['settings'\]" .
```

---

## テスト

### ユニットテスト例

```python
import unittest
from config_helper import ConfigHelper


class TestConfigHelper(unittest.TestCase):
    def setUp(self):
        self.config = ConfigHelper('config.json')

    def test_email_settings(self):
        """メール設定のテスト"""
        self.assertIsInstance(self.config.email_enabled, bool)
        self.assertIsInstance(self.config.email_to, str)
        self.assertIn('@', self.config.email_to)

    def test_calendar_settings(self):
        """カレンダー設定のテスト"""
        self.assertIsInstance(self.config.calendar_enabled, bool)
        self.assertEqual(self.config.calendar_id, 'primary')

    def test_filters(self):
        """フィルタ設定のテスト"""
        self.assertIsInstance(self.config.ng_keywords, list)
        self.assertGreater(len(self.config.ng_keywords), 0)

    def test_sources(self):
        """データソース設定のテスト"""
        self.assertIn('anilist', self.config.anime_sources)
        self.assertIsInstance(self.config.manga_sources, list)


if __name__ == '__main__':
    unittest.main()
```

---

## トラブルシューティング

### KeyError: 'email_notifications_enabled'
**原因:** 古い設定キーを使用している
**解決:** `config['notifications']['email']['enabled']` に変更

### KeyError: 'settings'
**原因:** settingsセクションが削除された
**解決:** 該当する設定を新しい階層から取得

### 設定が反映されない
**原因:** ConfigHelperの再読み込みが必要
**解決:** `config.reload()` を呼び出す

---

**更新日:** 2025-12-06
**作成者:** Fullstack Developer Agent
