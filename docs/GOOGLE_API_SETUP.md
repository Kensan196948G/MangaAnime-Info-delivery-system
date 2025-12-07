# Google API 認証設定ガイド

## 概要

このガイドでは、MangaAnime Info Systemで使用するGoogle Calendar APIとGmail APIの認証設定手順を説明します。

## 前提条件

- Googleアカウント（個人用でOK）
- Python 3.8以上
- インターネット接続

---

## 1. Google Cloud Consoleでのプロジェクト作成

### 1.1 プロジェクト作成

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. 右上のプロジェクト選択 → 「新しいプロジェクト」をクリック
3. プロジェクト名: `MangaAnime-Info-System`
4. 「作成」をクリック

### 1.2 APIの有効化

#### Google Calendar API

1. 左メニュー → 「APIとサービス」 → 「ライブラリ」
2. 検索ボックスに「Google Calendar API」と入力
3. 「Google Calendar API」を選択
4. 「有効にする」をクリック

#### Gmail API

1. 同様に「Gmail API」を検索
2. 「Gmail API」を選択
3. 「有効にする」をクリック

---

## 2. OAuth 2.0 認証情報の作成

### 2.1 同意画面の設定

1. 「APIとサービス」 → 「OAuth同意画面」
2. User Type: **外部** を選択（個人開発の場合）
3. 「作成」をクリック
4. 必須項目を入力:
   - アプリ名: `MangaAnime Info System`
   - ユーザーサポートメール: あなたのGmailアドレス
   - デベロッパーの連絡先情報: あなたのGmailアドレス
5. 「保存して次へ」をクリック
6. スコープ画面: **スキップ**（デフォルトのまま）
7. テストユーザー画面:
   - 「+ ADD USERS」をクリック
   - あなたのGmailアドレスを追加
8. 「保存して次へ」をクリック

### 2.2 OAuth 2.0 クライアントIDの作成

1. 「APIとサービス」 → 「認証情報」
2. 「+ 認証情報を作成」 → 「OAuth クライアント ID」
3. アプリケーションの種類: **デスクトップ アプリ**
4. 名前: `MangaAnime Desktop Client`
5. 「作成」をクリック
6. **JSONをダウンロード**ボタンをクリック
7. ダウンロードしたファイル名を `credentials.json` に変更

---

## 3. 認証情報ファイルの配置

### 3.1 credentials.jsonの配置

```bash
# ダウンロードフォルダから移動
mv ~/Downloads/credentials.json /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/

# または、ファイルマネージャーで以下のパスにコピー
# /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/credentials.json
```

### 3.2 必要なPythonパッケージのインストール

```bash
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system
pip install -r requirements.txt
```

requirements.txtには以下が含まれている必要があります:
```
google-auth==2.23.0
google-auth-oauthlib==1.1.0
google-auth-httplib2==0.1.1
google-api-python-client==2.100.0
```

---

## 4. 初回認証の実行

### 4.1 認証スクリプトの実行

```bash
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system
python3 scripts/test_google_apis.py
```

### 4.2 認証フロー

1. スクリプトを実行すると、ブラウザが自動的に開きます
2. Googleアカウントでログイン（テストユーザーとして追加したアカウント）
3. 警告画面が表示される場合:
   - 「詳細」をクリック
   - 「MangaAnime Info System（安全ではないページ）に移動」をクリック
   - ※これは開発中のアプリのため正常です
4. 権限リクエスト画面で「許可」をクリック
5. 「認証が完了しました」というメッセージが表示されます

### 4.3 token.jsonの生成確認

```bash
ls -la /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/token.json
```

このファイルが存在すれば認証成功です。

---

## 5. 動作確認

### 5.1 APIテストの実行

```bash
python3 scripts/test_google_apis.py
```

**期待される出力:**

```
=== Google Calendar API テスト ===
✅ カレンダー接続成功: 5件のイベント取得

今後のイベント:
- 2025-12-10 14:00: 会議
- 2025-12-12 10:00: アポイント
...

=== Gmail API テスト ===
✅ Gmail接続成功
✅ テストメール送信機能確認完了
```

### 5.2 トラブルシューティング

#### エラー: credentials.json が見つからない

```bash
# ファイルの存在確認
ls -la /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/credentials.json
```

存在しない場合は、手順2.2を再度実行してください。

#### エラー: access_denied

- Google Cloud Consoleで、使用しているアカウントがテストユーザーに追加されているか確認
- OAuth同意画面の設定を再確認

#### エラー: invalid_grant

```bash
# token.jsonを削除して再認証
rm /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/token.json
python3 scripts/test_google_apis.py
```

---

## 6. セキュリティ上の注意事項

### 6.1 認証情報の保護

**重要**: 以下のファイルは絶対にGitにコミットしないでください:

- `credentials.json` - OAuth 2.0クライアントシークレット
- `token.json` - アクセストークン
- `token.pickle` - トークンのキャッシュ（使用している場合）

`.gitignore`に以下が含まれていることを確認してください:

```gitignore
# Google API認証情報
credentials.json
token.json
token.pickle
*.json.bak
```

### 6.2 認証情報のバックアップ

```bash
# セキュアな場所にバックアップ（例）
mkdir -p ~/secure-backups
cp credentials.json ~/secure-backups/credentials.json.backup
chmod 600 ~/secure-backups/credentials.json.backup
```

### 6.3 token.jsonの有効期限

- アクセストークンは通常1時間で期限切れ
- リフレッシュトークンで自動更新されます
- 長期間使用しない場合は再認証が必要になることがあります

---

## 7. 本番環境への移行（オプション）

現在は「テストモード」ですが、一般公開する場合は以下の手順が必要です:

### 7.1 OAuth同意画面の公開申請

1. Google Cloud Console → 「OAuth同意画面」
2. 「アプリを公開」をクリック
3. Googleの審査を受ける（通常1-2週間）

### 7.2 サービスアカウントの利用（推奨）

サーバー環境で動作させる場合は、OAuth 2.0の代わりにサービスアカウントを使用することを推奨します。

---

## 8. よくある質問（FAQ）

### Q1: 個人利用だけなのに「外部」を選択する必要がありますか？

A: はい。Googleアカウントが個人アカウントの場合、Google Workspaceではないため「外部」を選択する必要があります。

### Q2: テストユーザーは何人まで追加できますか？

A: テストモードでは最大100人まで追加可能です。

### Q3: credentials.jsonを紛失した場合は？

A: Google Cloud Consoleで新しいOAuth 2.0クライアントIDを作成し、新しいcredentials.jsonをダウンロードしてください。古いIDは削除することを推奨します。

### Q4: token.jsonを他のPCで使えますか？

A: セキュリティ上推奨されません。各環境で個別に認証を行ってください。

---

## 9. サンプル: credentials.json の構造

実際のファイルは以下のような構造です（シークレット部分は伏せています）:

```json
{
  "installed": {
    "client_id": "123456789-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.apps.googleusercontent.com",
    "project_id": "mangaanime-info-system",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "GOCSPX-xxxxxxxxxxxxxxxxxxxxxxxx",
    "redirect_uris": ["http://localhost"]
  }
}
```

---

## 10. 参考リンク

- [Google Calendar API ドキュメント](https://developers.google.com/calendar)
- [Gmail API ドキュメント](https://developers.google.com/gmail)
- [OAuth 2.0 for Desktop Apps](https://developers.google.com/identity/protocols/oauth2/native-app)
- [Google API Python Client](https://github.com/googleapis/google-api-python-client)

---

**作成日**: 2025-12-07
**最終更新**: 2025-12-07
**バージョン**: 1.0.0
