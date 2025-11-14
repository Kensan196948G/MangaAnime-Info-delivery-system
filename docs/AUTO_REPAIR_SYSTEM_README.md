# GitHub Actions 統合自動修復システム

## 📋 概要

3つの自動修復ワークフロー（v2最適化版、本番版、7xループ版）を統合し、最適化した統一自動エラー検知・修復システムです。

### 主な機能

- **インテリジェント修復**: 段階的エスカレーションによる効率的なエラー修復
- **複数トリガー**: スケジュール、手動、Issueコメント、ワークフロー失敗時
- **自動Issue管理**: エラー発生時の自動Issue作成、修復完了時の自動クローズ
- **リソース効率化**: タイムアウト制御、リトライメカニズム、依存関係キャッシュ
- **包括的ログ**: 詳細なサマリーとアーティファクト保存

---

## 🚀 クイックスタート

### 1. 前提条件

- GitHubリポジトリへのadmin権限
- GitHub Actions有効化済み
- Python 3.11以上

### 2. セットアップ（5分）

```bash
# 1. リポジトリクローン（既にクローン済みの場合はスキップ）
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system

# 2. ラベル作成
bash scripts/setup/create-github-labels.sh

# 3. ワークフローファイル確認
ls -la .github/workflows/auto-repair-unified.yml

# 4. GitHub Actions権限設定（Web UIから）
# Settings > Actions > General > Workflow permissions
# → "Read and write permissions" を選択

# 5. テスト実行
gh workflow run auto-repair-unified.yml \
  --field max_loops=3 \
  --field repair_mode=conservative \
  --field dry_run=true
```

### 3. 動作確認

```bash
# 実行状況監視
gh run watch

# 結果確認
gh run list --workflow=auto-repair-unified.yml --limit 1
```

---

## 📁 ファイル構成

```
MangaAnime-Info-delivery-system/
├── .github/workflows/
│   ├── auto-repair-unified.yml          # 【NEW】統合ワークフロー
│   ├── auto-error-detection-repair-v2.yml  # v2最適化版（統合元）
│   ├── auto-error-detection-repair.yml     # 本番版（統合元）
│   └── auto-repair-7x-loop.yml             # 7xループ版（統合元）
│
├── requirements.txt                     # 【NEW】本番依存関係
├── requirements-dev.txt                 # 【NEW】開発依存関係
│
├── scripts/
│   ├── auto_error_repair_loop.py       # メイン修復スクリプト
│   ├── repair-loop-executor.py         # エグゼキュータスクリプト
│   ├── generate_repair_summary.py      # サマリー生成
│   └── setup/
│       └── create-github-labels.sh     # 【NEW】ラベル作成スクリプト
│
└── docs/
    ├── AUTO_REPAIR_SYSTEM_README.md    # 【NEW】このファイル
    └── setup/
        ├── AUTO_REPAIR_ACTIVATION_GUIDE.md   # 【NEW】有効化ガイド
        ├── AUTO_REPAIR_TESTING.md            # 【NEW】テストガイド
        └── GITHUB_ACTIONS_SECRETS.md         # 【NEW】シークレット設定
```

---

## 🔧 使用方法

### 手動実行

#### Web UIから

1. Actions タブ > 「統合自動修復システム」
2. **Run workflow** をクリック
3. パラメータ設定:
   - `max_loops`: ループ回数（デフォルト: 10）
   - `repair_mode`: standard/aggressive/conservative
   - `dry_run`: true（テスト時）/ false（本番）
   - `target_issue`: 対象Issue番号（オプション）

#### GitHub CLIから

```bash
# 標準実行
gh workflow run auto-repair-unified.yml

# カスタムパラメータ
gh workflow run auto-repair-unified.yml \
  --field max_loops=5 \
  --field repair_mode=aggressive \
  --field dry_run=false
```

### Issueコメントトリガー

1. 任意のIssueを開く
2. コメントに `@auto-repair` と入力
3. ワークフローが自動起動

### スケジュール実行

- デフォルト: 30分ごと
- カスタマイズ: `.github/workflows/auto-repair-unified.yml` の `cron` を編集

