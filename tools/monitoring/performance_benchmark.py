#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
データベース最適化効果測定ベンチマークテスト
MangaAnime-Info-delivery-system

実行方法:
python3 performance_benchmark.py --before  # 最適化前のテスト
python3 performance_benchmark.py --after   # 最適化後のテスト
python3 performance_benchmark.py --compare # 結果比較
"""

import sqlite3
import time
import json
import argparse
import statistics
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

class DatabaseBenchmark:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.results = {}
        
    def run_query_benchmark(self, query_name: str, sql: str, iterations: int = 10) -> Dict[str, Any]:
        """指定されたクエリのベンチマークを実行"""
        execution_times = []
        
        for i in range(iterations):
            start_time = time.perf_counter()
            
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute(sql)
                    results = cursor.fetchall()
                    result_count = len(results)
                    
                end_time = time.perf_counter()
                execution_times.append(end_time - start_time)
                
            except Exception as e:
                print(f"Error executing {query_name}: {e}")
                return None
        
        return {
            'query_name': query_name,
            'iterations': iterations,
            'result_count': result_count,
            'avg_time': statistics.mean(execution_times),
            'min_time': min(execution_times),
            'max_time': max(execution_times),
            'median_time': statistics.median(execution_times),
            'std_dev': statistics.stdev(execution_times) if len(execution_times) > 1 else 0,
            'total_time': sum(execution_times),
            'execution_times': execution_times
        }
    
    def get_database_stats(self) -> Dict[str, Any]:
        """データベースの統計情報を取得"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                stats = {}
                
                # テーブルサイズ
                cursor = conn.execute("SELECT COUNT(*) FROM works")
                stats['works_count'] = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM releases")
                stats['releases_count'] = cursor.fetchone()[0]
                
                # インデックス情報
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='index' AND sql IS NOT NULL")
                stats['indexes'] = [row[0] for row in cursor.fetchall()]
                
                # ファイルサイズ
                file_size = Path(self.db_path).stat().st_size
                stats['file_size_mb'] = round(file_size / (1024 * 1024), 2)
                
                # ページ数
                cursor = conn.execute("PRAGMA page_count")
                stats['page_count'] = cursor.fetchone()[0]
                
                cursor = conn.execute("PRAGMA page_size")
                stats['page_size'] = cursor.fetchone()[0]
                
                return stats
                
        except Exception as e:
            print(f"Error getting database stats: {e}")
            return {}
    
    def run_comprehensive_benchmark(self) -> Dict[str, Any]:
        """包括的なベンチマークテストを実行"""
        print("Starting comprehensive database benchmark...")
        
        benchmark_queries = {
            # 1. 最重要クエリ：今日の通知対象アニメ
            "today_anime_notifications": """
                SELECT w.title, r.platform, r.release_type, r.number 
                FROM works w 
                JOIN releases r ON w.id = r.work_id 
                WHERE w.type = 'anime' 
                  AND r.notified = 0 
                  AND r.release_date = date('now')
                ORDER BY r.platform, w.title
            """,
            
            # 2. プラットフォーム別今週のリリース
            "weekly_platform_releases": """
                SELECT w.title, r.release_date, r.release_type, r.number
                FROM works w
                JOIN releases r ON w.id = r.work_id
                WHERE r.platform = 'Netflix'
                  AND r.release_date BETWEEN date('now') AND date('now', '+7 days')
                ORDER BY r.release_date, w.title
            """,
            
            # 3. 作品別統計集計
            "work_stats_aggregation": """
                SELECT w.type, r.platform, COUNT(*) as release_count,
                       COUNT(CASE WHEN r.notified = 0 THEN 1 END) as pending_count
                FROM works w 
                JOIN releases r ON w.id = r.work_id 
                GROUP BY w.type, r.platform 
                ORDER BY release_count DESC
            """,
            
            # 4. 複雑な検索クエリ
            "complex_search": """
                SELECT w.title, w.type, r.platform, r.release_date,
                       COUNT(r.id) as total_releases
                FROM works w
                LEFT JOIN releases r ON w.id = r.work_id
                WHERE w.title LIKE '%攻撃%' OR w.title LIKE '%魔法%'
                GROUP BY w.id, w.title, w.type, r.platform, r.release_date
                HAVING COUNT(r.id) > 1
                ORDER BY total_releases DESC, r.release_date DESC
            """,
            
            # 5. 日付範囲検索
            "date_range_search": """
                SELECT w.title, r.release_date, r.platform
                FROM works w
                JOIN releases r ON w.id = r.work_id
                WHERE r.release_date BETWEEN date('now', '-30 days') AND date('now', '+30 days')
                  AND w.type = 'anime'
                ORDER BY r.release_date DESC
            """,
            
            # 6. 未通知レコード検索
            "unnotified_search": """
                SELECT w.title, r.release_type, r.number, r.release_date, r.platform
                FROM works w
                JOIN releases r ON w.id = r.work_id
                WHERE r.notified = 0
                  AND r.release_date <= date('now')
                ORDER BY r.release_date, w.title
            """,
            
            # 7. 重複チェッククエリ
            "duplicate_check": """
                SELECT work_id, release_type, number, platform, release_date, COUNT(*) as dup_count
                FROM releases
                GROUP BY work_id, release_type, number, platform, release_date
                HAVING COUNT(*) > 1
            """,
            
            # 8. 月別統計
            "monthly_statistics": """
                SELECT strftime('%Y-%m', r.release_date) as month,
                       w.type,
                       COUNT(*) as releases,
                       COUNT(DISTINCT w.id) as unique_works
                FROM works w
                JOIN releases r ON w.id = r.work_id
                WHERE r.release_date >= date('now', '-6 months')
                GROUP BY month, w.type
                ORDER BY month DESC
            """
        }
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'database_stats': self.get_database_stats(),
            'query_benchmarks': {}
        }
        
        total_start = time.perf_counter()
        
        for query_name, sql in benchmark_queries.items():
            print(f"Benchmarking: {query_name}")
            result = self.run_query_benchmark(query_name, sql, iterations=5)
            if result:
                results['query_benchmarks'][query_name] = result
        
        total_end = time.perf_counter()
        results['total_benchmark_time'] = total_end - total_start
        
        return results
    
    def save_results(self, results: Dict[str, Any], filename: str):
        """結果をJSONファイルに保存"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"Results saved to: {filename}")
    
    def load_results(self, filename: str) -> Dict[str, Any]:
        """JSONファイルから結果を読み込み"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"File not found: {filename}")
            return None

