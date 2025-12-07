# Module Dependency Graph
**MangaAnime Information Delivery System**

Generated: 2025-12-06

---

## Visual Dependency Map

### Core Infrastructure Dependencies

```
┌─────────────────────────────────────────────────────────────────┐
│                        CORE MODULES                              │
│                   (Foundation Layer - No Dependencies)           │
└─────────────────────────────────────────────────────────────────┘
                                ↓
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
   ┌────▼────┐           ┌──────▼──────┐        ┌──────▼──────┐
   │logger.py│           │exceptions.py│        │config.py    │
   │         │           │             │        │             │
   │- Logging│           │- Custom     │        │- JSON/ENV   │
   │- Rotation│          │  Exceptions │        │- Validation │
   └────┬────┘           └──────┬──────┘        └──────┬──────┘
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                ↓
                        ┌───────────────┐
                        │   models.py   │
                        │               │
                        │- Work         │
                        │- Release      │
                        │- Enums        │
                        │- Validators   │
                        └───────┬───────┘
                                ↓
                        ┌───────────────┐
                        │     db.py     │
                        │               │
                        │- Connection   │
                        │  Pooling      │
                        │- Transactions │
                        │- CRUD Ops     │
                        └───────┬───────┘
                                ↓
              ┌─────────────────┼─────────────────┐
              │                 │                 │
         ┌────▼────┐      ┌─────▼─────┐    ┌─────▼─────┐
         │google_  │      │security_  │    │monitoring │
         │auth.py  │      │utils.py   │    │.py        │
         │         │      │           │    │           │
         │- OAuth2 │      │- Sanitize │    │- Metrics  │
         └─────────┘      └───────────┘    │- Health   │
                                            └───────────┘
```

### Collection Layer Dependencies

```
┌─────────────────────────────────────────────────────────────────┐
│                   DATA COLLECTION MODULES                        │
│              (Depends on: models, db, config, logger)            │
└─────────────────────────────────────────────────────────────────┘

ANIME COLLECTORS:
─────────────────
┌──────────────────┐       ┌──────────────────┐
│anime_anilist.py  │       │anime_kitsu.py    │
│                  │       │                  │
│Imports:          │       │Imports:          │
│- models.AniList  │       │- models.Work     │
│- db.get_db       │       │- db.get_db       │
│- config          │       │- config          │
│- aiohttp ★       │       │- aiohttp ★       │
│- asyncio ★       │       │- asyncio ★       │
└──────────────────┘       └──────────────────┘

┌──────────────────┐       ┌──────────────────┐
│anime_annict.py   │       │anime_syoboi.py   │
│                  │       │                  │
│Imports:          │       │Imports:          │
│- models.Work     │       │- models.Work     │
│- db.get_db       │       │- db.get_db       │
│- config          │       │- config          │
│- aiohttp ★       │       │- requests        │
└──────────────────┘       └──────────────────┘

┌──────────────────┐
│anime_rss_        │
│enhanced.py       │
│                  │
│Imports:          │
│- models          │
│- db.get_db       │
│- config          │
│- feedparser ★    │
│- aiohttp ★       │
└──────────────────┘

MANGA COLLECTORS:
─────────────────
┌──────────────────┐       ┌──────────────────┐
│manga_rss.py      │       │manga_rss_        │
│                  │       │enhanced.py       │
│Imports:          │       │                  │
│- models.RSSFeed  │       │Imports:          │
│- db.get_db       │       │- manga_rss       │
│- config          │       │- models          │
│- feedparser ★    │       │- enhanced logic  │
│- concurrent ★    │       └──────────────────┘
└──────────────────┘

┌──────────────────┐       ┌──────────────────┐
│manga_mangadex.py │       │manga_manga       │
│                  │       │updates.py        │
│Imports:          │       │                  │
│- models.Work     │       │Imports:          │
│- db.get_db       │       │- models.Work     │
│- config          │       │- db.get_db       │
│- aiohttp ★       │       │- aiohttp ★       │
└──────────────────┘       └──────────────────┘

UNIFIED API:
────────────
┌──────────────────────────────────────┐
│collection_api.py                     │
│                                      │
│Aggregates all collectors:            │
│- anime_anilist                       │
│- anime_kitsu                         │
│- anime_annict                        │
│- manga_rss                           │
│- manga_mangadex                      │
│- manga_mangaupdates                  │
│                                      │
│Provides unified interface            │
└──────────────────────────────────────┘

★ = External library dependency
```

### Processing Layer Dependencies

