from typing import Any, Dict, List
#!/usr/bin/env python3
"""
Advanced Test Runner for MangaAnime Information Delivery System
Provides comprehensive testing with detailed reporting and analysis
"""

import os
import sys
import subprocess
import argparse
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
import xml.etree.ElementTree as ET


class TestRunner:
    """Advanced test runner with comprehensive features"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.test_dir = self.project_root / "tests"
        self.reports_dir = self.project_root / "test-reports"
        self.reports_dir.mkdir(exist_ok=True)

        # Test categories and their corresponding markers
        self.test_categories = {
            "unit": "unit and not slow",
            "integration": "integration",
            "e2e": "e2e",
            "performance": "performance",
            "security": "security",
            "all": None,
        }

        # Performance thresholds
        self.performance_thresholds = {
            "unit_tests_max_time": 120,  # seconds
            "integration_tests_max_time": 300,  # seconds
            "e2e_tests_max_time": 600,  # seconds
            "performance_tests_max_time": 900,  # seconds
            "min_coverage_percentage": 80,
        }

    def run_tests(self, test_type: str = "all", **kwargs) -> Dict[str, Any]:
        """Run tests with specified type and options"""
        logger.info(f"🧪 Running {test_type} tests...")

        start_time = time.time()

        # Build pytest command
        cmd = self._build_pytest_command(test_type, **kwargs)

        # Execute tests
        result = self._execute_test_command(cmd)

        end_time = time.time()
        execution_time = end_time - start_time

        # Parse results
        test_results = self._parse_test_results(test_type, result, execution_time)

        # Generate reports
        self._generate_reports(test_results, **kwargs)

        # Performance analysis
        if test_type == "performance" or test_type == "all":
            self._analyze_performance_results()

        return test_results

    def _build_pytest_command(self, test_type: str, **kwargs) -> List[str]:
        """Build pytest command with appropriate options"""
        cmd = ["python", "-m", "pytest"]

        # Test directory
        cmd.append(str(self.test_dir))

        # Test markers
        if test_type != "all" and test_type in self.test_categories:
            marker = self.test_categories[test_type]
            if marker:
                cmd.extend(["-m", marker])

        # Verbosity
        if kwargs.get("verbose", False):
            cmd.append("-v")
        else:
            cmd.append("-q")

        # Coverage
        if kwargs.get("coverage", True) and test_type in ["unit", "all"]:
            cmd.extend(
                [
                    "--cov=modules",
                    "--cov-report=html:htmlcov",
                    "--cov-report=xml:coverage.xml",
                    "--cov-report=term-missing",
                ]
            )

            coverage_threshold = kwargs.get("coverage_threshold", 80)
            cmd.extend([f"--cov-fail-under={coverage_threshold}"])

        # Output formats
        output_format = kwargs.get("output_format", "term")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if "html" in output_format:
            cmd.extend(
                [
                    "--html",
                    str(self.reports_dir / f"{test_type}_report_{timestamp}.html"),
                    "--self-contained-html",
                ]
            )

        if "xml" in output_format or "junit" in output_format:
            cmd.extend(
                [
                    "--junitxml",
                    str(self.reports_dir / f"{test_type}_junit_{timestamp}.xml"),
                ]
            )

        if "json" in output_format:
            cmd.extend(
                [
                    "--json-report",
                    "--json-report-file",
                    str(self.reports_dir / f"{test_type}_results_{timestamp}.json"),
                ]
            )

        # Parallel execution
        if kwargs.get("parallel", False):
            workers = kwargs.get("workers", "auto")
            cmd.extend(["-n", str(workers)])

        # Timeout
        if kwargs.get("timeout"):
            cmd.extend(["--timeout", str(kwargs["timeout"])])

        # Fail fast
        if kwargs.get("fail_fast", False):
            cmd.append("--maxfail=1")

        # Custom markers
        if kwargs.get("markers"):
            cmd.extend(["-m", kwargs["markers"]])

        # Performance benchmarks
        if test_type == "performance":
            cmd.extend(
                [
                    "--benchmark-json",
                    str(self.reports_dir / f"benchmark_{timestamp}.json"),
                    "--benchmark-histogram",
                    str(self.reports_dir / f"benchmark_histogram_{timestamp}"),
                ]
            )

        return cmd

    def _execute_test_command(self, cmd: List[str]) -> subprocess.CompletedProcess:
        """Execute test command and capture output"""
        logger.info(f"📋 Command: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=3600,  # 1 hour timeout
            )
            return result
        except subprocess.TimeoutExpired:
            logger.info("⏰ Test execution timed out!")
            raise
        except Exception as e:
            logger.info(f"❌ Test execution failed: {e}")
            raise

    def _parse_test_results(
        self, test_type: str, result: subprocess.CompletedProcess, execution_time: float
    ) -> Dict[str, Any]:
        """Parse test execution results"""

        # Basic result info
        test_results = {
            "test_type": test_type,
            "execution_time": execution_time,
            "return_code": result.returncode,
            "passed": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "timestamp": datetime.now().isoformat(),
        }

        # Parse pytest output for test counts
        stdout_lines = result.stdout.split("\n")
        for line in stdout_lines:
            if "passed" in line and "failed" in line:
                # Parse line like: "5 passed, 2 failed, 1 skipped in 10.5s"
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == "passed":
                        test_results["tests_passed"] = int(parts[i - 1])
                    elif part == "failed":
                        test_results["tests_failed"] = int(parts[i - 1])
                    elif part == "skipped":
                        test_results["tests_skipped"] = int(parts[i - 1])
                    elif part == "error" or part == "errors":
                        test_results["tests_error"] = int(parts[i - 1])

        # Parse coverage information
        if "--cov" in result.stdout:
            coverage_match = None
            for line in stdout_lines:
                if "TOTAL" in line and "%" in line:
                    parts = line.split()
                    for part in parts:
                        if part.endswith("%"):
                            coverage_match = part.rstrip("%")
                            break

            if coverage_match:
                test_results["coverage_percentage"] = float(coverage_match)

        # Parse JUnit XML if available
        junit_files = list(self.reports_dir.glob("*junit*.xml"))
        if junit_files:
            latest_junit = max(junit_files, key=os.path.getctime)
            junit_data = self._parse_junit_xml(latest_junit)
            test_results.update(junit_data)

        return test_results

    def _parse_junit_xml(self, junit_file: Path) -> Dict[str, Any]:
        """Parse JUnit XML file for detailed test information"""
        try:
            tree = ET.parse(junit_file)
            root = tree.getroot()

            # Extract testsuite attributes
            testsuite = root if root.tag == "testsuite" else root.find("testsuite")
            if testsuite is not None:
                return {
                    "junit_tests": int(testsuite.get("tests", 0)),
                    "junit_failures": int(testsuite.get("failures", 0)),
                    "junit_errors": int(testsuite.get("errors", 0)),
                    "junit_skipped": int(testsuite.get("skipped", 0)),
                    "junit_time": float(testsuite.get("time", 0)),
                }
        except Exception as e:
            logger.info(f"⚠️  Could not parse JUnit XML: {e}")

        return {}

    def _generate_reports(self, test_results: Dict[str, Any], **kwargs):
        """Generate comprehensive test reports"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # JSON report
        json_report_path = self.reports_dir / f"test_summary_{timestamp}.json"
        with open(json_report_path, "w") as f:
            json.dump(test_results, f, indent=2)

        # HTML summary report
        if kwargs.get("generate_html_summary", True):
            self._generate_html_summary(test_results, timestamp)

        # Performance analysis
        if test_results["test_type"] == "performance":
            self._generate_performance_analysis(test_results, timestamp)

        # Quality metrics report
        self._generate_quality_metrics_report(test_results, timestamp)

        logger.info(f"📄 Reports generated in: {self.reports_dir}")

    def _generate_html_summary(self, test_results: Dict[str, Any], timestamp: str):
        """Generate HTML summary report"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Summary - {test_results['test_type'].upper()}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .success {{ color: green; }}
                .failure {{ color: red; }}
                .warning {{ color: orange; }}
                .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
                .metric-card {{ background: #f9f9f9; padding: 15px; border-radius: 5px; text-align: center; }}
                .metric-value {{ font-size: 24px; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>MangaAnime System - {test_results['test_type'].upper()} Test Report</h1>
                <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p class="{'success' if test_results['passed'] else 'failure'}">
                    Status: {'✅ PASSED' if test_results['passed'] else '❌ FAILED'}
                </p>
            </div>

            <div class="metrics">
                <div class="metric-card">
                    <div class="metric-value">{test_results.get('tests_passed', 0)}</div>
                    <div>Tests Passed</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{test_results.get('tests_failed', 0)}</div>
                    <div>Tests Failed</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{test_results.get('tests_skipped', 0)}</div>
                    <div>Tests Skipped</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{test_results['execution_time']:.1f}s</div>
                    <div>Execution Time</div>
                </div>
                {f'<div class="metric-card"><div class="metric-value">{test_results.get("coverage_percentage", 0):.1f}%</div><div>Code Coverage</div></div>' if 'coverage_percentage' in test_results else ''}
            </div>

            <h2>Test Output</h2>
            <pre style="background: #f0f0f0; padding: 15px; border-radius: 5px; overflow-x: auto;">
{test_results['stdout']}
            </pre>

            {f'<h2>Error Output</h2><pre style="background: #ffe6e6; padding: 15px; border-radius: 5px; overflow-x: auto;">{test_results["stderr"]}</pre>' if test_results['stderr'] else ''}
        </body>
        </html>
        """

        html_report_path = self.reports_dir / f"summary_{timestamp}.html"
        with open(html_report_path, "w") as f:
            f.write(html_content)

    def _generate_performance_analysis(
        self, test_results: Dict[str, Any], timestamp: str
    ):
        """Generate performance analysis report"""
        # Look for benchmark JSON files
        benchmark_files = list(self.reports_dir.glob("benchmark_*.json"))
        if not benchmark_files:
            return

        latest_benchmark = max(benchmark_files, key=os.path.getctime)

        try:
            with open(latest_benchmark) as f:
                benchmark_data = json.load(f)

            analysis = {
                "timestamp": timestamp,
                "test_results": test_results,
                "benchmarks": benchmark_data,
                "performance_summary": self._analyze_benchmark_data(benchmark_data),
            }

            analysis_path = self.reports_dir / f"performance_analysis_{timestamp}.json"
            with open(analysis_path, "w") as f:
                json.dump(analysis, f, indent=2)

        except Exception as e:
            logger.info(f"⚠️  Could not analyze performance data: {e}")

    def _analyze_benchmark_data(self, benchmark_data: Dict) -> Dict[str, Any]:
        """Analyze benchmark data for insights"""
        if "benchmarks" not in benchmark_data:
            return {}

        benchmarks = benchmark_data["benchmarks"]

        # Calculate summary statistics
        mean_times = [b["stats"]["mean"] for b in benchmarks]
        max_times = [b["stats"]["max"] for b in benchmarks]
        min_times = [b["stats"]["min"] for b in benchmarks]

        return {
            "total_benchmarks": len(benchmarks),
            "avg_mean_time": sum(mean_times) / len(mean_times) if mean_times else 0,
            "slowest_test": max(max_times) if max_times else 0,
            "fastest_test": min(min_times) if min_times else 0,
            "performance_warnings": [
                b["name"]
                for b in benchmarks
                if b["stats"]["mean"] > 1.0  # Tests taking more than 1 second
            ],
        }

    def _generate_quality_metrics_report(
        self, test_results: Dict[str, Any], timestamp: str
    ):
        """Generate quality metrics report"""
        metrics = {
            "timestamp": timestamp,
            "test_type": test_results["test_type"],
            "quality_score": self._calculate_quality_score(test_results),
            "metrics": {
                "test_pass_rate": self._calculate_pass_rate(test_results),
                "execution_time": test_results["execution_time"],
                "coverage_percentage": test_results.get("coverage_percentage", 0),
            },
            "recommendations": self._generate_recommendations(test_results),
        }

        metrics_path = self.reports_dir / f"quality_metrics_{timestamp}.json"
        with open(metrics_path, "w") as f:
            json.dump(metrics, f, indent=2)

    def _calculate_quality_score(self, test_results: Dict[str, Any]) -> float:
        """Calculate overall quality score"""
        score = 100.0

        # Deduct for failed tests
        if "tests_failed" in test_results and test_results["tests_failed"] > 0:
            total_tests = test_results.get("tests_passed", 0) + test_results.get(
                "tests_failed", 0
            )
            if total_tests > 0:
                failure_rate = test_results["tests_failed"] / total_tests
                score -= failure_rate * 50  # Up to 50 points deduction

        # Deduct for low coverage
        coverage = test_results.get("coverage_percentage", 0)
        if coverage < 80:
            score -= (80 - coverage) * 0.5  # 0.5 points per percent below 80%

        # Deduct for long execution time
        execution_time = test_results["execution_time"]
        max_time = self.performance_thresholds.get(
            f"{test_results['test_type']}_tests_max_time", 300
        )
        if execution_time > max_time:
            score -= min(20, (execution_time - max_time) / max_time * 20)

        return max(0, score)

    def _calculate_pass_rate(self, test_results: Dict[str, Any]) -> float:
        """Calculate test pass rate"""
        passed = test_results.get("tests_passed", 0)
        failed = test_results.get("tests_failed", 0)
        total = passed + failed

        return (passed / total * 100) if total > 0 else 0

    def _generate_recommendations(self, test_results: Dict[str, Any]) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []

        # Test failures
        if test_results.get("tests_failed", 0) > 0:
            recommendations.append("Fix failing tests before deployment")

        # Coverage
        coverage = test_results.get("coverage_percentage", 0)
        if coverage < 80:
            recommendations.append(
                f"Increase test coverage from {coverage}% to at least 80%"
            )

        # Performance
        execution_time = test_results["execution_time"]
        max_time = self.performance_thresholds.get(
            f"{test_results['test_type']}_tests_max_time", 300
        )
        if execution_time > max_time:
            recommendations.append(
                f"Optimize test execution time (current: {execution_time}s, target: <{max_time}s)"
            )

        # Error output
        if test_results.get("stderr"):
            recommendations.append("Investigate and fix error messages in test output")

        return recommendations

    def _analyze_performance_results(self):
        """Analyze performance test results"""
        logger.info("📊 Analyzing performance results...")

        # Look for recent performance reports
        perf_files = list(self.reports_dir.glob("performance_analysis_*.json"))
        if not perf_files:
            return

        latest_perf = max(perf_files, key=os.path.getctime)

        try:
            with open(latest_perf) as f:
                perf_data = json.load(f)

            summary = perf_data.get("performance_summary", {})

            logger.info("🎯 Performance Summary:")
            logger.info(f"   Total benchmarks: {summary.get('total_benchmarks', 0)}")
            logger.info(f"   Average execution time: {summary.get('avg_mean_time', 0):.3f}s")
            logger.info(f"   Slowest test: {summary.get('slowest_test', 0):.3f}s")
            logger.info(f"   Fastest test: {summary.get('fastest_test', 0):.3f}s")

            warnings = summary.get("performance_warnings", [])
            if warnings:
                logger.info(f"⚠️  Slow tests detected: {len(warnings)}")
                for warning in warnings[:5]:  # Show first 5
                    logger.info(f"     - {warning}")

        except Exception as e:
            logger.info(f"⚠️  Could not analyze performance results: {e}")

    def clean_old_reports(self, days: int = 7):
        """Clean old test reports"""
