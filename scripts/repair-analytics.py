#!/usr/bin/env python3

"""
Advanced analytics script for the 30-minute auto-repair system
Analyzes repair patterns, success rates, failure trends, and generates optimization recommendations
"""

import json
import sqlite3
import sys
import os
import argparse
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import statistics
import re

try:
    import numpy as np
    import pandas as pd

    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    print("Warning: pandas/numpy not available. Some advanced analytics disabled.")

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler

    HAS_ML = True
except ImportError:
    HAS_ML = False
    print("Warning: ML libraries not available. ML analysis disabled.")


# Color codes for terminal output
class Colors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"


@dataclass
class FailurePattern:
    """Represents a failure pattern analysis"""

    pattern_type: str
    frequency: int
    success_rate: float
    avg_duration: float
    common_errors: List[str]
    time_pattern: str
    severity: str
    recommendations: List[str]


@dataclass
class OptimizationRecommendation:
    """Represents an optimization recommendation"""

    category: str
    priority: str  # high, medium, low
    description: str
    expected_impact: str
    implementation_complexity: str
    estimated_improvement: float


@dataclass
class PerformanceMetrics:
    """System performance metrics"""

    overall_success_rate: float
    avg_repair_duration: float
    repairs_per_day: float
    failure_recovery_rate: float
    system_availability: float
    mttr: float  # Mean Time To Repair
    mtbf: float  # Mean Time Between Failures


