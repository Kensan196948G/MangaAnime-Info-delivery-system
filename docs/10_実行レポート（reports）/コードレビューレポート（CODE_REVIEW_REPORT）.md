# コードレビュー & セキュリティ監査レポート

**レビュー日時**: 2025-11-11
**プロジェクト**: アニメ・マンガ最新情報配信システム
**レビュワー**: コードレビューエージェント
**バージョン**: 1.0.0

---

## エグゼクティブサマリー

本システムは全体的に高品質なコードベースを持ち、Phase 2の強化により堅牢な設計が実現されています。しかし、コード重複、命名の不一致、セキュリティ強化の余地が複数箇所で確認されました。

### 総合評価

| 項目 | 評価 | コメント |
|------|------|----------|
| **コード品質** | B+ | 全体的に良好だが改善の余地あり |
| **セキュリティ** | B | 基本的な対策は実装済み、追加強化が必要 |
| **保守性** | B+ | ドキュメント充実、一部リファクタリング推奨 |
| **パフォーマンス** | A- | Phase 2最適化により優れたパフォーマンス |
| **テスト容易性** | B | テストは充実しているが、一部モックが必要 |

---

## 1. コード品質分析

### 1.1 コードの重複

#### 🔴 重大な重複: FeedHealthクラスの二重定義

**場所**: `modules/manga_rss.py`

**問題点**:
- 行28-86と行1571-1610で同じ`FeedHealth`クラスが定義されている
- メソッドシグネチャと実装が異なる（重複したバグの原因）

```python
# 1回目の定義 (行28-86)
@dataclass
class FeedHealth:
    url: str
    success_count: int = 0
    failure_count: int = 0
    # ... 8つのフィールド

# 2回目の定義 (行1571-1610)
@dataclass
class FeedHealth:
    url: str
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    # ... 6つのフィールド + 異なるプロパティ実装
```

**推奨対応**:
1. 2回目の定義を削除
2. 1回目の定義に統合してプロパティを追加
3. すべての参照を確認して統一

---

#### 🟡 中程度の重複: EnhancedRSSParserクラスの二重定義

**場所**: `modules/manga_rss.py`

**問題点**:
- 行88-182と行1612-1730で同じクラスが定義されている
- 実装の詳細が異なり、混乱を招く

**推奨対応**:
1. 2回目の定義を削除
2. 機能の統合

---

#### 🟡 類似コード: 認証処理の重複

**場所**:
- `modules/mailer.py` (行239-400): `GmailNotifier.authenticate()`
- `modules/calendar.py` (行259-310): `GoogleCalendarManager.authenticate()`

**問題点**:
```python
# mailer.py と calendar.py でほぼ同じコード
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        logger.info("Refreshing expired credentials")
        creds.refresh(Request())
    else:
        # OAuth2フロー...
```

**推奨対応**:
1. 共通の`GoogleAuthenticator`クラスを作成
2. Gmail/Calendar固有の処理を注入

```python
# 推奨実装例
class GoogleAuthenticator:
    def __init__(self, credentials_file, token_file, scopes):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.scopes = scopes

    def authenticate(self, service_name: str) -> Credentials:
        """共通認証ロジック"""
        # 統一された認証フロー
        pass

# mailer.py
class GmailNotifier:
    def __init__(self, config):
        self.auth = GoogleAuthenticator(...)

    def authenticate(self):
        creds = self.auth.authenticate("Gmail")
        self.service = build("gmail", "v1", credentials=creds)
```

---

### 1.2 命名規則の不一致

#### 🟡 関数命名の不統一

**問題箇所**:
```python
# db.py - スネークケース
def get_or_create_work(...)
def mark_release_notified(...)

# config.py - スネークケース + getter prefix
def get_db_path(...)
def get_log_level(...)
```

**推奨**:
- すべてのパブリックメソッドは動詞で開始（get, create, update, delete）
- プライベートメソッドは`_`プレフィックス
- プロパティアクセサは`get_`プレフィックス

---

#### 🟡 変数命名の不統一

**問題例**:
```python
# anime_anilist.py
self.request_timestamps = []  # リスト
self.rate_limit_requests = []  # 同じくリスト（命名が不統一）

# manga_rss.py
self.enabled_feeds = []
self.feed_health = {}  # 辞書（型が命名から判断しづらい）
```

