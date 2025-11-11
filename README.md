# 🎬 アニメ・マンガ最新情報配信システム

アニメやマンガの最新リリース情報を自動で収集し、Gmailでの通知とGoogleカレンダーへの自動登録を行うPythonベースの自動化システムです。

## ✨ 主な機能

- **📡 多ソース情報収集**
  - AniList GraphQL API（アニメ情報）
  - RSS フィード（マンガ・アニメ配信情報）
  - 将来: しょぼいカレンダーAPI対応予定

- **🔍 インテリジェントフィルタリング**
  - NGキーワードによる自動除外
  - ジャンル・タグベースフィルタリング
  - 重複データの自動検出・排除

- **📧 自動通知システム**
  - Gmail API経由でのHTML形式メール通知
  - 美しいレスポンシブデザインテンプレート
  - 作品種別ごとの色分け表示

- **📅 カレンダー統合**
  - Google Calendar への自動イベント作成
  - 配信日時の自動設定
  - カスタマイズ可能なリマインダー

- **💾 データ管理**
  - SQLite による軽量データベース
  - 重複防止機能
  - 自動データクリーンアップ

## 📋 システム要件

### 必須要件
- **Python 3.8+**
- **インターネット接続**
- **Google アカウント** (Gmail + Calendar)

### サポート環境
- **Linux** (Ubuntu, CentOS, etc.)
- **macOS**
- **Windows** (WSL推奨)

## 🚀 クイックスタート

### 1. プロジェクトのクローン・ダウンロード
```bash
git clone <repository-url>
cd Manga&Anime-Info-delivery-system
```

### 2. 自動セットアップの実行
```bash
# 基本セットアップ
python3 setup_system.py

# フルセットアップ（開発用）
python3 setup_system.py --full-setup

# テスト実行付きセットアップ
python3 setup_system.py --test-run
```

### 3. Google API 認証設定

#### 3.1 Google Cloud Console でのプロジェクト設定
1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. 新しいプロジェクトを作成（または既存プロジェクトを選択）
3. 以下のAPIを有効化：
   - Gmail API
   - Google Calendar API

#### 3.2 OAuth 2.0 認証情報の作成
1. 「認証情報」→「認証情報を作成」→「OAuth クライアント ID」
2. アプリケーションの種類: **デスクトップアプリケーション**
3. 作成した認証情報をダウンロード
4. ダウンロードしたJSONファイルを `credentials.json` として保存

### 4. 設定ファイルの調整
`config.json` を編集してメールアドレスやその他設定を調整：

```json
{
  "google": {
    "gmail": {
      "from_email": "your-email@gmail.com",
      "to_email": "your-email@gmail.com"
    }
  }
}
```

### 5. テスト実行
```bash
# ドライラン（実際の通知なし）
python3 release_notifier.py --dry-run

# 詳細ログ付きテスト
python3 release_notifier.py --dry-run --verbose
```

### 6. 定期実行の設定
```bash
# cron設定をインストール
crontab crontab.example
```

## 📁 プロジェクト構造

```
Manga&Anime-Info-delivery-system/
├── 📄 release_notifier.py       # メイン実行スクリプト
├── 📄 setup_system.py          # 自動セットアップスクリプト
├── 📄 config.json              # システム設定
├── 📄 requirements.txt         # Python依存関係
├── 📄 requirements-dev.txt     # 開発用依存関係
├── 📄 crontab.example          # cron設定例
├── 📁 modules/                 # コアモジュール
│   ├── 📄 __init__.py
│   ├── 📄 config.py            # 設定管理
│   ├── 📄 db.py                # データベース管理
│   ├── 📄 logger.py            # ログ管理
│   ├── 📄 models.py            # データモデル
│   ├── 📄 anime_anilist.py     # AniList API連携
│   ├── 📄 manga_rss.py         # RSS収集
│   ├── 📄 filter_logic.py      # フィルタリング
│   ├── 📄 mailer.py            # Gmail通知
│   ├── 📄 calendar.py          # カレンダー統合
│   ├── 📄 security_utils.py    # セキュリティユーティリティ
│   └── 📄 qa_validation.py     # 品質保証
├── 📁 tests/                   # テストスイート
├── 📁 templates/               # メールテンプレート（Web UI）
├── 📁 static/                  # 静的ファイル（Web UI）
├── 📁 logs/                    # ログファイル
└── 📁 data/                    # データファイル
    └── 💾 db.sqlite3           # SQLiteデータベース
```

## ⚙️ 設定詳細

### メイン設定ファイル (`config.json`)

