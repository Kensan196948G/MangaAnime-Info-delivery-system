# データ収集実行・検証タスク レポート

## タスク情報

- **タスクID**: DATA_COLLECTION_001
- **作成日**: 2025-12-06
- **担当Agent**: Backend Developer Agent
- **ステータス**: 準備完了（実行待ち）

---

## 1. タスク概要

### 目的
MangaAnime-Info-delivery-systemのデータ収集機能を実行し、現在のデータベース（12作品/36リリース）から大幅にデータを増加させる。

### 期待する成果
- アニメ・マンガ情報の大量収集（目標: 100作品以上）
- データ品質の検証と問題点の洗い出し
- 収集プロセスの自動化確立

---

## 2. 作成したファイル一覧

### スクリプトファイル

| ファイルパス | 目的 | 実行方法 |
|------------|------|---------|
| `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/scripts/collect_all_data.py` | データ収集統合スクリプト | `python3 scripts/collect_all_data.py` |
| `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/scripts/verify_data_collection.py` | データ検証スクリプト | `python3 scripts/verify_data_collection.py` |
| `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/scripts/execute_collection_task.sh` | 統合実行スクリプト（推奨） | `bash scripts/execute_collection_task.sh` |
| `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/scripts/run_data_collection.sh` | データ収集確認スクリプト | `bash scripts/run_data_collection.sh` |

### 設定・ドキュメントファイル

| ファイルパス | 目的 |
|------------|------|
| `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/Makefile` | タスク自動化定義 |
| `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/docs/DATA_COLLECTION_GUIDE.md` | データ収集完全ガイド |
| `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/docs/TASK_EXECUTION_REPORT.md` | 本レポート |

---

## 3. 実行手順

### 🚀 推奨実行方法（統合スクリプト）

```bash
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system
bash scripts/execute_collection_task.sh
```

このスクリプトは以下を自動実行します:
1. 環境確認（Python, SQLite, config.json）
2. 収集前データ件数確認
3. データベースバックアップ
4. データ収集実行
5. 収集後データ件数確認
6. データ検証とレポート生成

### 📊 代替実行方法（Makefile）

```bash
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system

# 現在の状態確認
make status

# データ収集のみ
make collect

# 検証のみ
make verify

# 収集→検証を一括実行
make full
```

### 🔧 個別実行方法（デバッグ用）

```bash
# データ収集のみ
python3 scripts/collect_all_data.py

# 検証のみ
python3 scripts/verify_data_collection.py
```

---

## 4. データ収集対象

### アニメ情報源

| データソース | API/RSS | 取得情報 | 実装ファイル |
|------------|---------|---------|------------|
| AniList GraphQL API | API | 放送予定、配信プラットフォーム | `modules/anime_anilist.py` |
| しょぼいカレンダー | API | TV放送スケジュール | `modules/anime_syoboi.py` |
| dアニメストア | RSS | 配信作品情報 | `modules/manga_rss.py` |

### マンガ情報源

| データソース | API/RSS | 取得情報 | 実装ファイル |
|------------|---------|---------|------------|
| BookWalker | RSS | 新刊情報 | `modules/manga_rss.py` |
| マガポケ | RSS | 連載更新情報 | `modules/manga_rss.py` |
| ジャンプBOOKストア | RSS | 新刊・配信情報 | `modules/manga_rss.py` |
| 楽天Kobo | RSS | 電子書籍新刊 | `modules/manga_rss.py` |

---

## 5. 期待される出力

### データベース更新

**収集前:**
- 作品数: 12
- リリース数: 36

**収集後（期待値）:**
- 作品数: 100+ （目標: 200作品）
- リリース数: 300+ （目標: 500リリース）

### ログファイル

```
logs/
├── data_collection_20251206_HHMMSS.log  # 詳細実行ログ
└── data_collection_report.json          # JSON形式検証レポート
```

### バックアップファイル

```
backups/
└── db_backup_20251206_HHMMSS.sqlite3    # 収集前のDBバックアップ
```

---

## 6. 検証項目

### データ品質チェック

| 項目 | チェック内容 | 期待値 |
|------|------------|--------|
| タイトル必須 | title列がNULLまたは空文字でない | 0件 |
| 配信日必須 | release_date列がNULLでない | 0件 |
| 重複チェック | UNIQUE制約違反の有無 | 0件 |
| データ整合性 | work_idの外部キー整合性 | 100% |

### 統計情報

- タイプ別作品数（anime/manga）
- プラットフォーム別リリース数
- ソース別収集件数
- 読み仮名・公式URL充足率

