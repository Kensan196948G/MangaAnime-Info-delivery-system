"""
APIキー管理UI用のBlueprint

このモジュールは、WebブラウザからAPIキーを管理するためのUIを提供します。

Routes:
    - GET /api-keys/manage - APIキー管理ページ
"""

from flask import Blueprint, render_template, session, redirect, url_for, flash

# Blueprint定義
api_key_ui_bp = Bluelogger.info('api_key_ui', __name__)


def login_required(f):
    """ログイン必須デコレータ（シンプル版）"""
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('ログインが必要です', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@api_key_ui_bp.route('/api-keys/manage')
@login_required
def manage_api_keys():
    """
    APIキー管理ページ


    ログインユーザーのみアクセス可能
    """
    username = session.get('username')
    return render_template('api_keys.html', username=username)
