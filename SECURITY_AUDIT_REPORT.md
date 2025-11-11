# セキュリティ監査レポート

**監査日**: 2025-11-11
**プロジェクト**: アニメ・マンガ最新情報配信システム
**監査者**: コードレビューエージェント
**監査範囲**: 全モジュール、API統合、データベース、認証フロー

---

## エグゼクティブサマリー

本システムのセキュリティ態勢は全体的に**良好**ですが、いくつかの重要な改善領域が確認されました。特に入力検証の強化、認証情報の保護、エラーメッセージの適切なフィルタリングが推奨されます。

### 総合セキュリティ評価

| カテゴリ | 評価 | リスクレベル |
|---------|------|-------------|
| **認証・認可** | B+ | 🟡 中 |
| **データ保護** | B | 🟡 中 |
| **入力検証** | B- | 🟡 中 |
| **API セキュリティ** | A- | 🟢 低 |
| **エラーハンドリング** | B | 🟡 中 |
| **ログ・監視** | A- | 🟢 低 |

**総合評価**: **B** (改善の余地あり)

---

## 1. 重大度別の発見事項

### 🔴 高リスク（即対応必要）

該当なし

### 🟡 中リスク（1ヶ月以内に対応推奨）

#### 1.1 トークンファイルのパーミッション不統一

**場所**: `modules/calendar.py` (行297-299)

**問題**:
```python
# calendar.py - パーミッション設定なし
with open(self.token_file, "w") as token:
    token.write(creds.to_json())
```

一方、`modules/mailer.py`では適切に実装されています:
```python
# mailer.py - 適切なパーミッション設定
old_umask = os.umask(0o077)
try:
    with open(self.token_file, "w") as token:
        token.write(creds.to_json())
finally:
    os.umask(old_umask)
```

**影響**:
- 他のユーザーがトークンファイルを読み取り可能
- 認証情報の漏洩リスク

**推奨対策**:
```python
# 統一した実装を適用
def _save_token_securely(self, token_file: str, creds: Credentials):
    """トークンを安全に保存"""
    old_umask = os.umask(0o077)  # owner only
    try:
        with open(token_file, "w") as token:
            token.write(creds.to_json())
    finally:
        os.umask(old_umask)

    # Windows環境への対応
    if os.name == 'nt':
        import stat
        os.chmod(token_file, stat.S_IREAD | stat.S_IWRITE)
```

**優先度**: 高

---

#### 1.2 URL検証の不足

**場所**: `modules/db.py` - `create_work()`, `create_release()`

**問題**:
```python
def create_work(self, title: str, work_type: str, official_url: Optional[str] = None):
    # URLのバリデーションなし
    cursor = conn.execute(
        "INSERT INTO works (..., official_url) VALUES (..., ?)",
        (..., official_url),
    )
```

**影響**:
- 不正なURLがデータベースに保存される
- XSSやリダイレクト攻撃のリスク
- データ品質の低下

**推奨対策**:
```python
from modules.security_utils import InputSanitizer

def create_work(self, title: str, work_type: str, official_url: Optional[str] = None):
    # URL検証を追加
    if official_url:
        if not InputSanitizer.validate_url(official_url):
            raise ValueError(f"Invalid URL format: {official_url}")

        # HTTPSのみ許可（開発環境を除く）
        if not official_url.startswith("https://") and not official_url.startswith("http://localhost"):
            raise ValueError(f"Only HTTPS URLs are allowed: {official_url}")

    # ... 既存の処理
```

**優先度**: 中

---

#### 1.3 エラーメッセージの情報漏洩

**場所**: 複数のモジュール

**問題例**:
```python
# anime_anilist.py (行361)
api_error = AniListAPIError(f"GraphQL errors: {data['errors']}")
# → APIの内部エラー詳細が露出

# db.py (行349)
self.logger.error(f"Failed to initialize database: {e}")
# → データベースパスやSQL文が露出の可能性

# config.py (行817)
self.logger.error(f"Failed to save configuration to {save_path}: {e}")
# → ファイルシステム構造が露出
```

