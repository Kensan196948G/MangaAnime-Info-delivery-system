# テストケース一覧

**プロジェクト**: MangaAnime-Info-delivery-system
**作成日**: 2025-11-14
**バージョン**: 1.0

---

## 1. セキュリティテストケース

### 1.1 SQLインジェクション対策（SEC-001）

**目的**: SQLインジェクション攻撃からの保護を検証
**優先度**: 高
**前提条件**: アプリケーションが起動している

| ステップ | 操作 | 期待される結果 |
|---------|------|---------------|
| 1 | `' OR '1'='1`をクエリパラメータに送信 | 400または200でエラーハンドリング |
| 2 | `'; DROP TABLE works; --`を送信 | テーブルが削除されない |
| 3 | `1' UNION SELECT * FROM works--`を送信 | 不正なデータが返されない |
| 4 | `admin'--`を送信 | 認証バイパスされない |
| 5 | `' OR 1=1#`を送信 | 全データが露出しない |

**テストファイル**: `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/tests/test_api_security.py::test_sql_injection_protection`

---

### 1.2 XSS対策（SEC-002）

**目的**: クロスサイトスクリプティング攻撃からの保護を検証
**優先度**: 高
**前提条件**: アプリケーションが起動している

| ステップ | 操作 | 期待される結果 |
|---------|------|---------------|
| 1 | `<script>alert('XSS')</script>`を入力 | スクリプトがエスケープされる |
| 2 | `<img src=x onerror=alert('XSS')>`を入力 | スクリプトが実行されない |
| 3 | `javascript:alert('XSS')`を入力 | プロトコルハンドラが無効化される |
| 4 | `<svg/onload=alert('XSS')>`を入力 | SVGイベントが無効化される |

**テストファイル**: `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/tests/test_api_security.py::test_xss_protection`

---

### 1.3 CSRF対策（SEC-003）

**目的**: クロスサイトリクエストフォージェリ攻撃からの保護を検証
**優先度**: 高

| ステップ | 操作 | 期待される結果 |
|---------|------|---------------|
| 1 | CSRFトークンなしでPOSTリクエスト | 400/403エラー |
| 2 | 無効なトークンでPOSTリクエスト | 403エラー |
| 3 | 期限切れトークンでPOSTリクエスト | 403エラー |

**テストファイル**: `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/tests/test_api_security.py::test_csrf_token_validation`

---

### 1.4 認証必須エンドポイント（SEC-004）

**目的**: 認証が必要なエンドポイントの保護を検証
**優先度**: 高
**ステータス**: ⚠️ 要修正

| ステップ | 操作 | 期待される結果 | 現状 |
|---------|------|---------------|------|
| 1 | 認証なしで`/api/manual-collection`にアクセス | 401エラー | 200 OK |
| 2 | 認証なしで`/api/test-notification`にアクセス | 401エラー | 500エラー ❌ |
| 3 | 無効なトークンでアクセス | 401エラー | 未実装 |

**テストファイル**: `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/tests/test_api_security.py::test_authentication_required_endpoints`

**修正推奨事項**:
```python
from functools import wraps

def require_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or not validate_token(token):
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/test-notification', methods=['POST'])
@require_auth
def api_test_notification():
    # 処理
```

---

### 1.5 レート制限（SEC-005）

**目的**: 過度なリクエストからの保護を検証
**優先度**: 中

| ステップ | 操作 | 期待される結果 |
|---------|------|---------------|
| 1 | 50回連続でAPIリクエスト | 全て成功または429エラー |
| 2 | 1分間に100回リクエスト | 429エラーが返される |

**テストファイル**: `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/tests/test_api_security.py::test_rate_limiting`

---

### 1.6 パストラバーサル攻撃対策（SEC-007）

**目的**: ファイルシステムアクセスの不正な試みを防ぐ
**優先度**: 高

