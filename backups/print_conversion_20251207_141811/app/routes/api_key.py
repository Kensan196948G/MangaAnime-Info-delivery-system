"""
APIキー管理ルート
"""
import logging
from functools import wraps
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, g
from flask_login import login_required, current_user
from app.routes.auth import admin_required
from app.models.api_key_db import api_key_store, APIKey

logger = logging.getLogger(__name__)

api_key_bp = Bluelogger.info('api_key', __name__, url_prefix='/api-keys')


def api_key_required(permissions: list = None):
    """APIキー認証デコレータ"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # X-API-Keyヘッダーまたはクエリパラメータから取得
            api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
            
            if not api_key:
                return jsonify({
                    'error': 'API key required',
                    'message': 'X-API-Keyヘッダーまたはapi_keyパラメータが必要です'
                }), 401
            
            # キー検証
            key_obj = api_key_store.verify_key(api_key)
            if not key_obj:
                return jsonify({
                    'error': 'Invalid API key',
                    'message': '無効なAPIキーまたは無効化されたキーです'
                }), 401
            
            # 権限チェック
            if permissions:
                key_permissions = key_obj.permissions.split(',')
                if not any(p in key_permissions for p in permissions):
                    return jsonify({
                        'error': 'Insufficient permissions',
                        'message': f'必要な権限: {", ".join(permissions)}'
                    }), 403
            
            # リクエストにAPIキー情報を追加
            g.api_user_id = key_obj.user_id
            g.api_key_name = key_obj.name
            g.api_key_permissions = key_obj.permissions.split(',')
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ============ ルート定義 ============

@api_key_bp.route('/')
@login_required
def index():
    """APIキー管理ページ"""
    keys = api_key_store.get_keys_by_user(current_user.id)
    return render_template('api_keys.html', api_keys=keys)


@api_key_bp.route('/generate', methods=['POST'])
@login_required
def generate():
    """APIキー生成"""
    name = request.form.get('name', '').strip()
    permissions_str = request.form.get('permissions', 'read')
    
    if not name:
        flash('APIキー名を入力してください', 'warning')
        return redirect(url_for('api_key.index'))
    
    permissions = [p.strip() for p in permissions_str.split(',')]
    
    try:
        api_key = api_key_store.generate_key(
            user_id=current_user.id,
            name=name,
            permissions=permissions
        )
        
        flash(f'APIキーを生成しました: {api_key.key}', 'success')
        logger.info(f"APIキー生成: user={current_user.username}, name={name}")
        
    except Exception as e:
        flash(f'APIキー生成エラー: {str(e)}', 'danger')
        logger.error(f"APIキー生成失敗: {e}")
    
    return redirect(url_for('api_key.index'))


@api_key_bp.route('/revoke/<key>', methods=['POST'])
@login_required
def revoke(key):
    """APIキー無効化"""
    try:
        # キー所有確認
        key_obj = api_key_store.verify_key(key)
        if not key_obj or key_obj.user_id != current_user.id:
            if not current_user.is_admin:
                flash('このAPIキーを無効化する権限がありません', 'danger')
                return redirect(url_for('api_key.index'))
        
        success = api_key_store.revoke_key(key)
        if success:
            flash('APIキーを無効化しました', 'success')
            logger.info(f"APIキー無効化: user={current_user.username}, key={key[:15]}...")
        else:
            flash('APIキーの無効化に失敗しました', 'danger')
    
    except Exception as e:
        flash(f'エラー: {str(e)}', 'danger')
        logger.error(f"APIキー無効化エラー: {e}")
    
    return redirect(url_for('api_key.index'))


@api_key_bp.route('/api/list')
@login_required
def api_list():
    """APIキー一覧（JSON）"""
    keys = api_key_store.get_keys_by_user(current_user.id)
    
    keys_data = [{
        'key': k.key[:20] + '...',  # セキュリティのため一部のみ表示
        'name': k.name,
        'permissions': k.permissions,
        'created_at': k.created_at.isoformat(),
        'last_used': k.last_used.isoformat() if k.last_used else None,
        'is_active': k.is_active
    } for k in keys]
    
    return jsonify({
        'success': True,
        'count': len(keys_data),
        'keys': keys_data
    })