import logging

logger = logging.getLogger(__name__)

        cutoff_date = datetime.now() - timedelta(days=days)

logger = logging.getLogger(__name__)

        cleaned_count = 0

        for report_file in self.reports_dir.iterdir():
            if report_file.is_file():
                file_time = datetime.fromtimestamp(report_file.stat().st_mtime)
                if file_time < cutoff_date:
                    report_file.unlink()
                    cleaned_count += 1

        logger.info(f"🧹 Cleaned {cleaned_count} old report files")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Advanced Test Runner for MangaAnime Information Delivery System"
    )

    parser.add_argument(
        "--type",
        choices=["unit", "integration", "e2e", "performance", "security", "all"],
        default="all",
        help="Type of tests to run",
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--coverage", action="store_true", default=True, help="Generate coverage report"
    )
    parser.add_argument(
        "--coverage-threshold",
        type=int,
        default=80,
        help="Coverage threshold percentage",
    )
    parser.add_argument(
        "--parallel", "-p", action="store_true", help="Run tests in parallel"
    )
    parser.add_argument(
        "--workers", type=str, default="auto", help="Number of parallel workers"
    )
    parser.add_argument(
        "--fail-fast", "-", action="store_true", help="Stop on first failure"
    )
    parser.add_argument("--timeout", type=int, help="Test timeout in seconds")
    parser.add_argument("--markers", "-m", help="Pytest markers to run")
    parser.add_argument(
        "--output-format",
        choices=["term", "html", "xml", "json"],
        default="html",
        help="Output format",
    )
    parser.add_argument(
        "--clean-reports", type=int, help="Clean reports older than N days"
    )

    args = parser.parse_args()

    # Initialize test runner
    runner = TestRunner()

    # Clean old reports if requested
    if args.clean_reports:
        runner.clean_old_reports(args.clean_reports)

    # Run tests
    try:
        logger.info("🚀 Starting advanced test execution...")
        logger.info(f"🎯 Test type: {args.type}")
        logger.info(f"📊 Output format: {args.output_format}")
        logger.info("-" * 60)

        results = runner.run_tests(
            test_type=args.type,
            verbose=args.verbose,
            coverage=args.coverage,
            coverage_threshold=args.coverage_threshold,
            parallel=args.parallel,
            workers=args.workers,
            fail_fast=args.fail_fast,
            timeout=args.timeout,
            markers=args.markers,
            output_format=args.output_format,
            generate_html_summary=True,
        )

        logger.info("-" * 60)
        logger.info("📋 Test Execution Summary:")
        logger.info(f"   Status: {'✅ PASSED' if results['passed'] else '❌ FAILED'}")
        logger.info(f"   Execution time: {results['execution_time']:.1f}s")
        logger.info(f"   Tests passed: {results.get('tests_passed', 0)}")
        logger.info(f"   Tests failed: {results.get('tests_failed', 0)}")
        logger.info(f"   Tests skipped: {results.get('tests_skipped', 0)}")

        if "coverage_percentage" in results:
            logger.info(f"   Coverage: {results['coverage_percentage']:.1f}%")

        # Exit with appropriate code
        sys.exit(0 if results["passed"] else 1)

    except KeyboardInterrupt:
        logger.info("\n⏹️  Test execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.info(f"\n❌ Test execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
