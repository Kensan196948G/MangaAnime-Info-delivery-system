# データベースセキュリティガイドライン

## 目的
SQLインジェクション脆弱性を防止し、安全なデータベース操作を実現するためのガイドライン。

---

## 🛡️ 基本原則

### 1. パラメータ化クエリの徹底使用

**絶対にやってはいけないこと:**

```python
# ❌ f-string（絶対NG）
user_id = request.args.get('id')
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")

# ❌ 文字列結合（絶対NG）
query = "SELECT * FROM users WHERE name = '" + username + "'"
cursor.execute(query)

# ❌ format()（絶対NG）
cursor.execute("SELECT * FROM users WHERE email = '{}'".format(email))

# ❌ %フォーマット（絶対NG）
cursor.execute("SELECT * FROM users WHERE id = %s" % user_id)
```

**正しい方法:**

```python
# ✅ プレースホルダ（推奨）
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))

# ✅ 複数パラメータ
cursor.execute(
    "SELECT * FROM users WHERE name = ? AND age > ?",
    (username, age)
)

# ✅ IN句
ids = [1, 2, 3, 4, 5]
placeholders = ','.join('?' * len(ids))
cursor.execute(
    f"SELECT * FROM users WHERE id IN ({placeholders})",
    ids
)
```

---

## 📋 ケース別実装パターン

### パターン1: 基本的なCRUD操作

```python
class UserRepository:
    """安全なユーザー操作リポジトリ"""

    def __init__(self, db_path: str):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def create(self, username: str, email: str) -> int:
        """ユーザーを作成"""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, email) VALUES (?, ?)",
            (username, email)
        )
        self.conn.commit()
        return cursor.lastrowid

    def read(self, user_id: int) -> dict:
        """ユーザーを取得"""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def update(self, user_id: int, username: str, email: str) -> bool:
        """ユーザーを更新"""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE users SET username = ?, email = ? WHERE id = ?",
            (username, email, user_id)
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def delete(self, user_id: int) -> bool:
        """ユーザーを削除"""
        cursor = self.conn.cursor()
        cursor.execute(
            "DELETE FROM users WHERE id = ?",
            (user_id,)
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def search(self, keyword: str) -> list:
        """ユーザーを検索（LIKE検索）"""
        cursor = self.conn.cursor()
        # LIKEパターンもパラメータとして渡す
        cursor.execute(
            "SELECT * FROM users WHERE username LIKE ? OR email LIKE ?",
            (f"%{keyword}%", f"%{keyword}%")
        )
        return [dict(row) for row in cursor.fetchall()]
```

---

### パターン2: 動的テーブル名/カラム名の扱い

```python
# テーブル名やカラム名を動的に扱う必要がある場合

class DynamicQueryBuilder:
    """動的クエリビルダー（ホワイトリスト検証付き）"""

    # 許可されたテーブル
    ALLOWED_TABLES = {
        'users', 'works', 'releases', 'notifications', 'rss_feeds'
    }

    # テーブルごとの許可されたカラム
    ALLOWED_COLUMNS = {
        'users': {'id', 'username', 'email', 'created_at'},
        'works': {'id', 'title', 'title_kana', 'type', 'official_url'},
        'releases': {'id', 'work_id', 'release_type', 'number', 'platform'},
    }

    @classmethod
    def validate_table(cls, table_name: str) -> str:
        """テーブル名を検証"""
        if table_name not in cls.ALLOWED_TABLES:
            raise ValueError(f"Invalid table name: {table_name}")
        return table_name

    @classmethod
    def validate_column(cls, table_name: str, column_name: str) -> str:
        """カラム名を検証"""
        if table_name not in cls.ALLOWED_COLUMNS:
            raise ValueError(f"No column whitelist for table: {table_name}")

        if column_name not in cls.ALLOWED_COLUMNS[table_name]:
            raise ValueError(f"Invalid column name: {column_name}")

        return column_name

    @classmethod
    def build_select(cls, table_name: str, columns: list, where_params: dict) -> tuple:
        """安全なSELECT文を構築"""
        # テーブル名を検証
        table = cls.validate_table(table_name)

        # カラムを検証
        validated_columns = [
            cls.validate_column(table_name, col) for col in columns
        ]
        column_list = ', '.join(validated_columns)

        # WHERE句のカラムも検証
        where_clauses = []
        values = []

        for col, val in where_params.items():
            cls.validate_column(table_name, col)
            where_clauses.append(f"{col} = ?")
            values.append(val)

        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

        query = f"SELECT {column_list} FROM {table} WHERE {where_clause}"

        return query, tuple(values)


# 使用例
builder = DynamicQueryBuilder()

# ✅ 安全
query, params = builder.build_select(
    'users',
    ['id', 'username', 'email'],
    {'username': 'john'}
)
cursor.execute(query, params)

# ❌ 拒否される（無効なテーブル名）
try:
    query, params = builder.build_select('malicious_table', ['*'], {})
except ValueError as e:
    print(f"Error: {e}")
```