class RepairAnalytics:
    """Main analytics class for repair system analysis"""

    def __init__(self, base_path: str = ".."):
        self.base_path = Path(base_path)
        self.state_file = self.base_path / ".repair_state.json"
        self.log_dir = self.base_path / "logs"
        self.db_path = self.base_path / "repair_analytics.db"
        self.workflows_dir = self.base_path / ".github" / "workflows"

        self.init_database()
        self.populate_data_if_needed()

    def init_database(self):
        """Initialize analytics database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Enhanced repair history table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS repair_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    repair_type TEXT,
                    status TEXT,
                    duration REAL,
                    error_message TEXT,
                    workflow_name TEXT,
                    commit_hash TEXT,
                    retry_count INTEGER DEFAULT 0,
                    system_load REAL,
                    github_api_remaining INTEGER
                )
            """
            )

            # Performance metrics table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metric_name TEXT,
                    metric_value REAL,
                    context_data TEXT
                )
            """
            )

            # Pattern analysis table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS failure_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_hash TEXT UNIQUE,
                    pattern_type TEXT,
                    frequency INTEGER DEFAULT 1,
                    last_occurrence DATETIME DEFAULT CURRENT_TIMESTAMP,
                    success_rate REAL DEFAULT 0.0,
                    avg_duration REAL DEFAULT 0.0,
                    severity TEXT DEFAULT 'low',
                    resolution_strategy TEXT
                )
            """
            )

            # Optimization recommendations table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS recommendations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    category TEXT,
                    priority TEXT,
                    description TEXT,
                    expected_impact TEXT,
                    implementation_complexity TEXT,
                    estimated_improvement REAL,
                    status TEXT DEFAULT 'pending'
                )
            """
            )

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"{Colors.RED}Error initializing analytics database: {e}{Colors.END}")

    def populate_data_if_needed(self):
        """Populate database with sample data if empty (for demonstration)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check if we have data
            cursor.execute("SELECT COUNT(*) FROM repair_history")
            count = cursor.fetchone()[0]

            if count == 0:
                # Add sample repair data
                sample_repairs = [
                    (
                        "workflow_fix",
                        "success",
                        45.2,
                        None,
                        "auto-repair.yml",
                        "abc123",
                        0,
                        0.3,
                        4500,
                    ),
                    (
                        "dependency_update",
                        "failure",
                        120.5,
                        "Package not found",
                        "dependencies.yml",
                        "def456",
                        1,
                        0.8,
                        4450,
                    ),
                    (
                        "syntax_error",
                        "success",
                        30.1,
                        None,
                        "lint.yml",
                        "ghi789",
                        0,
                        0.2,
                        4400,
                    ),
                    (
                        "api_timeout",
                        "failure",
                        180.0,
                        "Request timeout",
                        "api-test.yml",
                        "jkl012",
                        2,
                        0.9,
                        4300,
                    ),
                    (
                        "security_scan",
                        "success",
                        90.3,
                        None,
                        "security.yml",
                        "mno345",
                        0,
                        0.4,
                        4250,
                    ),
                ]

                # Insert with timestamps spread over last 30 days
                base_time = datetime.now() - timedelta(days=30)
                for i, repair in enumerate(sample_repairs):
                    timestamp = base_time + timedelta(days=i * 6, hours=i * 2)
                    cursor.execute(
                        """
                        INSERT INTO repair_history 
                        (timestamp, repair_type, status, duration, error_message, workflow_name, 
                         commit_hash, retry_count, system_load, github_api_remaining)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (timestamp.isoformat(),) + repair,
                    )

                conn.commit()
                print(
                    f"{Colors.YELLOW}Populated database with sample data for analysis{Colors.END}"
                )

            conn.close()
        except Exception as e:
            print(
                f"{Colors.YELLOW}Warning: Could not populate sample data: {e}{Colors.END}"
            )

    def analyze_failure_patterns(self) -> List[FailurePattern]:
        """Analyze failure patterns and trends"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            patterns = []

            # Analyze by repair type
            cursor.execute(
                """
                SELECT repair_type, 
                       COUNT(*) as total,
                       SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful,
                       AVG(duration) as avg_duration,
                       GROUP_CONCAT(error_message, '|') as errors
                FROM repair_history 
                GROUP BY repair_type
                HAVING total > 1
            """
            )

            for row in cursor.fetchall():
                repair_type, total, successful, avg_duration, errors = row
                success_rate = (successful / total) * 100 if total > 0 else 0

                # Parse common errors
                error_list = []
                if errors:
                    error_messages = [e for e in errors.split("|") if e and e != "None"]
                    if error_messages:
                        error_counter = Counter(error_messages)
                        error_list = [
                            f"{error} ({count}x)"
                            for error, count in error_counter.most_common(3)
                        ]

                # Determine time pattern
                cursor.execute(
                    """
                    SELECT strftime('%H', timestamp) as hour, COUNT(*) as count
                    FROM repair_history 
                    WHERE repair_type = ? AND status = 'failure'
                    GROUP BY hour
                    ORDER BY count DESC
                    LIMIT 1
                """,
                    (repair_type,),
                )

                time_result = cursor.fetchone()
                time_pattern = (
                    f"Peak failures at {time_result[0]}:00"
                    if time_result
                    else "No clear pattern"
                )

                # Determine severity
                severity = (
                    "high"
                    if success_rate < 50
                    else "medium" if success_rate < 80 else "low"
                )

                # Generate recommendations
                recommendations = self.generate_pattern_recommendations(
                    repair_type, success_rate, avg_duration or 0
                )

                pattern = FailurePattern(
                    pattern_type=repair_type,
                    frequency=total,
                    success_rate=success_rate,
                    avg_duration=avg_duration or 0,
                    common_errors=error_list,
                    time_pattern=time_pattern,
                    severity=severity,
                    recommendations=recommendations,
                )
                patterns.append(pattern)

            conn.close()
            return sorted(patterns, key=lambda x: x.frequency, reverse=True)

        except Exception as e:
            print(f"{Colors.RED}Error analyzing failure patterns: {e}{Colors.END}")
            return []

    def generate_pattern_recommendations(
        self, repair_type: str, success_rate: float, avg_duration: float
    ) -> List[str]:
        """Generate recommendations based on failure patterns"""
        recommendations = []

        if success_rate < 50:
            recommendations.append(
                f"Critical: {repair_type} has very low success rate - review workflow logic"
            )
            recommendations.append(
                "Consider adding more robust error handling and retry mechanisms"
            )
        elif success_rate < 80:
            recommendations.append(
                f"Moderate: {repair_type} needs improvement - add better validation"
            )

        if avg_duration > 120:  # More than 2 minutes
            recommendations.append(
                "Optimize for faster execution - consider parallel processing"
            )
            recommendations.append("Add timeout mechanisms to prevent hanging")

        # Type-specific recommendations
        if "api" in repair_type.lower():
            recommendations.append("Implement exponential backoff for API calls")
            recommendations.append("Add API rate limit monitoring")
        elif "dependency" in repair_type.lower():
            recommendations.append("Cache dependencies to reduce download time")
            recommendations.append("Use dependency lock files for consistency")
        elif "security" in repair_type.lower():
            recommendations.append("Update security scanning rules regularly")
            recommendations.append("Whitelist known false positives")

        return recommendations

    def calculate_performance_metrics(self) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Overall success rate
            cursor.execute(
                """
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful
                FROM repair_history
            """
            )

            total, successful = cursor.fetchone()
            overall_success_rate = (successful / total * 100) if total > 0 else 0

            # Average repair duration
            cursor.execute(
                "SELECT AVG(duration) FROM repair_history WHERE status = 'success'"
            )
            avg_duration = cursor.fetchone()[0] or 0

            # Repairs per day (last 30 days)
            cursor.execute(
                """
                SELECT COUNT(*) / 30.0 as repairs_per_day
                FROM repair_history 
                WHERE timestamp > datetime('now', '-30 days')
            """
            )
            repairs_per_day = cursor.fetchone()[0] or 0

            # Failure recovery rate (retries that eventually succeeded)
            cursor.execute(
                """
                SELECT 
                    COUNT(*) as total_retries,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful_retries
                FROM repair_history 
                WHERE retry_count > 0
            """
            )

            retry_result = cursor.fetchone()
            failure_recovery_rate = 0
            if retry_result[0] > 0:
                failure_recovery_rate = (retry_result[1] / retry_result[0]) * 100

            # System availability (percentage of time system was operational)
            cursor.execute(
                """
                SELECT COUNT(*) as failure_count
                FROM repair_history 
                WHERE status = 'failure' AND timestamp > datetime('now', '-24 hours')
            """
            )

            failures_24h = cursor.fetchone()[0] or 0
            system_availability = max(
                0, 100 - (failures_24h * 2)
            )  # Assume each failure causes ~2% downtime

            # MTTR (Mean Time To Repair) - average time to resolve failures
            cursor.execute(
                """
                SELECT AVG(duration) 
                FROM repair_history 
                WHERE status = 'success' AND retry_count > 0
            """
            )
            mttr = cursor.fetchone()[0] or 0

            # MTBF (Mean Time Between Failures)
            cursor.execute(
                """
                SELECT 
                    (MAX(julianday(timestamp)) - MIN(julianday(timestamp))) * 24 / COUNT(*) as mtbf_hours
                FROM repair_history 
                WHERE status = 'failure'
            """
            )
            mtbf_result = cursor.fetchone()[0]
            mtbf = mtbf_result if mtbf_result else 168  # Default to 1 week

            conn.close()

            return PerformanceMetrics(
                overall_success_rate=overall_success_rate,
                avg_repair_duration=avg_duration,
                repairs_per_day=repairs_per_day,
                failure_recovery_rate=failure_recovery_rate,
                system_availability=system_availability,
                mttr=mttr,
                mtbf=mtbf,
            )

        except Exception as e:
            print(f"{Colors.RED}Error calculating performance metrics: {e}{Colors.END}")
            return PerformanceMetrics(0, 0, 0, 0, 0, 0, 0)

    def detect_anomalies(self) -> List[Dict[str, Any]]:
        """Detect anomalies in repair patterns using ML"""
        if not HAS_ML:
            return []

        try:
            conn = sqlite3.connect(self.db_path)

            # Load data for anomaly detection
            query = """
                SELECT duration, retry_count, system_load, github_api_remaining,
                       strftime('%H', timestamp) as hour,
                       CASE WHEN status = 'success' THEN 1 ELSE 0 END as success
                FROM repair_history
                WHERE duration IS NOT NULL AND system_load IS NOT NULL
            """

            df = pd.read_sql_query(query, conn)
            conn.close()

            if df.empty or len(df) < 10:
                return []

            # Prepare features for anomaly detection
            features = [
                "duration",
                "retry_count",
                "system_load",
                "github_api_remaining",
                "hour",
            ]
            X = df[features].fillna(0)

            # Standardize features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            # Detect anomalies using Isolation Forest
            iso_forest = IsolationForest(contamination=0.1, random_state=42)
            anomalies = iso_forest.fit_predict(X_scaled)

            # Identify anomalous records
            anomaly_records = []
            for i, is_anomaly in enumerate(anomalies):
                if is_anomaly == -1:  # Anomaly detected
                    record = df.iloc[i]
                    anomaly_records.append(
                        {
                            "index": i,
                            "duration": record["duration"],
                            "retry_count": record["retry_count"],
                            "system_load": record["system_load"],
                            "hour": record["hour"],
                            "success": record["success"],
                            "anomaly_score": iso_forest.decision_function(
                                X_scaled[i : i + 1]
                            )[0],
                        }
                    )

            return sorted(anomaly_records, key=lambda x: x["anomaly_score"])

        except Exception as e:
            print(f"{Colors.YELLOW}Warning: Anomaly detection failed: {e}{Colors.END}")
            return []

    def generate_optimization_recommendations(self) -> List[OptimizationRecommendation]:
        """Generate comprehensive optimization recommendations"""
        recommendations = []

        # Analyze current performance
        metrics = self.calculate_performance_metrics()
        patterns = self.analyze_failure_patterns()

        # Performance-based recommendations
        if metrics.overall_success_rate < 90:
            recommendations.append(
                OptimizationRecommendation(
                    category="Reliability",
                    priority="high",
                    description="Improve overall success rate through better error handling and validation",
                    expected_impact="Reduce failure rate by 50%",
                    implementation_complexity="medium",
                    estimated_improvement=10.0,
                )
            )

        if metrics.avg_repair_duration > 60:
            recommendations.append(
                OptimizationRecommendation(
                    category="Performance",
                    priority="medium",
                    description="Optimize repair workflows for faster execution",
                    expected_impact="Reduce average repair time by 30%",
                    implementation_complexity="low",
                    estimated_improvement=5.0,
                )
            )

        if metrics.system_availability < 95:
            recommendations.append(
                OptimizationRecommendation(
                    category="Availability",
                    priority="high",
                    description="Implement circuit breakers and graceful degradation",
                    expected_impact="Improve availability to 99%+",
                    implementation_complexity="high",
                    estimated_improvement=15.0,
                )
            )

        # Pattern-based recommendations
        high_failure_patterns = [p for p in patterns if p.severity == "high"]
        if high_failure_patterns:
            recommendations.append(
                OptimizationRecommendation(
                    category="Reliability",
                    priority="high",
                    description=f"Address {len(high_failure_patterns)} high-severity failure patterns",
                    expected_impact="Eliminate critical failure modes",
                    implementation_complexity="medium",
                    estimated_improvement=20.0,
                )
            )

        # Resource optimization
        if metrics.repairs_per_day > 10:
            recommendations.append(
                OptimizationRecommendation(
                    category="Efficiency",
                    priority="low",
                    description="Implement predictive maintenance to reduce reactive repairs",
                    expected_impact="Reduce repair frequency by 40%",
                    implementation_complexity="high",
                    estimated_improvement=8.0,
                )
            )

        # GitHub API optimization
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT AVG(github_api_remaining) FROM repair_history WHERE github_api_remaining > 0"
            )
            avg_api_remaining = cursor.fetchone()[0] or 5000
            conn.close()

            if avg_api_remaining < 1000:
                recommendations.append(
                    OptimizationRecommendation(
                        category="Resource Management",
                        priority="medium",
                        description="Optimize GitHub API usage with caching and batching",
                        expected_impact="Reduce API calls by 60%",
                        implementation_complexity="medium",
                        estimated_improvement=12.0,
                    )
                )
        except:
            pass

        return sorted(
            recommendations,
            key=lambda x: {"high": 3, "medium": 2, "low": 1}[x.priority],
            reverse=True,
        )

    def generate_trend_analysis(self, days: int = 30):
        """Generate trend analysis and predictions"""
        if not HAS_PANDAS:
            print(f"{Colors.YELLOW}Pandas not available for trend analysis{Colors.END}")
            return

        try:
            conn = sqlite3.connect(self.db_path)

            # Load time series data
            query = f"""
                SELECT DATE(timestamp) as date,
                       COUNT(*) as total_repairs,
                       SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful_repairs,
                       AVG(duration) as avg_duration
                FROM repair_history 
                WHERE timestamp > datetime('now', '-{days} days')
                GROUP BY DATE(timestamp)
                ORDER BY date
            """

            df = pd.read_sql_query(query, conn)
            conn.close()

            if df.empty:
                print(
                    f"{Colors.YELLOW}No data available for trend analysis{Colors.END}"
                )
                return

            df["date"] = pd.to_datetime(df["date"])
            df["success_rate"] = (df["successful_repairs"] / df["total_repairs"]) * 100

            # Calculate trends
            print(f"{Colors.YELLOW}📈 TREND ANALYSIS (Last {days} days){Colors.END}")

            # Success rate trend
            if len(df) > 1:
                success_trend = np.polyfit(range(len(df)), df["success_rate"], 1)[0]
                trend_direction = (
                    "↗️ improving"
                    if success_trend > 0
                    else "↘️ declining" if success_trend < 0 else "→ stable"
                )
                print(
                    f"   Success Rate Trend: {Colors.CYAN}{trend_direction} ({success_trend:.2f}%/day){Colors.END}"
                )

                # Duration trend
                duration_trend = np.polyfit(range(len(df)), df["avg_duration"], 1)[0]
                duration_direction = (
                    "↗️ increasing"
                    if duration_trend > 0
                    else "↘️ decreasing" if duration_trend < 0 else "→ stable"
                )
                print(
                    f"   Duration Trend:     {Colors.CYAN}{duration_direction} ({duration_trend:.2f}s/day){Colors.END}"
                )

                # Volume trend
                volume_trend = np.polyfit(range(len(df)), df["total_repairs"], 1)[0]
                volume_direction = (
                    "↗️ increasing"
                    if volume_trend > 0
                    else "↘️ decreasing" if volume_trend < 0 else "→ stable"
                )
                print(
                    f"   Repair Volume:      {Colors.CYAN}{volume_direction} ({volume_trend:.2f}/day){Colors.END}"
                )

            # Statistical summary
            print(f"\n{Colors.YELLOW}📊 STATISTICAL SUMMARY{Colors.END}")
            print(
                f"   Average Success Rate: {Colors.GREEN}{df['success_rate'].mean():.1f}%{Colors.END}"
            )
            print(
                f"   Success Rate StdDev:  {Colors.CYAN}{df['success_rate'].std():.1f}%{Colors.END}"
            )
            print(
                f"   Average Duration:     {Colors.GREEN}{df['avg_duration'].mean():.1f}s{Colors.END}"
            )
            print(
                f"   Total Repairs:        {Colors.GREEN}{df['total_repairs'].sum()}{Colors.END}"
            )

        except Exception as e:
            print(f"{Colors.RED}Error in trend analysis: {e}{Colors.END}")

    def create_visualizations(self, output_dir: str = "analytics_output"):
        """Create comprehensive visualizations"""
        if not HAS_ML:
            print(f"{Colors.YELLOW}Visualization libraries not available{Colors.END}")
            return

        try:
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)

            conn = sqlite3.connect(self.db_path)

            # Success rate over time
            df_time = pd.read_sql_query(
                """
                SELECT DATE(timestamp) as date,
                       COUNT(*) as total,
                       SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful
                FROM repair_history 
                GROUP BY DATE(timestamp)
                ORDER BY date
            """,
                conn,
            )

            if not df_time.empty:
                df_time["date"] = pd.to_datetime(df_time["date"])
                df_time["success_rate"] = (
                    df_time["successful"] / df_time["total"]
                ) * 100

                plt.figure(figsize=(12, 8))

                # Plot 1: Success rate over time
                plt.subplot(2, 2, 1)
                plt.plot(df_time["date"], df_time["success_rate"], "b-", linewidth=2)
                plt.title("Success Rate Over Time")
                plt.ylabel("Success Rate (%)")
                plt.xticks(rotation=45)
                plt.grid(True, alpha=0.3)

                # Plot 2: Repair volume
                plt.subplot(2, 2, 2)
                plt.bar(df_time["date"], df_time["total"], alpha=0.7, color="green")
                plt.title("Daily Repair Volume")
                plt.ylabel("Number of Repairs")
                plt.xticks(rotation=45)

                # Plot 3: Failure patterns
                df_patterns = pd.read_sql_query(
                    """
                    SELECT repair_type, COUNT(*) as count,
                           SUM(CASE WHEN status = 'failure' THEN 1 ELSE 0 END) as failures
                    FROM repair_history 
                    GROUP BY repair_type
                """,
                    conn,
                )

                if not df_patterns.empty:
                    plt.subplot(2, 2, 3)
                    plt.pie(
                        df_patterns["count"],
                        labels=df_patterns["repair_type"],
                        autopct="%1.1f%%",
                    )
                    plt.title("Repair Distribution by Type")

                # Plot 4: Duration distribution
                df_duration = pd.read_sql_query(
                    """
                    SELECT duration FROM repair_history 
                    WHERE duration IS NOT NULL AND duration > 0
                """,
                    conn,
                )

                if not df_duration.empty:
                    plt.subplot(2, 2, 4)
                    plt.hist(
                        df_duration["duration"], bins=20, alpha=0.7, color="orange"
                    )
                    plt.title("Repair Duration Distribution")
                    plt.xlabel("Duration (seconds)")
                    plt.ylabel("Frequency")

                plt.tight_layout()
                plt.savefig(
                    f"{output_dir}/repair_analytics_overview.png",
                    dpi=300,
                    bbox_inches="tight",
                )
                print(
                    f"{Colors.GREEN}Saved overview visualization to {output_dir}/repair_analytics_overview.png{Colors.END}"
                )

            conn.close()

        except Exception as e:
            print(f"{Colors.RED}Error creating visualizations: {e}{Colors.END}")

    def export_analysis_report(self, output_file: str):
        """Export comprehensive analysis report"""
        try:
            # Gather all analysis data
            metrics = self.calculate_performance_metrics()
            patterns = self.analyze_failure_patterns()
            recommendations = self.generate_optimization_recommendations()
            anomalies = self.detect_anomalies()

            report = {
                "report_metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "analysis_period": "Last 30 days",
                    "system_version": "Auto-Repair v1.0",
                },
                "performance_metrics": asdict(metrics),
                "failure_patterns": [asdict(p) for p in patterns],
                "optimization_recommendations": [asdict(r) for r in recommendations],
                "anomalies": anomalies,
                "summary": {
                    "total_patterns_analyzed": len(patterns),
                    "high_severity_patterns": len(
                        [p for p in patterns if p.severity == "high"]
                    ),
                    "optimization_opportunities": len(recommendations),
                    "anomalies_detected": len(anomalies),
                },
            }

            with open(output_file, "w") as f:
                json.dump(report, f, indent=2, default=str)

            print(
                f"{Colors.GREEN}Analysis report exported to: {output_file}{Colors.END}"
            )

        except Exception as e:
            print(f"{Colors.RED}Error exporting analysis report: {e}{Colors.END}")

    def display_analytics_dashboard(self):
        """Display comprehensive analytics dashboard"""
        os.system("clear")

        print(f"{Colors.BLUE}{'='*80}{Colors.END}")
        print(
            f"{Colors.BOLD}{Colors.CYAN}        AUTO-REPAIR ANALYTICS DASHBOARD        {Colors.END}"
        )
        print(f"{Colors.BLUE}{'='*80}{Colors.END}")
        print(
            f"{Colors.CYAN}Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.END}\n"
        )

        # Performance Metrics
        metrics = self.calculate_performance_metrics()
        print(f"{Colors.YELLOW}📊 PERFORMANCE METRICS{Colors.END}")
        print(
            f"   Overall Success Rate:    {self.colorize_metric(metrics.overall_success_rate, 90, 95)}%"
        )
        print(
            f"   Avg Repair Duration:     {Colors.CYAN}{metrics.avg_repair_duration:.1f}s{Colors.END}"
        )
        print(
            f"   Repairs per Day:         {Colors.CYAN}{metrics.repairs_per_day:.1f}{Colors.END}"
        )
        print(
            f"   Failure Recovery Rate:   {self.colorize_metric(metrics.failure_recovery_rate, 70, 85)}%"
        )
        print(
            f"   System Availability:     {self.colorize_metric(metrics.system_availability, 95, 99)}%"
        )
        print(
            f"   MTTR (Mean Time To Repair): {Colors.CYAN}{metrics.mttr:.1f}s{Colors.END}"
        )
        print(
            f"   MTBF (Mean Time Between Failures): {Colors.CYAN}{metrics.mtbf:.1f}h{Colors.END}"
        )
        print()

        # Failure Patterns
        patterns = self.analyze_failure_patterns()
        print(f"{Colors.YELLOW}🔍 FAILURE PATTERN ANALYSIS{Colors.END}")
        if patterns:
            for pattern in patterns[:3]:  # Show top 3 patterns
                severity_color = (
                    Colors.RED
                    if pattern.severity == "high"
                    else Colors.YELLOW if pattern.severity == "medium" else Colors.GREEN
                )
                print(
                    f"   {severity_color}[{pattern.severity.upper()}]{Colors.END} {pattern.pattern_type}"
                )
                print(
                    f"     └─ Frequency: {pattern.frequency}, Success Rate: {pattern.success_rate:.1f}%"
                )
        else:
            print(
                f"   {Colors.GREEN}No significant failure patterns detected{Colors.END}"
            )
        print()

        # Optimization Recommendations
        recommendations = self.generate_optimization_recommendations()
        print(f"{Colors.YELLOW}💡 OPTIMIZATION RECOMMENDATIONS{Colors.END}")
        if recommendations:
            for rec in recommendations[:3]:  # Show top 3 recommendations
                priority_color = (
                    Colors.RED
                    if rec.priority == "high"
                    else Colors.YELLOW if rec.priority == "medium" else Colors.GREEN
                )
                print(
                    f"   {priority_color}[{rec.priority.upper()}]{Colors.END} {rec.category}: {rec.description}"
                )
                print(
                    f"     └─ Expected: {rec.expected_impact} (Improvement: {rec.estimated_improvement:.1f}%)"
                )
        else:
            print(
                f"   {Colors.GREEN}System is well optimized - no critical recommendations{Colors.END}"
            )
        print()

        # Anomalies
        anomalies = self.detect_anomalies()
        print(f"{Colors.YELLOW}🚨 ANOMALY DETECTION{Colors.END}")
        if anomalies:
            print(
                f"   {Colors.RED}Detected {len(anomalies)} anomalous repair operations{Colors.END}"
            )
            for anomaly in anomalies[:2]:  # Show top 2 anomalies
                print(
                    f"     └─ Duration: {anomaly['duration']:.1f}s, Retries: {anomaly['retry_count']}"
                )
        else:
            print(
                f"   {Colors.GREEN}No anomalies detected in recent operations{Colors.END}"
            )
        print()

        # Trend Analysis
        self.generate_trend_analysis(7)  # Last 7 days

        print(f"\n{Colors.BLUE}{'='*80}{Colors.END}")

    def colorize_metric(self, value: float, warning: float, good: float) -> str:
        """Colorize metric based on thresholds"""
        if value >= good:
            return f"{Colors.GREEN}{value:.1f}"
        elif value >= warning:
            return f"{Colors.YELLOW}{value:.1f}"
        else:
            return f"{Colors.RED}{value:.1f}"


