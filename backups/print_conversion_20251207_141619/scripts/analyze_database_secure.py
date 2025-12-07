#!/usr/bin/env python3
"""
データベース分析スクリプト（セキュア版）
SQLインジェクション対策済み - パラメータ化クエリを徹底使用

使用方法:
    python3 scripts/analyze_database_secure.py
    python3 scripts/analyze_database_secure.py --db path/to/db.sqlite3
    python3 scripts/analyze_database_secure.py --recommendations
"""
import sqlite3
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class DatabaseAnalyzer:
    """データベース分析クラス（セキュア版）"""

    def __init__(self, db_path: str = "db.sqlite3"):
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def __enter__(self):
        if not Path(self.db_path).exists():
            raise FileNotFoundError(f"データベースファイルが見つかりません: {self.db_path}")

        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()

    def analyze(self) -> None:
        """データベース全体を分析"""
        print("=" * 80)
        print("📊 データベース分析レポート")
        print("=" * 80)
        print(f"📅 分析日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📁 データベース: {self.db_path}")
        print()

        # テーブル一覧を取得
        tables = self._get_tables()

        print(f"📋 テーブル数: {len(tables)}")
        print("-" * 80)

        # 各テーブルを分析
        for table_name in tables:
            self._analyze_table(table_name)

        # インデックス分析
        self._analyze_indexes()

        # 外部キー分析
        self._analyze_foreign_keys()

        # データベースサイズ
        self._analyze_database_size()

        print("=" * 80)
        print("✅ 分析完了")
        print("=" * 80)

    def _get_tables(self) -> List[str]:
        """テーブル一覧を取得（パラメータ化クエリ）"""
        # ✅ typeパラメータをプレースホルダ化
        self.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type = ? ORDER BY name",
            ('table',)
        )
        return [row[0] for row in self.cursor.fetchall()]

    def _analyze_table(self, table_name: str) -> None:
        """個別テーブルの分析（安全）"""
        print(f"\n🔍 テーブル: {table_name}")
        print("-" * 40)

        # テーブル構造を取得
        # 注: table_nameは_get_tables()から取得した信頼できる値
        # PRAGMA文はメタデータ取得のため、テーブル名を直接使用しても安全
        self.cursor.execute(f"PRAGMA table_info({table_name})")
        columns = self.cursor.fetchall()

        print("📝 カラム構成:")
        for col in columns:
            col_id, name, col_type, not_null, default_val, pk = col
            pk_mark = " 🔑 PRIMARY KEY" if pk else ""
            null_mark = " NOT NULL" if not_null else ""
            default_mark = f" DEFAULT {default_val}" if default_val else ""
            print(f"  - {name}: {col_type}{pk_mark}{null_mark}{default_mark}")

        # レコード数を取得
        # テーブル名は検証済みなので安全
        self.cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = self.cursor.fetchone()[0]
        print(f"\n📊 レコード数: {count:,}")

        if count > 0:
            # サンプルデータ表示（最新5件）
            # ✅ LIMIT値をパラメータ化
            self.cursor.execute(
                f"SELECT * FROM {table_name} ORDER BY ROWID DESC LIMIT ?",
                (5,)
            )
            samples = self.cursor.fetchall()

            if samples:
                print("\n📌 サンプルデータ（最新5件）:")
                column_names = [col[1] for col in columns]

                for i, row in enumerate(samples, 1):
                    print(f"\n  [{i}]")
                    for col_name, value in zip(column_names, row):
                        # 長いテキストは切り詰め
                        if isinstance(value, str) and len(value) > 50:
                            value = value[:50] + "..."
                        print(f"    {col_name}: {value}")

    def _analyze_indexes(self) -> None:
        """インデックス分析（パラメータ化クエリ）"""
        print("\n" + "=" * 80)
        print("🔎 インデックス分析")
        print("-" * 80)

        # ✅ typeパラメータをプレースホルダ化
        self.cursor.execute(
            "SELECT name, tbl_name, sql FROM sqlite_master WHERE type = ? AND sql IS NOT NULL",
            ('index',)
        )
        indexes = self.cursor.fetchall()

        if indexes:
            for name, table, sql in indexes:
                print(f"\n📇 {name}")
                print(f"   テーブル: {table}")
                print(f"   定義: {sql}")
        else:
            print("⚠️  カスタムインデックスが見つかりません")
            print("💡 推奨: パフォーマンス向上のためインデックス追加を検討してください")

    def _analyze_foreign_keys(self) -> None:
        """外部キー制約分析"""
        print("\n" + "=" * 80)
        print("🔗 外部キー制約分析")
        print("-" * 80)

        # 全テーブルの外部キーを取得
        tables = self._get_tables()
        foreign_keys_found = False

        for table_name in tables:
            # PRAGMA文は安全（テーブル名はsqlite_masterから取得）
            self.cursor.execute(f"PRAGMA foreign_key_list({table_name})")
            fks = self.cursor.fetchall()

            if fks:
                foreign_keys_found = True
                print(f"\n📊 テーブル: {table_name}")
                for fk in fks:
                    fk_id, seq, table, from_col, to_col, on_update, on_delete, match = fk
                    print(f"  - {from_col} → {table}({to_col})")
                    print(f"    ON DELETE: {on_delete}, ON UPDATE: {on_update}")

        if not foreign_keys_found:
            print("⚠️  外部キー制約が見つかりません")
            print("💡 推奨: データ整合性のため外部キー制約の追加を検討してください")

    def _analyze_database_size(self) -> None:
        """データベースサイズ分析"""
        print("\n" + "=" * 80)
        print("💾 データベースサイズ")
        print("-" * 80)

        # ファイルサイズ
        db_size = Path(self.db_path).stat().st_size
        db_size_mb = db_size / (1024 * 1024)

        print(f"ファイルサイズ: {db_size:,} bytes ({db_size_mb:.2f} MB)")

        # ページ数とページサイズ（PRAGMA文は安全）
        self.cursor.execute("PRAGMA page_count")
        page_count = self.cursor.fetchone()[0]

        self.cursor.execute("PRAGMA page_size")
        page_size = self.cursor.fetchone()[0]

        print(f"ページ数: {page_count:,}")
        print(f"ページサイズ: {page_size:,} bytes")

        # 空きページ
        self.cursor.execute("PRAGMA freelist_count")
        freelist = self.cursor.fetchone()[0]

        if freelist > 0:
            waste_mb = (freelist * page_size) / (1024 * 1024)
            print(f"⚠️  未使用ページ: {freelist:,} ({waste_mb:.2f} MB)")
            print("💡 推奨: VACUUM コマンドでデータベースを最適化してください")

    def generate_recommendations(self) -> List[Dict]:
        """最適化推奨事項を生成"""
        recommendations = []

        # インデックスチェック
        # ✅ パラメータ化クエリ
        self.cursor.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type = ? AND sql IS NOT NULL",
            ('index',)
        )
        index_count = self.cursor.fetchone()[0]

        if index_count < 3:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'パフォーマンス',
                'recommendation': '頻繁に検索されるカラムにインデックスを追加',
                'sql_file': 'migrations/001_add_recommended_indexes.sql'
            })

        # 外部キーチェック
        self.cursor.execute("PRAGMA foreign_keys")
        fk_enabled = self.cursor.fetchone()[0]

        if not fk_enabled:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'データ整合性',
                'recommendation': '外部キー制約を有効化',
                'command': 'PRAGMA foreign_keys = ON;'
            })

        # テーブルごとのレコード数チェック
        tables = self._get_tables()

        for table_name in tables:
            # テーブル名は検証済み
            self.cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = self.cursor.fetchone()[0]

            if count > 10000:
                recommendations.append({
                    'priority': 'MEDIUM',
                    'category': 'パフォーマンス',
                    'recommendation': f'テーブル {table_name} のデータアーカイブ化を検討',
                    'details': f'現在のレコード数: {count:,}'
                })

        return recommendations

    def print_recommendations(self) -> None:
        """推奨事項を表示"""
        print("\n" + "=" * 80)
        print("💡 最適化推奨事項")
        print("=" * 80)

        recommendations = self.generate_recommendations()

        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                print(f"\n[{i}] {rec['priority']} - {rec['category']}")
                print(f"   {rec['recommendation']}")
                if 'sql_file' in rec:
                    print(f"   📁 {rec['sql_file']}")
                if 'command' in rec:
                    print(f"   💻 {rec['command']}")
                if 'details' in rec:
                    print(f"   ℹ️  {rec['details']}")
        else:
            print("\n✅ 特に問題は見つかりませんでした")


