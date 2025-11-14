# GitHub Actions ワークフローテスト実行手順書

**バージョン**: 1.0.0
**最終更新**: 2025-11-14
**対象**: 開発者、QAエンジニア、DevOpsエンジニア

---

## 目次

1. [事前準備](#1-事前準備)
2. [構文検証テスト](#2-構文検証テスト)
3. [ロジック検証テスト](#3-ロジック検証テスト)
4. [ローカル統合テスト (act)](#4-ローカル統合テスト-act)
5. [GitHub Actions統合テスト](#5-github-actions統合テスト)
6. [パフォーマンステスト](#6-パフォーマンステスト)
7. [エラー修復シミュレーション](#7-エラー修復シミュレーション)
8. [トラブルシューティング](#8-トラブルシューティング)

---

## 1. 事前準備

### 1.1 必要なツールのインストール

#### actionlint (YAML検証ツール)

```bash
# macOS
brew install actionlint

# Linux
curl -sSL https://raw.githubusercontent.com/rhysd/actionlint/main/scripts/download-actionlint.bash | bash -s latest /usr/local/bin

# Windows (Chocolatey)
choco install actionlint

# インストール確認
actionlint --version
# 期待される出力: 1.7.8 以上
```

#### GitHub CLI (gh)

```bash
# macOS
brew install gh

# Linux (Debian/Ubuntu)
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh

# Windows (Chocolatey)
choco install gh

# 認証
gh auth login

# インストール確認
gh --version
```

#### act (ローカルテストツール)

```bash
# macOS
brew install act

# Linux
curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Windows (Chocolatey)
choco install act-cli

# インストール確認
act --version
# 期待される出力: 0.2.x 以上
```

#### Python 3.9+

```bash
# Python バージョン確認
python3 --version

# PyYAML のインストール
pip install PyYAML

# インストール確認
python3 -c "import yaml; print(yaml.__version__)"
```

---

### 1.2 リポジトリのクローン

```bash
# リポジトリをクローン
git clone https://github.com/yourusername/MangaAnime-Info-delivery-system.git
cd MangaAnime-Info-delivery-system

# テスト用ブランチの作成
git checkout -b test/workflow-validation
```

---

## 2. 構文検証テスト

### 2.1 actionlint による検証

#### 基本的な実行

```bash
# すべてのワークフローを検証
actionlint .github/workflows/*.yml

# 特定のファイルのみ検証
actionlint .github/workflows/e2e-tests.yml

# 詳細モード
actionlint -verbose .github/workflows/*.yml

# JSON形式で出力
actionlint -format '{{json .}}' .github/workflows/*.yml > actionlint-results.json
```

#### 期待される出力

```
.github/workflows/e2e-tests.yml:45:125: got unexpected character '+' while lexing expression [expression]
.github/workflows/auto-repair-7x-loop.yml:170:13: the runner of "actions/setup-python@v4" action is too old [action]
...
```

#### 結果の解釈

- **エラーなし**: ✅ 全ワークフローが正しく設定されている
- **警告あり**: 🟡 修正推奨（動作に影響する可能性）
- **エラーあり**: 🔴 即座に修正が必要

---

### 2.2 YAML構文検証

#### Pythonスクリプトによる検証

```bash
python3 << 'EOF'
import yaml
import os
import sys

workflow_dir = ".github/workflows"
errors = []

for filename in os.listdir(workflow_dir):
    if filename.endswith(('.yml', '.yaml')):
        filepath = os.path.join(workflow_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                yaml.safe_load(f)
            print(f"✅ {filename}: Valid YAML")
        except yaml.YAMLError as e:
            print(f"❌ {filename}: YAML Error - {e}")
            errors.append(filename)

if errors:
    print(f"\n❌ {len(errors)} ファイルでエラーが検出されました")
    sys.exit(1)
else:
    print(f"\n✅ すべてのファイルが正しいYAML形式です")
    sys.exit(0)
EOF
```

#### yamllint による高度な検証（オプション）

```bash
# yamllint のインストール
pip install yamllint

# .yamllint 設定ファイルの作成
cat > .yamllint << 'EOF'
extends: default

rules:
  line-length:
    max: 120
  indentation:
    spaces: 2
  comments:
    min-spaces-from-content: 1
EOF

# 検証実行
yamllint .github/workflows/
```

---

## 3. ロジック検証テスト

### 3.1 環境変数と入力パラメータの検証

#### 検証スクリプト

```bash
python3 << 'EOF'
import yaml
import re
import os

workflow_dir = ".github/workflows"

for filename in os.listdir(workflow_dir):
    if not filename.endswith(('.yml', '.yaml')):
        continue

    filepath = os.path.join(workflow_dir, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        workflow = yaml.safe_load(content)

    # 定義されている環境変数
    defined_env = set(workflow.get('env', {}).keys())
    jobs = workflow.get('jobs', {})
    for job_config in jobs.values():
        defined_env.update(job_config.get('env', {}).keys())

    # 使用されている環境変数
    env_pattern = r'\$\{\{\s*env\.(\w+)'
    used_env = set(re.findall(env_pattern, content))

    # 未定義変数のチェック
    undefined = used_env - defined_env
    if undefined:
        print(f"⚠️  {filename}: 未定義の環境変数 - {', '.join(undefined)}")
    else:
        print(f"✅ {filename}: 環境変数の整合性OK")
EOF
```

---

### 3.2 条件分岐の検証

#### 条件式の抽出と検証

```bash
python3 << 'EOF'
import yaml
import os

workflow_dir = ".github/workflows"

for filename in os.listdir(workflow_dir):
    if not filename.endswith(('.yml', '.yaml')):
        continue

    filepath = os.path.join(workflow_dir, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        workflow = yaml.safe_load(f)

    jobs = workflow.get('jobs', {})
    for job_name, job_config in jobs.items():
        if 'if' in job_config:
            condition = job_config['if']
            print(f"📋 {filename} > {job_name}")
            print(f"   条件: {condition}")

            # 複雑な条件のチェック
            if condition.count('&&') + condition.count('||') > 3:
                print(f"   ⚠️  複雑な条件式（リファクタリング推奨）")
            print()
EOF
```

---

### 3.3 タイムアウト設定の検証

```bash
python3 << 'EOF'
import yaml
import os

workflow_dir = ".github/workflows"

for filename in os.listdir(workflow_dir):
    if not filename.endswith(('.yml', '.yaml')):
        continue

    filepath = os.path.join(workflow_dir, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        workflow = yaml.safe_load(f)

    jobs = workflow.get('jobs', {})
    print(f"📄 {filename}")

    for job_name, job_config in jobs.items():
        steps = job_config.get('steps', [])
        has_timeout = 'timeout-minutes' in job_config

        if len(steps) > 5 and not has_timeout:
            print(f"  ⚠️  {job_name}: タイムアウト未設定（{len(steps)}ステップ）")
        elif has_timeout:
            print(f"  ✅ {job_name}: タイムアウト {job_config['timeout-minutes']}分")
    print()
EOF
```

---

## 4. ローカル統合テスト (act)

### 4.1 基本的なテスト実行

#### dry-run モード（実行計画の確認）

```bash
# 全ワークフローのdry-run
act -n

# 特定のワークフローのdry-run
act -n -W .github/workflows/ci-pipeline.yml

# 特定のジョブのdry-run
act -j test -n
```

#### 期待される出力

```
[CI Pipeline/test] 🚀  Start image=catthehacker/ubuntu:act-latest
[CI Pipeline/test]   🐳  docker pull image=catthehacker/ubuntu:act-latest platform= username= forcePull=true
[CI Pipeline/test]   🐳  docker create image=catthehacker/ubuntu:act-latest platform= entrypoint=["tail" "-f" "/dev/null"] cmd=[]
...
```

---

### 4.2 実際の実行

#### CIパイプラインのテスト

```bash
# testジョブを実行
act -j test -W .github/workflows/ci-pipeline.yml

# 環境変数を指定して実行
act -j test \
  --env DATABASE_URL=test.db \
  --env TESTING=true

# シークレットを指定（テスト用）
act -j test \
  --secret GITHUB_TOKEN=ghp_xxxxxxxxxxxxx
```

---

### 4.3 workflow_dispatch イベントのシミュレート

#### E2Eテストのシミュレーション

```bash
# workflow_dispatch イベントをトリガー
act workflow_dispatch \
  -W .github/workflows/e2e-tests.yml \
  --input browser=chromium \
  --input test_type=smoke \
  --input headed=false

# イベントペイロードをJSONで指定
cat > event.json << 'EOF'
{
  "inputs": {
    "browser": "chromium",
    "test_type": "full",
    "headed": false
  }
}
EOF

act workflow_dispatch \
  -W .github/workflows/e2e-tests.yml \
  --eventpath event.json
```

---

### 4.4 スケジュールイベントのテスト

```bash
# scheduleトリガーのシミュレート
act schedule -W .github/workflows/auto-repair-7x-loop.yml

# cronジョブの実行時刻をシミュレート
act schedule \
  --env GITHUB_EVENT_NAME=schedule
```

---

### 4.5 actの高度な使用方法

#### カスタムランナーイメージの使用

```bash
# Mediumサイズのイメージを使用（推奨）
act -P ubuntu-latest=catthehacker/ubuntu:act-latest

# Fullサイズのイメージを使用（完全な環境）
act -P ubuntu-latest=catthehacker/ubuntu:full-latest

# 設定ファイルに記述
cat > .actrc << 'EOF'
-P ubuntu-latest=catthehacker/ubuntu:act-latest
--container-architecture linux/amd64
EOF
```

#### デバッグモード

```bash
# 詳細ログを出力
act -v -j test

# 超詳細ログ
act -vv -j test

# ステップごとに確認
act --bind --dryrun
```

---

## 5. GitHub Actions統合テスト

### 5.1 手動トリガーによるテスト

#### workflow_dispatch の実行

```bash
# 基本的な実行
gh workflow run ci-pipeline.yml

# 入力パラメータを指定
gh workflow run e2e-tests.yml \
  --field browser=chromium \
  --field test_type=smoke \
  --field headed=false

# 特定のブランチで実行
gh workflow run auto-repair-7x-loop.yml \
  --ref test/workflow-validation \
  --field force_repair=true \
  --field target_issue=123
```

---

### 5.2 実行状況の監視

#### リアルタイム監視

```bash
# 最新のワークフロー実行を監視
gh run watch

# 特定のワークフローを監視
gh workflow view ci-pipeline.yml

# 実行中のワークフローをリスト表示
gh run list --workflow=ci-pipeline.yml --status in_progress
```

#### ログの確認

```bash
# 最新の実行ログを表示
gh run view --log

# 特定のジョブのログを表示
gh run view 123456789 --job test --log

# ログをファイルに保存
gh run view 123456789 --log > workflow-log.txt
```

---

### 5.3 アーティファクトの確認

```bash
# アーティファクトのリスト表示
gh run view 123456789 --json artifacts --jq '.artifacts'

# アーティファクトのダウンロード
gh run download 123456789

# 特定のアーティファクトのみダウンロード
gh run download 123456789 --name e2e-test-results-chromium
```

---

### 5.4 テスト結果の評価

#### ワークフロー実行の成否確認

```bash
# 最新の実行結果を確認
gh run list --workflow=ci-pipeline.yml --limit 1 --json conclusion --jq '.[0].conclusion'

# 期待される出力: "success", "failure", "cancelled"

# すべてのワークフローの実行状態を確認
gh run list --status completed --limit 10 \
  --json name,conclusion,createdAt \
  --jq '.[] | "\(.name): \(.conclusion) (\(.createdAt))"'
```

---

## 6. パフォーマンステスト

### 6.1 実行時間の計測

#### ワークフロー実行時間の取得

```bash
# 最近の実行時間を取得
gh run list --workflow=ci-pipeline.yml --limit 10 \
  --json name,conclusion,createdAt,updatedAt,databaseId \
  --jq '.[] | {
    id: .databaseId,
    conclusion: .conclusion,
    duration: ((.updatedAt | fromdateiso8601) - (.createdAt | fromdateiso8601)) / 60
  }'

# CSVファイルに保存
gh run list --workflow=ci-pipeline.yml --limit 50 \
  --json name,conclusion,createdAt,updatedAt \
  --jq -r '.[] | [.name, .conclusion, .createdAt, .updatedAt] | @csv' \
  > workflow-performance.csv
```

---

### 6.2 リソース使用量の確認

#### GitHub Actions使用統計

```bash
# 組織の使用統計
gh api /orgs/{org}/settings/billing/actions

# リポジトリの使用統計
gh api /repos/{owner}/{repo}/actions/cache/usage
```

---

### 6.3 ボトルネックの特定

#### ジョブごとの実行時間分析

```bash
python3 << 'EOF'
import subprocess
import json
from datetime import datetime

# 最新のワークフロー実行を取得
result = subprocess.run(
    ['gh', 'run', 'list', '--workflow=ci-pipeline.yml', '--limit', '1', '--json', 'databaseId'],
    capture_output=True, text=True
)
run_id = json.loads(result.stdout)[0]['databaseId']

# ジョブの詳細を取得
result = subprocess.run(
    ['gh', 'api', f'/repos/{{owner}}/{{repo}}/actions/runs/{run_id}/jobs'],
    capture_output=True, text=True
)
jobs = json.loads(result.stdout)['jobs']

print("ジョブ実行時間分析")
print("=" * 60)

for job in jobs:
    name = job['name']
    started = datetime.fromisoformat(job['started_at'].replace('Z', '+00:00'))
    completed = datetime.fromisoformat(job['completed_at'].replace('Z', '+00:00'))
    duration = (completed - started).total_seconds() / 60

    print(f"{name}: {duration:.2f}分")

    # ステップごとの時間も表示
    for step in job['steps']:
        if step.get('started_at') and step.get('completed_at'):
            step_started = datetime.fromisoformat(step['started_at'].replace('Z', '+00:00'))
            step_completed = datetime.fromisoformat(step['completed_at'].replace('Z', '+00:00'))
            step_duration = (step_completed - step_started).total_seconds()

            if step_duration > 30:  # 30秒以上のステップのみ表示
                print(f"  - {step['name']}: {step_duration:.1f}秒")

print("=" * 60)
EOF
```

---

## 7. エラー修復シミュレーション

### 7.1 意図的なエラーの作成

#### テストケースの準備

```bash
# 失敗するテストを作成
cat > tests/test_intentional_failure.py << 'EOF'
"""
意図的に失敗するテスト（自動修復システムのテスト用）
"""

def test_intentional_failure():
    """自動修復システムをトリガーするための失敗テスト"""
    assert False, "This is an intentional failure for repair testing"

def test_another_failure():
    """2つ目の失敗テスト"""
    raise ValueError("Intentional error to test repair system")
EOF

# コミット
git add tests/test_intentional_failure.py
git commit -m "test: Add intentional failure for repair system testing"
git push origin test/workflow-validation
```

---

### 7.2 修復プロセスの開始

#### CIの実行とエラー検知

```bash
# CIパイプラインを実行
gh workflow run ci-pipeline.yml --ref test/workflow-validation

# 実行の監視
gh run watch

# 失敗を確認
gh run list --workflow=ci-pipeline.yml --limit 1 --json conclusion
# 期待される出力: {"conclusion": "failure"}
```

---

### 7.3 自動修復の監視

#### 修復Issueの確認

```bash
# 自動修復Issueのリスト取得
gh issue list --label "auto-repair-7x" --state open

# 特定のIssueの詳細表示
gh issue view 123

# Issueのコメントを確認（修復ログ）
gh issue view 123 --comments
```

#### 修復ループの実行状況確認

```bash
# 自動修復ワークフローの実行状況
gh run list --workflow=auto-repair-7x-loop.yml --limit 5

# リアルタイム監視
gh run watch --workflow=auto-repair-7x-loop.yml

# 修復試行回数の確認
gh issue view 123 --json body --jq '.body' | grep "総試行回数"
```

---

### 7.4 修復成功の確認

#### テストの再実行

```bash
# 修復後にテストを再実行
gh workflow run ci-pipeline.yml --ref test/workflow-validation

# 成功を確認
gh run list --workflow=ci-pipeline.yml --limit 1 --json conclusion
# 期待される出力: {"conclusion": "success"}
```

#### 修復Issueのクローズ確認

```bash
# Issueがクローズされたか確認
gh issue view 123 --json state
# 期待される出力: {"state": "CLOSED"}

# クローズコメントの確認
gh issue view 123 --comments | tail -5
```

---

## 8. トラブルシューティング

### 8.1 actionlint エラーの解決

#### 問題: "the runner of action is too old"

**症状**:
```
the runner of "actions/setup-python@v4" action is too old to run on GitHub Actions
```

**解決策**:
```bash
# v5 に更新
sed -i 's/actions\/setup-python@v4/actions\/setup-python@v5/g' .github/workflows/*.yml

# 変更を確認
git diff .github/workflows/
```

---

#### 問題: "got unexpected character while lexing expression"

**症状**:
```
.github/workflows/e2e-tests.yml:45:125: got unexpected character '+' while lexing expression
```

**解決策**:
```yaml
# 修正前
browser: ${{ github.event.inputs.browser == 'all' && fromJson('["chromium", "firefox", "webkit"]') || fromJson('["' + github.event.inputs.browser + '"]') }}

# 修正後
browser: ${{ github.event.inputs.browser == 'all' && fromJson('["chromium", "firefox", "webkit"]') || fromJson(format('["{0}"]', github.event.inputs.browser)) }}
```

---

### 8.2 act 実行エラーの解決

#### 問題: "Error: Cannot connect to the Docker daemon"

**症状**:
```
Error: Cannot connect to the Docker daemon at unix:///var/run/docker.sock
```

**解決策**:
```bash
# Dockerが起動しているか確認
docker ps

# Docker デーモンを起動
sudo systemctl start docker

# ユーザーをdockerグループに追加
sudo usermod -aG docker $USER
newgrp docker
```

---

#### 問題: "Error: image pull failed"

**症状**:
```
Error: image pull failed: catthehacker/ubuntu:act-latest
```

**解決策**:
```bash
# イメージを手動でプル
docker pull catthehacker/ubuntu:act-latest

# または軽量版を使用
act -P ubuntu-latest=catthehacker/ubuntu:act-20.04
```

---

### 8.3 GitHub Actions実行エラーの解決

#### 問題: "workflow_dispatch not found"

**症状**:
```
could not create workflow dispatch event: HTTP 422: No ref found for: test/workflow-validation
```

**解決策**:
```bash
# ブランチをプッシュ
git push origin test/workflow-validation

# 最新のmainブランチから再作成
git checkout main
git pull
git checkout -b test/workflow-validation
git push -u origin test/workflow-validation
```

---

#### 問題: タイムアウトエラー

**症状**:
```
The job running on runner GitHub Actions X has exceeded the maximum execution time of 360 minutes.
```

**解決策**:
```yaml
# タイムアウトを明示的に設定
jobs:
  test:
    timeout-minutes: 30  # デフォルトの360分より短く設定
```

---

### 8.4 自動修復システムのデバッグ

#### 修復ループが動作しない場合

```bash
# 修復スクリプトが存在するか確認
ls -la scripts/repair-loop-executor.py

# スクリプトがない場合は手動で実行可能か確認
python3 -c "import sys; print('Python is working')"

# ワークフローログを詳細確認
gh run view --log | grep "repair"
```

---

#### Issue作成が失敗する場合

```bash
# GitHub トークンの権限を確認
gh auth status

# 必要な権限をチェック
gh api user --jq '.permissions'

# 必要に応じて再認証
gh auth login --scopes repo,workflow,write:packages
```

---

## 9. CI/CD統合チェックリスト

### 9.1 事前チェック

- [ ] すべてのワークフローがYAML構文的に正しい
- [ ] actionlint で警告がないことを確認
- [ ] 環境変数が適切に定義されている
- [ ] シークレットが適切に設定されている
- [ ] タイムアウトが全ジョブに設定されている

---

### 9.2 ローカルテスト

- [ ] act でdry-runが成功する
- [ ] 主要なワークフローがローカルで実行できる
- [ ] 環境変数とシークレットが正しく渡される

---

### 9.3 統合テスト

- [ ] テスト用ブランチでワークフローが実行できる
- [ ] 全てのジョブが成功する
- [ ] アーティファクトが正しく生成される
- [ ] 自動修復システムが動作する

---

### 9.4 本番デプロイ前

- [ ] すべてのテストが成功している
- [ ] パフォーマンスが許容範囲内
- [ ] ドキュメントが更新されている
- [ ] ロールバック手順が準備されている

---

## 10. 参考資料

### 10.1 公式ドキュメント

- [GitHub Actions Documentation](https://docs.github.com/actions)
- [actionlint Documentation](https://github.com/rhysd/actionlint)
- [nektos/act Documentation](https://github.com/nektos/act)
- [GitHub CLI Manual](https://cli.github.com/manual/)

---

### 10.2 ベストプラクティス

- [GitHub Actions Best Practices](https://docs.github.com/actions/learn-github-actions/security-hardening-for-github-actions)
- [Workflow Syntax Reference](https://docs.github.com/actions/using-workflows/workflow-syntax-for-github-actions)
- [Contexts and Expressions](https://docs.github.com/actions/learn-github-actions/contexts)

---

### 10.3 トラブルシューティングリソース

- [GitHub Actions Community Forum](https://github.community/c/code-to-cloud/github-actions)
- [GitHub Actions Status](https://www.githubstatus.com/)
- [act Issues](https://github.com/nektos/act/issues)

---

**作成者**: QA Agent
**レビュアー**: DevOps Agent
**承認者**: CTO Agent
**バージョン**: 1.0.0
**最終更新**: 2025-11-14
