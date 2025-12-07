# GitHub Actions Issueコメント投稿失敗 - 修正レポート

**作成日**: 2025-11-15
**ステータス**: 修正完了
**優先度**: 高

---

## 問題の概要

GitHub Actions ワークフロー `auto-error-detection-repair.yml` の「成功時にIssueコメント」ステップが `SyntaxError: Invalid or unexpected token` で失敗していました。

### 影響範囲
- ワークフロー実行ID: 19380963660
- 失敗ステップ: 成功時にIssueコメント（ステップ10）
- エラー行: line 58 (github-script内)

---

## 根本原因

### 1. JavaScriptテンプレートリテラル内のエスケープ問題

**問題のコード (修正前)**:
```yaml
script: |
  const data = JSON.parse(fs.readFileSync('repair_summary.json', 'utf8'));
  comment = \`
  ## ✅ 自動修復完了

  **実行ループ数**: \${data.total_loops || 0} / \${process.env.MAX_LOOPS}
  **成功した修復**: \${data.successful_repairs || 0}
  \`;
```

**エラー原因**:
- YAML内に埋め込まれたJavaScriptのテンプレートリテラル `${...}` が、YAMLパーサーによって GitHub式 `${{ }}` として誤解釈される
- バックスラッシュによるエスケープ `\${...}` は、YAMLとJavaScriptの二重解釈で構文エラーを引き起こす
- 特に複数行テンプレートリテラル内での `$` の扱いが不適切

### 2. 同様の問題が2箇所に存在

- **失敗時にIssue作成** ステップ (行172-241)
- **成功時にIssueコメント** ステップ (行222-270)

---

## 修正内容

### 戦略: テンプレートリテラル内の変数を事前に抽出

テンプレートリテラル内で直接 `${data.property}` を使う代わりに、変数に代入してから使用することで、YAMLとの競合を回避。

### 修正後のコード (成功時にIssueコメント)

```javascript
// 変数を事前に抽出
const totalLoops = data.total_loops || 0;
const successfulRepairs = data.successful_repairs || 0;
const detectedErrors = data.detected_errors?.length || 0;
const maxLoops = process.env.MAX_LOOPS;

// エスケープ不要なテンプレートリテラル
comment = `## ✅ 自動修復完了

**実行ループ数**: ${totalLoops} / ${maxLoops}
**成功した修復**: ${successfulRepairs}
**検出エラー数**: ${detectedErrors}

すべてのエラーが修復されました 🎉`;
```

### 修正後のコード (失敗時にIssue作成)

複雑な配列処理（`.map()`）も事前に文字列として整形：

```javascript
// エラー情報の整形
let errorsText = 'なし';
if (data.detected_errors && data.detected_errors.length > 0) {
  errorsText = data.detected_errors.map(e => `- ${e.type}: ${e.message}`).join('\n');
}

// 修復試行履歴の整形
let attemptsText = 'なし';
if (data.repair_attempts && data.repair_attempts.length > 0) {
  attemptsText = data.repair_attempts.map((a, i) => {
    const result = a.success ? '✅ 成功' : '❌ 失敗';
    const errorLine = a.error ? `\n- **エラー**: ${a.error}` : '';
    return `#### ループ ${i + 1}\n- **時刻**: ${a.timestamp}\n- **アクション**: ${a.action}\n- **結果**: ${result}${errorLine}`;
  }).join('\n\n');
}

// テンプレートリテラル内で整形済み変数を使用
summary = `## 🚨 自動修復失敗レポート

**実行日時**: ${timestamp}
**実行ループ数**: ${totalLoops} / ${maxLoops}

### 検出されたエラー
${errorsText}

### 修復試行履歴
${attemptsText}`;
```

---

## 修正ファイル

- **ファイル**: `.github/workflows/auto-error-detection-repair.yml`
- **修正箇所**:
  - 行172-241: 失敗時にIssue作成ステップ
  - 行222-270: 成功時にIssueコメントステップ

---

## 検証結果

### YAML構文チェック
```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/auto-error-detection-repair.yml'))"
# 結果: ✅ YAML構文: OK
```

### 改善点
1. **エスケープの問題解消**: `\${...}` を使わず、変数分離で解決
2. **可読性向上**: ロジックと表示の分離により、コードが読みやすく
3. **保守性向上**: 変数名により意図が明確化
4. **エラーハンドリング強化**: データ存在チェックを事前に実施

---

## 今後の推奨事項

### 1. GitHub Actionsでのベストプラクティス

**YAML内JavaScript記述時の注意点**:
```yaml
# ❌ 避けるべき記述
script: |
  const msg = `Value: \${data.value}`;  # YAMLとの競合リスク

# ✅ 推奨記述
script: |
  const value = data.value;
  const msg = `Value: ${value}`;  # 変数を事前抽出
```

### 2. テンプレートリテラル使用時のルール

- YAML内で複雑なテンプレートリテラルを使う場合は、変数を事前抽出
- `${...}` のエスケープ（`\${...}`）は予測困難な動作を引き起こすため避ける
- 複数行にまたがるテンプレートリテラルは特に注意

### 3. CI/CD改善案

```bash
# ワークフローYAML検証をpre-commitフックに追加
yamllint .github/workflows/*.yml
actionlint .github/workflows/*.yml
```

---

## 関連資料

- [GitHub Actions - github-script](https://github.com/actions/github-script)
- [YAML Multiline Strings](https://yaml-multiline.info/)
- [MDN - Template literals](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Template_literals)

---

## チェックリスト

- [x] エラー原因の特定
- [x] ワークフローファイルの修正
- [x] YAML構文検証
- [x] エラーハンドリング改善
- [x] ドキュメント作成
- [ ] 本番環境での動作確認（次回ワークフロー実行時）

---

**修正者**: Claude Code
**レビュー**: 未実施
**承認**: 未実施
