#!/usr/bin/env python3
with open('/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system/app/web_app.py', 'r') as f:
    lines = f.readlines()
    for i in range(min(60, len(lines))):
        print(f"{i+1:4d}: {lines[i]}", end='')
