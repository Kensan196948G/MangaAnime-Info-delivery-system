# E2E全階層テストガイド

## 概要

MangaAnime-Info-delivery-systemの全階層E2Eエラーチェックシステムです。
すべてのHTMLページ、APIエンドポイント、データベース操作を自動的に検証します。

---

## 📋 チェック対象

### 1. HTMLページ（11ページ）

| パス | 説明 | 期待値 |
|------|------|--------|
| `/` | トップページ | 200 OK |
| `/releases` | リリース一覧 | 200 OK |
| `/calendar` | カレンダー | 200 OK |
| `/config` | 設定 | 200 OK |
| `/watchlist` | ウォッチリスト | 200 OK |
| `/logs` | ログ | 200 OK |
| `/users` | ユーザー管理 | 200 OK |
| `/api-keys` | APIキー管理 | 200 OK |
| `/admin/audit-logs` | 監査ログ | 200 OK |
| `/admin/dashboard` | 管理ダッシュボード | 200 OK |
| `/auth/login` | ログイン | 200 OK |

### 2. APIエンドポイント（10個）

| エンドポイント | メソッド | 説明 |
|---------------|---------|------|
| `/api/stats` | GET | 統計情報 |
| `/api/sources` | GET | ソース一覧 |
| `/api/releases/recent` | GET | 最新リリース |
| `/api/releases/upcoming` | GET | 今後のリリース |
| `/api/works` | GET | 作品一覧 |
| `/api/calendar/events` | GET | カレンダーイベント |
| `/api/collection-status` | GET | コレクション状態 |
| `/health` | GET | ヘルスチェック |
| `/ready` | GET | レディネスチェック |
| `/metrics` | GET | メトリクス（Prometheus形式） |

### 3. チェック項目

- ✅ HTTPステータスコード（200, 302以外はエラー）
- ✅ Pythonトレースバック検出
- ✅ テンプレートレンダリングエラー
- ✅ データベース接続エラー
- ✅ JavaScript致命的エラー（Playwrightのみ）
- ✅ url_for()エンドポイント名検証

---

## 🚀 クイックスタート

### 基本チェック実行

```bash
# シンプルなE2Eチェック
python3 tests/test_e2e_comprehensive.py

# 完全E2Eテストスイート
python3 tests/test_e2e_complete.py
```

### 自動修復付き実行

```bash
# エラー検出 → 修復 → 再チェック
bash scripts/run_e2e_check.sh
```

### Playwrightブラウザテスト

```bash
# Playwrightインストール（初回のみ）
pip install playwright
playwright install

# ブラウザベースE2Eテスト
pytest tests/test_e2e_playwright.py -v
```

---

## 📊 出力形式

### コンソール出力

```
================================================================================
🔍 E2E 全階層エラーチェック開始
================================================================================

📄 HTMLページチェック...
  ✓ トップページ (/)
  ✓ リリース一覧 (/releases)
  ✗ 設定 (/config): 404 Not Found

🔌 APIエンドポイントチェック...
  ✓ 統計情報 (GET /api/stats): OK
  ✓ ソース一覧 (GET /api/sources): OK

================================================================================
📊 E2Eエラーチェック結果
================================================================================

✅ 成功: 15件
⚠️  警告: 2件
❌ エラー: 1件
  ✗ 設定 (/config): 404 Not Found
```

### HTMLレポート

```bash
# HTMLレポート生成
python3 scripts/generate_e2e_report.py

# 生成場所
reports/e2e_report_20250107_143022.html
```

HTMLレポートには以下が含まれます：
- 📊 統計サマリー（成功/失敗/警告件数）
- 📄 ページチェック結果一覧
- 🔌 APIエンドポイント結果一覧
- ❌ エラー詳細
- 💡 推奨事項

---

## 🔧 自動修復機能

### 修復対象

1. **未実装エンドポイント追加**
   - `/health`, `/ready`, `/metrics`
   - `/api/collection-status`

2. **テンプレートエラー修正**
   - `base.html` 作成
   - `auth/login.html` 作成
   - url_for() エンドポイント名修正

3. **ルーティングエラー修正**
   - `routes/__init__.py` 作成
   - Blueprint登録

4. **データベーススキーマ確認**
   - 必須テーブル存在確認
   - インデックス検証

### 手動修復実行

```bash
# バックアップ付き修復
python3 scripts/fix_e2e_errors.py

# バックアップ場所
backups/20250107_143022/
```

---

## 📁 ファイル構成

```
MangaAnime-Info-delivery-system/
├── tests/
│   ├── test_e2e_comprehensive.py    # 基本E2Eチェック
│   ├── test_e2e_complete.py         # 完全E2Eテストスイート
│   └── test_e2e_playwright.py       # Playwrightブラウザテスト
├── scripts/
│   ├── run_e2e_check.sh             # 自動チェック+修復スクリプト
│   ├── fix_e2e_errors.py            # エラー自動修復
│   └── generate_e2e_report.py       # HTMLレポート生成
├── reports/                          # 生成されたレポート
└── backups/                          # 修復前のバックアップ
```

---

## 🎯 使用シナリオ

### シナリオ1: デプロイ前チェック

```bash
# 完全E2Eテスト実行
python3 tests/test_e2e_complete.py

# エラーなし → デプロイOK
# エラーあり → 修復後再テスト
```

### シナリオ2: CI/CDパイプライン

```yaml
# .github/workflows/e2e-test.yml
- name: E2E Test
  run: |
    python3 tests/test_e2e_comprehensive.py
    python3 scripts/generate_e2e_report.py

- name: Upload Report
  uses: actions/upload-artifact@v3
  with:
    name: e2e-report
    path: reports/*.html
```

### シナリオ3: 定期監視

```bash
# crontabに登録
0 */6 * * * cd /path/to/project && python3 tests/test_e2e_comprehensive.py
```

---

## 🐛 トラブルシューティング

### エラー: "ModuleNotFoundError: No module named 'app'"

```bash
# プロジェクトルートから実行
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system
python3 tests/test_e2e_comprehensive.py
```

### エラー: "Playwright not found"

```bash
# Playwrightインストール
pip install playwright
playwright install chromium
```

### エラー: "Database is locked"

```bash
# データベース接続を閉じる
pkill -f web_app.py

# または
rm db.sqlite3-shm db.sqlite3-wal
```

### 警告: "Template not found"

```bash
# テンプレート自動生成
python3 scripts/fix_e2e_errors.py
```

---

## 📈 カバレッジ目標

| カテゴリ | 目標 | 現在 |
|---------|------|------|
| HTMLページ | 100% | - |
| APIエンドポイント | 100% | - |
| データベース操作 | 90% | - |
| エラーハンドリング | 80% | - |

---

## 🔄 継続的改善

### 定期実行

```bash
# 毎日1回実行
0 9 * * * /path/to/scripts/run_e2e_check.sh >> /var/log/e2e_check.log 2>&1
```

### 新機能追加時

1. エンドポイント追加
2. `test_e2e_comprehensive.py` にテスト追加
3. E2Eチェック実行
4. HTMLレポート確認

---

## 📚 参考資料

- [Flask Testing Documentation](https://flask.palletsprojects.com/en/2.3.x/testing/)
- [Playwright Python](https://playwright.dev/python/docs/intro)
- [pytest Documentation](https://docs.pytest.org/)

---

## 📝 メモ

- 初回実行時はデータベースが自動作成されます
- Playwrightテストはヘッドレスモードで実行されます
- 修復実行前に必ずバックアップが作成されます
- HTMLレポートはBootstrap 5でスタイリングされています

---

**最終更新**: 2025-01-07
**バージョン**: 1.0.0
