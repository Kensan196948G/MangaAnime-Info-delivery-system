# Refactoring Roadmap
**MangaAnime Information Delivery System**

Generated: 2025-12-06
Priority-Based Technical Improvement Plan

---

## Executive Summary

This roadmap outlines a phased approach to address technical debt and improve system architecture based on the comprehensive analysis documented in SYSTEM_ARCHITECTURE_ANALYSIS.md.

**Total Estimated Effort:** 8-10 weeks (1 developer)
**Expected Impact:** 30-40% code reduction, 50% better maintainability, 25% performance improvement

---

## Phase 1: Foundation Cleanup (Week 1-2)

### Priority: CRITICAL
**Goal:** Eliminate code duplication and standardize patterns

### Task 1.1: Merge Enhanced Modules

**Files to Consolidate:**
1. `filter_logic.py` + `filter_logic_enhanced.py` → `filter_logic.py`
2. `data_normalizer.py` + `data_normalizer_enhanced.py` → `data_normalizer.py`
3. `error_recovery.py` + `enhanced_error_recovery.py` → `error_recovery.py`
4. `manga_rss.py` + `manga_rss_enhanced.py` → `manga_rss.py`
5. `anime_rss_enhanced.py` → Integrate into `anime_anilist.py` or create unified `anime_rss.py`

**Implementation Strategy:**

```python
# Example: Merge filter_logic modules

# Step 1: Add feature flags to filter_logic.py
class ContentFilter:
    def __init__(self, config, enable_fuzzy=True, enable_ml=False):
        self.config = config
        self.enable_fuzzy = enable_fuzzy
        self.enable_ml = enable_ml

        # Load base features (always enabled)
        self.ng_keywords = self._load_ng_keywords()

        # Load optional features based on flags
        if self.enable_fuzzy:
            from difflib import SequenceMatcher
            self.fuzzy_matcher = SequenceMatcher()

        if self.enable_ml:
            # Lazy import ML dependencies
            try:
                import sklearn
                self.ml_classifier = self._load_ml_model()
            except ImportError:
                logger.warning("ML dependencies not available, disabling ML features")
                self.enable_ml = False

    def should_filter(self, item):
        # Base filtering (always run)
        if self._basic_keyword_match(item):
            return True

        # Fuzzy matching (optional)
        if self.enable_fuzzy and self._fuzzy_keyword_match(item):
            return True

        # ML classification (optional)
        if self.enable_ml and self._ml_classify(item):
            return True

        return False
```

**Benefits:**
- Single source of truth
- Reduced codebase by ~3,000 lines
- Feature flags allow gradual rollout
- Easier testing and maintenance

**Estimated Effort:** 2 days

---

### Task 1.2: Standardize Error Handling

**Goal:** Implement consistent error handling pattern across all modules

**Current Problems:**
- 5 different error handling patterns
- Inconsistent logging
- Missing retry logic in some modules
- No centralized error reporting

**Solution: Decorator-Based Error Handling**

```python
# modules/error_recovery.py (enhanced)

from functools import wraps
import time
import logging
from typing import Callable, Optional, Any
from dataclasses import dataclass

@dataclass
class ErrorHandlingConfig:
    retry_attempts: int = 3
    retry_delay: float = 1.0
    exponential_backoff: bool = True
    fallback_value: Optional[Any] = None
    alert_on_failure: bool = False
    retry_on_exceptions: tuple = (Exception,)
    skip_retry_on: tuple = (ValueError, TypeError)

def handle_errors(config: ErrorHandlingConfig = None):
    """
    Standardized error handling decorator.

    Usage:
        @handle_errors(ErrorHandlingConfig(
            retry_attempts=3,
            fallback_value=[],
            alert_on_failure=True
        ))
        def collect_data():
            return api.fetch()
    """
    if config is None:
        config = ErrorHandlingConfig()

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__module__)
            last_exception = None
            current_delay = config.retry_delay

            for attempt in range(config.retry_attempts + 1):
                try:
                    result = func(*args, **kwargs)
                    # Log success after retry
                    if attempt > 0:
                        logger.info(
                            f"{func.__name__} succeeded after {attempt} retries"
                        )
                    return result

                except config.skip_retry_on as e:
                    # Don't retry on specific exceptions
                    logger.error(
                        f"{func.__name__} failed with non-retryable error: {e}"
                    )
                    raise

                except config.retry_on_exceptions as e:
                    last_exception = e

                    # Last attempt failed
                    if attempt == config.retry_attempts:
                        logger.error(
                            f"{func.__name__} failed after {config.retry_attempts} retries: {e}"
                        )

                        # Send alert if configured
                        if config.alert_on_failure:
                            _send_error_alert(func.__name__, e)

                        # Return fallback value or raise
                        if config.fallback_value is not None:
                            return config.fallback_value
                        raise

                    # Log retry attempt
                    logger.warning(
                        f"{func.__name__} attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {current_delay:.1f}s..."
                    )

                    time.sleep(current_delay)

                    # Exponential backoff
                    if config.exponential_backoff:
                        current_delay *= 2

            # Should never reach here
            raise last_exception

        return wrapper
    return decorator


# Example usage across modules:

# In anime_anilist.py:
@handle_errors(ErrorHandlingConfig(
    retry_attempts=3,
    fallback_value=[],
    alert_on_failure=True,
    retry_on_exceptions=(aiohttp.ClientError, asyncio.TimeoutError)
))
async def collect_anime_data(self):
    return await self._fetch_from_anilist()

# In mailer.py:
@handle_errors(ErrorHandlingConfig(
    retry_attempts=5,
    retry_delay=2.0,
    alert_on_failure=True,
    skip_retry_on=(ValueError,)  # Don't retry on invalid data
))
def send_email(self, notification):
    return self._send_via_gmail_api(notification)

# In db.py:
@handle_errors(ErrorHandlingConfig(
    retry_attempts=3,
    retry_delay=0.5,
    fallback_value=None,
    retry_on_exceptions=(sqlite3.OperationalError,)
))
def execute_query(self, query, params):
    with self.get_connection() as conn:
        return conn.execute(query, params)
```

