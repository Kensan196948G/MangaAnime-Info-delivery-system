#!/usr/bin/env python3
"""
Fix hardcoded paths in Python files
"""

import os
import re
from pathlib import Path

# Old path pattern to replace
OLD_PATH = "/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system"

# Files to fix
FILES_TO_FIX = [
    "check_structure.py",
    "direct_file_check.py",
    "fix_all_tests.py",
    "fix_tests_final.py",
    "list_tests.py",
    "run_fixed_tests.py",
    "test_discovery.py",
    "verify_tests.py",
    "scripts/integration_test.py",
    "scripts/operational_monitoring.py",
    "scripts/performance_validation.py",
    ".claude/Agents/agent_loader.py",
]

def fix_file(filepath):
    """Fix hardcoded paths in a file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        if OLD_PATH not in content:
            print(f"  SKIP {filepath} - No hardcoded paths found")
            return False

        # Replace hardcoded paths with dynamic path resolution
        # Pattern 1: Direct string assignment
        content = re.sub(
            r'base_path = ["\']' + re.escape(OLD_PATH) + r'["\']',
            'base_path = str(Path(__file__).parent.resolve())',
            content
        )

        # Pattern 2: Path() constructor
        content = re.sub(
            r'Path\(["\']' + re.escape(OLD_PATH) + r'["\']\)',
            'Path(__file__).parent.resolve()',
            content
        )

        # Pattern 3: os.chdir or similar
        content = re.sub(
            r'["\']' + re.escape(OLD_PATH) + r'["\']',
            'str(Path(__file__).parent.resolve())',
            content
        )

        # Ensure Path is imported
        if 'from pathlib import Path' not in content and 'import pathlib' not in content:
            # Add import after shebang and docstring
            lines = content.split('\n')
            insert_pos = 0

            # Skip shebang
            if lines[0].startswith('#!'):
                insert_pos = 1

            # Skip docstring
            if insert_pos < len(lines) and lines[insert_pos].strip().startswith('"""'):
                while insert_pos < len(lines) and '"""' not in lines[insert_pos][3:]:
                    insert_pos += 1
                insert_pos += 1

            # Find import section
            while insert_pos < len(lines) and (lines[insert_pos].strip() == '' or lines[insert_pos].startswith('#')):
                insert_pos += 1

            # Add import
            if insert_pos < len(lines) and 'import' in lines[insert_pos]:
                # Find end of import block
                while insert_pos < len(lines) and (lines[insert_pos].startswith('import') or lines[insert_pos].startswith('from')):
                    insert_pos += 1
                lines.insert(insert_pos, 'from pathlib import Path')
            else:
                lines.insert(insert_pos, 'from pathlib import Path')

            content = '\n'.join(lines)

        # Write back
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"  OK   {filepath} - Fixed")
        return True

    except Exception as e:
        print(f"  ERR  {filepath} - Error: {e}")
        return False

def main():
    print("Fixing hardcoded paths in Python files...")
    print(f"Old path: {OLD_PATH}")
    print(f"New path: Dynamic (Path(__file__).parent.resolve())")
    print()

    project_root = Path(__file__).parent
    fixed_count = 0

    for file_path in FILES_TO_FIX:
        full_path = project_root / file_path
        if full_path.exists():
            if fix_file(full_path):
                fixed_count += 1
        else:
            print(f"  WARN {file_path} - File not found")

    print()
    print(f"Fixed {fixed_count} files")

if __name__ == "__main__":
    main()
