# フォルダ構造整理 - クイックスタートガイド

## はじめに

このガイドは、MangaAnime-Info-delivery-systemのルートディレクトリに散在する115個のファイルを、論理的なフォルダ構造に整理するための手順を説明します。

**所要時間**: 30-60分（自動化スクリプト使用時）
**難易度**: 中級
**リスク**: 中（バックアップと段階的移行で軽減）

---

## クイックスタート（5ステップ）

### ステップ1: バックアップ（3分）

```bash
# プロジェクトルートへ移動
cd D:\MangaAnime-Info-delivery-system

# 完全バックアップ
bash backup_full.sh

# Gitコミット
git add -A
git commit -m "[バックアップ] フォルダ構造整理前のスナップショット"

# 作業ブランチ作成
git checkout -b refactor/folder-structure
```

### ステップ2: 新しいディレクトリ構造作成（1分）

```bash
bash scripts/create_new_structure.sh
```

**出力例**:
```
=========================================
Creating new directory structure...
=========================================
[CREATED] app
[CREATED] auth/token_generators
[CREATED] scripts/startup
...
Directory structure created successfully!
```

### ステップ3: ファイル移動（DRY-RUNで確認）（5分）

```bash
# まずDRY-RUNで確認
bash scripts/migrate_files.sh --phase all --dry-run
```

問題なければ実行:

```bash
# 実際に移動
bash scripts/migrate_files.sh --phase all
```

または、段階的に実行:

```bash
bash scripts/migrate_files.sh --phase 1  # アプリケーション
bash scripts/migrate_files.sh --phase 2  # 認証
bash scripts/migrate_files.sh --phase 3  # テスト
bash scripts/migrate_files.sh --phase 4  # ツール
bash scripts/migrate_files.sh --phase 5  # スクリプト
bash scripts/migrate_files.sh --phase 6  # データ・設定
```

### ステップ4: インポートパス自動修正（5分）

```bash
# DRY-RUNで確認
python3 tools/setup/fix_import_paths.py --dry-run

# 実際に修正
python3 tools/setup/fix_import_paths.py
```

### ステップ5: 検証（10分）

```bash
# テスト実行
pytest tests/ -v

# システム検証
python3 tools/validation/validate_system.py

# Web UI起動確認
python3 app/web_app.py
# ブラウザで http://localhost:5000 にアクセス

# リリース通知テスト
python3 app/release_notifier.py --dry-run
```

---

## 詳細な手順

### 事前準備

#### 必要なツール
- Git
- Python 3.8+
- bash（WSL、Git Bash、または Linux環境）

#### 環境確認
```bash
git --version
python3 --version
bash --version
```

### フェーズ別実行（推奨）

各フェーズを個別に実行することで、問題が発生した際の影響範囲を最小化できます。

#### フェーズ1: メインアプリケーション

```bash
# 移動前のテスト
pytest tests/ -v > output/before_phase1.txt

# 移動実行
bash scripts/migrate_files.sh --phase 1

# インポートパス修正
python3 tools/setup/fix_import_paths.py

# 移動後のテスト
pytest tests/ -v > output/after_phase1.txt

# 差分確認
diff output/before_phase1.txt output/after_phase1.txt
```

問題なければ次のフェーズへ進みます。

#### フェーズ2: 認証関連

```bash
bash scripts/migrate_files.sh --phase 2
python3 tools/setup/fix_import_paths.py
pytest tests/integration/test_gmail_auth.py -v
```

#### フェーズ3: テスト関連

```bash
bash scripts/migrate_files.sh --phase 3
python3 tools/setup/fix_import_paths.py
pytest tests/ -v
```

#### フェーズ4: ツール類

```bash
bash scripts/migrate_files.sh --phase 4
python3 tools/setup/fix_import_paths.py
python3 tools/validation/validate_system.py
```

#### フェーズ5: スクリプト

```bash
bash scripts/migrate_files.sh --phase 5
# スクリプト実行確認
bash scripts/startup/quick_start.sh --help
```

#### フェーズ6: データ・設定

```bash
# データベースバックアップ（重要！）
cp db.sqlite3 db.sqlite3.backup.$(date +%Y%m%d_%H%M%S)

bash scripts/migrate_files.sh --phase 6

# データベース確認
sqlite3 data/db.sqlite3 "SELECT COUNT(*) FROM works;"
```

---

## トラブルシューティング

### 問題1: インポートエラー

