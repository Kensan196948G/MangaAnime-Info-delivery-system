#!/usr/bin/env python3
"""
Security and Quality Assurance Command Line Interface
Comprehensive security audit and QA validation tool for the Anime/Manga Information Delivery System.
"""

import argparse
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Import our security and QA modules
from modules.security_compliance import SecurityCompliance, SecurityTestRunner
from modules.qa_validation import QAFramework


def print_banner():
    """Print application banner"""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                  Security & QA Validation Framework                         ║
║              Anime/Manga Information Delivery System                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Comprehensive security auditing and quality assurance validation tool      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
    print(banner)


def run_security_audit(
    project_path: str, output_file: Optional[str] = None, verbose: bool = False
) -> Dict[str, Any]:
    """Run comprehensive security audit"""
    print("🔒 Starting Security Audit...")
    print("=" * 50)

    start_time = time.time()

    # Initialize security compliance scanner
    compliance = SecurityCompliance(project_path)

    if verbose:
        print("📊 Running static code analysis...")

    # Run comprehensive audit
    audit_results = compliance.run_comprehensive_security_audit()

    # Run additional security tests
    if verbose:
        print("🧪 Running security tests...")

    test_runner = SecurityTestRunner(project_path)
    test_results = test_runner.run_security_tests()

    # Combine results
    audit_results["security_tests"] = test_results

    execution_time = time.time() - start_time

    # Print summary
    print(f"\n🔒 Security Audit Results (completed in {execution_time:.2f}s)")
    print("-" * 50)
    print(f"Overall Score: {audit_results.get('overall_score', 0):.1f}/100")
    print(f"Total Findings: {audit_results.get('total_findings', 0)}")
    print(f"  • Critical: {audit_results.get('critical_findings', 0)}")
    print(f"  • High: {audit_results.get('high_findings', 0)}")
    print(f"  • Medium: {audit_results.get('medium_findings', 0)}")
    print(f"  • Low: {audit_results.get('low_findings', 0)}")

    security_tests = audit_results.get("security_tests", {})
    if security_tests:
        print(
            f"\nSecurity Tests: {security_tests.get('tests_passed', 0)}/{security_tests.get('tests_run', 0)} passed"
        )

    # Show top recommendations
    recommendations = audit_results.get("recommendations", [])
    if recommendations:
        print("\n📋 Top Recommendations:")
        for i, rec in enumerate(recommendations[:3], 1):
            print(f"  {i}. {rec}")

    # Save detailed report if requested
    if output_file:
        compliance.generate_security_report(output_file)
        print(f"\n📄 Detailed security report saved to: {output_file}")

    return audit_results


def run_qa_audit(
    project_path: str,
    db_path: Optional[str] = None,
    output_file: Optional[str] = None,
    verbose: bool = False,
) -> Dict[str, Any]:
    """Run comprehensive QA audit"""
    print("\n✅ Starting Quality Assurance Audit...")
    print("=" * 50)

    start_time = time.time()

    # Initialize QA framework
    if not db_path:
        db_path = str(Path(project_path) / "db.sqlite3")

    qa_framework = QAFramework(project_path, db_path)

    if verbose:
        print("📊 Analyzing code quality...")
        print("🔍 Validating data integrity...")
        print("⚡ Testing performance...")

    # Run comprehensive audit
    qa_results = qa_framework.run_comprehensive_qa_audit()

    execution_time = time.time() - start_time

    # Print summary
    print(f"\n✅ QA Audit Results (completed in {execution_time:.2f}s)")
    print("-" * 50)
    print(f"Overall Score: {qa_results.get('overall_score', 0):.1f}/100")
    print(
        f"Quality Level: {qa_results.get('summary', {}).get('quality_level', 'UNKNOWN')}"
    )
    print(f"Total Issues: {qa_results.get('summary', {}).get('total_issues_found', 0)}")

    summary = qa_results.get("summary", {})
    print("\nComponent Scores:")
    print(f"  • Code Quality: {summary.get('code_quality_score', 0):.1f}/100")
    print(f"  • Data Integrity: {summary.get('data_integrity_score', 0):.1f}/100")
    print(f"  • Performance: {summary.get('performance_score', 0):.1f}/100")

    # Show top action items
    action_items = qa_results.get("action_items", [])
    if action_items:
        print("\n📋 Top Action Items:")
        for i, item in enumerate(action_items[:3], 1):
            print(f"  {i}. {item}")

    # Save detailed report if requested
    if output_file:
        qa_framework.generate_qa_report(output_file)
        print(f"\n📄 Detailed QA report saved to: {output_file}")

    return qa_results


