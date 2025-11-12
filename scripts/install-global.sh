#!/bin/bash

echo "🌍 Installing Global AI Development Environment"
echo "================================================"

# グローバル設定ディレクトリ
GLOBAL_CONFIG_DIR="$HOME/.claude"
GLOBAL_AGENTS_DIR="$HOME/.claude/agents"
TEMPLATE_DIR="$HOME/.claude/templates"

# 1. グローバルディレクトリ作成
echo "📁 Creating global directories..."
mkdir -p "$GLOBAL_CONFIG_DIR"
mkdir -p "$GLOBAL_AGENTS_DIR"
mkdir -p "$TEMPLATE_DIR"

# 2. 設定ファイルをグローバルにコピー
echo "📋 Copying configuration files..."
cp -r .claude/agents/* "$GLOBAL_AGENTS_DIR/" 2>/dev/null || true
cp .claude/project-config.json "$GLOBAL_CONFIG_DIR/global-config.json"

# 3. グローバル初期化スクリプト作成
cat > "$GLOBAL_CONFIG_DIR/init-project.sh" << 'EOF'
#!/bin/bash

# 新規プロジェクトで実行するスクリプト
PROJECT_DIR=$(pwd)

echo "🚀 Initializing AI Development Environment for $PROJECT_DIR"

# .claudeディレクトリ作成
mkdir -p .claude/{agents,context7,flow-config,hooks,serena,workflows,reports}

# グローバル設定をシンボリックリンク
ln -sf ~/.claude/agents/* .claude/agents/
ln -sf ~/.claude/global-config.json .claude/project-config.json

# ローカル設定ファイル作成
cat > .claude/local-config.json << 'CONFIG'
{
  "projectName": "$(basename $PROJECT_DIR)",
  "inheritGlobal": true,
  "localOverrides": {}
}
CONFIG

echo "✅ AI Development Environment initialized!"
echo "   All features are now enabled for this project."
EOF

chmod +x "$GLOBAL_CONFIG_DIR/init-project.sh"

# 4. グローバルエイリアス設定
cat > "$GLOBAL_CONFIG_DIR/claude-env.sh" << 'EOF'
# Claude AI Development Environment
export CLAUDE_HOME="$HOME/.claude"
export PATH="$CLAUDE_HOME/bin:$PATH"

# エイリアス
alias claude-init="bash $CLAUDE_HOME/init-project.sh"
alias claude-flow="npx claude-flow@alpha swarm --claude"
alias claude-status="node $CLAUDE_HOME/scripts/status.js"

# 関数: 新規プロジェクト作成時に自動初期化
claude-new-project() {
  local project_name="$1"
  if [ -z "$project_name" ]; then
    echo "Usage: claude-new-project <project-name>"
    return 1
  fi
  
  mkdir -p "$project_name"
  cd "$project_name"
  claude-init
  npm init -y
  echo "✨ Project '$project_name' created with AI environment!"
}

# 関数: 既存プロジェクトに追加
claude-enable() {
  if [ ! -f "package.json" ]; then
    echo "⚠️  Not a Node.js project. Create package.json first."
    return 1
  fi
  
  claude-init
  echo "✨ AI environment enabled for current project!"
}
EOF

# 5. テンプレートファイルをグローバルに保存
echo "📦 Saving templates..."
cp -r .claude "$TEMPLATE_DIR/default-claude"
cp package.json "$TEMPLATE_DIR/package-template.json"
cp -r scripts "$TEMPLATE_DIR/scripts"
cp -r config "$TEMPLATE_DIR/config"
cp -r src "$TEMPLATE_DIR/src"

# 6. グローバルnpmパッケージのインストール（オプション）
echo "📦 Installing global npm tools..."
npm install -g claude-flow@alpha 2>/dev/null || echo "⚠️  claude-flow installation skipped"

# 7. シェル設定に追加
echo ""
echo "📝 Add the following line to your ~/.bashrc or ~/.zshrc:"
echo ""
echo "   source $GLOBAL_CONFIG_DIR/claude-env.sh"
echo ""
echo "Then reload your shell or run: source ~/.bashrc"

# 8. 完了メッセージ
echo ""
echo "========================================="
echo "✅ Global installation complete!"
echo "========================================="
echo ""
echo "Usage:"
echo "  claude-new-project <name>  - Create new project with AI env"
echo "  claude-enable              - Enable AI env in existing project"
echo "  claude-init                - Initialize AI env in current directory"
echo "  claude-flow                - Start Claude-Flow swarm"
echo ""
echo "The AI environment will now be available in ALL your projects!"