**Migration Plan:**

1. Week 1: Implement enhanced error_recovery.py
2. Week 1: Migrate core modules (db, config, logger)
3. Week 2: Migrate collection modules
4. Week 2: Migrate notification modules

**Estimated Effort:** 3 days

---

### Task 1.3: Consolidate Mailer Implementations

**Goal:** Unified email service with automatic fallback

**Current State:**
- `mailer.py` - Gmail API
- `smtp_mailer.py` - SMTP
- `email_sender.py` - Email composition
- Unclear which to use
- No automatic fallback

**Proposed Structure:**

```python
# modules/email_service.py (new unified module)

from typing import Protocol, Optional
from dataclasses import dataclass
from enum import Enum

class EmailBackend(Enum):
    GMAIL_API = "gmail_api"
    SMTP = "smtp"

class EmailProvider(Protocol):
    """Email provider interface"""

    def authenticate(self) -> bool:
        """Authenticate with email service"""
        ...

    def send(self, notification: EmailNotification) -> bool:
        """Send email notification"""
        ...

    def is_available(self) -> bool:
        """Check if provider is available"""
        ...


class GmailAPIProvider(EmailProvider):
    """Gmail API implementation (from mailer.py)"""

    def __init__(self, config):
        self.config = config
        self.service = None

    def authenticate(self) -> bool:
        # OAuth2 authentication
        pass

    def send(self, notification: EmailNotification) -> bool:
        # Send via Gmail API
        pass

    def is_available(self) -> bool:
        return self.service is not None


class SMTPProvider(EmailProvider):
    """SMTP implementation (from smtp_mailer.py)"""

    def __init__(self, config):
        self.config = config
        self.smtp_server = None

    def authenticate(self) -> bool:
        # SMTP authentication
        pass

    def send(self, notification: EmailNotification) -> bool:
        # Send via SMTP
        pass

    def is_available(self) -> bool:
        return self.smtp_server is not None


class EmailService:
    """
    Unified email service with automatic fallback.

    Tries Gmail API first, falls back to SMTP if needed.
    """

    def __init__(self, config, preferred_backend=EmailBackend.GMAIL_API):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Initialize providers
        self.providers = {
            EmailBackend.GMAIL_API: GmailAPIProvider(config),
            EmailBackend.SMTP: SMTPProvider(config),
        }

        # Set primary and fallback
        self.primary = self.providers[preferred_backend]
        self.fallback = (
            self.providers[EmailBackend.SMTP]
            if preferred_backend == EmailBackend.GMAIL_API
            else self.providers[EmailBackend.GMAIL_API]
        )

        # Authenticate on initialization
        self._authenticate_providers()

    def _authenticate_providers(self):
        """Authenticate all available providers"""
        for backend, provider in self.providers.items():
            try:
                if provider.authenticate():
                    self.logger.info(f"{backend.value} authenticated successfully")
                else:
                    self.logger.warning(f"{backend.value} authentication failed")
            except Exception as e:
                self.logger.error(f"{backend.value} authentication error: {e}")

    def send(self, notification: EmailNotification) -> bool:
        """
        Send email with automatic fallback.

        Tries primary provider first, falls back to secondary if needed.
        """
        # Try primary provider
        if self.primary.is_available():
            try:
                if self.primary.send(notification):
                    self.logger.info("Email sent via primary provider")
                    return True
                else:
                    self.logger.warning("Primary provider send failed")
            except Exception as e:
                self.logger.error(f"Primary provider error: {e}")

        # Try fallback provider
        if self.fallback.is_available():
            try:
                self.logger.info("Attempting fallback provider...")
                if self.fallback.send(notification):
                    self.logger.info("Email sent via fallback provider")
                    return True
            except Exception as e:
                self.logger.error(f"Fallback provider error: {e}")

        # All providers failed
        self.logger.error("All email providers failed")
        return False

    def send_batch(self, notifications: List[EmailNotification]) -> Dict[str, Any]:
        """Send multiple emails with progress tracking"""
        results = {
            "total": len(notifications),
            "sent": 0,
            "failed": 0,
            "errors": []
        }

        for i, notification in enumerate(notifications):
            try:
                if self.send(notification):
                    results["sent"] += 1
                else:
                    results["failed"] += 1
                    results["errors"].append({
                        "index": i,
                        "subject": notification.subject,
                        "error": "Send failed"
                    })
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "index": i,
                    "subject": notification.subject,
                    "error": str(e)
                })

        return results
```

