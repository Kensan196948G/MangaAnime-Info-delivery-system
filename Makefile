# アニメ・マンガ情報配信システム - Makefile

.PHONY: help setup install test run clean web lint security format docs

# デフォルトのPythonコマンド
PYTHON := python3
PIP := pip3

# プロジェクトの情報
PROJECT_NAME := MangaAnime情報配信システム
VERSION := 1.0.0

# ヘルプメッセージ
help:
	@echo "🎬 $(PROJECT_NAME) v$(VERSION)"
	@echo ""
	@echo "利用可能なコマンド:"
	@echo "  setup          システムのセットアップ"
	@echo "  install        依存関係のインストール"
	@echo "  test           テストの実行"
	@echo "  run            システムの実行"
	@echo "  run-dry        ドライラン実行"
	@echo "  web            Web UI の起動"
	@echo "  lint           コード品質チェック"
	@echo "  security       セキュリティチェック"
	@echo "  format         コードフォーマット"
	@echo "  clean          一時ファイルの削除"
	@echo "  docs           ドキュメント生成"
	@echo ""
	@echo "使用例:"
	@echo "  make setup     # 初回セットアップ"
	@echo "  make run-dry   # テスト実行"
	@echo "  make test      # 全テスト実行"

# システムのセットアップ
setup:
	@echo "🚀 システムセットアップを開始します..."
	$(PYTHON) setup_system.py --full-setup --test-run

# 依存関係のインストール
install:
	@echo "📦 依存関係をインストールしています..."
	$(PIP) install -r requirements.txt

# 開発用依存関係のインストール
install-dev:
	@echo "📦 開発用依存関係をインストールしています..."
	$(PIP) install -r requirements-dev.txt

# テストの実行
test:
	@echo "🧪 テストスイートを実行しています..."
	$(PYTHON) -m pytest tests/ -v --cov=modules --cov-report=term-missing

# テスト（カバレッジレポートHTML付き）
test-html:
	@echo "🧪 テスト（HTMLレポート付き）を実行しています..."
	$(PYTHON) -m pytest tests/ -v --cov=modules --cov-report=html
	@echo "カバレッジレポート: htmlcov/index.html"

# システムの実行
run:
	@echo "🎬 システムを実行しています..."
	$(PYTHON) release_notifier.py

# ドライラン実行
run-dry:
	@echo "🔒 ドライラン（テストモード）で実行しています..."
	$(PYTHON) release_notifier.py --dry-run --verbose

# 詳細ログ付き実行
run-verbose:
	@echo "🔍 詳細ログ付きでシステムを実行しています..."
	$(PYTHON) release_notifier.py --verbose

# Web UI の起動
web:
	@echo "🌐 Web UI を起動しています..."
	$(PYTHON) start_web_ui.py --debug

# Web UI（本番モード）の起動
web-prod:
	@echo "🌐 Web UI（本番モード）を起動しています..."
	$(PYTHON) start_web_ui.py --host 0.0.0.0 --port 5000

# コード品質チェック
lint:
	@echo "🔍 コード品質をチェックしています..."
	$(PYTHON) -m flake8 modules/ tests/ --max-line-length=100 --ignore=E203,W503
	$(PYTHON) -m mypy modules/ --ignore-missing-imports

# セキュリティチェック
security:
	@echo "🔐 セキュリティチェックを実行しています..."
	$(PYTHON) security_qa_cli.py --mode security --verbose

# 品質保証チェック
qa:
	@echo "✅ 品質保証チェックを実行しています..."
	$(PYTHON) security_qa_cli.py --mode qa --verbose

# 統合チェック（セキュリティ + QA）
audit:
	@echo "🔍 統合監査を実行しています..."
	$(PYTHON) security_qa_cli.py --mode full --output ./reports

# コードフォーマット
format:
	@echo "🎨 コードをフォーマットしています..."
	$(PYTHON) -m black modules/ tests/ *.py --line-length=100
	$(PYTHON) -m isort modules/ tests/ *.py --profile black

