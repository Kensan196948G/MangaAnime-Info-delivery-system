#!/usr/bin/env python3
"""
Pythonファイル整理・移行スクリプト

このスクリプトは、ルート直下の53個のPythonファイルを
適切なディレクトリ構造に移動し、import文を自動的に更新します。

Usage:
    python tools/dev/refactor_migrate_files.py --dry-run  # 確認モード
    python tools/dev/refactor_migrate_files.py --phase 1  # Phase 1のみ実行
    python tools/dev/refactor_migrate_files.py --execute  # 実行モード
"""

import os
import re
import shutil
import argparse
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime


class FileMigrator:
    """ファイル移行管理クラス"""

    def __init__(self, project_root: Path, dry_run: bool = True):
        self.project_root = project_root
        self.dry_run = dry_run
        self.moved_files = []
        self.updated_imports = []
        self.errors = []

    def create_directories(self) -> None:
        """必要なディレクトリを作成"""
        directories = [
            "app",
            "auth",
            "tools/testing",
            "tools/validation",
            "tools/repair",
            "tools/monitoring",
            "tools/dev",
            "archive/auth_variants",
            "tests/integration/backend",
            "tests/integration/notification",
            "tests/integration/security",
            "tests/integration/phase2",
        ]

        for directory in directories:
            dir_path = self.project_root / directory
            if not dir_path.exists():
                if self.dry_run:
                    print(f"[DRY-RUN] Would create directory: {directory}")
                else:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    print(f"Created directory: {directory}")

                # __init__.py を作成 (Pythonパッケージとして認識)
                if not directory.startswith("tools") and not directory.startswith("archive"):
                    init_file = dir_path / "__init__.py"
                    if not init_file.exists():
                        if self.dry_run:
                            print(f"[DRY-RUN] Would create: {directory}/__init__.py")
                        else:
                            init_file.write_text('"""{}"""\n'.format(directory.split("/")[-1]))
                            print(f"Created: {directory}/__init__.py")

    def get_migration_plan(self) -> Dict[str, List[Tuple[str, str]]]:
        """移行計画を取得"""
        return {
            "Phase 1: アプリケーション層": [
                ("web_app.py", "app/main.py"),
                ("release_notifier.py", "app/cli_notifier.py"),
                ("dashboard_main.py", "app/dashboard_app.py"),
            ],
            "Phase 2: 認証層": [
                ("auth_config.py", "auth/config_manager.py"),
                ("oauth_setup_helper.py", "auth/oauth_helper.py"),
                ("create_token.py", "auth/token_generator.py"),
                ("create_token_simple.py", "archive/auth_variants/create_token_simple.py"),
                ("create_token_improved.py", "archive/auth_variants/create_token_improved.py"),
                ("create_token_manual.py", "archive/auth_variants/create_token_manual.py"),
                ("generate_token.py", "archive/auth_variants/generate_token.py"),
            ],
            "Phase 3: テスト層 (統合テスト)": [
                ("test_backend_api.py", "tests/integration/backend/test_backend_api.py"),
                ("test_enhanced_backend.py", "tests/integration/backend/test_enhanced_backend.py"),
                ("test_email_delivery.py", "tests/integration/notification/test_email_delivery.py"),
                ("test_gmail_auth.py", "tests/integration/notification/test_gmail_auth.py"),
                ("test_mailer_improvements.py", "tests/integration/notification/test_mailer_improvements.py"),
                ("test_smtp_email.py", "tests/integration/notification/test_smtp_email.py"),
                ("test_notification.py", "tests/integration/notification/test_notification.py"),
                ("test_secret_key.py", "tests/integration/security/test_secret_key.py"),
                ("test_phase2_implementation.py", "tests/integration/phase2/test_phase2_implementation.py"),
                ("simple_phase2_test.py", "tests/integration/phase2/simple_phase2_test.py"),
            ],
            "Phase 4: テスト実行ツール": [
                ("test_runner.py", "tools/testing/test_runner.py"),
                ("run_check.py", "tools/testing/run_check.py"),
                ("run_failing_tests.py", "tools/testing/run_failing_tests.py"),
                ("run_fixed_tests.py", "tools/testing/run_fixed_tests.py"),
                ("simple_test_runner.py", "tools/testing/simple_test_runner.py"),
            ],
            "Phase 5: 検証ツール": [
                ("validate_system.py", "tools/validation/validate_system.py"),
                ("check_structure.py", "tools/validation/check_structure.py"),
                ("check_doc_references.py", "tools/validation/check_doc_references.py"),
                ("verify_tests.py", "tools/validation/verify_tests.py"),
                ("direct_file_check.py", "tools/validation/direct_file_check.py"),
                ("test_discovery.py", "tools/validation/test_discovery.py"),
            ],
            "Phase 6: 修復ツール": [
                ("fix_all_tests.py", "tools/repair/fix_all_tests.py"),
                ("fix_tests_final.py", "tools/repair/fix_tests_final.py"),
                ("fix_config_errors.py", "tools/repair/fix_config_errors.py"),
                ("fix_database_integrity.py", "tools/repair/fix_database_integrity.py"),
                ("fix_hardcoded_paths.py", "tools/repair/fix_hardcoded_paths.py"),
                ("fix_f821_imports.py", "tools/repair/fix_f821_imports.py"),
                ("auto_fix_lint.py", "tools/repair/auto_fix_lint.py"),
            ],
            "Phase 7: 監視ツール": [
                ("continuous_monitor.py", "tools/monitoring/continuous_monitor.py"),
                ("auto_repair_loop.py", "tools/monitoring/auto_repair_loop.py"),
                ("performance_benchmark.py", "tools/monitoring/performance_benchmark.py"),
                ("security_qa_cli.py", "tools/monitoring/security_qa_cli.py"),
                ("analyze_tests.py", "tools/monitoring/analyze_tests.py"),
                ("examine_test_content.py", "tools/monitoring/examine_test_content.py"),
            ],
            "Phase 8: 開発補助ツール": [
                ("setup_system.py", "tools/dev/setup_system.py"),
                ("example_usage.py", "tools/dev/example_usage.py"),
                ("init_demo_db.py", "tools/dev/init_demo_db.py"),
                ("start_web_ui.py", "tools/dev/start_web_ui.py"),
                ("get_test_info.py", "tools/dev/get_test_info.py"),
                ("simple_test_check.py", "tools/dev/simple_test_check.py"),
                ("list_tests.py", "tools/dev/list_tests.py"),
            ],
            "Phase 9: アーカイブ": [
                ("web_ui.py", "archive/web_ui_legacy.py"),
            ],
        }

    def move_file(self, source: str, destination: str) -> bool:
        """ファイルを移動"""
        src_path = self.project_root / source
        dst_path = self.project_root / destination

        if not src_path.exists():
            self.errors.append(f"Source not found: {source}")
            return False

        if self.dry_run:
            print(f"[DRY-RUN] Would move: {source} → {destination}")
            return True

        try:
            # 移動先ディレクトリが存在することを確認
            dst_path.parent.mkdir(parents=True, exist_ok=True)

            # ファイルを移動
            shutil.move(str(src_path), str(dst_path))
            self.moved_files.append((source, destination))
            print(f"Moved: {source} → {destination}")
            return True

        except Exception as e:
            self.errors.append(f"Failed to move {source}: {e}")
            return False

    def update_imports_in_file(self, file_path: Path) -> int:
        """ファイル内のimport文を更新"""
        if not file_path.exists() or not file_path.is_file():
            return 0

        # import置換ルール
        replacements = {
            r"\bfrom web_app import\b": "from app.main import",
            r"\bimport web_app\b": "import app.main as web_app",
            r"\bfrom release_notifier import\b": "from app.cli_notifier import",
            r"\bimport release_notifier\b": "import app.cli_notifier as release_notifier",
            r"\bfrom auth_config import\b": "from auth.config_manager import",
            r"\bimport auth_config\b": "import auth.config_manager as auth_config",
        }

        try:
            content = file_path.read_text(encoding="utf-8")
            original = content
            updates = 0

            for pattern, replacement in replacements.items():
                new_content = re.sub(pattern, replacement, content)
                if new_content != content:
                    updates += re.findall(pattern, content).__len__()
                    content = new_content

            if content != original:
                if self.dry_run:
                    print(f"[DRY-RUN] Would update imports in: {file_path.relative_to(self.project_root)} ({updates} changes)")
                else:
                    file_path.write_text(content, encoding="utf-8")
                    print(f"Updated imports in: {file_path.relative_to(self.project_root)} ({updates} changes)")
                    self.updated_imports.append(str(file_path.relative_to(self.project_root)))

            return updates

        except Exception as e:
            self.errors.append(f"Failed to update imports in {file_path}: {e}")
            return 0

    def update_all_imports(self) -> None:
        """プロジェクト全体のimport文を更新"""
        print("\n=== Updating imports ===")

        # 対象ファイル
        targets = [
            "setup.py",
            "tools/dev/start_web_ui.py",
            "tools/dev/setup_system.py",
            "tests/test_main.py",
            "tests/integration/notification/test_gmail_auth.py",
        ]

        total_updates = 0
        for target in targets:
            file_path = self.project_root / target
            if file_path.exists():
                updates = self.update_imports_in_file(file_path)
                total_updates += updates

        print(f"\nTotal import updates: {total_updates}")

    def create_backup(self) -> str:
        """バックアップを作成"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_root_py_{timestamp}.tar.gz"

        if self.dry_run:
            print(f"[DRY-RUN] Would create backup: {backup_name}")
            return backup_name

        import tarfile

        backup_path = self.project_root / backup_name

        with tarfile.open(backup_path, "w:gz") as tar:
            for py_file in self.project_root.glob("*.py"):
                tar.add(py_file, arcname=py_file.name)

        print(f"Created backup: {backup_name}")
        return backup_name

    def execute_phase(self, phase_name: str, migrations: List[Tuple[str, str]]) -> None:
        """特定のPhaseを実行"""
        print(f"\n{'='*60}")
        print(f"{phase_name}")
        print(f"{'='*60}")

        success = 0
        failed = 0

        for source, destination in migrations:
            if self.move_file(source, destination):
                success += 1
            else:
                failed += 1

        print(f"\n{phase_name} - Success: {success}, Failed: {failed}")

    def generate_report(self) -> str:
        """移行レポートを生成"""
        report = []
        report.append("=" * 60)
        report.append("File Migration Report")
        report.append("=" * 60)
        report.append(f"Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Mode: {'DRY-RUN' if self.dry_run else 'EXECUTE'}")
        report.append("")

        report.append(f"Files Moved: {len(self.moved_files)}")
        for source, dest in self.moved_files:
            report.append(f"  {source} → {dest}")

        report.append("")
        report.append(f"Imports Updated: {len(self.updated_imports)}")
        for file_path in self.updated_imports:
            report.append(f"  {file_path}")

        if self.errors:
            report.append("")
            report.append(f"Errors: {len(self.errors)}")
            for error in self.errors:
                report.append(f"  {error}")

        report.append("")
        report.append("=" * 60)

        return "\n".join(report)

    def run(self, phase: int = None) -> None:
        """移行を実行"""
        # バックアップ作成
        if not self.dry_run:
            self.create_backup()

        # ディレクトリ作成
        self.create_directories()

        # 移行計画取得
        migration_plan = self.get_migration_plan()

        # Phase指定がある場合は該当Phaseのみ実行
        if phase is not None:
            phase_names = list(migration_plan.keys())
            if 0 < phase <= len(phase_names):
                phase_name = phase_names[phase - 1]
                self.execute_phase(phase_name, migration_plan[phase_name])
            else:
                print(f"Error: Invalid phase number {phase} (valid: 1-{len(phase_names)})")
                return
        else:
            # 全Phase実行
            for phase_name, migrations in migration_plan.items():
                self.execute_phase(phase_name, migrations)

        # import更新
        self.update_all_imports()

        # レポート表示
        print("\n" + self.generate_report())

        # レポート保存
        if not self.dry_run:
            report_path = self.project_root / "migration_report.txt"
            report_path.write_text(self.generate_report(), encoding="utf-8")
            print(f"\nReport saved to: migration_report.txt")


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description="Pythonファイル整理・移行スクリプト")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="実際には移動せず、計画のみ表示"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="実際に移行を実行"
    )
    parser.add_argument(
        "--phase",
        type=int,
        help="特定のPhaseのみ実行 (1-9)"
    )

    args = parser.parse_args()

    # プロジェクトルート検出
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent.parent

    print(f"Project Root: {project_root}")
    print(f"Mode: {'EXECUTE' if args.execute else 'DRY-RUN'}")
    print()

    # 実行確認
    if args.execute:
        response = input("Are you sure you want to execute file migration? (yes/no): ")
        if response.lower() != "yes":
            print("Migration cancelled.")
            return

    # 移行実行
    migrator = FileMigrator(project_root, dry_run=not args.execute)
    migrator.run(phase=args.phase)

    # エラーがあれば終了コード1
    if migrator.errors:
        exit(1)


if __name__ == "__main__":
    main()
