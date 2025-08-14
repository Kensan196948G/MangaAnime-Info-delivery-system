#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Google OAuth2 token.json 生成・維持スクリプト（SSHトンネル対応 完全版）
- 初回: open_browser=False（URLをコンソールに出力。Windows側ブラウザで開く）
- 2回目以降: token.json を再利用。期限切れなら自動リフレッシュ
- --port でループバック用ポート指定（既定: 37259）
- 改行: LF, 文字コード: UTF-8 (BOMなし)
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# ===== 設定ここから =====
CREDENTIALS_FILE = "credentials.json"     # GCPの「デスクトップアプリ」用クライアントを配置
TOKEN_FILE = "token.json"                 # 生成・更新されるトークン
SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar.events",
]
DEFAULT_PORT = 37259
# ===== 設定ここまで =====


def log(msg: str) -> None:
    print(msg, flush=True)


def _save_creds(creds: Credentials, path: str = TOKEN_FILE) -> None:
    """認証情報を見やすいJSONで保存（機微情報なので権限管理・Git除外に注意）"""
    data = json.loads(creds.to_json())
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _load_saved_creds(path: str = TOKEN_FILE) -> Optional[Credentials]:
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Credentials.from_authorized_user_info(data, SCOPES)
    except Exception as e:
        log(f"⚠️ 既存 token.json の読み込みに失敗しました: {e}")
        return None


def _obtain_new_creds(port: int) -> Credentials:
    """SSHトンネル前提で新規に認証してトークン取得（ブラウザは自動起動しない）"""
    if not Path(CREDENTIALS_FILE).exists():
        raise FileNotFoundError(
            f"'{CREDENTIALS_FILE}' が見つかりません。Google Cloud Console で "
            f"OAuth クライアント（種別: デスクトップ アプリ）を作成し、同名で配置してください。"
        )

    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)

    try:
        log("🌐 手動認証モードを開始します。")
        log(f"   ※ SSHトンネル例:  ssh -L {port}:localhost:{port} <USER>@<HOST>")
        
        # 手動認証URLの生成
        flow.redirect_uri = f'http://localhost:{port}/'
        auth_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        
        log(f"\n📋 以下のURLをブラウザで開いて認証してください:")
        log(f"{auth_url}")
        log(f"\n許可後、認証コードが表示されます。そのコードを入力してください。")
        
        # 認証コードの手動入力
        try:
            auth_code = input("\n🔑 認証コードを入力してください: ").strip()
        except (EOFError, KeyboardInterrupt):
            raise Exception("認証がキャンセルされました")
        
        if not auth_code:
            raise Exception("認証コードが入力されませんでした")
        
        # トークンの取得
        flow.fetch_token(code=auth_code)
        creds = flow.credentials
        
    except OSError as e:
        # ポート衝突の場合は別ポートで再試行
        log(f"ℹ️ 指定ポート {port} が使用中です: {e}")
        return _obtain_new_creds(port + 1)
    except Exception as e:
        if "mismatching_state" in str(e) or "CSRF" in str(e):
            log("⚠️ CSRF状態不一致エラー。再度認証を試行します...")
            # 新しいフローを作成して再試行
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            flow.redirect_uri = f'http://localhost:{port}/'
            auth_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true'
            )
            
            log(f"\n📋 新しい認証URLです:")
            log(f"{auth_url}")
            
            try:
                auth_code = input("\n🔑 新しい認証コードを入力してください: ").strip()
                flow.fetch_token(code=auth_code)
                creds = flow.credentials
            except Exception as retry_e:
                raise Exception(f"認証に失敗しました: {retry_e}")
        else:
            raise e

    log("✅ 新規トークン取得に成功")
    _save_creds(creds)
    return creds


def _ensure_credentials(port: int) -> Credentials:
    """
    1) 既存 token.json が有効ならそのまま使用
    2) 有効期限切れかつ refresh_token があればリフレッシュ
    3) それ以外はローカルサーバ（open_browser=False）で新規取得
    """
    creds = _load_saved_creds()
    if creds and creds.valid:
        log("✅ 既存トークンが有効です（ブラウザ不要）")
        return creds

    if creds and creds.expired and creds.refresh_token:
        try:
            log("🔄 既存トークンのリフレッシュを実行中…")
            creds.refresh(Request())
            log("✅ トークンのリフレッシュ成功")
            _save_creds(creds)
            return creds
        except Exception as e:
            log(f"⚠️ トークンのリフレッシュに失敗: {e} → 新規取得に切り替えます。")

    return _obtain_new_creds(port)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create/refresh Google OAuth token.json (SSH tunnel friendly)"
    )
    parser.add_argument(
        "--port", type=int, default=DEFAULT_PORT,
        help=f"ループバック用ポート番号（既定: {DEFAULT_PORT}）"
    )
    args = parser.parse_args()

    log("🔐 token.json 作成／更新プロセスを開始します…")
    try:
        _ensure_credentials(args.port)
        log("🎉 完了: token.json は最新状態です！")
        return 0
    except Exception as e:
        log(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

