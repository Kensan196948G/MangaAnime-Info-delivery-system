# 🔐 GitHub Secrets 設定手順書

## 📋 **リポジトリ情報**
- **リポジトリURL:** https://github.com/Kensan196948G/MangaAnime-Info-delivery-system.git
- **アクセス:** Private Repository
- **用途:** MangaAnime情報配信システム

## 🎯 **必要なSecrets一覧**

### 1. **基本認証情報**

| Secret名 | 値 | 説明 |
|----------|----|----- |
| `GMAIL_APP_PASSWORD` | `sxsg mzbv ubsa jtok` | Gmail App Password (通知・配信用) |
| `NOTIFICATION_EMAIL` | `kensan1969@gmail.com` | エラー通知先メールアドレス |
| `SENDER_EMAIL` | `kensan1969@gmail.com` | 配信元メールアドレス |

### 2. **オプション設定**

| Secret名 | 値 | 説明 |
|----------|----|----- |
| `CODECOV_TOKEN` | `(未設定)` | コードカバレッジレポート用 (オプション) |
| `DISCORD_WEBHOOK` | `(未設定)` | Discord通知用 (オプション) |
| `SLACK_WEBHOOK` | `(未設定)` | Slack通知用 (オプション) |

## 🛠️ **設定手順**

### Step 1: GitHub リポジトリにアクセス

1. **リポジトリページを開く**
   ```
   https://github.com/Kensan196948G/MangaAnime-Info-delivery-system
   ```

2. **Settings タブをクリック**

### Step 2: Secrets ページに移動

1. **左サイドバーから選択**
   ```
   Settings → Secrets and variables → Actions
   ```

### Step 3: Repository Secrets を設定

**"New repository secret" ボタンをクリックして以下を順番に設定:**

#### 🔹 Secret 1: GMAIL_APP_PASSWORD
```
Name: GMAIL_APP_PASSWORD
Secret: sxsg mzbv ubsa jtok
```
**説明:** Gmail APIアクセス用のアプリパスワード

#### 🔹 Secret 2: NOTIFICATION_EMAIL
```
Name: NOTIFICATION_EMAIL
Secret: kensan1969@gmail.com
```
**説明:** システムエラー通知先メールアドレス

#### 🔹 Secret 3: SENDER_EMAIL
```
Name: SENDER_EMAIL
Secret: kensan1969@gmail.com
```
**説明:** メール配信元アドレス

### Step 4: 設定確認

設定完了後、以下が表示されることを確認：

```
Repository secrets
✅ GMAIL_APP_PASSWORD         Updated now
✅ NOTIFICATION_EMAIL         Updated now 
✅ SENDER_EMAIL              Updated now
```

## 🔍 **Actions設定確認**

### Actions 有効化確認

1. **Actions タブをクリック**
   ```
   リポジトリ → Actions
   ```

2. **Actions有効化**
   - "I understand my workflows, go ahead and enable them" をクリック

3. **ワークフロー権限設定**
   ```
   Settings → Actions → General
   ```
   
   **推奨設定:**
   ```
   ✅ Allow all actions and reusable workflows
   ✅ Read and write permissions
   ✅ Allow GitHub Actions to create and approve pull requests
   ```

## 📊 **ワークフロー概要**

### 自動実行ワークフロー

| ワークフロー | ファイル | 実行タイミング |
|-------------|----------|---------------|
| **メインCI/CD** | `ci.yml` | Push/PR時、毎日2時 |
| **システムヘルスチェック** | `mangaanime-system-check.yml` | 6時間おき |
| **自動デプロイ** | `auto-deployment.yml` | main branch push |
| **セキュリティ監査** | `security-audit.yml` | 週1回日曜2時 |

### 使用するSecrets

```yaml
# メール通知で使用
${{ secrets.GMAIL_APP_PASSWORD }}
${{ secrets.NOTIFICATION_EMAIL }}
${{ secrets.SENDER_EMAIL }}

# 将来的な拡張で使用予定
${{ secrets.CODECOV_TOKEN }}
${{ secrets.DISCORD_WEBHOOK }}
${{ secrets.SLACK_WEBHOOK }}
```

## 🚨 **セキュリティ注意事項**

### ✅ **推奨事項**
- Secrets は Repository level で設定
- 定期的なパスワード更新
- 不要になったSecretsは削除
- アクセスログの定期確認

### ❌ **禁止事項**
- Secretsの値をコードにハードコーディング
- ログ出力でSecretsを表示
- PRコメントでSecrets情報を共有
- PublicリポジトリでのSecrets使用

## 🔧 **トラブルシューティング**

### よくある問題

#### 1. **Gmail App Password エラー**
```bash
# 症状: SMTP認証失敗
# 対処: Gmail 2段階認証有効化後、新しいApp Password生成
```

#### 2. **Actions権限エラー**
```bash
# 症状: ワークフロー実行権限なし
# 対処: Settings → Actions → General → 権限設定確認
```

#### 3. **Secret参照エラー**
```bash
# 症状: secrets.SECRET_NAME が空
# 対処: Secret名のタイポ確認、大文字小文字チェック
```

### デバッグ方法

#### Secret設定確認
```yaml
# ワークフロー内でのデバッグ（値は表示されない）
- name: Debug Secrets
  run: |
    echo "GMAIL_APP_PASSWORD length: ${#GMAIL_APP_PASSWORD}"
    echo "NOTIFICATION_EMAIL: ${{ secrets.NOTIFICATION_EMAIL }}"
  env:
    GMAIL_APP_PASSWORD: ${{ secrets.GMAIL_APP_PASSWORD }}
```

#### テスト実行
```bash
# 手動ワークフロー実行でテスト
Actions → Select Workflow → Run workflow
```

## 📞 **サポート情報**

### 設定完了チェックリスト

- [ ] GitHub リポジトリアクセス確認
- [ ] Actions タブ有効化
- [ ] 3つのRepository Secrets設定完了
- [ ] ワークフロー権限設定確認
- [ ] 初回ワークフロー実行成功

### 問題発生時の連絡先

```
GitHub Issue: リポジトリのIssuesタブで報告
メール通知: kensan1969@gmail.com でエラー受信確認
ログ確認: Actions → 該当ワークフロー → 詳細ログ
```

---

**🎉 GitHub Secrets 設定完了後、強力なCI/CDパイプラインが稼働開始します！**