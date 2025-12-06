# Googleカレンダー機能 調査・分析レポート

**調査日**: 2025-12-06
**対象プロジェクト**: MangaAnime-Info-delivery-system
**プロジェクトパス**: `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/`

---

## 📋 エグゼクティブサマリー

本レポートは、アニメ・マンガ情報配信システムにおけるGoogleカレンダー連携機能の実装状況を調査し、有効化に必要な手順と動作検証の結果をまとめたものです。

---

## 1. 現状調査結果

### 1.1 ファイル構成調査

**調査項目:**
- カレンダー関連モジュールの存在
- Google API認証ファイル（credentials.json, token.json）
- 設定ファイル（config.json）
- 既存実装コード

**調査方法:**
以下のコマンドでプロジェクト全体をスキャン:

```bash
# カレンダー関連ファイル検索
find . -type f -name "*calendar*"

# Google認証ファイル検索
find . -name "credentials.json" -o -name "token.json"

# Pythonファイル内でcalendarキーワード検索
grep -r "calendar" modules/*.py backend/*.py app/*.py
```

**調査結果:** [調査スクリプト実行後に記入]

---

### 1.2 プロジェクト構造

```
MangaAnime-Info-delivery-system/
├── modules/              # バックエンドロジック
│   ├── calendar.py      # カレンダー連携モジュール（要確認）
│   ├── db.py
│   ├── mailer.py
│   └── ...
├── backend/             # APIサーバー
├── app/                 # フロントエンド
├── config.json          # システム設定
├── credentials.json     # Google API認証情報（要セットアップ）
└── token.json          # OAuth2トークン（初回認証時生成）
```

---

## 2. コード分析

### 2.1 カレンダーモジュール実装状況

**確認ファイル:** `modules/calendar.py`

#### 実装されるべき機能:
1. Google Calendar API認証
2. イベント作成機能
3. イベント更新/削除機能
4. エラーハンドリング

#### 実装コード例（期待される仕様）:

```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta

class CalendarManager:
    """Googleカレンダー管理クラス"""

    def __init__(self, credentials_path='credentials.json', token_path='token.json'):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None

    def authenticate(self):
        """OAuth2認証を実行"""
        creds = None
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)

            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())

        self.service = build('calendar', 'v3', credentials=creds)
        return True

    def create_event(self, title, description, start_datetime, end_datetime, calendar_id='primary'):
        """カレンダーイベントを作成"""
        event = {
            'summary': title,
            'description': description,
            'start': {
                'dateTime': start_datetime.isoformat(),
                'timeZone': 'Asia/Tokyo',
            },
            'end': {
                'dateTime': end_datetime.isoformat(),
                'timeZone': 'Asia/Tokyo',
            },
        }

        try:
            event_result = self.service.events().insert(
                calendarId=calendar_id,
                body=event
            ).execute()

            return {
                'success': True,
                'event_id': event_result['id'],
                'html_link': event_result.get('htmlLink')
            }

        except HttpError as error:
            return {
                'success': False,
                'error': str(error)
            }
```

---

### 2.2 認証フロー確認

#### OAuth2認証手順:

1. **Google Cloud Consoleでプロジェクト作成**
   - https://console.cloud.google.com/

2. **Calendar API有効化**
   - APIとサービス → ライブラリ → Google Calendar API

3. **認証情報作成**
   - OAuth 2.0 クライアントID作成
   - アプリケーションの種類: デスクトップアプリ
   - credentials.jsonダウンロード

4. **初回認証実行**
   - Pythonスクリプト実行時にブラウザが開く
   - Googleアカウントでログイン
   - token.json自動生成

---

### 2.3 エラーハンドリング確認項目

- [ ] 認証エラー処理
- [ ] APIクォータ超過対応
- [ ] ネットワークエラー対応
- [ ] 重複イベント防止
- [ ] ログ記録

---

## 3. テスト準備

### 3.1 テスト用イベントデータ