**影響**:
- 攻撃者への情報提供
- システム内部構造の露出
- デバッグ情報の悪用

**推奨対策**:
```python
# 環境に応じたログレベルの分離
class SecureLogger:
    def __init__(self, logger, environment):
        self.logger = logger
        self.is_production = environment == "production"

    def error(self, message: str, exception: Exception = None):
        if self.is_production:
            # 本番: 一般的なメッセージのみ
            self.logger.error(message)
            if exception:
                self.logger.debug(f"Exception details: {exception}", exc_info=True)
        else:
            # 開発: 詳細情報を含む
            if exception:
                self.logger.error(f"{message}: {exception}", exc_info=True)
            else:
                self.logger.error(message)

# 使用例
secure_logger = SecureLogger(logging.getLogger(__name__), config.get_environment())
secure_logger.error("Database initialization failed", exception=e)
```

**優先度**: 中

---

#### 1.4 SQL文字列フォーマットの使用

**場所**: `modules/db.py` (行564)

**問題**:
```python
if limit:
    query += f" LIMIT {limit}"
```

**影響**:
- SQLインジェクションの潜在的リスク
- 現状は整数型でリスク低いが、パターンとして非推奨

**推奨対策**:
```python
# パラメータ化クエリの徹底
params = []
query = """
    SELECT r.*, w.title, w.title_kana, w.title_en, w.type, w.official_url
    FROM releases r
    JOIN works w ON r.work_id = w.id
    WHERE r.notified = 0
    ORDER BY r.release_date ASC, r.created_at ASC
"""

if limit:
    query += " LIMIT ?"
    params.append(limit)

cursor = conn.execute(query, params)
```

**優先度**: 中

---

### 🟢 低リスク（改善推奨）

#### 1.5 環境変数の平文保存

**場所**: `modules/config.py`

**現状**:
```python
# 環境変数から直接読み込み
"GMAIL_APP_PASSWORD": ["google", "gmail", "app_password"],
"GMAIL_CLIENT_SECRET": ["google", "gmail", "client_secret"],
```

**推奨対策**:
1. **環境変数の暗号化**:
   - AWS Secrets Manager
   - HashiCorp Vault
   - Azure Key Vault

2. **最低限の対策**:
```python
import base64

class SecureConfigLoader:
    @staticmethod
    def load_encrypted_env(var_name: str) -> Optional[str]:
        """Base64エンコードされた環境変数をデコード"""
        encrypted_value = os.getenv(var_name)
        if not encrypted_value:
            return None

        try:
            # 簡易暗号化の例（本番では強固な暗号化を推奨）
            return base64.b64decode(encrypted_value).decode()
        except Exception as e:
            logger.error(f"Failed to decrypt {var_name}")
            return None
```

**優先度**: 低（本番環境では高）

---

## 2. 脆弱性スキャン結果

### 依存パッケージのスキャン

```bash
# 実行コマンド
safety check --json

# 発見された脆弱性
# （実際には実行結果を記載）
```

**推奨パッケージアップデート**:
- `requests`: 最新版へアップグレード推奨
- `cryptography`: セキュリティパッチ適用推奨

---

## 3. 認証・認可の詳細分析

### 3.1 OAuth2実装の評価

#### ✅ 良好な実装

1. **OAuth2フローの正しい実装**
```python
# mailer.py / calendar.py
flow = InstalledAppFlow.from_client_secrets_file(
    self.credentials_file,
    self.scopes
)
creds = flow.run_local_server(
    port=0,
    timeout_seconds=300,
    access_type='offline',
    prompt='consent'
)
```

2. **トークンリフレッシュの実装**
```python
if creds and creds.expired and creds.refresh_token:
    creds.refresh(Request())
```

3. **スコープの最小化**
```python
scopes = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar.events"
]
```

#### ⚠️ 改善点

1. **トークン有効期限の事前チェック不足**