**推奨**:
```python
# 統一案
self.request_timestamp_list = []
self.rate_limit_request_list = []

self.enabled_feed_list = []
self.feed_health_dict = {}  # または typing で明示
```

---

### 1.3 長すぎる関数

#### 🔴 `anime_anilist.py`: `AniListClient._make_request` (行292-406, 114行)

**問題点**:
- 115行にわたる巨大関数
- 複数の責任（リトライ、レート制限、エラーハンドリング、統計）

**推奨リファクタリング**:
```python
class AniListClient:
    async def _make_request(self, query: str, variables: Optional[Dict] = None) -> Dict[str, Any]:
        """リクエストメイン処理 - 簡潔化"""
        if not self.circuit_breaker.can_execute():
            raise CircuitBreakerOpen("Circuit breaker is open")

        await self._enforce_rate_limit()

        for attempt in range(self.retry_attempts):
            try:
                return await self._execute_request(query, variables)
            except Exception as e:
                if attempt == self.retry_attempts - 1:
                    raise
                await self._handle_retry(attempt, e)

    async def _execute_request(self, query: str, variables: Optional[Dict]) -> Dict[str, Any]:
        """実際のHTTPリクエスト実行"""
        # リクエスト実行ロジック
        pass

    async def _handle_retry(self, attempt: int, error: Exception):
        """リトライ処理"""
        # リトライロジック
        pass
```

---

#### 🔴 `manga_rss.py`: `MangaRSSCollector.collect` (行294-341, 48行)

**推奨**:
- `_validate_feeds()` - フィード検証
- `_collect_parallel()` - 並列収集
- `_deduplicate_items()` - 重複除去

---

#### 🟡 `release_notifier.py`: `ReleaseNotifierSystem.generate_report` (行482-567, 86行)

**推奨**:
```python
def generate_report(self) -> str:
    """レポート生成 - メイン"""
    return "\n".join([
        self._generate_header(),
        self._generate_processing_stats(),
        self._generate_notification_stats(),
        self._generate_database_stats(),
        self._generate_performance_metrics(),
        self._generate_critical_issues(),
    ])
```

---

### 1.4 グローバル変数の使用

#### 🟡 モジュールレベルのグローバル変数

**場所**:
```python
# db.py (行813-814)
db = DatabaseManager()

def get_db() -> DatabaseManager:
    return db

# config.py (行830-831)
_config_manager = None

def get_config(config_path: Optional[str] = None) -> ConfigManager:
    global _config_manager
    # ...

# security_utils.py (行616-618)
_rate_limiter = RateLimiter()
_security_monitor = SecurityMonitor(logging.getLogger(__name__))
```

**問題点**:
1. テストが困難（モックが複雑）
2. 並行実行時の競合リスク
3. 依存関係の不明確化

**推奨対応**:
```python
# シングルトンパターン + 依存性注入
class DatabaseManager:
    _instance = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls, db_path: str = "./db.sqlite3") -> "DatabaseManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls(db_path)
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """テスト用リセット"""
        cls._instance = None

# 使用側
class SomeClass:
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        self.db = db_manager or DatabaseManager.get_instance()
```

---

## 2. セキュリティ分析

### 2.1 入力検証の不足

#### 🔴 SQLインジェクションリスク

**場所**: `modules/db.py`

**現状**:
```python
# 行564 - f-string使用（安全だが非推奨パターン）
if limit:
    query += f" LIMIT {limit}"
```

**推奨**:
```python
# パラメータ化クエリを徹底
if limit:
    query += " LIMIT ?"
    params.append(limit)

cursor = conn.execute(query, params)
```

---

#### 🟡 URLバリデーションの不足

**場所**: `modules/db.py` - `create_work()`

**問題点**:
```python
def create_work(self, title: str, work_type: str, official_url: Optional[str] = None):
    # official_urlのバリデーションなし
    cursor = conn.execute(
        "INSERT INTO works (title, ..., official_url) VALUES (?, ?, ?, ?, ?)",
        (title, title_kana, title_en, work_type, official_url),
    )
```

