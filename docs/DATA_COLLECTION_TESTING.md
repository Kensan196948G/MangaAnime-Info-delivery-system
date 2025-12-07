# データ収集機能 統合テストガイド

## 概要

このドキュメントでは、MangaAnime-Info-delivery-systemのデータ収集機能の統合テストについて説明します。

## テスト対象

### 1. AniList API 連携
- GraphQL APIからの今期アニメ取得
- レート制限対応（90リクエスト/分）
- エラーハンドリング

### 2. RSS収集
- マンガ出版社のRSSフィード収集
- パースエラー処理
- データ正規化

### 3. データベース操作
- 作品情報の登録
- リリース情報の登録
- 重複チェック

### 4. エラーハンドリング
- リトライロジック
- エラーログ記録
- 管理者通知

## テスト実行方法

### クイックスタート

```bash
# シェルスクリプトで実行
bash scripts/run_integration_test.sh

# または、直接Python実行
python3 scripts/test_data_collection.py
```

### 詳細モード

```bash
# ログレベルをDEBUGに設定
export LOG_LEVEL=DEBUG
python3 scripts/test_data_collection.py
```

## テスト項目詳細

### Test 1: AniList API接続テスト

**目的**: AniList GraphQL APIから今期アニメを取得できることを確認

**成功条件**:
- API接続成功
- 1件以上のアニメデータ取得
- データ構造が正しい（title, startDate等）

**期待出力**:
```
=== AniList API テスト ===
✅ AniListクライアント初期化成功
✅ 今期アニメ取得成功: 10作品

取得した作品（最初の5件）:
  1. Anime Title 1
     日本語: アニメタイトル1
     放送開始: 2025/1/15
     配信: 3プラットフォーム
```

### Test 2: AniListコレクターテスト

**目的**: データ収集から正規化までの一連の処理を確認

**成功条件**:
- Work オブジェクトへの変換成功
- リリース情報の抽出成功
- データの整合性確認

**期待出力**:
```
=== AniList コレクター テスト ===
✅ AniListコレクター初期化成功
✅ アニメデータ収集成功: 10作品

収集したデータ（最初の3件）:
  1. アニメタイトル
     タイプ: anime
     URL: https://anilist.co/anime/12345
     リリース情報: 5件
```

### Test 3: マンガRSS収集テスト

**目的**: RSS フィードからマンガ情報を収集できることを確認

**成功条件**:
- RSS パース成功
- 1件以上のマンガデータ取得
- リリース日の抽出成功

**期待出力**:
```
=== マンガRSS収集テスト ===
✅ RSSコレクター初期化成功
✅ RSS収集成功: 15作品

収集したデータ（最初の5件）:
  1. マンガタイトル 第10巻
     タイプ: manga
     URL: https://bookwalker.jp/...
     リリース: 2025-12-15 (BookWalker)
```

### Test 4: データベース操作テスト

**目的**: SQLiteデータベースへの登録・取得が正常に動作することを確認

**成功条件**:
- 作品登録成功
- リリース情報登録成功
- 未通知データ取得成功
- クリーンアップ成功

**期待出力**:
```
=== データベース操作テスト ===
✅ データベース接続成功
✅ 作品登録成功: ID=1
✅ リリース情報登録成功: ID=1
✅ 未通知リリース取得: 1件
✅ テストデータクリーンアップ完了
```

### Test 5: エラーハンドリングテスト

**目的**: 異常系の処理が適切に動作することを確認

**成功条件**:
- 無効なURL処理成功
- レート制限ハンドリング成功
- 例外の適切な処理

**期待出力**:
```
=== エラーハンドリングテスト ===
無効なRSS URLテスト...
✅ 無効なURLを適切に処理

AniList レート制限テスト...
  リクエスト 1: 成功
  リクエスト 2: 成功
  リクエスト 3: 成功
✅ レート制限ハンドリング確認完了
```

### Test 6: リトライロジックテスト

**目的**: 一時的な障害からの自動復旧を確認

**成功条件**:
- リトライ処理成功
- バックオフ動作確認
- 最終的な成功

**期待出力**:
```
=== リトライロジックテスト ===
✅ リトライハンドラー初期化成功
✅ リトライ成功: 2回目で成功, 結果=成功
```

## テスト結果サマリー

全テスト成功時の出力例:

```
============================================================
テスト結果サマリー
============================================================
✅ PASS - anilist_api
✅ PASS - anilist_collector
✅ PASS - manga_rss
✅ PASS - database
✅ PASS - error_handling
✅ PASS - retry_logic

------------------------------------------------------------
合計: 6テスト
成功: 6テスト (100.0%)
失敗: 0テスト
実行時間: 12.45秒
============================================================
```

## トラブルシューティング

### AniList API エラー

**症状**: "Rate limit exceeded"

**対処法**:
1. テスト実行間隔を空ける（1分以上）
2. per_page パラメータを減らす
3. リトライ待機時間を長くする

### RSS収集エラー

**症状**: "Connection timeout"

**対処法**:
1. ネットワーク接続を確認
2. RSS URLが有効か確認
3. タイムアウト時間を延長

### データベースエラー

**症状**: "database is locked"

**対処法**:
1. 他のプロセスがDBを使用していないか確認
2. db.sqlite3 のパーミッション確認
3. 一時ファイル（.db-journal）を削除

## 環境要件

### Python パッケージ

```bash
pip install -r requirements.txt
```

必須パッケージ:
- requests >= 2.31.0
- feedparser >= 6.0.10
- python-dateutil >= 2.8.2

### 設定ファイル

`config.json` に以下の設定が必要:

```json
{
  "anime": {
    "anilist": {
      "enabled": true,
      "per_page": 10
    }
  },
  "manga": {
    "rss_feeds": {
      "enabled": true,
      "sources": [...]
    }
  },
  "database": {
    "path": "db.sqlite3"
  }
}
```

## CI/CD統合

### GitHub Actions設定例

```yaml
name: Data Collection Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run integration tests
        run: |
          bash scripts/run_integration_test.sh
```

## 定期実行設定

### Cron設定例

```bash
# 毎日午前8時にテスト実行
0 8 * * * cd /path/to/project && bash scripts/run_integration_test.sh >> logs/test.log 2>&1
```

## 参考資料

- [AniList GraphQL API Documentation](https://anilist.gitbook.io/anilist-apiv2-docs/)
- [Python feedparser Documentation](https://feedparser.readthedocs.io/)
- [SQLite Python Tutorial](https://docs.python.org/3/library/sqlite3.html)

## 更新履歴

- 2025-12-07: 初版作成
- データ収集統合テストスイート実装

---

**作成者**: Backend Developer Agent
**最終更新**: 2025-12-07
