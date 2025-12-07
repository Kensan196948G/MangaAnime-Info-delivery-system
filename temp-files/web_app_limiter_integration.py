"""
web_app.pyへのFlask-Limiter統合例

このファイルは、既存のweb_app.pyにレート制限機能を追加する際の
統合方法を示すサンプルコードです。

実際の統合時は、web_app.pyに以下のコードを適切に組み込んでください。
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_required, current_user
from flask_cors import CORS
import os
import sys

# レート制限関連のインポート
from app.utils.rate_limiter import init_limiter, get_rate_limit

# Flaskアプリケーションの作成
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# レート制限の設定
app.config['RATELIMIT_STORAGE_URI'] = os.environ.get(
    'RATELIMIT_STORAGE_URI',
    'memory://'  # 開発環境: メモリベース
    # 'redis://localhost:6379'  # 本番環境: Redis使用
)
app.config['RATELIMIT_DEFAULT'] = ["200 per day", "50 per hour"]

# CORS設定
CORS(app)

# LoginManager初期化
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# レート制限の初期化
limiter = init_limiter(app)


# ========================
# 既存のルート定義にレート制限を追加
# ========================

@app.route('/')
@limiter.limit("100 per minute")
def index():
    """トップページ"""
    return render_template('index.html')


@app.route('/dashboard')
@login_required
@limiter.limit("200 per hour")
def dashboard():
    """ダッシュボード"""
    return render_template('dashboard.html')


# ========================
# API エンドポイント
# ========================

@app.route('/api/manual-collection', methods=['POST'])
@login_required
@limiter.limit(get_rate_limit('api_collection'))
def api_manual_collection():
    """
    手動データ収集API
    レート制限: 10回/時間
    """
    try:
        # データ収集処理
        result = trigger_manual_collection()

        return jsonify({
            'success': True,
            'message': 'データ収集を開始しました',
            'data': result
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'データ収集エラー: {str(e)}'
        }), 500


@app.route('/api/settings', methods=['GET', 'POST'])
@login_required
@limiter.limit(get_rate_limit('api_settings'))
def api_settings():
    """
    設定API
    レート制限: 30回/時間
    """
    try:
        if request.method == 'GET':
            # 設定取得
            settings = get_current_settings()
            return jsonify({
                'success': True,
                'data': settings
            }), 200

        elif request.method == 'POST':
            # 設定更新
            data = request.get_json()
            update_settings(data)
            return jsonify({
                'success': True,
                'message': '設定を更新しました'
            }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'設定処理エラー: {str(e)}'
        }), 500


@app.route('/api/calendar/sync', methods=['POST'])
@login_required
@limiter.limit(get_rate_limit('api_calendar_sync'))
def api_calendar_sync():
    """
    カレンダー同期API
    レート制限: 15回/時間
    """
    try:
        # カレンダー同期処理
        result = sync_to_google_calendar()

        return jsonify({
            'success': True,
            'message': 'カレンダー同期を開始しました',
            'data': result
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'カレンダー同期エラー: {str(e)}'
        }), 500


@app.route('/api/notifications/send', methods=['POST'])
@login_required
@limiter.limit(get_rate_limit('api_notification'))
def api_send_notification():
    """
    通知送信API
    レート制限: 20回/時間
    """
    try:
        data = request.get_json()
        # 通知送信処理
        result = send_notification(data)

        return jsonify({
            'success': True,
            'message': '通知を送信しました',
            'data': result
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'通知送信エラー: {str(e)}'
        }), 500


@app.route('/api/rss/feeds', methods=['GET'])
@limiter.limit(get_rate_limit('api_rss'))
def api_rss_feeds():
    """
    RSSフィード取得API
    レート制限: 30回/時間
    """
    try:
        feeds = get_rss_feeds()

        return jsonify({
            'success': True,
            'data': feeds
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'RSSフィード取得エラー: {str(e)}'
        }), 500


@app.route('/api/data/scrape', methods=['POST'])
@login_required
@limiter.limit(get_rate_limit('api_scraping'))
def api_scrape_data():
    """
    スクレイピングAPI
    レート制限: 5回/時間（厳しい制限）
    """
    try:
        data = request.get_json()
        # スクレイピング処理
        result = scrape_external_data(data)

        return jsonify({
            'success': True,
            'message': 'スクレイピングを完了しました',
            'data': result
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'スクレイピングエラー: {str(e)}'
        }), 500


# ========================
# 管理者専用エンドポイント
# ========================

@app.route('/api/admin/users', methods=['GET'])
@login_required
@limiter.limit(get_rate_limit('admin_general'))
def api_admin_users():
    """
    管理者: ユーザー一覧取得
    レート制限: 500回/時間（緩い制限）
    """
    if not current_user.is_admin:
        return jsonify({
            'success': False,
            'message': '管理者権限が必要です'
        }), 403

    try:
        users = get_all_users()
        return jsonify({
            'success': True,
            'data': users
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'ユーザー取得エラー: {str(e)}'
        }), 500


# ========================
# エラーハンドラ
# ========================

@app.errorhandler(404)
def not_found(e):
    """404エラーハンドラ"""
    if request.path.startswith('/api/'):
        return jsonify({
            'error': 'Not Found',
            'message': '指定されたエンドポイントが見つかりません'
        }), 404
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(e):
    """500エラーハンドラ"""
    if request.path.startswith('/api/'):
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'サーバー内部エラーが発生しました'
        }), 500
    return render_template('500.html'), 500


# ========================
# ヘルパー関数（ダミー実装）
# ========================

def trigger_manual_collection():
    """手動データ収集のトリガー"""
    # 実際の実装に置き換える
    return {'status': 'started', 'jobs': 3}


def get_current_settings():
    """現在の設定を取得"""
    # 実際の実装に置き換える
    return {'notifications': True, 'calendar_sync': True}


def update_settings(data):
    """設定を更新"""
    # 実際の実装に置き換える
    pass


def sync_to_google_calendar():
    """Googleカレンダーに同期"""
    # 実際の実装に置き換える
    return {'synced': 10, 'failed': 0}


def send_notification(data):
    """通知を送信"""
    # 実際の実装に置き換える
    return {'sent': True, 'recipient': data.get('email')}


def get_rss_feeds():
    """RSSフィードを取得"""
    # 実際の実装に置き換える
    return [{'title': 'Feed 1', 'url': 'https://example.com/feed'}]


def scrape_external_data(data):
    """外部データをスクレイピング"""
    # 実際の実装に置き換える
    return {'items': 5, 'source': data.get('url')}


def get_all_users():
    """全ユーザーを取得（管理者用）"""
    # 実際の実装に置き換える
    return [{'id': 1, 'username': 'admin'}]


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=os.environ.get('FLASK_ENV') == 'development'
    )