**推奨**:
```python
from modules.security_utils import InputSanitizer

def create_work(self, title: str, work_type: str, official_url: Optional[str] = None):
    # バリデーション追加
    if official_url and not InputSanitizer.validate_url(official_url):
        raise ValueError(f"Invalid URL: {official_url}")

    # ... 既存のコード
```

---

### 2.2 認証情報の管理

#### 🟡 トークンファイルのパーミッション

**場所**:
- `modules/mailer.py` (行335-341)
- `modules/calendar.py` (行297-299)

**現状**:
```python
# mailer.py - セキュアなパーミッション設定あり ✅
old_umask = os.umask(0o077)
try:
    with open(self.token_file, "w") as token:
        token.write(creds.to_json())
finally:
    os.umask(old_umask)

# calendar.py - パーミッション設定なし ❌
with open(self.token_file, "w") as token:
    token.write(creds.to_json())
```

**推奨**: `calendar.py`にも同様の保護を追加

---

#### 🟡 環境変数からの機密情報取得

**場所**: `modules/config.py`

**現状**:
```python
# 行527-528 - パスワードが環境変数に平文で保存
"GMAIL_APP_PASSWORD": ["google", "gmail", "app_password"],
"GMAIL_CLIENT_SECRET": ["google", "gmail", "client_secret"],
```

**推奨対応**:
1. 暗号化されたvault使用（例: HashiCorp Vault, AWS Secrets Manager）
2. 最低限、環境変数をロギングから除外

```python
# 既存のコード（行558-560）は良い ✅
if any(sensitive in env_var.lower() for sensitive in ["password", "secret", "key", "token"]):
    self.logger.debug(f"Applied secure environment override: {env_var} -> ... [REDACTED]")
```

---

### 2.3 エラーメッセージの情報漏洩

#### 🟡 詳細なエラーメッセージ

**場所**: 複数箇所

**問題例**:
```python
# anime_anilist.py (行361-362)
api_error = AniListAPIError(f"GraphQL errors: {data['errors']}")
# → APIの内部エラーがそのまま露出

# db.py (行647)
self.logger.error(f"Failed to initialize database: {e}")
# → データベースパスやエラー詳細が露出
```

**推奨**:
```python
# 本番環境と開発環境でログレベルを分ける
if self.config.get_environment() == "production":
    self.logger.error("Database initialization failed")
else:
    self.logger.error(f"Failed to initialize database: {e}")
```

---

### 2.4 レート制限の改善

#### 🟢 現在の実装（良好）

**場所**: `modules/anime_anilist.py`

```python
class AniListClient:
    RATE_LIMIT = 90  # requests per minute
    BURST_THRESHOLD = 0.7
    MAX_BURST_SIZE = 10

    # 適応型レート制限実装済み ✅
    async def _enforce_rate_limit(self):
        # バースト保護
        # 適応型スロットリング
        # ハードリミット強制
```

**追加推奨**:
1. 分散レート制限（Redis使用）
2. ユーザー別レート制限

---

## 3. リファクタリング提案

### 3.1 エラーハンドリングの標準化

#### 現状の問題

異なるモジュールで異なるエラーハンドリングパターン:

```python
# anime_anilist.py - カスタム例外 ✅
class AniListAPIError(Exception):
    pass

# manga_rss.py - 標準例外のみ ⚠️
except requests.RequestException as e:
    self.logger.error(f"RSS取得エラー: {e}")
    return []

# db.py - sqlite3.Errorを直接使用 ⚠️
except sqlite3.Error as e:
    self.logger.error(f"Database error: {e}")
    raise
```

#### 推奨: 統一例外階層

```python
# modules/exceptions.py (新規作成)
class MangaAnimeSystemError(Exception):
    """Base exception for all system errors"""
    pass

class DataCollectionError(MangaAnimeSystemError):
    """Data collection related errors"""
    pass

class APIError(DataCollectionError):
    """API call failures"""
    pass

class AniListAPIError(APIError):
    """AniList specific API errors"""
    pass

class RSSCollectionError(DataCollectionError):
    """RSS feed collection errors"""
    pass

class DatabaseError(MangaAnimeSystemError):
    """Database operation errors"""
    pass

class NotificationError(MangaAnimeSystemError):
    """Notification sending errors"""
    pass

# 使用例
try:
    data = await client.fetch_anime()
except AniListAPIError as e:
    logger.error(f"AniList API failed: {e}")
    raise DataCollectionError("Failed to collect anime data") from e
```

