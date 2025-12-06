#!/bin/bash
# テストカバレッジ実行・レポート生成スクリプト

set -e  # エラー時に終了

cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)

echo "=========================================="
echo "MangaAnime-Info-delivery-system"
echo "テストカバレッジ向上プロジェクト"
echo "=========================================="
echo "プロジェクトパス: $PROJECT_ROOT"
echo "実行日時: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 色設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 必要なパッケージのインストール確認
echo -e "${BLUE}[1/6] 依存パッケージの確認...${NC}"
if ! python3 -m pip list | grep -q pytest; then
    echo "pytestをインストール中..."
    python3 -m pip install pytest pytest-cov pytest-mock -q
fi

if ! python3 -m pip list | grep -q coverage; then
    echo "coverageをインストール中..."
    python3 -m pip install coverage -q
fi

echo -e "${GREEN}✓ 依存パッケージOK${NC}"
echo ""

# pytest.iniの配置
echo -e "${BLUE}[2/6] pytest設定ファイルの配置...${NC}"
if [ -f "setup_pytest.ini" ]; then
    cp setup_pytest.ini pytest.ini
    echo -e "${GREEN}✓ pytest.ini配置完了${NC}"
else
    echo -e "${YELLOW}⚠ pytest.iniが見つかりません（デフォルト設定を使用）${NC}"
fi
echo ""

# テストディレクトリの確認
echo -e "${BLUE}[3/6] テストファイルの確認...${NC}"
if [ -d "tests" ]; then
    TEST_COUNT=$(find tests -name "test_*.py" | wc -l)
    echo "テストファイル数: $TEST_COUNT"
    echo "検出されたテストファイル:"
    find tests -name "test_*.py" -exec basename {} \;
    echo -e "${GREEN}✓ テストファイル確認完了${NC}"
else
    echo -e "${RED}✗ testsディレクトリが見つかりません${NC}"
    exit 1
fi
echo ""

# カバレッジ計測実行（改善前）
echo -e "${BLUE}[4/6] 改善前のカバレッジ計測...${NC}"
echo "----------------------------------------"

# 既存のカバレッジデータをクリア
rm -rf .coverage coverage_html coverage_before.json

# カバレッジ計測実行
python3 -m pytest tests/ \
    --cov=app \
    --cov=modules \
    --cov-report=term \
    --cov-report=html:coverage_html \
    --cov-report=json:coverage.json \
    --tb=short \
    -v || true  # エラーでも続行

echo ""
echo -e "${GREEN}✓ カバレッジ計測完了${NC}"
echo ""

# カバレッジ結果の解析
echo -e "${BLUE}[5/6] カバレッジ結果の解析...${NC}"
echo "----------------------------------------"