# データベースの初期化
init-db:
	@echo "💾 データベースを初期化しています..."
	rm -f db.sqlite3
	$(PYTHON) -c "from modules.db import DatabaseManager; DatabaseManager('./db.sqlite3')"

# ログの表示
logs:
	@echo "📋 最新のログを表示しています..."
	tail -f logs/app.log

# ログのクリア
clear-logs:
	@echo "🧹 ログファイルをクリアしています..."
	rm -f logs/*.log

# 一時ファイルの削除
clean:
	@echo "🧹 一時ファイルを削除しています..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf *.egg-info/
	rm -rf build/
	rm -rf dist/

# バックアップの作成
backup:
	@echo "💾 システムバックアップを作成しています..."
	mkdir -p backups
	tar -czf backups/backup_$(shell date +%Y%m%d_%H%M%S).tar.gz \
		--exclude=backups \
		--exclude=logs \
		--exclude=__pycache__ \
		--exclude=*.pyc \
		--exclude=.git \
		.

# 設定の検証
validate-config:
	@echo "⚙️ 設定ファイルを検証しています..."
	$(PYTHON) -c "from modules.config import get_config; config = get_config(); print('設定OK' if not config.validate_config() else '設定に問題があります')"

# 統計情報の表示
stats:
	@echo "📊 システム統計情報:"
	@echo "作品数: $$($(PYTHON) -c 'from modules.db import DatabaseManager; db = DatabaseManager("./db.sqlite3"); print(db.get_work_stats().get("total", 0))')"
	@echo "リリース数: $$($(PYTHON) -c 'from modules.db import DatabaseManager; db = DatabaseManager("./db.sqlite3"); print(db.get_work_stats().get("total_releases", 0))')"
	@echo "未通知数: $$($(PYTHON) -c 'from modules.db import DatabaseManager; db = DatabaseManager("./db.sqlite3"); print(len(db.get_unnotified_releases(1000)))')"

# cron設定のインストール
install-cron:
	@echo "📅 cron設定をインストールしています..."
	crontab crontab.example
	@echo "✅ cron設定がインストールされました"

# cron設定の確認
check-cron:
	@echo "📅 現在のcron設定:"
	crontab -l

# デモデータの生成
demo-data:
	@echo "🎲 デモデータを生成しています..."
	$(PYTHON) init_demo_db.py

# システムヘルスチェック
health:
	@echo "🏥 システムヘルスチェックを実行しています..."
	@echo "Python: $$($(PYTHON) --version)"
	@echo "データベース: $$(if [ -f db.sqlite3 ]; then echo '✅ 存在'; else echo '❌ なし'; fi)"
	@echo "設定ファイル: $$(if [ -f config.json ]; then echo '✅ 存在'; else echo '❌ なし'; fi)"
	@echo "認証情報: $$(if [ -f credentials.json ]; then echo '✅ 存在'; else echo '❌ なし'; fi)"
	@echo "ログディレクトリ: $$(if [ -d logs ]; then echo '✅ 存在'; else echo '❌ なし'; fi)"

# パフォーマンステスト
perf-test:
	@echo "⚡ パフォーマンステストを実行しています..."
	$(PYTHON) -m pytest tests/test_performance.py -v

# デプロイメント用ビルド
build:
	@echo "📦 デプロイメント用パッケージを構築しています..."
	mkdir -p dist
	tar -czf dist/manga-anime-system-$(VERSION).tar.gz \
		--exclude=dist \
		--exclude=tests \
		--exclude=__pycache__ \
		--exclude=*.pyc \
		--exclude=.git \
		--exclude=logs \
		--exclude=backups \
		.
	@echo "✅ パッケージが作成されました: dist/manga-anime-system-$(VERSION).tar.gz"

# 全体の品質チェック
quality-check: lint security test
	@echo "✅ 全体的な品質チェックが完了しました"

# 開発環境の初期化
dev-setup: install-dev init-db demo-data
	@echo "🛠️ 開発環境のセットアップが完了しました"

# 本番環境の準備
prod-setup: install validate-config
	@echo "🚀 本番環境の準備が完了しました"