**Migration:**
1. Create `email_service.py` with unified interface
2. Refactor `mailer.py` to `GmailAPIProvider`
3. Refactor `smtp_mailer.py` to `SMTPProvider`
4. Update `release_notifier.py` to use `EmailService`
5. Deprecate old modules

**Estimated Effort:** 2 days

---

## Phase 2: Configuration & Testing (Week 3-4)

### Priority: HIGH

### Task 2.1: Centralize Configuration

**Goal:** Single source of truth for all configuration

**Current Problems:**
- Configuration scattered (config.json, .env, hardcoded values)
- No validation
- Difficult to override for testing
- Missing documentation

**Solution: Enhanced Configuration System**

```python
# modules/config_enhanced.py

from typing import Any, Dict, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path
import json
import os
from enum import Enum

class ConfigSource(Enum):
    FILE = "file"
    ENV = "env"
    DEFAULT = "default"
    OVERRIDE = "override"

@dataclass
class ConfigValue:
    """Configuration value with metadata"""
    value: Any
    source: ConfigSource
    description: str = ""
    required: bool = False
    validator: Optional[callable] = None

class ConfigurationManager:
    """
    Enhanced configuration manager with:
    - Environment variable override
    - Validation
    - Type conversion
    - Documentation
    """

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path or "config.json")
        self._config: Dict[str, ConfigValue] = {}
        self._load_defaults()
        self._load_from_file()
        self._load_from_env()
        self._validate()

    def _load_defaults(self):
        """Load default configuration values"""
        defaults = {
            # API Configuration
            "api.anilist.rate_limit": ConfigValue(
                value=90,
                source=ConfigSource.DEFAULT,
                description="AniList API rate limit (requests per minute)",
                required=True
            ),
            "api.anilist.timeout": ConfigValue(
                value=30,
                source=ConfigSource.DEFAULT,
                description="AniList API timeout (seconds)"
            ),

            # Database Configuration
            "database.path": ConfigValue(
                value="./db.sqlite3",
                source=ConfigSource.DEFAULT,
                description="Database file path",
                required=True
            ),
            "database.connection_pool.max_connections": ConfigValue(
                value=5,
                source=ConfigSource.DEFAULT,
                description="Maximum database connections"
            ),
            "database.performance.slow_query_threshold": ConfigValue(
                value=1.0,
                source=ConfigSource.DEFAULT,
                description="Slow query threshold (seconds)"
            ),

            # Email Configuration
            "email.retry.max_attempts": ConfigValue(
                value=3,
                source=ConfigSource.DEFAULT,
                description="Maximum email retry attempts"
            ),
            "email.retry.delay_seconds": ConfigValue(
                value=5,
                source=ConfigSource.DEFAULT,
                description="Delay between email retries"
            ),

            # Filtering Configuration
            "filter.enable_fuzzy": ConfigValue(
                value=True,
                source=ConfigSource.DEFAULT,
                description="Enable fuzzy keyword matching"
            ),
            "filter.similarity_threshold": ConfigValue(
                value=0.8,
                source=ConfigSource.DEFAULT,
                description="Fuzzy match similarity threshold (0.0-1.0)",
                validator=lambda v: 0.0 <= v <= 1.0
            ),
        }

        self._config.update(defaults)

    def _load_from_file(self):
        """Load configuration from JSON file"""
        if not self.config_path.exists():
            return

        with open(self.config_path) as f:
            file_config = json.load(f)

        # Flatten nested config
        flattened = self._flatten_dict(file_config)

        for key, value in flattened.items():
            if key in self._config:
                self._config[key].value = value
                self._config[key].source = ConfigSource.FILE
            else:
                self._config[key] = ConfigValue(
                    value=value,
                    source=ConfigSource.FILE
                )

    def _load_from_env(self):
        """Load configuration from environment variables"""
        # Map environment variables to config keys
        env_mapping = {
            "ANILIST_RATE_LIMIT": "api.anilist.rate_limit",
            "DATABASE_PATH": "database.path",
            "MAX_DB_CONNECTIONS": "database.connection_pool.max_connections",
            "EMAIL_MAX_RETRIES": "email.retry.max_attempts",
            "ENABLE_FUZZY_FILTER": "filter.enable_fuzzy",
        }

        for env_var, config_key in env_mapping.items():
            value = os.getenv(env_var)
            if value is not None and config_key in self._config:
                # Type conversion
                original_type = type(self._config[config_key].value)
                if original_type == bool:
                    converted = value.lower() in ("true", "1", "yes")
                elif original_type == int:
                    converted = int(value)
                elif original_type == float:
                    converted = float(value)
                else:
                    converted = value

                self._config[config_key].value = converted
                self._config[config_key].source = ConfigSource.ENV

    def _flatten_dict(self, d: dict, parent_key: str = "") -> dict:
        """Flatten nested dictionary with dot notation"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}.{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def _validate(self):
        """Validate configuration"""
        errors = []

        for key, config_value in self._config.items():
            # Check required values
            if config_value.required and config_value.value is None:
                errors.append(f"Required configuration missing: {key}")

            # Run validator if present
            if config_value.validator and config_value.value is not None:
                try:
                    if not config_value.validator(config_value.value):
                        errors.append(
                            f"Validation failed for {key}: {config_value.value}"
                        )
                except Exception as e:
                    errors.append(f"Validator error for {key}: {e}")

        if errors:
            raise ValueError(f"Configuration validation failed:\n" + "\n".join(errors))

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        if key in self._config:
            return self._config[key].value
        return default

    def set(self, key: str, value: Any, source: ConfigSource = ConfigSource.OVERRIDE):
        """Set configuration value (runtime override)"""
        if key in self._config:
            self._config[key].value = value
            self._config[key].source = source
        else:
            self._config[key] = ConfigValue(
                value=value,
                source=source
            )

    def get_documentation(self) -> Dict[str, str]:
        """Get configuration documentation"""
        docs = {}
        for key, config_value in self._config.items():
            docs[key] = {
                "description": config_value.description,
                "default": config_value.value,
                "source": config_value.source.value,
                "required": config_value.required
            }
        return docs

    def export_template(self, output_path: str):
        """Export configuration template with documentation"""
        template = {
            "_metadata": {
                "description": "Configuration file for MangaAnime Information Delivery System",
                "version": "1.0.0"
            }
        }

        for key, config_value in self._config.items():
            parts = key.split(".")
            current = template
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]

            current[f"_{parts[-1]}_description"] = config_value.description
            current[parts[-1]] = config_value.value

        with open(output_path, "w") as f:
            json.dump(template, f, indent=2)
```

