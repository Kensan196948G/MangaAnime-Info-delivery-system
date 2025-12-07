# ウォッチリスト機能実装ガイド

**作成日**: 2025-12-07
**ステータス**: 完了

## 概要

ユーザーが気になるアニメ・マンガ作品を「ウォッチリスト（お気に入り）」に登録し、新エピソードや新刊の通知を受け取れる機能を実装しました。

## 実装ファイル

### 1. データベース

#### `/migrations/008_watchlist.sql`
- `watchlist` テーブル作成
- インデックス作成
- トリガー設定（updated_at自動更新）
- 統計ビュー作成

**主要カラム**:
```sql
- user_id: ユーザーID（外部キー）
- work_id: 作品ID（外部キー）
- notify_new_episodes: エピソード通知ON/OFF
- notify_new_volumes: 巻数通知ON/OFF
- priority: 優先度（0-5）
- notes: メモ
```

### 2. バックエンド

#### `/app/routes/watchlist.py`
FlaskのBlueprintとして実装。以下のエンドポイントを提供:

**ページ**:
- `GET /watchlist/` - ウォッチリスト表示ページ

**API**:
- `GET /watchlist/api/list` - ウォッチリスト一覧取得（JSON）
- `POST /watchlist/api/add` - 作品を追加
- `DELETE /watchlist/api/remove/<work_id>` - 作品を削除
- `PUT /watchlist/api/update/<work_id>` - 通知設定を更新
- `GET /watchlist/api/check/<work_id>` - 登録状態を確認
- `GET /watchlist/api/stats` - 統計情報取得

#### `/modules/watchlist_notifier.py`
通知処理のコアロジック:

**主要クラス**: `WatchlistNotifier`

**主要メソッド**:
- `get_new_releases_for_watchlist()` - ウォッチリスト登録作品の新規リリース取得
- `mark_as_notified()` - リリースを通知済みマーク
- `format_notification_email()` - 通知メールHTML生成
- `get_watchlist_summary()` - ウォッチリスト統計取得

### 3. フロントエンド

#### `/templates/watchlist.html`
ウォッチリスト表示ページ:
- 登録作品一覧（カード形式）
- 通知設定トグル（エピソード/巻別）
- 削除ボタン
- 統計情報表示
- 空状態UI

#### `/static/js/watchlist.js`
ウォッチリスト操作のJavaScriptライブラリ:

**主要クラス**: `WatchlistManager`

**機能**:
- ウォッチリスト状態のキャッシュ管理
- ボタン状態の自動更新
- 追加/削除のAJAX処理
- トースト通知表示

### 4. スクリプト

#### `/scripts/run_watchlist_notifications.py`
定期実行用の通知スクリプト:
- ウォッチリスト登録作品の新規リリースをチェック
- ユーザーごとにメール送信
- 送信済みリリースを自動マーク

#### `/scripts/migrate_watchlist.sh`
マイグレーション実行スクリプト:
- データベースバックアップ
- マイグレーション適用
- テーブル確認

### 5. テスト

#### `/tests/test_watchlist_comprehensive.py`
包括的なテストスイート:
- ユニットテスト
- APIテスト
- 統合テスト

## セットアップ手順

### 1. マイグレーション実行

```bash
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system
chmod +x scripts/migrate_watchlist.sh
./scripts/migrate_watchlist.sh
```

### 2. Blueprintを登録

`app/web_app.py` (またはメインのFlaskアプリファイル) に以下を追加:

```python
from app.routes.watchlist import watchlist_bp

# Blueprintを登録
app.register_blueprint(watchlist_bp)
```

### 3. JavaScriptを読み込み

ベーステンプレート (`templates/base.html`) に以下を追加:

```html
<!-- ウォッチリスト機能 -->
<script src="{{ url_for('static', filename='js/watchlist.js') }}"></script>
```

### 4. ナビゲーションバーにリンク追加

```html
{% if current_user.is_authenticated %}
<li class="nav-item">
    <a class="nav-link" href="{{ url_for('watchlist.watchlist_page') }}">
        <i class="bi bi-star-fill"></i> ウォッチリスト
        <span id="watchlistCount" class="badge bg-warning">0</span>
    </a>
</li>
{% endif %}
```

### 5. 作品一覧にウォッチリストボタン追加

作品一覧ページ（`templates/works.html`など）に:

```html
<button class="btn btn-sm btn-outline-warning watchlist-btn"
        data-work-id="{{ work.id }}"
        title="ウォッチリストに追加">
    <i class="bi bi-star"></i>
    <span class="btn-text">お気に入り</span>
</button>
```

### 6. 通知スクリプトをcronに登録

```bash
crontab -e
```

以下を追加（毎朝8時に実行）:

```cron
0 8 * * * cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system && python3 scripts/run_watchlist_notifications.py
```

## 使用方法

### ユーザー操作

1. **作品を追加**
   - 作品一覧で「お気に入り」ボタンをクリック
   - ボタンが黄色に変わり、星アイコンが塗りつぶされる

2. **ウォッチリスト表示**
   - ナビゲーションバーの「ウォッチリスト」をクリック
   - 登録した作品が一覧表示される

