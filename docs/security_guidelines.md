# Security Guidelines - Anime/Manga Information Delivery System

## Table of Contents
1. [OAuth2 Token Management](#oauth2-token-management)
2. [API Key Security](#api-key-security)
3. [Input Validation and Sanitization](#input-validation-and-sanitization)
4. [SQL Injection Prevention](#sql-injection-prevention)
5. [Rate Limiting and API Abuse Prevention](#rate-limiting-and-api-abuse-prevention)
6. [Secure Configuration Management](#secure-configuration-management)
7. [Data Protection and Privacy](#data-protection-and-privacy)
8. [Network Security](#network-security)
9. [Logging Security](#logging-security)
10. [Incident Response](#incident-response)

## 1. OAuth2 Token Management

### 1.1 Token Storage Security
- **CRITICAL**: Store OAuth2 tokens in encrypted format
- Use system keyring when available, fallback to encrypted file storage
- Set restrictive file permissions (600) on token files
- Never commit token files to version control

```python
# Secure token storage implementation
import os
import json
import base64
from cryptography.fernet import Fernet
from pathlib import Path

class SecureTokenManager:
    def __init__(self, token_file_path: str, encryption_key: bytes = None):
        self.token_file = Path(token_file_path)
        self.encryption_key = encryption_key or self._get_or_create_key()
        self.fernet = Fernet(self.encryption_key)
    
    def save_token(self, token_data: dict) -> None:
        encrypted_data = self.fernet.encrypt(json.dumps(token_data).encode())
        self.token_file.write_bytes(encrypted_data)
        os.chmod(self.token_file, 0o600)
    
    def load_token(self) -> dict:
        if not self.token_file.exists():
            return {}
        encrypted_data = self.token_file.read_bytes()
        decrypted_data = self.fernet.decrypt(encrypted_data)
        return json.loads(decrypted_data.decode())
```

### 1.2 Token Refresh Management
- Implement automatic token refresh before expiration
- Use refresh tokens securely with proper rotation
- Log token refresh events for monitoring
- Implement retry logic with exponential backoff

### 1.3 OAuth2 Scope Limitation
- Request minimal required scopes:
  - `https://www.googleapis.com/auth/gmail.send` (not gmail.readonly)
  - `https://www.googleapis.com/auth/calendar.events` (not calendar.readonly)
- Regularly audit and review granted permissions

## 2. API Key Security

### 2.1 AniList GraphQL API
- Store API credentials in environment variables or encrypted config
- Implement request signing for sensitive operations
- Use HTTPS only for all API communications
- Validate API responses before processing

### 2.2 API Key Rotation
- Implement regular API key rotation schedule
- Support multiple API keys with fallback mechanisms
- Monitor API key usage and detect anomalies
- Secure key distribution in multi-environment setups

```python
# API key management example
class APIKeyManager:
    def __init__(self, config_manager):
        self.config = config_manager
        self.active_keys = {}
    
    def get_api_key(self, service: str) -> str:
        key = os.environ.get(f"{service.upper()}_API_KEY")
        if not key:
            key = self.config.get_encrypted_value(f"api_keys.{service}")
        if not key:
            raise SecurityError(f"API key not found for service: {service}")
        return key
    
    def rotate_key(self, service: str, new_key: str) -> None:
        # Validate new key before rotation
        if self._validate_key(service, new_key):
            old_key = self.active_keys.get(service)
            self.active_keys[service] = new_key
            self.config.set_encrypted_value(f"api_keys.{service}", new_key)
            if old_key:
                self._revoke_key(service, old_key)
```

## 3. Input Validation and Sanitization

### 3.1 RSS Feed Validation
- Validate XML/RSS structure before parsing
- Sanitize HTML content from feed descriptions
- Limit feed size to prevent DoS attacks
- Validate URLs and domains against allowlists

```python
import bleach
import validators
from urllib.parse import urlparse

class InputSanitizer:
    ALLOWED_HTML_TAGS = ['p', 'br', 'strong', 'em', 'ul', 'ol', 'li']
    ALLOWED_ATTRIBUTES = {}
    MAX_FEED_SIZE = 5 * 1024 * 1024  # 5MB
    
    @staticmethod
    def sanitize_html_content(content: str) -> str:
        """Remove potentially dangerous HTML tags and attributes"""
        return bleach.clean(
            content, 
            tags=InputSanitizer.ALLOWED_HTML_TAGS,
            attributes=InputSanitizer.ALLOWED_ATTRIBUTES,
            strip=True
        )
    
    @staticmethod
    def validate_url(url: str, allowed_domains: list = None) -> bool:
        """Validate URL format and optionally check against allowlist"""
        if not validators.url(url):
            return False
        
        parsed = urlparse(url)
        if parsed.scheme not in ['https', 'http']:
            return False
            
        if allowed_domains:
            return parsed.netloc.lower() in [d.lower() for d in allowed_domains]
        
        return True
    
    @staticmethod
    def sanitize_anime_title(title: str) -> str:
        """Sanitize anime/manga titles for safe storage and display"""
        if not title or len(title) > 500:
            raise ValueError("Invalid title length")
        
        # Remove control characters and normalize unicode
        import unicodedata
        title = unicodedata.normalize('NFKC', title)
        title = ''.join(char for char in title if unicodedata.category(char)[0] != 'C')
        
        return title.strip()
```

### 3.2 Content Filtering
- Implement multi-layer NGword filtering
- Use both exact match and fuzzy matching
- Support regex patterns for advanced filtering
- Log filtered content for review

## 4. SQL Injection Prevention

### 4.1 Parameterized Queries
- Always use parameterized queries or ORM
- Never concatenate user input into SQL strings
- Validate input types before database operations
- Use database-specific escaping functions

```python
class DatabaseSecurity:
    def __init__(self, db_connection):
        self.conn = db_connection
    
    def safe_insert_work(self, title: str, title_kana: str, work_type: str, official_url: str):
        """Safely insert work data using parameterized queries"""
        # Input validation
        if not self._validate_work_data(title, work_type, official_url):
            raise ValueError("Invalid work data")
        
        query = """
        INSERT INTO works (title, title_kana, type, official_url)
        VALUES (?, ?, ?, ?)
        """
        
        try:
            self.conn.execute(query, (title, title_kana, work_type, official_url))
            self.conn.commit()
        except sqlite3.Error as e:
            self.conn.rollback()
            raise DatabaseSecurityError(f"Failed to insert work: {e}")
    
    def _validate_work_data(self, title: str, work_type: str, official_url: str) -> bool:
        """Validate work data before database insertion"""
        if not title or len(title) > 500:
            return False
        if work_type not in ['anime', 'manga']:
            return False
        if official_url and not validators.url(official_url):
            return False
        return True
```

### 4.2 Database Access Controls
- Use least privilege database user accounts
- Implement connection pooling with security controls
- Regular database security audits
- Encrypt sensitive data at rest

## 5. Rate Limiting and API Abuse Prevention

### 5.1 API Rate Limiting Implementation
```python
import time
from collections import defaultdict
from threading import Lock

class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)
        self.lock = Lock()
    
    def is_allowed(self, api_name: str, limit_per_minute: int) -> bool:
        """Check if API request is allowed under rate limit"""
        current_time = time.time()
        
        with self.lock:
            # Clean old requests
            cutoff_time = current_time - 60  # 1 minute ago
            self.requests[api_name] = [
                req_time for req_time in self.requests[api_name] 
                if req_time > cutoff_time
            ]
            
            # Check if under limit
            if len(self.requests[api_name]) < limit_per_minute:
                self.requests[api_name].append(current_time)
                return True
            
            return False
    
    def get_wait_time(self, api_name: str, limit_per_minute: int) -> float:
        """Get seconds to wait before next request"""
        if not self.requests[api_name]:
            return 0
        
        oldest_request = min(self.requests[api_name])
        wait_time = 60 - (time.time() - oldest_request)
        return max(0, wait_time)
```

### 5.2 Distributed Rate Limiting
- Use Redis for distributed rate limiting across multiple instances
- Implement sliding window rate limiting
- Add jitter to prevent thundering herd problems

## 6. Secure Configuration Management

### 6.1 Configuration Security
```python
import os
import json
from cryptography.fernet import Fernet
from typing import Any, Dict

class SecureConfig:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.encryption_key = self._get_encryption_key()
        self.fernet = Fernet(self.encryption_key)
        self._config_cache = None
    
    def _get_encryption_key(self) -> bytes:
        """Get encryption key from environment or generate new one"""
        key = os.environ.get('CONFIG_ENCRYPTION_KEY')
        if key:
            return base64.urlsafe_b64decode(key.encode())
        
        # Generate new key for first run
        new_key = Fernet.generate_key()
        print(f"Generated new config encryption key: {base64.urlsafe_b64encode(new_key).decode()}")
        print("Please set CONFIG_ENCRYPTION_KEY environment variable with this value")
        return new_key
    
    def get_value(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'database.path')"""
        config = self._load_config()
        
        keys = key_path.split('.')
        value = config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_encrypted_value(self, key_path: str, default: Any = None) -> Any:
        """Get encrypted configuration value"""
        encrypted_value = self.get_value(f"encrypted.{key_path}", default)
        if encrypted_value and encrypted_value != default:
            try:
                decrypted_bytes = self.fernet.decrypt(encrypted_value.encode())
                return decrypted_bytes.decode()
            except Exception:
                return default
        return default
    
    def set_encrypted_value(self, key_path: str, value: str) -> None:
        """Set encrypted configuration value"""
        encrypted_value = self.fernet.encrypt(value.encode()).decode()
        config = self._load_config()
        
        if 'encrypted' not in config:
            config['encrypted'] = {}
        
        keys = key_path.split('.')
        target = config['encrypted']
        
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]
        
        target[keys[-1]] = encrypted_value
        self._save_config(config)
```

### 6.2 Environment-Specific Configuration
- Use different configurations for development, testing, and production
- Validate configuration on startup
- Support configuration reloading without restart
- Audit configuration changes

## 7. Data Protection and Privacy

### 7.1 Personal Data Handling
- Minimize collection of personal data
- Implement data retention policies
- Provide data export capabilities
- Support user data deletion requests

### 7.2 Data Encryption
- Encrypt sensitive data at rest
- Use TLS 1.2+ for all network communications
- Implement proper key management
- Regular encryption key rotation

## 8. Network Security

### 8.1 HTTPS Enforcement
```python
import requests
import ssl
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class SecureHTTPSession:
    def __init__(self):
        self.session = requests.Session()
        self._setup_security()
    
    def _setup_security(self):
        """Configure secure HTTP session"""
        # Force HTTPS
        self.session.hooks = {
            'response': lambda r, *args, **kwargs: self._verify_https(r)
        }
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        
        # Set security headers
        self.session.headers.update({
            'User-Agent': 'MangaAnimeNotifier/1.0 (Security Enhanced)',
            'Accept': 'application/json, application/xml, text/xml',
            'Accept-Encoding': 'gzip, deflate',
        })
    
    def _verify_https(self, response):
        """Verify response came over HTTPS"""
        if not response.url.startswith('https://'):
            raise SecurityError(f"Non-HTTPS response: {response.url}")
        return response
```

### 8.2 Certificate Validation
- Always validate SSL certificates
- Implement certificate pinning for critical APIs
- Monitor certificate expiration dates
- Use certificate transparency logs

## 9. Logging Security

### 9.1 Secure Logging Practices
```python
import logging
import hashlib
import re
from logging.handlers import RotatingFileHandler

class SecureLogger:
    SENSITIVE_PATTERNS = [
        r'token["\s]*[:=]["\s]*([^"\s]+)',
        r'password["\s]*[:=]["\s]*([^"\s]+)',
        r'api[_-]?key["\s]*[:=]["\s]*([^"\s]+)',
        r'secret["\s]*[:=]["\s]*([^"\s]+)',
    ]
    
    def __init__(self, name: str, log_file: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Setup secure file handler
        handler = RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5
        )
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def _sanitize_message(self, message: str) -> str:
        """Remove sensitive information from log messages"""
        for pattern in self.SENSITIVE_PATTERNS:
            message = re.sub(
                pattern, 
                lambda m: f"{m.group(0).split('=')[0]}=***REDACTED***",
                message,
                flags=re.IGNORECASE
            )
        return message
    
    def info(self, message: str, **kwargs):
        """Log info message with sanitization"""
        sanitized = self._sanitize_message(str(message))
        self.logger.info(sanitized, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message with sanitization"""
        sanitized = self._sanitize_message(str(message))
        self.logger.error(sanitized, **kwargs)
```

### 9.2 Audit Logging
- Log all authentication events
- Log configuration changes
- Log data access patterns
- Implement log integrity protection

## 10. Incident Response

### 10.1 Security Incident Detection
```python
class SecurityMonitor:
    def __init__(self, logger):
        self.logger = logger
        self.incident_counter = defaultdict(int)
        self.last_incident_time = defaultdict(float)
    
    def check_rate_limit_violation(self, api_name: str, client_id: str):
        """Monitor for rate limit violations"""
        key = f"{api_name}_{client_id}"
        current_time = time.time()
        
        self.incident_counter[key] += 1
        
        # Check for repeated violations
        if self.incident_counter[key] > 10:
            if current_time - self.last_incident_time[key] < 300:  # 5 minutes
                self._trigger_security_alert(
                    "RATE_LIMIT_ABUSE",
                    f"Repeated rate limit violations from {client_id} on {api_name}"
                )
        
        self.last_incident_time[key] = current_time
    
    def check_authentication_failure(self, service: str, error_details: str):
        """Monitor for authentication failures"""
        self._trigger_security_alert(
            "AUTH_FAILURE",
            f"Authentication failure for {service}: {error_details}"
        )
    
    def _trigger_security_alert(self, incident_type: str, details: str):
        """Trigger security incident response"""
        alert_message = {
            'timestamp': time.time(),
            'incident_type': incident_type,
            'details': details,
            'severity': 'HIGH' if incident_type in ['AUTH_FAILURE', 'TOKEN_THEFT'] else 'MEDIUM'
        }
        
        self.logger.error(f"SECURITY_INCIDENT: {json.dumps(alert_message)}")
        
        # Additional alerting (email, webhook, etc.)
        self._send_incident_notification(alert_message)
```

### 10.2 Incident Response Procedures
1. **Immediate Response (0-15 minutes)**
   - Disable compromised API keys
   - Revoke OAuth2 tokens if necessary
   - Block suspicious IP addresses
   - Document incident timeline

2. **Investigation (15 minutes - 2 hours)**
   - Analyze logs for attack patterns
   - Assess data exposure risk
   - Identify affected systems
   - Gather forensic evidence

3. **Recovery (2-24 hours)**
   - Rotate all potentially compromised credentials
   - Apply security patches
   - Update monitoring rules
   - Restore normal operations

4. **Post-Incident (24-72 hours)**
   - Conduct lessons learned review
   - Update security procedures
   - Enhance monitoring capabilities
   - Document incident report

## Implementation Checklist

- [ ] Implement secure token management with encryption
- [ ] Deploy API rate limiting and monitoring
- [ ] Setup input validation and sanitization
- [ ] Configure secure database access
- [ ] Implement comprehensive logging
- [ ] Setup security monitoring and alerting
- [ ] Create incident response procedures
- [ ] Conduct security testing and validation
- [ ] Regular security audits and reviews
- [ ] Staff security training and awareness

## Security Contacts

- **Security Team Lead**: [Contact Information]
- **Incident Response**: [24/7 Contact]
- **Compliance Officer**: [Contact Information]

---

**Document Version**: 1.0  
**Last Updated**: 2025-01-08  
**Review Schedule**: Monthly  
**Classification**: Internal Use