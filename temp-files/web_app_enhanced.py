"""
Enhanced Flask Application with Session Security
MangaAnime-Info-delivery-system
"""

from flask import Flask, render_template, jsonify, request, send_from_directory
from modules.db import Database
import os
import logging
from datetime import datetime, timedelta
import sys
from pathlib import Path

# プロジェクトルートのmodulesをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from modules.config import Config
from app.utils.security import SecurityConfig, DevelopmentSecurityConfig

app = Flask(__name__, static_folder='static', template_folder='templates')

# 環境判定（開発環境か本番環境か）
ENV = os.environ.get('FLASK_ENV', 'development')

# 基本設定
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
app.config['ENV'] = ENV

# セキュリティ設定の適用
if ENV == 'production':
    SecurityConfig.init_app(app)
else:
    DevelopmentSecurityConfig.init_app(app)

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# データベース初期化
db = Database()

# 設定読み込み
try:
    config = Config()
    logger.info("Configuration loaded successfully")
except Exception as e:
    logger.error(f"Failed to load configuration: {e}")
    config = None


@app.route('/')
def index():
    """メインページ"""
    return render_template('index.html')


@app.route('/api/releases')
def get_releases():
    """リリース情報取得API"""
    try:
        releases = db.get_upcoming_releases(limit=50)
        return jsonify({
            'status': 'success',
            'data': releases
        })
    except Exception as e:
        logger.error(f"Error fetching releases: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/works')
def get_works():
    """作品情報取得API"""
    try:
        works = db.get_all_works()
        return jsonify({
            'status': 'success',
            'data': works
        })
    except Exception as e:
        logger.error(f"Error fetching works: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/api/config')
def get_config():
    """設定情報取得API"""
    try:
        if not config:
            return jsonify({
                'status': 'error',
                'message': 'Configuration not loaded'
            }), 500

        return jsonify({
            'status': 'success',
            'data': {
                'email_enabled': config.email_enabled,
                'calendar_enabled': config.calendar_enabled,
            }
        })
    except Exception as e:
        logger.error(f"Error fetching config: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@app.route('/static/<path:filename>')
def serve_static(filename):
    """静的ファイル配信"""
    return send_from_directory(app.static_folder, filename)


@app.errorhandler(404)
def not_found(error):
    """404エラーハンドラ"""
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """500エラーハンドラ"""
    logger.error(f"Internal server error: {error}")
    return render_template('500.html'), 500


if __name__ == '__main__':
    # 開発サーバー起動
    port = int(os.environ.get('PORT', 5000))
    debug = ENV == 'development'

    logger.info(f"Starting Flask application on port {port} (ENV: {ENV})")
    logger.info(f"Session security: {'ENABLED' if app.config.get('SESSION_COOKIE_SECURE') else 'DISABLED (HTTP)'}")

    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
