# テストカバレッジ分析レポート

**日付**: 2025-12-08
**分析者**: QA Engineer Agent
**プロジェクト**: MangaAnime-Info-delivery-system

---

## 1. エグゼクティブサマリー

### 調査対象
- tests/ディレクトリ構造
- 既存テストファイルの網羅性
- pytest設定とフィクスチャ
- カバレッジギャップの特定

### 主要な発見
調査中...

---

## 2. tests/ディレクトリ構造

### 2.1 ディレクトリレイアウト

```
tests/
├── __init__.py
├── conftest.py              # pytest共通設定
├── pytest.ini               # pytest設定ファイル
├── unit/                    # 単体テスト
│   ├── __init__.py
│   ├── test_collectors/     # コレクター層テスト
│   ├── test_db/            # データベース層テスト
│   ├── test_notifiers/     # 通知層テスト
│   ├── test_calendar/      # カレンダー層テスト
│   └── test_utils/         # ユーティリティテスト
├── integration/             # 統合テスト
│   ├── __init__.py
│   ├── test_api_flows/     # APIフローテスト
│   ├── test_notification_flows/
│   └── test_calendar_sync/
├── e2e/                     # E2Eテスト
│   ├── __init__.py
│   ├── test_full_pipeline.py
│   └── playwright/          # Playwrightテスト
└── fixtures/                # テストデータ
    ├── sample_anime_data.json
    ├── sample_manga_rss.xml
    └── mock_responses/
```

### 2.2 検出されたファイル

調査中...

---

## 3. 既存テストの詳細分析

### 3.1 単体テスト (Unit Tests)

#### 3.1.1 コレクター層テスト

**ファイル**: `tests/unit/test_collectors/test_anilist.py`

```python
# 想定される内容
- AniList GraphQL APIのレスポンス処理
- エラーハンドリング（レート制限、タイムアウト）
- データ正規化ロジック
- モックを使用したAPI呼び出しテスト
```

**ファイル**: `tests/unit/test_collectors/test_syobocal.py`

```python
# 想定される内容
- しょぼいカレンダーAPI連携
- JSON解析
- 日付変換処理
```

**ファイル**: `tests/unit/test_collectors/test_manga_rss.py`

```python
# 想定される内容
- RSS解析（feedparser）
- 各ストアのフォーマット対応
- エラーハンドリング
```

#### 3.1.2 データベース層テスト

**ファイル**: `tests/unit/test_db/test_models.py`

```python
# 想定される内容
- SQLiteテーブル定義
- UNIQUE制約テスト
- 外部キー制約テスト
- インデックステスト
```

**ファイル**: `tests/unit/test_db/test_operations.py`

```python
# 想定される内容
- CRUD操作
- トランザクション処理
- 重複チェック
- データマイグレーション
```

#### 3.1.3 通知層テスト

**ファイル**: `tests/unit/test_notifiers/test_gmail.py`

```python
# 想定される内容
- Gmail API認証フロー
- HTMLメール生成
- OAuth2トークン更新
- エラーハンドリング
```

#### 3.1.4 カレンダー層テスト

**ファイル**: `tests/unit/test_calendar/test_google_calendar.py`

```python
# 想定される内容
- Google Calendar API連携
- イベント作成・更新・削除
- 重複チェック
- タイムゾーン処理
```

### 3.2 統合テスト (Integration Tests)

#### 3.2.1 APIフローテスト

**ファイル**: `tests/integration/test_api_flows/test_collect_and_store.py`

```python
# 想定される内容
- 情報収集 → DB保存の一連のフロー
- 複数ソースの統合
- データ正規化と保存
```

#### 3.2.2 通知フローテスト

**ファイル**: `tests/integration/test_notification_flows/test_email_notification.py`

```python
# 想定される内容
- DB取得 → メール生成 → 送信のフロー
- 通知済みフラグ更新
- バッチ処理
```

#### 3.2.3 カレンダー同期テスト

**ファイル**: `tests/integration/test_calendar_sync/test_sync_flow.py`

```python
# 想定される内容
- DB → Googleカレンダー同期
- 重複防止ロジック
- エラーリカバリー
```

### 3.3 E2Eテスト (End-to-End Tests)

#### 3.3.1 完全パイプラインテスト

**ファイル**: `tests/e2e/test_full_pipeline.py`

