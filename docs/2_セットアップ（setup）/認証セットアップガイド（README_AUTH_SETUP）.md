# Google認証設定ガイド - MangaAnime-Info-delivery-system

このドキュメントでは、アニメ・マンガ情報配信システムでGmail通知とGoogleカレンダー連携を使用するための認証設定について説明します。

## 🔐 認証方式

本システムでは2つの認証方式をサポートしています：

1. **OAuth2認証** (推奨) - Gmail API + Google Calendar API
2. **App Password認証** - SMTP（Gmail）

## 📋 事前準備

### Google Cloud Console設定

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. 新しいプロジェクトを作成または既存プロジェクトを選択
3. 以下のAPIを有効化：
   - Gmail API
   - Google Calendar API
4. 「認証情報」→「認証情報を作成」→「OAuth クライアント ID」
5. アプリケーションの種類：「デスクトップ アプリケーション」
6. 作成したクライアント情報をJSONでダウンロード
7. ダウンロードしたファイルを `credentials.json` として配置

### Gmail App Password設定 (オプション)

1. Googleアカウントの2段階認証を有効化
2. [Googleアカウント設定](https://myaccount.google.com/) → セキュリティ
3. 「2段階認証プロセス」→「アプリ パスワード」
4. アプリ：「その他」、デバイス：「Linux」で生成
5. 16文字のパスワードをメモ

## 🚀 セットアップ手順

### Step 1: 認証設定の確認

```bash
python3 auth_config.py --validate
```

### Step 2: Gmail設定ファイルの作成（App Password用）

```bash
python3 auth_config.py --setup-gmail
```

生成された `gmail_config.json` を編集：

```json
{
  "gmail_settings": {
    "email_address": "your-actual-email@gmail.com",
    "app_password": "your-16-character-app-password",
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_name": "アニメ・マンガ通知システム"
  }
}
```

### Step 3: セキュリティ設定の適用

```bash
python3 auth_config.py --fix-permissions
```

### Step 4: OAuth2トークンの生成

```bash
python3 create_token.py
```

実行後、表示されるURLをブラウザで開き、認証コードを入力してください。

### Step 5: 認証テストの実行

全体テスト：
```bash
python3 test_gmail_auth.py
```

テストメール送信付き：
```bash
python3 test_gmail_auth.py --send-emails
```

OAuth2のみ：
```bash
python3 test_gmail_auth.py --oauth2-only
```

App Passwordのみ：
```bash
python3 test_gmail_auth.py --smtp-only
```

## 📁 ファイル構成

```
MangaAnime-Info-delivery-system/
├── credentials.json          # Google OAuth2クライアント情報 (600)
├── token.json               # OAuth2アクセストークン (600) *自動生成
├── gmail_config.json        # Gmail App Password設定 (600)
├── gmail_config.json.template # 設定テンプレート
├── create_token.py          # OAuth2トークン生成
├── auth_config.py           # 認証設定管理
├── test_gmail_auth.py       # 認証テスト
└── README_AUTH_SETUP.md     # このファイル
```

## 🔧 トラブルシューティング

### よくあるエラー

**1. `credentials.json が見つかりません`**
- Google Cloud Consoleで作成したクライアント情報をcredentials.jsonとして配置

**2. `認証に失敗しました`**
- App Passwordが正しく設定されているか確認
- 2段階認証が有効になっているか確認

**3. `パーミッションが不適切です`**
```bash
python3 auth_config.py --fix-permissions
```

**4. `token.json が見つかりません`**
```bash
python3 create_token.py
```

### ログの確認

詳細なエラー情報は以下で確認できます：
```bash
python3 test_gmail_auth.py 2>&1 | tee auth_test.log
```

## 🔒 セキュリティ注意事項

1. **認証ファイルのパーミッション**
   - credentials.json、token.json、gmail_config.json は必ず 600 に設定
   
2. **バージョン管理**
   - 認証ファイルは .gitignore に追加してコミットしない
   
3. **アクセス権限**
   - 最小権限の原則に従い、必要なスコープのみを使用

## 📞 サポート

問題が解決しない場合は、以下の情報と共にお問い合わせください：

1. エラーメッセージ
2. 実行したコマンド
3. 認証設定の検証結果：
   ```bash
   python3 auth_config.py --validate
   ```

---

*最終更新: 2025-09-03*