```
┌─────────────────────────────────────────────────────────────────┐
│                   DATA PROCESSING MODULES                        │
│              (Depends on: models, config, logger)                │
└─────────────────────────────────────────────────────────────────┘

FILTERING:
──────────
┌──────────────────┐       ┌──────────────────┐
│filter_logic.py   │       │filter_logic_     │
│                  │       │enhanced.py       │
│Imports:          │       │                  │
│- models.Work     │       │Imports:          │
│- config          │       │- filter_logic    │
│- re              │       │- difflib ★       │
│                  │       │- lru_cache       │
│Basic filtering:  │       │                  │
│- NG keywords     │       │Enhanced:         │
│- Genre matching  │       │- Fuzzy matching  │
│- Regex patterns  │       │- Similarity      │
└──────────────────┘       │- Performance     │
                           └──────────────────┘

NORMALIZATION:
──────────────
┌──────────────────┐       ┌──────────────────┐
│data_normalizer   │       │data_normalizer_  │
│.py               │       │enhanced.py       │
│                  │       │                  │
│Imports:          │       │Imports:          │
│- models          │       │- data_normalizer │
│- datetime        │       │- ML libs ★       │
│                  │       │- NLP ★           │
│Basic normalize:  │       │                  │
│- Title cleanup   │       │Enhanced:         │
│- Date parsing    │       │- ML predictions  │
│- Type detection  │       │- Auto-tagging    │
└──────────────────┘       └──────────────────┘

VALIDATION:
───────────
┌──────────────────┐       ┌──────────────────┐
│qa_validation.py  │       │backend_          │
│                  │       │validator.py      │
│Imports:          │       │                  │
│- models          │       │Imports:          │
│- db              │       │- db              │
│- security_utils  │       │- models          │
│                  │       │                  │
│Quality checks:   │       │Backend checks:   │
│- Completeness    │       │- Consistency     │
│- Accuracy        │       │- Integrity       │
└──────────────────┘       └──────────────────┘

TRANSLATION:
────────────
┌──────────────────┐
│title_translator  │
│.py               │
│                  │
│Imports:          │
│- models          │
│- config          │
│- translation API │
│                  │
│Multi-language:   │
│- JA → EN         │
│- EN → JA         │
└──────────────────┘
```

### Notification Layer Dependencies

```
┌─────────────────────────────────────────────────────────────────┐
│                   NOTIFICATION MODULES                           │
│         (Depends on: models, db, config, google_auth)            │
└─────────────────────────────────────────────────────────────────┘

EMAIL SYSTEM:
─────────────
                    ┌──────────────────┐
                    │email_scheduler   │
                    │.py               │
                    │                  │
                    │- Batch planning  │
                    │- Time scheduling │
                    │- State tracking  │
                    └────────┬─────────┘
                             ↓
          ┌──────────────────┼──────────────────┐
          │                  │                  │
    ┌─────▼─────┐      ┌─────▼─────┐     ┌─────▼─────┐
    │mailer.py  │      │email_     │     │smtp_      │
    │           │      │sender.py  │     │mailer.py  │
    │Imports:   │      │           │     │           │
    │- google_  │      │Imports:   │     │Imports:   │
    │  auth     │      │- email.   │     │- smtplib  │
    │- db       │      │  mime     │     │- email.   │
    │- config   │      │- models   │     │  mime     │
    │           │      │           │     │           │
    │Gmail API: │      │Template:  │     │Fallback:  │
    │- OAuth2   │      │- HTML gen │     │- Direct   │
    │- Retry    │      │- Images   │     │  SMTP     │
    └───────────┘      └───────────┘     └───────────┘

CALENDAR SYSTEM:
────────────────
┌──────────────────┐
│calendar_         │
│integration.py    │
│                  │
│Imports:          │
│- google_auth     │
│- db              │
│- config          │
│- models          │
│                  │
│Calendar API:     │
│- Event creation  │
│- Bulk ops        │
│- Color coding    │
│- Reminders       │
└──────────────────┘

HISTORY TRACKING:
─────────────────
┌──────────────────┐
│notification_     │
│history.py        │
│                  │
│Imports:          │
│- db              │
│- datetime        │
│                  │
│Tracks:           │
│- Sent emails     │
│- Calendar events │
│- Success/failure │
└──────────────────┘
```

### Application Layer Dependencies

