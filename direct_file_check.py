#!/usr/bin/env python3
import os
import glob
from pathlib import Path

base_path = str(Path(__file__).parent.resolve())

print("=== Direct File System Check ===")
print(f"Base path: {base_path}")
print(f"Path exists: {os.path.exists(base_path)}")

# List all files in base directory
print("\n=== Files in base directory ===")
try:
    items = os.listdir(base_path)
    for item in sorted(items):
        item_path = os.path.join(base_path, item)
        if os.path.isdir(item_path):
            print(f"📁 {item}/")
        else:
            print(f"📄 {item}")
except Exception as e:
    print(f"Error listing base directory: {e}")

# Check specifically for tests
tests_path = os.path.join(base_path, "tests")
print("\n=== Tests directory check ===")
print(f"Tests path: {tests_path}")
print(f"Tests exists: {os.path.exists(tests_path)}")

if os.path.exists(tests_path):
    print("Contents of tests/:")
    try:
        for item in sorted(os.listdir(tests_path)):
            item_path = os.path.join(tests_path, item)
            if os.path.isdir(item_path):
                print(f"📁 tests/{item}/")
                # List contents of subdirectory
                try:
                    for subitem in sorted(os.listdir(item_path)):
                        print(f"  📄 {subitem}")
                except:
                    pass
            else:
                print(f"📄 tests/{item}")
    except Exception as e:
        print(f"Error listing tests directory: {e}")

# Look for any Python test files anywhere
print("\n=== Searching for test files ===")
test_patterns = [
    os.path.join(base_path, "**/test_*.py"),
    os.path.join(base_path, "**/*_test.py"),
    os.path.join(base_path, "tests/**/*.py"),
]

all_test_files = []
for pattern in test_patterns:
    try:
        files = glob.glob(pattern, recursive=True)
        all_test_files.extend(files)
    except Exception as e:
        print(f"Error with pattern {pattern}: {e}")

all_test_files = list(set(all_test_files))  # Remove duplicates
print(f"Found {len(all_test_files)} test files:")
for f in sorted(all_test_files):
    print(f"  {f}")

# Check if pytest is installed
print("\n=== Python and pytest check ===")
import sys

print(f"Python version: {sys.version}")

try:
    import pytest

    print(f"Pytest version: {pytest.__version__}")
except ImportError:
    print("Pytest not installed")

# Try to run pytest if we found test files
if all_test_files:
    print("\n=== Attempting to run first test file ===")
    import subprocess

    first_test = all_test_files[0]
    print(f"Testing: {first_test}")

    try:
        os.chdir(base_path)
        result = subprocess.run(
            [sys.executable, "-m", "pytest", first_test, "-v", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        print(f"Return code: {result.returncode}")
        if result.stdout:
            print("STDOUT:")
            print(result.stdout[:1000])  # First 1000 chars
        if result.stderr:
            print("STDERR:")
            print(result.stderr[:1000])  # First 1000 chars

    except Exception as e:
        print(f"Error running test: {e}")

print("\n=== Check complete ===")
