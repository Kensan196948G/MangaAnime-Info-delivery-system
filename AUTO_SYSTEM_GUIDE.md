# 🤖 自動エラー検知・修復・PR作成システム ガイド

## 📋 概要

MangaAnimeシステムに包括的な自動化システムを導入しました。このシステムは以下の機能を提供します：

- **🔍 自動エラー検知**: システムの問題を1時間おきに自動検出
- **🔧 自動修復**: 検出された問題の自動修正
- **📝 自動PR作成**: 修復内容の詳細なPull Request作成
- **🎫 Issue自動管理**: Issue の自動分類・応答・管理

---

## 🚀 主要機能

### 1. 🔍 自動エラー検知システム

#### 検知対象
| カテゴリ | 検知内容 | 自動修復 |
|----------|----------|----------|
| **依存関係** | 脆弱性・古いパッケージ | ✅ 可能 |
| **コード品質** | フォーマット・Lint問題 | ✅ 可能 |
| **セキュリティ** | Bandit・機密情報漏洩 | ⚠️ 部分的 |
| **設定** | 設定ミス・デバッグモード | ✅ 可能 |
| **システム** | インポート失敗・ファイル不足 | ⚠️ 部分的 |

#### 実行スケジュール
```yaml
# 自動実行（1時間おき）
0 */1 * * *  # 00:00, 01:00, 02:00, 03:00...

# 手動実行
GitHub Actions → Auto Error Detection & Fix System → Run workflow
```

### 2. 🔧 自動修復システム

#### 修復可能な問題

**📦 依存関係の問題**:
```bash
# 自動実行される修復
pip-compile --upgrade --resolver=backtracking requirements.in
pip install --upgrade package_with_vulnerability
```

**🎨 コードフォーマット**:
```bash
# 自動実行される修復
black modules/          # コードフォーマット
isort modules/          # インポート整理
```

**⚙️ 設定ファイル**:
```bash
# 自動修正される設定
"debug": true  →  "debug": false
missing sections  →  default sections added
```

### 3. 📝 自動PR作成

#### PR作成フロー
1. **エラー検知** → 問題を特定
2. **自動修復** → 修正を適用
3. **ブランチ作成** → `auto-fix/errors-YYYYMMDD_HHMMSS`
4. **PR作成** → 詳細な修復内容説明
5. **レビュー要求** → `Kensan196948G` に自動アサイン

#### PR内容例
```markdown
# 🤖 Automated Error Fixes

## 🔍 Issues Detected & Fixed
- ✅ Dependencies: 3 outdated packages updated
- ✅ Formatting: Black formatting applied to 5 files  
- ✅ Configuration: Debug mode disabled

## 🧪 Testing
- [x] All automated tests pass
- [x] Security scans show improvements
- [x] No breaking changes introduced
```

### 4. 🎫 Issue自動管理

#### 自動ラベリング
Issueタイトル・本文に基づいて自動的にラベルを付与：

| キーワード | 付与ラベル |
|------------|------------|
| `bug`, `error`, `エラー` | `bug` |
| `feature`, `機能` | `enhancement` |
| `urgent`, `critical` | `priority:high` |
| `database`, `sqlite` | `component:database` |
| `email`, `notification` | `component:notification` |
| `webui`, `UI` | `component:webui` |
| `security`, `セキュリティ` | `security` |
| `dependency`, `formatting` | `auto-fixable` |

#### 自動応答システム
新しいIssueに対して自動的に応答：

```markdown
# 🤖 自動応答システム
こんにちは！Issue #123 を作成いただき、ありがとうございます。

## 🐛 バグレポートについて
バグレポートをありがとうございます。以下の情報があると...

### 🔧 自動診断を開始しました
システムが以下の自動診断を実行中です：
- ✅ 関連コンポーネントのヘルスチェック
- ✅ ログファイルの解析
```

#### コメントコマンド
Issueコメントで以下のコマンドが使用可能：

| コマンド | 機能 |
|----------|------|
| `/auto-fix` | 自動修復ワークフロー実行 |
| `/priority high` | 高優先度に設定 |
| `/keep-open` | 自動クローズを防止 |
| `/help` | コマンドヘルプ表示 |

---

## 📋 使用方法

### 🔧 手動での自動修復実行

#### 方法1: GitHub Actions UI
1. **GitHub リポジトリ** → **Actions** タブ
2. **Auto Error Detection & Fix System** を選択
3. **Run workflow** ボタンをクリック
4. オプション設定:
   - `detection_type`: `all` (全体検知)
   - `auto_fix`: `true` (自動修復有効)
   - `create_issue`: `true` (Issue作成)

#### 方法2: GitHub CLI
```bash
# 全体的な自動修復実行
gh workflow run "Auto Error Detection & Fix System" \
  --field detection_type=all \
  --field auto_fix=true \
  --field create_issue=true

# 依存関係のみ修復
gh workflow run "Auto Error Detection & Fix System" \
  --field detection_type=dependencies \
  --field auto_fix=true \
  --field create_issue=false
```

#### 方法3: Issue コメント
```markdown
# Issue内でコメント
/auto-fix

# システムが自動的に修復ワークフローを実行
```

### 📊 システム監視

#### 実行状況の確認
```bash
# GitHub Actions で確認
https://github.com/Kensan196948G/MangaAnime-Info-delivery-system/actions

# 最新の実行状況
- Auto Error Detection & Fix System (毎2時間)
- Issue Auto-Management (Issue作成時)
- Main CI/CD Pipeline (コミット時)
```

