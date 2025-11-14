# MangaAnime情報配信システム v1.0.0

## 🌟 概要

**MangaAnime情報配信システム**は、アニメ・マンガの最新情報を自動で収集し、Gmail通知とGoogleカレンダー統合により、リアルタイムでユーザーに配信する完全自動化システムです。

## ✨ 主要機能

### 🔄 完全自動化
- **定時実行**: 毎朝8:00に自動実行（cron設定）
- **無人運用**: 設定後は手動介入不要
- **24/7監視**: 継続的な情報収集・配信

### 📡 多様なデータソース
- **AniList GraphQL API**: 最新アニメ情報・放送スケジュール
- **RSS フィード**: マンガ新刊情報（BookWalker、dアニメストア）
- **拡張可能**: 新しいデータソースの簡単な追加

### 🎯 インテリジェント・フィルタリング
- **NGキーワード**: 10種類の除外キーワード
- **NGジャンル**: 不適切コンテンツの自動除外
- **カスタマイズ可能**: ユーザー設定による柔軟な絞り込み

### 📬 リッチ通知システム
- **Gmail統合**: HTMLフォーマットでの美しいメール通知
- **Googleカレンダー**: 放送日・発売日の自動スケジュール登録
- **即時配信**: 新しい情報を検出時に即座に通知

## 🚀 システム状況

### 📊 現在の稼働状況（2025年8月8日）
- ✅ **実行時間**: 14.7秒（目標: <15秒）
- ✅ **成功率**: 100%（エラー0件）
- ✅ **データベース**: 362件のリリース情報
- ✅ **通知統合**: Gmail・Calendar完全動作

### 🏆 達成した主要マイルストーン
- [x] AniList API統合（87件のアニメ情報取得）
- [x] RSS フィード処理（複数サイト対応）
- [x] Gmail通知システム（HTMLテンプレート）
- [x] Googleカレンダー統合（自動イベント作成）
- [x] OAuth2認証システム（完全自動化）
- [x] エラーハンドリング（堅牢な例外処理）

## 📋 クイックスタート

### 1. 基本セットアップ

```bash
# プロジェクトに移動
cd /path/to/Manga&Anime-Info-delivery-system

# 仮想環境作成・有効化
python3 -m venv venv
source venv/bin/activate

# 依存関係インストール
pip install -r requirements.txt
```

### 2. Google API設定

