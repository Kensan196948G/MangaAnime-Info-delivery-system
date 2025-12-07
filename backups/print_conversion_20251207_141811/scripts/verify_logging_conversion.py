#!/usr/bin/env python3
"""
Logging変換検証スクリプト

print文からloggingへの変換が正しく行われたかを検証します。
- 残存print文の検出
- logging設定の確認
- 変換品質のレポート生成
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple
import json
from datetime import datetime


class LoggingConversionVerifier:
    """Logging変換の検証クラス"""

    def __init__(self, project_root: str = "/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system"):
        self.project_root = Path(project_root)
        self.target_dirs = ["app", "modules", "scripts"]
        self.exclude_dirs = ["tests", "__pycache__", "venv", ".git", "backups"]

        self.results = {
            "total_files": 0,
            "files_with_prints": 0,
            "files_without_logger": 0,
            "total_print_statements": 0,
            "issues": [],
            "summary": {}
        }

    def should_check_file(self, file_path: Path) -> bool:
        """ファイルをチェックすべきか判定"""
        for exclude_dir in self.exclude_dirs:
            if exclude_dir in file_path.parts:
                return False

        if file_path.suffix != '.py':
            return False

        return True

    def find_print_statements(self, content: str) -> List[Tuple[int, str]]:
        """print文を検出"""
        prints = []
        lines = content.split('\n')

        for line_num, line in enumerate(lines, 1):
            # コメント内のprintは除外
            if line.strip().startswith('#'):
                continue

            # 文字列内のprintは除外（単純な実装）
            if 'logger.info(' in line:
                # docstring内かチェック
                stripped = line.strip()
                if not (stripped.startswith('"""') or stripped.startswith("'''")):
                    prints.append((line_num, line.strip()))

        return prints

    def has_logging_import(self, content: str) -> bool:
        """loggingインポートの確認"""
        return bool(re.search(r'import logging', content))