---

### パターン3: トランザクション処理

```python
class TransactionManager:
    """安全なトランザクション管理"""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def execute_transaction(self, operations: list) -> bool:
        """複数の操作をトランザクションとして実行"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # トランザクション開始
            conn.execute("BEGIN TRANSACTION")

            for query, params in operations:
                cursor.execute(query, params)

            # コミット
            conn.commit()
            return True

        except Exception as e:
            # エラー時はロールバック
            conn.rollback()
            print(f"Transaction failed: {e}")
            return False

        finally:
            conn.close()


# 使用例
tm = TransactionManager('db.sqlite3')

operations = [
    ("INSERT INTO users (username, email) VALUES (?, ?)", ('user1', 'user1@example.com')),
    ("INSERT INTO users (username, email) VALUES (?, ?)", ('user2', 'user2@example.com')),
    ("UPDATE users SET status = ? WHERE username = ?", ('active', 'user1')),
]

success = tm.execute_transaction(operations)
```

---

### パターン4: バルクインサート

```python
def bulk_insert_releases(releases: list) -> int:
    """リリース情報を一括挿入（安全）"""
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()

    try:
        # executemanyを使用
        cursor.executemany(
            """
            INSERT INTO releases
            (work_id, release_type, number, platform, release_date, source)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    rel['work_id'],
                    rel['release_type'],
                    rel['number'],
                    rel['platform'],
                    rel['release_date'],
                    rel['source']
                )
                for rel in releases
            ]
        )

        conn.commit()
        return cursor.rowcount

    except Exception as e:
        conn.rollback()
        print(f"Bulk insert failed: {e}")
        return 0

    finally:
        conn.close()
```

---

## 🔍 PRAGMA文の安全な使用

PRAGMA文はSQLiteのメタデータ操作に使用されますが、テーブル名を含むため注意が必要です。

```python
def get_table_info(table_name: str) -> list:
    """テーブル情報を取得（安全）"""

    # ホワイトリスト検証
    ALLOWED_TABLES = {'users', 'works', 'releases'}

    if table_name not in ALLOWED_TABLES:
        raise ValueError(f"Invalid table name: {table_name}")

    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()

    # テーブル名が検証済みなのでPRAGMAは安全
    cursor.execute(f"PRAGMA table_info({table_name})")

    columns = cursor.fetchall()
    conn.close()

    return columns


def get_tables_from_master() -> list:
    """sqlite_masterから全テーブルを取得（最も安全）"""
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()

    # sqlite_masterからの取得は常に安全
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type = ? ORDER BY name",
        ('table',)
    )

    tables = [row[0] for row in cursor.fetchall()]
    conn.close()

    return tables
```

---

## 🧪 テスト方法

### ユニットテスト

