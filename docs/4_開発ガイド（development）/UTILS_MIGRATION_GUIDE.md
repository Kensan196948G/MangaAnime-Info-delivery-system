# ユーティリティモジュール移行ガイド

**対象**: 全開発者
**作成日**: 2025-12-08
**バージョン**: 1.0.0

---

## 📋 目次

1. [概要](#概要)
2. [クイックスタート](#クイックスタート)
3. [モジュール別ガイド](#モジュール別ガイド)
4. [移行チェックリスト](#移行チェックリスト)
5. [トラブルシューティング](#トラブルシューティング)
6. [ベストプラクティス](#ベストプラクティス)

---

## 概要

### なぜ移行が必要か？

現在のコードベースには、以下の問題があります:

- ❌ DB接続コードが**139ファイル**で重複
- ❌ 環境変数読み込みが**65ファイル**で重複
- ❌ バリデーションロジックが各所で異なる
- ❌ フォーマット処理が統一されていない

### 移行後のメリット

- ✅ **コード量83%削減**
- ✅ バグ修正が1箇所で完結
- ✅ 一貫したエラーハンドリング
- ✅ テストカバレッジ向上
- ✅ 新機能追加が容易

---

## クイックスタート

### 1分でできる最小限の移行

#### Before: 重複コード
```python
import sqlite3
import os

class MyFeature:
    def __init__(self):
        self.db_path = os.getenv('DATABASE_PATH', 'db.sqlite3')

    def get_data(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.execute("SELECT * FROM works")
            return cursor.fetchall()
        finally:
            conn.close()
```

#### After: ユーティリティ使用
```python
from modules.utils.database import get_db_connection

class MyFeature:
    def get_data(self):
        with get_db_connection() as conn:
            cursor = conn.execute("SELECT * FROM works")
            return cursor.fetchall()
```

**削減**: 14行 → 5行 (64%削減)

---

## モジュール別ガイド

### 1. modules.utils.database

#### 基本的な使い方

**パターン1: コンテキストマネージャー (推奨)**
```python
from modules.utils.database import get_db_connection

def get_all_works():
    with get_db_connection() as conn:
        cursor = conn.execute("SELECT * FROM works")
        return cursor.fetchall()
```

**パターン2: クエリ実行ヘルパー**
```python
from modules.utils.database import execute_query

def get_work_by_id(work_id):
    query = "SELECT * FROM works WHERE id = ?"
    return execute_query(query, (work_id,), fetch_one=True)
```

**パターン3: DatabaseManager取得**
```python
from modules.utils.database import get_db_manager

def advanced_operation():
    db = get_db_manager()
    # DatabaseManagerの全機能が使える
    return db.get_works_by_type('anime')
```

#### 主要関数一覧

| 関数 | 用途 | 戻り値 |
|------|------|--------|
| `get_db_connection(db_path)` | DB接続取得 | Context Manager |
| `get_db_path(custom_path)` | DBパス取得 | str |
| `get_db_manager(db_path)` | DatabaseManager取得 | DatabaseManager |
| `execute_query(query, params)` | クエリ実行 | List[Row] |
| `check_table_exists(table)` | テーブル存在確認 | bool |
| `get_database_stats()` | DB統計取得 | dict |

#### 移行例

##### 例1: 単純なDB接続

```python
# Before
import sqlite3

conn = sqlite3.connect('db.sqlite3')
conn.row_factory = sqlite3.Row
cursor = conn.execute("SELECT * FROM works")
results = cursor.fetchall()
conn.close()

# After
from modules.utils.database import get_db_connection

with get_db_connection() as conn:
    cursor = conn.execute("SELECT * FROM works")
    results = cursor.fetchall()
```

##### 例2: クラス内のDB接続メソッド

```python
# Before
class DataManager:
    def __init__(self):
        self.db_path = 'db.sqlite3'

    def get_db_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_data(self):
        conn = self.get_db_connection()
        try:
            cursor = conn.execute("SELECT * FROM works")
            return cursor.fetchall()
        finally:
            conn.close()

# After
from modules.utils.database import get_db_connection

class DataManager:
    def get_data(self):
        with get_db_connection() as conn:
            cursor = conn.execute("SELECT * FROM works")
            return cursor.fetchall()
```

##### 例3: 複数のDB操作

```python
# Before
conn = sqlite3.connect('db.sqlite3')
try:
    conn.execute("INSERT INTO works ...")
    conn.execute("UPDATE releases ...")
    conn.commit()
except Exception as e:
    conn.rollback()
    raise
finally:
    conn.close()

# After
from modules.utils.database import get_db_connection

with get_db_connection() as conn:
    # 自動的にcommit/rollbackされる
    conn.execute("INSERT INTO works ...")
    conn.execute("UPDATE releases ...")
```

---

### 2. modules.utils.config

#### 基本的な使い方

**パターン1: 文字列設定**
```python
from modules.utils.config import ConfigHelper

db_path = ConfigHelper.get('DATABASE_PATH', './data/db.sqlite3')
sender_email = ConfigHelper.get('GMAIL_SENDER_EMAIL')
```

**パターン2: 型指定設定**
```python
is_test_mode = ConfigHelper.get_bool('TEST_MODE', False)
rate_limit = ConfigHelper.get_int('RATE_LIMIT_REQUESTS', 90)
ng_keywords = ConfigHelper.get_list('NG_KEYWORDS')
```

**パターン3: 構造化設定**
```python
from modules.utils.config import get_env_config

config = get_env_config()
# {
#   'database': {'path': '...', 'backup_enabled': True, ...},
#   'email': {'sender': '...', 'recipient': '...'},
#   ...
# }
```

#### 主要関数一覧

| 関数 | 用途 | 戻り値 |
|------|------|--------|
| `ConfigHelper.get(key, default)` | 文字列取得 | str |
| `ConfigHelper.get_bool(key, default)` | ブール値取得 | bool |
| `ConfigHelper.get_int(key, default)` | 整数取得 | int |
| `ConfigHelper.get_list(key, delimiter)` | リスト取得 | List[str] |
| `ConfigHelper.get_path(key, ensure_exists)` | パス取得 | Path |
| `get_env_config()` | 全設定取得 | dict |
| `validate_required_config()` | 必須設定検証 | List[str] |

#### 移行例

##### 例1: 環境変数読み込み

```python
# Before
import os

db_path = os.getenv('DATABASE_PATH', './data/db.sqlite3')
test_mode = os.getenv('TEST_MODE', 'false').lower() == 'true'
rate_limit = int(os.getenv('RATE_LIMIT_REQUESTS', '90'))
ng_keywords_str = os.getenv('NG_KEYWORDS', '')
ng_keywords = [k.strip() for k in ng_keywords_str.split(',')] if ng_keywords_str else []

# After
from modules.utils.config import ConfigHelper

db_path = ConfigHelper.get('DATABASE_PATH')
test_mode = ConfigHelper.get_bool('TEST_MODE')
rate_limit = ConfigHelper.get_int('RATE_LIMIT_REQUESTS', 90)
ng_keywords = ConfigHelper.get_list('NG_KEYWORDS')
```

##### 例2: 複数の環境変数

```python
# Before
sender = os.getenv('GMAIL_SENDER_EMAIL') or \
         gmail_config.get('from_email') or \
         os.getenv('GMAIL_ADDRESS')

if not sender:
    raise ValueError("Sender email not configured")

# After
from modules.utils.config import ConfigHelper

sender = ConfigHelper.get('GMAIL_SENDER_EMAIL')
if not sender:
    sender = ConfigHelper.get('GMAIL_ADDRESS')

if not sender:
    raise ValueError("Sender email not configured")
```

##### 例3: 設定検証

```python
# Before
required_vars = ['DATABASE_PATH', 'GMAIL_ADDRESS']
missing = [var for var in required_vars if not os.getenv(var)]
if missing:
    raise ValueError(f"Missing required config: {missing}")

# After
from modules.utils.config import validate_required_config

missing = validate_required_config()
if missing:
    raise ValueError(f"Missing required config: {missing}")
```

---

### 3. modules.utils.validation

#### 基本的な使い方

**パターン1: 基本的なバリデーション**
```python
from modules.utils.validation import is_valid_email, is_valid_url

if is_valid_email(email):
    send_notification(email)

if is_valid_url(url):
    fetch_data(url)
```

**パターン2: データ構造バリデーション**
```python
from modules.utils.validation import validate_work_data

work_data = {
    'title': 'タイトル',
    'type': 'anime',
    'official_url': 'https://example.com'
}

errors = validate_work_data(work_data)
if errors:
    raise ValueError(f"Validation errors: {errors}")
```

**パターン3: NGキーワードチェック**
```python
from modules.utils.validation import contains_ng_keywords
from modules.utils.config import get_ng_keywords

ng_keywords = get_ng_keywords()
if contains_ng_keywords(title, ng_keywords):
    logger.info(f"Filtered: {title}")
    return None
```

#### 主要関数一覧

| 関数 | 用途 | 戻り値 |
|------|------|--------|
| `is_valid_email(email)` | メール検証 | bool |
| `is_valid_url(url)` | URL検証 | bool |
| `is_valid_date(date_str, format)` | 日付検証 | bool |
| `validate_work_data(data)` | 作品データ検証 | List[str] |
| `validate_release_data(data)` | リリースデータ検証 | List[str] |
| `contains_ng_keywords(text, keywords)` | NGワードチェック | bool |
| `sanitize_string(text, max_length)` | 文字列サニタイズ | str |
| `safe_int(value, default)` | 安全な型変換 | int |

#### 移行例

##### 例1: メールバリデーション

```python
# Before
import re

def validate_email(email):
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

if validate_email(user_email):
    send_email(user_email)

# After
from modules.utils.validation import is_valid_email

if is_valid_email(user_email):
    send_email(user_email)
```

##### 例2: NGキーワードフィルタリング

```python
# Before
NG_KEYWORDS = ["エロ", "R18", "成人向け"]

def contains_ng_keywords(text):
    if not text:
        return False
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in NG_KEYWORDS)

if contains_ng_keywords(title):
    return None

# After
from modules.utils.validation import contains_ng_keywords
from modules.utils.config import get_ng_keywords

ng_keywords = get_ng_keywords()
if contains_ng_keywords(title, ng_keywords):
    return None
```

##### 例3: データバリデーション

```python
# Before
def validate_work(work):
    errors = []
    if not work.get('title'):
        errors.append('Title is required')
    if not work.get('type') or work['type'] not in ['anime', 'manga']:
        errors.append('Invalid work type')
    return errors

errors = validate_work(work_data)

# After
from modules.utils.validation import validate_work_data

errors = validate_work_data(work_data)
```

---

### 4. modules.utils.formatting

#### 基本的な使い方

**パターン1: 日付フォーマット**
```python
from modules.utils.formatting import format_date, format_japanese_date

# 標準フォーマット
date_str = format_date(release_date)  # "2025-12-08"

# 日本語フォーマット
jp_date = format_japanese_date(release_date)  # "2025年12月8日"
```

**パターン2: タイトルフォーマット**
```python
from modules.utils.formatting import format_release_title

title = format_release_title(
    work_title="進撃の巨人",
    release_type="episode",
    number="25",
    platform="Netflix"
)
# "進撃の巨人 第25話 (Netflix)"
```

**パターン3: 相対時間**
```python
from modules.utils.formatting import format_relative_time

relative = format_relative_time(created_at)  # "2時間前"
```

#### 主要関数一覧

| 関数 | 用途 | 戻り値 |
|------|------|--------|
| `format_date(date, format)` | 日付フォーマット | str |
| `format_japanese_date(date)` | 日本語日付 | str |
| `format_relative_time(dt)` | 相対時間 | str |
| `format_file_size(bytes)` | ファイルサイズ | str |
| `format_release_title(...)` | リリースタイトル | str |
| `format_email_subject(...)` | メール件名 | str |
| `format_duration(seconds)` | 期間表記 | str |
| `format_percentage(value)` | パーセント表記 | str |

#### 移行例

##### 例1: 日付フォーマット

```python
# Before
from datetime import datetime

date_str = release_date.strftime('%Y-%m-%d')
jp_date = release_date.strftime('%Y年%m月%d日')
jp_date = jp_date.replace('年0', '年').replace('月0', '月')

# After
from modules.utils.formatting import format_date, format_japanese_date

date_str = format_date(release_date)
jp_date = format_japanese_date(release_date)
```

##### 例2: タイトルフォーマット

```python
# Before
def format_title(work_title, release_type, number, platform=None):
    parts = [work_title]

    if release_type == 'episode':
        parts.append(f"第{number}話")
    elif release_type == 'volume':
        parts.append(f"第{number}巻")

    if platform:
        parts.append(f"({platform})")

    return ' '.join(parts)

title = format_title("進撃の巨人", "episode", "25", "Netflix")

# After
from modules.utils.formatting import format_release_title

title = format_release_title("進撃の巨人", "episode", "25", "Netflix")
```

##### 例3: メール件名生成

```python
# Before
subject = f"[アニメ・マンガ情報] {work_title} 第{number}話"

# After
from modules.utils.formatting import format_email_subject

subject = format_email_subject(work_title, "episode", number)
```

---

## 移行チェックリスト

### ファイル移行時のチェックポイント

#### 開始前
- [ ] 対象ファイルをバックアップ
- [ ] Gitで現在の状態をcommit
- [ ] 関連するテストファイルを確認

#### コード変更
- [ ] 不要なimport文を削除
- [ ] utils モジュールをimport
- [ ] 重複コードをutils呼び出しに置換
- [ ] エラーハンドリングを確認
- [ ] 型ヒントを追加/修正

#### テスト
- [ ] 既存テストが通ることを確認
- [ ] 新しいエッジケースをテスト
- [ ] パフォーマンステスト実施

#### 完了後
- [ ] コードレビュー依頼
- [ ] ドキュメント更新
- [ ] バックアップファイル削除
- [ ] 移行完了をチームに報告

### 完全な移行例

```bash
# 1. バックアップ
cp modules/my_module.py modules/my_module.py.bak

# 2. ファイル編集
vim modules/my_module.py

# 3. テスト実行
python3 -m pytest tests/test_my_module.py -v

# 4. 全体テスト
python3 -m pytest tests/ -k "not slow"

# 5. コミット
git add modules/my_module.py
git commit -m "refactor: migrate my_module to use utils"

# 6. バックアップ削除
rm modules/my_module.py.bak
```

---

## トラブルシューティング

### Q1: インポートエラーが発生する

```python
ImportError: No module named 'modules.utils'
```

**解決方法**:
```bash
# PYTHONPATHを確認
echo $PYTHONPATH

# プロジェクトルートから実行
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system
python3 your_script.py
```

### Q2: DB接続エラー

```python
sqlite3.OperationalError: unable to open database file
```

**解決方法**:
```python
# DBパスを明示的に指定
from modules.utils.database import get_db_connection

with get_db_connection('/path/to/db.sqlite3') as conn:
    # ...
```

### Q3: 環境変数が読み込まれない

```python
# None が返される
db_path = ConfigHelper.get('DATABASE_PATH')
```

**解決方法**:
```bash
# 環境変数を設定
export DATABASE_PATH=/path/to/db.sqlite3

# または .env ファイルを使用
echo "DATABASE_PATH=/path/to/db.sqlite3" >> .env
```

### Q4: テストが失敗する

**解決方法**:
```python
# テスト用のDB接続を使用
from modules.utils.database import get_db_connection

# テストフィクスチャ
@pytest.fixture
def test_db():
    with get_db_connection(':memory:') as conn:
        # テーブル作成
        conn.execute("CREATE TABLE works ...")
        yield conn
```

---

## ベストプラクティス

### DO: 推奨される使い方

✅ **コンテキストマネージャーを使う**
```python
with get_db_connection() as conn:
    # 自動的にクリーンアップ
    results = conn.execute("SELECT ...").fetchall()
```

✅ **型ヒントを活用**
```python
from typing import List, Dict, Optional
from modules.utils.database import get_db_connection

def get_works(work_type: str) -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        cursor = conn.execute("SELECT * FROM works WHERE type = ?", (work_type,))
        return [dict(row) for row in cursor.fetchall()]
```

✅ **エラーハンドリングを明示**
```python
from modules.utils.validation import is_valid_email, ValidationError

def send_notification(email: str):
    if not is_valid_email(email):
        raise ValidationError(f"Invalid email: {email}")

    # 送信処理
```

✅ **設定をモジュールトップで定義**
```python
from modules.utils.config import ConfigHelper

# モジュールレベルで定義
DB_PATH = ConfigHelper.get('DATABASE_PATH')
IS_TEST_MODE = ConfigHelper.get_bool('TEST_MODE')

def my_function():
    if IS_TEST_MODE:
        # テストモード処理
```

### DON'T: 避けるべき使い方

❌ **接続を閉じ忘れる**
```python
# BAD: closeし忘れる可能性
conn = get_simple_connection()
results = conn.execute("SELECT ...").fetchall()
# conn.close() を忘れている
```

❌ **環境変数を直接読み込む**
```python
# BAD: 直接os.getenv
import os
db_path = os.getenv('DATABASE_PATH')

# GOOD: ConfigHelperを使う
from modules.utils.config import ConfigHelper
db_path = ConfigHelper.get('DATABASE_PATH')
```

❌ **バリデーションロジックを重複させる**
```python
# BAD: 独自実装
def my_email_validator(email):
    return '@' in email and '.' in email

# GOOD: utilsを使う
from modules.utils.validation import is_valid_email
```

❌ **ハードコードされたパス**
```python
# BAD: ハードコード
conn = sqlite3.connect('/absolute/path/to/db.sqlite3')

# GOOD: 設定から取得
from modules.utils.database import get_db_connection
with get_db_connection() as conn:
    # ...
```

---

## 参考リンク

- [DRY原則リファクタリングレポート](../10_実行レポート（reports）/REFACTORING_DRY_PRINCIPLES_REPORT.md)
- [データベース設計](../3_技術仕様（technical）/architecture.md#database-layer)
- [設定管理](../3_技術仕様（technical）/configuration.md)
- [テストガイド](../2_セットアップ（setup）/TESTING_GUIDE.md)

---

**最終更新**: 2025-12-08
**バージョン**: 1.0.0
**メンテナー**: Serena Refactoring Expert Agent
