#!/usr/bin/env python3
"""
Database Analysis Script for MangaAnime-Info-delivery-system
データベーススキーマ、データ品質、パフォーマンス分析を実行
"""

import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path

class DatabaseAnalyzer:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.analysis_results = {
            "timestamp": datetime.now().isoformat(),
            "database_path": db_path,
            "schema": {},
            "indexes": {},
            "data_statistics": {},
            "integrity_checks": {},
            "performance_issues": [],
            "recommendations": []
        }

    def connect(self):
        """データベース接続"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            print(f"✓ Connected to database: {self.db_path}")
            return True
        except sqlite3.Error as e:
            print(f"✗ Database connection failed: {e}")
            return False

    def analyze_schema(self):
        """スキーマ構造の分析"""
        print("\n=== Analyzing Schema ===")

        # テーブル一覧取得
        self.cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table'
            ORDER BY name
        """)
        tables = [row[0] for row in self.cursor.fetchall()]

        for table in tables:
            # テーブルスキーマ取得
            self.cursor.execute(f"PRAGMA table_info({table})")
            columns = self.cursor.fetchall()

            # 外部キー取得
            self.cursor.execute(f"PRAGMA foreign_key_list({table})")
            foreign_keys = self.cursor.fetchall()

            self.analysis_results["schema"][table] = {
                "columns": [
                    {
                        "cid": col[0],
                        "name": col[1],
                        "type": col[2],
                        "notnull": bool(col[3]),
                        "default_value": col[4],
                        "pk": bool(col[5])
                    }
                    for col in columns
                ],
                "foreign_keys": [
                    {
                        "id": fk[0],
                        "seq": fk[1],
                        "table": fk[2],
                        "from": fk[3],
                        "to": fk[4],
                        "on_update": fk[5],
                        "on_delete": fk[6]
                    }
                    for fk in foreign_keys
                ]
            }

            print(f"  ✓ Table: {table} ({len(columns)} columns, {len(foreign_keys)} foreign keys)")

    def analyze_indexes(self):
        """インデックスの分析"""
        print("\n=== Analyzing Indexes ===")

        for table in self.analysis_results["schema"].keys():
            # インデックス一覧取得
            self.cursor.execute(f"PRAGMA index_list({table})")
            indexes = self.cursor.fetchall()

            table_indexes = []
            for idx in indexes:
                idx_name = idx[1]
                # インデックス詳細取得
                self.cursor.execute(f"PRAGMA index_info({idx_name})")
                idx_info = self.cursor.fetchall()

                table_indexes.append({
                    "name": idx_name,
                    "unique": bool(idx[2]),
                    "origin": idx[3],
                    "partial": bool(idx[4]),
                    "columns": [col[2] for col in idx_info]
                })

            self.analysis_results["indexes"][table] = table_indexes
            print(f"  ✓ Table: {table} ({len(table_indexes)} indexes)")

    def analyze_data_statistics(self):
        """データ統計の分析"""
        print("\n=== Analyzing Data Statistics ===")

        for table in self.analysis_results["schema"].keys():
            # レコード数
            self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = self.cursor.fetchone()[0]

            stats = {
                "total_records": count,
                "column_stats": {}
            }

            if count > 0:
                # 各カラムの統計
                for col_info in self.analysis_results["schema"][table]["columns"]:
                    col_name = col_info["name"]
                    col_type = col_info["type"]

                    try:
                        # NULL値の数
                        self.cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {col_name} IS NULL")
                        null_count = self.cursor.fetchone()[0]

                        # ユニーク値の数
                        self.cursor.execute(f"SELECT COUNT(DISTINCT {col_name}) FROM {table}")
                        distinct_count = self.cursor.fetchone()[0]

                        stats["column_stats"][col_name] = {
                            "type": col_type,
                            "null_count": null_count,
                            "null_percentage": (null_count / count * 100) if count > 0 else 0,
                            "distinct_count": distinct_count,
                            "cardinality": (distinct_count / count) if count > 0 else 0
                        }
                    except Exception as e:
                        print(f"    ⚠ Error analyzing column {table}.{col_name}: {e}")
                        stats["column_stats"][col_name] = {
                            "type": col_type,
                            "error": str(e)
                        }

            self.analysis_results["data_statistics"][table] = stats
            print(f"  ✓ Table: {table} ({count} records)")

    def check_data_integrity(self):
        """データ整合性チェック"""
        print("\n=== Checking Data Integrity ===")

        integrity_results = {}

        # 外部キー制約チェック
        self.cursor.execute("PRAGMA foreign_key_check")
        fk_violations = self.cursor.fetchall()

        integrity_results["foreign_key_violations"] = [
            {
                "table": violation[0],
                "rowid": violation[1],
                "parent": violation[2],
                "fkid": violation[3]
            }
            for violation in fk_violations
        ]

        # 重複チェック
        integrity_results["potential_duplicates"] = {}

        for table, schema in self.analysis_results["schema"].items():
            stats = self.analysis_results["data_statistics"].get(table, {})
            if stats.get("total_records", 0) == 0:
                continue

            # 主キー以外のカラムで重複をチェック
            if table == "works":
                try:
                    self.cursor.execute("""
                        SELECT title, type, COUNT(*) as cnt
                        FROM works
                        GROUP BY title, type
                        HAVING cnt > 1
                    """)
                    duplicates = self.cursor.fetchall()
                    if duplicates:
                        integrity_results["potential_duplicates"][table] = [
                            {"title": d[0], "type": d[1], "count": d[2]}
                            for d in duplicates[:10]
                        ]
                except Exception as e:
                    print(f"    ⚠ Error checking duplicates in {table}: {e}")

            elif table == "releases":
                try:
                    self.cursor.execute("""
                        SELECT work_id, release_type, number, platform, release_date, COUNT(*) as cnt
                        FROM releases
                        GROUP BY work_id, release_type, number, platform, release_date
                        HAVING cnt > 1
                    """)
                    duplicates = self.cursor.fetchall()
                    if duplicates:
                        integrity_results["potential_duplicates"][table] = [
                            {
                                "work_id": d[0],
                                "release_type": d[1],
                                "number": d[2],
                                "platform": d[3],
                                "release_date": d[4],
                                "count": d[5]
                            }
                            for d in duplicates[:10]
                        ]
                except Exception as e:
                    print(f"    ⚠ Error checking duplicates in {table}: {e}")

        self.analysis_results["integrity_checks"] = integrity_results

        if fk_violations:
            print(f"  ✗ Foreign key violations found: {len(fk_violations)}")
        else:
            print(f"  ✓ No foreign key violations")

        dup_count = sum(len(v) for v in integrity_results["potential_duplicates"].values())
        if dup_count > 0:
            print(f"  ⚠ Potential duplicates found: {dup_count} groups")
        else:
            print(f"  ✓ No duplicate issues detected")

    def identify_performance_issues(self):
        """パフォーマンス問題の特定"""
        print("\n=== Identifying Performance Issues ===")

        issues = []

        for table, schema in self.analysis_results["schema"].items():
            stats = self.analysis_results["data_statistics"].get(table, {})
            indexes = self.analysis_results["indexes"].get(table, [])
            record_count = stats.get("total_records", 0)

            # 大きなテーブルの外部キーインデックスチェック
            if record_count > 100:
                fk_columns = set()
                for fk in schema.get("foreign_keys", []):
                    fk_columns.add(fk["from"])

                indexed_columns = set()
                for idx in indexes:
                    indexed_columns.update(idx["columns"])

                missing_indexes = fk_columns - indexed_columns
                if missing_indexes:
                    severity = "HIGH" if record_count > 1000 else "MEDIUM"
                    issues.append({
                        "severity": severity,
                        "table": table,
                        "issue": "Missing indexes on foreign key columns",
                        "details": f"Columns {list(missing_indexes)} are foreign keys but not indexed ({record_count} records)",
                        "recommendation": f"CREATE INDEX idx_{table}_{'_'.join(missing_indexes)} ON {table}({', '.join(missing_indexes)})"
                    })

            # 高カーディナリティカラムのインデックスチェック
            for col_name, col_stats in stats.get("column_stats", {}).items():
                if "error" in col_stats:
                    continue

                cardinality = col_stats.get("cardinality", 0)
                if cardinality > 0.8 and record_count > 100:
                    is_indexed = any(col_name in idx["columns"] for idx in indexes)
                    if not is_indexed and col_name not in ["id", "created_at", "updated_at"]:
                        severity = "MEDIUM" if record_count > 1000 else "LOW"
                        issues.append({
                            "severity": severity,
                            "table": table,
                            "issue": "High cardinality column without index",
                            "details": f"Column '{col_name}' has {cardinality:.1%} cardinality ({record_count} records)",
                            "recommendation": f"Consider: CREATE INDEX idx_{table}_{col_name} ON {table}({col_name})"
                        })

            # NULL値が多いカラム
            for col_name, col_stats in stats.get("column_stats", {}).items():
                if "error" in col_stats:
                    continue

                null_pct = col_stats.get("null_percentage", 0)
                if null_pct > 80 and record_count > 10:
                    issues.append({
                        "severity": "LOW",
                        "table": table,
                        "issue": "High NULL percentage",
                        "details": f"Column '{col_name}' has {null_pct:.1f}% NULL values",
                        "recommendation": f"Review column '{col_name}' necessity or add default values"
                    })

        self.analysis_results["performance_issues"] = issues
        print(f"  Found {len(issues)} potential issues")
        for issue in issues:
            print(f"    [{issue['severity']}] {issue['table']}: {issue['issue']}")

    def generate_recommendations(self):
        """改善提案の生成"""
        print("\n=== Generating Recommendations ===")

        recommendations = []

        # スキーマベースの推奨事項
        for table, schema in self.analysis_results["schema"].items():
            if table == "sqlite_sequence":
                continue

            # タイムスタンプカラムのチェック
            has_created_at = any(col["name"] == "created_at" for col in schema["columns"])
            has_updated_at = any(col["name"] == "updated_at" for col in schema["columns"])

            if not has_created_at:
                recommendations.append({
                    "category": "SCHEMA",
                    "priority": "MEDIUM",
                    "table": table,
                    "recommendation": "Add 'created_at' timestamp for audit trail",
                    "sql": f"ALTER TABLE {table} ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP"
                })

            if not has_updated_at:
                recommendations.append({
                    "category": "SCHEMA",
                    "priority": "LOW",
                    "table": table,
                    "recommendation": "Add 'updated_at' timestamp for modification tracking",
                    "sql": f"ALTER TABLE {table} ADD COLUMN updated_at DATETIME"
                })

        # パフォーマンス改善提案
        for issue in self.analysis_results["performance_issues"]:
            if issue["severity"] in ["HIGH", "MEDIUM"]:
                sql_match = None
                if "CREATE INDEX" in issue["recommendation"]:
                    parts = issue["recommendation"].split("CREATE INDEX")
                    if len(parts) > 1:
                        sql_match = "CREATE INDEX" + parts[1]

                recommendations.append({
                    "category": "PERFORMANCE",
                    "priority": issue["severity"],
                    "table": issue["table"],
                    "recommendation": issue["details"],
                    "sql": sql_match
                })

        # データ整合性改善提案
        if self.analysis_results["integrity_checks"].get("foreign_key_violations"):
            recommendations.append({
                "category": "INTEGRITY",
                "priority": "HIGH",
                "table": "ALL",
                "recommendation": "Fix foreign key violations before enabling PRAGMA foreign_keys=ON",
                "sql": "-- Manual cleanup required"
            })

        # 正規化の提案
        for table, stats in self.analysis_results["data_statistics"].items():
            for col_name, col_stats in stats.get("column_stats", {}).items():
                if "error" in col_stats:
                    continue

                cardinality = col_stats.get("cardinality", 1)
                record_count = stats.get("total_records", 0)
                distinct_count = col_stats.get("distinct_count", 0)

                if cardinality < 0.05 and record_count > 100 and distinct_count > 1:
                    recommendations.append({
                        "category": "NORMALIZATION",
                        "priority": "LOW",
                        "table": table,
                        "recommendation": f"Column '{col_name}' has low cardinality ({distinct_count} values in {record_count} records) - consider normalization",
                        "sql": None
                    })

        self.analysis_results["recommendations"] = recommendations
        print(f"  Generated {len(recommendations)} recommendations")

    def generate_report(self, output_path: str):
        """分析レポートの生成"""
        print("\n=== Generating Report ===")

        report = []
        report.append("# Database Analysis Report")
        report.append(f"\n**Generated**: {self.analysis_results['timestamp']}")
        report.append(f"**Database**: {self.analysis_results['database_path']}")

        # エグゼクティブサマリー
        total_tables = len(self.analysis_results["schema"])
        total_records = sum(s.get("total_records", 0) for s in self.analysis_results["data_statistics"].values())
        total_issues = len(self.analysis_results["performance_issues"])
        total_recommendations = len(self.analysis_results["recommendations"])

        report.append("\n## Executive Summary")
        report.append(f"- Total Tables: {total_tables}")
        report.append(f"- Total Records: {total_records:,}")
        report.append(f"- Performance Issues: {total_issues}")
        report.append(f"- Recommendations: {total_recommendations}")

        # スキーマ図
        report.append("\n## 1. Schema Structure")
        for table, schema in sorted(self.analysis_results["schema"].items()):
            report.append(f"\n### Table: `{table}`")
            report.append("\n| Column | Type | Nullable | Default | PK |")
            report.append("|--------|------|----------|---------|-----|")
            for col in schema["columns"]:
                nullable = "Yes" if not col['notnull'] else "No"
                default = col['default_value'] if col['default_value'] else "-"
                pk = "✓" if col['pk'] else ""
                report.append(f"| {col['name']} | {col['type']} | {nullable} | {default} | {pk} |")

            if schema["foreign_keys"]:
                report.append("\n**Foreign Keys:**")
                for fk in schema["foreign_keys"]:
                    report.append(f"- `{fk['from']}` → `{fk['table']}.{fk['to']}`")

        # インデックス
        report.append("\n## 2. Indexes")
        total_indexes = sum(len(idx) for idx in self.analysis_results["indexes"].values())
        report.append(f"\n**Total Indexes**: {total_indexes}")

        for table, indexes in sorted(self.analysis_results["indexes"].items()):
            if indexes:
                report.append(f"\n### Table: `{table}`")
                for idx in indexes:
                    unique_str = " (UNIQUE)" if idx["unique"] else ""
                    cols = ", ".join(idx["columns"])
                    report.append(f"- `{idx['name']}`{unique_str}: {cols}")

        # データ統計
        report.append("\n## 3. Data Statistics")
        for table, stats in sorted(self.analysis_results["data_statistics"].items()):
            report.append(f"\n### Table: `{table}`")
            report.append(f"\n**Total Records**: {stats['total_records']:,}")

            if stats.get("column_stats"):
                report.append("\n| Column | Type | Distinct | NULL % | Cardinality |")
                report.append("|--------|------|----------|--------|-------------|")
                for col_name, col_stats in stats["column_stats"].items():
                    if "error" in col_stats:
                        report.append(f"| {col_name} | {col_stats['type']} | ERROR | - | - |")
                    else:
                        report.append(
                            f"| {col_name} | {col_stats['type']} | "
                            f"{col_stats['distinct_count']:,} | "
                            f"{col_stats['null_percentage']:.1f}% | "
                            f"{col_stats['cardinality']:.1%} |"
                        )

        # 整合性チェック
        report.append("\n## 4. Data Integrity")
        integrity = self.analysis_results["integrity_checks"]

        if integrity.get("foreign_key_violations"):
            report.append("\n### ⚠️ Foreign Key Violations")
            report.append(f"\n**Count**: {len(integrity['foreign_key_violations'])}")
            for violation in integrity["foreign_key_violations"][:10]:
                report.append(f"- Table `{violation['table']}` row {violation['rowid']}")
        else:
            report.append("\n### ✅ Foreign Key Integrity")
            report.append("\nNo foreign key violations detected")

        if integrity.get("potential_duplicates"):
            report.append("\n### ⚠️ Potential Duplicates")
            for table, duplicates in integrity["potential_duplicates"].items():
                report.append(f"\n**Table**: `{table}` ({len(duplicates)} groups)")
                for dup in duplicates[:5]:
                    report.append(f"- {dup}")
        else:
            report.append("\n### ✅ No Duplicates Detected")

        # パフォーマンス問題
        report.append("\n## 5. Performance Issues")
        if self.analysis_results["performance_issues"]:
            # 重要度別に分類
            by_severity = {"HIGH": [], "MEDIUM": [], "LOW": []}
            for issue in self.analysis_results["performance_issues"]:
                by_severity[issue["severity"]].append(issue)

            for severity in ["HIGH", "MEDIUM", "LOW"]:
                issues = by_severity[severity]
                if issues:
                    report.append(f"\n### [{severity}] Issues ({len(issues)})")
                    for issue in issues:
                        report.append(f"\n**Table**: `{issue['table']}`")
                        report.append(f"- **Issue**: {issue['issue']}")
                        report.append(f"- **Details**: {issue['details']}")
                        report.append(f"- **Fix**: {issue['recommendation']}")
        else:
            report.append("\n### ✅ No Critical Performance Issues")

        # 改善提案
        report.append("\n## 6. Recommendations")
        if self.analysis_results["recommendations"]:
            # カテゴリ別にグループ化
            by_category = {}
            for rec in self.analysis_results["recommendations"]:
                cat = rec["category"]
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(rec)

            for category in ["INTEGRITY", "PERFORMANCE", "SCHEMA", "NORMALIZATION"]:
                recs = by_category.get(category, [])
                if recs:
                    report.append(f"\n### {category} ({len(recs)} items)")
                    for rec in recs:
                        report.append(f"\n**[{rec['priority']}]** {rec['table']}")
                        report.append(f"- {rec['recommendation']}")
                        if rec.get("sql"):
                            report.append(f"\n```sql\n{rec['sql']}\n```")
        else:
            report.append("\n### ✅ Database is Well-Optimized")

        # ER図（Mermaid形式）
        report.append("\n## 7. ER Diagram")
        report.append("\n```mermaid")
        report.append("erDiagram")
        for table, schema in self.analysis_results["schema"].items():
            if table == "sqlite_sequence":
                continue

            # テーブル定義
            report.append(f"    {table.upper()} {{")
            for col in schema["columns"]:
                col_type = col["type"] or "ANY"
                pk_str = " PK" if col["pk"] else ""
                report.append(f"        {col_type} {col['name']}{pk_str}")
            report.append("    }")

            # リレーション
            for fk in schema.get("foreign_keys", []):
                report.append(f"    {table.upper()} ||--o{{ {fk['table'].upper()} : \"{fk['from']}\"")

        report.append("```")

        # ファイル出力
        report_content = "\n".join(report)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report_content)

        print(f"  ✓ Report saved to: {output_path}")

        # JSON出力
        json_path = output_path.replace(".md", ".json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(self.analysis_results, f, indent=2, ensure_ascii=False)

        print(f"  ✓ JSON data saved to: {json_path}")

        return report_path, json_path

    def close(self):
        """データベース接続のクローズ"""
        if self.conn:
            self.conn.close()
            print("\n✓ Database connection closed")

    def run_full_analysis(self, report_path: str):
        """完全分析の実行"""
        print("=" * 60)
        print("DATABASE ANALYSIS TOOL")
        print("=" * 60)

        if not self.connect():
            return False

        try:
            self.analyze_schema()
            self.analyze_indexes()
            self.analyze_data_statistics()
            self.check_data_integrity()
            self.identify_performance_issues()
            self.generate_recommendations()
            md_path, json_path = self.generate_report(report_path)

            print("\n" + "=" * 60)
            print("ANALYSIS COMPLETE")
            print("=" * 60)
            print(f"\n📊 Markdown Report: {md_path}")
            print(f"📊 JSON Data: {json_path}")

            return True

        except Exception as e:
            print(f"\n✗ Analysis failed: {e}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            self.close()


def main():
    # データベースパスの設定
    project_root = Path(__file__).parent
    db_path = project_root / "db.sqlite3"

    if not db_path.exists():
        print(f"⚠ Database not found: {db_path}")
        print("  Note: This script will analyze the existing database when available.")
        return 1

    # レポート出力パス
    report_path = project_root / "docs" / "database_analysis_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    # 分析実行
    analyzer = DatabaseAnalyzer(str(db_path))
    success = analyzer.run_full_analysis(str(report_path))

    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