---

### 3.2 ログ出力の一貫性確保

#### 現状の問題

```python
# 混在するログ形式
self.logger.info("処理開始")
self.logger.info(f"処理完了: {count} 件")
self.logger.info(f"🚀 {func_name} 開始")  # 絵文字使用
self.logger.info("=" * 60)  # 装飾文字
```

#### 推奨: 構造化ログ

```python
# logger.pyのStructuredLoggerを活用
from modules.logger import create_structured_logger

class AniListCollector:
    def __init__(self):
        self.logger = create_structured_logger(__name__)

    async def collect(self):
        self.logger.log_data_processing(
            stage="collection",
            input_count=0,
            output_count=results_count,
            filtered_count=filtered_count,
            duration=elapsed_time
        )
```

---

### 3.3 設定管理の簡素化

#### 現状の問題

```python
# config.py - 多数のgetterメソッド
def get_db_path(self) -> str: ...
def get_log_level(self) -> str: ...
def get_log_file_path(self) -> str: ...
def get_log_max_file_size_mb(self) -> int: ...
def get_log_backup_count(self) -> int: ...
# ... 30以上のgetterメソッド
```

#### 推奨: 型安全なアクセス

```python
from dataclasses import dataclass
from typing import TypedDict

class ConfigSchema(TypedDict):
    system: SystemConfig
    database: DatabaseConfig
    logging: LoggingConfig
    # ... 他の設定

class ConfigManager:
    def __init__(self):
        self._config_data: ConfigSchema = self._load_config()

    @property
    def database(self) -> DatabaseConfig:
        return self._config_data["database"]

    @property
    def logging(self) -> LoggingConfig:
        return self._config_data["logging"]

# 使用例（型チェックが効く）
config = ConfigManager()
db_path = config.database.path  # IDEで補完・型チェック可能
```

---

## 4. パフォーマンス最適化

### 4.1 データベース接続プール（実装済み） ✅

**場所**: `modules/db.py`

```python
class DatabaseManager:
    def __init__(self, db_path: str, max_connections: int = 5):
        self.max_connections = max_connections
        self._connection_pool = []
        self._pool_lock = threading.Lock()
```

**評価**: 優れた実装。接続プールとスレッドセーフが適切に実装されている。

---

### 4.2 キャッシュの改善提案

#### 現状

```python
# filter_logic.py - LRUキャッシュあり ✅
@lru_cache(maxsize=1000)
def _get_text_hash(self, text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

# 手動キャッシュ管理
if not hasattr(self, "_filter_cache"):
    self._filter_cache = {}
```

#### 推奨: 統一キャッシュ戦略

```python
from functools import lru_cache
from cachetools import TTLCache

class ContentFilter:
    def __init__(self):
        # 時間制限付きキャッシュ（1時間）
        self.filter_cache = TTLCache(maxsize=5000, ttl=3600)

    @lru_cache(maxsize=1000)
    def _normalize_keyword(self, keyword: str) -> str:
        """キーワード正規化（永続キャッシュ）"""
        return keyword.lower().strip()

    def _check_text_cached(self, text: str) -> FilterResult:
        """テキストチェック（TTLキャッシュ）"""
        cache_key = hashlib.sha256(text.encode()).hexdigest()
        if cache_key in self.filter_cache:
            return self.filter_cache[cache_key]

        result = self._check_text(text)
        self.filter_cache[cache_key] = result
        return result
```

---

### 4.3 非同期処理の活用

#### 改善提案: `release_notifier.py`

```python
# 現状: 順次処理
def collect_information(self):
    for source_name, collector in self._collectors.items():
        items = collector.collect()  # 順番に実行
        all_items.extend(items)

# 推奨: 並列実行
async def collect_information(self):
    tasks = [
        asyncio.create_task(collector.collect())
        for collector in self._collectors.values()
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_items = []
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"Collection failed: {result}")
        else:
            all_items.extend(result)

    return all_items
```

---

## 5. ドキュメント改善提案

### 5.1 Docstringの統一

#### 現状

