#!/usr/bin/env python3
"""
GitHub Actions ワークフロー検証スクリプト
"""

import yaml
import sys
from pathlib import Path


def validate_workflow(filepath):
    """単一のワークフローファイルを検証"""
    errors = []

    try:
        with open(filepath, "r") as f:
            content = f.read()

        # YAMLパース試行
        try:
            workflow = yaml.safe_load(content)
        except yaml.YAMLError as e:
            errors.append(f"YAML構文エラー: {e}")
            return errors

        # 基本構造チェック
        if not workflow:
            errors.append("空のワークフローファイル")
            return errors

        if "name" not in workflow:
            errors.append("'name' フィールドが見つかりません")

        if "on" not in workflow:
            errors.append("'on' トリガーが定義されていません")
        else:
            # スケジュールの検証
            if "schedule" in workflow["on"]:
                for schedule_item in workflow["on"]["schedule"]:
                    if "cron" in schedule_item:
                        cron = schedule_item["cron"]
                        if not isinstance(cron, str):
                            errors.append(f"cronが文字列ではありません: {cron}")

        if "jobs" not in workflow:
            errors.append("'jobs' セクションが見つかりません")

    except Exception as e:
        errors.append(f"ファイル読み込みエラー: {e}")

    return errors


def main():
    """メイン処理"""
    workflows_dir = Path(".github/workflows")


    if not workflows_dir.exists():
        logger.info("❌ .github/workflows ディレクトリが見つかりません")
        sys.exit(1)

    all_valid = True
    workflow_files = list(workflows_dir.glob("*.yml")) + list(
        workflows_dir.glob("*.yaml")
    )

    logger.info(f"🔍 {len(workflow_files)} 個のワークフローファイルを検証中...\n")

    for filepath in workflow_files:
        errors = validate_workflow(filepath)

        if errors:
            all_valid = False
            logger.info(f"❌ {filepath.name}:")
            for error in errors:
                logger.info(f"   - {error}")
        else:
            logger.info(f"✅ {filepath.name}: OK")

    logger.info("\n" + "=" * 50)

    if all_valid:
        logger.info("✅ すべてのワークフローが有効です！")
        sys.exit(0)
    else:
        logger.info("❌ 一部のワークフローにエラーがあります")
        sys.exit(1)


if __name__ == "__main__":
    main()
