# ファイル移行実行ガイド

## 概要
このガイドは、ルート直下の53個のPythonファイルを適切なディレクトリ構造に移行する手順を説明します。

---

## 前提条件

### 必須
- Git管理下にあること
- Python 3.11以上
- すべてのテストがパスしていること

### 推奨
- 作業用ブランチを作成済み
- バックアップを取得済み
- 他の開発者と調整済み

---

## 実行手順

### Step 1: 準備

#### 1.1 現在の状態を確認
```bash
# ワーキングディレクトリをクリーンにする
git status

# すべてのテストが通ることを確認
pytest tests/

# ルート直下のファイル数を確認
ls -1 *.py | wc -l
# 期待値: 53
```

#### 1.2 作業用ブランチを作成
```bash
git checkout -b refactor/file-reorganization
```

#### 1.3 バックアップを作成 (オプション)
```bash
tar -czf backup_root_py_$(date +%Y%m%d).tar.gz *.py
```

---

### Step 2: ドライラン実行

#### 2.1 全体計画の確認
```bash
python tools/dev/refactor_migrate_files.py --dry-run
```

**期待される出力**:
- ディレクトリ作成計画
- ファイル移動計画 (Phase 1-9)
- import更新計画
- レポートサマリー

#### 2.2 Phase 1のみドライラン
```bash
python tools/dev/refactor_migrate_files.py --dry-run --phase 1
```

#### 2.3 ドライランレポートの確認
出力を確認し、以下を検証:
- [ ] 移動先パスが正しい
- [ ] 重複するファイル名がない
- [ ] 必要なファイルがすべて含まれている

---

### Step 3: 段階的実行 (推奨)

#### 3.1 Phase 1: アプリケーション層
```bash
# 実行
python tools/dev/refactor_migrate_files.py --execute --phase 1

# 確認
ls app/
# 期待: main.py, cli_notifier.py, dashboard_app.py

# テスト
python -m pytest tests/ -v
```

#### 3.2 Phase 2: 認証層
```bash
# 実行
python tools/dev/refactor_migrate_files.py --execute --phase 2

# 確認
ls auth/
ls archive/auth_variants/

# テスト
python -c "from auth.config_manager import AuthConfig; print('OK')"
```

#### 3.3 Phase 3: テスト層
```bash
# 実行
python tools/dev/refactor_migrate_files.py --execute --phase 3

# 確認
ls tests/integration/backend/
ls tests/integration/notification/
ls tests/integration/security/
ls tests/integration/phase2/

# テスト実行
pytest tests/integration/ -v
```

#### 3.4 Phase 4-8: ツール類
```bash
# Phase 4: テスト実行ツール
python tools/dev/refactor_migrate_files.py --execute --phase 4

# Phase 5: 検証ツール
python tools/dev/refactor_migrate_files.py --execute --phase 5

# Phase 6: 修復ツール
python tools/dev/refactor_migrate_files.py --execute --phase 6

# Phase 7: 監視ツール
python tools/dev/refactor_migrate_files.py --execute --phase 7

# Phase 8: 開発補助ツール
python tools/dev/refactor_migrate_files.py --execute --phase 8

# Phase 9: アーカイブ
python tools/dev/refactor_migrate_files.py --execute --phase 9
```

---

### Step 4: 一括実行 (上級者向け)

```bash
# すべてのPhaseを一度に実行
python tools/dev/refactor_migrate_files.py --execute

# 確認プロンプトで "yes" を入力
```

---

### Step 5: 移行後の検証

#### 5.1 ファイル構造の検証
```bash
python tools/dev/validate_migration.py
```

**期待される出力**:
```
=== File Structure Validation ===
✓ app/__init__.py
✓ app/main.py
✓ app/cli_notifier.py
...
✓ All validations passed!
```

#### 5.2 import検証
```bash
# Flask app
python -c "from app.main import app; print(type(app))"
# 期待: <class 'flask.app.Flask'>

# CLI notifier
python -c "from app.cli_notifier import main; print('OK')"

# Auth config
python -c "from auth.config_manager import AuthConfig; print('OK')"

# Modules (変更なし)
python -c "from modules.db import DatabaseManager; print('OK')"
```

#### 5.3 全テスト実行
```bash
pytest tests/ -v --cov=app --cov=auth --cov=modules
```

#### 5.4 Web UI起動確認
```bash
# 開発サーバー起動
python -m app.main

# ブラウザで確認
# http://localhost:5000
```

#### 5.5 CLI実行確認
```bash
python -m app.cli_notifier --dry-run --verbose
```

---

### Step 6: import更新

#### 6.1 setup.py の更新
```python
# Before
entry_points={
    "console_scripts": [
        "manga-anime-notifier=release_notifier:main",
    ],
}

# After
entry_points={
    "console_scripts": [
        "manga-anime-notifier=app.cli_notifier:main",
    ],
}
```

#### 6.2 依存ファイルの更新
スクリプトが自動更新するファイル:
- `setup.py`
- `tools/dev/start_web_ui.py`
- `tools/dev/setup_system.py`
- `tests/test_main.py`

手動更新が必要なファイル:
- ドキュメント内のコード例 (5箇所)
- CI/CD設定ファイル
- cron/systemd設定

---

### Step 7: ドキュメント更新

#### 7.1 運用マニュアル
```bash
# docs/operations/運用マニュアル.md
# 検索・置換
from release_notifier import → from app.cli_notifier import
```

#### 7.2 トラブルシューティング
```bash
# docs/troubleshooting/トラブルシューティング.md
# 検索・置換
from release_notifier import → from app.cli_notifier import
```

#### 7.3 README更新
```bash
# README.md のコード例を更新
python release_notifier.py → python -m app.cli_notifier
```

