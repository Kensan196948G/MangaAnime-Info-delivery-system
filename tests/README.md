# Manga/Anime Information Delivery System - Testing Framework

This comprehensive testing framework provides complete coverage for the Manga/Anime information delivery system, including unit tests, integration tests, end-to-end workflow testing, performance testing, and monitoring validation.

## 📁 Test Structure

```
tests/
├── README.md                    # This file
├── conftest.py                 # Pytest configuration and shared fixtures
├── pytest.ini                 # Pytest configuration file
│
├── 🧪 Unit Tests
│   ├── test_config.py          # Configuration management tests
│   ├── test_database.py        # Database operations tests  
│   ├── test_filtering.py       # Content filtering tests
│
├── 🔗 Integration Tests
│   ├── test_anilist_api.py     # AniList GraphQL API integration
│   ├── test_rss_processing.py  # RSS feed processing tests
│   ├── test_google_apis.py     # Google APIs integration tests
│   ├── test_mailer_integration.py    # Email notification integration
│   ├── test_calendar_integration.py  # Calendar integration tests
│
├── 🔄 End-to-End Tests  
│   └── test_e2e_workflow.py    # Complete system workflow tests
│
├── ⚡ Performance Tests
│   └── test_performance.py     # Load testing and performance validation
│
├── 📊 Monitoring Tests
│   └── test_monitoring.py      # System monitoring and observability
│
└── 🛠 Test Utilities
    └── test_utils.py           # Test data factories and helper functions
```

## 🚀 Quick Start

### Prerequisites

```bash
# Install testing dependencies
pip install pytest pytest-cov pytest-mock pytest-asyncio pytest-html pytest-xdist

# Install additional tools for comprehensive testing
pip install flake8 black mypy bandit safety memory-profiler psutil faker
```

### Basic Test Execution

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=modules --cov-report=html

# Run specific test categories
python -m pytest -m "unit"                    # Unit tests only
python -m pytest -m "integration"             # Integration tests only  
python -m pytest -m "e2e"                     # End-to-end tests only
python -m pytest -m "performance"             # Performance tests only

# Run tests excluding slow ones
python -m pytest -m "not slow"

# Run with verbose output
python -m pytest -v

# Run tests in parallel (faster execution)
python -m pytest -n auto
```

### Using the Test Runner Script

The project includes a comprehensive test runner script with advanced features:

```bash
# Basic usage
./scripts/run_tests.sh

# Run specific test types
./scripts/run_tests.sh --type unit --verbose
./scripts/run_tests.sh --type performance --parallel --output html
./scripts/run_tests.sh --type integration --fail-fast

# Advanced usage
./scripts/run_tests.sh --markers "not slow and not api" --coverage 85 --timeout 600
```

### Test Runner Options

| Option | Description | Example |
|--------|-------------|---------|
| `--type` | Test type: unit, integration, e2e, performance, all | `--type unit` |
| `--coverage` | Coverage threshold percentage | `--coverage 85` |
| `--verbose` | Verbose output | `--verbose` |
| `--parallel` | Run tests in parallel | `--parallel` |
| `--fail-fast` | Stop on first failure | `--fail-fast` |
| `--output` | Output format: term, html, xml, json | `--output html` |
| `--reports-dir` | Reports directory | `--reports-dir test-reports` |
| `--markers` | Pytest markers to run | `--markers "not slow"` |
| `--timeout` | Test timeout in seconds | `--timeout 300` |

## 📋 Test Categories

### 🧪 Unit Tests

**Purpose**: Test individual components in isolation with mocked dependencies.

**Coverage**:
- ✅ Database operations and schema validation
- ✅ Configuration management and validation  
- ✅ Content filtering logic and NG keyword detection
- ✅ Data models and serialization
- ✅ Utility functions and helpers

**Key Features**:
- Fast execution (< 30 seconds total)
- No external dependencies
- High code coverage (80%+ target)
- Comprehensive edge case testing

### 🔗 Integration Tests

**Purpose**: Test interactions between system components and external APIs.

**Coverage**:
- ✅ AniList GraphQL API integration and rate limiting
- ✅ RSS feed collection from multiple sources
- ✅ Gmail API for email notifications
- ✅ Google Calendar API for event creation
- ✅ Authentication flows (OAuth2)

**Key Features**:
- Mocked external APIs for reliability
- Error handling and retry logic validation
- API response format validation
- Rate limiting compliance testing

### 🔄 End-to-End Tests

**Purpose**: Test complete system workflows from data collection to notification.

**Coverage**:
- ✅ Full anime collection and notification workflow
- ✅ Manga RSS processing workflow  
- ✅ Multi-source data integration
- ✅ Error recovery scenarios
- ✅ High-volume data processing

**Key Features**:
- Realistic workflow simulation
- Multi-step process validation
- Data consistency verification
- Integration between all components

### ⚡ Performance Tests

**Purpose**: Validate system performance under various load conditions.

**Coverage**:
- ✅ Database performance with bulk operations
- ✅ API response time monitoring
- ✅ Memory usage patterns
- ✅ Concurrent request handling
- ✅ Resource utilization monitoring

**Key Features**:
- Load testing scenarios
- Performance threshold validation
- Resource usage monitoring
- Scalability testing

### 📊 Monitoring Tests

**Purpose**: Validate monitoring, alerting, and observability features.

**Coverage**:
- ✅ Health check endpoints
- ✅ Metrics collection and analysis
- ✅ Error pattern detection
- ✅ Alert system validation
- ✅ Compliance and audit logging

## 🎯 Test Markers

Use pytest markers to run specific test subsets:

```bash
# Test markers available
pytest -m "unit"           # Unit tests only
pytest -m "integration"    # Integration tests only  
pytest -m "e2e"           # End-to-end tests only
pytest -m "performance"    # Performance tests only
pytest -m "slow"          # Slow-running tests
pytest -m "api"           # Tests that call external APIs
pytest -m "auth"          # Authentication-related tests
pytest -m "db"            # Database-related tests

