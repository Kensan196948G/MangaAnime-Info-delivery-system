# 推奨コマンド一覧

## 開発環境セットアップ
```bash
# 依存パッケージインストール
pip install -r requirements.txt
pip install -r requirements-test.txt  # テスト用

# Makefileによるセットアップ
make dev-setup
```

## テスト実行
```bash
# 全テスト実行
pytest tests/ -v

# カバレッジ付きテスト
pytest tests/ --cov=modules --cov-report=term-missing

# 特定マーカーのテスト
pytest -m "unit"        # ユニットテストのみ
pytest -m "integration" # 統合テストのみ
pytest -m "not slow"    # 遅いテストを除外
```

## アプリケーション実行
```bash
# データ収集
make collect

# データ検証
make verify

# 全処理実行（収集→検証）
make full

# 状態確認
make status
```

## データベース操作
```bash
# バックアップ
make backup-db

# リストア
make restore-db

# SQLite直接操作
sqlite3 db.sqlite3
```

## ログ管理
```bash
# 古いログ削除
make clean
```

## Git操作
```bash
git status
git diff
git log --oneline -10
```

## 開発Tips
- Python 3.xが必要
- pytestで実行時、`--cov-fail-under=20` により最低20%のカバレッジが必須
- `pytest.ini` に詳細設定あり