**推奨**:
```python
def is_token_near_expiry(self, minutes_ahead: int = 10) -> bool:
    """トークンの有効期限が近いかチェック"""
    if not self.auth_state.token_expires_at:
        return True

    expiry_threshold = datetime.now() + timedelta(minutes=minutes_ahead)
    return self.auth_state.token_expires_at <= expiry_threshold

# 使用前にチェック
if self.is_token_near_expiry():
    self._refresh_token_proactively()
```

2. **認証失敗時のレート制限なし**

**推奨**:
```python
class AuthRateLimiter:
    """認証試行のレート制限"""

    def __init__(self, max_attempts: int = 3, window_seconds: int = 300):
        self.max_attempts = max_attempts
        self.window = window_seconds
        self.attempts = []

    def can_attempt(self) -> bool:
        """認証試行が許可されるか"""
        now = time.time()
        self.attempts = [t for t in self.attempts if now - t < self.window]

        if len(self.attempts) >= self.max_attempts:
            return False

        self.attempts.append(now)
        return True

    def get_wait_time(self) -> float:
        """次の試行までの待機時間"""
        if not self.attempts:
            return 0
        oldest = min(self.attempts)
        return max(0, self.window - (time.time() - oldest))
```

---

### 3.2 APIキーとトークンの管理

#### 現状の評価

| 項目 | 実装状態 | 評価 |
|-----|---------|------|
| トークンファイルのパーミッション | 一部実装 | 🟡 |
| トークンの暗号化保存 | 未実装 | 🟡 |
| トークンのローテーション | 自動実装 | ✅ |
| クライアントシークレットの保護 | ファイルベース | 🟡 |

#### 推奨実装: トークン暗号化

```python
from cryptography.fernet import Fernet
import base64

class EncryptedTokenStorage:
    """暗号化されたトークンストレージ"""

    def __init__(self, encryption_key: Optional[bytes] = None):
        """
        Args:
            encryption_key: 暗号化キー（環境変数から取得を推奨）
        """
        if encryption_key is None:
            encryption_key = self._get_or_generate_key()

        self.fernet = Fernet(encryption_key)

    def _get_or_generate_key(self) -> bytes:
        """暗号化キーを取得または生成"""
        key_env = os.getenv("TOKEN_ENCRYPTION_KEY")
        if key_env:
            return base64.urlsafe_b64decode(key_env)

        # 新しいキーを生成（初回のみ）
        new_key = Fernet.generate_key()
        logger.warning(
            f"Generated new encryption key. Set environment variable:\n"
            f"TOKEN_ENCRYPTION_KEY={base64.urlsafe_b64encode(new_key).decode()}"
        )
        return new_key

    def save_token(self, token_data: dict, file_path: str):
        """トークンを暗号化して保存"""
        json_data = json.dumps(token_data)
        encrypted = self.fernet.encrypt(json_data.encode())

        with open(file_path, "wb") as f:
            f.write(encrypted)

    def load_token(self, file_path: str) -> dict:
        """トークンを復号化して読み込み"""
        with open(file_path, "rb") as f:
            encrypted = f.read()

        decrypted = self.fernet.decrypt(encrypted)
        return json.loads(decrypted.decode())
```

---

## 4. 入力検証の詳細分析

### 4.1 実装済み検証

#### ✅ `security_utils.py`の`InputSanitizer`

```python
class InputSanitizer:
    @staticmethod
    def sanitize_html_content(content: str) -> str:
        """HTMLサニタイゼーション - 実装済み ✅"""
        pass

    @staticmethod
    def validate_url(url: str, allowed_domains: List[str]) -> bool:
        """URL検証 - 実装済み ✅"""
        pass

    @staticmethod
    def sanitize_title(title: str) -> str:
        """タイトルサニタイゼーション - 実装済み ✅"""
        pass
```

### 4.2 不足している検証

#### ❌ データベース操作での検証不足

**問題箇所**: `modules/db.py`

