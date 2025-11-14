# システムアーキテクチャ整理計画

## エグゼクティブサマリー

**現状**: ルート直下に115個のファイルが散在しており、保守性と可読性が低下しています。

**目標**: 論理的なフォルダ構造への再編成により、開発効率の向上とコードベースの理解容易性を実現します。

**影響範囲**: Pythonファイル 53個、シェルスクリプト 20個、設定ファイル 11個、その他

---

## 1. 現状分析

### 1.1 ルート直下のファイル分類

#### A. メインアプリケーション（3ファイル）
- **web_app.py** - Flask Web UIメインアプリケーション
- **release_notifier.py** - リリース通知システムエントリポイント
- **dashboard_main.py** - ダッシュボード機能統合版

#### B. 認証・OAuth関連（6ファイル）
- auth_config.py
- oauth_setup_helper.py
- create_token.py
- create_token_simple.py
- create_token_improved.py
- create_token_manual.py
- generate_token.py

#### C. テスト関連（25ファイル）
**テストランナー系**:
- test_runner.py
- simple_test_runner.py
- run_check.py
- run_failing_tests.py
- simple_test_check.py
- analyze_tests.py
- examine_test_content.py

**機能テスト系**:
- test_email_delivery.py
- test_gmail_auth.py
- test_smtp_email.py
- test_mailer_improvements.py
- test_notification.py
- test_secret_key.py
- test_backend_api.py
- test_enhanced_backend.py
- test_phase2_implementation.py
- test_discovery.py

**テストユーティリティ系**:
- get_test_info.py
- list_tests.py
- verify_tests.py
- fix_all_tests.py
- fix_tests_final.py
- run_fixed_tests.py
- simple_phase2_test.py

#### D. システム修復・監視（8ファイル）
- auto_repair_loop.py
- continuous_monitor.py
- fix_config_errors.py
- fix_database_integrity.py
- validate_system.py
- performance_benchmark.py
- check_structure.py
- check_doc_references.py

#### E. セットアップ・初期化（6ファイル）
- setup.py
- setup_system.py
- init_demo_db.py
- example_usage.py
- direct_file_check.py
- security_qa_cli.py

#### F. 開発ツール（3ファイル）
- auto_fix_lint.py
- fix_f821_imports.py
- web_ui.py (旧バージョン)

#### G. シェルスクリプト（20ファイル）
**起動系**:
- start_web_ui.py (これはPython)
- start_mangaanime_web.sh
- start_webui_manual.sh
- start-automation.sh
- start-local-repair.sh
- start-repair-background.sh
- start_integrated_ai_development.sh

**セットアップ系**:
- setup_cron.sh
- setup_email.sh
- setup_env.sh
- install_auto_startup.sh
- install_webui_autostart.sh

**運用系**:
- run_now.sh
- run_validation.sh
- quick_start.sh
- run_claude_autoloop.sh
- local-repair-system.sh
- show_webui_access.sh

**テスト系**:
- check_tests.sh
- test-repair-demo.sh

**バックアップ系**:
- backup_full.sh

#### H. 設定ファイル（11 JSONファイル）
**アプリケーション設定**:
- config.json (メイン設定)
- config.json.template
- settings.local.json
- package.json
- package-lock.json

**テンプレート**:
- gmail_config.json.template

**レポート系**:
- CRITICAL_FIXES_REPORT.json
- performance-regression-report.json
- phase2_test_results.json
- qa_audit_report.json
- security_audit_report.json
- repair_summary.json
- DOC_REFERENCE_REPORT.json

#### I. その他の設定ファイル
- .env
- .env.example
- .env.template
- .gitignore
- agents.yaml
- pytest.ini
- playwright.config.ts
- Makefile
- Makefile.new

#### J. データファイル
- db.sqlite3
- .coverage

#### K. ドキュメント（3ファイル）
- README.md
- README日本語版.md
- CLAUDE.md

#### L. 出力・ログ系テキストファイル（8ファイル）
- coverage_output.txt
- test_results.txt
- test_summary.txt
- init_output.txt
- temp_file_check.txt

#### M. 依存関係管理
- requirements.txt
- requirements-dev.txt
- requirements-backend-enhanced.txt

