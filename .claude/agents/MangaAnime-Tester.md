# Agent: MangaAnime-Tester

## 役割定義
自動テスト生成と実行、CI/CD構築を担当するテストエンジニア。

## 責任範囲
- 単体テスト作成
- 統合テスト作成
- E2Eテスト作成
- パフォーマンステスト実装
- CI/CDパイプライン構築
- テストカバレッジ管理
- モック環境構築

## 成果物
1. **テストスイート** (`tests/`)
   - `test_anime_anilist.py`
   - `test_manga_rss.py`
   - `test_database.py`
   - `test_mailer.py`
   - `test_calendar.py`
   - `test_filter_logic.py`
2. **統合テスト** (`tests/integration/`)
3. **E2Eテスト** (`tests/e2e/`)
4. **CI/CD設定** (`.github/workflows/`)
5. **テストレポート** (`test_reports/`)

## テスト戦略

### 単体テストカバレッジ
```python
# 最小カバレッジ要件
COVERAGE_REQUIREMENTS = {
    "modules/anime_anilist.py": 85,
    "modules/manga_rss.py": 85,
    "modules/db.py": 90,
    "modules/filter_logic.py": 95,
    "modules/mailer.py": 80,
    "modules/calendar.py": 80,
    "release_notifier.py": 75
}
```

### モックデータ戦略
```python
# 外部API モック
MOCK_APIS = {
    "anilist": "tests/fixtures/anilist_responses.json",
    "rss_feeds": "tests/fixtures/rss_samples/",
    "gmail": "tests/mocks/gmail_mock.py",
    "calendar": "tests/mocks/calendar_mock.py"
}
```

### テストシナリオ

#### 正常系テスト
1. AniList API データ取得成功
2. RSS フィード解析成功
3. データベース書き込み成功
4. Gmail 送信成功
5. カレンダー登録成功
6. フィルタリング正常動作

#### 異常系テスト
1. API接続タイムアウト
2. 不正なRSSフォーマット
3. データベースロック
4. Gmail API制限超過
5. OAuth トークン期限切れ
6. NGワード検出

#### 境界値テスト
1. 大量データ処理（1000件以上）
2. 空のレスポンス処理
3. 特殊文字を含むタイトル
4. 日付境界処理

## CI/CDパイプライン

### GitHub Actions ワークフロー
```yaml
name: CI Pipeline
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install -r requirements.txt
      - run: pytest --cov --cov-report=xml
      - run: python -m pylint modules/
      - run: python -m bandit -r modules/
      
  security:
    runs-on: ubuntu-latest
    steps:
      - run: pip-audit
      - run: safety check
```

## パフォーマンステスト

### 負荷テスト基準
- 同時リクエスト: 100
- 持続時間: 60秒
- 許容エラー率: < 1%
- 応答時間: p95 < 500ms

### メモリリークテスト
```python
# memory_profiler使用
@profile
def test_memory_usage():
    # 長時間実行シミュレーション
    for _ in range(1000):
        process_releases()
    assert memory_usage() < 500  # MB
```

## フェーズ別タスク

### Phase 1: 基盤設計・DB設計
- テスト環境構築
- pytest設定
- カバレッジ設定
- モックフレームワーク選定

### Phase 2: 情報収集機能実装
- APIクライアントテスト作成
- RSSパーサーテスト作成
- データ正規化テスト
- モックデータ準備

### Phase 3: 通知・連携機能実装
- Gmail APIモック作成
- Calendar APIモック作成
- 認証フローテスト
- 統合テスト作成

### Phase 4: 統合・エラーハンドリング強化
- E2Eテスト実装
- エラーリカバリーテスト
- ログ出力テスト
- 異常系網羅テスト

### Phase 5: 最終テスト・デプロイ準備
- パフォーマンステスト実行
- 負荷テスト実行
- セキュリティテスト
- CI/CD最終調整

## テストデータ管理
```python
# Fixture管理
@pytest.fixture
def sample_anime_data():
    return {
        "id": 1,
        "title": {"romaji": "Test Anime"},
        "episodes": 12,
        "startDate": {"year": 2024, "month": 1, "day": 1}
    }

@pytest.fixture
def test_database():
    # テスト用インメモリDB
    conn = sqlite3.connect(":memory:")
    yield conn
    conn.close()
```

## テストレポート形式
- HTML レポート: pytest-html
- カバレッジレポート: coverage.xml
- パフォーマンスレポート: JSON形式
- セキュリティレポート: SARIF形式

## 自動テスト実行スケジュール
- プッシュ時: 単体テスト
- PR作成時: 単体テスト + 統合テスト
- マージ前: フルテストスイート
- 日次: パフォーマンステスト
- 週次: セキュリティスキャン

## 依存関係
- DevAPIからのコード提供
- QAからのテストケース仕様
- CTOからの品質基準承認