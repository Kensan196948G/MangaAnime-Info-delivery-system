#!/bin/bash
# GitHub Actions ワークフロー修正スクリプト

echo "🔧 GitHub Actions ワークフロー修正を開始します..."

# 必要なディレクトリの作成
echo "📁 必要なディレクトリを作成中..."
mkdir -p config
mkdir -p logs
mkdir -p backup
mkdir -p tests
mkdir -p dist

# config.jsonがない場合は作成
if [ ! -f config.json ]; then
    echo "⚠️  config.json が見つかりません。CI用設定から作成します..."
    if [ -f config/config.ci.json ]; then
        cp config/config.ci.json config.json
        echo "✅ config.json を作成しました"
    elif [ -f config.json.template ]; then
        cp config.json.template config.json
        # テンプレート値を置換
        sed -i 's/"your-email@gmail.com"/"test@example.com"/g' config.json
        echo "✅ config.json をテンプレートから作成しました"
    else
        # 最小限のconfig.jsonを作成
        cat > config.json << 'EOF'
{
  "ng_keywords": ["test"],
  "notification_email": "test@example.com",
  "email": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "test@example.com",
    "sender_password": "${GMAIL_APP_PASSWORD}",
    "use_tls": true,
    "enabled": false
  },
  "error_notifications": {
    "enabled": false,
    "recipient_email": "test@example.com",
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "test@example.com",
    "sender_password": "${GMAIL_APP_PASSWORD}",
    "use_tls": true
  },
  "apis": {
    "anilist": {
      "graphql_url": "https://graphql.anilist.co"
    }
  },
  "notifications": {
    "anime": true,
    "manga": true
  },
  "database": {
    "path": "./test.db"
  },
  "system": {
    "name": "Test System"
  }
}
EOF
        echo "✅ 最小限のconfig.jsonを作成しました"
    fi
fi

# backup_full.shがない場合は作成
if [ ! -f backup_full.sh ]; then
    echo "⚠️  backup_full.sh が見つかりません。作成します..."
    cat > backup_full.sh << 'EOF'
#!/bin/bash
# MangaAnime システムバックアップスクリプト

SOURCE_DIR="."
BACKUP_DIR="./backup"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="backup_${TIMESTAMP}"

log_message() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

log_message "バックアップを開始します..."

# バックアップディレクトリの作成
mkdir -p "${BACKUP_DIR}"

# rsyncでバックアップ実行
if command -v rsync >/dev/null 2>&1; then
    rsync -av --exclude='.git' --exclude='venv' --exclude='__pycache__' \
          --exclude='backup' --exclude='*.pyc' --exclude='test.db' \
          "${SOURCE_DIR}/" "${BACKUP_DIR}/${BACKUP_NAME}/"
    log_message "バックアップが完了しました: ${BACKUP_DIR}/${BACKUP_NAME}"
else
    log_message "rsyncが利用できません。tarを使用します..."
    tar -czf "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" \
        --exclude='.git' --exclude='venv' --exclude='__pycache__' \
        --exclude='backup' --exclude='*.pyc' --exclude='test.db' \
        .
    log_message "バックアップが完了しました: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
fi

log_message "バックアップ処理が完了しました"
EOF
    chmod +x backup_full.sh
    echo "✅ backup_full.sh を作成しました"
fi

# .gitkeepファイルの作成
touch backup/.gitkeep
touch logs/.gitkeep
touch dist/.gitkeep

echo "✅ ワークフロー修正の準備が完了しました"

# Pythonファイルのシンタックスチェック
echo "🐍 Pythonファイルのシンタックスをチェック中..."
for py_file in $(find . -name "*.py" -not -path "./venv/*" -not -path "./.git/*"); do
    python -m py_compile "$py_file" 2>/dev/null || echo "⚠️  構文エラー: $py_file"
done

echo "✅ 修正スクリプトの実行が完了しました"