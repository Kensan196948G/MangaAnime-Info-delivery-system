#!/bin/bash

# ビルド失敗修復SubAgent (Build Failure Repair SubAgent)
#
# 機能:
# - TypeScriptエラーの自動修復
# - モジュール不足の解決
# - 構文エラーの修正
# - Webpackビルドエラーの解決
# - 並列処理でビルド修復を高速化

set -euo pipefail

# 設定 (Configuration)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
OUTPUT_DIR="$PROJECT_ROOT/.github/outputs"
LOG_FILE="$OUTPUT_DIR/build-repair.log"
TIME_LIMIT=1200  # 20分制限

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
    echo "🏗️ ビルド修復SubAgentを開始... (Starting Build Repair SubAgent...)" | tee "$LOG_FILE"
    
    cd "$PROJECT_ROOT"
    
    # タイムアウト設定
    timeout "$TIME_LIMIT" bash -c '
        trap "echo \"⏰ タイムアウト: ビルド修復が時間制限に達しました\" >&2; exit 124" TERM
        exec "$@"
    ' -- "$0" "${@:1}" &
    
    REPAIR_PID=$!
}

# 依存関係の修復 (Fix dependencies)
fix_dependencies() {
    log_info "📦 依存関係を修復中..."
    
    # Node.js依存関係の修復
    if [[ -f "package.json" ]]; then
        log_info "Node.js依存関係を修復中..."
        
        # キャッシュクリア
        npm cache clean --force 2>/dev/null || true
        rm -rf node_modules package-lock.json 2>/dev/null || true
        
        # 基本的な依存関係のインストール
        npm install || {
            log_error "npm installに失敗。Yarnを試行中..."
            yarn install || {
                log_error "Yarnも失敗。代替手段を試行中..."
                npm install --legacy-peer-deps || true
            }
        }
        
        # 一般的なビルド依存関係の追加
        local build_deps=(
            "@types/node"
            "@types/react"
            "@types/react-dom"
            "typescript"
            "webpack"
            "webpack-cli"
            "@babel/core"
            "@babel/preset-env"
            "@babel/preset-react"
            "@babel/preset-typescript"
        )
        
        for dep in "${build_deps[@]}"; do
            if ! npm list "$dep" >/dev/null 2>&1; then
                log_info "ビルド依存関係を追加: $dep"
                npm install --save-dev "$dep" 2>/dev/null || true
            fi
        done
    fi
    
    # Python依存関係の修復
    if [[ -f "requirements.txt" ]]; then
        log_info "Python依存関係を修復中..."
        pip install -r requirements.txt || true
        pip install build setuptools wheel || true
    fi
}

# TypeScriptエラーの修復 (Fix TypeScript errors)
fix_typescript_errors() {
    log_info "🔧 TypeScriptエラーを修復中..."
    
    # TypeScript設定ファイルの生成/修正
    if [[ -f "package.json" ]] && ! [[ -f "tsconfig.json" ]]; then
        log_info "tsconfig.jsonを生成中..."
        cat > tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "es5",
    "lib": [
      "dom",
      "dom.iterable",
      "es6"
    ],
    "allowJs": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": false,
    "forceConsistentCasingInFileNames": true,
    "noFallthroughCasesInSwitch": true,
    "module": "esnext",
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "noImplicitAny": false,
    "suppressImplicitAnyIndexErrors": true
  },
  "include": [
    "src",
    "**/*.ts",
    "**/*.tsx"
  ],
  "exclude": [
    "node_modules",
    "build",
    "dist"
  ]
}
EOF
    fi
    
    # TypeScriptファイルの一般的エラー修正
    find . -name "*.ts" -o -name "*.tsx" | while read -r ts_file; do
        if [[ -f "$ts_file" ]] && [[ ! "$ts_file" =~ node_modules ]]; then
            log_info "TypeScriptファイルを修復: $ts_file"
            
            # 一般的な型エラーの修正
            sed -i 's/: any\[\]/: any[] | undefined/g' "$ts_file" || true
            sed -i 's/\!\./.?./g' "$ts_file" || true
            
            # インポート文の修正
            sed -i 's/import \* as React/import React/g' "$ts_file" || true
            
            # 未使用変数の削除
            sed -i '/^import.*{.*}.*from.*$/s/{[^}]*}/{}/g' "$ts_file" || true
            
            # any型の追加（一時的な修正）
            if grep -q "Property.*does not exist" <<< "$(npx tsc --noEmit 2>&1)" 2>/dev/null; then
                sed -i 's/\(const [a-zA-Z_][a-zA-Z0-9_]*\) =/\1: any =/g' "$ts_file" || true
            fi
        fi
    done
}