| ステップ | 操作 | 期待される結果 |
|---------|------|---------------|
| 1 | `../../../etc/passwd`をパラメータに | 400/404エラー |
| 2 | `..\\..\\..\\windows\\system32\\`を送信 | 400/404エラー |
| 3 | `/etc/shadow`を送信 | 400/404エラー |

**テストファイル**: `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/tests/test_api_security.py::test_path_traversal_protection`

---

## 2. API機能テストケース

### 2.1 手動データ収集（API-001）

**目的**: 手動でデータ収集をトリガーできることを検証
**優先度**: 高

| ステップ | 操作 | 期待される結果 |
|---------|------|---------------|
| 1 | POST `/api/manual-collection` | 200/202 OK |
| 2 | `source: 'anilist'`を指定 | AniListからデータ収集 |
| 3 | レスポンスJSON確認 | `status`または`message`フィールド存在 |

**テストファイル**: `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/tests/test_data_update_api.py::test_manual_collection_endpoint`

---

### 2.2 作品一覧取得（API-002）

**目的**: 登録されている作品の一覧を取得できることを検証
**優先度**: 高

| ステップ | 操作 | 期待される結果 |
|---------|------|---------------|
| 1 | GET `/api/works` | 200 OK |
| 2 | レスポンスJSON確認 | 配列またはオブジェクト |
| 3 | 作品データの構造確認 | `id`, `title`, `type`フィールド存在 |

**テストファイル**: `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/tests/test_data_update_api.py::test_works_api_get`

---

### 2.3 作品フィルタリング（API-003）

**目的**: タイプ別に作品をフィルタリングできることを検証
**優先度**: 中

| ステップ | 操作 | 期待される結果 |
|---------|------|---------------|
| 1 | GET `/api/works?type=anime` | 200 OK |
| 2 | 結果を確認 | 全作品の`type`が`anime` |
| 3 | GET `/api/works?type=manga` | 200 OK |
| 4 | 結果を確認 | 全作品の`type`が`manga` |

**テストファイル**: `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/tests/test_data_update_api.py::test_works_api_filtering`

---

### 2.4 作品検索（API-004）

**目的**: キーワードで作品を検索できることを検証
**優先度**: 中

| ステップ | 操作 | 期待される結果 |
|---------|------|---------------|
| 1 | GET `/api/works?search=test` | 200 OK |
| 2 | GET `/api/works?search=anime` | 200 OK |
| 3 | GET `/api/works?search=進撃` | 200 OK |
| 4 | 日本語検索の動作確認 | 適切な結果が返される |

**テストファイル**: `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/tests/test_data_update_api.py::test_works_api_search`

---

### 2.5 作品詳細取得（API-005）

**目的**: 特定の作品の詳細情報を取得できることを検証
**優先度**: 高
**ステータス**: ⚠️ 要修正（テストDB分離）

| ステップ | 操作 | 期待される結果 |
|---------|------|---------------|
| 1 | テスト作品をDBに挿入 | 挿入成功 |
| 2 | GET `/api/works/{work_id}` | 200 OK |
| 3 | レスポンスデータ確認 | タイトルが一致 |
| 4 | リリース情報確認 | 関連リリースが含まれる |

**テストファイル**: `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/tests/test_data_update_api.py::test_work_detail_api`

---

### 2.6 統計情報取得（API-007）

**目的**: システム統計情報を取得できることを検証
**優先度**: 中

| ステップ | 操作 | 期待される結果 |
|---------|------|---------------|
| 1 | GET `/api/stats` | 200 OK |
| 2 | レスポンス確認 | `total_works`フィールド存在 |
| 3 | レスポンス確認 | `total_releases`フィールド存在 |
| 4 | データ型確認 | 数値型である |

**テストファイル**: `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/tests/test_data_update_api.py::test_stats_api`

---

### 2.7 ページネーション（API-012）

**目的**: 大量データのページング処理を検証
**優先度**: 中

