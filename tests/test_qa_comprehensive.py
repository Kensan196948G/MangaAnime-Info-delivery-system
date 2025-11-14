#!/usr/bin/env python3
"""
Comprehensive Quality Assurance testing suite for the Anime/Manga Information Delivery System.
Tests code quality standards, data integrity, performance benchmarks, and system reliability.
"""

import pytest
import json
import sqlite3
import time
from unittest.mock import patch
from pathlib import Path

from modules.qa_validation import (
    CodeQualityValidator,
    DataIntegrityValidator,
    PerformanceValidator,
    QAFramework,
)


class TestCodeQualityValidation:
    """Test code quality validation framework"""

    def test_function_length_validation(self, tmp_path):
        """Test function length validation"""
        test_project = tmp_path / "test_project"
        test_project.mkdir()

        # Create test file with long function
        test_file = test_project / "test_module.py"
        long_function = (
            """
def very_long_function():
    '''A function that is too long'''
"""
            + "\n".join([f"    line_{i} = {i}" for i in range(60)])
            + """
    return line_59
"""
        )
        test_file.write_text(long_function)

        validator = CodeQualityValidator(str(test_project))
        results = validator.validate_code_quality()

        # Should detect long function
        assert results["total_issues"] > 0

        # Check for function length issue
        long_function_issues = [
            issue
            for issue in validator.issues
            if "too long" in issue.description
            and "function" in issue.description.lower()
        ]
        assert len(long_function_issues) > 0

    def test_magic_number_detection(self, tmp_path):
        """Test magic number detection"""
        test_project = tmp_path / "test_project"
        test_project.mkdir()

        test_file = test_project / "test_module.py"
        code_with_magic_numbers = """
def calculate_something():
    # Magic numbers should be detected
    result = value * 3.14159  # Pi - should be constant
    timeout = 30  # Should be configuration
    max_retries = 5  # Should be constant

    # These should be acceptable
    if count > 0:  # 0 is acceptable
        items = items[1:]  # 1 is acceptable
        percentage = (value / 100) * 10  # 100 and 10 should be flagged

    return result + 42  # Magic number
"""
        test_file.write_text(code_with_magic_numbers)

        validator = CodeQualityValidator(str(test_project))
        validator.validate_code_quality()

        # Should detect magic numbers
        magic_number_issues = [
            issue
            for issue in validator.issues
            if "magic number" in issue.description.lower()
        ]
        assert len(magic_number_issues) > 0

    def test_docstring_validation(self, tmp_path):
        """Test docstring presence and quality validation"""
        test_project = tmp_path / "test_project"
        test_project.mkdir()

        test_file = test_project / "test_module.py"
        code_with_docstring_issues = """
def function_without_docstring():
    return "no docstring"

def function_with_short_docstring():
    '''Too short'''
    return "short docstring"

def function_with_good_docstring():
    '''
    This function has a comprehensive docstring that explains
    what it does, its parameters, return value, and provides examples.
    This should meet the minimum length requirements.
    '''
    return "good docstring"

class ClassWithoutDocstring:
    def method(self):
        pass

class ClassWithDocstring:
    '''This class has proper documentation explaining its purpose.'''
    def method(self):
        pass
"""
        test_file.write_text(code_with_docstring_issues)

        validator = CodeQualityValidator(str(test_project))
        validator.validate_code_quality()

        # Should detect missing and insufficient docstrings
        docstring_issues = [
            issue
            for issue in validator.issues
            if "docstring" in issue.description.lower()
        ]
        assert len(docstring_issues) >= 3  # Missing, short, and class without docstring

    def test_code_style_validation(self, tmp_path):
        """Test code style validation"""
        test_project = tmp_path / "test_project"
        test_project.mkdir()

        # Use a filename without 'test' in it to avoid being skipped
        test_file = test_project / "module.py"
        code_with_style_issues = """
# This line is way too long and should be flagged by the line length checker because it exceeds the maximum allowed line length which is typically set to 120 characters
def function_with_issues():
    # TODO: Fix this later
    print("This should use logging instead")  # Print statement issue

    try:
        risky_operation()
    except: pass

    return 123  # Magic number
"""
        test_file.write_text(code_with_style_issues)

        validator = CodeQualityValidator(str(test_project))
        validator.validate_code_quality()

        # Should detect various style issues
        style_issues = validator.issues

        # Check for specific issue types
        issue_descriptions = [issue.description.lower() for issue in style_issues]

        # Should detect long lines
        assert any("line too long" in desc for desc in issue_descriptions)

        # Should detect TODO comments
        assert any("todo" in desc for desc in issue_descriptions)

        # Should detect print statements
        assert any("print" in desc for desc in issue_descriptions)

        # Should detect empty except blocks
        assert any("empty except" in desc for desc in issue_descriptions)

    def test_function_parameter_validation(self, tmp_path):
        """Test function parameter count validation"""
        test_project = tmp_path / "test_project"
        test_project.mkdir()

        test_file = test_project / "test_module.py"
        code_with_parameter_issues = """
def function_with_too_many_params(a, b, c, d, e, f, g, h, i, j):
    '''Function with too many parameters'''
    return a + b + c + d + e + f + g + h + i + j

def function_with_acceptable_params(a, b, c):
    '''Function with acceptable parameter count'''
    return a + b + c
"""
        test_file.write_text(code_with_parameter_issues)

        validator = CodeQualityValidator(str(test_project))
        validator.validate_code_quality()

        # Should detect function with too many parameters
        parameter_issues = [
            issue
            for issue in validator.issues
            if "parameter" in issue.description.lower()
            and "too many" in issue.description.lower()
        ]
        assert len(parameter_issues) > 0

    def test_quality_score_calculation(self, tmp_path):
        """Test quality score calculation"""
        test_project = tmp_path / "test_project"
        test_project.mkdir()

        # Create file with minimal issues
        good_file = test_project / "good_module.py"
        good_code = '''
"""
A well-written module with good code quality.
This module demonstrates proper Python coding practices.
"""

def well_documented_function(param1: str, param2: int) -> str:
    """
    A function with proper documentation and implementation.

    Args:
        param1: A string parameter for processing
        param2: An integer parameter for calculation

    Returns:
        A processed string result

    Example:
        >>> result = well_documented_function("test", some_value)
        >>> return result
        test processed with some_value
    """
    if not param1:
        return "empty"

    result = f"{param1} processed with {param2}"
    return result


class WellDocumentedClass:
    """A class that follows good documentation practices."""

    def __init__(self, value: str):
        """Initialize the class with a value."""
        self.value = value

    def process_value(self) -> str:
        """Process the stored value and return result."""
        return f"Processed: {self.value}"
'''
        good_file.write_text(good_code)

        validator = CodeQualityValidator(str(test_project))
        results = validator.validate_code_quality()

        # Should have high quality score with minimal issues
        assert results["quality_score"] >= 90
        assert results["total_issues"] <= 5  # Allow for a few minor issues

    def test_quality_recommendations(self, tmp_path):
        """Test quality improvement recommendations"""
        test_project = tmp_path / "test_project"
        test_project.mkdir()

        # Create file with various issues
        problematic_file = test_project / "problematic_module.py"
        problematic_code = """
password = "hardcoded_password"  # Security issue
def bad_function():
    # TODO: Implement this
    print("Debug message")
    try:
        dangerous_operation()
    except:
        pass
""" + "\n".join(
            [f"    line_{i} = {i}" for i in range(60)]
        )  # Make function long

        problematic_file.write_text(problematic_code)

        validator = CodeQualityValidator(str(test_project))
        results = validator.validate_code_quality()

        # Should generate recommendations
        recommendations = results["recommendations"]
        assert len(recommendations) > 0

        # Should recommend addressing high-priority issues
        recommendation_text = " ".join(recommendations).lower()
        assert any(
            word in recommendation_text for word in ["fix", "improve", "address"]
        )


