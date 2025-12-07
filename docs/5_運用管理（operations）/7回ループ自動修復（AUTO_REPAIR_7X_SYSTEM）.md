# 🔄 7回ループ自動修復システム

## 概要

GitHub Actionsのエラーを自動検知し、7回の修復試行を3サイクル（合計21回）実行する完全自動修復システムです。
各サイクル間には30分のクールダウン期間を設け、リソースを効率的に使用しながら積極的な修復を実現します。

## ✨ 特徴

- **🤖 完全自動実行**: ワークフロー失敗を自動検知し、人間の介入なしで修復
- **📊 Issue管理**: 修復履歴をGitHub Issueに完全記録
- **⏸️ スマートクールダウン**: 7回試行後に30分休憩
- **🚨 自動エスカレーション**: 21回失敗時に@メンションで通知
- **🧹 自動クリーンアップ**: 古いIssueを自動的にクローズ

## 📋 動作フロー

```mermaid
graph TD
    A[ワークフロー失敗] -->|自動検知| B[Issue自動作成]
    B -->|ラベル: auto-repair-7x| C[修復サイクル1]
    C -->|7回試行| D{成功?}
    D -->|Yes| E[Issue自動クローズ]
    D -->|No| F[30分クールダウン]
    F --> G[修復サイクル2]
    G -->|7回試行| H{成功?}
    H -->|Yes| E
    H -->|No| I[30分クールダウン]
    I --> J[修復サイクル3]
    J -->|7回試行| K{成功?}
    K -->|Yes| E
    K -->|No| L[エスカレーション]
    L -->|@メンション| M[人間の介入待ち]
```

## 🚀 自動実行トリガー

### 1. ワークフロー失敗時（即座）
```yaml
workflow_run:
  workflows: ["CI Pipeline", "Security Check", "Test Suite"]
  types: [completed]
```

### 2. 定期実行（30分ごと）
```yaml
schedule:
  - cron: '*/30 * * * *'
```

### 3. Issue作成時
`auto-repair-7x`ラベル付きIssueが作成されると自動起動

## 📊 修復戦略

各試行で異なる修復戦略を実行：

1. **Import エラー修正**: 不足モジュールの自動インストール
2. **構文エラー修正**: autopep8とblackによる自動フォーマット
3. **依存関係修復**: requirements.txtからの再インストール
4. **Lintingエラー修正**: isortとblackによる修正
5. **テストエラー修正**: テストファイルの修復・再生成
6. **テストファイル再生成**: __init__.pyの作成など
7. **環境リセット**: キャッシュクリアと再初期化

## 📈 期待される効果

| メトリクス | 効果 |
|----------|------|
| 自動修復率 | 約70-80%のエラーを自動解決 |
| 人的介入削減 | 21回試行後のみ人間が介入 |
| リソース効率 | API制限を回避しつつ積極修復 |
| 追跡性 | 全修復履歴がIssueに記録 |

## 🔧 カスタマイズ

`.github/workflows/auto-repair-7x-loop.yml`で調整可能：

```yaml
env:
  MAX_ATTEMPTS_PER_CYCLE: 7  # サイクルあたりの試行回数
  COOLDOWN_MINUTES: 30        # クールダウン時間（分）
  MAX_CYCLES: 3               # 最大サイクル数
```

## 📝 Issue フォーマット

自動作成されるIssueの例：

```markdown
## 🚨 自動修復タスク

**検出されたエラー:**
- ワークフロー: CI Pipeline
- 失敗リンク: [View Run]
- 検出時刻: 2024-08-17 15:30:00 UTC

## 📊 修復ステータス

### サイクル 1/3
- [x] 試行 1/7 ✅
- [x] 試行 2/7 ❌
- [ ] 試行 3/7
...

## 📝 修復ログ

| 時刻 | サイクル | 試行 | 結果 | 詳細 |
|------|---------|------|------|------|
| 15:30 | 1 | 1/7 | ✅ | Import error fixed |
| 15:35 | 1 | 2/7 | ❌ | Syntax error remains |
```

## 🛡️ 安全機能

- **無限ループ防止**: 最大21回で自動停止
- **タイムアウト**: 各修復試行に5分制限
- **重複防止**: 同時に複数の修復Issueを作成しない
- **古いIssueクリーンアップ**: 7日間更新なしで自動クローズ

## 🔍 デバッグ

### 手動実行
```bash
# GitHub Actionsから
Actions → 7x Auto Repair Loop System → Run workflow

# CLIから特定Issueを修復
gh workflow run auto-repair-7x-loop.yml \
  -f force_repair=true \
  -f target_issue=123
```

### ログ確認
```bash
# 修復ログの確認
cat .repair_logs/issue_123.log

# ワークフロー実行状況
gh run list --workflow=auto-repair-7x-loop.yml
```

## 📋 必要な権限

リポジトリ設定で以下の権限が必要：

- Actions: Read and write
- Issues: Read and write
- Pull requests: Read and write
- Contents: Write

## 🎯 使用例

1. **自動起動**
   - コードをプッシュ
   - CIが失敗
   - 自動修復システムが起動
   - Issueで進捗を確認

2. **手動介入が必要な場合**
   - 21回の試行後、メンション通知
   - Issueを確認して手動修正
   - 修正後、Issueをクローズ

## 📞 サポート

問題が発生した場合：
1. `.repair_logs/`ディレクトリのログを確認
2. GitHub Issueで`auto-repair-7x`ラベルを確認
3. 必要に応じて手動でワークフローを再実行

---

このシステムにより、GitHub Actionsのエラーが発生しても自動的に修復され、開発者の介入を最小限に抑えることができます。