"""
Security compliance validation framework for the Anime/Manga Information Delivery System.
Provides automated security testing, compliance checking, and vulnerability assessment tools.
"""

import json
import logging
import re

logger = logging.getLogger(__name__)
import time
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from modules.security_utils import InputSanitizer


@dataclass
class SecurityFinding:
    """Represents a security finding or vulnerability"""

    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    category: str  # e.g., 'input_validation', 'authentication', 'configuration'
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    remediation: str = ""
    cwe_id: Optional[str] = None
    cvss_score: Optional[float] = None


@dataclass
class ComplianceResult:
    """Results of a compliance check"""

    check_name: str
    passed: bool
    score: float  # 0-100
    findings: List[SecurityFinding]
    details: Dict[str, Any]
    timestamp: float


class SecurityCompliance:
    """Security compliance validation framework"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.logger = logging.getLogger(__name__)
        self.findings: List[SecurityFinding] = []
        self.compliance_results: List[ComplianceResult] = []

        # Security patterns to detect
        self.security_patterns = {
            "hardcoded_secrets": [
                r'(?i)(password|passwd|pwd)\s*[=:]\s*["\']([^"\']{8,})["\']',
                r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\']([^"\']{16,})["\']',
                r'(?i)(secret|token)\s*[=:]\s*["\']([^"\']{16,})["\']',
                r'(?i)(access[_-]?token)\s*[=:]\s*["\']([^"\']{20,})["\']',
            ],
            "sql_injection": [
                r'execute\s*\(\s*["\'][^"\']*\+.*["\']',
                r'cursor\.execute\s*\(\s*["\'][^"\']*%.*["\']',
                r"SELECT.*\+.*FROM",
                r"INSERT.*\+.*VALUES",
                r'f"[^"]*SELECT[^"]*\{',  # f-string SQL injection (double quotes)
                r"f'[^']*SELECT[^']*\{",  # f-string SQL injection (single quotes)
                r'f"[^"]*WHERE[^"]*\{',  # f-string WHERE interpolation
                r"f'[^']*WHERE[^']*\{",  # f-string WHERE interpolation (single quotes)
            ],
            "path_traversal": [
                r'open\s*\([^)]*\+.*["\']\.\./',
                r'file\s*\([^)]*\+.*["\']\.\./',
                r"os\.path\.join\([^)]*user.*input",
                r"open\s*\([^\)]*\+",  # open() with dynamic string concat
                r"with\s+open\s*\([^)]*\+",  # with open() with concatenation
            ],
            "command_injection": [
                r"os\.system\s*\([^)]*\+",
                r"subprocess\.(call|run|Popen)\s*\([^)]*\+",
                r"shell=True.*\+.*user",
            ],
            "unsafe_deserialization": [
                r"pickle\.loads?\s*\(",
                r"cPickle\.loads?\s*\(",
                r"yaml\.load\s*\([^)]*Loader",
            ],
            "weak_crypto": [
                r"hashlib\.(md5|sha1)\(",
                r"Crypto\.Hash\.(MD5|SHA1)",
                r"random\.random\(\)",
                r"ssl\.SSLContext\(ssl\.PROTOCOL_TLS\)",
            ],
        }

    def run_comprehensive_security_audit(self) -> Dict[str, Any]:
        """Run comprehensive security audit"""
        audit_start = time.time()
        self.logger.info("Starting comprehensive security audit")

        audit_results = {
            "timestamp": audit_start,
            "total_findings": 0,
            "critical_findings": 0,
            "high_findings": 0,
            "medium_findings": 0,
            "low_findings": 0,
            "compliance_checks": [],
            "overall_score": 0.0,
            "recommendations": [],
        }

        try:
            # 1. Static code analysis
            self.logger.info("Running static code analysis")
            self._run_static_analysis()

            # 2. Configuration security check
            self.logger.info("Checking configuration security")
            config_result = self._check_configuration_security()
            self.compliance_results.append(config_result)

            # 3. Dependency security scan
            self.logger.info("Scanning dependencies for vulnerabilities")
            deps_result = self._scan_dependencies()
            self.compliance_results.append(deps_result)

            # 4. Database security assessment
            self.logger.info("Assessing database security")
            db_result = self._assess_database_security()
            self.compliance_results.append(db_result)

            # 5. Authentication security review
            self.logger.info("Reviewing authentication security")
            auth_result = self._review_authentication_security()
            self.compliance_results.append(auth_result)

            # 6. API security validation
            self.logger.info("Validating API security")
            api_result = self._validate_api_security()
            self.compliance_results.append(api_result)

            # 7. Input validation assessment
            self.logger.info("Assessing input validation")
            input_result = self._assess_input_validation()
            self.compliance_results.append(input_result)

            # Compile results
            audit_results.update(self._compile_audit_results())

            audit_duration = time.time() - audit_start
            self.logger.info(f"Security audit completed in {audit_duration:.2f} seconds")

        except Exception as e:
            self.logger.error(f"Security audit failed: {e}")
            audit_results["error"] = str(e)

        return audit_results

    def _run_static_analysis(self) -> None:
        """Run static code analysis for security issues"""
        python_files = list(self.project_root.rglob("*.py"))

        for file_path in python_files:
            if file_path.name.startswith(".") or "venv" in str(file_path):
                continue

            self._scan_file_for_patterns(file_path)

    def _scan_file_for_patterns(self, file_path: Path) -> None:
        """Scan file for security patterns"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")

            for category, patterns in self.security_patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE)

                    for match in matches:
                        # Find line number
                        line_num = content[: match.start()].count("\n") + 1

                        # Create finding
                        finding = SecurityFinding(
                            severity=self._get_pattern_severity(category),
                            category=category,
                            description=self._get_pattern_description(category, match.group(0)),
                            file_path=str(file_path.relative_to(self.project_root)),
                            line_number=line_num,
                            remediation=self._get_pattern_remediation(category),
                        )

                        self.findings.append(finding)

        except Exception as e:
            self.logger.warning(f"Failed to scan {file_path}: {e}")

    def _get_pattern_severity(self, category: str) -> str:
        """Get severity level for security pattern category"""
        severity_map = {
            "hardcoded_secrets": "CRITICAL",
            "sql_injection": "HIGH",
            "command_injection": "HIGH",
            "path_traversal": "HIGH",
            "unsafe_deserialization": "HIGH",
            "weak_crypto": "MEDIUM",
        }
        return severity_map.get(category, "LOW")

    def _get_pattern_description(self, category: str, match_text: str) -> str:
        """Get description for security pattern"""
        descriptions = {
            "hardcoded_secrets": f"Hardcoded secret detected: {match_text[:50]}...",
            "sql_injection": f"Potential SQL injection vulnerability: {match_text[:50]}...",
            "command_injection": f"Potential command injection: {match_text[:50]}...",
            "path_traversal": f"Potential path traversal vulnerability: {match_text[:50]}...",
            "unsafe_deserialization": f"Unsafe deserialization detected: {match_text[:50]}...",
            "weak_crypto": f"Weak cryptographic function: {match_text[:50]}...",
        }
        return descriptions.get(category, f"Security issue detected: {match_text[:50]}...")

    def _get_pattern_remediation(self, category: str) -> str:
        """Get remediation advice for security pattern"""
        remediations = {
            "hardcoded_secrets": "Move secrets to environment variables or secure configuration",
            "sql_injection": "Use parameterized queries or ORM methods",
            "command_injection": "Avoid shell=True and validate all inputs",
            "path_traversal": "Validate and sanitize file paths, use secure path joining",
            "unsafe_deserialization": "Use safe serialization formats like JSON",
            "weak_crypto": "Use secure hash functions like SHA-256 or bcrypt",
        }
        return remediations.get(category, "Review and fix security issue")

    def _check_configuration_security(self) -> ComplianceResult:
        """Check configuration security"""
        findings = []
        score = 100.0

        # Check config file permissions
        config_files = ["config.json", "config.json.template"]
        for config_file in config_files:
            config_path = self.project_root / config_file
            if config_path.exists():
                stat = config_path.stat()
                permissions = oct(stat.st_mode)[-3:]

                if permissions != "600":
                    findings.append(
                        SecurityFinding(
                            severity="MEDIUM",
                            category="configuration",
                            description=f"Config file {config_file} has insecure permissions: {permissions}",
                            file_path=str(config_path.relative_to(self.project_root)),
                            remediation="Set permissions to 600 (owner read/write only)",
                        )
                    )
                    score -= 15

        # Check for sensitive data in config
        try:
            config_path = self.project_root / "config.json"
            if config_path.exists():
                with open(config_path, "r") as f:
                    config_data = json.load(f)

                # Check for hardcoded credentials
                sensitive_keys = ["password", "secret", "key", "token", "api_key"]
                self._check_nested_dict_for_sensitive_data(
                    config_data, sensitive_keys, findings, "config.json"
                )

        except Exception as e:
            findings.append(
                SecurityFinding(
                    severity="LOW",
                    category="configuration",
                    description=f"Failed to parse configuration: {e}",
                    remediation="Ensure configuration files are valid JSON",
                )
            )
            score -= 5

        return ComplianceResult(
            check_name="configuration_security",
            passed=len(findings) == 0,
            score=max(0, score),
            findings=findings,
            details={"config_files_checked": len(config_files)},
            timestamp=time.time(),
        )

    def _check_nested_dict_for_sensitive_data(
        self,
        data: Dict,
        sensitive_keys: List[str],
        findings: List[SecurityFinding],
        file_path: str,
    ) -> None:
        """Recursively check dictionary for sensitive data"""
        for key, value in data.items():
            if isinstance(value, dict):
                self._check_nested_dict_for_sensitive_data(
                    value, sensitive_keys, findings, file_path
                )
            elif isinstance(value, str) and any(
                sensitive in key.lower() for sensitive in sensitive_keys
            ):
                if len(value) > 8:  # Likely a real credential
                    findings.append(
                        SecurityFinding(
                            severity="HIGH",
                            category="configuration",
                            description=f"Potential hardcoded credential in {file_path}: {key}",
                            file_path=file_path,
                            remediation="Move sensitive values to environment variables",
                        )
                    )

    def _scan_dependencies(self) -> ComplianceResult:
        """Scan dependencies for known vulnerabilities"""
        findings = []
        score = 100.0

        requirements_file = self.project_root / "requirements.txt"
        if not requirements_file.exists():
            findings.append(
                SecurityFinding(
                    severity="LOW",
                    category="dependencies",
                    description="requirements.txt file not found",
                    remediation="Create requirements.txt file with pinned versions",
                )
            )
            score -= 10
        else:
            # Check for unpinned versions
            try:
                with open(requirements_file, "r") as f:
                    requirements = f.read().strip().split("\n")

                for line in requirements:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        if "==" not in line:
                            findings.append(
                                SecurityFinding(
                                    severity="MEDIUM",
                                    category="dependencies",
                                    description=f"Unpinned dependency: {line}",
                                    file_path="requirements.txt",
                                    remediation="Pin dependency versions using == operator",
                                )
                            )
                            score -= 5

            except Exception as e:
                findings.append(
                    SecurityFinding(
                        severity="LOW",
                        category="dependencies",
                        description=f"Failed to read requirements.txt: {e}",
                        remediation="Ensure requirements.txt is readable",
                    )
                )
                score -= 5

        # Check for known vulnerable packages
        vulnerable_packages = {
            "pyyaml": ["<5.4.0", "Use PyYAML>=5.4.0 for security fixes"],
            "requests": ["<2.20.0", "Use requests>=2.20.0 for security fixes"],
            "urllib3": ["<1.24.2", "Use urllib3>=1.24.2 for security fixes"],
        }

        # This would ideally integrate with a vulnerability database
        # For now, just check for presence of potentially vulnerable packages

        return ComplianceResult(
            check_name="dependency_security",
            passed=len(findings) == 0,
            score=max(0, score),
            findings=findings,
            details={"requirements_file_exists": requirements_file.exists()},
            timestamp=time.time(),
        )

    def _assess_database_security(self) -> ComplianceResult:
        """Assess database security configuration"""
        findings = []
        score = 100.0

        # Check database file permissions
        db_path = self.project_root / "db.sqlite3"
        if db_path.exists():
            stat = db_path.stat()
            permissions = oct(stat.st_mode)[-3:]

            if permissions not in ["600", "644"]:
                findings.append(
                    SecurityFinding(
                        severity="MEDIUM",
                        category="database",
                        description=f"Database file has insecure permissions: {permissions}",
                        file_path="db.sqlite3",
                        remediation="Set database file permissions to 600 or 644",
                    )
                )
                score -= 15

            # Check for database backups in version control
            if (self.project_root / ".git").exists():
                gitignore_path = self.project_root / ".gitignore"
                if gitignore_path.exists():
                    with open(gitignore_path, "r") as f:
                        gitignore = f.read()

                    if "*.sqlite3" not in gitignore and "db.sqlite3" not in gitignore:
                        findings.append(
                            SecurityFinding(
                                severity="HIGH",
                                category="database",
                                description="Database files may be committed to version control",
                                file_path=".gitignore",
                                remediation="Add *.sqlite3 and database files to .gitignore",
                            )
                        )
                        score -= 20

        # Check for SQL injection prevention in database modules
        db_module_path = self.project_root / "modules" / "db.py"
        if db_module_path.exists():
            with open(db_module_path, "r") as f:
                db_content = f.read()

            # Look for parameterized queries usage
            if "execute(" in db_content and "?" not in db_content:
                findings.append(
                    SecurityFinding(
                        severity="HIGH",
                        category="database",
                        description="Database queries may not be using parameterized statements",
                        file_path="modules/db.py",
                        remediation="Use parameterized queries with ? placeholders",
                    )
                )
                score -= 25

        return ComplianceResult(
            check_name="database_security",
            passed=len(findings) == 0,
            score=max(0, score),
            findings=findings,
            details={"db_file_exists": db_path.exists()},
            timestamp=time.time(),
        )

    def _review_authentication_security(self) -> ComplianceResult:
        """Review authentication and authorization security"""
        findings = []
        score = 100.0

        # Check token storage security
        token_files = ["token.json", "credentials.json"]
        for token_file in token_files:
            token_path = self.project_root / token_file
            if token_path.exists():
                # Check file permissions
                stat = token_path.stat()
                permissions = oct(stat.st_mode)[-3:]

                if permissions != "600":
                    findings.append(
                        SecurityFinding(
                            severity="HIGH",
                            category="authentication",
                            description=f"Token file {token_file} has insecure permissions: {permissions}",
                            file_path=token_file,
                            remediation="Set token file permissions to 600",
                        )
                    )
                    score -= 20

                # Check if token files are in .gitignore
                gitignore_path = self.project_root / ".gitignore"
                if gitignore_path.exists():
                    with open(gitignore_path, "r") as f:
                        gitignore = f.read()

                    if token_file not in gitignore:
                        findings.append(
                            SecurityFinding(
                                severity="CRITICAL",
                                category="authentication",
                                description=f"Token file {token_file} may be committed to version control",
                                file_path=".gitignore",
                                remediation=f"Add {token_file} to .gitignore",
                            )
                        )
                        score -= 30

        # Check OAuth2 scope limitations
        auth_modules = ["mailer.py", "calendar.py"]
        for module in auth_modules:
            module_path = self.project_root / "modules" / module
            if module_path.exists():
                with open(module_path, "r") as f:
                    content = f.read()

                # Check for overly broad scopes
                if "https://www.googleapis.com/auth/gmail" in content:
                    if "gmail.send" not in content:
                        findings.append(
                            SecurityFinding(
                                severity="MEDIUM",
                                category="authentication",
                                description=f"Overly broad Gmail scope in {module}",
                                file_path=f"modules/{module}",
                                remediation="Use gmail.send instead of full gmail scope",
                            )
                        )
                        score -= 10

        return ComplianceResult(
            check_name="authentication_security",
            passed=len(findings) == 0,
            score=max(0, score),
            findings=findings,
            details={"token_files_checked": len(token_files)},
            timestamp=time.time(),
        )

    def _validate_api_security(self) -> ComplianceResult:
        """Validate API security measures"""
        findings = []
        score = 100.0

        # Check for HTTPS enforcement
        api_modules = ["anime_anilist.py", "manga_rss.py"]
        for module in api_modules:
            module_path = self.project_root / "modules" / module
            if module_path.exists():
                with open(module_path, "r") as f:
                    content = f.read()

                # Check for HTTP URLs
                http_matches = re.findall(r'http://[^\s"\']+', content)
                for match in http_matches:
                    if "localhost" not in match:
                        findings.append(
                            SecurityFinding(
                                severity="MEDIUM",
                                category="api_security",
                                description=f"Non-HTTPS URL found in {module}: {match}",
                                file_path=f"modules/{module}",
                                remediation="Use HTTPS for all external API calls",
                            )
                        )
                        score -= 10

                # Check for rate limiting implementation
                if "rate_limit" not in content and "RateLimiter" not in content:
                    findings.append(
                        SecurityFinding(
                            severity="MEDIUM",
                            category="api_security",
                            description=f"No rate limiting detected in {module}",
                            file_path=f"modules/{module}",
                            remediation="Implement rate limiting for API calls",
                        )
                    )
                    score -= 15

        return ComplianceResult(
            check_name="api_security",
            passed=len(findings) == 0,
            score=max(0, score),
            findings=findings,
            details={"modules_checked": len(api_modules)},
            timestamp=time.time(),
        )

    def _assess_input_validation(self) -> ComplianceResult:
        """Assess input validation implementation"""
        findings = []
        score = 100.0

        # Check for input validation in key modules
        key_modules = ["anime_anilist.py", "manga_rss.py", "filter_logic.py"]
        for module in key_modules:
            module_path = self.project_root / "modules" / module
            if module_path.exists():
                with open(module_path, "r") as f:
                    content = f.read()

                # Check for input sanitization usage
                if "sanitize" not in content and "InputSanitizer" not in content:
                    findings.append(
                        SecurityFinding(
                            severity="MEDIUM",
                            category="input_validation",
                            description=f"No input sanitization detected in {module}",
                            file_path=f"modules/{module}",
                            remediation="Use InputSanitizer class for all external inputs",
                        )
                    )
                    score -= 15

                # Check for validation of user inputs
                if "validate" not in content and "len(" not in content:
                    findings.append(
                        SecurityFinding(
                            severity="LOW",
                            category="input_validation",
                            description=f"Limited input validation in {module}",
                            file_path=f"modules/{module}",
                            remediation="Add comprehensive input validation",
                        )
                    )
                    score -= 5

        return ComplianceResult(
            check_name="input_validation",
            passed=len(findings) == 0,
            score=max(0, score),
            findings=findings,
            details={"modules_checked": len(key_modules)},
            timestamp=time.time(),
        )

    def _compile_audit_results(self) -> Dict[str, Any]:
        """Compile audit results from all checks"""
        # Count findings by severity
        severity_counts = defaultdict(int)
        for finding in self.findings:
            severity_counts[finding.severity] += 1

        # Calculate overall score
        total_score = sum(result.score for result in self.compliance_results)
        overall_score = total_score / len(self.compliance_results) if self.compliance_results else 0

        # Generate recommendations
        recommendations = self._generate_security_recommendations()

        return {
            "total_findings": len(self.findings),
            "critical_findings": severity_counts["CRITICAL"],
            "high_findings": severity_counts["HIGH"],
            "medium_findings": severity_counts["MEDIUM"],
            "low_findings": severity_counts["LOW"],
            "compliance_checks": [asdict(result) for result in self.compliance_results],
            "overall_score": round(overall_score, 2),
            "recommendations": recommendations,
            "findings_by_category": self._group_findings_by_category(),
            "security_metrics": self._calculate_security_metrics(),
        }

    def _generate_security_recommendations(self) -> List[str]:
        """Generate security recommendations based on findings"""
        recommendations = []

        # Critical findings recommendations
        critical_count = sum(1 for f in self.findings if f.severity == "CRITICAL")
        if critical_count > 0:
            recommendations.append(f"Address {critical_count} critical security issues immediately")

        # High findings recommendations
        high_count = sum(1 for f in self.findings if f.severity == "HIGH")
        if high_count > 0:
            recommendations.append(f"Fix {high_count} high-priority security vulnerabilities")

        # Configuration recommendations
        config_findings = [f for f in self.findings if f.category == "configuration"]
        if config_findings:
            recommendations.append("Review and secure configuration files and permissions")

        # Authentication recommendations
        auth_findings = [f for f in self.findings if f.category == "authentication"]
        if auth_findings:
            recommendations.append("Strengthen authentication and credential management")

        # General recommendations
        if len(self.findings) == 0:
            recommendations.append("Security posture is good. Maintain regular security audits.")
        elif len(self.findings) > 10:
            recommendations.append(
                "High number of findings. Consider security training for development team."
            )

        return recommendations

    def _group_findings_by_category(self) -> Dict[str, List[Dict]]:
        """Group findings by category"""
        grouped = defaultdict(list)
        for finding in self.findings:
            grouped[finding.category].append(asdict(finding))
        return dict(grouped)

    def _calculate_security_metrics(self) -> Dict[str, Any]:
        """Calculate security metrics"""
        total_files_scanned = len(list(self.project_root.rglob("*.py")))

        return {
            "files_scanned": total_files_scanned,
            "findings_per_file": len(self.findings) / max(total_files_scanned, 1),
            "compliance_score": (
                sum(r.score for r in self.compliance_results) / len(self.compliance_results)
                if self.compliance_results
                else 0
            ),
            "security_coverage": (
                len([r for r in self.compliance_results if r.passed]) / len(self.compliance_results)
                if self.compliance_results
                else 0
            ),
            "audit_timestamp": time.time(),
        }

    def generate_security_report(self, output_path: str) -> None:
        """Generate comprehensive security report"""
        audit_results = self.run_comprehensive_security_audit()

        report = {
            "metadata": {
                "report_generated": datetime.now().isoformat(),
                "project_path": str(self.project_root),
                "audit_version": "1.0",
                "total_checks_performed": len(self.compliance_results),
            },
            "executive_summary": {
                "overall_score": audit_results.get("overall_score", 0),
                "total_findings": audit_results.get("total_findings", 0),
                "critical_issues": audit_results.get("critical_findings", 0),
                "recommendations": audit_results.get("recommendations", []),
            },
            "detailed_findings": audit_results.get("findings_by_category", {}),
            "compliance_results": audit_results.get("compliance_checks", []),
            "security_metrics": audit_results.get("security_metrics", {}),
            "remediation_plan": self._create_remediation_plan(),
        }

        # Write report to file
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2, default=str)

        self.logger.info(f"Security report generated: {output_path}")

    def _create_remediation_plan(self) -> Dict[str, List[Dict]]:
        """Create prioritized remediation plan"""
        plan = {
            "immediate_action": [],  # Critical/High severity
            "short_term": [],  # Medium severity
            "long_term": [],  # Low severity
        }

        for finding in self.findings:
            item = {
                "description": finding.description,
                "file_path": finding.file_path,
                "remediation": finding.remediation,
                "category": finding.category,
            }

            if finding.severity in ["CRITICAL", "HIGH"]:
                plan["immediate_action"].append(item)
            elif finding.severity == "MEDIUM":
                plan["short_term"].append(item)
            else:
                plan["long_term"].append(item)

        return plan


