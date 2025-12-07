# Print文からLoggingモジュールへの変換ガイド

## 概要

このドキュメントは、プロジェクト内の全print文をPythonの標準loggingモジュールに変換するプロセスを説明します。

**目的**: 約2,499箇所のprint文を適切なloggingレベルに自動変換

## 変換ツール

### 1. 変換スクリプト
- **ファイル**: `/scripts/convert_print_to_logging.py`
- **機能**: print文を自動的にlogging呼び出しに変換
- **バックアップ**: 変更前に全ファイルを自動バックアップ

### 2. 検証スクリプト
- **ファイル**: `/scripts/verify_logging_conversion.py`
- **機能**: 変換の完全性を検証、残存print文を検出

### 3. 実行スクリプト
- **ファイル**: `/scripts/run_logging_conversion.sh`
- **機能**: 完全な変換プロセスを自動実行

## 変換ルール

### 基本変換パターン

| 変換前 | 変換後 | 理由 |
|--------|--------|------|
| `print("...")` | `logger.info("...")` | 一般的な情報出力 |
| `print(f"Error: {e}")` | `logger.error(f"Error: {e}")` | エラー情報 |
| `print("Warning: ...")` | `logger.warning("Warning: ...")` | 警告メッセージ |
| `print("DEBUG: ...")` | `logger.debug("DEBUG: ...")` | デバッグ情報 |
| `print("Success!")` | `logger.info("Success!")` | 成功メッセージ |

### 詳細な変換ルール

#### エラー系
```python
# 変換前
print(f"Error: {error_message}")
print("ERROR: Failed to connect")
print(f"Failed to load {file_name}")
print(f"Exception occurred: {e}")

# 変換後
logger.error(f"Error: {error_message}")
logger.error("ERROR: Failed to connect")
logger.error(f"Failed to load {file_name}")
logger.error(f"Exception occurred: {e}")
```

#### 警告系
```python
# 変換前
print("Warning: Configuration missing")
print("WARNING: Deprecated function")

# 変換後
logger.warning("Warning: Configuration missing")
logger.warning("WARNING: Deprecated function")
```

#### デバッグ系
```python
# 変換前
print(f"DEBUG: Variable value = {value}")
print("Debug: Entering function")

# 変換後
logger.debug(f"DEBUG: Variable value = {value}")
logger.debug("Debug: Entering function")
```

#### 情報系（デフォルト）
```python
# 変換前
print("Processing started")
print(f"User {username} logged in")
print("Success: Data saved")

# 変換後
logger.info("Processing started")
logger.info(f"User {username} logged in")
logger.info("Success: Data saved")
```

## 自動セットアップ

変換スクリプトは自動的に以下を追加します：

```python
import logging

logger = logging.getLogger(__name__)
```

### セットアップの配置ルール

1. **インポートセクション**: 既存のimport文の後に`import logging`を追加
2. **ロガーインスタンス**: インポートセクション後に`logger = logging.getLogger(__name__)`を追加
3. **docstring考慮**: モジュールdocstringがある場合はその後に配置

## 使用方法

### 完全自動実行（推奨）

```bash
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system
bash scripts/run_logging_conversion.sh
```

このスクリプトは以下を実行します：

1. **事前検証**: 現在のprint文の数を確認
2. **バックアップ作成**: 変更前のファイルをバックアップ
3. **変換実行**: print文をloggingに変換
4. **事後検証**: 変換結果を検証
5. **レポート生成**: 詳細なレポートを生成

### 個別実行

#### ステップ1: 事前検証
```bash
python3 scripts/verify_logging_conversion.py \
    --project-root /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system \
    --save-report
```

#### ステップ2: 変換実行
```bash
python3 scripts/convert_print_to_logging.py \
    --project-root /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system
```

#### ステップ3: 事後検証
```bash
python3 scripts/verify_logging_conversion.py \
    --project-root /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system \
    --save-report \
    --generate-fix
```

### ドライラン（変更なし）

```bash
python3 scripts/convert_print_to_logging.py \
    --project-root /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system \
    --dry-run
```

## バックアップとロールバック

### 自動バックアップ

変換実行時、全ファイルは自動的にバックアップされます：

```
/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/backups/
└── print_conversion_20250807_143025/
    ├── app/
    ├── modules/
    └── scripts/
```

### ロールバック手順

変換に問題があった場合、簡単にロールバックできます：

```bash
python3 scripts/convert_print_to_logging.py --rollback
```

これにより、最新のバックアップから全ファイルが復元されます。

## 対象範囲

### 対象ディレクトリ
- `app/` - アプリケーションコード
- `modules/` - モジュールコード
- `scripts/` - スクリプト

### 除外ディレクトリ
- `tests/` - テストコード（print文を保持）
- `__pycache__/` - キャッシュファイル
- `venv/` - 仮想環境
- `.git/` - Git管理ファイル
- `backups/` - バックアップディレクトリ