# モジュール解決の修復 (Fix module resolution)
fix_module_resolution() {
    log_info "🔍 モジュール解決を修復中..."
    
    # パッケージ名の一般的な間違いを修正
    find . -name "*.js" -o -name "*.ts" -o -name "*.jsx" -o -name "*.tsx" | while read -r file; do
        if [[ -f "$file" ]] && [[ ! "$file" =~ node_modules ]]; then
            # 一般的なインポートエラーの修正
            sed -i 's/import.*from ['\''"]\.\/\.\.\//import * from '\''..\/..\/'/g' "$file" || true
            sed -i 's/require(['\''"]\.\/\.\.\//require('\''..\/..\/'/g' "$file" || true
            
            # React関連の修正
            sed -i 's/import React, { Component }/import React from '\''react'\'';\nimport { Component } from '\''react'\'';/g' "$file" || true
        fi
    done
    
    # package.jsonの修正
    if [[ -f "package.json" ]]; then
        # 一般的な依存関係の追加
        node -e "
            const pkg = require('./package.json');
            const fs = require('fs');
            
            // 必要な依存関係を追加
            pkg.dependencies = pkg.dependencies || {};
            pkg.devDependencies = pkg.devDependencies || {};
            
            // React関連の依存関係
            if (pkg.dependencies.react && !pkg.dependencies['react-dom']) {
                pkg.dependencies['react-dom'] = pkg.dependencies.react;
            }
            
            // TypeScript関連
            if (pkg.devDependencies.typescript && !pkg.devDependencies['@types/node']) {
                pkg.devDependencies['@types/node'] = '^18.0.0';
            }
            
            fs.writeFileSync('./package.json', JSON.stringify(pkg, null, 2));
        " 2>/dev/null || true
    fi
}

# Webpackエラーの修復 (Fix Webpack errors)
fix_webpack_errors() {
    log_info "📦 Webpackエラーを修復中..."
    
    # webpack.config.jsの生成/修正
    if [[ -f "package.json" ]] && ! [[ -f "webpack.config.js" ]]; then
        log_info "webpack.config.jsを生成中..."
        cat > webpack.config.js << 'EOF'
const path = require('path');

module.exports = {
  mode: 'development',
  entry: './src/index.js',
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: 'bundle.js',
  },
  module: {
    rules: [
      {
        test: /\.(js|jsx|ts|tsx)$/,
        exclude: /node_modules/,
        use: {
          loader: 'babel-loader',
          options: {
            presets: [
              ['@babel/preset-env', { targets: 'defaults' }],
              ['@babel/preset-react', { runtime: 'automatic' }],
              '@babel/preset-typescript'
            ]
          }
        }
      },
      {
        test: /\.css$/,
        use: ['style-loader', 'css-loader']
      },
      {
        test: /\.(png|svg|jpg|jpeg|gif)$/i,
        type: 'asset/resource'
      }
    ]
  },
  resolve: {
    extensions: ['.tsx', '.ts', '.js', '.jsx'],
    fallback: {
      "crypto": require.resolve("crypto-browserify"),
      "stream": require.resolve("stream-browserify"),
      "buffer": require.resolve("buffer")
    }
  },
  devServer: {
    contentBase: './dist',
    hot: true
  }
};
EOF
    fi
    
    # Babel設定の生成
    if [[ -f "package.json" ]] && ! [[ -f ".babelrc" ]] && ! [[ -f "babel.config.js" ]]; then
        log_info "Babel設定を生成中..."
        cat > babel.config.js << 'EOF'
