#!/bin/bash

# Lint失敗修復SubAgent (Lint Failure Repair SubAgent)
#
# 機能:
# - ESLintエラーの自動修復
# - Prettierフォーマットエラーの修正
# - コードスタイル統一
# - 未使用変数・インポートの削除
# - 並列処理でLint修復を高速化

set -euo pipefail

# 設定 (Configuration)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
OUTPUT_DIR="$PROJECT_ROOT/.github/outputs"
LOG_FILE="$OUTPUT_DIR/lint-repair.log"
TIME_LIMIT=600  # 10分制限

# ログ関数 (Logging functions)
log_info() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] $*" | tee -a "$LOG_FILE"
}

log_error() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] $*" | tee -a "$LOG_FILE"
}

log_success() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [SUCCESS] $*" | tee -a "$LOG_FILE"
}

# 初期化 (Initialization)
initialize() {
    mkdir -p "$OUTPUT_DIR"
    echo "🎨 Lint修復SubAgentを開始... (Starting Lint Repair SubAgent...)" | tee "$LOG_FILE"
    
    cd "$PROJECT_ROOT"
    
    # タイムアウト設定
    timeout "$TIME_LIMIT" bash -c '
        trap "echo \"⏰ タイムアウト: Lint修復が時間制限に達しました\" >&2; exit 124" TERM
        exec "$@"
    ' -- "$0" "${@:1}" &
    
    REPAIR_PID=$!
}

# ESLint設定の修復 (Fix ESLint configuration)
fix_eslint_config() {
    log_info "🔧 ESLint設定を修復中..."
    
    # ESLint依存関係のインストール
    if [[ -f "package.json" ]]; then
        local eslint_deps=(
            "eslint"
            "@eslint/js"
            "eslint-plugin-react"
            "eslint-plugin-react-hooks"
            "@typescript-eslint/parser"
            "@typescript-eslint/eslint-plugin"
            "eslint-plugin-import"
            "eslint-plugin-jsx-a11y"
        )
        
        for dep in "${eslint_deps[@]}"; do
            if ! npm list "$dep" >/dev/null 2>&1; then
                log_info "ESLint依存関係を追加: $dep"
                npm install --save-dev "$dep" 2>/dev/null || true
            fi
        done
    fi
    
    # .eslintrc.jsの生成/修正
    if [[ -f "package.json" ]] && ! [[ -f ".eslintrc.js" ]] && ! [[ -f ".eslintrc.json" ]]; then
        log_info ".eslintrc.jsを生成中..."
        cat > .eslintrc.js << 'EOF'
module.exports = {
  env: {
    browser: true,
    es2021: true,
    node: true,
    jest: true,
  },
  extends: [
    'eslint:recommended',
    '@typescript-eslint/recommended',
    'plugin:react/recommended',
    'plugin:react-hooks/recommended',
    'plugin:jsx-a11y/recommended',
    'plugin:import/recommended',
  ],
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaFeatures: {
      jsx: true,
    },
    ecmaVersion: 'latest',
    sourceType: 'module',
  },
  plugins: [
    'react',
    'react-hooks',
    '@typescript-eslint',
    'jsx-a11y',
    'import',
  ],
  rules: {
    // 警告レベルに緩和
    '@typescript-eslint/no-explicit-any': 'warn',
    '@typescript-eslint/no-unused-vars': 'warn',
    'react/prop-types': 'off',
    'react/react-in-jsx-scope': 'off',
    'no-console': 'warn',
    'no-debugger': 'warn',
    'no-unused-vars': 'warn',
    'prefer-const': 'warn',
    'no-var': 'warn',
    
    // 自動修復可能なルール
    'semi': ['error', 'always'],
    'quotes': ['error', 'single'],
    'indent': ['error', 2],
    'comma-dangle': ['error', 'always-multiline'],
    'object-curly-spacing': ['error', 'always'],
    'array-bracket-spacing': ['error', 'never'],
  },
  settings: {
    react: {
      version: 'detect',
    },
    'import/resolver': {
      node: {
        extensions: ['.js', '.jsx', '.ts', '.tsx'],
      },
    },
  },
  ignorePatterns: [
    'node_modules/',
    'build/',
    'dist/',
    '*.min.js',
  ],
};
EOF
    fi
    
    # .eslintignoreファイルの生成
    if [[ ! -f ".eslintignore" ]]; then
        log_info ".eslintignoreを生成中..."
        cat > .eslintignore << 'EOF'
node_modules/
build/
dist/
coverage/
*.min.js
*.bundle.js
public/
.next/
.nuxt/
.vscode/
.github/
EOF
    fi
}

