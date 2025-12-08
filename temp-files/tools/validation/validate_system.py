#!/usr/bin/env python3
"""
システム修復検証スクリプト

修復されたシステムが正常に動作することを包括的に検証する。
"""

import json
import os
import sys
import subprocess
import logging
from typing import List, Dict, Any

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_config_validation():
    """設定ファイルの検証テスト"""
    logger.info("🔧 設定ファイル検証テスト")
    
    try:
        from modules.config import get_config
        config = get_config()
        errors = config.validate_config()
        
        if errors:
            logger.error(f"❌ 設定エラーが検出されました: {errors}")
            return False
        else:
            logger.info("✅ 設定ファイルの検証成功")
            return True
    except Exception as e:
        logger.error(f"❌ 設定検証テストでエラー: {e}")
        return False


def test_system_startup():
    """システム起動テスト"""
    logger.info("🚀 システム起動テスト")
    
    try:
        result = subprocess.run(
            [sys.executable, "release_notifier.py", "--dry-run"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            logger.info("✅ システム起動テスト成功")
            logger.info("stdout の最後の5行:")
            for line in result.stdout.strip().split('\\n')[-5:]:
                logger.info(f"  {line}")
            return True
        else:
            logger.error(f"❌ システム起動テスト失敗 (code: {result.returncode})")
            logger.error(f"stderr: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("❌ システム起動テストがタイムアウト")
        return False
    except Exception as e:
        logger.error(f"❌ システム起動テストでエラー: {e}")
        return False


def test_module_imports():
    """主要モジュールのインポートテスト"""
    logger.info("📦 モジュールインポートテスト")
    
    modules_to_test = [
        "modules.config",
        "modules.db",
        "modules.anime_anilist",
        "modules.manga_rss",
        "modules.filter_logic",
        "modules.mailer",
        "modules.calendar",
        "release_notifier"
    ]
    
    all_success = True
    for module in modules_to_test:
        try:
            __import__(module)
            logger.info(f"  ✅ {module}")
        except Exception as e:
            logger.error(f"  ❌ {module}: {e}")
            all_success = False
    
    return all_success


def test_database_connection():
    """データベース接続テスト"""
    logger.info("🗄️  データベース接続テスト")
    
    try:
        from modules.db import DatabaseManager, get_db
        db = get_db()
        
        # 簡単なクエリを実行
        db.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
        logger.info("✅ データベース接続テスト成功")
        return True
        
    except Exception as e:
        logger.error(f"❌ データベース接続テストでエラー: {e}")
        return False


def test_api_configs():
    """API設定テスト"""
    logger.info("🌐 API設定テスト")
    
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        # Google API設定
        google_config = config.get('apis', {}).get('google', {})
        if google_config.get('credentials_file'):
            if os.path.exists(google_config['credentials_file']):
                logger.info("  ✅ Google認証ファイルが存在")
            else:
                logger.warning(f"  ⚠️ Google認証ファイルが見つかりません: {google_config['credentials_file']}")
        
        # Email設定
        email_config = config.get('notification', {}).get('email', {})
        if email_config.get('sender') and email_config.get('recipients'):
            logger.info("  ✅ Email設定が存在")
        else:
            logger.warning("  ⚠️ Email設定が不完全")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ API設定テストでエラー: {e}")
        return False


def generate_test_report(results: Dict[str, bool]):
    """テスト結果レポートの生成"""
    logger.info("=" * 60)
    logger.info("📊 システム検証レポート")
    logger.info("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results.values() if r)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
    
    logger.info("=" * 60)
    logger.info(f"📊 テスト結果: {passed_tests}/{total_tests} PASSED")
    
    if passed_tests == total_tests:
        logger.info("🎉 すべてのテストが成功しました！")
        logger.info("システムは完全に修復され、正常に動作しています。")
        return True
    else:
        logger.warning(f"⚠️ {total_tests - passed_tests}件のテストが失敗しました")
        return False


def main():
    """メイン関数"""
    logger.info("=" * 60)
    logger.info("🚀 MangaAnime Info Delivery System 検証")
    logger.info("=" * 60)
    
    test_results = {}
    
    # 各種テストを実行
    test_results["設定ファイル検証"] = test_config_validation()
    test_results["モジュールインポート"] = test_module_imports()
    test_results["データベース接続"] = test_database_connection()
    test_results["API設定"] = test_api_configs()
    test_results["システム起動"] = test_system_startup()
    
    # レポート生成
    success = generate_test_report(test_results)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()