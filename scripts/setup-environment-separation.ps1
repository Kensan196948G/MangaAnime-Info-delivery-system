##############################################################################
# MangaAnime情報配信システム - 環境分離セットアップスクリプト (Windows版)
##############################################################################
#
# 用途: 開発環境と本番環境を完全に分離し、Git Worktreeベースの並列開発環境を構築
#
# 実行方法:
#   PowerShell -ExecutionPolicy Bypass -File scripts\setup-environment-separation.ps1
#
# 前提条件:
#   - 管理者権限で実行
#   - Git for Windows インストール済み
#   - Python 3.8+ インストール済み
#   - WSL2インストール済み（Linuxディレクトリアクセス用）
#
##############################################################################

# エラー処理設定
$ErrorActionPreference = "Stop"

# カラー関数
function Write-Info { param($Message) Write-Host "[INFO] $Message" -ForegroundColor Blue }
function Write-Success { param($Message) Write-Host "[SUCCESS] $Message" -ForegroundColor Green }
function Write-Warning { param($Message) Write-Host "[WARNING] $Message" -ForegroundColor Yellow }
function Write-ErrorMsg { param($Message) Write-Host "[ERROR] $Message" -ForegroundColor Red }
function Write-Section {
    param($Message)
    Write-Host ""
    Write-Host "===================================================" -ForegroundColor Cyan
    Write-Host "  $Message" -ForegroundColor Cyan
    Write-Host "===================================================" -ForegroundColor Cyan
    Write-Host ""
}

# プロジェクトルート取得
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

# LinuxパスをWindowsパスに変換
if ($ProjectRoot -match "^/mnt/([a-z])/(.*)") {
    $DriveLetter = $matches[1].ToUpper()
    $PathPart = $matches[2]
    $ProjectRoot = "${DriveLetter}:\$PathPart"
    Write-Info "Windowsパスに変換: $ProjectRoot"
}

# Windows用Worktreeの基準パスを推定
$BaseRepo = $ProjectRoot
if ($BaseRepo -match "-dev-win$") {
    $BaseRepo = $BaseRepo -replace "-dev-win$", ""
} elseif ($BaseRepo -match "-win$") {
    $BaseRepo = $BaseRepo -replace "-win$", ""
}

$ProjectName = Split-Path -Leaf $BaseRepo
Write-Info "プロジェクトルート: $ProjectRoot"
Write-Info "プロジェクト名: $ProjectName"

# 設定（Windows用OS別Worktree）
$ProdDir = "$BaseRepo-win"
$DevDir = "$BaseRepo-dev-win"
$IPAddress = "192.168.0.187"
$DevHttpPort = "5000"
$DevHttpsPort = "8444"
$ProdHttpPort = "3030"
$ProdHttpsPort = "8446"
$ProdBranch = "main-win"
$DevBranch = "develop-win"

##############################################################################
# Phase 1: 前提条件チェック
##############################################################################

Write-Section "Phase 1: 前提条件チェック"

# 管理者権限確認
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-ErrorMsg "このスクリプトは管理者権限で実行する必要があります"
    Write-Info "PowerShellを管理者として実行してください"
    exit 1
}
Write-Success "管理者権限確認完了"

# Gitリポジトリ確認
if (-not (Test-Path "$ProjectRoot\.git")) {
    Write-ErrorMsg "Gitリポジトリが見つかりません: $ProjectRoot\.git"
    exit 1
}
Write-Success "Gitリポジトリ確認完了"

# Python確認
try {
    $PythonVersion = & python --version 2>&1
    Write-Success "Python確認完了: $PythonVersion"
} catch {
    Write-ErrorMsg "Pythonがインストールされていません"
    exit 1
}

# Git確認
try {
    $GitVersion = & git --version
    Write-Success "Git確認完了: $GitVersion"
} catch {
    Write-ErrorMsg "Gitがインストールされていません"
    exit 1
}

##############################################################################
# Phase 2: Git Worktree構成
##############################################################################