def run_combined_audit(
    project_path: str,
    db_path: Optional[str] = None,
    output_dir: Optional[str] = None,
    verbose: bool = False,
) -> Dict[str, Any]:
    """Run combined security and QA audit"""
    print_banner()

    overall_start = time.time()

    # Run security audit
    security_results = run_security_audit(
        project_path,
        str(Path(output_dir) / "security_report.json") if output_dir else None,
        verbose,
    )

    # Run QA audit
    qa_results = run_qa_audit(
        project_path,
        db_path,
        str(Path(output_dir) / "qa_report.json") if output_dir else None,
        verbose,
    )

    overall_execution_time = time.time() - overall_start

    # Calculate combined scores
    security_score = security_results.get("overall_score", 0)
    qa_score = qa_results.get("overall_score", 0)
    combined_score = (security_score * 0.5) + (qa_score * 0.5)  # 50/50 weighting

    # Determine overall health
    if combined_score >= 90:
        health_status = "🟢 EXCELLENT"
        health_color = "green"
    elif combined_score >= 80:
        health_status = "🔵 GOOD"
        health_color = "blue"
    elif combined_score >= 70:
        health_status = "🟡 ACCEPTABLE"
        health_color = "yellow"
    elif combined_score >= 60:
        health_status = "🟠 NEEDS IMPROVEMENT"
        health_color = "orange"
    else:
        health_status = "🔴 CRITICAL"
        health_color = "red"

    # Print combined summary
    print("\n" + "=" * 80)
    print("📊 COMBINED AUDIT SUMMARY")
    print("=" * 80)
    print(f"Overall System Health: {health_status}")
    print(f"Combined Score: {combined_score:.1f}/100")
    print(f"Audit Duration: {overall_execution_time:.1f}s")

    print("\nDetailed Breakdown:")
    print(f"  Security Score: {security_score:.1f}/100")
    print(f"  QA Score: {qa_score:.1f}/100")

    # Critical issues summary
    total_critical = security_results.get("critical_findings", 0)
    total_high = security_results.get("high_findings", 0) + qa_results.get(
        "summary", {}
    ).get("total_issues_found", 0)

    if total_critical > 0:
        print(
            f"\n⚠️  CRITICAL: {total_critical} critical security issues require immediate attention!"
        )

    if total_high > 0:
        print(f"⚠️  HIGH: {total_high} high-priority issues should be addressed soon")

    # Combined recommendations
    all_recommendations = []
    all_recommendations.extend(security_results.get("recommendations", []))
    all_recommendations.extend(qa_results.get("action_items", []))

    if all_recommendations:
        print("\n📋 Priority Actions:")
        for i, rec in enumerate(all_recommendations[:5], 1):
            print(f"  {i}. {rec}")

        if len(all_recommendations) > 5:
            print(
                f"  ... and {len(all_recommendations) - 5} more (see detailed reports)"
            )

    # Next steps
    print("\n🎯 Next Steps:")
    if combined_score < 70:
        print("  1. Address critical and high-priority security issues")
        print("  2. Implement recommended code quality improvements")
        print("  3. Fix data integrity issues")
        print("  4. Schedule follow-up audit in 1 week")
    elif combined_score < 85:
        print("  1. Address remaining medium-priority issues")
        print("  2. Implement performance optimizations")
        print("  3. Schedule follow-up audit in 2 weeks")
    else:
        print("  1. Monitor system regularly")
        print("  2. Maintain current quality standards")
        print("  3. Schedule routine audit in 1 month")

    if output_dir:
        # Create combined report
        combined_report = {
            "metadata": {
                "audit_timestamp": time.time(),
                "project_path": project_path,
                "audit_duration": overall_execution_time,
                "tool_version": "1.0",
            },
            "summary": {
                "combined_score": combined_score,
                "health_status": health_status.replace("🟢 ", "")
                .replace("🔵 ", "")
                .replace("🟡 ", "")
                .replace("🟠 ", "")
                .replace("🔴 ", ""),
                "security_score": security_score,
                "qa_score": qa_score,
                "total_critical_issues": total_critical,
                "total_high_issues": total_high,
            },
            "security_results": security_results,
            "qa_results": qa_results,
            "recommendations": all_recommendations,
            "next_steps": [],  # Would be populated based on score
        }

        combined_report_path = Path(output_dir) / "combined_audit_report.json"
        with open(combined_report_path, "w") as f:
            json.dump(combined_report, f, indent=2, default=str)

        print(f"\n📄 Combined audit report saved to: {combined_report_path}")

    return {
        "combined_score": combined_score,
        "health_status": health_status,
        "security_results": security_results,
        "qa_results": qa_results,
        "execution_time": overall_execution_time,
    }