#### N. サービス定義
- local-automation.service
- mangaanime-web.service

#### O. バッチファイル
- create_pr.bat

#### P. SQLファイル
- optimize_database.sql

#### Q. 自動化・CI/CD関連
- .automation-state.json
- .ci-trigger
- .ci-test-trigger
- .repair-state.json

---

## 2. 新しいフォルダ構造設計

```
MangaAnime-Info-delivery-system/
│
├── app/                          # メインアプリケーション
│   ├── main.py -> ../web_app.py (シンボリックリンクまたは移動)
│   ├── web_app.py                # Flask Web UI
│   ├── release_notifier.py       # リリース通知システム
│   └── dashboard_main.py         # ダッシュボード統合版
│
├── modules/                      # ✅ 既存（コアロジックモジュール）
│   ├── __init__.py
│   ├── anime_anilist.py
│   ├── manga_rss.py
│   ├── filter_logic.py
│   ├── db.py
│   ├── mailer.py
│   └── ... (その他のモジュール)
│
├── src/                          # ✅ 既存（統合とメモリ管理）
│   ├── integrations/
│   └── memory/
│
├── config/                       # ✅ 既存（設定ファイル）
│   ├── config.json               # メイン設定
│   ├── config.json.template
│   ├── gmail_config.json.template
│   ├── settings.local.json
│   ├── .env
│   ├── .env.example
│   └── .env.template
│
├── auth/                         # 🆕 認証関連
│   ├── oauth_setup_helper.py
│   ├── auth_config.py
│   └── token_generators/
│       ├── create_token.py
│       ├── create_token_simple.py
│       ├── create_token_improved.py
│       ├── create_token_manual.py
│       └── generate_token.py
│
├── scripts/                      # ✅ 既存 - 運用スクリプト（拡張）
│   ├── startup/                  # 🆕 起動スクリプト
│   │   ├── start_web.sh
│   │   ├── start_automation.sh
│   │   ├── start_repair.sh
│   │   └── quick_start.sh
│   │
│   ├── setup/                    # 🆕 セットアップスクリプト
│   │   ├── setup_cron.sh
│   │   ├── setup_email.sh
│   │   ├── setup_env.sh
│   │   ├── install_auto_startup.sh
│   │   └── install_webui_autostart.sh
│   │
│   ├── maintenance/              # 🆕 メンテナンススクリプト
│   │   ├── backup_full.sh
│   │   ├── validate.sh
│   │   └── run_validation.sh
│   │
│   └── ... (既存のPythonスクリプト)
│
├── tools/                        # 🆕 開発・デバッグツール
│   ├── monitoring/
│   │   ├── continuous_monitor.py
│   │   ├── performance_benchmark.py
│   │   └── check_structure.py
│   │
│   ├── repair/
│   │   ├── auto_repair_loop.py
│   │   ├── fix_config_errors.py
│   │   └── fix_database_integrity.py
│   │
│   ├── validation/
│   │   ├── validate_system.py
│   │   └── check_doc_references.py
│   │
│   ├── linting/
│   │   ├── auto_fix_lint.py
│   │   └── fix_f821_imports.py
│   │
│   └── setup/
│       ├── setup.py
│       ├── setup_system.py
│       ├── init_demo_db.py
│       └── security_qa_cli.py
│
├── tests/                        # ✅ 既存（テストコード）
│   ├── unit/                     # 🆕 ユニットテスト
│   │   ├── test_filtering.py
│   │   ├── test_database_fixed.py
│   │   └── test_anilist_api.py
│   │
│   ├── integration/              # 🆕 統合テスト
│   │   ├── test_enhanced_backend_integration.py
│   │   ├── test_mailer_integration.py
│   │   └── test_google_apis.py
│   │
│   ├── e2e/                      # 🆕 E2Eテスト
│   │   ├── test_backend_api.py
│   │   ├── test_enhanced_backend.py
│   │   └── test_phase2_implementation.py
│   │
│   ├── security/                 # 🆕 セキュリティテスト
│   │   └── test_security_comprehensive.py
│   │
│   ├── runners/                  # 🆕 テストランナー
│   │   ├── test_runner.py
│   │   ├── simple_test_runner.py
│   │   ├── run_check.py
│   │   ├── run_failing_tests.py
│   │   └── simple_test_check.py
│   │
│   ├── utilities/                # 🆕 テストユーティリティ
│   │   ├── get_test_info.py
│   │   ├── list_tests.py
│   │   ├── verify_tests.py
│   │   ├── analyze_tests.py
│   │   └── examine_test_content.py
│   │
│   ├── fixtures/                 # 🆕 テストフィクスチャ
│   │   └── (テストデータ)
│   │
│   └── test_*.py                 # ルート直下から移動
│
├── bin/                          # 🆕 実行可能スクリプト（エントリポイント）
│   ├── run_notifier              # release_notifier.pyへのラッパー
│   ├── run_webapp                # web_app.pyへのラッパー
│   └── run_dashboard             # dashboard_main.pyへのラッパー
│
├── data/                         # 🆕 データファイル
│   ├── db.sqlite3                # データベース
│   └── backups/                  # バックアップ保存先
│
├── logs/                         # ✅ 既存（ログファイル）
│
├── docs/                         # ✅ 既存（ドキュメント）
│   ├── README.md
│   ├── README日本語版.md
│   ├── CLAUDE.md
│   └── ARCHITECTURE_REFACTORING_PROPOSAL.md (このファイル)
│
├── reports/                      # 🆕 レポート出力
│   ├── security_audit_report.json
│   ├── qa_audit_report.json
│   ├── performance-regression-report.json
│   ├── CRITICAL_FIXES_REPORT.json
│   ├── DOC_REFERENCE_REPORT.json
│   ├── phase2_test_results.json
│   └── repair_summary.json
│
├── output/                       # 🆕 一時出力ファイル
│   ├── coverage_output.txt
│   ├── test_results.txt
│   ├── test_summary.txt
│   ├── init_output.txt
│   └── temp_file_check.txt
│
├── systemd/                      # 🆕 systemdサービス定義
│   ├── local-automation.service
│   └── mangaanime-web.service
│
├── database/                     # 🆕 データベース関連
│   └── migrations/
│       └── optimize_database.sql
│
├── static/                       # ✅ 既存（静的ファイル）
├── templates/                    # ✅ 既存（HTMLテンプレート）
│
├── .claude/                      # ✅ 既存（Claude設定）
├── .github/                      # ✅ 既存（GitHub Actions）
├── workflows/                    # ✅ 既存（ワークフロー定義）
│
├── archive/                      # 🆕 非推奨・旧ファイル
│   ├── old_versions/
│   │   ├── web_ui.py (旧版)
│   │   └── Makefile.new
│   └── deprecated/
│       ├── create_token_improved.py (統合済み)
│       └── create_token_manual.py (統合済み)
│
├── .automation-state.json
├── .ci-trigger
├── .ci-test-trigger
├── .coverage
├── .gitignore
├── .repair-state.json
├── agents.yaml
├── pytest.ini
├── playwright.config.ts
├── Makefile
├── package.json
├── package-lock.json
├── requirements.txt
├── requirements-dev.txt
├── requirements-backend-enhanced.txt
└── create_pr.bat
```

