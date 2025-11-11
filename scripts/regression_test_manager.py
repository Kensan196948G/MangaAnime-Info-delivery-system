#!/usr/bin/env python3
"""
Regression Test Manager
Manages baseline data, detects regressions, and provides comparative analysis
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import sqlite3
from dataclasses import dataclass, asdict
import subprocess
import shutil


@dataclass
class RegressionBaseline:
    """Regression test baseline data"""

    timestamp: str
    version: str
    test_results: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    coverage_data: Dict[str, Any]
    system_info: Dict[str, Any]
    data_hash: str = ""

    def __post_init__(self):
        if not self.data_hash:
            data_str = json.dumps(
                {
                    "test_results": self.test_results,
                    "performance_metrics": self.performance_metrics,
                    "coverage_data": self.coverage_data,
                },
                sort_keys=True,
            )
            self.data_hash = hashlib.sha256(data_str.encode()).hexdigest()


@dataclass
class RegressionComparison:
    """Comparison between current and baseline results"""

    current_baseline: RegressionBaseline
    previous_baseline: RegressionBaseline
    test_regressions: List[Dict[str, Any]]
    performance_regressions: List[Dict[str, Any]]
    coverage_regressions: List[Dict[str, Any]]
    improvements: List[Dict[str, Any]]
    overall_score: float
    recommendation: str


class RegressionTestManager:
    """Manages regression testing and baseline comparisons"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.baselines_dir = self.project_root / "test-reports" / "baselines"
        self.baselines_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.baselines_dir / "regression_history.db"
        self.initialize_database()

    def initialize_database(self):
        """Initialize regression tracking database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS baselines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    version TEXT NOT NULL,
                    data_hash TEXT NOT NULL UNIQUE,
                    baseline_data TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS regression_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    comparison_timestamp TEXT NOT NULL,
                    current_baseline_id INTEGER,
                    previous_baseline_id INTEGER,
                    regression_count INTEGER,
                    overall_score REAL,
                    report_data TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (current_baseline_id) REFERENCES baselines (id),
                    FOREIGN KEY (previous_baseline_id) REFERENCES baselines (id)
                )
            """
            )

            conn.commit()

    def create_baseline(self, version: str = "auto") -> RegressionBaseline:
        """Create a new regression baseline"""
        print("📊 Creating regression baseline...")

        if version == "auto":
            version = self._detect_version()

        # Collect current test results
        test_results = self._collect_test_results()
        performance_metrics = self._collect_performance_metrics()
        coverage_data = self._collect_coverage_data()
        system_info = self._collect_system_info()

        # Create baseline
        baseline = RegressionBaseline(
            timestamp=datetime.now().isoformat(),
            version=version,
            test_results=test_results,
            performance_metrics=performance_metrics,
            coverage_data=coverage_data,
            system_info=system_info,
        )

        # Save to database
        self._save_baseline(baseline)

        # Save to file for easy access
        baseline_file = (
            self.baselines_dir / f"baseline_{baseline.timestamp.replace(':', '-')}.json"
        )
        with open(baseline_file, "w") as f:
            json.dump(asdict(baseline), f, indent=2)

        print(f"✅ Baseline created: {baseline.timestamp}")
        return baseline

    def _detect_version(self) -> str:
        """Auto-detect version from git or other sources"""
        try:
            # Try git
            result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )
            if result.returncode == 0:
                return f"git-{result.stdout.strip()}"
        except:
            pass

        # Fallback to timestamp-based version
        return f"auto-{datetime.now().strftime('%Y%m%d-%H%M')}"

    def _collect_test_results(self) -> Dict[str, Any]:
        """Collect current test results"""
        # Run tests and collect results
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            str(self.project_root / "tests"),
            "--json-report",
            "--json-report-file=test-results-regression.json",
            "--tb=no",
            "-q",
        ]

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=self.project_root, timeout=300
            )

            # Load results
            results_file = self.project_root / "test-results-regression.json"
            if results_file.exists():
                with open(results_file) as f:
                    json_data = json.load(f)

                return {
                    "summary": json_data.get("summary", {}),
                    "tests": json_data.get("tests", []),
                    "return_code": result.returncode,
                    "duration": json_data.get("duration", 0),
                }
        except Exception as e:
            print(f"⚠️  Could not collect test results: {e}")

        return {"error": "Could not collect test results"}

    def _collect_performance_metrics(self) -> Dict[str, Any]:
        """Collect performance metrics"""
        # Run performance tests if they exist
        perf_cmd = [
            sys.executable,
            "-m",
            "pytest",
            str(self.project_root / "tests"),
            "-m",
            "performance",
            "--benchmark-json=benchmark-results-regression.json",
            "--tb=no",
            "-q",
        ]

        try:
            result = subprocess.run(
                perf_cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=300,
            )

            # Load benchmark results
            benchmark_file = self.project_root / "benchmark-results-regression.json"
            if benchmark_file.exists():
                with open(benchmark_file) as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️  Could not collect performance metrics: {e}")

        return {"error": "No performance data available"}

    def _collect_coverage_data(self) -> Dict[str, Any]:
        """Collect coverage data"""
        # Run tests with coverage
        cov_cmd = [
            sys.executable,
            "-m",
            "pytest",
            str(self.project_root / "tests"),
            "--cov=modules",
            "--cov-report=json:coverage-regression.json",
            "--tb=no",
            "-q",
        ]

        try:
            result = subprocess.run(
                cov_cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=300,
            )

            # Load coverage results
            coverage_file = self.project_root / "coverage-regression.json"
            if coverage_file.exists():
                with open(coverage_file) as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️  Could not collect coverage data: {e}")

        return {"error": "No coverage data available"}

    def _collect_system_info(self) -> Dict[str, Any]:
        """Collect system information for reproducibility"""
        import platform
        import pkg_resources

        return {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "architecture": platform.architecture(),
            "processor": platform.processor(),
            "installed_packages": {
                pkg.project_name: pkg.version
                for pkg in pkg_resources.working_set
                if pkg.project_name in ["pytest", "coverage", "requests", "flask"]
            },
            "timestamp": datetime.now().isoformat(),
        }

    def _save_baseline(self, baseline: RegressionBaseline):
        """Save baseline to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO baselines 
                (timestamp, version, data_hash, baseline_data)
                VALUES (?, ?, ?, ?)
            """,
                (
                    baseline.timestamp,
                    baseline.version,
                    baseline.data_hash,
                    json.dumps(asdict(baseline)),
                ),
            )
            conn.commit()

    def compare_with_baseline(
        self, baseline_id: Optional[int] = None
    ) -> RegressionComparison:
        """Compare current results with a baseline"""
        print("🔍 Comparing with baseline...")

        # Get previous baseline
        previous_baseline = self._get_baseline(baseline_id)
        if not previous_baseline:
            print("⚠️  No baseline found for comparison")
            return None

        # Create current baseline
        current_baseline = self.create_baseline()

        # Perform comparison
        comparison = self._perform_comparison(current_baseline, previous_baseline)

        # Save comparison report
        self._save_comparison_report(comparison)

        return comparison

    def _get_baseline(
        self, baseline_id: Optional[int] = None
    ) -> Optional[RegressionBaseline]:
        """Get baseline by ID or latest"""
        with sqlite3.connect(self.db_path) as conn:
            if baseline_id:
                cursor = conn.execute(
                    """
                    SELECT baseline_data FROM baselines WHERE id = ?
                """,
                    (baseline_id,),
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT baseline_data FROM baselines 
                    ORDER BY created_at DESC LIMIT 1
                """
                )

            row = cursor.fetchone()
            if row:
                data = json.loads(row[0])
                return RegressionBaseline(**data)

        return None

    def _perform_comparison(
        self, current: RegressionBaseline, previous: RegressionBaseline
    ) -> RegressionComparison:
        """Perform detailed comparison between baselines"""

        test_regressions = self._compare_test_results(current, previous)
        performance_regressions = self._compare_performance_metrics(current, previous)
        coverage_regressions = self._compare_coverage_data(current, previous)
        improvements = self._identify_improvements(current, previous)

        # Calculate overall score
        overall_score = self._calculate_overall_score(
            test_regressions,
            performance_regressions,
            coverage_regressions,
            improvements,
        )

        # Generate recommendation
        recommendation = self._generate_recommendation(
            test_regressions,
            performance_regressions,
            coverage_regressions,
            overall_score,
        )

        return RegressionComparison(
            current_baseline=current,
            previous_baseline=previous,
            test_regressions=test_regressions,
            performance_regressions=performance_regressions,
            coverage_regressions=coverage_regressions,
            improvements=improvements,
            overall_score=overall_score,
            recommendation=recommendation,
        )

    def _compare_test_results(
        self, current: RegressionBaseline, previous: RegressionBaseline
    ) -> List[Dict[str, Any]]:
        """Compare test results for regressions"""
        regressions = []

        current_summary = current.test_results.get("summary", {})
        previous_summary = previous.test_results.get("summary", {})

        # Check for test count changes
        if current_summary.get("total", 0) < previous_summary.get("total", 0):
            regressions.append(
                {
                    "type": "test_count_decrease",
                    "description": f"Test count decreased from {previous_summary.get('total', 0)} to {current_summary.get('total', 0)}",
                    "severity": "high",
                    "current_value": current_summary.get("total", 0),
                    "previous_value": previous_summary.get("total", 0),
                }
            )

        # Check for pass rate changes
        current_passed = current_summary.get("passed", 0)
        current_total = current_summary.get("total", 1)
        previous_passed = previous_summary.get("passed", 0)
        previous_total = previous_summary.get("total", 1)

        current_pass_rate = (
            (current_passed / current_total) * 100 if current_total > 0 else 0
        )
        previous_pass_rate = (
            (previous_passed / previous_total) * 100 if previous_total > 0 else 0
        )

        if current_pass_rate < previous_pass_rate - 5:  # 5% threshold
            regressions.append(
                {
                    "type": "pass_rate_decrease",
                    "description": f"Pass rate decreased from {previous_pass_rate:.1f}% to {current_pass_rate:.1f}%",
                    "severity": "high",
                    "current_value": current_pass_rate,
                    "previous_value": previous_pass_rate,
                }
            )

        # Check for new failures
        current_failed = current_summary.get("failed", 0)
        previous_failed = previous_summary.get("failed", 0)

        if current_failed > previous_failed:
            regressions.append(
                {
                    "type": "new_test_failures",
                    "description": f"New test failures: {current_failed - previous_failed}",
                    "severity": "high",
                    "current_value": current_failed,
                    "previous_value": previous_failed,
                }
            )

        return regressions

    def _compare_performance_metrics(
        self, current: RegressionBaseline, previous: RegressionBaseline
    ) -> List[Dict[str, Any]]:
        """Compare performance metrics for regressions"""
        regressions = []

        current_benchmarks = current.performance_metrics.get("benchmarks", [])
        previous_benchmarks = previous.performance_metrics.get("benchmarks", [])

        # Create lookup for previous benchmarks
        previous_lookup = {b.get("name", ""): b for b in previous_benchmarks}

        # Compare each current benchmark with previous
        for current_bench in current_benchmarks:
            name = current_bench.get("name", "")
            if name in previous_lookup:
                previous_bench = previous_lookup[name]

                current_mean = current_bench.get("stats", {}).get("mean", 0)
                previous_mean = previous_bench.get("stats", {}).get("mean", 0)

                # Check for performance regression (20% slower threshold)
                if current_mean > previous_mean * 1.2:
                    regressions.append(
                        {
                            "type": "performance_regression",
                            "test_name": name,
                            "description": f"{name} performance regressed by {((current_mean / previous_mean - 1) * 100):.1f}%",
                            "severity": "medium",
                            "current_value": current_mean,
                            "previous_value": previous_mean,
                        }
                    )

        return regressions

    def _compare_coverage_data(
        self, current: RegressionBaseline, previous: RegressionBaseline
    ) -> List[Dict[str, Any]]:
        """Compare coverage data for regressions"""
        regressions = []

        current_coverage = current.coverage_data.get("totals", {}).get(
            "percent_covered", 0
        )
        previous_coverage = previous.coverage_data.get("totals", {}).get(
            "percent_covered", 0
        )

        # Check for coverage decrease (5% threshold)
        if current_coverage < previous_coverage - 5:
            regressions.append(
                {
                    "type": "coverage_regression",
                    "description": f"Coverage decreased from {previous_coverage:.1f}% to {current_coverage:.1f}%",
                    "severity": "medium",
                    "current_value": current_coverage,
                    "previous_value": previous_coverage,
                }
            )

        return regressions

    def _identify_improvements(
        self, current: RegressionBaseline, previous: RegressionBaseline
    ) -> List[Dict[str, Any]]:
        """Identify improvements over previous baseline"""
        improvements = []

        # Test improvements
        current_summary = current.test_results.get("summary", {})
        previous_summary = previous.test_results.get("summary", {})

        if current_summary.get("total", 0) > previous_summary.get("total", 0):
            improvements.append(
                {
                    "type": "test_count_increase",
                    "description": f"Test count increased from {previous_summary.get('total', 0)} to {current_summary.get('total', 0)}",
                    "improvement": current_summary.get("total", 0)
                    - previous_summary.get("total", 0),
                }
            )

        # Coverage improvements
        current_coverage = current.coverage_data.get("totals", {}).get(
            "percent_covered", 0
        )
        previous_coverage = previous.coverage_data.get("totals", {}).get(
            "percent_covered", 0
        )

        if current_coverage > previous_coverage + 2:  # 2% improvement threshold
            improvements.append(
                {
                    "type": "coverage_improvement",
                    "description": f"Coverage improved from {previous_coverage:.1f}% to {current_coverage:.1f}%",
                    "improvement": current_coverage - previous_coverage,
                }
            )

        return improvements

    def _calculate_overall_score(
        self,
        test_regressions: List,
        performance_regressions: List,
        coverage_regressions: List,
        improvements: List,
    ) -> float:
        """Calculate overall regression score (0-100, higher is better)"""
        base_score = 100.0

        # Deduct points for regressions
        for regression in test_regressions:
            if regression["severity"] == "high":
                base_score -= 20
            elif regression["severity"] == "medium":
                base_score -= 10
            else:
                base_score -= 5

        for regression in performance_regressions:
            base_score -= 10

        for regression in coverage_regressions:
            base_score -= 15

        # Add points for improvements
        for improvement in improvements:
            base_score += 5

        return max(0, min(100, base_score))

    def _generate_recommendation(
        self,
        test_regressions: List,
        performance_regressions: List,
        coverage_regressions: List,
        overall_score: float,
    ) -> str:
        """Generate recommendation based on regression analysis"""
        if overall_score >= 90:
            return "✅ No significant regressions detected. Safe to proceed."
        elif overall_score >= 70:
            return "⚠️  Minor regressions detected. Review and address before release."
        elif overall_score >= 50:
            return "🚨 Significant regressions detected. Investigation required."
        else:
            return "🔥 Critical regressions detected. Do not release until resolved."

    def _save_comparison_report(self, comparison: RegressionComparison):
        """Save comparison report to database and file"""
        # Save to database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO regression_reports 
                (comparison_timestamp, regression_count, overall_score, report_data)
                VALUES (?, ?, ?, ?)
            """,
                (
                    datetime.now().isoformat(),
                    len(
                        comparison.test_regressions
                        + comparison.performance_regressions
                        + comparison.coverage_regressions
                    ),
                    comparison.overall_score,
                    json.dumps(asdict(comparison), default=str),
                ),
            )
            conn.commit()
            report_id = cursor.lastrowid

        # Save to file
        report_file = (
            self.baselines_dir
            / f"regression_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(report_file, "w") as f:
            json.dump(asdict(comparison), f, indent=2, default=str)

        print(f"📄 Regression report saved: {report_file}")

    def generate_regression_summary_report(self) -> Dict[str, Any]:
        """Generate summary report of all regression tests"""
        with sqlite3.connect(self.db_path) as conn:
            # Get baseline count
            baseline_count = conn.execute("SELECT COUNT(*) FROM baselines").fetchone()[
                0
            ]

            # Get recent reports
            reports = conn.execute(
                """
                SELECT comparison_timestamp, overall_score, regression_count
                FROM regression_reports
                ORDER BY created_at DESC
                LIMIT 10
            """
            ).fetchall()

            # Calculate statistics
            if reports:
                scores = [r[1] for r in reports if r[1] is not None]
                avg_score = sum(scores) / len(scores) if scores else 0
                min_score = min(scores) if scores else 0
                max_score = max(scores) if scores else 0
            else:
                avg_score = min_score = max_score = 0

        return {
            "baseline_count": baseline_count,
            "recent_reports_count": len(reports),
            "average_score": avg_score,
            "min_score": min_score,
            "max_score": max_score,
            "recent_reports": [
                {"timestamp": r[0], "score": r[1], "regression_count": r[2]}
                for r in reports
            ],
            "recommendations": self._generate_summary_recommendations(
                avg_score, reports
            ),
        }

    def _generate_summary_recommendations(
        self, avg_score: float, reports: List
    ) -> List[str]:
        """Generate recommendations based on summary statistics"""
        recommendations = []

        if avg_score < 70:
            recommendations.append("Focus on fixing recurring regression issues")
            recommendations.append(
                "Implement additional regression prevention measures"
            )

        if len(reports) < 3:
            recommendations.append(
                "Create more regression baselines for better tracking"
            )

        if reports:
            recent_scores = [r[1] for r in reports[:3] if r[1] is not None]
            if len(recent_scores) >= 2 and all(
                recent_scores[i] < recent_scores[i + 1]
                for i in range(len(recent_scores) - 1)
            ):
                recommendations.append(
                    "Regression scores are trending downward - investigate root causes"
                )

        return recommendations


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Regression Test Manager")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument(
        "--create-baseline", action="store_true", help="Create new baseline"
    )
    parser.add_argument("--version", default="auto", help="Version for baseline")
    parser.add_argument(
        "--compare", action="store_true", help="Compare with latest baseline"
    )
    parser.add_argument(
        "--baseline-id", type=int, help="Specific baseline ID to compare with"
    )
    parser.add_argument(
        "--summary", action="store_true", help="Generate summary report"
    )

    args = parser.parse_args()

    # Initialize manager
    manager = RegressionTestManager(args.project_root)

    try:
        if args.create_baseline:
            baseline = manager.create_baseline(args.version)
            print(f"✅ Baseline created: {baseline.timestamp}")

        elif args.compare:
            comparison = manager.compare_with_baseline(args.baseline_id)
            if comparison:
                print("\n" + "=" * 60)
                print("🔍 REGRESSION COMPARISON RESULTS")
                print("=" * 60)
                print(f"Overall Score: {comparison.overall_score:.1f}/100")
                print(f"Recommendation: {comparison.recommendation}")

                if comparison.test_regressions:
                    print(f"\n🚨 Test Regressions ({len(comparison.test_regressions)}):")
                    for reg in comparison.test_regressions[:5]:  # Show top 5
                        print(f"  - {reg['description']}")

                if comparison.performance_regressions:
                    print(
                        f"\n⏱️  Performance Regressions ({len(comparison.performance_regressions)}):"
                    )
                    for reg in comparison.performance_regressions[:5]:
                        print(f"  - {reg['description']}")

                if comparison.improvements:
                    print(f"\n✅ Improvements ({len(comparison.improvements)}):")
                    for imp in comparison.improvements[:3]:
                        print(f"  - {imp['description']}")

        elif args.summary:
            summary = manager.generate_regression_summary_report()
            print("\n" + "=" * 60)
            print("📊 REGRESSION TESTING SUMMARY")
            print("=" * 60)
            print(f"Total Baselines: {summary['baseline_count']}")
            print(f"Recent Reports: {summary['recent_reports_count']}")
            print(f"Average Score: {summary['average_score']:.1f}/100")
            print(
                f"Score Range: {summary['min_score']:.1f} - {summary['max_score']:.1f}"
            )

            if summary["recommendations"]:
                print("\n📋 Recommendations:")
                for rec in summary["recommendations"]:
                    print(f"  - {rec}")

        else:
            print("Use --create-baseline, --compare, or --summary")

    except Exception as e:
        print(f"❌ Operation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
