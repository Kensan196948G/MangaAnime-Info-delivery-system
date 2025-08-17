#!/usr/bin/env python3
import os

def read_file_safely(filepath):
    """Read a file safely and return its content"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading {filepath}: {e}"

def main():
    base_path = '/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system'
    tests_dir = os.path.join(base_path, 'tests')
    
    print("=== Examining test file contents ===")
    
    if not os.path.exists(tests_dir):
        print(f"❌ Tests directory doesn't exist: {tests_dir}")
        return
    
    # Get all Python files in tests directory
    test_files = []
    for root, dirs, files in os.walk(tests_dir):
        for file in files:
            if file.endswith('.py'):
                test_files.append(os.path.join(root, file))
    
    print(f"Found {len(test_files)} Python files in tests/")
    
    for test_file in test_files:
        print(f"\n{'='*60}")
        print(f"FILE: {test_file}")
        print('='*60)
        
        content = read_file_safely(test_file)
        print(content[:2000])  # First 2000 characters
        if len(content) > 2000:
            print("\n... [truncated] ...")
    
    # Also check for conftest.py or other important test config files
    conftest_path = os.path.join(tests_dir, 'conftest.py')
    if os.path.exists(conftest_path):
        print(f"\n{'='*60}")
        print(f"CONFTEST: {conftest_path}")
        print('='*60)
        print(read_file_safely(conftest_path))

if __name__ == "__main__":
    main()