---

## 3. ファイル移動計画詳細

### 3.1 フェーズ1: ディレクトリ構造の作成

```bash
mkdir -p app
mkdir -p auth/token_generators
mkdir -p scripts/{startup,setup,maintenance}
mkdir -p tools/{monitoring,repair,validation,linting,setup}
mkdir -p tests/{unit,integration,e2e,security,runners,utilities,fixtures}
mkdir -p bin
mkdir -p data/backups
mkdir -p docs
mkdir -p reports
mkdir -p output
mkdir -p systemd
mkdir -p database/migrations
mkdir -p archive/{old_versions,deprecated}
```

### 3.2 フェーズ2: メインアプリケーションの移動

| 移動元 | 移動先 | 説明 |
|--------|--------|------|
| web_app.py | app/web_app.py | Flask Web UIメイン |
| release_notifier.py | app/release_notifier.py | リリース通知メイン |
| dashboard_main.py | app/dashboard_main.py | ダッシュボードメイン |

**影響分析**:
- scriptsディレクトリ内のスクリプトからの参照を修正
- bin/にエントリポイントラッパーを作成

### 3.3 フェーズ3: 認証関連の移動

| 移動元 | 移動先 |
|--------|--------|
| auth_config.py | auth/auth_config.py |
| oauth_setup_helper.py | auth/oauth_setup_helper.py |
| create_token.py | auth/token_generators/create_token.py |
| create_token_simple.py | auth/token_generators/create_token_simple.py |
| create_token_improved.py | archive/deprecated/create_token_improved.py |
| create_token_manual.py | archive/deprecated/create_token_manual.py |
| generate_token.py | auth/token_generators/generate_token.py |

