#!/usr/bin/env python3
"""
エラー検知スクリプト - 自動修復システム用

機能:
- Python構文エラー検知
- インポートエラー検知
- セキュリティスキャン
- 型チェック (オプション)
- 結果のJSON/Markdown出力

使用方法:
    python scripts/detect_errors.py [--format json|markdown] [--output FILE]
"""

import ast
import json
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class ErrorReport:
    """エラーレポートのデータクラス"""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    syntax_errors: list = field(default_factory=list)
    import_errors: list = field(default_factory=list)
    security_issues: list = field(default_factory=list)
    type_errors: list = field(default_factory=list)

    @property
    def total_errors(self) -> int:
        return (
            len(self.syntax_errors) +
            len(self.import_errors) +
            len([i for i in self.security_issues if i.get('severity') == 'HIGH'])
        )

    @property
    def has_critical_errors(self) -> bool:
        return self.total_errors > 0

    def to_dict(self) -> dict:
        return {
            'timestamp': self.timestamp,
            'total_errors': self.total_errors,
            'has_critical_errors': self.has_critical_errors,
            'syntax_errors': self.syntax_errors,
            'import_errors': self.import_errors,
            'security_issues': self.security_issues,
            'type_errors': self.type_errors,
        }

    def to_markdown(self) -> str:
        md = f"""# 🔍 エラー検知レポート

**生成日時**: {self.timestamp}
**総エラー数**: {self.total_errors}
**クリティカル**: {'あり ❌' if self.has_critical_errors else 'なし ✅'}

---

## 📊 サマリー

| カテゴリ | 件数 | ステータス |
|---------|------|----------|
| 構文エラー | {len(self.syntax_errors)} | {'❌' if self.syntax_errors else '✅'} |
| インポートエラー | {len(self.import_errors)} | {'❌' if self.import_errors else '✅'} |
| セキュリティ(High) | {len([i for i in self.security_issues if i.get('severity') == 'HIGH'])} | {'❌' if any(i.get('severity') == 'HIGH' for i in self.security_issues) else '✅'} |
| 型エラー | {len(self.type_errors)} | {'⚠️' if self.type_errors else '✅'} |

"""

        if self.syntax_errors:
            md += "\n## ❌ 構文エラー\n\n"
            for err in self.syntax_errors:
                md += f"- `{err['file']}:{err.get('line', '?')}` - {err.get('message', 'Unknown error')}\n"

        if self.import_errors:
            md += "\n## ❌ インポートエラー\n\n"
            for err in self.import_errors:
                md += f"- `{err['file']}` - {err.get('message', 'Import error')}\n"

        if self.security_issues:
            md += "\n## 🔒 セキュリティ問題\n\n"
            for issue in self.security_issues:
                severity = issue.get('severity', 'Unknown')
                icon = '🔴' if severity == 'HIGH' else '🟡' if severity == 'MEDIUM' else '🟢'
                md += f"- {icon} [{severity}] `{issue.get('file', '?')}:{issue.get('line', '?')}` - {issue.get('issue', 'Unknown')}\n"

        if self.type_errors:
            md += "\n## ⚠️ 型エラー\n\n"
            for err in self.type_errors:
                md += f"- `{err['file']}:{err.get('line', '?')}` - {err.get('message', 'Type error')}\n"

        md += "\n---\n🤖 Auto Repair System\n"
        return md


def find_python_files(directories: list[str]) -> list[Path]:
    """指定ディレクトリ内のPythonファイルを検索"""
    files = []
    for dir_name in directories:
        dir_path = Path(dir_name)
        if dir_path.exists():
            files.extend(dir_path.rglob('*.py'))
    return files


def check_syntax_errors(files: list[Path]) -> list[dict]:
    """構文エラーをチェック"""
    errors = []
    for file in files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                source = f.read()
            ast.parse(source)
        except SyntaxError as e:
            errors.append({
                'file': str(file),
                'line': e.lineno,
                'column': e.offset,
                'message': str(e.msg),
                'text': e.text.strip() if e.text else None,
            })
        except Exception as e:
            errors.append({
                'file': str(file),
                'message': str(e),
            })
    return errors


def check_import_errors(files: list[Path]) -> list[dict]:
    """インポートエラーをチェック"""
    errors = []
    for file in files:
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'py_compile', str(file)],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                errors.append({
                    'file': str(file),
                    'message': result.stderr.strip() or 'Compilation error',
                })
        except subprocess.TimeoutExpired:
            errors.append({
                'file': str(file),
                'message': 'Timeout during compilation',
            })
        except Exception as e:
            errors.append({
                'file': str(file),
                'message': str(e),
            })
    return errors