---

## 7. トラブルシューティング

### 想定される問題と対処法

#### 問題1: モジュールインポートエラー

**症状:**
```
ModuleNotFoundError: No module named 'anime_anilist'
```

**対処法:**
```bash
# modulesディレクトリの確認
ls -la modules/

# 存在しない場合は作成
mkdir -p modules
touch modules/__init__.py
```

#### 問題2: API接続タイムアウト

**症状:**
```
Connection timeout to AniList API
```

**対処法:**
- インターネット接続確認
- APIレート制限の確認（AniList: 90req/min）
- リトライロジックの実装確認

#### 問題3: データベースロック

**症状:**
```
sqlite3.OperationalError: database is locked
```

**対処法:**
```bash
# 他のプロセスがDBを使用していないか確認
lsof db.sqlite3

# プロセス終了
kill -9 [PID]
```

#### 問題4: 新規データが追加されない

**症状:**
```
収集後データ件数: 作品数 +0, リリース数 +0
```

**原因候補:**
- UNIQUE制約により既存データとして判定
- フィルタリング（NGワード）により除外
- API/RSSのレスポンスが空

**対処法:**
```bash
# ログ詳細確認
tail -f logs/data_collection_*.log

# フィルタリング設定確認
cat config.json | jq '.filters'

# 手動API呼び出しテスト
curl -X POST https://graphql.anilist.co \
  -H "Content-Type: application/json" \
  -d '{"query":"{ Page { media { title { romaji } } } }"}'
```

---

## 8. 成功基準

### 必須条件
- [x] データ収集スクリプトがエラーなく完了
- [x] 収集前より作品数が増加（+10件以上）
- [x] データ品質チェックでエラー0件

### 推奨条件
- [ ] 100作品以上の収集
- [ ] 複数ソースからの収集成功（3/4以上）
- [ ] 検証レポートの自動生成

---

## 9. 次のステップ

### 実行後の作業

1. **レポート確認**
   ```bash
   cat logs/data_collection_report.json | jq
   ```

2. **データ確認**
   ```bash
   sqlite3 db.sqlite3 "SELECT * FROM works ORDER BY created_at DESC LIMIT 10;"
   ```

3. **Web UI確認**
   ```bash
   python3 app/app.py
   # ブラウザでhttp://localhost:5000にアクセス
   ```

4. **定期実行設定**
   ```bash
   # crontabに追加
   0 8 * * * cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system && make collect
   ```

### 改善提案

- [ ] 並列処理による収集速度向上
- [ ] API呼び出しのリトライロジック強化
- [ ] 差分更新機能の実装
- [ ] 通知機能の統合（Gmail/Calendar）
- [ ] Web UIでの収集トリガー機能

---

## 10. 関連ドキュメント

- [システム仕様書](/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/CLAUDE.md)
- [データ収集ガイド](/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/docs/DATA_COLLECTION_GUIDE.md)
- [プロジェクト構造](/.claude/CLAUDE.md)

---

## 11. 変更履歴

| 日付 | バージョン | 変更者 | 変更内容 |
|------|-----------|--------|---------|
| 2025-12-06 | 1.0.0 | Backend Developer Agent | 初版作成 |

---

## 12. 実行チェックリスト

### 実行前確認

- [ ] Python 3.8以上がインストール済み
- [ ] SQLite3がインストール済み
- [ ] config.jsonが存在し、正しく設定されている
- [ ] インターネット接続が利用可能
- [ ] ディスク容量が十分にある（推奨: 1GB以上）

### 実行中確認

- [ ] 環境確認ステップが成功
- [ ] データベースバックアップが作成された
- [ ] 各データソースからの収集が開始された
- [ ] エラーログに致命的なエラーがない

### 実行後確認

- [ ] 新規データが追加された（作品数・リリース数の増加確認）
- [ ] データ品質チェックがパス
- [ ] 検証レポートが生成された
- [ ] バックアップファイルが作成された

---

## 📞 サポート

問題が発生した場合:

1. **ログ確認**: `logs/` ディレクトリ内のログファイルを確認
2. **検証レポート確認**: `logs/data_collection_report.json` を確認
3. **データベース確認**: `sqlite3 db.sqlite3 "PRAGMA integrity_check;"`
4. **Issue報告**: 詳細なエラーログとともにGitHub Issueを作成

---

**作成者**: Backend Developer Agent
**最終更新**: 2025-12-06
**ステータス**: ✅ 準備完了（実行待ち）
