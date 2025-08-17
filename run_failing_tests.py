#!/usr/bin/env python3
import subprocess
import sys


def run_failing_tests():
    """Run pytest to identify failing tests"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "--tb=no", "-q"],
            capture_output=True,
            text=True,
            cwd="/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system",
        )

        print("STDOUT:")
        print(result.stdout)
        print("\nSTDERR:")
        print(result.stderr)
        print(f"\nReturn code: {result.returncode}")

        # Extract failed tests
        failed_lines = [line for line in result.stdout.split("\n") if "FAILED" in line]
        if failed_lines:
            print("\n=== FAILED TESTS ===")
            for line in failed_lines:
                print(line)

    except Exception as e:
        print(f"Error running tests: {e}")


if __name__ == "__main__":
    run_failing_tests()
