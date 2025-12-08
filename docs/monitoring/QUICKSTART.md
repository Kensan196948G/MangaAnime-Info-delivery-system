# 監視システム クイックスタートガイド

## 5分でセットアップ

### ステップ1: 監視システムセットアップ

```bash
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system

# 監視用パッケージインストール
pip install -r requirements-monitoring.txt

# セットアップスクリプト実行
chmod +x scripts/setup-monitoring.sh
./scripts/setup-monitoring.sh
```

### ステップ2: アプリケーションに監視機能を統合

```python
# app.py または main.py

from flask import Flask
from modules.metrics import init_metrics, track_request, MetricsCollector
from modules.tracing import init_tracing, init_flask_tracing

app = Flask(__name__)

# メトリクス初期化
init_metrics(app)

# トレーシング初期化
init_tracing(
    service_name="mangaanime-info-delivery",
    jaeger_host="localhost",
    jaeger_port=6831
)
init_flask_tracing(app)

# ルート定義
@app.route('/')
@track_request
def index():
    return "Hello, World!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### ステップ3: ダッシュボードアクセス

1. Grafana: http://localhost:3000
   - ユーザー: admin
   - パスワード: admin123

2. Prometheus: http://localhost:9090

3. Jaeger: http://localhost:16686

### ステップ4: アラート設定

```bash
# Slack Webhook URL設定
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# Alertmanager設定更新
sed -i "s|YOUR_SLACK_WEBHOOK_URL|$SLACK_WEBHOOK_URL|g" \
  config/alertmanager/config.yml

# Alertmanager再起動
docker-compose -f docker-compose-monitoring.yml restart alertmanager
```

## 使用例

### データベース操作にメトリクス追加

```python
from modules.metrics import track_db_operation

@track_db_operation(operation='select', table='works')
def get_all_works():
    conn = sqlite3.connect('data/db.sqlite3')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM works")
    results = cursor.fetchall()
    conn.close()
    return results
```

### API取得にトレーシング追加

```python
from modules.tracing import trace_anime_fetch
import requests

@trace_anime_fetch(source='anilist')
def fetch_from_anilist():
    response = requests.post(
        'https://graphql.anilist.co',
        json={'query': query}
    )
    return response.json()
```

### 通知送信にメトリクス記録

```python
from modules.metrics import record_notification

def send_email_notification(recipient, subject, body):
    try:
        # メール送信処理
        send_mail(recipient, subject, body)
        record_notification('email', 'success')
    except Exception as e:
        record_notification('email', 'error')
        raise
```

### カスタムメトリクス作成

```python
from prometheus_client import Counter, Histogram

# カスタムカウンター
custom_counter = Counter(
    'custom_events_total',
    'Total custom events',
    ['event_type']
)

# 使用
custom_counter.labels(event_type='user_action').inc()

# カスタムヒストグラム
custom_histogram = Histogram(
    'custom_duration_seconds',
    'Custom operation duration',
    buckets=(0.1, 0.5, 1.0, 5.0, 10.0)
)

# 使用
with custom_histogram.time():
    # 処理
    pass
```

## よくある質問

### Q: メトリクスが表示されない

A: 以下を確認してください:
1. アプリケーションが /metrics エンドポイントを公開しているか
2. Prometheusが正しくスクレイプしているか (http://localhost:9090/targets)
3. ファイアウォールが適切に設定されているか

### Q: アラートが発火しない

A: 以下を確認してください:
1. Prometheusでアラートルールが評価されているか (http://localhost:9090/alerts)
2. Alertmanagerが動作しているか (http://localhost:9093)
3. Webhook URLが正しく設定されているか

### Q: Jaegerにトレースが表示されない

A: 以下を確認してください:
1. OpenTelemetryパッケージがインストールされているか
2. init_tracing()が呼ばれているか
3. Jaegerエージェントが動作しているか (docker ps)

### Q: Grafanaにログインできない

A: デフォルト認証情報:
- ユーザー: admin
- パスワード: admin123

初回ログイン後、パスワード変更を推奨します。

## メトリクスのベストプラクティス

1. **命名規則を守る**
   - カウンター: `*_total`
   - ヒストグラム: `*_seconds`, `*_bytes`
   - ゲージ: そのまま

2. **適切なラベルを使用**
   ```python
   # 良い例
   http_requests_total.labels(method='GET', endpoint='/api/works').inc()

   # 悪い例（カーディナリティが高い）
   http_requests_total.labels(user_id=user_id).inc()
   ```

3. **ヒストグラムのバケットを適切に設定**
   ```python
   # レイテンシ測定用
   buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
   ```

4. **定期的にメトリクスをレビュー**
   - 使用されていないメトリクスを削除
   - 新しい要件に応じて追加

## トレーシングのベストプラクティス

1. **重要な操作にスパンを追加**
   - API呼び出し
   - データベースクエリ
   - 外部サービス連携

2. **適切な属性を設定**
   ```python
   with trace_span("db_query", {"table": "works", "operation": "select"}):
       # クエリ実行
       pass
   ```

3. **エラー情報を記録**
   ```python
   try:
       # 処理
       pass
   except Exception as e:
       span.set_status(Status(StatusCode.ERROR, str(e)))
       span.record_exception(e)
       raise
   ```

## 次のステップ

1. [詳細ドキュメント](README.md)を確認
2. カスタムダッシュボードを作成
3. アラートルールをカスタマイズ
4. 本番環境用の設定を調整

## サポート

問題が発生した場合:

1. ログを確認:
   ```bash
   docker-compose -f docker-compose-monitoring.yml logs
   ```

2. 設定を検証:
   ```bash
   docker-compose -f docker-compose-monitoring.yml config
   ```

3. サービスを再起動:
   ```bash
   docker-compose -f docker-compose-monitoring.yml restart
   ```
