# セキュリティ設定ガイド

## 概要

MangaAnime情報配信システムのセキュリティ強化機能について説明します。このシステムでは以下のセキュリティ機能を提供しています：

- 環境変数ベースの設定管理
- 機密データの暗号化
- OAuth2認証の自動リフレッシュ
- セキュアなファイル権限設定
- プロアクティブトークン管理

## 🔒 セキュリティ機能

### 1. 環境変数による設定管理

機密情報は環境変数として管理され、設定ファイルにハードコードされません。

```bash
# 重要な環境変数
GMAIL_CLIENT_SECRET=your-secret
MANGA_ANIME_MASTER_PASSWORD=your-master-password
MANGA_ANIME_ENCRYPTION_KEY=generated-key
```

### 2. 機密データの暗号化

設定ファイル内の機密データは自動的に暗号化されます。

```python
from modules.config import ConfigManager

# 暗号化を有効にして初期化
config = ConfigManager(enable_encryption=True)

# 機密データの安全な保存
config.set_secure('api.secret_key', 'sensitive_value')

# 自動復号化による取得
secret = config.get_secure('api.secret_key')
```

### 3. プロアクティブOAuth2トークン管理

トークンの有効期限を監視し、期限切れ前に自動更新します。

```python
from modules.mailer import GmailNotifier

gmail = GmailNotifier(config)

# トークンの状態をチェック
if gmail._is_token_near_expiry():
    gmail._refresh_token_proactively()
```

## 🛠️ セットアップ手順

### 1. 自動セキュリティセットアップ

```bash
# セキュリティセットアップスクリプトを実行
python3 scripts/security_setup.py
```

このスクリプトは以下を実行します：
- セキュアなディレクトリ作成
- 暗号化キーの生成
- 環境変数の設定
- ファイル権限の設定
- 設定の検証

### 2. 手動セットアップ

#### 2.1 環境変数ファイルの作成

```bash
# テンプレートをコピー
cp .env.example .env

# 実際の値で編集
nano .env
```

#### 2.2 必要な環境変数

```bash
# システム設定
MANGA_ANIME_ENVIRONMENT=production
MANGA_ANIME_LOG_LEVEL=INFO

# Gmail OAuth2設定
GMAIL_CLIENT_ID=your-client-id.googleusercontent.com
GMAIL_CLIENT_SECRET=your-client-secret

# セキュリティキー
MANGA_ANIME_MASTER_PASSWORD=your-master-password
MANGA_ANIME_ENCRYPTION_KEY=your-encryption-key
```

#### 2.3 ファイル権限の設定

```bash
# 機密ファイルの権限を制限
chmod 600 .env
chmod 600 credentials.json
chmod 600 token.json

# ディレクトリの権限設定
chmod 700 tokens/
chmod 700 backups/
```

## 🔐 OAuth2認証の強化

### Gmail API認証

```python
from modules.mailer import GmailNotifier

# 設定にOAuth2クライアント情報を含める
config = {
    'google': {
        'gmail': {
            'client_id': os.environ.get('GMAIL_CLIENT_ID'),
            'client_secret': os.environ.get('GMAIL_CLIENT_SECRET')
        }
    }
}

gmail = GmailNotifier(config)

# 認証の実行（自動リフレッシュ機能付き）
if gmail.authenticate():
    print("認証成功")
```

### Calendar API認証

```python
from modules.calendar_integration import GoogleCalendarManager

calendar = GoogleCalendarManager(config)

# プロアクティブなトークンリフレッシュ
if calendar._is_token_near_expiry():
    calendar._refresh_token_proactively()
```

## 📊 セキュリティ監視

### 認証状態の監視

```python
# Gmail認証状態
auth_state = gmail.auth_state
print(f"認証済み: {auth_state.is_authenticated}")
print(f"トークン有効期限: {auth_state.token_expires_at}")
print(f"リフレッシュ回数: {auth_state.token_refresh_count}")

# Calendar認証状態
cal_auth_state = calendar.auth_state
print(f"連続認証失敗: {cal_auth_state.consecutive_auth_failures}")
```

### ログ監視

```python
import logging

# セキュリティ関連のログレベル設定
logging.getLogger('modules.config').setLevel(logging.INFO)
logging.getLogger('modules.mailer').setLevel(logging.INFO)
logging.getLogger('modules.calendar').setLevel(logging.INFO)
```

