#!/bin/bash

# MangaAnime Web UI 自動起動設定インストールスクリプト

echo "=== MangaAnime Web UI 自動起動設定 ==="

# 現在のディレクトリを確認
if [ ! -f "web_app.py" ]; then
    echo "エラー: web_app.py が見つかりません。正しいディレクトリで実行してください。"
    exit 1
fi

# systemd サービスファイルをシステムディレクトリにコピー
echo "1. systemd サービスファイルをインストール中..."
sudo cp mangaanime-web.service /etc/systemd/system/

# systemd デーモンをリロード
echo "2. systemd デーモンをリロード中..."
sudo systemctl daemon-reload

# サービスを有効化（自動起動設定）
echo "3. サービスを有効化中..."
sudo systemctl enable mangaanime-web.service

# ファイアウォール設定（必要に応じて）
echo "4. ファイアウォール設定を確認中..."
if command -v ufw >/dev/null 2>&1; then
    if sudo ufw status | grep -q "Status: active"; then
        echo "   ファイアウォールでポート3030を許可中..."
        sudo ufw allow 3030
    fi
fi

# サービスを開始
echo "5. サービスを開始中..."
sudo systemctl start mangaanime-web.service

# ステータス確認
echo "6. サービスステータスを確認中..."
sudo systemctl status mangaanime-web.service --no-pager -l

echo ""
echo "=== インストール完了 ==="
echo "サービス名: mangaanime-web.service"
echo "アクセスURL: http://192.168.3.135:3030"
echo ""
echo "管理コマンド:"
echo "  サービス開始: sudo systemctl start mangaanime-web"
echo "  サービス停止: sudo systemctl stop mangaanime-web"
echo "  サービス再起動: sudo systemctl restart mangaanime-web"
echo "  サービス状態確認: sudo systemctl status mangaanime-web"
echo "  ログ確認: sudo journalctl -u mangaanime-web -f"
echo ""
echo "PC再起動後も自動でWebUIが起動します。"