# ユーザー管理機能 統合手順書

## 概要
管理者専用のユーザー管理画面の統合手順を説明します。

## 実装済みファイル

### 1. `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/app/routes/users.py`
- ユーザー管理用Blueprintルート
- CRUD操作（作成・削除・権限切り替え）
- 管理者権限チェック
- API統計エンドポイント

### 2. `/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/templates/users/list.html`
- Bootstrap 5ベースのレスポンシブUI
- ユーザー一覧テーブル
- 新規作成モーダル
- 削除確認モーダル
- 管理者権限切り替え機能
- CSRF保護完備

## 統合作業

### ステップ1: UserStoreクラス拡張

`app/routes/auth.py` の `UserStore` クラスに以下のメソッドを追加:

```python
def get_all_users(self) -> list:
    """全ユーザーを取得"""
    return list(self._users.values())

def delete_user(self, user_id: str) -> bool:
    """ユーザーを削除"""
    if user_id in self._users:
        del self._users[user_id]
        return True
    return False

def get_user_count(self) -> int:
    """ユーザー数を取得"""
    return len(self._users)
```

**追加位置**: `get_user_by_username` メソッドの直後

### ステップ2: web_app.pyにBlueprint登録

`app/web_app.py` に以下を追加:

#### インポート追加
```python
from app.routes.users import users_bp
```

**追加位置**: `from app.routes.auth import auth_bp, login_manager` の直後

#### Blueprint登録
```python
app.register_blueprint(users_bp)
```

**追加位置**: `app.register_blueprint(auth_bp)` の直後

### ステップ3: base.htmlにナビゲーション追加

`templates/base.html` のナビゲーションメニューに管理者専用リンクを追加:

**変更前:**
```html
{% if current_user.is_authenticated %}
    <li class="nav-item">
        <a class="nav-link" href="{{ url_for('auth.logout') }}">
            <i class="bi bi-box-arrow-right"></i> ログアウト
        </a>
    </li>
{% else %}
    ...
{% endif %}
```

**変更後:**
```html
{% if current_user.is_authenticated %}
    {% if current_user.is_admin %}
    <li class="nav-item">
        <a class="nav-link" href="{{ url_for('users.user_list') }}">
            <i class="bi bi-people-fill"></i> ユーザー管理
        </a>
    </li>
    {% endif %}
    <li class="nav-item">
        <a class="nav-link" href="{{ url_for('auth.logout') }}">
            <i class="bi bi-box-arrow-right"></i> ログアウト
        </a>
    </li>
{% else %}
    ...
{% endif %}
```

## 動作確認

### 1. アプリケーション起動
```bash
python app/web_app.py
```

### 2. アクセス確認
- URL: `http://localhost:5000/users/`
- 管理者アカウントでログイン必須

### 3. 機能テスト

#### 3.1 ユーザー作成
1. 「新規ユーザー作成」ボタンをクリック
2. ユーザー名、パスワードを入力
3. 必要に応じて管理者権限にチェック
4. 「作成」ボタンをクリック

**検証項目:**
- [ ] ユーザー名は3文字以上（バリデーション）
- [ ] パスワードは6文字以上（バリデーション）
- [ ] 重複ユーザー名の拒否
- [ ] 成功時のフラッシュメッセージ表示

#### 3.2 権限切り替え
1. 対象ユーザーの「権限切り替え」ボタンをクリック
2. 確認ダイアログで承認

**検証項目:**
- [ ] 自分自身の権限は変更不可
- [ ] バッジ色の変更（管理者: 赤、一般: グレー）
- [ ] 成功メッセージ表示

#### 3.3 ユーザー削除
1. 対象ユーザーの「削除」ボタンをクリック
2. モーダルで削除確認
3. 「削除する」ボタンをクリック

**検証項目:**
- [ ] 自分自身は削除不可
- [ ] 削除確認モーダル表示
- [ ] テーブルからユーザーが削除される
- [ ] 統計カードの更新

#### 3.4 統計情報
- [ ] 総ユーザー数の正確性
- [ ] 管理者数のカウント
- [ ] 一般ユーザー数のカウント

## セキュリティチェックリスト

