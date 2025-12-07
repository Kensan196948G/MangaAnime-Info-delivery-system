# E2E全階層テスト - クイックガイド

## 最速実行方法

### 方法1: メニュー形式（推奨）

```bash
bash RUN_E2E_TEST.sh
```

対話形式で実行するテストを選択できます。

---

### 方法2: 直接実行

```bash
# 基本E2Eチェック（5秒程度）
python3 tests/test_e2e_comprehensive.py

# 完全E2Eテストスイート（10秒程度）
python3 tests/test_e2e_complete.py

# 自動修復付き
bash scripts/run_e2e_check.sh
```

---

## 📊 チェック内容

### ✅ 11個のHTMLページ
- `/` - トップページ
- `/releases` - リリース一覧
- `/calendar` - カレンダー
- `/config` - 設定
- `/watchlist` - ウォッチリスト
- `/logs` - ログ
- `/users` - ユーザー管理
- `/api-keys` - APIキー管理
- `/admin/audit-logs` - 監査ログ
- `/admin/dashboard` - 管理ダッシュボード
- `/auth/login` - ログイン

### ✅ 10個のAPIエンドポイント
- `/api/stats` - 統計情報
- `/api/sources` - ソース一覧
- `/api/releases/recent` - 最新リリース
- `/api/releases/upcoming` - 今後のリリース
- `/api/works` - 作品一覧
- `/api/calendar/events` - カレンダーイベント
- `/api/collection-status` - コレクション状態
- `/health` - ヘルスチェック
- `/ready` - レディネスチェック
- `/metrics` - メトリクス

### ✅ エラー検出
- ❌ HTTPステータスコード異常（200, 302以外）
- ❌ Pythonトレースバック
- ❌ テンプレートレンダリングエラー
- ❌ データベース接続エラー
- ❌ JavaScriptエラー（Playwrightのみ）

---

## 🔧 エラーが見つかった場合

### 自動修復

```bash
python3 scripts/fix_e2e_errors.py
```

以下が自動で修正されます：
- 未実装エンドポイント追加
- テンプレートファイル作成
- ルーティング設定
- データベーススキーマ確認

### 手動確認

エラーメッセージを確認して個別対応：

```
❌ エラー: 1件
  ✗ 設定 (/config): 404 Not Found
```

→ `/config` ルートが未実装

---

## 📈 出力例

```
================================================================================
🔍 E2E 全階層エラーチェック開始
================================================================================

📄 HTMLページチェック...
  ✓ トップページ (/)
  ✓ リリース一覧 (/releases)
  ✓ カレンダー (/calendar)
  ✓ 設定 (/config)
  ✓ ウォッチリスト (/watchlist)
  ✓ ログ (/logs)
  ✓ ユーザー管理 (/users)
  ✓ APIキー管理 (/api-keys)
  ✓ 監査ログ (/admin/audit-logs)
  ✓ 管理ダッシュボード (/admin/dashboard)
  ✓ ログイン (/auth/login)

🔌 APIエンドポイントチェック...
  ✓ 統計情報 (GET /api/stats): OK
  ✓ ソース一覧 (GET /api/sources): OK
  ✓ 最新リリース (GET /api/releases/recent): OK
  ✓ 今後のリリース (GET /api/releases/upcoming): OK
  ✓ 作品一覧 (GET /api/works): OK
  ✓ カレンダーイベント (GET /api/calendar/events): OK
  ✓ コレクション状態 (GET /api/collection-status): OK
  ✓ ヘルスチェック (GET /health): OK
  ✓ レディネスチェック (GET /ready): OK
  ✓ メトリクス (GET /metrics): OK

🔐 認証フローチェック...
  ✓ ログインページアクセス可能
  ✓ ログアウト処理正常

💾 データベースチェック...
  ✓ テーブル 'works' 存在 (0件)
  ✓ テーブル 'releases' 存在 (0件)
  ✓ テーブル 'users' 存在 (1件)
  ✓ テーブル 'api_keys' 存在 (0件)
  ✓ テーブル 'audit_logs' 存在 (0件)
  ✓ テーブル 'collection' 存在 (0件)

================================================================================
📊 E2Eエラーチェック結果
================================================================================

✅ 成功: 32件
⚠️  警告: 0件
❌ エラー: 0件

================================================================================
✅ すべてのチェックに合格しました！
================================================================================
```

---

## 📄 HTMLレポート

詳細なHTMLレポートを生成：

```bash
python3 scripts/generate_e2e_report.py
```

生成場所：
```
reports/e2e_report_20250107_143022.html
```

ブラウザで開いて確認：
- 統計サマリー
- ページチェック結果
- APIエンドポイント結果
- エラー詳細
- 推奨事項

---

## 💡 Tips

1. **定期実行**: cronで毎日実行してエラー早期発見
2. **CI/CD統合**: GitHub Actionsでプルリク時に自動実行
3. **レポート保存**: HTMLレポートを保存してトレンド分析
4. **Playwright**: ブラウザテストでJavaScriptエラーも検出

---

**実行時間**: 約5-10秒
**対象**: 全21エンドポイント + データベース
**カバレッジ**: 100%
