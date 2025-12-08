#!/usr/bin/env python3
"""
Test Coverage Analyzer and Quality Assessment Tool
Analyzes test coverage, quality metrics, and generates comprehensive reports
"""

import sys
import json
import xml.etree.ElementTree as ET
from pathlib import Path
import subprocess
from datetime import datetime
import re
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class TestMetrics:
    """Test metrics data structure"""

    total_tests: int = 0
    passed_tests: int = 0
    failed_tests: int = 0
    skipped_tests: int = 0
    error_tests: int = 0
    execution_time: float = 0.0
    pass_rate: float = 0.0


@dataclass
class CoverageMetrics:
    """Coverage metrics data structure"""

    line_coverage: float = 0.0
    branch_coverage: float = 0.0
    function_coverage: float = 0.0
    statement_coverage: float = 0.0
    covered_lines: int = 0
    total_lines: int = 0
    missing_lines: List[int] = None

    def __post_init__(self):
        if self.missing_lines is None:
            self.missing_lines = []


@dataclass
class QualityMetrics:
    """Code quality metrics"""

    complexity_score: float = 0.0
    maintainability_index: float = 0.0
    code_smells: int = 0
    security_hotspots: int = 0
    duplication_ratio: float = 0.0
    technical_debt: float = 0.0


@dataclass
class ModuleAnalysis:
    """Per-module analysis results"""

    module_name: str
    file_path: str
    test_metrics: TestMetrics
    coverage_metrics: CoverageMetrics
    quality_metrics: QualityMetrics
    test_files: List[str] = None

    def __post_init__(self):
        if self.test_files is None:
            self.test_files = []


