# Googleカレンダー連携 クイックスタートガイド

## 目次
1. [前提条件](#前提条件)
2. [セットアップ（5分）](#セットアップ5分)
3. [動作確認](#動作確認)
4. [トラブルシューティング](#トラブルシューティング)

---

## 前提条件

- Python 3.7以上
- Googleアカウント
- インターネット接続

---

## セットアップ（5分）

### ステップ1: 自動セットアップスクリプト実行

```bash
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system
bash setup_google_calendar.sh
```

このスクリプトが以下を自動で行います:
- 必要なPythonパッケージのインストール
- ファイル構成の確認
- 認証テストの実行（オプション）

---

### ステップ2: Google Cloud Console設定

**credentials.jsonがない場合のみ実施**

1. https://console.cloud.google.com/ にアクセス

2. 新しいプロジェクトを作成
   - プロジェクト名: `MangaAnime-Calendar`（任意）

3. Google Calendar APIを有効化
   - 左メニュー「APIとサービス」→「ライブラリ」
   - 「Google Calendar API」を検索
   - 「有効にする」をクリック

4. OAuth 2.0認証情報を作成
   - 左メニュー「APIとサービス」→「認証情報」
   - 「認証情報を作成」→「OAuth クライアントID」
   - アプリケーションの種類: **デスクトップアプリ**
   - 名前: `MangaAnime Calendar Client`（任意）
   - 「作成」をクリック

5. credentials.jsonをダウンロード
   - ダウンロードボタンをクリック
   - ファイル名を `credentials.json` に変更
   - プロジェクトルートに配置

```bash
# ダウンロードしたファイルを移動
mv ~/Downloads/credentials.json /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/

# パーミッション設定
chmod 600 /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/credentials.json
```

---

### ステップ3: 初回認証

```bash
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system
python3 modules/calendar.py --authenticate
```

**何が起きるか:**
1. ブラウザが自動で開きます
2. Googleアカウントでログイン
3. アプリケーションにカレンダーアクセスを許可
4. `token.json` が自動生成されます

**ブラウザが開かない場合:**
- ターミナルに表示されるURLを手動でブラウザにコピー＆ペースト

---

## 動作確認

### テスト1: Dry-run（実際のカレンダーに影響なし）

```bash
python3 test_calendar_dry_run.py
```

**期待される出力:**
```
================================================================================
環境チェック
================================================================================

Pythonバージョン: Python 3.x.x

必要パッケージ確認:
  ✓ google.oauth2.credentials
  ✓ googleapiclient.discovery
  ✓ googleapiclient.errors

認証ファイル確認:
  ✓ credentials.json: 存在
  ✓ token.json: 存在
  ✓ config.json: 存在

...

[テストケース 1]
--------------------------------------------------------------------------------
タイトル: [テスト] 呪術廻戦 第15話配信 - Netflix
説明:
配信プラットフォーム: Netflix
...
```

---

### テスト2: 実際のイベント作成

```bash
python3 modules/calendar.py --create-test-event
```

**期待される出力:**
```
================================================================================
テストイベント作成
================================================================================

✓ 認証成功

タイトル: [テスト] カレンダー連携テスト
開始日時: 2025-12-07 12:00:00

✓ イベント作成成功
  Event ID: abc123xyz
  Link: https://www.google.com/calendar/event?eid=...
================================================================================
```

**確認方法:**
1. https://calendar.google.com/ にアクセス
2. 明日の予定に「[テスト] カレンダー連携テスト」が表示されているか確認

---

### テスト3: 既存イベント一覧取得

```bash
python3 -c "
from modules.calendar import CalendarManager
cal = CalendarManager()
cal.authenticate()
events = cal.list_events(max_results=5)
for event in events:
    start = event['start'].get('dateTime', event['start'].get('date'))
    print(f'{start}: {event.get(\"summary\", \"No title\")}')
"
```

---

## トラブルシューティング

### エラー1: `ModuleNotFoundError: No module named 'google'`

**原因:** Google APIライブラリ未インストール

**解決策:**
```bash
pip3 install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

---

### エラー2: `credentials.json not found`

**原因:** 認証ファイルが配置されていない

**解決策:**
1. Google Cloud Consoleから`credentials.json`をダウンロード
2. プロジェクトルートに配置
3. `chmod 600 credentials.json`

---

### エラー3: `token.json has expired`

**原因:** 認証トークンの期限切れ

**解決策:**
```bash
# token.jsonを削除して再認証
rm token.json
python3 modules/calendar.py --authenticate
```

---

### エラー4: `Calendar API has not been used in project`

**原因:** Google Cloud ConsoleでCalendar APIが有効化されていない

**解決策:**
1. https://console.cloud.google.com/
2. 「APIとサービス」→「ライブラリ」
3. 「Google Calendar API」を検索
4. 「有効にする」をクリック

---

### エラー5: `Access blocked: This app's request is invalid`

**原因:** OAuth同意画面の設定が不完全

**解決策:**
1. https://console.cloud.google.com/
2. 「APIとサービス」→「OAuth同意画面」
3. 必須項目を全て入力
4. テストユーザーに自分のGoogleアカウントを追加

---

## 使用例

### アニメ配信通知をカレンダーに追加

```python
from modules.calendar import CalendarManager
from datetime import datetime, timedelta

cal = CalendarManager()
cal.authenticate()

# 明日の深夜0時に配信
start = datetime.now() + timedelta(days=1)
start = start.replace(hour=0, minute=0, second=0)

result = cal.create_event(
    title='呪術廻戦 第15話配信 - Netflix',
    description='配信プラットフォーム: Netflix\n公式サイト: https://example.com',
    start_datetime=start,
    color='9'  # 青色（アニメ）
)

if result['success']:
    print(f"イベント作成成功: {result['html_link']}")
else:
    print(f"エラー: {result['error']}")
```

---

### マンガ発売日をカレンダーに追加

```python
from modules.calendar import CalendarManager
from datetime import datetime

cal = CalendarManager()
cal.authenticate()

result = cal.create_event(
    title='ワンピース 第110巻発売',
    description='電子版配信\n出版社: 集英社',
    start_datetime=datetime(2025, 12, 15, 0, 0, 0),
    color='10'  # 緑色（マンガ）
)

if result['success']:
    print(f"イベント作成成功: {result['html_link']}")
```

---

## 参考資料

### 公式ドキュメント
- [Google Calendar API Overview](https://developers.google.com/calendar/api/v3/reference)
- [Python Quickstart](https://developers.google.com/calendar/api/quickstart/python)
- [OAuth 2.0](https://developers.google.com/identity/protocols/oauth2)

### プロジェクト内ドキュメント
- [CALENDAR_INVESTIGATION_REPORT.md](./CALENDAR_INVESTIGATION_REPORT.md) - 詳細調査レポート
- [modules/calendar_template.py](./modules/calendar_template.py) - カレンダーモジュール実装例

---

## チェックリスト

セットアップ完了確認:

- [ ] Python 3.7以上がインストール済み
- [ ] 必要なPythonパッケージがインストール済み
- [ ] Google Cloud Consoleでプロジェクト作成済み
- [ ] Google Calendar API有効化済み
- [ ] OAuth 2.0認証情報作成済み
- [ ] credentials.json配置済み
- [ ] 初回OAuth認証完了（token.json生成済み）
- [ ] Dry-runテスト成功
- [ ] テストイベント作成成功
- [ ] Googleカレンダーでイベント確認済み

---

**セットアップ完了！**

詳細な実装については `CALENDAR_INVESTIGATION_REPORT.md` を参照してください。