class TestDataIntegrityValidation:
    """Test data integrity validation framework"""

    def test_referential_integrity_checking(self, tmp_path):
        """Test referential integrity validation"""
        db_file = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_file))

        # Create tables with all columns the validator expects
        conn.executescript(
            """
            CREATE TABLE works (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                type TEXT NOT NULL,
                official_url TEXT
            );

            CREATE TABLE releases (
                id INTEGER PRIMARY KEY,
                work_id INTEGER,
                release_type TEXT,
                number TEXT,
                platform TEXT,
                release_date TEXT
            );
        """
        )

        # Insert test data with referential integrity issues
        conn.execute(
            "INSERT INTO works (id, title, type) VALUES (1, 'Test Anime', 'anime')"
        )
        conn.execute(
            "INSERT INTO releases (work_id, release_type, number, platform, release_date) VALUES (1, 'episode', '1', 'Netflix', '2024-01-01')"
        )
        conn.execute(
            "INSERT INTO releases (work_id, release_type, number, platform, release_date) VALUES (999, 'episode', '1', 'Netflix', '2024-01-01')"
        )  # Orphaned

        conn.commit()
        conn.close()

        validator = DataIntegrityValidator(str(db_file))
        results = validator.validate_data_integrity()

        # Should detect orphaned releases
        assert results["integrity_issues"] > 0

        # Check for specific referential integrity issues
        integrity_issues = [
            issue
            for issue in validator.issues
            if "reference" in issue.description.lower()
            or "orphaned" in issue.description.lower()
        ]
        assert len(integrity_issues) > 0

    def test_data_consistency_checking(self, tmp_path):
        """Test data consistency validation"""
        db_file = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_file))

        conn.executescript(
            """
            CREATE TABLE works (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                type TEXT NOT NULL,
                official_url TEXT
            );

            CREATE TABLE releases (
                id INTEGER PRIMARY KEY,
                work_id INTEGER,
                release_type TEXT,
                number TEXT,
                platform TEXT,
                release_date TEXT
            );
        """
        )

        # Insert test data with consistency issues
        conn.execute(
            "INSERT INTO works (title, type) VALUES ('', 'anime')"
        )  # Empty title
        conn.execute(
            "INSERT INTO works (title, type) VALUES ('Valid Title', 'invalid_type')"
        )  # Invalid type
        conn.execute("INSERT INTO works (title, type) VALUES ('Normal Title', 'anime')")

        # Invalid release dates
        conn.execute(
            "INSERT INTO releases (work_id, release_type, number, platform, release_date) VALUES (3, 'episode', '1', 'Netflix', '1800-01-01')"
        )  # Too old
        conn.execute(
            "INSERT INTO releases (work_id, release_type, number, platform, release_date) VALUES (3, 'episode', '2', 'Netflix', '2030-01-01')"
        )  # Too future

        conn.commit()
        conn.close()

        validator = DataIntegrityValidator(str(db_file))
        results = validator.validate_data_integrity()

        # Should detect consistency issues
        assert results["integrity_issues"] > 0

        # Check for specific consistency issues
        consistency_issues = [
            issue for issue in validator.issues if issue.category == "data_consistency"
        ]
        assert len(consistency_issues) > 0

    def test_duplicate_data_detection(self, tmp_path):
        """Test duplicate data detection"""
        db_file = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_file))

        conn.executescript(
            """
            CREATE TABLE works (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                type TEXT NOT NULL
            );

            CREATE TABLE releases (
                id INTEGER PRIMARY KEY,
                work_id INTEGER,
                release_type TEXT,
                number TEXT,
                platform TEXT,
                release_date TEXT
            );
        """
        )

        # Insert duplicate data
        conn.execute(
            "INSERT INTO works (title, type) VALUES ('Duplicate Title', 'anime')"
        )
        conn.execute(
            "INSERT INTO works (title, type) VALUES ('Duplicate Title', 'anime')"
        )  # Duplicate
        conn.execute("INSERT INTO works (title, type) VALUES ('Unique Title', 'manga')")

        # Duplicate releases
        conn.execute(
            "INSERT INTO releases (work_id, release_type, number, platform, release_date) VALUES (1, 'episode', '1', 'Netflix', '2024-01-01')"
        )
        conn.execute(
            "INSERT INTO releases (work_id, release_type, number, platform, release_date) VALUES (1, 'episode', '1', 'Netflix', '2024-01-01')"
        )  # Exact duplicate

        conn.commit()
        conn.close()

        validator = DataIntegrityValidator(str(db_file))
        validator.validate_data_integrity()

        # Should detect duplicates
        duplicate_issues = [
            issue
            for issue in validator.issues
            if "duplicate" in issue.description.lower()
        ]
        assert len(duplicate_issues) > 0

    def test_data_completeness_checking(self, tmp_path):
        """Test data completeness validation"""
        db_file = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_file))

        conn.executescript(
            """
            CREATE TABLE works (
                id INTEGER PRIMARY KEY,
                title TEXT,
                type TEXT
            );

            CREATE TABLE releases (
                id INTEGER PRIMARY KEY,
                work_id INTEGER,
                platform TEXT,
                release_date TEXT
            );
        """
        )

        # Insert incomplete data
        conn.execute("INSERT INTO works (title) VALUES ('Title Only')")  # Missing type
        conn.execute("INSERT INTO works (type) VALUES ('anime')")  # Missing title
        conn.execute(
            "INSERT INTO works (title, type) VALUES ('Complete Work', 'anime')"
        )

        # Incomplete releases
        conn.execute(
            "INSERT INTO releases (work_id) VALUES (3)"
        )  # Missing platform and date
        conn.execute(
            "INSERT INTO releases (work_id, platform, release_date) VALUES (3, 'Netflix', '2024-01-01')"
        )

        conn.commit()
        conn.close()

        validator = DataIntegrityValidator(str(db_file))
        validator.validate_data_integrity()

        # Should detect incomplete data
        completeness_issues = [
            issue for issue in validator.issues if issue.category == "data_completeness"
        ]
        assert len(completeness_issues) > 0

    def test_data_format_compliance(self, tmp_path):
        """Test data format compliance validation"""
        db_file = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_file))

        conn.executescript(
            """
            CREATE TABLE works (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                type TEXT NOT NULL,
                official_url TEXT
            );
        """
        )

        # Insert data with format issues
        conn.execute(
            "INSERT INTO works (title, type, official_url) VALUES ('Valid Work', 'anime', 'https://example.com')"
        )
        conn.execute(
            "INSERT INTO works (title, type, official_url) VALUES ('Invalid URL Work', 'anime', 'not-a-url')"
        )
        conn.execute(
            "INSERT INTO works (title, type, official_url) VALUES ('FTP URL Work', 'anime', 'ftp://example.com')"
        )

        conn.commit()
        conn.close()

        validator = DataIntegrityValidator(str(db_file))
        validator.validate_data_integrity()

        # Should detect format issues
        format_issues = [
            issue for issue in validator.issues if issue.category == "data_format"
        ]
        assert len(format_issues) > 0

    def test_integrity_score_calculation(self, tmp_path):
        """Test data integrity score calculation"""
        # Create clean database
        db_file = tmp_path / "clean_test.db"
        conn = sqlite3.connect(str(db_file))

        conn.executescript(
            """
            CREATE TABLE works (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                type TEXT NOT NULL,
                official_url TEXT
            );

            CREATE TABLE releases (
                id INTEGER PRIMARY KEY,
                work_id INTEGER,
                release_type TEXT,
                platform TEXT,
                release_date TEXT
            );
        """
        )

        # Insert clean data
        conn.execute(
            "INSERT INTO works (title, type, official_url) VALUES ('Clean Work', 'anime', 'https://example.com')"
        )
        conn.execute(
            "INSERT INTO releases (work_id, release_type, platform, release_date) VALUES (1, 'episode', 'Netflix', '2024-01-01')"
        )

        conn.commit()
        conn.close()

        validator = DataIntegrityValidator(str(db_file))
        results = validator.validate_data_integrity()

        # Should have high consistency score with clean data
        assert results["consistency_score"] >= 95


