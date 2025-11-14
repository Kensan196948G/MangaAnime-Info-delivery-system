# システムアーキテクチャ

## 概要

アニメ・マンガ情報配信システムの全体アーキテクチャ、データフロー、およびコンポーネント構成について説明します。

## 目次

1. [アーキテクチャ概要](#アーキテクチャ概要)
2. [システム構成](#システム構成)
3. [データフロー](#データフロー)
4. [コンポーネント詳細](#コンポーネント詳細)
5. [エラーハンドリング](#エラーハンドリング)
6. [パフォーマンス最適化](#パフォーマンス最適化)

---

## アーキテクチャ概要

### システム構成図

```
┌─────────────────────────────────────────────────────────────────┐
│                        外部データソース                          │
├─────────────────────────────────────────────────────────────────┤
│  AniList API  │  しょぼいカレンダー  │  RSS Feeds  │  その他   │
└────────┬────────────────┬────────────────┬──────────────┬───────┘
         │                │                │              │
         v                v                v              v
┌─────────────────────────────────────────────────────────────────┐
│                      データ収集レイヤー                          │
├─────────────────────────────────────────────────────────────────┤
│  anime_anilist.py  │  manga_rss.py  │  その他コレクター         │
└────────┬───────────────────────────────────────────────┬────────┘
         │                                               │
         v                                               v
┌─────────────────────────────────────────────────────────────────┐
│                      正規化レイヤー                              │
├─────────────────────────────────────────────────────────────────┤
│  データ整形  │  重複除去  │  ハッシュ生成  │  検証             │
└────────┬───────────────────────────────────────────────┬────────┘
         │                                               │
         v                                               v
┌─────────────────────────────────────────────────────────────────┐
│                    フィルタリングレイヤー                        │
├─────────────────────────────────────────────────────────────────┤
│  NGワードフィルター  │  ジャンルフィルター  │  品質チェック     │
└────────┬───────────────────────────────────────────────┬────────┘
         │                                               │
         v                                               v
┌─────────────────────────────────────────────────────────────────┐
│                      データストレージ                            │
├─────────────────────────────────────────────────────────────────┤
│                     SQLite (db.sqlite3)                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                     │
│  │  works   │  │ releases │  │  logs    │                     │
│  └──────────┘  └──────────┘  └──────────┘                     │
└────────┬───────────────────────────────────────────────┬────────┘
         │                                               │
         v                                               v
┌─────────────────────────────────────────────────────────────────┐
│                      配信レイヤー                                │
├─────────────────────────────────────────────────────────────────┤
│  Gmail API  │  Google Calendar API  │  その他通知方法          │
└────────┬───────────────────────────────────────────────┬────────┘
         │                                               │
         v                                               v
┌─────────────────────────────────────────────────────────────────┐
│                      Web UIレイヤー                              │
├─────────────────────────────────────────────────────────────────┤
│  Flask Application  │  Dashboard  │  Configuration             │
└─────────────────────────────────────────────────────────────────┘
```

### レイヤー構成

| レイヤー | 役割 | 主要コンポーネント |
|---------|------|-------------------|
| **データ収集** | 外部APIからデータ取得 | anime_anilist.py, manga_rss.py |
| **正規化** | データの標準化と整形 | db.py, data_normalizer.py |
| **フィルタリング** | 不要データの除外 | filter_logic.py |
| **ストレージ** | データ永続化 | SQLite, db.py |
| **配信** | 通知とカレンダー登録 | mailer.py, calendar.py |
| **Web UI** | ユーザーインターフェース | web_app.py, templates/ |

---

## システム構成

### ディレクトリ構造

```
MangaAnime-Info-delivery-system/
├── app/                        # Webアプリケーション
│   ├── start_web_ui.py        # サーバー起動スクリプト
│   ├── web_app.py             # Flaskアプリケーション
│   ├── templates/             # HTMLテンプレート
│   └── static/                # 静的ファイル
│
├── modules/                    # コアモジュール
│   ├── anime_anilist.py       # AniList API連携
│   ├── manga_rss.py           # RSS Feed取得
│   ├── filter_logic.py        # フィルタリングロジック
│   ├── db.py                  # データベース管理
│   ├── mailer.py              # Gmail送信
│   ├── calendar.py            # Googleカレンダー
│   └── config.py              # 設定管理
│
├── auth/                       # 認証関連
│   ├── auth_config.py         # OAuth2設定
│   ├── credentials.json       # Google認証情報
│   └── token.json             # アクセストークン
│
├── docs/                       # ドキュメント
│   ├── ARCHITECTURE.md        # このファイル
│   ├── SERVER_CONFIGURATION.md
│   ├── API_REFERENCE.md
│   └── DATABASE_DESIGN.md
│
├── tests/                      # テストコード
├── logs/                       # ログファイル
├── config.json                 # システム設定
├── db.sqlite3                  # データベース
├── requirements.txt            # Python依存関係
└── start_server.sh            # サーバー起動スクリプト
```

### 主要ファイル

| ファイル | 役割 | 重要度 |
|---------|------|--------|
| `config.json` | システム全体の設定 | 高 |
| `db.sqlite3` | データベース | 高 |
| `app/web_app.py` | Web UI本体 | 高 |
| `modules/db.py` | データベースロジック | 高 |
| `start_server.sh` | サーバー起動 | 中 |

---

## データフロー

### 1. データ収集フロー

```
[外部API] → [API Client] → [Response Parser] → [Data Normalizer]
                                                       ↓
                                                  [Database]
```

#### 処理ステップ

1. **API呼び出し**: 各データソースから情報を取得
2. **レスポンス解析**: JSON/XMLをパース
3. **データ正規化**: 統一フォーマットに変換
4. **重複チェック**: ハッシュ値で重複を検出
5. **データベース保存**: SQLiteに格納

#### コード例

```python
# modules/anime_anilist.py
def fetch_anime_data():
    # 1. API呼び出し
    response = requests.post(ANILIST_API_URL, json=query)

    # 2. レスポンス解析
    data = response.json()

    # 3. データ正規化
    normalized = normalize_anime_data(data)

    # 4. 重複チェック
    if not is_duplicate(normalized):
        # 5. データベース保存
        save_to_database(normalized)
```

### 2. フィルタリングフロー

```
[Raw Data] → [NG Keyword Filter] → [Genre Filter] → [Quality Check]
                                                           ↓
                                                    [Filtered Data]
```

#### フィルタリング基準

1. **NGワードフィルター**
   - config.jsonの `ng_keywords` リストと照合
   - タイトル、説明文、タグを対象

2. **ジャンルフィルター**
   - 許可されたジャンルのみを通過
   - `allowed_genres` リストで管理

3. **品質チェック**
   - データの完全性を検証
   - 必須フィールドの存在確認

#### コード例

```python
# modules/filter_logic.py
def apply_filters(work_data):
    # 1. NGワードチェック
    if contains_ng_keywords(work_data):
        return None

    # 2. ジャンルチェック
    if not is_allowed_genre(work_data):
        return None

    # 3. 品質チェック
    if not validate_data_quality(work_data):
        return None

    return work_data
```

### 3. 通知フロー

```
[Database] → [Notification Manager] → [Gmail API / Calendar API]
                                              ↓
                                        [User Inbox / Calendar]
```

#### 通知処理

1. **未通知データの取得**
   - `notified = 0` のレコードを抽出
   - 日付順にソート

2. **メール生成**
   - HTMLテンプレートを使用
   - 作品情報を埋め込み

3. **カレンダーイベント作成**
   - 配信日時を設定
   - リマインダーを追加

4. **通知状態の更新**
   - `notified = 1` に更新
   - 送信ログを記録

### 4. Web UIフロー

```
[User Browser] ↔ [Flask Server] ↔ [Database]
                       ↓
                 [API Endpoints]
```

#### リクエスト処理

1. **ルーティング**: URLパターンに基づいてハンドラーを選択
2. **認証チェック**: セッション検証 (将来実装)
3. **データ取得**: SQLiteからデータを読み込み
4. **テンプレートレンダリング**: Jinja2でHTMLを生成
5. **レスポンス返送**: ブラウザにHTMLを送信

---

## コンポーネント詳細

### データ収集コンポーネント

#### AniList API連携 (`modules/anime_anilist.py`)

**機能**:
- GraphQL APIを使用したアニメ情報取得
- レート制限の遵守 (90 req/min)
- リトライロジック

**主要メソッド**:
```python
def fetch_anime_releases():
    """最新のアニメリリース情報を取得"""
    pass

def parse_anilist_response(response):
    """AniListレスポンスを正規化"""
    pass
```

#### RSS Feed取得 (`modules/manga_rss.py`)

**機能**:
- マンガ配信サイトのRSSフィード解析
- 複数フィードの並列取得
- エラーハンドリング

**主要メソッド**:
```python
def fetch_rss_feeds():
    """全RSSフィードを取得"""
    pass

def parse_rss_entry(entry):
    """RSSエントリを正規化"""
    pass
```

### データベースコンポーネント (`modules/db.py`)

**テーブル設計**:

#### works テーブル
```sql
CREATE TABLE works (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,              -- 日本語タイトル
  title_kana TEXT,                  -- カナ表記
  title_en TEXT,                    -- 英語タイトル
  type TEXT CHECK(type IN ('anime','manga')),
  official_url TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### releases テーブル
```sql
CREATE TABLE releases (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  work_id INTEGER NOT NULL,
  release_type TEXT CHECK(release_type IN ('episode','volume')),
  number TEXT,                      -- 話数/巻数
  platform TEXT,                    -- 配信プラットフォーム
  release_date DATE,
  source TEXT,                      -- データソース
  source_url TEXT,
  notified INTEGER DEFAULT 0,       -- 通知済みフラグ
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(work_id, release_type, number, platform, release_date)
);
```

**主要メソッド**:
```python
def init_database():
    """データベース初期化"""
    pass

def insert_work(work_data):
    """作品レコードを挿入"""
    pass

def insert_release(release_data):
    """リリースレコードを挿入"""
    pass

def get_unnotified_releases():
    """未通知のリリースを取得"""
    pass
```

### Web UIコンポーネント (`app/web_app.py`)

**主要ルート**:

| ルート | メソッド | 機能 |
|-------|---------|------|
| `/` | GET | ダッシュボード |
| `/releases` | GET | リリース一覧 |
| `/calendar` | GET | カレンダービュー |
| `/config` | GET/POST | 設定管理 |
| `/logs` | GET | ログビュー |
| `/api/stats` | GET | 統計情報API |
| `/api/works` | GET | 作品データAPI |

**キャッシング戦略**:
```python
# APIステータスのキャッシュ (30秒)
api_status_cache = {
    "data": None,
    "timestamp": 0
}
CACHE_DURATION = 30
```

---

## エラーハンドリング

### エラーハンドリング戦略

#### 1. API呼び出しエラー

```python
def safe_api_call(api_func, *args, **kwargs):
    """安全なAPI呼び出しラッパー"""
    max_retries = 3
    retry_delay = 5

    for attempt in range(max_retries):
        try:
            return api_func(*args, **kwargs)
        except requests.exceptions.Timeout:
            logger.warning(f"API timeout (attempt {attempt + 1}/{max_retries})")
            time.sleep(retry_delay)
        except requests.exceptions.RequestException as e:
            logger.error(f"API error: {e}")
            if attempt == max_retries - 1:
                raise
            time.sleep(retry_delay)
```

#### 2. データベースエラー

```python
def safe_db_operation(operation, *args, **kwargs):
    """安全なDB操作ラッパー"""
    try:
        return operation(*args, **kwargs)
    except sqlite3.IntegrityError as e:
        logger.warning(f"Integrity error (duplicate?): {e}")
        return None
    except sqlite3.OperationalError as e:
        logger.error(f"Database operational error: {e}")
        raise
```

#### 3. 通知エラー

```python
def send_notification_with_retry(notification_data):
    """リトライ機能付き通知送信"""
    max_retries = 3

    for attempt in range(max_retries):
        try:
            send_notification(notification_data)
            return True
        except Exception as e:
            logger.error(f"Notification failed (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(5)

    return False
```

### ログ管理

**ログレベル**:
- `DEBUG`: 詳細な診断情報
- `INFO`: 通常の動作情報
- `WARNING`: 警告メッセージ
- `ERROR`: エラー情報
- `CRITICAL`: 重大なエラー

**ログファイル**:
```
logs/
├── app.log         # Webアプリケーションログ
├── system.log      # システムログ
├── backup.log      # バックアップログ
└── api.log         # API呼び出しログ
```

**ログローテーション**:
```python
logging_config = {
    "file_path": "./logs/app.log",
    "max_file_size_mb": 10,
    "backup_count": 5,
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "date_format": "%Y-%m-%d %H:%M:%S"
}
```

---

## パフォーマンス最適化

### データベース最適化

#### インデックス戦略

```sql
-- リリース日での検索を高速化
CREATE INDEX idx_releases_date ON releases(release_date);

-- 作品IDでの結合を高速化
CREATE INDEX idx_releases_work_id ON releases(work_id);

-- 未通知レコードの検索を高速化
CREATE INDEX idx_releases_notified ON releases(notified);

-- プラットフォームでのフィルタリングを高速化
CREATE INDEX idx_releases_platform ON releases(platform);
```

#### クエリ最適化

**改善前**:
```python
# N+1クエリ問題
releases = db.execute("SELECT * FROM releases")
for release in releases:
    work = db.execute("SELECT * FROM works WHERE id = ?", [release['work_id']])
```

**改善後**:
```python
# JOIN を使用
releases = db.execute("""
    SELECT r.*, w.title, w.type
    FROM releases r
    JOIN works w ON r.work_id = w.id
    WHERE r.release_date >= date('now', '-7 days')
""")
```

### API呼び出し最適化

#### バッチ処理

```python
def fetch_multiple_works(work_ids):
    """複数作品を一度に取得"""
    # GraphQLでバッチクエリを使用
    query = """
    query ($ids: [Int]) {
      Page {
        media(id_in: $ids) {
          id
          title { romaji native english }
          ...
        }
      }
    }
    """
    return execute_graphql(query, variables={"ids": work_ids})
```

#### 並列処理

```python
import concurrent.futures

def fetch_all_rss_feeds():
    """並列でRSSフィードを取得"""
    feeds = get_rss_feed_urls()

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(fetch_rss, url) for url in feeds]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    return results
```

### キャッシング戦略

#### メモリキャッシュ

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_work_details(work_id):
    """作品詳細をキャッシュ"""
    return db.execute("SELECT * FROM works WHERE id = ?", [work_id]).fetchone()
```

#### APIレスポンスキャッシュ

```python
cache = {
    "api_status": {"data": None, "timestamp": 0, "ttl": 30},
    "stats": {"data": None, "timestamp": 0, "ttl": 60},
}

def get_cached_data(key):
    """キャッシュからデータを取得"""
    entry = cache.get(key)
    if entry and time.time() - entry["timestamp"] < entry["ttl"]:
        return entry["data"]
    return None

def set_cached_data(key, data):
    """キャッシュにデータを保存"""
    cache[key]["data"] = data
    cache[key]["timestamp"] = time.time()
```

---

## セキュリティ

### 認証と認可

**現在の実装**:
- OAuth2を使用したGoogle API認証
- セッション管理 (Flask Secret Key)

**将来の実装**:
- ユーザー認証システム
- ロールベースアクセス制御 (RBAC)
- APIキー管理

### データ保護

**機密情報の管理**:
```python
# 環境変数を使用
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key")

# credentials.jsonは.gitignoreに追加
# token.jsonもバージョン管理から除外
```

**SQLインジェクション対策**:
```python
# プレースホルダーを使用
cursor.execute("SELECT * FROM works WHERE id = ?", [work_id])

# 動的クエリを避ける
# BAD: f"SELECT * FROM works WHERE title = '{title}'"
```

### レート制限

**API呼び出し制限**:
```python
from time import sleep
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, max_requests, time_window):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []

    def wait_if_needed(self):
        """必要に応じて待機"""
        now = datetime.now()
        self.requests = [r for r in self.requests
                        if now - r < timedelta(seconds=self.time_window)]

        if len(self.requests) >= self.max_requests:
            sleep_time = (self.requests[0] +
                         timedelta(seconds=self.time_window) - now).total_seconds()
            sleep(max(0, sleep_time))

        self.requests.append(now)

# 使用例
anilist_limiter = RateLimiter(max_requests=90, time_window=60)
```

---

## モニタリングとメトリクス

### システムメトリクス

**収集する指標**:
- API呼び出し回数と成功率
- データベースクエリ実行時間
- 通知送信成功率
- エラー発生頻度

**実装例**:
```python
metrics = {
    "api_calls": {"total": 0, "success": 0, "failed": 0},
    "db_queries": {"total": 0, "avg_time": 0},
    "notifications": {"sent": 0, "failed": 0}
}

def track_api_call(success=True):
    """API呼び出しを追跡"""
    metrics["api_calls"]["total"] += 1
    if success:
        metrics["api_calls"]["success"] += 1
    else:
        metrics["api_calls"]["failed"] += 1
```

### ヘルスチェック

```python
@app.route("/health")
def health_check():
    """システムヘルスチェック"""
    checks = {
        "database": check_database_connection(),
        "api_connectivity": check_api_connectivity(),
        "disk_space": check_disk_space(),
        "memory_usage": check_memory_usage()
    }

    all_healthy = all(checks.values())
    status_code = 200 if all_healthy else 503

    return jsonify({
        "status": "healthy" if all_healthy else "unhealthy",
        "checks": checks,
        "timestamp": datetime.now().isoformat()
    }), status_code
```

---

## スケーラビリティ

### 水平スケーリング

**現在の制約**:
- SQLiteはシングルライター
- ファイルベースのデータベース

**スケーリング戦略**:

1. **データベース移行**:
   - PostgreSQL/MySQLへの移行
   - レプリケーション設定

2. **キャッシュレイヤー**:
   - Redisの導入
   - セッション管理の分離

3. **負荷分散**:
   - Nginxでのロードバランシング
   - 複数Flaskインスタンス

### 垂直スケーリング

**リソース最適化**:
- メモリ使用量の削減
- コネクションプーリング
- 非同期処理の導入

---

## まとめ

このドキュメントでは、アニメ・マンガ情報配信システムの全体アーキテクチャについて説明しました。

**キーポイント**:
1. レイヤー化されたアーキテクチャ
2. モジュラーなコンポーネント設計
3. 堅牢なエラーハンドリング
4. パフォーマンス最適化
5. セキュリティ対策
6. スケーラビリティの考慮

**次のステップ**:
- [サーバー設定ガイド](SERVER_CONFIGURATION.md)
- [データベース設計](DATABASE_DESIGN.md)
- [API リファレンス](API_REFERENCE.md)

---

*最終更新: 2025-11-14*
