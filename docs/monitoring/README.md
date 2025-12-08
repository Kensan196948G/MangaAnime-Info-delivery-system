# 監視システムドキュメント

## 概要

MangaAnime-Info-delivery-systemの監視・可観測性システムは、以下のコンポーネントで構成されています:

- **Prometheus**: メトリクス収集とアラート評価
- **Grafana**: 可視化ダッシュボード
- **Alertmanager**: アラート管理とルーティング
- **Jaeger**: 分散トレーシング
- **Node Exporter**: システムメトリクス収集
- **cAdvisor**: コンテナメトリクス収集

## セットアップ

### 1. 監視スタック起動

```bash
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system
docker-compose -f docker-compose-monitoring.yml up -d
```

### 2. アクセスURL

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin123)
- **Alertmanager**: http://localhost:9093
- **Jaeger UI**: http://localhost:16686
- **Node Exporter**: http://localhost:9100/metrics
- **cAdvisor**: http://localhost:8080

### 3. 環境変数設定

Slack/Discord Webhook URLを設定:

```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/YOUR/WEBHOOK/URL"
```

設定ファイル更新:

```bash
# config/alertmanager/config.yml を編集
sed -i "s|YOUR_SLACK_WEBHOOK_URL|$SLACK_WEBHOOK_URL|g" config/alertmanager/config.yml
sed -i "s|YOUR_DISCORD_WEBHOOK_URL|$DISCORD_WEBHOOK_URL|g" config/alertmanager/config.yml
```

## アーキテクチャ

```
┌─────────────────────────────────────────────────────────────┐
│                    MangaAnime Application                    │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  Flask App  │  │  metrics.py  │  │  tracing.py  │       │
│  │  /metrics   │──│  Prometheus  │  │  OpenTelemetry│      │
│  └─────────────┘  │  Client      │  └──────────────┘       │
│                   └──────────────┘          │               │
└────────────────────────────────────────────│───────────────┘
                                              │
                     ┌────────────────────────┼──────────────┐
                     │                        │              │
              ┌──────▼──────┐        ┌───────▼──────┐       │
              │  Prometheus │        │    Jaeger    │       │
              │   :9090     │        │   :16686     │       │
              └──────┬──────┘        └──────────────┘       │
                     │                                       │
         ┌───────────┼───────────┐                          │
         │           │           │                          │
  ┌──────▼──────┐ ┌─▼──────┐ ┌──▼──────────┐               │
  │   Grafana   │ │ Alert  │ │ Node/cAdv   │               │
  │   :3000     │ │ Manager│ │ Exporters   │               │
  └─────────────┘ │ :9093  │ └─────────────┘               │
                  └────┬───┘                                │
                       │                                    │
                  ┌────▼────┐                               │
                  │  Slack  │                               │
                  │ Discord │                               │
                  └─────────┘                               │
```

## メトリクス

### アプリケーションメトリクス

#### HTTPリクエスト
- `http_requests_total`: リクエスト総数
- `http_request_duration_seconds`: レイテンシヒストグラム
- `http_request_errors_total`: エラー総数

#### データベース
- `db_operations_total`: DB操作総数
- `db_operation_duration_seconds`: DB操作レイテンシ

#### API取得
- `api_fetch_total`: API取得総数
- `api_fetch_duration_seconds`: API取得レイテンシ

#### 通知
- `notifications_sent_total`: 通知送信総数
- `calendar_sync_total`: カレンダー同期総数
- `calendar_events_created`: カレンダーイベント作成数

#### 作品数
- `anime_works_total`: アニメ作品総数
- `manga_works_total`: マンガ作品総数
- `releases_pending`: 未通知リリース数

#### システムリソース
- `system_cpu_usage_percent`: CPU使用率
- `system_memory_usage_bytes`: メモリ使用量
- `system_disk_usage_percent`: ディスク使用率

### Prometheusクエリ例

```promql
# リクエストレート (req/sec)
rate(http_requests_total[5m])

# p95レイテンシ
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# エラー率
rate(http_request_errors_total[5m]) / rate(http_requests_total[5m])

# 成功率
(1 - (rate(api_fetch_total{status="error"}[5m]) / rate(api_fetch_total[5m]))) * 100
```

## アラート

### アラートレベル

- **Critical**: 即座に対応が必要（5分間隔で通知）
- **Warning**: 監視が必要（1時間間隔で通知）

### 主要アラート

#### システムリソース
- `HighCPUUsage`: CPU使用率 > 80%
- `CriticalCPUUsage`: CPU使用率 > 95%
- `HighMemoryUsage`: メモリ使用量 > 7GB
- `CriticalMemoryUsage`: メモリ使用量 > 14GB
- `HighDiskUsage`: ディスク使用率 > 85%
- `CriticalDiskUsage`: ディスク使用率 > 95%

#### アプリケーション
- `HighErrorRate`: エラー率 > 0.05 errors/sec
- `CriticalErrorRate`: エラー率 > 0.1 errors/sec
- `HighLatency`: p95レイテンシ > 1秒
- `CriticalLatency`: p95レイテンシ > 5秒

#### データベース
- `HighDatabaseLatency`: p95 DB操作 > 0.5秒
- `DatabaseErrorRate`: DBエラー率 > 0.01 errors/sec

#### API取得
- `APIFetchFailure`: API取得失敗率 > 0.1 failures/sec
- `SlowAPIFetch`: p95取得時間 > 30秒
- `NoAPIFetchActivity`: 1時間APIアクティビティなし