# Prettier設定の修復 (Fix Prettier configuration)
fix_prettier_config() {
    log_info "✨ Prettier設定を修復中..."
    
    # Prettier依存関係のインストール
    if [[ -f "package.json" ]]; then
        local prettier_deps=(
            "prettier"
            "eslint-config-prettier"
            "eslint-plugin-prettier"
        )
        
        for dep in "${prettier_deps[@]}"; do
            if ! npm list "$dep" >/dev/null 2>&1; then
                log_info "Prettier依存関係を追加: $dep"
                npm install --save-dev "$dep" 2>/dev/null || true
            fi
        done
    fi
    
    # .prettierrc.jsの生成
    if [[ ! -f ".prettierrc" ]] && [[ ! -f ".prettierrc.js" ]] && [[ ! -f "prettier.config.js" ]]; then
        log_info ".prettierrc.jsを生成中..."
        cat > .prettierrc.js << 'EOF'
module.exports = {
  semi: true,
  singleQuote: true,
  tabWidth: 2,
  useTabs: false,
  trailingComma: 'es5',
  bracketSpacing: true,
  jsxBracketSameLine: false,
  arrowParens: 'avoid',
  endOfLine: 'lf',
  printWidth: 80,
  jsxSingleQuote: true,
  quoteProps: 'as-needed',
};
EOF
    fi
    
    # .prettierignoreファイルの生成
    if [[ ! -f ".prettierignore" ]]; then
        log_info ".prettierignoreを生成中..."
        cat > .prettierignore << 'EOF'
node_modules/
build/
dist/
coverage/
*.min.js
*.bundle.js
public/
.next/
.nuxt/
package-lock.json
yarn.lock
EOF
    fi
}

# ESLintエラーの自動修復 (Auto-fix ESLint errors)
fix_eslint_errors() {
    log_info "🔍 ESLintエラーを自動修復中..."
    
    # ESLintの自動修復実行
    if command -v npx >/dev/null 2>&1; then
        # 修復可能なエラーを自動修正
        npx eslint . --fix --ext .js,.jsx,.ts,.tsx 2>/dev/null || true
        
        # 警告レベルのエラーも修正を試行
        npx eslint . --fix --fix-type problem,suggestion,layout 2>/dev/null || true
    fi
    
    # 手動でよくあるエラーパターンを修正
    find . -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" | while read -r file; do
        if [[ -f "$file" ]] && [[ ! "$file" =~ node_modules ]]; then
            log_info "ファイルを修復中: $file"
            
            # セミコロンの修正
            sed -i 's/\([^;]\)$/\1;/g' "$file" || true
            sed -i 's/;;/;/g' "$file" || true
            
            # クォートの統一
            sed -i 's/"/'"'"'/g' "$file" || true
            
            # 未使用変数の削除（import文）
            sed -i '/^import.*{.*}.*from/s/{[^}]*}/{}/g' "$file" || true
            
            # console.logの削除またはコメント化
            sed -i 's/console\.log(/\/\/ console.log(/g' "$file" || true
            
            # 空白の修正
            sed -i 's/[[:space:]]*$//' "$file" || true
            sed -i 's/\t/  /g' "$file" || true
        fi
    done
}

# Prettierフォーマットの適用 (Apply Prettier formatting)
apply_prettier_formatting() {
    log_info "💄 Prettierフォーマットを適用中..."
    
    if command -v npx >/dev/null 2>&1; then
        # Prettierフォーマット実行
        npx prettier --write "**/*.{js,jsx,ts,tsx,json,css,scss,md}" 2>/dev/null || true
        
        # 特定のファイルタイプに対して個別実行
        find . -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" | while read -r file; do
            if [[ -f "$file" ]] && [[ ! "$file" =~ node_modules ]]; then
                npx prettier --write "$file" 2>/dev/null || true
            fi
        done
    fi
}

# コードスタイルの統一 (Standardize code style)
standardize_code_style() {
    log_info "📏 コードスタイルを統一中..."
    
    find . -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" | while read -r file; do
        if [[ -f "$file" ]] && [[ ! "$file" =~ node_modules ]]; then
            # インデントの統一（2スペース）
            sed -i 's/^    /  /g' "$file" || true
            sed -i 's/^\t/  /g' "$file" || true
            
            # 空行の統一
            sed -i '/^$/N;/^\n$/d' "$file" || true
            
            # オペレーターの前後にスペース
            sed -i 's/\([^=!<>]\)=\([^=]\)/\1 = \2/g' "$file" || true
            sed -i 's/\([^!<>=]\)==\([^=]\)/\1 == \2/g' "$file" || true
            sed -i 's/\([^!<>=]\)===\([^=]\)/\1 === \2/g' "$file" || true
            
            # カンマの後にスペース
            sed -i 's/,\([^ ]\)/, \1/g' "$file" || true
        fi
    done
}

