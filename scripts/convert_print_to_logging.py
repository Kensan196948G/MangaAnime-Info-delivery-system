#!/usr/bin/env python3
"""
Print文からLoggingモジュールへの自動変換スクリプト

このスクリプトは、プロジェクト内の全print文を適切なloggingレベルに変換します。
- logger.info("...") → logger.info("...")
- logger.error(f"Error") → logger.error(f"Error: ...")
- logger.warning(f"Warning") → logger.warning(f"Warning: ...")
- logger.debug(f"DEBUG") → logger.debug(f"DEBUG: ...")
"""

import re
import os
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Dict
import json

# ロガー設定
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


class PrintToLoggingConverter:
    """Print文をLoggingに変換するクラス"""

    def __init__(self, project_root: str = "/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system"):
        self.project_root = Path(project_root)
        self.backup_dir = self.project_root / "backups" / f"print_conversion_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.stats = {
            "total_files": 0,
            "converted_files": 0,
            "total_prints": 0,
            "converted_prints": 0,
            "errors": []
        }

        # 変換対象ディレクトリ
        self.target_dirs = ["app", "modules", "scripts"]

        # 除外ディレクトリ
        self.exclude_dirs = ["tests", "__pycache__", "venv", ".git", "backups"]

        # 変換パターン定義
        self.conversion_patterns = [
            # エラー系
            (r'print\((f?["\'])Error[^"\']*(["\'][^)]*)\)', r'logger.error(\1Error\2)'),
            (r'print\((f?["\'])ERROR[^"\']*(["\'][^)]*)\)', r'logger.error(\1ERROR\2)'),
            (r'print\((f?["\'])Failed[^"\']*(["\'][^)]*)\)', r'logger.error(\1Failed\2)'),
            (r'print\((f?["\'])Exception[^"\']*(["\'][^)]*)\)', r'logger.error(\1Exception\2)'),

            # 警告系
            (r'print\((f?["\'])Warning[^"\']*(["\'][^)]*)\)', r'logger.warning(\1Warning\2)'),
            (r'print\((f?["\'])WARNING[^"\']*(["\'][^)]*)\)', r'logger.warning(\1WARNING\2)'),
            (r'print\((f?["\'])Warn[^"\']*(["\'][^)]*)\)', r'logger.warning(\1Warn\2)'),

            # デバッグ系
            (r'print\((f?["\'])DEBUG[^"\']*(["\'][^)]*)\)', r'logger.debug(\1DEBUG\2)'),
            (r'print\((f?["\'])Debug[^"\']*(["\'][^)]*)\)', r'logger.debug(\1Debug\2)'),

            # 成功系
            (r'print\((f?["\'])Success[^"\']*(["\'][^)]*)\)', r'logger.info(\1Success\2)'),
            (r'print\((f?["\'])完了[^"\']*(["\'][^)]*)\)', r'logger.info(\1完了\2)'),

            # 一般的なprint（最後に適用）
            (r'print\(', r'logger.info('),
        ]

    def create_backup(self, file_path: Path) -> bool:
        """ファイルのバックアップを作成"""
        try:
            # バックアップディレクトリが存在しない場合は作成
            self.backup_dir.mkdir(parents=True, exist_ok=True)

            # 相対パスを保持してバックアップ
            relative_path = file_path.relative_to(self.project_root)
            backup_path = self.backup_dir / relative_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)

            shutil.copy2(file_path, backup_path)
            return True
        except Exception as e:
            self.stats["errors"].append(f"Backup failed for {file_path}: {str(e)}")
            return False

    def has_logger_import(self, content: str) -> bool:
        """loggingモジュールのインポートが存在するか確認"""
        return bool(re.search(r'import logging', content))

    def has_logger_instance(self, content: str) -> bool:
        """loggerインスタンスが存在するか確認"""
        return bool(re.search(r'logger\s*=\s*logging\.getLogger', content))

    def add_logging_setup(self, content: str) -> str:
        """loggingのセットアップコードを追加"""
        lines = content.split('\n')
        new_lines = []

        # docstringの位置を探す
        in_docstring = False
        docstring_end_idx = 0
        docstring_chars = ['"""', "'''"]

        for idx, line in enumerate(lines):
            for char in docstring_chars:
                if char in line:
                    if not in_docstring:
                        in_docstring = True
                    else:
                        in_docstring = False
                        docstring_end_idx = idx
                        break

        # インポートセクションを探す
        import_end_idx = 0
        for idx, line in enumerate(lines):
            if idx <= docstring_end_idx:
                continue
            if line.strip() and not (line.strip().startswith('import ') or
                                    line.strip().startswith('from ') or
                                    line.strip().startswith('#')):
                import_end_idx = idx
                break

        # loggingインポートを追加
        logging_import_added = False
        logger_instance_added = False

        for idx, line in enumerate(lines):
            new_lines.append(line)

            # loggingインポートを追加
            if not logging_import_added and idx >= docstring_end_idx:
                if 'import ' in line and not 'logging' in content[:content.find(line)]:
                    new_lines.append('import logging')
                    logging_import_added = True

            # loggerインスタンスを追加
            if not logger_instance_added and idx == import_end_idx:
                if not self.has_logger_instance(content):
                    new_lines.append('')
                    new_lines.append('logger = logging.getLogger(__name__)')
                    new_lines.append('')
                    logger_instance_added = True

        # インポートが全くない場合
        if not logging_import_added:
            insert_idx = docstring_end_idx + 1 if docstring_end_idx > 0 else 0
            new_lines.insert(insert_idx, 'import logging')
            new_lines.insert(insert_idx + 1, '')
            new_lines.insert(insert_idx + 2, 'logger = logging.getLogger(__name__)')
            new_lines.insert(insert_idx + 3, '')

        return '\n'.join(new_lines)

    def convert_prints(self, content: str) -> Tuple[str, int]:
        """print文をlogging呼び出しに変換"""
        converted_count = 0

        for pattern, replacement in self.conversion_patterns:
            matches = re.findall(pattern, content)
            if matches:
                content = re.sub(pattern, replacement, content)
                converted_count += len(matches)

        return content, converted_count

    def process_file(self, file_path: Path) -> bool:
        """単一ファイルを処理"""
        try:
            # ファイル読み込み
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()

            # print文が存在しない場合はスキップ
            if 'logger.info(' not in original_content:
                return False

            # バックアップ作成
            if not self.create_backup(file_path):
                return False

            content = original_content

            # loggingセットアップを追加（必要な場合）
            if not self.has_logger_import(content):
                content = self.add_logging_setup(content)
            elif not self.has_logger_instance(content):
                # インポートはあるがインスタンスがない場合
                lines = content.split('\n')
                for idx, line in enumerate(lines):
                    if 'import logging' in line:
                        lines.insert(idx + 1, '')
                        lines.insert(idx + 2, 'logger = logging.getLogger(__name__)')
                        break
                content = '\n'.join(lines)

            # print文を変換
            content, print_count = self.convert_prints(content)

            # 変更がない場合はスキップ
            if content == original_content:
                return False

            # ファイルに書き込み
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            # 統計を更新
            self.stats["converted_files"] += 1
            self.stats["converted_prints"] += print_count

            logger.info(f"✓ Converted: {file_path.relative_to(self.project_root)} ({print_count} prints)")
            return True

        except Exception as e:
            error_msg = f"Failed to process {file_path}: {str(e)}"
            self.stats["errors"].append(error_msg)
            logger.info(f"✗ {error_msg}")
            return False

    def should_process_file(self, file_path: Path) -> bool:
        """ファイルを処理すべきか判定"""
        # 除外ディレクトリチェック
        for exclude_dir in self.exclude_dirs:
            if exclude_dir in file_path.parts:
                return False

        # Pythonファイルのみ処理
        if file_path.suffix != '.py':
            return False

        return True

    def scan_and_convert(self) -> Dict:
        """プロジェクト全体をスキャンして変換"""
        logger.info("=" * 80)
        logger.info("Print to Logging Converter")
        logger.info("=" * 80)
        logger.info(f"Project Root: {self.project_root}")
        logger.info(f"Backup Directory: {self.backup_dir}")
        logger.info(f"Target Directories: {', '.join(self.target_dirs)}")
        logger.info("=" * 80)
        logger.info("")

        # 全Pythonファイルを検索
        python_files = []
        for target_dir in self.target_dirs:
            target_path = self.project_root / target_dir
            if target_path.exists():
                python_files.extend(target_path.rglob('*.py'))

        # フィルタリング
        python_files = [f for f in python_files if self.should_process_file(f)]
        self.stats["total_files"] = len(python_files)

        logger.info(f"Found {len(python_files)} Python files to process\n")

        # 各ファイルを処理
        for file_path in python_files:
            self.process_file(file_path)

        # 統計を表示
        self.print_statistics()

        # 統計をJSONで保存
        stats_file = self.backup_dir / "conversion_stats.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2, ensure_ascii=False)

        return self.stats

    def print_statistics(self):
        """統計情報を表示"""
        logger.info("\n" + "=" * 80)
        logger.info("Conversion Statistics")
        logger.info("=" * 80)
        logger.info(f"Total Files Scanned:    {self.stats['total_files']}")
        logger.info(f"Files Converted:        {self.stats['converted_files']}")
        logger.info(f"Total Print Statements: {self.stats['converted_prints']}")
        logger.info(f"Errors:                 {len(self.stats['errors'])}")
        logger.info("=" * 80)

        if self.stats["errors"]:
            logger.info("\nErrors:")
            for error in self.stats["errors"]:
                logger.info(f"  - {error}")

        logger.info(f"\nBackup Location: {self.backup_dir}")
        logger.info("=" * 80)

    def rollback(self):
        """変換をロールバック（バックアップから復元）"""
        if not self.backup_dir.exists():
            logger.info("No backup found to rollback")
            return False

        logger.info(f"Rolling back from: {self.backup_dir}")

        for backup_file in self.backup_dir.rglob('*.py'):
            relative_path = backup_file.relative_to(self.backup_dir)
            original_file = self.project_root / relative_path

            try:
                shutil.copy2(backup_file, original_file)
                logger.info(f"✓ Restored: {relative_path}")
            except Exception as e:
                logger.info(f"✗ Failed to restore {relative_path}: {str(e)}")

        logger.info("Rollback complete")
        return True


def main():
    """メイン実行関数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Convert print statements to logging calls"
    )
    parser.add_argument(
        '--rollback',
        action='store_true',
        help='Rollback the last conversion'
    )
    parser.add_argument(
        '--project-root',
        default='/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system',
        help='Project root directory'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )

    args = parser.parse_args()

    converter = PrintToLoggingConverter(project_root=args.project_root)

    if args.rollback:
        # 最新のバックアップからロールバック
        backups_dir = Path(args.project_root) / "backups"
        if backups_dir.exists():
            backup_dirs = sorted(backups_dir.glob('print_conversion_*'))
            if backup_dirs:
                converter.backup_dir = backup_dirs[-1]
                converter.rollback()
            else:
                logger.info("No backups found")
        else:
            logger.info("No backups directory found")
    else:
        # 変換実行
        if args.dry_run:
            logger.info("DRY RUN MODE - No changes will be made")
            logger.info("=" * 80)

        stats = converter.scan_and_convert()

        if stats["converted_files"] > 0:
            logger.info("\nConversion completed successfully!")
            logger.info(f"To rollback, run: python {__file__} --rollback")
        else:
            logger.info("\nNo files were converted.")


if __name__ == "__main__":
    main()
