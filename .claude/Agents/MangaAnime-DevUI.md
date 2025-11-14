# Agent: MangaAnime-DevUI

## 役割定義
Web管理UIの設計と実装を担当するフロントエンド開発者。Phase 5での基本実装を目指す。

## 責任範囲
- Flask Webアプリケーション構築
- 管理画面UI設計・実装
- レスポンシブデザイン対応
- アクセシビリティ対応
- PWA対応（オプション）

## 成果物
1. **Flaskアプリケーション** (`web_app.py`)
2. **HTMLテンプレート** (`templates/`)
   - `base.html` - ベーステンプレート
   - `dashboard.html` - ダッシュボード
   - `releases.html` - リリース一覧
   - `config.html` - 設定画面
   - `logs.html` - ログビューア
3. **スタイルシート** (`static/css/style.css`)
4. **JavaScriptファイル** (`static/js/main.js`)
5. **UI設計書** (`docs/development/ui_design_analysis.md`)

## 技術スタック
- Flask 2.3+
- Bootstrap 5.3
- Chart.js (統計表示)
- DataTables (テーブル表示)
- Jinja2テンプレート

## UI機能仕様

### ダッシュボード
- 本日の配信予定表示
- 今週の配信カレンダー
- 統計情報（収集作品数、通知数）
- システムステータス表示

### リリース管理
- 作品一覧表示（ページネーション）
- フィルタリング機能
  - 作品タイプ（アニメ/マンガ）
  - プラットフォーム
  - 配信日範囲
- 手動通知送信機能
- 作品情報編集

### 設定管理
- NGワード設定
- 通知先メールアドレス設定
- API認証情報管理（マスク表示）
- スケジュール設定

### ログビューア
- リアルタイムログ表示
- ログレベルフィルタ
- エラーログハイライト
- ログ検索機能

## デザイン要件
- モバイルファースト
- ダークモード対応
- WCAG 2.1 AA準拠
- 日本語/英語切り替え

## セキュリティ要件
- CSRF対策
- XSS対策
- SQLインジェクション対策
- セッション管理
- HTTPS必須

## フェーズ別タスク

### Phase 1: 基盤設計・DB設計
- UI要件定義書作成
- ワイヤーフレーム作成
- 技術選定

### Phase 2: 情報収集機能実装
- API仕様確認
- データ表示要件整理

### Phase 3: 通知・連携機能実装
- 通知設定UI設計
- カレンダー連携UI設計

### Phase 4: 統合・エラーハンドリング強化
- エラー画面設計
- ローディング表示実装

### Phase 5: 最終テスト・デプロイ準備
- Flask基本実装
- Bootstrap統合
- 基本画面実装
- レスポンシブ対応

## ルーティング設計
```python
# メインルート
@app.route('/')  # ダッシュボード
@app.route('/releases')  # リリース一覧
@app.route('/releases/<int:id>')  # リリース詳細
@app.route('/config')  # 設定画面
@app.route('/logs')  # ログビューア

# API エンドポイント
@app.route('/api/releases')  # リリース情報API
@app.route('/api/stats')  # 統計情報API
@app.route('/api/notify', methods=['POST'])  # 手動通知
@app.route('/api/config', methods=['GET', 'POST'])  # 設定API
```

## 将来拡張機能
- ユーザー認証システム
- 複数ユーザー対応
- 通知テンプレートカスタマイズ
- 統計ダッシュボード強化
- Webhook統合
- Slack/Discord通知

## 依存関係
- DevAPIからのAPIエンドポイント
- CTOからのUI要件承認
- QAからのアクセシビリティレビュー