### 3.4 フェーズ4: テスト関連の整理

#### A. テストランナー
| 移動元 | 移動先 |
|--------|--------|
| test_runner.py | tests/runners/test_runner.py |
| simple_test_runner.py | tests/runners/simple_test_runner.py |
| run_check.py | tests/runners/run_check.py |
| run_failing_tests.py | tests/runners/run_failing_tests.py |
| simple_test_check.py | tests/runners/simple_test_check.py |

#### B. テストユーティリティ
| 移動元 | 移動先 |
|--------|--------|
| analyze_tests.py | tests/utilities/analyze_tests.py |
| examine_test_content.py | tests/utilities/examine_test_content.py |
| get_test_info.py | tests/utilities/get_test_info.py |
| list_tests.py | tests/utilities/list_tests.py |
| verify_tests.py | tests/utilities/verify_tests.py |
| fix_all_tests.py | tests/utilities/fix_all_tests.py |
| fix_tests_final.py | tests/utilities/fix_tests_final.py |
| run_fixed_tests.py | tests/utilities/run_fixed_tests.py |
| simple_phase2_test.py | tests/utilities/simple_phase2_test.py |
| test_discovery.py | tests/utilities/test_discovery.py |

#### C. E2Eテスト
| 移動元 | 移動先 |
|--------|--------|
| test_backend_api.py | tests/e2e/test_backend_api.py |
| test_enhanced_backend.py | tests/e2e/test_enhanced_backend.py |
| test_phase2_implementation.py | tests/e2e/test_phase2_implementation.py |

#### D. メール/認証テスト
| 移動元 | 移動先 |
|--------|--------|
| test_email_delivery.py | tests/integration/test_email_delivery.py |
| test_gmail_auth.py | tests/integration/test_gmail_auth.py |
| test_smtp_email.py | tests/integration/test_smtp_email.py |
| test_mailer_improvements.py | tests/integration/test_mailer_improvements.py |
| test_notification.py | tests/integration/test_notification.py |
| test_secret_key.py | tests/integration/test_secret_key.py |

### 3.5 フェーズ5: ツール類の移動

#### A. 監視ツール
| 移動元 | 移動先 |
|--------|--------|
| continuous_monitor.py | tools/monitoring/continuous_monitor.py |
| performance_benchmark.py | tools/monitoring/performance_benchmark.py |
| check_structure.py | tools/monitoring/check_structure.py |
| check_doc_references.py | tools/monitoring/check_doc_references.py |

#### B. 修復ツール
| 移動元 | 移動先 |
|--------|--------|
| auto_repair_loop.py | tools/repair/auto_repair_loop.py |
| fix_config_errors.py | tools/repair/fix_config_errors.py |
| fix_database_integrity.py | tools/repair/fix_database_integrity.py |

#### C. バリデーションツール
| 移動元 | 移動先 |
|--------|--------|
| validate_system.py | tools/validation/validate_system.py |

#### D. Lintingツール
| 移動元 | 移動先 |
|--------|--------|
| auto_fix_lint.py | tools/linting/auto_fix_lint.py |
| fix_f821_imports.py | tools/linting/fix_f821_imports.py |

#### E. セットアップツール
| 移動元 | 移動先 |
|--------|--------|
| setup.py | tools/setup/setup.py |
| setup_system.py | tools/setup/setup_system.py |
| init_demo_db.py | tools/setup/init_demo_db.py |
| security_qa_cli.py | tools/setup/security_qa_cli.py |
| example_usage.py | tools/setup/example_usage.py |
| direct_file_check.py | tools/setup/direct_file_check.py |

