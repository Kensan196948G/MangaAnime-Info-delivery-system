#!/usr/bin/env python3
"""
Database Validator
データベース整合性・パフォーマンス・セキュリティチェックツール
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "db.sqlite3"


class DatabaseValidator:
    """データベース検証クラス"""

    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.issues = []
        self.warnings = []
        self.info = []

    def connect(self):
        """データベース接続"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def close(self):
        """データベース切断"""
        if self.conn:
            self.conn.close()

    def add_issue(self, category, message):
        """問題点を記録"""
        self.issues.append({"category": category, "message": message})

    def add_warning(self, category, message):
        """警告を記録"""
        self.warnings.append({"category": category, "message": message})

    def add_info(self, category, message):
        """情報を記録"""
        self.info.append({"category": category, "message": message})

    def check_foreign_keys(self):
        """外部キー制約チェック"""
        print("\n[CHECK] Foreign Key Constraints")

        # 外部キーが有効か確認
        self.cursor.execute("PRAGMA foreign_keys")
        fk_enabled = self.cursor.fetchone()[0]

        if fk_enabled:
            self.add_info("Foreign Keys", "Foreign key constraints are ENABLED")
        else:
            self.add_issue("Foreign Keys", "Foreign key constraints are DISABLED")

        # 外部キー違反チェック
        self.cursor.execute("PRAGMA foreign_key_check")
        violations = self.cursor.fetchall()

        if violations:
            for violation in violations:
                self.add_issue(
                    "Foreign Key Violation",
                    f"Table: {violation[0]}, Row: {violation[1]}, "
                    f"Parent: {violation[2]}, FK Index: {violation[3]}"
                )
        else:
            self.add_info("Foreign Keys", "No foreign key violations found")

    def check_indexes(self):
        """インデックスチェック"""
        print("\n[CHECK] Indexes")

        # すべてのテーブル取得
        self.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%'"
        )
        tables = [row[0] for row in self.cursor.fetchall()]

        for table in tables:
            # テーブルのインデックス一覧
            self.cursor.execute(
                f"SELECT name FROM sqlite_master "
                f"WHERE type='index' AND tbl_name='{table}'"
            )
            indexes = [row[0] for row in self.cursor.fetchall()]

            if not indexes:
                self.add_warning("Index", f"Table '{table}' has no indexes")
            else:
                self.add_info("Index", f"Table '{table}' has {len(indexes)} index(es)")

            # 外部キー列にインデックスがあるか確認
            self.cursor.execute(f"PRAGMA foreign_key_list({table})")
            fks = self.cursor.fetchall()

            for fk in fks:
                fk_column = fk[3]  # from column
                # インデックス名に列名が含まれているか簡易チェック
                has_index = any(fk_column in idx for idx in indexes)

                if not has_index:
                    self.add_warning(
                        "Index",
                        f"Foreign key column '{table}.{fk_column}' might need an index"
                    )

    def check_data_integrity(self):
        """データ整合性チェック"""
        print("\n[CHECK] Data Integrity")

        # works テーブル
        if self.table_exists("works"):
            # 空のタイトルチェック
            self.cursor.execute("SELECT COUNT(*) FROM works WHERE title IS NULL OR TRIM(title) = ''")
            empty_titles = self.cursor.fetchone()[0]
            if empty_titles > 0:
                self.add_issue("Data Integrity", f"Found {empty_titles} works with empty titles")

            # タイプ不正チェック
            self.cursor.execute("SELECT COUNT(*) FROM works WHERE type NOT IN ('anime', 'manga')")
            invalid_types = self.cursor.fetchone()[0]
            if invalid_types > 0:
                self.add_issue("Data Integrity", f"Found {invalid_types} works with invalid type")

        # releases テーブル
        if self.table_exists("releases"):
            # 未通知の古いリリース
            self.cursor.execute(
                "SELECT COUNT(*) FROM releases "
                "WHERE notified = 0 AND release_date < DATE('now', '-7 days')"
            )
            old_unnotified = self.cursor.fetchone()[0]
            if old_unnotified > 0:
                self.add_warning(
                    "Data Integrity",
                    f"Found {old_unnotified} unnotified releases older than 7 days"
                )

            # 未来すぎるリリース日
            self.cursor.execute(
                "SELECT COUNT(*) FROM releases "
                "WHERE release_date > DATE('now', '+2 years')"
            )
            far_future = self.cursor.fetchone()[0]
            if far_future > 0:
                self.add_warning(
                    "Data Integrity",
                    f"Found {far_future} releases more than 2 years in the future"
                )

    def check_performance(self):
        """パフォーマンスチェック"""
        print("\n[CHECK] Performance")

        # データベースサイズ
        db_size = self.db_path.stat().st_size / (1024 * 1024)  # MB
        self.add_info("Performance", f"Database size: {db_size:.2f} MB")

        if db_size > 100:
            self.add_warning("Performance", "Database size exceeds 100MB - consider archiving old data")

        # ANALYZE統計の確認
        self.cursor.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='sqlite_stat1'"
        )
        has_stats = self.cursor.fetchone()[0] > 0

        if has_stats:
            self.add_info("Performance", "ANALYZE statistics present")
        else:
            self.add_warning("Performance", "No ANALYZE statistics - run 'ANALYZE;' to optimize queries")

        # 各テーブルのレコード数
        self.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%'"
        )
        tables = [row[0] for row in self.cursor.fetchall()]

        for table in tables:
            self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = self.cursor.fetchone()[0]
            self.add_info("Table Stats", f"{table}: {count:,} records")

    def check_normalization(self):
        """正規化チェック"""
        print("\n[CHECK] Normalization")

        # 重複データチェック（works テーブル）
        if self.table_exists("works"):
            self.cursor.execute(
                "SELECT title, type, COUNT(*) as cnt FROM works "
                "GROUP BY title, type HAVING cnt > 1"
            )
            duplicates = self.cursor.fetchall()

            if duplicates:
                for dup in duplicates:
                    self.add_warning(
                        "Normalization",
                        f"Duplicate work found: '{dup[0]}' ({dup[1]}) - {dup[2]} times"
                    )
            else:
                self.add_info("Normalization", "No duplicate works found")

    def check_security(self):
        """セキュリティチェック"""
        print("\n[CHECK] Security")

        # ユーザーテーブルのパスワードハッシュ確認（存在する場合）
        if self.table_exists("users"):
            self.cursor.execute("PRAGMA table_info(users)")
            columns = [col[1] for col in self.cursor.fetchall()]

            if "password" in columns:
                self.add_issue(
                    "Security",
                    "Table 'users' has 'password' column - ensure it's hashed!"
                )

            if "email" in columns:
                # 平文メールアドレスの警告
                self.add_warning(
                    "Security",
                    "Email addresses stored in plaintext - consider encryption for sensitive data"
                )

    def table_exists(self, table_name):
        """テーブル存在確認"""
        self.cursor.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        return self.cursor.fetchone()[0] > 0

    def generate_report(self):
        """レポート生成"""
        print("\n" + "=" * 70)
        print("DATABASE VALIDATION REPORT")
        print("=" * 70)
        print(f"Database: {self.db_path}")
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)

        # 問題点
        if self.issues:
            print(f"\n[ISSUES] {len(self.issues)} issue(s) found:")
            for i, issue in enumerate(self.issues, 1):
                print(f"  {i}. [{issue['category']}] {issue['message']}")
        else:
            print("\n[ISSUES] No critical issues found")

        # 警告
        if self.warnings:
            print(f"\n[WARNINGS] {len(self.warnings)} warning(s):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. [{warning['category']}] {warning['message']}")
        else:
            print("\n[WARNINGS] No warnings")

        # 情報
        if self.info:
            print(f"\n[INFO] {len(self.info)} informational message(s):")
            for i, info in enumerate(self.info, 1):
                print(f"  {i}. [{info['category']}] {info['message']}")

        print("\n" + "=" * 70)

        # スコア計算
        score = 100
        score -= len(self.issues) * 10
        score -= len(self.warnings) * 2
        score = max(0, score)

        if score >= 90:
            status = "EXCELLENT"
        elif score >= 70:
            status = "GOOD"
        elif score >= 50:
            status = "FAIR"
        else:
            status = "NEEDS IMPROVEMENT"

        print(f"\nOVERALL SCORE: {score}/100 ({status})")
        print("=" * 70 + "\n")

    def run_all_checks(self):
        """すべてのチェック実行"""
        self.check_foreign_keys()
        self.check_indexes()
        self.check_data_integrity()
        self.check_performance()
        self.check_normalization()
        self.check_security()
        self.generate_report()


def main():
    """メイン関数"""
    print("Starting Database Validation...")

    validator = DatabaseValidator()

    try:
        validator.connect()
        validator.run_all_checks()

    except Exception as e:
        print(f"\n[ERROR] Validation failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        validator.close()


if __name__ == "__main__":
    main()
