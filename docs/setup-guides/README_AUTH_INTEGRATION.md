# 認証統合 - クイックスタート

## 実行方法

```bash
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system

# 方法1: シェルスクリプトで実行（推奨）
chmod +x run_and_verify.sh
./run_and_verify.sh

# 方法2: Pythonスクリプトを直接実行
python3 final_integration.py
```

## 統合内容

1. **app/routes/__init__.py** - 認証モジュールのエクスポート
2. **app/web_app.py** - 認証機構の統合とルート保護
3. **templates/base.html** - ログイン状態表示の追加

## 保護されるルート

- `/settings` - 設定画面
- `/api/settings/update` - 設定更新
- `/api/clear-history` - 履歴削除
- `/api/delete-work/<id>` - 作品削除

## テスト

```bash
# アプリ起動
python3 app/web_app.py

# ブラウザでアクセス
# 1. http://localhost:5000/auth/register - ユーザー登録
# 2. http://localhost:5000/auth/login - ログイン
# 3. http://localhost:5000/settings - 保護ルートのテスト
```

## バックアップ

統合実行時に自動バックアップが作成されます:
```
backups/auth_integration_YYYYMMDD_HHMMSS/
```

復元が必要な場合:
```bash
cp backups/auth_integration_*/web_app.py.bak app/web_app.py
cp backups/auth_integration_*/base.html.bak templates/base.html
```

## 詳細ドキュメント

完全なドキュメントは以下を参照:
- `AUTHENTICATION_INTEGRATION_COMPLETE.md` - 詳細レポート
- `RUN_INTEGRATION.md` - 実行手順とトラブルシューティング
