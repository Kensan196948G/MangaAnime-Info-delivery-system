#!/usr/bin/env python3
"""
GitHub Issue一括クローズスクリプト
Issue #12-#27（自動修復失敗Issue）を一括でクローズします
"""

import os
import sys
import json

# GitHubトークンの確認
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = "Kensan196948G/MangaAnime-Info-delivery-system"
ISSUE_RANGE = range(12, 28)  # #12-#27
COMMIT_HASH = "18a17ff"

CLOSE_MESSAGE = f"""✅ 修正完了

このIssueで報告されていた問題は、以下のコミットで修正されました：
- **Commit**: {COMMIT_HASH}
- **修正内容**:
  - 依存関係の問題を解決（requirements.txt更新）
  - 構文エラーを修正（security_utils.py: E999）
  - Flake8エラーをすべて修正
    - E722: bare except → except Exception:
    - E712: == False → is not False
    - W291/W293: 行末空白を削除
    - F541: 不要なf-stringを修正
    - F811: 重複関数定義を修正
  - コード品質を全体的に改善

GitHub Actions CI/CDが正常に動作することを確認しました。
このIssueをクローズします。

関連PR: https://github.com/{REPO}/pull/new/claude/current-development-011CV2Fqxaa3qTXa6hpCYGtN
"""


def close_issues_with_curl():
    """curlコマンドを使用してIssueをクローズ"""
    if not GITHUB_TOKEN:
        print("⚠️ GITHUB_TOKENが設定されていません")
        print("")
        print("以下の手順でトークンを設定してください：")
        print("1. https://github.com/settings/tokens にアクセス")
        print("2. 'Generate new token (classic)' をクリック")
        print("3. 'repo' スコープを選択")
        print("4. トークンを生成してコピー")
        print("5. 以下のコマンドを実行：")
        print("")
        print("   export GITHUB_TOKEN='your_token_here'")
        print("   python3 close_issues.py")
        print("")
        return False

    import subprocess

    print(f"🔄 Issue #{ISSUE_RANGE.start}-{ISSUE_RANGE.stop - 1} を一括クローズします...")
    print("")

    success_count = 0
    fail_count = 0

    for issue_num in ISSUE_RANGE:
        print(f"  Closing issue #{issue_num}...", end=" ")

        # Issueをクローズ
        close_cmd = [
            "curl",
            "-X",
            "PATCH",
            "-H",
            f"Authorization: token {GITHUB_TOKEN}",
            "-H",
            "Accept: application/vnd.github.v3+json",
            f"https://api.github.com/repos/{REPO}/issues/{issue_num}",
            "-d",
            json.dumps({"state": "closed"}),
        ]

        try:
            result = subprocess.run(
                close_cmd, capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                # コメントを追加
                comment_cmd = [
                    "curl",
                    "-X",
                    "POST",
                    "-H",
                    f"Authorization: token {GITHUB_TOKEN}",
                    "-H",
                    "Accept: application/vnd.github.v3+json",
                    f"https://api.github.com/repos/{REPO}/issues/{issue_num}/comments",
                    "-d",
                    json.dumps({"body": CLOSE_MESSAGE}),
                ]
                subprocess.run(comment_cmd, capture_output=True, timeout=10)

                print("✅")
                success_count += 1
            else:
                print(f"❌ ({result.stderr[:50]}...)")
                fail_count += 1
        except Exception as e:
            print(f"❌ ({str(e)[:50]}...)")
            fail_count += 1

    print("")
    print(f"✅ 完了: {success_count}件クローズ, {fail_count}件失敗")
    return success_count > 0


def print_manual_instructions():
    """手動クローズの手順を表示"""
    print("=" * 60)
    print("📋 Issue一括クローズの手順")
    print("=" * 60)
    print("")
    print("方法1: GitHub Web UIで手動クローズ（推奨）")
    print("-" * 60)
    print(f"1. https://github.com/{REPO}/issues にアクセス")
    print(f"2. Issue #12-#27 を順番に開いてクローズ")
    print("3. 各Issueに以下のコメントを追加：")
    print("")
    print(CLOSE_MESSAGE)
    print("")
    print("")
    print("方法2: 自動クローズ（GitHubトークンが必要）")
    print("-" * 60)
    print("1. GitHubトークンを取得:")
    print("   https://github.com/settings/tokens")
    print("")
    print("2. 環境変数を設定:")
    print("   export GITHUB_TOKEN='your_token_here'")
    print("")
    print("3. このスクリプトを再実行:")
    print("   python3 close_issues.py")
    print("")
    print("=" * 60)


if __name__ == "__main__":
    print("🚀 GitHub Issue一括クローズツール")
    print("")

    if GITHUB_TOKEN:
        success = close_issues_with_curl()
        if not success:
            print("")
            print_manual_instructions()
    else:
        print_manual_instructions()
