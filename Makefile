# Makefile for MangaAnime-Info-delivery-system
# 作成日: 2025-12-06

.PHONY: help setup collect verify clean test

PROJECT_ROOT := /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system
PYTHON := python3
SCRIPTS_DIR := $(PROJECT_ROOT)/scripts

help:
	@echo "========================================="
	@echo "MangaAnime-Info-delivery-system Makefile"
	@echo "========================================="
	@echo ""
	@echo "利用可能なコマンド:"
	@echo "  make setup      - 初期セットアップ"
	@echo "  make collect    - データ収集実行"
	@echo "  make verify     - データ検証"
	@echo "  make full       - 収集→検証を一括実行"
	@echo "  make clean      - ログファイルクリーンアップ"
	@echo "  make test       - テスト実行"
	@echo "  make status     - 現在の状態確認"
	@echo ""

setup:
	@echo "初期セットアップを実行します..."
	@chmod +x $(SCRIPTS_DIR)/setup.sh
	@bash $(SCRIPTS_DIR)/setup.sh

collect:
	@echo "データ収集を開始します..."
	@chmod +x $(SCRIPTS_DIR)/collect_all_data.py
	@$(PYTHON) $(SCRIPTS_DIR)/collect_all_data.py

verify:
	@echo "データ検証を開始します..."
	@chmod +x $(SCRIPTS_DIR)/verify_data_collection.py
	@$(PYTHON) $(SCRIPTS_DIR)/verify_data_collection.py

full: collect verify
	@echo ""
	@echo "========================================="
	@echo "全処理完了"
	@echo "========================================="

status:
	@echo "現在のシステム状態を確認します..."
	@echo ""
	@echo "--- データベース状態 ---"
	@if [ -f "$(PROJECT_ROOT)/db.sqlite3" ]; then \
		sqlite3 $(PROJECT_ROOT)/db.sqlite3 "SELECT 'Works:', COUNT(*) FROM works UNION ALL SELECT 'Releases:', COUNT(*) FROM releases;"; \
	else \
		echo "データベースファイルが見つかりません"; \
	fi
	@echo ""
	@echo "--- 最新ログファイル ---"
	@ls -lht $(PROJECT_ROOT)/logs/ | head -5 || echo "ログディレクトリが見つかりません"

clean:
	@echo "ログファイルをクリーンアップします..."
	@find $(PROJECT_ROOT)/logs -name "*.log" -mtime +7 -delete 2>/dev/null || true
	@echo "✓ 7日以上前のログファイルを削除しました"

test:
	@echo "テストを実行します..."
	@if [ -d "$(PROJECT_ROOT)/tests" ]; then \
		$(PYTHON) -m pytest $(PROJECT_ROOT)/tests -v; \
	else \
		echo "testsディレクトリが見つかりません"; \
	fi

# dry-run用コマンド
dry-run:
	@echo "DRY-RUN モードでデータ収集を実行します..."
	@echo "（実際のDB更新は行いません）"
	@# TODO: dry-runオプションを各モジュールに追加

# 開発用コマンド
dev-setup:
	@echo "開発環境セットアップ..."
	@pip install -r requirements.txt 2>/dev/null || echo "requirements.txtが見つかりません"
	@echo "✓ 開発環境セットアップ完了"

# データベースバックアップ
backup-db:
	@echo "データベースをバックアップします..."
	@mkdir -p $(PROJECT_ROOT)/backups
	@cp $(PROJECT_ROOT)/db.sqlite3 $(PROJECT_ROOT)/backups/db_backup_$(shell date +%Y%m%d_%H%M%S).sqlite3
	@echo "✓ バックアップ完了: $(PROJECT_ROOT)/backups/"

# データベースリストア
restore-db:
	@echo "利用可能なバックアップ:"
	@ls -lht $(PROJECT_ROOT)/backups/db_backup_*.sqlite3 | head -5
	@echo ""
	@echo "リストアするには: cp backups/[ファイル名] db.sqlite3"

.DEFAULT_GOAL := help