logger = logging.getLogger(__name__)

    def has_logger_instance(self, content: str) -> bool:
        """loggerインスタンスの確認"""
        return bool(re.search(r'logger\s*=\s*logging\.getLogger', content))

    def count_logging_calls(self, content: str) -> Dict[str, int]:
        """logging呼び出しをカウント"""
        levels = {
            'debug': len(re.findall(r'logger\.debug\(', content)),
            'info': len(re.findall(r'logger\.info\(', content)),
            'warning': len(re.findall(r'logger\.warning\(', content)),
            'error': len(re.findall(r'logger\.error\(', content)),
            'critical': len(re.findall(r'logger\.critical\(', content)),
        }
        levels['total'] = sum(levels.values())
        return levels

    def verify_file(self, file_path: Path) -> Dict:
        """単一ファイルの検証"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            result = {
                'file': str(file_path.relative_to(self.project_root)),
                'has_logging_import': self.has_logging_import(content),
                'has_logger_instance': self.has_logger_instance(content),
                'print_statements': self.find_print_statements(content),
                'logging_calls': self.count_logging_calls(content),
                'issues': []
            }

            # 問題の検出
            if result['print_statements']:
                result['issues'].append({
                    'type': 'PRINT_FOUND',
                    'count': len(result['print_statements']),
                    'lines': [line_num for line_num, _ in result['print_statements']]
                })
                self.results['files_with_prints'] += 1
                self.results['total_print_statements'] += len(result['print_statements'])

            if result['logging_calls']['total'] > 0 and not result['has_logger_instance']:
                result['issues'].append({
                    'type': 'MISSING_LOGGER_INSTANCE',
                    'message': 'Uses logging but missing logger instance'
                })
                self.results['files_without_logger'] += 1

            if result['logging_calls']['total'] > 0 and not result['has_logging_import']:
                result['issues'].append({
                    'type': 'MISSING_LOGGING_IMPORT',
                    'message': 'Uses logging but missing import'
                })

            return result

        except Exception as e:
            return {
                'file': str(file_path.relative_to(self.project_root)),
                'error': str(e)
            }

    def scan_project(self) -> Dict:
        """プロジェクト全体をスキャン"""
        logger.info("=" * 80)
        logger.info("Logging Conversion Verification")
        logger.info("=" * 80)
        logger.info(f"Project Root: {self.project_root}")
        logger.info(f"Target Directories: {', '.join(self.target_dirs)}")
        logger.info("=" * 80)
        logger.info()

        # 全Pythonファイルを検索
        python_files = []
        for target_dir in self.target_dirs:
            target_path = self.project_root / target_dir
            if target_path.exists():
                python_files.extend(target_path.rglob('*.py'))

        python_files = [f for f in python_files if self.should_check_file(f)]
        self.results['total_files'] = len(python_files)

        logger.info(f"Scanning {len(python_files)} Python files...\n")

        # 各ファイルを検証
        for file_path in python_files:
            result = self.verify_file(file_path)

            if result.get('issues'):
                self.results['issues'].append(result)
                logger.info(f"⚠ Issues found: {result['file']}")
                for issue in result['issues']:
                    logger.info(f"  - {issue['type']}")
                    if 'lines' in issue:
                        logger.info(f"    Lines: {', '.join(map(str, issue['lines'][:5]))}" +
                              (f" ... (+{len(issue['lines'])-5} more)" if len(issue['lines']) > 5 else ""))

        # サマリー生成
        self.generate_summary()

        return self.results

    def generate_summary(self):
        """検証サマリーを生成"""
        total_files = self.results['total_files']
        files_with_issues = len(self.results['issues'])
        files_clean = total_files - files_with_issues

        self.results['summary'] = {
            'total_files': total_files,
            'files_clean': files_clean,
            'files_with_issues': files_with_issues,
            'total_print_statements': self.results['total_print_statements'],
            'files_with_prints': self.results['files_with_prints'],
            'files_without_logger': self.results['files_without_logger'],
            'success_rate': f"{(files_clean / total_files * 100):.2f}%" if total_files > 0 else "N/A"
        }

    def print_report(self):
        """検証レポートを表示"""
        logger.info("\n" + "=" * 80)
        logger.info("Verification Report")
        logger.info("=" * 80)

        summary = self.results['summary']
        logger.info(f"Total Files Scanned:        {summary['total_files']}")
        logger.info(f"Files Clean:                {summary['files_clean']}")
        logger.info(f"Files with Issues:          {summary['files_with_issues']}")
        logger.info(f"Success'success_rate']}")
        logger.info()
        logger.info(f"Remaining Print Statements: {summary['total_print_statements']}")
        logger.info(f"Files with Prints:          {summary['files_with_prints']}")
        logger.info(f"Files without Logger:       {summary['files_without_logger']}")
        logger.info("=" * 80)

        if self.results['files_with_prints'] > 0:
            logger.info("\n⚠ WARNING: Print statements still found in the following files:")
            for issue in self.results['issues']:
                if any(i['type'] == 'PRINT_FOUND' for i in issue['issues']):
                    logger.info(f"  - {issue['file']}")

        if self.results['total_print_statements'] == 0:
            logger.info("\n✓ SUCCESS: All print statements have been converted to logging!")
        else:
            logger.info(f"\n✗ INCOMPLETE: {self.results['total_print_statements']} print statements remain")

        logger.info("=" * 80)

    def save_report(self, output_file: str = None):
        """レポートをJSONで保存"""
        if output_file is None:
            output_file = self.project_root / f"logging_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        logger.info(f"\nDetailed report saved to: {output_file}")

    def generate_fix_script(self, output_file: str = None):
        """残存print文を修正するスクリプトを生成"""
        if self.results['total_print_statements'] == 0:
            logger.info("No print statements to fix")
            return

        if output_file is None:
            output_file = self.project_root / "scripts" / "fix_remaining_prints.py"

        script_content = """#!/usr/bin/env python3
# Auto-generated script to fix remaining print statements

import re
from pathlib import Path

files_to_fix = {
"""

        for issue in self.results['issues']:
            if any(i['type'] == 'PRINT_FOUND' for i in issue['issues']):
                script_content += f'    "{issue["file"]}": [\n'
                for line_num, line in issue['print_statements']:
                    script_content += f'        ({line_num}, r"""{line}"""),\n'
                script_content += '    ],\n'

        script_content += """
}

# Add conversion logic here
logger.info(f"Found {len(files_to_fix)} files with print statements to fix")
"""

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(script_content)

        logger.info(f"Fix script generated: {output_file}")


def main():
    """メイン実行関数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Verify print to logging conversion"
    )
    parser.add_argument(
        '--project-root',
        default='/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system',
        help='Project root directory'
    )
    parser.add_argument(
        '--save-report',
        action='store_true',
        help='Save detailed report as JSON'
    )
    parser.add_argument(
        '--generate-fix',
        action='store_true',
        help='Generate script to fix remaining issues'
    )

    args = parser.parse_args()

    verifier = LoggingConversionVerifier(project_root=args.project_root)
    verifier.scan_project()
    verifier.print_report()

    if args.save_report:
        verifier.save_report()

    if args.generate_fix:
        verifier.generate_fix_script()


if __name__ == "__main__":
    main()