# Combine markers
pytest -m "unit and not slow"
pytest -m "integration or e2e"
pytest -m "not api and not slow"
```

## 📊 Coverage Reporting

The testing framework provides comprehensive coverage reporting:

```bash
# Generate HTML coverage report
pytest --cov=modules --cov-report=html

# Generate XML coverage report (for CI/CD)
pytest --cov=modules --cov-report=xml

# Generate terminal coverage report
pytest --cov=modules --cov-report=term-missing

# Set coverage threshold
pytest --cov=modules --cov-fail-under=80
```

Coverage reports are generated in:
- HTML: `htmlcov/index.html`
- XML: `coverage.xml`
- Terminal: displayed inline

## 🔧 Test Configuration

### pytest.ini

The project uses a comprehensive pytest configuration:

```ini
[tool:pytest]
minversion = 7.0
addopts = 
    -ra
    -q
    --strict-markers
    --strict-config
    --cov=modules
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
    --tb=short

testpaths = tests
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*

markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    api: marks tests that call external APIs
    auth: marks tests related to OAuth2 authentication
    db: marks tests related to database operations
    performance: marks performance tests
    e2e: marks end-to-end tests
```

### Fixtures and Test Data

The framework includes comprehensive fixtures in `conftest.py`:

- **Database fixtures**: Temporary databases with test data
- **API mocks**: Realistic mock responses for external APIs
- **Configuration fixtures**: Test-specific configuration data
- **Performance fixtures**: Performance testing parameters
- **Data generators**: Factories for creating test data

## 🤖 Continuous Integration

### GitHub Actions Workflow

The project includes a comprehensive CI/CD pipeline (`.github/workflows/ci.yml`):

**Pipeline Stages**:
1. 🔍 **Code Quality** - Linting, formatting, type checking, security analysis
2. 🧪 **Unit Tests** - Fast unit tests across multiple Python versions  
3. 🔗 **Integration Tests** - API integration and service interaction tests
4. 🔄 **E2E Tests** - Complete workflow validation
5. ⚡ **Performance Tests** - Load testing and performance validation
6. 🔒 **Security Scan** - Vulnerability scanning and security analysis
7. 📦 **Build Package** - Package building and validation
8. 📊 **Test Summary** - Comprehensive test reporting
9. 🚀 **Deploy** - Automated deployment (production only)
10. 📢 **Notifications** - Status notifications and monitoring

**Supported Python Versions**: 3.9, 3.10, 3.11, 3.12

**Key CI Features**:
- Parallel test execution for faster feedback
- Comprehensive test result reporting  
- Automatic coverage reporting to Codecov
- Security vulnerability scanning
- Performance regression detection
- Automated deployment on successful tests

### Local CI Simulation

Run the same checks locally as in CI:

```bash
# Code quality checks
flake8 modules/ tests/
black --check modules/ tests/
mypy modules/ --ignore-missing-imports
bandit -r modules/
safety check

# Full test suite with coverage  
pytest --cov=modules --cov-report=html --cov-fail-under=80

# Performance tests
pytest -m "performance" --timeout=300
```

## 📈 Test Data and Fixtures

### Test Data Factory

The `TestDataFactory` class provides realistic test data:

```python
from tests.test_utils import TestDataFactory

factory = TestDataFactory()

# Generate anime data
anime_works = factory.generate_work_data('anime', count=10)

# Generate manga data  
manga_works = factory.generate_work_data('manga', count=5)

# Generate AniList API responses
anilist_response = factory.generate_anilist_response(media_count=20)

# Generate RSS feed data
rss_data = factory.generate_rss_feed_data(entry_count=15, feed_type='manga')
```

### Mock Services

Pre-configured mock services for testing:

```python
from tests.test_utils import MockServiceFactory

# Gmail API mock
gmail_service = MockServiceFactory.create_mock_gmail_service()

# Calendar API mock  
calendar_service = MockServiceFactory.create_mock_calendar_service()

# AniList client mock
anilist_client = MockServiceFactory.create_mock_anilist_client()
```

## 🐛 Debugging Tests

### Running Individual Tests

```bash
# Run a specific test file
pytest tests/test_database.py -v

