"""
Flask Web UI for Manga/Anime Information Delivery System
アニメ・マンガ情報配信システム Web UI
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from datetime import datetime, timedelta
import sqlite3
import json
import os
from typing import Dict, List, Any
from modules.db import DatabaseManager
from modules.dashboard import dashboard_bp, dashboard_service
from modules.monitoring import PerformanceMonitor
import logging

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

# ダッシュボード Blueprint を登録
app.register_blueprint(dashboard_bp)

# グローバル変数
db_manager = DatabaseManager()
performance_monitor = PerformanceMonitor()

@app.route('/')
def index():
    """メインページ"""
    try:
        # 最新のリリース情報を取得
        with sqlite3.connect("db.sqlite3") as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT w.title, r.release_type, r.number, r.platform, 
                       r.release_date, r.notified, w.type
                FROM releases r 
                JOIN works w ON r.work_id = w.id 
                ORDER BY r.release_date DESC, r.created_at DESC 
                LIMIT 50
            """)
            releases = [dict(row) for row in cursor.fetchall()]
            
            # 統計情報を取得
            cursor = conn.execute("SELECT COUNT(*) as count FROM works")
            total_works = cursor.fetchone()['count']
            
            cursor = conn.execute("SELECT COUNT(*) as count FROM releases WHERE notified = 1")
            notified_releases = cursor.fetchone()['count']
            
            cursor = conn.execute("""
                SELECT COUNT(*) as count FROM releases 
                WHERE release_date >= date('now') AND release_date <= date('now', '+7 days')
            """)
            upcoming_releases = cursor.fetchone()['count']
    
    except Exception as e:
        logger.error(f"Error loading index page: {e}")
        releases = []
        total_works = 0
        notified_releases = 0
        upcoming_releases = 0
    
    stats = {
        'total_works': total_works,
        'notified_releases': notified_releases,
        'upcoming_releases': upcoming_releases
    }
    
    return render_template('index.html', releases=releases, stats=stats)

@app.route('/works')
def works():
    """作品一覧ページ"""
    try:
        search_query = request.args.get('search', '').strip()
        work_type = request.args.get('type', '').strip()
        
        with sqlite3.connect("db.sqlite3") as conn:
            conn.row_factory = sqlite3.Row
            
            # 基本クエリ
            query = """
                SELECT w.*, 
                       COUNT(r.id) as release_count,
                       MAX(r.release_date) as latest_release
                FROM works w 
                LEFT JOIN releases r ON w.id = r.work_id
                WHERE 1=1
            """
            params = []
            
            # 検索条件を追加
            if search_query:
                query += " AND (w.title LIKE ? OR w.title_kana LIKE ? OR w.title_en LIKE ?)"
                search_param = f"%{search_query}%"
                params.extend([search_param, search_param, search_param])
            
            if work_type:
                query += " AND w.type = ?"
                params.append(work_type)
            
            query += " GROUP BY w.id ORDER BY w.created_at DESC"
            
            cursor = conn.execute(query, params)
            works_data = [dict(row) for row in cursor.fetchall()]
    
    except Exception as e:
        logger.error(f"Error loading works page: {e}")
        works_data = []
    
    return render_template('works.html', works=works_data, 
                         search_query=search_query, work_type=work_type)

@app.route('/work/<int:work_id>')
def work_detail(work_id):
    """作品詳細ページ"""
    try:
        with sqlite3.connect("db.sqlite3") as conn:
            conn.row_factory = sqlite3.Row
            
            # 作品情報を取得
            cursor = conn.execute("SELECT * FROM works WHERE id = ?", (work_id,))
            work = cursor.fetchone()
            
            if not work:
                flash('指定された作品が見つかりません。', 'error')
                return redirect(url_for('works'))
            
            # リリース情報を取得
            cursor = conn.execute("""
                SELECT * FROM releases 
                WHERE work_id = ? 
                ORDER BY release_date DESC, created_at DESC
            """, (work_id,))
            releases = [dict(row) for row in cursor.fetchall()]
    
    except Exception as e:
        logger.error(f"Error loading work detail for ID {work_id}: {e}")
        flash('作品詳細の読み込みでエラーが発生しました。', 'error')
        return redirect(url_for('works'))
    
    return render_template('work_detail.html', work=dict(work), releases=releases)

@app.route('/settings')
def settings():
    """設定ページ"""
    try:
        # 設定ファイルが存在するかチェック
        config_exists = os.path.exists('config.json')
        config_data = {}
        
        if config_exists:
            with open('config.json', 'r', encoding='utf-8') as f:
                config_data = json.load(f)
    
    except Exception as e:
        logger.error(f"Error loading settings: {e}")
        config_exists = False
        config_data = {}
    
    return render_template('settings.html', config_exists=config_exists, config=config_data)

@app.route('/api/trigger-collection', methods=['POST'])
def api_trigger_collection():
    """手動データ収集トリガー API"""
    try:
        # パフォーマンス監視開始
        with performance_monitor.measure_time("manual_collection"):
            # ここで実際のデータ収集処理を呼び出す
            # release_notifier.py の main() 関数を呼び出すか、
            # 必要な収集処理を実行
            
            # ダッシュボード統計を更新
            dashboard_service.record_metric(
                "manual_collection", 1, "counter", 
                source="web_ui", metadata={"timestamp": datetime.now().isoformat()}
            )
            
            # システムヘルス状態を更新
            dashboard_service.update_system_health(
                "manual_collection", "healthy", 
                performance_score=1.0
            )
        
        return jsonify({
            'success': True,
            'message': 'データ収集を開始しました',
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error triggering collection: {e}")
        
        # エラー時のダッシュボード更新
        dashboard_service.update_system_health(
            "manual_collection", "error", 
            error_message=str(e)
        )
        
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/system-stats')
def api_system_stats():
    """システム統計情報 API"""
    try:
        with sqlite3.connect("db.sqlite3") as conn:
            conn.row_factory = sqlite3.Row
            
            # 基本統計
            cursor = conn.execute("SELECT COUNT(*) as count FROM works")
            total_works = cursor.fetchone()['count']
            
            cursor = conn.execute("SELECT COUNT(*) as count FROM works WHERE type = 'anime'")
            anime_count = cursor.fetchone()['count']
            
            cursor = conn.execute("SELECT COUNT(*) as count FROM works WHERE type = 'manga'")
            manga_count = cursor.fetchone()['count']
            
            cursor = conn.execute("SELECT COUNT(*) as count FROM releases WHERE notified = 1")
            total_notifications = cursor.fetchone()['count']
            
            cursor = conn.execute("""
                SELECT COUNT(*) as count FROM releases 
                WHERE notified = 1 AND created_at > datetime('now', '-24 hours')
            """)
            recent_notifications = cursor.fetchone()['count']
            
            return jsonify({
                'total_works': total_works,
                'anime_count': anime_count,
                'manga_count': manga_count,
                'total_notifications': total_notifications,
                'recent_notifications': recent_notifications,
                'timestamp': datetime.now().isoformat()
            })
    
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    # データベースの初期化
    db_manager.initialize_database()
    
    # 開発モードでの実行
    app.run(debug=True, host='0.0.0.0', port=5000)