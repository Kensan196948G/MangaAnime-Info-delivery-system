# Database Migrations

このディレクトリは、MangaAnime-Info-delivery-systemのデータベーススキーママイグレーションを管理します。

## ディレクトリ構造

```
migrations/
├── README.md                    # このファイル
├── 001_initial_schema.sql       # 初期スキーマ（works, releases）
├── 002_add_notification_logs.sql # 通知ログテーブル追加
├── 003_add_user_and_filters.sql  # ユーザー管理とフィルター
├── 004_add_api_logs_and_cache.sql # APIログとキャッシュ
└── rollback/                    # ロールバックスクリプト
    ├── 001_rollback.sql
    ├── 002_rollback.sql
    ├── 003_rollback.sql
    └── 004_rollback.sql
```

## 使用方法

### マイグレーション管理スクリプト

```bash
# プロジェクトルートから実行
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system

# 現在のマイグレーション状態確認
python3 scripts/migrate.py status

# すべてのマイグレーションを適用
python3 scripts/migrate.py up

# 特定バージョンまでマイグレーション
python3 scripts/migrate.py up 2

# 1つ前のバージョンにロールバック
python3 scripts/migrate.py down

# 特定バージョンまでロールバック
python3 scripts/migrate.py down 1

# データベースバックアップ作成
python3 scripts/migrate.py backup
```

### 手動実行（非推奨）

```bash
# SQLiteで直接実行
sqlite3 db.sqlite3 < migrations/001_initial_schema.sql

# ロールバック
sqlite3 db.sqlite3 < migrations/rollback/001_rollback.sql
```

## マイグレーション詳細

### 001_initial_schema.sql

**適用内容**:
- `schema_migrations` テーブル作成（バージョン管理）
- `works` テーブル作成（作品マスター）
- `releases` テーブル作成（リリース情報）
- 必須インデックス追加
- 外部キー制約設定
- 更新日時自動更新トリガー

**主要テーブル**:
- `works`: アニメ・マンガ作品の基本情報
- `releases`: 各作品のエピソード/巻数リリース情報

### 002_add_notification_logs.sql

**適用内容**:
- `notification_logs` テーブル作成（通知履歴）
- `calendar_events` テーブル作成（カレンダー登録履歴）
- Gmail/Calendar API連携用のメタデータ保存

### 003_add_user_and_filters.sql

**適用内容**:
- `users` テーブル作成（ユーザー管理）
- `user_preferences` テーブル作成（ユーザー設定）
- `ng_keywords` テーブル作成（NGワードマスター）
- `genre_filters` テーブル作成（ジャンルフィルター）
- `platform_filters` テーブル作成（プラットフォームフィルター）

**デフォルトデータ**:
- NGワード: エロ、R18、成人向け、BL、百合、ボーイズラブ

### 004_add_api_logs_and_cache.sql

**適用内容**:
- `api_call_logs` テーブル作成（API呼び出しログ）
- `error_logs` テーブル作成（エラーログ）
- `anilist_cache` テーブル作成（AniList APIキャッシュ）
- `rss_cache` テーブル作成（RSSフィードキャッシュ）
- `rss_items` テーブル作成（RSSアイテムキャッシュ）
- `system_stats` テーブル作成（システム統計）

## マイグレーション作成ガイドライン

### 新規マイグレーション作成手順

1. **ファイル名規則**: `{version}_description.sql`
   ```
   005_add_user_favorites.sql
   ```

2. **テンプレート**:
   ```sql
   -- Migration: 005_add_user_favorites.sql
   -- Date: YYYY-MM-DD
   -- Description: ユーザーお気に入り機能追加
   -- Author: Your Name

   BEGIN TRANSACTION;

   -- テーブル作成
   CREATE TABLE IF NOT EXISTS user_favorites (
     id INTEGER PRIMARY KEY AUTOINCREMENT,
     user_id INTEGER NOT NULL,
     work_id INTEGER NOT NULL,
     created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
     FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
     FOREIGN KEY (work_id) REFERENCES works(id) ON DELETE CASCADE,
     UNIQUE(user_id, work_id)
   );

   -- インデックス追加
   CREATE INDEX idx_user_favorites_user_id ON user_favorites(user_id);
   CREATE INDEX idx_user_favorites_work_id ON user_favorites(work_id);

   -- マイグレーション記録
   INSERT INTO schema_migrations(version, description, script_name)
   VALUES(5, 'Add user favorites feature', '005_add_user_favorites.sql');

   COMMIT;
   ```

