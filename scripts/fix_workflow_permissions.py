#!/usr/bin/env python3
"""
GitHub Actions ワークフローの権限設定を修正するスクリプト
"""

import os
import re
import yaml
from pathlib import Path

# 各ワークフローに応じた適切な権限設定
WORKFLOW_PERMISSIONS = {
    'auto-deployment': {
        'contents': 'read',
        'deployments': 'write',
        'packages': 'write',
        'actions': 'read'
    },
    'issue-auto-management': {
        'contents': 'read',
        'issues': 'write',
        'pull-requests': 'write',
        'actions': 'write'
    },
    'mangaanime-system-check': {
        'contents': 'read',
        'issues': 'write',
        'actions': 'read'
    },
    'security-audit': {
        'contents': 'read',
        'security-events': 'write',
        'actions': 'read'
    },
    'system-health-fix': {
        'contents': 'read',
        'issues': 'write',
        'actions': 'read'
    },
    'ci': {
        'contents': 'read',
        'issues': 'write',
        'pull-requests': 'write',
        'checks': 'write',
        'actions': 'read'
    },
    'auto-error-detection-and-fix': {
        'contents': 'write',
        'issues': 'write',
        'pull-requests': 'write',
        'checks': 'read',
        'actions': 'read'
    }
}


def fix_workflow_permissions(workflow_path):
    """ワークフローファイルに権限設定を追加"""
    filename = Path(workflow_path).stem
    
    # 適切な権限を選択
    permissions = None
    for workflow_name, perms in WORKFLOW_PERMISSIONS.items():
        if workflow_name in filename:
            permissions = perms
            break
    
    if not permissions:
        # デフォルト権限
        permissions = {
            'contents': 'read',
            'actions': 'read'
        }
    
    # ファイルを読み込み
    with open(workflow_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # すでにpermissions:が存在するか確認
    if re.search(r'^permissions:', content, re.MULTILINE):
        print(f"✅ {filename}: Already has permissions")
        return False
    
    # YAMLとして解析
    try:
        workflow_data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        print(f"❌ {filename}: YAML parse error: {e}")
        return False
    
    # permissions を追加
    workflow_data['permissions'] = permissions
    
    # YAMLを再生成（きれいにフォーマット）
    with open(workflow_path, 'w', encoding='utf-8') as f:
        yaml.dump(workflow_data, f, default_flow_style=False, sort_keys=False)
    
    print(f"✅ {filename}: Added permissions")
    return True


def main():
    """メイン処理"""
    workflows_dir = Path('.github/workflows')
    
    if not workflows_dir.exists():
        print(f"❌ Directory not found: {workflows_dir}")
        return 1
    
    # 全ワークフローファイルを処理
    fixed_count = 0
    for workflow_file in workflows_dir.glob('*.yml'):
        if fix_workflow_permissions(workflow_file):
            fixed_count += 1
    
    for workflow_file in workflows_dir.glob('*.yaml'):
        if fix_workflow_permissions(workflow_file):
            fixed_count += 1
    
    print(f"\n📊 Summary: Fixed {fixed_count} workflow files")
    
    # 結果を確認
    print("\n🔍 Verification:")
    for workflow_file in workflows_dir.glob('*.yml'):
        with open(workflow_file, 'r') as f:
            content = f.read()
            if 'permissions:' in content:
                print(f"  ✅ {workflow_file.name}: Has permissions")
            else:
                print(f"  ❌ {workflow_file.name}: Missing permissions")
    
    return 0


if __name__ == '__main__':
    exit(main())