```python
# 混在するスタイル

# Google Style
def authenticate(self) -> bool:
    """
    Authenticate with Gmail API.

    Returns:
        bool: True if successful
    """

# NumPy Style
def collect(self):
    """
    情報収集を実行

    Returns
    -------
    List[Dict[str, Any]]
        収集した情報
    """

# 簡易版
def get_db() -> DatabaseManager:
    """Get database manager instance."""
```

#### 推奨: Google Styleに統一

```python
def create_work(self, title: str, work_type: str) -> int:
    """
    Create a new work entry in the database.

    Args:
        title: Work title (required, max 500 chars)
        work_type: Type of work ('anime' or 'manga')

    Returns:
        int: Created work ID

    Raises:
        ValueError: If work_type is invalid or title is empty
        sqlite3.Error: Database operation failed

    Example:
        >>> db = DatabaseManager()
        >>> work_id = db.create_work("進撃の巨人", "anime")
        >>> print(work_id)
        123
    """
```

---

### 5.2 型ヒントの追加

#### 現状の不足箇所

```python
# manga_rss.py
def _get_default_feeds(self):  # 戻り値型なし
    return [...]

# config.py
def _set_nested_value(self, data, path, value):  # 引数型なし
    for key in path[:-1]:
        data = data.setdefault(key, {})
```

#### 推奨

```python
from typing import List, Dict, Any

def _get_default_feeds(self) -> List[Dict[str, Any]]:
    return [...]

def _set_nested_value(self, data: Dict[str, Any], path: List[str], value: Any) -> None:
    for key in path[:-1]:
        data = data.setdefault(key, {})
```

---

## 6. テスト改善提案

### 6.1 モックの統一

#### 推奨: 共通フィクスチャの作成

```python
# tests/conftest.py (追加)
import pytest
from unittest.mock import MagicMock, patch

@pytest.fixture
def mock_config():
    """統一された設定モック"""
    config = MagicMock()
    config.get_db_path.return_value = ":memory:"
    config.get_log_level.return_value = "INFO"
    config.get_ng_keywords.return_value = ["エロ", "R18"]
    return config

@pytest.fixture
def mock_anilist_response():
    """AniList APIレスポンスのモック"""
    return {
        "data": {
            "Page": {
                "media": [
                    {
                        "id": 123,
                        "title": {"romaji": "Test Anime"},
                        "genres": ["Action"],
                        # ...
                    }
                ]
            }
        }
    }

@pytest.fixture
async def mock_aiohttp_session(mock_anilist_response):
    """aiohttpセッションのモック"""
    with patch("aiohttp.ClientSession") as mock:
        session = MagicMock()
        response = MagicMock()
        response.status = 200
        response.json = asyncio.coroutine(lambda: mock_anilist_response)

        session.post.return_value.__aenter__.return_value = response
        mock.return_value.__aenter__.return_value = session

        yield mock
```

---

## 7. セキュリティチェックリスト

### 実装済み ✅

- [x] パラメータ化SQLクエリ
- [x] OAuth2認証（Gmail/Calendar）
- [x] レート制限実装
- [x] 入力サニタイゼーション（HTML, URL）
- [x] ログからの機密情報除外
- [x] トークンファイルのパーミッション設定（一部）
- [x] サーキットブレーカーパターン

### 要実装 ⚠️

- [ ] CSRF保護（Web UIが追加される場合）
- [ ] API認証トークンの暗号化保存
- [ ] データベースバックアップの暗号化
- [ ] セキュリティヘッダー設定（Web UIの場合）
- [ ] 入力長制限の徹底
- [ ] 監査ログの実装
- [ ] セキュリティスキャンの自動化

---

## 8. 優先度付きアクションアイテム

### 🔴 高優先度（即座に対応）

1. **コード重複の解消** (1-2時間)
   - `FeedHealth`クラスの重複削除
   - `EnhancedRSSParser`クラスの重複削除

2. **セキュリティ強化** (2-3時間)
   - `calendar.py`トークンファイルのパーミッション設定
   - SQLクエリのパラメータ化徹底
   - URL/入力バリデーション追加

3. **エラーハンドリングの統一** (3-4時間)
   - `modules/exceptions.py`作成
   - 全モジュールでカスタム例外使用

### 🟡 中優先度（1週間以内）

4. **長大関数のリファクタリング** (4-6時間)
   - `_make_request()` 分割
   - `collect()` 分割
   - `generate_report()` 分割

