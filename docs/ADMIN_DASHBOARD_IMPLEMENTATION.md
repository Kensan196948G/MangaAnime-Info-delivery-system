# 管理者用セキュリティダッシュボード実装ガイド

## 概要

管理者向けのセキュリティダッシュボードを実装しました。システム全体の監視、セキュリティアラート、監査ログ分析、API使用統計を一元管理できます。

## 実装内容

### 1. バックエンド実装

#### ファイル: `/app/routes/admin_dashboard.py`

**主要機能:**
- 統計情報収集（ユーザー数、APIキー数、監査ログ数、ロック中アカウント数）
- セキュリティアラート生成（ブルートフォース攻撃検出、異常なAPI使用）
- 監査ログ分析（アクション別統計、時間別統計）
- アカウントロック解除機能

**エンドポイント:**

| エンドポイント | メソッド | 説明 |
|------------|------|------|
| `/admin/dashboard` | GET | メインダッシュボード画面 |
| `/admin/security` | GET | セキュリティ専用ダッシュボード |
| `/admin/api/dashboard-stats` | GET | 統計データJSON |
| `/admin/api/security-alerts` | GET | セキュリティアラートJSON |
| `/admin/api/audit-stats` | GET | 監査ログ統計JSON |
| `/admin/api/api-usage` | GET | API使用統計JSON |
| `/admin/api/unlock-account/<id>` | POST | アカウントロック解除 |

### 2. フロントエンド実装

#### メインダッシュボード: `templates/admin/dashboard.html`

**機能:**
- 4つの統計カード（グラデーション背景）
  - 総ユーザー数 / アクティブユーザー数
  - アクティブAPIキー数
  - 監査ログ数（24時間） / 失敗ログイン数
  - ロック中アカウント数

- セキュリティアラート表示
  - 危険度別カラー分け（danger, warning, info）
  - ブルートフォース攻撃検出
  - アカウントロック通知
  - 異常なAPI使用検出

- ロック中アカウント一覧
  - テーブル表示
  - ワンクリックでロック解除
  - リアルタイム更新

- 最近の失敗ログイン
  - タイムライン形式
  - IPアドレス表示
  - 詳細情報表示

- 自動リフレッシュ（30秒ごと）
- リフレッシュボタン（固定位置、アニメーション付き）

#### セキュリティダッシュボード: `templates/admin/security.html`

**機能:**
- Chart.js統合グラフ
  - アクション別統計（ドーナツチャート）
  - 時間別ログ統計（ラインチャート）
  - API使用統計（バーチャート）

- API使用詳細テーブル
  - キー名、プレフィックス、リクエスト数
  - 使用状況バッジ（高/中/正常）

- セキュリティ推奨事項
- 自動リフレッシュ（60秒ごと）

### 3. デザイン仕様

**カラースキーム:**
- プライマリ: グラデーション（#667eea → #764ba2）
- サクセス: グラデーション（#f093fb → #f5576c）
- インフォ: グラデーション（#4facfe → #00f2fe）
- ワーニング: グラデーション（#fa709a → #fee140）

**UI/UXポイント:**
- レスポンシブ対応（Bootstrap 5）
- ホバーエフェクト（カードが浮き上がる）
- スムーズなアニメーション
- アイコン統合（Bootstrap Icons）
- 視認性の高いカラーコーディング

## 統合手順

### 1. ルート登録

`app/__init__.py` または `app/web_app.py` に以下を追加:

```python
from app.routes.admin_dashboard import admin_dash_bp

# ブループリント登録
app.register_blueprint(admin_dash_bp)
```

### 2. ナビゲーション追加

`templates/base.html` の管理者メニューに追加:

```html
{% if current_user.is_authenticated and current_user.is_admin %}
<li class="nav-item dropdown">
    <a class="nav-link dropdown-toggle" href="#" id="adminDropdown"
       role="button" data-bs-toggle="dropdown">
        <i class="bi bi-shield-lock"></i> 管理者
    </a>
    <ul class="dropdown-menu">
        <li><a class="dropdown-item" href="/admin/dashboard">
            <i class="bi bi-speedometer2"></i> ダッシュボード
        </a></li>
        <li><a class="dropdown-item" href="/admin/security">
            <i class="bi bi-shield-check"></i> セキュリティ
        </a></li>
        <li><hr class="dropdown-divider"></li>
        <li><a class="dropdown-item" href="/admin/users">
            <i class="bi bi-people"></i> ユーザー管理
        </a></li>
        <li><a class="dropdown-item" href="/admin/audit">
            <i class="bi bi-list-ul"></i> 監査ログ
        </a></li>
        <li><a class="dropdown-item" href="/admin/api-keys">
            <i class="bi bi-key"></i> APIキー管理
        </a></li>
    </ul>
</li>
{% endif %}
```

