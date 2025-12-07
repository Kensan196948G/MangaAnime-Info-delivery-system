#!/usr/bin/env python3
"""
Security setup script for MangaAnime Info Delivery System.

This script helps set up secure configuration with proper file permissions,
environment variable validation, and OAuth2 token encryption.
"""

import os
import sys
import getpass
import stat
import base64
import secrets
from pathlib import Path
import logging

# Add the parent directory to the path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
except ImportError as e:
    print(f"Error: Cannot import configuration modules: {e}")
    print("Please run this script from the project root directory.")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SecuritySetup:
    """Security setup and configuration helper."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.config_dir = self.project_root / "config"
        self.env_file = self.project_root / ".env"
        self.secure_config = None

    def run_setup(self):
        """Run the complete security setup process."""
        print("🔒 MangaAnime Info Delivery System - Security Setup")
        print("=" * 60)

        try:
            # Step 1: Create directories with proper permissions
            self._create_secure_directories()

            # Step 2: Generate secure keys
            self._generate_secure_keys()

            # Step 3: Setup environment variables
            self._setup_environment_variables()

            # Step 4: Secure file permissions
            self._secure_file_permissions()

            # Step 5: Validate configuration
            self._validate_security_setup()

            print("\n✅ Security setup completed successfully!")
            print("\n📝 Next steps:")
            print("1. Review and update .env file with your actual credentials")
            print("2. Place your Google API credentials.json file in the project root")
            print("3. Run the OAuth2 setup: python3 create_token.py")
            print("4. Test the configuration: python3 -m pytest tests/")

        except Exception as e:
            logger.error(f"Security setup failed: {e}")
            print(f"\n❌ Setup failed: {e}")
            sys.exit(1)

    def _create_secure_directories(self):
        """Create necessary directories with secure permissions."""
        print("\n📁 Creating secure directories...")

        directories = [
            self.config_dir,
            self.project_root / "logs",
            self.project_root / "backups",
            self.project_root / "tokens",
            self.project_root / "templates",
        ]

        for directory in directories:
            directory.mkdir(mode=0o750, parents=True, exist_ok=True)
            logger.info(f"Created directory: {directory}")

        print("   ✓ Directories created with secure permissions (750)")

    def _generate_secure_keys(self):
        """Generate secure keys for encryption and authentication."""
        print("\n🔑 Generating secure keys...")

        # Generate secret key
        secret_key = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()

        # Generate encryption key
        encryption_key = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()

        # Generate salt
        salt = base64.urlsafe_b64encode(secrets.token_bytes(16)).decode()

        # Store in environment variables dict for later use
        self.generated_keys = {
            "MANGA_ANIME_SECRET_KEY": secret_key,
            "MANGA_ANIME_ENCRYPTION_KEY": encryption_key,
            "MANGA_ANIME_SALT": salt,
        }

        print("   ✓ Generated secure keys for encryption and authentication")

    def _setup_environment_variables(self):
        """Setup environment variables from user input."""
        print("\n🔧 Setting up environment variables...")

        # Base environment variables
        env_vars = {
            "MANGA_ANIME_ENVIRONMENT": "production",
            "MANGA_ANIME_LOG_LEVEL": "INFO",
            "MANGA_ANIME_DB_PATH": "./db.sqlite3",
            "MANGA_ANIME_LOG_PATH": "./logs/app.log",
            "MANGA_ANIME_CREDENTIALS_FILE": "credentials.json",
            "MANGA_ANIME_TOKEN_FILE": "token.json",
            "MANGA_ANIME_CALENDAR_ID": "primary",
        }

        # Add generated keys
        env_vars.update(self.generated_keys)

        # Interactive input for sensitive data
        print("\n📧 Gmail Configuration:")
        gmail_from = input("Enter your Gmail address: ").strip()
        if gmail_from:
            env_vars["MANGA_ANIME_GMAIL_FROM"] = gmail_from
            env_vars["MANGA_ANIME_GMAIL_TO"] = gmail_from  # Default to same email

        print(
            "\n🔐 Would you like to set up OAuth2 client credentials now? (y/n): ",
            end="",
        )
        setup_oauth = input().strip().lower() == "y"

        if setup_oauth:
            gmail_client_id = input("Enter Gmail OAuth2 Client ID: ").strip()
            if gmail_client_id:
                env_vars["GMAIL_CLIENT_ID"] = gmail_client_id

            gmail_client_secret = getpass.getpass(
                "Enter Gmail OAuth2 Client Secret: "
            ).strip()
            if gmail_client_secret:
                env_vars["GMAIL_CLIENT_SECRET"] = gmail_client_secret

            calendar_client_id = input(
                "Enter Calendar OAuth2 Client ID (or press Enter to use Gmail ID): "
            ).strip()
            env_vars["CALENDAR_CLIENT_ID"] = calendar_client_id or gmail_client_id

            if not calendar_client_id:
                env_vars["CALENDAR_CLIENT_SECRET"] = gmail_client_secret
            else:
                calendar_client_secret = getpass.getpass(
                    "Enter Calendar OAuth2 Client Secret: "
                ).strip()
                if calendar_client_secret:
                    env_vars["CALENDAR_CLIENT_SECRET"] = calendar_client_secret

        # Master password for encryption
        print("\n🔒 Set master password for sensitive data encryption:")
        master_password = getpass.getpass("Enter master password: ").strip()
        if master_password:
            env_vars["MANGA_ANIME_MASTER_PASSWORD"] = master_password

        # Write environment file
        self._write_env_file(env_vars)
        print("   ✓ Environment variables configured")

    def _write_env_file(self, env_vars: Dict[str, str]):
        """Write environment variables to .env file."""
        env_content = "# MangaAnime Info Delivery System Environment Configuration\n"
        env_content += "# Generated by security_setup.py\n\n"

        sections = {
            "System Settings": [
                "MANGA_ANIME_ENVIRONMENT",
                "MANGA_ANIME_LOG_LEVEL",
                "MANGA_ANIME_LOG_PATH",
            ],
            "Database": ["MANGA_ANIME_DB_PATH"],
            "Gmail Configuration": [
                "MANGA_ANIME_GMAIL_FROM",
                "MANGA_ANIME_GMAIL_TO",
                "GMAIL_CLIENT_ID",
                "GMAIL_CLIENT_SECRET",
            ],
            "Calendar Configuration": [
                "MANGA_ANIME_CALENDAR_ID",
                "CALENDAR_CLIENT_ID",
                "CALENDAR_CLIENT_SECRET",
            ],
            "Google API Files": [
                "MANGA_ANIME_CREDENTIALS_FILE",
                "MANGA_ANIME_TOKEN_FILE",
            ],
            "Security Keys": [
                "MANGA_ANIME_SECRET_KEY",
                "MANGA_ANIME_ENCRYPTION_KEY",
                "MANGA_ANIME_SALT",
                "MANGA_ANIME_MASTER_PASSWORD",
            ],
        }

        for section, keys in sections.items():
            env_content += f"# {section}\n"
            for key in keys:
                if key in env_vars:
                    env_content += f"{key}={env_vars[key]}\n"
            env_content += "\n"

        # Write with secure permissions
        old_umask = os.umask(0o077)
        try:
            with open(self.env_file, "w") as f:
                f.write(env_content)
        finally:
            os.umask(old_umask)

    def _secure_file_permissions(self):
        """Set secure file permissions on sensitive files."""
        print("\n🛡️  Setting secure file permissions...")

        # Files that should be readable only by owner
        secure_files = [
            self.env_file,
            self.project_root / "credentials.json",
            self.project_root / "token.json",
            self.project_root / "service-account.json",
        ]

        for file_path in secure_files:
            if file_path.exists():
                file_path.chmod(0o600)  # Read/write for owner only
                logger.info(f"Secured permissions for: {file_path}")

        # Directories that should be accessible only by owner
        secure_dirs = [self.project_root / "tokens", self.project_root / "backups"]

        for dir_path in secure_dirs:
            if dir_path.exists():
                dir_path.chmod(0o700)  # Full access for owner only
                logger.info(f"Secured directory permissions for: {dir_path}")

        print("   ✓ File permissions secured")

    def _validate_security_setup(self):
        """Validate the security setup."""
        print("\n✅ Validating security setup...")

        # Check environment file
        if not self.env_file.exists():
            raise RuntimeError("Environment file not created")

        # Check file permissions
        env_stat = self.env_file.stat()
        if stat.filemode(env_stat.st_mode) != "-rw-------":
            logger.warning(
                f"Environment file permissions may be too permissive: {stat.filemode(env_stat.st_mode)}"
            )

        # Test configuration loading
        try:
            # Load environment variables from file
            self._load_env_file()

            # Test configuration manager
            config_manager = ConfigManager(enable_encryption=True)
            logger.info("Configuration manager initialized successfully")

        except Exception as e:
            raise RuntimeError(f"Configuration validation failed: {e}")

        print("   ✓ Security setup validation passed")

    def _load_env_file(self):
        """Load environment variables from .env file for testing."""
        if not self.env_file.exists():
            return

        with open(self.env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key] = value


def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h"]:
        print("Usage: python3 scripts/security_setup.py")
        print(
            "\nThis script sets up secure configuration for the MangaAnime Info Delivery System."
        )
        print("It will:")
        print("- Create secure directories with proper permissions")
        print("- Generate secure keys for encryption")
        print("- Set up environment variables")
        print("- Configure file permissions")
        print("- Validate the security setup")
        return

    setup = SecuritySetup()
    setup.run_setup()


if __name__ == "__main__":
    main()
