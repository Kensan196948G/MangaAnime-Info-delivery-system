# タスク完了時のチェックリスト

## コード変更後
1. **型ヒントの確認**: 全ての関数/メソッドに型ヒントがあるか
2. **Docstringsの確認**: 新規/変更した関数にdocstringがあるか
3. **エラーハンドリング**: 適切な例外処理が実装されているか

## テスト実行
```bash
# 必須: 全テスト実行
pytest tests/ -v

# カバレッジ確認（20%以上必須）
pytest tests/ --cov=modules --cov-report=term-missing --cov-fail-under=20
```

## コード品質
```bash
# リンター（もし設定されていれば）
# flake8 modules/
# mypy modules/
```

## データベース変更がある場合
- `modules/db.py` の `initialize_database` メソッドでスキーマ更新を確認
- 既存データとの互換性を確認
- マイグレーションスクリプトが必要かどうか検討

## 設定変更がある場合
- `config.json` の更新
- `config.schema.json` の更新（スキーマ変更時）

## Git操作
```bash
git status
git diff
git add <files>
git commit -m "適切なコミットメッセージ"
```

## ドキュメント更新
- README.mdの更新（機能追加時）
- CLAUDE.mdの更新（開発プロセス変更時）