### 3. データベーステーブル確認

以下のテーブルが必要です（既存の場合はスキップ）:

```sql
-- ユーザーテーブル（ロック機能付き）
ALTER TABLE users ADD COLUMN locked_until DATETIME;
ALTER TABLE users ADD COLUMN failed_attempts INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN last_login DATETIME;

-- 監査ログテーブル
CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    action TEXT NOT NULL,
    username TEXT,
    ip_address TEXT,
    details TEXT
);

-- APIキーテーブル
CREATE TABLE IF NOT EXISTS api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key_name TEXT NOT NULL,
    key_prefix TEXT NOT NULL,
    key_hash TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## 使用方法

### 1. ダッシュボードアクセス

管理者としてログイン後、以下のURLにアクセス:

- メインダッシュボード: `http://localhost:5000/admin/dashboard`
- セキュリティダッシュボード: `http://localhost:5000/admin/security`

### 2. セキュリティアラートの確認

ダッシュボード上部に自動的に表示されます:

- **危険（赤）**: ブルートフォース攻撃の可能性
- **警告（黄）**: アカウントロック、異常な動作
- **情報（青）**: 高API使用量など

### 3. アカウントロック解除

1. ダッシュボードの「ロック中アカウント」セクションを確認
2. 該当ユーザーの「解除」ボタンをクリック
3. 確認ダイアログで承認
4. ロックが即座に解除され、監査ログに記録

### 4. データの自動更新

- メインダッシュボード: 30秒ごと
- セキュリティダッシュボード: 60秒ごと
- 手動更新: 右下のリフレッシュボタンをクリック

## セキュリティ機能

### 1. ブルートフォース攻撃検出

1時間以内に同一ユーザー・IPから5回以上の失敗ログインを検出すると警告

### 2. 異常なAPI使用検出

1時間に100回以上のAPIリクエストを検出すると警告

### 3. アカウント自動ロック

連続した失敗ログインにより自動的にアカウントをロック

### 4. 監査ログ記録

すべての管理者アクション（ロック解除など）を自動記録

## カスタマイズ

### アラート閾値の変更

`app/routes/admin_dashboard.py` の以下の値を変更:

```python
# ブルートフォース検出閾値
BRUTE_FORCE_THRESHOLD = 5  # 回数
BRUTE_FORCE_WINDOW = 1     # 時間（時間単位）

# API使用量警告閾値
API_USAGE_THRESHOLD = 100  # 回数/時間
```

### グラフの色変更

`templates/admin/security.html` の Chart.js 設定を編集:

```javascript
backgroundColor: [
    '#667eea',  // カラー1
    '#764ba2',  // カラー2
    // 追加のカラー...
]
```

### 自動リフレッシュ間隔の変更

```javascript
// メインダッシュボード（ミリ秒単位）
autoRefreshInterval = setInterval(updateDashboard, 30000);

// セキュリティダッシュボード
setInterval(function() {
    location.reload();
}, 60000);
```

## トラブルシューティング

### 問題: グラフが表示されない

**解決策:**
1. Chart.js CDNが読み込まれているか確認
2. ブラウザのコンソールでエラーチェック
3. データが空でないか確認

### 問題: 統計データが更新されない

**解決策:**
1. データベース接続を確認
2. 監査ログが正しく記録されているか確認
3. ブラウザのキャッシュをクリア

### 問題: アカウントロック解除が動作しない

**解決策:**
1. CSRF トークンが有効か確認
2. 管理者権限があるか確認
3. データベースのロック状態を直接確認

## パフォーマンス最適化

### 1. データベースインデックス

```sql
CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp);
CREATE INDEX idx_audit_action ON audit_logs(action);
CREATE INDEX idx_users_locked ON users(locked_until);
CREATE INDEX idx_users_last_login ON users(last_login);
```

### 2. キャッシュ導入（オプション）

Flask-Caching を使用して統計データをキャッシュ:

```python
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@cache.cached(timeout=30)
def get_dashboard_statistics():
    # ...
```

## 今後の拡張案

1. **リアルタイムWebSocket通信**
   - Socket.IO統合
   - 即座のアラート通知

2. **エクスポート機能**
   - PDF/CSVレポート生成
   - 定期レポートメール送信

3. **高度な分析**
   - 機械学習による異常検出
   - 予測分析

4. **カスタムダッシュボード**
   - ユーザーごとのウィジェット配置
   - カスタムメトリクス設定

## ライセンス

このダッシュボードは MangaAnime-Info-delivery-system プロジェクトの一部です。

---

**作成日**: 2025-12-07
**バージョン**: 1.0.0
**担当**: Fullstack Developer Agent