## レポート

### 生成されるレポート

変換完了後、以下のレポートが生成されます：

```
/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/reports/logging_conversion/
├── pre_conversion_report.txt      # 変換前の状態
├── conversion_log.txt              # 変換ログ
├── post_conversion_report.txt      # 変換後の検証結果
└── ROLLBACK_INSTRUCTIONS.txt       # ロールバック手順
```

### レポート内容

#### 変換統計
```
Conversion Statistics
====================
Total Files Scanned:    127
Files Converted:        89
Total Print Statements: 2,499
Errors:                 0
```

#### 検証レポート
```
Verification Report
===================
Total Files Scanned:        127
Files Clean:                127
Files with Issues:          0
Success Rate:               100.00%

Remaining Print Statements: 0
Files with Prints:          0
Files without Logger:       0
```

## トラブルシューティング

### 変換が失敗する場合

#### 1. ファイルエンコーディングエラー
```bash
# UTF-8エンコーディングを確認
file -i app/your_file.py

# 必要に応じて変換
iconv -f ISO-8859-1 -t UTF-8 app/your_file.py > app/your_file_utf8.py
```

#### 2. 構文エラー
```bash
# 変換前にPythonファイルの構文を確認
python3 -m py_compile app/your_file.py
```

#### 3. 残存print文
```bash
# 残存print文を手動確認
grep -r "print(" app/ modules/ scripts/ --include="*.py"

# 修正スクリプトを生成
python3 scripts/verify_logging_conversion.py --generate-fix
```

### よくある問題と解決策

#### 問題1: 一部のprint文が変換されない

**原因**: 複雑なprint構文や特殊なパターン

**解決策**:
```bash
# 検証スクリプトで残存print文を確認
python3 scripts/verify_logging_conversion.py

# 手動で修正
vim app/problem_file.py
```

#### 問題2: ロガーインスタンスが重複

**原因**: 既存のロガー設定と競合

**解決策**:
```python
# 重複を削除（手動）
# Before:
logger = logging.getLogger(__name__)
logger = logging.getLogger(__name__)  # 重複

# After:
logger = logging.getLogger(__name__)
```

#### 問題3: import文の順序

**原因**: PEP8の順序規則に違反

**解決策**:
```bash
# isortで自動整形
pip install isort
isort app/ modules/ scripts/
```

## ベストプラクティス

### 1. 段階的な変換

大規模プロジェクトの場合、段階的に変換することを推奨：

```bash
# ディレクトリごとに変換
python3 scripts/convert_print_to_logging.py --target-dir app/routes
python3 scripts/convert_print_to_logging.py --target-dir app/utils
python3 scripts/convert_print_to_logging.py --target-dir modules
```

### 2. 変換後のテスト

```bash
# ユニットテストを実行
pytest tests/

# 統合テストを実行
python3 -m pytest tests/integration/
```

### 3. コードレビュー

変換後、以下を確認：

- [ ] 適切なログレベルが使用されているか
- [ ] ログメッセージが明確か
- [ ] 機密情報がログに含まれていないか
- [ ] パフォーマンスに影響がないか

### 4. ログ設定の確認

変換後、ログ設定を確認：

```python
# config/logging_config.py
import logging.config

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'level': 'INFO',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/app.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5,
            'formatter': 'standard',
            'level': 'DEBUG',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'DEBUG',
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
```

## パフォーマンス考慮事項

### ログレベルの最適化

開発環境と本番環境でログレベルを調整：

```python
# 開発環境
logger.setLevel(logging.DEBUG)

# 本番環境
logger.setLevel(logging.INFO)
```

### 遅延評価

大きなオブジェクトのログ出力は遅延評価を使用：

```python
# Bad
logger.debug(f"Large data: {expensive_operation()}")

# Good
logger.debug("Large data: %s", expensive_operation())
```

## 次のステップ

変換完了後の推奨アクション：

1. **ログ収集システムの導入** - ELK Stack、Splunkなど
2. **ログ監視の設定** - アラート、メトリクス
3. **ログローテーション** - logrotateの設定
4. **ログ分析** - パターン検出、異常検知

## 関連ドキュメント

- [Pythonロギング公式ドキュメント](https://docs.python.org/3/library/logging.html)
- [ロギングのベストプラクティス](https://docs.python-guide.org/writing/logging/)
- [PEP 282 - A Logging System](https://www.python.org/dev/peps/pep-0282/)

## サポート

問題が発生した場合：

1. `reports/logging_conversion/`のレポートを確認
2. ロールバックして元の状態に戻す
3. 個別ファイルで手動変換を試す
4. イシューを報告（該当する場合）

## まとめ

このガイドに従うことで、プロジェクト内の全print文を安全かつ効率的にloggingモジュールに変換できます。自動バックアップとロールバック機能により、リスクを最小限に抑えながら変換を実行できます。
