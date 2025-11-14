# データ更新API 検証クイックリファレンス

---

## 検証実行方法

### 包括的テスト（推奨）
```bash
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system
python3 tests/test_refresh_data_validation.py
```

### エラーシナリオテスト
```bash
python3 tests/test_error_scenarios.py
```

### CORSパッチ情報表示
```bash
python3 tests/cors_fix_patch.py
```

---

## 手動テスト（curl）

### 基本的なテスト
```bash
curl http://localhost:3030/api/refresh-data
```

### 詳細情報付き
```bash
curl -v http://localhost:3030/api/refresh-data
```

### ヘッダー情報のみ
```bash
curl -I http://localhost:3030/api/refresh-data
```

### JSON整形表示（jq必要）
```bash
curl -s http://localhost:3030/api/refresh-data | jq .
```

### タイミング測定
```bash
time curl -s http://localhost:3030/api/refresh-data
```

---

## データベース確認

### 作品数確認
```bash
sqlite3 /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/app/db.sqlite3 \
  "SELECT COUNT(*) FROM works;"
```

### リリース数確認
```bash
sqlite3 /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/app/db.sqlite3 \
  "SELECT COUNT(*) FROM releases;"
```

### 最新10件表示
```bash
sqlite3 -header -column /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/app/db.sqlite3 \
  "SELECT w.title, r.release_type, r.number, r.platform, r.release_date
   FROM releases r
   JOIN works w ON r.work_id = w.id
   ORDER BY r.release_date DESC
   LIMIT 10;"
```

---

## エラー再現

### スクリプトファイル不在エラー
```bash
# バックアップ
mv insert_sample_data.py insert_sample_data.py.bak

# テスト
curl http://localhost:3030/api/refresh-data

# 復元
mv insert_sample_data.py.bak insert_sample_data.py
```

### タイムアウトエラー（疑似）
```python
# insert_sample_data.py の先頭に追加
import time
time.sleep(35)
```

---

## サーバーログ確認

### リアルタイムログ監視
```bash
tail -f /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/app/logs/*.log
```

### エラーログのみ
```bash
grep -i error /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/app/logs/*.log
```

---

## パフォーマンステスト

### 連続10回実行
```bash
for i in {1..10}; do
  echo "リクエスト $i"
  time curl -s http://localhost:3030/api/refresh-data | jq -r '.success'
  sleep 1
done
```

### 同時5リクエスト
```bash
for i in {1..5}; do
  curl -s http://localhost:3030/api/refresh-data &
done
wait
```

---

## トラブルシューティング

### サーバーが起動しているか確認
```bash
ps aux | grep "start_web_ui.py"
netstat -tlnp | grep 3030
```

### サーバーログ確認
```bash
ls -la /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/app/logs/
```

### データベース接続確認
```bash
sqlite3 /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/app/db.sqlite3 ".tables"
```

### ポート使用状況
```bash
lsof -i :3030
```

---

## 期待される結果

### 正常系
```json
{
  "message": "データ更新が完了しました",
  "output": "",
  "success": true,
  "timestamp": "2025-11-14T22:04:57.030503"
}
```

### エラー: スクリプト不在
```json
{
  "success": false,
  "error": "データ投入スクリプトが見つかりません"
}
```
**HTTPステータス**: 404

### エラー: スクリプト実行失敗
```json
{
  "success": false,
  "error": "データ更新中にエラーが発生しました",
  "details": "..."
}
```
**HTTPステータス**: 500

### エラー: タイムアウト
```json
{
  "success": false,
  "error": "データ更新がタイムアウトしました"
}
```
**HTTPステータス**: 500

---

## よく使うコマンド

### サーバー起動
```bash
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system
python3 app/start_web_ui.py --port 3030
```

### サーバー停止
```bash
pkill -f start_web_ui.py
```

### データベースリセット
```bash
python3 insert_sample_data.py
```

### ログクリア
```bash
rm -f app/logs/*.log
```

---

## レポート参照

- **詳細レポート**: `/tests/DATA_UPDATE_API_VALIDATION_REPORT.md`
- **サマリー**: `/tests/VALIDATION_SUMMARY.md`

---

## 連絡先

問題が発生した場合は、以下のファイルを確認してください:
- `/tests/DATA_UPDATE_API_VALIDATION_REPORT.md` - 詳細な検証結果
- `/tests/test_refresh_data_validation.py` - テストスクリプト
- `/app/web_app.py` - API実装コード

---

**最終更新**: 2025-11-14
**作成者**: QA Agent