```yaml
schedule:
  - cron: '*/30 * * * *'  # 30分ごと
  # - cron: '0 * * * *'    # 1時間ごと
  # - cron: '0 */6 * * *'  # 6時間ごと
```

---

## ⚙️ 修復モード

### Standard（推奨）

- **対象**: クリティカルエラーのみ
- **用途**: 本番環境、日常運用
- **リスク**: 低

```bash
gh workflow run auto-repair-unified.yml \
  --field repair_mode=standard
```

### Aggressive

- **対象**: クリティカルエラー + 警告
- **用途**: 完全なクリーンアップ、メンテナンス時
- **リスク**: 中

```bash
gh workflow run auto-repair-unified.yml \
  --field repair_mode=aggressive
```

### Conservative

- **対象**: エラー検知のみ（修復なし）
- **用途**: テスト、調査、影響評価
- **リスク**: なし

```bash
gh workflow run auto-repair-unified.yml \
  --field repair_mode=conservative \
  --field dry_run=true
```

---

## 📊 ワークフロー構成

### ジョブ1: 事前チェック（pre-check）

- 既存修復Issueの確認
- 修復戦略の決定
- 実行パラメータの検証

**タイムアウト**: 5分

### ジョブ2: 修復ループ（repair-loop）

- Python環境セットアップ
- 依存関係インストール（リトライ付き）
- 修復スクリプト実行
- 結果サマリー作成
- Issue自動作成/更新

**タイムアウト**: 30分

### ジョブ3: クリーンアップ（cleanup）

- 30日以上更新なしのIssueを自動クローズ
- スケジュール実行時のみ

**タイムアウト**: 5分

---

## 🔐 シークレット・権限設定

### 必須シークレット

| 名前 | 説明 | 設定 |
|------|------|------|
| `GITHUB_TOKEN` | GitHub自動提供トークン | 不要（自動） |

### 必須権限

```yaml
permissions:
  contents: write       # コード変更
  issues: write         # Issue操作
  actions: write        # ワークフロー実行
  pull-requests: write  # PR操作
  checks: read          # チェック結果
```

### リポジトリ設定

1. **Settings** > **Actions** > **General**
2. **Workflow permissions**
3. "Read and write permissions" を選択

詳細: [docs/setup/GITHUB_ACTIONS_SECRETS.md](./setup/GITHUB_ACTIONS_SECRETS.md)

---

## 🧪 テスト方法

### 基本テスト

```bash
# ドライランテスト
gh workflow run auto-repair-unified.yml \
  --field max_loops=3 \
  --field repair_mode=conservative \
  --field dry_run=true

# 実行監視
gh run watch
```

### 完全テストスイート

```bash
# テスト1: 手動実行
gh workflow run auto-repair-unified.yml --field dry_run=true

# テスト2: Issueコメントトリガー
ISSUE_NUM=$(gh issue create --title "Test" --body "Test issue" | grep -oE '[0-9]+$')
gh issue comment $ISSUE_NUM --body "@auto-repair"

# テスト3: 各修復モード
for mode in standard aggressive conservative; do
  gh workflow run auto-repair-unified.yml \
    --field repair_mode=$mode \
    --field max_loops=3 \
    --field dry_run=true
done
```

詳細: [docs/setup/AUTO_REPAIR_TESTING.md](./setup/AUTO_REPAIR_TESTING.md)

---

## 📈 監視・分析

### 実行統計

```bash
# 過去7日間の実行
gh run list --workflow=auto-repair-unified.yml \
  --created ">=$(date -d '7 days ago' +%Y-%m-%d)"

# 成功率計算
gh run list --workflow=auto-repair-unified.yml --limit 50 \
  --json conclusion --jq \
  'group_by(.conclusion) | map({conclusion: .[0].conclusion, count: length})'
```

### ログ分析

```bash
# アーティファクトダウンロード
RUN_ID=$(gh run list --workflow=auto-repair-unified.yml --limit 1 --json databaseId --jq '.[0].databaseId')
gh run download $RUN_ID

# サマリー確認
cat repair-logs-*/repair_summary.json | jq .
```

---