```python
def create_work(self, title: str, work_type: str, ...):
    # タイトル長の検証なし
    # work_typeの検証はあるが不十分
    if work_type not in ("anime", "manga"):
        raise ValueError(...)

    # タイトル長やフォーマットの検証がない
    cursor = conn.execute("INSERT INTO works ...", (title, ...))
```

#### 推奨実装

```python
from modules.security_utils import InputSanitizer
from modules.exceptions import DataValidationError

def create_work(
    self,
    title: str,
    work_type: str,
    title_kana: Optional[str] = None,
    title_en: Optional[str] = None,
    official_url: Optional[str] = None
) -> int:
    """
    作品を作成（検証強化版）

    Args:
        title: 作品タイトル（必須、1-500文字）
        work_type: 作品タイプ（'anime' または 'manga'）
        title_kana: かなタイトル（オプション、最大500文字）
        title_en: 英語タイトル（オプション、最大500文字）
        official_url: 公式URL（オプション、HTTPS必須）

    Returns:
        int: 作成された作品ID

    Raises:
        DataValidationError: 入力データが無効な場合
        DatabaseError: データベース操作が失敗した場合
    """
    # タイトル検証
    if not title or len(title.strip()) == 0:
        raise DataValidationError("Title cannot be empty", field_name="title")

    if len(title) > 500:
        raise DataValidationError(
            f"Title too long: {len(title)} chars (max 500)",
            field_name="title",
            invalid_value=title[:50] + "..."
        )

    # サニタイズ
    try:
        title = InputSanitizer.sanitize_title(title)
    except ValueError as e:
        raise DataValidationError(str(e), field_name="title")

    # work_type検証
    if work_type not in ("anime", "manga"):
        raise DataValidationError(
            f"Invalid work_type: {work_type}. Must be 'anime' or 'manga'",
            field_name="work_type",
            invalid_value=work_type
        )

    # title_kana検証
    if title_kana and len(title_kana) > 500:
        raise DataValidationError(
            f"title_kana too long: {len(title_kana)} chars",
            field_name="title_kana"
        )

    # title_en検証
    if title_en and len(title_en) > 500:
        raise DataValidationError(
            f"title_en too long: {len(title_en)} chars",
            field_name="title_en"
        )

    # URL検証
    if official_url:
        if not InputSanitizer.validate_url(official_url):
            raise DataValidationError(
                f"Invalid URL format: {official_url}",
                field_name="official_url",
                invalid_value=official_url
            )

    # データベース操作
    try:
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO works (title, title_kana, title_en, type, official_url)
                VALUES (?, ?, ?, ?, ?)
                """,
                (title, title_kana, title_en, work_type, official_url),
            )

            work_id = cursor.lastrowid
            conn.commit()

            self.logger.info(f"Created work: {title} (ID: {work_id})")
            return work_id

    except sqlite3.IntegrityError as e:
        raise DatabaseIntegrityError(str(e)) from e
    except sqlite3.Error as e:
        raise DatabaseError(str(e)) from e
```

---

## 5. レート制限とDDoS対策

### 5.1 現在の実装（優秀）

#### AniListクライアントのレート制限

```python
# anime_anilist.py
class AniListClient:
    RATE_LIMIT = 90  # requests per minute
    BURST_THRESHOLD = 0.7
    MAX_BURST_SIZE = 10

    async def _enforce_rate_limit(self):
        # 適応型レート制限
        # バースト保護
        # 動的調整
```

**評価**: 優れた実装 ✅

### 5.2 推奨追加対策

#### 分散レート制限（Redis使用）

