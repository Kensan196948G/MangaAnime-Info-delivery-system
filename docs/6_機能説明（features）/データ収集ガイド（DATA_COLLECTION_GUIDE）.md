# データ収集実行ガイド

## 概要

このガイドでは、MangaAnime-Info-delivery-systemのデータ収集機能を実行し、アニメ・マンガ情報をデータベースに取り込む手順を説明します。

作成日: 2025-12-06

---

## 📋 前提条件

### 必須要件
- Python 3.8以上
- SQLite3
- インターネット接続

### 必要な認証情報
- Google API認証（Gmail/Calendar用）※任意
- AniList API アクセス（無料、認証不要）

---

## 🚀 クイックスタート

### 方法1: Makefileを使用（推奨）

```bash
# プロジェクトディレクトリに移動
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system

# 現在の状態確認
make status

# データ収集実行
make collect

# データ検証
make verify

# または一括実行
make full
```

### 方法2: 個別スクリプト実行

```bash
# データ収集
python3 scripts/collect_all_data.py

# 検証
python3 scripts/verify_data_collection.py
```

---

## 📊 収集対象データソース

| データソース | タイプ | 情報内容 | 実装状況 |
|---------|------|---------|---------|
| AniList API | アニメ | 放送予定、配信情報 | ✓ |
| しょぼいカレンダー | アニメ | TV放送スケジュール | ✓ |
| 各種RSS | マンガ | 新刊情報、配信情報 | ✓ |
| 配信プラットフォーム | 両方 | Netflix, Prime等 | △ |

---

## 🔧 詳細手順

### ステップ1: 初期セットアップ

```bash
# セットアップスクリプト実行
make setup

# または
bash scripts/setup.sh
```

このスクリプトは以下を実行します:
- 必要なディレクトリ作成（logs, backups等）
- データベース初期化（既存の場合はスキップ）
- 設定ファイル確認

### ステップ2: 設定ファイル確認

`config.json` の内容を確認します:

```json
{
  "data_sources": {
    "anilist": {
      "enabled": true,
      "api_url": "https://graphql.anilist.co"
    },
    "syoboi": {
      "enabled": true,
      "api_url": "https://cal.syoboi.jp/json.php"
    },
    "rss_feeds": {
      "enabled": true,
      "sources": [
        "https://anime.dmkt-sp.jp/animestore/CF/rss/",
        "..."
      ]
    }
  },
  "filters": {
    "ng_keywords": ["R18", "成人向け", "BL", "百合"],
    "genres": {
      "exclude": []
    }
  }
}
```

### ステップ3: データ収集実行

```bash
# 全データソースから収集
make collect

# 実行ログ確認
tail -f logs/data_collection_*.log
```

### ステップ4: 収集結果確認

```bash
# 検証スクリプト実行
make verify
```

検証レポートには以下が含まれます:
- 総作品数・リリース数
- タイプ別統計（アニメ/マンガ）
- プラットフォーム別統計
- データ品質チェック結果
- 最近追加されたデータ一覧

---

## 📁 出力ファイル

### ログファイル
```
logs/
├── data_collection_20251206_120000.log  # 収集ログ
└── data_collection_report.json          # 検証レポート（JSON）
```

### データベース
```
db.sqlite3  # メインデータベース
```

---

## 🔍 トラブルシューティング

### 問題1: モジュールが見つからない

**エラー:**
```
ModuleNotFoundError: No module named 'anime_anilist'
```

**解決策:**
```bash
# modulesディレクトリの存在確認
ls -la modules/

# sys.pathの確認
python3 -c "import sys; print('\n'.join(sys.path))"
```

### 問題2: API接続エラー

**エラー:**
```
Connection error: timeout
```

**解決策:**
- インターネット接続確認
- APIエンドポイント確認
- レート制限の確認（AniListは90req/min）

### 問題3: データベースロックエラー

**エラー:**
```
sqlite3.OperationalError: database is locked
```

**解決策:**
```bash
# 他のプロセスがDBを使用していないか確認
lsof db.sqlite3

# データベース整合性チェック
sqlite3 db.sqlite3 "PRAGMA integrity_check;"
```

---

## 📈 パフォーマンス最適化

### 収集速度の向上

1. **並列実行**（将来実装予定）
   ```python
   # concurrent.futuresを使用した並列化
   ```

2. **キャッシング**
   - 既に収集済みのデータをスキップ
   - UNIQUE制約で重複防止

3. **バッチ処理**
   - 複数件をまとめてINSERT

### データベース最適化

```sql
-- インデックス作成
CREATE INDEX idx_works_title ON works(title);
CREATE INDEX idx_releases_date ON releases(release_date);
CREATE INDEX idx_releases_platform ON releases(platform);

-- VACUUM実行（定期メンテナンス）
VACUUM;
```

---

## 🔄 定期実行設定

### cronで自動実行

```bash
# crontab編集
crontab -e

# 毎日朝8時に実行
0 8 * * * cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system && make collect >> logs/cron.log 2>&1
```

### systemdタイマーで実行

```ini
# /etc/systemd/system/manga-anime-collector.timer
[Unit]
Description=MangaAnime Data Collection Timer

[Timer]
OnCalendar=daily
OnCalendar=08:00
Persistent=true

[Install]
WantedBy=timers.target
```

---

## 📊 収集データの活用

### データエクスポート

```bash
# CSV出力
sqlite3 db.sqlite3 -header -csv "SELECT * FROM works;" > works.csv
sqlite3 db.sqlite3 -header -csv "SELECT * FROM releases;" > releases.csv

# JSON出力
sqlite3 db.sqlite3 "SELECT json_group_array(json_object('id', id, 'title', title)) FROM works;" > works.json
```

### API経由でのアクセス

```python
# Flask APIエンドポイント例
@app.route('/api/works')
def get_works():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM works LIMIT 100")
    works = cursor.fetchall()
    return jsonify(works)
```

---

## 🧪 テスト実行

```bash
# 単体テスト
make test

# 統合テスト
python3 -m pytest tests/integration/

# カバレッジ計測
python3 -m pytest --cov=modules tests/
```

---

## 📚 関連ドキュメント

- [システム仕様書](../CLAUDE.md)
- [API設計書](./API_DESIGN.md)
- [データベーススキーマ](./DATABASE_SCHEMA.md)
- [トラブルシューティング](./TROUBLESHOOTING.md)

---

## 📝 変更履歴

| 日付 | バージョン | 変更内容 |
|------|-----------|---------|
| 2025-12-06 | 1.0.0 | 初版作成 |

---

**作成者**: Backend Developer Agent
**最終更新**: 2025-12-06
