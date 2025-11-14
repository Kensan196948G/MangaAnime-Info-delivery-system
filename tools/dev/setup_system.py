#!/usr/bin/env python3
"""
アニメ・マンガ情報配信システム - セットアップスクリプト

このスクリプトは以下のセットアップ作業を自動化します：
1. Python依存関係のインストール
2. データベースの初期化
3. ログディレクトリの作成
4. 設定ファイルの検証
5. Google API認証情報の確認
6. サンプルcron設定の生成

Usage:
    python3 setup_system.py [--full-setup] [--test-run]
"""

import sys
import json
import subprocess
import argparse
from pathlib import Path
import logging

# プロジェクトルートの設定
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# 必要な依存関係
REQUIRED_PACKAGES = [
    "google-auth>=2.17.0",
    "google-auth-oauthlib>=1.0.0",
    "google-auth-httplib2>=0.1.0",
    "google-api-python-client>=2.80.0",
    "feedparser>=6.0.10",
    "requests>=2.31.0",
    "aiohttp>=3.8.5",
]

# オプション依存関係
OPTIONAL_PACKAGES = [
    "flask>=2.3.0",
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
]


class SystemSetup:
    """システムセットアップ管理クラス"""

    def __init__(self, full_setup: bool = False, test_run: bool = False):
        self.full_setup = full_setup
        self.test_run = test_run
        self.project_root = PROJECT_ROOT

        # ログ設定
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)],
        )
        self.logger = logging.getLogger(__name__)

    def check_python_version(self) -> bool:
        """Python バージョンの確認"""
        self.logger.info("🐍 Python バージョンを確認しています...")

        if sys.version_info < (3, 8):
            self.logger.error("❌ Python 3.8 以上が必要です")
            self.logger.error(f"現在のバージョン: {sys.version}")
            return False

        self.logger.info(f"✅ Python {sys.version.split()[0]} が確認されました")
        return True

    def install_dependencies(self) -> bool:
        """依存関係のインストール"""
        self.logger.info("📦 依存関係をインストールしています...")

        try:
            # pip のアップグレード
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
                check=True,
                capture_output=True,
            )

            # 必須パッケージのインストール
            for package in REQUIRED_PACKAGES:
                self.logger.info(f"  インストール中: {package}")
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", package],
                    check=True,
                    capture_output=True,
                )

            # オプション依存関係のインストール（full-setupの場合）
            if self.full_setup:
                self.logger.info("🔧 オプション依存関係をインストールしています...")
                for package in OPTIONAL_PACKAGES:
                    try:
                        self.logger.info(f"  インストール中: {package}")
                        subprocess.run(
                            [sys.executable, "-m", "pip", "install", package],
                            check=True,
                            capture_output=True,
                        )
                    except subprocess.CalledProcessError:
                        self.logger.warning(f"⚠️ オプションパッケージのインストールに失敗: {package}")

            self.logger.info("✅ 依存関係のインストールが完了しました")
            return True

        except subprocess.CalledProcessError as e:
            self.logger.error(f"❌ パッケージインストールエラー: {e}")
            return False

    def create_directories(self) -> bool:
        """必要なディレクトリの作成"""
        self.logger.info("📁 ディレクトリ構造を作成しています...")

        directories = ["logs", "data", "backups", "temp"]

        try:
            for dir_name in directories:
                dir_path = self.project_root / dir_name
                dir_path.mkdir(exist_ok=True)
                self.logger.info(f"  作成: {dir_path}")

            self.logger.info("✅ ディレクトリ作成が完了しました")
            return True

        except Exception as e:
            self.logger.error(f"❌ ディレクトリ作成エラー: {e}")
            return False

    def initialize_database(self) -> bool:
        """データベースの初期化"""
        self.logger.info("💾 データベースを初期化しています...")

        try:
            # 設定ファイルの読み込み
            config_path = self.project_root / "config.json"
            if not config_path.exists():
                self.logger.error("❌ config.json が見つかりません")
                return False

            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)

            # データベースパスの取得
            db_path = config.get("database", {}).get("path", "./db.sqlite3")
            if not db_path.startswith("/"):
                db_path = self.project_root / db_path

            # データベースの初期化
            from modules.db import DatabaseManager

            db = DatabaseManager(str(db_path))

            self.logger.info(f"  データベース作成: {db_path}")
            self.logger.info("✅ データベース初期化が完了しました")
            return True

        except Exception as e:
            self.logger.error(f"❌ データベース初期化エラー: {e}")
            return False

    def validate_config(self) -> bool:
        """設定ファイルの検証"""
        self.logger.info("⚙️ 設定ファイルを検証しています...")

        try:
            config_path = self.project_root / "config.json"
            if not config_path.exists():
                self.logger.error("❌ config.json が見つかりません")
                return False

            from modules.config import get_config

            config = get_config(str(config_path))

            # 設定の検証
            errors = config.validate_config()
            if errors:
                self.logger.warning("⚠️ 設定に問題があります:")
                for error in errors:
                    self.logger.warning(f"  - {error}")
            else:
                self.logger.info("✅ 設定ファイルの検証が完了しました")

            return True

        except Exception as e:
            self.logger.error(f"❌ 設定ファイル検証エラー: {e}")
            return False

    def check_google_credentials(self) -> bool:
        """Google API認証情報の確認"""
        self.logger.info("🔐 Google API 認証情報を確認しています...")

        try:
            credentials_path = self.project_root / "credentials.json"
            token_path = self.project_root / "token.json"

            if not credentials_path.exists():
                self.logger.warning("⚠️ credentials.json が見つかりません")
                self.logger.warning(
                    "Google Cloud Console から OAuth 2.0 認証情報をダウンロードして配置してください"
                )
                self.logger.warning("https://console.cloud.google.com/apis/credentials")
                return False

            if token_path.exists():
                self.logger.info("✅ 既存の認証トークンが見つかりました")
            else:
                self.logger.info("ℹ️ 初回実行時に認証フローが開始されます")

            self.logger.info("✅ Google API 認証情報の確認が完了しました")
            return True

        except Exception as e:
            self.logger.error(f"❌ Google API認証情報確認エラー: {e}")
            return False

    def generate_cron_config(self) -> bool:
        """cron設定ファイルの生成"""
        self.logger.info("📅 cron設定ファイルを生成しています...")

        try:
            cron_config = """# アニメ・マンガ情報配信システム cron設定
# 毎朝8時に実行
0 8 * * * {sys.executable} {self.project_root}/release_notifier.py >> {self.project_root}/logs/cron.log 2>&1

# 追加の実行例（コメントアウト）:
# 1日2回実行（朝8時と夜20時）
# 0 8,20 * * * {sys.executable} {self.project_root}/release_notifier.py >> {self.project_root}/logs/cron.log 2>&1

# テスト用（5分毎、dry-run）
# */5 * * * * {sys.executable} {self.project_root}/release_notifier.py --dry-run >> {self.project_root}/logs/cron-test.log 2>&1
"""

            cron_path = self.project_root / "crontab.example"
            with open(cron_path, "w", encoding="utf-8") as f:
                f.write(cron_config)

            self.logger.info(f"✅ cron設定ファイルを作成しました: {cron_path}")
            self.logger.info("インストール方法: crontab crontab.example")
            return True

        except Exception as e:
            self.logger.error(f"❌ cron設定生成エラー: {e}")
            return False

    def run_test(self) -> bool:
        """システムテストの実行"""
        self.logger.info("🧪 システムテストを実行しています...")

        try:
            # ドライランでシステムを実行
            from release_notifier import ReleaseNotifierSystem

            with ReleaseNotifierSystem(dry_run=True) as system:
                success = system.run()

            if success:
                self.logger.info("✅ システムテストが正常に完了しました")
                return True
            else:
                self.logger.warning("⚠️ システムテストでエラーが発生しました")
                return False

        except Exception as e:
            self.logger.error(f"❌ システムテストエラー: {e}")
            return False

    def run_setup(self) -> bool:
        """セットアップの実行"""
        self.logger.info("🚀 アニメ・マンガ情報配信システム セットアップ開始")
        self.logger.info("=" * 60)

        setup_steps = [
            ("Python バージョン確認", self.check_python_version),
            ("依存関係インストール", self.install_dependencies),
            ("ディレクトリ作成", self.create_directories),
            ("データベース初期化", self.initialize_database),
            ("設定ファイル検証", self.validate_config),
            ("Google API認証確認", self.check_google_credentials),
            ("cron設定生成", self.generate_cron_config),
        ]

        if self.test_run:
            setup_steps.append(("システムテスト", self.run_test))

        success_count = 0
        total_steps = len(setup_steps)

        for step_name, step_func in setup_steps:
            self.logger.info(f"\n📋 {step_name}...")
            try:
                if step_func():
                    success_count += 1
                else:
                    self.logger.error(f"❌ {step_name} に失敗しました")
            except Exception as e:
                self.logger.error(f"❌ {step_name} でエラー: {e}")

        self.logger.info("\n" + "=" * 60)
        self.logger.info(f"📊 セットアップ結果: {success_count}/{total_steps} 成功")

        if success_count == total_steps:
            self.logger.info("🎉 セットアップが正常に完了しました！")
            self.logger.info("\n次の手順:")
            self.logger.info("1. Google Cloud Console でOAuth認証情報を設定")
            self.logger.info("2. credentials.json を配置")
            self.logger.info("3. config.json の設定を確認・調整")
            self.logger.info("4. python3 release_notifier.py --dry-run でテスト実行")
            self.logger.info("5. crontab crontab.example で定期実行を設定")
            return True
        else:
            self.logger.error("❌ セットアップ中にエラーが発生しました")
            return False


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="アニメ・マンガ情報配信システム セットアップ",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python3 setup_system.py                    # 基本セットアップ
  python3 setup_system.py --full-setup       # フルセットアップ（開発用）
  python3 setup_system.py --test-run         # テスト実行付きセットアップ
        """.strip(),
    )

    parser.add_argument(
        "--full-setup",
        action="store_true",
        help="フルセットアップ（オプション依存関係も含む）",
    )
    parser.add_argument("--test-run", action="store_true", help="セットアップ後にテスト実行")

    args = parser.parse_args()

    # セットアップの実行
    setup = SystemSetup(full_setup=args.full_setup, test_run=args.test_run)

    success = setup.run_setup()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
