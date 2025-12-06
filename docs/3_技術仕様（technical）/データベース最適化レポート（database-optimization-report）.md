# データベース最適化提案書

**作成日**: 2025-12-06
**対象**: MangaAnime-Info-delivery-system
**データベース**: SQLite 3.x

---

## 1. 現状のテーブル構造

### 1.1 works テーブル
```sql
CREATE TABLE works (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  title_kana TEXT,
  title_en TEXT,
  type TEXT CHECK(type IN ('anime','manga')),
  official_url TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 1.2 releases テーブル
```sql
CREATE TABLE releases (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  work_id INTEGER NOT NULL,
  release_type TEXT CHECK(release_type IN ('episode','volume')),
  number TEXT,
  platform TEXT,
  release_date DATE,
  source TEXT,
  source_url TEXT,
  notified INTEGER DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(work_id, release_type, number, platform, release_date)
);
```

---

## 2. 推奨インデックス戦略

### 2.1 高優先度インデックス（必須）

#### works テーブル
```sql
-- タイトル検索用（部分一致検索で頻繁に使用）
CREATE INDEX idx_works_title ON works(title);

-- タイプ別フィルタリング用（anime/manga絞り込み）
CREATE INDEX idx_works_type ON works(type);

-- 作成日時でのソート用（新着順表示）
CREATE INDEX idx_works_created_at ON works(created_at DESC);

-- 複合インデックス: タイプ × 作成日時（よく使われる組み合わせ）
CREATE INDEX idx_works_type_created ON works(type, created_at DESC);
```

#### releases テーブル
```sql
-- work_idでのJOIN最適化（最重要）
CREATE INDEX idx_releases_work_id ON releases(work_id);

-- 配信日検索用（日付範囲検索で頻繁に使用）
CREATE INDEX idx_releases_date ON releases(release_date);

-- 未通知レコード抽出用（毎日の通知処理で使用）
CREATE INDEX idx_releases_notified ON releases(notified, release_date);

-- プラットフォーム別検索用
CREATE INDEX idx_releases_platform ON releases(platform);

-- 複合インデックス: 未通知 × 配信日（通知処理の最適化）
CREATE INDEX idx_releases_notified_date ON releases(notified, release_date DESC);

-- 複合インデックス: work_id × release_date（作品別の最新リリース取得）
CREATE INDEX idx_releases_work_date ON releases(work_id, release_date DESC);
```

### 2.2 中優先度インデックス（推奨）

```sql
-- ソース別集計用
CREATE INDEX idx_releases_source ON releases(source);

-- リリースタイプ別フィルタリング
CREATE INDEX idx_releases_type ON releases(release_type);

-- かな読み検索用（五十音順表示で使用）
CREATE INDEX idx_works_kana ON works(title_kana) WHERE title_kana IS NOT NULL;
```

### 2.3 全文検索インデックス（オプション）

```sql
-- タイトルの全文検索用（FTS5仮想テーブル）
CREATE VIRTUAL TABLE works_fts USING fts5(
  title,
  title_kana,
  title_en,
  content=works,
  content_rowid=id
);

-- トリガー設定（works更新時に自動同期）
CREATE TRIGGER works_fts_insert AFTER INSERT ON works BEGIN
  INSERT INTO works_fts(rowid, title, title_kana, title_en)
  VALUES (new.id, new.title, new.title_kana, new.title_en);
END;

CREATE TRIGGER works_fts_update AFTER UPDATE ON works BEGIN
  UPDATE works_fts SET
    title = new.title,
    title_kana = new.title_kana,
    title_en = new.title_en
  WHERE rowid = new.id;
END;

CREATE TRIGGER works_fts_delete AFTER DELETE ON works BEGIN
  DELETE FROM works_fts WHERE rowid = old.id;
END;
```

---

## 3. スキーマ改善提案

### 3.1 外部キー制約の追加（強く推奨）

現在のスキーマには外部キー制約が明示されていません。データ整合性を保証するため、以下を追加すべきです：

```sql
-- releasesテーブルに外部キー制約を追加
CREATE TABLE releases_new (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  work_id INTEGER NOT NULL,
  release_type TEXT CHECK(release_type IN ('episode','volume')),
  number TEXT,
  platform TEXT,
  release_date DATE,
  source TEXT,
  source_url TEXT,
  notified INTEGER DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(work_id, release_type, number, platform, release_date),
  FOREIGN KEY (work_id) REFERENCES works(id) ON DELETE CASCADE
);