Write-Section "Phase 2: Git Worktree構成"

Set-Location $ProjectRoot

# developブランチ作成（存在しない場合）
$BranchExists = & git show-ref --verify --quiet refs/heads/develop 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Info "developブランチを作成します..."
    & git branch develop
    Write-Success "developブランチ作成完了"
} else {
    Write-Warning "developブランチは既に存在します"
}

# Windows用ブランチ作成（存在しない場合）
$ProdBranchExists = & git show-ref --verify --quiet "refs/heads/$ProdBranch" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Info "$ProdBranch ブランチを作成します..."
    & git branch $ProdBranch main
    Write-Success "$ProdBranch ブランチ作成完了"
} else {
    Write-Warning "$ProdBranch ブランチは既に存在します"
}

$DevBranchExists = & git show-ref --verify --quiet "refs/heads/$DevBranch" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Info "$DevBranch ブランチを作成します..."
    & git branch $DevBranch develop
    Write-Success "$DevBranch ブランチ作成完了"
} else {
    Write-Warning "$DevBranch ブランチは既に存在します"
}

# Windows本番Worktree作成
if (Test-Path $ProdDir) {
    Write-Warning "本番環境ディレクトリが既に存在します: $ProdDir"
} else {
    Write-Info "Windows本番Worktreeを作成します..."
    & git worktree add $ProdDir $ProdBranch
    Write-Success "Windows本番Worktree作成完了: $ProdDir"
}

# Windows開発Worktree作成
if (Test-Path $DevDir) {
    Write-Warning "開発環境ディレクトリが既に存在します: $DevDir"
    Write-Info "既存の開発環境は削除せず保持します"
} else {
    Write-Info "Windows開発Worktreeを作成します..."
    & git worktree add $DevDir $DevBranch
    Write-Success "Windows開発Worktree作成完了: $DevDir"
}

# Worktree一覧表示
Write-Info "Worktree一覧:"
& git worktree list

##############################################################################
# Phase 3: ディレクトリ構造整備
##############################################################################

Write-Section "Phase 3: ディレクトリ構造整備"

# 本番環境ディレクトリ
Write-Info "本番環境ディレクトリを整備します..."
@("data", "logs\prod", "backups\prod", "config") | ForEach-Object {
    $Dir = Join-Path $ProdDir $_
    if (-not (Test-Path $Dir)) {
        New-Item -Path $Dir -ItemType Directory -Force | Out-Null
    }
}

# 開発環境ディレクトリ
Write-Info "開発環境ディレクトリを整備します..."
@("data", "logs\dev", "backups\dev", "config", "sample_data") | ForEach-Object {
    $Dir = Join-Path $DevDir $_
    if (-not (Test-Path $Dir)) {
        New-Item -Path $Dir -ItemType Directory -Force | Out-Null
    }
}

Write-Success "ディレクトリ構造整備完了"

##############################################################################
# Phase 4: Python仮想環境構築
##############################################################################

Write-Section "Phase 4: Python仮想環境構築"

# 本番環境Python仮想環境
$ProdVenv = Join-Path $ProdDir "venv_prod"
if (-not (Test-Path $ProdVenv)) {
    Write-Info "本番環境Python仮想環境を作成します..."
    Set-Location $ProdDir
    & python -m venv venv_prod
    & "$ProdVenv\Scripts\python.exe" -m pip install --upgrade pip setuptools wheel

    $RequirementsFile = Join-Path $ProdDir "requirements.txt"
    if (Test-Path $RequirementsFile) {
        & "$ProdVenv\Scripts\pip.exe" install -r $RequirementsFile
    }

    # Gunicornは不要（Windows版）
    Write-Success "本番環境Python仮想環境作成完了"
} else {
    Write-Warning "本番環境Python仮想環境は既に存在します"
}

