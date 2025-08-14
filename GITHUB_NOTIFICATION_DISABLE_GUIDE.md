# 📧 GitHub 失敗メール通知 完全無効化ガイド

## 🚨 問題
GitHub Actions の失敗時にメール通知が送信され続ける問題を解決します。

## 🎯 解決策
GitHubの **3つのレベル** で通知設定を無効化する必要があります。

---

## 📋 Step 1: リポジトリレベル設定

### 1-1. リポジトリ通知設定
```bash
URL: https://github.com/Kensan196948G/MangaAnime-Info-delivery-system/settings/notifications
```

**無効化する項目:**
- [ ] **Send notifications for failing workflows**
- [ ] **Send notifications for workflow runs**  
- [ ] **Send notifications for approved workflows**
- [ ] **Send notifications for requested reviews**

### 1-2. リポジトリWatch設定
```bash
リポジトリページ → Watch ボタン → Custom
```

**無効化する項目:**
- [ ] **Actions** - Workflow runs and completion status
- [ ] **Issues** - Issues and their comments  
- [ ] **Pull requests** - Pull requests and their comments
- [ ] **Releases** - Published releases

**推奨設定:** `Participating and @mentions` のみ

---

## 📋 Step 2: 個人アカウントレベル設定

### 2-1. 全体通知設定
```bash
URL: https://github.com/settings/notifications
```

### 2-2. Actions 通知セクション
**Email 通知:**
- [ ] **Actions** - Notifications for workflow runs

**Web 通知:**
- [ ] **Actions** - Browser notifications for workflow runs

### 2-3. Repository watching 設定
```
Automatically watch repositories: Never
Automatically watch teams: Never
```

### 2-4. Email 通知の詳細設定
```
Email notification preferences:
☐ Include your own updates
☐ Comments on Issues and Pull Requests  
☐ Pull Request reviews
☐ Pull Request pushes
☐ Actions workflows
```

---

## 📋 Step 3: Organization/Team レベル設定 (該当する場合)

### 3-1. Organization通知
```bash
URL: https://github.com/organizations/YOUR_ORG/settings/notifications
```

### 3-2. Team通知
```bash
URL: https://github.com/orgs/YOUR_ORG/teams/YOUR_TEAM/notifications
```

---

## 🔍 設定確認チェックリスト

### ✅ 確認方法
以下の全ての項目が無効化されていることを確認：

#### リポジトリレベル
```bash
# 設定確認URL
https://github.com/Kensan196948G/MangaAnime-Info-delivery-system/settings/notifications

確認項目:
□ Workflow runs notifications: OFF
□ Failed workflows notifications: OFF  
□ Watch setting: Custom (Actions OFF)
```

#### 個人アカウントレベル  
```bash
# 設定確認URL
https://github.com/settings/notifications

確認項目:
□ Email Actions notifications: OFF
□ Web Actions notifications: OFF
□ Auto-watch repositories: Never
```

---

## 🧪 設定テスト方法

### 意図的な失敗テストの作成
失敗通知設定が正しく無効化されているかテストできます：

```bash
# 1. GitHub Actionsで手動実行
Actions → Auto Error Detection & Fix System → Run workflow

# 2. 意図的にエラーを発生させるテストワークフロー作成
# （オプション - 必要に応じて）
```

### テスト結果の確認
```bash
設定成功の場合:
✅ GitHub Actions 実行失敗
✅ メール通知が送信されない
✅ GitHub上でのみ失敗状況確認可能

設定未完了の場合:
❌ GitHub Actions 実行失敗  
❌ メール通知が依然として送信される
→ 上記設定を再確認
```

---

## 🔧 追加の高度な設定

### GitHub CLI での一括設定
```bash
# GitHub CLI でリポジトリ通知設定
gh api repos/Kensan196948G/MangaAnime-Info-delivery-system/subscription \
  --method PUT \
  --field subscribed=false \
  --field ignored=false

# 個人通知設定の確認  
gh api user/email \
  --jq '.[] | select(.verified==true) | .email'
```

### ブラウザ開発者ツールでの確認
```javascript
// GitHub通知設定の現在値確認
// ブラウザ開発者コンソールで実行
fetch('/settings/notifications')
  .then(response => response.text())
  .then(html => {
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, 'text/html');
    const checkboxes = doc.querySelectorAll('input[type="checkbox"]:checked');
    console.log('有効な通知設定:', Array.from(checkboxes).map(cb => cb.name));
  });
```

---

## 🚨 トラブルシューティング

### よくある問題と解決法

#### 1. **設定したのにまだメールが来る**
```bash
原因: キャッシュまたは設定反映の遅延
解決: 
- ブラウザキャッシュをクリア
- 24時間待機して再確認
- GitHub Support に問い合わせ
```

#### 2. **一部の通知のみ止まらない**  
```bash
原因: 複数レベルで重複設定
解決:
- リポジトリ・個人・Organization全てを確認
- Watch設定を"Participating and @mentions"に変更
```

#### 3. **Organizationレベルで強制有効化されている**
```bash
原因: Organization管理者による強制設定
解決:
- Organization管理者に相談
- 個人リポジトリへの移行検討
```

### GitHub Support への問い合わせテンプレート
```
件名: Disable GitHub Actions failure email notifications

本文:
Hello GitHub Support,

I am unable to disable email notifications for GitHub Actions workflow failures 
in my repository: https://github.com/Kensan196948G/MangaAnime-Info-delivery-system

Settings I have already configured:
- Repository notifications: Disabled workflow notifications
- Personal notifications: Disabled Actions email notifications  
- Repository watch: Set to "Participating and @mentions" only

However, I am still receiving email notifications when workflows fail.
Could you please help me completely disable these notifications?

Repository: Kensan196948G/MangaAnime-Info-delivery-system
Email: kensan1969@gmail.com

Thank you for your assistance.
```

---

## 📊 設定後の期待結果

### ✅ 成功時の状態
```bash
GitHub Actions 失敗時:
✅ GitHub Actions ログに記録される
✅ GitHub UI で失敗状況確認可能
✅ Issue/PR コメントで失敗通知（リポジトリ内のみ）
❌ メール通知は一切送信されない

GitHub Actions 成功時:
✅ 自動修復成功時のみメール通知
✅ GitHub Actions ログに記録される
✅ PR作成通知（リポジトリ内のみ）
```

### 📈 運用上のメリット
- **ノイズ削減**: 重要でない失敗通知の排除
- **集中力向上**: 重要な成功通知にフォーカス  
- **ログ活用**: GitHub上での体系的な失敗管理
- **効率化**: メール整理時間の削減

---

## 📞 サポート

### 設定で困った場合
1. **このガイドの再確認**: 3つのレベル全てをチェック
2. **24時間待機**: 設定反映に時間がかかる場合がある
3. **GitHub Support**: 上記テンプレートで問い合わせ
4. **Issue作成**: このリポジトリで `/help` コマンド使用

### 関連ドキュメント
- **自動化システム**: `AUTO_SYSTEM_GUIDE.md`
- **GitHub Secrets**: `GITHUB_SECRETS_SETUP.md`
- **エラー通知**: `ERROR_NOTIFICATION_GUIDE.md`

---

**🎯 GitHub失敗メール通知を完全に無効化して、ストレスフリーな開発環境を実現！**