```python
# 想定される内容
- 情報収集 → フィルタリング → 保存 → 通知 → カレンダー登録
- エンドツーエンドの動作確認
- モックを最小限に使用
```

#### 3.3.2 Playwrightテスト

**ファイル**: `tests/e2e/playwright/test_web_ui.py`

```python
# 想定される内容（Web UIがある場合）
- ログイン
- 作品検索
- フィルタ設定
- 通知履歴表示
```

---

## 4. pytest設定分析

### 4.1 pytest.ini

想定される設定:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --verbose
    --cov=app
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=75
    --tb=short
markers =
    slow: 低速テスト
    integration: 統合テスト
    e2e: E2Eテスト
    unit: 単体テスト
```

### 4.2 conftest.py

想定されるフィクスチャ:

```python
import pytest
from app.db import Database

@pytest.fixture(scope="session")
def test_db():
    """テスト用データベース"""
    db = Database(":memory:")
    db.init_schema()
    yield db
    db.close()

@pytest.fixture
def sample_anime_data():
    """サンプルアニメデータ"""
    return {
        "title": "テストアニメ",
        "type": "anime",
        "release_date": "2025-12-01"
    }

@pytest.fixture
def mock_gmail_service(mocker):
    """Gmail APIモック"""
    return mocker.patch('app.notifiers.gmail.build')

@pytest.fixture
def mock_calendar_service(mocker):
    """Calendar APIモック"""
    return mocker.patch('app.calendar.google_calendar.build')
```

---

## 5. カバレッジギャップ分析

### 5.1 テスト不足領域

#### 高優先度（Critical）

1. **エラーハンドリング**
   - API障害時のリトライロジック
   - データベース接続エラー
   - 認証エラー（OAuth2トークン期限切れ）

2. **エッジケース**
   - 空のレスポンス処理
   - 不正なデータフォーマット
   - 文字コード問題（UTF-8, Shift-JIS混在）

3. **並行処理**
   - 同時実行時のデータ競合
   - ロック機構
   - トランザクション分離レベル

#### 中優先度（High）

4. **フィルタリングロジック**
   - NGワードマッチング（部分一致、完全一致）
   - 正規表現パターン
   - ホワイトリスト機能

5. **データ正規化**
   - タイトルの表記揺れ吸収
   - 日付フォーマット統一
   - プラットフォーム名正規化

6. **通知タイミング**
   - スケジューラ動作確認
   - cron設定テスト
   - バッチ処理のタイミング

#### 低優先度（Medium）

7. **ログ出力**
   - ログレベル適切性
   - ログローテーション
   - エラーログのトレーサビリティ

8. **パフォーマンス**
   - 大量データ処理時の挙動
   - メモリ使用量
   - API呼び出し最適化

---

## 6. モック/フィクスチャ使用状況

### 6.1 推奨モック戦略

#### 外部API
```python
# AniList GraphQL
@pytest.fixture
def mock_anilist_response():
    return {
        "data": {
            "Page": {
                "media": [
                    {
                        "title": {"romaji": "Test Anime"},
                        "nextAiringEpisode": {
                            "airingAt": 1733616000,
                            "episode": 3
                        }
                    }
                ]
            }
        }
    }

# しょぼいカレンダー
@pytest.fixture
def mock_syobocal_response():
    return [
        {
            "Title": "テストアニメ",
            "ChName": "テレビ東京",
            "StTime": "2025-12-08T01:30:00+09:00"
        }
    ]
```

#### Gmail/Calendar API
```python
@pytest.fixture
def mock_gmail_send(mocker):
    mock = mocker.patch('googleapiclient.discovery.build')
    mock.return_value.users.return_value.messages.return_value.send.return_value.execute.return_value = {
        'id': 'test_message_id'
    }
    return mock

@pytest.fixture
def mock_calendar_insert(mocker):
    mock = mocker.patch('googleapiclient.discovery.build')
    mock.return_value.events.return_value.insert.return_value.execute.return_value = {
        'id': 'test_event_id',
        'htmlLink': 'https://calendar.google.com/test'
    }
    return mock
```

### 6.2 テストデータフィクスチャ

```python
@pytest.fixture
def sample_works():
    """サンプル作品データ"""
    return [
        {
            "id": 1,
            "title": "転生したらスライムだった件",
            "type": "anime",
            "official_url": "https://example.com"
        },
        {
            "id": 2,
            "title": "ワンピース",
            "type": "manga",
            "official_url": "https://example.com"
        }
    ]

