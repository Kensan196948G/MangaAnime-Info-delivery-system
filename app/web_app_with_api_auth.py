"""
Web Application with API Key Authentication

このファイルは、FlaskベースのWebアプリケーションにAPIキー認証機能を追加したバージョンです。

主な追加機能:
- APIキー認証デコレータ (@api_key_required)
- 読み取り専用APIエンドポイントの保護
- APIキー管理UI（Blueprint統合）

使用方法:
    python app/web_app_with_api_auth.py
"""

import os
import sys
from datetime import datetime, timedelta

from flask import Flask, flash, g, jsonify, redirect, render_template, request, session, url_for

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging

from modules.config import load_config
from modules.db import get_db_connection

logger = logging.getLogger(__name__)

# APIキー認証モジュールのインポート
try:
    from app.routes.api_auth import api_auth_bp, api_key_required, user_store
    API_AUTH_ENABLED = True
except ImportError:
    logger.warning("API authentication module not available")
    API_AUTH_ENABLED = False

    # フォールバック用のダミーデコレータ
    def api_key_required(f):
        return f

app = Flask(__name__,
            template_folder='../templates',
            static_folder='../static')

# セッション設定
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

# API認証Blueprintの登録
if API_AUTH_ENABLED:
    app.register_blueprint(api_auth_bp)

# =====================================
# 基本ページ（非API）
# =====================================

@app.route('/')
def index():
    """トップページ"""
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """ログインページ"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if API_AUTH_ENABLED:
            user = user_store.verify_user(username, password)
            if user:
                session['username'] = username
                session.permanent = True
                flash('ログインしました', 'success')
                next_page = request.args.get('next', '/')
                return redirect(next_page)

        flash('ユーザー名またはパスワードが正しくありません', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    """ログアウト"""
    session.clear()
    flash('ログアウトしました', 'info')
    return redirect(url_for('index'))


@app.route('/dashboard')
def dashboard():
    """ダッシュボード（認証不要）"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 統計情報を取得
    cursor.execute("SELECT COUNT(*) FROM works WHERE type='anime'")
    anime_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM works WHERE type='manga'")
    manga_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM releases WHERE notified=1")
    notified_count = cursor.fetchone()[0]

    conn.close()

    return render_template('dashboard.html',
                         anime_count=anime_count,
                         manga_count=manga_count,
                         notified_count=notified_count)


# =====================================
# API Endpoints (API Key Required)
# =====================================