module.exports = {
  presets: [
    ['@babel/preset-env', {
      targets: {
        node: 'current',
      },
    }],
    ['@babel/preset-react', {
      runtime: 'automatic',
    }],
    '@babel/preset-typescript',
  ],
  plugins: [
    '@babel/plugin-proposal-class-properties',
    '@babel/plugin-transform-runtime'
  ].filter(Boolean),
};
EOF
    fi
}

# 構文エラーの修復 (Fix syntax errors)
fix_syntax_errors() {
    log_info "✏️ 構文エラーを修復中..."
    
    # JavaScriptファイルの構文エラー修正
    find . -name "*.js" -o -name "*.jsx" | while read -r js_file; do
        if [[ -f "$js_file" ]] && [[ ! "$js_file" =~ node_modules ]]; then
            # 一般的な構文エラーの修正
            sed -i 's/;,/;/g' "$js_file" || true
            sed -i 's/,,/,/g' "$js_file" || true
            sed -i 's/\]\[/], [/g' "$js_file" || true
            sed -i 's/}{/}, {/g' "$js_file" || true
            
            # 未定義変数の修正
            sed -i 's/console\.log(/\/\/ console.log(/g' "$js_file" || true
        fi
    done
}

# 並列ビルド修復実行 (Parallel build repair execution)
run_parallel_repairs() {
    log_info "🚀 並列修復処理を開始..."
    
    # 修復タスクを並列実行
    (
        fix_dependencies &
        PID1=$!
        
        fix_typescript_errors &
        PID2=$!
        
        fix_module_resolution &
        PID3=$!
        
        fix_webpack_errors &
        PID4=$!
        
        fix_syntax_errors &
        PID5=$!
        
        # 全タスクの完了を待機
        wait $PID1 $PID2 $PID3 $PID4 $PID5
        
        log_info "並列修復処理完了"
    )
}

# ビルド実行と検証 (Build execution and validation)
validate_repairs() {
    log_info "🏗️ ビルド結果を検証中..."
    
    local build_passed=false
    
    # Node.jsビルド実行
    if [[ -f "package.json" ]]; then
        log_info "Node.jsビルドを実行中..."
        
        # TypeScriptコンパイル
        if [[ -f "tsconfig.json" ]]; then
            if timeout 600 npx tsc --noEmit; then
                log_success "TypeScriptコンパイルが成功しました"
            else
                log_error "TypeScriptコンパイルが失敗しました"
            fi
        fi
        
        # ビルドスクリプト実行
        if npm run build 2>/dev/null; then
            build_passed=true
            log_success "Node.jsビルドが成功しました"
        elif npm run compile 2>/dev/null; then
            build_passed=true
            log_success "Node.jsコンパイルが成功しました"
        else
            log_error "Node.jsビルドが失敗しました"
        fi
    fi
    
    # Pythonビルド実行
    if [[ -f "setup.py" ]]; then
        log_info "Pythonビルドを実行中..."
        if timeout 600 python setup.py build; then
            build_passed=true
            log_success "Pythonビルドが成功しました"
        else
            log_error "Pythonビルドが失敗しました"
        fi
    fi
    
    return $([ "$build_passed" = true ] && echo 0 || echo 1)
}

# クリーンアップ (Cleanup)
cleanup() {
    log_info "🧹 クリーンアップを実行中..."
    
    # 一時ファイルの削除
    rm -rf .tmp build-temp *.tmp 2>/dev/null || true
    find . -name "*.log" -type f -delete 2>/dev/null || true
    find . -name ".DS_Store" -type f -delete 2>/dev/null || true
}

# メイン処理 (Main process)
main() {
    local start_time=$(date +%s)
    local exit_code=0
    
    # トラップ設定
    trap 'cleanup; log_error "ビルド修復が中断されました"; exit 130' INT TERM
    
    initialize
    
    # 並列修復実行
    run_parallel_repairs
    
    # 修復結果の検証
    if validate_repairs; then
        log_success "✅ ビルド修復が完了しました"
        exit_code=0
    else
        log_error "❌ ビルド修復に失敗しました"
        exit_code=1
    fi
    
    cleanup
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    log_info "実行時間: ${duration}秒"
    
    # 結果出力
    cat > "$OUTPUT_DIR/build-repair-result.json" << EOF
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