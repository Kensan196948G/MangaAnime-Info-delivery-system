"""
F821エラー（未定義名）を自動修正するスクリプト

主な対象:
- typing.List, Dict, Any, Optional, Tupleなどのimport忘れ
- datetime.datetimeのimport忘れ
- その他の標準ライブラリimport忘れ
"""

import re
import subprocess
from pathlib import Path
from typing import List, Dict, Set


def get_f821_errors() -> List[str]:
    """F821エラー一覧を取得"""
    result = subprocess.run(
        ['python', '-m', 'flake8', '--select=F821',
         '--format=%(path)s:%(row)d:%(col)d: %(text)s'],
        capture_output=True,
        text=True
    )
    return result.stdout.strip().split('\n') if result.stdout else []


def analyze_missing_imports(errors: List[str]) -> Dict[str, Set[str]]:
    """各ファイルに必要なimportを分析"""
    file_imports = {}

    for error in errors:
        if not error.strip():
            continue

        # エラーメッセージから情報を抽出
        match = re.match(r"(.+?):(\d+):(\d+): undefined name '(.+?)'", error)
        if not match:
            continue

        file_path = match.group(1)
        undefined_name = match.group(4)

        if file_path not in file_imports:
            file_imports[file_path] = set()

        file_imports[file_path].add(undefined_name)

    return file_imports


def determine_import_source(name: str) -> tuple:
    """未定義名からimport元を決定"""
    typing_names = {
        'List', 'Dict', 'Any', 'Optional', 'Tuple', 'Set',
        'Union', 'Callable', 'Type', 'TypeVar'
    }

    if name in typing_names:
        return ('typing', name)
    elif name == 'datetime':
        return ('datetime', 'datetime')
    elif name == 'timedelta':
        return ('datetime', 'timedelta')
    elif name == 'get_config':
        return ('modules', 'get_config')
    elif name == 'get_db':
        return ('modules', 'get_db')
    elif name == 'random':
        return ('random', None)  # module import
    else:
        return (None, None)


def add_imports_to_file(file_path: str, missing_names: Set[str]) -> bool:
    """ファイルに必要なimportを追加"""
    try:
        content = Path(file_path).read_text(encoding='utf-8')
        lines = content.split('\n')

        # import元ごとにグループ化
        imports_by_module = {}
        module_imports = set()

        for name in missing_names:
            module, item = determine_import_source(name)
            if module is None:
                continue

            if item is None:
                # モジュールimport (import random)
                module_imports.add(module)
            else:
                # from import
                if module not in imports_by_module:
                    imports_by_module[module] = set()
                imports_by_module[module].add(item)

        if not imports_by_module and not module_imports:
            return False

        # 既存のimport行を探す
        import_section_end = 0
        has_typing_import = False
        typing_import_line = -1

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('from typing import'):
                has_typing_import = True
                typing_import_line = i
                import_section_end = i + 1
            elif stripped.startswith(('import ', 'from ')):
                import_section_end = i + 1
            elif stripped and not stripped.startswith('#'):
                # 最初の非import行に到達
                break

        # 新しいimport文を生成
        new_imports = []

        # モジュールimportを追加
        for module in sorted(module_imports):
            if f"import {module}" not in content:
                new_imports.append(f"import {module}")

        # from importを追加
        for module, items in sorted(imports_by_module.items()):
            if module == 'typing' and has_typing_import:
                # 既存のtyping importに追加
                old_line = lines[typing_import_line]
                # 既存のimportを抽出
                match = re.search(r'from typing import (.+)', old_line)
                if match:
                    existing = set(item.strip()
                                   for item in match.group(1).split(','))
                    all_items = existing | items
                    new_line = f"from typing import {', '.join(sorted(all_items))}"
                    lines[typing_import_line] = new_line
            else:
                import_line = f"from {module} import {', '.join(sorted(items))}"
                if import_line not in content:
                    new_imports.append(import_line)

        # 新しいimportを挿入
        if new_imports:
            # docstringの後に挿入
            insert_pos = import_section_end if import_section_end > 0 else 0
            for imp in reversed(new_imports):
                lines.insert(insert_pos, imp)

            new_content = '\n'.join(lines)
            Path(file_path).write_text(new_content, encoding='utf-8')
            return True

        return False

    except Exception as e:
        print(f"[ERROR] {file_path}: {e}")
        return False


def main():
    """メイン処理"""
    print("[FIX F821] 未定義名エラーを修正します...\n")

    # F821エラーを収集
    print("[INFO] F821エラーを収集中...")
    errors = get_f821_errors()
    print(f"       検出: {len(errors)}件\n")

    # ファイルごとに必要なimportを分析
    print("[INFO] 必要なimportを分析中...")
    file_imports = analyze_missing_imports(errors)
    print(f"       対象ファイル: {len(file_imports)}個\n")

    # 各ファイルを修正
    fixed_count = 0
    for file_path, missing_names in file_imports.items():
        if add_imports_to_file(file_path, missing_names):
            fixed_count += 1
            print(f"[OK] import追加: {file_path}")
            print(f"     追加: {', '.join(sorted(missing_names))}")

    # 結果サマリー
    print("\n" + "="*60)
    print(f"[SUMMARY] {fixed_count}ファイル修正完了")
    print("="*60)

    # 修正後のエラー確認
    print("\n[CHECK] 修正後のF821エラー確認...")
    subprocess.run(['python', '-m', 'flake8', '--select=F821',
                    '--statistics', '--count'])


if __name__ == '__main__':
    main()
