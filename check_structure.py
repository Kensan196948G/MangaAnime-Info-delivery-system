#!/usr/bin/env python3
import os

def check_project_structure():
    """Check the project structure and find test files"""
    base_path = '/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system'
    
    print("=== Project Structure ===")
    
    # Check if tests directory exists
    tests_dir = os.path.join(base_path, 'tests')
    if os.path.exists(tests_dir):
        print(f"✅ Tests directory exists: {tests_dir}")
        
        # List all files in tests directory
        test_files = []
        for item in os.listdir(tests_dir):
            item_path = os.path.join(tests_dir, item)
            if os.path.isfile(item_path):
                test_files.append(item)
                print(f"  📄 {item}")
            elif os.path.isdir(item_path):
                print(f"  📁 {item}/")
                # List files in subdirectory
                for subitem in os.listdir(item_path):
                    print(f"    📄 {subitem}")
        
        return test_files
    else:
        print(f"❌ Tests directory not found: {tests_dir}")
        return []

def check_main_modules():
    """Check if main modules exist"""
    base_path = '/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system'
    
    print("\n=== Main Modules ===")
    
    important_files = [
        'main.py',
        'release_notifier.py',
        'app.py',
        'config.json'
    ]
    
    for file in important_files:
        file_path = os.path.join(base_path, file)
        if os.path.exists(file_path):
            print(f"✅ {file}")
        else:
            print(f"❌ {file}")
    
    # Check modules directory
    modules_dir = os.path.join(base_path, 'modules')
    if os.path.exists(modules_dir):
        print(f"✅ modules/ directory exists")
        for item in os.listdir(modules_dir):
            if item.endswith('.py'):
                print(f"  📄 modules/{item}")
    else:
        print(f"❌ modules/ directory not found")

if __name__ == "__main__":
    test_files = check_project_structure()
    check_main_modules()
    
    if test_files:
        print(f"\n=== Found {len(test_files)} test files ===")
        for file in test_files:
            print(f"  - {file}")
    else:
        print("\n❌ No test files found to fix!")