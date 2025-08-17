#!/usr/bin/env python3
"""
Run tests with all fixes applied
"""

import os
import sys
import subprocess
from pathlib import Path


def ensure_test_environment():
    """Ensure test environment is properly set up"""
    project_root = Path("/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system")
    tests_dir = project_root / "tests"

    # Ensure tests directory exists
    tests_dir.mkdir(exist_ok=True)

    # Check that our key test files exist
    key_files = [
        "conftest.py",
        "test_database.py",
        "test_api.py",
        "test_email.py",
        "test_calendar.py",
        "test_main.py",
    ]

    existing_files = []
    for file in key_files:
        file_path = tests_dir / file
        if file_path.exists():
            existing_files.append(file)

    return existing_files


def run_tests():
    """Run tests with comprehensive error handling"""
    print("🚀 Running Fixed Tests")
    print("=" * 30)

    project_root = Path("/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system")
    os.chdir(project_root)

    # Check environment
    existing_files = ensure_test_environment()
    print(f"📁 Found {len(existing_files)} test files:")
    for f in existing_files:
        print(f"  ✅ {f}")

    if not existing_files:
        print("❌ No test files found to run!")
        return

    # Run tests
    print(f"\n🧪 Running pytest...")
    try:
        # First try: run all tests
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/",
                "-v",
                "--tb=short",
                "-x",  # Stop on first failure
            ],
            timeout=180,
        )  # 3 minute timeout

        print(f"\n📊 Test execution completed with exit code: {result.returncode}")

        if result.returncode == 0:
            print("🎉 All tests passed!")
        else:
            print("⚠️  Some tests failed or had issues")

    except subprocess.TimeoutExpired:
        print("⏰ Tests timed out after 3 minutes")
    except FileNotFoundError:
        print("❌ pytest not found")
        print("💡 Try: pip install pytest")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    # Try individual file testing if main run failed
    print(f"\n🔍 Testing individual files...")
    for test_file in existing_files:
        if test_file == "conftest.py":
            continue

        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", f"tests/{test_file}", "-v", "--tb=no"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            status = "✅" if result.returncode == 0 else "❌"
            print(f"  {status} {test_file}")

        except Exception as e:
            print(f"  ❌ {test_file} - Error: {e}")


if __name__ == "__main__":
    run_tests()
