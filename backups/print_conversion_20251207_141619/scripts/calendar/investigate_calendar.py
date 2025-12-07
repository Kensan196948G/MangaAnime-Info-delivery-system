#!/usr/bin/env python3
"""
Googleカレンダー機能調査スクリプト
"""
import os
import json
from pathlib import Path

PROJECT_ROOT = Path("/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system")

def find_files(pattern, root_dir):
    """ファイルを再帰的に検索"""
    result = []
    for path in Path(root_dir).rglob(pattern):
        result.append(str(path))
    return result

def main():
    print("=" * 80)
    print("Googleカレンダー機能 調査レポート")
    print("=" * 80)

    # 1. Calendar関連ファイル検索
    print("\n[1] Calendar関連ファイル検索")
    calendar_files = find_files("*calendar*", PROJECT_ROOT)
    if calendar_files:
        for f in calendar_files:
            print(f"  - {f}")
    else:
        print("  カレンダー関連ファイルは見つかりませんでした")

    # 2. modules/ディレクトリ確認
    print("\n[2] modules/ディレクトリ構造")
    modules_dir = PROJECT_ROOT / "modules"
    if modules_dir.exists():
        for item in sorted(modules_dir.iterdir()):
            print(f"  - {item.name}")
    else:
        print("  modules/ディレクトリが存在しません")

    # 3. Google認証ファイル確認
    print("\n[3] Google認証ファイル確認")
    credentials_file = PROJECT_ROOT / "credentials.json"
    token_file = PROJECT_ROOT / "token.json"

    print(f"  credentials.json: {'存在' if credentials_file.exists() else '不在'}")
    print(f"  token.json: {'存在' if token_file.exists() else '不在'}")

    # authディレクトリ内も確認
    auth_dir = PROJECT_ROOT / "auth"
    if auth_dir.exists():
        print(f"\n  auth/ディレクトリ内:")
        for item in sorted(auth_dir.iterdir()):
            print(f"    - {item.name}")

    # 4. config.json確認
    print("\n[4] config.json確認")
    config_file = PROJECT_ROOT / "config.json"
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # Google Calendar関連設定を抽出
            if 'google' in config:
                print("  Google設定が存在:")
                print(json.dumps(config['google'], indent=4, ensure_ascii=False))
            else:
                print("  Google設定が見つかりません")
        except Exception as e:
            print(f"  エラー: {e}")
    else:
        print("  config.jsonが存在しません")

    # 5. Pythonファイル内でcalendarキーワード検索
    print("\n[5] Pythonファイル内でcalendarキーワード検索")
    python_files = find_files("*.py", PROJECT_ROOT / "modules")
    calendar_mentions = []

    for py_file in python_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'calendar' in content.lower():
                    calendar_mentions.append(py_file)
        except:
            pass

    if calendar_mentions:
        for f in calendar_mentions:
            print(f"  - {f}")
    else:
        print("  カレンダー関連のコードは見つかりませんでした")

    # 6. backend/app/構造確認
    print("\n[6] プロジェクト構造確認")
    for subdir in ['app', 'backend', 'scripts', 'tests']:
        target_dir = PROJECT_ROOT / subdir
        if target_dir.exists():
            print(f"\n  {subdir}/:")
            items = list(target_dir.iterdir())[:10]  # 最初の10件
            for item in sorted(items):
                print(f"    - {item.name}")

    print("\n" + "=" * 80)
    print("調査完了")
    print("=" * 80)

if __name__ == "__main__":
    main()
