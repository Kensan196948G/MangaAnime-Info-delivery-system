#!/usr/bin/env python3
"""現在の状態を確認"""
import os
import re

BASE = '/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system'

def check_file(path, label):
    print(f"\n{'='*80}")
    print(f"{label}: {path}")
    print('='*80)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"Length: {len(content)} chars, {len(content.splitlines())} lines")

        # 最初の50行を表示
        lines = content.splitlines()
        print("\n--- First 50 lines ---")
        for i, line in enumerate(lines[:50], 1):
            print(f"{i:4d}: {line}")

        return content
    else:
        print("FILE NOT FOUND")
        return None

# 各ファイルをチェック
web_app = check_file(f'{BASE}/app/web_app.py', 'web_app.py')
auth = check_file(f'{BASE}/app/routes/auth.py', 'auth.py')
routes_init = check_file(f'{BASE}/app/routes/__init__.py', 'routes/__init__.py')

# web_app.py のルート一覧を抽出
if web_app:
    print(f"\n{'='*80}")
    print("Routes in web_app.py")
    print('='*80)
    pattern = r"@app\.route\('([^']+)'(?:, methods=(\[[^\]]+\]))?\)\s*\ndef (\w+)\("
    routes = re.findall(pattern, web_app)
    for i, (path, methods, func) in enumerate(routes, 1):
        methods_str = methods if methods else "['GET']"
        print(f"{i:3d}. {func:30s} {path:40s} {methods_str}")
