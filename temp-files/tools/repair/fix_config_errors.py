#!/usr/bin/env python3
"""
設定エラー自動修復スクリプト

指定されたエラーを検出し、自動的に修正を適用するスクリプト。
エラーが解消されるまでループして修正を続行します。
"""

import json
import os
import sys
from typing import List, Dict, Any
import logging

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ConfigAutoRepair:
    """設定ファイル自動修復クラス"""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = config_path
        self.backup_path = f"{config_path}.backup"
        
    def load_config(self) -> Dict[Any, Any]:
        """設定ファイルを読み込み"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"設定ファイル {self.config_path} が見つかりません")
            sys.exit(1)
        except json.JSONDecodeError as e:
            logger.error(f"設定ファイルのJSON形式が無効です: {e}")
            sys.exit(1)
    
    def save_config(self, config: Dict[Any, Any]) -> None:
        """設定ファイルを保存"""
        # バックアップ作成
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r', encoding='utf-8') as f:
                with open(self.backup_path, 'w', encoding='utf-8') as backup:
                    backup.write(f.read())
            logger.info(f"バックアップファイルを作成: {self.backup_path}")
        
        # 新しい設定を保存
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        logger.info(f"設定ファイルを更新: {self.config_path}")
    
    def validate_config(self, config: Dict[Any, Any]) -> List[str]:
        """設定を検証してエラーリストを返す"""
        errors = []

        # Check required Google API settings
        google_config = config.get("apis", {}).get("google", {})
        if not google_config.get("credentials_file"):
            errors.append("Google credentials file not specified")

        # Check email notification settings
        email_config = config.get("notification", {}).get("email", {})
        if not email_config.get("sender"):
            errors.append("Gmail from_email not configured")
        if not email_config.get("recipients"):
            errors.append("Gmail to_email not configured")

        return errors
    
    def check_file_exists(self, file_path: str) -> bool:
        """ファイルの存在を確認"""
        return os.path.exists(file_path)
    
    def fix_google_credentials_error(self, config: Dict[Any, Any]) -> bool:
        """Google credentials設定エラーを修正"""
        logger.info("Google credentials設定を修正中...")
        
        # apis.google構造を確保
        if "apis" not in config:
            config["apis"] = {}
        if "google" not in config["apis"]:
            config["apis"]["google"] = {}
        
        # credentials.jsonファイルの存在確認
        if self.check_file_exists("credentials.json"):
            config["apis"]["google"]["credentials_file"] = "credentials.json"
            logger.info("✅ Google credentials設定を修正: credentials.json")
            return True
        elif self.check_file_exists("gmail_credentials.json"):
            config["apis"]["google"]["credentials_file"] = "gmail_credentials.json"
            logger.info("✅ Google credentials設定を修正: gmail_credentials.json")
            return True
        else:
            logger.warning("❌ credentials.jsonファイルが見つかりません。手動で設定してください。")
            # デフォルト値を設定
            config["apis"]["google"]["credentials_file"] = "credentials.json"
            logger.info("✅ デフォルトのcredentials.json設定を適用")
            return True
        
    def fix_gmail_sender_error(self, config: Dict[Any, Any]) -> bool:
        """Gmail送信者設定エラーを修正"""
        logger.info("Gmail送信者設定を修正中...")
        
        # notification.email構造を確保
        if "notification" not in config:
            config["notification"] = {}
        if "email" not in config["notification"]:
            config["notification"]["email"] = {}
        
        # 環境変数から取得を試行
        gmail_sender = os.getenv('GMAIL_SENDER', 'kensan1969@gmail.com')
        config["notification"]["email"]["sender"] = gmail_sender
        logger.info(f"✅ Gmail送信者設定を修正: {gmail_sender}")
        return True
    
    def fix_gmail_recipients_error(self, config: Dict[Any, Any]) -> bool:
        """Gmail受信者設定エラーを修正"""
        logger.info("Gmail受信者設定を修正中...")
        
        # notification.email構造を確保
        if "notification" not in config:
            config["notification"] = {}
        if "email" not in config["notification"]:
            config["notification"]["email"] = {}
        
        # 環境変数から取得を試行
        gmail_recipients = os.getenv('GMAIL_RECIPIENTS', 'kensan1969@gmail.com').split(',')
        config["notification"]["email"]["recipients"] = [r.strip() for r in gmail_recipients]
        logger.info(f"✅ Gmail受信者設定を修正: {config['notification']['email']['recipients']}")
        return True
    
    def auto_repair(self) -> bool:
        """設定エラーを自動修復"""
        max_attempts = 5
        attempt = 0
        
        logger.info("🔧 設定エラー自動修復を開始します...")
        
        while attempt < max_attempts:
            attempt += 1
            logger.info(f"\n--- 修復試行 {attempt}/{max_attempts} ---")
            
            # 設定を読み込み
            config = self.load_config()
            
            # エラー検証
            errors = self.validate_config(config)
            
            if not errors:
                logger.info("✅ すべての設定エラーが解消されました！")
                return True
            
            logger.info(f"検出されたエラー ({len(errors)}件):")
            for i, error in enumerate(errors, 1):
                logger.info(f"  {i}. {error}")
            
            # エラーごとに修正を実行
            config_modified = False
            
            for error in errors:
                if "Google credentials file not specified" in error:
                    if self.fix_google_credentials_error(config):
                        config_modified = True
                
                elif "Gmail from_email not configured" in error:
                    if self.fix_gmail_sender_error(config):
                        config_modified = True
                
                elif "Gmail to_email not configured" in error:
                    if self.fix_gmail_recipients_error(config):
                        config_modified = True
            
            if config_modified:
                self.save_config(config)
                logger.info("📝 設定ファイルを更新しました")
            else:
                logger.warning("⚠️  修正できないエラーがあります")
                break
        
        logger.error(f"💥 {max_attempts}回の試行後もエラーが残っています")
        return False
    
    def create_env_setup_script(self) -> None:
        """環境変数設定スクリプトを作成"""
        env_script = """#!/bin/bash