**Estimated Effort:** 2 days

---

### Task 2.2: Comprehensive Test Suite

**Goal:** 75% code coverage with unit + integration tests

**Test Structure:**

```
tests/
├── unit/
│   ├── test_db.py                 # Database operations
│   ├── test_models.py             # Data models
│   ├── test_config.py             # Configuration
│   ├── test_filter_logic.py       # Filtering
│   ├── test_data_normalizer.py    # Normalization
│   ├── collectors/
│   │   ├── test_anilist.py
│   │   ├── test_kitsu.py
│   │   └── test_manga_rss.py
│   └── notification/
│       ├── test_email_service.py
│       └── test_calendar.py
├── integration/
│   ├── test_collection_pipeline.py
│   ├── test_notification_pipeline.py
│   └── test_web_ui.py
├── e2e/
│   └── test_full_system.py
├── fixtures/
│   ├── mock_api_responses.py
│   ├── sample_data.py
│   └── test_config.json
└── conftest.py                    # Shared fixtures
```

**Example Test Implementation:**

```python
# tests/unit/test_filter_logic.py

import pytest
from modules.filter_logic import ContentFilter, FilterResult
from modules.models import Work, WorkType
from modules.config import ConfigurationManager

@pytest.fixture
def config():
    """Test configuration"""
    config = ConfigurationManager()
    config.set("filter.ng_keywords", ["エロ", "R18"])
    config.set("filter.enable_fuzzy", True)
    config.set("filter.similarity_threshold", 0.8)
    return config

@pytest.fixture
def filter_service(config):
    """Content filter instance"""
    return ContentFilter(config)

class TestBasicFiltering:
    def test_exact_keyword_match(self, filter_service):
        work = Work(title="エロゲー", work_type=WorkType.ANIME)
        result = filter_service.filter_work(work)
        assert result.is_filtered is True
        assert "エロ" in result.matched_keywords

    def test_no_match(self, filter_service):
        work = Work(title="進撃の巨人", work_type=WorkType.ANIME)
        result = filter_service.filter_work(work)
        assert result.is_filtered is False

    def test_case_insensitive(self, filter_service):
        work = Work(title="R18ゲーム", work_type=WorkType.ANIME)
        result = filter_service.filter_work(work)
        assert result.is_filtered is True

class TestFuzzyMatching:
    def test_fuzzy_match(self, filter_service):
        work = Work(title="エロチック", work_type=WorkType.ANIME)
        result = filter_service.filter_work(work)
        # Should match "エロ" with fuzzy matching
        assert result.is_filtered is True

    def test_fuzzy_disabled(self, config):
        config.set("filter.enable_fuzzy", False)
        filter_service = ContentFilter(config)
        work = Work(title="エロチック", work_type=WorkType.ANIME)
        result = filter_service.filter_work(work)
        # Exact match only, should not filter
        assert result.is_filtered is False

class TestPerformance:
    def test_large_batch_filtering(self, filter_service, benchmark):
        """Test filtering performance with large dataset"""
        works = [
            Work(title=f"Title {i}", work_type=WorkType.ANIME)
            for i in range(1000)
        ]

        def filter_batch():
            return [filter_service.filter_work(w) for w in works]

        results = benchmark(filter_batch)
        assert len(results) == 1000

    def test_caching_effectiveness(self, filter_service):
        """Test that LRU cache improves performance"""
        work = Work(title="同じタイトル", work_type=WorkType.ANIME)

        # First call (cache miss)
        result1 = filter_service.filter_work(work)

        # Second call (cache hit)
        result2 = filter_service.filter_work(work)

        assert result1.is_filtered == result2.is_filtered
        # Check cache hit statistics
        assert filter_service.cache_hits > 0
```