@app.route('/api/stats')
@api_key_required
def api_stats():
    """
    統計情報API

    認証: X-API-Key ヘッダー または api_key クエリパラメータ

    Response:
        {
            "success": true,
            "stats": {
                "total_works": 100,
                "anime_count": 60,
                "manga_count": 40,
                "total_releases": 500,
                "notified_releases": 450
            },
            "user_id": "username"
        }
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM works")
        total_works = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM works WHERE type='anime'")
        anime_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM works WHERE type='manga'")
        manga_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM releases")
        total_releases = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM releases WHERE notified=1")
        notified_releases = cursor.fetchone()[0]

        conn.close()

        return jsonify({
            'success': True,
            'stats': {
                'total_works': total_works,
                'anime_count': anime_count,
                'manga_count': manga_count,
                'total_releases': total_releases,
                'notified_releases': notified_releases
            },
            'user_id': g.get('api_user_id', 'unknown')
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/releases')
@api_key_required
def api_releases():
    """
    リリース一覧API

    認証: X-API-Key ヘッダー または api_key クエリパラメータ

    Query Parameters:
        - type: anime/manga (optional)
        - limit: int (default: 50)
        - offset: int (default: 0)

    Response:
        {
            "success": true,
            "count": 50,
            "releases": [...]
        }
    """
    try:
        release_type = request.args.get('type')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))

        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT r.*, w.title, w.type
            FROM releases r
            JOIN works w ON r.work_id = w.id
        """
        params = []

        if release_type:
            query += " WHERE w.type = ?"
            params.append(release_type)

        query += " ORDER BY r.release_date DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        releases = cursor.fetchall()

        conn.close()

        return jsonify({
            'success': True,
            'count': len(releases),
            'limit': limit,
            'offset': offset,
            'releases': [dict(r) for r in releases],
            'user_id': g.get('api_user_id', 'unknown')
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/releases/upcoming')
@api_key_required
def api_upcoming_releases():
    """
    今後のリリース情報API

    認証: X-API-Key ヘッダー または api_key クエリパラメータ

    Query Parameters:
        - days: int (default: 7) - 今後何日分のリリースを取得するか
        - type: anime/manga (optional)

    Response:
        {
            "success": true,
            "count": 20,
            "releases": [...]
        }
    """
    try:
        days = int(request.args.get('days', 7))
        release_type = request.args.get('type')

        conn = get_db_connection()
        cursor = conn.cursor()

        query = """
            SELECT r.*, w.title, w.type
            FROM releases r
            JOIN works w ON r.work_id = w.id
            WHERE r.release_date >= date('now')
            AND r.release_date <= date('now', '+' || ? || ' days')
        """
        params = [days]

        if release_type:
            query += " AND w.type = ?"
            params.append(release_type)

        query += " ORDER BY r.release_date ASC"

        cursor.execute(query, params)
        releases = cursor.fetchall()

        conn.close()

        return jsonify({
            'success': True,
            'count': len(releases),
            'days': days,
            'releases': [dict(r) for r in releases],
            'user_id': g.get('api_user_id', 'unknown')
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/works')
@api_key_required
def api_works():
    """
    作品一覧API

    認証: X-API-Key ヘッダー または api_key クエリパラメータ

    Query Parameters:
        - type: anime/manga (optional)
        - search: 検索キーワード (optional)
        - limit: int (default: 50)
        - offset: int (default: 0)

    Response:
        {
            "success": true,
            "count": 50,
            "works": [...]
        }
    """
    try:
        work_type = request.args.get('type')
        search = request.args.get('search')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))

        conn = get_db_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM works WHERE 1=1"
        params = []

        if work_type:
            query += " AND type = ?"
            params.append(work_type)

        if search:
            query += " AND (title LIKE ? OR title_kana LIKE ? OR title_en LIKE ?)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term])

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        works = cursor.fetchall()

        conn.close()

        return jsonify({
            'success': True,
            'count': len(works),
            'limit': limit,
            'offset': offset,
            'works': [dict(w) for w in works],
            'user_id': g.get('api_user_id', 'unknown')
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/works/<int:work_id>')
@api_key_required
def api_work_detail(work_id):
    """
    作品詳細API

    認証: X-API-Key ヘッダー または api_key クエリパラメータ

    Response:
        {
            "success": true,
            "work": {...},
            "releases": [...]
        }
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 作品情報を取得
        cursor.execute("SELECT * FROM works WHERE id = ?", (work_id,))
        work = cursor.fetchone()

        if not work:
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Work not found'
            }), 404

        # リリース情報を取得
        cursor.execute("""
            SELECT * FROM releases
            WHERE work_id = ?
            ORDER BY release_date DESC
        """, (work_id,))
        releases = cursor.fetchall()

        conn.close()

        return jsonify({
            'success': True,
            'work': dict(work),
            'releases': [dict(r) for r in releases],
            'user_id': g.get('api_user_id', 'unknown')
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# =====================================
# エラーハンドラー
# =====================================

@app.errorhandler(404)
def not_found(error):
    """404エラーハンドラー"""
    if request.path.startswith('/api/'):
        return jsonify({
            'success': False,
            'error': 'Endpoint not found',
            'status': 404
        }), 404
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """500エラーハンドラー"""
    if request.path.startswith('/api/'):
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'status': 500
        }), 500
    return render_template('500.html'), 500


# =====================================
# アプリケーション起動
# =====================================

if __name__ == '__main__':
    # 開発環境用のデフォルトユーザーを作成（環境変数から取得）
    if API_AUTH_ENABLED:
        default_admin_password = os.environ.get('DEFAULT_ADMIN_PASSWORD')
        if not default_admin_password:
            logger.error("ERROR: DEFAULT_ADMIN_PASSWORD environment variable is required")
            logger.info("Set it in .env file or as environment variable")
            sys.exit(1)
        try:
            user_store.create_user('admin', default_admin_password)
            logger.info("Default admin user created")
        except ValueError:
            logger.info("Default user already exists")

    logger.info("\n" + "="*60)
    logger.info("Flask Web Application with API Key Authentication")
    logger.info("="*60)
    logger.info(f"API Authentication: {'Enabled' if API_AUTH_ENABLED else 'Disabled'}")
    logger.info(f"Server URL: http://127.0.0.1:5000")
    logger.info(f"Dashboard: http://127.0.0.1:5000/dashboard")
    if API_AUTH_ENABLED:
        logger.info(f"Login: http://127.0.0.1:5000/login")
        logger.info(f"API Key Management: http://127.0.0.1:5000/auth/api-keys")
    logger.info("="*60 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
