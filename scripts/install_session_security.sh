#!/bin/bash

# セッションセキュリティ強化セットアップスクリプト
# MangaAnime-Info-delivery-system

set -e

echo "========================================"
echo "セッションセキュリティ強化セットアップ"
echo "========================================"
echo ""

# プロジェクトルート取得
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "📁 プロジェクトルート: $PROJECT_ROOT"
echo ""

# 1. Flask-Session インストール
echo "📦 Flask-Session をインストール中..."
pip install Flask-Session>=0.5.0
echo "✅ Flask-Session インストール完了"
echo ""

# 2. redis-py インストール（オプション）
read -p "📦 Redis（本番環境用）もインストールしますか？ (y/N): " install_redis
if [[ "$install_redis" =~ ^[Yy]$ ]]; then
    echo "📦 redis-py をインストール中..."
    pip install redis>=5.0.0
    echo "✅ redis-py インストール完了"
else
    echo "⏭️  Redis のインストールをスキップしました"
fi
echo ""

# 3. セッションディレクトリ作成
echo "📁 セッションディレクトリを作成中..."
mkdir -p flask_session
echo "✅ flask_session/ ディレクトリ作成完了"
echo ""

# 4. .gitignore 更新
echo "📝 .gitignore を更新中..."
if [ -f .gitignore ]; then
    # flask_session/ がまだ追加されていない場合のみ追加
    if ! grep -q "flask_session/" .gitignore; then
        cat .gitignore.session >> .gitignore
        echo "✅ .gitignore に flask_session/ を追加しました"
    else
        echo "ℹ️  .gitignore にはすでに flask_session/ が含まれています"
    fi
else
    cp .gitignore.session .gitignore
    echo "✅ .gitignore を作成しました"
fi
echo ""

# 5. 環境変数チェック
echo "🔍 環境変数をチェック中..."
if [ -z "$SECRET_KEY" ]; then
    echo "⚠️  WARNING: SECRET_KEY が設定されていません"
    echo "   本番環境では必ず設定してください:"
    echo "   export SECRET_KEY='your-secret-key-here'"
else
    echo "✅ SECRET_KEY が設定されています"
fi

if [ -z "$FLASK_ENV" ]; then
    echo "ℹ️  FLASK_ENV が未設定です（デフォルト: development）"
    echo "   本番環境では設定してください:"
    echo "   export FLASK_ENV=production"
else
    echo "✅ FLASK_ENV=$FLASK_ENV"
fi
echo ""

# 6. テスト実行
echo "🧪 セキュリティ設定のテストを実行しますか？"
read -p "   (y/N): " run_tests
if [[ "$run_tests" =~ ^[Yy]$ ]]; then
    echo "🧪 テスト実行中..."
    python -m pytest tests/test_session_security.py -v
    echo "✅ テスト完了"
else
    echo "⏭️  テストをスキップしました"
fi
echo ""

# 7. 完了メッセージ
echo "========================================"
echo "✅ セッションセキュリティ強化完了！"
echo "========================================"
echo ""
echo "次のステップ:"
echo "1. 環境変数を設定してください:"
echo "   export SECRET_KEY='your-secret-key-here'"
echo "   export FLASK_ENV=development  # または production"
echo ""
echo "2. アプリケーションを起動してください:"
echo "   python app/web_app.py"
echo ""
echo "3. セキュリティ設定を確認してください:"
echo "   詳細: docs/SESSION_SECURITY_SETUP.md"
echo ""
echo "📚 ドキュメント:"
echo "   - セットアップガイド: docs/SESSION_SECURITY_SETUP.md"
echo "   - セキュリティ設定: app/utils/security.py"
echo ""