```python
# テストケース1: アニメ配信通知
test_event_anime = {
    'title': '[テスト] 呪術廻戦 第15話配信',
    'description': 'Netflix配信開始\n\n※これはテストイベントです',
    'start_datetime': datetime(2025, 12, 10, 0, 0, 0),
    'end_datetime': datetime(2025, 12, 10, 0, 30, 0),
}

# テストケース2: マンガ発売通知
test_event_manga = {
    'title': '[テスト] ワンピース 第110巻発売',
    'description': '電子版配信\n公式URL: https://example.com\n\n※これはテストイベントです',
    'start_datetime': datetime(2025, 12, 15, 0, 0, 0),
    'end_datetime': datetime(2025, 12, 15, 23, 59, 59),
}
```

### 3.2 Dry-runモード実装

```python
def create_event_dry_run(title, description, start_datetime, end_datetime):
    """
    実際にAPIを呼ばずに、作成されるイベントの内容を表示
    """
    print("=" * 60)
    print("[DRY-RUN] 以下のイベントが作成されます:")
    print("=" * 60)
    print(f"タイトル: {title}")
    print(f"説明: {description}")
    print(f"開始: {start_datetime}")
    print(f"終了: {end_datetime}")
    print("=" * 60)
    return {'success': True, 'dry_run': True}
```

---

## 4. 動作検証計画

### 4.1 検証ステップ

#### Step 1: 環境確認
```bash
# 必要なPythonパッケージインストール
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client

# インストール確認
python3 -c "import google.oauth2.credentials; print('OK')"
```

#### Step 2: 認証ファイル配置
1. credentials.jsonをプロジェクトルートに配置
2. パーミッション確認: `chmod 600 credentials.json`

#### Step 3: テスト実行
```bash
# Dry-runモードでテスト
python3 test_calendar_dry_run.py

# 実際のイベント作成テスト（テストカレンダー使用推奨）
python3 test_calendar_real.py
```

#### Step 4: 結果確認
- Googleカレンダーにアクセスしてイベント確認
- ログファイル確認
- エラーがないか確認

---

### 4.2 チェックリスト

**実装確認:**
- [ ] modules/calendar.py 存在確認
- [ ] CalendarManager クラス実装確認
- [ ] authenticate() メソッド実装確認
- [ ] create_event() メソッド実装確認
- [ ] エラーハンドリング実装確認

**認証確認:**
- [ ] credentials.json 配置
- [ ] Google Cloud Console プロジェクト設定
- [ ] Calendar API 有効化
- [ ] OAuth 2.0 認証情報作成

**動作確認:**
- [ ] 認証フロー成功
- [ ] token.json 生成確認
- [ ] テストイベント作成成功
- [ ] Googleカレンダーに表示確認
- [ ] エラーログなし

---

## 5. 必要な追加実装

### 5.1 優先度: 高

1. **重複防止機能**
   - 同じrelease_idのイベントは作成しない
   - DBにcalendar_event_idを記録

2. **エラーリトライ機能**
   - ネットワークエラー時に3回までリトライ
   - Exponential backoff実装

3. **イベント更新機能**
   - 配信日時変更に対応
   - 既存イベントを更新

### 5.2 優先度: 中

1. **カレンダー色分け機能**
   - アニメ: 青
   - マンガ: 緑
   - プラットフォーム別に色分け

2. **リマインダー設定**
   - 1日前に通知
   - 1時間前に通知

3. **バッチ作成機能**
   - 複数イベントを一度に作成
   - API呼び出し回数削減

### 5.3 優先度: 低

1. **カレンダー共有機能**
2. **iCal形式エクスポート**
3. **複数カレンダー対応**

---

## 6. 認証設定手順書

### 6.1 Google Cloud Console設定

#### 手順1: プロジェクト作成
1. https://console.cloud.google.com/ にアクセス
2. 新しいプロジェクト作成（例: "MangaAnime-Calendar"）
3. プロジェクトを選択

#### 手順2: Calendar API有効化
1. 「APIとサービス」→「ライブラリ」
2. 「Google Calendar API」を検索
3. 「有効にする」をクリック

#### 手順3: OAuth 2.0認証情報作成
1. 「APIとサービス」→「認証情報」
2. 「認証情報を作成」→「OAuth クライアントID」
3. アプリケーションの種類: 「デスクトップアプリ」
4. 名前: "MangaAnime Calendar Client"
5. 「作成」をクリック
6. credentials.jsonをダウンロード

#### 手順4: OAuth同意画面設定
1. 「OAuth同意画面」タブ
2. ユーザータイプ: 「外部」（個人用なら「内部」）
3. アプリ名、サポートメール等を入力
4. スコープ追加:
   - `https://www.googleapis.com/auth/calendar`
   - `https://www.googleapis.com/auth/calendar.events`