3. **ロールバックスクリプト作成**: `rollback/005_rollback.sql`
   ```sql
   -- Rollback: 005_rollback.sql

   BEGIN TRANSACTION;

   DROP INDEX IF EXISTS idx_user_favorites_work_id;
   DROP INDEX IF EXISTS idx_user_favorites_user_id;
   DROP TABLE IF EXISTS user_favorites;

   DELETE FROM schema_migrations WHERE version = 5;

   COMMIT;
   ```

### マイグレーションベストプラクティス

1. **原子性**: 各マイグレーションは独立して実行可能にする
2. **冪等性**: 複数回実行しても結果が同じになるようにする（`IF NOT EXISTS`使用）
3. **ロールバック**: すべてのマイグレーションにロールバックスクリプトを用意
4. **バックアップ**: 本番環境では必ず事前バックアップを取得
5. **テスト**: 開発環境で十分にテストしてから本番適用

### 禁止事項

- ❌ 既存のマイグレーションファイルを編集しない
- ❌ バージョン番号を飛ばさない（001, 002, 003...）
- ❌ データ損失を伴う操作は慎重に（DROP TABLE など）
- ❌ 本番環境で直接SQLを実行しない（必ずスクリプト経由）

## データベース検証

### スキーマ整合性チェック

```bash
# データベース検証実行
python3 scripts/db_validator.py
```

**チェック項目**:
- 外部キー制約の有効性
- インデックスの最適性
- データ整合性
- パフォーマンス評価
- 正規化レベル
- セキュリティ

### ER図生成

```bash
# ER図生成
python3 scripts/generate_er_diagram.py
```

**出力ファイル**:
- `docs/database/schema_ascii.txt` - ASCII形式のER図
- `docs/database/schema_mermaid.md` - Mermaid形式（Markdown）
- `docs/database/schema.dbml` - DBML形式（dbdiagram.io）
- `docs/database/schema_stats.json` - スキーマ統計

## トラブルシューティング

### マイグレーション失敗時

1. **エラーメッセージ確認**
   ```bash
   python3 scripts/migrate.py status
   ```

2. **バックアップから復元**
   ```bash
   # バックアップファイル一覧
   ls -lh db_backup_*.sqlite3

   # 復元
   cp db_backup_YYYYMMDD_HHMMSS.sqlite3 db.sqlite3
   ```

3. **手動修正後に再試行**
   ```bash
   python3 scripts/migrate.py up
   ```

### 外部キー制約エラー

```sql
-- 外部キー制約確認
PRAGMA foreign_key_check;

-- 外部キー有効化確認
PRAGMA foreign_keys;

-- 外部キー無効化（緊急時のみ）
PRAGMA foreign_keys = OFF;
```

### データベースロック

```bash
# ロックファイル削除（慎重に）
rm db.sqlite3-journal
rm db.sqlite3-wal
rm db.sqlite3-shm

# プロセス確認
lsof db.sqlite3
```

## パフォーマンス最適化

### ANALYZE実行（定期実行推奨）

```sql
-- 統計情報更新
ANALYZE;

-- 特定テーブルのみ
ANALYZE works;
ANALYZE releases;
```

### VACUUM実行（週次推奨）

```sql
-- データベース最適化
VACUUM;

-- 自動VACUUM有効化
PRAGMA auto_vacuum = FULL;
```

### インデックス再構築

```sql
-- インデックス再構築
REINDEX;

-- 特定インデックスのみ
REINDEX idx_releases_notified_date;
```

## セキュリティ

### バックアップ戦略

```bash
# 日次バックアップ（cron設定推奨）
0 2 * * * cd /path/to/project && python3 scripts/migrate.py backup

# バックアップ保持期間管理（30日以上古いものを削除）
find . -name "db_backup_*.sqlite3" -mtime +30 -delete
```

### アクセス制御

```bash
# ファイルパーミッション設定
chmod 600 db.sqlite3
chmod 700 migrations/

# 所有者設定
chown app_user:app_group db.sqlite3
```

## 参考リンク

- [SQLite公式ドキュメント](https://www.sqlite.org/docs.html)
- [SQLite Foreign Keys](https://www.sqlite.org/foreignkeys.html)
- [Database Migration Best Practices](https://www.prisma.io/dataguide/types/relational/migration-strategies)
- [プロジェクト技術仕様](../docs/database-analysis-report.md)

---

**最終更新**: 2025-12-07
**担当**: Database Designer Agent
