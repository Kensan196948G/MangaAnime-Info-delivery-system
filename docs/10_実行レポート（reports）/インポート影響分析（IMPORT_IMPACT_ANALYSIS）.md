# Import影響分析レポート

## 分析日: 2025-11-14
## 対象: ルート直下53ファイルの移動による影響

---

## 1. エグゼクティブサマリー

### 検出された依存関係
- **直接依存**: 6箇所
- **ドキュメント参照**: 5箇所
- **影響を受けるファイル**: 8ファイル
- **修正優先度**: 中 (既存機能への影響は限定的)

### 主要な発見
1. ルート直下ファイルへの外部依存は少ない (良好)
2. `modules/` 配下への依存が主流 (安定)
3. `web_app.py`, `release_notifier.py`, `auth_config.py` が主要な被依存ファイル

---

## 2. 直接依存関係マップ

### 2.1 web_app.py への依存

#### start_web_ui.py → web_app.py
```python
# 現在
from web_app import app

# 移動後
# app/main.py へ改名される場合
from app.main import app
```

**影響度**: 低
**対策**: `start_web_ui.py` を `tools/dev/` に移動し、import更新

---

#### REFERENCE_INTEGRITY_REPORT.md
```bash
# 現在
$ python -c "import web_app; print('OK')"

# 移動後
$ python -c "from app import main; print('OK')"
```

**影響度**: 低 (ドキュメントのみ)
**対策**: ドキュメント更新

---

### 2.2 release_notifier.py への依存

#### setup_system.py → release_notifier.py
```python
# 現在
from release_notifier import ReleaseNotifierSystem

# 移動後 (app/cli_notifier.py に改名)
from app.cli_notifier import ReleaseNotifierSystem
```

**影響度**: 中
**対策**: setup_system.py のimport修正

---

#### tests/test_main.py → release_notifier.py
```python
# 現在
from release_notifier import main as release_main

# 移動後
from app.cli_notifier import main as release_main
```

**影響度**: 中 (テストの破損)
**対策**: テストファイルのimport修正

---

#### docs/operations/運用マニュアル.md (2箇所)
```python
# 現在
from release_notifier import ReleaseNotifier

# 移動後
from app.cli_notifier import ReleaseNotifier
```

**影響度**: 低 (ドキュメントのみ)
**対策**: 運用マニュアル更新

---

#### docs/troubleshooting/トラブルシューティング.md (2箇所)
```python
# 現在
from release_notifier import ReleaseNotifier

# 移動後
from app.cli_notifier import ReleaseNotifier
```

**影響度**: 低 (ドキュメントのみ)
**対策**: トラブルシューティングガイド更新

---

### 2.3 auth_config.py への依存

#### test_gmail_auth.py → auth_config.py
```python
# 現在
from auth_config import AuthConfig

# 移動後 (auth/config_manager.py に改名)
from auth.config_manager import AuthConfig
```

**影響度**: 中 (テストの破損)
**対策**: テストファイルのimport修正

---

## 3. 間接依存関係 (modules経由)

### 3.1 modules/ 内からルート直下への依存

#### 検証コマンド実行結果
```bash
$ grep -r "import web_app\|import release_notifier\|import auth_config" modules/
# 結果: 0件 (依存なし)
```

**結論**: `modules/` 配下からルート直下ファイルへの依存は**存在しない** (理想的な設計)

---

### 3.2 主要アプリからmodules/への依存

#### web_app.py の依存
```python
# 標準ライブラリ
import os, json, sqlite3, requests, time, logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, flash, redirect, url_for

# プロジェクト内 (暗黙的)
# 直接importなし (動的SQL使用)
```

**特記事項**: `modules/` への明示的importなし (直接DB操作)
**移動影響**: なし

---

#### release_notifier.py の依存
```python
# プロジェクト内
from modules import get_config
from modules.db import DatabaseManager
from modules.logger import setup_logging
from modules.email_scheduler import EmailScheduler
```

