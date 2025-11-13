#!/bin/bash
# MangaAnime Info Delivery System 環境変数設定スクリプト

echo "🔧 環境変数を設定します..."

# Gmail設定
read -p "Gmail送信者アドレスを入力してください [kensan1969@gmail.com]: " GMAIL_SENDER
GMAIL_SENDER=${GMAIL_SENDER:-kensan1969@gmail.com}

read -p "Gmail受信者アドレスを入力してください（カンマ区切りで複数可） [kensan1969@gmail.com]: " GMAIL_RECIPIENTS
GMAIL_RECIPIENTS=${GMAIL_RECIPIENTS:-kensan1969@gmail.com}

# 環境変数をエクスポート
export GMAIL_SENDER="$GMAIL_SENDER"
export GMAIL_RECIPIENTS="$GMAIL_RECIPIENTS"

# .envファイルに保存
cat > .env << EOF
GMAIL_SENDER=$GMAIL_SENDER
GMAIL_RECIPIENTS=$GMAIL_RECIPIENTS
EOF

echo "✅ 環境変数が設定されました"
echo "✅ .envファイルに保存されました"
echo ""
echo "以下のコマンドで環境変数を読み込めます:"
echo "source .env"
