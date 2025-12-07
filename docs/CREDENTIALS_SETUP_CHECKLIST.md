# Google API認証設定チェックリスト

このチェックリストに従って、Google APIの認証設定を段階的に進めてください。

## Phase 1: Google Cloud Console設定

### ステップ1: プロジェクト作成
- [ ] Google Cloud Consoleにアクセス
- [ ] 新しいプロジェクト「MangaAnime-Info-System」を作成
- [ ] プロジェクトIDをメモ: `___________________`

### ステップ2: API有効化
- [ ] Google Calendar APIを有効化
- [ ] Gmail APIを有効化

### ステップ3: OAuth同意画面設定
- [ ] User Type: 外部 を選択
- [ ] アプリ名: `MangaAnime Info System`
- [ ] サポートメール: `___________________`
- [ ] デベロッパー連絡先: `___________________`
- [ ] テストユーザーに自分のメールアドレスを追加

### ステップ4: OAuth 2.0クライアントID作成
- [ ] アプリケーションタイプ: デスクトップアプリ
- [ ] 名前: `MangaAnime Desktop Client`
- [ ] credentials.jsonをダウンロード

## Phase 2: ローカル環境設定

### ステップ5: ファイル配置
- [ ] credentials.jsonをプロジェクトルートに配置
  ```bash
  cp ~/Downloads/credentials.json /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/
  ```

### ステップ6: パッケージインストール
- [ ] 必要なPythonパッケージをインストール
  ```bash
  pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
  ```

### ステップ7: 権限確認
- [ ] credentials.jsonの権限を確認（読み取り専用推奨）
  ```bash
  chmod 600 credentials.json
  ```

## Phase 3: 初回認証

### ステップ8: 認証テスト実行
- [ ] テストスクリプトを実行
  ```bash
  python3 scripts/test_google_apis.py
  ```

### ステップ9: ブラウザ認証
- [ ] ブラウザが自動的に開くことを確認
- [ ] Googleアカウントでログイン
- [ ] 「安全ではないページ」警告が表示された場合、「詳細」→「移動」をクリック
- [ ] 権限リクエストで「許可」をクリック

### ステップ10: token.json生成確認
- [ ] token.jsonが生成されたことを確認
  ```bash
  ls -la token.json
  ```

## Phase 4: 動作確認

### ステップ11: Calendar API動作確認
- [ ] カレンダーイベント取得が成功
- [ ] テストイベント作成が成功
- [ ] テストイベント削除が成功

### ステップ12: Gmail API動作確認
- [ ] プロフィール取得が成功
- [ ] ドラフト作成が成功

### ステップ13: エラーハンドリング確認
- [ ] 認証エラー時のメッセージが適切
- [ ] ファイル不在時のガイダンスが表示される

## Phase 5: セキュリティ確認

### ステップ14: .gitignore確認
- [ ] credentials.json がignoreされている
- [ ] token.json がignoreされている
- [ ] token.pickle がignoreされている

### ステップ15: バックアップ
- [ ] credentials.jsonをセキュアな場所にバックアップ
  ```bash
  mkdir -p ~/secure-backups
  cp credentials.json ~/secure-backups/credentials.json.backup
  chmod 600 ~/secure-backups/credentials.json.backup
  ```

### ステップ16: Git状態確認
- [ ] 認証情報ファイルがステージングされていないことを確認
  ```bash
  git status
  ```

## トラブルシューティング

### credentials.jsonが見つからない
- [ ] ダウンロードフォルダを確認
- [ ] Google Cloud Consoleで再ダウンロード

### 認証エラー: access_denied
- [ ] テストユーザーに自分のアカウントが追加されているか確認
- [ ] OAuth同意画面の設定を再確認

### 認証エラー: invalid_grant
- [ ] token.jsonを削除して再認証
  ```bash
  rm token.json
  python3 scripts/test_google_apis.py
  ```

### モジュールインポートエラー
- [ ] modules/calendar_integration.py が存在するか確認
- [ ] modules/mailer.py が存在するか確認
- [ ] 必要なパッケージがインストールされているか確認

## 完了確認

すべてのチェックボックスにチェックが入ったら、設定完了です！

```bash
python3 scripts/test_google_apis.py
```

上記コマンドで以下が表示されれば成功:
```
✅ Google Calendar API テスト完了
✅ Gmail API テスト完了
🎉 すべてのテストが成功しました！
```

---

**設定完了日**: ___________________
**設定者**: ___________________
**バージョン**: 1.0.0
