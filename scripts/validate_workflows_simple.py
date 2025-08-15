#!/usr/bin/env python3
"""
GitHub Actions ワークフロー検証スクリプト（シンプル版）
ruamel.yamlを使用してonキーワードの問題を回避
"""

import os
import sys
from pathlib import Path

def validate_workflow(filepath):
    """単一のワークフローファイルを検証"""
    errors = []
    
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            
        # テキストベースの基本検証
        lines = content.split('\n')
        
        # 必須フィールドの存在確認
        has_name = any('name:' in line for line in lines)
        has_on = any(line.strip().startswith('on:') for line in lines)
        has_jobs = any('jobs:' in line for line in lines)
        
        if not has_name:
            errors.append("'name' フィールドが見つかりません")
            
        if not has_on:
            errors.append("'on' トリガーが定義されていません")
            
        if not has_jobs:
            errors.append("'jobs' セクションが見つかりません")
            
        # 構文エラーのパターンチェック
        for i, line in enumerate(lines, 1):
            # 'true:' が行頭にある場合
            if line.strip() == 'true:':
                errors.append(f"行 {i}: 'true:' は 'on:' である必要があります")
                
            # 'workflow_dispatch: null' のチェック
            if 'workflow_dispatch: null' in line:
                errors.append(f"行 {i}: 'workflow_dispatch: null' は無効です")
                
            # cron式が引用符で囲まれていない場合
            if 'cron:' in line and not any(quote in line for quote in ["'", '"']):
                if line.strip().startswith('- cron:'):
                    cron_value = line.split('cron:')[1].strip()
                    if cron_value and not cron_value.startswith(("'", '"')):
                        errors.append(f"行 {i}: cron式は引用符で囲む必要があります")
                        
    except Exception as e:
        errors.append(f"ファイル読み込みエラー: {e}")
        
    return errors

def main():
    """メイン処理"""
    workflows_dir = Path('.github/workflows')
    
    if not workflows_dir.exists():
        print("❌ .github/workflows ディレクトリが見つかりません")
        sys.exit(1)
        
    all_valid = True
    workflow_files = list(workflows_dir.glob('*.yml')) + list(workflows_dir.glob('*.yaml'))
    
    print(f"🔍 {len(workflow_files)} 個のワークフローファイルを検証中...\n")
    
    for filepath in workflow_files:
        errors = validate_workflow(filepath)
        
        if errors:
            all_valid = False
            print(f"❌ {filepath.name}:")
            for error in errors:
                print(f"   - {error}")
        else:
            print(f"✅ {filepath.name}: OK")
            
    print("\n" + "="*50)
    
    if all_valid:
        print("✅ すべてのワークフローが有効です！")
        sys.exit(0)
    else:
        print("❌ 一部のワークフローにエラーがあります")
        sys.exit(1)

if __name__ == "__main__":
    main()