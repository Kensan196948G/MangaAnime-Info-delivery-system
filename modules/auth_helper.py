#!/usr/bin/env python3
"""
Google API 認証ヘルパーモジュール

このモジュールは、Google Calendar APIとGmail APIの認証処理を共通化します。
OAuth 2.0フローを使用してアクセストークンを取得・管理します。
"""

import pickle
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


class GoogleAuthHelper:
    """Google API認証のヘルパークラス"""

    # OAuth 2.0のスコープ定義
    SCOPES = {
        "calendar": ["https://www.googleapis.com/auth/calendar"],
        "gmail": [
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/gmail.readonly",
            "https://www.googleapis.com/auth/gmail.compose",
        ],
    }

    def __init__(self, project_root=None):
        """
        初期化

        Args:
            project_root (str): プロジェクトルートのパス。Noneの場合は自動検出。
        """
        if project_root is None:
            # このファイルの親の親ディレクトリをプロジェクトルートとする
            self.project_root = Path(__file__).parent.parent
        else:
            self.project_root = Path(project_root)

        self.credentials_path = self.project_root / "credentials.json"
        self.token_path = self.project_root / "token.json"
        self.token_pickle_path = self.project_root / "token.pickle"

    def get_credentials(self, scopes_type="calendar"):
        """
        Google APIの認証情報を取得

        Args:
            scopes_type (str): 'calendar' または 'gmail' または 'both'

        Returns:
            Credentials: Google API認証情報

        Raises:
            FileNotFoundError: credentials.jsonが見つからない場合
        """
        # スコープの決定
        if scopes_type == "both":
            scopes = self.SCOPES["calendar"] + self.SCOPES["gmail"]
        elif scopes_type in self.SCOPES:
            scopes = self.SCOPES[scopes_type]
        else:
            raise ValueError(f"Invalid scopes_type: {scopes_type}")

        creds = None

        # token.jsonまたはtoken.pickleから既存の認証情報を読み込み
        if self.token_path.exists():
            creds = Credentials.from_authorized_user_file(str(self.token_path), scopes)
        elif self.token_pickle_path.exists():
            with open(self.token_pickle_path, "rb") as token:
                creds = pickle.load(token)

        # 認証情報が無効または存在しない場合
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                # トークンが期限切れの場合、リフレッシュ
                print("トークンをリフレッシュ中...")
                creds.refresh(Request())
            else:
                # 新規認証フローを開始
                if not self.credentials_path.exists():
                    raise FileNotFoundError(
                        f"credentials.json が見つかりません: {self.credentials_path}\n"
                        f"docs/GOOGLE_API_SETUP.md の手順に従って取得してください。"
                    )

                print("初回認証を開始します...")
                print(
                    "ブラウザが開きますので、Googleアカウントでログインしてください。"
                )
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path), scopes
                )
                creds = flow.run_local_server(port=0)

            # 認証情報を保存
            with open(self.token_path, "w") as token:
                token.write(creds.to_json())

            print(f"認証情報を保存しました: {self.token_path}")

        return creds

    def get_calendar_service(self):
        """
        Google Calendar APIサービスを取得

        Returns:
            Resource: Google Calendar APIサービスオブジェクト
        """
        creds = self.get_credentials(scopes_type="calendar")
        service = build("calendar", "v3", credentials=creds)
        return service

    def get_gmail_service(self):
        """
        Gmail APIサービスを取得

        Returns:
            Resource: Gmail APIサービスオブジェクト
        """
        creds = self.get_credentials(scopes_type="gmail")
        service = build("gmail", "v1", credentials=creds)
        return service

    def revoke_credentials(self):
        """
        認証情報を取り消し、保存されたトークンを削除

        Returns:
            bool: 成功した場合True
        """
        try:
            # token.jsonを削除
            if self.token_path.exists():
                self.token_path.unlink()
                print(f"削除しました: {self.token_path}")

            # token.pickleを削除
            if self.token_pickle_path.exists():
                self.token_pickle_path.unlink()
                print(f"削除しました: {self.token_pickle_path}")

            print("認証情報を取り消しました。次回実行時に再認証が必要です。")
            return True
        except Exception as e:
            print(f"エラー: 認証情報の取り消しに失敗しました - {e}")
            return False

    def check_credentials_file(self):
        """
        credentials.jsonの存在確認

        Returns:
            bool: 存在する場合True
        """
        return self.credentials_path.exists()

    def get_credentials_path(self):
        """
        credentials.jsonのパスを取得

        Returns:
            Path: credentials.jsonのパス
        """
        return self.credentials_path


# モジュール単体でのテスト用
if __name__ == "__main__":
    print("Google API 認証ヘルパー - テストモード")
    print("=" * 60)

    helper = GoogleAuthHelper()

    # credentials.jsonの確認
    print(f"\n1. credentials.json の確認")
    print(f"   パス: {helper.get_credentials_path()}")
    print(f"   存在: {'✅ はい' if helper.check_credentials_file() else '❌ いいえ'}")

    if not helper.check_credentials_file():
        print("\n❌ credentials.jsonが見つかりません")
        print("   docs/GOOGLE_API_SETUP.md の手順に従って設定してください")
        exit(1)

    # Calendar API認証テスト
    print(f"\n2. Google Calendar API 認証テスト")
    try:
        service = helper.get_calendar_service()
        print("   ✅ Calendar APIサービスの取得成功")
    except Exception as e:
        print(f"   ❌ エラー: {e}")

    # Gmail API認証テスト
    print(f"\n3. Gmail API 認証テスト")
    try:
        service = helper.get_gmail_service()
        print("   ✅ Gmail APIサービスの取得成功")
    except Exception as e:
        print(f"   ❌ エラー: {e}")

    print("\n" + "=" * 60)
    print("テスト完了")