def run_quick_scan(project_path: str, verbose: bool = False) -> Dict[str, Any]:
    """Run quick security and QA scan"""
    print("🚀 Running Quick System Scan...")
    print("-" * 30)

    start_time = time.time()

    # Quick security checks
    compliance = SecurityCompliance(project_path)

    # Run subset of security checks
    config_result = compliance._check_configuration_security()
    auth_result = compliance._review_authentication_security()

    security_score = (config_result.score + auth_result.score) / 2
    security_issues = len(config_result.findings) + len(auth_result.findings)

    # Quick QA checks
    qa_framework = QAFramework(project_path)
    code_results = qa_framework.code_quality.validate_code_quality()

    qa_score = code_results.get("quality_score", 0)
    qa_issues = code_results.get("total_issues", 0)

    execution_time = time.time() - start_time

    # Print results
    print(f"\n🚀 Quick Scan Results (completed in {execution_time:.1f}s)")
    print("-" * 40)
    print(f"Security: {security_score:.0f}/100 ({security_issues} issues)")
    print(f"Code Quality: {qa_score:.0f}/100 ({qa_issues} issues)")

    overall_score = (security_score + qa_score) / 2

    if overall_score >= 80:
        status = "✅ System looks healthy"
    elif overall_score >= 60:
        status = "⚠️  Some issues detected"
    else:
        status = "❌ Issues require attention"

    print(f"\nStatus: {status}")
    print("💡 Run full audit for detailed analysis: --mode full")

    return {
        "security_score": security_score,
        "qa_score": qa_score,
        "overall_score": overall_score,
        "security_issues": security_issues,
        "qa_issues": qa_issues,
        "execution_time": execution_time,
    }


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="Security and Quality Assurance Validation Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --mode security                    # Security audit only
  %(prog)s --mode qa                          # QA audit only
  %(prog)s --mode full                        # Combined audit
  %(prog)s --mode quick                       # Quick scan
  %(prog)s --mode full --output ./reports     # Save reports to directory
  %(prog)s --project /path/to/project         # Specify project path
        """,
    )

    parser.add_argument(
        "--mode",
        "-m",
        choices=["security", "qa", "full", "quick"],
        default="full",
        help="Audit mode to run (default: full)",
    )

    parser.add_argument(
        "--project",
        "-p",
        default=".",
        help="Project root path (default: current directory)",
    )

    parser.add_argument(
        "--database", "-d", help="Database path (default: PROJECT/db.sqlite3)"
    )

    parser.add_argument("--output", "-o", help="Output directory for reports")

    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    parser.add_argument(
        "--json", action="store_true", help="Output results in JSON format"
    )

    args = parser.parse_args()

    # Validate project path
    project_path = Path(args.project).resolve()
    if not project_path.exists():
        print(f"❌ Project path does not exist: {project_path}")
        sys.exit(1)

    # Create output directory if specified
    if args.output:
        output_path = Path(args.output)
        output_path.mkdir(parents=True, exist_ok=True)

    try:
        # Run selected audit mode
        if args.mode == "security":
            results = run_security_audit(
                str(project_path),
                (
                    str(Path(args.output) / "security_report.json")
                    if args.output
                    else None
                ),
                args.verbose,
            )

        elif args.mode == "qa":
            results = run_qa_audit(
                str(project_path),
                args.database,
                str(Path(args.output) / "qa_report.json") if args.output else None,
                args.verbose,
            )

        elif args.mode == "full":
            results = run_combined_audit(
                str(project_path), args.database, args.output, args.verbose
            )

        elif args.mode == "quick":
            results = run_quick_scan(str(project_path), args.verbose)

        # Output JSON if requested
        if args.json:
            print(f"\n{json.dumps(results, indent=2, default=str)}")

        # Exit with appropriate code
        if args.mode == "full":
            combined_score = results.get("combined_score", 0)
            if combined_score < 60:
                sys.exit(2)  # Critical issues
            elif combined_score < 80:
                sys.exit(1)  # Warning issues
        else:
            score = results.get(
                "overall_score",
                results.get("security_score", results.get("qa_score", 0)),
            )
            if score < 60:
                sys.exit(2)
            elif score < 80:
                sys.exit(1)

        sys.exit(0)  # Success

    except KeyboardInterrupt:
        print("\n⚠️  Audit interrupted by user")
        sys.exit(130)

    except Exception as e:
        print(f"\n❌ Audit failed: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
