#!/usr/bin/env python3
"""
Monitoring Integration Example
監視システム統合のサンプルコード
"""

from flask import Flask, jsonify, request
import sqlite3
import time
import random
from datetime import datetime

# 監視モジュールインポート
from modules.metrics import (
    init_metrics,
    track_request,
    track_db_operation,
    track_api_fetch,
    record_notification,
    record_calendar_sync,
    record_calendar_event_created,
    MetricsCollector
)
from modules.tracing import (
    init_tracing,
    init_flask_tracing,
    trace_span,
    trace_function,
    TracedOperation
)

# Flaskアプリケーション初期化
app = Flask(__name__)

# メトリクス初期化
init_metrics(app)

# トレーシング初期化
init_tracing(
    service_name="mangaanime-info-delivery",
    jaeger_host="localhost",
    jaeger_port=6831,
    enable_flask=False  # init_flask_tracingで個別に初期化
)
init_flask_tracing(app)

# データベース接続
def get_db_connection():
    """データベース接続を取得"""
    conn = sqlite3.connect('data/db.sqlite3')
    conn.row_factory = sqlite3.Row
    return conn


# ルート定義

@app.route('/')
@track_request
def index():
    """トップページ"""
    return jsonify({
        'message': 'MangaAnime Info Delivery System',
        'version': '1.0.0',
        'monitoring': 'enabled'
    })


