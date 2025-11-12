#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
自動検証・修復ループシステム
システム全体を自動的に検証し、エラーを検出して修復を行う
"""

import os
import sys
import json
import time
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/auto_repair.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutoRepairSystem:
    """自動検証・修復システム"""
    
    def __init__(self):
        self.base_dir = Path('.')
        self.max_iterations = 10
        self.iteration = 0
        self.errors_found = []
        self.repairs_done = []
        self.start_time = datetime.now()
        
    def run_validation_tests(self) -> Dict[str, any]:
        """システム全体の検証テストを実行"""
        logger.info("🔍 システム検証を開始...")
        results = {
            'timestamp': datetime.now().isoformat(),
            'checks': {},
            'errors': [],
            'warnings': []
        }
        
        # 1. ファイル存在チェック
        logger.info("📁 必須ファイルの存在確認...")
        required_files = [
            'config.json',
            'credentials.json',
            'gmail_config.json',
            'requirements.txt',
            'web_app.py'
        ]
        
        for file in required_files:
            if not Path(file).exists():
                results['errors'].append(f"Missing required file: {file}")
                logger.error(f"❌ {file} が見つかりません")
            else:
                results['checks'][file] = 'OK'
                
        # 2. Python構文チェック
        logger.info("🐍 Python構文チェック...")
        python_files = list(Path('.').glob('**/*.py'))
        for py_file in python_files[:20]:  # 最初の20ファイルをチェック
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    compile(f.read(), py_file, 'exec')
                results['checks'][str(py_file)] = 'Valid syntax'
            except SyntaxError as e:
                results['errors'].append(f"Syntax error in {py_file}: {e}")
                logger.error(f"❌ 構文エラー: {py_file}")
                
        # 3. パーミッションチェック
        logger.info("🔒 認証ファイルのパーミッション確認...")
        secure_files = ['credentials.json', 'gmail_config.json', 'token.json']
        for file in secure_files:
            if Path(file).exists():
                perms = oct(os.stat(file).st_mode)[-3:]
                if perms != '600':
                    results['warnings'].append(f"{file} has insecure permissions: {perms}")
                    logger.warning(f"⚠️ {file} のパーミッションが不適切: {perms}")
                    
        # 4. 設定ファイル検証
        logger.info("⚙️ 設定ファイルの妥当性確認...")
        if Path('config.json').exists():
            try:
                with open('config.json', 'r') as f:
                    config = json.load(f)
                    
                # 必須キーの確認
                required_keys = ['system', 'database', 'notification', 'sources']
                for key in required_keys:
                    if key not in config:
                        results['errors'].append(f"Missing config key: {key}")
                        
                # ポート番号確認
                if Path('web_app.py').exists():
                    with open('web_app.py', 'r') as f:
                        content = f.read()
                        if 'port=3033' not in content:
                            results['warnings'].append("Web app port might not be 3033")
                            
            except json.JSONDecodeError as e:
                results['errors'].append(f"Invalid JSON in config.json: {e}")
                
        # 5. 依存関係チェック
        logger.info("📦 Python依存関係の確認...")
        try:
            result = subprocess.run(
                ['python3', '-c', 'import flask, google.auth, feedparser, schedule'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                results['errors'].append("Missing Python dependencies")
                logger.error("❌ 必要なPythonパッケージが不足")
        except Exception as e:
            results['warnings'].append(f"Could not check dependencies: {e}")
            
        # 6. データベース接続チェック
        logger.info("🗄️ データベース接続確認...")
        if Path('db.sqlite3').exists():
            try:
                import sqlite3
                conn = sqlite3.connect('db.sqlite3')
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                table_count = cursor.fetchone()[0]
                conn.close()
                results['checks']['database'] = f"{table_count} tables found"
            except Exception as e:
                results['errors'].append(f"Database error: {e}")
                
        return results
    
    def auto_repair(self, errors: List[str]) -> List[str]:
        """検出されたエラーを自動修復"""
        logger.info("🔧 エラーの自動修復を開始...")
        repairs = []
        
        for error in errors:
            logger.info(f"修復中: {error}")
            
            # ファイル不足の修復
            if "Missing required file" in error:
                filename = error.split(": ")[1]
                
                if filename == "credentials.json":
                    # テンプレートから作成
                    template = {
                        "installed": {
                            "client_id": "YOUR_CLIENT_ID",
                            "project_id": "YOUR_PROJECT_ID",
                            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                            "token_uri": "https://oauth2.googleapis.com/token",
                            "client_secret": "YOUR_CLIENT_SECRET"
                        }
                    }
                    with open(filename, 'w') as f:
                        json.dump(template, f, indent=2)
                    os.chmod(filename, 0o600)
                    repairs.append(f"Created template {filename}")
                    logger.info(f"✅ {filename} テンプレートを作成")
                    
                elif filename == "gmail_config.json":
                    if Path("gmail_config.json.template").exists():
                        subprocess.run(['cp', 'gmail_config.json.template', 'gmail_config.json'])
                        os.chmod('gmail_config.json', 0o600)
                        repairs.append("Copied gmail_config.json from template")
                        logger.info("✅ gmail_config.json をテンプレートから作成")
                        
            # パーミッション修復
            elif "insecure permissions" in error:
                filename = error.split(" has")[0]
                if Path(filename).exists():
                    os.chmod(filename, 0o600)
                    repairs.append(f"Fixed permissions for {filename}")
                    logger.info(f"✅ {filename} のパーミッションを修正")
                    
            # 構文エラーの報告（自動修復は困難）
            elif "Syntax error" in error:
                repairs.append(f"Syntax error detected - manual fix required: {error}")
                logger.warning(f"⚠️ 構文エラーは手動修正が必要: {error}")
                
            # 依存関係の修復
            elif "Missing Python dependencies" in error:
                logger.info("📦 依存関係をインストール中...")
                subprocess.run(['pip3', 'install', '-r', 'requirements.txt'])
                repairs.append("Installed Python dependencies")
                
        return repairs
    
    def run_loop(self):
        """自動検証・修復ループを実行"""
        logger.info("=" * 60)
        logger.info("🔄 自動検証・修復ループを開始")
        logger.info("=" * 60)
        
        while self.iteration < self.max_iterations:
            self.iteration += 1
            logger.info(f"\n🔁 イテレーション {self.iteration}/{self.max_iterations}")
            
            # 検証実行
            validation_results = self.run_validation_tests()
            
            # エラー集計
            total_errors = len(validation_results['errors'])
            total_warnings = len(validation_results['warnings'])
            
            logger.info(f"📊 検証結果: エラー {total_errors}件, 警告 {total_warnings}件")
            
            if total_errors == 0:
                logger.info("✅ エラーなし！システムは正常です")
                
                # 警告のみの場合
                if total_warnings > 0:
                    logger.info(f"⚠️ {total_warnings}件の警告があります:")
                    for warning in validation_results['warnings']:
                        logger.warning(f"  - {warning}")
                        
                # 成功レポート作成
                self.create_report(validation_results, 'SUCCESS')
                break
                
            else:
                logger.info(f"❌ {total_errors}件のエラーを検出")
                
                # エラー修復
                repairs = self.auto_repair(validation_results['errors'])
                self.repairs_done.extend(repairs)
                
                logger.info(f"🔧 {len(repairs)}件の修復を実行")
                
                # 少し待機
                time.sleep(2)
                
        # 最終レポート
        self.create_final_report()
        
    def create_report(self, results: Dict, status: str):
        """検証レポートを作成"""
        report_file = f"logs/validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = {
            'status': status,
            'iteration': self.iteration,
            'timestamp': datetime.now().isoformat(),
            'duration': str(datetime.now() - self.start_time),
            'results': results,
            'repairs_done': self.repairs_done
        }
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        logger.info(f"📄 レポートを保存: {report_file}")
        
    def create_final_report(self):
        """最終レポートを作成"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 自動検証・修復ループ完了レポート")
        logger.info("=" * 60)
        logger.info(f"実行時間: {datetime.now() - self.start_time}")
        logger.info(f"イテレーション数: {self.iteration}")
        logger.info(f"修復項目数: {len(self.repairs_done)}")
        
        if self.repairs_done:
            logger.info("\n🔧 実行された修復:")
            for repair in self.repairs_done:
                logger.info(f"  ✓ {repair}")
                
        logger.info("\n✅ ループ完了")

def main():
    """メイン処理"""
    system = AutoRepairSystem()
    
    try:
        system.run_loop()
        sys.exit(0)
    except KeyboardInterrupt:
        logger.info("\n⚠️ ユーザーによる中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ エラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()