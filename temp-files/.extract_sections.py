#!/usr/bin/env python3
"""
主要セクションを抽出して表示
"""
import os

BASE = '/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system'

# 1. web_app.py のインポート部とアプリ初期化部
with open(f'{BASE}/app/web_app.py', 'r') as f:
    lines = f.readlines()

print("=== web_app.py: Import Section (Lines 1-30) ===")
for i, line in enumerate(lines[:30], 1):
    print(f"{i:3d}: {line}", end='')

print("\n=== web_app.py: App Creation and Config (around line 27-40) ===")
for i, line in enumerate(lines[25:45], 26):
    print(f"{i:3d}: {line}", end='')

# アプリの最後の部分（Blueprint登録があるか確認）
print("\n=== web_app.py: Bottom Section (Last 30 lines) ===")
for i, line in enumerate(lines[-30:], len(lines)-29):
    print(f"{i:3d}: {line}", end='')

# 2. auth.py の全体
print("\n\n" + "="*80)
print("=== app/routes/auth.py (Full Content) ===")
print("="*80)
try:
    with open(f'{BASE}/app/routes/auth.py', 'r') as f:
        print(f.read())
except FileNotFoundError:
    print("[FILE NOT FOUND]")

# 3. routes/__init__.py
print("\n" + "="*80)
print("=== app/routes/__init__.py ===")
print("="*80)
try:
    with open(f'{BASE}/app/routes/__init__.py', 'r') as f:
        print(f.read())
except FileNotFoundError:
    print("[FILE NOT FOUND or EMPTY]")

# 4. base.html のナビゲーション
print("\n" + "="*80)
print("=== templates/base.html: Navigation Section ===")
print("="*80)
with open(f'{BASE}/templates/base.html', 'r') as f:
    content = f.read()
    # nav タグを探す
    nav_start = content.find('<nav')
    if nav_start != -1:
        nav_end = content.find('</nav>', nav_start) + 6
        nav_section = content[nav_start:nav_end]
        for i, line in enumerate(nav_section.split('\n'), 1):
            print(f"{i:3d}: {line}")
    else:
        print("[Navigation not found, showing lines 40-100]")
        lines = content.split('\n')
        for i, line in enumerate(lines[39:100], 40):
            print(f"{i:3d}: {line}")