@app.route('/health')
def health():
    """ヘルスチェックエンドポイント"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    })


@app.route('/api/works')
@track_request
@trace_function(span_name='get_all_works')
def get_works():
    """全作品取得（メトリクス・トレーシング統合例）"""
    work_type = request.args.get('type', None)

    with trace_span('db_query', {'table': 'works', 'filter': work_type}):
        works = get_all_works(work_type)

    # メトリクス更新
    anime_count = len([w for w in works if w['type'] == 'anime'])
    manga_count = len([w for w in works if w['type'] == 'manga'])
    MetricsCollector.update_work_counts(anime_count, manga_count)

    return jsonify({
        'total': len(works),
        'anime': anime_count,
        'manga': manga_count,
        'works': works
    })


@track_db_operation(operation='select', table='works')
@trace_function()
def get_all_works(work_type=None):
    """データベースから全作品取得"""
    conn = get_db_connection()
    cursor = conn.cursor()

    if work_type:
        cursor.execute("SELECT * FROM works WHERE type = ?", (work_type,))
    else:
        cursor.execute("SELECT * FROM works")

    works = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return works


@app.route('/api/releases/pending')
@track_request
def get_pending_releases():
    """未通知リリース取得（メトリクス更新例）"""
    pending = get_pending_releases_from_db()

    anime_pending = len([r for r in pending if r['work_type'] == 'anime'])
    manga_pending = len([r for r in pending if r['work_type'] == 'manga'])

    # メトリクス更新
    MetricsCollector.update_pending_releases(anime_pending, manga_pending)

    return jsonify({
        'total': len(pending),
        'anime': anime_pending,
        'manga': manga_pending,
        'releases': pending
    })


@track_db_operation(operation='select', table='releases')
def get_pending_releases_from_db():
    """未通知リリースをDBから取得"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT r.*, w.title, w.type as work_type
        FROM releases r
        JOIN works w ON r.work_id = w.id
        WHERE r.notified = 0
    """)

    releases = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return releases


@app.route('/api/fetch/simulate')
@track_request
def simulate_fetch():
    """API取得シミュレーション（メトリクス記録例）"""
    source = request.args.get('source', 'anilist')

    # シミュレート
    result = simulate_api_fetch(source)

    return jsonify(result)


@track_api_fetch(source='anilist')
@trace_function()
def simulate_api_fetch(source):
    """API取得をシミュレート"""
    # 実際のAPI呼び出しをシミュレート
    time.sleep(random.uniform(0.1, 2.0))

    # ランダムでエラーをシミュレート（10%の確率）
    if random.random() < 0.1:
        raise Exception(f"API fetch failed for {source}")

    return {
        'source': source,
        'status': 'success',
        'items_fetched': random.randint(5, 50)
    }


@app.route('/api/notify/simulate')
@track_request
def simulate_notification():
    """通知送信シミュレーション（メトリクス記録例）"""
    notification_type = request.args.get('type', 'email')

    try:
        # 通知送信をシミュレート
        time.sleep(random.uniform(0.05, 0.5))

        # ランダムでエラーをシミュレート（5%の確率）
        if random.random() < 0.05:
            raise Exception(f"Notification failed: {notification_type}")

        # 成功記録
        record_notification(notification_type, 'success')

        return jsonify({
            'status': 'success',
            'type': notification_type
        })

    except Exception as e:
        # エラー記録
        record_notification(notification_type, 'error')
        return jsonify({
            'status': 'error',
            'type': notification_type,
            'error': str(e)
        }), 500


@app.route('/api/calendar/simulate')
@track_request
def simulate_calendar_sync():
    """カレンダー同期シミュレーション（メトリクス記録例）"""
    try:
        # 同期をシミュレート
        with TracedOperation('calendar_sync', 'calendar') as op:
            time.sleep(random.uniform(0.1, 1.0))

            # イベント作成数をシミュレート
            events_created = random.randint(1, 10)
            op.add_attribute('events_created', events_created)

            # ランダムでエラーをシミュレート（5%の確率）
            if random.random() < 0.05:
                raise Exception("Calendar sync failed")

            # 成功記録
            for _ in range(events_created):
                record_calendar_event_created()

            record_calendar_sync('success')

        return jsonify({
            'status': 'success',
            'events_created': events_created
        })

    except Exception as e:
        # エラー記録
        record_calendar_sync('error')
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/load/simulate')
@track_request
def simulate_load():
    """負荷シミュレーション（パフォーマンステスト用）"""
    duration = float(request.args.get('duration', 1.0))
    error_rate = float(request.args.get('error_rate', 0.0))

    # 処理時間シミュレート
    time.sleep(duration)

    # エラーシミュレート
    if random.random() < error_rate:
        raise Exception("Simulated error")

    return jsonify({
        'status': 'success',
        'duration': duration,
        'error_rate': error_rate
    })


@app.errorhandler(Exception)
def handle_error(error):
    """エラーハンドラ（トレーシングにエラー記録）"""
    return jsonify({
        'error': str(error),
        'type': type(error).__name__
    }), 500


# システムメトリクス定期更新（バックグラウンドタスク例）
def update_system_metrics():
    """システムメトリクスを定期更新"""
    while True:
        try:
            MetricsCollector.collect_system_metrics()
            time.sleep(15)  # 15秒ごとに更新
        except Exception as e:
            print(f"Error updating system metrics: {e}")
            time.sleep(15)


if __name__ == '__main__':
    # システムメトリクス更新をバックグラウンドで開始
    import threading
    metrics_thread = threading.Thread(target=update_system_metrics, daemon=True)
    metrics_thread.start()

    print("=" * 60)
    print("MangaAnime Info Delivery System - Monitoring Integration")
    print("=" * 60)
    print("")
    print("Application: http://localhost:5000")
    print("Metrics:     http://localhost:5000/metrics")
    print("Health:      http://localhost:5000/health")
    print("")
    print("Monitoring Stack:")
    print("  Prometheus:   http://localhost:9090")
    print("  Grafana:      http://localhost:3000")
    print("  Jaeger:       http://localhost:16686")
    print("")
    print("API Endpoints:")
    print("  GET /api/works")
    print("  GET /api/releases/pending")
    print("  GET /api/fetch/simulate?source=anilist")
    print("  GET /api/notify/simulate?type=email")
    print("  GET /api/calendar/simulate")
    print("  GET /api/load/simulate?duration=1.0&error_rate=0.1")
    print("")

    # アプリケーション起動
    app.run(host='0.0.0.0', port=5000, debug=False)