---

### Step 8: CI/CD更新

#### 8.1 GitHub Actions (例)
```yaml
# .github/workflows/test.yml

# Before
- name: Run tests
  run: |
    pytest test_*.py
    pytest tests/

# After
- name: Run tests
  run: |
    pytest tests/
```

#### 8.2 pre-commit設定
```yaml
# .pre-commit-config.yaml
exclude: ^(archive/|__pycache__/)
```

---

### Step 9: 本番環境対応

#### 9.1 cron設定更新
```bash
# Before
0 8 * * * cd /path/to/project && python3 release_notifier.py

# After (オプション1: 直接実行)
0 8 * * * cd /path/to/project && python3 -m app.cli_notifier

# After (オプション2: エントリポイント - 推奨)
0 8 * * * /usr/local/bin/manga-anime-notifier
```

#### 9.2 systemdサービス更新
```ini
# /etc/systemd/system/manga-anime-notifier.service

# Before
[Service]
ExecStart=/usr/bin/python3 /path/to/project/release_notifier.py

# After
[Service]
ExecStart=/usr/local/bin/manga-anime-notifier
```

再起動:
```bash
sudo systemctl daemon-reload
sudo systemctl restart manga-anime-notifier
sudo systemctl status manga-anime-notifier
```

---

### Step 10: コミット

#### 10.1 変更内容の確認
```bash
git status
git diff
```

#### 10.2 ステージング
```bash
git add app/
git add auth/
git add tests/integration/
git add tools/
git add archive/
git add setup.py
git add docs/
```

#### 10.3 コミット
```bash
git commit -m "Refactor: Reorganize 53 Python files into logical directory structure

- Move app files: web_app.py → app/main.py, etc.
- Create auth/ module: auth_config.py → auth/config_manager.py
- Reorganize tests: test_*.py → tests/integration/
- Organize tools: fix_*.py → tools/repair/, etc.
- Archive old variants: archive/auth_variants/
- Update imports in setup.py, tests/, and tools/
- Update documentation references

Refs: docs/ARCHITECTURE_REFACTORING_PLAN.md
Refs: docs/IMPORT_IMPACT_ANALYSIS.md"
```

#### 10.4 プッシュ
```bash
git push origin refactor/file-reorganization
```

---

## トラブルシューティング

### import エラー: ModuleNotFoundError

**症状**:
```
ModuleNotFoundError: No module named 'app'
```

**原因**: PYTHONPATH未設定

**解決策**:
```bash
# 方法1: 環境変数設定
export PYTHONPATH=/path/to/project:$PYTHONPATH

# 方法2: 開発モードインストール
pip install -e .

# 方法3: sys.path追加 (スクリプト内)
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
```

---

### Flask起動エラー: template not found

**症状**:
```
TemplateNotFound: index.html
```

**原因**: テンプレートパスが相対パス

**解決策**:
```python
# app/main.py
from pathlib import Path

template_dir = Path(__file__).parent.parent / "templates"
app = Flask(__name__, template_folder=str(template_dir))
```

---

### テスト失敗: conftest.py

**症状**:
```
pytest: cannot import name 'DatabaseManager'
```

**原因**: tests/conftest.py 未設定

**解決策**:
```python
# tests/conftest.py
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
```

---

### cron実行エラー

**症状**: cronから実行すると失敗

**原因**: 環境変数/PYTHONPATHが未設定

**解決策**:
```cron
# エントリポイント使用 (推奨)
0 8 * * * /usr/local/bin/manga-anime-notifier

# または環境変数設定
0 8 * * * cd /path/to/project && PYTHONPATH=. python3 -m app.cli_notifier
```

---

## ロールバック手順

### Git経由
```bash
# コミット前
git reset --hard HEAD

# コミット後
git revert HEAD

# ブランチ削除
git checkout main
git branch -D refactor/file-reorganization
```

### バックアップから復元
```bash
# バックアップ解凍
tar -xzf backup_root_py_YYYYMMDD.tar.gz

# テスト実行
pytest tests/
```

---

## チェックリスト

### 実行前
- [ ] Git管理下にある
- [ ] すべてのテストがパス
- [ ] 作業用ブランチを作成
- [ ] バックアップを作成
- [ ] 他の開発者と調整

### 実行中
- [ ] Phase 1実行 + テスト
- [ ] Phase 2実行 + テスト
- [ ] Phase 3実行 + テスト
- [ ] Phase 4-9実行
- [ ] 移行後検証実行

### 実行後
- [ ] 全テストパス
- [ ] Flask起動確認
- [ ] CLI実行確認
- [ ] import検証パス
- [ ] ドキュメント更新
- [ ] CI/CD更新
- [ ] 本番環境設定更新
- [ ] コミット + プッシュ

---

## 推定作業時間

| フェーズ | 時間 |
|---------|------|
| 準備 (Step 1-2) | 30分 |
| 段階的実行 (Step 3-4) | 1-2時間 |
| 検証 (Step 5) | 30分 |
| import更新 (Step 6) | 30分 |
| ドキュメント更新 (Step 7) | 30分 |
| CI/CD更新 (Step 8) | 30分 |
| 本番環境対応 (Step 9) | 30分 |
| コミット (Step 10) | 15分 |
| **合計** | **4-5時間** |

---

## 関連ドキュメント

- `docs/ARCHITECTURE_REFACTORING_PLAN.md`: 全体計画
- `docs/IMPORT_IMPACT_ANALYSIS.md`: 影響分析
- `tools/dev/refactor_migrate_files.py`: 移行スクリプト
- `tools/dev/validate_migration.py`: 検証スクリプト

---

**作成者**: System Architecture Designer
**作成日**: 2025-11-14
**バージョン**: 1.0
