#!/usr/bin/env python3
import os

# List everything in tests/ directory
tests_path = "/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/tests"

print("=== Checking tests directory ===")
if os.path.exists(tests_path):
    print(f"✅ {tests_path} exists")

    for item in os.listdir(tests_path):
        item_path = os.path.join(tests_path, item)
        if os.path.isfile(item_path):
            print(f"📄 {item} ({os.path.getsize(item_path)} bytes)")

            # If it's a Python file, show first few lines
            if item.endswith(".py"):
                try:
                    with open(item_path, "r") as f:
                        lines = f.readlines()[:10]
                    print("   First lines:")
                    for i, line in enumerate(lines, 1):
                        print(f"   {i:2d}: {line.rstrip()}")
                    if len(lines) == 10:
                        print("   ...")
                    print()
                except Exception as e:
                    print(f"   Error reading: {e}")
        else:
            print(f"📁 {item}/")
else:
    print(f"❌ {tests_path} does not exist")

# Also check if there are any test files in the root
root_path = "/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system"
print(f"\n=== Checking for test files in root: {root_path} ===")
for item in os.listdir(root_path):
    if item.startswith("test_") and item.endswith(".py"):
        print(f"📄 {item} (in root)")