**Test Coverage Tools:**

```bash
# Install coverage tools
pip install pytest pytest-cov pytest-benchmark

# Run tests with coverage
pytest --cov=modules --cov-report=html --cov-report=term

# Generate coverage report
coverage html
open htmlcov/index.html
```

**Estimated Effort:** 1 week

---

## Phase 3: Performance Optimization (Week 5-6)

### Priority: MEDIUM

### Task 3.1: Implement Caching Strategy

**Goal:** 30-50% performance improvement through intelligent caching

**Multi-Level Caching:**

```python
# modules/cache_manager.py

from typing import Any, Optional, Callable
from functools import lru_cache, wraps
from dataclasses import dataclass
from datetime import datetime, timedelta
import hashlib
import json
import logging

@dataclass
class CacheConfig:
    ttl_seconds: int = 3600  # 1 hour default
    max_size: int = 1000
    enable_compression: bool = False

class CacheManager:
    """
    Multi-level cache manager:
    1. In-memory LRU cache (fast, limited size)
    2. Redis cache (optional, persistent)
    3. Database cache (fallback)
    """

    def __init__(self, config: CacheConfig = None):
        self.config = config or CacheConfig()
        self.logger = logging.getLogger(__name__)
        self._memory_cache = {}
        self._cache_stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0
        }

        # Try to initialize Redis
        try:
            import redis
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=0,
                decode_responses=True
            )
            self.redis_available = self.redis_client.ping()
        except:
            self.redis_client = None
            self.redis_available = False
            self.logger.info("Redis not available, using memory cache only")

    def cached(self, ttl: int = None, key_prefix: str = ""):
        """
        Decorator for caching function results.

        Usage:
            @cache_manager.cached(ttl=3600, key_prefix="work_")
            def get_work_by_title(title):
                return db.query(...)
        """
        ttl = ttl or self.config.ttl_seconds

        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = self._generate_key(key_prefix, func.__name__, args, kwargs)

                # Try memory cache first
                cached_value = self._get_from_memory(cache_key)
                if cached_value is not None:
                    self._cache_stats["hits"] += 1
                    return cached_value

                # Try Redis cache
                if self.redis_available:
                    cached_value = self._get_from_redis(cache_key)
                    if cached_value is not None:
                        self._cache_stats["hits"] += 1
                        # Populate memory cache
                        self._set_in_memory(cache_key, cached_value, ttl)
                        return cached_value

                # Cache miss - execute function
                self._cache_stats["misses"] += 1
                result = func(*args, **kwargs)

                # Store in caches
                self._set_in_memory(cache_key, result, ttl)
                if self.redis_available:
                    self._set_in_redis(cache_key, result, ttl)

                return result

            return wrapper
        return decorator

    def _generate_key(self, prefix: str, func_name: str, args: tuple, kwargs: dict) -> str:
        """Generate unique cache key"""
        # Serialize arguments
        key_parts = [prefix, func_name]
        if args:
            key_parts.append(str(args))
        if kwargs:
            key_parts.append(json.dumps(kwargs, sort_keys=True))

        key_string = ":".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()

    def _get_from_memory(self, key: str) -> Optional[Any]:
        """Get value from memory cache"""
        if key in self._memory_cache:
            entry = self._memory_cache[key]
            if datetime.now() < entry["expires_at"]:
                return entry["value"]
            else:
                # Expired
                del self._memory_cache[key]
                self._cache_stats["evictions"] += 1
        return None

    def _set_in_memory(self, key: str, value: Any, ttl: int):
        """Set value in memory cache"""
        # Check size limit
        if len(self._memory_cache) >= self.config.max_size:
            # Evict oldest entry
            oldest_key = min(
                self._memory_cache.keys(),
                key=lambda k: self._memory_cache[k]["created_at"]
            )
            del self._memory_cache[oldest_key]
            self._cache_stats["evictions"] += 1

        self._memory_cache[key] = {
            "value": value,
            "created_at": datetime.now(),
            "expires_at": datetime.now() + timedelta(seconds=ttl)
        }

    def _get_from_redis(self, key: str) -> Optional[Any]:
        """Get value from Redis cache"""
        try:
            value_json = self.redis_client.get(key)
            if value_json:
                return json.loads(value_json)
        except Exception as e:
            self.logger.warning(f"Redis get error: {e}")
        return None

    def _set_in_redis(self, key: str, value: Any, ttl: int):
        """Set value in Redis cache"""
        try:
            value_json = json.dumps(value)
            self.redis_client.setex(key, ttl, value_json)
        except Exception as e:
            self.logger.warning(f"Redis set error: {e}")

    def invalidate(self, pattern: str):
        """Invalidate cache entries matching pattern"""
        # Memory cache
        keys_to_delete = [
            k for k in self._memory_cache.keys()
            if pattern in k
        ]
        for key in keys_to_delete:
            del self._memory_cache[key]

        # Redis cache
        if self.redis_available:
            try:
                keys = self.redis_client.keys(f"*{pattern}*")
                if keys:
                    self.redis_client.delete(*keys)
            except Exception as e:
                self.logger.warning(f"Redis invalidate error: {e}")

    def get_stats(self) -> dict:
        """Get cache statistics"""
        total_requests = self._cache_stats["hits"] + self._cache_stats["misses"]
        hit_rate = (
            self._cache_stats["hits"] / total_requests
            if total_requests > 0
            else 0
        )

        return {
            "hits": self._cache_stats["hits"],
            "misses": self._cache_stats["misses"],
            "evictions": self._cache_stats["evictions"],
            "hit_rate": f"{hit_rate:.2%}",
            "memory_entries": len(self._memory_cache),
            "redis_available": self.redis_available
        }


# Usage in modules:

# In db.py:
from modules.cache_manager import CacheManager, CacheConfig

cache_manager = CacheManager(CacheConfig(
    ttl_seconds=3600,  # 1 hour
    max_size=500
))

class DatabaseManager:
    @cache_manager.cached(ttl=3600, key_prefix="work_title_")
    def get_work_by_title(self, title: str, work_type: Optional[str] = None):
        # Database query (expensive)
        with self.get_connection() as conn:
            # ... query logic
            return result

    def create_work(self, ...):
        # ... create work
        # Invalidate cache on write
        cache_manager.invalidate("work_")
        return work_id

# In anime_anilist.py:
@cache_manager.cached(ttl=7200, key_prefix="anilist_")
async def fetch_anime_metadata(self, anime_id: int):
    # API call (expensive)
    async with self.session.get(...) as response:
        return await response.json()
```

