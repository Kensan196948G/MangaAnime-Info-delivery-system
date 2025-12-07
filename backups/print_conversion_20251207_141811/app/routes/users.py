"""
ユーザー管理機能ルート
管理者専用のユーザーCRUD操作を提供
"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from functools import wraps
from app.routes.auth import user_store
from datetime import datetime
import secrets
import hashlib

users_bp = Bluelogger.info('users', __name__, url_prefix='/users')


def admin_required(f):
    """管理者権限チェックデコレーター"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('この機能は管理者のみ使用できます。', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@users_bp.route('/')
@admin_required
def user_list():
    """ユーザー一覧表示"""
    users = user_store.get_all_users()

    # ユーザー情報を辞書形式に変換（テンプレート用）
    users_data = []
    for user in users:
        users_data.append({
            'id': user.id,
            'username': user.username,
            'is_admin': user.is_admin,
            'created_at': getattr(user, 'created_at', 'N/A'),
            'last_login': getattr(user, 'last_login', 'N/A')
        })

    return render_template('users/list.html', users=users_data)


@users_bp.route('/create', methods=['POST'])
@admin_required
def create_user():
    """新規ユーザー作成"""
    try:
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        is_admin = request.form.get('is_admin') == 'on'

        # バリデーション
        if not username or not password:
            flash('ユーザー名とパスワードは必須です。', 'danger')
            return redirect(url_for('users.user_list'))

        if len(username) < 3:
            flash('ユーザー名は3文字以上で入力してください。', 'danger')
            return redirect(url_for('users.user_list'))

        if len(password) < 6:
            flash('パスワードは6文字以上で入力してください。', 'danger')
            return redirect(url_for('users.user_list'))

        # 既存ユーザーチェック
        if user_store.get_user_by_username(username):
            flash(f'ユーザー名 "{username}" は既に使用されています。', 'danger')
            return redirect(url_for('users.user_list'))

        # ユーザー作成
        user = user_store.add_user(
            username=username,
            password=password,
            is_admin=is_admin
        )

        if user:
            flash(f'ユーザー "{username}" を作成しました。', 'success')
        else:
            flash('ユーザー作成に失敗しました。', 'danger')

    except Exception as e:
        flash(f'エラーが発生しました: {str(e)}', 'danger')

    return redirect(url_for('users.user_list'))


@users_bp.route('/<user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    """ユーザー削除"""
    try:
        # 自分自身は削除できない
        if user_id == current_user.id:
            flash('自分自身を削除することはできません。', 'danger')
            return redirect(url_for('users.user_list'))

        # ユーザー情報取得（ログ用）
        user = user_store.get_user_by_id(user_id)
        if not user:
            flash('ユーザーが見つかりません。', 'danger')
            return redirect(url_for('users.user_list'))

        username = user.username

        # 削除実行
        success = user_store.delete_user(user_id)

        if success:
            flash(f'ユーザー "{username}" を削除しました。', 'success')
        else:
            flash('ユーザー削除に失敗しました。', 'danger')

    except Exception as e:
        flash(f'エラーが発生しました: {str(e)}', 'danger')

    return redirect(url_for('users.user_list'))


@users_bp.route('/<user_id>/toggle-admin', methods=['POST'])
@admin_required
def toggle_admin(user_id):
    """管理者権限の切り替え"""
    try:
        # 自分自身の権限は変更できない
        if user_id == current_user.id:
            return jsonify({'success': False, 'message': '自分自身の権限は変更できません。'}), 400

        user = user_store.get_user_by_id(user_id)
        if not user:
            return jsonify({'success': False, 'message': 'ユーザーが見つかりません。'}), 404

        # 権限切り替え
        user.is_admin = not user.is_admin

        return jsonify({
            'success': True,
            'is_admin': user.is_admin,
            'message': f'{"管理者権限を付与しました" if user.is_admin else "管理者権限を削除しました"}'
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@users_bp.route('/api/stats')
@admin_required
def user_stats():
    """ユーザー統計情報API"""
import logging

logger = logging.getLogger(__name__)

    users = user_store.get_all_users()

logger = logging.getLogger(__name__)


    stats = {
        'total_users': len(users),
        'admin_users': sum(1 for u in users if u.is_admin),
        'regular_users': sum(1 for u in users if not u.is_admin)
    }

    return jsonify(stats)