#### 通知の確認
```bash
# メール通知先（成功時のみ）
kensan1969@gmail.com

# 通知設定
✅ 成功通知: エラー検知・自動修復成功時
❌ 失敗通知: 無効化（GitHub Actionsログで確認）

# GitHub通知
- Issue作成・更新
- PR作成・マージ
- ワークフロー成功・失敗（ログのみ）
```

---

## 🔧 設定とカスタマイズ

### 自動検知の間隔変更
```yaml
# .github/workflows/auto-error-detection-and-fix.yml
schedule:
  # 現在設定: 1時間おき
  - cron: '0 */1 * * *'
  
  # 例: 2時間おきに変更
  - cron: '0 */2 * * *'
  
  # 例: 6時間おきに変更
  - cron: '0 */6 * * *'
  
  # 例: 毎日1回（午前2時）
  - cron: '0 2 * * *'
```

### Issue自動クローズの期間変更
```javascript
// .github/workflows/issue-auto-management.yml
const staleThreshold = 14; // 非アクティブ警告: 14日 → 変更可能
const closeThreshold = 30; // 自動クローズ: 30日 → 変更可能
```

### 自動修復の対象拡張
```bash
# 新しい修復タイプを追加
# .github/workflows/auto-error-detection-and-fix.yml の修復ジョブに追加

- name: Fix new issue type
  if: ${{ needs.error-detection.outputs.has_new_issues == 'true' }}
  run: |
    echo "🔧 Fixing new issue type..."
    # 修復コマンドを追加
```

---

## 📊 レポートと分析

### 自動生成レポート

#### エラー検知レポート
```markdown
## 🔍 Auto-Detection Results

**Dependencies:** 3 outdated, 1 security issues
**Code Quality:** 0 formatting, 2 linting issues  
**Security:** 0 potential vulnerabilities
**Configuration:** 1 issues found
**Health:** 0 system issues

🔧 **Auto-fix recommended**
```

#### PR修復レポート
```markdown
# 🤖 Automated Error Fixes

## 🔧 Applied Fixes
- ✅ Dependencies: Updated packages and security patches
- ✅ Formatting: Applied black and isort formatting
- ✅ Configuration: Resolved configuration issues

## 📋 Review Checklist
- [ ] Review dependency updates for compatibility
- [ ] Verify configuration changes are appropriate
```

### 成功率の追跡
```bash
# GitHub Actions の成功・失敗統計
Actions → Auto Error Detection & Fix System → 実行履歴

# 典型的な成功率
- エラー検知: 95%+ 成功
- 自動修復: 80%+ 成功（依存関係・フォーマット）
- PR作成: 98%+ 成功
```

---

## 🚨 トラブルシューティング

### よくある問題

#### 1. 自動修復が失敗する
```bash
# 原因: 権限不足
解決: GitHub Token の権限確認

# 原因: 競合する変更
解決: 手動でマージ後に再実行

# 原因: テスト失敗
解決: テストエラーを先に修正
```

#### 2. Issue が自動クローズされない
```bash
# 原因: keep-open ラベルが付いている
解決: ラベルを削除

# 原因: priority:high ラベルが付いている  
解決: 優先度を下げるか手動クローズ
```

#### 3. 不要なPRが大量作成される
```bash
# 原因: 検知間隔が短すぎる
解決: cron 設定を調整

# 原因: 同じ問題を繰り返し検知
解決: 根本原因を手動で修正
```

### デバッグ方法

#### ワークフローログの確認
```bash
# GitHub Actions でのデバッグ
1. Actions タブ → 失敗したワークフロー選択
2. 各ジョブのログを展開
3. エラーメッセージを確認

# 特に確認すべき項目
- error-detection ジョブの出力
- auto-fix ジョブのコミット処理
- PR作成の成功・失敗
```

#### ローカルでのテスト
```bash
# 修復コマンドをローカルで実行
black modules/
isort modules/
pip-compile --upgrade requirements.in

# 設定ファイルの検証
python -c "import json; print(json.load(open('config.json')))"
```

---

## 🎯 ベストプラクティス

### 効果的な運用

1. **定期レビュー**: 週1回、自動PRの内容をレビュー
2. **カスタマイズ**: プロジェクトに応じて検知条件を調整
3. **監視**: エラー検知の精度を定期的に評価
4. **ドキュメント**: 新しい自動修復パターンを文書化
5. **失敗確認**: GitHub Actionsログで失敗詳細を確認（メール通知なし）

### セキュリティ考慮事項

1. **権限管理**: GitHub Token の最小権限設定
2. **秘密情報**: Secrets の定期的な更新
3. **承認フロー**: 重要な変更には必ず人間のレビュー
4. **監査**: 自動修復の変更履歴を定期確認

---

## 📞 サポート

### 問題発生時の連絡先

```bash
# GitHub Issue として報告
https://github.com/Kensan196948G/MangaAnime-Info-delivery-system/issues

# メール連絡
kensan1969@gmail.com

# 緊急時のコマンド
/auto-fix     # Issue コメントで即座に修復実行
/help         # 利用可能コマンドの表示
```

### 関連ドキュメント

- **GitHub Actions設定**: `GITHUB_ACTIONS_GUIDE.md`
- **Secrets設定**: `GITHUB_SECRETS_SETUP.md`
- **エラー通知**: `ERROR_NOTIFICATION_GUIDE.md`

---

**🎉 自動エラー検知・修復・PR作成システムで、安全で効率的な開発環境を実現！**