**特記事項**: `modules/` への依存あり (相対パス不要)
**移動影響**: `modules/` がルート配下に残る限り影響なし

---

#### dashboard_main.py の依存
```python
from modules.db import DatabaseManager
from modules.anime_anilist import AniListCollector
from modules.manga_rss import MangaRSSCollector
from modules.filter_logic import ContentFilter
from modules.mailer import GmailNotifier
from modules.calendar_integration import GoogleCalendarManager
from modules.dashboard_integration import dashboard_integration, track_performance
```

**特記事項**: `modules/` への多数依存
**移動影響**: なし (相対パス不変)

---

## 4. パス依存性の分析

### 4.1 ハードコードされたパス

#### 検証実行
```bash
$ grep -r "web_app.py\|release_notifier.py" --include="*.py" --include="*.sh" --include="*.md" .
```

#### 発見事項
1. **ドキュメント内パス**: 5箇所 (すべて例示コード)
2. **シェルスクリプト**: 0箇所
3. **Pythonコード内**: 0箇所 (良好)

---

### 4.2 テンプレート/静的ファイルパス

#### web_app.py のFlask設定
```python
app = Flask(__name__)
# デフォルト: templates/, static/
```

**移動後の調整**:
```python
# app/main.py
from pathlib import Path

template_dir = Path(__file__).parent.parent / "templates"
static_dir = Path(__file__).parent.parent / "static"

app = Flask(__name__,
            template_folder=str(template_dir),
            static_folder=str(static_dir))
```

**影響度**: 低 (明示的パス指定で解決)

---

### 4.3 データベースパス

#### 環境変数経由 (推奨パターン)
```python
# modules/db.py (想定)
DB_PATH = os.getenv("DATABASE_PATH", "db.sqlite3")
```

**移動影響**: なし (環境変数ベース)

---

## 5. エントリポイント影響分析

### 5.1 setup.py の console_scripts

#### 現在の定義
```python
entry_points={
    "console_scripts": [
        "manga-anime-notifier=release_notifier:main",
    ],
}
```

#### 移動後の修正
```python
entry_points={
    "console_scripts": [
        "manga-anime-notifier=app.cli_notifier:main",
    ],
}
```

**影響度**: 高 (CLIコマンドの破損)
**対策**: setup.py の即時更新必須

---

### 5.2 systemd/cron サービス

#### 想定される設定
```ini
# /etc/systemd/system/manga-anime-notifier.service
[Service]
ExecStart=/usr/bin/python3 /path/to/release_notifier.py
```

#### 移動後
```ini
# オプション1: 絶対パス更新
ExecStart=/usr/bin/python3 /path/to/app/cli_notifier.py

# オプション2: エントリポイント使用 (推奨)
ExecStart=/usr/local/bin/manga-anime-notifier
```

**影響度**: 高 (本番環境の破損)
**対策**: デプロイ時の設定更新必須

---

### 5.3 cron設定

#### 想定される設定
```cron
0 8 * * * cd /path/to/project && python3 release_notifier.py
```

#### 移動後
```cron
# オプション1: パス更新
0 8 * * * cd /path/to/project && python3 app/cli_notifier.py

# オプション2: PYTHONPATH設定 (推奨)
0 8 * * * cd /path/to/project && PYTHONPATH=. python3 -m app.cli_notifier

# オプション3: エントリポイント使用 (最推奨)
0 8 * * * /usr/local/bin/manga-anime-notifier
```

**影響度**: 高 (自動実行の停止)
**対策**: crontab更新 + 本番環境テスト

---

## 6. テスト依存性の分析

### 6.1 pytest検出パターン

#### 現在の検出
```bash
$ pytest
# 自動検出: ./test_*.py, tests/test_*.py
```

#### 移動後
```bash
# tests/integration/ への移動後も自動検出される
$ pytest tests/integration/
```