### 3.6 フェーズ6: シェルスクリプトの整理

#### A. 起動スクリプト
| 移動元 | 移動先 |
|--------|--------|
| start_mangaanime_web.sh | scripts/startup/start_web.sh |
| start_webui_manual.sh | scripts/startup/start_webui.sh |
| start-automation.sh | scripts/startup/start_automation.sh |
| start-local-repair.sh | scripts/startup/start_repair.sh |
| start-repair-background.sh | scripts/startup/start_repair_bg.sh |
| start_integrated_ai_development.sh | scripts/startup/start_ai_dev.sh |
| quick_start.sh | scripts/startup/quick_start.sh |
| run_now.sh | scripts/startup/run_now.sh |
| run_claude_autoloop.sh | scripts/startup/run_claude.sh |

#### B. セットアップスクリプト
| 移動元 | 移動先 |
|--------|--------|
| setup_cron.sh | scripts/setup/setup_cron.sh |
| setup_email.sh | scripts/setup/setup_email.sh |
| setup_env.sh | scripts/setup/setup_env.sh |
| install_auto_startup.sh | scripts/setup/install_autostart.sh |
| install_webui_autostart.sh | scripts/setup/install_webui_autostart.sh |

#### C. メンテナンススクリプト
| 移動元 | 移動先 |
|--------|--------|
| backup_full.sh | scripts/maintenance/backup_full.sh |
| run_validation.sh | scripts/maintenance/validate.sh |
| check_tests.sh | scripts/maintenance/check_tests.sh |
| test-repair-demo.sh | scripts/maintenance/test_repair.sh |
| local-repair-system.sh | scripts/maintenance/repair_system.sh |
| show_webui_access.sh | scripts/maintenance/show_access.sh |

### 3.7 フェーズ7: 設定ファイル・データの移動

#### A. レポートファイル
| 移動元 | 移動先 |
|--------|--------|
| CRITICAL_FIXES_REPORT.json | reports/critical_fixes.json |
| performance-regression-report.json | reports/performance_regression.json |
| phase2_test_results.json | reports/phase2_test_results.json |
| qa_audit_report.json | reports/qa_audit.json |
| security_audit_report.json | reports/security_audit.json |
| repair_summary.json | reports/repair_summary.json |
| DOC_REFERENCE_REPORT.json | reports/doc_references.json |

#### B. 出力ファイル
| 移動元 | 移動先 |
|--------|--------|
| coverage_output.txt | output/coverage.txt |
| test_results.txt | output/test_results.txt |
| test_summary.txt | output/test_summary.txt |
| init_output.txt | output/init_output.txt |
| temp_file_check.txt | output/temp_file_check.txt |

#### C. データベースファイル
| 移動元 | 移動先 |
|--------|--------|
| db.sqlite3 | data/db.sqlite3 |

#### D. systemdサービス
| 移動元 | 移動先 |
|--------|--------|
| local-automation.service | systemd/local-automation.service |
| mangaanime-web.service | systemd/mangaanime-web.service |

#### E. データベースマイグレーション
| 移動元 | 移動先 |
|--------|--------|
| optimize_database.sql | database/migrations/optimize_database.sql |

### 3.8 フェーズ8: アーカイブ

#### A. 旧バージョン
| 移動元 | 移動先 |
|--------|--------|
| web_ui.py | archive/old_versions/web_ui_old.py |
| Makefile.new | archive/old_versions/Makefile.new |

#### B. 非推奨ファイル
| 移動元 | 移動先 |
|--------|--------|
| start_web_ui.py | archive/deprecated/start_web_ui.py |

---

## 4. import文・参照の影響分析

### 4.1 Python Import文の影響

#### 影響を受けるファイル（19ファイル確認済み）

