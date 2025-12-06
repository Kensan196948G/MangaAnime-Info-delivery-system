# Quick Reference: GitHub Actions github-script エラーハンドリング

## Issue番号の安全な取得

### 基本パターン
```javascript
// Optional chainingでIssue番号を取得
const issueNumber = context.issue?.number || context.payload?.issue?.number;

// 番号が取得できない場合はスキップ
if (!issueNumber) {
  console.log('⚠️ Issue番号が取得できませんでした');
  return;
}
```

### トリガー別の可用性

| トリガー | `context.issue.number` | `context.payload.issue.number` |
|---------|------------------------|-------------------------------|
| `issue_comment` | ✅ 利用可能 | ✅ 利用可能 |
| `issues` | ✅ 利用可能 | ✅ 利用可能 |
| `pull_request` | ✅ 利用可能（PRの場合） | ❌ 利用不可 |
| `schedule` | ❌ 利用不可 | ❌ 利用不可 |
| `workflow_dispatch` | ❌ 利用不可 | ❌ 利用不可 |
| `push` | ❌ 利用不可 | ❌ 利用不可 |

---

## エラーハンドリングテンプレート

### 1. ファイル読み込み + API呼び出し
```javascript
const fs = require('fs');

// 1. Issue番号の検証
const issueNumber = context.issue?.number || context.payload?.issue?.number;
if (!issueNumber) {
  console.log('⚠️ Issue番号が取得できませんでした');
  return;
}

// 2. ファイル読み込み（エラーは無視）
let data = null;
try {
  if (fs.existsSync('data.json')) {
    data = JSON.parse(fs.readFileSync('data.json', 'utf8'));
  }
} catch (error) {
  console.error('⚠️ ファイル読み込みエラー:', error.message);
}

// 3. コメント本文の生成
const comment = data
  ? `詳細情報: ${data.info}`
  : 'デフォルトメッセージ';

// 4. API呼び出し（エラーはワークフロー失敗）
try {
  await github.rest.issues.createComment({
    owner: context.repo.owner,
    repo: context.repo.repo,
    issue_number: issueNumber,
    body: comment
  });
  console.log(`✅ Issue #${issueNumber} にコメント投稿完了`);
} catch (error) {
  console.error('❌ API呼び出しエラー:', error.message);
  core.setFailed(`コメント投稿失敗: ${error.message}`);
}
```

### 2. Issue作成（重複チェック付き）
```javascript
try {
  // 既存Issueをチェック
  const existingIssues = await github.rest.issues.listForRepo({
    owner: context.repo.owner,
    repo: context.repo.repo,
    labels: 'auto-generated',
    state: 'open'
  });

  // 上限チェック
  if (existingIssues.data.length >= 5) {
    console.log('⚠️ 既存Issueが5個以上あるため作成をスキップ');
    return;
  }

  // 新規Issue作成
  const issue = await github.rest.issues.create({
    owner: context.repo.owner,
    repo: context.repo.repo,
    title: 'エラーレポート',
    body: '詳細情報...',
    labels: ['auto-generated', 'bug']
  });

  console.log(`✅ Issue #${issue.data.number} を作成しました`);
} catch (error) {
  console.error('❌ Issue作成エラー:', error.message);
  core.setFailed(`Issue作成失敗: ${error.message}`);
}
```

### 3. PR情報の取得
```javascript
try {
  const prNumber = context.issue?.number || context.payload?.pull_request?.number;

  if (!prNumber) {
    console.log('⚠️ PR番号が取得できませんでした');
    return;
  }

  const { data: pr } = await github.rest.pulls.get({
    owner: context.repo.owner,
    repo: context.repo.repo,
    pull_number: prNumber
  });

  console.log(`✅ PR情報取得: ${pr.title}`);
} catch (error) {
  console.error('❌ PR取得エラー:', error.message);
}
```

---

## よくあるエラーと対処法

### エラー1: `Cannot read property 'number' of undefined`
**原因**: `context.issue`がundefinedのときに`context.issue.number`にアクセス

**修正**:
```javascript
// ❌ Bad
const issueNumber = context.issue.number;

