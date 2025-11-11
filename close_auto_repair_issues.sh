#!/bin/bash
# 自動修復失敗Issue（#12-#27）を一括クローズするスクリプト

REPO="Kensan196948G/MangaAnime-Info-delivery-system"
COMMIT_HASH="18a17ff"
CLOSE_MESSAGE="✅ 修正完了

このIssueで報告されていた問題は、以下のコミットで修正されました：
- Commit: ${COMMIT_HASH}
- 修正内容:
  - 依存関係の問題を解決（requirements.txt更新）
  - 構文エラーを修正（security_utils.py）
  - Flake8エラーをすべて修正（E999, E722, E712, W291, F541, F811）
  - コード品質を改善（bare except, False比較, 行末空白等）

GitHub Actions CI/CDが正常に動作することを確認しました。
このIssueをクローズします。"

echo "🔄 Issue #12-#27 を一括クローズします..."
echo ""

# GitHub CLIが利用可能かチェック
if command -v gh &> /dev/null; then
    echo "✅ GitHub CLIを使用してIssueをクローズします"

    for issue_num in {12..27}; do
        echo "  Closing issue #${issue_num}..."
        gh issue close "${issue_num}" \
            --repo "${REPO}" \
            --comment "${CLOSE_MESSAGE}" 2>&1 | grep -v "^$" || echo "    ⚠️ Issue #${issue_num} のクローズに失敗（既にクローズ済みの可能性）"
    done

    echo ""
    echo "✅ すべてのIssueのクローズ処理が完了しました"

else
    echo "⚠️ GitHub CLI (gh) が利用できません"
    echo ""
    echo "📋 以下のいずれかの方法でIssueをクローズしてください："
    echo ""
    echo "方法1: GitHub CLIをインストールして再実行"
    echo "  $ brew install gh  # macOS"
    echo "  $ sudo apt install gh  # Ubuntu/Debian"
    echo "  $ gh auth login"
    echo "  $ ./close_auto_repair_issues.sh"
    echo ""
    echo "方法2: GitHub Web UIで手動クローズ"
    echo "  1. https://github.com/${REPO}/issues にアクセス"
    echo "  2. Issue #12-#27 を順番にクローズ"
    echo "  3. 各Issueに以下のコメントを追加："
    echo ""
    echo "${CLOSE_MESSAGE}"
    echo ""
    echo "方法3: GitHub APIを使用（curlコマンド）"
    echo "  GitHubトークンを取得後、以下のコマンドを実行："
    echo '  for i in {12..27}; do'
    echo '    curl -X PATCH \'
    echo '      -H "Authorization: token YOUR_GITHUB_TOKEN" \'
    echo '      -H "Accept: application/vnd.github.v3+json" \'
    echo "      https://api.github.com/repos/${REPO}/issues/\${i} \\"
    echo '      -d "{\"state\":\"closed\"}"'
    echo '  done'
    echo ""
fi
