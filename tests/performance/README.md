# パフォーマンステストガイド

## 概要

Locustを使用した負荷テストとパフォーマンステストの実行方法を説明します。

## セットアップ

### 1. 依存関係のインストール

```bash
pip install locust
```

### 2. テストファイルの確認

```bash
ls tests/performance/locustfile.py
```

## テスト実行方法

### 基本的な実行

```bash
# Web UIモード（推奨）
locust -f tests/performance/locustfile.py --host=http://localhost:5000

# ブラウザで http://localhost:8089 にアクセス
```

### コマンドラインモード

```bash
# ユーザー数とスポーンレートを指定
locust -f tests/performance/locustfile.py \
  --host=http://localhost:5000 \
  --users=100 \
  --spawn-rate=10 \
  --run-time=5m \
  --headless

# CSV出力
locust -f tests/performance/locustfile.py \
  --host=http://localhost:5000 \
  --users=100 \
  --spawn-rate=10 \
  --run-time=5m \
  --headless \
  --csv=results/load_test
```

## テストシナリオ

### 1. AnimeUserBehavior（一般ユーザー）

通常のユーザー行動をシミュレート

- ホームページ閲覧
- 作品一覧表示
- リリース情報確認
- 検索実行

```bash
locust -f tests/performance/locustfile.py AnimeUserBehavior \
  --host=http://localhost:5000
```

### 2. PowerUserBehavior（パワーユーザー）

高頻度利用者の行動をシミュレート

- 高速なページ遷移
- 連続検索
- 複雑なフィルタリング

```bash
locust -f tests/performance/locustfile.py PowerUserBehavior \
  --host=http://localhost:5000
```

### 3. AdminUserBehavior（管理者）

管理者操作をシミュレート

- 作品作成
- リリース作成
- ダッシュボード閲覧

```bash
locust -f tests/performance/locustfile.py AdminUserBehavior \
  --host=http://localhost:5000
```

### 4. StressTestUser（ストレステスト）

システムの限界を測定

```bash
locust -f tests/performance/locustfile.py StressTestUser \
  --host=http://localhost:5000 \
  --users=500 \
  --spawn-rate=50
```

### 5. CustomLoadTest（ユーザージャーニー）

実際のユーザー行動をトレース

```bash
locust -f tests/performance/locustfile.py CustomLoadTest \
  --host=http://localhost:5000
```

## テストタグの使用

特定の機能のみテスト

```bash
# ホームページのみ
locust -f tests/performance/locustfile.py --tags homepage

# 作品関連のみ
locust -f tests/performance/locustfile.py --tags works

# API関連のみ
locust -f tests/performance/locustfile.py --tags intensive

# 複数タグ
locust -f tests/performance/locustfile.py --tags works --tags releases
```

## パフォーマンス目標

### 応答時間

| エンドポイント           | 目標レスポンスタイム | 許容レスポンスタイム |
| ------------------- | ----------- | ----------- |
| /api/health         | < 50ms      | < 100ms     |
| /api/works          | < 200ms     | < 500ms     |
| /api/releases       | < 200ms     | < 500ms     |
| /api/works/:id      | < 150ms     | < 300ms     |
| /api/search         | < 300ms     | < 1000ms    |
| /api/calendar/events | < 250ms     | < 600ms     |

### スループット

- 最小: 100 req/sec
- 目標: 500 req/sec
- 最大: 1000 req/sec

### 同時接続数

- 通常: 100 concurrent users
- ピーク: 500 concurrent users
- ストレス: 1000 concurrent users

## 結果の解析

### Web UIで確認

1. ブラウザで `http://localhost:8089` にアクセス
2. ダッシュボードで以下を確認:
   - Requests per second (RPS)
   - Response time percentiles
   - Failure rate

### CSVファイルで確認

```bash
# 統計情報
cat results/load_test_stats.csv

# 詳細ログ
cat results/load_test_stats_history.csv

# 失敗したリクエスト
cat results/load_test_failures.csv
```

### レポート生成

```bash
# HTML レポート生成（カスタムスクリプト）
python scripts/generate_perf_report.py results/load_test_stats.csv
```

## CI/CD統合

GitHub Actionsでの自動実行

```yaml
# .github/workflows/performance-tests.yml
- name: Run performance tests
  run: |
    locust -f tests/performance/locustfile.py \
      --host=http://localhost:5000 \
      --users=100 \
      --spawn-rate=10 \
      --run-time=2m \
      --headless \
      --csv=results/ci_load_test
```

## ベストプラクティス

### 1. 段階的な負荷増加

```bash
# 初回: 少ないユーザー数でテスト
locust --users=10 --spawn-rate=1 --run-time=1m

# 次に: 徐々に増やす
locust --users=50 --spawn-rate=5 --run-time=3m

# 最後: 目標負荷でテスト
locust --users=100 --spawn-rate=10 --run-time=5m
```

### 2. タグを活用した部分テスト

```bash
# まず軽い操作のみテスト
locust --tags homepage --tags search

# 問題なければ全機能テスト
locust
```

### 3. 定期的な実行

```bash
# cron設定例
0 3 * * * cd /path/to/project && locust -f tests/performance/locustfile.py --headless --users=100 --run-time=10m --csv=results/daily_$(date +\%Y\%m\%d)
```

## トラブルシューティング

### Connection Errors

```bash
# サーバーが起動しているか確認
curl http://localhost:5000/api/health

# ファイアウォール設定確認
sudo ufw status
```

### High Failure Rate

- データベース接続数の確認
- アプリケーションログの確認
- システムリソース（CPU/メモリ）の確認

### Slow Response Times

- データベースクエリの最適化
- キャッシュの活用
- インデックスの追加

## 参考資料

- [Locust公式ドキュメント](https://docs.locust.io/)
- [パフォーマンステストのベストプラクティス](https://martinfowler.com/articles/performance-testing.html)