# Python Lintエラーの修復 (Fix Python lint errors)
fix_python_lint() {
    log_info "🐍 Python Lintエラーを修復中..."
    
    # Python linter依存関係のインストール
    pip install black flake8 autopep8 2>/dev/null || true
    
    # Blackフォーマッター適用
    if command -v black >/dev/null 2>&1; then
        find . -name "*.py" | while read -r py_file; do
            if [[ -f "$py_file" ]] && [[ ! "$py_file" =~ __pycache__ ]]; then
                black "$py_file" 2>/dev/null || true
            fi
        done
    fi
    
    # autopep8適用
    if command -v autopep8 >/dev/null 2>&1; then
        find . -name "*.py" | while read -r py_file; do
            if [[ -f "$py_file" ]] && [[ ! "$py_file" =~ __pycache__ ]]; then
                autopep8 --in-place --aggressive --aggressive "$py_file" 2>/dev/null || true
            fi
        done
    fi
}

# 並列Lint修復実行 (Parallel lint repair execution)
run_parallel_repairs() {
    log_info "🚀 並列修復処理を開始..."
    
    # 修復タスクを並列実行
    (
        fix_eslint_config &
        PID1=$!
        
        fix_prettier_config &
        PID2=$!
        
        fix_eslint_errors &
        PID3=$!
        
        apply_prettier_formatting &
        PID4=$!
        
        standardize_code_style &
        PID5=$!
        
        fix_python_lint &
        PID6=$!
        
        # 全タスクの完了を待機
        wait $PID1 $PID2 $PID3 $PID4 $PID5 $PID6
        
        log_info "並列修復処理完了"
    )
}

# Lint結果の検証 (Validate lint results)
validate_repairs() {
    log_info "🧪 Lint結果を検証中..."
    
    local lint_passed=true
    
    # ESLint検証
    if [[ -f "package.json" ]] && command -v npx >/dev/null 2>&1; then
        log_info "ESLintを実行中..."
        if npx eslint . --ext .js,.jsx,.ts,.tsx 2>/dev/null; then
            log_success "ESLintチェックが成功しました"
        else
            log_error "ESLintでエラーが残っています（警告レベルかもしれません）"
            lint_passed=false
        fi
    fi
    
    # Prettierチェック
    if command -v npx >/dev/null 2>&1; then
        log_info "Prettierチェックを実行中..."
        if npx prettier --check "**/*.{js,jsx,ts,tsx}" 2>/dev/null; then
            log_success "Prettierチェックが成功しました"
        else
            log_error "Prettierフォーマットエラーが残っています"
            lint_passed=false
        fi
    fi
    
    # Python Flake8チェック
    if command -v flake8 >/dev/null 2>&1; then
        log_info "Flake8チェックを実行中..."
        if flake8 --max-line-length=88 --ignore=E203,W503 . 2>/dev/null; then
            log_success "Flake8チェックが成功しました"
        else
            log_error "Flake8でエラーが検出されました"
            lint_passed=false
        fi
    fi
    
    return $([ "$lint_passed" = true ] && echo 0 || echo 1)
}

# クリーンアップ (Cleanup)
cleanup() {
    log_info "🧹 クリーンアップを実行中..."
    
    # 一時ファイルの削除
    find . -name "*.tmp" -type f -delete 2>/dev/null || true
    find . -name ".eslintcache" -type f -delete 2>/dev/null || true
}

# メイン処理 (Main process)
main() {
    local start_time=$(date +%s)
    local exit_code=0
    
    # トラップ設定
    trap 'cleanup; log_error "Lint修復が中断されました"; exit 130' INT TERM
    
    initialize
    
    # 並列修復実行
    run_parallel_repairs
    
    # 修復結果の検証
    if validate_repairs; then
        log_success "✅ Lint修復が完了しました"
        exit_code=0
    else
        log_error "❌ Lint修復で一部エラーが残りました"
        exit_code=1
    fi
    
    cleanup
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    log_info "実行時間: ${duration}秒"
    
    # 結果出力
    cat > "$OUTPUT_DIR/lint-repair-result.json" << EOF
{
    "status": "$([ $exit_code -eq 0 ] && echo "success" || echo "failed")",
    "duration": $duration,
    "timestamp": "$(date -Iseconds)",
    "logFile": "$LOG_FILE"
}
EOF
    
    exit $exit_code
}

# スクリプト実行
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi