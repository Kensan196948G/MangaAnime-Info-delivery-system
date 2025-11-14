#!/usr/bin/env python3
"""
Flask SECRET_KEY設定テストスクリプト
改善されたSECRET_KEY管理機能の動作確認を行います。
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch

# プロジェクトルートをPATHに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class TestSecretKeyConfig(unittest.TestCase):
    """SECRET_KEY設定のテストクラス"""
    
    def setUp(self):
        """テスト前の準備"""
        # 既存の環境変数を保存
        self.original_env = {
            'SECRET_KEY': os.environ.get('SECRET_KEY'),
            'FLASK_SECRET_KEY': os.environ.get('FLASK_SECRET_KEY'),
            'MANGA_ANIME_SECRET_KEY': os.environ.get('MANGA_ANIME_SECRET_KEY'),
        }
        
        # テスト用に環境変数をクリア
        for key in self.original_env:
            if key in os.environ:
                del os.environ[key]
    
    def tearDown(self):
        """テスト後のクリーンアップ"""
        # 元の環境変数を復元
        for key, value in self.original_env.items():
            if value is not None:
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]
    
    def test_config_functions_import(self):
        """config.pyの関数がインポートできることを確認"""
        try:
            from modules.config import (
                get_flask_secret_key,
                generate_secret_key,
                validate_secret_key,
                setup_flask_secret_key
            )
            self.assertTrue(True, "関数のインポートに成功")
        except ImportError as e:
            self.fail(f"config.pyの関数インポートに失敗: {e}")
    
    def test_generate_secret_key(self):
        """SECRET_KEY生成機能のテスト"""
        from modules.config import generate_secret_key, validate_secret_key
        
        # 10回生成してテスト
        for i in range(10):
            key = generate_secret_key()
            
            # 基本チェック
            self.assertIsInstance(key, str, "生成されたキーが文字列である")
            self.assertGreaterEqual(len(key), 32, "生成されたキーが32文字以上である")
            self.assertTrue(validate_secret_key(key), "生成されたキーが妥当性検証をパス")
    
    def test_validate_secret_key(self):
        """SECRET_KEY妥当性検証のテスト"""
        from modules.config import validate_secret_key
        
        # 有効なキー
        valid_keys = [
            "abcdef1234567890abcdef1234567890",  # 32文字
            "secure-random-key-123456789012345",  # 34文字
            "VerySecureRandomGeneratedKey12345678"  # 36文字
        ]
        
        for key in valid_keys:
            self.assertTrue(validate_secret_key(key), f"有効なキーが認識される: {key}")
        
        # 無効なキー
        invalid_keys = [
            None,  # None
            "",  # 空文字
            "short",  # 短すぎる
            "your-secret-key-here",  # デフォルト値
            "dev-secret-key-change-in-production",  # デフォルト値
            "your-secret-key-change-this-in-production",  # デフォルト値
        ]
        
        for key in invalid_keys:
            self.assertFalse(validate_secret_key(key), f"無効なキーが拒否される: {key}")
    
    def test_secret_key_priority(self):
        """SECRET_KEY優先順位のテスト"""
        from modules.config import get_flask_secret_key
        
        # 複数の環境変数を設定
        os.environ['SECRET_KEY'] = 'priority1-key-32chars-long-test'
        os.environ['FLASK_SECRET_KEY'] = 'priority2-key-32chars-long-test'
        os.environ['MANGA_ANIME_SECRET_KEY'] = 'priority3-key-32chars-long-test'
        
        # SECRET_KEYが最優先されることを確認
        key = get_flask_secret_key()
        self.assertEqual(key, 'priority1-key-32chars-long-test')
        
        # SECRET_KEYを削除してFLASK_SECRET_KEYが使われることを確認
        del os.environ['SECRET_KEY']
        key = get_flask_secret_key()
        self.assertEqual(key, 'priority2-key-32chars-long-test')
        
        # FLASK_SECRET_KEYも削除してMANGA_ANIME_SECRET_KEYが使われることを確認
        del os.environ['FLASK_SECRET_KEY']
        key = get_flask_secret_key()
        self.assertEqual(key, 'priority3-key-32chars-long-test')
    
    def test_no_secret_key_error(self):
        """SECRET_KEY未設定時のエラーのテスト"""
        from modules.config import get_flask_secret_key
        
        # 全ての環境変数がない状態でエラーが発生することを確認
        with self.assertRaises(RuntimeError):
            get_flask_secret_key()
    
    def test_short_secret_key_error(self):
        """短すぎるSECRET_KEYでエラーが発生することを確認"""
        from modules.config import get_flask_secret_key
        
        # 16文字未満のキーでエラーが発生することを確認
        os.environ['SECRET_KEY'] = 'short'
        with self.assertRaises(RuntimeError):
            get_flask_secret_key()
    
    def test_flask_app_integration(self):
        """FlaskアプリとのSECRET_KEY統合テスト"""
        from flask import Flask
        from modules.config import setup_flask_secret_key
        
        # テスト用のFlaskアプリを作成
        app = Flask(__name__)
        
        # 有効なSECRET_KEYを設定
        os.environ['SECRET_KEY'] = 'test-secret-key-32chars-long-valid'
        
        # setup_flask_secret_key関数でSECRET_KEYを設定
        setup_flask_secret_key(app)
        
        # アプリにSECRET_KEYが設定されたことを確認
        self.assertEqual(app.secret_key, 'test-secret-key-32chars-long-valid')


def main():
    """テストの実行"""
    print("SECRET_KEY設定テストを開始します...")
    
    # SECRET_KEY生成のデモンストレーション
    print("\n=== SECRET_KEY生成デモ ===")
    try:
        from modules.config import generate_secret_key, validate_secret_key
        
        for i in range(3):
            key = generate_secret_key()
            is_valid = validate_secret_key(key)
            print(f"生成キー {i+1}: {key} (妥当性: {'OK' if is_valid else 'NG'})")
    except ImportError:
        print("ERROR: modules.configがインポートできません")
    
    # 環境変数設定デモ
    print("\n=== 環境変数設定例 ===")
    print("以下のコマンドでSECRET_KEYを設定できます:")
    try:
        from modules.config import generate_secret_key
        example_key = generate_secret_key()
        print(f"export SECRET_KEY='{example_key}'")
        print(f"echo 'SECRET_KEY={example_key}' >> .env")
    except ImportError:
        print("python3 -c \"import secrets; print('export SECRET_KEY=' + secrets.token_urlsafe(32))\"")
    
    # ユニットテスト実行
    print("\n=== ユニットテスト実行 ===")
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == '__main__':
    main()