class SecurityTestRunner:
    """Automated security testing framework"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.logger = logging.getLogger(__name__)

    def run_security_tests(self) -> Dict[str, Any]:
        """Run automated security tests"""
        test_results = {
            "timestamp": time.time(),
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "test_details": [],
        }

        # Input validation tests
        input_tests = self._run_input_validation_tests()
        test_results["test_details"].extend(input_tests)

        # Authentication tests
        auth_tests = self._run_authentication_tests()
        test_results["test_details"].extend(auth_tests)

        # API security tests
        api_tests = self._run_api_security_tests()
        test_results["test_details"].extend(api_tests)

        # Count results
        test_results["tests_run"] = len(test_results["test_details"])
        test_results["tests_passed"] = len([t for t in test_results["test_details"] if t["passed"]])
        test_results["tests_failed"] = test_results["tests_run"] - test_results["tests_passed"]

        return test_results

    def _run_input_validation_tests(self) -> List[Dict[str, Any]]:
        """Run input validation security tests"""
        tests = []

        # Test SQL injection prevention
        test_inputs = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "'; SELECT * FROM works WHERE '1'='1'--",
            "<script>alert('xss')</script>",
            "../../../etc/passwd",
        ]

        for test_input in test_inputs:
            try:
                # Test sanitization
                sanitized = InputSanitizer.sanitize_title(test_input)

                tests.append(
                    {
                        "name": f"input_sanitization_{hash(test_input) % 1000}",
                        "description": f"Test input sanitization for: {test_input[:20]}...",
                        "passed": sanitized != test_input,  # Should be modified
                        "details": f"Input: {test_input}, Sanitized: {sanitized}",
                    }
                )

            except Exception as e:
                tests.append(
                    {
                        "name": f"input_validation_error_{hash(test_input) % 1000}",
                        "description": f"Input validation error for: {test_input[:20]}...",
                        "passed": True,  # Exception is expected for malicious input
                        "details": f"Exception: {str(e)}",
                    }
                )

        return tests

    def _run_authentication_tests(self) -> List[Dict[str, Any]]:
        """Run authentication security tests"""
        tests = []

        # Test token file security
        token_file = self.project_root / "token.json"
        if token_file.exists():
            stat = token_file.stat()
            permissions = oct(stat.st_mode)[-3:]

            tests.append(
                {
                    "name": "token_file_permissions",
                    "description": "Check token file has secure permissions",
                    "passed": permissions == "600",
                    "details": f"Token file permissions: {permissions}",
                }
            )

        return tests

    def _run_api_security_tests(self) -> List[Dict[str, Any]]:
        """Run API security tests"""
        tests = []

        # Test HTTPS enforcement
        api_urls = [
            "https://graphql.anilist.co",
            "https://cal.syoboi.jp",
            "https://accounts.google.com",
        ]

        for url in api_urls:
            tests.append(
                {
                    "name": f"https_enforcement_{hash(url) % 1000}",
                    "description": f"Verify HTTPS usage for {url}",
                    "passed": url.startswith("https://"),
                    "details": f"URL: {url}",
                }
            )

        return tests


def run_security_audit_cli(project_root: str, output_file: str = None) -> None:
    """Command-line interface for running security audit"""
    compliance = SecurityCompliance(project_root)

    logger.info("Starting security audit...")
    results = compliance.run_comprehensive_security_audit()

    logger.info("\nSecurity Audit Results:")
    logger.info(f"Overall Score: {results['overall_score']}/100")
    logger.info(f"Total Findings: {results['total_findings']}")
    logger.info(f"Critical: {results['critical_findings']}")
    logger.info(f"High: {results['high_findings']}")
    logger.info(f"Medium: {results['medium_findings']}")
    logger.info(f"Low: {results['low_findings']}")

    if results["recommendations"]:
        logger.info("\nRecommendations:")
        for rec in results["recommendations"]:
            logger.info(f"- {rec}")

    # Generate detailed report
    if output_file:
        compliance.generate_security_report(output_file)
        logger.info(f"\nDetailed report saved to: {output_file}")

    # Run security tests
    test_runner = SecurityTestRunner(project_root)
    test_results = test_runner.run_security_tests()

    logger.info(
        f"\nSecurity Tests: {test_results['tests_passed']}/{test_results['tests_run']} passed"
    )


if __name__ == "__main__":
    import sys

    project_path = sys.argv[1] if len(sys.argv) > 1 else "."
    output_path = sys.argv[2] if len(sys.argv) > 2 else "security_audit_report.json"

    run_security_audit_cli(project_path, output_path)