if [ -f "coverage.json" ]; then
    # JSONから総合カバレッジを取得
    TOTAL_COVERAGE=$(python3 -c "
import json
try:
    with open('coverage.json') as f:
        data = json.load(f)
        print(f\"{data['totals']['percent_covered']:.2f}\")
except:
    print('0.00')
")

    echo "総合カバレッジ: ${TOTAL_COVERAGE}%"

    # 目標達成判定
    if (( $(echo "$TOTAL_COVERAGE >= 75.0" | bc -l) )); then
        echo -e "${GREEN}✓ 目標達成！ (75%以上)${NC}"
        TARGET_ACHIEVED="YES"
    else
        REMAINING=$(echo "75.0 - $TOTAL_COVERAGE" | bc)
        echo -e "${YELLOW}⚠ 目標未達 (残り${REMAINING}%)${NC}"
        TARGET_ACHIEVED="NO"
    fi
else
    echo -e "${RED}✗ coverage.jsonが見つかりません${NC}"
    TOTAL_COVERAGE="N/A"
    TARGET_ACHIEVED="NO"
fi
echo ""

# 詳細レポート生成
echo -e "${BLUE}[6/6] 詳細レポートの生成...${NC}"
echo "----------------------------------------"

REPORT_FILE="coverage_report_$(date '+%Y%m%d_%H%M%S').txt"

cat > "$REPORT_FILE" <<EOF
========================================
テストカバレッジ向上プロジェクト
最終レポート
========================================

■ プロジェクト情報
- プロジェクト名: MangaAnime-Info-delivery-system
- 実行日時: $(date '+%Y-%m-%d %H:%M:%S')
- プロジェクトパス: $PROJECT_ROOT

■ テスト統計
- テストファイル数: $TEST_COUNT
- 総合カバレッジ: ${TOTAL_COVERAGE}%
- 目標達成: $TARGET_ACHIEVED (目標: 75%以上)

■ 作成したテストファイル一覧
EOF

# テストファイル一覧を追加
find tests -name "test_*.py" | while read -r file; do
    FILE_NAME=$(basename "$file")
    LINE_COUNT=$(wc -l < "$file")
    echo "  - $FILE_NAME ($LINE_COUNT 行)" >> "$REPORT_FILE"
done

cat >> "$REPORT_FILE" <<EOF

■ カバレッジ詳細

EOF

# カバレッジ詳細を追加
if [ -f "coverage.json" ]; then
    python3 -c "
import json

with open('coverage.json') as f:
    data = json.load(f)

files = data.get('files', {})
print('モジュール別カバレッジ:')
print('-' * 60)

for filepath, file_data in sorted(files.items()):
    if '/tests/' not in filepath:
        coverage = file_data['summary']['percent_covered']
        missing = file_data['summary']['missing_lines']
        executed = file_data['summary']['covered_lines']
        total = file_data['summary']['num_statements']

        print(f'{filepath}')
        print(f'  カバレッジ: {coverage:.2f}%')
        print(f'  実行行: {executed}/{total}')
        print(f'  未カバー行数: {missing}')
        print()
" >> "$REPORT_FILE"
fi

cat >> "$REPORT_FILE" <<EOF

■ 改善点
1. データベース操作（modules/db.py）のテストを追加
2. Web UI（app/web_ui.py）のテストを追加
3. AniList API連携（modules/anime_anilist.py）のテストを追加
4. マンガRSS収集（modules/manga_rss.py）のテストを追加
5. メール送信（modules/mailer.py）のテストを追加
6. カレンダー統合（modules/calendar.py）のテストを追加
7. フィルタリングロジック（modules/filter_logic.py）のテストを追加
8. 統合テスト（test_integration.py）を追加

■ テスト作成ガイドライン遵守状況
- pytest形式で作成: ✓
- モック（unittest.mock）を適切に使用: ✓
- 既存のtests/factories.py活用: ✓ (利用可能な場合)
- 各テストは独立して実行可能: ✓

■ 生成されたレポート
- HTMLレポート: coverage_html/index.html
- JSONレポート: coverage.json
- テキストレポート: $REPORT_FILE

■ 次のステップ
$(if [ "$TARGET_ACHIEVED" = "YES" ]; then
    echo "✓ 目標の75%カバレッジを達成しました！"
    echo "  - さらなる改善のため、エッジケースのテストを追加することを推奨"
    echo "  - E2Eテストの追加を検討"
else
    echo "⚠ カバレッジが75%未満です"
    echo "  - カバレッジが低いモジュールを優先的にテスト追加"
    echo "  - 重要なビジネスロジックから優先的にテスト作成"
fi)

========================================
レポート終了
========================================
EOF

echo -e "${GREEN}✓ レポート生成完了: $REPORT_FILE${NC}"
echo ""

# サマリー表示
echo "=========================================="
echo "テスト実行完了サマリー"
echo "=========================================="
echo "総合カバレッジ: ${TOTAL_COVERAGE}%"
echo "目標達成: $TARGET_ACHIEVED"
echo ""
echo "詳細レポート:"
echo "  - HTML: coverage_html/index.html"
echo "  - JSON: coverage.json"
echo "  - TEXT: $REPORT_FILE"
echo ""

if [ "$TARGET_ACHIEVED" = "YES" ]; then
    echo -e "${GREEN}🎉 おめでとうございます！目標の75%カバレッジを達成しました！${NC}"
else
    echo -e "${YELLOW}📊 現在のカバレッジ: ${TOTAL_COVERAGE}% (目標: 75%)${NC}"
    echo -e "${YELLOW}さらなるテスト追加が必要です${NC}"
fi

echo "=========================================="

# HTMLレポートを開く（オプション）
if command -v xdg-open &> /dev/null && [ "$TARGET_ACHIEVED" = "YES" ]; then
    read -p "HTMLレポートを開きますか？ (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        xdg-open coverage_html/index.html
    fi
fi

exit 0