1. **security_qa_cli.py** - 2箇所
2. **test_backend_api.py** - 1箇所
3. **example_usage.py** - 1箇所
4. **dashboard_main.py** - 8箇所
5. **web_ui.py** - 3箇所
6. **release_notifier.py** - 4箇所
7. **test_phase2_implementation.py** - 4箇所
8. **test_notification.py** - 5箇所
9. **test_email_delivery.py** - 3箇所
10. **tests/test_filtering.py** - 1箇所
11. **tests/test_enhanced_backend_integration.py** - 6箇所
12. **tests/test_database_fixed.py** - 1箇所
13. **tests/test_security_comprehensive.py** - 3箇所
14. **tests/test_qa_comprehensive.py** - 1箇所
15. **tests/test_anilist_api.py** - 1箇所
16. **tests/test_mailer_integration.py** - 1箇所
17. **tests/test_google_apis.py** - 2箇所
18. **scripts/send_pending_notifications.py** - 1箇所
19. **modules/security_compliance.py** - 1箇所

**合計**: 49箇所の`from modules`インポート

#### 修正方針

**modulesディレクトリは移動しない** ため、ルート直下から移動するファイルのインポートパスを調整する必要があります。

##### 例: app/release_notifier.py

```python
# 移動前（ルート直下）
from modules import get_config
from modules.db import DatabaseManager

# 移動後（app/配下）
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules import get_config
from modules.db import DatabaseManager
```

または、相対インポートを使用:

```python
# app/release_notifier.py
import sys
sys.path.append('..')

from modules import get_config
from modules.db import DatabaseManager
```

##### 例: tests/e2e/test_backend_api.py

```python
# 移動前
from modules.backend_validator import validate_backend

# 移動後
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from modules.backend_validator import validate_backend
```

### 4.2 シェルスクリプトのパス参照影響

#### 影響例

##### scripts/startup/quick_start.sh（移動後）

```bash
# 移動前
python3 web_app.py

# 移動後
python3 ../../app/web_app.py
```

または、プロジェクトルートへの移動を追加:

```bash
#!/bin/bash
cd "$(dirname "$0")/../.."  # プロジェクトルートへ
python3 app/web_app.py
```

### 4.3 設定ファイルのパス参照

#### config/config.json

```json
{
  "database_path": "../data/db.sqlite3"
}
```

#### 環境変数の更新

```bash
# .env
DATABASE_PATH=./data/db.sqlite3
LOG_DIR=./logs
```

---

## 5. 移行リスクと軽減策

### 5.1 リスク評価

| リスク | 深刻度 | 確率 | 軽減策 |
|--------|--------|------|--------|
| インポートパスの破損 | 高 | 中 | 自動テスト、段階的移行 |
| スクリプト実行エラー | 中 | 中 | パス正規化、テスト実行 |
| 既存データの消失 | 高 | 低 | 完全バックアップ |
| CI/CDパイプラインの破損 | 中 | 低 | .github/workflows更新 |

### 5.2 軽減策詳細

#### A. 完全バックアップの実施

```bash
bash backup_full.sh
```

#### B. Git作業ブランチの作成

```bash
git checkout -b refactor/folder-structure
```

#### C. 段階的な移行

1. フェーズ1: ディレクトリ作成
2. フェーズ2: コピー（移動ではなく）
3. フェーズ3: インポートパス修正
4. フェーズ4: テスト実行
5. フェーズ5: 問題なければ元ファイル削除

#### D. 自動テストによる検証

各フェーズ後に以下を実行:

```bash
pytest tests/ -v
python3 tools/validation/validate_system.py
```

#### E. シンボリックリンクによる互換性維持（一時的）

```bash
# 例: web_app.pyへのシンボリックリンク
ln -s app/web_app.py web_app.py
```

移行完了後に削除。

---

## 6. 実装手順

### 6.1 準備フェーズ

1. **完全バックアップ**
   ```bash
   bash backup_full.sh
   git add -A
   git commit -m "[バックアップ] フォルダ構造整理前のスナップショット"
   ```

2. **作業ブランチ作成**
   ```bash
   git checkout -b refactor/folder-structure-reorganization
   ```

3. **ベースラインテスト**
   ```bash
   pytest tests/ -v > output/baseline_tests.txt
   ```

### 6.2 実装フェーズ

#### ステップ1: ディレクトリ構造作成スクリプト

```bash
bash scripts/create_new_structure.sh
```

#### ステップ2: ファイル移動スクリプト（自動化）