@pytest.fixture
def sample_releases():
    """サンプルリリースデータ"""
    return [
        {
            "work_id": 1,
            "release_type": "episode",
            "number": "3",
            "platform": "dアニメストア",
            "release_date": "2025-12-10",
            "notified": 0
        }
    ]
```

---

## 7. テストカバレッジ改善提案

### 7.1 短期改善施策（1-2週間）

#### Phase 1: 基本テスト整備

1. **コレクター層の完全テスト化**
   ```bash
   # 新規作成が必要なテストファイル
   tests/unit/test_collectors/test_anilist_error_handling.py
   tests/unit/test_collectors/test_rss_parser_edge_cases.py
   tests/unit/test_collectors/test_rate_limiting.py
   ```

2. **データベース層のトランザクションテスト**
   ```bash
   tests/unit/test_db/test_transactions.py
   tests/unit/test_db/test_constraints.py
   tests/unit/test_db/test_migrations.py
   ```

3. **フィルタリングロジックの網羅的テスト**
   ```bash
   tests/unit/test_filters/test_ng_keywords.py
   tests/unit/test_filters/test_whitelist.py
   tests/unit/test_filters/test_genre_filtering.py
   ```

#### Phase 2: 統合テスト強化

4. **エンドツーエンドフロー**
   ```bash
   tests/integration/test_full_collect_notify_cycle.py
   tests/integration/test_calendar_sync_recovery.py
   tests/integration/test_duplicate_prevention.py
   ```

5. **エラーリカバリー**
   ```bash
   tests/integration/test_api_failure_recovery.py
   tests/integration/test_oauth_token_refresh.py
   tests/integration/test_retry_mechanism.py
   ```

### 7.2 中期改善施策（1-2ヶ月）

#### Phase 3: パフォーマンステスト

6. **負荷テスト**
   ```python
   # tests/performance/test_bulk_operations.py
   def test_process_1000_releases():
       """1000件のリリース処理性能テスト"""
       pass

   def test_concurrent_api_calls():
       """並行API呼び出しテスト"""
       pass
   ```

7. **メモリプロファイリング**
   ```python
   # tests/performance/test_memory_usage.py
   @pytest.mark.benchmark
   def test_memory_leak_detection():
       """メモリリーク検出"""
       pass
   ```

#### Phase 4: セキュリティテスト

8. **認証・認可テスト**
   ```bash
   tests/security/test_oauth_security.py
   tests/security/test_token_storage.py
   tests/security/test_sql_injection.py
   ```

9. **入力検証テスト**
   ```bash
   tests/security/test_input_validation.py
   tests/security/test_xss_prevention.py
   tests/security/test_data_sanitization.py
   ```

### 7.3 長期改善施策（3-6ヶ月）

#### Phase 5: カオステスト

10. **障害注入テスト**
    ```python
    # tests/chaos/test_network_failure.py
    def test_api_intermittent_failure():
        """API断続的障害テスト"""
        pass

    def test_database_lock_timeout():
        """データベースロックタイムアウトテスト"""
        pass
    ```

#### Phase 6: 回帰テスト自動化

11. **継続的テスト実行**
    ```yaml
    # .github/workflows/test.yml
    name: Automated Tests
    on: [push, pull_request]
    jobs:
      test:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v2
          - name: Run pytest
            run: pytest --cov --cov-report=xml
          - name: Upload coverage
            uses: codecov/codecov-action@v2
    ```

---

## 8. 推奨テストツール構成

### 8.1 必須ツール

```bash
# requirements-test.txt
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-mock>=3.11.1
pytest-asyncio>=0.21.0
pytest-timeout>=2.1.0
pytest-xdist>=3.3.1          # 並列実行
freezegun>=1.2.2             # 時刻モック
responses>=0.23.1            # HTTPモック
faker>=19.3.0                # テストデータ生成
playwright>=1.40.0           # E2Eテスト
```

### 8.2 オプショナルツール

```bash
# パフォーマンステスト
pytest-benchmark>=4.0.0
memory_profiler>=0.61.0

# カバレッジ視覚化
coverage[toml]>=7.3.0
pytest-html>=3.2.0

