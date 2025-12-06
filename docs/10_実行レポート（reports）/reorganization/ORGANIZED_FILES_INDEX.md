# 整理済みファイルインデックス

**更新日**: 2025-12-06
**目的**: 整理後のファイル配置を一覧管理

---

## 📂 scripts/calendar/ (9ファイル)

### カレンダー統合関連スクリプト

| ファイル名 | 種類 | 説明 | 使用例 |
|----------|------|------|--------|
| `setup_calendar.sh` | Bash | カレンダー初期セットアップ | `bash scripts/calendar/setup_calendar.sh` |
| `setup_google_calendar.sh` | Bash | Google Calendar API設定 | `bash scripts/calendar/setup_google_calendar.sh` |
| `finalize_calendar_setup.sh` | Bash | セットアップ最終処理 | `bash scripts/calendar/finalize_calendar_setup.sh` |
| `run_calendar_integration_test.sh` | Bash | カレンダー統合テスト実行 | `bash scripts/calendar/run_calendar_integration_test.sh` |
| `check_calendar_status.py` | Python | カレンダー機能状態確認 | `python3 scripts/calendar/check_calendar_status.py` |
| `enable_calendar.py` | Python | カレンダー機能有効化 | `python3 scripts/calendar/enable_calendar.py` |
| `investigate_calendar.py` | Python | カレンダー設定調査 | `python3 scripts/calendar/investigate_calendar.py` |
| `test_calendar_dry_run.py` | Python | ドライランテスト | `python3 scripts/calendar/test_calendar_dry_run.py` |
| `test_calendar_dryrun.py` | Python | ドライランテスト (重複) | `python3 scripts/calendar/test_calendar_dryrun.py` |

### 推奨実行順序

```bash
# 1. カレンダーセットアップ
bash scripts/calendar/setup_calendar.sh

# 2. Google Calendar API設定
bash scripts/calendar/setup_google_calendar.sh

# 3. セットアップ完了処理
bash scripts/calendar/finalize_calendar_setup.sh

# 4. 状態確認
python3 scripts/calendar/check_calendar_status.py

# 5. 統合テスト
bash scripts/calendar/run_calendar_integration_test.sh
```

---

## 📂 scripts/setup/ (4ファイル)

### プロジェクトセットアップ関連

| ファイル名 | 種類 | 説明 | 使用例 |
|----------|------|------|--------|
| `check_structure.sh` | Bash | プロジェクト構造確認 | `bash scripts/setup/check_structure.sh` |
| `make_executable.sh` | Bash | スクリプトに実行権限付与 | `bash scripts/setup/make_executable.sh` |
| `setup_pytest.ini` | Bash | pytest設定ファイル作成 | `bash scripts/setup/setup_pytest.ini` |
| `setup_tests.sh` | Bash | テスト環境セットアップ | `bash scripts/setup/setup_tests.sh` |

### 初回セットアップ手順

```bash
# 1. プロジェクト構造確認
bash scripts/setup/check_structure.sh

# 2. 実行権限付与
bash scripts/setup/make_executable.sh

# 3. pytest設定
bash scripts/setup/setup_pytest.ini

# 4. テスト環境構築
bash scripts/setup/setup_tests.sh
```

---

## 📂 config/ (3ファイル)

### 設定ファイル

| ファイル名 | 種類 | 説明 | 使用例 |
|----------|------|------|--------|
| `config.production.json` | JSON | 本番環境設定 | アプリ起動時に読み込み |
| `config.schema.json` | JSON Schema | 設定ファイルのスキーマ定義 | 設定バリデーション |
| `env.example` | Env Template | 環境変数テンプレート | `cp config/env.example .env` |

### 設定ファイル使用方法

#### 1. 環境変数設定
```bash
# テンプレートをコピー
cp config/env.example .env

# .envファイルを編集
vim .env
```

#### 2. 本番環境設定
```python
import json

# 設定読み込み
with open('config/config.production.json', 'r') as f:
    config = json.load(f)
```

#### 3. 設定バリデーション
```python
import json
from jsonschema import validate

# スキーマ読み込み
with open('config/config.schema.json', 'r') as f:
    schema = json.load(f)

# 設定ファイル読み込み
with open('config/config.production.json', 'r') as f:
    config = json.load(f)

# バリデーション
validate(instance=config, schema=schema)
```

---

## 📂 tests/ (追加2ファイル)

### テストファイル

| ファイル名 | 種類 | 説明 | テスト対象 |
|----------|------|------|----------|
| `test_new_api_sources.py` | pytest | 新規APIソーステスト | API統合機能 |
| `test_notification_history.py` | pytest | 通知履歴テスト | 通知履歴機能 |

### テスト実行

```bash
# 個別テスト
pytest tests/test_new_api_sources.py -v
pytest tests/test_notification_history.py -v

# 全テスト
pytest tests/ -v
```

---

## 🗑️ 削除されたファイル

### クリーンアップ対象