```bash
bash scripts/migrate_files.sh --phase 1  # アプリケーション
bash scripts/migrate_files.sh --phase 2  # 認証
bash scripts/migrate_files.sh --phase 3  # テスト
bash scripts/migrate_files.sh --phase 4  # ツール
bash scripts/migrate_files.sh --phase 5  # スクリプト
bash scripts/migrate_files.sh --phase 6  # データ
```

#### ステップ3: インポートパス自動修正

```bash
python3 tools/setup/fix_import_paths.py
```

#### ステップ4: 検証テスト

```bash
pytest tests/ -v
python3 tools/validation/validate_system.py
bash scripts/maintenance/check_tests.sh
```

#### ステップ5: クリーンアップ

```bash
# シンボリックリンク削除
find . -maxdepth 1 -type l -delete

# 空ディレクトリ削除
find . -type d -empty -delete
```

### 6.3 検証フェーズ

1. **機能テスト**
   - Web UIの起動確認
   - リリース通知の実行確認
   - ダッシュボードの動作確認

2. **統合テスト**
   ```bash
   pytest tests/integration/ -v
   ```

3. **E2Eテスト**
   ```bash
   pytest tests/e2e/ -v
   ```

4. **パフォーマンステスト**
   ```bash
   python3 tools/monitoring/performance_benchmark.py
   ```

### 6.4 デプロイフェーズ

1. **ドキュメント更新**
   - README.md
   - CLAUDE.md
   - docs/内の各種ドキュメント

2. **CI/CD設定更新**
   - .github/workflows/の各種ワークフロー

3. **マージ**
   ```bash
   git add -A
   git commit -m "[リファクタリング] フォルダ構造の整理完了"
   git checkout main
   git merge refactor/folder-structure-reorganization
   git push origin main
   ```

---

## 7. 今後の保守方針

### 7.1 フォルダ配置ルール

| ディレクトリ | 用途 | 配置基準 |
|--------------|------|----------|
| app/ | メインアプリケーション | Flask、エントリポイント |
| modules/ | コアロジック | ビジネスロジック、データアクセス |
| tests/ | テストコード | 全てのテスト |
| tools/ | 開発ツール | CLI、監視、修復、バリデーション |
| scripts/ | 運用スクリプト | 起動、セットアップ、メンテナンス |
| config/ | 設定 | JSON、YAML、.env |
| data/ | データ | DB、バックアップ |
| reports/ | レポート | JSON形式のレポート |
| output/ | 一時出力 | テキスト出力、カバレッジ |
| docs/ | ドキュメント | Markdown |
| bin/ | 実行エントリ | ユーザー向けコマンド |

### 7.2 ファイル命名規則

- **Pythonモジュール**: `snake_case.py`
- **テストファイル**: `test_*.py`
- **スクリプト**: `動詞_目的語.sh` (例: `start_web.sh`)
- **設定ファイル**: `名詞.json` または `.env`
- **ドキュメント**: `大文字始まり.md`

### 7.3 定期的なメンテナンス

1. **月次レビュー**: ルート直下のファイル数をチェック
2. **四半期リファクタリング**: 非推奨ファイルのarchive化
3. **年次クリーンアップ**: archive/の削除可能ファイル確認

---

## 8. 成功基準

### 8.1 定量的指標

- [ ] ルート直下のファイル数: 115個 → 30個以下
- [ ] テスト成功率: 100%維持
- [ ] ビルド時間: 変化なし（±5%以内）
- [ ] コードカバレッジ: 低下なし

### 8.2 定性的指標

- [ ] 新規開発者が5分以内にプロジェクト構造を理解できる
- [ ] ファイル検索時間が50%削減
- [ ] コードレビューの効率が向上
- [ ] CI/CDパイプラインが正常動作

---

## 9. 付録

### 9.1 自動化スクリプト例

#### scripts/create_new_structure.sh

```bash
#!/bin/bash
set -e

echo "Creating new directory structure..."

mkdir -p app
mkdir -p auth/token_generators
mkdir -p scripts/{startup,setup,maintenance}
mkdir -p tools/{monitoring,repair,validation,linting,setup}
mkdir -p tests/{unit,integration,e2e,security,runners,utilities,fixtures}
mkdir -p bin
mkdir -p data/backups
mkdir -p reports
mkdir -p output
mkdir -p systemd
mkdir -p database/migrations
mkdir -p archive/{old_versions,deprecated}

echo "Directory structure created successfully."
```

