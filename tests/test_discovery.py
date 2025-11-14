#!/usr/bin/env python3
"""
Test discovery and failure analysis script
"""
import os
import sys
import subprocess
from pathlib import Path


def main():
    # Change to project directory
    project_root = Path(__file__).parent.resolve()
    os.chdir(project_root)

    print(f"Working directory: {os.getcwd()}")

    # Step 1: Check if tests directory exists
    tests_dir = project_root / "tests"
    if not tests_dir.exists():
        print("❌ No tests directory found")
        return

    print(f"✅ Tests directory found: {tests_dir}")

    # Step 2: List all test files
    test_files = list(tests_dir.rglob("test_*.py")) + list(tests_dir.rglob("*_test.py"))
    print(f"\n📁 Found {len(test_files)} test files:")
    for f in test_files:
        print(f"  - {f.relative_to(project_root)}")

    if not test_files:
        print("❌ No test files found")
        return

    # Step 3: Run pytest to collect test failures
    print("\n🧪 Running pytest to identify failures...")

    try:
        # First, just try to collect tests
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(tests_dir), "--collect-only", "-q"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        print(f"Test collection result: {result.returncode}")
        if result.returncode != 0:
            print("Collection errors:")
            print(result.stdout)
            print(result.stderr)

        # Now run the actual tests
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(tests_dir), "-v", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        print(f"\nTest execution result: {result.returncode}")
        print("STDOUT:")
        print(result.stdout)

        if result.stderr:
            print("\nSTDERR:")
            print(result.stderr)

        # Extract failed tests
        failed_tests = []
        for line in result.stdout.split("\n"):
            if "FAILED" in line and "::" in line:
                failed_tests.append(line.strip())

        if failed_tests:
            print(f"\n❌ Found {len(failed_tests)} failed tests:")
            for i, test in enumerate(failed_tests, 1):
                print(f"{i}. {test}")
        else:
            print("\n✅ No failed tests found (or tests didn't run)")

    except subprocess.TimeoutExpired:
        print("⏰ Test execution timed out")
    except Exception as e:
        print(f"💥 Error running tests: {e}")


if __name__ == "__main__":
    main()
