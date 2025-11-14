#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
継続的監視・自動修復システム
定期的にシステムを監視し、問題を自動的に検出・修復する
"""

import os
import sys
import json
import time
import signal
import sqlite3
import hashlib
import threading
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    handlers=[
        logging.FileHandler('logs/continuous_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ContinuousMonitor:
    """継続的監視システム"""
    
    def __init__(self):
        self.running = True
        self.base_dir = Path('.')
        self.check_interval = 30  # 30秒ごとにチェック
        self.metrics = {
            'checks_performed': 0,
            'errors_found': 0,
            'errors_fixed': 0,
            'uptime': 0,
            'last_check': None
        }
        self.error_history = []
        self.repair_strategies = self.load_repair_strategies()
        
    def load_repair_strategies(self) -> Dict:
        """修復戦略をロード"""
        return {
            'file_missing': self.repair_missing_file,
            'permission_error': self.repair_permissions,
            'config_invalid': self.repair_config,
            'database_error': self.repair_database,
            'dependency_missing': self.repair_dependencies,
            'service_down': self.repair_service,
            'memory_high': self.optimize_memory,
            'disk_full': self.cleanup_disk
        }
        
    def perform_health_check(self) -> Dict:
        """システムヘルスチェック実行"""
        health = {
            'timestamp': datetime.now().isoformat(),
            'status': 'healthy',
            'issues': [],
            'metrics': {}
        }
        
        # 1. プロセス監視
        try:
            # Web UIプロセスチェック
            result = subprocess.run(
                ['pgrep', '-f', 'web_app.py'],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                health['issues'].append({
                    'type': 'service_down',
                    'service': 'web_app',
                    'severity': 'warning'
                })
                
        except Exception as e:
            logger.warning(f"プロセスチェックエラー: {e}")
            
        # 2. メモリ使用率チェック
        try:
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
                mem_total = int([x for x in meminfo.split('\n') if 'MemTotal' in x][0].split()[1])
                mem_available = int([x for x in meminfo.split('\n') if 'MemAvailable' in x][0].split()[1])
                mem_usage = ((mem_total - mem_available) / mem_total) * 100
                
                health['metrics']['memory_usage'] = f"{mem_usage:.1f}%"
                
                if mem_usage > 90:
                    health['issues'].append({
                        'type': 'memory_high',
                        'usage': mem_usage,
                        'severity': 'critical'
                    })
                elif mem_usage > 80:
                    health['issues'].append({
                        'type': 'memory_high',
                        'usage': mem_usage,
                        'severity': 'warning'
                    })
                    
        except Exception as e:
            logger.warning(f"メモリチェックエラー: {e}")
            
        # 3. ディスク使用率チェック
        try:
            result = subprocess.run(
                ['df', '-h', '.'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    disk_info = lines[1].split()
                    if len(disk_info) >= 5:
                        usage_str = disk_info[4].replace('%', '')
                        disk_usage = int(usage_str)
                        health['metrics']['disk_usage'] = f"{disk_usage}%"
                        
                        if disk_usage > 95:
                            health['issues'].append({
                                'type': 'disk_full',
                                'usage': disk_usage,
                                'severity': 'critical'
                            })
                            
        except Exception as e:
            logger.warning(f"ディスクチェックエラー: {e}")
            
        # 4. データベース整合性チェック
        if Path('db.sqlite3').exists():
            try:
                conn = sqlite3.connect('db.sqlite3')
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check")
                result = cursor.fetchone()
                
                if result[0] != 'ok':
                    health['issues'].append({
                        'type': 'database_error',
                        'error': result[0],
                        'severity': 'critical'
                    })
                    
                # テーブル数確認
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                table_count = cursor.fetchone()[0]
                health['metrics']['database_tables'] = table_count
                
                conn.close()
                
            except Exception as e:
                health['issues'].append({
                    'type': 'database_error',
                    'error': str(e),
                    'severity': 'critical'
                })
                
        # 5. ログファイルチェック
        log_dir = Path('logs')
        if log_dir.exists():
            log_files = list(log_dir.glob('*.log'))
            total_size = sum(f.stat().st_size for f in log_files)
            health['metrics']['log_size_mb'] = f"{total_size / 1024 / 1024:.1f}"
            
            # 大きすぎるログファイル
            if total_size > 100 * 1024 * 1024:  # 100MB
                health['issues'].append({
                    'type': 'disk_full',
                    'component': 'logs',
                    'size': total_size,
                    'severity': 'warning'
                })
                
        # 6. 設定ファイルの妥当性
        config_files = ['config.json', 'gmail_config.json']
        for config_file in config_files:
            if Path(config_file).exists():
                try:
                    with open(config_file, 'r') as f:
                        json.load(f)
                except json.JSONDecodeError as e:
                    health['issues'].append({
                        'type': 'config_invalid',
                        'file': config_file,
                        'error': str(e),
                        'severity': 'critical'
                    })
                    
        # ステータス判定
        if any(issue['severity'] == 'critical' for issue in health['issues']):
            health['status'] = 'critical'
        elif any(issue['severity'] == 'warning' for issue in health['issues']):
            health['status'] = 'warning'
            
        return health
    
    def auto_repair_issue(self, issue: Dict) -> bool:
        """検出された問題を自動修復"""
        issue_type = issue.get('type')
        
        if issue_type in self.repair_strategies:
            logger.info(f"🔧 自動修復実行: {issue_type}")
            try:
                return self.repair_strategies[issue_type](issue)
            except Exception as e:
                logger.error(f"修復エラー: {e}")
                return False
        else:
            logger.warning(f"未知の問題タイプ: {issue_type}")
            return False
            
    def repair_missing_file(self, issue: Dict) -> bool:
        """不足ファイルを修復"""
        filename = issue.get('file')
        if filename == 'requirements.txt':
            # 基本的な依存関係を作成
            content = """flask==2.3.0
