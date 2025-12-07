#!/usr/bin/env python3
"""
データベース構造分析スクリプト
db.sqlite3の詳細情報を取得し、レポートを生成します。

使用方法:
    python3 scripts/analyze_database.py
"""

import sqlite3
import os
import json
from datetime import datetime
from pathlib import Path


class DatabaseAnalyzer:
    # 許可されたテーブル名のホワイトリスト（SQLインジェクション対策）
    ALLOWED_TABLES = {'works', 'releases', 'notification_history', 'settings',
                      'rss_feeds', 'api_sources', 'calendar_events'}

    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
        self.report = {
            'analyzed_at': datetime.now().isoformat(),
            'database_path': str(db_path),
            'database_size_mb': 0,
            'tables': {},
            'indexes': [],
            'pragma_settings': {},
            'data_quality': {},
            'recommendations': []
        }

    def _validate_identifier(self, identifier: str) -> bool:
        """識別子（テーブル名/カラム名）の安全性を検証"""
        import re
        # 英数字とアンダースコアのみ許可
        return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', identifier))

    def _safe_identifier(self, identifier: str) -> str:
        """安全な識別子を返す（検証失敗時は例外）"""
        if not self._validate_identifier(identifier):
            raise ValueError(f"不正な識別子: {identifier}")
        return identifier

    def connect(self):
        """データベースに接続"""
        if not os.path.exists(self.db_path):
            logger.info(f"エラー: データベースファイルが見つかりません: {self.db_path}")
            return False

        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            return True
        except Exception as e:
            logger.info(f"接続エラー: {e}")
            return False

    def get_database_info(self):
        """データベース基本情報を取得"""
        # ファイルサイズ
        self.report['database_size_mb'] = round(
            os.path.getsize(self.db_path) / (1024 * 1024), 2
        )

        # PRAGMA設定
        pragma_queries = [
            'journal_mode',
            'synchronous',
            'cache_size',
            'temp_store',
            'foreign_keys',
            'auto_vacuum'
        ]

        for pragma in pragma_queries:
            cursor = self.conn.execute(f'PRAGMA {pragma}')
            value = cursor.fetchone()[0]
            self.report['pragma_settings'][pragma] = value

    def get_table_list(self):
        """全テーブル一覧を取得"""
        cursor = self.conn.execute("""
            SELECT name FROM sqlite_master
            WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        return [row['name'] for row in cursor.fetchall()]

    def get_table_schema(self, table_name):
        """テーブルスキーマを取得"""
        cursor = self.conn.execute(f"PRAGMA table_info({table_name})")
        columns = []
        for row in cursor.fetchall():
            columns.append({
                'cid': row['cid'],
                'name': row['name'],
                'type': row['type'],
                'notnull': bool(row['notnull']),
                'default_value': row['dflt_value'],
                'pk': bool(row['pk'])
            })

        # CREATE TABLE文を取得
        cursor = self.conn.execute("""
            SELECT sql FROM sqlite_master
            WHERE type = 'table' AND name = ?
        """, (table_name,))
        create_sql = cursor.fetchone()['sql']

        return {
            'columns': columns,
            'create_sql': create_sql
        }

    def get_table_statistics(self, table_name):
        """テーブル統計情報を取得"""
        # テーブル名を検証（SQLインジェクション対策）
        safe_table = self._safe_identifier(table_name)
        stats = {}

        # レコード数（識別子は検証済みなので安全）
        cursor = self.conn.execute(f"SELECT COUNT(*) FROM [{safe_table}]")
        stats['row_count'] = cursor.fetchone()[0]

        # 各カラムのNULL数とユニーク数
        schema = self.get_table_schema(table_name)
        column_stats = {}

        for col in schema['columns']:
            col_name = col['name']
            # カラム名も検証
            safe_col = self._safe_identifier(col_name)
            col_stats = {}

            # NULL数
            cursor = self.conn.execute(
                f"SELECT COUNT(*) FROM [{safe_table}] WHERE [{safe_col}] IS NULL"
            )
            col_stats['null_count'] = cursor.fetchone()[0]

            # ユニーク数
            try:
                cursor = self.conn.execute(
                    f"SELECT COUNT(DISTINCT [{safe_col}]) FROM [{safe_table}]"
                )
                col_stats['distinct_count'] = cursor.fetchone()[0]
            except Exception:
                col_stats['distinct_count'] = None

            column_stats[col_name] = col_stats

        stats['columns'] = column_stats
        return stats

    def get_indexes(self):
        """全インデックスを取得"""
        cursor = self.conn.execute("""
            SELECT name, tbl_name, sql
            FROM sqlite_master
            WHERE type = 'index' AND name NOT LIKE 'sqlite_%'
            ORDER BY tbl_name, name
        """)

        indexes = []
        for row in cursor.fetchall():
            indexes.append({
                'name': row['name'],
                'table': row['tbl_name'],
                'sql': row['sql']
            })

        return indexes

    def check_data_quality(self):
        """データ品質チェック"""
        quality_issues = []

        tables = self.get_table_list()

        # worksテーブルのチェック
        if 'works' in tables:
            # 必須カラムのNULLチェック
            cursor = self.conn.execute("SELECT COUNT(*) FROM works WHERE title IS NULL")
            null_titles = cursor.fetchone()[0]
            if null_titles > 0:
                quality_issues.append({
                    'severity': 'high',
                    'table': 'works',
                    'issue': f'{null_titles}件のレコードでtitleがNULL'
                })

            # 重複タイトルチェック
            cursor = self.conn.execute("""
                SELECT title, COUNT(*) as count
                FROM works
                GROUP BY title
                HAVING count > 1
            """)
            duplicates = cursor.fetchall()
            if duplicates:
                quality_issues.append({
                    'severity': 'medium',
                    'table': 'works',
                    'issue': f'{len(duplicates)}件の重複タイトル',
                    'examples': [{'title': row[0], 'count': row[1]} for row in duplicates[:5]]
                })

        # releasesテーブルのチェック
        if 'releases' in tables:
            # 孤立レコードチェック（work_idが存在しない）
            if 'works' in tables:
                cursor = self.conn.execute("""
                    SELECT COUNT(*) FROM releases r
                    LEFT JOIN works w ON r.work_id = w.id
                    WHERE w.id IS NULL
                """)
                orphaned = cursor.fetchone()[0]
                if orphaned > 0:
                    quality_issues.append({
                        'severity': 'critical',
                        'table': 'releases',
                        'issue': f'{orphaned}件の孤立レコード（対応するworksが存在しない）'
                    })

            # 未通知レコードの確認
            cursor = self.conn.execute("""
                SELECT COUNT(*) FROM releases
                WHERE notified = 0 AND release_date <= DATE('now')
            """)
            pending_notifications = cursor.fetchone()[0]
            if pending_notifications > 0:
                quality_issues.append({
                    'severity': 'info',
                    'table': 'releases',
                    'issue': f'{pending_notifications}件の未通知レコード（配信日を過ぎている）'
                })

        return quality_issues

    def get_recommendations(self):
        """最適化推奨事項を生成"""
        recommendations = []

        # インデックスチェック
        indexes = self.get_indexes()
        index_names = [idx['name'] for idx in indexes]

        required_indexes = {
            'idx_works_title': 'works',
            'idx_works_type': 'works',
            'idx_releases_work_id': 'releases',
            'idx_releases_date': 'releases',
            'idx_releases_notified': 'releases'
        }

        for idx_name, table in required_indexes.items():
            if idx_name not in index_names:
                recommendations.append({
                    'priority': 'high',
                    'category': 'index',
                    'suggestion': f'{table}テーブルに{idx_name}インデックスを作成してください',
                    'sql': self._get_index_sql(idx_name)
                })

        # PRAGMA設定チェック
        if self.report['pragma_settings'].get('journal_mode') != 'wal':
            recommendations.append({
                'priority': 'high',
                'category': 'configuration',
                'suggestion': 'WALモードを有効化してパフォーマンスを向上させてください',
                'sql': 'PRAGMA journal_mode = WAL;'
            })

        if self.report['pragma_settings'].get('foreign_keys') != 1:
            recommendations.append({
                'priority': 'high',
                'category': 'configuration',
                'suggestion': '外部キー制約を有効化してデータ整合性を保証してください',
                'sql': 'PRAGMA foreign_keys = ON;'
            })

        # データベースサイズチェック
        if self.report['database_size_mb'] > 100:
            recommendations.append({
                'priority': 'medium',
                'category': 'maintenance',
                'suggestion': 'データベースサイズが100MBを超えています。VACUUMを実行してください',
                'sql': 'VACUUM;'
            })

        return recommendations

    def _get_index_sql(self, index_name):
        """推奨インデックスのSQL文を返す"""
        index_sqls = {
            'idx_works_title': 'CREATE INDEX idx_works_title ON works(title);',
            'idx_works_type': 'CREATE INDEX idx_works_type ON works(type);',
            'idx_releases_work_id': 'CREATE INDEX idx_releases_work_id ON releases(work_id);',
            'idx_releases_date': 'CREATE INDEX idx_releases_date ON releases(release_date);',
            'idx_releases_notified': 'CREATE INDEX idx_releases_notified ON releases(notified, release_date);'
        }
        return index_sqls.get(index_name, '')

    def analyze(self):
        """完全分析を実行"""
        if not self.connect():
            return None

        logger.info("データベース分析を開始します...")
        logger.info(f"対象: {self.db_path}")
        logger.info()

        # 基本情報
        logger.info("1. データベース基本情報を取得中...")
        self.get_database_info()

        # テーブル情報
        logger.info("2. テーブル情報を取得中...")
        tables = self.get_table_list()
        for table in tables:
            logger.info(f"   - {table}")
            schema = self.get_table_schema(table)
            stats = self.get_table_statistics(table)
            self.report['tables'][table] = {
                'schema': schema,
                'statistics': stats
            }

        # インデックス情報
        logger.info("3. インデックス情報を取得中...")
        self.report['indexes'] = self.get_indexes()

        # データ品質チェック
        logger.info("4. データ品質チェック中...")
        self.report['data_quality']['issues'] = self.check_data_quality()

        # 推奨事項
        logger.info("5. 最適化推奨事項を生成中...")
        self.report['recommendations'] = self.get_recommendations()

        logger.info()
        logger.info("分析完了!")
        return self.report

    def save_report(self, output_path):
        """レポートをJSONファイルに保存"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.report, f, ensure_ascii=False, indent=2)
        logger.info(f"レポートを保存しました: {output_path}")

    def print_summary(self):
        """サマリーをコンソールに出力"""
import logging

logger = logging.getLogger(__name__)

        logger.info("\n" + "=" * 80)

logger = logging.getLogger(__name__)

        logger.info("データベース分析サマリー")
        logger.info("=" * 80)

        logger.info(f"\nデータベース: {self.report['database_path']}")
        logger.info(f"サイズ: {self.report['database_size_mb']} MB")
        logger.info(f"分析日時: {self.report['analyzed_at']}")

        logger.info("\n--- テーブル一覧 ---")
        for table_name, table_data in self.report['tables'].items():
            stats = table_data['statistics']
            logger.info(f"{table_name}: {stats['row_count']:,} レコード")

        logger.info("\n--- インデックス一覧 ---")
        if self.report['indexes']:
            for idx in self.report['indexes']:
                logger.info(f"  {idx['name']} on {idx['table']}")
        else:
            logger.info("  インデックスが見つかりません（要作成！）")

        logger.info("\n--- データ品質チェック結果 ---")
        issues = self.report['data_quality']['issues']
        if issues:
            for issue in issues:
                severity_icon = {
                    'critical': '🔴',
                    'high': '🟠',
                    'medium': '🟡',
                    'info': '🔵'
                }.get(issue['severity'], '⚪')
                logger.info(f"  {severity_icon} [{issue['severity'].upper()}] {issue['issue']}")
        else:
            logger.info("  問題は検出されませんでした")

        logger.info("\n--- 最適化推奨事項 ---")
        if self.report['recommendations']:
            for rec in self.report['recommendations']:
                priority_icon = {
                    'high': '🔴',
                    'medium': '🟡',
                    'low': '🟢'
                }.get(rec['priority'], '⚪')
                logger.info(f"  {priority_icon} [{rec['priority'].upper()}] {rec['suggestion']}")
        else:
            logger.info("  推奨事項はありません")

        logger.info("\n" + "=" * 80)

    def close(self):
        """データベース接続を閉じる"""
        if self.conn:
            self.conn.close()


def main():
    # プロジェクトルートからの相対パス
    project_root = Path(__file__).parent.parent
    db_path = project_root / 'db.sqlite3'

    analyzer = DatabaseAnalyzer(db_path)
    report = analyzer.analyze()

    if report:
        # レポートを保存
        report_path = project_root / 'docs' / 'technical' / 'database-analysis-report.json'
        analyzer.save_report(report_path)

        # サマリーを表示
        analyzer.print_summary()

        # 詳細レポートへのパス表示
        logger.info(f"\n詳細レポート: {report_path}")
        logger.info(f"最適化ガイド: {project_root / 'docs' / 'technical' / 'database-optimization-report.md'}")

    analyzer.close()


if __name__ == '__main__':
    main()