class TestPerformanceValidation:
    """Test performance validation framework"""

    def test_database_performance_validation(self, tmp_path):
        """Test database performance validation"""
        db_file = tmp_path / "perf_test.db"
        conn = sqlite3.connect(str(db_file))

        # Create test database with some data
        conn.executescript(
            """
            CREATE TABLE works (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                type TEXT NOT NULL
            );

            CREATE TABLE releases (
                id INTEGER PRIMARY KEY,
                work_id INTEGER,
                release_type TEXT,
                platform TEXT,
                release_date TEXT
            );
        """
        )

        # Insert test data
        for i in range(100):
            conn.execute(
                "INSERT INTO works (title, type) VALUES (?, ?)",
                (f"Test Work {i}", "anime"),
            )
            conn.execute(
                "INSERT INTO releases (work_id, release_type, platform, release_date) VALUES (?, ?, ?, ?)",
                (i + 1, "episode", "Netflix", f"2024-01-{(i % 30) + 1:02d}"),
            )

        conn.commit()
        conn.close()

        # Copy database to test project
        test_project = tmp_path / "test_project"
        test_project.mkdir()
        (test_project / "db.sqlite3").write_bytes(db_file.read_bytes())

        validator = PerformanceValidator(str(test_project))
        results = validator.validate_performance()

        # Should run database performance tests
        db_tests = [
            test
            for test in results["performance_tests"]
            if test["test_name"] == "database_performance"
        ]
        assert len(db_tests) > 0

        # Database queries should be reasonably fast
        db_test = db_tests[0]
        if db_test["passed"]:
            # If test passed, verify performance metrics are reasonable
            details = db_test["details"]
            assert details["simple_query_time_ms"] < 1000  # Less than 1 second
            assert details["join_query_time_ms"] < 2000  # Less than 2 seconds

    @pytest.mark.skipif(
        not pytest.psutil_available if hasattr(pytest, "psutil_available") else False,
        reason="psutil not available",
    )
    def test_memory_performance_validation(self, tmp_path):
        """Test memory performance validation"""
        test_project = tmp_path / "test_project"
        test_project.mkdir()

        validator = PerformanceValidator(str(test_project))
        results = validator.validate_performance()

        # Should run memory performance tests
        memory_tests = [
            test
            for test in results["performance_tests"]
            if test["test_name"] == "memory_performance"
        ]

        if memory_tests:  # Only test if psutil is available
            memory_test = memory_tests[0]

            # Memory usage should be reasonable
            if memory_test["passed"]:
                details = memory_test["details"]
                assert details["memory_increase_mb"] < 100  # Less than 100MB increase

    def test_api_performance_simulation(self, tmp_path):
        """Test API performance simulation"""
        test_project = tmp_path / "test_project"
        test_project.mkdir()

        validator = PerformanceValidator(str(test_project))
        results = validator.validate_performance()

        # Should run API performance simulation
        api_tests = [
            test
            for test in results["performance_tests"]
            if test["test_name"] == "api_performance_simulation"
        ]
        assert len(api_tests) > 0

        api_test = api_tests[0]

        # API simulation should complete in reasonable time
        assert api_test["execution_time"] < 5.0  # Less than 5 seconds

        # Should process data efficiently
        if api_test["passed"]:
            details = api_test["details"]
            assert details["processed_items"] > 0
            assert details["processing_time_seconds"] < 1.0

    def test_performance_bottleneck_detection(self, tmp_path):
        """Test performance bottleneck detection"""
        test_project = tmp_path / "test_project"
        test_project.mkdir()

        # Create scenario that might cause performance issues
        # (This is simulated since we can't easily create real bottlenecks in tests)

        validator = PerformanceValidator(str(test_project))

        # Mock a slow database performance
        with patch.object(validator, "_test_database_performance") as mock_db_test:
            mock_db_test.return_value = {
                "test_name": "database_performance",
                "passed": False,  # Simulate failure
                "details": {
                    "simple_query_time_ms": 1000,  # Slow query
                    "join_query_time_ms": 2000,  # Very slow join
                    "threshold_ms": 500,
                },
                "execution_time": 2.5,
            }

            results = validator.validate_performance()

            # Should detect bottleneck
            assert "database_performance" in results.get("bottlenecks", [])

            # Should provide recommendations
            recommendations = results.get("recommendations", [])
            assert any("database" in rec.lower() for rec in recommendations)

    def test_performance_score_calculation(self, tmp_path):
        """Test performance score calculation"""
        test_project = tmp_path / "test_project"
        test_project.mkdir()

        validator = PerformanceValidator(str(test_project))

        # Mock all tests passing
        with patch.object(
            validator, "_test_database_performance"
        ) as mock_db, patch.object(
            validator, "_test_memory_performance"
        ) as mock_mem, patch.object(
            validator, "_test_api_performance_simulation"
        ) as mock_api:
            mock_db.return_value = {
                "test_name": "database_performance",
                "passed": True,
                "execution_time": 0.1,
            }
            mock_mem.return_value = {
                "test_name": "memory_performance",
                "passed": True,
                "execution_time": 0.1,
            }
            mock_api.return_value = {
                "test_name": "api_performance_simulation",
                "passed": True,
                "execution_time": 0.1,
            }

            validator.performance_tests = [
                mock_db.return_value,
                mock_mem.return_value,
                mock_api.return_value,
            ]

            results = validator._compile_performance_results()

            # Should have perfect score with all tests passing
            assert results["performance_score"] == 100.0
            assert len(results["bottlenecks"]) == 0


