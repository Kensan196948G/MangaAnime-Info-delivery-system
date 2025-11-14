# E2Eテスト実行ガイド

MangaAnime-Info-delivery-systemのEnd-to-Endテスト実行方法について説明します。

## 📋 概要

このE2Eテストスイートは、Playwrightを使用してWebアプリケーションの重要なユーザーフローをテストします。

### テスト対象機能
- ✅ 基本ナビゲーション
- ✅ 設定管理（NGワード、メール、カレンダー）
- ✅ リリース一覧表示・フィルタリング・検索
- ✅ カレンダー連携
- ✅ エラーハンドリング
- ✅ 統合ワークフロー

### サポートブラウザ
- 🌐 Chromium (Chrome/Edge)
- 🦊 Firefox
- 🧭 WebKit (Safari)
- 📱 Mobile Chrome/Safari

## 🚀 セットアップ

### 必要環境
- Node.js 18以上
- Python 3.8以上
- npm または yarn

### 依存関係インストール

```bash
# プロジェクトルートで実行
npm install

# Playwrightブラウザのインストール
npx playwright install
```

## 🧪 テスト実行方法

### 基本的な実行

```bash
# 全テスト実行（ヘッドレス）
npm run test:e2e

# ブラウザ表示付きで実行
npm run test:e2e:headed

# UIモードで実行（インタラクティブ）
npm run test:e2e:ui
```

### 個別テスト実行

```bash
# 特定のテストファイルのみ
npx playwright test tests/e2e/01-navigation.spec.ts

# 特定のブラウザのみ
npx playwright test --project=chromium

# 特定のパターンにマッチするテスト
npx playwright test --grep "設定機能"
```

### デバッグ実行

```bash
# デバッグモードで実行（1つのテストのみ）
npx playwright test --debug tests/e2e/01-navigation.spec.ts

# ヘッドレス無効化で実行
npx playwright test --headed

# スロー実行（動作確認用）
npx playwright test --headed --slowMo=1000
```

## 📊 テストレポート

### レポート確認

```bash
# HTMLレポート表示
npx playwright show-report

# レポート生成後の確認
open tests/e2e/reports/html/index.html
```

### レポートファイル
- `tests/e2e/reports/html/` - HTMLレポート
- `tests/e2e/reports/junit.xml` - JUnitレポート（CI用）
- `tests/e2e/reports/test-results.json` - JSONレポート
- `tests/e2e/test-results/` - スクリーンショット・ビデオ

## 🛠️ CI/CD統合

### GitHub Actions
`.github/workflows/e2e-tests.yml`で自動実行されます。

```bash
# 手動トリガー実行
gh workflow run e2e-tests.yml -f browser=chromium -f test_type=smoke
```

### ローカルCI実行

```bash
# CI環境をシミュレート
./tests/e2e/ci/run-tests.sh

# スモークテストのみ
./tests/e2e/ci/run-tests.sh --smoke

# 特定ブラウザのみ
./tests/e2e/ci/run-tests.sh --browser chromium

# ヘッド付きデバッグ実行
./tests/e2e/ci/run-tests.sh --headed --browser chromium
```

## 📝 テストファイル構成

```
tests/e2e/
├── 01-navigation.spec.ts           # 基本ナビゲーション
├── 02-configuration.spec.ts        # 設定機能
├── 03-releases-filtering.spec.ts   # リリース一覧・フィルタ
├── 04-calendar-integration.spec.ts # カレンダー連携
├── 05-error-handling.spec.ts       # エラーハンドリング
├── 06-integration-workflow.spec.ts # 統合ワークフロー
├── pages/                          # ページオブジェクト
│   ├── base-page.ts
│   ├── home-page.ts
│   ├── config-page.ts
│   └── releases-page.ts
├── utils/                          # テストユーティリティ
│   └── test-helpers.ts
├── ci/                             # CI/CD用スクリプト
│   └── run-tests.sh
├── global-setup.ts                 # グローバルセットアップ
├── global-teardown.ts              # グローバルティアダウン
└── README.md                       # このファイル
```

## 🎯 テストシナリオ詳細

### 1. ナビゲーションテスト (`01-navigation.spec.ts`)
- ページ間の遷移
- レスポンシブ対応
- アクセシビリティ
- パフォーマンス基準

### 2. 設定機能テスト (`02-configuration.spec.ts`)
- NGワード管理
- メール設定
- カレンダー設定
- フォームバリデーション

### 3. リリース一覧テスト (`03-releases-filtering.spec.ts`)
- データ表示
- フィルタリング
- ソート機能
- 検索機能
- ページネーション

### 4. カレンダー連携テスト (`04-calendar-integration.spec.ts`)
- カレンダー表示
- イベント管理
- API連携
- エラーハンドリング

### 5. エラーハンドリングテスト (`05-error-handling.spec.ts`)
- ネットワークエラー
- API失敗
- フォーム検証エラー
- 認証エラー

### 6. 統合ワークフローテスト (`06-integration-workflow.spec.ts`)
- オンボーディングフロー
- 日常運用フロー
- トラブルシューティング
- 高度な統合シナリオ

## 🔧 カスタマイズ

### 設定変更

`playwright.config.ts`で以下を調整可能：
- ベースURL
- タイムアウト値
- 並列実行数
- レポート出力形式
- ブラウザ設定

### テスト環境の準備

```bash
# テスト用データベース作成
python -c "
import sqlite3
conn = sqlite3.connect('test_e2e.db')
# データベース初期化処理
conn.close()
"

# アプリケーションサーバー起動
FLASK_ENV=testing python web_app.py
```

## 📈 パフォーマンス基準

- ページ読み込み: 5秒以内
- フィルタリング: 3秒以内
- 検索: 2秒以内
- ナビゲーション: 3秒以内

## 🐛 トラブルシューティング

### よくある問題

**1. サーバーが起動しない**
```bash
# ポート確認
lsof -i :3033

# プロセス終了
kill $(lsof -t -i:3033)
```

**2. ブラウザがインストールされていない**
```bash
# 再インストール
npx playwright install --force
```

**3. テストがタイムアウトする**
```bash
# タイムアウト値を増やす
npx playwright test --timeout=120000
```

**4. 権限エラー**
```bash
# 実行権限付与
chmod +x tests/e2e/ci/run-tests.sh
```

### デバッグのヒント

1. `--headed`でブラウザ表示
2. `--debug`でステップ実行
3. `console.log()`でデバッグ出力
4. スクリーンショット・ビデオを確認
5. ネットワークタブで通信確認

## 📞 サポート

問題が発生した場合は以下を確認してください：

1. [Playwright公式ドキュメント](https://playwright.dev/)
2. プロジェクトのIssues
3. テストレポートのエラー詳細
4. サーバーログの確認

---

*このE2Eテストスイートは、MangaAnime-Info-delivery-systemの品質保証と継続的なデリバリーを支援します。*