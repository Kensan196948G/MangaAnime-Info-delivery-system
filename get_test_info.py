#!/usr/bin/env python3
import os
import sys

# Add the project to Python path
sys.path.insert(0, "/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system")

print("=== Test File Analysis ===")

# Check tests directory
tests_dir = "/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/tests"
print(f"Tests directory: {tests_dir}")
print(f"Exists: {os.path.exists(tests_dir)}")

if os.path.exists(tests_dir):
    files = os.listdir(tests_dir)
    print(f"Files: {files}")

    # Read each test file
    for filename in files:
        if filename.endswith(".py"):
            filepath = os.path.join(tests_dir, filename)
            print(f"\n--- {filename} ---")
            try:
                with open(filepath, "r") as f:
                    content = f.read()
                print(f"Size: {len(content)} characters")
                print("Content preview:")
                print(content[:500])
                if len(content) > 500:
                    print("...")
            except Exception as e:
                print(f"Error reading {filename}: {e}")

# Try to run pytest directly
print("\n=== Running pytest directly ===")
try:
    os.chdir("/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system")

    import subprocess

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=no"],
        capture_output=True,
        text=True,
        timeout=30,
    )

    print("Return code:", result.returncode)
    print("STDOUT:")
    print(result.stdout)
    print("STDERR:")
    print(result.stderr)

    # Extract failed tests
    lines = result.stdout.split("\n")
    failed = [line for line in lines if "FAILED" in line]
    print(f"\nFailed tests ({len(failed)}):")
    for f in failed:
        print(f"  {f}")

except Exception as e:
    print(f"Error running pytest: {e}")

print("\n=== Analysis complete ===")

# Let's also just check what Python modules are available
print("\n=== Module availability ===")
modules_to_check = ["pytest", "unittest", "sqlite3", "requests", "flask"]
for module in modules_to_check:
    try:
        __import__(module)
        print(f"✅ {module}")
    except ImportError:
        print(f"❌ {module}")

# Check the main modules directory
modules_dir = "/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/modules"
if os.path.exists(modules_dir):
    print("\n=== modules/ directory ===")
    for item in os.listdir(modules_dir):
        if item.endswith(".py"):
            print(f"  📄 {item}")
else:
    print("\n❌ modules/ directory not found")
