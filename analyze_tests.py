#!/usr/bin/env python3
import os
import sys


def find_test_files():
    """Find all test files in the project"""
    test_files = []

    for root, dirs, files in os.walk(
        "/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system"
    ):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                test_files.append(os.path.join(root, file))

    return test_files


def main():
    print("=== Finding test files ===")
    test_files = find_test_files()

    if not test_files:
        print("No test files found!")
        return

    print(f"Found {len(test_files)} test files:")
    for file in test_files:
        print(f"  - {file}")

    # Try to run pytest on each file individually
    print("\n=== Testing each file individually ===")
    import subprocess

    os.chdir("/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system")

    for test_file in test_files:
        rel_path = os.path.relpath(test_file)
        print(f"\n--- Testing {rel_path} ---")

        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", rel_path, "-v"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                print(f"✅ {rel_path} - PASSED")
            else:
                print(f"❌ {rel_path} - FAILED")
                print("Error output:")
                print(result.stdout[-500:] if result.stdout else "No stdout")
                print(result.stderr[-500:] if result.stderr else "No stderr")

        except subprocess.TimeoutExpired:
            print(f"⏰ {rel_path} - TIMEOUT")
        except Exception as e:
            print(f"💥 {rel_path} - ERROR: {e}")


if __name__ == "__main__":
    main()
