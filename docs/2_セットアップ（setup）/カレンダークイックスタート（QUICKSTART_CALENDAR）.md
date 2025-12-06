# Google Calendar連携 クイックスタート

このガイドでは、最速でGoogle Calendar連携機能を使い始める方法を説明します。

## 5分でセットアップ

### ステップ1: 状態確認（1分）

```bash
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system
python3 check_calendar_status.py
```

### ステップ2: 設定有効化（30秒）

```bash
python3 enable_calendar.py
```

### ステップ3: Dry-runテスト（30秒）

```bash
python3 test_calendar_dryrun.py
```

ここまでで、実装が正しいことを確認できます。

---

## 実際のカレンダー連携を有効化

### ステップ4: credentials.jsonを取得（2分）

1. [Google Cloud Console](https://console.cloud.google.com/apis/credentials) にアクセス
2. 新しいプロジェクトを作成
3. Google Calendar APIを有効化
4. OAuth 2.0 クライアントIDを作成（デスクトップアプリ）
5. credentials.jsonをダウンロード
6. プロジェクトルートに配置

**詳細手順:** [docs/CALENDAR_SETUP_GUIDE.md](docs/CALENDAR_SETUP_GUIDE.md)

### ステップ5: パッケージインストール（1分）

```bash
pip3 install google-auth google-auth-oauthlib google-api-python-client
```

### ステップ6: 初回認証（1分）

```bash
python3 modules/calendar_integration.py
```

ブラウザが開き、Googleアカウントでの認証を求められます。

「許可」をクリックすれば完了です。

---

## 動作確認

### 今後7日間のイベントを表示

```bash
python3 -c "from modules.calendar_integration import list_upcoming_events; list_upcoming_events(7)"
```

### テストイベントを作成（Dry-run）

```bash
python3 test_calendar_dryrun.py
```

---

## メインスクリプトからの使用

```python
import json
from modules.calendar_integration import sync_releases_to_calendar

# 設定を読み込み
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# リリース情報
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
sync_releases_to_calendar(releases, config)
```

---

## トラブルシューティング

### credentials.jsonが見つからない

→ ステップ4を実行してください

### パッケージエラー

```bash
pip3 install google-auth google-auth-oauthlib google-api-python-client
```

### 認証エラー

```bash
rm token.json
python3 modules/calendar_integration.py
```

---

## 詳細ドキュメント

- **完全セットアップガイド:** [docs/CALENDAR_SETUP_GUIDE.md](docs/CALENDAR_SETUP_GUIDE.md)
- **実装レポート:** [CALENDAR_INTEGRATION_REPORT.md](CALENDAR_INTEGRATION_REPORT.md)

---

**所要時間:** 約10分
**難易度:** 初級