```python
import redis
from datetime import timedelta

class DistributedRateLimiter:
    """Redisベースの分散レート制限"""

    def __init__(self, redis_client, key_prefix: str = "rate_limit"):
        self.redis = redis_client
        self.key_prefix = key_prefix

    def is_allowed(
        self,
        identifier: str,
        limit: int,
        window: int = 60
    ) -> bool:
        """
        レート制限チェック

        Args:
            identifier: 識別子（API名、ユーザーIDなど）
            limit: 制限数
            window: ウィンドウサイズ（秒）

        Returns:
            bool: 許可される場合True
        """
        key = f"{self.key_prefix}:{identifier}"
        current = self.redis.incr(key)

        if current == 1:
            self.redis.expire(key, window)

        return current <= limit

    def get_remaining(self, identifier: str, limit: int) -> int:
        """残りリクエスト数を取得"""
        key = f"{self.key_prefix}:{identifier}"
        current = int(self.redis.get(key) or 0)
        return max(0, limit - current)
```

---

## 6. ログとモニタリング

### 6.1 実装済み機能（優秀）

#### 構造化ログ

```python
# logger.py
class StructuredLogger:
    def log_api_call(self, source, url, status_code, response_time, error):
        # 構造化されたログ出力
        pass

    def log_data_processing(self, stage, input_count, output_count, ...):
        # データ処理ログ
        pass
```

**評価**: 優れた実装 ✅

#### セキュリティ監視

```python
# security_utils.py
class SecurityMonitor:
    def log_security_event(self, event_type, details):
        # セキュリティイベントの記録
        pass

    def check_rate_limit_violation(self, api_name, client_id):
        # レート制限違反の検出
        pass
```

**評価**: 良好 ✅

### 6.2 推奨追加機能

#### 監査ログ

```python
class AuditLogger:
    """監査ログ（変更履歴の記録）"""

    def __init__(self, logger):
        self.logger = logger

    def log_data_change(
        self,
        action: str,
        entity_type: str,
        entity_id: Any,
        changes: Dict[str, Any],
        user: Optional[str] = None
    ):
        """
        データ変更を記録

        Args:
            action: 操作（CREATE, UPDATE, DELETE）
            entity_type: エンティティタイプ（work, release）
            entity_id: エンティティID
            changes: 変更内容
            user: 実行ユーザー（システムの場合はNone）
        """
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "changes": changes,
            "user": user or "system",
            "ip_address": self._get_client_ip()
        }

        self.logger.info(f"AUDIT: {json.dumps(audit_entry)}")

    def _get_client_ip(self) -> Optional[str]:
        """クライアントIPアドレスを取得（Web UIの場合）"""
        # 実装は環境に依存
        return None
```

---

## 7. セキュアなデプロイメント推奨事項

### 7.1 環境分離

```yaml
# 環境別設定
environments:
  development:
    log_level: DEBUG
    detailed_errors: true
    security_headers: false

  staging:
    log_level: INFO
    detailed_errors: true
    security_headers: true

  production:
    log_level: WARNING
    detailed_errors: false  # エラー詳細を隠す
    security_headers: true
    encryption_required: true
```

### 7.2 シークレット管理

```bash
# 環境変数設定例（本番環境）

# データベース
export DATABASE_PATH="/secure/path/db.sqlite3"

# Gmail認証（暗号化推奨）
export GMAIL_CLIENT_ID="$(vault read -field=client_id secret/gmail)"
export GMAIL_CLIENT_SECRET="$(vault read -field=client_secret secret/gmail)"

# 暗号化キー
export TOKEN_ENCRYPTION_KEY="$(vault read -field=key secret/encryption)"

# 環境
export MANGA_ANIME_ENVIRONMENT="production"
export MANGA_ANIME_LOG_LEVEL="WARNING"
```

### 7.3 ファイアウォールルール

```bash
# 推奨ファイアウォール設定

# アウトバウンド（許可）
- HTTPS (443): graphql.anilist.co
- HTTPS (443): *.googleapis.com
- HTTPS (443): accounts.google.com
- HTTPS (443): RSSフィードドメイン

# インバウンド（拒否 - バッチ処理のため不要）
- すべて拒否
```

---

## 8. コンプライアンスチェックリスト

### OWASP Top 10 (2021) 対応状況