**影響度**: 低 (pytestの自動検出機能で対応)

---

### 6.2 conftest.py の調整

#### 追加すべき設定
```python
# tests/conftest.py
import sys
from pathlib import Path

# プロジェクトルートをPYTHONPATHに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
```

**目的**: すべてのテストから `modules/`, `app/`, `auth/` にアクセス可能にする

---

## 7. CI/CD パイプライン影響

### 7.1 GitHub Actions (想定)

#### 現在の想定設定
```yaml
# .github/workflows/test.yml
- name: Run tests
  run: |
    python -m pytest test_*.py
    python -m pytest tests/
```

#### 移動後の修正
```yaml
- name: Run tests
  run: |
    python -m pytest tests/
    python -m pytest tests/integration/
```

**影響度**: 中
**対策**: CI設定ファイルの更新

---

### 7.2 Lint/フォーマッタ設定

#### pyproject.toml / setup.cfg
```ini
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"

[tool.flake8]
exclude = .git,__pycache__,build,dist,archive
```

**影響度**: 低
**対策**: `exclude` に `archive/` 追加

---

## 8. 外部ツール依存性

### 8.1 IDEプロジェクト設定

#### VSCode (.vscode/settings.json)
```json
{
  "python.analysis.extraPaths": ["./modules"],
  "python.testing.pytestArgs": ["tests"]
}
```

#### 移動後
```json
{
  "python.analysis.extraPaths": ["./modules", "./app", "./auth"],
  "python.testing.pytestArgs": ["tests"],
  "python.testing.pytestEnabled": true
}
```

---

### 8.2 MyPy型チェック

#### mypy.ini
```ini
[mypy]
mypy_path = modules:app:auth
```

**対策**: 新ディレクトリをmypy_pathに追加

---

## 9. 優先順位別修正リスト

### 優先度: 高 (機能停止リスク)

| 対象 | 現在のパス | 修正内容 |
|------|-----------|---------|
| setup.py | `release_notifier:main` | `app.cli_notifier:main` |
| cron設定 | `python3 release_notifier.py` | エントリポイント使用 |
| systemdサービス | `/path/to/release_notifier.py` | エントリポイント使用 |
| start_web_ui.py | `from web_app import app` | `from app.main import app` |

---

### 優先度: 中 (テスト/セットアップ)

| 対象 | 現在のパス | 修正内容 |
|------|-----------|---------|
| tests/test_main.py | `from release_notifier import main` | `from app.cli_notifier import main` |
| test_gmail_auth.py | `from auth_config import AuthConfig` | `from auth.config_manager import AuthConfig` |
| setup_system.py | `from release_notifier import ...` | `from app.cli_notifier import ...` |
| CI/CD設定 | `pytest test_*.py` | `pytest tests/` |

---

### 優先度: 低 (ドキュメント)

| 対象 | 修正内容 |
|------|---------|
| 運用マニュアル | import文の更新 (2箇所) |
| トラブルシューティング | import文の更新 (2箇所) |
| REFERENCE_INTEGRITY_REPORT.md | コマンド例の更新 |

---

## 10. 自動化スクリプト提案

### 10.1 import自動書き換えスクリプト

```python
#!/usr/bin/env python3
"""
Import文自動書き換えツール
"""

import re
from pathlib import Path

REPLACEMENTS = {
    r"from web_app import": "from app.main import",
    r"import web_app": "import app.main as web_app",
    r"from release_notifier import": "from app.cli_notifier import",
    r"import release_notifier": "import app.cli_notifier as release_notifier",
    r"from auth_config import": "from auth.config_manager import",
    r"import auth_config": "import auth.config_manager as auth_config",
}

def rewrite_imports(file_path: Path):
    """指定ファイルのimport文を書き換え"""
    content = file_path.read_text(encoding="utf-8")
    original = content

    for pattern, replacement in REPLACEMENTS.items():
        content = re.sub(pattern, replacement, content)

    if content != original:
        file_path.write_text(content, encoding="utf-8")
        print(f"Updated: {file_path}")
        return True
    return False

def main():
    """メイン処理"""
    project_root = Path(__file__).parent.parent

    # 対象ファイル
    targets = [
        "start_web_ui.py",
        "setup_system.py",
        "tests/test_main.py",
        "test_gmail_auth.py",
    ]

    updated = 0
    for target in targets:
        file_path = project_root / target
        if file_path.exists():
            if rewrite_imports(file_path):
                updated += 1

    print(f"\nTotal updated: {updated} files")

if __name__ == "__main__":
    main()
```

