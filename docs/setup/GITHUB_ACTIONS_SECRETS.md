# GitHub Actions シークレット・環境変数設定ガイド

## 📋 概要

このドキュメントでは、GitHub Actions自動修復システムに必要なシークレットと環境変数の設定方法を説明します。

---

## 🔐 必須シークレット

### 1. GITHUB_TOKEN (自動提供)

- **説明**: GitHub Actionsが自動的に提供するトークン
- **用途**:
  - リポジトリへのアクセス
  - Issue/PRの作成・更新
  - ワークフロー実行
- **設定**: **不要**（GitHubが自動提供）
- **権限**: ワークフローファイルの `permissions` セクションで制御

```yaml
permissions:
  contents: write      # コード変更
  issues: write        # Issue操作
  actions: write       # ワークフロー実行
  pull-requests: write # PR操作
  checks: read         # チェック結果読み取り
```

---

## ⚙️ オプションシークレット

以下は、拡張機能を使用する場合に必要となるシークレットです。

### 2. PERSONAL_ACCESS_TOKEN (オプション)

- **説明**: より高度な権限が必要な場合の個人用アクセストークン
- **用途**:
  - プライベートリポジトリへのアクセス
  - 他のリポジトリへのアクセス
  - より高い API レート制限
- **設定方法**:
  1. GitHub Settings > Developer settings > Personal access tokens > Tokens (classic)
  2. "Generate new token" をクリック
  3. 必要な権限を選択:
     - `repo` (フルアクセス)
     - `workflow` (ワークフロー更新)
     - `admin:org` (組織管理、必要に応じて)
  4. トークンをコピー
  5. リポジトリ Settings > Secrets and variables > Actions > New repository secret
  6. 名前: `PERSONAL_ACCESS_TOKEN`、値: コピーしたトークン

### 3. SLACK_WEBHOOK_URL (オプション)

- **説明**: Slack通知用のWebhook URL
- **用途**: 修復失敗時の即時通知
- **設定方法**:
  1. Slack App設定で Incoming Webhook を有効化
  2. Webhook URLを取得
  3. GitHub リポジトリシークレットに追加

### 4. DISCORD_WEBHOOK_URL (オプション)

- **説明**: Discord通知用のWebhook URL
- **用途**: 修復失敗時の即時通知
- **設定方法**:
  1. Discordサーバー設定 > 連携サービス > Webhook
  2. Webhook URLを取得
  3. GitHub リポジトリシークレットに追加

---

## 🌍 環境変数

### ワークフロー内で設定済みの環境変数

以下の環境変数はワークフローファイル内で定義されており、変更不要です。

```yaml
env:
  # デフォルト設定
  DEFAULT_MAX_LOOPS: 10
  REPAIR_INTERVAL_SECONDS: 30
  RETRY_MAX_ATTEMPTS: 3
  RETRY_DELAY_SECONDS: 10

  # ラベル設定
  LABEL_AUTO_REPAIR: 'auto-repair'
  LABEL_IN_PROGRESS: 'repair-in-progress'
  LABEL_COMPLETED: 'repair-completed'
  LABEL_FAILED: 'repair-failed'
  LABEL_CRITICAL: 'critical'

  # タイムアウト設定
  TIMEOUT_CHECKOUT: 5
  TIMEOUT_SETUP: 8
  TIMEOUT_INSTALL: 10
  TIMEOUT_REPAIR: 20
```

### カスタマイズ可能な環境変数

必要に応じて、以下の環境変数を変更できます：

| 変数名 | デフォルト値 | 説明 |
|--------|-------------|------|
| `DEFAULT_MAX_LOOPS` | 10 | 修復ループの最大回数 |
| `REPAIR_INTERVAL_SECONDS` | 30 | 各修復試行の間隔（秒） |
| `RETRY_MAX_ATTEMPTS` | 3 | 依存関係インストールの最大試行回数 |
| `TIMEOUT_REPAIR` | 20 | 修復処理のタイムアウト（分） |

---

## 📝 シークレット設定手順

### リポジトリレベルでの設定

1. GitHubリポジトリページに移動
2. **Settings** タブをクリック
3. 左サイドバーから **Secrets and variables** > **Actions** を選択
4. **New repository secret** をクリック
5. シークレット名と値を入力
6. **Add secret** をクリック

### 組織レベルでの設定（複数リポジトリで共有）

1. GitHub組織ページに移動
2. **Settings** タブをクリック
3. 左サイドバーから **Secrets and variables** > **Actions** を選択
4. **New organization secret** をクリック
5. シークレット名と値を入力
6. アクセス許可するリポジトリを選択
7. **Add secret** をクリック

---

## 🔒 セキュリティベストプラクティス

### 1. 最小権限の原則

- 必要最小限の権限のみを付与
- `GITHUB_TOKEN` で十分な場合は個人アクセストークンを使用しない

### 2. トークンのローテーション

- 定期的にトークンを再生成（推奨: 90日ごと）
- 古いトークンは必ず削除

### 3. シークレットの暗号化

- GitHubは自動的にシークレットを暗号化
- ログに出力されることはない（マスクされる）

### 4. アクセス制御

- リポジトリへのアクセス権限を適切に管理
- 必要なメンバーのみにシークレットへのアクセスを許可

---

## ✅ 設定確認チェックリスト

- [ ] `GITHUB_TOKEN` の権限が適切に設定されている
- [ ] ワークフローファイルが `.github/workflows/` に配置されている
- [ ] リポジトリラベルが作成されている（auto-repair, repair-in-progress, etc.）
- [ ] （オプション）通知用Webhookが設定されている
- [ ] ワークフローが有効化されている（Actions タブで確認）

---

## 🛠️ トラブルシューティング

### エラー: "Resource not accessible by integration"

**原因**: `GITHUB_TOKEN` の権限不足

**解決方法**:
1. ワークフローファイルの `permissions` セクションを確認
2. 必要な権限を追加:
   ```yaml
   permissions:
     contents: write
     issues: write
     actions: write
   ```

### エラー: "Bad credentials"

**原因**: 無効または期限切れのトークン

**解決方法**:
1. 個人アクセストークンを再生成
2. リポジトリシークレットを更新

### エラー: "API rate limit exceeded"

**原因**: GitHub API レート制限超過

**解決方法**:
1. `GITHUB_TOKEN` の代わりに個人アクセストークンを使用（より高いレート制限）
2. ワークフロー実行頻度を調整（cron スケジュール）

---

## 📚 参考リンク

- [GitHub Actions - Using secrets](https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions)
- [GitHub Actions - Automatic token authentication](https://docs.github.com/en/actions/security-guides/automatic-token-authentication)
- [GitHub Actions - Permissions](https://docs.github.com/en/actions/using-jobs/assigning-permissions-to-jobs)
- [Creating a personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)

---

**最終更新日**: 2025-11-14
**バージョン**: 1.0.0
