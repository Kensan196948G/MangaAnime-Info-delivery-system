# ユーザーデータベース移行ガイド

## 概要

このガイドでは、インメモリベースのユーザーストアからSQLiteデータベースベースのユーザー管理システムへの移行手順を説明します。

## 移行の利点

### インメモリ版の課題
- サーバー再起動でユーザーデータが消失
- スケーラビリティの制限
- データの永続化なし

### DB版の利点
- ユーザーデータの永続化
- スケーラブルな運用
- 監査ログとの統合
- バックアップとリカバリ機能
- 詳細な統計情報

## アーキテクチャ

```
┌─────────────────────────────────────────┐
│         Flask Application               │
├─────────────────────────────────────────┤
│  app/routes/auth.py                     │
│    ↓                                    │
│  USE_DB_STORE 環境変数で切り替え          │
│    ↓                                    │
│  ┌──────────────┬──────────────────┐    │
│  │ InMemory     │ Database         │    │
│  │ UserStore    │ UserDBStore      │    │
│  └──────────────┴──────────────────┘    │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│         SQLite Database                 │
│  - users table                          │
│  - indexes                              │
│  - triggers                             │
│  - views                                │
└─────────────────────────────────────────┘
```

## ファイル構成

```
MangaAnime-Info-delivery-system/
├── migrations/
│   └── 007_users_table.sql           # マイグレーションSQL
├── app/
│   ├── models/
│   │   ├── __init__.py
│   │   └── user_db.py                # UserDBStore実装
│   └── routes/
│       └── auth.py                   # 認証ルート（要更新）
├── scripts/
│   └── migrate_users_to_db.py        # 移行スクリプト
└── docs/
    └── USER_DB_MIGRATION_GUIDE.md    # このファイル
```

## データベーススキーマ

### usersテーブル

| カラム名        | 型       | 説明                    |
|--------------|----------|------------------------|
| id           | TEXT     | 主キー (UUID形式)        |
| username     | TEXT     | ユーザー名 (UNIQUE)      |
| password_hash| TEXT     | パスワードハッシュ         |
| email        | TEXT     | メールアドレス           |
| is_admin     | INTEGER  | 管理者フラグ (0/1)       |
| is_active    | INTEGER  | アクティブフラグ (0/1)    |
| created_at   | DATETIME | 作成日時                |
| last_login   | DATETIME | 最終ログイン日時         |
| updated_at   | DATETIME | 更新日時                |

### インデックス

```sql
idx_users_username      -- ユーザー名検索の高速化
idx_users_email         -- メールアドレス検索
idx_users_is_admin      -- 管理者フィルタリング
idx_users_created_at    -- 作成日時ソート
idx_users_is_active     -- アクティブユーザー検索
```

### トリガー

```sql
users_updated_at_trigger  -- 更新時にupdated_atを自動更新
```

### ビュー

```sql
user_stats  -- ユーザー統計情報
  - total_users: 総ユーザー数
  - admin_count: 管理者数
  - active_count: アクティブユーザー数
  - logged_in_count: ログイン済みユーザー数
```

## 移行手順

### 1. 前提条件の確認

```bash
# Pythonバージョン確認 (3.8以上)
python3 --version

# 必要なパッケージがインストールされていることを確認
pip install -r requirements.txt
```

### 2. バックアップ作成

```bash
# 既存データベースのバックアップ（存在する場合）
cp db.sqlite3 db.sqlite3.backup_manual_$(date +%Y%m%d_%H%M%S)
```

### 3. マイグレーション実行

```bash
# 完全なマイグレーションプロセスを実行
python scripts/migrate_users_to_db.py migrate
```

実行内容:
1. データベースの自動バックアップ
2. マイグレーションSQL実行
3. デフォルトユーザーの作成
4. 結果の検証
5. ログファイルの保存

### 4. 検証

```bash
# マイグレーション結果を検証
python scripts/migrate_users_to_db.py verify
```

検証項目:
- ユーザー統計情報の表示
- デフォルト管理者の存在確認
- パスワード認証の動作確認

### 5. app/routes/auth.py の更新

既存の `app/routes/auth.py` を以下のように更新します:

```python
import os
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

# 環境変数でストアを切り替え
USE_DB_STORE = os.getenv('USE_DB_STORE', 'true').lower() == 'true'

if USE_DB_STORE:
    from app.models.user_db import UserDBStore as UserStore
    user_store = UserStore()
else:
    # インメモリ版（後方互換性）
    from app.models.user_inmemory import InMemoryUserStore as UserStore
    user_store = UserStore()

# 以降の実装は変更なし
```

### 6. 環境変数の設定

```bash
# .envファイルまたはシステム環境変数
export USE_DB_STORE=true

# または .env ファイルに追加
echo "USE_DB_STORE=true" >> .env
```

### 7. アプリケーション再起動

```bash
# Flaskアプリケーションを再起動
python app/web_app.py
```

## ロールバック手順

問題が発生した場合、以下の手順でロールバックできます:

### 自動ロールバック

```bash
# 最新のバックアップから復元
python scripts/migrate_users_to_db.py rollback
```

### 手動ロールバック