## 🛠️ カスタマイズ

### タイムアウト調整

```yaml
env:
  TIMEOUT_CHECKOUT: 5   # チェックアウト（分）
  TIMEOUT_SETUP: 8      # 環境セットアップ（分）
  TIMEOUT_INSTALL: 10   # 依存関係インストール（分）
  TIMEOUT_REPAIR: 20    # 修復処理（分）
```

### リトライ設定

```yaml
env:
  RETRY_MAX_ATTEMPTS: 3     # 最大試行回数
  RETRY_DELAY_SECONDS: 10   # 試行間隔（秒）
```

### ループ設定

```yaml
env:
  DEFAULT_MAX_LOOPS: 10         # デフォルトループ回数
  REPAIR_INTERVAL_SECONDS: 30   # ループ間隔（秒）
```

---

## 🚨 トラブルシューティング

### よくある問題と解決策

#### 問題1: 権限エラー

**エラー**: "Resource not accessible by integration"

**解決策**:
```bash
# リポジトリ設定確認
# Settings > Actions > General
# Workflow permissions: "Read and write permissions"
```

#### 問題2: スクリプト不在

**エラー**: "修復スクリプトが見つかりません"

**解決策**:
```bash
# スクリプト存在確認
ls -la scripts/auto_error_repair_loop.py
ls -la scripts/repair-loop-executor.py

# 少なくとも1つ必要
```

#### 問題3: 依存関係エラー

**エラー**: pip install タイムアウト

**解決策**:
```yaml
# タイムアウト延長
env:
  TIMEOUT_INSTALL: 15  # 10 → 15分
```

### 詳細なトラブルシューティング

- [有効化ガイド - トラブルシューティング](./setup/AUTO_REPAIR_ACTIVATION_GUIDE.md#トラブルシューティング)
- [テストガイド - トラブルシューティング](./setup/AUTO_REPAIR_TESTING.md#トラブルシューティング)

---

## 📊 比較表: 統合前 vs 統合後

| 項目 | 統合前（3ワークフロー） | 統合後（unified） |
|------|----------------------|------------------|
| ワークフロー数 | 3個 | 1個 |
| 修復モード | 固定 | 選択可能（3種） |
| トリガー | 個別設定 | 統一（4種） |
| Issue管理 | 部分的 | 完全自動化 |
| エラーハンドリング | 基本的 | 包括的 |
| リトライ機能 | なし/限定的 | 全体に適用 |
| キャッシュ | 部分的 | 最適化済み |
| タイムアウト制御 | 固定 | 段階的 |
| ドライラン | なし | あり |
| 保守性 | 低（重複多） | 高（統一） |

---

## 📚 ドキュメント一覧

1. **[AUTO_REPAIR_SYSTEM_README.md](./AUTO_REPAIR_SYSTEM_README.md)** (このファイル)
   - システム概要とクイックスタート

2. **[AUTO_REPAIR_ACTIVATION_GUIDE.md](./setup/AUTO_REPAIR_ACTIVATION_GUIDE.md)**
   - 詳細な有効化手順
   - カスタマイズ方法

3. **[AUTO_REPAIR_TESTING.md](./setup/AUTO_REPAIR_TESTING.md)**
   - 包括的テスト手順
   - パフォーマンステスト

4. **[GITHUB_ACTIONS_SECRETS.md](./setup/GITHUB_ACTIONS_SECRETS.md)**
   - シークレット設定
   - 権限管理

---

## 🔄 更新履歴

### v1.0.0 (2025-11-14)

- 初回リリース
- 3ワークフローの統合
- インテリジェント修復機能
- 包括的ドキュメント

---

## 🤝 貢献

バグ報告や機能提案は Issue でお願いします。

---

## 📝 ライセンス

このプロジェクトのライセンスに従います。

---

## 📞 サポート

- **ドキュメント**: `docs/setup/` 配下のガイドを参照
- **Issue**: GitHub Issues で報告
- **Discussion**: GitHub Discussions で質問

---

**最終更新**: 2025-11-14
**バージョン**: 1.0.0
**メンテナー**: MangaAnime-Info-delivery-system チーム