```json
{
  "system": {
    "name": "MangaAnime情報配信システム",
    "version": "1.0.0",
    "environment": "production"
  },
  "apis": {
    "anilist": {
      "rate_limit": {
        "requests_per_minute": 90
      }
    }
  },
  "google": {
    "credentials_file": "./credentials.json",
    "gmail": {
      "from_email": "your-email@gmail.com",
      "to_email": "your-email@gmail.com",
      "subject_prefix": "[アニメ・マンガ情報]"
    },
    "calendar": {
      "calendar_id": "primary",
      "reminder_minutes": [60, 10]
    }
  },
  "filtering": {
    "ng_keywords": [
      "エロ", "R18", "成人向け", "BL", "百合"
    ]
  }
}
```

## 🖥️ Web UI (オプション)

システムにはオプションのWeb管理インターフェースが含まれています：

```bash
# Web UIの起動
python3 start_web_ui.py

# カスタムポート・ホストで起動
python3 start_web_ui.py --host 0.0.0.0 --port 8080
```

**機能:**
- 📊 ダッシュボード（統計・最新情報）
- 📅 カレンダービュー
- ⚙️ 設定管理
- 📋 リリース履歴
- 📝 システムログ

## 🧪 テスト

### テストスイートの実行
```bash
# 全テストの実行
python3 -m pytest tests/

# カバレッジレポート付き
python3 -m pytest tests/ --cov=modules --cov-report=html

# 特定のテストのみ
python3 -m pytest tests/test_db.py -v
```

### セキュリティ・品質チェック
```bash
# セキュリティスキャン
python3 security_qa_cli.py --mode security

# 品質チェック
python3 security_qa_cli.py --mode qa

# 統合チェック
python3 security_qa_cli.py --mode full
```

## 📊 使用例・ログ出力

### 正常実行時の出力
```
============================================================
🚀 MangaAnime情報配信システム v1.0.0 開始
環境: production
ドライランモード: 無効
============================================================
📡 情報収集を開始します...
  anilist から情報収集中...
  anilist: 25 件の情報を取得
  manga_rss から情報収集中...
  manga_rss: 12 件の情報を取得
📡 情報収集完了: 総計 37 件
🔍 データ処理とフィルタリングを開始します...
🔍 フィルタリング完了: 35 件が残存 (2 件除外)
💾 データベース保存を開始します...
💾 データベース保存完了: 8 件の新しいリリース
📧 通知処理を開始します: 8 件
✅ メール通知を送信しました
✅ カレンダーイベントを 8 件作成しました
============================================================
📊 実行結果レポート
============================================================
実行時間: 45.2秒
新リリース数: 8
通知送信数: 1
カレンダーイベント作成数: 8
エラー発生回数: 0
============================================================
✅ すべての処理が正常に完了しました
```

## 🔧 トラブルシューティング

### よくある問題と解決方法

#### 1. Google API 認証エラー
```
❌ Gmail認証に失敗しました
```
**解決方法:**
- `credentials.json` が正しく配置されているか確認
- Google Cloud Console でAPIが有効化されているか確認
- OAuth同意画面の設定を確認

#### 2. データベースエラー
```
❌ データベース初期化エラー
```
**解決方法:**
```bash
# データベースファイルの削除と再作成
rm db.sqlite3
python3 setup_system.py
```

#### 3. RSS フィード取得エラー
```
❌ manga_rss でエラーが発生
```
**解決方法:**
- インターネット接続を確認
- RSS URLが変更されていないか確認
- プロキシ設定が必要な環境の場合は設定を追加

### ログファイルの確認
```bash
# 最新のログを確認
tail -f logs/app.log

# エラーログのみ確認
grep ERROR logs/app.log

# 特定日付のログ確認
grep "2024-08-08" logs/app.log
```

## 🔐 セキュリティ考慮事項

- **認証情報の管理**: `credentials.json` と `token.json` は適切なファイル権限で保護
- **NGワードフィルタ**: 不適切なコンテンツの自動除外
- **レート制限**: API制限の遵守
- **入力検証**: 外部データの安全な処理
- **ログ管理**: 機密情報のログ出力防止

## 🤝 開発・貢献

### 開発環境セットアップ
```bash
# 開発用依存関係のインストール
pip install -r requirements-dev.txt

# フルセットアップ
python3 setup_system.py --full-setup

# 開発用サーバー起動
python3 start_web_ui.py --debug
```

### コード品質
```bash
# フォーマット
black modules/ tests/

# リント
flake8 modules/ tests/

# 型チェック
mypy modules/
```

## 📄 ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。

## 🙏 謝辞

- **AniList**: アニメデータAPI提供
- **RSS フィードプロバイダ**: マンガ・アニメ情報提供
- **Google APIs**: Gmail・Calendar統合
- **オープンソースコミュニティ**: 使用ライブラリ開発

---

## 📞 サポート

問題や質問がある場合は、以下をご利用ください：

- **バグレポート**: GitHub Issues
- **機能要望**: GitHub Discussions  
- **ドキュメント**: このREADME + コード内docstring

**🤖 Generated with ClaudeCode Agent System**