class BenchmarkComparator:
    def __init__(self, before_results: Dict[str, Any], after_results: Dict[str, Any]):
        self.before = before_results
        self.after = after_results
    
    def generate_comparison_report(self) -> str:
        """最適化前後の比較レポートを生成"""
        report = []
        report.append("=" * 80)
        report.append("データベース最適化効果レポート")
        report.append("=" * 80)
        report.append("")
        
        # データベース統計比較
        report.append("## データベース統計比較")
        report.append("")
        before_stats = self.before.get('database_stats', {})
        after_stats = self.after.get('database_stats', {})
        
        for key in ['works_count', 'releases_count', 'file_size_mb', 'page_count']:
            before_val = before_stats.get(key, 0)
            after_val = after_stats.get(key, 0)
            report.append(f"- {key}: {before_val} → {after_val}")
        
        report.append(f"- インデックス数: {len(before_stats.get('indexes', []))} → {len(after_stats.get('indexes', []))}")
        report.append("")
        
        # クエリパフォーマンス比較
        report.append("## クエリパフォーマンス比較")
        report.append("")
        report.append("| クエリ名 | 最適化前(ms) | 最適化後(ms) | 改善率(%) | 結果件数 |")
        report.append("|----------|-------------|-------------|-----------|----------|")
        
        before_queries = self.before.get('query_benchmarks', {})
        after_queries = self.after.get('query_benchmarks', {})
        
        total_before = 0
        total_after = 0
        improvements = []
        
        for query_name in before_queries.keys():
            if query_name in after_queries:
                before_time = before_queries[query_name]['avg_time'] * 1000
                after_time = after_queries[query_name]['avg_time'] * 1000
                improvement = ((before_time - after_time) / before_time) * 100
                result_count = after_queries[query_name]['result_count']
                
                improvements.append(improvement)
                total_before += before_time
                total_after += after_time
                
                report.append(f"| {query_name} | {before_time:.2f} | {after_time:.2f} | {improvement:+.1f}% | {result_count} |")
        
        report.append("")
        
        # 総合パフォーマンス
        overall_improvement = ((total_before - total_after) / total_before) * 100 if total_before > 0 else 0
        avg_improvement = statistics.mean(improvements) if improvements else 0
        
        report.append("## 総合パフォーマンス改善")
        report.append("")
        report.append(f"- 総実行時間: {total_before:.2f}ms → {total_after:.2f}ms")
        report.append(f"- 総合改善率: {overall_improvement:+.1f}%")
        report.append(f"- 平均改善率: {avg_improvement:+.1f}%")
        report.append(f"- 最大改善率: {max(improvements):+.1f}%" if improvements else "- 最大改善率: N/A")
        report.append(f"- 最小改善率: {min(improvements):+.1f}%" if improvements else "- 最小改善率: N/A")
        report.append("")
        
        # 推奨事項
        report.append("## 推奨事項")
        report.append("")
        if avg_improvement > 10:
            report.append("✅ 大幅な性能向上が確認されました。最適化は成功しています。")
        elif avg_improvement > 5:
            report.append("✅ 適度な性能向上が確認されました。")
        elif avg_improvement > 0:
            report.append("⚠️ 軽微な性能向上が確認されました。追加の最適化を検討してください。")
        else:
            report.append("❌ 性能向上が確認されませんでした。最適化戦略の見直しが必要です。")
        
        report.append("")
        
        # 詳細分析
        report.append("## 詳細分析")
        report.append("")
        
        for query_name in before_queries.keys():
            if query_name in after_queries:
                before_q = before_queries[query_name]
                after_q = after_queries[query_name]
                
                report.append(f"### {query_name}")
                report.append(f"- 平均実行時間: {before_q['avg_time']*1000:.2f}ms → {after_q['avg_time']*1000:.2f}ms")
                report.append(f"- 最短実行時間: {before_q['min_time']*1000:.2f}ms → {after_q['min_time']*1000:.2f}ms")
                report.append(f"- 最長実行時間: {before_q['max_time']*1000:.2f}ms → {after_q['max_time']*1000:.2f}ms")
                report.append(f"- 標準偏差: {before_q['std_dev']*1000:.2f}ms → {after_q['std_dev']*1000:.2f}ms")
                report.append("")
        
        return "\n".join(report)