**Expected Performance Improvements:**
- Database queries: 50-70% faster (cached results)
- API calls: 80-90% faster (cached responses)
- Work lookups: 90% faster (in-memory cache)

**Estimated Effort:** 3 days

---

### Task 3.2: Database Query Optimization

**Goal:** Eliminate N+1 queries, add batch operations

```python
# modules/db.py (enhanced)

class DatabaseManager:
    def get_works_batch(self, work_ids: List[int]) -> Dict[int, Dict]:
        """
        Batch fetch works (solves N+1 problem).

        Before:
            for release in releases:
                work = db.get_work(release.work_id)  # N queries!

        After:
            work_ids = [r.work_id for r in releases]
            works = db.get_works_batch(work_ids)  # 1 query!
        """
        if not work_ids:
            return {}

        placeholders = ",".join("?" * len(work_ids))
        query = f"SELECT * FROM works WHERE id IN ({placeholders})"

        with self.get_connection() as conn:
            cursor = conn.execute(query, work_ids)
            return {row["id"]: dict(row) for row in cursor.fetchall()}

    def get_releases_with_works(
        self,
        limit: Optional[int] = None,
        work_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Get releases with work data in single query (JOIN).

        Replaces multiple queries with efficient JOIN.
        """
        query = """
            SELECT
                r.*,
                w.title,
                w.title_kana,
                w.title_en,
                w.type,
                w.official_url
            FROM releases r
            JOIN works w ON r.work_id = w.id
            WHERE 1=1
        """

        params = []
        if work_type:
            query += " AND w.type = ?"
            params.append(work_type)

        query += " ORDER BY r.release_date DESC, r.created_at DESC"

        if limit:
            query += f" LIMIT {limit}"

        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def bulk_create_releases(
        self,
        releases: List[Dict[str, Any]]
    ) -> List[int]:
        """
        Bulk insert releases (much faster than individual inserts).

        Performance: ~10-100x faster for large batches
        """
        if not releases:
            return []

        with self.get_transaction() as conn:
            inserted_ids = []

            # Use executemany for bulk insert
            query = """
                INSERT OR IGNORE INTO releases
                (work_id, release_type, number, platform, release_date, source, source_url)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """

            data = [
                (
                    r["work_id"],
                    r["release_type"],
                    r.get("number"),
                    r.get("platform"),
                    r.get("release_date"),
                    r.get("source"),
                    r.get("source_url")
                )
                for r in releases
            ]

            conn.executemany(query, data)

            # Get inserted IDs (approximate, for new releases only)
            # For exact IDs, need individual queries or RETURNING clause (PostgreSQL)
            cursor = conn.execute("SELECT last_insert_rowid()")
            last_id = cursor.fetchone()[0]

            # Estimate range
            inserted_ids = list(range(last_id - len(releases) + 1, last_id + 1))

            return inserted_ids
```

