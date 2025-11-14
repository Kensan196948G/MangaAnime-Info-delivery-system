#!/bin/bash

# Project Validation Script
# セットアップ検証

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "========================================="
echo "  Validation - $(basename "$PROJECT_DIR")"
echo "========================================="

ERRORS=0
WARNINGS=0

# 検証項目
echo "Checking project structure..."

# 1. 必須ディレクトリ
for dir in .claude scripts app tests docs config; do
    if [ -d "$PROJECT_DIR/$dir" ]; then
        echo "  ✓ $dir directory exists"
    else
        echo "  ✗ $dir directory missing"
        ((ERRORS++))
    fi
done

# 2. エージェント設定
agent_count=$(ls "$PROJECT_DIR/.claude/Agents"/*.yaml 2>/dev/null | wc -l)
if [ $agent_count -eq 20 ]; then
    echo "  ✓ All 20 agents configured"
else
    echo "  ⚠ Only $agent_count agents found (expected 20)"
    ((WARNINGS++))
fi

# 3. CLAUDE.md
if [ -f "$PROJECT_DIR/.claude/CLAUDE.md" ]; then
    echo "  ✓ CLAUDE.md exists"
else
    echo "  ✗ CLAUDE.md missing"
    ((ERRORS++))
fi

# 4. MCP設定
if grep -q "mcp_enabled" "$PROJECT_DIR/config/settings.json" 2>/dev/null; then
    echo "  ✓ MCP configuration found"
else
    echo "  ⚠ MCP not configured"
    ((WARNINGS++))
fi

# 結果サマリー
echo
echo "========================================="
if [ $ERRORS -eq 0 ]; then
    if [ $WARNINGS -eq 0 ]; then
        echo "✅ Validation passed (Perfect!)"
    else
        echo "⚠️  Validation passed with $WARNINGS warnings"
    fi
else
    echo "❌ Validation failed with $ERRORS errors, $WARNINGS warnings"
fi
echo "========================================="

exit $ERRORS