# Run a specific test class
pytest tests/test_database.py::TestDatabaseManager -v

# Run a specific test method  
pytest tests/test_database.py::TestDatabaseManager::test_database_initialization -v

# Run with debugging
pytest --pdb tests/test_database.py::TestDatabaseManager::test_database_initialization

# Run with print statements (capture=no)
pytest -s tests/test_database.py
```

### Test Output and Logging

```bash
# Show local variables on failures
pytest --tb=long

# Show brief traceback
pytest --tb=short

# Show no traceback
pytest --tb=no

# Enable logging output
pytest --log-cli-level=DEBUG

# Save output to file
pytest --resultlog=tests.log
```

## 📝 Writing New Tests

### Test Naming Convention

- Test files: `test_*.py`
- Test classes: `Test*`
- Test methods: `test_*`
- Use descriptive names that explain what is being tested

### Example Test Structure

```python
import pytest
from unittest.mock import Mock, patch

class TestNewFeature:
    """Test new feature functionality."""
    
    @pytest.mark.unit
    def test_basic_functionality(self):
        """Test basic functionality works correctly."""
        # Arrange
        input_data = "test input"
        expected_output = "expected output"
        
        # Act  
        result = function_under_test(input_data)
        
        # Assert
        assert result == expected_output
    
    @pytest.mark.integration
    @patch('module.external_service')
    def test_integration_with_external_service(self, mock_service):
        """Test integration with external service."""
        # Setup mock
        mock_service.return_value = "mocked response"
        
        # Test integration
        result = integration_function()
        
        # Verify
        assert result is not None
        mock_service.assert_called_once()
    
    @pytest.mark.performance
    def test_performance_requirements(self):
        """Test performance meets requirements."""
        import time
        
        start_time = time.time()
        
        # Run performance test
        perform_heavy_operation()
        
        execution_time = time.time() - start_time
        
        # Verify performance
        assert execution_time < 1.0, f"Operation took {execution_time:.2f}s, should be under 1.0s"
```

### Best Practices

1. **Test Organization**:
   - Group related tests in classes
   - Use descriptive test names
   - Follow AAA pattern (Arrange, Act, Assert)

2. **Test Independence**:
   - Each test should be independent
   - Use fixtures for setup/teardown
   - Don't rely on test execution order

3. **Mock External Dependencies**:
   - Mock all external APIs and services
   - Use realistic mock data
   - Test both success and failure scenarios

4. **Performance Testing**:
   - Set clear performance thresholds
   - Test with realistic data volumes
   - Monitor resource usage

5. **Error Testing**:
   - Test error conditions and edge cases
   - Validate error messages and types
   - Test recovery mechanisms

## 🔍 Test Analysis and Reporting

### Coverage Analysis

```bash
# View uncovered lines
pytest --cov=modules --cov-report=term-missing

# Generate detailed HTML report
pytest --cov=modules --cov-report=html
open htmlcov/index.html

# Find files with low coverage
pytest --cov=modules --cov-report=term --cov-fail-under=90
```

### Performance Analysis

```bash
# Profile test execution
pytest --profile

# Run performance tests with detailed output
pytest -m "performance" -v --tb=short

# Monitor resource usage during tests
pytest -m "performance" --capture=no
```

### Test Report Generation

```bash
# Generate HTML test report
pytest --html=report.html --self-contained-html

# Generate JUnit XML for CI
pytest --junitxml=junit.xml

# Generate JSON report
pytest --json-report --json-report-file=report.json
```

## 🆘 Troubleshooting

### Common Issues

**Tests fail with import errors**:
```bash
# Add current directory to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest
```

**Database connection issues**:
```bash
# Run with isolated database
pytest --tb=short -k "not integration"
```

**Slow test execution**:
```bash
# Run tests in parallel
pip install pytest-xdist
pytest -n auto

# Skip slow tests during development
pytest -m "not slow"
```

**Memory issues during testing**:
```bash
# Run tests with memory profiling
pip install memory-profiler
pytest --profile-svg
```

### Getting Help

1. Check test logs in `test-reports/` directory
2. Run tests with verbose output: `pytest -v`
3. Use debugging: `pytest --pdb` 
4. Check CI build logs for detailed error information

## 📚 Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Python Testing Best Practices](https://realpython.com/python-testing/)
- [Mock Object Documentation](https://docs.python.org/3/library/unittest.mock.html)

---

## 📈 Test Metrics and Goals

| Metric | Target | Current |
|--------|--------|---------|
| **Code Coverage** | ≥ 80% | 🎯 |
| **Test Count** | 200+ tests | ✅ |
| **Test Execution Time** | < 2 minutes | ⚡ |
| **Performance Test Coverage** | 100% critical paths | 📊 |
| **Integration Test Coverage** | All external APIs | 🔗 |

**Quality Gates**:
- ✅ All tests must pass before merging
- ✅ Coverage must be ≥ 80%  
- ✅ No security vulnerabilities
- ✅ Performance tests within thresholds
- ✅ Code quality checks pass