def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description="Auto-Repair System Analytics")
    parser.add_argument(
        "--base-path", default="..", help="Base path to project directory"
    )
    parser.add_argument(
        "--dashboard", "-d", action="store_true", help="Show analytics dashboard"
    )
    parser.add_argument(
        "--patterns", "-p", action="store_true", help="Analyze failure patterns"
    )
    parser.add_argument(
        "--recommendations",
        "-r",
        action="store_true",
        help="Generate optimization recommendations",
    )
    parser.add_argument(
        "--trends",
        "-t",
        type=int,
        metavar="DAYS",
        default=30,
        help="Analyze trends for N days",
    )
    parser.add_argument(
        "--anomalies", "-a", action="store_true", help="Detect anomalies"
    )
    parser.add_argument(
        "--visualize", "-v", action="store_true", help="Create visualizations"
    )
    parser.add_argument("--export", "-e", help="Export analysis report to file")
    parser.add_argument(
        "--output-dir", default="analytics_output", help="Output directory for files"
    )

    args = parser.parse_args()

    analytics = RepairAnalytics(args.base_path)

    if args.dashboard:
        analytics.display_analytics_dashboard()
    elif args.patterns:
        patterns = analytics.analyze_failure_patterns()
        print(f"{Colors.YELLOW}Failure Pattern Analysis:{Colors.END}")
        for pattern in patterns:
            print(f"Pattern: {pattern.pattern_type}")
            print(f"  Frequency: {pattern.frequency}")
            print(f"  Success Rate: {pattern.success_rate:.1f}%")
            print(f"  Recommendations: {', '.join(pattern.recommendations[:2])}")
            print()
    elif args.recommendations:
        recommendations = analytics.generate_optimization_recommendations()
        print(f"{Colors.YELLOW}Optimization Recommendations:{Colors.END}")
        for rec in recommendations:
            print(f"[{rec.priority.upper()}] {rec.category}: {rec.description}")
            print(f"  Expected Impact: {rec.expected_impact}")
            print(f"  Estimated Improvement: {rec.estimated_improvement:.1f}%")
            print()
    elif args.trends:
        analytics.generate_trend_analysis(args.trends)
    elif args.anomalies:
        anomalies = analytics.detect_anomalies()
        print(f"{Colors.YELLOW}Anomaly Detection Results:{Colors.END}")
        for anomaly in anomalies:
            print(f"Anomaly Score: {anomaly['anomaly_score']:.3f}")
            print(f"  Duration: {anomaly['duration']:.1f}s")
            print(f"  Retries: {anomaly['retry_count']}")
            print()
    elif args.visualize:
        analytics.create_visualizations(args.output_dir)
    elif args.export:
        analytics.export_analysis_report(args.export)
    else:
        analytics.display_analytics_dashboard()


if __name__ == "__main__":
    main()