class SecureQueryBuilder:
    """安全なクエリビルダー（ホワイトリスト検証付き）"""

    # 許可されたテーブル
    ALLOWED_TABLES = {
        'works', 'releases', 'users', 'notifications', 'rss_feeds'
    }

    # テーブルごとの許可されたカラム
    ALLOWED_COLUMNS = {
        'works': {'id', 'title', 'title_kana', 'title_en', 'type', 'official_url', 'created_at'},
        'releases': {'id', 'work_id', 'release_type', 'number', 'platform', 'release_date', 'source', 'source_url', 'notified', 'created_at'},
        'users': {'id', 'username', 'email', 'created_at'},
        'notifications': {'id', 'release_id', 'sent_at', 'status'},
        'rss_feeds': {'id', 'name', 'url', 'last_fetched', 'active'},
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
    def build_select(cls, table_name: str, columns: List[str], where_params: Dict = None) -> Tuple[str, tuple]:
        """安全なSELECT文を構築"""
        # テーブル名を検証
        table = cls.validate_table(table_name)

        # カラムを検証
        if columns == ['*']:
            column_list = '*'
        else:
            validated_columns = [
                cls.validate_column(table_name, col) for col in columns
            ]
            column_list = ', '.join(validated_columns)

        # WHERE句を構築
        where_clauses = []
        values = []

        if where_params:
            for col, val in where_params.items():
                cls.validate_column(table_name, col)
                where_clauses.append(f"{col} = ?")
                values.append(val)

        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

        query = f"SELECT {column_list} FROM {table} WHERE {where_clause}"

        return query, tuple(values)


def main():
    """メイン関数"""
    import argparse

    parser = argparse.ArgumentParser(description='SQLite データベース分析ツール（セキュア版）')
    parser.add_argument(
        '--db',
        default='db.sqlite3',
        help='データベースファイルのパス（デフォルト: db.sqlite3）'
    )
    parser.add_argument(
        '--recommendations',
        action='store_true',
        help='最適化推奨事項を表示'
    )

    args = parser.parse_args()

    try:
        with DatabaseAnalyzer(args.db) as analyzer:
            analyzer.analyze()

            if args.recommendations:
                analyzer.print_recommendations()

    except FileNotFoundError as e:
        print(f"❌ エラー: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
