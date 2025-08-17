#!/usr/bin/env python3
import os
import subprocess
import sys

# Go to the project directory
os.chdir('/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system')

print("Current directory:", os.getcwd())
print("Contents of current directory:")
for item in os.listdir('.'):
    print(f"  {item}")

print("\nChecking for tests directory...")
if os.path.exists('tests'):
    print("tests/ directory exists")
    print("Contents of tests/:")
    for item in os.listdir('tests'):
        print(f"  {item}")
else:
    print("tests/ directory does not exist")

print("\nTrying to run pytest...")
try:
    # Run pytest with basic options
    result = subprocess.run([
        sys.executable, "-m", "pytest", "--version"
    ], capture_output=True, text=True)
    print(f"Pytest version check: {result.returncode}")
    print(f"Output: {result.stdout.strip()}")
    
    # Now try to run tests
    result = subprocess.run([
        sys.executable, "-m", "pytest", "tests/", "-v"
    ], capture_output=True, text=True, timeout=30)
    
    print(f"\nTest run result code: {result.returncode}")
    print("STDOUT:")
    print(result.stdout)
    print("STDERR:")
    print(result.stderr)
    
except subprocess.TimeoutExpired:
    print("Test run timed out")
except Exception as e:
    print(f"Error: {e}")

print("\nDone.")