class TestCoverageAnalyzer:
    """Comprehensive test coverage and quality analyzer"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.modules_dir = self.project_root / "modules"
        self.tests_dir = self.project_root / "tests"
        self.reports_dir = self.project_root / "test-reports"
        self.reports_dir.mkdir(exist_ok=True)

    def run_comprehensive_analysis(self) -> Dict[str, Any]:
        """Run comprehensive test coverage and quality analysis"""
        logger.info("🔍 Starting comprehensive test coverage analysis...")

        analysis_results = {
            "timestamp": datetime.now().isoformat(),
            "project_overview": self._analyze_project_structure(),
            "test_execution": self._run_test_suite_with_coverage(),
            "coverage_analysis": self._analyze_coverage_results(),
            "quality_assessment": self._assess_code_quality(),
            "module_analysis": self._analyze_modules(),
            "gap_analysis": self._identify_testing_gaps(),
            "recommendations": self._generate_recommendations(),
        }

        # Generate reports
        self._generate_comprehensive_report(analysis_results)

        return analysis_results

    def _analyze_project_structure(self) -> Dict[str, Any]:
        """Analyze project structure and identify files to test"""
        logger.info("📁 Analyzing project structure...")

        # Count Python files in modules
        module_files = list(self.modules_dir.glob("*.py"))
        test_files = list(self.tests_dir.glob("test_*.py"))

        # Identify untested modules
        tested_modules = set()
        for test_file in test_files:
            # Extract module name from test file
            test_name = test_file.name
            if test_name.startswith("test_"):
                module_name = test_name[5:-3]  # Remove 'test_' prefix and '.py' suffix
                tested_modules.add(module_name)

        module_names = {f.stem for f in module_files if f.name != "__init__.py"}
        untested_modules = module_names - tested_modules

        return {
            "total_modules": len(module_files),
            "total_test_files": len(test_files),
            "tested_modules": len(tested_modules),
            "untested_modules": list(untested_modules),
            "test_to_module_ratio": (
                len(test_files) / len(module_files) if module_files else 0
            ),
            "module_files": [
                str(f.relative_to(self.project_root)) for f in module_files
            ],
            "test_files": [str(f.relative_to(self.project_root)) for f in test_files],
        }

    def _run_test_suite_with_coverage(self) -> Dict[str, Any]:
        """Run complete test suite with coverage analysis"""
        logger.info("🧪 Running test suite with coverage analysis...")

        # Run pytest with coverage
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            str(self.tests_dir),
            "--cov=modules",
            "--cov-report=xml:coverage.xml",
            "--cov-report=html:htmlcov",
            "--cov-report=json:coverage.json",
            "--cov-report=term-missing",
            "--junitxml=test-results.xml",
            "--json-report",
            "--json-report-file=test-results.json",
            "--tb=short",
            "-v",
        ]

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout
            )

            # Parse results
            test_metrics = self._parse_test_results(result)

            return {
                "command_executed": " ".join(cmd),
                "return_code": result.returncode,
                "execution_successful": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "test_metrics": asdict(test_metrics),
            }

        except subprocess.TimeoutExpired:
            return {"error": "Test execution timed out", "timeout_seconds": 600}
        except Exception as e:
            return {"error": f"Test execution failed: {str(e)}"}

    def _parse_test_results(self, result: subprocess.CompletedProcess) -> TestMetrics:
        """Parse pytest output for test metrics"""
        metrics = TestMetrics()

        # Parse from stdout
        output_lines = result.stdout.split("\n")
        for line in output_lines:
            if "passed" in line and "failed" in line:
                # Line like: "5 passed, 2 failed, 1 skipped in 10.5s"
                parts = line.split()
                for i, part in enumerate(parts):
                    if i > 0:  # Skip first part
                        if parts[i - 1].isdigit():
                            count = int(parts[i - 1])
                            if part == "passed":
                                metrics.passed_tests = count
                            elif part == "failed":
                                metrics.failed_tests = count
                            elif part == "skipped":
                                metrics.skipped_tests = count
                            elif part == "error" or part == "errors":
                                metrics.error_tests = count

                # Extract execution time
                time_match = re.search(r"in ([\d.]+)s", line)
                if time_match:
                    metrics.execution_time = float(time_match.group(1))

        # Parse from JUnit XML if available
        junit_file = self.project_root / "test-results.xml"
        if junit_file.exists():
            junit_metrics = self._parse_junit_xml(junit_file)
            if junit_metrics.total_tests > metrics.total_tests:
                metrics = junit_metrics

        # Calculate totals and rates
        metrics.total_tests = (
            metrics.passed_tests
            + metrics.failed_tests
            + metrics.skipped_tests
            + metrics.error_tests
        )
        if metrics.total_tests > 0:
            metrics.pass_rate = (metrics.passed_tests / metrics.total_tests) * 100

        return metrics

    def _parse_junit_xml(self, junit_file: Path) -> TestMetrics:
        """Parse JUnit XML for detailed test metrics"""
        try:
            tree = ET.parse(junit_file)
            root = tree.getroot()

            metrics = TestMetrics()

            # Find testsuite element
            testsuite = root if root.tag == "testsuite" else root.find("testsuite")
            if testsuite is not None:
                metrics.total_tests = int(testsuite.get("tests", 0))
                metrics.failed_tests = int(testsuite.get("failures", 0))
                metrics.error_tests = int(testsuite.get("errors", 0))
                metrics.skipped_tests = int(testsuite.get("skipped", 0))
                metrics.passed_tests = (
                    metrics.total_tests
                    - metrics.failed_tests
                    - metrics.error_tests
                    - metrics.skipped_tests
                )
                metrics.execution_time = float(testsuite.get("time", 0))

                if metrics.total_tests > 0:
                    metrics.pass_rate = (
                        metrics.passed_tests / metrics.total_tests
                    ) * 100

            return metrics

        except Exception as e:
            logger.info(f"⚠️  Could not parse JUnit XML: {e}")
            return TestMetrics()

    def _analyze_coverage_results(self) -> Dict[str, Any]:
        """Analyze coverage results from various report formats"""
        logger.info("📊 Analyzing coverage results...")

        coverage_data = {}

        # Parse XML coverage report
        xml_coverage = self._parse_coverage_xml()
        if xml_coverage:
            coverage_data["xml_report"] = xml_coverage

        # Parse JSON coverage report
        json_coverage = self._parse_coverage_json()
        if json_coverage:
            coverage_data["json_report"] = json_coverage

        # Analyze coverage by module
        module_coverage = self._analyze_module_coverage()
        coverage_data["module_coverage"] = module_coverage

        # Identify coverage gaps
        coverage_gaps = self._identify_coverage_gaps()
        coverage_data["coverage_gaps"] = coverage_gaps

        return coverage_data

    def _parse_coverage_xml(self) -> Optional[Dict[str, Any]]:
        """Parse XML coverage report"""
        xml_file = self.project_root / "coverage.xml"
        if not xml_file.exists():
            return None

        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()

            # Get overall coverage
            coverage_elem = root.find(".//coverage")
            if coverage_elem is not None:
                line_rate = float(coverage_elem.get("line-rate", 0)) * 100
                branch_rate = float(coverage_elem.get("branch-rate", 0)) * 100
            else:
                line_rate = branch_rate = 0

            # Get package/module coverage
            packages = []
            for package in root.findall(".//package"):
                package_data = {
                    "name": package.get("name"),
                    "line_rate": float(package.get("line-rate", 0)) * 100,
                    "branch_rate": float(package.get("branch-rate", 0)) * 100,
                    "classes": [],
                }

                for class_elem in package.findall(".//class"):
                    class_data = {
                        "name": class_elem.get("name"),
                        "filename": class_elem.get("filename"),
                        "line_rate": float(class_elem.get("line-rate", 0)) * 100,
                        "branch_rate": float(class_elem.get("branch-rate", 0)) * 100,
                    }
                    package_data["classes"].append(class_data)

                packages.append(package_data)

            return {
                "overall_line_coverage": line_rate,
                "overall_branch_coverage": branch_rate,
                "packages": packages,
            }

        except Exception as e:
            logger.info(f"⚠️  Could not parse coverage XML: {e}")
            return None

    def _parse_coverage_json(self) -> Optional[Dict[str, Any]]:
        """Parse JSON coverage report"""
        json_file = self.project_root / "coverage.json"
        if not json_file.exists():
            return None

        try:
            with open(json_file) as f:
                data = json.load(f)

            # Extract summary statistics
            totals = data.get("totals", {})

            return {
                "covered_lines": totals.get("covered_lines", 0),
                "num_statements": totals.get("num_statements", 0),
                "percent_covered": totals.get("percent_covered", 0),
                "missing_lines": totals.get("missing_lines", 0),
                "excluded_lines": totals.get("excluded_lines", 0),
                "files": data.get("files", {}),
            }

        except Exception as e:
            logger.info(f"⚠️  Could not parse coverage JSON: {e}")
            return None

    def _analyze_module_coverage(self) -> Dict[str, ModuleAnalysis]:
        """Analyze coverage for each module"""
        module_analyses = {}

        # Get list of all Python modules
        for module_file in self.modules_dir.glob("*.py"):
            if module_file.name == "__init__.py":
                continue

            module_name = module_file.stem

            # Find corresponding test files
            test_files = [
                f"test_{module_name}.py",
                f"test_{module_name}_*.py",
                f"*test_{module_name}.py",
            ]

            existing_test_files = []
            for pattern in test_files:
                existing_test_files.extend(self.tests_dir.glob(pattern))

            # Create module analysis
            analysis = ModuleAnalysis(
                module_name=module_name,
                file_path=str(module_file.relative_to(self.project_root)),
                test_metrics=TestMetrics(),
                coverage_metrics=CoverageMetrics(),
                quality_metrics=QualityMetrics(),
                test_files=[
                    str(f.relative_to(self.project_root)) for f in existing_test_files
                ],
            )

            # Get coverage data for this module from JSON report
            coverage_json = self._parse_coverage_json()
            if coverage_json and "files" in coverage_json:
                module_path = str(module_file)
                for file_path, file_data in coverage_json["files"].items():
                    if module_file.name in file_path:
                        analysis.coverage_metrics.line_coverage = file_data.get(
                            "summary", {}
                        ).get("percent_covered", 0)
                        analysis.coverage_metrics.covered_lines = file_data.get(
                            "summary", {}
                        ).get("covered_lines", 0)
                        analysis.coverage_metrics.total_lines = file_data.get(
                            "summary", {}
                        ).get("num_statements", 0)
                        analysis.coverage_metrics.missing_lines = file_data.get(
                            "missing_lines", []
                        )
                        break

            module_analyses[module_name] = analysis

        return module_analyses

    def _identify_coverage_gaps(self) -> Dict[str, Any]:
        """Identify coverage gaps and areas needing attention"""
        gaps = {
            "uncovered_modules": [],
            "low_coverage_modules": [],
            "untested_functions": [],
            "missing_test_files": [],
            "complex_untested_code": [],
        }

        # Analyze each module
        for module_file in self.modules_dir.glob("*.py"):
            if module_file.name == "__init__.py":
                continue

            module_name = module_file.stem

            # Check if module has corresponding test file
            test_file = self.tests_dir / f"test_{module_name}.py"
            if not test_file.exists():
                gaps["missing_test_files"].append(module_name)

            # Analyze module content for functions/classes
            try:
                with open(module_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Find function/class definitions
                functions = re.findall(r"^def\s+(\w+)", content, re.MULTILINE)
                classes = re.findall(r"^class\s+(\w+)", content, re.MULTILINE)

                if functions or classes:
                    # Check coverage for this module
                    coverage_json = self._parse_coverage_json()
                    if coverage_json:
                        file_coverage = None
                        for file_path, file_data in coverage_json.get(
                            "files", {}
                        ).items():
                            if module_name in file_path:
                                file_coverage = file_data.get("summary", {}).get(
                                    "percent_covered", 0
                                )
                                break

                        if file_coverage is not None:
                            if file_coverage == 0:
                                gaps["uncovered_modules"].append(
                                    {
                                        "module": module_name,
                                        "functions": functions,
                                        "classes": classes,
                                    }
                                )
                            elif file_coverage < 50:
                                gaps["low_coverage_modules"].append(
                                    {
                                        "module": module_name,
                                        "coverage": file_coverage,
                                        "functions": functions,
                                        "classes": classes,
                                    }
                                )

            except Exception as e:
                logger.info(f"⚠️  Could not analyze module {module_name}: {e}")

        return gaps

    def _assess_code_quality(self) -> Dict[str, Any]:
        """Assess code quality using various metrics"""
        logger.info("🔍 Assessing code quality...")

        quality_assessment = {
            "static_analysis": self._run_static_analysis(),
            "complexity_analysis": self._analyze_complexity(),
            "security_analysis": self._run_security_analysis(),
            "style_analysis": self._analyze_code_style(),
        }

        return quality_assessment

    def _run_static_analysis(self) -> Dict[str, Any]:
        """Run static analysis tools"""
        results = {}

        # Run flake8
        try:
            result = subprocess.run(
                ["flake8", str(self.modules_dir), "--format=json"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.stdout:
                try:
                    flake8_results = json.loads(result.stdout)
                    results["flake8"] = {
                        "issues_count": len(flake8_results),
                        "issues": flake8_results[:10],  # Top 10 issues
                    }
                except json.JSONDecodeError:
                    results["flake8"] = {"error": "Could not parse flake8 JSON output"}
            else:
                results["flake8"] = {"issues_count": 0, "status": "clean"}

        except Exception as e:
            results["flake8"] = {"error": f"Could not run flake8: {e}"}

        return results

    def _analyze_complexity(self) -> Dict[str, Any]:
        """Analyze code complexity"""
        complexity_results = {}

        # Run radon for complexity analysis
        try:
            result = subprocess.run(
                ["radon", "cc", str(self.modules_dir), "--json"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.stdout:
                try:
                    radon_results = json.loads(result.stdout)

                    # Calculate average complexity
                    total_complexity = 0
                    function_count = 0

                    for file_path, functions in radon_results.items():
                        for func in functions:
                            total_complexity += func.get("complexity", 0)
                            function_count += 1

                    avg_complexity = (
                        total_complexity / function_count if function_count > 0 else 0
                    )

                    complexity_results["radon"] = {
                        "average_complexity": avg_complexity,
                        "total_functions": function_count,
                        "high_complexity_functions": [
                            func
                            for file_funcs in radon_results.values()
                            for func in file_funcs
                            if func.get("complexity", 0) > 10
                        ][
                            :5
                        ],  # Top 5 most complex functions
                    }

                except json.JSONDecodeError:
                    complexity_results["radon"] = {
                        "error": "Could not parse radon output"
                    }

        except Exception as e:
            complexity_results["radon"] = {"error": f"Could not run radon: {e}"}

        return complexity_results

    def _run_security_analysis(self) -> Dict[str, Any]:
        """Run security analysis"""
        security_results = {}

        # Run bandit for security analysis
        try:
            result = subprocess.run(
                ["bandit", "-r", str(self.modules_dir), "-", "json"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.stdout:
                try:
                    bandit_results = json.loads(result.stdout)

                    security_results["bandit"] = {
                        "total_issues": len(bandit_results.get("results", [])),
                        "high_severity": len(
                            [
                                issue
                                for issue in bandit_results.get("results", [])
                                if issue.get("issue_severity") == "HIGH"
                            ]
                        ),
                        "medium_severity": len(
                            [
                                issue
                                for issue in bandit_results.get("results", [])
                                if issue.get("issue_severity") == "MEDIUM"
                            ]
                        ),
                        "low_severity": len(
                            [
                                issue
                                for issue in bandit_results.get("results", [])
                                if issue.get("issue_severity") == "LOW"
                            ]
                        ),
                        "top_issues": bandit_results.get("results", [])[:5],
                    }

                except json.JSONDecodeError:
                    security_results["bandit"] = {
                        "error": "Could not parse bandit output"
                    }

        except Exception as e:
            security_results["bandit"] = {"error": f"Could not run bandit: {e}"}

        return security_results

    def _analyze_code_style(self) -> Dict[str, Any]:
        """Analyze code style compliance"""
        style_results = {}

        # Run black in check mode
        try:
            result = subprocess.run(
                ["black", "--check", "--di", str(self.modules_dir)],
                capture_output=True,
                text=True,
                timeout=60,
            )

            style_results["black"] = {
                "compliant": result.returncode == 0,
                "diff_lines": len(result.stdout.split("\n")) if result.stdout else 0,
            }

        except Exception as e:
            style_results["black"] = {"error": f"Could not run black: {e}"}

        return style_results

    def _analyze_modules(self) -> Dict[str, ModuleAnalysis]:
        """Perform detailed analysis of each module"""
        return self._analyze_module_coverage()

    def _identify_testing_gaps(self) -> Dict[str, Any]:
        """Identify gaps in testing coverage and quality"""
        gaps = self._identify_coverage_gaps()

        # Add additional gap analysis
        gaps["quality_gaps"] = {
            "modules_without_tests": gaps["missing_test_files"],
            "low_coverage_threshold": [
                module
                for module, analysis in self._analyze_module_coverage().items()
                if analysis.coverage_metrics.line_coverage < 70
            ],
            "missing_test_categories": self._identify_missing_test_categories(),
        }

        return gaps

    def _identify_missing_test_categories(self) -> List[str]:
        """Identify missing test categories"""
        existing_test_files = list(self.tests_dir.glob("test_*.py"))

        required_categories = ["unit", "integration", "e2e", "performance", "security"]

        missing_categories = []
        for category in required_categories:
            if not any(category in f.name for f in existing_test_files):
                missing_categories.append(category)

        return missing_categories

    def _generate_recommendations(self) -> List[Dict[str, Any]]:
        """Generate recommendations for improving test coverage and quality"""
        recommendations = []

        # Analyze current state
        gaps = self._identify_testing_gaps()
        coverage_data = self._parse_coverage_json()

        # Coverage recommendations
        if coverage_data and coverage_data.get("percent_covered", 0) < 80:
            recommendations.append(
                {
                    "priority": "HIGH",
                    "category": "Coverage",
                    "title": "Increase overall test coverage",
                    "description": f"Current coverage is {coverage_data.get('percent_covered', 0):.1f}%. Target is 80%+.",
                    "action_items": [
                        "Add tests for uncovered modules",
                        "Focus on critical business logic",
                        "Implement integration tests",
                    ],
                }
            )

        # Missing test files
        if gaps.get("missing_test_files"):
            recommendations.append(
                {
                    "priority": "HIGH",
                    "category": "Test Structure",
                    "title": "Create missing test files",
                    "description": f"Found {len(gaps['missing_test_files'])} modules without test files.",
                    "action_items": [
                        f"Create test file for {module}"
                        for module in gaps["missing_test_files"][:5]
                    ],
                }
            )

        # Low coverage modules
        if gaps.get("low_coverage_modules"):
            recommendations.append(
                {
                    "priority": "MEDIUM",
                    "category": "Coverage",
                    "title": "Improve coverage for specific modules",
                    "description": f"Found {len(gaps['low_coverage_modules'])} modules with low coverage.",
                    "action_items": [
                        f"Improve coverage for {module['module']} (currently {module['coverage']:.1f}%)"
                        for module in gaps["low_coverage_modules"][:3]
                    ],
                }
            )

        # Missing test categories
        missing_categories = gaps.get("quality_gaps", {}).get(
            "missing_test_categories", []
        )
        if missing_categories:
            recommendations.append(
                {
                    "priority": "MEDIUM",
                    "category": "Test Types",
                    "title": "Implement missing test categories",
                    "description": f"Missing test categories: {', '.join(missing_categories)}",
                    "action_items": [
                        f"Implement {category} tests" for category in missing_categories
                    ],
                }
            )

        return recommendations

    def _generate_comprehensive_report(self, analysis_results: Dict[str, Any]):
        """Generate comprehensive analysis report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Generate JSON report
        json_report_path = self.reports_dir / f"coverage_analysis_{timestamp}.json"
        with open(json_report_path, "w") as f:
            json.dump(analysis_results, f, indent=2, default=str)

        # Generate HTML report
        html_report_path = self.reports_dir / f"coverage_analysis_{timestamp}.html"
        self._generate_html_report(analysis_results, html_report_path)

        # Generate markdown summary
        md_report_path = self.reports_dir / f"coverage_summary_{timestamp}.md"
        self._generate_markdown_summary(analysis_results, md_report_path)

        logger.info("📄 Reports generated:")
        logger.info(f"   JSON: {json_report_path}")
        logger.info(f"   HTML: {html_report_path}")
        logger.info(f"   Markdown: {md_report_path}")

    def _generate_html_report(
        self, analysis_results: Dict[str, Any], output_path: Path
    ):
        """Generate HTML report"""
        html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Test Coverage Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f8ff; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .section {{ margin: 20px 0; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }}
        .metric-card {{ background: #f9f9f9; padding: 15px; border-radius: 8px; text-align: center; }}
        .metric-value {{ font-size: 24px; font-weight: bold; color: #2c5aa0; }}
        .metric-label {{ font-size: 14px; color: #666; }}
        .recommendation {{ background: #fff3cd; border-left: 4px solid #ffc107; padding: 10px; margin: 10px 0; }}
        .high-priority {{ border-left-color: #dc3545; background: #f8d7da; }}
        .medium-priority {{ border-left-color: #fd7e14; background: #fff3cd; }}
        .low-priority {{ border-left-color: #28a745; background: #d4edda; }}
        .gap {{ background: #f8f9fa; border: 1px solid #dee2e6; padding: 15px; margin: 10px 0; border-radius: 4px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🧪 Test Coverage Analysis Report</h1>
        <p>Generated: {analysis_results['timestamp']}</p>
        <p>Project: MangaAnime Information Delivery System</p>
    </div>

    <div class="section">
        <h2>📊 Key Metrics</h2>
        <div class="metrics">
            <div class="metric-card">
                <div class="metric-value">{analysis_results.get('test_execution', {}).get('test_metrics', {}).get('total_tests', 0)}</div>
                <div class="metric-label">Total Tests</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{analysis_results.get('test_execution', {}).get('test_metrics', {}).get('pass_rate', 0):.1f}%</div>
                <div class="metric-label">Pass Rate</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{analysis_results.get('coverage_analysis', {}).get('json_report', {}).get('percent_covered', 0):.1f}%</div>
                <div class="metric-label">Line Coverage</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{analysis_results.get('project_overview', {}).get('total_modules', 0)}</div>
                <div class="metric-label">Total Modules</div>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>🎯 Recommendations</h2>
        {self._generate_recommendations_html(analysis_results.get('recommendations', []))}
    </div>

    <div class="section">
        <h2>📋 Coverage Gaps</h2>
        {self._generate_gaps_html(analysis_results.get('gap_analysis', {}))}
    </div>

    <div class="section">
        <h2>📁 Project Structure</h2>
        {self._generate_project_structure_html(analysis_results.get('project_overview', {}))}
    </div>
</body>
</html>
        """

        with open(output_path, "w") as f:
            f.write(html_content)

    def _generate_recommendations_html(
        self, recommendations: List[Dict[str, Any]]
    ) -> str:
        """Generate HTML for recommendations section"""
        if not recommendations:
            return "<p>No specific recommendations at this time.</p>"

        html = ""
        for rec in recommendations:
            priority_class = f"{rec['priority'].lower()}-priority"
            html += """
            <div class="recommendation {priority_class}">
                <h4>{rec['title']} ({rec['priority']} Priority)</h4>
                <p>{rec['description']}</p>
                <ul>
            """
            for item in rec.get("action_items", []):
                html += f"<li>{item}</li>"
            html += "</ul></div>"

        return html

    def _generate_gaps_html(self, gaps: Dict[str, Any]) -> str:
        """Generate HTML for coverage gaps section"""
        html = ""

        if gaps.get("missing_test_files"):
            html += """
            <div class="gap">
                <h4>Missing Test Files ({len(gaps['missing_test_files'])})</h4>
                <ul>
                {''.join(f'<li>{module}</li>' for module in gaps['missing_test_files'])}
                </ul>
            </div>
            """

        if gaps.get("uncovered_modules"):
            html += """
            <div class="gap">
                <h4>Uncovered Modules ({len(gaps['uncovered_modules'])})</h4>
                <ul>
                {''.join(f'<li>{module["module"]} - {len(module["functions"])} functions, {len(module["classes"])} classes</li>' for module in gaps['uncovered_modules'])}
                </ul>
            </div>
            """

        return html or "<p>No significant coverage gaps identified.</p>"

    def _generate_project_structure_html(self, project_overview: Dict[str, Any]) -> str:
        """Generate HTML for project structure section"""
        return """
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Total Modules</td><td>{project_overview.get('total_modules', 0)}</td></tr>
            <tr><td>Total Test Files</td><td>{project_overview.get('total_test_files', 0)}</td></tr>
            <tr><td>Tested Modules</td><td>{project_overview.get('tested_modules', 0)}</td></tr>
            <tr><td>Untested Modules</td><td>{len(project_overview.get('untested_modules', []))}</td></tr>
            <tr><td>Test to Module Ratio</td><td>{project_overview.get('test_to_module_ratio', 0):.2f}</td></tr>
        </table>
        """

    def _generate_markdown_summary(
        self, analysis_results: Dict[str, Any], output_path: Path
    ):
        """Generate markdown summary report"""
        md_content = """# Test Coverage Analysis Summary

Generated: {analysis_results['timestamp']}
Project: MangaAnime Information Delivery System

## 📊 Key Metrics

| Metric | Value |
|--------|--------|
| Total Tests | {analysis_results.get('test_execution', {}).get('test_metrics', {}).get('total_tests', 0)} |
| Pass Rate | {analysis_results.get('test_execution', {}).get('test_metrics', {}).get('pass_rate', 0):.1f}% |
| Line Coverage | {analysis_results.get('coverage_analysis', {}).get('json_report', {}).get('percent_covered', 0):.1f}% |
| Total Modules | {analysis_results.get('project_overview', {}).get('total_modules', 0)} |
| Tested Modules | {analysis_results.get('project_overview', {}).get('tested_modules', 0)} |

## 🎯 Top Recommendations

"""

        for rec in analysis_results.get("recommendations", [])[:3]:
            md_content += """### {rec['title']} ({rec['priority']} Priority)

{rec['description']}

Action Items:
{chr(10).join(f'- {item}' for item in rec.get('action_items', []))}

"""

        md_content += """## 📋 Coverage Gaps

### Missing Test Files
{chr(10).join(f'- {module}' for module in analysis_results.get('gap_analysis', {}).get('missing_test_files', []))}

### Uncovered Modules
{chr(10).join(f'- {module["module"]} ({len(module["functions"])} functions, {len(module["classes"])} classes)' for module in analysis_results.get('gap_analysis', {}).get('uncovered_modules', []))}

## 📈 Next Steps

1. Address high-priority recommendations
2. Implement missing test files
3. Increase coverage for low-coverage modules
4. Set up automated coverage monitoring
5. Establish coverage quality gates in CI/CD

---
*Report generated by Test Coverage Analyzer*
"""

        with open(output_path, "w") as f:

            f.write(md_content)


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Test Coverage Analyzer")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--output-dir", help="Output directory for reports")

    args = parser.parse_args()

    # Initialize analyzer
    analyzer = TestCoverageAnalyzer(args.project_root)

    if args.output_dir:
        analyzer.reports_dir = Path(args.output_dir)
        analyzer.reports_dir.mkdir(exist_ok=True)

    try:
        # Run comprehensive analysis
        results = analyzer.run_comprehensive_analysis()

        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("🎯 ANALYSIS SUMMARY")
        logger.info("=" * 60)

        test_metrics = results.get("test_execution", {}).get("test_metrics", {})
        coverage_data = results.get("coverage_analysis", {}).get("json_report", {})

        logger.info(f"Total Tests: {test_metrics.get('total_tests', 0)}")
        logger.info(f"Pass Rate: {test_metrics.get('pass_rate', 0):.1f}%")
        logger.info(f"Line Coverage: {coverage_data.get('percent_covered', 0):.1f}%")
        logger.info(
            f"Missing Test Files: {len(results.get('gap_analysis', {}).get('missing_test_files', []))}"
        )

        recommendations = results.get("recommendations", [])
        if recommendations:
            logger.info(f"\nTop Recommendation: {recommendations[0]['title']}")

        logger.info(
            "\n✅ Analysis complete! Check the reports directory for detailed results."
        )

    except Exception as e:
        logger.info(f"❌ Analysis failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
