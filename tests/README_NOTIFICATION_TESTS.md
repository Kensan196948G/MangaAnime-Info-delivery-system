# テスト通知機能 テストガイド

このディレクトリには、テスト通知機能の包括的なテストスイートが含まれています。

---

## 📁 ファイル構成

```
tests/
├── test_notification_comprehensive.py  # Pytest単体テスト（13テストケース）
├── test_notification_api.sh           # curlを使用したAPIテスト
├── test_notification_ui.spec.ts       # Playwright E2Eテスト
├── generate_test_report.py            # 統合テストレポート生成
└── README_NOTIFICATION_TESTS.md       # このファイル
```

---

## 🚀 クイックスタート

### 1. Pytest単体テスト（推奨）

最も簡単で速いテスト方法です。

```bash
# 基本実行
pytest tests/test_notification_comprehensive.py -v

# カバレッジ付き
pytest tests/test_notification_comprehensive.py --cov=app --cov-report=html

# 特定のテストクラスのみ
pytest tests/test_notification_comprehensive.py::TestNotificationNormalCases -v
```

**実行時間**: 約1秒
**必要な環境**: Python 3.8+, pytest

### 2. curlによるAPIテスト

実際のサーバーを起動してテストします。

```bash
# サーバーを起動（別ターミナル）
bash start_server.sh

# テスト実行
bash tests/test_notification_api.sh
```

**実行時間**: 約30秒
**必要な環境**: bash, curl, 起動中のサーバー

### 3. Playwright E2Eテスト

ブラウザを使用した完全なE2Eテストです。

```bash
# 初回のみ: インストール
npm install
npx playwright install

# テスト実行
npx playwright test tests/test_notification_ui.spec.ts

# ヘッドモード（ブラウザ表示）
npx playwright test tests/test_notification_ui.spec.ts --headed
```

**実行時間**: 約45秒
**必要な環境**: Node.js, Playwright, 起動中のサーバー

---

## 📊 テストレポート生成

全てのテストを実行して統合レポートを生成します。

```bash
python3 tests/generate_test_report.py
```

生成されるファイル:
- `docs/reports/test_notification_report_YYYYMMDD_HHMMSS.md`
- `docs/reports/test_notification_report_YYYYMMDD_HHMMSS.html` (pandoc利用可能時)

---

## 📋 テストケース一覧

### 正常系テスト (3ケース)

1. **基本的なテスト通知送信**
   - 正しいパラメータで通知が送信される
   - HTTPステータス200、success: true

2. **カスタムメッセージでの送信**
   - カスタムメッセージが正しく処理される

3. **デフォルトメッセージでの送信**
   - メッセージ未指定時にデフォルト値が使用される

### 異常系テスト (5ケース)

4. **メールアドレス未設定エラー**
   - 設定不足時に適切なエラーメッセージ

5. **Gmailアプリパスワード未設定エラー**
   - 認証情報不足時のエラー処理

6. **不正なGmail認証情報エラー**
   - SMTP認証失敗時の処理

7. **ネットワークエラー**
   - 接続失敗時のエラーハンドリング

8. **SMTP接続タイムアウト**
   - タイムアウト時の適切な処理

### 入力検証テスト (3ケース)

9. **空のJSONボディ**
   - 空リクエストでもクラッシュしない

10. **非常に長いメッセージ**
    - 1000文字の長文でも処理可能

11. **特殊文字を含むメッセージ**
    - HTMLエスケープ、XSS対策

### レスポンス形式テスト (2ケース)

12. **成功レスポンスの形式検証**
    - 必須フィールド: success, message, details

13. **エラーレスポンスの形式検証**
    - エラー時の適切な形式

---

## 🎯 テスト実行コマンド一覧

### Pytest

```bash
# 全テスト実行
pytest tests/test_notification_comprehensive.py -v

# 詳細出力
pytest tests/test_notification_comprehensive.py -v -s

# 失敗時のみ詳細表示
pytest tests/test_notification_comprehensive.py --tb=short

# カバレッジ付き
pytest tests/test_notification_comprehensive.py --cov=app --cov-report=term-missing

# HTMLレポート生成
pytest tests/test_notification_comprehensive.py --html=test-reports/report.html --self-contained-html

# 並列実行（高速化）
pytest tests/test_notification_comprehensive.py -n auto

# 特定のテストのみ
pytest tests/test_notification_comprehensive.py::TestNotificationNormalCases::test_send_notification_success -v
```