#### tools/setup/fix_import_paths.py

```python
#!/usr/bin/env python3
"""
Automatically fix import paths after folder restructuring
"""

import os
import re
from pathlib import Path

def fix_imports_in_file(file_path, depth):
    """
    Fix import statements based on new directory depth
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Add sys.path adjustment at the top
    if 'from modules' in content or 'import modules' in content:
        sys_path_insert = f"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent{''.join(['.parent'] * depth)}))
"""
        # Insert after shebang and docstring
        lines = content.split('\n')
        insert_pos = 0
        for i, line in enumerate(lines):
            if line.startswith('#!') or line.startswith('"""'):
                continue
            if line.strip() and not line.startswith('#'):
                insert_pos = i
                break

        lines.insert(insert_pos, sys_path_insert)
        content = '\n'.join(lines)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def main():
    # app/ ディレクトリ (depth=1)
    for file in Path('app').glob('*.py'):
        fix_imports_in_file(file, 1)

    # tests/ サブディレクトリ (depth=2)
    for subdir in ['unit', 'integration', 'e2e', 'security', 'runners', 'utilities']:
        for file in Path(f'tests/{subdir}').glob('*.py'):
            fix_imports_in_file(file, 2)

    # tools/ サブディレクトリ (depth=2)
    for subdir in ['monitoring', 'repair', 'validation', 'linting', 'setup']:
        for file in Path(f'tools/{subdir}').glob('*.py'):
            fix_imports_in_file(file, 2)

    print("Import paths fixed successfully.")

if __name__ == '__main__':
    main()
```

### 9.2 検証チェックリスト

```markdown
## 移行後検証チェックリスト

### 基本動作確認
- [ ] Web UI起動 (`python3 app/web_app.py`)
- [ ] リリース通知実行 (`python3 app/release_notifier.py --dry-run`)
- [ ] ダッシュボード起動 (`python3 app/dashboard_main.py`)

### テスト実行
- [ ] ユニットテスト (`pytest tests/unit/ -v`)
- [ ] 統合テスト (`pytest tests/integration/ -v`)
- [ ] E2Eテスト (`pytest tests/e2e/ -v`)
- [ ] セキュリティテスト (`pytest tests/security/ -v`)

### スクリプト実行
- [ ] 起動スクリプト (`bash scripts/startup/quick_start.sh`)
- [ ] セットアップスクリプト (`bash scripts/setup/setup_env.sh`)
- [ ] バックアップスクリプト (`bash scripts/maintenance/backup_full.sh`)

### ツール実行
- [ ] 監視ツール (`python3 tools/monitoring/check_structure.py`)
- [ ] バリデーション (`python3 tools/validation/validate_system.py`)
- [ ] Linting (`python3 tools/linting/auto_fix_lint.py`)

### CI/CD
- [ ] GitHub Actions ワークフロー実行確認
- [ ] ビルド成功
- [ ] デプロイ成功

### ドキュメント
- [ ] README.md 更新確認
- [ ] CLAUDE.md 更新確認
- [ ] API ドキュメント整合性確認
```

---

## 10. まとめ

本提案により、以下の効果が期待できます:

1. **可読性向上**: 論理的なフォルダ構造により、ファイルの役割が明確に
2. **保守性向上**: 関連ファイルのグルーピングにより、変更影響範囲が明確に
3. **開発効率向上**: ファイル検索時間の削減、新規開発者のオンボーディング短縮
4. **品質向上**: テスト構造の整理により、テスト戦略が明確に
5. **拡張性向上**: 新機能追加時の配置場所が明確に

**推奨実施時期**: 次回メジャーリリース前
**想定作業時間**: 8-12時間（自動化スクリプト使用時）
**リスクレベル**: 中（適切なバックアップと段階的移行により軽減可能）

---

**文書バージョン**: 1.0
**作成日**: 2025-11-14
**作成者**: System Architecture Designer (Claude)
**承認者**: （未承認）