#### 通知・カレンダー
- `NotificationFailure`: 通知失敗率 > 0.01 failures/sec
- `CalendarSyncFailure`: カレンダー同期失敗率 > 0.01 failures/sec
- `NoNotificationActivity`: 6時間通知アクティビティなし

### アラート通知先

- **Critical**: `#critical-alerts` (Slack) + Discord Webhook
- **Warning**: `#warnings` (Slack)
- **Infrastructure**: `#infra-alerts` (Slack)
- **Application**: `#app-alerts` (Slack)
- **Database**: `#db-alerts` (Slack)

## 分散トレーシング

### Jaeger統合

アプリケーションコードに以下を追加:

```python
from modules.tracing import init_tracing, trace_function, trace_span

# アプリケーション初期化時
init_tracing(
    service_name="mangaanime-info-delivery",
    jaeger_host="localhost",
    jaeger_port=6831
)

# 関数トレーシング
@trace_function(attributes={"component": "anime_fetcher"})
def fetch_anime_data():
    # 処理
    pass

# 手動スパン作成
with trace_span("custom_operation", {"key": "value"}):
    # 処理
    pass
```

### トレース確認

Jaeger UI: http://localhost:16686

1. サービス選択: `mangaanime-info-delivery`
2. 操作選択: 確認したい操作
3. 時間範囲選択
4. "Find Traces"クリック

## ダッシュボード

### メインダッシュボード

Grafana: http://localhost:3000/d/mangaanime-main

パネル構成:

1. **HTTP Request Rate**: リクエストレート推移
2. **API Response Time (p95)**: レイテンシゲージ
3. **System CPU Usage**: CPU使用率推移
4. **System Memory Usage**: メモリ使用量推移
5. **System Disk Usage**: ディスク使用率推移
6. **Database Operations Rate**: DB操作レート
7. **Database Operation Duration (p95)**: DB操作レイテンシ
8. **Total Anime Works**: アニメ作品総数
9. **Total Manga Works**: マンガ作品総数
10. **Pending Releases**: 未通知リリース数
11. **Notification Rate**: 通知レート
12. **API Fetch Rate**: API取得レート
13. **API Fetch Duration (p95)**: API取得レイテンシ
14. **Error Rate**: エラー率推移

### カスタムダッシュボード作成

1. Grafana UIにアクセス
2. "+" → "Dashboard"
3. "Add new panel"
4. Prometheusクエリ入力
5. 可視化設定
6. 保存

## トラブルシューティング

### メトリクスが表示されない

1. アプリケーションの /metrics エンドポイント確認:
   ```bash
   curl http://localhost:5000/metrics
   ```

2. Prometheusターゲット確認:
   http://localhost:9090/targets

3. Prometheusログ確認:
   ```bash
   docker logs mangaanime-prometheus
   ```

### アラートが発火しない

1. Prometheusアラート確認:
   http://localhost:9090/alerts

2. Alertmanager確認:
   http://localhost:9093

3. Webhook URL設定確認:
   ```bash
   cat config/alertmanager/config.yml | grep webhook
   ```

### Jaegerにトレースが表示されない

1. Jaegerエージェント接続確認:
   ```bash
   docker logs mangaanime-jaeger
   ```

2. アプリケーション側トレーシング有効化確認:
   ```python
   from modules.tracing import TRACING_AVAILABLE
   print(f"Tracing available: {TRACING_AVAILABLE}")
   ```

3. OpenTelemetryパッケージインストール確認:
   ```bash
   pip list | grep opentelemetry
   ```

## メンテナンス

### データ保持期間

- **Prometheus**: 30日間（設定変更可能）
- **Jaeger**: 7日間（デフォルト）

### バックアップ

```bash
# Prometheusデータバックアップ
docker run --rm -v mangaanime-info-delivery-system_prometheus-data:/data \
  -v $(pwd)/backup:/backup alpine tar czf /backup/prometheus-backup.tar.gz /data

# Grafanaデータバックアップ
docker run --rm -v mangaanime-info-delivery-system_grafana-data:/data \
  -v $(pwd)/backup:/backup alpine tar czf /backup/grafana-backup.tar.gz /data
```

### リストア

```bash
# Prometheusデータリストア
docker run --rm -v mangaanime-info-delivery-system_prometheus-data:/data \
  -v $(pwd)/backup:/backup alpine tar xzf /backup/prometheus-backup.tar.gz -C /

# Grafanaデータリストア
docker run --rm -v mangaanime-info-delivery-system_grafana-data:/data \
  -v $(pwd)/backup:/backup alpine tar xzf /backup/grafana-backup.tar.gz -C /
```

## ベストプラクティス

### メトリクス命名規則

- カウンター: `*_total`
- ゲージ: そのまま
- ヒストグラム: `*_seconds`, `*_bytes`
- サマリー: `*_summary`

### アラート設定

- しきい値は環境に応じて調整
- `for`句で一時的なスパイクを除外
- `annotations`で詳細情報を記載
- `runbook_url`で対応手順を参照可能に

### ダッシュボード設計

- パネルは目的別に整理
- 重要なメトリクスは上部に配置
- 時間範囲は柔軟に選択可能に
- テンプレート変数で動的フィルタリング

## 参考リンク

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Alertmanager Documentation](https://prometheus.io/docs/alerting/latest/alertmanager/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
