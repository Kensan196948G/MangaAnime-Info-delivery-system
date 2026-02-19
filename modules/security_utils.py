"""
Security utilities module for the Anime/Manga Information Delivery System.
Provides input validation, sanitization, rate limiting, and secure configuration management.
"""

import base64
import hashlib
import json
import logging
import os
import re
import sqlite3
import time
import unicodedata
from collections import defaultdict
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

# Handle optional dependencies gracefully
try:
    import validators
except ImportError:
    validators = None

try:
    import bleach
except ImportError:
    bleach = None

try:
    from cryptography.fernet import Fernet
except ImportError:
    Fernet = None


class SecurityError(Exception):
    """Custom exception for security-related errors"""


class InputSanitizer:
    """Provides input validation and sanitization functionality"""

    ALLOWED_HTML_TAGS = ["p", "br", "strong", "em", "ul", "ol", "li", "a"]
    ALLOWED_ATTRIBUTES = {
        "a": ["hre", "title"],
    }
    MAX_FEED_SIZE = 5 * 1024 * 1024  # 5MB
    MAX_TITLE_LENGTH = 500
    MAX_DESCRIPTION_LENGTH = 2000

    # NGword patterns for content filtering
    NG_KEYWORDS = [
        "エロ",
        "R18",
        "成人向け",
        "BL",
        "百合",
        "ボーイズラブ",
        "アダルト",
        "18禁",
        "官能",
        "ハーレクイン",
        "Hentai",
        "Ecchi",
    ]

    # Allowed domains for RSS feeds and APIs
    ALLOWED_DOMAINS = [
        "graphql.anilist.co",
        "anilist.co",
        "cal.syoboi.jp",
        "anime.dmkt-sp.jp",
        "bookwalker.jp",
        "www.googleapis.com",
        "googleapis.com",
        "accounts.google.com",
        "example.com",  # テスト・開発用汎用ドメイン
    ]

    @staticmethod
    def sanitize_html_content(content: str) -> str:
        """Remove potentially dangerous HTML tags and attributes"""
        if not content:
            return ""

        if bleach is None:
            # Fallback: remove all HTML tags if bleach is not available
            import re

            clean_content = re.sub(r"<[^>]+>", "", content)
            return clean_content.strip()

        return bleach.clean(
            content,
            tags=InputSanitizer.ALLOWED_HTML_TAGS,
            attributes=InputSanitizer.ALLOWED_ATTRIBUTES,
            strip=True,
        )

    @staticmethod
    def validate_url(url: str, allowed_domains: List[str] = None) -> bool:
        """Validate URL format and optionally check against allowlist"""
        if not url:
            return False

        # Basic URL validation if validators module is not available
        if validators is None:
            # Simple URL validation using urllib.parse
            try:
                parsed = urlparse(url)
                if not parsed.scheme or not parsed.netloc:
                    return False
            except Exception:
                return False
        else:
            if not validators.url(url):
                return False

        parsed = urlparse(url)

        # Only allow HTTPS (except for localhost in development)
        if parsed.scheme not in ["https"] and parsed.netloc not in ["localhost", "127.0.0.1"]:
            return False

        # Check against allowed domains (default to ALLOWED_DOMAINS if not provided)
        if allowed_domains is None:
            allowed_domains = InputSanitizer.ALLOWED_DOMAINS

        if allowed_domains:
            return any(parsed.netloc.lower().endswith(domain.lower()) for domain in allowed_domains)

        return True

    @staticmethod
    def sanitize_title(title: str) -> str:
        """Sanitize anime/manga titles for safe storage and display"""
        if not title:
            raise ValueError("Title cannot be empty")

        if len(title) > InputSanitizer.MAX_TITLE_LENGTH:
            raise ValueError(f"Title too long (max {InputSanitizer.MAX_TITLE_LENGTH} chars)")

        # Remove control characters and normalize unicode
        title = unicodedata.normalize("NFKC", title)
        title = "".join(char for char in title if unicodedata.category(char)[0] != "C")

        # Remove potentially dangerous characters
        title = re.sub(r'[<>"\'\x00-\x1f\x7f-\x9f]', "", title)

        # Remove dangerous protocol prefixes (XSS prevention)
        title = re.sub(r'(?i)javascript\s*:', '', title)
        title = re.sub(r'(?i)vbscript\s*:', '', title)
        title = re.sub(r'(?i)data\s*:', '', title)

        # Remove HTML event handler attributes (onerror=, onclick=, etc.)
        title = re.sub(r'(?i)\bon\w+\s*=', '', title)

        # Remove SQL injection patterns (defense in depth)
        title = re.sub(
            r'(?i)\b(DROP|DELETE|TRUNCATE|ALTER|CREATE|INSERT|UPDATE|UNION|SELECT|EXEC(?:UTE)?)\s+(TABLE|DATABASE|FROM|INTO|ALL)\b',
            '', title
        )
        title = re.sub(r'--', '', title)   # SQLコメントマーカー除去
        title = re.sub(r';+', '', title)   # ステートメント区切り除去

        return title.strip()

    @staticmethod
    def sanitize_description(description: str) -> str:
        """Sanitize description content"""
        if not description:
            return ""

        if len(description) > InputSanitizer.MAX_DESCRIPTION_LENGTH:
            description = description[: InputSanitizer.MAX_DESCRIPTION_LENGTH] + "..."

        # Sanitize HTML content
        description = InputSanitizer.sanitize_html_content(description)

        # Normalize unicode
        description = unicodedata.normalize("NFKC", description)

        return description.strip()

    @staticmethod
    def contains_ng_words(content: str) -> bool:
        """Check if content contains NG keywords"""
        if not content:
            return False

        content_lower = content.lower()

        for keyword in InputSanitizer.NG_KEYWORDS:
            if keyword.lower() in content_lower:
                return True

        return False

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email address format"""
        if not email:
            return False

        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(email_pattern, email))


class RateLimiter:
    """Implements rate limiting for API requests"""

    def __init__(self):
        self.requests = defaultdict(list)
        self.lock = Lock()

    def is_allowed(self, identifier: str, limit_per_minute: int) -> bool:
        """Check if request is allowed under rate limit"""
        current_time = time.time()

        with self.lock:
            # Clean old requests (older than 1 minute)
            cutoff_time = current_time - 60
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier] if req_time > cutoff_time
            ]

            # Check if under limit
            if len(self.requests[identifier]) < limit_per_minute:
                self.requests[identifier].append(current_time)
                return True

            return False

    def get_wait_time(self, identifier: str) -> float:
        """Get seconds to wait before next request"""
        if not self.requests[identifier]:
            return 0

        oldest_request = min(self.requests[identifier])
        wait_time = 60 - (time.time() - oldest_request)
        return max(0, wait_time)

    def get_remaining_requests(self, identifier: str, limit_per_minute: int) -> int:
        """Get remaining requests in current window"""
        current_requests = len(self.requests.get(identifier, []))
        return max(0, limit_per_minute - current_requests)


class SecureTokenManager:
    """Manages OAuth2 tokens with encryption"""

    def __init__(self, token_file_path: str, encryption_key: bytes = None):
        self.token_file = Path(token_file_path)
        self.encryption_key = encryption_key or self._get_or_create_key()

        if Fernet is None:
            logging.warning(
                "Cryptography module not available - tokens will be stored in plain text"
            )
            self.fernet = None
        else:
            self.fernet = Fernet(self.encryption_key)

        # Ensure directory exists
        self.token_file.parent.mkdir(parents=True, exist_ok=True)

    def _get_or_create_key(self) -> bytes:
        """Get encryption key from environment or create new one"""
        if Fernet is None:
            return b"dummy_key_for_fallback"

        key_env = os.environ.get("TOKEN_ENCRYPTION_KEY")
        if key_env:
            try:
                return base64.urlsafe_b64decode(key_env.encode())
            except Exception:
                pass

        # Generate new key
        new_key = Fernet.generate_key()
        encoded_key = base64.urlsafe_b64encode(new_key).decode()
        logging.warning(
            f"Generated new token encryption key. Set TOKEN_ENCRYPTION_KEY={encoded_key}"
        )
        return new_key

    def save_token(self, token_data: Dict[str, Any]) -> None:
        """Save encrypted token data"""
        try:
            # Validate token data
            required_fields = ["access_token"]
            for field in required_fields:
                if field not in token_data:
                    raise ValueError(f"Missing required token field: {field}")

            # Encrypt and save or save as plain text if encryption not
            # available
            json_data = json.dumps(token_data, indent=2)

            if self.fernet is not None:
                encrypted_data = self.fernet.encrypt(json_data.encode())
                with open(self.token_file, "wb") as f:
                    f.write(encrypted_data)
                logging.info(f"Token saved securely (encrypted) to {self.token_file}")
            else:
                with open(self.token_file, "w") as f:
                    f.write(json_data)
                logging.warning(f"Token saved without encryption to {self.token_file}")

            # Set restrictive permissions
            os.chmod(self.token_file, 0o600)

        except Exception as e:
            raise SecurityError(f"Failed to save token: {e}")

    def load_token(self) -> Dict[str, Any]:
        """Load and decrypt token data"""
        if not self.token_file.exists():
            return {}

        try:
            if self.fernet is not None:
                # Try to load encrypted token
                try:
                    with open(self.token_file, "rb") as f:
                        encrypted_data = f.read()

                    decrypted_data = self.fernet.decrypt(encrypted_data)
                    token_data = json.loads(decrypted_data.decode())
                    return token_data
                except Exception:
                    # Fall back to plain text if decryption fails
                    pass

            # Load as plain text
            with open(self.token_file, "r") as f:
                token_data = json.load(f)
            return token_data

        except Exception as e:
            logging.error(f"Failed to load token: {e}")
            return {}

    def is_token_valid(self, token_data: Dict[str, Any]) -> bool:
        """Check if token is valid and not expired"""
        if not token_data or "access_token" not in token_data:
            return False

        # Check expiration if available
        if "expires_at" in token_data:
            current_time = time.time()
            expires_at = token_data["expires_at"]
            # Consider token expired 5 minutes before actual expiration
            return expires_at > (current_time + 300)

        return True

    def delete_token(self) -> None:
        """Securely delete token file"""
        if self.token_file.exists():
            try:
                # Overwrite file with random data before deletion
                file_size = self.token_file.stat().st_size
                with open(self.token_file, "wb") as f:
                    f.write(os.urandom(file_size))

                self.token_file.unlink()
                logging.info("Token file securely deleted")

            except Exception as e:
                logging.error(f"Failed to delete token file: {e}")


class SecureConfig:
    """Manages secure configuration with encryption support"""

    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.encryption_key = self._get_encryption_key()

        if Fernet is None or self.encryption_key is None:
            self.fernet = None
        else:
            self.fernet = Fernet(self.encryption_key)
        self._config_cache = None
        self._last_modified = 0

    def _get_encryption_key(self) -> Optional[bytes]:
        """Get encryption key from environment"""
        if Fernet is None:
            return None

        key_env = os.environ.get("CONFIG_ENCRYPTION_KEY")
        if key_env:
            try:
                return base64.urlsafe_b64decode(key_env.encode())
            except Exception:
                logging.warning("Invalid CONFIG_ENCRYPTION_KEY format")

        return None

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if not self.config_path.exists():
            return {}

        # Check if file was modified since last cache
        current_mtime = self.config_path.stat().st_mtime
        if self._config_cache and current_mtime == self._last_modified:
            return self._config_cache

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)

            self._config_cache = config
            self._last_modified = current_mtime
            return config

        except Exception as e:
            logging.error(f"Failed to load config: {e}")
            return {}

    def get_value(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation"""
        config = self._load_config()

        keys = key_path.split(".")
        value = config

        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

    def get_encrypted_value(self, key_path: str, default: Any = None) -> Any:
        """Get and decrypt configuration value"""
        if not self.fernet:
            logging.warning("No encryption key available for encrypted values")
            return default

        encrypted_value = self.get_value(f"encrypted.{key_path}")
        if not encrypted_value:
            return default

        try:
            decrypted_bytes = self.fernet.decrypt(encrypted_value.encode())
            return decrypted_bytes.decode()
        except Exception as e:
            logging.error(f"Failed to decrypt config value {key_path}: {e}")
            return default

    def validate_config(self) -> List[str]:
        """Validate configuration and return list of errors"""
        config = self._load_config()
        errors = []

        # Required sections
        required_sections = ["system", "database", "apis", "google"]
        for section in required_sections:
            if section not in config:
                errors.append(f"Missing required section: {section}")

        # Validate Google API configuration
        if "google" in config:
            google_config = config["google"]
            if "credentials_file" not in google_config:
                errors.append("Missing google.credentials_file")
            if "scopes" not in google_config:
                errors.append("Missing google.scopes")

        # Validate database configuration
        if "database" in config:
            db_config = config["database"]
            if "path" not in db_config:
                errors.append("Missing database.path")

        return errors