## 🚨 セキュリティベストプラクティス

### 1. 環境変数の管理

- `.env` ファイルをGitにコミットしない
- 本番環境では環境変数を直接設定
- 定期的にパスワードとキーをローテーション

### 2. ファイル権限

```bash
# 推奨ファイル権限
-rw------- .env                 # 600
-rw------- credentials.json     # 600
-rw------- token.json          # 600
drwx------ tokens/             # 700
drwx------ backups/            # 700
```

### 3. 認証トークンの管理

- トークンの定期的な更新
- 期限切れ前の自動リフレッシュ
- 認証失敗時の適切なエラーハンドリング

### 4. 監査とモニタリング

```python
# セキュリティイベントのログ出力
logger.info(f"OAuth2 token refreshed (count: {auth_state.token_refresh_count})")
logger.warning(f"Authentication failed {auth_state.consecutive_auth_failures} times")
```

## 🧪 セキュリティテスト

```bash
# セキュリティ関連のテストを実行
python3 tests/test_security_config.py

# 全体のテストスイート
python3 -m pytest tests/ -v
```

## 🔍 トラブルシューティング

### 一般的な問題と解決策

#### 1. 認証エラー

```
Error: Gmail authentication failed
```

**解決策:**
1. 環境変数の確認
2. credentials.json の存在確認
3. OAuth2クライアントの設定確認

#### 2. トークンリフレッシュ失敗

```
Error: Token refresh failed
```

**解決策:**
1. refresh_token の存在確認
2. OAuth2設定でofflineアクセスの有効化
3. 手動での再認証

#### 3. ファイル権限エラー

```
Error: Permission denied
```

**解決策:**
```bash
# ファイル権限の修正
chmod 600 .env credentials.json token.json
chmod 700 tokens/ backups/
```

### デバッグモード

```bash
# デバッグログの有効化
export MANGA_ANIME_LOG_LEVEL=DEBUG
export VERBOSE_LOGGING=true

# セキュリティ設定の検証
python3 scripts/security_setup.py --validate
```

## 📝 設定例

### 完全な.envファイルの例

```bash
# MangaAnime Info Delivery System Environment Configuration

# System Settings
MANGA_ANIME_ENVIRONMENT=production
MANGA_ANIME_LOG_LEVEL=INFO
MANGA_ANIME_LOG_PATH=./logs/app.log

# Database
MANGA_ANIME_DB_PATH=./db.sqlite3

# Gmail Configuration
MANGA_ANIME_GMAIL_FROM=your-email@gmail.com
MANGA_ANIME_GMAIL_TO=your-notification-email@gmail.com
GMAIL_CLIENT_ID=your-client-id.googleusercontent.com
GMAIL_CLIENT_SECRET=your-client-secret

# Calendar Configuration
MANGA_ANIME_CALENDAR_ID=primary
CALENDAR_CLIENT_ID=your-calendar-client-id.googleusercontent.com
CALENDAR_CLIENT_SECRET=your-calendar-client-secret

# Google API Files
MANGA_ANIME_CREDENTIALS_FILE=credentials.json
MANGA_ANIME_TOKEN_FILE=token.json

# Security Keys
MANGA_ANIME_SECRET_KEY=generated-secret-key
MANGA_ANIME_ENCRYPTION_KEY=generated-encryption-key
MANGA_ANIME_SALT=generated-salt
MANGA_ANIME_MASTER_PASSWORD=your-master-password
```

## 🔒 高度なセキュリティ設定

### 1. 追加の暗号化

```python
# カスタム暗号化マネージャー
from modules.config import SecureConfigManager

secure_manager = SecureConfigManager("your-master-password")
encrypted_value = secure_manager.encrypt_value("sensitive_data")
```

### 2. セキュリティヘッダー

```python
# セキュリティヘッダーの設定
config = {
    'security': {
        'secure_headers': True,
        'force_https': True,
        'session_timeout_minutes': 60
    }
}
```

### 3. 監査ログ

```python
# セキュリティイベントの追跡
import logging

security_logger = logging.getLogger('security')
security_logger.info(f"User authenticated: {user_email}")
security_logger.warning(f"Failed authentication attempt from: {ip_address}")
```

このガイドに従って設定することで、MangaAnime情報配信システムのセキュリティを大幅に強化できます。