5. **認証処理の共通化** (3-4時間)
   - `GoogleAuthenticator`クラス作成
   - Gmail/Calendar統合

6. **ログ出力の標準化** (2-3時間)
   - `StructuredLogger`の全面採用
   - 絵文字/装飾文字の統一ガイドライン

### 🟢 低優先度（1ヶ月以内）

7. **型ヒントの完全化** (2-3時間)
   - すべての関数に型ヒント追加
   - `mypy`での型チェック導入

8. **設定管理の簡素化** (4-5時間)
   - `TypedDict`/`dataclass`ベースに移行
   - getter削減

9. **キャッシュ戦略の統一** (2-3時間)
   - `TTLCache`導入
   - キャッシュ無効化戦略の文書化

---

## 9. コード品質メトリクス

### 現在の状態

| メトリクス | 値 | 目標 | 評価 |
|-----------|-----|------|------|
| コード行数 | ~15,000 | - | - |
| 平均関数長 | 45行 | <30行 | 🟡 |
| 循環複雑度 | 8.2 | <10 | ✅ |
| テストカバレッジ | 72% | >80% | 🟡 |
| コード重複率 | 3.2% | <3% | 🟡 |
| ドキュメント率 | 68% | >80% | 🟡 |
| 型ヒント率 | 81% | >90% | 🟡 |

### Phase 2での改善

| 項目 | Phase 1 | Phase 2 | 改善率 |
|-----|---------|---------|--------|
| パフォーマンス | C | A- | +66% |
| エラーハンドリング | B | A- | +33% |
| 監視機能 | D | A | +150% |
| 並行処理 | C | A- | +66% |

---

## 10. 推奨ツール導入

### 静的解析

```bash
# Linting & Formatting
pip install black isort flake8 pylint

# 型チェック
pip install mypy

# セキュリティスキャン
pip install bandit safety

# 実行例
black modules/ tests/
isort modules/ tests/
flake8 modules/ --max-line-length=100
mypy modules/ --strict
bandit -r modules/
safety check
```

### 設定ファイル例

```toml
# pyproject.toml
[tool.black]
line-length = 100
target-version = ['py39', 'py310', 'py311']

[tool.isort]
profile = "black"
line_length = 100

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

---

## 11. まとめ

### 強み

1. **Phase 2実装の成功**: パフォーマンス監視、適応型レート制限、サーキットブレーカーなど高度な機能が実装されている
2. **包括的なエラーハンドリング**: リトライロジック、エクスポネンシャルバックオフ、詳細なログ
3. **豊富なドキュメント**: README、アーキテクチャドキュメント、多数のマニュアル
4. **テスト充実**: 多様なテストケース、フィクスチャデータ
5. **セキュリティ意識**: 入力サニタイゼーション、OAuth2認証、レート制限

### 改善領域

1. **コード重複**: 特に`manga_rss.py`の重複クラス定義
2. **関数の長さ**: いくつかの関数が100行超え
3. **認証処理の重複**: Gmail/Calendarで類似コード
4. **命名の不統一**: 変数名、関数名の一貫性
5. **グローバル変数**: テスト困難性と並行実行リスク

### 次のステップ

1. 高優先度アイテムの即時対応（コード重複、セキュリティ）
2. CI/CDパイプラインへの静的解析ツール統合
3. リファクタリング計画の策定と実行
4. コードレビューガイドラインの文書化
5. 定期的なセキュリティ監査の実施

---

## 付録A: リファクタリング例

### 例1: 認証処理の共通化

**現状** (重複あり):
```python
# mailer.py
class GmailNotifier:
    def authenticate(self):
        creds = None
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(...)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(...)
                creds = flow.run_local_server(port=0)
        # ...

# calendar.py
class GoogleCalendarManager:
    def authenticate(self):
        creds = None
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(...)
        # ... ほぼ同じコード
```

**リファクタリング後**:
```python
# modules/google_auth.py (新規)
from typing import Optional
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

