"""
Google API認証の共通処理モジュール

GmailとGoogle Calendarで共通する認証ロジックを統合し、
コードの重複を排除し保守性を向上させる。
"""

import os
import logging
from typing import Optional, List
from pathlib import Path
from datetime import datetime, timedelta

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False


class GoogleAuthenticationError(Exception):
    """Google認証関連のエラー"""



class GoogleAuthenticator:
    """
    Google API認証の共通処理クラス

    Gmail、Google Calendar等のGoogle APIサービスで
    共通するOAuth2認証フローを提供する。
    """

    def __init__(
        self,
        credentials_file: str,
        token_file: str,
        scopes: List[str],
        service_name: str = "Google API",
    ):
        """
        認証マネージャーの初期化

        Args:
            credentials_file: OAuth2クライアントシークレットファイルのパス
            token_file: 保存されたトークンファイルのパス
            scopes: 要求するAPIスコープのリスト
            service_name: サービス名（ログ用）
        """
        if not GOOGLE_AVAILABLE:
            raise GoogleAuthenticationError(
                "Google API libraries not available. "
                "Install google-auth, google-auth-oauthlib, google-api-python-client"
            )

        self.credentials_file = credentials_file
        self.token_file = token_file
        self.scopes = scopes
        self.service_name = service_name
        self.logger = logging.getLogger(__name__)

        # 認証状態の追跡
        self._credentials: Optional[Credentials] = None
        self._last_auth_time: Optional[datetime] = None
        self._auth_failure_count = 0

    def authenticate(self) -> Optional[Credentials]:
        """
        OAuth2認証を実行

        Returns:
            Optional[Credentials]: 認証成功時はCredentials、失敗時はNone

        Raises:
            GoogleAuthenticationError: 認証に致命的な問題がある場合
        """
        try:
            self.logger.info(f"{self.service_name}認証を開始...")

            # 既存トークンの読み込み
            creds = self._load_existing_token()

            # トークンの検証と更新
            if not creds or not creds.valid:
                creds = self._refresh_or_reauthorize(creds)

            # 認証成功
            if creds and creds.valid:
                self._save_token(creds)
                self._credentials = creds
                self._last_auth_time = datetime.now()
                self._auth_failure_count = 0

                self.logger.info(
                    f"{self.service_name}認証に成功しました "
                    f"(有効期限: {creds.expiry or '不明'})"
                )
                return creds

            # 認証失敗
            self._auth_failure_count += 1
            self.logger.error(f"{self.service_name}認証に失敗しました")
            return None

        except Exception as e:
            self._auth_failure_count += 1
            error_msg = f"{self.service_name}認証でエラーが発生: {e}"
            self.logger.error(error_msg)
            raise GoogleAuthenticationError(error_msg) from e

    def _load_existing_token(self) -> Optional[Credentials]:
        """
        既存のトークンをファイルから読み込み

        Returns:
            Optional[Credentials]: 読み込まれたCredentials、存在しない場合はNone
        """
        if not os.path.exists(self.token_file):
            self.logger.debug(f"トークンファイルが存在しません: {self.token_file}")
            return None

        try:
            creds = Credentials.from_authorized_user_file(self.token_file, self.scopes)
            self.logger.debug("既存のトークンを読み込みました")
            return creds

        except Exception as e:
            self.logger.warning(f"トークンの読み込みに失敗: {e}")

            # 破損したトークンファイルを削除
            try:
                os.remove(self.token_file)
                self.logger.info("破損したトークンファイルを削除しました")
            except OSError:
                pass

            return None

    def _refresh_or_reauthorize(
        self, creds: Optional[Credentials]
    ) -> Optional[Credentials]:
        """
        トークンをリフレッシュまたは再認証

        Args:
            creds: 既存のCredentials

        Returns:
            Optional[Credentials]: 更新されたCredentials
        """
        # リフレッシュ試行
        if creds and creds.expired and creds.refresh_token:
            try:
                self.logger.info("トークンをリフレッシュ中...")
                creds.refresh(Request())
                self.logger.info("トークンのリフレッシュに成功しました")
                return creds

            except Exception as e:
                self.logger.warning(f"トークンのリフレッシュに失敗: {e}")
                # リフレッシュ失敗時は再認証へ

        # 再認証実行
        return self._run_oauth_flow()

    def _run_oauth_flow(self) -> Optional[Credentials]:
        """
        OAuth2認証フローを実行

        Returns:
            Optional[Credentials]: 認証成功時のCredentials

        Raises:
            GoogleAuthenticationError: クライアントシークレットファイルが存在しない場合
        """
        # クライアントシークレットファイルの確認
        if not os.path.exists(self.credentials_file):
            error_msg = f"クライアントシークレットファイルが見つかりません: {self.credentials_file}"
            self.logger.error(error_msg)
            raise GoogleAuthenticationError(error_msg)

        try:
            self.logger.info(f"{self.service_name} OAuth2フローを開始...")
            self.logger.info("ブラウザが開きます。Googleアカウントで認証してください。")

            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_file, self.scopes
            )

            # ローカルサーバーを起動して認証
            creds = flow.run_local_server(
                port=0,
                timeout_seconds=300,  # 5分タイムアウト
                access_type="offline",
                prompt="consent",
            )

            self.logger.info("OAuth2認証フローが完了しました")
            return creds

        except Exception as e:
            error_msg = f"OAuth2フローでエラーが発生: {e}"
            self.logger.error(error_msg)
            return None

    def _save_token(self, creds: Credentials) -> None:
        """
        トークンを安全にファイルへ保存

        Args:
            creds: 保存するCredentials
        """
        try:
            # ディレクトリが存在することを確認
            token_path = Path(self.token_file)
            token_path.parent.mkdir(parents=True, exist_ok=True)

            # セキュアなファイルパーミッション設定（Linux/Mac）
            old_umask = os.umask(0o077)  # owner read/write only
            try:
                with open(self.token_file, "w") as token:
                    token.write(creds.to_json())
            finally:
                os.umask(old_umask)

            # Windows環境でもファイルパーミッションを制限
            try:
                if os.name == "nt":  # Windows
                    import stat

                    os.chmod(self.token_file, stat.S_IREAD | stat.S_IWRITE)
            except Exception:
                pass

            self.logger.info(f"トークンを安全に保存しました: {self.token_file}")

        except Exception as e:
            self.logger.error(f"トークンの保存に失敗: {e}")
            # 保存失敗はクリティカルではないため、例外を再発生させない

    def is_authenticated(self) -> bool:
        """
        認証済みかどうかを確認

        Returns:
            bool: 認証済みでトークンが有効な場合True
        """
        if not self._credentials:
            return False

        if not self._credentials.valid:
            return False

        # 有効期限のチェック
        if self._credentials.expiry:
            # 5分以内に期限切れの場合は再認証が必要
            if self._credentials.expiry < datetime.now() + timedelta(minutes=5):
                return False

        return True

    def get_credentials(self) -> Optional[Credentials]:
        """
        現在のCredentialsを取得

        Returns:
            Optional[Credentials]: 認証済みの場合はCredentials、未認証の場合はNone
        """
        return self._credentials if self.is_authenticated() else None

    def revoke_authentication(self) -> None:
        """
        認証を取り消し、トークンファイルを削除
        """
        try:
            # トークンファイルの削除
            if os.path.exists(self.token_file):
                # セキュアな削除（上書き後削除）
                try:
                    file_size = os.path.getsize(self.token_file)
                    with open(self.token_file, "wb") as f:
                        f.write(os.urandom(file_size))
                except Exception:
                    pass

                os.remove(self.token_file)
                self.logger.info("トークンファイルを削除しました")

            # 内部状態のクリア
            self._credentials = None
            self._last_auth_time = None

        except Exception as e:
            self.logger.error(f"トークン削除エラー: {e}")

    def get_auth_status(self) -> dict:
        """
        認証状態の情報を取得

        Returns:
            dict: 認証状態の詳細情報
        """
        status = {
            "is_authenticated": self.is_authenticated(),
            "service_name": self.service_name,
            "token_file": self.token_file,
            "token_exists": os.path.exists(self.token_file),
            "last_auth_time": (
                self._last_auth_time.isoformat() if self._last_auth_time else None
            ),
            "auth_failure_count": self._auth_failure_count,
        }

        if self._credentials and self._credentials.expiry:
            status["token_expiry"] = self._credentials.expiry.isoformat()
            status["time_until_expiry_seconds"] = (
                self._credentials.expiry - datetime.now()
            ).total_seconds()

        return status