- [x] CSRF保護実装
- [x] 管理者権限チェック（@admin_required）
- [x] ログイン必須（@login_required）
- [x] 自己削除の防止
- [x] 自己権限変更の防止
- [x] パスワード長バリデーション（6文字以上）
- [x] ユーザー名バリデーション（3文字以上）
- [x] HTMLエスケープ（Jinja2自動）
- [x] XSS対策（CSP推奨）

## アクセシビリティ対応

- [x] ARIA属性設定
- [x] キーボードナビゲーション対応
- [x] スクリーンリーダー対応
- [x] 適切なセマンティックHTML
- [x] フォーカス管理
- [x] エラーメッセージの明確化

## トラブルシューティング

### Q1: 「この機能は管理者のみ使用できます」と表示される
**A:** 現在のユーザーが管理者権限を持っていません。管理者アカウントでログインしてください。

### Q2: モーダルが表示されない
**A:** Bootstrap 5のJavaScriptが正しく読み込まれているか確認してください。
```html
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
```

### Q3: CSRFトークンエラー
**A:** Flask-WTFのCSRF保護が有効か確認してください。
```python
app.config['WTF_CSRF_ENABLED'] = True
```

### Q4: 権限切り替えが反映されない
**A:** ブラウザのキャッシュをクリアしてページをリロードしてください。

## パフォーマンス最適化

### 推奨事項
1. **大量ユーザー対応**: ページネーション実装
2. **検索機能**: DataTablesなどのライブラリ導入
3. **非同期処理**: Ajaxによる部分更新
4. **キャッシュ**: Flask-Cachingでユーザー一覧をキャッシュ

### 実装例（ページネーション）
```python
from flask import request

@users_bp.route('/')
@admin_required
def user_list():
    page = request.args.get('page', 1, type=int)
    per_page = 20

    users = user_store.get_all_users()
    total = len(users)
    start = (page - 1) * per_page
    end = start + per_page

    paginated_users = users[start:end]

    return render_template('users/list.html',
                         users=paginated_users,
                         page=page,
                         total=total,
                         per_page=per_page)
```

## API仕様

### GET /users/
**権限**: 管理者のみ
**レスポンス**: HTML（ユーザー一覧ページ）

### POST /users/create
**権限**: 管理者のみ
**パラメータ**:
- `username` (string, required): ユーザー名（3文字以上）
- `password` (string, required): パスワード（6文字以上）
- `is_admin` (checkbox, optional): 管理者権限フラグ

**レスポンス**: リダイレクト（/users/）

### POST /users/<user_id>/delete
**権限**: 管理者のみ
**レスポンス**: リダイレクト（/users/）

### POST /users/<user_id>/toggle-admin
**権限**: 管理者のみ
**レスポンス**: JSON
```json
{
  "success": true,
  "is_admin": true,
  "message": "管理者権限を付与しました"
}
```

### GET /users/api/stats
**権限**: 管理者のみ
**レスポンス**: JSON
```json
{
  "total_users": 10,
  "admin_users": 2,
  "regular_users": 8
}
```

## 今後の拡張案

1. **ユーザー編集機能**: パスワード変更、プロフィール編集
2. **ロール管理**: 細かい権限設定（RBAC）
3. **監査ログ**: ユーザー操作履歴の記録
4. **メール通知**: アカウント作成時の通知
5. **2要素認証**: セキュリティ強化
6. **エクスポート**: CSV/Excel形式でユーザーリスト出力
7. **インポート**: 一括ユーザー登録
8. **パスワードリセット**: セキュアなパスワードリセット機能

## 関連ファイル

- `/app/routes/users.py` - ルート定義
- `/app/routes/auth.py` - UserStoreクラス（要拡張）
- `/templates/users/list.html` - UIテンプレート
- `/templates/base.html` - ナビゲーション（要更新）
- `/app/web_app.py` - Blueprint登録（要更新）

## まとめ

この実装により、以下が実現されます:

- ✅ 完全なユーザーCRUD操作
- ✅ セキュアな管理者権限管理
- ✅ モダンで使いやすいUI
- ✅ レスポンシブデザイン
- ✅ アクセシビリティ対応
- ✅ CSRF保護
- ✅ 適切なバリデーション

**次のステップ**: 上記の「統合作業」セクションの手順に従って、既存コードに統合してください。