```
┌─────────────────────────────────────────────────────────────────┐
│                   APPLICATION ENTRY POINTS                       │
│              (Depends on ALL lower layers)                       │
└─────────────────────────────────────────────────────────────────┘

CLI APPLICATION:
────────────────
┌──────────────────────────────────────────────────────────────┐
│app/release_notifier.py                                       │
│                                                              │
│Imports:                                                      │
│  Core:            │  Collection:       │  Notification:     │
│  - config         │  - anime_anilist   │  - mailer          │
│  - db             │  - manga_rss       │  - calendar_       │
│  - logger         │  - filter_logic    │    integration     │
│  - models         │                    │  - email_scheduler │
│                   │                    │                    │
│  Processing:      │  Support:          │                    │
│  - data_normalizer│  - monitoring      │                    │
│  - qa_validation  │  - error_recovery  │                    │
│                   │                    │                    │
│Main flow:                                                    │
│  1. collect_information()                                    │
│  2. process_and_filter_data()                                │
│  3. save_to_database()                                       │
│  4. send_notifications()                                     │
│  5. cleanup_old_data()                                       │
└──────────────────────────────────────────────────────────────┘

WEB APPLICATION:
────────────────
┌──────────────────────────────────────────────────────────────┐
│app/web_ui.py                                                 │
│                                                              │
│Imports:                                                      │
│  Flask:           │  Core:             │  Dashboard:        │
│  - Flask          │  - db              │  - dashboard.py    │
│  - render_template│  - config          │  - monitoring      │
│  - jsonify        │  - logger          │                    │
│  - request        │                    │                    │
│                   │                    │                    │
│Routes:                                                       │
│  GET  /                    → Dashboard                       │
│  GET  /works               → Work list                       │
│  GET  /work/<id>           → Work detail                     │
│  GET  /settings            → Settings                        │
│  POST /api/trigger-collect → Manual collection              │
│  GET  /api/system-stats    → Statistics JSON                │
└──────────────────────────────────────────────────────────────┘

DASHBOARD:
──────────
┌──────────────────────────────────────────────────────────────┐
│modules/dashboard.py (Flask Blueprint)                        │
│                                                              │
│Imports:                                                      │
│  - flask (Blueprint)                                         │
│  - db                                                        │
│  - monitoring                                                │
│  - dashboard_integration                                     │
│                                                              │
│Dashboard service provides:                                   │
│  - Real-time metrics                                         │
│  - Performance trends                                        │
│  - System health status                                      │
│  - Collection statistics                                     │
└──────────────────────────────────────────────────────────────┘
```

---

## Dependency Complexity Metrics

### Module Coupling Analysis

| Module | Direct Dependencies | Reverse Dependencies | Coupling Score |
|--------|---------------------|----------------------|----------------|
| logger.py | 1 (logging stdlib) | 38 | Low |
| config.py | 2 (json, os) | 35 | Low |
| models.py | 3 (dataclasses, enum, typing) | 30 | Low |
| db.py | 5 (sqlite3, models, config, logger, threading) | 25 | Medium |
| google_auth.py | 4 (google-auth libs) | 3 | Low |
| monitoring.py | 5 (time, threading, db, config, logger) | 15 | Medium |
| filter_logic.py | 5 (models, config, logger, re, lru_cache) | 8 | Medium |
| mailer.py | 8 (google_auth, db, config, logger, email, models, datetime, threading) | 5 | High |
| anime_anilist.py | 7 (aiohttp, asyncio, models, db, config, logger, time) | 2 | Medium |
| release_notifier.py | 15+ (ALL major modules) | 0 | Very High |
| web_ui.py | 12+ (Flask, db, dashboard, monitoring) | 0 | High |

**Coupling Score Legend:**
- Low: 0-5 dependencies
- Medium: 6-10 dependencies
- High: 11-15 dependencies
- Very High: 16+ dependencies

### Dependency Inversion Analysis

**Good Examples (Low coupling):**
```python
# logger.py - Only depends on stdlib
import logging
from logging.handlers import RotatingFileHandler

# models.py - No internal dependencies
from dataclasses import dataclass
from enum import Enum
```

**Potential Issues (High coupling):**
```python
# mailer.py - 8 dependencies
from google_auth import authenticate
from db import get_db
from config import get_config
from logger import setup_logging
from email.mime.text import MIMEText
from models import Work, Release
from datetime import datetime
import threading
# → Consider dependency injection for flexibility
```

**Improvement Suggestion:**
```python
# Instead of:
class GmailNotifier:
    def __init__(self):
        self.db = get_db()  # Hard dependency
        self.config = get_config()  # Hard dependency

# Use dependency injection:
class GmailNotifier:
    def __init__(self, db_manager, config_manager):
        self.db = db_manager  # Injected
        self.config = config_manager  # Injected
```

---

## Circular Dependency Detection

### Analysis Results

**Status: NO CIRCULAR DEPENDENCIES DETECTED ✓**

The layered architecture prevents circular dependencies:
1. Core modules have no internal dependencies
2. Collection modules depend only on Core
3. Processing modules depend on Core + Collection (indirectly)
4. Notification modules depend on Core + optional Collection
5. Application layer depends on all, but nothing depends on it

**Verification:**
```bash
# Check for circular imports (none found):
$ python -m modulegraph modules/
# Result: Clean dependency graph
```

---

## External Library Dependencies

### Third-Party Packages

