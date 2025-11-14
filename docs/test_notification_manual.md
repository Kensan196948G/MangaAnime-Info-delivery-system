# テスト通知機能 動作確認手順書

## 目次
1. [事前準備](#事前準備)
2. [テスト環境セットアップ](#テスト環境セットアップ)
3. [ブラウザUIでのテスト](#ブラウザuiでのテスト)
4. [curlでのAPIテスト](#curlでのapiテスト)
5. [自動テストの実行](#自動テストの実行)
6. [トラブルシューティング](#トラブルシューティング)

---

## 事前準備

### 必要な環境変数の設定

`.env`ファイルに以下の設定が必要です：

```bash
# Gmail設定
GMAIL_ADDRESS=your.email@gmail.com
GMAIL_APP_PASSWORD=your_app_password_here
```

### Gmail アプリパスワードの取得方法

1. Googleアカウントにログイン
2. セキュリティ設定 > 2段階認証プロセスを有効化
3. アプリパスワードを生成
4. 生成されたパスワードを`.env`ファイルに設定

### 設定ファイルの確認

`config.json`に以下の設定があることを確認：

```json
{
  "notification_email": "your.email@gmail.com",
  "enable_notifications": true
}
```

---

## テスト環境セットアップ

### 1. サーバーの起動

```bash
# プロジェクトルートディレクトリで実行
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system

# サーバー起動
bash start_server.sh

# または
python3 app/web_app.py
```

### 2. サーバー起動確認

```bash
# 別のターミナルで確認
curl http://localhost:5000
```

正常に起動していれば、HTMLレスポンスが返ってきます。

---

## ブラウザUIでのテスト

### テストケース1: 基本的なテスト通知送信

#### 手順：

1. ブラウザで http://localhost:5000 にアクセス
2. ダッシュボードが表示されることを確認
3. 「テスト通知」ボタンまたはリンクを探す
4. ボタンをクリック

#### 期待される結果：

- ローディング表示が出る
- 数秒後に成功メッセージが表示される
- 「テスト通知を送信しました」というメッセージ
- 送信先メールアドレスが表示される

#### 確認項目：

- [ ] ボタンクリック後、ローディング表示が出る
- [ ] 成功メッセージが緑色で表示される
- [ ] メールアドレスが正しく表示される
- [ ] JavaScriptエラーが発生しない（ブラウザのコンソールを確認）

### テストケース2: カスタムメッセージでの送信

#### 手順：

1. テスト通知のモーダルまたはフォームを開く
2. メッセージ入力欄にカスタムメッセージを入力
   例：「手動テスト実施 - 2024年11月14日」
3. 送信ボタンをクリック

#### 期待される結果：

- カスタムメッセージで送信される
- 成功メッセージが表示される

### テストケース3: 実際のメール受信確認

#### 手順：

1. ブラウザからテスト通知を送信
2. Gmail（または設定したメールサービス）を開く
3. 受信トレイを確認

#### 期待される結果：

- 「【MangaAnime】テスト通知 ✅」という件名のメールが届く
- HTMLメールとして正しくフォーマットされている
- 送信日時が表示されている
- システム情報が含まれている

#### 確認項目：

- [ ] メールが1〜2分以内に到着する
- [ ] 件名が正しい
- [ ] HTMLが正しく表示される
- [ ] 日本語が文字化けしていない
- [ ] 絵文字が正しく表示される

### テストケース4: エラーハンドリング確認

#### 手順：

1. `.env`ファイルのGMAIL_APP_PASSWORDを一時的に無効な値に変更
2. サーバーを再起動
3. テスト通知を送信

#### 期待される結果：

- エラーメッセージが表示される
- 「Gmailアプリパスワードが設定されていません」というメッセージ

#### 確認項目：

- [ ] エラーメッセージが赤色で表示される
- [ ] エラー内容が具体的で分かりやすい
- [ ] ページがクラッシュしない

#### テスト後：

```bash
# .envファイルを元に戻す
# 正しいGMAIL_APP_PASSWORDに戻してサーバー再起動
```

---

## curlでのAPIテスト

### テストケース5: 正常なリクエスト

```bash
curl -X POST http://localhost:5000/api/test-notification \
  -H "Content-Type: application/json" \
  -d '{"message": "curlからのテスト通知"}'
```

#### 期待される結果：

```json
{
  "success": true,
  "message": "✅ テスト通知を送信しました！\n\n送信先: your.email@gmail.com\nメールボックスをご確認ください。",
  "details": {
    "from": "your.email@gmail.com",
    "to": "your.email@gmail.com",
    "sent_at": "2024-11-14T12:00:00.000000"
  }
}
```

### テストケース6: デフォルトメッセージ

```bash
curl -X POST http://localhost:5000/api/test-notification \
  -H "Content-Type: application/json" \
  -d '{}'
```

#### 期待される結果：

デフォルトメッセージで送信される

### テストケース7: 不正なJSON

```bash
curl -X POST http://localhost:5000/api/test-notification \
  -H "Content-Type: application/json" \
  -d '{invalid json}'
```

#### 期待される結果：

```json
{
  "success": false,
  "error": "..."
}
```

HTTPステータスコード: 400 または 500

### テストケース8: GETメソッド（許可されていない）

```bash
curl -X GET http://localhost:5000/api/test-notification
```

#### 期待される結果：

HTTPステータスコード: 405 Method Not Allowed

### テストケース9: 詳細なレスポンス確認

```bash
curl -X POST http://localhost:5000/api/test-notification \
  -H "Content-Type: application/json" \
  -d '{"message": "詳細テスト"}' \
  -w "\nHTTP Status: %{http_code}\n" \
  -v
```

#### 確認項目：

- [ ] HTTPステータスコード 200
- [ ] Content-Type: application/json
- [ ] レスポンスボディが有効なJSON
- [ ] success: true

---

## 自動テストの実行

### Pytestによる単体テスト

```bash
# テスト通知機能の包括的テスト実行
pytest tests/test_notification_comprehensive.py -v

# カバレッジ付き
pytest tests/test_notification_comprehensive.py --cov=app --cov-report=html

# 特定のテストクラスのみ実行
pytest tests/test_notification_comprehensive.py::TestNotificationNormalCases -v
```

#### 期待される結果：

```
tests/test_notification_comprehensive.py::TestNotificationNormalCases::test_send_notification_success PASSED
tests/test_notification_comprehensive.py::TestNotificationNormalCases::test_send_notification_with_custom_message PASSED
tests/test_notification_comprehensive.py::TestNotificationErrorCases::test_missing_email_address PASSED
...
========== 13 passed in 5.23s ==========
```

### curlスクリプトによるAPIテスト

```bash
# 包括的APIテスト実行
bash tests/test_notification_api.sh

# 別のポートでテスト
bash tests/test_notification_api.sh http://localhost:8080
```

#### 期待される結果：

```
======================================================================
テスト通知API 包括的テスト
======================================================================
API URL: http://localhost:5000
テスト開始時刻: 2024-11-14 12:00:00
======================================================================

[Test 1] 正常系: 基本的なテスト通知
  ✅ PASSED

[Test 2] 正常系: カスタムメッセージ
  ✅ PASSED

...

======================================================================
テスト結果サマリー
======================================================================
総テスト数: 9
成功: 9
失敗: 0
成功率: 100%
✅ 全てのテストが成功しました！
======================================================================
```

### Playwrightによる E2E テスト

```bash
# インストール（初回のみ）
npm install
npx playwright install

# テスト実行
npx playwright test tests/test_notification_ui.spec.ts

# ヘッドモードで実行（ブラウザを表示）
npx playwright test tests/test_notification_ui.spec.ts --headed

# デバッグモード
npx playwright test tests/test_notification_ui.spec.ts --debug
```

#### 期待される結果：

```
Running 13 tests using 3 workers

  ✓ テストケース1: 基本的なテスト通知送信 (5s)
  ✓ テストケース2: モーダルダイアログでのテスト通知 (4s)
  ✓ テストケース3: レスポンシブデザイン確認 (3s)
  ...

  13 passed (45s)
```

---

## トラブルシューティング

### 問題1: メールが送信されない

#### 症状：
- 成功メッセージは表示されるが、メールが届かない

#### 確認事項：
1. Gmail アプリパスワードが正しく設定されているか
2. 迷惑メールフォルダを確認
3. Gmail の「2段階認証」が有効か
4. サーバーログを確認：
   ```bash
   tail -f logs/app.log
   ```

#### 解決方法：
```bash
# .envファイルの確認
cat .env | grep GMAIL

# 環境変数が読み込まれているか確認
python3 -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('GMAIL_ADDRESS'))"
```

### 問題2: 認証エラー

#### 症状：
- 「Gmailアプリパスワードが設定されていません」エラー

#### 解決方法：
1. `.env`ファイルを確認
2. サーバーを再起動
3. アプリパスワードを再生成

### 問題3: ネットワークエラー

#### 症状：
- タイムアウトまたは接続エラー

#### 確認事項：
```bash
# インターネット接続確認
ping smtp.gmail.com

# ファイアウォール確認
sudo ufw status

# ポート465が開いているか確認
telnet smtp.gmail.com 465
```

### 問題4: JSON パースエラー

#### 症状：
- 不正なJSONエラー

#### 解決方法：
- Content-Typeヘッダーを確認
- JSONフォーマットを確認：
  ```bash
  echo '{"message": "テスト"}' | jq .
  ```

### 問題5: テストが失敗する

#### デバッグ方法：
```bash
# 詳細なログ出力
pytest tests/test_notification_comprehensive.py -v -s

# 特定のテストのみ実行
pytest tests/test_notification_comprehensive.py::TestNotificationNormalCases::test_send_notification_success -v -s

# ログファイル確認
tail -f logs/app.log
```

---

## チェックリスト

### 事前準備
- [ ] `.env`ファイルにGMAIL_ADDRESSを設定
- [ ] `.env`ファイルにGMAIL_APP_PASSWORDを設定
- [ ] `config.json`にnotification_emailを設定
- [ ] サーバーが起動している

### ブラウザUIテスト
- [ ] テスト通知ボタンが表示される
- [ ] ボタンクリックで成功メッセージが表示される
- [ ] 実際にメールが届く
- [ ] JavaScriptエラーがない

### APIテスト
- [ ] 正常なリクエストで200が返る
- [ ] レスポンスがJSONフォーマット
- [ ] エラー時に適切なステータスコード
- [ ] エラーメッセージが分かりやすい

### 自動テスト
- [ ] Pytestが全て成功
- [ ] curlスクリプトが全て成功
- [ ] Playwrightテストが全て成功
- [ ] テストカバレッジ75%以上

---

## テスト実施記録

| 日付 | テスト実施者 | テスト環境 | 結果 | 備考 |
|------|------------|-----------|------|------|
| 2024-11-14 | QA Agent | Ubuntu 22.04 | ✅ | 初回テスト |
|  |  |  |  |  |
|  |  |  |  |  |

---

## 付録

### 使用した技術スタック

- **バックエンド**: Flask (Python)
- **メール送信**: smtplib (Gmail SMTP)
- **テストフレームワーク**: pytest, Playwright
- **APIテスト**: curl

### 参考リンク

- [Flask公式ドキュメント](https://flask.palletsprojects.com/)
- [Gmail SMTP設定](https://support.google.com/mail/answer/7126229)
- [pytest公式ドキュメント](https://docs.pytest.org/)
- [Playwright公式ドキュメント](https://playwright.dev/)
