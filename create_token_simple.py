#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
簡単なGoogle OAuth2 認証URLジェネレーター
認証URLを表示し、ユーザーがブラウザで認証後にコードを取得する方式
"""

import json
import os
from google_auth_oauthlib.flow import InstalledAppFlow

# 設定
CREDENTIALS_FILE = "credentials.json"
TOKEN_FILE = "token.json"
SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar.events",
]

def main():
    print("🔐 Google OAuth2 認証URL生成")
    
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"❌ {CREDENTIALS_FILE} が見つかりません。")
        return 1
    
    try:
        # フローの作成
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        
        # 認証URLを生成（リダイレクトURIは適当に設定）
        flow.redirect_uri = 'http://localhost:8080/'
        auth_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        
        print("\n📋 以下のURLをブラウザで開いてください:")
        print(f"{auth_url}")
        print("\n✅ 許可すると、ブラウザに認証コードが表示されます。")
        print("⚠️ エラーページが表示されても、URLに含まれる 'code=' パラメーターの値をコピーしてください。")
        print("\n🔑 取得したコードで以下のPythonコードを実行してください:")
        print("```python")
        print("from google_auth_oauthlib.flow import InstalledAppFlow")
        print("import json")
        print("")
        print("# コードをここに貼り付け")
        print('AUTH_CODE = "ここに認証コードを貼り付け"')
        print("")
        print('flow = InstalledAppFlow.from_client_secrets_file("credentials.json", [')
        print('    "https://www.googleapis.com/auth/gmail.send",')
        print('    "https://www.googleapis.com/auth/calendar.events"')
        print('])')
        print('flow.redirect_uri = "http://localhost:8080/"')
        print('flow.fetch_token(code=AUTH_CODE)')
        print('')
        print('# token.json作成')
        print('with open("token.json", "w", encoding="utf-8") as f:')
        print('    json.dump(json.loads(flow.credentials.to_json()), f, indent=2, ensure_ascii=False)')
        print('')
        print('print("✅ token.json作成完了！")')
        print("```")
        
        return 0
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return 1

if __name__ == "__main__":
    exit(main())