def run_security_scan(directories: list[str]) -> list[dict]:
    """Banditでセキュリティスキャン"""
    issues = []
    try:
        result = subprocess.run(
            ['bandit', '-r'] + directories + ['-f', 'json', '-ll'],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.stdout:
            data = json.loads(result.stdout)
            for issue in data.get('results', []):
                issues.append({
                    'file': issue.get('filename', '?'),
                    'line': issue.get('line_number', 0),
                    'severity': issue.get('issue_severity', 'UNKNOWN'),
                    'confidence': issue.get('issue_confidence', 'UNKNOWN'),
                    'issue': issue.get('issue_text', 'Unknown issue'),
                    'test_id': issue.get('test_id', ''),
                })
    except FileNotFoundError:
        print("⚠️ Banditがインストールされていません: pip install bandit", file=sys.stderr)
    except subprocess.TimeoutExpired:
        print("⚠️ セキュリティスキャンがタイムアウトしました", file=sys.stderr)
    except json.JSONDecodeError:
        print("⚠️ セキュリティスキャン結果の解析に失敗しました", file=sys.stderr)
    except Exception as e:
        print(f"⚠️ セキュリティスキャンエラー: {e}", file=sys.stderr)
    return issues


def run_type_check(directories: list[str]) -> list[dict]:
    """mypyで型チェック（オプション）"""
    errors = []
    try:
        result = subprocess.run(
            ['mypy'] + directories + ['--ignore-missing-imports', '--no-error-summary'],
            capture_output=True,
            text=True,
            timeout=120,
        )
        for line in result.stdout.strip().split('\n'):
            if line and ':' in line:
                parts = line.split(':', 3)
                if len(parts) >= 4:
                    errors.append({
                        'file': parts[0],
                        'line': int(parts[1]) if parts[1].isdigit() else 0,
                        'column': int(parts[2]) if parts[2].isdigit() else 0,
                        'message': parts[3].strip(),
                    })
    except FileNotFoundError:
        print("ℹ️ mypyがインストールされていません（スキップ）", file=sys.stderr)
    except subprocess.TimeoutExpired:
        print("⚠️ 型チェックがタイムアウトしました", file=sys.stderr)
    except Exception as e:
        print(f"⚠️ 型チェックエラー: {e}", file=sys.stderr)
    return errors


def main():
    import argparse

    parser = argparse.ArgumentParser(description='エラー検知スクリプト')
    parser.add_argument('--format', choices=['json', 'markdown'], default='markdown',
                        help='出力形式 (default: markdown)')
    parser.add_argument('--output', '-o', type=str, help='出力ファイル')
    parser.add_argument('--directories', '-d', nargs='+', default=['app', 'modules'],
                        help='検査対象ディレクトリ (default: app modules)')
    parser.add_argument('--skip-security', action='store_true', help='セキュリティスキャンをスキップ')
    parser.add_argument('--skip-types', action='store_true', help='型チェックをスキップ')

    args = parser.parse_args()

    print("🔍 エラー検知を開始します...", file=sys.stderr)

    # Pythonファイルを検索
    files = find_python_files(args.directories)
    print(f"📁 {len(files)} ファイルを検査します", file=sys.stderr)

    # レポート作成
    report = ErrorReport()

    # 構文エラーチェック
    print("🔍 構文エラーをチェック中...", file=sys.stderr)
    report.syntax_errors = check_syntax_errors(files)

    # インポートエラーチェック
    print("🔍 インポートエラーをチェック中...", file=sys.stderr)
    report.import_errors = check_import_errors(files)

    # セキュリティスキャン
    if not args.skip_security:
        print("🔒 セキュリティスキャン中...", file=sys.stderr)
        report.security_issues = run_security_scan(args.directories)

    # 型チェック
    if not args.skip_types:
        print("📝 型チェック中...", file=sys.stderr)
        report.type_errors = run_type_check(args.directories)

    # 結果出力
    if args.format == 'json':
        output = json.dumps(report.to_dict(), indent=2, ensure_ascii=False)
    else:
        output = report.to_markdown()

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"📄 結果を {args.output} に保存しました", file=sys.stderr)
    else:
        print(output)

    # 終了コード
    if report.has_critical_errors:
        print(f"\n❌ クリティカルエラー {report.total_errors} 件検出", file=sys.stderr)
        sys.exit(1)
    else:
        print("\n✅ クリティカルエラーなし", file=sys.stderr)
        sys.exit(0)


if __name__ == '__main__':
    main()
