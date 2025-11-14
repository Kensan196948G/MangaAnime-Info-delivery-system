# GitHub Actions 自動修復システム テストガイド

## 📋 目次

1. [概要](#概要)
2. [テスト環境準備](#テスト環境準備)
3. [テストシナリオ](#テストシナリオ)
4. [パフォーマンステスト](#パフォーマンステスト)
5. [トラブルシューティング](#トラブルシューティング)

---

## 🎯 概要

このドキュメントでは、統合自動修復システムの動作確認とテスト方法を説明します。

### テストの目的

- システムが正しく動作することを確認
- 各トリガー（スケジュール、手動、コメント、ワークフロー失敗）の動作検証
- エラーハンドリングの確認
- パフォーマンスの検証

---

## 🛠️ テスト環境準備

### 1. 必要なファイルの確認

```bash
# プロジェクトルートで実行
cd /mnt/Linux-ExHDD/MangaAnime-Info-delivery-system

# 必須ファイルの存在確認
ls -la .github/workflows/auto-repair-unified.yml
ls -la requirements.txt requirements-dev.txt
ls -la scripts/auto_error_repair_loop.py

# ディレクトリ構造確認
tree -L 2 -I '__pycache__|*.pyc|.git'
```

### 2. ローカル環境でのスクリプトテスト

```bash
# Python環境セットアップ
python3 -m venv venv
source venv/bin/activate

# 依存関係インストール
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 修復スクリプトのドライラン実行
python scripts/auto_error_repair_loop.py \
  --max-loops 3 \
  --interval 5 \
  --dry-run

# 実行結果確認
cat repair_summary.json
```

### 3. GitHub Actions環境の確認

```bash
# GitHub CLIで Actions が有効か確認
gh api repos/{owner}/{repo}/actions/permissions

# ワークフロー一覧取得
gh workflow list

# 統合自動修復システムのステータス確認
gh workflow view "統合自動修復システム (Unified Auto-Repair System)"
```

---

## 🧪 テストシナリオ

### テスト1: 手動実行（基本動作確認）

#### 目的
- ワークフローの基本動作を確認
- すべてのジョブが正常に実行されるか検証

#### 手順

1. **GitHub Web UIから実行**
   - Actions タブ > 「統合自動修復システム」
   - **Run workflow** をクリック
   - 以下のパラメータを設定：
     ```
     max_loops: 3
     repair_mode: conservative
     dry_run: true
     ```
   - **Run workflow** を実行

2. **GitHub CLIから実行**
   ```bash
   gh workflow run "auto-repair-unified.yml" \
     --field max_loops=3 \
     --field repair_mode=conservative \
     --field dry_run=true
   ```

3. **実行状況の監視**
   ```bash
   # 最新の実行を監視
   gh run watch

   # または、実行一覧を確認
   gh run list --workflow=auto-repair-unified.yml
   ```

#### 期待される結果

- ✅ すべてのジョブが成功
- ✅ Job Summary に実行パラメータが表示される
- ✅ repair_summary.json が作成される
- ✅ ログファイルがアーティファクトとして保存される

#### 検証コマンド

```bash
# 最新実行のステータス取得
RUN_ID=$(gh run list --workflow=auto-repair-unified.yml --limit 1 --json databaseId --jq '.[0].databaseId')

# ジョブステータス確認
gh run view $RUN_ID

# アーティファクトのダウンロード
gh run download $RUN_ID
ls -la repair-logs-*/
```

---

### テスト2: Issueコメントトリガー

#### 目的
- Issueコメントからのワークフロー起動を確認
- Issueへの自動コメント機能を検証

#### 手順

1. **テスト用Issueの作成**
   ```bash
   gh issue create \
     --title "自動修復テスト" \
     --body "このIssueは自動修復システムのテスト用です" \
     --label "test"
   ```

2. **トリガーコメントの投稿**
   ```bash
   ISSUE_NUMBER=$(gh issue list --label test --limit 1 --json number --jq '.[0].number')

   gh issue comment $ISSUE_NUMBER \
     --body "@auto-repair テスト実行"
   ```

3. **ワークフロー起動確認**
   ```bash
   # 数秒待機
   sleep 10

   # 最新実行を確認
   gh run list --workflow=auto-repair-unified.yml --limit 1
   ```

#### 期待される結果

- ✅ コメント投稿後にワークフローが起動
- ✅ 実行完了後、Issueに結果コメントが追加される
- ✅ Issueに適切なラベルが付与される

#### 検証

```bash
# Issue詳細とコメント確認
gh issue view $ISSUE_NUMBER

# コメント一覧
gh issue view $ISSUE_NUMBER --json comments --jq '.comments[].body'
```

---

### テスト3: ドライランモード

#### 目的
- 修復を実際に実行せず、検出のみを確認
- システムへの影響なしでテスト

#### 手順

```bash
# ドライランで実行
gh workflow run "auto-repair-unified.yml" \
  --field max_loops=5 \
  --field repair_mode=aggressive \
  --field dry_run=true

# 実行監視
gh run watch
```

#### 期待される結果

- ✅ エラー検出が実行される
- ✅ 修復は実際には行われない
- ✅ repair_summary.json に検出結果が記録される

---

### テスト4: 修復モード別テスト

#### Standard モード（クリティカルエラーのみ）

```bash
gh workflow run "auto-repair-unified.yml" \
  --field max_loops=10 \
  --field repair_mode=standard \
  --field dry_run=false
```

**期待動作**: クリティカルエラーのみ修復試行

#### Aggressive モード（警告も含む）

```bash
gh workflow run "auto-repair-unified.yml" \
  --field max_loops=10 \
  --field repair_mode=aggressive \
  --field dry_run=false
```

**期待動作**: クリティカルエラー + 警告も修復試行

#### Conservative モード（検知のみ）

```bash
gh workflow run "auto-repair-unified.yml" \
  --field max_loops=3 \
  --field repair_mode=conservative \
  --field dry_run=true
```

**期待動作**: エラー検知のみ、修復なし

---

### テスト5: エラーハンドリングテスト

#### 目的
- 異常系の動作を確認
- タイムアウト、失敗時の挙動を検証

#### テストケース

##### 5-1. スクリプト不在エラー

```bash
# 一時的にスクリプトを移動
mv scripts/auto_error_repair_loop.py scripts/auto_error_repair_loop.py.bak

# ワークフロー実行
gh workflow run "auto-repair-unified.yml" \
  --field max_loops=3 \
  --field repair_mode=standard

# 実行監視
gh run watch

# スクリプトを戻す
mv scripts/auto_error_repair_loop.py.bak scripts/auto_error_repair_loop.py
```

**期待結果**: エラーメッセージが表示され、適切に失敗

##### 5-2. 依存関係エラー

```bash
# requirements.txt に存在しないパッケージを一時追加
echo "nonexistent-package==99.99.99" >> requirements.txt

# ワークフロー実行
gh workflow run "auto-repair-unified.yml"

# 元に戻す
git checkout requirements.txt
```

**期待結果**: リトライ機能が動作し、最終的に失敗

##### 5-3. 権限エラー

リポジトリ設定で一時的に権限を制限してテスト

**期待結果**: 明確なエラーメッセージ

---

### テスト6: 同時実行制御

#### 目的
- concurrency設定が正しく機能するか確認

#### 手順

```bash
# 2つのワークフローを連続実行
gh workflow run "auto-repair-unified.yml" \
  --field max_loops=10 \
  --field repair_mode=standard &

sleep 2

gh workflow run "auto-repair-unified.yml" \
  --field max_loops=10 \
  --field repair_mode=standard &

# 実行一覧確認
gh run list --workflow=auto-repair-unified.yml --limit 5
```

#### 期待される結果

- ✅ 最初のワークフローが実行中
- ✅ 2番目のワークフローは待機（pending）状態
- ✅ 1番目が完了後、2番目が開始

---

## 📊 パフォーマンステスト

### テスト7: 実行時間測定

#### 目的
- 各ジョブの実行時間を測定
- タイムアウト設定の妥当性を確認

#### 測定方法

```bash
# 実行
gh workflow run "auto-repair-unified.yml" \
  --field max_loops=10 \
  --field repair_mode=standard

# 実行ID取得
RUN_ID=$(gh run list --workflow=auto-repair-unified.yml --limit 1 --json databaseId --jq '.[0].databaseId')

# 完了待機
gh run watch $RUN_ID

# 実行時間取得
gh run view $RUN_ID --json jobs --jq '.jobs[] | {name: .name, duration: (.completedAt | fromdateiso8601) - (.startedAt | fromdateiso8601)}'
```

#### ベンチマーク目標

| ジョブ | 目標時間 | 最大許容時間 |
|--------|---------|-------------|
| pre-check | 1分以内 | 5分 |
| repair-loop | 15分以内 | 30分 |
| cleanup | 1分以内 | 5分 |

---

### テスト8: リソース使用量測定

#### GitHub Actions分単位の確認

```bash
# 今月の使用量確認
gh api /repos/{owner}/{repo}/actions/cache/usage

# ワークフロー実行統計
gh api /repos/{owner}/{repo}/actions/workflows/auto-repair-unified.yml/timing
```

---

## 🔍 テスト結果の分析

### 1. ログ分析

```bash
# アーティファクトダウンロード
gh run download $RUN_ID

# repair_summary.json の分析
cat repair-logs-*/repair_summary.json | jq .

# 重要指標の抽出
jq '{
  status: .final_status,
  loops: .total_loops,
  success: .successful_repairs,
  failed: .failed_repairs,
  reduction: .error_reduction_rate
}' repair-logs-*/repair_summary.json
```

### 2. Issue追跡

```bash
# 自動修復関連のIssueを全取得
gh issue list --label "auto-repair" --state all

# 成功率計算
TOTAL=$(gh issue list --label "auto-repair" --state all --json number --jq 'length')
COMPLETED=$(gh issue list --label "repair-completed" --state closed --json number --jq 'length')

echo "成功率: $(( COMPLETED * 100 / TOTAL ))%"
```

---

## 🚨 トラブルシューティング

### 問題1: ワークフローが起動しない

**診断コマンド**:
```bash
# ワークフローファイルの文法チェック
yamllint .github/workflows/auto-repair-unified.yml

# Actionsの有効性確認
gh api repos/{owner}/{repo}/actions/permissions
```

### 問題2: テストが失敗する

**診断手順**:
1. ログ詳細確認
   ```bash
   gh run view $RUN_ID --log-failed
   ```

2. 特定ジョブのログ
   ```bash
   gh run view $RUN_ID --job=repair-loop --log
   ```

3. エラーメッセージ抽出
   ```bash
   gh run view $RUN_ID --log | grep -i "error"
   ```

### 問題3: タイムアウト発生

**対策**:
- タイムアウト設定を延長
- ループ回数を削減
- repair_interval を短縮

---

## ✅ テスト完了チェックリスト

すべてのテストが完了したら、以下を確認：

- [ ] 手動実行テストが成功
- [ ] Issueコメントトリガーが動作
- [ ] ドライランモードが正常動作
- [ ] 3つの修復モードすべてで動作確認
- [ ] エラーハンドリングが適切
- [ ] 同時実行制御が機能
- [ ] パフォーマンスが目標範囲内
- [ ] リソース使用量が許容範囲内
- [ ] ログとサマリーが正確
- [ ] Issueの自動作成・更新が動作

---

## 📈 継続的な監視

### 週次チェック

```bash
# 過去7日間の実行統計
gh run list \
  --workflow=auto-repair-unified.yml \
  --created ">=$(date -d '7 days ago' +%Y-%m-%d)" \
  --json status,conclusion,createdAt

# 成功率計算
gh run list --workflow=auto-repair-unified.yml --limit 50 \
  --json conclusion --jq \
  'group_by(.conclusion) | map({conclusion: .[0].conclusion, count: length})'
```

### 月次レポート

```bash
# 今月の実行回数
gh run list \
  --workflow=auto-repair-unified.yml \
  --created ">=$(date -d '1 month ago' +%Y-%m-%d)" \
  --json number --jq 'length'

# 平均実行時間
gh api /repos/{owner}/{repo}/actions/workflows/auto-repair-unified.yml/timing \
  | jq '.billable.UBUNTU.total_ms / 60000' # 分単位
```

---

## 📚 参考資料

- [GitHub Actions - Testing workflows](https://docs.github.com/en/actions/learn-github-actions/testing-workflows)
- [GitHub CLI - Run commands](https://cli.github.com/manual/gh_run)
- [有効化ガイド](./AUTO_REPAIR_ACTIVATION_GUIDE.md)
- [シークレット設定](./GITHUB_ACTIONS_SECRETS.md)

---

**最終更新日**: 2025-11-14
**バージョン**: 1.0.0
**テスト対象**: auto-repair-unified.yml