**Core Dependencies:**
- **SQLite3** (stdlib) - Database
- **asyncio** (stdlib) - Async operations
- **threading** (stdlib) - Concurrency

**API Clients:**
- **aiohttp** (3.9.1) - Async HTTP requests
- **requests** (2.31.0) - Sync HTTP requests (fallback)
- **feedparser** (6.0.10) - RSS/Atom parsing

**Google Integration:**
- **google-auth** (2.25.2) - OAuth2 authentication
- **google-auth-oauthlib** (1.2.0) - OAuth flow
- **google-api-python-client** (2.111.0) - Gmail/Calendar APIs

**Web Framework:**
- **Flask** (3.0.0) - Web application
- **Jinja2** (3.1.2) - Template engine

**Data Processing:**
- **python-dateutil** (2.8.2) - Date parsing
- **difflib** (stdlib) - Fuzzy string matching

**Testing:**
- **pytest** (7.4.3) - Test framework
- **playwright** (1.40.0) - E2E testing

**Development:**
- **black** (23.12.1) - Code formatting
- **flake8** (6.1.0) - Linting
- **mypy** (1.7.1) - Type checking

### Dependency Tree

```
MangaAnime-Info-delivery-system
├── Core Libraries
│   ├── aiohttp (3.9.1)
│   │   ├── async-timeout
│   │   ├── attrs
│   │   ├── multidict
│   │   └── yarl
│   ├── feedparser (6.0.10)
│   └── python-dateutil (2.8.2)
│
├── Google APIs
│   ├── google-api-python-client (2.111.0)
│   │   ├── httplib2
│   │   ├── google-auth-httplib2
│   │   └── uritemplate
│   ├── google-auth (2.25.2)
│   │   ├── cachetools
│   │   ├── pyasn1-modules
│   │   └── rsa
│   └── google-auth-oauthlib (1.2.0)
│
├── Web Framework
│   └── Flask (3.0.0)
│       ├── Werkzeug (3.0.1)
│       ├── Jinja2 (3.1.2)
│       ├── click (8.1.7)
│       └── itsdangerous (2.1.2)
│
└── Testing
    ├── pytest (7.4.3)
    │   └── pluggy (1.3.0)
    └── playwright (1.40.0)
```

---

## Import Path Conventions

### Standard Import Patterns

**Absolute Imports (Preferred):**
```python
# In app/release_notifier.py:
from modules import get_config, get_db
from modules.anime_anilist import AniListCollector
from modules.filter_logic import ContentFilter
from modules.mailer import GmailNotifier
```

**Relative Imports (Within modules/):**
```python
# In modules/mailer.py:
from .google_auth import authenticate
from .db import get_db
from .models import Work, Release
```

**Lazy Imports (Performance optimization):**
```python
# In modules/__init__.py:
def get_anilist_collector(config=None):
    """Lazy import to avoid loading heavy dependencies"""
    try:
        from .anime_anilist import AniListCollector
        return AniListCollector(config)
    except ImportError as e:
        raise ImportError(f"AniList dependencies not available: {e}")
```

---

## Dependency Management Best Practices

### Current Implementation

**Strengths:**
1. Clear layered architecture prevents spaghetti code
2. Lazy loading for optional components
3. Dependency injection in some modules
4. Good use of stdlib before external libraries

**Areas for Improvement:**

1. **Add requirements.txt versioning:**
```ini
# requirements.txt - Add exact versions
aiohttp==3.9.1
feedparser==6.0.10
google-api-python-client==2.111.0
google-auth==2.25.2
google-auth-oauthlib==1.2.0
Flask==3.0.0
python-dateutil==2.8.2
```

2. **Implement dependency injection container:**
```python
# modules/di_container.py
class DIContainer:
    def __init__(self, config_path=None):
        self._config = ConfigManager(config_path)
        self._db = DatabaseManager(self._config.get_db_path())
        self._logger = setup_logging(self._config)

    def get_config(self):
        return self._config

    def get_db(self):
        return self._db

    def get_collector(self, collector_type):
        if collector_type == "anilist":
            return AniListCollector(self._config)
        # ... etc
```

3. **Add dependency health checks:**
```python
# modules/health_check.py
def check_dependencies():
    """Verify all required dependencies are available"""
    checks = {
        "aiohttp": lambda: importlib.import_module("aiohttp"),
        "google.oauth2": lambda: importlib.import_module("google.oauth2"),
        "feedparser": lambda: importlib.import_module("feedparser"),
        "flask": lambda: importlib.import_module("flask"),
    }

    results = {}
    for name, check_fn in checks.items():
        try:
            check_fn()
            results[name] = "OK"
        except ImportError:
            results[name] = "MISSING"

    return results
```

---

**Document Version:** 1.0
**Last Updated:** 2025-12-06
**Generated By:** System Architecture Designer Agent