-- データ移行
INSERT INTO releases_new SELECT * FROM releases;
DROP TABLE releases;
ALTER TABLE releases_new RENAME TO releases;

-- 外部キー制約を有効化（SQLiteではデフォルト無効）
PRAGMA foreign_keys = ON;
```

### 3.2 追加カラムの提案

#### works テーブル
```sql
-- 更新日時トラッキング
ALTER TABLE works ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP;

-- ソフトデリート対応
ALTER TABLE works ADD COLUMN deleted_at DATETIME DEFAULT NULL;

-- メタデータ
ALTER TABLE works ADD COLUMN description TEXT;
ALTER TABLE works ADD COLUMN image_url TEXT;
ALTER TABLE works ADD COLUMN genres TEXT; -- JSON形式で複数ジャンル格納
```

#### releases テーブル
```sql
-- 更新日時トラッキング
ALTER TABLE releases ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP;

-- 通知日時記録
ALTER TABLE releases ADD COLUMN notified_at DATETIME DEFAULT NULL;

-- エラーハンドリング
ALTER TABLE releases ADD COLUMN notification_retry_count INTEGER DEFAULT 0;
ALTER TABLE releases ADD COLUMN last_error TEXT DEFAULT NULL;
```

### 3.3 新規テーブルの提案

#### notification_logs テーブル（通知履歴管理）
```sql
CREATE TABLE notification_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  release_id INTEGER NOT NULL,
  notification_type TEXT CHECK(notification_type IN ('email','calendar')),
  status TEXT CHECK(status IN ('success','failed','pending')),
  error_message TEXT,
  sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (release_id) REFERENCES releases(id) ON DELETE CASCADE
);

