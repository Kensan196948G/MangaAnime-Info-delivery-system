from google_auth_oauthlib.flow import InstalledAppFlow
import json

# 取得した認証コード
AUTH_CODE = "4/0AVMBsJiawd1QdBJFJvsOS8FzDTcA6orSztPGgHKAfg5P6O3QI43fnJGiru3i6whqIreCPQ"

flow = InstalledAppFlow.from_client_secrets_file(
    "credentials.json",
    [
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/calendar.events",
    ],
)
flow.redirect_uri = "http://localhost:8080/"
flow.fetch_token(code=AUTH_CODE)

# token.json作成
with open("token.json", "w", encoding="utf-8") as f:
    json.dump(json.loads(flow.credentials.to_json()), f, indent=2, ensure_ascii=False)

print("✅ token.json作成完了！")
