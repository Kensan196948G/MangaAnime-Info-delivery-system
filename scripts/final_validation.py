#!/usr/bin/env python3
"""
最終システム検証・本番運用準備確認スクリプト
Final System Validation and Production Readiness Check
"""

import asyncio
import json
import logging
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import sys
import os

# プロジェクトルートをパスに追加
project_root = Path("/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system")
sys.path.insert(0, str(project_root))

# スクリプトインポート
try:
    from scripts.performance_validation import PerformanceValidator
    from scripts.operational_monitoring import OperationalMonitor
except ImportError:
    print("⚠️ パフォーマンス・監視モジュールのインポートに失敗しました")

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(project_root / "logs" / "final_validation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FinalSystemValidator:
    """最終システム検証クラス"""
    
    def __init__(self):
        self.project_root = project_root
        self.validation_start_time = time.time()
        self.results = {}
        
    def check_system_prerequisites(self) -> Dict[str, Any]:
        """システム前提条件チェック"""
        logger.info("🔍 システム前提条件チェック開始")
        
        prerequisites = {
            "python_version": self.check_python_version(),
            "required_packages": self.check_required_packages(),
            "directory_structure": self.check_directory_structure(),
            "configuration_files": self.check_configuration_files(),
            "database_setup": self.check_database_setup(),
            "permissions": self.check_file_permissions(),
            "external_dependencies": self.check_external_dependencies()
        }
        
        # 前提条件の合格判定
        failed_checks = []
        for check_name, result in prerequisites.items():
            if not result.get("status", False):
                failed_checks.append(check_name)
        
        prerequisites["overall_status"] = len(failed_checks) == 0
        prerequisites["failed_checks"] = failed_checks
        
        return prerequisites
    
    def check_python_version(self) -> Dict[str, Any]:
        """Python バージョンチェック"""
        try:
            python_version = sys.version_info
            required_major, required_minor = 3, 8
            
            version_ok = (python_version.major > required_major or 
                         (python_version.major == required_major and python_version.minor >= required_minor))
            
            return {
                "status": version_ok,
                "current_version": f"{python_version.major}.{python_version.minor}.{python_version.micro}",
                "required_version": f"{required_major}.{required_minor}+",
                "message": "OK" if version_ok else f"Python {required_major}.{required_minor}以上が必要です"
            }
        except Exception as e:
            return {"status": False, "error": str(e)}
    
    def check_required_packages(self) -> Dict[str, Any]:
        """必要パッケージチェック"""
        required_packages = [
            "requests", "aiohttp", "psutil", "schedule", 
            "google-auth", "google-auth-oauthlib", "google-auth-httplib2",
            "google-api-python-client", "flask", "feedparser"
        ]
        
        package_status = {}
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                package_status[package] = {"installed": True}
            except ImportError:
                package_status[package] = {"installed": False}
                missing_packages.append(package)
        
        return {
            "status": len(missing_packages) == 0,
            "package_status": package_status,
            "missing_packages": missing_packages,
            "total_required": len(required_packages),
            "installed_count": len(required_packages) - len(missing_packages)
        }
    
    def check_directory_structure(self) -> Dict[str, Any]:
        """ディレクトリ構造チェック"""
        required_dirs = [
            "modules", "scripts", "logs", "config", "templates", "static"
        ]
        
        required_files = [
            "app.py", "requirements.txt", "config/config.json",
            "modules/enhanced_error_recovery.py", "modules/dashboard.py"
        ]
        
        dir_status = {}
        missing_dirs = []
        
        for dir_name in required_dirs:
            dir_path = self.project_root / dir_name
            exists = dir_path.exists() and dir_path.is_dir()
            dir_status[dir_name] = {"exists": exists, "path": str(dir_path)}
            if not exists:
                missing_dirs.append(dir_name)
        
        file_status = {}
        missing_files = []
        
        for file_name in required_files:
            file_path = self.project_root / file_name
            exists = file_path.exists() and file_path.is_file()
            file_status[file_name] = {"exists": exists, "path": str(file_path)}
            if not exists:
                missing_files.append(file_name)
        
        return {
            "status": len(missing_dirs) == 0 and len(missing_files) == 0,
            "directories": dir_status,
            "files": file_status,
            "missing_directories": missing_dirs,
            "missing_files": missing_files
        }
    
    def check_configuration_files(self) -> Dict[str, Any]:
        """設定ファイルチェック"""
        config_checks = {}
        
        # config.json チェック
        config_path = self.project_root / "config" / "config.json"
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                required_sections = ["database", "apis", "notification", "filtering"]
                missing_sections = [section for section in required_sections if section not in config_data]
                
                config_checks["config_json"] = {
                    "exists": True,
                    "valid_json": True,
                    "required_sections": required_sections,
                    "missing_sections": missing_sections,
                    "complete": len(missing_sections) == 0
                }
            except json.JSONDecodeError as e:
                config_checks["config_json"] = {
                    "exists": True,
                    "valid_json": False,
                    "error": str(e)
                }
        else:
            config_checks["config_json"] = {"exists": False}
        
        # Google API認証ファイルチェック
        credentials_path = self.project_root / "credentials.json"
        token_path = self.project_root / "token.json"
        
        config_checks["google_auth"] = {
            "credentials_exists": credentials_path.exists(),
            "token_exists": token_path.exists(),
            "ready": credentials_path.exists() and token_path.exists()
        }
        
        # 全体ステータス
        all_configs_ok = (
            config_checks.get("config_json", {}).get("complete", False) and
            config_checks.get("google_auth", {}).get("ready", False)
        )
        
        return {
            "status": all_configs_ok,
            "details": config_checks
        }
    
    def check_database_setup(self) -> Dict[str, Any]:
        """データベースセットアップチェック"""
        db_path = self.project_root / "db.sqlite3"
        
        if not db_path.exists():
            return {
                "status": False,
                "exists": False,
                "message": "データベースファイルが存在しません"
            }
        
        try:
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # テーブル存在確認
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            required_tables = ["works", "releases"]
            missing_tables = [table for table in required_tables if table not in tables]
            
            # テーブル構造確認
            table_info = {}
            for table in required_tables:
                if table in tables:
                    cursor.execute(f"PRAGMA table_info({table})")
                    columns = [col[1] for col in cursor.fetchall()]
                    table_info[table] = {"columns": columns}
            
            conn.close()
            
            return {
                "status": len(missing_tables) == 0,
                "exists": True,
                "tables": tables,
                "missing_tables": missing_tables,
                "table_info": table_info,
                "size_mb": db_path.stat().st_size / (1024 * 1024)
            }
            
        except Exception as e:
            return {
                "status": False,
                "exists": True,
                "error": str(e)
            }
    
    def check_file_permissions(self) -> Dict[str, Any]:
        """ファイル権限チェック"""
        permission_checks = {}
        
        # 重要ファイルの権限確認
        critical_files = [
            self.project_root / "app.py",
            self.project_root / "config" / "config.json",
            self.project_root / "db.sqlite3"
        ]
        
        for file_path in critical_files:
            if file_path.exists():
                try:
                    # 読み取り権限確認
                    readable = os.access(file_path, os.R_OK)
                    # 書き込み権限確認（設定ファイルとDBには必要）
                    writable = os.access(file_path, os.W_OK) if file_path.name in ["config.json", "db.sqlite3"] else True
                    
                    permission_checks[file_path.name] = {
                        "readable": readable,
                        "writable": writable,
                        "ok": readable and writable
                    }
                except Exception as e:
                    permission_checks[file_path.name] = {"error": str(e), "ok": False}
        
        # ディレクトリ権限確認
        log_dir = self.project_root / "logs"
        if log_dir.exists():
            permission_checks["logs_directory"] = {
                "writable": os.access(log_dir, os.W_OK),
                "ok": os.access(log_dir, os.W_OK)
            }
        
        all_permissions_ok = all(check.get("ok", False) for check in permission_checks.values())
        
        return {
            "status": all_permissions_ok,
            "details": permission_checks
        }
    
    def check_external_dependencies(self) -> Dict[str, Any]:
        """外部依存関係チェック"""
        dependencies = {}
        
        # インターネット接続確認
        try:
            import requests
            response = requests.get("https://google.com", timeout=10)
            dependencies["internet"] = {
                "available": response.status_code == 200,
                "response_time": response.elapsed.total_seconds()
            }
        except Exception as e:
            dependencies["internet"] = {"available": False, "error": str(e)}
        
        # AniList API 接続確認
        try:
            response = requests.post(
                "https://graphql.anilist.co",
                json={"query": "query { Viewer { id } }"},
                timeout=10
            )
            dependencies["anilist_api"] = {
                "available": response.status_code in [200, 401],  # 401 = 未認証だが接続OK
                "status_code": response.status_code
            }
        except Exception as e:
            dependencies["anilist_api"] = {"available": False, "error": str(e)}
        
        # cron 利用可能性確認
        try:
            result = subprocess.run(["which", "crontab"], capture_output=True)
            dependencies["cron"] = {
                "available": result.returncode == 0,
                "path": result.stdout.decode().strip() if result.returncode == 0 else None
            }
        except Exception as e:
            dependencies["cron"] = {"available": False, "error": str(e)}
        
        all_dependencies_ok = all(dep.get("available", False) for dep in dependencies.values())
        
        return {
            "status": all_dependencies_ok,
            "details": dependencies
        }
    
    async def run_comprehensive_validation(self) -> Dict[str, Any]:
        """包括的検証実行"""
        logger.info("🚀 最終システム検証開始")
        
        validation_results = {
            "validation_timestamp": datetime.now().isoformat(),
            "prerequisites": {},
            "performance": {},
            "integration": {},
            "operational_readiness": {},
            "final_score": 0,
            "production_readiness": False,
            "recommendations": [],
            "critical_issues": [],
            "warnings": []
        }
        
        try:
            # 1. 前提条件チェック
            logger.info("📋 前提条件チェック実行中...")
            validation_results["prerequisites"] = self.check_system_prerequisites()
            
            # 2. パフォーマンス検証
            logger.info("⚡ パフォーマンス検証実行中...")
            try:
                performance_validator = PerformanceValidator()
                validation_results["performance"] = performance_validator.generate_performance_report()
            except Exception as e:
                logger.error(f"パフォーマンス検証エラー: {e}")
                validation_results["performance"] = {"error": str(e), "status": "failed"}
            
            # 3. 統合テスト実行
            logger.info("🔗 統合テスト実行中...")
            try:
                from scripts.integration_test import IntegrationTestSuite
                integration_tester = IntegrationTestSuite()
                validation_results["integration"] = await integration_tester.run_full_integration_test()
            except Exception as e:
                logger.error(f"統合テスト実行エラー: {e}")
                validation_results["integration"] = {"error": str(e), "status": "failed"}
            
            # 4. 運用準備確認
            logger.info("🔧 運用準備確認実行中...")
            try:
                operational_monitor = OperationalMonitor()
                health_check = operational_monitor.check_system_health()
                daily_report = operational_monitor.generate_daily_report()
                validation_results["operational_readiness"] = {
                    "health_status": health_check,
                    "daily_report": daily_report,
                    "monitoring_ready": True
                }
            except Exception as e:
                logger.error(f"運用準備確認エラー: {e}")
                validation_results["operational_readiness"] = {"error": str(e), "status": "failed"}
            
            # 5. 最終評価とスコア計算
            final_assessment = self.calculate_final_score(validation_results)
            validation_results.update(final_assessment)
            
        except Exception as e:
            logger.error(f"包括的検証実行エラー: {e}")
            validation_results["critical_error"] = str(e)
        
        validation_results["total_validation_time"] = time.time() - self.validation_start_time
        
        return validation_results
    
    def calculate_final_score(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """最終スコア計算と本番運用準備評価"""
        score_components = {}
        
        # 前提条件スコア (0-25点)
        prerequisites = results.get("prerequisites", {})
        if prerequisites.get("overall_status", False):
            score_components["prerequisites"] = 25
        else:
            failed_count = len(prerequisites.get("failed_checks", []))
            score_components["prerequisites"] = max(0, 25 - (failed_count * 5))
        
        # パフォーマンススコア (0-25点)
        performance = results.get("performance", {})
        if "overall_performance_score" in performance:
            score_components["performance"] = min(25, performance["overall_performance_score"] / 4)
        else:
            score_components["performance"] = 0
        
        # 統合テストスコア (0-25点)
        integration = results.get("integration", {})
        if "overall_score" in integration:
            score_components["integration"] = min(25, integration["overall_score"] / 4)
        else:
            score_components["integration"] = 0
        
        # 運用準備スコア (0-25点)
        operational = results.get("operational_readiness", {})
        if "health_status" in operational:
            health_status = operational["health_status"].get("overall_status", "error")
            if health_status == "healthy":
                score_components["operational"] = 25
            elif health_status == "warning":
                score_components["operational"] = 15
            else:
                score_components["operational"] = 5
        else:
            score_components["operational"] = 0
        
        # 総合スコア
        final_score = sum(score_components.values())
        
        # 本番運用準備判定
        production_readiness = final_score >= 80 and all(score >= 15 for score in score_components.values())
        
        # 推奨事項生成
        recommendations = self.generate_final_recommendations(results, score_components, final_score)
        
        # 重要課題特定
        critical_issues = self.identify_critical_issues(results, score_components)
        
        # 警告事項特定
        warnings = self.identify_warnings(results, score_components)
        
        return {
            "final_score": final_score,
            "score_breakdown": score_components,
            "production_readiness": production_readiness,
            "recommendations": recommendations,
            "critical_issues": critical_issues,
            "warnings": warnings,
            "readiness_level": self.get_readiness_level(final_score)
        }
    
    def generate_final_recommendations(self, results: Dict[str, Any], score_components: Dict[str, float], final_score: float) -> List[str]:
        """最終推奨事項生成"""
        recommendations = []
        
        if final_score < 60:
            recommendations.append("🚨 システムに重大な問題があります。本番運用前に必須修正が必要です。")
        elif final_score < 80:
            recommendations.append("⚠️ システムの安定性向上が必要です。推奨修正を適用してください。")
        else:
            recommendations.append("✅ システムは本番運用準備が整っています。")
        
        # 個別推奨事項
        if score_components.get("prerequisites", 0) < 20:
            recommendations.append("📋 システム前提条件を満たしてください（Python版本、必要パッケージなど）")
        
        if score_components.get("performance", 0) < 15:
            recommendations.append("⚡ システムパフォーマンスの最適化が必要です")
        
        if score_components.get("integration", 0) < 15:
            recommendations.append("🔗 統合テストで問題が検出されました。API連携や機能統合を確認してください")
        
        if score_components.get("operational", 0) < 15:
            recommendations.append("🔧 運用監視体制の強化が必要です")
        
        # 具体的な改善提案
        if final_score >= 80:
            recommendations.extend([
                "🎯 定期的なシステムヘルスチェックの実施",
                "📊 パフォーマンス監視とアラート設定",
                "🔄 自動バックアップスケジュールの確認",
                "📧 障害通知システムの設定"
            ])
        
        return recommendations
    
    def identify_critical_issues(self, results: Dict[str, Any], score_components: Dict[str, float]) -> List[str]:
        """重要課題特定"""
        critical_issues = []
        
        # 前提条件の重要問題
        prerequisites = results.get("prerequisites", {})
        if not prerequisites.get("overall_status", False):
            failed_checks = prerequisites.get("failed_checks", [])
            if "python_version" in failed_checks:
                critical_issues.append("Python バージョンが要件を満たしていません")
            if "required_packages" in failed_checks:
                critical_issues.append("必要なPythonパッケージがインストールされていません")
            if "database_setup" in failed_checks:
                critical_issues.append("データベースの設定が完了していません")
        
        # パフォーマンスの重要問題
        performance = results.get("performance", {})
        if performance.get("overall_performance_score", 0) < 50:
            critical_issues.append("システムパフォーマンスが基準値を大幅に下回っています")
        
        # 統合テストの重要問題
        integration = results.get("integration", {})
        if integration.get("overall_status") == "failed":
            critical_issues.append("統合テストで重大なエラーが発生しました")
        
        # 運用の重要問題
        operational = results.get("operational_readiness", {})
        health_status = operational.get("health_status", {})
        if health_status.get("overall_status") == "critical":
            critical_issues.append("システムヘルスチェックで重大な問題が検出されました")
        
        return critical_issues
    
    def identify_warnings(self, results: Dict[str, Any], score_components: Dict[str, float]) -> List[str]:
        """警告事項特定"""
        warnings = []
        
        # 設定関連の警告
        prerequisites = results.get("prerequisites", {})
        config_details = prerequisites.get("configuration_files", {}).get("details", {})
        if not config_details.get("google_auth", {}).get("ready", False):
            warnings.append("Google API認証設定が未完了です（Gmail/Calendar機能が利用できません）")
        
        # パフォーマンス警告
        performance = results.get("performance", {})
        if 50 <= performance.get("overall_performance_score", 0) < 80:
            warnings.append("パフォーマンスに改善の余地があります")
        
        # 統合テスト警告
        integration = results.get("integration", {})
        if integration.get("overall_status") == "warning":
            warnings.append("統合テストで軽微な問題が検出されました")
        
        # 運用警告
        operational = results.get("operational_readiness", {})
        health_status = operational.get("health_status", {})
        if health_status.get("overall_status") == "warning":
            warnings.append("システム監視で注意が必要な項目があります")
        
        return warnings
    
    def get_readiness_level(self, score: float) -> str:
        """準備レベル取得"""
        if score >= 90:
            return "優秀 - 本番運用準備完了"
        elif score >= 80:
            return "良好 - 本番運用可能"
        elif score >= 70:
            return "普通 - 軽微な改善推奨"
        elif score >= 60:
            return "要改善 - 修正後に再評価"
        else:
            return "不合格 - 重大な問題あり"

def generate_comprehensive_report(results: Dict[str, Any]) -> str:
    """包括的レポート生成"""
    report_lines = []
    
    report_lines.extend([
        "=" * 100,
        "🎯 アニメ・マンガ情報配信システム - 最終システム検証レポート",
        "=" * 100,
        f"📅 検証実行日時: {results['validation_timestamp']}",
        f"⏱️ 総検証時間: {results.get('total_validation_time', 0):.2f}秒",
        "",
        "📊 総合評価",
        "-" * 50,
        f"🎯 最終スコア: {results['final_score']:.1f}/100",
        f"🏆 準備レベル: {results['readiness_level']}",
        f"✅ 本番運用準備: {'完了' if results['production_readiness'] else '未完了'}",
        "",
    ])
    
    # スコア内訳
    report_lines.extend([
        "📈 スコア内訳",
        "-" * 50,
    ])
    
    score_breakdown = results.get('score_breakdown', {})
    for component, score in score_breakdown.items():
        component_names = {
            'prerequisites': '前提条件',
            'performance': 'パフォーマンス',
            'integration': '統合テスト',
            'operational': '運用準備'
        }
        name = component_names.get(component, component)
        report_lines.append(f"  {name}: {score:.1f}/25")
    
    report_lines.append("")
    
    # 重要課題
    if results.get('critical_issues'):
        report_lines.extend([
            "🚨 重要課題",
            "-" * 50,
        ])
        for i, issue in enumerate(results['critical_issues'], 1):
            report_lines.append(f"  {i}. {issue}")
        report_lines.append("")
    
    # 警告事項
    if results.get('warnings'):
        report_lines.extend([
            "⚠️ 警告事項",
            "-" * 50,
        ])
        for i, warning in enumerate(results['warnings'], 1):
            report_lines.append(f"  {i}. {warning}")
        report_lines.append("")
    
    # 推奨事項
    if results.get('recommendations'):
        report_lines.extend([
            "💡 推奨事項",
            "-" * 50,
        ])
        for i, rec in enumerate(results['recommendations'], 1):
            report_lines.append(f"  {i}. {rec}")
        report_lines.append("")
    
    # 詳細結果サマリー
    report_lines.extend([
        "📋 詳細結果サマリー",
        "-" * 50,
    ])
    
    # 前提条件
    prerequisites = results.get('prerequisites', {})
    status_emoji = "✅" if prerequisites.get('overall_status', False) else "❌"
    report_lines.append(f"  {status_emoji} 前提条件: {'合格' if prerequisites.get('overall_status', False) else '不合格'}")
    
    # パフォーマンス
    performance = results.get('performance', {})
    perf_score = performance.get('overall_performance_score', 0)
    status_emoji = "✅" if perf_score >= 80 else "⚠️" if perf_score >= 60 else "❌"
    report_lines.append(f"  {status_emoji} パフォーマンス: {perf_score:.1f}/100")
    
    # 統合テスト
    integration = results.get('integration', {})
    int_status = integration.get('overall_status', 'failed')
    status_emoji = "✅" if int_status == 'passed' else "⚠️" if int_status == 'warning' else "❌"
    report_lines.append(f"  {status_emoji} 統合テスト: {int_status}")
    
    # 運用準備
    operational = results.get('operational_readiness', {})
    op_status = operational.get('health_status', {}).get('overall_status', 'error')
    status_emoji = "✅" if op_status == 'healthy' else "⚠️" if op_status == 'warning' else "❌"
    report_lines.append(f"  {status_emoji} 運用準備: {op_status}")
    
    report_lines.extend([
        "",
        "=" * 100,
        "🎉 検証完了 - システムの準備状況を確認してください",
        "=" * 100
    ])
    
    return "\n".join(report_lines)

async def main():
    """メイン実行関数"""
    logger.info("🚀 最終システム検証開始")
    
    # ログディレクトリ作成
    (project_root / "logs").mkdir(exist_ok=True)
    
    validator = FinalSystemValidator()
    
    try:
        # 包括的検証実行
        results = await validator.run_comprehensive_validation()
        
        # 結果保存
        results_path = project_root / "FINAL_VALIDATION_REPORT.json"
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        
        # 人間可読レポート生成
        readable_report = generate_comprehensive_report(results)
        report_path = project_root / "FINAL_VALIDATION_REPORT.txt"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(readable_report)
        
        # コンソール出力
        print(readable_report)
        
        print(f"\n📄 詳細JSON結果: {results_path}")
        print(f"📄 読みやすいレポート: {report_path}")
        
        logger.info("✅ 最終システム検証完了")
        
        # 終了コード設定
        if results.get('production_readiness', False):
            sys.exit(0)  # 本番準備完了
        elif results.get('final_score', 0) >= 70:
            sys.exit(1)  # 軽微な問題あり
        else:
            sys.exit(2)  # 重大な問題あり
        
    except Exception as e:
        logger.error(f"❌ 最終検証実行エラー: {e}")
        print(f"\n❌ 検証実行中にエラーが発生しました: {e}")
        sys.exit(3)

if __name__ == "__main__":
    asyncio.run(main())