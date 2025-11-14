# システム要件・運用ガイド

## 📋 システム要件

### 最小システム要件
- **OS**: Ubuntu 18.04 LTS以上、CentOS 7以上、またはその他のLinux系OS
- **Python**: Python 3.8以上
- **メモリ**: 2GB以上 (推奨: 4GB以上)
- **CPU**: 1コア以上 (推奨: 2コア以上)
- **ストレージ**: 10GB以上の空き容量 (推奨: 20GB以上)
- **ネットワーク**: 安定したインターネット接続 (1Mbps以上)

### 推奨システム要件
- **OS**: Ubuntu 20.04 LTS / 22.04 LTS
- **Python**: Python 3.9以上
- **メモリ**: 8GB以上
- **CPU**: 4コア以上
- **ストレージ**: 50GB以上 SSD
- **ネットワーク**: 10Mbps以上の安定接続

## 🔧 事前セットアップ

### 1. システムパッケージ
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv sqlite3 curl wget cron

# CentOS/RHEL
sudo yum update
sudo yum install python3 python3-pip sqlite curl wget cronie
```

### 2. Python環境
```bash
# Python版本確認
python3 --version  # 3.8以上であること

# pip更新
python3 -m pip install --upgrade pip
```

### 3. プロジェクトディレクトリ準備
```bash
cd /path/to/MangaAnime-Info-delivery-system
chmod +x run_validation.sh
chmod +x scripts/*.py
chmod +x scripts/*.sh
```

## ⚡ 最終検証実行方法

### 1. 自動検証スクリプト実行 (推奨)
```bash
# 完全検証実行
./run_validation.sh --full

# 高速チェックのみ
./run_validation.sh --quick

# パフォーマンステストのみ
./run_validation.sh --performance
```

### 2. Makefile使用
```bash
# ヘルプ表示
make help

# 完全検証
make final-validation

# 高速確認
make quick-check

# 継続監視開始
make monitoring-start
```

### 3. 手動実行
```bash
# 前提条件セットアップ
make setup

# パフォーマンス検証
python3 scripts/performance_validation.py

# 統合テスト
python3 scripts/integration_test.py

# システム監視
python3 scripts/operational_monitoring.py

# 最終検証
python3 scripts/final_validation.py
```

## 📊 検証結果の解釈

### スコア基準
- **90-100点**: 優秀 - 本番運用準備完了
- **80-89点**: 良好 - 本番運用可能
- **70-79点**: 普通 - 軽微な改善推奨
- **60-69点**: 要改善 - 修正後に再評価
- **0-59点**: 不合格 - 重大な問題あり

### 検証項目別配点
- **前提条件** (25点): Python環境、パッケージ、ファイル構成
- **パフォーマンス** (25点): API応答時間、DB性能、リソース効率
- **統合テスト** (25点): 外部API連携、機能統合、エンドツーエンド
- **運用準備** (25点): 監視体制、自動化、ヘルスチェック

## 🚀 本番運用開始手順

### 1. 最終確認
```bash
# システム要件確認
./run_validation.sh --full

# スコア80点以上であることを確認
cat FINAL_VALIDATION_REPORT.txt
```

### 2. 設定ファイル準備
```bash
# 設定ファイル編集
vi config/config.json

# Google API認証設定
# - credentials.json配置
# - Gmail/Calendar API有効化
```

### 3. cron設定
```bash
# crontab編集
crontab -e

# 毎朝8時実行設定追加
0 8 * * * cd /path/to/project && python3 release_notifier.py
```

### 4. 継続監視開始
```bash
# 監視開始
make monitoring-start

# 監視状況確認
ps aux | grep operational_monitoring
```

## 📈 パフォーマンス最適化

### データベース最適化
```sql
-- インデックス作成
CREATE INDEX idx_releases_date ON releases(release_date);
CREATE INDEX idx_works_type ON works(type);

-- 統計情報更新
ANALYZE;
```

### システムリソース最適化
```bash
# メモリ使用量確認
free -h

# CPU使用率確認
top

# ディスク使用量確認
df -h
```

### ネットワーク最適化
```bash
# 接続速度テスト
curl -o /dev/null -s -w "%{time_total}\n" https://graphql.anilist.co

# DNS設定最適化 (Google DNS使用)
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
```

## 🔧 運用保守

### 日次作業
- [ ] システムヘルスチェック確認
- [ ] ログファイル確認
- [ ] 外部API接続状況確認
- [ ] データベースバックアップ

### 週次作業
- [ ] パフォーマンス監視レポート確認
- [ ] ログファイルローテーション
- [ ] システム更新確認

### 月次作業
- [ ] 依存パッケージ更新
- [ ] セキュリティ更新適用
- [ ] 災害復旧テスト
- [ ] 容量計画見直し

## 🚨 トラブルシューティング

### よくある問題と対処法

#### 1. Python依存関係エラー
```bash
# パッケージ再インストール
pip3 install -r requirements.txt --force-reinstall

# 仮想環境使用
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 2. データベース接続エラー
```bash
# データベースファイル権限確認
ls -la db.sqlite3
chmod 664 db.sqlite3

# データベース整合性確認
sqlite3 db.sqlite3 "PRAGMA integrity_check;"
```

#### 3. 外部API接続エラー
```bash
# 接続テスト
curl -X POST https://graphql.anilist.co \
  -H "Content-Type: application/json" \
  -d '{"query":"query{Viewer{id}}"}'

# DNS確認
nslookup graphql.anilist.co
```

#### 4. Gmail API認証エラー
- credentials.jsonファイルの確認
- Google Cloud Platform設定確認
- APIクォータ制限確認
- OAuth2認証フロー再実行

## 📞 サポート・連絡先

### ログファイル確認場所
- システムログ: `/logs/`
- パフォーマンスログ: `/logs/performance_validation.log`
- 監視ログ: `/logs/operational_monitoring.log`
- 統合テストログ: `/logs/integration_test.log`

### デバッグ情報収集
```bash
# デバッグ情報収集
make debug

# システム情報取得
make system-info

# ログ確認
make logs
```

### 緊急時対応
1. システム停止: `make monitoring-stop`
2. バックアップ確認: `make backup`
3. ログ収集: `make logs`
4. 設定復旧: `git checkout config/`

## 📚 参考資料

- [AniList GraphQL API ドキュメント](https://anilist.gitbook.io/anilist-apiv2-docs/)
- [Google Calendar API ガイド](https://developers.google.com/calendar/api/guides/overview)
- [Gmail API ドキュメント](https://developers.google.com/gmail/api/guides)
- [SQLite 最適化ガイド](https://sqlite.org/optoverview.html)
- [Python 3.8+ 新機能](https://docs.python.org/3/whatsnew/)

---

💡 **重要**: 本番運用前に必ず最終検証を実行し、スコア80点以上を確認してください。