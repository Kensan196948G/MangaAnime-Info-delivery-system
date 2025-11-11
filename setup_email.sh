#!/bin/bash
# Gmail設定用スクリプト

echo "📧 MangaAnime メール設定ウィザード"
echo "=================================="
echo ""
echo "Gmail App Passwordを設定します"
echo ""
echo "1. まず以下のURLでアプリパスワードを生成してください:"
echo "   https://myaccount.google.com/apppasswords"
echo ""
echo "2. 生成された16文字のパスワードを入力してください"
echo "   (スペースは自動的に削除されます)"
echo ""
read -p "App Password: " APP_PASSWORD

# スペースを削除
APP_PASSWORD="${APP_PASSWORD// /}"

# .envファイルに保存
echo "GMAIL_APP_PASSWORD=$APP_PASSWORD" > .env
echo "GMAIL_SENDER_EMAIL=kensan1969@gmail.com" >> .env
echo "GMAIL_RECIPIENT_EMAIL=kensan1969@gmail.com" >> .env

echo ""
echo "✅ 設定を保存しました"
echo ""
echo "テストメールを送信しますか？ (y/n)"
read -p "> " SEND_TEST

if [ "$SEND_TEST" = "y" ]; then
    python scripts/test_email.py
fi
