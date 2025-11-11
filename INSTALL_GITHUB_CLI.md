# GitHub CLI (gh) インストールガイド

## Windows でのインストール方法

### 方法1: winget を使用（推奨）

Windows 10/11 に標準搭載されているパッケージマネージャーです。

```powershell
# PowerShellまたはコマンドプロンプトで実行
winget install --id GitHub.cli
```

### 方法2: 公式インストーラーを使用

1. 公式サイトにアクセス: https://cli.github.com/
2. 「Download for Windows」をクリック
3. ダウンロードした `.msi` ファイルを実行
4. インストールウィザードに従ってインストール

### 方法3: Chocolatey を使用

Chocolatey がインストールされている場合：

```powershell
choco install gh
```

### 方法4: Scoop を使用

Scoop がインストールされている場合：

```powershell
scoop install gh
```

---

## インストール後の確認

新しいコマンドプロンプトまたはPowerShellウィンドウを開いて、以下を実行：

```bash
gh --version
```

**期待される出力:**
```
gh version 2.x.x (YYYY-MM-DD)
```

---

## GitHub CLI の認証

インストール完了後、以下のコマンドで認証してください：

```bash
gh auth login
```

**インタラクティブな質問に答えます:**

1. **Where do you use GitHub?**
   ```
   > GitHub.com
   ```

2. **What is your preferred protocol for Git operations?**
   ```
   > HTTPS (推奨)
   ```

3. **Authenticate Git with your GitHub credentials?**
   ```
   > Yes
   ```

4. **How would you like to authenticate GitHub CLI?**
   ```
   > Login with a web browser (推奨)
   ```

5. ブラウザが開くので、表示された認証コードを入力してログイン

---

## 認証確認

```bash
gh auth status
```

**期待される出力:**
```
github.com
  ✓ Logged in to github.com as Kensan196948G
  ✓ Git operations for github.com configured to use https protocol.
  ✓ Token: *******************
```

---

## トラブルシューティング

### Q: winget が使えない

**A: Windows Updateを実行してください**
```powershell
# PowerShellで実行
Get-AppxPackage -name 'Microsoft.DesktopAppInstaller'
```

存在しない場合は、Microsoft Store から「アプリ インストーラー」をインストールしてください。

### Q: インストール後も `gh: command not found` エラーが出る

**A: 環境変数のPATHが更新されていません**

1. コマンドプロンプト/PowerShellを再起動
2. それでも解決しない場合、以下のパスが環境変数に含まれているか確認：
   ```
   C:\Program Files\GitHub CLI\
   ```

### Q: 認証でエラーが出る

**A: ファイアウォールやプロキシを確認してください**

プロキシ環境の場合：
```bash
# プロキシ設定
set HTTP_PROXY=http://proxy.example.com:8080
set HTTPS_PROXY=http://proxy.example.com:8080

gh auth login
```

---

## 次のステップ

インストールと認証が完了したら：

1. ✅ Claude Code に戻る
2. ✅ `/commit-push-pr` コマンドを実行
3. ✅ 自動的にコミット・プッシュ・PR作成が完了

---

**ヘルプ:**
```bash
# GitHub CLI のヘルプ
gh --help

# 特定コマンドのヘルプ
gh repo --help
gh pr --help
```

**公式ドキュメント:**
https://cli.github.com/manual/
