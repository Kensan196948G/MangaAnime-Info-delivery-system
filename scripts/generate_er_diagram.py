#!/usr/bin/env python3
"""
ER Diagram Generator
データベーススキーマからER図（テキスト形式）を生成
"""

import sqlite3
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "db.sqlite3"


class ERDiagramGenerator:
    """ER図生成クラス"""

    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.tables = {}
        self.relationships = []

    def connect(self):
        """データベース接続"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def close(self):
        """データベース切断"""
        if self.conn:
            self.conn.close()

    def analyze_tables(self):
        """テーブル構造解析"""
        # テーブル一覧取得
        self.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        table_names = [row[0] for row in self.cursor.fetchall()]

        for table_name in table_names:
            # カラム情報取得
            self.cursor.execute(f"PRAGMA table_info({table_name})")
            columns = []

            for col in self.cursor.fetchall():
                col_info = {
                    "name": col[1],
                    "type": col[2],
                    "notnull": col[3],
                    "default": col[4],
                    "pk": col[5]
                }
                columns.append(col_info)

            # 外部キー情報取得
            self.cursor.execute(f"PRAGMA foreign_key_list({table_name})")
            foreign_keys = []

            for fk in self.cursor.fetchall():
                fk_info = {
                    "from_col": fk[3],
                    "to_table": fk[2],
                    "to_col": fk[4],
                    "on_delete": fk[6],
                    "on_update": fk[5]
                }
                foreign_keys.append(fk_info)

                # リレーションシップ記録
                self.relationships.append({
                    "from_table": table_name,
                    "from_col": fk[3],
                    "to_table": fk[2],
                    "to_col": fk[4],
                    "type": "1:N"  # SQLiteでは基本的に1:N
                })

            # インデックス情報取得
            self.cursor.execute(f"PRAGMA index_list({table_name})")
            indexes = [row[1] for row in self.cursor.fetchall()]

            self.tables[table_name] = {
                "columns": columns,
                "foreign_keys": foreign_keys,
                "indexes": indexes
            }

    def generate_ascii_diagram(self):
        """ASCII形式のER図生成"""
        lines = []
        lines.append("\n" + "=" * 80)
        lines.append("DATABASE SCHEMA - ER DIAGRAM")
        lines.append("=" * 80 + "\n")

        # 各テーブルの詳細
        for table_name, info in self.tables.items():
            max_name_len = max(len(col["name"]) for col in info["columns"]) + 2
            max_type_len = max(len(col["type"]) for col in info["columns"]) + 2

            # テーブルヘッダー
            box_width = max(50, max_name_len + max_type_len + 20)
            lines.append("┌" + "─" * (box_width - 2) + "┐")
            lines.append("│ " + table_name.upper().center(box_width - 4) + " │")
            lines.append("├" + "─" * (box_width - 2) + "┤")

            # カラム一覧
            for col in info["columns"]:
                markers = []
                if col["pk"]:
                    markers.append("PK")
                if col["notnull"]:
                    markers.append("NOT NULL")

                # 外部キーチェック
                for fk in info["foreign_keys"]:
                    if fk["from_col"] == col["name"]:
                        markers.append(f"FK→{fk['to_table']}")

                marker_str = " ".join(markers) if markers else ""

                col_line = f"│ {col['name']:<{max_name_len}} {col['type']:<{max_type_len}} {marker_str}"
                col_line += " " * (box_width - len(col_line) - 1) + "│"
                lines.append(col_line)

            lines.append("└" + "─" * (box_width - 2) + "┘\n")

        # リレーションシップ
        if self.relationships:
            lines.append("\n" + "=" * 80)
            lines.append("RELATIONSHIPS")
            lines.append("=" * 80 + "\n")

            for rel in self.relationships:
                lines.append(
                    f"{rel['from_table']}.{rel['from_col']} "
                    f"──► {rel['to_table']}.{rel['to_col']} "
                    f"({rel['type']})"
                )

        return "\n".join(lines)

    def generate_mermaid_diagram(self):
        """Mermaid形式のER図生成（Markdown用）"""
        lines = []
        lines.append("```mermaid")
        lines.append("erDiagram")

        # リレーションシップ定義
        for rel in self.relationships:
            # Mermaid記法: TableA ||--o{ TableB : relationship
            lines.append(
                f"    {rel['to_table']} ||--o{{ {rel['from_table']} : has"
            )

        # テーブル定義
        for table_name, info in self.tables.items():
            lines.append(f"\n    {table_name} {{")

            for col in info["columns"]:
                col_type = col["type"] or "TEXT"
                constraints = []

                if col["pk"]:
                    constraints.append("PK")
                if col["notnull"]:
                    constraints.append("NOT NULL")

                # 外部キーチェック
                for fk in info["foreign_keys"]:
                    if fk["from_col"] == col["name"]:
                        constraints.append(f"FK")

                constraint_str = f" {','.join(constraints)}" if constraints else ""
                lines.append(f"        {col_type} {col['name']}{constraint_str}")

            lines.append("    }")

        lines.append("```")
        return "\n".join(lines)

    def generate_dbml_diagram(self):
        """DBML形式のER図生成（dbdiagram.io用）"""
        lines = []
        lines.append("// Database Schema (DBML Format)")
        lines.append("// Generated by ER Diagram Generator")
        lines.append("// Visit https://dbdiagram.io to visualize\n")

        # テーブル定義
        for table_name, info in self.tables.items():
            lines.append(f"Table {table_name} {{")

            for col in info["columns"]:
                col_type = col["type"] or "TEXT"
                constraints = []

                if col["pk"]:
                    constraints.append("pk")
                if col["notnull"]:
                    constraints.append("not null")
                if col["default"]:
                    constraints.append(f"default: {col['default']}")

                constraint_str = f" [{', '.join(constraints)}]" if constraints else ""
                lines.append(f"  {col['name']} {col_type}{constraint_str}")

            lines.append("}\n")

        # リレーションシップ定義
        if self.relationships:
            for rel in self.relationships:
                lines.append(
                    f"Ref: {rel['from_table']}.{rel['from_col']} "
                    f"> {rel['to_table']}.{rel['to_col']}"
                )

        return "\n".join(lines)

    def save_diagrams(self):
        """各形式のダイアグラムをファイル保存"""
        output_dir = PROJECT_ROOT / "docs" / "database"
        output_dir.mkdir(parents=True, exist_ok=True)

        # ASCII形式
        ascii_path = output_dir / "schema_ascii.txt"
        with open(ascii_path, "w", encoding="utf-8") as f:
            f.write(self.generate_ascii_diagram())
        print(f"[INFO] ASCII diagram saved: {ascii_path}")

        # Mermaid形式
        mermaid_path = output_dir / "schema_mermaid.md"
        with open(mermaid_path, "w", encoding="utf-8") as f:
            f.write("# Database Schema - Mermaid Diagram\n\n")
            f.write(self.generate_mermaid_diagram())
        print(f"[INFO] Mermaid diagram saved: {mermaid_path}")

        # DBML形式
        dbml_path = output_dir / "schema.dbml"
        with open(dbml_path, "w", encoding="utf-8") as f:
            f.write(self.generate_dbml_diagram())
        print(f"[INFO] DBML diagram saved: {dbml_path}")

        # 統計情報
        stats_path = output_dir / "schema_stats.json"
        import json
        stats = {
            "total_tables": len(self.tables),
            "total_relationships": len(self.relationships),
            "tables": {
                name: {
                    "columns": len(info["columns"]),
                    "foreign_keys": len(info["foreign_keys"]),
                    "indexes": len(info["indexes"])
                }
                for name, info in self.tables.items()
            }
        }
        with open(stats_path, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        print(f"[INFO] Schema stats saved: {stats_path}")

    def run(self):
        """ER図生成実行"""
        print("\n[INFO] Analyzing database schema...")
        self.analyze_tables()

        print(f"[INFO] Found {len(self.tables)} tables")
        print(f"[INFO] Found {len(self.relationships)} relationships")

        print("\n[INFO] Generating diagrams...")
        self.save_diagrams()

        print("\n[SUCCESS] ER diagrams generated successfully!\n")


def main():
    """メイン関数"""
    generator = ERDiagramGenerator()

    try:
        generator.connect()
        generator.run()

    except Exception as e:
        print(f"\n[ERROR] Diagram generation failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        generator.close()


if __name__ == "__main__":
    main()
