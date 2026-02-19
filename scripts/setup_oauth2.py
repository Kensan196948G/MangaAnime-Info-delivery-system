#!/usr/bin/env python3
"""
Phase 1: Google OAuth2認証セットアップスクリプト

このスクリプトは以下を実行します:
1. SMTP メール送信の動作確認（即時テスト）
2. credentials.json の存在確認
3. Gmail API と Calendar API の OAuth2 認証フロー実行
4. token.json の生成・検証

使用方法:
    # ステップ1: SMTP確認（credentials.json不要）
    python scripts/setup_oauth2.py --smtp-only

    # ステップ2: OAuth2セットアップ（credentials.json必要）
    python scripts/setup_oauth2.py --oauth2

    # すべて実行
    python scripts/setup_oauth2.py --all

    # 状態確認のみ
    python scripts/setup_oauth2.py --status
"""

import argparse
import io
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Windows環境でUTF-8出力を強制
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ファイルパス定義
CREDENTIALS_FILE = project_root / "credentials.json"
GMAIL_TOKEN_FILE = project_root / "auth" / "gmail_token.json"
CALENDAR_TOKEN_FILE = project_root / "auth" / "calendar_token.json"
LEGACY_TOKEN_FILE = project_root / "token.json"  # 旧パス

# OAuth2スコープ
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
]
CALENDAR_SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
]
COMBINED_SCOPES = GMAIL_SCOPES + CALENDAR_SCOPES


