#!/usr/bin/env python3
"""
Automatically fix import paths after folder restructuring

This script adds sys.path adjustments to Python files that have been moved
to subdirectories, ensuring they can still import from the 'modules' package.

Author: System Architecture Designer
Date: 2025-11-14
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple


class ImportPathFixer:
    """Fix import paths in Python files after directory restructuring"""

    def __init__(self, project_root: Path, dry_run: bool = False):
        self.project_root = project_root
        self.dry_run = dry_run
        self.fixed_files = []
        self.skipped_files = []
        self.errors = []

    def needs_sys_path_fix(self, content: str) -> bool:
        """Check if file needs sys.path adjustment"""
        has_modules_import = bool(
            re.search(r'^\s*from modules', content, re.MULTILINE) or
            re.search(r'^\s*import modules', content, re.MULTILINE)
        )
        has_sys_path_fix = bool(
            re.search(r'sys\.path\.insert', content) or
            re.search(r'sys\.path\.append', content)
        )
        return has_modules_import and not has_sys_path_fix

    def calculate_depth(self, file_path: Path) -> int:
        """Calculate how many levels deep the file is from project root"""
        try:
            relative = file_path.relative_to(self.project_root)
            return len(relative.parents) - 1  # -1 because parents includes '.'
        except ValueError:
            return 0

    def generate_sys_path_code(self, depth: int) -> str:
        """Generate sys.path insertion code based on depth"""
        parent_chain = '.parent' * depth if depth > 0 else ''
        return f"""
import sys
from pathlib import Path
# Add project root to sys.path to allow 'from modules' imports
sys.path.insert(0, str(Path(__file__).parent{parent_chain}))
"""

    def find_insertion_point(self, lines: List[str]) -> int:
        """Find the best place to insert sys.path code"""
        in_docstring = False
        docstring_char = None

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Skip shebang
            if i == 0 and stripped.startswith('#!'):
                continue

            # Track docstrings
            if stripped.startswith('"""') or stripped.startswith("'''"):
                if not in_docstring:
                    in_docstring = True
                    docstring_char = stripped[:3]
                elif stripped.endswith(docstring_char):
                    in_docstring = False
                    continue

            # Skip comments and empty lines
            if stripped.startswith('#') or not stripped:
                continue

            # If we're past docstrings and comments, this is the insertion point
            if not in_docstring:
                return i

        return 0

    def fix_file(self, file_path: Path) -> bool:
        """Fix import paths in a single file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if not self.needs_sys_path_fix(content):
                self.skipped_files.append(str(file_path))
                return False

            lines = content.split('\n')
            depth = self.calculate_depth(file_path)
            sys_path_code = self.generate_sys_path_code(depth)
            insertion_point = self.find_insertion_point(lines)

            # Insert the sys.path code
            new_lines = (
                lines[:insertion_point] +
                sys_path_code.split('\n') +
                lines[insertion_point:]
            )
            new_content = '\n'.join(new_lines)

            if self.dry_run:
                print(f"[DRY-RUN] Would fix: {file_path}")
                print(f"  Depth: {depth}")
                print(f"  Insertion point: line {insertion_point}")
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"[FIXED] {file_path}")

            self.fixed_files.append(str(file_path))
            return True

        except Exception as e:
            error_msg = f"Error processing {file_path}: {e}"
            self.errors.append(error_msg)
            print(f"[ERROR] {error_msg}")
            return False

    def fix_directory(self, directory: Path, pattern: str = "*.py"):
        """Fix all Python files in a directory"""
        if not directory.exists():
            print(f"[SKIP] Directory does not exist: {directory}")
            return

        for file_path in directory.rglob(pattern):
            if file_path.is_file():
                self.fix_file(file_path)

    def print_summary(self):
        """Print summary of changes"""
        print("\n" + "=" * 60)
        print("IMPORT PATH FIX SUMMARY")
        print("=" * 60)
        print(f"Fixed files:   {len(self.fixed_files)}")
        print(f"Skipped files: {len(self.skipped_files)}")
        print(f"Errors:        {len(self.errors)}")

        if self.fixed_files:
            print("\nFixed files:")
            for f in self.fixed_files:
                print(f"  - {f}")

        if self.errors:
            print("\nErrors:")
            for e in self.errors:
                print(f"  - {e}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Fix import paths after folder restructuring"
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help="Show what would be changed without making changes"
    )
    parser.add_argument(
        '--project-root',
        type=Path,
        default=Path(__file__).parent.parent.parent,
        help="Project root directory (default: auto-detected)"
    )

    args = parser.parse_args()

    fixer = ImportPathFixer(args.project_root, args.dry_run)

    print(f"Project root: {args.project_root}")
    print(f"Dry run: {args.dry_run}")
    print("")

    # Fix files in app/
    print("Processing app/ directory...")
    fixer.fix_directory(args.project_root / 'app')

    # Fix files in auth/
    print("\nProcessing auth/ directory...")
    fixer.fix_directory(args.project_root / 'auth')

    # Fix files in tests/ subdirectories
    print("\nProcessing tests/ subdirectories...")
    for subdir in ['unit', 'integration', 'e2e', 'security', 'runners', 'utilities']:
        test_dir = args.project_root / 'tests' / subdir
        if test_dir.exists():
            print(f"  - {subdir}/")
            fixer.fix_directory(test_dir)

    # Fix files in tools/ subdirectories
    print("\nProcessing tools/ subdirectories...")
    for subdir in ['monitoring', 'repair', 'validation', 'linting', 'setup']:
        tool_dir = args.project_root / 'tools' / subdir
        if tool_dir.exists():
            print(f"  - {subdir}/")
            fixer.fix_directory(tool_dir)

    # Print summary
    fixer.print_summary()

    if args.dry_run:
        print("\n" + "=" * 60)
        print("This was a DRY RUN. No files were modified.")
        print("Run without --dry-run to apply changes.")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("Import paths have been fixed!")
        print("Next steps:")
        print("  1. Run tests: pytest tests/ -v")
        print("  2. Validate system: python3 tools/validation/validate_system.py")
        print("=" * 60)


if __name__ == '__main__':
    main()