### curl スクリプト

```bash
# 基本実行
bash tests/test_notification_api.sh

# 別のポート指定
bash tests/test_notification_api.sh http://localhost:8080

# レポートファイル確認
cat test-reports/notification_api_test_*.txt
```

### Playwright

```bash
# 全テスト実行
npx playwright test tests/test_notification_ui.spec.ts

# ブラウザ表示
npx playwright test tests/test_notification_ui.spec.ts --headed

# デバッグモード
npx playwright test tests/test_notification_ui.spec.ts --debug

# 特定のブラウザのみ
npx playwright test tests/test_notification_ui.spec.ts --project=chromium

# レポート表示
npx playwright show-report
```

---

## 🔧 トラブルシューティング

### Q1: Pytestテストが失敗する

**症状**: `ModuleNotFoundError: No module named 'app'`

**解決方法**:
```bash
# プロジェクトルートから実行
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system
pytest tests/test_notification_comprehensive.py -v
```

### Q2: curlテストがサーバーに接続できない

**症状**: `サーバーに接続できません`

**解決方法**:
```bash
# 別ターミナルでサーバー起動
bash start_server.sh

# サーバー起動確認
curl http://localhost:5000
```

### Q3: Playwrightテストが動作しない

**症状**: `Error: Playwright executable not found`

**解決方法**:
```bash
# Playwrightインストール
npm install
npx playwright install

# ブラウザ依存関係インストール
npx playwright install-deps
```

### Q4: テストは成功するが実際にメールが届かない

**原因**: モックを使用しているため、実際のメール送信は行われません。

**解決方法**:
- curlスクリプトで実際のサーバーをテスト
- ブラウザUIから手動テスト
- `.env`ファイルの設定を確認

---

## 📚 関連ドキュメント

- **動作確認手順書**: `/docs/test_notification_manual.md`
  - ブラウザUIでの手動テスト手順
  - 実際のメール受信確認方法
  - 詳細なトラブルシューティング

- **最終テストレポート**: `/docs/reports/TEST_NOTIFICATION_FINAL_REPORT.md`
  - テスト結果の詳細
  - 品質メトリクス
  - 改善提案

- **システム仕様書**: `/CLAUDE.md`
  - システム全体の仕様
  - アーキテクチャ設計

---

## 🎓 ベストプラクティス

### テスト実行の順序

1. **開発中**: Pytestで素早くテスト
   ```bash
   pytest tests/test_notification_comprehensive.py -v
   ```

2. **統合テスト**: curlでAPIをテスト
   ```bash
   bash tests/test_notification_api.sh
   ```

3. **本番前**: Playwrightで完全テスト
   ```bash
   npx playwright test tests/test_notification_ui.spec.ts
   ```

4. **リリース前**: 統合レポート生成
   ```bash
   python3 tests/generate_test_report.py
   ```

### CI/CD統合

```yaml
# .github/workflows/test.yml 例
name: Test Notification API

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
          pip install pytest pytest-cov
      - name: Run tests
        run: |
          pytest tests/test_notification_comprehensive.py -v --cov=app
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

---

## 📞 サポート

問題が発生した場合:

1. このREADMEのトラブルシューティングセクションを確認
2. `/docs/test_notification_manual.md`の詳細ガイドを参照
3. ログファイルを確認: `tail -f logs/app.log`
4. issueを作成（GitHubを使用している場合）

---

## 📝 テスト実施チェックリスト

開発者向けチェックリスト:

- [ ] Pytestが全て成功する
- [ ] curlテストが全て成功する
- [ ] 実際のサーバーで手動テストを実施
- [ ] .envファイルの設定が正しい
- [ ] メールが実際に届くことを確認
- [ ] エラーメッセージが分かりやすい
- [ ] ログに機密情報が含まれていない
- [ ] ドキュメントが最新

---

**最終更新**: 2024年11月14日
**作成者**: QA Agent (Claude Code)
