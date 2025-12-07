#!/usr/bin/env python3
"""現在のファイル状態を表示"""

# web_app.py の最初の50行
print("="*80)
print("app/web_app.py - Lines 1-50")
print("="*80)
with open('/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/app/web_app.py', 'r') as f:
    for i, line in enumerate(f, 1):
        if i <= 50:
            print(f"{i:4d}: {line}", end='')
        else:
            break

# app = Flask(__name__) の周辺を探す
print("\n" + "="*80)
print("app/web_app.py - Around 'app = Flask(__name__)'")
print("="*80)
with open('/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/app/web_app.py', 'r') as f:
    lines = f.readlines()
    for i, line in enumerate(lines):
        if 'app = Flask(__name__)' in line:
            start = max(0, i - 3)
            end = min(len(lines), i + 15)
            for j in range(start, end):
                marker = ">>>" if j == i else "   "
                print(f"{marker} {j+1:4d}: {lines[j]}", end='')
            break

print("\n" + "="*80)
print("END OF FILE PREVIEW")
print("="*80)
