#!/usr/bin/env python3
"""
Advanced test coverage analysis and quality gates system
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
import subprocess
import os
import re
from datetime import datetime
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


@dataclass
class CoverageMetrics:
    """Test coverage metrics data structure."""

    module_name: str
    lines_total: int
    lines_covered: int
    lines_missing: int
    coverage_percentage: float
    branches_total: int = 0
    branches_covered: int = 0
    branch_coverage_percentage: float = 0.0
    functions_total: int = 0
    functions_covered: int = 0
    function_coverage_percentage: float = 0.0


@dataclass
class QualityGate:
    """Quality gate configuration."""

    name: str
    metric: str
    threshold: float
    operator: str  # 'gte', 'lte', 'eq'
    severity: str  # 'error', 'warning', 'info'
    description: str


@dataclass
class QualityGateResult:
    """Quality gate evaluation result."""

    gate: QualityGate
    actual_value: float
    passed: bool
    message: str


class CoverageAnalyzer:
    """Advanced test coverage analyzer with quality gates."""

    def __init__(self, project_root: str = None):
        """Initialize coverage analyzer."""
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.coverage_data_dir = self.project_root / "test-reports"
        self.coverage_data_dir.mkdir(exist_ok=True)

        # Default quality gates
        self.quality_gates = [
            QualityGate(
                name="overall_line_coverage",
                metric="line_coverage",
                threshold=80.0,
                operator="gte",
                severity="error",
                description="Overall line coverage must be at least 80%",
            ),
            QualityGate(
                name="critical_modules_coverage",
                metric="critical_module_coverage",
                threshold=90.0,
                operator="gte",
                severity="error",
                description="Critical modules (db, mailer, calendar) must have 90%+ coverage",
            ),
            QualityGate(
                name="branch_coverage",
                metric="branch_coverage",
                threshold=70.0,
                operator="gte",
                severity="warning",
                description="Branch coverage should be at least 70%",
            ),
            QualityGate(
                name="new_code_coverage",
                metric="new_code_coverage",
                threshold=95.0,
                operator="gte",
                severity="error",
                description="New code must have at least 95% coverage",
            ),
            QualityGate(
                name="coverage_regression",
                metric="coverage_change",
                threshold=-5.0,
                operator="gte",
                severity="warning",
                description="Coverage should not decrease by more than 5%",
            ),
        ]

        self.critical_modules = ["db", "mailer", "calendar", "config", "security_utils"]

    def parse_coverage_xml(self, xml_file: Path) -> List[CoverageMetrics]:
        """Parse coverage XML report and extract metrics."""

        if not xml_file.exists():
            raise FileNotFoundError(f"Coverage XML file not found: {xml_file}")

        tree = ET.parse(xml_file)
        root = tree.getroot()

        coverage_data = []

        # Parse packages and classes
        for package in root.findall(".//package"):
            package_name = package.get("name", "").replace("/", ".")

            for class_elem in package.findall(".//class"):
                filename = class_elem.get("filename", "")
                module_name = self._extract_module_name(filename)

                # Get line coverage
                lines = class_elem.find("lines")
                if lines is not None:
                    line_elements = lines.findall("line")
                    lines_total = len(line_elements)
                    lines_covered = len(
                        [l for l in line_elements if l.get("hits", "0") != "0"]
                    )
                    lines_missing = lines_total - lines_covered
                    line_coverage = (
                        (lines_covered / lines_total * 100) if lines_total > 0 else 0
                    )
                else:
                    lines_total = lines_covered = lines_missing = 0
                    line_coverage = 0

                # Get branch coverage (if available)
                branches_total = branches_covered = 0
                branch_coverage = 0

                for line in class_elem.findall('.//line[@branch="true"]'):
                    condition_coverage = line.get("condition-coverage", "")
                    if condition_coverage:
                        # Parse "50% (1/2)" format
                        match = re.search(r"(\d+)/(\d+)", condition_coverage)
                        if match:
                            covered, total = map(int, match.groups())
                            branches_covered += covered
                            branches_total += total

                if branches_total > 0:
                    branch_coverage = branches_covered / branches_total * 100

                coverage_data.append(
                    CoverageMetrics(
                        module_name=module_name,
                        lines_total=lines_total,
                        lines_covered=lines_covered,
                        lines_missing=lines_missing,
                        coverage_percentage=line_coverage,
                        branches_total=branches_total,
                        branches_covered=branches_covered,
                        branch_coverage_percentage=branch_coverage,
                    )
                )

        return coverage_data

    def parse_coverage_json(self, json_file: Path) -> List[CoverageMetrics]:
        """Parse coverage JSON report and extract metrics."""

        if not json_file.exists():
            raise FileNotFoundError(f"Coverage JSON file not found: {json_file}")

        with open(json_file, "r") as f:
            data = json.load(f)

        coverage_data = []

        files = data.get("files", {})
        for filepath, file_data in files.items():
            module_name = self._extract_module_name(filepath)

            summary = file_data.get("summary", {})
            lines = summary.get("lines", {})
            branches = summary.get("branches", {})
            functions = summary.get("functions", {})

            coverage_data.append(
                CoverageMetrics(
                    module_name=module_name,
                    lines_total=lines.get("num_statements", 0),
                    lines_covered=lines.get("covered_lines", 0),
                    lines_missing=lines.get("missing_lines", 0),
                    coverage_percentage=lines.get("percent_covered", 0),
                    branches_total=branches.get("num_branches", 0),
                    branches_covered=branches.get("covered_branches", 0),
                    branch_coverage_percentage=branches.get("percent_covered", 0),
                    functions_total=functions.get("num_functions", 0),
                    functions_covered=functions.get("covered_functions", 0),
                    function_coverage_percentage=functions.get("percent_covered", 0),
                )
            )

        return coverage_data

    def _extract_module_name(self, filepath: str) -> str:
        """Extract module name from file path."""
        # Convert path to module name
        path = Path(filepath)

        # Remove common prefixes and suffixes
        parts = path.parts
        if "modules" in parts:
            idx = parts.index("modules")
            parts = parts[idx + 1:]

        if parts and parts[-1].endswith(".py"):
            parts = parts[:-1] + (parts[-1][:-3],)

        return ".".join(parts) if parts else "unknown"

    def calculate_overall_metrics(
        self, coverage_data: List[CoverageMetrics]
    ) -> Dict[str, float]:
        """Calculate overall coverage metrics."""

        if not coverage_data:
            return {}

        total_lines = sum(m.lines_total for m in coverage_data)
        covered_lines = sum(m.lines_covered for m in coverage_data)
        total_branches = sum(m.branches_total for m in coverage_data)
        covered_branches = sum(m.branches_covered for m in coverage_data)
        total_functions = sum(m.functions_total for m in coverage_data)
        covered_functions = sum(m.functions_covered for m in coverage_data)

        return {
            "line_coverage": (
                (covered_lines / total_lines * 100) if total_lines > 0 else 0
            ),
            "branch_coverage": (
                (covered_branches / total_branches * 100) if total_branches > 0 else 0
            ),
            "function_coverage": (
                (covered_functions / total_functions * 100)
                if total_functions > 0
                else 0
            ),
            "total_lines": total_lines,
            "covered_lines": covered_lines,
            "total_branches": total_branches,
            "covered_branches": covered_branches,
            "total_functions": total_functions,
            "covered_functions": covered_functions,
        }

    def analyze_critical_modules(
        self, coverage_data: List[CoverageMetrics]
    ) -> Dict[str, float]:
        """Analyze coverage for critical modules."""

        critical_coverage = {}

        for module_name in self.critical_modules:
            matching_modules = [
                m for m in coverage_data if module_name in m.module_name.lower()
            ]

            if matching_modules:
                total_lines = sum(m.lines_total for m in matching_modules)
                covered_lines = sum(m.lines_covered for m in matching_modules)
                coverage = (covered_lines / total_lines * 100) if total_lines > 0 else 0
                critical_coverage[module_name] = coverage
            else:
                critical_coverage[module_name] = 0

        return critical_coverage

    def detect_coverage_regression(
        self, current_data: List[CoverageMetrics], baseline_file: Path = None
    ) -> Dict[str, float]:
        """Detect coverage regression compared to baseline."""

        if not baseline_file or not baseline_file.exists():
            return {}

        # Load baseline data
        try:
            if baseline_file.suffix == ".xml":
                baseline_data = self.parse_coverage_xml(baseline_file)
            elif baseline_file.suffix == ".json":
                baseline_data = self.parse_coverage_json(baseline_file)
            else:
                return {}
        except Exception:
            return {}

        # Calculate changes
        current_metrics = self.calculate_overall_metrics(current_data)
        baseline_metrics = self.calculate_overall_metrics(baseline_data)

        changes = {}
        for metric in ["line_coverage", "branch_coverage", "function_coverage"]:
            current_val = current_metrics.get(metric, 0)
            baseline_val = baseline_metrics.get(metric, 0)
            changes[metric] = current_val - baseline_val

        return changes

    def evaluate_quality_gates(
        self, coverage_data: List[CoverageMetrics], baseline_file: Path = None
    ) -> List[QualityGateResult]:
        """Evaluate all quality gates against coverage data."""

        overall_metrics = self.calculate_overall_metrics(coverage_data)
        critical_modules = self.analyze_critical_modules(coverage_data)
        regression_data = self.detect_coverage_regression(coverage_data, baseline_file)

        results = []

        for gate in self.quality_gates:
            actual_value = 0

            if gate.metric == "line_coverage":
                actual_value = overall_metrics.get("line_coverage", 0)
            elif gate.metric == "branch_coverage":
                actual_value = overall_metrics.get("branch_coverage", 0)
            elif gate.metric == "critical_module_coverage":
                # Use minimum coverage of critical modules
                if critical_modules:
                    actual_value = min(critical_modules.values())
            elif gate.metric == "coverage_change":
                actual_value = regression_data.get("line_coverage", 0)
            elif gate.metric == "new_code_coverage":
                # For now, use overall coverage (would need git diff analysis for true new code)
                actual_value = overall_metrics.get("line_coverage", 0)

            # Evaluate gate
            passed = self._evaluate_threshold(
                actual_value, gate.threshold, gate.operator
            )

            message = f"{gate.description}: {actual_value:.1f}% (threshold: {gate.threshold}%)"
            if not passed:
                message = f"FAILED - {message}"
            else:
                message = f"PASSED - {message}"

            results.append(
                QualityGateResult(
                    gate=gate, actual_value=actual_value, passed=passed, message=message
                )
            )

        return results

    def _evaluate_threshold(
        self, value: float, threshold: float, operator: str
    ) -> bool:
        """Evaluate if value meets threshold based on operator."""

        if operator == "gte":
            return value >= threshold
        elif operator == "lte":
            return value <= threshold
        elif operator == "eq":
            return abs(value - threshold) < 0.01  # Small tolerance for float comparison
        else:
            return False

    def generate_coverage_report(
        self,
        coverage_data: List[CoverageMetrics],
        quality_gate_results: List[QualityGateResult],
        output_file: Path = None,
    ) -> Dict[str, Any]:
        """Generate comprehensive coverage report."""

        overall_metrics = self.calculate_overall_metrics(coverage_data)
        critical_modules = self.analyze_critical_modules(coverage_data)

        # Module breakdown
        module_breakdown = []
        for metric in coverage_data:
            module_breakdown.append(
                {
                    "module": metric.module_name,
                    "line_coverage": metric.coverage_percentage,
                    "lines_total": metric.lines_total,
                    "lines_covered": metric.lines_covered,
                    "lines_missing": metric.lines_missing,
                    "branch_coverage": metric.branch_coverage_percentage,
                    "function_coverage": metric.function_coverage_percentage,
                }
            )

        # Quality gates summary
        gates_passed = sum(1 for result in quality_gate_results if result.passed)
        gates_failed = len(quality_gate_results) - gates_passed

        quality_summary = {
            "total_gates": len(quality_gate_results),
            "passed": gates_passed,
            "failed": gates_failed,
            "pass_rate": (
                (gates_passed / len(quality_gate_results) * 100)
                if quality_gate_results
                else 0
            ),
        }

        # Generate recommendations
        recommendations = self._generate_recommendations(
            coverage_data, quality_gate_results
        )

        report = {
            "timestamp": datetime.now().isoformat(),
            "overall_metrics": overall_metrics,
            "critical_modules": critical_modules,
            "module_breakdown": module_breakdown,
            "quality_gates": {
                "summary": quality_summary,
                "results": [asdict(result) for result in quality_gate_results],
            },
            "recommendations": recommendations,
            "coverage_trends": self._analyze_coverage_trends(),
            "risk_analysis": self._analyze_coverage_risks(coverage_data),
        }

        if output_file:
            with open(output_file, "w") as f:
                json.dump(report, f, indent=2, default=str)

        return report

    def _generate_recommendations(
        self,
        coverage_data: List[CoverageMetrics],
        quality_gate_results: List[QualityGateResult],
    ) -> List[str]:
        """Generate coverage improvement recommendations."""

        recommendations = []

        # Overall coverage recommendations
        overall_metrics = self.calculate_overall_metrics(coverage_data)
        line_coverage = overall_metrics.get("line_coverage", 0)

        if line_coverage < 80:
            recommendations.append(
                f"Increase overall line coverage from {line_coverage:.1f}% to at least 80%"
            )

        # Module-specific recommendations
        low_coverage_modules = [
            m
            for m in coverage_data
            if m.coverage_percentage < 70 and m.lines_total > 10
        ]

        if low_coverage_modules:
            module_names = [m.module_name for m in low_coverage_modules[:3]]  # Top 3
            recommendations.append(
                f"Focus on improving coverage for modules: {', '.join(module_names)}"
            )

        # Branch coverage recommendations
        branch_coverage = overall_metrics.get("branch_coverage", 0)
        if branch_coverage < 70:
            recommendations.append(
                f"Improve branch coverage from {branch_coverage:.1f}% to at least 70% by adding conditional testing"
            )

        # Quality gate failures
        failed_gates = [
            result
            for result in quality_gate_results
            if not result.passed and result.gate.severity == "error"
        ]
        if failed_gates:
            recommendations.append(
                f"Address {len(failed_gates)} critical quality gate failures before deployment"
            )

        # Missing tests for critical functions
        critical_low_coverage = [
            module
            for module, coverage in self.analyze_critical_modules(coverage_data).items()
            if coverage < 90
        ]

        if critical_low_coverage:
            recommendations.append(
                f"Add comprehensive tests for critical modules: {', '.join(critical_low_coverage)}"
            )

        return recommendations

    def _analyze_coverage_trends(self) -> Dict[str, Any]:
        """Analyze coverage trends over time."""

        # This would require historical data storage
        # For now, return placeholder structure
        return {
            "trend_direction": "stable",
            "weekly_change": 0.0,
            "monthly_change": 0.0,
            "historical_data_available": False,
        }

    def _analyze_coverage_risks(
        self, coverage_data: List[CoverageMetrics]
    ) -> Dict[str, Any]:
        """Analyze coverage risks and hotspots."""

        risks = {
            "high_risk_modules": [],
            "untested_code_hotspots": [],
            "complexity_vs_coverage": [],
            "risk_score": 0,
        }

        # High-risk modules (low coverage + critical functionality)
        for module in coverage_data:
            if (
                any(
                    critical in module.module_name.lower()
                    for critical in self.critical_modules
                )
                and module.coverage_percentage < 80
            ):
                risks["high_risk_modules"].append(
                    {
                        "module": module.module_name,
                        "coverage": module.coverage_percentage,
                        "untested_lines": module.lines_missing,
                    }
                )

        # Calculate overall risk score
        if coverage_data:
            overall_coverage = self.calculate_overall_metrics(coverage_data).get(
                "line_coverage", 0
            )
            critical_modules_count = len(risks["high_risk_modules"])

            # Simple risk scoring (0-100, lower is better)
            risk_score = max(0, 100 - overall_coverage) + (critical_modules_count * 10)
            risks["risk_score"] = min(100, risk_score)

        return risks

    def generate_visual_reports(
        self, coverage_data: List[CoverageMetrics], output_dir: Path = None
    ) -> List[Path]:
        """Generate visual coverage reports."""

        if not output_dir:
            output_dir = self.coverage_data_dir / "visual_reports"

        output_dir.mkdir(exist_ok=True)

        generated_files = []

        # Coverage by module bar chart
        try:
            fig, ax = plt.subplots(figsize=(12, 8))

            modules = [m.module_name for m in coverage_data[:15]]  # Top 15 modules
            coverages = [m.coverage_percentage for m in coverage_data[:15]]

            bars = ax.bar(
                modules,
                coverages,
                color=[
                    "green" if c >= 80 else "orange" if c >= 60 else "red"
                    for c in coverages
                ],
            )

            ax.set_title("Test Coverage by Module")
            ax.set_ylabel("Coverage Percentage")
            ax.set_xlabel("Module")
            ax.axhline(
                y=80, color="red", linestyle="--", alpha=0.7, label="Target (80%)"
            )
            ax.legend()

            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()

            coverage_chart = output_dir / "coverage_by_module.png"
            plt.savefig(coverage_chart, dpi=300, bbox_inches="tight")
            plt.close()

            generated_files.append(coverage_chart)

        except Exception as e:
            print(f"Error generating coverage chart: {e}")

        # Coverage distribution histogram
        try:
            fig, ax = plt.subplots(figsize=(10, 6))

            coverages = [m.coverage_percentage for m in coverage_data]
            ax.hist(coverages, bins=20, alpha=0.7, color="skyblue", edgecolor="black")

            ax.set_title("Coverage Distribution")
            ax.set_xlabel("Coverage Percentage")
            ax.set_ylabel("Number of Modules")
            ax.axvline(
                x=80, color="red", linestyle="--", alpha=0.7, label="Target (80%)"
            )
            ax.legend()

            plt.tight_layout()

            distribution_chart = output_dir / "coverage_distribution.png"
            plt.savefig(distribution_chart, dpi=300, bbox_inches="tight")
            plt.close()

            generated_files.append(distribution_chart)

        except Exception as e:
            print(f"Error generating distribution chart: {e}")

        return generated_files

    def store_historical_data(
        self,
        coverage_data: List[CoverageMetrics],
        quality_results: List[QualityGateResult],
    ):
        """Store coverage data for historical trend analysis."""

        db_file = self.coverage_data_dir / "coverage_history.db"

        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # Create tables if they don't exist
        cursor.executescript(
            """
            CREATE TABLE IF NOT EXISTS coverage_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                overall_line_coverage REAL,
                overall_branch_coverage REAL,
                total_modules INTEGER,
                git_commit TEXT
            );
            
            CREATE TABLE IF NOT EXISTS module_coverage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id INTEGER,
                module_name TEXT,
                line_coverage REAL,
                lines_total INTEGER,
                lines_covered INTEGER,
                branch_coverage REAL,
                FOREIGN KEY (snapshot_id) REFERENCES coverage_snapshots(id)
            );
            
            CREATE TABLE IF NOT EXISTS quality_gate_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_id INTEGER,
                gate_name TEXT,
                threshold_value REAL,
                actual_value REAL,
                passed BOOLEAN,
                FOREIGN KEY (snapshot_id) REFERENCES coverage_snapshots(id)
            );
        """
        )

        # Insert current snapshot
        overall_metrics = self.calculate_overall_metrics(coverage_data)

        cursor.execute(
            """
            INSERT INTO coverage_snapshots (overall_line_coverage, overall_branch_coverage, total_modules)
            VALUES (?, ?, ?)
        """,
            (
                overall_metrics.get("line_coverage", 0),
                overall_metrics.get("branch_coverage", 0),
                len(coverage_data),
            ),
        )

        snapshot_id = cursor.lastrowid

        # Insert module data
        for module in coverage_data:
            cursor.execute(
                """
                INSERT INTO module_coverage (snapshot_id, module_name, line_coverage, 
                                           lines_total, lines_covered, branch_coverage)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    snapshot_id,
                    module.module_name,
                    module.coverage_percentage,
                    module.lines_total,
                    module.lines_covered,
                    module.branch_coverage_percentage,
                ),
            )

        # Insert quality gate results
        for result in quality_results:
            cursor.execute(
                """
                INSERT INTO quality_gate_history (snapshot_id, gate_name, threshold_value, 
                                                 actual_value, passed)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    snapshot_id,
                    result.gate.name,
                    result.gate.threshold,
                    result.actual_value,
                    result.passed,
                ),
            )

        conn.commit()
        conn.close()


def run_coverage_analysis(
    project_root: str = None,
    coverage_xml: str = None,
    coverage_json: str = None,
    baseline_file: str = None,
) -> Dict[str, Any]:
    """Main function to run comprehensive coverage analysis."""

    analyzer = CoverageAnalyzer(project_root)

    # Parse coverage data
    coverage_data = []

    if coverage_xml:
        xml_path = Path(coverage_xml)
        if xml_path.exists():
            coverage_data.extend(analyzer.parse_coverage_xml(xml_path))

    if coverage_json:
        json_path = Path(coverage_json)
        if json_path.exists():
            coverage_data.extend(analyzer.parse_coverage_json(json_path))

    if not coverage_data:
        raise ValueError("No coverage data found. Provide coverage XML or JSON file.")

    # Evaluate quality gates
    baseline_path = Path(baseline_file) if baseline_file else None
    quality_results = analyzer.evaluate_quality_gates(coverage_data, baseline_path)

    # Generate comprehensive report
    report = analyzer.generate_coverage_report(
        coverage_data,
        quality_results,
        analyzer.coverage_data_dir / "coverage_analysis.json",
    )

    # Generate visual reports
    visual_files = analyzer.generate_visual_reports(coverage_data)
    report["visual_reports"] = [str(f) for f in visual_files]

    # Store historical data
    analyzer.store_historical_data(coverage_data, quality_results)

    # Print summary
    overall_metrics = analyzer.calculate_overall_metrics(coverage_data)
    print("\n" + "=" * 60)
    print("TEST COVERAGE ANALYSIS SUMMARY")
    print("=" * 60)
    print(f"Overall Line Coverage: {overall_metrics.get('line_coverage', 0):.1f}%")
    print(f"Overall Branch Coverage: {overall_metrics.get('branch_coverage', 0):.1f}%")
    print(f"Total Lines: {overall_metrics.get('total_lines', 0)}")
    print(f"Covered Lines: {overall_metrics.get('covered_lines', 0)}")

    print("\nQUALITY GATES:")
    for result in quality_results:
        status = "✅ PASS" if result.passed else "❌ FAIL"
        print(f"{status} {result.message}")

    gates_passed = sum(1 for r in quality_results if r.passed)
    print(f"\nQuality Gates: {gates_passed}/{len(quality_results)} passed")

    return report


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Run coverage analysis with quality gates"
    )
    parser.add_argument("--xml", help="Path to coverage XML file")
    parser.add_argument("--json", help="Path to coverage JSON file")
    parser.add_argument("--baseline", help="Path to baseline coverage file")
    parser.add_argument("--project-root", help="Project root directory", default=".")

    args = parser.parse_args()

    try:
        report = run_coverage_analysis(
            project_root=args.project_root,
            coverage_xml=args.xml,
            coverage_json=args.json,
            baseline_file=args.baseline,
        )
        print(
            f"\nDetailed report saved to: {Path(args.project_root) / 'test-reports' / 'coverage_analysis.json'}"
        )

    except Exception as e:
        print(f"Error running coverage analysis: {e}")
        exit(1)