| ステップ | 操作 | 期待される結果 |
|---------|------|---------------|
| 1 | GET `/api/works?page=1&per_page=10` | 200 OK |
| 2 | 結果件数確認 | 最大10件 |
| 3 | GET `/api/works?page=2&per_page=10` | 200 OK |
| 4 | ページ間のデータ重複確認 | 重複なし |

**テストファイル**: `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/tests/test_data_update_api.py::test_pagination_support`

---

### 2.8 エラーハンドリング（API-010, API-011）

**目的**: 不正なリクエストが適切にハンドリングされることを検証
**優先度**: 高

| ステップ | 操作 | 期待される結果 |
|---------|------|---------------|
| 1 | GET `/api/works/99999` | 404 Not Found |
| 2 | POST `/api/manual-collection` (無効JSON) | 400 Bad Request |
| 3 | GET `/api/works/invalid_id` | 400 Bad Request |

**テストファイル**: `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/tests/test_data_update_api.py::test_error_handling_*`

---

## 3. パフォーマンステストケース

### 3.1 APIレスポンスタイム（PERF-001, 002, 003）

**目的**: APIのレスポンスタイムが要件を満たすことを検証
**優先度**: 高

| エンドポイント | 目標時間 | テストケース |
|--------------|---------|-------------|
| `/api/stats` | < 2.0秒 | `test_api_response_time_stats` |
| `/api/works` | < 3.0秒 | `test_api_response_time_works` |
| `/api/releases/recent` | < 2.0秒 | `test_api_response_time_recent_releases` |

**テストファイル**: `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/tests/test_performance_qa.py`

---

### 3.2 データベースクエリパフォーマンス（PERF-004）

**目的**: データベース操作のパフォーマンスを検証
**優先度**: 高

| 操作 | データ量 | 目標時間 | テストケース |
|-----|---------|---------|-------------|
| 挿入 | 1,000件 | < 10秒 | `test_database_query_performance` |
| 検索 | 1,000件 | < 1秒 | 同上 |
| 更新 | 100回 | < 2秒 | `test_data_update_performance` |
| 結合 | 300件 | < 1秒 | `test_join_query_performance` |

**テストファイル**: `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/tests/test_performance_qa.py`

---

### 3.3 同時アクセステスト（PERF-005）

**目的**: 並列リクエストを適切に処理できることを検証
**優先度**: 高
**ステータス**: ⚠️ 要修正（Flask context問題）

| ステップ | 操作 | 期待される結果 |
|---------|------|---------------|
| 1 | 20並列で`/api/stats`にリクエスト | 全て200 OK |
| 2 | 平均レスポンスタイム確認 | < 3.0秒 |
| 3 | エラー発生確認 | エラーなし |

**テストファイル**: `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/tests/test_performance_qa.py::test_concurrent_api_requests`

**修正推奨事項**: GunicornまたはuWSGIを使用した本番環境での再テスト

---

### 3.4 大量データ処理（PERF-006）

**目的**: 大量のデータを効率的に処理できることを検証
**優先度**: 中

| ステップ | 操作 | 期待される結果 |
|---------|------|---------------|
| 1 | 500件のデータを挿入 | < 5秒 |
| 2 | ページネーション実行 | < 2秒 |
| 3 | 検索実行（200件中） | < 2秒 |

**テストファイル**: `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/tests/test_performance_qa.py::test_large_dataset_pagination`

---

### 3.5 インデックス効率（PERF-011）

**目的**: データベースインデックスが適切に機能することを検証
**優先度**: 中

| ステップ | 操作 | 期待される結果 |
|---------|------|---------------|
| 1 | インデックス作成 | 成功 |
| 2 | 1,000件データ挿入 | < 5秒 |
| 3 | インデックス使用クエリ実行 | < 0.5秒 |

**テストファイル**: `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/tests/test_performance_qa.py::test_index_usage`

---