**症状**:
```
ModuleNotFoundError: No module named 'modules'
```

**解決策**:
```bash
# インポートパス修正スクリプトを再実行
python3 tools/setup/fix_import_paths.py

# または、手動で修正
# ファイルの先頭に以下を追加:
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
```

### 問題2: テスト失敗

**症状**:
```
pytest tests/ -v
# 複数のテストが失敗
```

**解決策**:
```bash
# pytest.ini のパス設定を確認
cat pytest.ini

# テストディレクトリ構造を確認
tree tests/

# 個別テストを実行して原因特定
pytest tests/unit/test_filtering.py -v
```

### 問題3: データベースアクセスエラー

**症状**:
```
sqlite3.OperationalError: unable to open database file
```

**解決策**:
```bash
# 設定ファイルのパスを修正
# config/config.json
{
  "database_path": "../data/db.sqlite3"
}

# または環境変数で上書き
export DATABASE_PATH=./data/db.sqlite3
python3 app/web_app.py
```

### 問題4: シェルスクリプトのパスエラー

**症状**:
```bash
bash scripts/startup/quick_start.sh
# python3: can't open file 'web_app.py': [Errno 2] No such file or directory
```

**解決策**:
スクリプト内のパスを修正:
```bash
# scripts/startup/quick_start.sh
#!/bin/bash
cd "$(dirname "$0")/../.."  # プロジェクトルートへ移動
python3 app/web_app.py
```

---

## ロールバック手順

問題が解決できない場合は、ロールバックできます:

```bash
# 作業ブランチを破棄
git checkout main
git branch -D refactor/folder-structure

# または、バックアップから復元
bash backup/restore_latest.sh
```

---

## 検証チェックリスト

整理完了後、以下を確認してください:

### 基本動作

- [ ] Web UI起動（`python3 app/web_app.py`）
- [ ] リリース通知実行（`python3 app/release_notifier.py --dry-run`）
- [ ] ダッシュボード起動（`python3 app/dashboard_main.py`）

### テスト

- [ ] ユニットテスト（`pytest tests/unit/ -v`）
- [ ] 統合テスト（`pytest tests/integration/ -v`）
- [ ] E2Eテスト（`pytest tests/e2e/ -v`）
- [ ] 全テスト（`pytest tests/ -v`）

### ツール

- [ ] システム検証（`python3 tools/validation/validate_system.py`）
- [ ] 構造チェック（`python3 tools/monitoring/check_structure.py`）
- [ ] パフォーマンステスト（`python3 tools/monitoring/performance_benchmark.py`）

### スクリプト

- [ ] クイックスタート（`bash scripts/startup/quick_start.sh`）
- [ ] バックアップ（`bash scripts/maintenance/backup_full.sh`）
- [ ] 検証スクリプト（`bash scripts/maintenance/validate.sh`）

### ドキュメント

- [ ] README.md が正しく表示される
- [ ] CLAUDE.md のパス参照が正しい
- [ ] docs/ 内のドキュメントが有効

---

## 完了後のクリーンアップ

全ての検証が完了したら、以下を実行:

```bash
# シンボリックリンク削除
find . -maxdepth 1 -type l -delete

# 空ディレクトリ削除
find . -type d -empty -delete

# コミット
git add -A
git commit -m "[リファクタリング] フォルダ構造の整理完了

- ルート直下のファイル数: 115個 → 30個以下
- 論理的なディレクトリ構造へ移行
- インポートパス自動修正
- 全テスト通過確認済み"

# メインブランチへマージ
git checkout main
git merge refactor/folder-structure
git push origin main
```

---

## 参考資料

- [詳細設計書](./ARCHITECTURE_REFACTORING_PROPOSAL.md) - 完全な仕様と影響分析
- [プロジェクトルート]/scripts/create_new_structure.sh - ディレクトリ作成スクリプト
- [プロジェクトルート]/scripts/migrate_files.sh - ファイル移動スクリプト
- [プロジェクトルート]/tools/setup/fix_import_paths.py - インポートパス修正

---

## サポート

問題が発生した場合:

1. [トラブルシューティング](#トラブルシューティング)セクションを確認
2. [詳細設計書](./ARCHITECTURE_REFACTORING_PROPOSAL.md)の影響分析を参照
3. Gitの履歴を確認（`git log --oneline`）
4. 必要に応じてロールバック

---

**最終更新**: 2025-11-14
**作成者**: System Architecture Designer (Claude)
