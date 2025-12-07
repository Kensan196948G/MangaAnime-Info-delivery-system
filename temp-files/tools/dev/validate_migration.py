#!/usr/bin/env python3
"""
移行後検証スクリプト

ファイル移行後にimportが正常に動作するか検証します。

Usage:
    python tools/dev/validate_migration.py
"""

import sys
import importlib
from pathlib import Path
from typing import List, Tuple

# プロジェクトルートをPYTHONPATHに追加
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class MigrationValidator:
    """移行検証クラス"""

    def __init__(self):
        self.passed = []
        self.failed = []

    def validate_import(self, module_path: str, description: str = "") -> bool:
        """指定されたモジュールをimportして検証"""
        try:
            importlib.import_module(module_path)
            self.passed.append((module_path, description))
            print(f"✓ {module_path:40s} {description}")
            return True
        except ImportError as e:
            self.failed.append((module_path, description, str(e)))
            print(f"✗ {module_path:40s} {description} - Error: {e}")
            return False
        except Exception as e:
            self.failed.append((module_path, description, str(e)))
            print(f"✗ {module_path:40s} {description} - Unexpected Error: {e}")
            return False

    def validate_class_import(self, module_path: str, class_name: str) -> bool:
        """指定されたクラスをimportして検証"""
        try:
            module = importlib.import_module(module_path)
            getattr(module, class_name)
            self.passed.append((f"{module_path}.{class_name}", "Class import"))
            print(f"✓ {module_path}.{class_name:30s} Class import")
            return True
        except (ImportError, AttributeError) as e:
            self.failed.append((f"{module_path}.{class_name}", "Class import", str(e)))
            print(f"✗ {module_path}.{class_name:30s} Class import - Error: {e}")
            return False

    def validate_function_import(self, module_path: str, function_name: str) -> bool:
        """指定された関数をimportして検証"""
        try:
            module = importlib.import_module(module_path)
            getattr(module, function_name)
            self.passed.append((f"{module_path}.{function_name}", "Function import"))
            print(f"✓ {module_path}.{function_name:30s} Function import")
            return True
        except (ImportError, AttributeError) as e:
            self.failed.append((f"{module_path}.{function_name}", "Function import", str(e)))
            print(f"✗ {module_path}.{function_name:30s} Function import - Error: {e}")
            return False

    def validate_all(self) -> bool:
        """すべての移行を検証"""
        print("=" * 70)
        print("Migration Validation")
        print("=" * 70)
        print()

        # 1. アプリケーション層
        print("--- Application Layer ---")
        self.validate_import("app.main", "Flask Web UI")
        self.validate_import("app.cli_notifier", "CLI Notifier")
        self.validate_import("app.dashboard_app", "Dashboard App")
        print()

        # 2. 認証層
        print("--- Authentication Layer ---")
        self.validate_import("auth.config_manager", "Auth Config Manager")
        self.validate_class_import("auth.config_manager", "AuthConfig")
        self.validate_import("auth.oauth_helper", "OAuth Helper")
        self.validate_import("auth.token_generator", "Token Generator")
        print()

        # 3. modules/ (既存 - 変更なし)
        print("--- Core Modules (unchanged) ---")
        self.validate_import("modules.db", "Database Manager")
        self.validate_class_import("modules.db", "DatabaseManager")
        self.validate_import("modules.mailer", "Gmail Notifier")
        self.validate_import("modules.anime_anilist", "AniList Collector")
        self.validate_import("modules.manga_rss", "Manga RSS Collector")
        print()

        # 4. テスト層
        print("--- Test Layer ---")
        self.validate_import("tests.integration.backend.test_backend_api", "Backend API Test")
        self.validate_import("tests.integration.notification.test_email_delivery", "Email Delivery Test")
        self.validate_import("tests.integration.notification.test_gmail_auth", "Gmail Auth Test")
        self.validate_import("tests.integration.security.test_secret_key", "Secret Key Test")
        print()

        # 5. ツール層
        print("--- Tools Layer ---")
        self.validate_import("tools.testing.test_runner", "Test Runner")
        self.validate_import("tools.validation.validate_system", "System Validator")
        self.validate_import("tools.repair.fix_all_tests", "Test Fixer")
        self.validate_import("tools.monitoring.continuous_monitor", "Continuous Monitor")
        print()

        # 6. Flask app インスタンス
        print("--- Flask Application Instance ---")
        try:
            from app.main import app
            print(f"✓ Flask app instance available: {type(app)}")
            self.passed.append(("app.main.app", "Flask instance"))
        except Exception as e:
            print(f"✗ Flask app instance - Error: {e}")
            self.failed.append(("app.main.app", "Flask instance", str(e)))
        print()

        # 7. CLI エントリポイント
        print("--- CLI Entry Points ---")
        self.validate_function_import("app.cli_notifier", "main")
        print()

        # 結果サマリー
        print("=" * 70)
        print("Validation Summary")
        print("=" * 70)
        print(f"Passed: {len(self.passed)}")
        print(f"Failed: {len(self.failed)}")
        print()

        if self.failed:
            print("Failed imports:")
            for module, desc, error in self.failed:
                print(f"  - {module} ({desc})")
                print(f"    Error: {error}")
            print()

        return len(self.failed) == 0

    def validate_file_structure(self) -> bool:
        """ファイル構造の検証"""
        print("=" * 70)
        print("File Structure Validation")
        print("=" * 70)
        print()

        required_files = [
            "app/__init__.py",
            "app/main.py",
            "app/cli_notifier.py",
            "auth/__init__.py",
            "auth/config_manager.py",
            "auth/token_generator.py",
            "tests/integration/__init__.py",
            "tests/integration/backend/__init__.py",
            "tests/integration/notification/__init__.py",
            "tools/testing/test_runner.py",
            "tools/validation/validate_system.py",
        ]

        missing_files = []
        for file_path in required_files:
            full_path = PROJECT_ROOT / file_path
            if full_path.exists():
                print(f"✓ {file_path}")
            else:
                print(f"✗ {file_path} - NOT FOUND")
                missing_files.append(file_path)

        print()
        print(f"Total files checked: {len(required_files)}")
        print(f"Missing files: {len(missing_files)}")
        print()

        return len(missing_files) == 0

    def validate_old_files_removed(self) -> bool:
        """旧ファイルが削除されているか検証"""
        print("=" * 70)
        print("Old Files Cleanup Validation")
        print("=" * 70)
        print()

        old_files = [
            "web_app.py",
            "release_notifier.py",
            "auth_config.py",
            "create_token.py",
            "test_backend_api.py",
            "test_gmail_auth.py",
        ]

        remaining_files = []
        for file_path in old_files:
            full_path = PROJECT_ROOT / file_path
            if full_path.exists():
                print(f"✗ {file_path} - STILL EXISTS (should be moved)")
                remaining_files.append(file_path)
            else:
                print(f"✓ {file_path} - Properly moved")

        print()
        print(f"Total files checked: {len(old_files)}")
        print(f"Remaining old files: {len(remaining_files)}")
        print()

        return len(remaining_files) == 0


def main():
    """メイン処理"""
    validator = MigrationValidator()

    # ファイル構造検証
    structure_ok = validator.validate_file_structure()

    # import検証
    imports_ok = validator.validate_all()

    # 旧ファイル削除確認
    cleanup_ok = validator.validate_old_files_removed()

    # 総合判定
    print("=" * 70)
    print("Overall Result")
    print("=" * 70)
    print(f"File Structure: {'✓ PASS' if structure_ok else '✗ FAIL'}")
    print(f"Import Tests:   {'✓ PASS' if imports_ok else '✗ FAIL'}")
    print(f"File Cleanup:   {'✓ PASS' if cleanup_ok else '✗ FAIL'}")
    print()

    if structure_ok and imports_ok and cleanup_ok:
        print("✅ All validations passed! Migration successful.")
        return 0
    else:
        print("❌ Some validations failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
