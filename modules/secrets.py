"""
Secrets Management Module
==========================

シークレット管理モジュール
HashiCorp Vault / AWS Secrets Manager / Azure Key Vault対応

Features:
- 複数プロバイダー対応
- 自動ローテーション
- キャッシュ機能
- フォールバック機能
"""

import hashlib
import json
import logging
import os

logger = logging.getLogger(__name__)
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, Optional


class SecretProvider(ABC):
    """シークレットプロバイダー基底クラス"""

    @abstractmethod
    def get_secret(self, key: str) -> Optional[str]:
        """シークレットを取得"""

    @abstractmethod
    def set_secret(self, key: str, value: str) -> bool:
        """シークレットを設定"""

    @abstractmethod
    def delete_secret(self, key: str) -> bool:
        """シークレットを削除"""

    @abstractmethod
    def list_secrets(self) -> list:
        """シークレット一覧を取得"""


class EnvSecretProvider(SecretProvider):
    """環境変数ベースのシークレットプロバイダー（開発用）"""

    def __init__(self, prefix: str = "SECRET_"):
        self.prefix = prefix

    def get_secret(self, key: str) -> Optional[str]:
        env_key = f"{self.prefix}{key.upper()}"
        return os.environ.get(env_key)

    def set_secret(self, key: str, value: str) -> bool:
        env_key = f"{self.prefix}{key.upper()}"
        os.environ[env_key] = value
        return True

    def delete_secret(self, key: str) -> bool:
        env_key = f"{self.prefix}{key.upper()}"
        if env_key in os.environ:
            del os.environ[env_key]
            return True
        return False

    def list_secrets(self) -> list:
        return [
            k.replace(self.prefix, "").lower()
            for k in os.environ.keys()
            if k.startswith(self.prefix)
        ]


class VaultSecretProvider(SecretProvider):
    """HashiCorp Vault シークレットプロバイダー"""

    def __init__(
        self,
        url: str = "http://127.0.0.1:8200",
        token: Optional[str] = None,
        mount_point: str = "secret",
        namespace: Optional[str] = None,
    ):
        self.url = url
        self.token = token or os.environ.get("VAULT_TOKEN")
        self.mount_point = mount_point
        self.namespace = namespace
        self._client = None

    @property
    def client(self):
        if self._client is None:
            try:
                import hvac

                self._client = hvac.Client(url=self.url, token=self.token)
                if self.namespace:
                    self._client.namespace = self.namespace
            except ImportError:
                logger.warning("hvac package not installed. Install with: pip install hvac")
                raise
        return self._client

    def get_secret(self, key: str) -> Optional[str]:
        try:
            response = self.client.secrets.kv.v2.read_secret_version(
                path=key, mount_point=self.mount_point
            )
            data = response.get("data", {}).get("data", {})
            return data.get("value") if "value" in data else json.dumps(data)
        except Exception as e:
            logger.error(f"Failed to get secret {key}: {e}")
            return None

    def set_secret(self, key: str, value: str) -> bool:
        try:
            self.client.secrets.kv.v2.create_or_update_secret(
                path=key, secret={"value": value}, mount_point=self.mount_point
            )
            return True
        except Exception as e:
            logger.error(f"Failed to set secret {key}: {e}")
            return False

    def delete_secret(self, key: str) -> bool:
        try:
            self.client.secrets.kv.v2.delete_metadata_and_all_versions(
                path=key, mount_point=self.mount_point
            )
            return True
        except Exception as e:
            logger.error(f"Failed to delete secret {key}: {e}")
            return False

    def list_secrets(self) -> list:
        try:
            response = self.client.secrets.kv.v2.list_secrets(path="", mount_point=self.mount_point)
            return response.get("data", {}).get("keys", [])
        except Exception as e:
            logger.error(f"Failed to list secrets: {e}")
            return []


class AWSSecretProvider(SecretProvider):
    """AWS Secrets Manager プロバイダー"""

    def __init__(
        self,
        region_name: str = "ap-northeast-1",
        prefix: str = "mangaanime/",
    ):
        self.region_name = region_name
        self.prefix = prefix
        self._client = None

    @property
    def client(self):
        if self._client is None:
            try:
                import boto3

                self._client = boto3.client("secretsmanager", region_name=self.region_name)
            except ImportError:
                logger.warning("boto3 package not installed. Install with: pip install boto3")
                raise
        return self._client

    def _full_key(self, key: str) -> str:
        return f"{self.prefix}{key}"

    def get_secret(self, key: str) -> Optional[str]:
        try:
            response = self.client.get_secret_value(SecretId=self._full_key(key))
            return response.get("SecretString")
        except Exception as e:
            logger.error(f"Failed to get secret {key}: {e}")
            return None

    def set_secret(self, key: str, value: str) -> bool:
        try:
            full_key = self._full_key(key)
            try:
                self.client.update_secret(SecretId=full_key, SecretString=value)
            except self.client.exceptions.ResourceNotFoundException:
                self.client.create_secret(Name=full_key, SecretString=value)
            return True
        except Exception as e:
            logger.error(f"Failed to set secret {key}: {e}")
            return False

    def delete_secret(self, key: str) -> bool:
        try:
            self.client.delete_secret(SecretId=self._full_key(key), ForceDeleteWithoutRecovery=True)
            return True
        except Exception as e:
            logger.error(f"Failed to delete secret {key}: {e}")
            return False

    def list_secrets(self) -> list:
        try:
            secrets = []
            paginator = self.client.get_paginator("list_secrets")
            for page in paginator.paginate():
                for secret in page.get("SecretList", []):
                    name = secret.get("Name", "")
                    if name.startswith(self.prefix):
                        secrets.append(name.replace(self.prefix, ""))
            return secrets
        except Exception as e:
            logger.error(f"Failed to list secrets: {e}")
            return []


class SecretCache:
    """シークレットキャッシュ"""

    def __init__(self, ttl_seconds: int = 300):
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, tuple] = {}

    def get(self, key: str) -> Optional[str]:
        if key in self._cache:
            value, expiry = self._cache[key]
            if datetime.now() < expiry:
                return value
            del self._cache[key]
        return None

    def set(self, key: str, value: str) -> None:
        expiry = datetime.now() + timedelta(seconds=self.ttl_seconds)
        self._cache[key] = (value, expiry)

    def delete(self, key: str) -> None:
        if key in self._cache:
            del self._cache[key]

    def clear(self) -> None:
        self._cache.clear()


class SecretsManager:
    """統合シークレットマネージャー"""

    def __init__(
        self,
        provider: Optional[SecretProvider] = None,
        cache_ttl: int = 300,
        fallback_to_env: bool = True,
    ):
        """
        初期化

        Args:
            provider: シークレットプロバイダー
            cache_ttl: キャッシュTTL（秒）
            fallback_to_env: 環境変数へのフォールバック
        """
        self.provider = provider or self._auto_detect_provider()
        self.cache = SecretCache(ttl_seconds=cache_ttl)
        self.fallback_to_env = fallback_to_env
        self._env_provider = EnvSecretProvider() if fallback_to_env else None

    def _auto_detect_provider(self) -> SecretProvider:
        """プロバイダーを自動検出"""
        # Vault
        if os.environ.get("VAULT_ADDR") and os.environ.get("VAULT_TOKEN"):
            logger.info("Using HashiCorp Vault as secret provider")
            return VaultSecretProvider(url=os.environ.get("VAULT_ADDR"))

        # AWS
        if os.environ.get("AWS_SECRET_ACCESS_KEY") or os.environ.get("AWS_PROFILE"):
            logger.info("Using AWS Secrets Manager as secret provider")
            return AWSSecretProvider()

        # デフォルト: 環境変数
        logger.info("Using environment variables as secret provider")
        return EnvSecretProvider()

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        シークレットを取得

        Args:
            key: シークレットキー
            default: デフォルト値

        Returns:
            シークレット値
        """
        # キャッシュ確認
        cached = self.cache.get(key)
        if cached is not None:
            return cached

        # プロバイダーから取得
        value = self.provider.get_secret(key)

        # フォールバック
        if value is None and self.fallback_to_env and self._env_provider:
            value = self._env_provider.get_secret(key)

        # デフォルト値
        if value is None:
            return default

        # キャッシュに保存
        self.cache.set(key, value)
        return value

    def set(self, key: str, value: str) -> bool:
        """シークレットを設定"""
        result = self.provider.set_secret(key, value)
        if result:
            self.cache.set(key, value)
        return result

    def delete(self, key: str) -> bool:
        """シークレットを削除"""
        result = self.provider.delete_secret(key)
        if result:
            self.cache.delete(key)
        return result

    def list(self) -> list:
        """シークレット一覧を取得"""
        return self.provider.list_secrets()

    def rotate(self, key: str, new_value: str) -> bool:
        """
        シークレットをローテーション

        Args:
            key: シークレットキー
            new_value: 新しい値

        Returns:
            成功/失敗
        """
        # 古い値を取得（ロールバック用）
        old_value = self.get(key)

        # 新しい値を設定
        if self.set(key, new_value):
            logger.info(f"Secret {key} rotated successfully")
            return True

        logger.error(f"Failed to rotate secret {key}")
        return False


# グローバルインスタンス
_secrets_manager: Optional[SecretsManager] = None


def get_secrets_manager() -> SecretsManager:
    """シークレットマネージャーのシングルトンを取得"""
    global _secrets_manager
    if _secrets_manager is None:
        _secrets_manager = SecretsManager()
    return _secrets_manager


def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """シークレットを取得（ショートカット関数）"""
    return get_secrets_manager().get(key, default)


def mask_secret(value: str, visible_chars: int = 4) -> str:
    """シークレット値をマスク"""
    if not value or len(value) <= visible_chars:
        return "*" * len(value) if value else ""
    return value[:visible_chars] + "*" * (len(value) - visible_chars)


def hash_secret(value: str) -> str:
    """シークレット値をハッシュ化"""
    return hashlib.sha256(value.encode()).hexdigest()


if __name__ == "__main__":
    # テスト
    logging.basicConfig(level=logging.INFO)

    # 環境変数テスト
    os.environ["SECRET_TEST_KEY"] = "test_value"

    manager = SecretsManager()
    print(f"Detected provider: {type(manager.provider).__name__}")
    print(f"Get test_key: {manager.get('test_key')}")
    print(f"List secrets: {manager.list()}")