CREATE INDEX idx_notification_logs_release ON notification_logs(release_id);
CREATE INDEX idx_notification_logs_status ON notification_logs(status);
```

#### user_settings テーブル（ユーザー設定管理）
```sql
CREATE TABLE user_settings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_email TEXT NOT NULL UNIQUE,
  notify_anime INTEGER DEFAULT 1,
  notify_manga INTEGER DEFAULT 1,
  preferred_platforms TEXT, -- JSON配列
  ng_keywords TEXT, -- JSON配列
  notification_time TIME DEFAULT '08:00:00',
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_settings_email ON user_settings(user_email);
```

#### platforms テーブル（正規化）
```sql
CREATE TABLE platforms (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  type TEXT CHECK(type IN ('anime','manga','both')),
  official_url TEXT,
  icon_url TEXT,
  active INTEGER DEFAULT 1,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- releasesテーブルのplatformカラムをplatform_idに変更
ALTER TABLE releases ADD COLUMN platform_id INTEGER;
UPDATE releases SET platform_id = (SELECT id FROM platforms WHERE name = releases.platform);
-- 移行完了後、platformカラムを削除
```

---

## 4. クエリパフォーマンス最適化

### 4.1 よく使われるクエリパターン

#### パターン1: 未通知の最新リリース取得
```sql
-- 最適化前（フルスキャン）
SELECT r.*, w.title
FROM releases r
JOIN works w ON r.work_id = w.id
WHERE r.notified = 0 AND r.release_date <= DATE('now')
ORDER BY r.release_date;

-- 最適化後（インデックス使用）
-- idx_releases_notified_date + idx_releases_work_id使用
EXPLAIN QUERY PLAN
SELECT r.*, w.title
FROM releases r
JOIN works w ON r.work_id = w.id
WHERE r.notified = 0 AND r.release_date <= DATE('now')
ORDER BY r.release_date;
```

#### パターン2: 作品別の最新エピソード取得
```sql
-- 最適化前
SELECT * FROM releases
WHERE work_id = ?
ORDER BY release_date DESC
LIMIT 1;

-- 最適化後（idx_releases_work_date使用）
SELECT * FROM releases
WHERE work_id = ?
ORDER BY release_date DESC
LIMIT 1;
```

#### パターン3: プラットフォーム別の今週のリリース
```sql
-- 最適化前
SELECT w.title, r.*
FROM releases r
JOIN works w ON r.work_id = w.id
WHERE r.platform = 'dアニメストア'
  AND r.release_date BETWEEN DATE('now', 'weekday 0', '-7 days')
                         AND DATE('now', 'weekday 0')
ORDER BY r.release_date;

-- 最適化後（idx_releases_platform + idx_releases_date使用）
-- または複合インデックス作成
CREATE INDEX idx_releases_platform_date ON releases(platform, release_date);
```

### 4.2 クエリ最適化のベストプラクティス

1. **EXPLAIN QUERY PLANの活用**
```sql
EXPLAIN QUERY PLAN
SELECT ... FROM ... WHERE ...;
```

2. **サブクエリよりJOINを優先**
```sql
-- 非推奨
SELECT * FROM works
WHERE id IN (SELECT work_id FROM releases WHERE notified = 0);

-- 推奨
SELECT DISTINCT w.*
FROM works w
INNER JOIN releases r ON w.id = r.work_id
WHERE r.notified = 0;
```

3. **カバリングインデックスの活用**
```sql
-- よく使うカラムをインデックスに含める
CREATE INDEX idx_releases_covering ON releases(
  notified, release_date, work_id, platform
) WHERE notified = 0;
```

4. **パーティャルインデックスの活用**
```sql
-- 未通知レコードのみインデックス化（容量節約）
CREATE INDEX idx_releases_unnotified ON releases(release_date)
WHERE notified = 0;
```

---

## 5. データ品質チェック

### 5.1 推奨バリデーションクエリ

#### NULL値チェック
```sql
-- worksテーブルの必須カラム
SELECT COUNT(*) FROM works WHERE title IS NULL;
SELECT COUNT(*) FROM works WHERE type IS NULL;

-- releasesテーブルの必須カラム
SELECT COUNT(*) FROM releases WHERE work_id IS NULL;
SELECT COUNT(*) FROM releases WHERE release_date IS NULL;
```

#### 孤立レコードチェック
```sql
-- work_idが存在しないreleases
SELECT COUNT(*) FROM releases r
LEFT JOIN works w ON r.work_id = w.id
WHERE w.id IS NULL;
```

#### 重複データチェック
```sql
-- 重複タイトル検出
SELECT title, COUNT(*) as count
FROM works
GROUP BY title
HAVING count > 1;

-- UNIQUE制約違反候補
SELECT work_id, release_type, number, platform, release_date, COUNT(*) as count
FROM releases
GROUP BY work_id, release_type, number, platform, release_date
HAVING count > 1;
```

#### データ分布確認
```sql
-- タイプ別作品数
SELECT type, COUNT(*) FROM works GROUP BY type;

-- プラットフォーム別リリース数
SELECT platform, COUNT(*) FROM releases GROUP BY platform;

-- 通知状況
SELECT notified, COUNT(*) FROM releases GROUP BY notified;

-- 月別リリース数
SELECT strftime('%Y-%m', release_date) as month, COUNT(*)
FROM releases
GROUP BY month
ORDER BY month DESC;
```

### 5.2 定期実行推奨のメンテナンスクエリ

```sql
-- インデックス再構築（月次）
REINDEX;

-- データベース最適化（週次）
VACUUM;

-- 統計情報更新（日次）
ANALYZE;

-- 古い通知済みレコードのアーカイブ（月次）
-- 6ヶ月以上前の通知済みレコードを削除または別テーブルに移動
DELETE FROM releases
WHERE notified = 1
  AND release_date < DATE('now', '-6 months');
```

---

## 6. バックアップ・リカバリ戦略

### 6.1 推奨バックアップ方式

#### 方式1: シンプルなファイルコピー
```bash
#!/bin/bash
# daily_backup.sh
BACKUP_DIR="/path/to/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
cp db.sqlite3 "$BACKUP_DIR/db_backup_$TIMESTAMP.sqlite3"

# 7日以上古いバックアップを削除
find "$BACKUP_DIR" -name "db_backup_*.sqlite3" -mtime +7 -delete
```

#### 方式2: SQLiteダンプ（推奨）
```bash
#!/bin/bash
# dump_backup.sh
BACKUP_DIR="/path/to/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# SQL形式でダンプ
sqlite3 db.sqlite3 .dump > "$BACKUP_DIR/db_dump_$TIMESTAMP.sql"

# 圧縮
gzip "$BACKUP_DIR/db_dump_$TIMESTAMP.sql"

# 古いバックアップ削除
find "$BACKUP_DIR" -name "db_dump_*.sql.gz" -mtime +30 -delete
```

#### 方式3: 増分バックアップ（SQLiteのバックアップAPI使用）
```python
#!/usr/bin/env python3
import sqlite3
from datetime import datetime

def backup_database():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    source = sqlite3.connect('db.sqlite3')
    backup = sqlite3.connect(f'backups/db_backup_{timestamp}.sqlite3')

    with backup:
        source.backup(backup)

    source.close()
    backup.close()
    print(f"Backup completed: db_backup_{timestamp}.sqlite3")

if __name__ == '__main__':
    backup_database()
```

### 6.2 リストア手順

```bash
# SQL形式からリストア
gunzip -c db_dump_20251206_080000.sql.gz | sqlite3 db_restored.sqlite3

# バックアップファイルから直接リストア
cp backups/db_backup_20251206_080000.sqlite3 db.sqlite3
```

### 6.3 マイグレーション管理

推奨ツール: **Alembic** または **sqlite-migrate**

#### ディレクトリ構成
```
migrations/
├── versions/
│   ├── 001_initial_schema.sql
│   ├── 002_add_indexes.sql
│   ├── 003_add_foreign_keys.sql
│   └── 004_add_notification_logs.sql
└── migrate.py
```

#### マイグレーションスクリプト例
```python
#!/usr/bin/env python3
# migrations/migrate.py
import sqlite3
import os

MIGRATIONS_DIR = 'migrations/versions'

def get_applied_migrations(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('SELECT version FROM schema_migrations ORDER BY version')
    return {row[0] for row in cursor.fetchall()}

def apply_migrations(db_path):
    conn = sqlite3.connect(db_path)
    applied = get_applied_migrations(conn)

    migrations = sorted([f for f in os.listdir(MIGRATIONS_DIR) if f.endswith('.sql')])

    for migration_file in migrations:
        version = int(migration_file.split('_')[0])

        if version in applied:
            print(f"Skipping {migration_file} (already applied)")
            continue

        print(f"Applying {migration_file}...")
        with open(os.path.join(MIGRATIONS_DIR, migration_file), 'r') as f:
            sql = f.read()
            conn.executescript(sql)
            conn.execute('INSERT INTO schema_migrations (version) VALUES (?)', (version,))
            conn.commit()
        print(f"Applied {migration_file}")

    conn.close()

if __name__ == '__main__':
    apply_migrations('db.sqlite3')
```

---

## 7. セキュリティ対策

### 7.1 SQLインジェクション対策

```python
# 非推奨（脆弱）
title = request.args.get('title')
cursor.execute(f"SELECT * FROM works WHERE title = '{title}'")

# 推奨（プレースホルダ使用）
title = request.args.get('title')
cursor.execute("SELECT * FROM works WHERE title = ?", (title,))
```

### 7.2 ファイルパーミッション

```bash
# データベースファイルの権限を制限
chmod 600 db.sqlite3

# バックアップディレクトリの権限
chmod 700 backups/
```

### 7.3 暗号化（オプション）

SQLCipherを使用したデータベース暗号化：

```python
from pysqlcipher3 import dbapi2 as sqlite

conn = sqlite.connect('encrypted.db')
conn.execute("PRAGMA key='your-secret-key'")
```

---

## 8. モニタリング・アラート

### 8.1 推奨メトリクス

1. **データベースサイズ**
```bash
ls -lh db.sqlite3
```

2. **テーブル別レコード数**
```sql
SELECT 'works' as table_name, COUNT(*) as count FROM works
UNION ALL
SELECT 'releases', COUNT(*) FROM releases;
```

3. **クエリパフォーマンス**
```sql
-- 遅いクエリの検出（ログ解析）
PRAGMA query_only = ON;
EXPLAIN QUERY PLAN SELECT ...;
```

4. **インデックス使用状況**
```sql
SELECT name, sql FROM sqlite_master WHERE type = 'index';
```

### 8.2 アラート設定

```python
import os

# データベースサイズチェック
db_size = os.path.getsize('db.sqlite3') / (1024 * 1024)  # MB
if db_size > 500:  # 500MBを超えたらアラート
    send_alert(f"Database size exceeded: {db_size}MB")

# 孤立レコードチェック
orphaned = cursor.execute('''
    SELECT COUNT(*) FROM releases r
    LEFT JOIN works w ON r.work_id = w.id
    WHERE w.id IS NULL
''').fetchone()[0]

if orphaned > 0:
    send_alert(f"Found {orphaned} orphaned releases")
```

---

## 9. パフォーマンスチューニング設定

### 9.1 推奨PRAGMA設定

```sql
-- WALモード有効化（読み込みパフォーマンス向上）
PRAGMA journal_mode = WAL;

-- 同期モード（NORMAL推奨、クラッシュ時のデータ損失リスクあり）
PRAGMA synchronous = NORMAL;

-- キャッシュサイズ（デフォルト2000ページ → 10000ページに増加）
PRAGMA cache_size = -10000;  -- 負の値はKB単位

-- 一時ファイルをメモリに保存
PRAGMA temp_store = MEMORY;

-- 自動VACUUM有効化
PRAGMA auto_vacuum = INCREMENTAL;

-- 外部キー制約有効化
PRAGMA foreign_keys = ON;
```

### 9.2 接続プール設定（Python）

```python
import sqlite3
from contextlib import contextmanager

class DatabasePool:
    def __init__(self, db_path, pool_size=5):
        self.db_path = db_path
        self.pool = []
        for _ in range(pool_size):
            conn = sqlite3.connect(db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute('PRAGMA journal_mode = WAL')
            conn.execute('PRAGMA foreign_keys = ON')
            self.pool.append(conn)

    @contextmanager
    def get_connection(self):
        conn = self.pool.pop()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self.pool.append(conn)

# 使用例
db_pool = DatabasePool('db.sqlite3')

with db_pool.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM works')
```

---

## 10. 実装チェックリスト

### Phase 1: 緊急対応（即座に実装）
- [ ] 外部キー制約の追加
- [ ] 基本インデックスの作成（work_id, release_date, notified）
- [ ] バックアップスクリプトの作成
- [ ] PRAGMA設定の適用

### Phase 2: 短期対応（1週間以内）
- [ ] 全推奨インデックスの作成
- [ ] データバリデーションクエリの定期実行
- [ ] マイグレーション管理の導入
- [ ] モニタリングスクリプトの作成

### Phase 3: 中期対応（1ヶ月以内）
- [ ] notification_logsテーブルの追加
- [ ] user_settingsテーブルの追加
- [ ] 全文検索機能の実装
- [ ] パフォーマンステストの実施

### Phase 4: 長期対応（3ヶ月以内）
- [ ] platformsテーブルによる正規化
- [ ] データアーカイブ戦略の実装
- [ ] レプリケーション/HA構成の検討
- [ ] PostgreSQL移行の検討（スケーラビリティ要件次第）

---

## 11. 付録: 便利なSQLスニペット

### 作品ランキング生成
```sql
SELECT
  w.title,
  COUNT(r.id) as release_count,
  MAX(r.release_date) as latest_release
FROM works w
LEFT JOIN releases r ON w.id = r.work_id
GROUP BY w.id
ORDER BY release_count DESC
LIMIT 10;
```

### 週次配信カレンダー
```sql
SELECT
  strftime('%w', release_date) as weekday,
  COUNT(*) as count
FROM releases
WHERE release_date >= DATE('now')
GROUP BY weekday
ORDER BY weekday;
```

### プラットフォーム別統計
```sql
SELECT
  platform,
  COUNT(*) as total,
  SUM(CASE WHEN notified = 1 THEN 1 ELSE 0 END) as notified,
  SUM(CASE WHEN notified = 0 THEN 1 ELSE 0 END) as pending
FROM releases
GROUP BY platform
ORDER BY total DESC;
```

---

**推奨優先度**: 高
**実装難易度**: 中
**期待効果**: パフォーマンス向上、データ整合性確保、運用効率化

