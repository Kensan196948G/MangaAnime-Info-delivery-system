# テストカバレッジ向上プロジェクト - 実行ガイド

## 概要

MangaAnime-Info-delivery-systemプロジェクトのテストカバレッジを75%以上に向上させるためのテストスイートです。

## 作成日

2025-12-06

## テストファイル一覧

### 主要モジュールのテスト

1. **test_db.py** - データベース操作テスト
   - テーブル初期化
   - 作品データの挿入・取得
   - リリース情報の管理
   - 通知ステータス管理

2. **test_web_ui.py** - Web UIテスト
   - ルーティング
   - テンプレートレンダリング
   - APIエンドポイント
   - エラーハンドリング

3. **test_anime_anilist.py** - AniList API連携テスト
   - GraphQLクエリ
   - データフェッチ
   - レスポンス解析
   - エラーハンドリング

4. **test_manga_rss.py** - マンガRSS収集テスト
   - RSSフィード取得
   - XML解析
   - 巻数抽出
   - データ正規化

5. **test_mailer.py** - メール送信テスト
   - メール作成
   - SMTP送信
   - Gmail API統合
   - テンプレートレンダリング

6. **test_filter_logic.py** - フィルタリングロジックテスト
   - NGキーワードフィルタ
   - ジャンル/タグフィルタ
   - カスタムフィルタ

7. **test_integration.py** - 統合テスト
   - エンドツーエンドワークフロー
   - データ整合性
   - エラーリカバリ
   - パフォーマンス

## セットアップ

### 1. 依存パッケージのインストール

```bash
# テスト関連パッケージのインストール
pip install -r test_requirements.txt
```

### 2. プロジェクト構造の確認

```
MangaAnime-Info-delivery-system/
├── app/                    # アプリケーションコード
├── modules/                # モジュール
├── tests/                  # テストコード
│   ├── test_db.py
│   ├── test_web_ui.py
│   ├── test_anime_anilist.py
│   ├── test_manga_rss.py
│   ├── test_mailer.py
│   ├── test_filter_logic.py
│   └── test_integration.py
├── scripts/                # スクリプト
│   ├── check_coverage.sh
│   └── run_coverage_tests.sh
└── pytest.ini              # pytest設定
```

## テスト実行方法

### 方法1: 自動スクリプトで実行（推奨）

```bash
# スクリプトに実行権限を付与
chmod +x scripts/run_coverage_tests.sh

# カバレッジ測定を含むテスト実行
bash scripts/run_coverage_tests.sh
```

### 方法2: pytestコマンドで実行

```bash
# 全テスト実行
pytest tests/ -v

# カバレッジ測定付き
pytest tests/ \
    --cov=app \
    --cov=modules \
    --cov-report=term \
    --cov-report=html:coverage_html \
    --cov-report=json:coverage.json \
    -v

# 特定のテストファイルのみ実行
pytest tests/test_db.py -v

# 特定のテストクラスのみ実行
pytest tests/test_db.py::TestDatabaseInit -v

# 特定のテスト関数のみ実行
pytest tests/test_db.py::TestDatabaseInit::test_init_db_creates_tables -v
```

### 方法3: カバレッジ確認のみ

```bash
chmod +x scripts/check_coverage.sh
bash scripts/check_coverage.sh
```

## レポートの確認

### HTMLレポート

```bash
# ブラウザでHTMLレポートを開く
xdg-open coverage_html/index.html  # Linux
open coverage_html/index.html      # macOS
start coverage_html/index.html     # Windows
```

### ターミナル出力

テスト実行後、ターミナルに以下の情報が表示されます:

```
Name                           Stmts   Miss  Cover   Missing
------------------------------------------------------------
modules/db.py                    120     12    90%   45-48, 78-82
modules/anime_anilist.py         150     20    87%   112-125, 200-205
modules/manga_rss.py             100     15    85%   67-75, 140-145
modules/mailer.py                 80      8    90%   45-50, 95
modules/filter_logic.py           60      5    92%   23-27
app/web_ui.py                    110     18    84%   89-95, 145-155
------------------------------------------------------------
TOTAL                            620     78    87%
```

## カバレッジ目標

- **目標**: 75%以上
- **現状**: テスト実行後に確認
- **優先度**:
  1. データベース操作（modules/db.py）
  2. Web UI（app/web_ui.py）
  3. API連携（modules/anime_anilist.py, manga_rss.py）
  4. 通知機能（modules/mailer.py）

## テスト作成ガイドライン

### 1. pytest形式で作成

```python
import pytest

class TestMyModule:
    def test_something(self):
        result = my_function()
        assert result == expected_value
```

### 2. モックの使用

```python
from unittest.mock import Mock, patch

@patch('module.external_api')
def test_with_mock(mock_api):
    mock_api.return_value = {'data': 'test'}
    result = function_using_api()
    assert result is not None
```

### 3. フィクスチャの活用

```python
@pytest.fixture
def test_database(tmp_path):
    db_path = str(tmp_path / "test.db")
    init_database(db_path)
    yield db_path
    # クリーンアップ
```

### 4. 独立性の確保

各テストは他のテストに依存せず、独立して実行可能にする。

## トラブルシューティング

### ModuleNotFoundError

```bash
# プロジェクトルートをPYTHONPATHに追加
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest tests/
```

### ImportError: modules not found

```bash
# sys.pathに追加されているか確認
python3 -c "import sys; print(sys.path)"

# または、テストファイル内で明示的に追加
sys.path.insert(0, str(Path(__file__).parent.parent))
```

### カバレッジが0%と表示される

```bash
# ソースディレクトリが正しく指定されているか確認
pytest tests/ --cov=app --cov=modules --cov-report=term
```

## 継続的改善

### カバレッジが75%未満の場合

1. カバレッジレポートで未カバー行を確認
2. 重要度の高い機能から優先的にテスト追加
3. エッジケース・エラーハンドリングのテスト追加

### カバレッジが75%以上の場合

1. エッジケースのテスト追加
2. E2Eテストの追加
3. パフォーマンステストの追加
4. セキュリティテストの追加

## CI/CD統合

### GitHub Actions設定例

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r test_requirements.txt
      - name: Run tests with coverage
        run: |
          pytest tests/ --cov=app --cov=modules --cov-report=xml
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v2
```

## 参考資料

- [pytest公式ドキュメント](https://docs.pytest.org/)
- [coverage.py公式ドキュメント](https://coverage.readthedocs.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)

## 作成者メモ

### テスト作成時の注意点

1. **モックの適切な使用**: 外部API、データベース、ファイルI/Oは必ずモック化
2. **テストの独立性**: 各テストは独立して実行可能に
3. **エッジケースの考慮**: 正常系だけでなく異常系もテスト
4. **命名規則**: テスト名は機能を明確に表現

### 改善履歴

- 2025-12-06: 初回テストスイート作成
  - 7つの主要テストファイル追加
  - カバレッジ測定スクリプト作成
  - 統合テスト追加

---

**次のステップ**: テストを実行して75%達成を確認してください！

```bash
bash scripts/run_coverage_tests.sh
```