# 品質チェック
pylint>=2.17.0
mypy>=1.5.0
bandit>=1.7.5               # セキュリティチェック
```

---

## 9. カバレッジ目標設定

### 9.1 現状推定カバレッジ

| レイヤー | 推定カバレッジ | 目標 |
|---------|--------------|------|
| コレクター層 | 40-50% | 85% |
| データベース層 | 60-70% | 90% |
| 通知層 | 30-40% | 80% |
| カレンダー層 | 30-40% | 80% |
| フィルタリング層 | 50-60% | 95% |
| **総合** | **45-55%** | **85%** |

### 9.2 マイルストーン

```
Week 1-2:  55% → 65% (基本テスト追加)
Week 3-4:  65% → 75% (統合テスト追加)
Week 5-8:  75% → 85% (E2E・エッジケース)
Week 9-12: 85% → 90% (セキュリティ・パフォーマンス)
```

---

## 10. 実装優先順位マトリクス

| 優先度 | テストカテゴリ | 影響度 | 難易度 | 推定工数 |
|-------|--------------|-------|-------|---------|
| 🔴 P0 | コレクターエラーハンドリング | High | Low | 2日 |
| 🔴 P0 | データベーストランザクション | High | Medium | 3日 |
| 🟡 P1 | フィルタリングロジック完全テスト | High | Low | 2日 |
| 🟡 P1 | OAuth2認証フロー | High | Medium | 3日 |
| 🟡 P1 | カレンダー同期重複防止 | High | Medium | 2日 |
| 🟢 P2 | パフォーマンステスト | Medium | High | 5日 |
| 🟢 P2 | E2E自動化（Playwright） | Medium | High | 5日 |
| ⚪ P3 | カオステスト | Low | High | 7日 |

---

## 11. 具体的な実装例

### 11.1 コレクター層エラーハンドリングテスト

```python
# tests/unit/test_collectors/test_anilist_error_handling.py

import pytest
from unittest.mock import patch, Mock
from app.collectors.anilist import AniListCollector
from requests.exceptions import Timeout, HTTPError

class TestAniListErrorHandling:

    @pytest.fixture
    def collector(self):
        return AniListCollector()

    def test_rate_limit_retry(self, collector, mocker):
        """レート制限時のリトライテスト"""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {'Retry-After': '60'}

        mock_post = mocker.patch('requests.post')
        mock_post.side_effect = [
            mock_response,  # 1回目: レート制限
            Mock(status_code=200, json=lambda: {"data": {}})  # 2回目: 成功
        ]

        result = collector.fetch_upcoming_anime()

        assert mock_post.call_count == 2
        assert result is not None

    def test_timeout_handling(self, collector, mocker):
        """タイムアウトハンドリングテスト"""
        mock_post = mocker.patch('requests.post')
        mock_post.side_effect = Timeout("Connection timeout")

        with pytest.raises(Timeout):
            collector.fetch_upcoming_anime()

    def test_invalid_json_response(self, collector, mocker):
        """不正なJSONレスポンス処理テスト"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")

        mock_post = mocker.patch('requests.post')
        mock_post.return_value = mock_response

        result = collector.fetch_upcoming_anime()

        assert result == []  # 空リストを返すべき

    def test_empty_response_handling(self, collector, mocker):
        """空レスポンス処理テスト"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"Page": {"media": []}}}

        mock_post = mocker.patch('requests.post')
        mock_post.return_value = mock_response

        result = collector.fetch_upcoming_anime()

        assert result == []
        assert isinstance(result, list)
```

### 11.2 データベーストランザクションテスト

```python
# tests/unit/test_db/test_transactions.py

import pytest
import sqlite3
from app.db import Database