// ✅ Good
const issueNumber = context.issue?.number;
```

### エラー2: `JSON.parse: unexpected character`
**原因**: JSONファイルが不正な形式

**修正**:
```javascript
try {
  const data = JSON.parse(fs.readFileSync('data.json', 'utf8'));
} catch (error) {
  console.error('JSON解析エラー:', error.message);
  // デフォルト値を使用
  const data = { default: true };
}
```

### エラー3: `Resource not accessible by integration`
**原因**: GitHub Tokenの権限不足

**修正**:
```yaml
# workflow YAMLに権限を追加
permissions:
  issues: write
  pull-requests: write
  contents: read
```

### エラー4: `createComment failed with 404`
**原因**: Issue番号が無効、またはIssueが削除済み

**修正**:
```javascript
try {
  // Issueの存在確認
  await github.rest.issues.get({
    owner: context.repo.owner,
    repo: context.repo.repo,
    issue_number: issueNumber
  });

  // コメント投稿
  await github.rest.issues.createComment({...});
} catch (error) {
  if (error.status === 404) {
    console.log('⚠️ Issueが見つかりませんでした');
  } else {
    throw error;
  }
}
```

---

## デバッグテクニック

### 1. Context情報の出力
```javascript
// すべてのcontext情報を出力
console.log('Context:', JSON.stringify(context, null, 2));

// 特定の情報のみ出力
console.log('Event Name:', context.eventName);
console.log('Actor:', context.actor);
console.log('Repo:', `${context.repo.owner}/${context.repo.repo}`);
```

### 2. 条件付きログ出力
```javascript
// 環境変数でデバッグモードを制御
const DEBUG = process.env.DEBUG === 'true';

if (DEBUG) {
  console.log('Debug Info:', { issueNumber, data });
}
```

### 3. ドライランモード
```javascript
const DRY_RUN = process.env.DRY_RUN === 'true';

if (DRY_RUN) {
  console.log('[DRY-RUN] 本来は以下のコメントを投稿します:');
  console.log(comment);
  return;
}

await github.rest.issues.createComment({...});
```

---

## ベストプラクティス

### 1. Early Return パターンを使用
```javascript
// ❌ ネストが深い
if (issueNumber) {
  if (data) {
    if (data.valid) {
      // 処理...
    }
  }
}

// ✅ Early Return
if (!issueNumber) return;
if (!data) return;
if (!data.valid) return;
// 処理...
```

### 2. エラーメッセージを明確に
```javascript
// ❌ 不明瞭
catch (error) {
  console.error('Error:', error);
}

// ✅ 明確
catch (error) {
  console.error('❌ Issue作成エラー:', error.message);
  console.error('スタックトレース:', error.stack);
}
```

### 3. ログレベルを適切に使い分け
```javascript
console.log('✅ 成功: 処理が完了しました');    // 通常の成功
console.log('ℹ️ 情報: データを読み込みました');   // 情報
console.log('⚠️ 警告: ファイルが見つかりません'); // 警告
console.error('❌ エラー: API呼び出しに失敗');  // エラー
```

### 4. リトライロジックを実装
```javascript
async function createCommentWithRetry(options, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await github.rest.issues.createComment(options);
    } catch (error) {
      console.log(`⚠️ リトライ ${i + 1}/${maxRetries}`);
      if (i === maxRetries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
    }
  }
}
```

---

## チェックリスト

作成前に確認:
- [ ] Issue番号の取得にOptional chainingを使用している
- [ ] Issue番号がない場合の処理がある（Early Return）
- [ ] ファイル読み込みはtry-catchで囲んでいる
- [ ] API呼び出しはtry-catchで囲んでいる
- [ ] エラーメッセージが明確である
- [ ] ログ出力が適切なレベルである
- [ ] 必要な権限がworkflow YAMLに設定されている
- [ ] テストケースを考慮している

---

**作成日**: 2025-11-15
**対象**: GitHub Actions github-script アクション
**関連ドキュメント**: `github-actions-issue-comment-fix.md`
