#!/usr/bin/env python3
import subprocess
import sys
import os

# Change to the project directory
project_dir = "/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system"
os.chdir(project_dir)

print(f"Current directory: {os.getcwd()}")
print("=== Checking if pytest is available ===")

try:
    # Check if pytest is installed
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--version"], capture_output=True, text=True
    )
    print(f"Pytest version check: {result.returncode}")
    if result.stdout:
        print(f"Stdout: {result.stdout.strip()}")
    if result.stderr:
        print(f"Stderr: {result.stderr.strip()}")
except Exception as e:
    print(f"Error checking pytest: {e}")

print("\n=== Checking for test files ===")
if os.path.exists("tests"):
    print("tests/ directory exists")
    try:
        files = os.listdir("tests")
        print(f"Files in tests/: {files}")
    except Exception as e:
        print(f"Error listing tests/: {e}")
else:
    print("tests/ directory does not exist")

print("\n=== Running simple pytest command ===")
try:
    # Try running pytest with minimal options
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-v"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    print(f"Return code: {result.returncode}")
    print("Stdout:")
    print(result.stdout)
    if result.stderr:
        print("Stderr:")
        print(result.stderr)
except subprocess.TimeoutExpired:
    print("Pytest command timed out")
except Exception as e:
    print(f"Error running pytest: {e}")