# 開発環境Python仮想環境
$DevVenv = Join-Path $DevDir "venv_dev"
if (-not (Test-Path $DevVenv)) {
    Write-Info "開発環境Python仮想環境を作成します..."
    Set-Location $DevDir
    & python -m venv venv_dev
    & "$DevVenv\Scripts\python.exe" -m pip install --upgrade pip setuptools wheel

    $RequirementsFile = Join-Path $DevDir "requirements.txt"
    if (Test-Path $RequirementsFile) {
        & "$DevVenv\Scripts\pip.exe" install -r $RequirementsFile
    }

    # 開発用パッケージインストール
    & "$DevVenv\Scripts\pip.exe" install pytest pytest-cov black flake8 mypy ipython
    Write-Success "開発環境Python仮想環境作成完了"
} else {
    Write-Warning "開発環境Python仮想環境は既に存在します"
}

##############################################################################
# Phase 5: 設定ファイル作成
##############################################################################

Write-Section "Phase 5: 設定ファイル作成"

# 本番環境設定ファイル
$ProdConfigSrc = Join-Path $ProdDir "config\config.json"
$ProdConfigDst = Join-Path $ProdDir "config\config.prod.json"
if ((Test-Path $ProdConfigSrc) -and -not (Test-Path $ProdConfigDst)) {
    Write-Info "本番環境設定ファイルを作成します..."
    Copy-Item $ProdConfigSrc $ProdConfigDst

    # 本番環境設定を更新（PowerShell版）
    $Config = Get-Content $ProdConfigDst | ConvertFrom-Json
    $Config.system.environment = "production"
    $Config.server.port = [int]$ProdHttpPort
    $Config.database.path = "data/prod_db.sqlite3"
    $Config.logging.file_path = "./logs/prod/app.log"
    $Config | ConvertTo-Json -Depth 10 | Set-Content $ProdConfigDst

    Write-Success "本番環境設定ファイル作成完了"
}

# 開発環境設定ファイル
$DevConfigSrc = Join-Path $DevDir "config\config.json"
$DevConfigDst = Join-Path $DevDir "config\config.dev.json"
if ((Test-Path $DevConfigSrc) -and -not (Test-Path $DevConfigDst)) {
    Write-Info "開発環境設定ファイルを作成します..."
    Copy-Item $DevConfigSrc $DevConfigDst

    # 開発環境設定を更新（PowerShell版）
    $Config = Get-Content $DevConfigDst | ConvertFrom-Json
    $Config.system.environment = "development"
    $Config.system.log_level = "DEBUG"
    $Config.server.port = [int]$DevHttpPort
    $Config.database.path = "data/dev_db.sqlite3"
    $Config.logging.file_path = "./logs/dev/app.log"
    $Config | ConvertTo-Json -Depth 10 | Set-Content $DevConfigDst

    Write-Success "開発環境設定ファイル作成完了"
}

##############################################################################
# Phase 6: Windows Serviceスクリプト作成（NSSM使用推奨）
##############################################################################

Write-Section "Phase 6: Windows Serviceスクリプト作成"

Write-Info "Windows環境では、NSSmを使用してサービス化することを推奨します"
Write-Info "NSSM (Non-Sucking Service Manager) ダウンロード: https://nssm.cc/download"

# 開発環境起動スクリプト
$DevStartScript = Join-Path $DevDir "start-dev.ps1"
@"
`$ErrorActionPreference = "Stop"
Set-Location "$DevDir"
`$env:FLASK_ENV = "development"
`$env:FLASK_DEBUG = "1"
`$env:CONFIG_FILE = "config/config.dev.json"
`$env:DATABASE_PATH = "data/dev_db.sqlite3"
`$env:LOG_PATH = "logs/dev/app.log"
`$env:PORT = "$DevHttpPort"

& "$DevVenv\Scripts\python.exe" app\web_app.py
"@ | Set-Content $DevStartScript

Write-Success "開発環境起動スクリプト作成: $DevStartScript"

# 本番環境起動スクリプト
$ProdStartScript = Join-Path $ProdDir "start-prod.ps1"
@"
`$ErrorActionPreference = "Stop"
Set-Location "$ProdDir"
`$env:FLASK_ENV = "production"
`$env:FLASK_DEBUG = "0"
`$env:CONFIG_FILE = "config/config.prod.json"
`$env:DATABASE_PATH = "data/prod_db.sqlite3"
`$env:LOG_PATH = "logs/prod/app.log"
`$env:PORT = "$ProdHttpPort"