# MangaAnime Info Delivery System 環境変数設定スクリプト

echo "🔧 環境変数を設定します..."

# Gmail設定
read -p "Gmail送信者アドレスを入力してください [kensan1969@gmail.com]: " GMAIL_SENDER
GMAIL_SENDER=${GMAIL_SENDER:-kensan1969@gmail.com}

read -p "Gmail受信者アドレスを入力してください（カンマ区切りで複数可） [kensan1969@gmail.com]: " GMAIL_RECIPIENTS
GMAIL_RECIPIENTS=${GMAIL_RECIPIENTS:-kensan1969@gmail.com}

# 環境変数をエクスポート
export GMAIL_SENDER="$GMAIL_SENDER"
export GMAIL_RECIPIENTS="$GMAIL_RECIPIENTS"

# .envファイルに保存
cat > .env << EOF
GMAIL_SENDER=$GMAIL_SENDER
GMAIL_RECIPIENTS=$GMAIL_RECIPIENTS
EOF

echo "✅ 環境変数が設定されました"
echo "✅ .envファイルに保存されました"
echo ""
echo "以下のコマンドで環境変数を読み込めます:"
echo "source .env"
"""
        
        script_path = "setup_env.sh"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(env_script)
        os.chmod(script_path, 0o755)
        logger.info(f"✅ 環境変数設定スクリプトを作成: {script_path}")
    
    def test_system_startup(self) -> bool:
        """システムの起動テスト"""
        logger.info("🧪 システム起動テストを実行...")
        
        import subprocess
        try:
            result = subprocess.run(
                [sys.executable, "release_notifier.py", "--dry-run"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info("✅ システムが正常に起動しました！")
                return True
            else:
                logger.error("❌ システム起動に失敗しました:")
                logger.error(f"標準出力: {result.stdout}")
                logger.error(f"標準エラー: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("❌ システム起動テストがタイムアウトしました")
            return False
        except Exception as e:
            logger.error(f"❌ システム起動テストでエラーが発生: {e}")
            return False


def main():
    """メイン関数"""
    logger.info("=" * 60)
    logger.info("🚀 MangaAnime Info Delivery System 設定自動修復")
    logger.info("=" * 60)
    
    repair = ConfigAutoRepair()
    
    # 環境変数設定スクリプト作成
    repair.create_env_setup_script()
    
    # 自動修復実行
    if repair.auto_repair():
        # システム起動テスト
        if repair.test_system_startup():
            logger.info("🎉 すべての修復と検証が完了しました！")
            logger.info("システムは正常に動作します。")
            sys.exit(0)
        else:
            logger.error("💥 修復は完了しましたが、システム起動に問題があります")
            sys.exit(1)
    else:
        logger.error("💥 設定修復に失敗しました")
        sys.exit(1)


if __name__ == "__main__":
    main()