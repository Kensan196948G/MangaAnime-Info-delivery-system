#!/usr/bin/env python3
"""
Simple test verification script to check current test status
"""

import os
import sys
import subprocess
from pathlib import Path


def check_test_status():
    """Check the current status of tests"""
    print("🔍 Test Status Verification")
    print("=" * 40)

    # Change to project directory
    project_root = Path("/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system")
    os.chdir(project_root)

    print(f"📁 Project: {project_root}")

    # Check tests directory
    tests_dir = project_root / "tests"
    print(f"📂 Tests dir exists: {tests_dir.exists()}")

    if tests_dir.exists():
        test_files = list(tests_dir.glob("*.py"))
        print(f"📋 Test files ({len(test_files)}):")
        for f in test_files:
            size = f.stat().st_size
            print(f"  - {f.name} ({size} bytes)")

    # Try running a simple pytest command
    print(f"\n🧪 Testing pytest availability...")
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import pytest; print(f'pytest {pytest.__version__}')",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            print(f"✅ {result.stdout.strip()}")
        else:
            print(f"❌ pytest import failed")
    except Exception as e:
        print(f"❌ pytest check error: {e}")

    # Try running tests if they exist
    if tests_dir.exists() and any(tests_dir.glob("*.py")):
        print(f"\n🏃 Quick test run...")
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    str(tests_dir),
                    "--collect-only",
                    "-q",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            print(f"Collection result: {result.returncode}")
            if result.stdout:
                lines = result.stdout.strip().split("\n")
                for line in lines[-5:]:  # Last 5 lines
                    print(f"  {line}")

        except Exception as e:
            print(f"❌ Test collection error: {e}")

    print(f"\n📊 Summary:")
    print(f"  - Tests directory: {'✅ exists' if tests_dir.exists() else '❌ missing'}")
    print(
        f"  - Test files: {len(list(tests_dir.glob('*.py'))) if tests_dir.exists() else 0}"
    )
    print(
        f"  - Ready to run: {'✅' if tests_dir.exists() and any(tests_dir.glob('*.py')) else '❌'}"
    )


if __name__ == "__main__":
    check_test_status()