## 4. フロントエンドUIテストケース

### 4.1 ページレンダリング（UI-001）

**目的**: 全ページが正常にレンダリングされることを検証
**優先度**: 高
**ステータス**: ⏳ 保留（BeautifulSoup4インストール必要）

| ステップ | 操作 | 期待される結果 |
|---------|------|---------------|
| 1 | GET `/` | 200 OK、HTMLが返される |
| 2 | GET `/works` | 200 OK |
| 3 | GET `/calendar` | 200 OK |
| 4 | GET `/config` | 200 OK |

**テストファイル**: `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/tests/test_frontend_ui.py::test_*_page`

---

### 4.2 レスポンシブデザイン（UI-002）

**目的**: レスポンシブデザインが実装されていることを検証
**優先度**: 中

| ステップ | 操作 | 期待される結果 |
|---------|------|---------------|
| 1 | viewportメタタグ確認 | `width=device-width`が設定 |
| 2 | モバイルメニュー確認 | ハンバーガーメニュー存在 |
| 3 | レスポンシブCSSクラス確認 | Bootstrap等のクラス使用 |

**テストファイル**: `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/tests/test_frontend_ui.py::test_responsive_meta_tags`

---

### 4.3 アクセシビリティ（UI-003）

**目的**: アクセシビリティ基準を満たしていることを検証
**優先度**: 中

| ステップ | 操作 | 期待される結果 |
|---------|------|---------------|
| 1 | 全画像のalt属性確認 | alt属性が設定されている |
| 2 | フォームラベル確認 | labelまたはaria-label設定 |
| 3 | キーボードナビゲーション確認 | Tab移動可能 |

**テストファイル**: `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/tests/test_frontend_ui.py::test_accessibility_*`

---

## 5. テスト実行手順

### 5.1 環境準備

```bash
# 依存パッケージインストール
pip install pytest pytest-cov beautifulsoup4 lxml

# プロジェクトディレクトリに移動
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system
```

### 5.2 個別テスト実行

```bash
# セキュリティテストのみ
pytest tests/test_api_security.py -v

# API機能テストのみ
pytest tests/test_data_update_api.py -v

# パフォーマンステストのみ
pytest tests/test_performance_qa.py -v

# UIテストのみ
pytest tests/test_frontend_ui.py -v
```

### 5.3 全テスト実行

```bash
# 全テストを実行
pytest tests/ -v

# 詳細なレポート付き
pytest tests/ -v --tb=short --html=test_report.html

# カバレッジ付き
pytest tests/ --cov=app --cov=modules --cov-report=html
```

### 5.4 特定のテストケースのみ実行

```bash
# 特定のテストクラスのみ
pytest tests/test_api_security.py::TestAPISecurity -v

# 特定のテストメソッドのみ
pytest tests/test_api_security.py::TestAPISecurity::test_sql_injection_protection -v
```

---

## 6. テストデータ管理

### 6.1 テストデータベース

```sql
-- テスト用データベース初期化
CREATE TABLE IF NOT EXISTS works (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    type TEXT CHECK(type IN ('anime','manga')),
    official_url TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS releases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    work_id INTEGER NOT NULL,
    release_type TEXT CHECK(release_type IN ('episode','volume')),
    number TEXT,
    release_date DATE,
    notified INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 6.2 テストフィクスチャ

```python
@pytest.fixture
def test_db(tmp_path):
    """一時的なテストデータベースを作成"""
    db_path = tmp_path / "test.db"
    # データベース初期化処理
    yield str(db_path)
```

---

## 7. 継続的インテグレーション

### 7.1 GitHub Actions設定例

```yaml
# .github/workflows/test.yml
name: Run Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest beautifulsoup4
      - name: Run tests
        run: pytest tests/ -v
```

---

**文書管理**
- 作成日: 2025-11-14
- 最終更新: 2025-11-14
- 次回レビュー: 2025-11-21