```bash
# バックアップファイルを確認
ls -la db.sqlite3.backup_*

# 特定のバックアップから復元
cp db.sqlite3.backup_20251207_120000 db.sqlite3

# 環境変数を無効化
export USE_DB_STORE=false
```

## デフォルトユーザー

マイグレーション後、以下のデフォルトユーザーが作成されます:

| ユーザー名 | パスワード    | 権限   |
|---------|------------|--------|
| admin   | changeme123| 管理者  |

**重要**: 初回ログイン後、必ずパスワードを変更してください。

```python
# パスワード変更例
from app.models.user_db import UserDBStore
store = UserDBStore()
admin = store.get_user_by_username('admin')
store.update_password(admin.id, 'new_secure_password')
```

## API変更点

### UserDBStore クラスの主要メソッド

```python
# ユーザー追加
user = store.add_user(
    username="newuser",
    password="password",
    email="user@example.com",
    is_admin=False
)

# ユーザー取得
user = store.get_user_by_id("user-uuid")
user = store.get_user_by_username("username")
users = store.get_all_users()

# ユーザー削除
success = store.delete_user("user-uuid")

# パスワード更新
success = store.update_password("user-uuid", "new_password")

# 最終ログイン更新
success = store.update_last_login("user-uuid")

# ステータス更新
success = store.update_user_status("user-uuid", is_active=False)

# 統計取得
stats = store.get_user_stats()
```

## トラブルシューティング

### 問題: マイグレーションファイルが見つからない

```bash
# マイグレーションファイルの存在確認
ls -la migrations/007_users_table.sql

# ない場合は手動で作成
# （migrations/007_users_table.sql の内容を参照）
```

### 問題: 既存のusersテーブルと競合

```bash
# 既存テーブルを削除（注意: データが失われます）
sqlite3 db.sqlite3 "DROP TABLE IF EXISTS users;"

# マイグレーション再実行
python scripts/migrate_users_to_db.py migrate
```

### 問題: デフォルト管理者でログインできない

```python
# Pythonインタプリタで確認
from app.models.user_db import UserDBStore
store = UserDBStore()
admin = store.get_user_by_username('admin')
print(admin.check_password('changeme123'))  # Trueであるべき
```

### 問題: パフォーマンスが遅い

```bash
# インデックスの再構築
sqlite3 db.sqlite3 "REINDEX;"

# VACUUM実行
sqlite3 db.sqlite3 "VACUUM;"
```

## セキュリティ考慮事項

### パスワードハッシュ

- Werkzeugの`scrypt`アルゴリズムを使用
- ソルト付き（自動）
- レインボーテーブル攻撃に対する耐性

### SQLインジェクション対策

- プリペアドステートメント使用
- パラメータバインディング
- ユーザー入力の検証

### セッション管理

- Flask-Loginとの統合
- セッションタイムアウト設定推奨

```python
# app/web_app.py に追加
from datetime import timedelta
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
```

## パフォーマンス最適化

### インデックス戦略

現在のインデックス:
- username: ログイン時の高速検索
- email: メールアドレス検索
- is_admin: 管理者フィルタリング
- created_at: 作成日時ソート
- is_active: アクティブユーザー検索

### クエリ最適化

```python
# バッチ操作の例
with store._get_connection() as conn:
    cursor = conn.cursor()
    cursor.executemany("""
        INSERT INTO users (id, username, password_hash)
        VALUES (?, ?, ?)
    """, user_batch)
    conn.commit()
```

### 接続プーリング（将来の改善案）

```python
# SQLAlchemyへの移行を検討
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    'sqlite:///db.sqlite3',
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10
)
```

## 監視とログ

### ログレベル設定

```python
# app/web_app.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

# UserDBStoreのロガー
logger = logging.getLogger('app.models.user_db')
logger.setLevel(logging.DEBUG)
```

### 統計モニタリング

```python
# 定期的な統計取得
from app.models.user_db import UserDBStore
store = UserDBStore()
stats = store.get_user_stats()

print(f"Total users: {stats['total_users']}")
print(f"Active users: {stats['active_count']}")
print(f"Admin users: {stats['admin_count']}")
```

## 次のステップ

1. **監査ログとの統合**: ユーザー操作を audit_logs テーブルに記録
2. **パスワードリセット機能**: メールベースのパスワードリセット
3. **2要素認証**: TOTP/SMS認証の追加
4. **OAuth統合**: Google/GitHub認証
5. **ユーザー管理UI**: 管理者向けWeb UI

## 関連ドキュメント

- [USER_MANAGEMENT_README.md](./USER_MANAGEMENT_README.md)
- [SESSION_SECURITY_IMPLEMENTATION_REPORT.md](./SESSION_SECURITY_IMPLEMENTATION_REPORT.md)
- [AUDIT_LOG_SYSTEM.md](./AUDIT_LOG_SYSTEM.md)

## サポート

問題が発生した場合:
1. マイグレーションログを確認: `migration_log_*.txt`
2. データベースの整合性チェック: `sqlite3 db.sqlite3 "PRAGMA integrity_check;"`
3. バックアップから復元: `python scripts/migrate_users_to_db.py rollback`

## 変更履歴

| 日付       | バージョン | 変更内容                    |
|-----------|----------|---------------------------|
| 2025-12-07| 1.0.0    | 初回リリース                |
