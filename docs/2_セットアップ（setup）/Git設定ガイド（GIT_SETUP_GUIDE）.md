# Git & GitHub セットアップガイド

## 前提条件

- Git がインストールされている
- GitHub アカウントを持っている
- GitHub CLI (`gh`) がインストールされている（PR作成に必要）

---

## 1️⃣ Gitリポジトリの初期化

### ステップ1: Gitリポジトリを初期化

```bash
# プロジェクトのルートディレクトリで実行
git init
```

### ステップ2: .gitignore の確認

既に `.gitignore` ファイルが存在しますが、以下の内容が含まれているか確認してください：

```bash
cat .gitignore
```

**追加すべき重要な項目**（機密情報保護）:
```gitignore
# 認証情報
token.json
calendar_token.json
credentials.json
*.json.enc

# 環境変数
.env
.env.local
.env.*.local

# データベース
*.db
*.sqlite
*.sqlite3

# ログ
logs/
*.log

# Python
__pycache__/
*.py[cod]
*$py.class
venv/
.venv/
*.so

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# カバレッジ
htmlcov/
.coverage
.pytest_cache/

# その他
node_modules/
```

### ステップ3: 初期コミット

```bash
# すべてのファイルをステージング
git add .

# 初期コミットを作成
git commit -m "Initial commit: MangaAnime情報配信システム

- プロジェクト構造の確立
- 基本モジュールの実装
- テストスイートの追加
- ドキュメントの整備

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 2️⃣ GitHubリポジトリの作成と連携

### オプションA: GitHub CLIを使用（推奨）

```bash
# GitHub CLIで認証（初回のみ）
gh auth login

# 新しいリポジトリを作成して連携
gh repo create MangaAnime-Info-delivery-system --private --source=. --remote=origin --push
```

### オプションB: 手動でリポジトリを作成

1. **GitHubでリポジトリを作成**
   - https://github.com/new にアクセス
   - リポジトリ名: `MangaAnime-Info-delivery-system`
   - プライベート/パブリックを選択
   - 「Create repository」をクリック

2. **ローカルリポジトリとリモートを連携**

```bash
# リモートリポジトリを追加（URLは自分のものに置き換える）
git remote add origin https://github.com/YOUR_USERNAME/MangaAnime-Info-delivery-system.git

# デフォルトブランチ名を設定
git branch -M main

# 初回プッシュ
git push -u origin main
```

---

## 3️⃣ GitHub CLIのセットアップ（PR作成に必要）

### インストール

**Windows:**
```bash
# winget を使用
winget install GitHub.cli

# または Chocolatey
choco install gh

# または Scoop
scoop install gh
```

**確認:**
```bash
gh --version
```

### 認証

```bash
# インタラクティブ認証
gh auth login

# ブラウザで認証を選択
# GitHubアカウントでログイン
# 必要な権限を許可
```

**認証状態の確認:**
```bash
gh auth status
```

---

## 4️⃣ ブランチ戦略の設定

### 開発用ブランチの作成

```bash
# 開発ブランチを作成
git checkout -b develop

# 機能開発用のブランチ作成例
git checkout -b feature/backend-enhancements
```

### 推奨ブランチ戦略

```
main (production)
  ↑
develop (development)
  ↑
feature/xxx (機能開発)
```

**ブランチ命名規則:**
- `feature/機能名` - 新機能開発
- `bugfix/バグ名` - バグ修正
- `hotfix/修正名` - 緊急修正
- `refactor/対象名` - リファクタリング
- `docs/内容名` - ドキュメント更新

---

## 5️⃣ `/commit-push-pr` コマンドの使用

これで `/commit-push-pr` スラッシュコマンドが使えるようになりました！

### 基本的な使い方

```
# Claude Codeで以下を入力
/commit-push-pr
```

Claudeが自動的に以下を実行します：
1. 変更内容の分析
2. 適切なコミットメッセージの生成
3. コミット・プッシュの実行
4. Pull Requestの作成

### 実行前のチェックリスト

- [ ] 機能ブランチで作業している（main/masterではない）
- [ ] 機密情報を含むファイルが変更に含まれていない
- [ ] テストが通っている（可能であれば）
- [ ] コードレビュー可能な状態になっている

---

## 6️⃣ トラブルシューティング

### Q: `git push` で Permission denied エラーが出る

**A: SSH鍵の設定またはPATの設定が必要です**

**オプション1: SSH鍵を使用**
```bash
# SSH鍵の生成
ssh-keygen -t ed25519 -C "your_email@example.com"

# 公開鍵をGitHubに追加
# https://github.com/settings/keys
cat ~/.ssh/id_ed25519.pub
```

**オプション2: Personal Access Token (PAT) を使用**
```bash
# GitHubでPATを生成
# https://github.com/settings/tokens

# リモートURLをHTTPSに変更
git remote set-url origin https://github.com/USERNAME/REPO.git

# プッシュ時にPATを使用
# Username: あなたのGitHubユーザー名
# Password: 生成したPAT
```

### Q: `gh pr create` でエラーが出る

**A: 認証を再実行してください**
```bash
gh auth logout
gh auth login
```

### Q: コミット時にpre-commitフックでエラーが出る

**A: フックの内容を確認し、修正してください**
```bash
# フックのエラー内容を確認
# コードフォーマットなどの自動修正を実行
black modules/ tests/
flake8 modules/ tests/

# 再度コミット
git add .
git commit --amend --no-edit
```

---

## 7️⃣ セットアップ完了の確認

以下のコマンドがすべて正常に動作すれば、セットアップ完了です：

```bash
# Gitリポジトリの状態確認
git status

# リモートリポジトリの確認
git remote -v

# GitHub CLIの動作確認
gh repo view

# 現在のブランチ確認
git branch --show-current
```

**期待される出力:**
```
$ git remote -v
origin  https://github.com/USERNAME/MangaAnime-Info-delivery-system.git (fetch)
origin  https://github.com/USERNAME/MangaAnime-Info-delivery-system.git (push)

$ gh repo view
USERNAME/MangaAnime-Info-delivery-system
...
```

---

## 🎉 次のステップ

1. ✅ 開発用ブランチを作成
2. ✅ 並列開発で作成されたファイルをコミット
3. ✅ `/commit-push-pr` コマンドを実行
4. ✅ Pull Requestのレビュー・マージ

---

**作成日**: 2025年11月11日
**バージョン**: 1.0.0
