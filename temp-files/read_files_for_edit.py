#!/usr/bin/env python3
"""
Edit ツールで編集するための情報を収集
"""
import os

BASE = '/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system'

print("="*80)
print("web_app.py - Lines 1-30 (imports and app creation)")
print("="*80)
with open(f'{BASE}/app/web_app.py', 'r') as f:
    lines = f.readlines()
    for i in range(min(30, len(lines))):
        print(f"{i+1:3d}: {lines[i]}", end='')

print("\n" + "="*80)
print("web_app.py - Search for 'def settings'")
print("="*80)
for i, line in enumerate(lines):
    if 'def settings(' in line or '@app.route' in line and i < len(lines) - 1 and 'def settings' in lines[i+1]:
        for j in range(max(0, i-2), min(len(lines), i+5)):
            marker = ">>>" if j == i else "   "
            print(f"{marker} {j+1:3d}: {lines[j]}", end='')
        break

print("\n" + "="*80)
print("auth.py - Full file")
print("="*80)
auth_path = f'{BASE}/app/routes/auth.py'
if os.path.exists(auth_path):
    with open(auth_path, 'r') as f:
        print(f.read())
else:
    print("[FILE NOT FOUND]")

print("\n" + "="*80)
print("routes/__init__.py")
print("="*80)
init_path = f'{BASE}/app/routes/__init__.py'
if os.path.exists(init_path):
    with open(init_path, 'r') as f:
        print(f.read())
else:
    print("[FILE NOT FOUND - will be created]")

print("\n" + "="*80)
print("base.html - Lines containing </nav>")
print("="*80)
with open(f'{BASE}/templates/base.html', 'r') as f:
    html_lines = f.readlines()
    for i, line in enumerate(html_lines):
        if '</nav>' in line:
            for j in range(max(0, i-10), min(len(html_lines), i+3)):
                marker = ">>>" if j == i else "   "
                print(f"{marker} {j+1:3d}: {line}", end='')
            break

print("\n" + "="*80)
print("Summary: Files exist check")
print("="*80)
files_to_check = [
    f'{BASE}/app/web_app.py',
    f'{BASE}/app/routes/auth.py',
    f'{BASE}/app/routes/__init__.py',
    f'{BASE}/templates/base.html'
]
for fpath in files_to_check:
    exists = "✓" if os.path.exists(fpath) else "✗"
    print(f"{exists} {fpath}")
