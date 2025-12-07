# Commit, Push, PR, and Merge

以下の手順で、変更をコミット、プッシュ、Pull Request作成、そして自動マージを実行します：

## 実行手順

1. **変更の確認**
   - `git status` で変更ファイルを確認
   - `git diff` で変更内容を確認
   - 機密情報（.env、credentials.json等）が含まれていないか確認

2. **コミットの作成**
   - 変更内容を分析し、適切なコミットメッセージを作成
   - `git add .` でステージング
   - コミット実行

3. **プッシュ**
   - `git push origin <branch-name>`

4. **Pull Request作成**
   - `gh pr create` でPR作成
   - タイトル: コミットメッセージの1行目
   - 本文: 変更内容の詳細

5. **自動マージ**
   - `gh pr merge --auto --squash` で自動マージ設定
   - CIテストが通過したら自動マージ
   - または即座にマージ: `gh pr merge --squash --delete-branch`

## 出力

最後に以下を表示：

```
✅ コミット完了
✅ プッシュ完了  
✅ PR作成完了
✅ 自動マージ設定完了

PR URL: <url>
```
