#!/usr/bin/env python3
from google_auth_oauthlib.flow import InstalledAppFlow
import json

print("🔐 token.json作成開始...")

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

    # ブラウザで認証 → token.json 自動作成
    creds = flow.run_local_server(port=37259)
    print("✅ トークン取得成功")

    # token.json作成（見やすい整形）
    with open("token.json", "w", encoding="utf-8") as token_file:
        json.dump(json.loads(creds.to_json()), token_file, indent=2, ensure_ascii=False)
    print("✅ token.json作成成功！")

except Exception as e:
    print(f"❌ エラー: {e}")
    import traceback

    traceback.print_exc()
