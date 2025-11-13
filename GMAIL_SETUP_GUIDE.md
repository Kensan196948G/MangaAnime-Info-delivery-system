# Gmail App Password 設定ガイド

## 📧 Gmail通知機能を有効にする手順

### ステップ1: Googleアカウントの2段階認証を有効化

1. [Googleアカウント設定](https://myaccount.google.com/security)にアクセス
2. 「2段階認証プロセス」をクリック
3. 画面の指示に従って2段階認証を設定

### ステップ2: アプリパスワードの生成

1. [アプリパスワード](https://myaccount.google.com/apppasswords)にアクセス
2. 「アプリを選択」で「メール」を選択
3. 「デバイスを選択」で「その他（カスタム名）」を選択
4. 「MangaAnime-Info-System」など識別しやすい名前を入力
5. 「生成」をクリック
6. 表示された16文字のパスワードをコピー（スペースは不要）

### ステップ3: パスワードファイルの作成

```bash
# パスワードファイルを作成（xxxの部分を実際のパスワードに置き換え）
echo 'xxxxxxxxxxxxxxxx' > gmail_app_password.txt

# ファイル権限を設定（セキュリティのため）
chmod 600 gmail_app_password.txt
```

### ステップ4: 設定確認

```bash
# テストスクリプトを実行
venv/bin/python test_email_delivery.py
```

### ステップ5: 実際の送信テスト

```bash
# ドライランで動作確認
venv/bin/python release_notifier.py --dry-run

# 実際に送信（強制送信）
venv/bin/python release_notifier.py --force-send
```

## ⚠️ 注意事項

- アプリパスワードは**通常のGoogleパスワードとは異なります**
- 16文字の専用パスワードです（スペースなし）
- 一度生成したパスワードは再表示されません
- 紛失した場合は新しいパスワードを生成してください

## 🔒 セキュリティ

- `gmail_app_password.txt`は絶対にGitにコミットしないでください
- ファイル権限は必ず`600`に設定してください
- `.gitignore`に含まれていることを確認してください

## トラブルシューティング

### エラー: 認証失敗
- アプリパスワードが正しくコピーされているか確認
- スペースが含まれていないか確認
- 2段階認証が有効になっているか確認

### エラー: ファイルが見つからない
```bash
# ファイルの存在確認
ls -la gmail_app_password.txt

# 権限確認
stat gmail_app_password.txt
```

### エラー: SMTP接続エラー
- ファイアウォール設定を確認
- ポート587が開いているか確認
- インターネット接続を確認

## サポート

問題が解決しない場合は、以下を確認してください：
- システムログ: `logs/app.log`
- エラーログ: `logs/error.log`
- テストスクリプト: `test_email_delivery.py`