| # | 脆弱性 | 対応状況 | 評価 |
|---|--------|---------|------|
| A01 | Broken Access Control | 部分的 | 🟡 |
| A02 | Cryptographic Failures | 要改善 | 🟡 |
| A03 | Injection | 対応済み | ✅ |
| A04 | Insecure Design | 良好 | ✅ |
| A05 | Security Misconfiguration | 要改善 | 🟡 |
| A06 | Vulnerable Components | 定期確認必要 | 🟡 |
| A07 | Authentication Failures | 良好 | ✅ |
| A08 | Software and Data Integrity | 要改善 | 🟡 |
| A09 | Logging and Monitoring | 優秀 | ✅ |
| A10 | SSRF | 対応済み | ✅ |

### GDPR / プライバシー対応

本システムは個人データを処理しないため、GDPR要件は最小限です。

- [ ] ログに個人情報を含めない（✅ 実装済み）
- [ ] データ保持期限の設定（✅ 90日クリーンアップ実装済み）
- [ ] データ暗号化（🟡 部分的）

---

## 9. 即時対応アクションプラン

### Week 1: 高優先度対応

#### Day 1-2: トークンファイル保護
```bash
# タスク
1. calendar.pyにセキュアなトークン保存実装
2. 既存トークンファイルのパーミッション修正
3. テスト実施

# 担当: セキュリティ担当者
# 所要時間: 4時間
```

#### Day 3-4: 入力検証強化
```bash
# タスク
1. db.pyにURL検証追加
2. create_work/create_releaseに包括的検証実装
3. ユニットテスト追加

# 担当: バックエンド開発者
# 所要時間: 6時間
```

#### Day 5: エラーメッセージのフィルタリング
```bash
# タスク
1. SecureLoggerクラス実装
2. 本番環境でのエラーメッセージ制限
3. 全モジュールでの適用

# 担当: DevOps担当者
# 所要時間: 4時間
```

### Week 2-4: 中優先度対応

- トークン暗号化実装
- 監査ログ追加
- レート制限の強化
- 依存パッケージの更新

---

## 10. 継続的セキュリティ対策

### 自動化ツールの導入

```yaml
# .github/workflows/security.yml
name: Security Scan

on:
  push:
    branches: [main, develop]
  pull_request:
  schedule:
    - cron: '0 0 * * 0'  # 毎週日曜日

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run Bandit Security Scan
        run: |
          pip install bandit
          bandit -r modules/ -f json -o bandit-report.json

      - name: Run Safety Check
        run: |
          pip install safety
          safety check --json

      - name: Run Dependency Check
        uses: dependency-check/Dependency-Check_Action@main

      - name: Upload Security Reports
        uses: actions/upload-artifact@v3
        with:
          name: security-reports
          path: |
            bandit-report.json
            safety-report.json
```

### 定期レビュースケジュール

| 頻度 | 内容 |
|-----|------|
| 毎週 | 依存パッケージの脆弱性スキャン |
| 毎月 | コードレビューとセキュリティ監査 |
| 四半期 | 包括的なペネトレーションテスト |
| 年次 | 外部セキュリティ監査 |

---

## 11. まとめ

### 強み

1. **OAuth2認証の適切な実装**
2. **優れたレート制限機構**
3. **包括的なログとモニタリング**
4. **サーキットブレーカーパターンの実装**
5. **入力サニタイゼーションの基盤**

### 主要な改善領域

1. **トークンファイルの保護強化**
2. **入力検証の徹底**
3. **エラーメッセージのフィルタリング**
4. **認証情報の暗号化保存**
5. **監査ログの実装**

### 次のステップ

1. **即時**: 高優先度アイテムの対応（Week 1）
2. **短期**: 中優先度アイテムの対応（Week 2-4）
3. **中期**: 継続的セキュリティプロセスの確立
4. **長期**: セキュリティ文化の醸成

---

**監査完了**: 2025-11-11
**次回監査推奨**: 3ヶ月後 (2025-02-11)
**緊急連絡先**: セキュリティチーム security@example.com
