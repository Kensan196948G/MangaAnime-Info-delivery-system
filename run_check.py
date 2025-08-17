#!/usr/bin/env python3
import os
import sys
import subprocess

# Change to project directory
os.chdir('/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system')

# Just run a simple pytest command to see all test results
print("=== Running pytest with maximum detail ===")
try:
    result = subprocess.run([
        sys.executable, "-m", "pytest", "tests/", 
        "-v", "--tb=long", "--no-header"
    ], capture_output=True, text=True)
    
    print("FULL OUTPUT:")
    print("=" * 80)
    print(result.stdout)
    if result.stderr:
        print("\nERRORS:")
        print("=" * 80)
        print(result.stderr)
    
    print(f"\nExit code: {result.returncode}")
    
    # Parse for failed tests
    failed_tests = []
    for line in result.stdout.split('\n'):
        if 'FAILED' in line and '::' in line:
            failed_tests.append(line.strip())
    
    if failed_tests:
        print(f"\n=== {len(failed_tests)} FAILED TESTS ===")
        for test in failed_tests:
            print(f"❌ {test}")
    else:
        print("\n✅ No failed tests found or no tests detected")
        
except Exception as e:
    print(f"Error: {e}")
    
    # Fallback: just list what's in tests/
    print("\n=== Fallback: Listing tests directory ===")
    try:
        if os.path.exists('tests'):
            for item in os.listdir('tests'):
                print(f"  {item}")
        else:
            print("tests/ directory not found")
    except Exception as e2:
        print(f"Fallback error: {e2}")