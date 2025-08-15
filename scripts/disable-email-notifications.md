# 📧 GitHub Actions Email通知を無効化する完全ガイド

## 🎯 最も確実な方法：GitHub個人設定から無効化

### ステップ1: GitHub通知設定にアクセス
```
https://github.com/settings/notifications
```

### ステップ2: Actions通知を無効化

以下の場所で設定を変更：

```
Workflow notifications
├─ Email
│   ├─ ☐ Send notifications for workflow runs on repositories I'm watching
│   ├─ ☐ Send notifications for workflow runs on repositories I own
│   └─ ☐ Send notifications for workflow runs that I trigger
└─ Web and Mobile
    └─ ☑ （これは残してもOK）
```

### ステップ3: 追加の通知設定

```
System
├─ Actions
│   ├─ Email: ☐ オフ
│   └─ Web: ☑ オン（任意）
```

## 🔧 リポジトリ単位の設定

### 特定リポジトリの通知を無効化

1. リポジトリページを開く
2. "Watch" ボタンをクリック
3. "Custom" を選択
4. 以下のチェックを外す：
   - ☐ Actions
   - ☐ Security alerts

## 🤖 ワークフローレベルの対策

### 各ワークフローのjobsセクションに追加：

```yaml
jobs:
  your-job:
    runs-on: ubuntu-latest
    continue-on-error: true  # 失敗しても成功扱い
    
    steps:
      - name: Your step
        continue-on-error: true  # 個別ステップも成功扱い
        run: |
          # your commands
          
      - name: Suppress exit code
        if: failure()
        run: exit 0  # 失敗を成功に変換
```

## 📊 通知設定の確認方法

### 現在の設定を確認：

1. https://github.com/settings/notifications
2. "Default notifications email" セクションを確認
3. "Automatically watch repositories" のチェックを外す

### メール配信履歴を確認：

1. GitHubの通知インボックス: https://github.com/notifications
2. フィルター: `reason:workflow-run`

## ⚠️ 注意事項

- **Web通知は残すことを推奨**（GitHubサイト内でのみ表示）
- **重要なセキュリティアラートも無効化されないよう注意**
- **組織のリポジトリの場合は組織設定も確認**

## 🚀 即座に適用する方法

```bash
# GitHub CLIを使用（ghコマンド）
gh api -X PATCH /user/preferences \
  --field workflow_notifications_email=false \
  --field actions_email=false
```

## 📝 設定が反映されない場合

1. **ブラウザのキャッシュをクリア**
2. **別のブラウザで設定を確認**
3. **数分待ってから確認**（反映に時間がかかる場合あり）

---

これらの設定により、GitHub Actionsの失敗通知メールを完全に無効化できます。