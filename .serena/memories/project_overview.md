# MangaAnime-Info-delivery-system プロジェクト概要

## プロジェクトの目的
アニメ・マンガの最新情報を自動で収集し、Gmail通知とGoogleカレンダー統合により、リアルタイムでユーザーに配信する完全自動化システム。

## 技術スタック
- **言語**: Python 3.x
- **データベース**: SQLite3（WAL モード対応）
- **API連携**: 
  - AniList GraphQL API（アニメ情報）
  - しょぼいカレンダーAPI（放送情報）
  - Google Calendar API / Gmail API（通知）
- **Webフレームワーク**: Flask（Web UI用）
- **RSSパーサー**: feedparser
- **HTTP クライアント**: requests, httpx
- **テスト**: pytest（カバレッジ20%以上必須）

## 主要ディレクトリ構造
```
./
├── modules/              # コアモジュール群
│   ├── db.py            # データベースマネージャー
│   ├── anime_anilist.py # AniList API連携
│   ├── anime_syoboi.py  # しょぼいカレンダー連携
│   ├── manga_rss.py     # マンガRSS収集
│   ├── mailer.py        # メール送信
│   ├── calendar_integration.py  # カレンダー連携
│   ├── config.py        # 設定管理
│   └── filter_logic.py  # NGワードフィルタリング
├── app/                  # アプリケーションエントリポイント
│   ├── web_ui.py        # Web UI
│   └── release_notifier.py  # 通知スクリプト
├── tests/               # テストコード
├── scripts/             # 自動化スクリプト
├── auth/                # OAuth認証関連
├── config.json          # 設定ファイル
└── db.sqlite3           # データベース
```

## データベーススキーマ
- **works**: 作品情報（タイトル、タイプ、URL等）
- **releases**: リリース情報（話数、プラットフォーム、配信日等）
- **settings**: システム設定
- **notification_history**: 通知履歴

## 外部API
- AniList: GraphQL API（1分あたり90リクエスト制限）
- しょぼいカレンダー: 日本国内TV放送情報
- dアニメストア公式RSS
- 出版社/電子書籍ストアRSS