3. **通知設定**
   - ウォッチリストページでベルアイコンをクリック
   - エピソード通知/巻数通知を個別にON/OFF可能

4. **作品を削除**
   - ゴミ箱アイコンをクリックして削除

### 管理者操作

1. **手動で通知実行**
```bash
python3 scripts/run_watchlist_notifications.py
```

2. **ログ確認**
```bash
tail -f logs/watchlist_notifications_$(date +%Y%m%d).log
```

3. **統計確認**
```sql
sqlite3 db.sqlite3 "SELECT * FROM watchlist_stats;"
```

## API仕様

### POST /watchlist/api/add
作品をウォッチリストに追加

**リクエスト**:
```json
{
  "work_id": 123
}
```

**レスポンス**:
```json
{
  "success": true,
  "message": "「作品名」をウォッチリストに追加しました",
  "watchlist_id": 1,
  "work": {
    "id": 123,
    "title": "作品名"
  }
}
```

### DELETE /watchlist/api/remove/<work_id>
作品をウォッチリストから削除

**レスポンス**:
```json
{
  "success": true,
  "message": "「作品名」をウォッチリストから削除しました"
}
```

### PUT /watchlist/api/update/<work_id>
通知設定を更新

**リクエスト**:
```json
{
  "notify_new_episodes": true,
  "notify_new_volumes": false
}
```

**レスポンス**:
```json
{
  "success": true,
  "message": "通知設定を更新しました",
  "settings": {
    "notify_new_episodes": true,
    "notify_new_volumes": false
  }
}
```

### GET /watchlist/api/check/<work_id>
登録状態を確認

**レスポンス**:
```json
{
  "success": true,
  "in_watchlist": true,
  "notify_new_episodes": true,
  "notify_new_volumes": true
}
```

### GET /watchlist/api/stats
統計情報を取得

**レスポンス**:
```json
{
  "success": true,
  "stats": {
    "total": 10,
    "anime": 6,
    "manga": 4,
    "notify_episodes": 8,
    "notify_volumes": 7
  }
}
```

## 通知メール例

**件名**: 【ウォッチリスト】新エピソード3件 / 新刊2件 - MangaAnime Info

**本文**（HTML形式）:
- ユーザー名挨拶
- 統計サマリー
- 作品別の新規リリース情報
  - エピソード番号、配信日、プラットフォーム
  - 巻数、発売日、販売元
  - 視聴/購入リンク
- 公式サイトリンク
- ウォッチリスト管理リンク

## データベーススキーマ

### watchlistテーブル

| カラム名 | 型 | 説明 |
|---------|-----|------|
| id | INTEGER | 主キー |
| user_id | TEXT | ユーザーID |
| work_id | INTEGER | 作品ID |
| notify_new_episodes | INTEGER | エピソード通知（0/1） |
| notify_new_volumes | INTEGER | 巻数通知（0/1） |
| priority | INTEGER | 優先度（0-5） |
| notes | TEXT | メモ |
| created_at | DATETIME | 登録日時 |
| updated_at | DATETIME | 更新日時 |

### watchlist_statsビュー

| カラム名 | 型 | 説明 |
|---------|-----|------|
| user_id | TEXT | ユーザーID |
| total_watching | INTEGER | 総登録数 |
| anime_count | INTEGER | アニメ数 |
| manga_count | INTEGER | マンガ数 |
| notify_enabled_count | INTEGER | 通知有効数 |

## トラブルシューティング

### ウォッチリストボタンが表示されない
- `watchlist.js` が読み込まれているか確認
- ブラウザコンソールでエラーを確認
- ログインしているか確認

### 通知が届かない
- メーラー設定を確認（`modules/mailer.py`）
- ログファイルを確認
- メールアドレスが設定されているか確認
- メールアドレスが検証済みか確認

### マイグレーションエラー
- データベースファイルのパーミッションを確認
- バックアップから復元: `cp db.sqlite3.backup_* db.sqlite3`

## 今後の拡張案

1. **優先度機能の活用**
   - 優先度の高い作品を先に通知
   - 優先度別の表示フィルター

2. **メモ機能**
   - 作品ごとにメモを残せる機能

3. **一括操作**
   - 複数作品を一括で追加/削除
   - 通知設定の一括変更

4. **通知頻度設定**
   - 即時通知/日次/週次から選択

5. **プッシュ通知**
   - WebPush APIを使ったブラウザ通知

6. **カレンダー連携**
   - ウォッチリスト作品を自動でカレンダーに追加

7. **共有機能**
   - ウォッチリストを他のユーザーと共有

8. **レコメンデーション**
   - ウォッチリストに基づいたおすすめ作品

## 参考資料

- Flask Blueprint: https://flask.palletsprojects.com/en/2.3.x/blueprints/
- Bootstrap 5: https://getbootstrap.com/docs/5.3/
- SQLite: https://www.sqlite.org/docs.html
- Bootstrap Icons: https://icons.getbootstrap.com/

---

**実装者**: Fullstack Developer Agent
**レビュー**: Required
**テスト**: Comprehensive Test Suite Included
