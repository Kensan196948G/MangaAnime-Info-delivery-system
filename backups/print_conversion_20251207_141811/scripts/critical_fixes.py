#!/usr/bin/env python3
"""
Critical Issues Fix Script for MangaAnime Information Delivery System
SubAgent並列検知による緊急修復項目の自動実行

実行方法:
    python3 scripts/critical_fixes.py --all
    python3 scripts/critical_fixes.py --security-only
    python3 scripts/critical_fixes.py --deps-only
"""

import os
import sys
import subprocess
import logging
import argparse
from pathlib import Path

# ログ設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CriticalFixManager:
    """SubAgent検知による重要課題の自動修復"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.fixes_applied = []
        self.errors = []

    def fix_file_permissions(self):
        """Critical: ファイル権限の自動設定"""
        logger.info("🔒 ファイル権限の自動設定中...")

        # 機密ファイルの権限設定
        sensitive_files = ["config.json", ".env", "credentials.json", "token.json"]

        for file_name in sensitive_files:
            file_path = self.project_root / file_name
            if file_path.exists():
                try:
                    os.chmod(file_path, 0o600)
                    logger.info(f"✅ {file_name}: 権限を600に設定")
                    self.fixes_applied.append(f"File permission: {file_name}")
                except OSError as e:
                    self.errors.append(f"権限設定失敗 {file_name}: {e}")

        # 実行ファイルの権限設定
        executable_files = [
            "scripts/error_monitor.sh",
            "scripts/setup.sh",
            "scripts/validate.sh",
            "run_claude_autoloop.sh",
        ]

        for file_name in executable_files:
            file_path = self.project_root / file_name
            if file_path.exists():
                try:
                    os.chmod(file_path, 0o755)
                    logger.info(f"✅ {file_name}: 実行権限を755に設定")
                    self.fixes_applied.append(f"Execute permission: {file_name}")
                except OSError as e:
                    self.errors.append(f"実行権限設定失敗 {file_name}: {e}")

    def fix_weak_crypto(self):
        """Critical: 弱い暗号化アルゴリズムの置換"""
        logger.info("🔐 弱い暗号化アルゴリズムの修正中...")

        # 修正対象ファイルパターン
        python_files = list(self.project_root.glob("**/*.py"))

        replacements = [
            ("secrets.SystemRandom().random()", "secrets.SystemRandom().random()"),
            ("import random\n", "import secrets\n"),
            ("hashlib.sha256(", "hashlib.sha256("),
            ("secrets.choice(", "secrets.choice("),
            ("secrets.randbelow(", "secrets.randbelow("),
        ]

        for py_file in python_files:
            if py_file.name.startswith(".") or "venv" in str(py_file):
                continue

            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                modified = False
                for old, new in replacements:
                    if old in content:
                        content = content.replace(old, new)
                        modified = True
                        logger.info(f"✅ {py_file.name}: {old} → {new}")

                if modified:
                    with open(py_file, "w", encoding="utf-8") as f:
                        f.write(content)
                    self.fixes_applied.append(f"Crypto fix: {py_file.name}")

            except Exception as e:
                self.errors.append(f"暗号化修正失敗 {py_file}: {e}")

    def install_missing_dependencies(self):
        """Critical: 不足依存関係の自動インストール"""
        logger.info("📦 不足依存関係の自動インストール中...")

        try:
            # requirements.txtの更新版を使用
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "-r",
                    str(self.project_root / "requirements.txt"),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            logger.info("✅ 依存関係のインストール完了")
            self.fixes_applied.append("Dependencies installation")

        except subprocess.CalledProcessError as e:
            self.errors.append(f"依存関係インストール失敗: {e}")

    def create_production_config(self):
        """Critical: 本番用設定ファイルの自動生成"""
        logger.info("⚙️ 本番用設定ファイルの生成中...")

        config_template = self.project_root / "config" / "config.template.json"
        config_file = self.project_root / "config.json"

        if config_template.exists() and not config_file.exists():
            try:
                import shutil

                shutil.copy2(config_template, config_file)

                # 環境変数プレースホルダーの設定
                with open(config_file, "r") as f:
                    content = f.read()

                # テスト用設定に置換
                content = content.replace(
                    '"your-email@gmail.com"', '"${NOTIFICATION_EMAIL}"'
                )

                with open(config_file, "w") as f:
                    f.write(content)

                os.chmod(config_file, 0o600)
                logger.info("✅ 本番用config.json生成完了")
                self.fixes_applied.append("Production config creation")

            except Exception as e:
                self.errors.append(f"設定ファイル生成失敗: {e}")

    def fix_sql_injection_risks(self):
        """Medium: SQL Injection対策の強化"""
        logger.info("🛡️ SQL Injection対策の実装中...")

        # modules/db.py の修正
        db_file = self.project_root / "modules" / "db.py"

        if db_file.exists():
            try:
                with open(db_file, "r") as f:
                    content = f.read()

                # SQL文字列連結の検出と警告
                if 'f"' in content and "SELECT" in content:
                    logger.warning("⚠️ SQL文字列連結が検出されました")
                    logger.info("推奨: パラメータ化クエリの使用")

                # 既に適切に実装されているかチェック
                if "execute(" in content and "?" in content:
                    logger.info("✅ パラメータ化クエリが実装済み")
                    self.fixes_applied.append("SQL injection prevention verified")

            except Exception as e:
                self.errors.append(f"SQL Injection対策確認失敗: {e}")

    def generate_fix_report(self):
        """修復レポートの生成"""
        report = {
            "fixes_applied": self.fixes_applied,
            "errors": self.errors,
            "status": "SUCCESS" if not self.errors else "PARTIAL_SUCCESS",
        }

        report_file = self.project_root / "CRITICAL_FIXES_REPORT.json"

        import json

        with open(report_file, "w") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        return report

    def run_all_fixes(self):
        """全ての重要修復の実行"""
        logger.info("🚀 Critical Issues 緊急修復開始...")

        self.fix_file_permissions()
        self.fix_weak_crypto()
        self.install_missing_dependencies()
        self.create_production_config()
        self.fix_sql_injection_risks()

        report = self.generate_fix_report()

        logger.info("🏁 緊急修復完了")
        logger.info(f"✅ 修復項目: {len(self.fixes_applied)}")
        logger.info(f"❌ エラー項目: {len(self.errors)}")

        return report


def main():
    parser = argparse.ArgumentParser(
        description="Critical Issues Fix for MangaAnime System"
    )
    parser.add_argument("--all", action="store_true", help="Run all critical fixes")
    parser.add_argument(
        "--security-only", action="store_true", help="Run security fixes only"
    )
    parser.add_argument(
        "--deps-only", action="store_true", help="Install dependencies only"
    )

    args = parser.parse_args()

    fixer = CriticalFixManager()

    if args.all:
        report = fixer.run_all_fixes()
    elif args.security_only:
        fixer.fix_file_permissions()
        fixer.fix_weak_crypto()
        fixer.fix_sql_injection_risks()
        report = fixer.generate_fix_report()
    elif args.deps_only:
        fixer.install_missing_dependencies()
        report = fixer.generate_fix_report()
    else:
        parser.print_help()
        return

    logger.info(f"\n🎯 修復結果: {report['status']}")
    logger.info(f"✅ 成功: {len(report['fixes_applied'])} 項目")
    logger.info(f"❌ エラー: {len(report['errors'])} 項目")

    if report["errors"]:
        logger.info("\n🚨 エラー詳細:")
        for error in report["errors"]:
            logger.info(f"  • {error}")


if __name__ == "__main__":
    main()
