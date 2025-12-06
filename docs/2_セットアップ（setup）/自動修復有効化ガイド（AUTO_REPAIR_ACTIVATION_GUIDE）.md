# GitHub Actions 自動修復システム 有効化ガイド

## 📋 目次

1. [概要](#概要)
2. [前提条件](#前提条件)
3. [有効化手順](#有効化手順)
4. [動作確認](#動作確認)
5. [カスタマイズ](#カスタマイズ)
6. [トラブルシューティング](#トラブルシューティング)

---

## 🎯 概要

このガイドでは、GitHub Actions自動エラー検知・修復ループシステムを有効化する手順を説明します。

### システムの特徴

- **統合ワークフロー**: 3つの既存ワークフローを1つに統合
- **インテリジェント修復**: 段階的エスカレーション機能
- **複数トリガー**: スケジュール、手動、コメント、ワークフロー失敗時
- **自動Issue管理**: 失敗時に自動Issue作成、成功時に自動クローズ
- **リソース効率化**: タイムアウト、リトライ、キャッシュ機能

---

## ✅ 前提条件

### 1. リポジトリ要件

- [ ] GitHubリポジトリへのadminまたはmaintainer権限
- [ ] GitHub Actionsが有効化されている
- [ ] Python 3.11以上がプロジェクトで使用されている

### 2. 必要なファイル

以下のファイルが存在することを確認してください：

```bash
# ワークフローファイル
.github/workflows/auto-repair-unified.yml

# 依存関係ファイル
requirements.txt
requirements-dev.txt

# 修復スクリプト（少なくとも1つ）
scripts/auto_error_repair_loop.py
scripts/repair-loop-executor.py
```

### 3. 確認コマンド

```bash
# ファイル存在確認
ls -la .github/workflows/auto-repair-unified.yml
ls -la requirements.txt requirements-dev.txt
ls -la scripts/auto_error_repair_loop.py
```

---

## 🚀 有効化手順

### ステップ1: ラベルの作成

GitHubリポジトリに必要なラベルを作成します。

#### 方法1: GitHub Web UIから

1. リポジトリページの **Issues** タブに移動
2. **Labels** をクリック
3. 以下のラベルを作成：

| ラベル名 | 色 | 説明 |
|---------|-----|------|
| `auto-repair` | `#0E8A16` | 自動修復システム関連 |
| `repair-in-progress` | `#FBCA04` | 修復実行中 |
| `repair-completed` | `#0E8A16` | 修復完了 |
| `repair-failed` | `#D73A4A` | 修復失敗 |
| `critical` | `#B60205` | クリティカルエラー |

#### 方法2: GitHub CLIから（推奨）

```bash
# GitHub CLI でラベル一括作成
gh label create "auto-repair" --color "0E8A16" --description "自動修復システム関連"
gh label create "repair-in-progress" --color "FBCA04" --description "修復実行中"
gh label create "repair-completed" --color "0E8A16" --description "修復完了"
gh label create "repair-failed" --color "D73A4A" --description "修復失敗"
gh label create "critical" --color "B60205" --description "クリティカルエラー"
```

### ステップ2: ワークフローファイルの配置確認

```bash
# ワークフローファイルが正しい場所にあるか確認
ls -la .github/workflows/auto-repair-unified.yml

# YAMLの文法チェック（オプション）
yamllint .github/workflows/auto-repair-unified.yml
```

### ステップ3: ワークフローの有効化

#### 方法1: 自動有効化（デフォルト）

- ワークフローファイルをmainブランチにpushすると自動的に有効化されます

```bash
git add .github/workflows/auto-repair-unified.yml
git commit -m "feat: 統合自動修復システムを追加"
git push origin main
```

#### 方法2: GitHub Web UIから確認

1. リポジトリページの **Actions** タブに移動
2. 左サイドバーに「統合自動修復システム」が表示されることを確認
3. ワークフローをクリックして詳細を確認

### ステップ4: 権限設定の確認

ワークフローファイルに以下の権限が設定されていることを確認：

```yaml
permissions:
  contents: write
  issues: write
  actions: write
  pull-requests: write
  checks: read
```

リポジトリ設定で Actions の権限を確認：

1. **Settings** > **Actions** > **General**
2. **Workflow permissions** セクション
3. "Read and write permissions" を選択（推奨）
4. "Allow GitHub Actions to create and approve pull requests" にチェック（オプション）

### ステップ5: スケジュール実行の設定（オプション）

デフォルトでは30分ごとに実行されます。変更する場合：

```yaml
on:
  schedule:
    - cron: '*/30 * * * *'  # 30分ごと（デフォルト）
    # - cron: '0 * * * *'    # 1時間ごと
    # - cron: '0 */6 * * *'  # 6時間ごと
```

---

## 🧪 動作確認

### テスト1: 手動実行

1. **Actions** タブに移動
2. 「統合自動修復システム」ワークフローを選択
3. **Run workflow** をクリック
4. パラメータを設定（すべてデフォルトでOK）
5. **Run workflow** を実行
6. 実行結果を確認

#### 推奨テストパラメータ

```
max_loops: 3
repair_mode: conservative (初回テスト)
dry_run: true (実際の修復を行わない)
```

### テスト2: Issueコメントトリガー

1. 任意のIssueを開く（または新規作成）
2. コメントに `@auto-repair` と入力
3. ワークフローが起動することを確認
4. Issue に修復結果がコメントされることを確認

### テスト3: スケジュール実行（待機が必要）

- 次のスケジュール時刻（30分後）まで待機
- **Actions** タブで自動実行を確認

---

## ⚙️ カスタマイズ

### 1. 修復モードの選択

| モード | 説明 | 推奨用途 |
|--------|------|---------|
| `standard` | クリティカルエラーのみ修復 | 本番環境（デフォルト） |
| `aggressive` | 警告も含めて修復 | 開発環境、完全なクリーンアップ |
| `conservative` | エラー検知のみ（修復なし） | テスト、調査 |

### 2. タイムアウト設定のカスタマイズ

```yaml
env:
  TIMEOUT_CHECKOUT: 5   # チェックアウト（分）
  TIMEOUT_SETUP: 8      # Python環境セットアップ（分）
  TIMEOUT_INSTALL: 10   # 依存関係インストール（分）
  TIMEOUT_REPAIR: 20    # 修復処理（分）
```

### 3. リトライ設定のカスタマイズ

```yaml
env:
  RETRY_MAX_ATTEMPTS: 3     # 最大試行回数
  RETRY_DELAY_SECONDS: 10   # 試行間隔（秒）
```

### 4. ループ回数の調整

```yaml
env:
  DEFAULT_MAX_LOOPS: 10         # デフォルトループ回数
  REPAIR_INTERVAL_SECONDS: 30   # ループ間隔（秒）
```

---

## 🔧 トラブルシューティング

### 問題1: ワークフローが実行されない

**症状**: Actions タブにワークフローが表示されない

**解決策**:
1. ファイルパスを確認: `.github/workflows/auto-repair-unified.yml`
2. YAMLの文法エラーをチェック
3. mainブランチにpushされているか確認

```bash
# ブランチ確認
git branch

# YAMLチェック
yamllint .github/workflows/auto-repair-unified.yml
```

### 問題2: 権限エラー "Resource not accessible by integration"

**症状**: ワークフロー実行中に権限エラー

**解決策**:
1. リポジトリ設定を確認: **Settings** > **Actions** > **General**
2. "Workflow permissions" を "Read and write permissions" に変更
3. ワークフローファイルの `permissions` セクションを確認

### 問題3: 修復スクリプトが見つからない

**症状**: "修復スクリプトが見つかりません" エラー

**解決策**:
```bash
# スクリプトファイルの存在確認
ls -la scripts/auto_error_repair_loop.py
ls -la scripts/repair-loop-executor.py

# 少なくとも1つのスクリプトが必要
# 見つからない場合は作成またはリポジトリから取得
```

### 問題4: 依存関係インストール失敗

**症状**: pip install でタイムアウトまたはエラー

**解決策**:
```yaml
# タイムアウトを延長
env:
  TIMEOUT_INSTALL: 15  # 10 → 15分に延長

# または、requirements.txt のパッケージを削減
```

### 問題5: スケジュール実行が動作しない

**症状**: 定期実行されない

**原因**: GitHubの仕様上、スケジュール実行には遅延が発生する場合があります

**解決策**:
- 手動実行で代替
- workflow_dispatch で必要時に実行
- cron 式を確認: [crontab.guru](https://crontab.guru/)

---

## 📊 実行状況の監視

### ダッシュボード確認

1. **Actions** タブ > 「統合自動修復システム」
2. 実行履歴を確認
3. 各実行の詳細ログを確認

### 通知設定（オプション）

リポジトリの **Settings** > **Notifications** で以下を設定可能：

- ワークフロー失敗時のメール通知
- Slack/Discord連携（Webhookが必要）

---

## 🎯 次のステップ

### 推奨設定（本番環境）

1. **スケジュール実行**: 1時間ごとに変更
   ```yaml
   schedule:
     - cron: '0 * * * *'
   ```

2. **修復モード**: standard（デフォルト）

3. **監視**: 週次でIssue確認

### 高度な設定

- カスタム修復ロジックの追加
- 複数環境対応（dev/staging/prod）
- 外部通知システムとの連携

---

## 📚 関連ドキュメント

- [シークレット設定ガイド](./GITHUB_ACTIONS_SECRETS.md)
- [テスト方法](./AUTO_REPAIR_TESTING.md)
- [GitHub Actions公式ドキュメント](https://docs.github.com/actions)

---

## ✅ 有効化完了チェックリスト

最終確認として、以下をチェックしてください：

- [ ] 必要なラベルがすべて作成されている
- [ ] ワークフローファイルが `.github/workflows/` に配置されている
- [ ] 権限設定が適切（Read and write permissions）
- [ ] 手動実行テストが成功した
- [ ] requirements.txt と requirements-dev.txt が存在する
- [ ] 修復スクリプトが存在する（少なくとも1つ）
- [ ] Actions タブで実行履歴が確認できる
- [ ] （オプション）通知設定が完了している

---

**最終更新日**: 2025-11-14
**バージョン**: 1.0.0
**対応ワークフロー**: auto-repair-unified.yml