def print_section(title: str):
    """セクションヘッダー出力"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_step(step: str, status: str = "", detail: str = ""):
    """ステップ出力"""
    icons = {"ok": "✅", "ng": "❌", "warn": "⚠️ ", "info": "ℹ️ ", "run": "🔄"}
    icon = icons.get(status, "  ")
    print(f"  {icon} {step}")
    if detail:
        for line in detail.split("\n"):
            print(f"       {line}")


# ─────────────────────────────────────────────────
# 1. ステータス確認
# ─────────────────────────────────────────────────

def check_status() -> dict:
    """現在の認証状態を確認"""
    print_section("認証状態の確認")

    status = {
        "smtp_configured": False,
        "credentials_found": False,
        "gmail_token_found": False,
        "calendar_token_found": False,
        "google_libs_available": False,
    }

    # SMTP設定確認
    gmail_address = os.getenv("GMAIL_ADDRESS")
    gmail_password = os.getenv("GMAIL_APP_PASSWORD")
    if gmail_address and gmail_password:
        status["smtp_configured"] = True
        print_step("SMTP設定", "ok", f"送信元: {gmail_address}")
    else:
        missing = []
        if not gmail_address:
            missing.append("GMAIL_ADDRESS")
        if not gmail_password:
            missing.append("GMAIL_APP_PASSWORD")
        print_step("SMTP設定", "ng", f"未設定: {', '.join(missing)}")

    # Google APIライブラリ確認
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        status["google_libs_available"] = True
        print_step("Google API ライブラリ", "ok", "インストール済み")
    except ImportError as e:
        print_step("Google API ライブラリ", "ng",
                   f"未インストール: {e}\n"
                   "pip install google-auth google-auth-oauthlib google-api-python-client")

    # credentials.json確認
    if CREDENTIALS_FILE.exists():
        status["credentials_found"] = True
        try:
            with open(CREDENTIALS_FILE, "r", encoding="utf-8") as f:
                cred_data = json.load(f)
            # installed or web app type
            app_type = "installed" if "installed" in cred_data else "web"
            client_info = cred_data.get(app_type, {})
            client_id = client_info.get("client_id", "不明")[:40] + "..."
            print_step("credentials.json", "ok", f"種別: {app_type}, クライアントID: {client_id}")
        except Exception as e:
            print_step("credentials.json", "warn", f"読み取りエラー: {e}")
    else:
        print_step("credentials.json", "ng",
                   f"見つかりません: {CREDENTIALS_FILE}\n"
                   "Google Cloud Consoleからダウンロードが必要です")

    # Gmail トークン確認
    _check_token_file("Gmail APIトークン", GMAIL_TOKEN_FILE, GMAIL_SCOPES, status, "gmail_token_found")
    if not status["gmail_token_found"] and LEGACY_TOKEN_FILE.exists():
        print_step("  旧トークンファイル", "warn",
                   f"旧パスに存在: {LEGACY_TOKEN_FILE}\n"
                   f"  auth/gmail_token.json に移動することを推奨")
        status["gmail_token_found"] = True  # 旧パスでも有効

    # Calendar トークン確認
    _check_token_file("Calendar APIトークン", CALENDAR_TOKEN_FILE, CALENDAR_SCOPES, status, "calendar_token_found")

    return status


def _check_token_file(label: str, token_path: Path, scopes: list, status: dict, key: str):
    """トークンファイルの状態確認"""
    if not token_path.exists():
        print_step(label, "ng", f"見つかりません: {token_path}")
        return

    try:
        from google.oauth2.credentials import Credentials
        creds = Credentials.from_authorized_user_file(str(token_path), scopes)
        if creds.valid:
            expiry = creds.expiry.strftime("%Y-%m-%d %H:%M") if creds.expiry else "不明"
            print_step(label, "ok", f"有効（有効期限: {expiry}）")
            status[key] = True
        elif creds.expired and creds.refresh_token:
            print_step(label, "warn", "期限切れ（リフレッシュトークンあり・自動更新可能）")
            status[key] = True
        else:
            print_step(label, "ng", "無効（再認証が必要）")
    except Exception as e:
        print_step(label, "warn", f"読み取りエラー: {e}")


# ─────────────────────────────────────────────────
# 2. SMTP テスト
# ─────────────────────────────────────────────────

def test_smtp(send_test_email: bool = False) -> bool:
    """SMTP経由のGmail送信テスト"""
    print_section("SMTP メール送信テスト")

    try:
        from modules.smtp_mailer import SMTPGmailSender
        sender = SMTPGmailSender()

        if not sender.validate_config():
            print_step("設定確認", "ng", ".envファイルのGMAIL_ADDRESS / GMAIL_APP_PASSWORDを確認してください")
            return False

        print_step("設定確認", "ok",
                   f"送信元: {sender.sender_email}\n"
                   f"送信先: {sender.recipient_email}\n"
                   f"App Password: {'設定済み' if sender.app_password else '未設定'}")

        if send_test_email:
            print_step("テストメール送信", "run", "送信中...")
            success = sender.send_test_email()
            if success:
                print_step("テストメール送信", "ok",
                           f"{sender.recipient_email} にメールを送信しました\n"
                           "受信ボックスを確認してください")
                return True
            else:
                print_step("テストメール送信", "ng",
                           "送信失敗。App Passwordが正しいか確認してください\n"
                           "Googleアカウント → セキュリティ → アプリパスワード")
                return False
        else:
            print_step("接続テスト", "info", "--send-test-email フラグで実際のメール送信をテストできます")
            return True

    except ImportError as e:
        print_step("モジュール読み込み", "ng", f"エラー: {e}")
        return False
    except Exception as e:
        print_step("SMTP テスト", "ng", f"エラー: {e}")
        return False


# ─────────────────────────────────────────────────
# 3. OAuth2 認証フロー
# ─────────────────────────────────────────────────

def run_oauth2_flow(scopes: list, token_file: Path, service_name: str) -> bool:
    """OAuth2認証フローを実行してtoken.jsonを生成"""
    print_section(f"{service_name} OAuth2 認証")

    if not CREDENTIALS_FILE.exists():
        print_step("credentials.json確認", "ng",
                   f"ファイルが見つかりません: {CREDENTIALS_FILE}\n"
                   "\n手順:\n"
                   "1. https://console.cloud.google.com/ にアクセス\n"
                   "2. プロジェクト選択 → APIとサービス → 認証情報\n"
                   "3. + 認証情報を作成 → OAuth クライアント ID\n"
                   "4. アプリケーションの種類: デスクトップ アプリ\n"
                   f"5. ダウンロードして {CREDENTIALS_FILE} に配置")
        return False

    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow

        # 既存トークンの確認
        if token_file.exists():
            print_step("既存トークン確認", "warn",
                       f"既存のトークンが見つかりました: {token_file}")
            response = input("  上書きしますか？ (y/N): ").strip().lower()
            if response != "y":
                print_step("スキップ", "info", "既存のトークンを保持します")
                return True

        # ディレクトリ作成
        token_file.parent.mkdir(parents=True, exist_ok=True)

        print_step("OAuth2フロー開始", "run",
                   "ブラウザが自動的に開きます...\n"
                   "Googleアカウントでログインして権限を許可してください\n"
                   "(ブラウザが開かない場合はコンソールのURLをコピーしてください)")

        flow = InstalledAppFlow.from_client_secrets_file(
            str(CREDENTIALS_FILE),
            scopes,
        )

        # ローカルサーバーでコールバックを受け取る
        creds = flow.run_local_server(
            port=0,           # 自動ポート選択
            timeout_seconds=300,
            access_type="offline",
            prompt="consent",  # リフレッシュトークン取得のため強制
        )

        # トークン保存
        with open(str(token_file), "w", encoding="utf-8") as f:
            f.write(creds.to_json())

        expiry = creds.expiry.strftime("%Y-%m-%d %H:%M") if creds.expiry else "不明"
        print_step("認証完了", "ok",
                   f"トークン保存: {token_file}\n"
                   f"有効期限: {expiry}\n"
                   f"リフレッシュトークン: {'あり' if creds.refresh_token else 'なし'}")
        return True

    except ImportError as e:
        print_step("ライブラリエラー", "ng",
                   f"{e}\n"
                   "pip install google-auth-oauthlib google-api-python-client")
        return False
    except KeyboardInterrupt:
        print_step("中断", "warn", "ユーザーにより中断されました")
        return False
    except Exception as e:
        print_step("OAuth2 エラー", "ng",
                   f"{e}\n"
                   "\nトラブルシューティング:\n"
                   "- ポートがブロックされていないか確認\n"
                   "- credentials.json が正しいファイルか確認\n"
                   "- Google Cloud Console でテストユーザーに追加されているか確認")
        return False


def setup_gmail_oauth2() -> bool:
    """Gmail API の OAuth2 セットアップ"""
    return run_oauth2_flow(
        scopes=GMAIL_SCOPES,
        token_file=GMAIL_TOKEN_FILE,
        service_name="Gmail API",
    )


def setup_calendar_oauth2() -> bool:
    """Google Calendar API の OAuth2 セットアップ"""
    return run_oauth2_flow(
        scopes=CALENDAR_SCOPES,
        token_file=CALENDAR_TOKEN_FILE,
        service_name="Google Calendar API",
    )


def setup_combined_oauth2() -> bool:
    """Gmail + Calendar 統合 OAuth2 セットアップ（1回の認証で両方取得）"""
    combined_token = project_root / "auth" / "combined_token.json"
    result = run_oauth2_flow(
        scopes=COMBINED_SCOPES,
        token_file=combined_token,
        service_name="Gmail + Calendar API (統合)",
    )
    if result:
        # 統合トークンをコピーして両方に使用
        import shutil
        if not GMAIL_TOKEN_FILE.exists():
            shutil.copy(str(combined_token), str(GMAIL_TOKEN_FILE))
            print_step("Gmail トークン", "ok", f"コピー完了: {GMAIL_TOKEN_FILE}")
        if not CALENDAR_TOKEN_FILE.exists():
            shutil.copy(str(combined_token), str(CALENDAR_TOKEN_FILE))
            print_step("Calendar トークン", "ok", f"コピー完了: {CALENDAR_TOKEN_FILE}")
    return result


# ─────────────────────────────────────────────────
# 4. API 動作テスト
# ─────────────────────────────────────────────────

def test_gmail_api() -> bool:
    """Gmail API 接続テスト"""
    print_section("Gmail API 接続テスト")

    token_file = GMAIL_TOKEN_FILE if GMAIL_TOKEN_FILE.exists() else LEGACY_TOKEN_FILE
    if not token_file.exists():
        print_step("トークン確認", "ng",
                   "token.json が見つかりません\n"
                   "先に OAuth2 認証を実行してください: python scripts/setup_oauth2.py --gmail")
        return False

    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        creds = Credentials.from_authorized_user_file(str(token_file), GMAIL_SCOPES)

        if not creds.valid:
            if creds.expired and creds.refresh_token:
                print_step("トークン更新", "run", "期限切れのためリフレッシュ中...")
                creds.refresh(Request())
                print_step("トークン更新", "ok", "リフレッシュ成功")
            else:
                print_step("トークン確認", "ng", "無効なトークン。再認証が必要です")
                return False

        service = build("gmail", "v1", credentials=creds, cache_discovery=False)
        profile = service.users().getProfile(userId="me").execute()
        email = profile.get("emailAddress", "不明")
        messages_total = profile.get("messagesTotal", 0)

        print_step("Gmail API 接続", "ok",
                   f"メールアドレス: {email}\n"
                   f"メッセージ総数: {messages_total:,}件")
        return True

    except Exception as e:
        print_step("Gmail API テスト", "ng", f"エラー: {e}")
        return False


def test_calendar_api() -> bool:
    """Google Calendar API 接続テスト"""
    print_section("Google Calendar API 接続テスト")

    token_file = CALENDAR_TOKEN_FILE if CALENDAR_TOKEN_FILE.exists() else LEGACY_TOKEN_FILE
    if not token_file.exists():
        print_step("トークン確認", "ng",
                   "calendar_token.json が見つかりません\n"
                   "先に OAuth2 認証を実行してください: python scripts/setup_oauth2.py --calendar")
        return False

    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        creds = Credentials.from_authorized_user_file(str(token_file), CALENDAR_SCOPES)

        if not creds.valid:
            if creds.expired and creds.refresh_token:
                print_step("トークン更新", "run", "リフレッシュ中...")
                creds.refresh(Request())
                print_step("トークン更新", "ok", "リフレッシュ成功")
            else:
                print_step("トークン確認", "ng", "無効なトークン。再認証が必要です")
                return False

        service = build("calendar", "v3", credentials=creds, cache_discovery=False)
        calendar_list = service.calendarList().list().execute()
        calendars = calendar_list.get("items", [])

        print_step("Calendar API 接続", "ok",
                   f"利用可能なカレンダー: {len(calendars)}件")
        for cal in calendars[:5]:
            primary = " [PRIMARY]" if cal.get("primary") else ""
            print(f"       - {cal['summary']}{primary}")
        return True

    except Exception as e:
        print_step("Calendar API テスト", "ng", f"エラー: {e}")
        return False


# ─────────────────────────────────────────────────
# 5. セットアップガイド表示
# ─────────────────────────────────────────────────

def show_setup_guide():
    """Google Cloud Console セットアップガイドを表示"""
    print_section("Google Cloud Console セットアップガイド")
    print("""
  credentials.json を取得するには以下の手順が必要です:

  1. Google Cloud Console にアクセス
     https://console.cloud.google.com/

  2. プロジェクト作成（初回のみ）
     プロジェクト名: MangaAnime-Info-System

  3. API の有効化
     APIとサービス → ライブラリ → 以下を有効化:
     - "Gmail API"
     - "Google Calendar API"

  4. OAuth同意画面の設定
     APIとサービス → OAuth同意画面
     - ユーザータイプ: 外部
     - アプリ名: MangaAnime Info System
     - テストユーザーに自分のGmailを追加

  5. OAuth クライアントID の作成
     APIとサービス → 認証情報
     → + 認証情報を作成 → OAuth クライアント ID
     → アプリケーションの種類: デスクトップ アプリ
     → JSONをダウンロード

  6. ファイルの配置
     ダウンロードしたJSONを credentials.json にリネームして配置:
""")
    print(f"     {CREDENTIALS_FILE}")
    print("""
  7. OAuth2 セットアップ実行
     python scripts/setup_oauth2.py --oauth2

  詳細: docs/GOOGLE_API_SETUP.md
""")


# ─────────────────────────────────────────────────
# メイン
# ─────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Google OAuth2 認証セットアップ",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python scripts/setup_oauth2.py --status          # 認証状態確認
  python scripts/setup_oauth2.py --smtp            # SMTP設定確認
  python scripts/setup_oauth2.py --smtp --send     # SMTPテストメール送信
  python scripts/setup_oauth2.py --guide           # セットアップガイド表示
  python scripts/setup_oauth2.py --gmail           # Gmail OAuth2 設定
  python scripts/setup_oauth2.py --calendar        # Calendar OAuth2 設定
  python scripts/setup_oauth2.py --oauth2          # Gmail+Calendar 統合設定
  python scripts/setup_oauth2.py --test-gmail      # Gmail API テスト
  python scripts/setup_oauth2.py --test-calendar   # Calendar API テスト
  python scripts/setup_oauth2.py --all             # すべて実行
        """,
    )

    parser.add_argument("--status", action="store_true", help="認証状態を確認")
    parser.add_argument("--smtp", action="store_true", help="SMTP設定を確認")
    parser.add_argument("--send", action="store_true", help="SMTPテストメールを送信（--smtpと併用）")
    parser.add_argument("--guide", action="store_true", help="セットアップガイドを表示")
    parser.add_argument("--gmail", action="store_true", help="Gmail OAuth2 認証を実行")
    parser.add_argument("--calendar", action="store_true", help="Calendar OAuth2 認証を実行")
    parser.add_argument("--oauth2", action="store_true", help="Gmail+Calendar 統合 OAuth2 認証を実行")
    parser.add_argument("--test-gmail", action="store_true", help="Gmail API 接続テスト")
    parser.add_argument("--test-calendar", action="store_true", help="Calendar API 接続テスト")
    parser.add_argument("--all", action="store_true", help="すべてのテストを実行")

    args = parser.parse_args()

    # デフォルト: --status
    if not any(vars(args).values()):
        args.status = True

    print("\n" + "=" * 60)
    print("  MangaAnime Info System - OAuth2 セットアップ")
    print(f"  実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    results = {}

    if args.status or args.all:
        results["status"] = check_status()

    if args.smtp or args.all:
        results["smtp"] = test_smtp(send_test_email=args.send or args.all)

    if args.guide:
        show_setup_guide()

    if args.gmail:
        results["gmail_oauth2"] = setup_gmail_oauth2()

    if args.calendar:
        results["calendar_oauth2"] = setup_calendar_oauth2()

    if args.oauth2 or args.all:
        results["oauth2"] = setup_combined_oauth2()

    if args.test_gmail or args.all:
        results["gmail_api"] = test_gmail_api()

    if args.test_calendar or args.all:
        results["calendar_api"] = test_calendar_api()

    # サマリー表示
    if len(results) > 0:
        print_section("結果サマリー")
        icons = {True: "✅", False: "❌"}

        if "status" in results:
            s = results["status"]
            print(f"  SMTP設定:             {icons[s['smtp_configured']]}")
            print(f"  Google API ライブラリ: {icons[s['google_libs_available']]}")
            print(f"  credentials.json:     {icons[s['credentials_found']]}")
            print(f"  Gmail トークン:        {icons[s['gmail_token_found']]}")
            print(f"  Calendar トークン:     {icons[s['calendar_token_found']]}")
        if "smtp" in results:
            print(f"  SMTP テスト:          {icons[results['smtp']]}")
        if "gmail_oauth2" in results:
            print(f"  Gmail OAuth2:         {icons[results['gmail_oauth2']]}")
        if "calendar_oauth2" in results:
            print(f"  Calendar OAuth2:      {icons[results['calendar_oauth2']]}")
        if "oauth2" in results:
            print(f"  統合 OAuth2:          {icons[results['oauth2']]}")
        if "gmail_api" in results:
            print(f"  Gmail API テスト:     {icons[results['gmail_api']]}")
        if "calendar_api" in results:
            print(f"  Calendar API テスト:  {icons[results['calendar_api']]}")

        # 次のステップ
        if "status" in results:
            s = results["status"]
            print("\n  📋 次のステップ:")
            if not s["credentials_found"]:
                print("  → credentials.json を取得: python scripts/setup_oauth2.py --guide")
            elif not s["gmail_token_found"] or not s["calendar_token_found"]:
                print("  → OAuth2 認証実行: python scripts/setup_oauth2.py --oauth2")
            elif s["smtp_configured"] and s["gmail_token_found"] and s["calendar_token_found"]:
                print("  → Phase 1 完了！次は Phase 2: AniList API テスト")

    print()


if __name__ == "__main__":
    main()
