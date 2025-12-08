#!/usr/bin/env python3
"""
Googleカレンダー機能調査スクリプト
"""
import os
import logging
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
    logger.info("=" * 80)
    logger.info("Googleカレンダー機能 調査レポート")
    logger.info("=" * 80)

    # 1. Calendar関連ファイル検索
    logger.info("\n[1] Calendar関連ファイル検索")
    calendar_files = find_files("*calendar*", PROJECT_ROOT)
    if calendar_files:
        for f in calendar_files:
            logger.info(f"  - {f}")
    else:
        logger.info("  カレンダー関連ファイルは見つかりませんでした")

    # 2. modules/ディレクトリ確認
    logger.info("\n[2] modules/ディレクトリ構造")
    modules_dir = PROJECT_ROOT / "modules"
    if modules_dir.exists():
        for item in sorted(modules_dir.iterdir()):
            logger.info(f"  - {item.name}")
    else:
        logger.info("  modules/ディレクトリが存在しません")

    # 3. Google認証ファイル確認
    logger.info("\n[3] Google認証ファイル確認")
    credentials_file = PROJECT_ROOT / "credentials.json"
    token_file = PROJECT_ROOT / "token.json"

    logger.info(f"  credentials.json: {'存在' if credentials_file.exists() else '不在'}")
    logger.info(f"  token.json: {'存在' if token_file.exists() else '不在'}")

    # authディレクトリ内も確認
    auth_dir = PROJECT_ROOT / "auth"
    if auth_dir.exists():
        logger.info(f"\n  auth/ディレクトリ内:")
        for item in sorted(auth_dir.iterdir()):
            logger.info(f"    - {item.name}")

    # 4. config.json確認
    logger.info("\n[4] config.json確認")
    config_file = PROJECT_ROOT / "config.json"
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # Google Calendar関連設定を抽出
            if 'google' in config:
                logger.info("  Google設定が存在:")
                logger.info(json.dumps(config['google'], indent=4, ensure_ascii=False))
            else:
                logger.info("  Google設定が見つかりません")
        except Exception as e:
            logger.info(f"  エラー: {e}")
    else:
        logger.info("  config.jsonが存在しません")

    # 5. Pythonファイル内でcalendarキーワード検索
    logger.info("\n[5] Pythonファイル内でcalendarキーワード検索")
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
            logger.info(f"  - {f}")
    else:
        logger.info("  カレンダー関連のコードは見つかりませんでした")

    # 6. backend/app/構造確認
    logger.info("\n[6] プロジェクト構造確認")
    for subdir in ['app', 'backend', 'scripts', 'tests']:
        target_dir = PROJECT_ROOT / subdir
        if target_dir.exists():
            logger.info(f"\n  {subdir}/:")
            items = list(target_dir.iterdir())[:10]  # 最初の10件
            for item in sorted(items):
                logger.info(f"    - {item.name}")

    logger.info("\n" + "=" * 80)
    logger.info("調査完了")
    logger.info("=" * 80)

if __name__ == "__main__":
    main()
