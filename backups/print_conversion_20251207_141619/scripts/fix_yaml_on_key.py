#!/usr/bin/env python3
"""
GitHub Actions ワークフローの 'true:' を 'on:' に修正するスクリプト
YAMLライブラリがonをブール値として解釈する問題を文字列処理で解決
"""

from pathlib import Path


def fix_workflow_file(filepath):
    """単一のワークフローファイルを修正"""
    with open(filepath, "r") as f:
        lines = f.readlines()

    modified = False
    new_lines = []

    for line in lines:
        # 'true:' を 'on:' に置換（行頭のみ）
        if line.strip() == "true:":
            new_lines.append(line.replace("true:", "on:"))
            modified = True
            print(f"   修正: 'true:' → 'on:' at line {len(new_lines)}")
        else:
            new_lines.append(line)

    if modified:
        with open(filepath, "w") as f:
            f.writelines(new_lines)
        return True

    return False


def main():
    """メイン処理"""
    workflows_dir = Path(".github/workflows")

    if not workflows_dir.exists():
        print("❌ .github/workflows ディレクトリが見つかりません")
        return 1

    workflow_files = list(workflows_dir.glob("*.yml")) + list(
        workflows_dir.glob("*.yaml")
    )

    print(f"🔧 {len(workflow_files)} 個のワークフローファイルをチェック中...\n")

    fixed_count = 0

    for filepath in workflow_files:
        print(f"📄 {filepath.name}:")
        if fix_workflow_file(filepath):
            print("   ✅ 修正完了")
            fixed_count += 1
        else:
            print("   ⚪ 修正不要")

    print("\n" + "=" * 50)
    print(f"✅ {fixed_count} 個のファイルを修正しました")

    return 0


if __name__ == "__main__":
    exit(main())