---

### 10.2 検証スクリプト

```python
#!/usr/bin/env python3
"""
移動後のimport検証スクリプト
"""

import sys
from pathlib import Path

def validate_imports():
    """すべてのimportが正常か検証"""
    errors = []

    # app/からのimportテスト
    try:
        from app.main import app
        print("✓ app.main")
    except ImportError as e:
        errors.append(f"✗ app.main: {e}")

    try:
        from app.cli_notifier import main
        print("✓ app.cli_notifier")
    except ImportError as e:
        errors.append(f"✗ app.cli_notifier: {e}")

    # auth/からのimportテスト
    try:
        from auth.config_manager import AuthConfig
        print("✓ auth.config_manager")
    except ImportError as e:
        errors.append(f"✗ auth.config_manager: {e}")

    # modules/からのimportテスト (変更なし)
    try:
        from modules.db import DatabaseManager
        print("✓ modules.db")
    except ImportError as e:
        errors.append(f"✗ modules.db: {e}")

    if errors:
        print("\n❌ Import errors detected:")
        for error in errors:
            print(f"  {error}")
        return False

    print("\n✅ All imports are valid!")
    return True

if __name__ == "__main__":
    sys.exit(0 if validate_imports() else 1)
```

---

## 11. ロールバック計画

### 緊急時の復旧手順

```bash
# 1. Gitでロールバック
git reset --hard HEAD~1

# 2. バックアップから復元
tar -xzf backup_root_py_YYYYMMDD.tar.gz

# 3. テスト実行
pytest tests/

# 4. サービス再起動
sudo systemctl restart manga-anime-notifier
```

---

## 12. 移行後の検証チェックリスト

### アプリケーション層
- [ ] Flask Web UI起動確認 (`python -m app.main`)
- [ ] CLI通知実行確認 (`manga-anime-notifier --dry-run`)
- [ ] ダッシュボードアクセス確認

### 認証層
- [ ] OAuth2フロー動作確認
- [ ] トークン生成確認
- [ ] トークン検証確認

### テスト層
- [ ] 全テストパス (`pytest tests/`)
- [ ] カバレッジ維持確認
- [ ] CI/CD正常動作

### ツール層
- [ ] 検証ツール動作確認 (`python tools/validation/validate_system.py`)
- [ ] 修復ツール動作確認 (`python tools/repair/fix_all_tests.py`)
- [ ] 監視ツール動作確認 (`python tools/monitoring/continuous_monitor.py`)

### 本番環境
- [ ] cron実行確認
- [ ] systemdサービス起動確認
- [ ] ログ出力確認

---

## 13. まとめ

### 影響範囲の総括
- **直接影響ファイル**: 8ファイル
- **修正難易度**: 低〜中
- **推定作業時間**: 2-3時間
- **リスクレベル**: 低 (段階的実施により)

### 推奨事項
1. **段階的移行**: Phase毎にテスト実行
2. **自動化活用**: import書き換えスクリプト使用
3. **本番環境**: エントリポイント方式への移行
4. **ドキュメント**: 移行完了後に即時更新

---

**分析者**: System Architecture Designer
**分析日**: 2025-11-14
**バージョン**: 1.0
**関連ドキュメント**: `ARCHITECTURE_REFACTORING_PLAN.md`
