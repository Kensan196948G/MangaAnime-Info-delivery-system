# Claude Code スラッシュコマンド

このディレクトリには、Claude Codeで使用できるカスタムスラッシュコマンドが含まれています。

## 利用可能なコマンド

### `/commit-push-pr`

変更のコミット、プッシュ、Pull Request作成を一連で実行します。

#### 使い方

```
/commit-push-pr
```

このコマンドを実行すると、Claudeが以下を自動的に行います：

1. ✅ 変更ファイルの確認と分析
2. ✅ 適切なコミットメッセージの生成
3. ✅ 変更のステージングとコミット
4. ✅ リモートリポジトリへのプッシュ
5. ✅ Pull Requestの作成

#### 実行例

```
ユーザー: /commit-push-pr

Claude:
変更内容を確認しています...
[git status と git diff の実行]

以下のファイルが変更されています：
- modules/anime_syoboi.py (新規)
- modules/manga_rss_enhanced.py (新規)
- tests/test_enhanced_backend_integration.py (新規)
...

コミットメッセージを作成しています...
[機能追加] 新規データソースとバックエンド強化機能を追加

- しょぼいカレンダーAPI統合
- 拡張マンガRSSコレクター実装
- 統合テスト追加

変更をコミットしています...
✅ コミット完了 (abc1234)

リモートにプッシュしています...
✅ プッシュ完了

Pull Requestを作成しています...
✅ PR作成完了
   URL: https://github.com/user/repo/pull/123
```

#### 前提条件

- Git リポジトリが初期化されている
- リモートリポジトリが設定されている
- GitHub CLI (`gh`) がインストール・認証済み

#### 注意事項

- **機密情報のチェック**: .env、token.json等の機密ファイルは自動的に除外されます
- **ブランチ確認**: main/masterブランチへの直接コミットは警告が表示されます
- **pre-commitフック**: フックが設定されている場合、失敗時は内容を確認して対応します

#### エラー対処

**GitHub CLIがない場合:**
```bash
# Windows (winget)
winget install GitHub.cli

# または公式サイトからダウンロード
# https://cli.github.com/
```

**認証が必要な場合:**
```bash
gh auth login
```

**リモートとの差異がある場合:**
コマンド実行前に以下を実行：
```bash
git pull --rebase
```

## コマンドのカスタマイズ

各コマンドは `.claude/commands/<コマンド名>.md` ファイルで定義されています。
必要に応じて内容を編集できます。

## 新しいコマンドの追加

1. `.claude/commands/` に新しい `.md` ファイルを作成
2. ファイル名がコマンド名になります（例: `test.md` → `/test`）
3. ファイル内にClaude への指示を記述

### 例: `/test` コマンド

`.claude/commands/test.md`:
```markdown
# Run Tests

すべてのテストを実行し、結果を報告してください。

pytest tests/ -v --cov=modules --cov-report=term
```

## 関連ドキュメント

- [Claude Code ドキュメント](https://docs.claude.com/claude-code)
- [スラッシュコマンドガイド](https://docs.claude.com/claude-code/slash-commands)