| ファイル名 | 削除理由 |
|----------|---------|
| `.gitignore_calendar` | メインの`.gitignore`に統合済み |
| `.investigation_script.sh` | 開発時の一時スクリプト |
| `.run_investigation.sh` | 開発時の一時スクリプト |

---

## 📋 ファイル移動マップ

### 移動前 → 移動後

```
ルート/setup_calendar.sh                  → scripts/calendar/setup_calendar.sh
ルート/setup_google_calendar.sh           → scripts/calendar/setup_google_calendar.sh
ルート/finalize_calendar_setup.sh         → scripts/calendar/finalize_calendar_setup.sh
ルート/run_calendar_integration_test.sh   → scripts/calendar/run_calendar_integration_test.sh
ルート/check_calendar_status.py           → scripts/calendar/check_calendar_status.py
ルート/enable_calendar.py                 → scripts/calendar/enable_calendar.py
ルート/investigate_calendar.py            → scripts/calendar/investigate_calendar.py
ルート/test_calendar_dry_run.py           → scripts/calendar/test_calendar_dry_run.py
ルート/test_calendar_dryrun.py            → scripts/calendar/test_calendar_dryrun.py

ルート/check_structure.sh                 → scripts/setup/check_structure.sh
ルート/make_executable.sh                 → scripts/setup/make_executable.sh
ルート/setup_pytest.ini                   → scripts/setup/setup_pytest.ini
ルート/setup_tests.sh                     → scripts/setup/setup_tests.sh

ルート/config.production.json             → config/config.production.json
ルート/config.schema.json                 → config/config.schema.json
ルート/env.example                        → config/env.example

ルート/test_new_api_sources.py            → tests/test_new_api_sources.py
ルート/test_notification_history.py       → tests/test_notification_history.py
```

---

## 🔍 ファイル検索ガイド

### 機能別ファイル検索

#### カレンダー機能
```bash
# カレンダー関連ファイル一覧
ls -lh scripts/calendar/

# カレンダーセットアップスクリプト
find scripts/calendar/ -name "setup*.sh"

# カレンダーテストスクリプト
find scripts/calendar/ -name "test*.py"
```

#### セットアップ機能
```bash
# セットアップ関連ファイル一覧
ls -lh scripts/setup/

# セットアップスクリプト
find scripts/setup/ -name "setup*.sh"
```

#### 設定ファイル
```bash
# 設定ファイル一覧
ls -lh config/

# JSON設定ファイル
find config/ -name "*.json"

# 環境変数テンプレート
find config/ -name "*.example"
```

---

## 📊 ディレクトリ統計

| ディレクトリ | ファイル数 | 合計サイズ | 主な用途 |
|------------|-----------|----------|---------|
| `scripts/calendar/` | 9 | ~50KB | カレンダー統合 |
| `scripts/setup/` | 4 | ~20KB | プロジェクトセットアップ |
| `config/` | 3 | ~10KB | 設定管理 |
| `tests/` (追加) | 2 | ~15KB | テスト |

**合計移動**: 18ファイル
**合計削除**: 3ファイル

---

## 🎯 利用シーン別クイックリファレンス

### シーン1: 新規開発者のオンボーディング

```bash
# 1. プロジェクト構造確認
bash scripts/setup/check_structure.sh

# 2. 環境設定
cp config/env.example .env

# 3. テスト環境セットアップ
bash scripts/setup/setup_tests.sh

# 4. カレンダー機能セットアップ
bash scripts/calendar/setup_calendar.sh
```

### シーン2: カレンダー機能のトラブルシューティング

```bash
# 1. 状態確認
python3 scripts/calendar/check_calendar_status.py

# 2. 設定調査
python3 scripts/calendar/investigate_calendar.py

# 3. ドライランテスト
python3 scripts/calendar/test_calendar_dry_run.py

# 4. 統合テスト
bash scripts/calendar/run_calendar_integration_test.sh
```

### シーン3: 本番環境デプロイ

```bash
# 1. 設定ファイル確認
cat config/config.production.json

# 2. 環境変数設定
cp config/env.example .env
vim .env

# 3. カレンダーセットアップ
bash scripts/calendar/setup_calendar.sh
bash scripts/calendar/finalize_calendar_setup.sh

# 4. デプロイ実行
bash scripts/deploy.sh
```

---

## 🔧 メンテナンス

### 定期チェック (週次)

```bash
# ファイル整合性確認
bash scripts/setup/check_structure.sh

# 実行権限確認
find scripts/ -type f -name "*.sh" ! -executable
```

### 定期クリーンアップ (月次)

```bash
# 未使用ファイル検索
find . -name "*.bak" -o -name "*.tmp" -o -name "*~"

# ログファイル整理
find logs/ -name "*.log" -mtime +30 -delete
```

---

## 📞 問い合わせ先

- **ファイル配置に関する質問**: DevOps Engineer Agent
- **カレンダー機能**: `scripts/calendar/README.md` (作成予定)
- **セットアップ手順**: `docs/QUICKSTART.md`

---

**最終更新**: 2025-12-06
**次回レビュー**: 2025-12-13
