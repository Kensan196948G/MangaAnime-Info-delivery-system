#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
認証設定管理モジュール
- OAuth2認証（token.json）とGmail App Password設定を統合管理
- セキュリティ設定の自動適用
- 設定ファイルの検証機能
"""

import json
import os
import stat
from pathlib import Path
from typing import Dict, Optional, Tuple
import logging

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AuthConfig:
    """認証設定管理クラス"""
    
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.token_file = self.base_dir / "token.json"
        self.credentials_file = self.base_dir / "credentials.json"
        self.gmail_config_file = self.base_dir / "gmail_config.json"
        self.template_file = self.base_dir / "gmail_config.json.template"
    
    def check_oauth2_setup(self) -> Tuple[bool, str]:
        """OAuth2認証の設定状況をチェック"""
        try:
            # credentials.json の存在確認
            if not self.credentials_file.exists():
                return False, f"credentials.json が見つかりません: {self.credentials_file}"
            
            # パーミッション確認
            creds_perms = oct(os.stat(self.credentials_file).st_mode)[-3:]
            if creds_perms != '600':
                return False, f"credentials.json のパーミッションが不適切です: {creds_perms} (600が推奨)"
            
            # token.json の存在確認（オプション）
            if self.token_file.exists():
                token_perms = oct(os.stat(self.token_file).st_mode)[-3:]
                if token_perms != '600':
                    return False, f"token.json のパーミッションが不適切です: {token_perms} (600が推奨)"
                logger.info("✅ token.json が存在し、適切なパーミッションが設定されています")
            else:
                logger.info("ℹ️ token.json は未作成です。create_token.py で生成してください")
            
            return True, "OAuth2認証設定は正常です"
            
        except Exception as e:
            return False, f"OAuth2設定チェック中にエラー: {e}"
    
    def check_gmail_config_setup(self) -> Tuple[bool, str]:
        """Gmail App Password設定状況をチェック"""
        try:
            if not self.gmail_config_file.exists():
                if self.template_file.exists():
                    return False, f"gmail_config.json が見つかりません。{self.template_file} をコピーして作成してください"
                else:
                    return False, "gmail_config.json とテンプレートファイルが見つかりません"
            
            # パーミッション確認
            gmail_perms = oct(os.stat(self.gmail_config_file).st_mode)[-3:]
            if gmail_perms != '600':
                return False, f"gmail_config.json のパーミッションが不適切です: {gmail_perms} (600が推奨)"
            
            # 設定ファイル内容の確認
            with open(self.gmail_config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            gmail_settings = config.get('gmail_settings', {})
            required_fields = ['email_address', 'app_password', 'smtp_server', 'smtp_port']
            missing_fields = [field for field in required_fields if not gmail_settings.get(field)]
            
            if missing_fields:
                return False, f"gmail_config.json に必須フィールドが不足: {', '.join(missing_fields)}"
            
            # デフォルト値チェック
            if gmail_settings['email_address'] == 'your-email@gmail.com':
                return False, "gmail_config.json のemail_addressがデフォルト値のままです"
            
            if gmail_settings['app_password'] == 'your-16-character-app-password':
                return False, "gmail_config.json のapp_passwordがデフォルト値のままです"
            
            return True, "Gmail App Password設定は正常です"
            
        except json.JSONDecodeError:
            return False, "gmail_config.json の形式が正しくありません"
        except Exception as e:
            return False, f"Gmail設定チェック中にエラー: {e}"
    
    def load_gmail_config(self) -> Optional[Dict]:
        """Gmail設定を読み込み"""
        try:
            if not self.gmail_config_file.exists():
                logger.error(f"Gmail設定ファイルが見つかりません: {self.gmail_config_file}")
                return None
            
            with open(self.gmail_config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('gmail_settings')
        except Exception as e:
            logger.error(f"Gmail設定読み込みエラー: {e}")
            return None
    
    def setup_secure_permissions(self) -> bool:
        """認証ファイルのセキュアなパーミッション設定"""
        try:
            files_to_secure = [
                self.credentials_file,
                self.token_file,
                self.gmail_config_file
            ]
            
            secured_count = 0
            for file_path in files_to_secure:
                if file_path.exists():
                    os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR)  # 600
                    logger.info(f"✅ {file_path.name} のパーミッションを600に設定")
                    secured_count += 1
            
            if secured_count > 0:
                logger.info(f"🔒 {secured_count}個のファイルにセキュアなパーミッションを適用しました")
                return True
            else:
                logger.warning("セキュア設定すべきファイルが見つかりませんでした")
                return False
                
        except Exception as e:
            logger.error(f"パーミッション設定エラー: {e}")
            return False
    
    def create_gmail_config_from_template(self) -> bool:
        """テンプレートからGmail設定ファイルを作成"""
        try:
            if self.gmail_config_file.exists():
                logger.warning("gmail_config.json は既に存在します")
                return False
            
            if not self.template_file.exists():
                logger.error("テンプレートファイルが見つかりません")
                return False
            
            # テンプレートをコピー
            with open(self.template_file, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            with open(self.gmail_config_file, 'w', encoding='utf-8') as f:
                f.write(template_content)
            
            # セキュアなパーミッション設定
            os.chmod(self.gmail_config_file, stat.S_IRUSR | stat.S_IWUSR)
            
            logger.info(f"✅ gmail_config.json をテンプレートから作成しました")
            logger.info("⚠️ email_address と app_password を実際の値に変更してください")
            
            return True
            
        except Exception as e:
            logger.error(f"Gmail設定ファイル作成エラー: {e}")
            return False
    
    def validate_all_configs(self) -> Dict[str, Tuple[bool, str]]:
        """全ての認証設定を検証"""
        results = {}
        
        results['oauth2'] = self.check_oauth2_setup()
        results['gmail'] = self.check_gmail_config_setup()
        
        # 総合結果
        all_valid = all(result[0] for result in results.values())
        
        if all_valid:
            logger.info("🎉 全ての認証設定が正常です！")
        else:
            logger.warning("⚠️ 一部の認証設定に問題があります")
        
        return results


def main():
    """認証設定の検証とセットアップ"""
    import argparse
    
    parser = argparse.ArgumentParser(description="認証設定の管理と検証")
    parser.add_argument("--setup-gmail", action="store_true", help="テンプレートからGmail設定を作成")
    parser.add_argument("--fix-permissions", action="store_true", help="認証ファイルのパーミッションを修正")
    parser.add_argument("--validate", action="store_true", help="全設定を検証")
    
    args = parser.parse_args()
    
    auth_config = AuthConfig()
    
    if args.setup_gmail:
        auth_config.create_gmail_config_from_template()
    
    if args.fix_permissions:
        auth_config.setup_secure_permissions()
    
    if args.validate or not any([args.setup_gmail, args.fix_permissions]):
        # デフォルトで検証実行
        results = auth_config.validate_all_configs()
        
        print("\n📋 認証設定検証結果:")
        for config_type, (is_valid, message) in results.items():
            status = "✅" if is_valid else "❌"
            print(f"  {status} {config_type}: {message}")


if __name__ == "__main__":
    main()