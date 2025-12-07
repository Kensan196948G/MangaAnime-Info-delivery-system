# Google API認証設定クイックスタート

このガイドは、MangaAnime Info SystemでGoogle Calendar APIとGmail APIを使用するための最小限の手順を示します。

## 必要なもの

- Googleアカウント
- Python 3.8以上
- インターネット接続

## 3ステップで完了

### Step 1: Google Cloud Consoleでcredentials.jsonを取得

1. https://console.cloud.google.com/ にアクセス
2. 新しいプロジェクトを作成
3. Google Calendar API と Gmail API を有効化
4. OAuth 2.0 クライアントID（デスクトップアプリ）を作成
5. credentials.json をダウンロード

詳細手順: [docs/GOOGLE_API_SETUP.md](docs/GOOGLE_API_SETUP.md)

### Step 2: credentials.jsonを配置

```bash
# ダウンロードしたファイルをプロジェクトルートに移動
mv ~/Downloads/credentials.json /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/

# または、絶対パスで直接コピー
cp ~/Downloads/credentials.json ./credentials.json
```

### Step 3: 初回認証を実行

```bash
# 必要なパッケージをインストール
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client

# テストスクリプトを実行
python3 scripts/test_google_apis.py
```

ブラウザが開いて認証画面が表示されます。Googleアカウントでログインして「許可」をクリックしてください。

## 成功の確認

以下のメッセージが表示されれば成功です:

```
✅ カレンダーサービスの初期化成功
✅ Gmailサービスの初期化成功
🎉 すべてのテストが成功しました！
```

## トラブルシューティング

### credentials.json が見つからない

```bash
# ファイルの存在確認
ls -la credentials.json
```

存在しない場合は、Step 1 を再度実行してください。

### 認証エラーが発生する

1. Google Cloud Consoleでテストユーザーに自分のアカウントを追加
2. token.jsonを削除して再認証

```bash
rm token.json
python3 scripts/test_google_apis.py
```

### モジュールが見つからない

必要なPythonパッケージをインストールしてください:

```bash
pip install -r requirements.txt
```

## セキュリティ注意

以下のファイルは**絶対にGitにコミットしないでください**:

- `credentials.json` - OAuth 2.0クライアントシークレット
- `token.json` - アクセストークン

`.gitignore`に含まれていることを確認してください。

## 詳細ドキュメント

- **完全設定ガイド**: [docs/GOOGLE_API_SETUP.md](docs/GOOGLE_API_SETUP.md)
- **チェックリスト**: [docs/CREDENTIALS_SETUP_CHECKLIST.md](docs/CREDENTIALS_SETUP_CHECKLIST.md)

## サポート

問題が解決しない場合は、以下を確認してください:

1. Python 3.8以上がインストールされているか
2. インターネット接続が有効か
3. Google Cloud Consoleで正しいAPIが有効化されているか

---

**最終更新**: 2025-12-07
