#!/usr/bin/env python3
"""ファイル構造分析スクリプト"""
import os
import re

# ファイルパス
BASE_DIR = '/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system'
WEB_APP_PATH = os.path.join(BASE_DIR, 'app/web_app.py')
AUTH_PATH = os.path.join(BASE_DIR, 'app/routes/auth.py')
ROUTES_INIT_PATH = os.path.join(BASE_DIR, 'app/routes/__init__.py')
BASE_TEMPLATE_PATH = os.path.join(BASE_DIR, 'templates/base.html')

def read_file_safe(path, max_lines=None):
    """ファイルを安全に読み取り"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            if max_lines:
                return ''.join([f.readline() for _ in range(max_lines)])
            return f.read()
    except FileNotFoundError:
        return f"[FILE NOT FOUND: {path}]"
    except Exception as e:
        return f"[ERROR reading {path}: {e}]"

print("=" * 80)
print("1. app/web_app.py - 最初の50行")
print("=" * 80)
print(read_file_safe(WEB_APP_PATH, 50))

print("\n" + "=" * 80)
print("2. app/routes/auth.py - 全体")
print("=" * 80)
print(read_file_safe(AUTH_PATH))

print("\n" + "=" * 80)
print("3. app/routes/__init__.py")
print("=" * 80)
print(read_file_safe(ROUTES_INIT_PATH))

print("\n" + "=" * 80)
print("4. templates/base.html - ナビゲーション部分（60-90行目想定）")
print("=" * 80)
base_html = read_file_safe(BASE_TEMPLATE_PATH)
lines = base_html.split('\n')
for i, line in enumerate(lines[55:95], start=56):
    print(f"{i:3d}: {line}")

print("\n" + "=" * 80)
print("5. web_app.py のルート一覧")
print("=" * 80)
web_app_content = read_file_safe(WEB_APP_PATH)
route_pattern = r'@app\.route\([\'"]([^\'"]+).*?\)\s*(?:.*?\n)?def\s+(\w+)\('
routes = re.findall(route_pattern, web_app_content, re.DOTALL)
for i, (path, func) in enumerate(routes, 1):
    print(f"{i:2d}. {func:30s} -> {path}")
