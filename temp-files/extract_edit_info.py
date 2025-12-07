#!/usr/bin/env python3
"""
Edit ツールで使用する old_string を抽出
"""
import os

BASE = '/mnt/Linux-ExHDD/MangaAnime-Info-delivery-system'

print("="*80)
print("EXTRACTION FOR EDIT TOOL")
print("="*80)

# 1. web_app.py のインポートセクション
print("\n[1] web_app.py - Import Section for Edit")
print("-"*80)
with open(f'{BASE}/app/web_app.py', 'r') as f:
    lines = f.readlines()
    # 最初の from flask import から logger までを抽出
    import_section = []
    in_import_section = False
    for line in lines:
        if 'from flask import' in line:
            in_import_section = True
        if in_import_section:
            import_section.append(line)
        if 'logger = logging.getLogger(__name__)' in line:
            break

    print("OLD_STRING (imports):")
    print("```")
    print(''.join(import_section))
    print("```")

# 2. app = Flask(__name__) の周辺
print("\n[2] web_app.py - App Creation Section")
print("-"*80)
for i, line in enumerate(lines):
    if 'app = Flask(__name__)' in line:
        # この行だけを抽出
        print("OLD_STRING (app creation - SINGLE LINE):")
        print("```")
        print(line, end='')
        print("```")
        break

# 3. settings ルートの定義
print("\n[3] web_app.py - Settings Route")
print("-"*80)
for i, line in enumerate(lines):
    if "@app.route('/settings')" in line:
        # @app.route から def settings まで
        route_section = []
        route_section.append(line)
        route_section.append(lines[i+1])  # def settings():
        print("OLD_STRING (settings route):")
        print("```")
        print(''.join(route_section), end='')
        print("```")
        break

# 4. その他の保護が必要なルート
print("\n[4] web_app.py - Other Protected Routes")
print("-"*80)
protected = [
    ("/api/settings/update", "update_settings"),
    ("/api/clear-history", "clear_history"),
    ("/api/delete-work", "delete_work")
]
for path, func_name in protected:
    for i, line in enumerate(lines):
        if f"@app.route('{path}" in line:
            print(f"\n{func_name}:")
            print("OLD_STRING:")
            print("```")
            print(line, end='')
            print(lines[i+1], end='')
            print("```")
            break

# 5. routes/__init__.py の存在確認
print("\n[5] routes/__init__.py")
print("-"*80)
init_path = f'{BASE}/app/routes/__init__.py'
if os.path.exists(init_path):
    print("EXISTS - Content:")
    with open(init_path, 'r') as f:
        print(f.read())
else:
    print("DOES NOT EXIST - Will create new file")

# 6. base.html の </nav>
print("\n[6] templates/base.html - Navigation End")
print("-"*80)
with open(f'{BASE}/templates/base.html', 'r') as f:
    html = f.read()
    # </nav> を含む前後10行を表示
    lines = html.split('\n')
    for i, line in enumerate(lines):
        if '</nav>' in line:
            start = max(0, i - 5)
            end = min(len(lines), i + 2)
            print("OLD_STRING (nav section):")
            print("```")
            for j in range(start, end):
                print(lines[j])
            print("```")
            break

print("\n" + "="*80)
print("END OF EXTRACTION")
print("="*80)