& "$ProdVenv\Scripts\python.exe" app\web_app.py
"@ | Set-Content $ProdStartScript

Write-Success "本番環境起動スクリプト作成: $ProdStartScript"

##############################################################################
# Phase 7: 完了レポート
##############################################################################

Write-Section "セットアップ完了"

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host "  MangaAnime情報配信システム - 環境分離セットアップ完了 (Windows版)" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host ""

Write-Host "📁 ディレクトリ構成:" -ForegroundColor Cyan
Write-Host "  本番環境: $ProdDir"
Write-Host "  開発環境: $DevDir"
Write-Host ""

Write-Host "🌐 アクセスURL:" -ForegroundColor Cyan
Write-Host "  【開発環境】" -ForegroundColor Yellow
Write-Host "    HTTP  : http://${IPAddress}:${DevHttpPort}"
Write-Host "    HTTPS : https://${IPAddress}:${DevHttpsPort} (要IIS/Nginx設定)"
Write-Host "  【本番環境】" -ForegroundColor Green
Write-Host "    HTTP  : http://${IPAddress}:${ProdHttpPort}"
Write-Host "    HTTPS : https://${IPAddress}:${ProdHttpsPort} (要IIS/Nginx設定)"
Write-Host ""

Write-Host "🔧 起動方法:" -ForegroundColor Cyan
Write-Host "  # 開発環境起動"
Write-Host "  PowerShell -ExecutionPolicy Bypass -File `"$DevStartScript`""
Write-Host ""
Write-Host "  # 本番環境起動"
Write-Host "  PowerShell -ExecutionPolicy Bypass -File `"$ProdStartScript`""
Write-Host ""

Write-Host "⚙️  Windows Service化（NSSM推奨）:" -ForegroundColor Cyan
Write-Host "  # NSSmダウンロード: https://nssm.cc/download"
Write-Host ""
Write-Host "  # 開発環境サービス登録"
Write-Host "  nssm install MangaAnime-Dev PowerShell -ExecutionPolicy Bypass -File `"$DevStartScript`""
Write-Host ""
Write-Host "  # 本番環境サービス登録"
Write-Host "  nssm install MangaAnime-Prod PowerShell -ExecutionPolicy Bypass -File `"$ProdStartScript`""
Write-Host ""

Write-Host "🌳 Git Worktree管理:" -ForegroundColor Cyan
Write-Host "  # Worktree一覧表示"
Write-Host "  cd `"$ProdDir`" ; git worktree list"
Write-Host ""
Write-Host "  # 機能開発用Worktree作成"
Write-Host "  cd `"$ProdDir`" ; git worktree add ..\MangaAnime-Info-delivery-system-feature-XXX feature/XXX"
Write-Host ""
Write-Host "  # Worktree削除"
Write-Host "  cd `"$ProdDir`" ; git worktree remove ..\MangaAnime-Info-delivery-system-feature-XXX"
Write-Host ""

Write-Host "📚 次のステップ:" -ForegroundColor Cyan
Write-Host "  1. IIS/Nginx設定（HTTPS対応）"
Write-Host "  2. Windowsファイアウォール設定（ポート開放）"
Write-Host "  3. サンプルデータ投入（開発環境）"
Write-Host "  4. 本番データ移行・クリーニング"
Write-Host "  5. ブックマーク作成"
Write-Host ""

Write-Host "📖 詳細ドキュメント:" -ForegroundColor Cyan
Write-Host "  $ProdDir\docs\ENVIRONMENT_SEPARATION_DESIGN.md"
Write-Host ""

Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Success "環境分離セットアップが正常に完了しました! (Windows版)"
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host ""
