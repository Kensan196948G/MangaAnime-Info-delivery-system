# SQLセキュリティ対策 クイックスタートガイド

## 🚀 5分でできるセキュリティチェック

このガイドでは、SQLインジェクション脆弱性の検出と修正を5分で開始できます。

---

## 📋 前提条件

- Python 3.7以上
- プロジェクトルートディレクトリへのアクセス

---

## ⚡ クイックスタート

### ステップ1: セットアップ（1分）

```bash
# プロジェクトルートに移動
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system

# セットアップスクリプトを実行
bash scripts/setup_security_tools.sh
```

### ステップ2: 脆弱性スキャン（2分）

```bash
# プロジェクト全体をスキャン
python3 scripts/scan_sql_vulnerabilities.py

# レポート確認
cat docs/SQL_INJECTION_SCAN_REPORT.md
```

### ステップ3: 結果の確認（2分）

スキャン結果を確認し、脆弱性があれば修正します。

---

## 🛠️ 詳細な使用方法

### 1. 脆弱性スキャンツール

#### 基本実行
```bash
python3 scripts/scan_sql_vulnerabilities.py
```

#### カスタム設定
```bash
# 特定のディレクトリをスキャン
python3 scripts/scan_sql_vulnerabilities.py --project-root /path/to/project

# カスタム出力先を指定
python3 scripts/scan_sql_vulnerabilities.py --output custom_report.md
```

#### 出力例
```
🔍 スキャン中... (125ファイル)

================================================================================
🛡️  SQLインジェクション脆弱性スキャン結果
================================================================================

⚠️  15件の脆弱性を検出しました
📁 影響を受けるファイル: 3件

--------------------------------------------------------------------------------
📄 scripts/analyze_database.py
   脆弱性: 12件

   🔴 行 45: f-stringによるSQL構築（危険）
      種類: F-STRING_SQL
      コード: cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
```

---

### 2. データベース分析ツール（セキュア版）

#### 基本実行
```bash
python3 scripts/analyze_database_secure.py
```

#### 推奨事項も表示
```bash
python3 scripts/analyze_database_secure.py --recommendations
```

#### カスタムDB指定
```bash
python3 scripts/analyze_database_secure.py --db path/to/custom.db
```

#### 出力例
```
================================================================================
📊 データベース分析レポート
================================================================================
📅 分析日時: 2025-12-07 14:30:00
📁 データベース: db.sqlite3

📋 テーブル数: 5
--------------------------------------------------------------------------------

🔍 テーブル: works
----------------------------------------
📝 カラム構成:
  - id: INTEGER 🔑 PRIMARY KEY
  - title: TEXT NOT NULL
  - type: TEXT

📊 レコード数: 150
```

---

## 🔧 脆弱性の修正方法

### パターン1: f-stringの修正

**Before (脆弱)**:
```python
# ❌ 危険
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
```

**After (安全)**:
```python
# ✅ 安全
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
```

---

### パターン2: 文字列結合の修正

**Before (脆弱)**:
```python
# ❌ 危険
query = "SELECT * FROM " + table_name + " WHERE id = " + str(user_id)
cursor.execute(query)
```

**After (安全)**:
```python
# ✅ 安全（テーブル名はホワイトリスト検証後）
ALLOWED_TABLES = {'users', 'works', 'releases'}
if table_name not in ALLOWED_TABLES:
    raise ValueError("Invalid table")

cursor.execute(f"SELECT * FROM {table_name} WHERE id = ?", (user_id,))
```

---

### パターン3: LIKE検索の修正

**Before (脆弱)**:
```python
# ❌ 危険
cursor.execute(f"SELECT * FROM users WHERE name LIKE '%{keyword}%'")
```

**After (安全)**:
```python
# ✅ 安全
cursor.execute(
    "SELECT * FROM users WHERE name LIKE ?",
    (f"%{keyword}%",)
)
```

---

### パターン4: IN句の修正

**Before (脆弱)**:
```python
# ❌ 危険
ids_str = ','.join(map(str, ids))
cursor.execute(f"SELECT * FROM users WHERE id IN ({ids_str})")
```

**After (安全)**:
```python
# ✅ 安全
placeholders = ','.join('?' * len(ids))
cursor.execute(
    f"SELECT * FROM users WHERE id IN ({placeholders})",
    ids
)
```

---

## 🧪 セキュリティテスト

### テストコード例

```python
import pytest
import sqlite3

def test_sql_injection_protection():
    """SQLインジェクション対策のテスト"""
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()

    # テーブル作成
    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT
        )
    """)

    # テストデータ
    cursor.execute("INSERT INTO users (username) VALUES (?)", ('admin',))
    conn.commit()

    # 攻撃パターン
    malicious_input = "admin' OR '1'='1"

    # パラメータ化クエリでは攻撃が無効化される
    cursor.execute(
        "SELECT * FROM users WHERE username = ?",
        (malicious_input,)
    )
    result = cursor.fetchall()

    # 攻撃は失敗（該当レコードなし）
    assert len(result) == 0

    conn.close()
```

### テスト実行

```bash
# テストの実行
pytest tests/test_sql_injection_protection.py -v

# カバレッジ付きで実行
pytest tests/ --cov=modules --cov-report=html
```

---

## 📊 CI/CD統合

### GitHub Actions設定

ワークフローファイルはすでに作成されています：
```
.github/workflows/sql-security-scan.yml
```

### 有効化方法

1. GitHub リポジトリにプッシュ
   ```bash
   git add .github/workflows/sql-security-scan.yml
   git commit -m "Add SQL security scan workflow"
   git push
   ```

