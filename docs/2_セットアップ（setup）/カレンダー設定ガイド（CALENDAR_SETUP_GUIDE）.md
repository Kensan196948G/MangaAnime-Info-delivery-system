# Google Calendar連携セットアップガイド

## 概要

このガイドでは、MangaAnime-Info-delivery-systemでGoogle Calendar連携機能を有効化する手順を説明します。

## 前提条件

- Pythonがインストールされていること（Python 3.7以上）
- Googleアカウントを持っていること
- インターネット接続があること

## セットアップ手順

### 1. Google Cloud Console でプロジェクトを作成

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. 新しいプロジェクトを作成（または既存のものを選択）
   - プロジェクト名: `MangaAnime-Notifier` など任意の名前

### 2. Google Calendar API を有効化

1. Google Cloud Consoleで作成したプロジェクトを選択
2. 左メニューから「APIとサービス」→「ライブラリ」を選択
3. 検索ボックスで「Google Calendar API」を検索
4. 「Google Calendar API」をクリック
5. 「有効にする」ボタンをクリック

### 3. OAuth 2.0 認証情報を作成

1. 左メニューから「APIとサービス」→「認証情報」を選択
2. 「認証情報を作成」→「OAuth クライアント ID」を選択
3. 同意画面の構成を求められた場合:
   - ユーザータイプ: 「外部」を選択
   - アプリ名: `MangaAnime Notifier`
   - ユーザーサポートメール: 自分のメールアドレス
   - デベロッパーの連絡先情報: 自分のメールアドレス
   - 「保存して続行」
4. スコープの追加:
   - 「スコープを追加または削除」
   - `https://www.googleapis.com/auth/calendar` を追加
   - 「更新」→「保存して続行」
5. テストユーザーを追加:
   - 自分のGoogleアカウントのメールアドレスを追加
   - 「保存して続行」
6. OAuth クライアント ID の作成:
   - アプリケーションの種類: 「デスクトップアプリ」
   - 名前: `MangaAnime Calendar Client`
   - 「作成」をクリック
7. 認証情報をダウンロード:
   - 作成完了後、JSONファイルをダウンロード
   - ファイル名を `credentials.json` に変更

### 4. credentials.json をプロジェクトに配置

```bash
# ダウンロードした credentials.json をプロジェクトルートにコピー
cp ~/Downloads/credentials.json /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/
```

### 5. 必要なPythonパッケージをインストール

```bash
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system

# 必要なパッケージをインストール
pip3 install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### 6. カレンダー連携を有効化

```bash
# config.json の calendar.enabled を true に設定
python3 enable_calendar.py
```

### 7. 初回認証を実行

```bash
# カレンダーモジュールを実行して認証フローを開始
python3 modules/calendar_integration.py
```

ブラウザが自動的に開き、Googleアカウントでの認証を求められます:

1. 使用するGoogleアカウントを選択
2. 「アプリがアカウントへのアクセスをリクエストしています」の画面で「許可」をクリック
3. 「認証フローが完了しました」のメッセージが表示されればOK

認証が完了すると、プロジェクトルートに `token.json` が自動生成されます。

### 8. 動作確認

```bash
# 状態確認スクリプトを実行
python3 check_calendar_status.py

# Dry-runテストを実行
python3 test_calendar_dryrun.py

# 今後7日間のカレンダーイベントを取得
python3 -c "from modules.calendar_integration import list_upcoming_events; list_upcoming_events(7)"
```

## ファイル構成

セットアップ完了後、以下のファイルが存在するはずです:

```
MangaAnime-Info-delivery-system/
├── config.json                         # calendar.enabled: true
├── credentials.json                    # Google OAuth認証情報（秘密）
├── token.json                          # アクセストークン（秘密・自動生成）
├── modules/
│   └── calendar_integration.py         # カレンダー連携モジュール
├── enable_calendar.py                  # 設定有効化スクリプト
├── check_calendar_status.py            # 状態確認スクリプト
├── test_calendar_dryrun.py             # Dry-runテストスクリプト
└── docs/
    └── CALENDAR_SETUP_GUIDE.md         # このファイル
```

## トラブルシューティング

### credentials.json が見つからない

```
FileNotFoundError: credentials.json が見つかりません
```

**解決方法:**
1. Google Cloud Consoleで認証情報を再度ダウンロード
2. ファイル名が `credentials.json` であることを確認
3. プロジェクトルートに配置されていることを確認

### パッケージが見つからない

```
ModuleNotFoundError: No module named 'google'
```

**解決方法:**
```bash
pip3 install google-auth google-auth-oauthlib google-api-python-client
```

### 認証エラー

```
google.auth.exceptions.RefreshError: The credentials do not contain the necessary fields
```

**解決方法:**
1. `token.json` を削除
2. 再度認証フローを実行

```bash
rm token.json
python3 modules/calendar_integration.py
```

### アクセス権限エラー

```
HttpError 403: Access Not Configured
```

**解決方法:**
1. Google Cloud ConsoleでGoogle Calendar APIが有効化されているか確認
2. OAuth同意画面でテストユーザーに自分のアカウントが追加されているか確認

## セキュリティに関する注意事項

- `credentials.json` と `token.json` は秘密情報です
- これらのファイルをGitにコミットしないでください
- `.gitignore` に以下を追加してください:

```gitignore
credentials.json
token.json
```

## 使用方法（メインスクリプトからの呼び出し）

```python
import json
from modules.calendar_integration import sync_releases_to_calendar

# 設定を読み込み
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# リリース情報（例）
releases = [
    {
        'title': '葬送のフリーレン',
        'type': 'anime',
        'release_type': 'episode',
        'number': '10',
        'platform': 'dアニメストア',
        'release_date': '2025-12-10',
        'source_url': 'https://example.com/frieren'
    }
]

# カレンダーに同期
created_count = sync_releases_to_calendar(releases, config)
print(f"{created_count}件のイベントを作成しました")
```

## サポート

問題が解決しない場合は、以下を確認してください:

1. ログを確認: `logs/calendar.log`
2. 状態確認スクリプトを実行: `python3 check_calendar_status.py`
3. Google Cloud ConsoleでプロジェクトとAPIの設定を再確認

---

**最終更新:** 2025-12-06