**Estimated Effort:** 2 days

---

## Phase 4: Security Hardening (Week 7)

### Priority: HIGH (for production deployment)

### Task 4.1: Fix Security Vulnerabilities

**Critical Issues:**

1. **Hardcoded Secret Key**
```python
# app/web_ui.py - BEFORE:
app.secret_key = "your-secret-key-change-this-in-production"  # DANGEROUS!

# AFTER:
import secrets
import os

app.secret_key = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)

# In production, set environment variable:
# export FLASK_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
```

2. **Input Sanitization**
```python
# modules/security_utils.py (enhanced)

from markupsafe import escape
from urllib.parse import urlparse
import re

class InputValidator:
    """Input validation and sanitization"""

    @staticmethod
    def sanitize_html(text: str) -> str:
        """Remove HTML tags and escape special characters"""
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", text)
        # Escape special characters
        return escape(text)

    @staticmethod
    def validate_url(url: str, allowed_schemes=("http", "https")) -> bool:
        """Validate URL safety"""
        try:
            parsed = urlparse(url)
            return (
                parsed.scheme in allowed_schemes
                and parsed.netloc
                and not parsed.netloc.startswith("localhost")
                and not parsed.netloc.startswith("127.0.0.1")
            )
        except:
            return False

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent path traversal"""
        # Remove path components
        filename = os.path.basename(filename)
        # Remove dangerous characters
        filename = re.sub(r"[^\w\s.-]", "", filename)
        return filename

# Usage in web_ui.py:
from modules.security_utils import InputValidator

@app.route("/works")
def works():
    search_query = request.args.get("search", "")
    # Sanitize user input
    search_query = InputValidator.sanitize_html(search_query)
    # ... rest of code
```

3. **Rate Limiting**
```python
# app/web_ui.py - Add rate limiting

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"  # or "redis://localhost:6379"
)

@app.route("/api/trigger-collection", methods=["POST"])
@limiter.limit("5 per hour")  # Strict limit for expensive operations
def api_trigger_collection():
    # ... implementation

@app.route("/api/system-stats")
@limiter.limit("60 per minute")  # More lenient for read operations
def api_system_stats():
    # ... implementation
```

**Estimated Effort:** 1 day

---

### Task 4.2: Security Audit & Compliance

**Checklist:**

- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (input sanitization, output escaping)
- [ ] CSRF protection (Flask-WTF tokens)
- [ ] Rate limiting (API and web endpoints)
- [ ] Secure token storage (encrypted token.json)
- [ ] HTTPS enforcement (production deployment)
- [ ] Security headers (CSP, X-Frame-Options, etc.)
- [ ] Dependency vulnerability scanning (pip-audit)
- [ ] Secrets management (environment variables, not hardcoded)
- [ ] Logging sensitive data prevention

**Implementation:**

```python
# modules/security_compliance.py (enhanced)

class SecurityAuditor:
    """Automated security compliance checker"""

    def run_audit(self) -> Dict[str, Any]:
        """Run comprehensive security audit"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "checks": [],
            "score": 0,
            "issues": []
        }

        # Check 1: SQL injection prevention
        sql_check = self._check_sql_injection_prevention()
        results["checks"].append(sql_check)

        # Check 2: Secret key configuration
        secret_check = self._check_secret_configuration()
        results["checks"].append(secret_check)

        # Check 3: Input validation
        input_check = self._check_input_validation()
        results["checks"].append(input_check)

        # Check 4: Rate limiting
        rate_limit_check = self._check_rate_limiting()
        results["checks"].append(rate_limit_check)

        # Check 5: Dependency vulnerabilities
        dep_check = self._check_dependencies()
        results["checks"].append(dep_check)

        # Calculate score
        passed = sum(1 for c in results["checks"] if c["passed"])
        results["score"] = (passed / len(results["checks"])) * 100

        # Collect issues
        for check in results["checks"]:
            if not check["passed"]:
                results["issues"].append({
                    "check": check["name"],
                    "severity": check["severity"],
                    "message": check["message"]
                })

        return results

    def _check_sql_injection_prevention(self) -> Dict:
        """Check for SQL injection vulnerabilities"""
        # Scan code for dangerous patterns like string formatting in SQL
        # ... implementation
        return {
            "name": "SQL Injection Prevention",
            "passed": True,
            "severity": "CRITICAL",
            "message": "All SQL queries use parameterized statements"
        }

    # ... other checks
```

**Estimated Effort:** 2 days

---

## Phase 5: Scalability Preparation (Week 8-10)

### Priority: LOW (future-proofing)

### Task 5.1: Celery Task Queue (Optional)

**Goal:** Asynchronous background processing

