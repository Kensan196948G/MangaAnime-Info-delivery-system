# Google Calendar連携機能 - ドキュメントインデックス

**プロジェクト:** MangaAnime-Info-delivery-system
**機能:** Google Calendar統合
**ステータス:** 実装完了・認証待ち

---

## クイックアクセス

### 今すぐ始める

- **[クイックスタート（10分）](QUICKSTART_CALENDAR.md)** - 最速でセットアップ
- **[実装サマリー](IMPLEMENTATION_SUMMARY.md)** - 全体像を把握

### 詳細情報

- **[セットアップガイド](docs/CALENDAR_SETUP_GUIDE.md)** - 完全な手順書
- **[実装レポート](CALENDAR_INTEGRATION_REPORT.md)** - 技術詳細

---

## ディレクトリ構成

```
/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/
│
├── 📚 ドキュメント
│   ├── README_CALENDAR.md                   # このファイル
│   ├── QUICKSTART_CALENDAR.md               # クイックスタート
│   ├── IMPLEMENTATION_SUMMARY.md            # 実装サマリー
│   ├── CALENDAR_INTEGRATION_REPORT.md       # 詳細レポート
│   └── docs/
│       └── CALENDAR_SETUP_GUIDE.md          # セットアップガイド
│
├── 🔧 スクリプト
│   ├── enable_calendar.py                   # 設定有効化
│   ├── check_calendar_status.py             # 状態確認
│   ├── test_calendar_dryrun.py              # Dry-runテスト
│   ├── run_calendar_integration_test.sh     # 統合テスト
│   ├── setup_calendar.sh                    # セットアップ
│   └── finalize_calendar_setup.sh           # 最終セットアップ
│
├── 💻 実装
│   └── modules/
│       └── calendar_integration.py          # カレンダー統合モジュール
│
└── ⚙️ 設定
    ├── config.json                          # 設定ファイル
    ├── .gitignore_calendar                  # セキュリティ設定
    ├── credentials.json                     # OAuth認証情報（要配置）
    └── token.json                           # アクセストークン（自動生成）
```

---

## セットアップフロー

### 最速セットアップ（10分）

```bash
# 1. 統合テスト実行
bash finalize_calendar_setup.sh

# 2. credentials.json配置（Google Cloud Consoleから取得）
# 詳細: docs/CALENDAR_SETUP_GUIDE.md

# 3. パッケージインストール
pip3 install google-auth google-auth-oauthlib google-api-python-client

# 4. 初回認証
python3 modules/calendar_integration.py
```

### 段階的セットアップ

```bash
# ステップ1: 状態確認
python3 check_calendar_status.py

# ステップ2: 設定有効化
python3 enable_calendar.py

# ステップ3: Dry-runテスト
python3 test_calendar_dryrun.py

# ステップ4: credentials.json配置（手動）

# ステップ5: 初回認証
python3 modules/calendar_integration.py
```

---

## 使用方法

### 基本的な使い方

```python
import json
from modules.calendar_integration import sync_releases_to_calendar

# 設定読み込み
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

# カレンダー同期
created_count = sync_releases_to_calendar(releases, config)
print(f"{created_count}件のイベントを作成しました")
```

### 今後のイベント取得

```python
from modules.calendar_integration import list_upcoming_events

# 今後7日間のイベント取得
events = list_upcoming_events(7)
```

---

## 主要機能

### カレンダー統合モジュール（modules/calendar_integration.py）

| 関数 | 説明 |
|------|------|
| `get_calendar_service()` | Google Calendar APIサービス取得 |
| `create_calendar_event()` | イベント作成 |
| `check_event_exists()` | 重複チェック |
| `sync_releases_to_calendar()` | リリース情報をカレンダーに同期 |
| `list_upcoming_events()` | 今後のイベント取得 |
| `delete_event()` | イベント削除 |

### 設定オプション（config.json）

```json
{
  "calendar": {
    "enabled": true,
    "calendar_id": "primary",
    "event_color_anime": "9",    // ブルーベリー
    "event_color_manga": "10"    // バジル
  }
}
```

---

## トラブルシューティング

### よくある問題

| 問題 | 解決方法 |
|------|----------|
| credentials.jsonが見つからない | [セットアップガイド](docs/CALENDAR_SETUP_GUIDE.md)参照 |
| パッケージエラー | `pip3 install google-auth google-auth-oauthlib google-api-python-client` |
| 認証エラー | `rm token.json && python3 modules/calendar_integration.py` |

### 状態確認

```bash
python3 check_calendar_status.py
```

---

## セキュリティ

### 重要な注意事項

以下のファイルは**絶対にGitにコミットしないでください**:

- `credentials.json` - OAuth認証情報
- `token.json` - アクセストークン

### .gitignoreの設定

```bash
# .gitignore_calendarの内容を.gitignoreにマージ
cat .gitignore_calendar >> .gitignore
```

---

## ドキュメント詳細

### 📘 QUICKSTART_CALENDAR.md

**対象:** 初心者・すぐに使いたい方
**所要時間:** 10分
**内容:**
- 5分でセットアップ
- 最速フロー
- トラブルシューティング

### 📗 docs/CALENDAR_SETUP_GUIDE.md

**対象:** 初回セットアップを行う方
**所要時間:** 30分
**内容:**
- Google Cloud Console設定手順
- OAuth認証情報取得方法
- 詳細なトラブルシューティング
- セキュリティ注意事項

### 📕 CALENDAR_INTEGRATION_REPORT.md

**対象:** 開発者・技術詳細を知りたい方
**所要時間:** 15分
**内容:**
- 実装詳細
- 技術仕様
- API仕様
- 関数リファレンス

### 📙 IMPLEMENTATION_SUMMARY.md

**対象:** プロジェクト管理者・全体把握が必要な方
**所要時間:** 5分
**内容:**
- 実装概要
- ファイル構成
- チェックリスト
- 今後の拡張予定

---

## サポート

### コマンド一覧

```bash
# 状態確認
python3 check_calendar_status.py

# 設定有効化
python3 enable_calendar.py

# Dry-runテスト
python3 test_calendar_dryrun.py

# 統合テスト
bash run_calendar_integration_test.sh

# 最終セットアップ
bash finalize_calendar_setup.sh

# 初回認証
python3 modules/calendar_integration.py

# 今後のイベント取得
python3 -c "from modules.calendar_integration import list_upcoming_events; list_upcoming_events(7)"
```

---

## 実装ステータス

### ✅ 完了

- カレンダー統合モジュール
- 設定管理
- テスト環境
- ドキュメント
- セキュリティ設定

### ⚠️ 手動作業が必要

- Google Cloud Console設定
- credentials.json取得
- 初回認証実行

---

## バージョン情報

- **実装日:** 2025-12-06
- **実装者:** Backend Developer Agent
- **バージョン:** 1.0.0
- **Python要件:** 3.7以上
- **API:** Google Calendar API v3

---

## リンク

### プロジェクト内

- [クイックスタート](QUICKSTART_CALENDAR.md)
- [セットアップガイド](docs/CALENDAR_SETUP_GUIDE.md)
- [実装レポート](CALENDAR_INTEGRATION_REPORT.md)
- [実装サマリー](IMPLEMENTATION_SUMMARY.md)

### 外部

- [Google Calendar API Documentation](https://developers.google.com/calendar/api)
- [Google Cloud Console](https://console.cloud.google.com/)
- [OAuth 2.0 Guide](https://developers.google.com/identity/protocols/oauth2)

---

**最終更新:** 2025-12-06
**メンテナー:** Backend Developer Agent
**ライセンス:** プロジェクトに準拠
