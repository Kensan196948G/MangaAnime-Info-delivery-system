"""
Lintエラー自動修正スクリプト

自動修正対象:
- W291: 末尾の余分なスペース
- W293: 空白行の余分なスペース
- F401: 未使用のimport文
- F541: プレースホルダーのないf-string
"""

import re
import subprocess
from pathlib import Path
from typing import List


def run_flake8() -> List[str]:
    """Flake8を実行してエラー一覧を取得"""
    result = subprocess.run(
        ['python', '-m', 'flake8', '--format=%(path)s:%(row)d:%(col)d: '
         '%(code)s %(text)s'],
        capture_output=True,
        text=True
    )
    return result.stdout.strip().split('\n') if result.stdout else []


def fix_trailing_whitespace(file_path: Path) -> int:
    """W291, W293エラーを修正（末尾空白と空白行のスペース）"""
    content = file_path.read_text(encoding='utf-8')
    original = content

    # 末尾の余分なスペースを削除
    lines = content.split('\n')
    fixed_lines = [line.rstrip() for line in lines]
    content = '\n'.join(fixed_lines)

    if content != original:
        file_path.write_text(content, encoding='utf-8')
        return 1
    return 0


def fix_f541_fstring(file_path: Path) -> int:
    """F541エラーを修正（プレースホルダーのないf-stringを通常文字列に）"""
    content = file_path.read_text(encoding='utf-8')
    original = content

    # "..."または'...'でプレースホルダー{}がないものを通常文字列に変換
    # シンプルなケースのみ対応
    pattern = r'f(["\'])([^"\']*?)\1'

    def replace_if_no_placeholder(match):
        quote = match.group(1)
        text = match.group(2)
        # プレースホルダー（{...}）が含まれていない場合のみ変換
        if '{' not in text and '}' not in text:
            return f'{quote}{text}{quote}'
        return match.group(0)

    content = re.sub(pattern, replace_if_no_placeholder, content)

    if content != original:
        file_path.write_text(content, encoding='utf-8')
        return 1
    return 0


def fix_f401_unused_import(file_path: Path, errors: List[str]) -> int:
    """F401エラーを修正（未使用のimport文を削除）"""
    # このファイルに関連するF401エラーを抽出
    file_errors = [e for e in errors if str(file_path) in e and 'F401' in e]
    if not file_errors:
        return 0

    content = file_path.read_text(encoding='utf-8')
    lines = content.split('\n')

    # 削除すべき行番号を収集
    lines_to_remove = set()
    for error in file_errors:
        match = re.search(r':(\d+):\d+: F401', error)
        if match:
            line_num = int(match.group(1)) - 1  # 0-indexed
            lines_to_remove.add(line_num)

    if not lines_to_remove:
        return 0

    # 未使用importを含む行を削除
    new_lines = []
    for i, line in enumerate(lines):
        if i not in lines_to_remove:
            new_lines.append(line)

    new_content = '\n'.join(new_lines)
    if new_content != content:
        file_path.write_text(new_content, encoding='utf-8')
        return 1
    return 0


def get_python_files() -> List[Path]:
    """修正対象のPythonファイル一覧を取得"""
    root = Path('.')
    python_files = []

    # 主要なPythonファイルを収集
    patterns = [
        '*.py',
        'modules/**/*.py',
        'tests/**/*.py',
        'scripts/**/*.py'
    ]

    for pattern in patterns:
        python_files.extend(root.glob(pattern))

    # 除外パターン
    exclude = {'.venv', 'venv', '__pycache__', '.git', 'node_modules'}

    return [
        f for f in python_files
        if not any(part in exclude for part in f.parts)
    ]


def main():
    """メイン処理"""
    print("[LINT FIX] Lintエラー自動修正を開始します...\n")

    # Flake8エラーを取得
    print("[INFO] Flake8エラーを収集中...")
    errors = run_flake8()
    print(f"       検出: {len(errors)}件\n")

    # Pythonファイル一覧を取得
    python_files = get_python_files()
    print(f"[INFO] 対象ファイル: {len(python_files)}個\n")

    # 修正カウンター
    stats = {
        'W291/W293': 0,
        'F541': 0,
        'F401': 0
    }

    # 各ファイルを修正
    for file_path in python_files:
        try:
            # W291, W293を修正
            if fix_trailing_whitespace(file_path):
                stats['W291/W293'] += 1
                print(f"[OK] W291/W293修正: {file_path}")

            # F541を修正
            if fix_f541_fstring(file_path):
                stats['F541'] += 1
                print(f"[OK] F541修正: {file_path}")

            # F401を修正
            if fix_f401_unused_import(file_path, errors):
                stats['F401'] += 1
                print(f"[OK] F401修正: {file_path}")

        except Exception as e:
            print(f"[WARN] エラー ({file_path}): {e}")

    # 結果サマリー
    print("\n" + "="*60)
    print("[SUMMARY] 修正結果サマリー")
    print("="*60)
    for error_type, count in stats.items():
        print(f"  {error_type}: {count}ファイル")
    print(f"  合計: {sum(stats.values())}ファイル修正")
    print("="*60)

    # 修正後のFlake8結果
    print("\n[CHECK] 修正後のFlake8チェック...")
    subprocess.run(['python', '-m', 'flake8', '--statistics', '--count'])


if __name__ == '__main__':
    main()