```python
# modules/celery_app.py (new)

from celery import Celery
from celery.schedules import crontab

# Initialize Celery
app = Celery(
    'manga_anime_system',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

# Configuration
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Tokyo',
    enable_utc=True,
)

# Define tasks
@app.task(bind=True, max_retries=3)
def collect_from_anilist(self):
    """Async task: Collect data from AniList"""
    try:
        from modules.anime_anilist import AniListCollector
        collector = AniListCollector()
        results = collector.collect()
        return {"status": "success", "count": len(results)}
    except Exception as e:
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

@app.task
def collect_from_all_sources():
    """Async task: Collect from all sources in parallel"""
    from celery import group

    # Create parallel task group
    job = group(
        collect_from_anilist.s(),
        collect_from_kitsu.s(),
        collect_from_manga_rss.s(),
    )

    # Execute in parallel
    result = job.apply_async()
    return result.get()

@app.task
def send_email_notification(release_data):
    """Async task: Send email notification"""
    from modules.email_service import EmailService
    email_service = EmailService()
    return email_service.send(release_data)

# Scheduled tasks (Celery Beat)
app.conf.beat_schedule = {
    'collect-every-hour': {
        'task': 'modules.celery_app.collect_from_all_sources',
        'schedule': crontab(minute=0, hour='*/1'),  # Every hour
    },
    'send-morning-digest': {
        'task': 'modules.celery_app.send_daily_digest',
        'schedule': crontab(hour=8, minute=0),  # 8:00 AM
    },
}
```

**Benefits:**
- Parallel processing (3-5x faster collection)
- Retry logic built-in
- Scheduled tasks (replace cron)
- Better resource utilization

**Estimated Effort:** 3 days

---

### Task 5.2: PostgreSQL Migration (Optional)

**Goal:** Better concurrency and scalability

**Migration Strategy:**

```python
# Step 1: Add SQLAlchemy ORM layer
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Work(Base):
    __tablename__ = 'works'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    title_kana = Column(String)
    title_en = Column(String)
    type = Column(String, nullable=False)
    official_url = Column(String)
    created_at = Column(DateTime, server_default='NOW()')

# Step 2: Dual-write period (write to both databases)
def create_work(title, work_type):
    # Write to SQLite
    sqlite_id = sqlite_db.create_work(title, work_type)

    # Write to PostgreSQL
    pg_session = pg_sessionmaker()
    pg_work = Work(title=title, type=work_type)
    pg_session.add(pg_work)
    pg_session.commit()
    pg_id = pg_work.id

    return sqlite_id  # Return SQLite ID for now

# Step 3: Switch reads to PostgreSQL
# Step 4: Remove SQLite writes
# Step 5: Deprecate SQLite
```

**Estimated Effort:** 1-2 weeks

---

## Implementation Timeline

### Sprint Planning

| Sprint | Week | Focus | Deliverables |
|--------|------|-------|--------------|
| Sprint 1 | 1-2 | Foundation | Merged modules, standardized errors, unified mailer |
| Sprint 2 | 3-4 | Config & Testing | Centralized config, 75% test coverage |
| Sprint 3 | 5-6 | Performance | Caching layer, query optimization |
| Sprint 4 | 7 | Security | Fixed vulnerabilities, audit compliance |
| Sprint 5 | 8-10 | Scalability (Optional) | Celery, PostgreSQL migration |

---

## Success Metrics

### Before Refactoring
- Lines of Code: ~25,000
- Module Count: 39
- Code Duplication: ~15-20%
- Test Coverage: Unknown
- Average API Response: 2-3 seconds
- Database Query Time: 100-200ms

### After Refactoring (Target)
- Lines of Code: ~20,000 (20% reduction)
- Module Count: 32 (merged enhanced modules)
- Code Duplication: <5%
- Test Coverage: 75%+
- Average API Response: 1-1.5 seconds (40% improvement)
- Database Query Time: 20-50ms (75% improvement with caching)

---

## Risk Assessment

### Low Risk
- Module merging (well-defined scope)
- Test suite addition (no impact on existing code)
- Configuration centralization (backward compatible)

### Medium Risk
- Error handling standardization (touches all modules)
- Caching implementation (potential cache invalidation issues)
- Database optimization (need careful testing)

### High Risk
- PostgreSQL migration (major infrastructure change)
- Celery introduction (new dependency, complexity)

**Mitigation:**
- Phased rollout
- Comprehensive testing at each phase
- Feature flags for gradual deployment
- Rollback plan for each change

---

## Conclusion

This refactoring roadmap provides a structured approach to improving the MangaAnime Information Delivery System. By following these phases:

1. **Foundation** improvements will immediately reduce maintenance overhead
2. **Configuration & Testing** will increase confidence in changes
3. **Performance** optimizations will improve user experience
4. **Security** hardening will enable production deployment
5. **Scalability** preparations will future-proof the system

**Recommended Approach:** Complete Phases 1-4 (Weeks 1-7) as minimum viable refactoring. Phase 5 can be deferred until scalability becomes a pressing need.

---

**Document Version:** 1.0
**Last Updated:** 2025-12-06
**Prepared By:** System Architecture Designer Agent
**Approval Status:** Ready for Team Review