def main():
    parser = argparse.ArgumentParser(description='Database Performance Benchmark')
    parser.add_argument('--before', action='store_true', help='Run benchmark before optimization')
    parser.add_argument('--after', action='store_true', help='Run benchmark after optimization')
    parser.add_argument('--compare', action='store_true', help='Compare before and after results')
    parser.add_argument('--db-path', default='db.sqlite3', help='Path to database file')
    
    args = parser.parse_args()
    
    if args.before:
        benchmark = DatabaseBenchmark(args.db_path)
        results = benchmark.run_comprehensive_benchmark()
        benchmark.save_results(results, 'benchmark_before.json')
        
    elif args.after:
        benchmark = DatabaseBenchmark(args.db_path)
        results = benchmark.run_comprehensive_benchmark()
        benchmark.save_results(results, 'benchmark_after.json')
        
    elif args.compare:
        benchmark = DatabaseBenchmark(args.db_path)
        before_results = benchmark.load_results('benchmark_before.json')
        after_results = benchmark.load_results('benchmark_after.json')
        
        if before_results and after_results:
            comparator = BenchmarkComparator(before_results, after_results)
            report = comparator.generate_comparison_report()
            print(report)
            
            # レポートをファイルに保存
            with open('optimization_report.txt', 'w', encoding='utf-8') as f:
                f.write(report)
            print("\nレポートが optimization_report.txt に保存されました。")
        else:
            print("比較に必要なファイルが見つかりません。")
    
    else:
        print("使用方法: python3 performance_benchmark.py [--before|--after|--compare]")

if __name__ == "__main__":
    main()