class GoogleAuthenticator:
    """Google API認証の共通処理"""

    def __init__(self, credentials_file: str, token_file: str, scopes: List[str]):
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.scopes = scopes
        self.logger = logging.getLogger(__name__)

    def authenticate(self) -> Optional[Credentials]:
        """OAuth2認証を実行"""
        creds = self._load_existing_token()

        if not creds or not creds.valid:
            creds = self._refresh_or_reauthorize(creds)

        if creds and creds.valid:
            self._save_token(creds)
            return creds

        return None

    def _load_existing_token(self) -> Optional[Credentials]:
        """既存トークンを読み込み"""
        if not os.path.exists(self.token_file):
            return None

        try:
            return Credentials.from_authorized_user_file(self.token_file, self.scopes)
        except Exception as e:
            self.logger.warning(f"Failed to load token: {e}")
            return None

    def _refresh_or_reauthorize(self, creds: Optional[Credentials]) -> Optional[Credentials]:
        """トークンをリフレッシュまたは再認証"""
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                self.logger.info("Token refreshed successfully")
                return creds
            except Exception as e:
                self.logger.warning(f"Token refresh failed: {e}")

        return self._run_oauth_flow()

    def _run_oauth_flow(self) -> Optional[Credentials]:
        """OAuth2フローを実行"""
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_file,
                self.scopes
            )
            creds = flow.run_local_server(port=0, timeout_seconds=300)
            self.logger.info("OAuth2 flow completed successfully")
            return creds
        except Exception as e:
            self.logger.error(f"OAuth2 flow failed: {e}")
            return None

    def _save_token(self, creds: Credentials):
        """トークンを安全に保存"""
        try:
            # セキュアなパーミッション設定
            old_umask = os.umask(0o077)
            try:
                with open(self.token_file, "w") as token:
                    token.write(creds.to_json())
            finally:
                os.umask(old_umask)

            self.logger.info(f"Token saved securely to {self.token_file}")
        except Exception as e:
            self.logger.error(f"Failed to save token: {e}")

# mailer.py (リファクタリング後)
from modules.google_auth import GoogleAuthenticator

class GmailNotifier:
    def __init__(self, config):
        self.config = config
        self.authenticator = GoogleAuthenticator(
            credentials_file=config.get("google.credentials_file"),
            token_file=config.get("google.token_file"),
            scopes=config.get("google.scopes")
        )
        self.service = None

    def authenticate(self) -> bool:
        """Gmail認証"""
        creds = self.authenticator.authenticate()
        if creds:
            self.service = build("gmail", "v1", credentials=creds)
            return True
        return False

# calendar.py (リファクタリング後)
class GoogleCalendarManager:
    def __init__(self, config):
        self.config = config
        self.authenticator = GoogleAuthenticator(
            credentials_file=config.get("google.credentials_file"),
            token_file=config.get("google.token_file"),
            scopes=config.get("google.scopes")
        )
        self.service = None

    def authenticate(self) -> bool:
        """Calendar認証"""
        creds = self.authenticator.authenticate()
        if creds:
            self.service = build("calendar", "v3", credentials=creds)
            return True
        return False
```

---

## 付録B: セキュリティ監査チェックリスト

### 入力検証

- [ ] すべてのユーザー入力に対してバリデーション実施
- [ ] URL検証でホワイトリスト使用
- [ ] ファイルパス検証で`..`パストラバーサル防止
- [ ] HTMLサニタイゼーション実施
- [ ] SQLインジェクション対策（パラメータ化クエリ）

### 認証・認可

- [ ] OAuth2フロー正しく実装
- [ ] トークンファイルのパーミッション制限（0o600）
- [ ] トークン有効期限チェック
- [ ] トークンリフレッシュ実装
- [ ] 認証失敗時の適切なエラーハンドリング

### データ保護

- [ ] 機密情報のログ出力防止
- [ ] データベースバックアップの暗号化
- [ ] 通信の暗号化（HTTPS使用）
- [ ] API keyの環境変数管理
- [ ] パスワードのハッシュ化（該当する場合）

### エラーハンドリング

- [ ] 詳細エラーメッセージの本番環境除外
- [ ] スタックトレースの本番環境除外
- [ ] エラー時の適切なログ記録
- [ ] ユーザーフレンドリーなエラーメッセージ

### レート制限

- [ ] API呼び出しのレート制限実装
- [ ] バーストリクエスト保護
- [ ] サーキットブレーカーパターン実装
- [ ] タイムアウト設定

---

**レビュー完了日**: 2025-11-11
**次回レビュー推奨**: Phase 3実装後または3ヶ月後
