# Web UI for Anime/Manga Information Delivery System

## 概要

このWeb UIは、アニメ・マンガ情報配信システムの管理インターフェースです。ブラウザから直感的にシステムの状態確認、設定変更、リリース履歴の閲覧などが行えます。

## 機能

### 📊 ダッシュボード
- システム統計の表示（総作品数、リリース数、未通知件数など）
- 最近のリリース一覧（7日以内）
- 今後の予定（7日以内）
- リアルタイム更新（5分間隔）

### 📋 リリース履歴
- 全リリースの検索・フィルタリング
- 作品名、種類、プラットフォーム別の絞り込み
- ページネーション対応
- CSV/JSON形式でのエクスポート

### 📅 カレンダー表示
- 月別カレンダーでのリリース予定表示
- 日付別詳細表示
- Googleカレンダーとの連携

### ⚙️ 設定管理
- 通知先メールアドレス設定
- データソース有効/無効切り替え
- NGワード管理
- チェック間隔設定

### 📝 ログ・システム状態
- リアルタイムログビューア
- システム状態監視
- ログレベル別フィルタリング
- ログファイルのダウンロード

## 起動方法

### 基本的な起動

```bash
python3 start_web_ui.py
```

または

```bash
python3 web_app.py
```

### オプション付き起動

```bash
# ポート指定
python3 start_web_ui.py --port 8080

# ホスト指定
python3 start_web_ui.py --host 192.168.1.100

# デバッグモード
python3 start_web_ui.py --debug

# 全オプション
python3 start_web_ui.py --host 0.0.0.0 --port 5000 --debug
```

## アクセス方法

ブラウザで以下のURLにアクセスしてください：

- ローカル: `http://localhost:5000`
- ネットワーク: `http://[サーバーIP]:5000`

## 前提条件

### 必要なPythonパッケージ
```bash
pip install flask flask-bootstrap bootstrap-flask
```

または

```bash
pip install -r requirements.txt
```

### 必要なファイル（オプション）
- `db.sqlite3` - データベースファイル（メインシステムで作成）
- `config.json` - 設定ファイル

これらのファイルがない場合でもWeb UIは起動しますが、一部機能が制限されます。

## ディレクトリ構成

```
/
├── web_app.py              # メインFlaskアプリケーション
├── start_web_ui.py         # 起動スクリプト
├── templates/              # HTMLテンプレート
│   ├── base.html          # ベーステンプレート
│   ├── dashboard.html     # ダッシュボード
│   ├── releases.html      # リリース履歴
│   ├── calendar.html      # カレンダー
│   ├── config.html        # 設定
│   └── logs.html          # ログ・状態
├── static/                 # 静的ファイル
│   ├── css/
│   │   └── style.css      # カスタムCSS
│   └── js/
│       └── main.js        # JavaScript
└── logs/                   # ログディレクトリ
```

## 技術仕様

### フロントエンド
- **Bootstrap 5.3**: レスポンシブUI
- **Bootstrap Icons**: アイコンフォント
- **jQuery 3.7**: DOM操作
- **カスタムCSS/JS**: アニメーション、インタラクション

### バックエンド
- **Flask 2.3**: Webフレームワーク
- **Flask-Bootstrap**: Bootstrap統合
- **SQLite3**: データベース
- **Python 3.9+**: 実行環境

### 機能
- **リアルタイム更新**: AJAX
- **レスポンシブデザイン**: モバイル対応
- **検索・フィルタ**: 高速検索
- **エクスポート**: CSV/JSON
- **多言語対応**: 日本語UI

## API エンドポイント

### データ取得
- `GET /api/stats` - システム統計
- `GET /api/releases/recent` - 最近のリリース

### 設定管理
- `GET /config` - 設定表示
- `POST /config` - 設定保存

### その他
- `GET /releases` - リリース履歴
- `GET /calendar` - カレンダー
- `GET /logs` - ログ表示

## カスタマイズ

### テーマ変更
`static/css/style.css`でカスタムスタイルを変更できます。

### 言語設定
テンプレート内のテキストを変更することで多言語化可能です。

### 機能拡張
- 新しいページを追加する場合は`templates/`にHTMLファイルを作成
- ルートを`web_app.py`に追加
- 必要に応じてCSS/JSを`static/`に追加

## トラブルシューティング

### ポートが使用中の場合
```bash
python3 start_web_ui.py --port 8080
```

### パーミッションエラー
```bash
sudo python3 start_web_ui.py --port 80
```

### ログが表示されない
`logs/`ディレクトリが存在し、書き込み権限があることを確認してください。

### データベースエラー
メインシステムを先に実行してデータベースを初期化してください。

## セキュリティ

### 本番環境での注意点
- `SECRET_KEY`環境変数を設定
- `debug=False`で起動
- リバースプロキシ（nginx等）の使用を推奨
- HTTPS通信の設定

### 環境変数
```bash
export SECRET_KEY="your-secret-key-here"
export FLASK_ENV="production"
```

## 更新履歴

- v1.0.0: 初期リリース
  - ダッシュボード機能
  - リリース履歴表示
  - カレンダー表示
  - 設定管理
  - ログビューア

## サポート

質問や問題がある場合は、メインプロジェクトのドキュメントを参照するか、システムログを確認してください。