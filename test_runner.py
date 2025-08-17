#!/usr/bin/env python3
import subprocess
import sys
import os

# Change to project directory
os.chdir('/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system')

print("=== Running pytest to identify failing tests ===")

# Run pytest with more verbose output
try:
    result = subprocess.run([
        sys.executable, "-m", "pytest", "tests/", 
        "-v", "--tb=short"
    ], capture_output=True, text=True)
    
    print("STDOUT:")
    print(result.stdout)
    if result.stderr:
        print("\nSTDERR:")
        print(result.stderr)
    
    print(f"\nReturn code: {result.returncode}")
    
    # Extract failed test info
    lines = result.stdout.split('\n')
    failed_tests = []
    for line in lines:
        if 'FAILED' in line:
            failed_tests.append(line.strip())
    
    if failed_tests:
        print("\n=== FAILED TESTS SUMMARY ===")
        for test in failed_tests:
            print(test)
    else:
        print("\n=== NO FAILED TESTS FOUND ===")
        
except Exception as e:
    print(f"Error: {e}")