google-auth==2.40.3
google-auth-oauthlib==1.2.2
google-auth-httplib2==0.2.0
google-api-python-client==2.179.0
feedparser==6.0.11
schedule==1.2.2
requests==2.31.0
flask-cors==6.0.1"""
            with open('requirements.txt', 'w') as f:
                f.write(content)
            logger.info(f"✅ {filename} を作成")
            return True
        return False
        
    def repair_permissions(self, issue: Dict) -> bool:
        """パーミッションを修復"""
        filename = issue.get('file')
        if filename and Path(filename).exists():
            os.chmod(filename, 0o600)
            logger.info(f"✅ {filename} のパーミッションを修正")
            return True
        return False
        
    def repair_config(self, issue: Dict) -> bool:
        """設定ファイルを修復"""
        filename = issue.get('file')
        if filename == 'config.json':
            # バックアップから復元を試みる
            backup_file = Path(f"{filename}.backup")
            if backup_file.exists():
                subprocess.run(['cp', str(backup_file), filename])
                logger.info(f"✅ {filename} をバックアップから復元")
                return True
        return False
        
    def repair_database(self, issue: Dict) -> bool:
        """データベースを修復"""
        try:
            conn = sqlite3.connect('db.sqlite3')
            cursor = conn.cursor()
            cursor.execute("VACUUM")
            cursor.execute("REINDEX")
            conn.commit()
            conn.close()
            logger.info("✅ データベースを最適化")
            return True
        except Exception as e:
            logger.error(f"データベース修復エラー: {e}")
            return False
            
    def repair_dependencies(self, issue: Dict) -> bool:
        """依存関係を修復"""
        try:
            subprocess.run(['pip3', 'install', '-r', 'requirements.txt'], check=True)
            logger.info("✅ 依存関係をインストール")
            return True
        except Exception as e:
            logger.error(f"依存関係インストールエラー: {e}")
            return False
            
    def repair_service(self, issue: Dict) -> bool:
        """サービスを再起動"""
        service = issue.get('service')
        if service == 'web_app':
            try:
                # バックグラウンドでWeb UIを起動
                subprocess.Popen(
                    ['python3', 'web_app.py'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
                logger.info("✅ Web UIサービスを起動")
                return True
            except Exception as e:
                logger.error(f"サービス起動エラー: {e}")
                return False
        return False
        
    def optimize_memory(self, issue: Dict) -> bool:
        """メモリを最適化"""
        try:
            # Pythonのガベージコレクション実行
            import gc
            gc.collect()
            
            # システムキャッシュをクリア（権限が必要）
            subprocess.run(['sync'], check=True)
            
            logger.info("✅ メモリを最適化")
            return True
        except Exception as e:
            logger.warning(f"メモリ最適化警告: {e}")
            return False
            
    def cleanup_disk(self, issue: Dict) -> bool:
        """ディスクをクリーンアップ"""
        try:
            # 古いログファイルを削除
            log_dir = Path('logs')
            if log_dir.exists():
                cutoff_date = datetime.now() - timedelta(days=7)
                for log_file in log_dir.glob('*.log'):
                    if log_file.stat().st_mtime < cutoff_date.timestamp():
                        log_file.unlink()
                        logger.info(f"✅ 古いログファイルを削除: {log_file.name}")
                        
            # 一時ファイルを削除
            for tmp_file in Path('.').glob('*.tmp'):
                tmp_file.unlink()
                
            return True
        except Exception as e:
            logger.error(f"ディスククリーンアップエラー: {e}")
            return False
            
    def monitoring_loop(self):
        """監視ループ"""
        logger.info("🔄 継続的監視を開始...")
        
        while self.running:
            try:
                # ヘルスチェック実行
                health = self.perform_health_check()
                self.metrics['checks_performed'] += 1
                self.metrics['last_check'] = datetime.now().isoformat()
                
                # 結果表示
                status_icon = {
                    'healthy': '✅',
                    'warning': '⚠️',
                    'critical': '❌'
                }.get(health['status'], '❓')
                
                logger.info(f"{status_icon} 状態: {health['status'].upper()}")
                
                if health['metrics']:
                    logger.info(f"📊 メトリクス: {health['metrics']}")
                    
                # 問題があれば修復
                if health['issues']:
                    logger.info(f"🔍 {len(health['issues'])}件の問題を検出")
                    
                    for issue in health['issues']:
                        self.metrics['errors_found'] += 1
                        self.error_history.append({
                            'timestamp': datetime.now().isoformat(),
                            'issue': issue
                        })
                        
                        # 自動修復試行
                        if self.auto_repair_issue(issue):
                            self.metrics['errors_fixed'] += 1
                            logger.info(f"✅ 修復成功: {issue['type']}")
                        else:
                            logger.warning(f"⚠️ 修復失敗: {issue['type']}")
                            
                # 統計表示（5分ごと）
                if self.metrics['checks_performed'] % 10 == 0:
                    self.show_statistics()
                    
                # 次回チェックまで待機
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"監視エラー: {e}")
                time.sleep(self.check_interval)
                
    def show_statistics(self):
        """統計情報を表示"""
        logger.info("=" * 60)
        logger.info("📊 監視統計")
        logger.info(f"チェック回数: {self.metrics['checks_performed']}")
        logger.info(f"検出エラー数: {self.metrics['errors_found']}")
        logger.info(f"修復成功数: {self.metrics['errors_fixed']}")
        logger.info(f"修復成功率: {self.metrics['errors_fixed'] / max(1, self.metrics['errors_found']) * 100:.1f}%")
        logger.info("=" * 60)
        
    def signal_handler(self, signum, frame):
        """シグナルハンドラー"""
        logger.info("\n⚠️ 監視を停止中...")
        self.running = False
        
    def run(self):
        """監視システムを実行"""
        # シグナルハンドラー設定
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        logger.info("=" * 60)
        logger.info("🚀 継続的監視システムを起動")
        logger.info(f"チェック間隔: {self.check_interval}秒")
        logger.info("停止するには Ctrl+C を押してください")
        logger.info("=" * 60)
        
        # 監視ループ開始
        self.monitoring_loop()
        
        # 終了処理
        logger.info("\n📊 最終統計:")
        self.show_statistics()
        logger.info("✅ 監視システムを終了")

def main():
    """メイン処理"""
    monitor = ContinuousMonitor()
    monitor.run()

if __name__ == "__main__":
    main()