```python
import pytest
import sqlite3

class TestSQLInjectionProtection:
    """SQLインジェクション対策のテスト"""

    @pytest.fixture
    def db_connection(self):
        """テスト用DB接続"""
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()

        # テストテーブル作成
        cursor.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                email TEXT NOT NULL
            )
        """)

        # テストデータ挿入
        cursor.execute(
            "INSERT INTO users (username, email) VALUES (?, ?)",
            ('admin', 'admin@example.com')
        )
        conn.commit()

        yield conn

        conn.close()

    def test_sql_injection_in_where_clause(self, db_connection):
        """WHERE句でのSQLインジェクション攻撃テスト"""
        cursor = db_connection.cursor()

        # 攻撃パターン: OR 1=1
        malicious_input = "admin' OR '1'='1"

        # パラメータ化クエリでは単なる文字列として扱われる
        cursor.execute(
            "SELECT * FROM users WHERE username = ?",
            (malicious_input,)
        )
        result = cursor.fetchall()

        # 攻撃は失敗し、結果は0件
        assert len(result) == 0

    def test_sql_injection_union_attack(self, db_connection):
        """UNION攻撃のテスト"""
        cursor = db_connection.cursor()

        # 攻撃パターン: UNION SELECT
        malicious_input = "1' UNION SELECT id, username, email FROM users--"

        cursor.execute(
            "SELECT * FROM users WHERE id = ?",
            (malicious_input,)
        )
        result = cursor.fetchall()

        # 攻撃は失敗
        assert len(result) == 0

    def test_valid_query(self, db_connection):
        """正常なクエリが動作することを確認"""
        cursor = db_connection.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username = ?",
            ('admin',)
        )
        result = cursor.fetchall()

        # 正常なクエリは成功
        assert len(result) == 1
        assert result[0][1] == 'admin'
```

---

## 📊 コードレビューチェックリスト

### SQLインジェクション対策

- [ ] すべての `cursor.execute()` でパラメータ化クエリを使用
- [ ] f-string、文字列結合、format() でSQL構築していない
- [ ] 動的なテーブル名/カラム名はホワイトリスト検証済み
- [ ] ユーザー入力を直接SQL文に埋め込んでいない
- [ ] LIKE検索でもパラメータ化クエリを使用
- [ ] IN句でもプレースホルダを使用
- [ ] トランザクション処理でrollbackを実装
- [ ] エラーハンドリングが適切

### セキュリティベストプラクティス

- [ ] 最小権限の原則（必要な権限のみ付与）
- [ ] エラーメッセージに機密情報を含めない
- [ ] ログに機密情報を記録しない
- [ ] 外部キー制約を有効化
- [ ] 定期的なVACUUM実行
- [ ] バックアップの自動化

---

## 🔧 静的解析ツールの活用

### Bandit（セキュリティスキャナー）

```bash
# インストール
pip install bandit

# スキャン実行
bandit -r . -f json -o security_report.json

# 特定の脆弱性のみチェック
bandit -r . -s B608  # SQL injection check
```

### SQLFluff（SQLリンター）

```bash
# インストール
pip install sqlfluff

# 設定ファイル .sqlfluff
[sqlfluff]
dialect = sqlite
exclude_rules = L003,L009

# 実行
sqlfluff lint migrations/*.sql
```

---

## 📚 参考資料

1. **OWASP SQL Injection Prevention Cheat Sheet**
   - https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html

2. **Python DB-API 2.0 Specification**
   - https://www.python.org/dev/peps/pep-0249/

3. **SQLite Security**
   - https://www.sqlite.org/security.html

4. **CWE-89: SQL Injection**
   - https://cwe.mitre.org/data/definitions/89.html

---

## 🚨 インシデント対応

SQLインジェクション攻撃が疑われる場合：

1. **即時対応**
   - 影響を受けるサービスを一時停止
   - データベース接続をブロック
   - 管理者に通知

2. **調査**
   - アクセスログの確認
   - データベースログの確認
   - 不正なクエリの特定

3. **復旧**
   - バックアップからの復元
   - 脆弱性の修正
   - セキュリティパッチの適用

4. **事後対応**
   - インシデントレポート作成
   - 再発防止策の実施
   - セキュリティトレーニング

---

**作成日**: 2025-12-07
**作成者**: Database Designer Agent
**バージョン**: 1.0
**ステータス**: Active
