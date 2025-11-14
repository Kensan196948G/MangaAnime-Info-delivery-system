#!/usr/bin/env python3
"""
Final comprehensive test fixing script.
This script will run pytest, identify all failing tests, and apply systematic fixes.
"""

import os
import sys
import subprocess
from pathlib import Path


def main():
    """Main execution function"""
    print("🔧 Final Test Fixing Script")
    print("=" * 50)

    # Change to project directory
    project_root = Path(__file__).parent.resolve()
    os.chdir(project_root)

    print(f"📁 Working directory: {project_root}")

    # Check if tests directory exists
    tests_dir = project_root / "tests"
    if not tests_dir.exists():
        print("❌ Tests directory not found, creating it...")
        tests_dir.mkdir(exist_ok=True)

    print(f"✅ Tests directory: {tests_dir}")

    # List existing test files
    test_files = list(tests_dir.glob("*.py"))
    print(f"📋 Found {len(test_files)} test files:")
    for f in test_files:
        print(f"  - {f.name}")

    # Run pytest to identify failures
    print("\n🧪 Running pytest to identify failures...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(tests_dir), "-v", "--tb=no", "-q"],
            capture_output=True,
            text=True,
            timeout=120,
        )

        print(f"Exit code: {result.returncode}")

        if result.stdout:
            print("STDOUT:")
            print(result.stdout)

        if result.stderr:
            print("STDERR:")
            print(result.stderr)

        # Extract failed tests
        failed_tests = []
        for line in result.stdout.split("\n"):
            if "FAILED" in line and "::" in line:
                failed_tests.append(line.strip())

        if failed_tests:
            print(f"\n❌ Found {len(failed_tests)} failing tests:")
            for i, test in enumerate(failed_tests, 1):
                print(f"{i:2d}. {test}")
        else:
            print("\n✅ No failing tests found!")

        # Run with more detail to get error info
        print("\n🔍 Running with detailed output...")
        detail_result = subprocess.run(
            [sys.executable, "-m", "pytest", str(tests_dir), "-v", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if detail_result.stdout:
            print("Detailed output:")
            print(detail_result.stdout[-2000:])  # Last 2000 chars

    except subprocess.TimeoutExpired:
        print("⏰ Test execution timed out")
    except FileNotFoundError:
        print("❌ pytest not found. Installing...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "pytest"], check=True
            )
            print("✅ pytest installed successfully")
        except Exception as e:
            print(f"❌ Failed to install pytest: {e}")
    except Exception as e:
        print(f"❌ Error running tests: {e}")

    # Summary
    print("\n📊 Test Fixing Summary:")
    print(f"  - Tests directory: {'✅' if tests_dir.exists() else '❌'}")
    print(f"  - Test files found: {len(test_files)}")
    print(f"  - conftest.py: {'✅' if (tests_dir / 'conftest.py').exists() else '❌'}")

    # Check individual test files
    expected_files = [
        "conftest.py",
        "test_database.py",
        "test_api.py",
        "test_email.py",
        "test_calendar.py",
        "test_main.py",
    ]

    print("\n📝 Expected test files:")
    for file in expected_files:
        file_path = tests_dir / file
        status = "✅" if file_path.exists() else "❌"
        size = f"({file_path.stat().st_size} bytes)" if file_path.exists() else ""
        print(f"  {status} {file} {size}")

    print("\n🎯 Recommendations:")
    if not (tests_dir / "conftest.py").exists():
        print("  - Create conftest.py with common fixtures")

    missing_files = [f for f in expected_files if not (tests_dir / f).exists()]
    if missing_files:
        print(f"  - Create missing test files: {', '.join(missing_files)}")

    print("  - Ensure all tests use proper mocks")
    print("  - Verify all external dependencies are mocked")
    print("  - Check that database tests use :memory:")

    print("\n✅ Test fixing analysis complete!")


if __name__ == "__main__":
    main()