class DatabaseSecurity:
    """Database security utilities"""

    def __init__(self, db_connection):
        self.conn = db_connection
        self.logger = logging.getLogger(__name__)

    def safe_execute(self, query: str, parameters: tuple = ()) -> sqlite3.Cursor:
        """Execute SQL query safely with parameterized statements"""
        try:
            cursor = self.conn.execute(query, parameters)
            return cursor
        except sqlite3.Error as e:
            self.logger.error(f"Database error: {e}")
            self.conn.rollback()
            raise SecurityError(f"Database operation failed: {e}")

    def validate_work_data(self, title: str, work_type: str, official_url: str = None) -> bool:
        """Validate work data before database operations"""
        try:
            # Validate title
            if not title or len(title) > 500:
                return False

            # Validate work type
            if work_type not in ["anime", "manga"]:
                return False

            # Validate URL if provided
            if official_url and not InputSanitizer.validate_url(official_url):
                return False

            return True

        except Exception:
            return False

    def hash_identifier(self, data: str) -> str:
        """Create secure hash for identifiers"""
        return hashlib.sha256(data.encode("utf-8")).hexdigest()


class SecurityMonitor:
    """Security monitoring and incident detection"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.incident_counter = defaultdict(int)
        self.last_incident_time = defaultdict(float)
        self.security_events = []

    def log_security_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """Log security event for monitoring"""
        event = {
            "timestamp": time.time(),
            "event_type": event_type,
            "details": details,
            "severity": self._get_event_severity(event_type),
        }

        self.security_events.append(event)
        self.logger.warning(f"SECURITY_EVENT: {event_type} - {json.dumps(details)}")

        # Keep only last 1000 events
        if len(self.security_events) > 1000:
            self.security_events = self.security_events[-1000:]

    def check_rate_limit_violation(self, api_name: str, client_id: str = "default") -> None:
        """Monitor for rate limit violations"""
        key = f"rate_limit_{api_name}_{client_id}"
        current_time = time.time()

        self.incident_counter[key] += 1

        # Check for repeated violations
        if self.incident_counter[key] > 5:
            time_diff = current_time - self.last_incident_time.get(key, 0)
            if time_diff < 300:  # 5 minutes
                self.log_security_event(
                    "RATE_LIMIT_ABUSE",
                    {
                        "api_name": api_name,
                        "client_id": client_id,
                        "violation_count": self.incident_counter[key],
                        "time_window": time_diff,
                    },
                )

        self.last_incident_time[key] = current_time

    def check_authentication_failure(self, service: str, error_details: str) -> None:
        """Monitor authentication failures"""
        self.log_security_event(
            "AUTH_FAILURE",
            {"service": service, "error": error_details, "timestamp": time.time()},
        )

    def check_input_validation_failure(self, input_type: str, reason: str) -> None:
        """Monitor input validation failures"""
        self.log_security_event(
            "INPUT_VALIDATION_FAILURE",
            {"input_type": input_type, "reason": reason, "timestamp": time.time()},
        )

    def _get_event_severity(self, event_type: str) -> str:
        """Determine severity level for security event"""
        high_severity = ["AUTH_FAILURE", "TOKEN_THEFT", "SQL_INJECTION"]
        medium_severity = ["RATE_LIMIT_ABUSE", "INPUT_VALIDATION_FAILURE"]

        if event_type in high_severity:
            return "HIGH"
        elif event_type in medium_severity:
            return "MEDIUM"
        else:
            return "LOW"

    def get_security_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get security event summary for specified time period"""
        cutoff_time = time.time() - (hours * 3600)
        recent_events = [
            event for event in self.security_events if event["timestamp"] > cutoff_time
        ]

        event_types = defaultdict(int)
        severity_counts = defaultdict(int)

        for event in recent_events:
            event_types[event["event_type"]] += 1
            severity_counts[event["severity"]] += 1

        return {
            "total_events": len(recent_events),
            "event_types": dict(event_types),
            "severity_counts": dict(severity_counts),
            "time_period_hours": hours,
        }


# Global instances
_rate_limiter = RateLimiter()
_security_monitor = SecurityMonitor(logging.getLogger(__name__))


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance"""
    return _rate_limiter


def get_security_monitor() -> SecurityMonitor:
    """Get global security monitor instance"""
    return _security_monitor
