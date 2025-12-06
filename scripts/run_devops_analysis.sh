#!/bin/bash

# DevOps/CI/CD総合分析実行スクリプト
# 作成日: 2025-12-06

SCRIPT_DIR="/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/scripts"
REPORT_DIR="/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/docs/operations"

echo "========================================="
echo "DevOps/CI/CD総合分析を開始します"
echo "========================================="
echo ""

# スクリプトに実行権限を付与
chmod +x "$SCRIPT_DIR/analyze_workflows.sh"
chmod +x "$SCRIPT_DIR/analyze_deployment.sh"

# レポートディレクトリの作成
mkdir -p "$REPORT_DIR"

# 1. ワークフロー分析
echo "Step 1: GitHub Actionsワークフロー分析"
echo "========================================="
bash "$SCRIPT_DIR/analyze_workflows.sh" | tee "$REPORT_DIR/workflows-analysis.txt"
echo ""

# 2. デプロイメント設定分析
echo "Step 2: デプロイメント設定分析"
echo "========================================="
bash "$SCRIPT_DIR/analyze_deployment.sh" | tee "$REPORT_DIR/deployment-analysis.txt"
echo ""

# 3. プロジェクト構造の確認
echo "Step 3: プロジェクト構造確認"
echo "========================================="
tree -L 3 -I '__pycache__|*.pyc|node_modules|.git' /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system > "$REPORT_DIR/project-structure.txt" 2>/dev/null || \
find /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system -maxdepth 3 -type d | grep -v "__pycache__\|\.git\|node_modules" > "$REPORT_DIR/project-structure.txt"
echo "プロジェクト構造を project-structure.txt に出力しました"
echo ""

# 4. Gitフック確認
echo "Step 4: Gitフック確認"
echo "========================================="
if [ -d "/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/.git/hooks" ]; then
    echo "Gitフックディレクトリが存在します"
    ls -la /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/.git/hooks | grep -v "\.sample" | tee "$REPORT_DIR/git-hooks.txt"
else
    echo "Gitフックディレクトリが存在しません" | tee "$REPORT_DIR/git-hooks.txt"
fi
echo ""

# 5. サマリーレポート生成
echo "Step 5: サマリーレポート生成"
echo "========================================="

cat > "$REPORT_DIR/devops-summary.md" << 'EOF'
# DevOps/CI/CD分析サマリー

**生成日**: $(date +%Y-%m-%d)
**プロジェクト**: MangaAnime-Info-delivery-system

## 分析結果ファイル

1. `workflows-analysis.txt` - GitHub Actionsワークフロー詳細
2. `deployment-analysis.txt` - デプロイメント設定詳細
3. `project-structure.txt` - プロジェクトディレクトリ構造
4. `git-hooks.txt` - Gitフック設定

## 主要な発見事項

### GitHub Actions
- 検出されたワークフロー数: 調査中
- 自動実行設定: 調査中
- 使用しているアクション: 調査中

### デプロイメント
- Docker設定: 調査中
- 環境変数管理: 調査中
- スケジューリング: 調査中

### 改善提案
1. 詳細は各分析ファイルを参照してください
2. 最適化候補の特定
3. セキュリティ強化項目

EOF

echo "サマリーレポートを devops-summary.md に生成しました"
echo ""

echo "========================================="
echo "全ての分析が完了しました"
echo "========================================="
echo ""
echo "レポート保存先: $REPORT_DIR"
echo ""
echo "生成されたファイル:"
ls -lh "$REPORT_DIR"/*.txt "$REPORT_DIR"/*.md 2>/dev/null
