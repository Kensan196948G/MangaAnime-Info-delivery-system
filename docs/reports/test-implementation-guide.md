# テスト実装ガイド

**プロジェクト**: MangaAnime-Info-delivery-system
**作成日**: 2025-12-08
**作成者**: QA Engineer Agent

---

## 📋 目次

1. [テストディレクトリ構造](#テストディレクトリ構造)
2. [テスト実行方法](#テスト実行方法)
3. [作成済みテストファイル](#作成済みテストファイル)
4. [今後の実装計画](#今後の実装計画)
5. [ベストプラクティス](#ベストプラクティス)

---

## 1. テストディレクトリ構造

現在のプロジェクトには以下のテストインフラが整備されました：

```
tests/
├── __init__.py                          # テストパッケージ初期化
├── conftest.py                          # pytest共通設定・フィクスチャ ✅作成済み
├── pytest.ini                           # pytest設定ファイル ✅作成済み
├── run_tests.sh                         # テスト実行スクリプト ✅作成済み
│
├── unit/                                # 単体テスト
│   ├── __init__.py
│   ├── test_collectors/
│   │   ├── __init__.py
│   │   ├── test_anilist.py             # AniList APIテスト ✅作成済み
│   │   ├── test_syobocal.py            # しょぼいカレンダーテスト
│   │   └── test_manga_rss.py           # マンガRSSテスト
│   ├── test_db/
│   │   ├── __init__.py
│   │   ├── test_operations.py          # DB操作テスト ✅作成済み
│   │   ├── test_models.py              # モデルテスト
│   │   └── test_transactions.py        # トランザクションテスト
│   ├── test_notifiers/
│   │   ├── __init__.py
│   │   ├── test_gmail.py               # Gmail通知テスト
│   │   └── test_batch.py               # バッチ通知テスト
│   ├── test_calendar/
│   │   ├── __init__.py
│   │   └── test_google_calendar.py     # カレンダー同期テスト
│   └── test_filters/
│       ├── __init__.py
│       ├── test_ng_keywords.py         # NGワードフィルタテスト
│       └── test_whitelist.py           # ホワイトリストテスト
│
├── integration/                         # 統合テスト
│   ├── __init__.py
│   ├── test_full_pipeline.py           # 完全パイプラインテスト ✅作成済み
│   ├── test_api_flows/
│   │   ├── __init__.py
│   │   └── test_collect_and_store.py
│   ├── test_notification_flows/
│   │   ├── __init__.py
│   │   └── test_email_notification.py
│   └── test_calendar_sync/
│       ├── __init__.py
│       └── test_sync_flow.py
│
├── e2e/                                 # E2Eテスト
│   ├── __init__.py
│   ├── test_end_to_end.py
│   └── playwright/
│       ├── __init__.py
│       └── test_web_ui.py
│
└── fixtures/                            # テストデータ
    ├── sample_anime_data.json
    ├── sample_manga_rss.xml
    └── mock_responses/
        ├── anilist_response.json
        └── syobocal_response.json
```

---

## 2. テスト実行方法

### 2.1 シェルスクリプトを使用（推奨）

```bash
# 実行権限付与
chmod +x tests/run_tests.sh

# 対話的にテスト実行
./tests/run_tests.sh

# オプション選択:
# 1. 全テスト実行（カバレッジ付き）
# 2. 単体テストのみ
# 3. 統合テストのみ
# 4. E2Eテストのみ
# 5. 高速テスト（並列実行）
# 6. カバレッジレポート表示
# 7. 特定のテストファイルを実行
```

### 2.2 pytestコマンドを直接使用

```bash
# 全テスト実行
pytest tests/ --verbose --cov=app

# 単体テストのみ
pytest tests/unit/ -v

# 統合テストのみ
pytest tests/integration/ -v -m integration

# 特定のファイル
pytest tests/unit/test_collectors/test_anilist.py -v

# 特定のテストクラス
pytest tests/unit/test_db/test_operations.py::TestDatabaseOperations -v

# 特定のテスト関数
pytest tests/unit/test_db/test_operations.py::TestDatabaseOperations::test_insert_work -v

# カバレッジ付き実行
pytest tests/ --cov=app --cov-report=html

# 並列実行（高速化）
pytest tests/unit/ -n auto

# 低速テストをスキップ
pytest tests/ -m "not slow"

# 失敗したテストを最初に実行
pytest tests/ --failed-first
```

### 2.3 カバレッジレポート表示

```bash
# HTMLレポート生成後
xdg-open htmlcov/index.html   # Linux
open htmlcov/index.html        # macOS

# ターミナルで確認
pytest tests/ --cov=app --cov-report=term-missing
```

---

## 3. 作成済みテストファイル

### 3.1 conftest.py（pytest共通設定）

**提供フィクスチャ:**

#### データベースフィクスチャ
- `test_db`: インメモリSQLiteデータベース
- `sample_works`: サンプル作品データ（3件）
- `sample_releases`: サンプルリリースデータ（4件）
- `large_dataset`: 大量データセット（1000件）

#### APIモックフィクスチャ
- `mock_anilist_response`: AniList GraphQLレスポンス
- `mock_syobocal_response`: しょぼいカレンダーレスポンス
- `mock_rss_feed`: RSSフィード

#### Gmail/Calendarモック
- `mock_gmail_service`: Gmail APIサービスモック
- `mock_calendar_service`: Google Calendar APIサービスモック
- `mock_oauth_credentials`: OAuth2認証情報モック

#### テストデータ
- `ng_keywords`: NGキーワードリスト
- `sample_anime_data`: サンプルアニメデータ
- `sample_manga_data`: サンプルマンガデータ
- `sample_email_template`: メールテンプレート

#### 環境設定
- `mock_env_vars`: 環境変数モック
- `mock_config_file`: 設定ファイルモック
- `mock_token_file`: OAuth2トークンファイルモック

**使用例:**

```python
def test_example(test_db, sample_works, mock_gmail_service):
    cursor = test_db.cursor()
    works = cursor.execute("SELECT * FROM works").fetchall()
    assert len(works) == 3

    # Gmail送信テスト
    # mock_gmail_service.users().messages().send().execute()
```

---

### 3.2 pytest.ini（pytest設定）

**主要設定:**

- テストパス: `tests/`
- カバレッジ対象: `app/`, `scripts/`
- 最低カバレッジ: 75%
- 並列実行: 有効（`-n auto`）
- レポート形式: HTML, XML, ターミナル

**マーカー定義:**

```python
@pytest.mark.slow          # 低速テスト（5秒以上）
@pytest.mark.integration   # 統合テスト
@pytest.mark.e2e           # E2Eテスト
@pytest.mark.unit          # 単体テスト
@pytest.mark.api           # 外部API連携テスト
@pytest.mark.database      # データベース操作テスト
@pytest.mark.security      # セキュリティテスト
@pytest.mark.performance   # パフォーマンステスト
```

**使用例:**

```python
@pytest.mark.slow
@pytest.mark.performance
def test_bulk_operation():
    # パフォーマンステスト
    pass
```

---

### 3.3 test_anilist.py（AniList APIテスト）

**テストケース:**

#### 正常系
- ✅ `test_fetch_upcoming_anime_success`: 正常にアニメ情報を取得
- ✅ `test_parse_graphql_response`: GraphQLレスポンス解析
- ✅ `test_extract_streaming_platforms`: 配信プラットフォーム抽出

#### エラーハンドリング
- ✅ `test_rate_limit_handling`: レート制限（429）時のリトライ
- ✅ `test_timeout_handling`: タイムアウト処理
- ✅ `test_connection_error_handling`: 接続エラー処理
- ✅ `test_invalid_json_response`: 不正JSONレスポンス処理
- ✅ `test_empty_response_handling`: 空レスポンス処理
- ✅ `test_http_500_error_handling`: サーバーエラー処理

#### エッジケース
- ✅ `test_missing_next_airing_episode`: nextAiringEpisode null時の処理
- ✅ `test_unicode_title_handling`: Unicode文字処理
- ✅ `test_pagination_handling`: ページネーション処理

#### フィルタリング
- ✅ `test_filter_by_genre`: ジャンルフィルタリング
- ✅ `test_filter_adult_content`: 成人向けコンテンツフィルタ

#### パフォーマンス
- ✅ `test_bulk_fetch_performance`: 大量データ取得性能

#### データ正規化
- ✅ `test_normalize_title`: タイトル正規化
- ✅ `test_normalize_date_format`: 日付フォーマット正規化

---

### 3.4 test_operations.py（DB操作テスト）

**テストケース:**

#### CRUD操作
- ✅ `test_insert_work`: 作品データ挿入
- ✅ `test_select_work_by_id`: ID検索
- ✅ `test_update_work`: 作品情報更新
- ✅ `test_delete_work`: 作品削除
- ✅ `test_insert_release`: リリースデータ挿入
- ✅ `test_get_unnotified_releases`: 未通知リリース取得
- ✅ `test_mark_as_notified`: 通知済みフラグ更新

#### 制約テスト
- ✅ `test_unique_constraint`: UNIQUE制約
- ✅ `test_foreign_key_constraint`: 外部キー制約
- ✅ `test_check_constraint_type`: CHECK制約

#### トランザクション
- ✅ `test_transaction_commit`: コミット処理
- ✅ `test_transaction_rollback`: ロールバック処理
- ✅ `test_concurrent_transaction_handling`: 並行トランザクション

#### JOIN操作
- ✅ `test_join_works_and_releases`: 作品とリリースのJOIN
- ✅ `test_left_join_with_no_releases`: LEFT JOIN

#### インデックス
- ✅ `test_index_on_notified_column`: notifiedインデックス
- ✅ `test_index_on_release_date`: release_dateインデックス

#### 集計
- ✅ `test_count_releases_by_platform`: プラットフォーム別集計
- ✅ `test_upcoming_releases_next_7_days`: 今後7日間のリリース

#### データ整合性
- ✅ `test_cascade_delete`: カスケード削除
- ✅ `test_orphaned_releases`: 孤立リリース検出

---

### 3.5 test_full_pipeline.py（統合テスト）

**テストケース:**

#### エンドツーエンドフロー
- ✅ `test_collect_filter_store_notify_pipeline`: 完全パイプライン
- ✅ `test_duplicate_prevention`: 重複データ防止
- ✅ `test_error_recovery_on_notification_failure`: 通知失敗時のリカバリ
- ✅ `test_calendar_sync_retry_on_failure`: カレンダー同期リトライ

#### バッチ処理
- ✅ `test_batch_notification`: 大量データ一括通知
- ✅ `test_incremental_calendar_sync`: 増分カレンダー同期

#### スケジューラ
- ✅ `test_scheduled_job_execution`: 定期実行テスト

#### ロールバック
- ✅ `test_rollback_on_db_error`: DB操作エラー時のロールバック

#### パフォーマンス
- ✅ `test_full_pipeline_performance`: 完全パイプライン性能

#### データ整合性
- ✅ `test_data_consistency_across_tables`: テーブル間整合性
- ✅ `test_timezone_consistency`: タイムゾーン整合性

---

## 4. 今後の実装計画

### Phase 1: 基本単体テスト（優先度: 🔴 P0）

**実装が必要なテストファイル:**

```bash
tests/unit/test_collectors/
├── test_syobocal.py              # しょぼいカレンダーAPIテスト
├── test_manga_rss.py             # マンガRSSテスト
└── test_rate_limiting.py         # レート制限テスト

tests/unit/test_notifiers/
├── test_gmail.py                 # Gmail通知テスト
└── test_batch.py                 # バッチ通知テスト

tests/unit/test_calendar/
└── test_google_calendar.py       # Googleカレンダーテスト

tests/unit/test_filters/
├── test_ng_keywords.py           # NGワードフィルタテスト
└── test_whitelist.py             # ホワイトリストテスト
```

**推定工数:** 5日

---

### Phase 2: 統合テスト拡充（優先度: 🟡 P1）

**実装が必要なテストファイル:**

```bash
tests/integration/test_api_flows/
└── test_collect_and_store.py     # 収集→保存フローテスト

tests/integration/test_notification_flows/
└── test_email_notification.py    # メール通知フローテスト

tests/integration/test_calendar_sync/
└── test_sync_flow.py             # カレンダー同期フローテスト
```

**推定工数:** 3日

---

### Phase 3: E2Eテスト（優先度: 🟢 P2）

**実装が必要なテストファイル:**

```bash
tests/e2e/
├── test_end_to_end.py            # 完全E2Eテスト
└── playwright/
    └── test_web_ui.py            # WebUI E2Eテスト（Web UIがある場合）
```

**推定工数:** 5日

---

### Phase 4: セキュリティ・パフォーマンステスト（優先度: 🟢 P2）

**実装が必要なテストファイル:**

```bash
tests/security/
├── test_oauth_security.py        # OAuth2セキュリティ
├── test_token_storage.py         # トークン保管
├── test_input_validation.py      # 入力検証
└── test_sql_injection.py         # SQLインジェクション防止

tests/performance/
├── test_bulk_operations.py       # 大量データ処理
├── test_memory_usage.py          # メモリ使用量
└── test_concurrent_api_calls.py  # 並行API呼び出し
```

**推定工数:** 7日

---

## 5. ベストプラクティス

### 5.1 テスト命名規則

```python
# ❌ 悪い例
def test1():
    pass

# ✅ 良い例
def test_insert_work_with_valid_data():
    """有効なデータで作品を挿入できることを確認"""
    pass

def test_fetch_anime_handles_rate_limit_error():
    """レート制限エラー時に適切にリトライすることを確認"""
    pass
```

### 5.2 アサーション

```python
# ❌ 悪い例
assert result

# ✅ 良い例
assert result is not None, "結果がNoneであってはならない"
assert len(result) == 3, f"期待: 3件, 実際: {len(result)}件"
assert result[0]['title'] == "転生したらスライムだった件"
```

### 5.3 モックの使用

```python
# ✅ 外部APIはモック化
def test_fetch_anime(mocker):
    mock_post = mocker.patch('requests.post')
    mock_post.return_value.json.return_value = {"data": {}}

    # collector.fetch_upcoming_anime()

    mock_post.assert_called_once()

# ✅ データベースは実物を使用（インメモリ）
def test_insert_work(test_db):
    cursor = test_db.cursor()
    cursor.execute("INSERT INTO works (title, type) VALUES ('Test', 'anime')")
    test_db.commit()

    result = cursor.execute("SELECT * FROM works WHERE title = 'Test'").fetchone()
    assert result is not None
```

### 5.4 フィクスチャの活用

```python
# ✅ 共通設定はフィクスチャ化
@pytest.fixture
def configured_collector():
    """設定済みコレクターインスタンス"""
    collector = AniListCollector(api_key="test_key")
    collector.set_timeout(30)
    return collector

def test_with_fixture(configured_collector):
    result = configured_collector.fetch_upcoming_anime()
    assert result is not None
```

### 5.5 テストの独立性

```python
# ❌ 悪い例（前のテストに依存）
def test_insert():
    db.insert("data1")

def test_count():
    assert db.count() == 1  # test_insertに依存

# ✅ 良い例（独立）
def test_insert(test_db):
    cursor = test_db.cursor()
    cursor.execute("INSERT INTO works (title, type) VALUES ('Test', 'anime')")
    test_db.commit()

    count = cursor.execute("SELECT COUNT(*) FROM works").fetchone()[0]
    assert count >= 1

def test_count(test_db, sample_works):
    cursor = test_db.cursor()
    count = cursor.execute("SELECT COUNT(*) FROM works").fetchone()[0]
    assert count == 3
```

### 5.6 パラメトライズドテスト

```python
# ✅ 複数のケースを効率的にテスト
@pytest.mark.parametrize("title,expected", [
    ("普通のアニメ", True),
    ("エロアニメ", False),
    ("R18作品", False),
    ("BLアニメ", False),
])
def test_ng_keyword_filter(title, expected):
    filter = NGKeywordFilter(keywords=["エロ", "R18", "BL"])
    result = filter.is_allowed(title)
    assert result == expected
```

---

## 6. CI/CD統合

### 6.1 GitHub Actions設定例

`.github/workflows/test.yml` を作成:

```yaml
name: Test Coverage

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-test.txt

    - name: Run tests
      run: |
        pytest tests/ --cov=app --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### 6.2 Pre-commit Hook

`.git/hooks/pre-commit` を作成:

```bash
#!/bin/bash

echo "Running tests before commit..."

pytest tests/unit -v --tb=short

if [ $? -ne 0 ]; then
    echo "Tests failed. Commit aborted."
    exit 1
fi

echo "All tests passed!"
exit 0
```

実行権限付与:

```bash
chmod +x .git/hooks/pre-commit
```

---

## 7. トラブルシューティング

### 7.1 よくある問題

#### 問題: ModuleNotFoundError

```bash
# 解決方法
export PYTHONPATH=/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system:$PYTHONPATH
```

#### 問題: テストが見つからない

```bash
# 解決方法
pytest tests/ --collect-only  # テスト一覧表示
```

#### 問題: カバレッジが低い

```bash
# 解決方法
pytest tests/ --cov=app --cov-report=term-missing
# 未カバーの行を確認
```

---

## 8. 次のステップ

1. **test_gmail.py の実装**
   - Gmail API認証テスト
   - メール送信テスト
   - エラーハンドリングテスト

2. **test_google_calendar.py の実装**
   - カレンダーイベント作成テスト
   - 重複チェックテスト
   - 同期処理テスト

3. **test_ng_keywords.py の実装**
   - NGワードマッチングテスト
   - ホワイトリストテスト
   - 正規表現パターンテスト

4. **CI/CD統合**
   - GitHub Actions設定
   - Codecov連携
   - 自動テスト実行

---

**作成日**: 2025-12-08
**更新日**: 2025-12-08
**QA Engineer Agent**
