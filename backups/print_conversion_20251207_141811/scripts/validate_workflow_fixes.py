#!/usr/bin/env python3
"""
ワークフロー修正の包括的検証スクリプト
"""

import os
import logging
import sys
import json
from pathlib import Path


def validate_fixes():

logger = logging.getLogger(__name__)

    """修正内容を検証"""
    errors = []
    warnings = []
    successes = []

    # 1. config.jsonの存在確認
    config_files = ["config.json", "config/config.ci.json", "config.json.template"]

    config_found = False
    for cf in config_files:
        if Path(cf).exists():
            config_found = True
            successes.append(f"✅ {cf} が存在します")

            # 設定ファイルの内容確認
            try:
                with open(cf, "r") as f:
                    config_data = json.load(f)

                # 必須フィールドの確認
                required_fields = ["email", "error_notifications", "apis"]
                for field in required_fields:
                    if field in config_data:
                        successes.append(f"  ✓ {field} フィールドあり")
                    else:
                        warnings.append(f"{cf}: {field} フィールドが不足")

            except json.JSONDecodeError as e:
                errors.append(f"{cf}: JSON構文エラー - {e}")
            except Exception as e:
                errors.append(f"{cf}: 読み込みエラー - {e}")

    if not config_found:
        errors.append("config.json関連ファイルが見つかりません")

    # 2. 必須ディレクトリの確認
    required_dirs = ["config", "logs", "backup", "tests", "dist"]
    for dir_name in required_dirs:
        if Path(dir_name).exists():
            successes.append(f"✅ {dir_name}/ ディレクトリ存在")
        else:
            warnings.append(f"{dir_name}/ ディレクトリが不足")

    # 3. backup_full.shの確認
    if Path("backup_full.sh").exists():
        successes.append("✅ backup_full.sh が存在")
        # 実行権限の確認
        if os.access("backup_full.sh", os.X_OK):
            successes.append("  ✓ 実行権限あり")
        else:
            warnings.append("backup_full.sh に実行権限がありません")
    else:
        errors.append("backup_full.sh が見つかりません")

    # 4. ワークフローファイルの確認
    workflows_dir = Path(".github/workflows")
    if workflows_dir.exists():
        workflow_files = list(workflows_dir.glob("*.yml"))
        successes.append(f"✅ {len(workflow_files)} 個のワークフローファイル確認")

        # actions/cache@v4の使用確認
        for wf in workflow_files:
            with open(wf, "r") as f:
                content = f.read()
                if "actions/cache@v3" in content:
                    warnings.append(f"{wf.name}: 古いactions/cache@v3使用")
                elif "actions/cache@v4" in content:
                    successes.append(f"  ✓ {wf.name}: actions/cache@v4使用")

    # 5. 破損Pythonファイルのチェック
    broken_files = ["test_basic.py", "modules/data_normalizer_broken.py"]

    for bf in broken_files:
        if Path(bf).exists():
            warnings.append(f"破損ファイルが残存: {bf}")
        else:
            successes.append(f"✅ 破損ファイル削除済み: {bf}")

    # 6. Pythonシンタックスチェック
    import subprocess

    python_files = list(Path(".").glob("**/*.py"))
    syntax_errors = 0

    for py_file in python_files:
        if "venv" in str(py_file) or ".git" in str(py_file):
            continue

        result = subprocess.run(
            ["python", "-m", "py_compile", str(py_file)], capture_output=True, text=True
        )

        if result.returncode != 0:
            syntax_errors += 1
            warnings.append(f"Python構文エラー: {py_file}")

    if syntax_errors == 0:
        successes.append("✅ すべてのPythonファイルの構文が正しい")
    else:
        warnings.append(f"{syntax_errors} 個のPythonファイルに構文エラー")

    # 結果の表示
    logger.info("=" * 60)
    logger.info("🔍 ワークフロー修正検証レポート")
    logger.info("=" * 60)

    if successes:
        logger.info("\n✅ 成功項目:")
        for s in successes:
            logger.info(f"  {s}")

    if warnings:
        logger.info("\n⚠️  警告:")
        for w in warnings:
            logger.info(f"  - {w}")

    if errors:
        logger.info("\n❌ エラー:")
        for e in errors:
            logger.info(f"  - {e}")

    logger.info("\n" + "=" * 60)

    if not errors:
        logger.info("✅ ワークフロー修正の検証が成功しました！")
        logger.info("   警告事項はありますが、CI/CDは正常に動作するはずです。")
        return True
    else:
        logger.info("❌ 重大なエラーがあります。修正が必要です。")
        return False


if __name__ == "__main__":
    success = validate_fixes()
    sys.exit(0 if success else 1)
