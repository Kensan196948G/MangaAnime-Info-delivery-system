# クイックスタート: データ収集実行

最終更新: 2025-12-06

---

## 🚀 すぐに実行（推奨）

```bash
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system
bash scripts/execute_collection_task.sh
```

これだけで以下が自動実行されます:
- 環境確認
- データベースバックアップ
- データ収集
- 検証レポート生成

---

## 📋 実行前の確認（初回のみ）

### 1. 必要なパッケージのインストール

```bash
# Python3とSQLite3が必要
sudo apt-get update
sudo apt-get install -y python3 python3-pip sqlite3

# Pythonライブラリ（必要に応じて）
pip3 install requests feedparser
```

### 2. 設定ファイルの確認

```bash
# config.jsonが存在することを確認
cat config.json
```

---

## 📊 結果確認

### データ件数確認

```bash
# Makefileで確認（簡単）
make status

# または直接SQLiteで確認
sqlite3 db.sqlite3 "SELECT COUNT(*) as works FROM works;"
sqlite3 db.sqlite3 "SELECT COUNT(*) as releases FROM releases;"
```

### 詳細レポート確認

```bash
# 検証レポート表示
cat logs/data_collection_report.json | jq

# または検証スクリプト再実行
python3 scripts/verify_data_collection.py
```

### 最新データ確認

```bash
# 最新5件の作品
sqlite3 db.sqlite3 "SELECT id, title, type FROM works ORDER BY created_at DESC LIMIT 5;"

# 最新5件のリリース
sqlite3 db.sqlite3 "SELECT w.title, r.platform, r.release_date FROM releases r JOIN works w ON r.work_id = w.id ORDER BY r.created_at DESC LIMIT 5;"
```

---

## 🔄 定期実行設定（任意）

### cron設定

```bash
# crontab編集
crontab -e

# 毎日朝8時に自動実行
0 8 * * * cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system && bash scripts/execute_collection_task.sh >> logs/cron.log 2>&1
```

---

## 🛠️ トラブルシューティング

### エラーが発生した場合

```bash
# ログ確認
tail -f logs/data_collection_*.log

# データベース整合性チェック
sqlite3 db.sqlite3 "PRAGMA integrity_check;"

# バックアップからリストア
cp backups/db_backup_[最新のタイムスタンプ].sqlite3 db.sqlite3
```

---

## 📚 詳細ドキュメント

- **完全ガイド**: [docs/DATA_COLLECTION_GUIDE.md](docs/DATA_COLLECTION_GUIDE.md)
- **実行レポート**: [docs/TASK_EXECUTION_REPORT.md](docs/TASK_EXECUTION_REPORT.md)
- **システム仕様**: [CLAUDE.md](CLAUDE.md)

---

## ✅ 実行コマンド一覧

| コマンド | 説明 |
|---------|------|
| `make status` | 現在の状態確認 |
| `make collect` | データ収集のみ実行 |
| `make verify` | データ検証のみ実行 |
| `make full` | 収集→検証を一括実行 |
| `make backup-db` | データベースバックアップ |
| `bash scripts/execute_collection_task.sh` | 統合実行（推奨） |

---

**準備完了！上記のコマンドでデータ収集を開始してください。**