2. GitHub Actionsタブで確認
   - https://github.com/YOUR_USERNAME/YOUR_REPO/actions

3. 自動実行タイミング
   - `push`: main, develop, feature/*ブランチ
   - `pull_request`: main, developブランチ
   - `schedule`: 毎週月曜日午前2時

---

## 📚 詳細ドキュメント

### セキュリティガイドライン
完全な実装ガイド、ベストプラクティス、テスト方法を含みます。

```bash
cat docs/DATABASE_SECURITY_GUIDELINES.md
```

**内容**:
- パラメータ化クエリの使用方法
- 動的テーブル名/カラム名の扱い
- トランザクション処理
- バルクインサート
- PRAGMA文の安全な使用
- テスト方法
- コードレビューチェックリスト

---

### 修正サマリー
修正対象ファイルと修正内容の概要です。

```bash
cat docs/SQL_INJECTION_FIX_SUMMARY.md
```

**内容**:
- 修正対象ファイル一覧
- 修正前後のコード比較
- 提供ツールの説明
- 次のステップ

---

### 実装完了レポート
プロジェクト全体の修正完了報告書です。

```bash
cat docs/SQL_INJECTION_FIX_IMPLEMENTATION_REPORT.md
```

**内容**:
- 実施内容サマリー
- 提供ツール詳細
- セキュリティ強化ポイント
- テスト戦略
- 期待される効果
- 次のステップ

---

## 🎯 よくある質問（FAQ）

### Q1: PRAGMA文は安全ですか？

**A**: PRAGMA文自体は安全ですが、テーブル名を含む場合は注意が必要です。

```python
# ✅ 安全（テーブル名はsqlite_masterから取得）
cursor.execute(
    "SELECT name FROM sqlite_master WHERE type = ?",
    ('table',)
)
tables = [row[0] for row in cursor.fetchall()]

for table in tables:
    # テーブル名は検証済み
    cursor.execute(f"PRAGMA table_info({table})")
```

---

### Q2: テーブル名を動的に扱う必要がある場合は？

**A**: ホワイトリスト検証を実装してください。

```python
ALLOWED_TABLES = {'users', 'works', 'releases'}

def get_table_data(table_name: str):
    if table_name not in ALLOWED_TABLES:
        raise ValueError(f"Invalid table: {table_name}")

    # テーブル名は検証済み
    cursor.execute(f"SELECT * FROM {table_name}")
    return cursor.fetchall()
```

---

### Q3: ORMを使えばSQLインジェクションは防げますか？

**A**: はい、SQLAlchemyなどのORMは自動的にパラメータ化クエリを使用します。

```python
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String)

# 自動的にパラメータ化される
session.query(User).filter(User.username == user_input).all()
```

---

### Q4: 既存コードの修正優先度は？

**A**: 以下の優先順位で修正してください：

1. **HIGH**: ユーザー入力を直接SQLに埋め込んでいる箇所
2. **MEDIUM**: 内部データを使用しているが、パラメータ化していない箇所
3. **LOW**: ハードコードされた値を使用している箇所

---

## 🔍 トラブルシューティング

### スキャンツールが動作しない

```bash
# Python3の確認
python3 --version

# 実行権限の確認
ls -la scripts/scan_sql_vulnerabilities.py

# 実行権限の付与
chmod +x scripts/scan_sql_vulnerabilities.py
```

---

### レポートが生成されない

```bash
# docsディレクトリの確認
ls -la docs/

# ディレクトリが存在しない場合は作成
mkdir -p docs

# 再実行
python3 scripts/scan_sql_vulnerabilities.py
```

---

### CI/CDワークフローが実行されない

1. ワークフローファイルの配置確認
   ```bash
   ls -la .github/workflows/sql-security-scan.yml
   ```

2. YAMLの構文チェック
   ```bash
   yamllint .github/workflows/sql-security-scan.yml
   ```

3. GitHub Actionsの有効化確認
   - リポジトリ設定 → Actions → General

---

## 📞 サポート

### 問い合わせ先

- **技術的な質問**: Database Designer Agent
- **セキュリティ関連**: Security Auditor Agent

### 関連ドキュメント

- [DATABASE_SECURITY_GUIDELINES.md](DATABASE_SECURITY_GUIDELINES.md)
- [SQL_INJECTION_FIX_SUMMARY.md](SQL_INJECTION_FIX_SUMMARY.md)
- [SQL_INJECTION_FIX_IMPLEMENTATION_REPORT.md](SQL_INJECTION_FIX_IMPLEMENTATION_REPORT.md)

---

## 🎓 追加リソース

### 外部リンク

1. **OWASP SQL Injection**
   - https://owasp.org/www-community/attacks/SQL_Injection

2. **Python DB-API 2.0**
   - https://www.python.org/dev/peps/pep-0249/

3. **SQLite Security**
   - https://www.sqlite.org/security.html

### 推奨ツール

- **Bandit**: Pythonセキュリティスキャナー
- **SQLFluff**: SQLリンター
- **pytest**: テストフレームワーク

---

## ✅ チェックリスト

セキュリティ対策の進捗を確認：

- [ ] セットアップスクリプトを実行
- [ ] 脆弱性スキャンを実行
- [ ] 検出された脆弱性を確認
- [ ] 脆弱性を修正
- [ ] ユニットテストを追加
- [ ] テストを実行して確認
- [ ] CI/CDパイプラインを有効化
- [ ] ドキュメントを確認
- [ ] チームに共有

---

**更新日**: 2025-12-07
**作成者**: Database Designer Agent
**バージョン**: 1.0
