#!/usr/bin/env python3
"""
データベースパスを data/db.sqlite3 に更新
"""
import os

# config.json更新
config_file = 'config/config.json'
if os.path.exists(config_file):
    import json
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    config['database'] = {'path': 'data/db.sqlite3'}
    
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print('✅ config.json更新: database.path = data/db.sqlite3')

# シンボリックリンク作成（互換性のため）
if not os.path.exists('db.sqlite3') and os.path.exists('data/db.sqlite3'):
    os.symlink('data/db.sqlite3', 'db.sqlite3')
    print('✅ シンボリックリンク作成: db.sqlite3 -> data/db.sqlite3')
elif os.path.exists('db.sqlite3') and not os.path.islink('db.sqlite3'):
    # 既存のdb.sqlite3をdata/に移動
    import shutil
    if not os.path.exists('data/db.sqlite3'):
        shutil.move('db.sqlite3', 'data/db.sqlite3')
        os.symlink('data/db.sqlite3', 'db.sqlite3')
        print('✅ db.sqlite3 を data/ に移動してシンボリックリンク作成')

print('データベースパス設定完了')