---

### 6.2 ローカル環境設定

```bash
# 1. credentials.jsonを配置
cp ~/Downloads/credentials.json /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/

# 2. パーミッション設定
chmod 600 /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/credentials.json

# 3. 必要パッケージインストール
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client

# 4. 初回認証実行（ブラウザが開きます）
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system
python3 modules/calendar.py --authenticate

# 5. token.json生成確認
ls -la token.json
```

---

### 6.3 config.json設定例

```json
{
  "google": {
    "calendar": {
      "enabled": true,
      "calendar_id": "primary",
      "credentials_path": "credentials.json",
      "token_path": "token.json",
      "timezone": "Asia/Tokyo",
      "event_duration_minutes": 30,
      "reminder_minutes": [1440, 60],
      "colors": {
        "anime": "9",
        "manga": "10"
      }
    }
  }
}
```

---

## 7. テスト実行スクリプト

### test_calendar_dry_run.py

```python
#!/usr/bin/env python3
"""
Googleカレンダー機能 Dry-runテスト
実際にAPIを呼ばずに動作確認
"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

def test_calendar_dry_run():
    print("=" * 80)
    print("Googleカレンダー Dry-runテスト")
    print("=" * 80)

    # テストデータ
    test_cases = [
        {
            'title': '[テスト] 呪術廻戦 第15話配信 - Netflix',
            'description': '配信プラットフォーム: Netflix\n\n※これはテストイベントです',
            'start': datetime.now() + timedelta(days=3),
            'end': datetime.now() + timedelta(days=3, minutes=30),
        },
        {
            'title': '[テスト] ワンピース 第110巻発売',
            'description': '電子版配信\n公式サイト: https://example.com\n\n※これはテストイベントです',
            'start': datetime.now() + timedelta(days=7),
            'end': datetime.now() + timedelta(days=7, hours=23, minutes=59),
        },
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n[テストケース {i}]")
        print("-" * 80)
        print(f"タイトル: {test_case['title']}")
        print(f"説明:\n{test_case['description']}")
        print(f"開始: {test_case['start'].strftime('%Y-%m-%d %H:%M')}")
        print(f"終了: {test_case['end'].strftime('%Y-%m-%d %H:%M')}")
        print("-" * 80)

    print("\n" + "=" * 80)
    print("Dry-runテスト完了")
    print("実際のイベント作成は行われていません")
    print("=" * 80)

if __name__ == "__main__":
    test_calendar_dry_run()
```

---

## 8. 結論と推奨事項

### 8.1 現状判定

**[調査完了後に記入]**

- 実装状況: [完了 / 一部実装 / 未実装]
- 認証設定: [完了 / 未完了]
- 動作確認: [成功 / 失敗 / 未実施]

---

### 8.2 推奨アクション

#### 即座に実施すべき項目:
1. [ ] credentials.json取得と配置
2. [ ] 必要パッケージインストール
3. [ ] 初回OAuth認証実行

#### 短期的に実施すべき項目:
1. [ ] テストイベント作成
2. [ ] エラーハンドリング強化
3. [ ] ログ記録実装

#### 中長期的に実施すべき項目:
1. [ ] 重複防止機能実装
2. [ ] イベント更新機能実装
3. [ ] 色分け・リマインダー機能実装

---

### 8.3 リスクと注意事項

**セキュリティ:**
- credentials.json, token.jsonは絶対に公開リポジトリにコミットしない
- .gitignoreに追加必須

**APIクォータ:**
- Google Calendar APIは無料枠: 1,000,000クエリ/日
- 通常使用では問題ないが、バッチ処理時は注意

**タイムゾーン:**
- 日本時間（Asia/Tokyo）で統一
- サーバーのタイムゾーン設定確認

---

## 9. 参考資料

- [Google Calendar API公式ドキュメント](https://developers.google.com/calendar/api/v3/reference)
- [Python Quickstart](https://developers.google.com/calendar/api/quickstart/python)
- [OAuth 2.0認証](https://developers.google.com/identity/protocols/oauth2)

---

**レポート作成者**: Backend Developer Agent
**最終更新**: 2025-12-06