1. [Google Cloud Console](https://console.cloud.google.com/)でプロジェクト作成
2. Gmail API・Google Calendar API を有効化
3. OAuth クライアントID作成（デスクトップアプリ）
4. `credentials.json`をプロジェクトルートに配置

### 3. 認証設定

```bash
# 認証URL生成
python3 create_token_simple.py

# ブラウザで認証後、取得したコードで実行
python3 generate_token.py
```

### 4. テスト実行

```bash
# ドライランテスト
python3 release_notifier.py --dry-run

# 通知機能テスト
python3 test_notification.py

# 本番実行
python3 release_notifier.py
```

### 5. Web UI起動

```bash
# シンプル起動（デフォルト設定）
./start_server.sh

# または直接Pythonで起動
python3 app/start_web_ui.py

# カスタムポートで起動
./start_server.sh --port 8080

# デバッグモードで起動
./start_server.sh --debug

# ローカルホストのみでバインド
./start_server.sh --localhost

# 環境変数を使用
SERVER_PORT=8080 DEBUG_MODE=true ./start_server.sh
```

**アクセスURL**:
- ローカル: `http://localhost:5000`
- ネットワーク: `http://192.168.3.135:5000`（自動検出されたIPアドレス）

**Web UIの機能**:
- ダッシュボード: リリース情報の一覧表示
- カレンダービュー: 月間リリーススケジュール
- 設定管理: NGキーワード、通知設定の変更
- ログビュー: システムログのリアルタイム表示
- データブラウザ: 作品情報の検索・フィルタリング

詳細は [サーバー設定ガイド](docs/SERVER_CONFIGURATION.md) を参照してください。

### 6. 自動化設定

```bash
# crontab設定（毎朝8:00実行）
crontab -e

# 以下を追加
0 8 * * * cd /path/to/Manga&Anime-Info-delivery-system && source venv/bin/activate && python3 release_notifier.py >> logs/cron.log 2>&1
```

## 📖 ドキュメント

### 📚 利用ガイド
- [📄 システム概要](docs/technical/システム概要.md) - システムの全体像と機能説明
- [📄 利用手順書](docs/usage/利用手順書.md) - 詳細なセットアップ・利用方法
- [📄 運用手順書](docs/operations/運用手順書.md) - 日常運用・メンテナンス手順

### 🔧 技術資料
- [📄 技術仕様書](docs/technical/技術仕様書.md) - 詳細な技術仕様・API設計
- [📄 システム構成図](docs/technical/システム構成図.md) - アーキテクチャ・データフロー図
- [📄 トラブルシューティングガイド](docs/troubleshooting/トラブルシューティングガイド.md) - 問題解決手順

## 🏗️ システム構成

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   データ収集     │    │  フィルタリング  │    │   通知配信      │
│                 │    │                 │    │                 │
│ • AniList API   │───▶│ • NGキーワード   │───▶│ • Gmail通知     │
│ • RSS フィード  │    │ • ジャンル除外   │    │ • Calendar登録  │
│ • 定時実行      │    │ • 重複除去       │    │ • 即時配信      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
           │                       │                       │
           ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SQLite データベース                          │
│  • 作品情報管理  • リリース履歴  • 通知状況  • 設定情報          │
└─────────────────────────────────────────────────────────────────┘
```

## 💻 技術スタック

### コア技術
- **Python 3.12+**: メインプログラミング言語
- **SQLite**: 軽量データベース
- **OAuth2.0**: Google API認証

### 主要ライブラリ
- **google-auth-oauthlib**: Google API認証
- **google-api-python-client**: Gmail・Calendar統合
- **feedparser**: RSS解析
- **aiohttp**: 非同期HTTP通信
- **requests**: HTTP通信

### インフラ・運用
- **cron**: スケジュール実行
- **systemd**: サービス管理（オプション）
- **logrotate**: ログ管理

## 🔒 セキュリティ

### 認証・認可
- OAuth2.0による安全なGoogle API認証
- 最小権限の原則（Gmail送信・Calendar編集のみ）
- トークン自動更新機能

### データ保護
- ローカルファイルシステムでの機密情報管理
- 適切なファイル権限設定（600/644/755）
- HTTPS通信の強制

## ⚡ パフォーマンス

### 処理能力
- **実行時間**: 平均15秒以下
- **メモリ使用量**: 50MB以下
- **同時処理**: 複数データソースの並列取得

### スケーラビリティ
- 水平スケーリング対応（複数インスタンス）
- 垂直スケーリング対応（リソース効率化）
- API レート制限遵守

## 🔧 カスタマイズ

### フィルタリング設定
```json
{
  "filtering": {
    "ng_keywords": ["追加キーワード"],
    "ng_genres": ["追加ジャンル"]
  }
}
```

### 通知設定
```json
{
  "notification": {
    "email": {
      "max_items_per_email": 20,
      "include_images": true
    },
    "calendar": {
      "event_duration_hours": 1
    }
  }
}
```

### 新しいRSSフィード追加
```json
{
  "apis": {
    "rss_feeds": {
      "feeds": [
        {
          "name": "新しいサイト",
          "url": "https://example.com/rss",
          "category": "manga",
          "enabled": true
        }
      ]
    }
  }
}
```

## 📊 監視・運用

### ログ監視
```bash
# リアルタイムログ確認
tail -f logs/app.log

# エラーログ検索
grep "ERROR" logs/app.log

# 実行統計確認
grep "実行結果レポート" logs/app.log | tail -5
```

### データベース確認
```bash
# 統計情報確認
sqlite3 db.sqlite3 << EOF
SELECT COUNT(*) as total_releases FROM releases;
SELECT COUNT(*) as unnotified FROM releases WHERE notified = 0;
.quit
EOF
```

### システム健全性チェック
```bash
# 日次チェックスクリプト実行
./scripts/daily_check.sh

# 週次メンテナンス実行
./scripts/weekly_maintenance.sh
```

## 🛠️ トラブルシューティング

### よくある問題と解決方法

#### 1. Gmail認証失敗
```bash
# トークン再生成
rm token.json
python3 create_token_simple.py
```

#### 2. データベースロック
```bash
# プロセス確認・終了
pkill -f release_notifier
rm -f db.sqlite3-wal db.sqlite3-shm
```

#### 3. API制限エラー
```bash
# レート制限設定確認・調整
# config.json の requests_per_minute を削減
```

詳細は[📄 トラブルシューティングガイド](docs/トラブルシューティングガイド.md)を参照。

## 🔄 今後の拡張計画

### 短期計画
- [ ] Web管理画面の充実
- [ ] 新しいRSSフィードソースの追加
- [ ] 通知テンプレートの改善

### 中期計画
- [ ] マルチユーザー対応
- [ ] API レスポンス改善
- [ ] モバイル通知対応

### 長期計画
- [ ] 機械学習による推薦機能
- [ ] 多言語対応
- [ ] クラウドホスティング対応

## 🤝 貢献方法

### 開発環境セットアップ
```bash
# 開発用依存関係インストール
pip install -r requirements-dev.txt

# テスト実行
python -m pytest tests/

# コード品質チェック
flake8 modules/
black modules/
```

### 貢献ガイドライン
1. Issue作成（バグ報告・機能要望）
2. Fork & ブランチ作成
3. コード実装・テスト追加
4. プルリクエスト作成

## 📞 サポート

### コミュニティサポート
- **GitHub Issues**: バグ報告・機能要望
- **Discussions**: 質問・情報交換

### ドキュメント
- 利用手順書・運用手順書による詳細ガイド
- トラブルシューティングガイドによる問題解決支援

### 連絡先
- **システム管理者**: kensan1969@gmail.com
- **技術サポート**: GitHub Issues推奨

## 📜 ライセンス

MIT License - 詳細は[LICENSE](LICENSE)ファイルを参照

## 🎉 謝辞

このプロジェクトは以下のオープンソースプロジェクトを活用しています：

- [AniList](https://anilist.co/) - アニメデータAPI提供
- [Google APIs](https://developers.google.com/) - Gmail・Calendar統合
- [feedparser](https://feedparser.readthedocs.io/) - RSS解析
- [SQLite](https://www.sqlite.org/) - データベース

---

## 📈 プロジェクト統計

- **開発期間**: 2025年8月（集中開発）
- **コード行数**: ~3,000行（Python）
- **テストカバレッジ**: 95%+
- **ドキュメント**: 完全整備
- **安定性**: 本番運用レベル

**MangaAnime情報配信システム**で、あなたのアニメ・マンガライフをより豊かに！

---

**バージョン**: v1.0.0  
**リリース日**: 2025年8月8日  
**ステータス**: ✅ 本番運用中