class TestIntegratedQAFramework:
    """Test integrated QA framework functionality"""

    def test_comprehensive_qa_audit(self, tmp_path):
        """Test comprehensive QA audit workflow"""
        # Create test project structure
        test_project = tmp_path / "test_project"
        test_project.mkdir()
        (test_project / "modules").mkdir()

        # Create test database
        db_file = test_project / "db.sqlite3"
        conn = sqlite3.connect(str(db_file))
        conn.executescript(
            """
            CREATE TABLE works (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                type TEXT NOT NULL
            );

            CREATE TABLE releases (
                id INTEGER PRIMARY KEY,
                work_id INTEGER,
                release_type TEXT,
                platform TEXT,
                release_date TEXT
            );
        """
        )

        # Insert some test data
        conn.execute("INSERT INTO works (title, type) VALUES ('Test Anime', 'anime')")
        conn.execute(
            "INSERT INTO releases (work_id, release_type, platform, release_date) VALUES (1, 'episode', 'Netflix', '2024-01-01')"
        )
        conn.commit()
        conn.close()

        # Create test Python module
        test_module = test_project / "modules" / "test_module.py"
        test_module.write_text(
            """
def well_written_function(param1: str, param2: int) -> str:
    '''
    A well-documented function that follows coding standards.

    Args:
        param1: String parameter for processing
        param2: Integer parameter for calculation

    Returns:
        Processed string result
    '''
    if not param1:
        return "empty"

    return f"{param1} processed with {param2}"


class TestClass:
    '''A test class for QA validation.'''

    def __init__(self, value: str):
        '''Initialize with value.'''
        self.value = value

    def process(self) -> str:
        '''Process the value.'''
        return f"Processed: {self.value}"
"""
        )

        # Run comprehensive QA audit
        qa_framework = QAFramework(str(test_project))
        results = qa_framework.run_comprehensive_qa_audit()

        # Verify all components ran
        assert "code_quality_results" in results
        assert "data_integrity_results" in results
        assert "performance_results" in results
        assert "overall_score" in results
        assert "summary" in results

        # Should have reasonable overall score
        assert 0 <= results["overall_score"] <= 100

        # Should provide quality level assessment
        assert results["summary"]["quality_level"] in [
            "EXCELLENT",
            "GOOD",
            "ACCEPTABLE",
            "NEEDS_IMPROVEMENT",
            "POOR",
        ]

    def test_qa_report_generation(self, tmp_path):
        """Test QA report generation"""
        # Create minimal test project
        test_project = tmp_path / "test_project"
        test_project.mkdir()
        (test_project / "modules").mkdir()

        # Create minimal database
        db_file = test_project / "db.sqlite3"
        conn = sqlite3.connect(str(db_file))
        conn.execute(
            "CREATE TABLE works (id INTEGER PRIMARY KEY, title TEXT, type TEXT)"
        )
        conn.commit()
        conn.close()

        # Create test module
        (test_project / "modules" / "test.py").write_text("def test(): pass")

        qa_framework = QAFramework(str(test_project))

        # Generate report
        report_file = tmp_path / "qa_report.json"
        qa_framework.generate_qa_report(str(report_file))

        # Verify report was generated
        assert report_file.exists()

        # Load and verify report structure
        with open(report_file, "r") as f:
            report = json.load(f)

        assert "metadata" in report
        assert "executive_summary" in report
        assert "detailed_results" in report
        assert "action_plan" in report
        assert "quality_metrics" in report

        # Verify metadata
        metadata = report["metadata"]
        assert "report_generated" in metadata
        assert "project_path" in metadata
        assert "qa_framework_version" in metadata

        # Verify action plan structure
        action_plan = report["action_plan"]
        assert "immediate_actions" in action_plan
        assert "short_term_goals" in action_plan
        assert "long_term_improvements" in action_plan

    def test_quality_level_classification(self, tmp_path):
        """Test quality level classification"""
        test_project = tmp_path / "test_project"
        test_project.mkdir()

        qa_framework = QAFramework(str(test_project))

        # Test different score ranges
        test_cases = [
            (95, "EXCELLENT"),
            (85, "GOOD"),
            (75, "ACCEPTABLE"),
            (65, "NEEDS_IMPROVEMENT"),
            (45, "POOR"),
        ]

        for score, expected_level in test_cases:
            level = qa_framework._get_quality_level(score)
            assert (
                level == expected_level
            ), f"Score {score} should be {expected_level}, got {level}"

    def test_overall_score_calculation(self, tmp_path):
        """Test overall QA score calculation"""
        test_project = tmp_path / "test_project"
        test_project.mkdir()

        qa_framework = QAFramework(str(test_project))

        # Test score compilation with mock results
        code_results = {"quality_score": 80}
        data_results = {"consistency_score": 90}
        performance_results = {"performance_score": 70}

        compiled = qa_framework._compile_overall_results(
            code_results, data_results, performance_results
        )

        # Should calculate weighted average (40% code, 30% data, 30% performance)
        expected_score = (80 * 0.4) + (90 * 0.3) + (70 * 0.3)
        assert abs(compiled["overall_score"] - expected_score) < 0.1

        # Should include individual scores in summary
        summary = compiled["summary"]
        assert summary["code_quality_score"] == 80
        assert summary["data_integrity_score"] == 90
        assert summary["performance_score"] == 70


