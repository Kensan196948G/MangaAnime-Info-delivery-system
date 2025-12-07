# Google API認証 クイックリファレンス

## 最速セットアップ（3ステップ）

### 1. credentials.jsonを取得

```bash
# Google Cloud Console (https://console.cloud.google.com/) で:
# - プロジェクト作成
# - Calendar API & Gmail API 有効化
# - OAuth 2.0クライアントID（デスクトップアプリ）作成
# - credentials.json ダウンロード
```

### 2. ファイルを配置

```bash
mv ~/Downloads/credentials.json /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/
```

### 3. セットアップ実行

```bash
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system
bash scripts/setup_google_auth.sh
```

---

## トラブルシューティング早見表

| エラー | 原因 | 解決方法 |
|--------|------|----------|
| `credentials.json not found` | ファイルが配置されていない | Step 1-2を実行 |
| `access_denied` | テストユーザーに未登録 | Cloud Consoleでテストユーザー追加 |
| `invalid_grant` | トークン期限切れ | `rm token.json` して再実行 |
| `ModuleNotFoundError` | パッケージ未インストール | `pip install -r requirements.txt` |

---

## よく使うコマンド

```bash
# 認証テスト
python3 scripts/test_google_apis.py

# 認証情報リセット
rm token.json
python3 scripts/test_google_apis.py

# モジュール単体テスト
python3 modules/auth_helper.py

# 自動セットアップ
bash scripts/setup_google_auth.sh
```

---

## セキュリティチェック

```bash
# Gitステータス確認（credentials.jsonがステージングされていないこと）
git status

# .gitignore確認
grep -E "credentials|token" .gitignore

# ファイル権限確認（600推奨）
ls -la credentials.json token.json
```

---

## ファイル一覧

| ファイル | 説明 | Gitコミット |
|----------|------|-------------|
| `credentials.json` | OAuth 2.0クライアントシークレット | ❌ 絶対NG |
| `token.json` | アクセストークン | ❌ 絶対NG |
| `credentials.json.sample` | サンプルファイル | ✅ OK |

---

## APIスコープ

### Calendar API
```python
['https://www.googleapis.com/auth/calendar']
```

### Gmail API
```python
[
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.compose'
]
```

---

## 詳細ドキュメント

- **完全ガイド**: [GOOGLE_API_SETUP.md](GOOGLE_API_SETUP.md)
- **チェックリスト**: [CREDENTIALS_SETUP_CHECKLIST.md](CREDENTIALS_SETUP_CHECKLIST.md)
- **クイックスタート**: [../README_GOOGLE_AUTH.md](../README_GOOGLE_AUTH.md)

---

**最終更新**: 2025-12-07
