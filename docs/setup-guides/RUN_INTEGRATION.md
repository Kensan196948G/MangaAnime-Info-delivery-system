# 認証機構統合 - 実行手順

## 概要
このドキュメントは、認証機構をメインアプリケーションに統合するプロセスを説明します。

## 実行コマンド

```bash
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system
chmod +x integrate_auth_complete.sh
./integrate_auth_complete.sh
```

## 統合内容

### 1. app/routes/__init__.py
- 認証Blueprintとinit_login_managerをエクスポート
- 新規作成または既存ファイルに追加

### 2. app/web_app.py
以下の変更を実施:
- `flask_login` からのインポート追加
- `app.routes.auth` からのインポート追加
- `SECRET_KEY` 設定
- `init_login_manager(app)` 呼び出し
- `auth_bp` Blueprint登録
- 保護が必要なルートに `@login_required` デコレータ追加:
  - `/settings`
  - `/api/settings/update`
  - `/api/clear-history`
  - `/api/delete-work/<int:work_id>`

### 3. templates/base.html
- ナビゲーションバーにログイン状態表示を追加
- ログイン済み: ユーザー名とドロップダウンメニュー
- 未ログイン: ログイン/登録リンク

## バックアップ
統合実行時に自動的にバックアップが作成されます:
- `backups/auth_integration_YYYYMMDD_HHMMSS/`

## 検証手順

### 1. アプリケーション起動
```bash
python3 app/web_app.py
```

### 2. ユーザー登録
```
http://localhost:5000/auth/register
```

### 3. ログイン
```
http://localhost:5000/auth/login
```

### 4. 保護されたルートへのアクセステスト
- ログイン前: `/settings` にアクセス → ログインページにリダイレクト
- ログイン後: `/settings` にアクセス → 正常に表示

## トラブルシューティング

### インポートエラーが発生する場合
```bash
# Flask-Login がインストールされているか確認
pip3 show Flask-Login

# インストールされていない場合
pip3 install Flask-Login
```

### データベースエラーが発生する場合
```bash
# users テーブルが作成されているか確認
sqlite3 db.sqlite3 ".schema users"

# テーブルが存在しない場合、認証モジュールを初期化
python3 -c "from app.routes.auth import init_db; init_db()"
```

### バックアップから復元する場合
```bash
# 最新のバックアップを確認
ls -la backups/auth_integration_*/

# 復元（例）
cp backups/auth_integration_20250101_120000/web_app.py.bak app/web_app.py
cp backups/auth_integration_20250101_120000/base.html.bak templates/base.html
```

## 確認事項

統合後、以下を確認してください:

- [ ] アプリケーションが正常に起動する
- [ ] `/auth/register` でユーザー登録できる
- [ ] `/auth/login` でログインできる
- [ ] ログイン状態がナビゲーションバーに表示される
- [ ] `/settings` などの保護ルートがログイン必須になっている
- [ ] ログアウトが正常に機能する

## 次のステップ

1. **セキュリティ設定の確認**
   - 本番環境では `SECRET_KEY` を環境変数で設定
   - HTTPS の有効化を検討

2. **権限管理の追加**
   - 管理者権限の実装
   - ユーザーごとのアクセス制御

3. **セッション管理の最適化**
   - セッションタイムアウトの設定
   - Remember Me 機能の実装

4. **監査ログの実装**
   - ログインログの記録
   - 重要な操作の監査ログ
