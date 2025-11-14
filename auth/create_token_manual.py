#!/usr/bin/env python3
import json
from google_auth_oauthlib.flow import InstalledAppFlow

print("🔐 手動認証でtoken.json作成開始...")

try:
    # 認証情報読み込み
    with open("credentials.json", "r", encoding="utf-8") as f:
        client_config = json.load(f)
    print("✅ credentials.json読み込み成功")

    # フローの作成
    flow = InstalledAppFlow.from_client_config(
        client_config,
        [
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/calendar.events",
        ],
    )
    print("✅ OAuth2フロー作成成功")

    # 認証URLを生成
    auth_url, _ = flow.authorization_url(prompt="consent")
    print("\n📋 以下のURLをブラウザで開いて認証してください:")
    print(f"{auth_url}\n")

    # 認証コードの入力を求める
    auth_code = input("認証コードを入力してください: ").strip()

    # トークンを取得
    flow.fetch_token(code=auth_code)
    creds = flow.credentials
    print("✅ トークン取得成功")

    # token.json作成（見やすい整形）
    with open("token.json", "w", encoding="utf-8") as token_file:
        json.dump(json.loads(creds.to_json()), token_file, indent=2, ensure_ascii=False)
    print("✅ token.json作成成功！")

    print("\n🎉 認証が完了しました！")

except Exception as e:
    print(f"❌ エラー: {e}")
    import traceback

    traceback.print_exc()