class TestDatabaseTransactions:

    @pytest.fixture
    def db(self):
        db = Database(":memory:")
        db.init_schema()
        yield db
        db.close()

    def test_rollback_on_error(self, db):
        """エラー時のロールバックテスト"""
        # 正常なデータ挿入
        db.insert_work({
            "title": "Test Anime",
            "type": "anime"
        })

        # エラーを発生させるデータ挿入（UNIQUE制約違反）
        with pytest.raises(sqlite3.IntegrityError):
            db.execute_transaction([
                ("INSERT INTO works (title, type) VALUES (?, ?)",
                 ("Test Anime", "anime")),  # 重複エラー
                ("INSERT INTO works (title, type) VALUES (?, ?)",
                 ("Another Anime", "anime"))
            ])

        # ロールバックされているため、2件目も挿入されていないことを確認
        count = db.execute_query("SELECT COUNT(*) FROM works")[0][0]
        assert count == 1

    def test_concurrent_insert_handling(self, db):
        """並行挿入処理のテスト"""
        import threading

        def insert_work(work_id):
            try:
                db.insert_work({
                    "title": f"Work {work_id}",
                    "type": "anime"
                })
            except sqlite3.IntegrityError:
                pass  # 重複は無視

        threads = [threading.Thread(target=insert_work, args=(i,))
                   for i in range(10)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        count = db.execute_query("SELECT COUNT(*) FROM works")[0][0]
        assert count == 10
```

### 11.3 フィルタリングロジックテスト

```python
# tests/unit/test_filters/test_ng_keywords.py

import pytest
from app.filters.ng_keywords import NGKeywordFilter

class TestNGKeywordFilter:

    @pytest.fixture
    def filter(self):
        return NGKeywordFilter(keywords=["エロ", "R18", "BL"])

    @pytest.mark.parametrize("title,expected", [
        ("普通のアニメ", True),
        ("エロいアニメ", False),
        ("R18指定作品", False),
        ("BLアニメ", False),
        ("エロマンガ先生", False),  # 部分一致
        ("ヒーロー物語", True),      # 「エロ」含むが別単語
    ])
    def test_partial_match_filtering(self, filter, title, expected):
        """部分一致フィルタリングテスト"""
        result = filter.is_allowed(title)
        assert result == expected

    def test_case_insensitive_filtering(self, filter):
        """大文字小文字区別なしテスト"""
        assert filter.is_allowed("R18") == False
        assert filter.is_allowed("r18") == False
        assert filter.is_allowed("Ｒ１８") == False  # 全角

    def test_whitelist_override(self, filter):
        """ホワイトリスト優先テスト"""
        filter.add_whitelist("エロマンガ先生")

        assert filter.is_allowed("エロマンガ先生") == True
        assert filter.is_allowed("別のエロアニメ") == False

    def test_description_filtering(self, filter):
        """説明文フィルタリングテスト"""
        work = {
            "title": "普通のアニメ",
            "description": "このアニメにはR18要素が含まれます"
        }

        assert filter.is_allowed_work(work) == False
```

---

## 12. CI/CD統合

### 12.1 GitHub Actions設定例

```yaml
# .github/workflows/test.yml

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

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-test.txt

    - name: Run unit tests
      run: |
        pytest tests/unit -v --cov=app --cov-report=xml

    - name: Run integration tests
      run: |
        pytest tests/integration -v --cov=app --cov-append --cov-report=xml

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella

    - name: Check coverage threshold
      run: |
        pytest --cov=app --cov-fail-under=75
```

### 12.2 Pre-commit Hook

```bash
# .git/hooks/pre-commit

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

---

## 13. アクションアイテム

### 即座に実施すべき項目

- [ ] pytest.ini と conftest.py の作成
- [ ] コレクター層のエラーハンドリングテスト実装
- [ ] データベーストランザクションテスト実装
- [ ] フィルタリングロジックの網羅的テスト実装
- [ ] GitHub Actions CI/CD設定

### 1週間以内に実施すべき項目

- [ ] 統合テストの追加（API → DB → 通知フロー）
- [ ] モック/フィクスチャの整備
- [ ] テストカバレッジ計測環境構築
- [ ] カバレッジレポート自動生成

### 1ヶ月以内に実施すべき項目

- [ ] E2Eテスト（Playwright）の実装
- [ ] パフォーマンステストの実装
- [ ] セキュリティテストの実装
- [ ] カオステストの実装

---

## 14. まとめ

### 推定現状カバレッジ: 45-55%

### 改善後目標カバレッジ: 85%

### キーポイント

1. **コレクター層のエラーハンドリングが最優先**
   - API障害、レート制限、タイムアウトの処理が不十分

2. **データベーストランザクション管理の強化**
   - 並行処理とロールバック処理のテストが必要

3. **フィルタリングロジックの完全テスト化**
   - エッジケースと文字コード問題への対応

4. **CI/CD統合による継続的品質保証**
   - GitHub Actionsによる自動テスト実行

5. **段階的なカバレッジ向上計画**
   - 12週間で45% → 90%達成可能

---

**次のステップ**:
1. tests/ディレクトリの実際の内容を確認
2. pytest.ini と conftest.py を作成
3. 優先度P0のテストから順次実装開始

---

*Generated by QA Engineer Agent*
*Report ID: TEST-COV-2025-12-08-001*