class TestQAPerformanceImpact:
    """Test that QA validation doesn't negatively impact system performance"""

    def test_code_quality_validation_performance(self, tmp_path):
        """Test code quality validation performance"""
        test_project = tmp_path / "test_project"
        test_project.mkdir()

        # Create multiple test files
        for i in range(10):
            test_file = test_project / f"module_{i}.py"
            test_file.write_text(
                """
def function_{i}(param):
    '''Function {i} documentation'''
    return param + {i}

class Class{i}:
    '''Class {i} documentation'''
    def method(self):
        return {i}
"""
            )

        validator = CodeQualityValidator(str(test_project))

        start_time = time.time()
        results = validator.validate_code_quality()
        end_time = time.time()

        # Should complete in reasonable time
        validation_time = end_time - start_time
        assert (
            validation_time < 5.0
        ), f"Code quality validation took {validation_time:.2f}s"

        # Should process all files
        assert results["files_analyzed"] > 0

    def test_data_integrity_validation_performance(self, tmp_path):
        """Test data integrity validation performance"""
        db_file = tmp_path / "large_test.db"
        conn = sqlite3.connect(str(db_file))

        # Create tables and insert test data
        conn.executescript(
            """
            CREATE TABLE works (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                type TEXT NOT NULL
            );

            CREATE TABLE releases (
                id INTEGER PRIMARY KEY,
                work_id INTEGER,
                release_type TEXT,
                release_date TEXT
            );
        """
        )

        # Insert larger dataset
        for i in range(1000):
            conn.execute(
                "INSERT INTO works (title, type) VALUES (?, ?)", (f"Work {i}", "anime")
            )
            conn.execute(
                "INSERT INTO releases (work_id, release_type, release_date) VALUES (?, ?, ?)",
                (i + 1, "episode", "2024-01-01"),
            )

        conn.commit()
        conn.close()

        validator = DataIntegrityValidator(str(db_file))

        start_time = time.time()
        validator.validate_data_integrity()
        end_time = time.time()

        # Should complete in reasonable time even with larger dataset
        validation_time = end_time - start_time
        assert (
            validation_time < 10.0
        ), f"Data integrity validation took {validation_time:.2f}s"


@pytest.mark.integration
class TestQAIntegration:
    """Integration tests for QA framework with real system components"""

    def test_qa_with_real_modules(self, tmp_path):
        """Test QA validation with real system modules"""
        # This would test against actual modules in the system
        # For now, we'll simulate with the project structure

        project_root = Path(__file__).parent.parent
        modules_dir = project_root / "modules"

        if modules_dir.exists():
            validator = CodeQualityValidator(str(project_root))
            results = validator.validate_code_quality()

            # Should analyze real modules
            assert results["files_analyzed"] > 0

            # Quality score should be reasonable for real code
            assert results["quality_score"] >= 60  # Minimum acceptable quality


if __name__ == "__main__":
    # Set psutil availability for tests
    try:
        pass

        pytest.psutil_available = True
    except ImportError:
        pytest.psutil_available = False

    pytest.main([__file__, "-v", "--tb=short"])
