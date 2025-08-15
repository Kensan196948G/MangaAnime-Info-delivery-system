"""
Enhanced Monitoring and alerting module for the Anime/Manga Information Delivery System.
Provides system health monitoring, performance tracking, security incident alerting, and integrated error recovery.
"""

import os
import json
import time
import smtplib
import logging
import sqlite3
from collections import deque
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import psutil
import asyncio
from pathlib import Path

try:
    import psutil
except ImportError:
    psutil = None
    logging.warning("psutil not available - system metrics will be limited")


@dataclass
class SystemMetrics:
    """System resource metrics"""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    active_connections: int
    load_average: float


@dataclass
class ApplicationMetrics:
    """Application-specific metrics"""
    timestamp: float
    api_calls_total: int
    api_calls_by_service: Dict[str, int]
    average_response_times: Dict[str, float]
    error_counts: Dict[str, int]
    processed_items: Dict[str, int]
    active_tokens: int
    failed_authentications: int


@dataclass
class AlertCondition:
    """Alert condition configuration"""
    name: str
    condition_type: str  # 'threshold', 'rate', 'pattern'
    metric_path: str
    operator: str  # '>', '<', '==', '!='
    threshold: float
    duration_seconds: int
    severity: str  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    enabled: bool = True


@dataclass
class Alert:
    """Alert instance"""
    condition_name: str
    severity: str
    message: str
    timestamp: float
    metric_value: float
    resolved: bool = False
    resolved_timestamp: Optional[float] = None


class HealthChecker:
    """System health monitoring"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._last_check = 0
        self._check_interval = 60  # 60 seconds
    
    def check_database_health(self, db_path: str) -> Tuple[bool, str]:
        """Check database connectivity and integrity"""
        try:
            conn = sqlite3.connect(db_path, timeout=5)
            
            # Test basic connectivity
            cursor = conn.execute("SELECT 1")
            cursor.fetchone()
            
            # Check table integrity
            cursor = conn.execute("PRAGMA integrity_check")
            integrity_result = cursor.fetchone()[0]
            
            conn.close()
            
            if integrity_result == 'ok':
                return True, "Database healthy"
            else:
                return False, f"Database integrity issue: {integrity_result}"
                
        except sqlite3.Error as e:
            return False, f"Database connection failed: {e}"
    
    def check_api_endpoints(self) -> Dict[str, Tuple[bool, str]]:
        """Check external API endpoints availability"""
        endpoints = {
            'anilist': 'https://graphql.anilist.co',
            'syoboi': 'https://cal.syoboi.jp/json.php',
            'google_oauth': 'https://accounts.google.com/.well-known/openid_configuration'
        }
        
        results = {}
        
        for name, url in endpoints.items():
            try:
                import requests
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    results[name] = (True, f"OK ({response.status_code})")
                else:
                    results[name] = (False, f"HTTP {response.status_code}")
                    
            except requests.RequestException as e:
                results[name] = (False, f"Request failed: {e}")
        
        return results
    
    def check_file_system(self) -> Dict[str, Tuple[bool, str]]:
        """Check file system health"""
        results = {}
        
        # Check log directory
        log_dir = self.config.get('logging', {}).get('file_path', './logs/app.log')
        log_dir = os.path.dirname(log_dir)
        
        if os.path.exists(log_dir) and os.access(log_dir, os.W_OK):
            results['log_directory'] = (True, "Writable")
        else:
            results['log_directory'] = (False, "Not writable or missing")
        
        # Check database directory
        db_path = self.config.get('database', {}).get('path', './db.sqlite3')
        db_dir = os.path.dirname(os.path.abspath(db_path))
        
        if os.path.exists(db_dir) and os.access(db_dir, os.W_OK):
            results['database_directory'] = (True, "Writable")
        else:
            results['database_directory'] = (False, "Not writable or missing")
        
        # Check token file directory
        token_file = self.config.get('google', {}).get('token_file', './token.json')
        token_dir = os.path.dirname(os.path.abspath(token_file))
        
        if os.path.exists(token_dir) and os.access(token_dir, os.W_OK):
            results['token_directory'] = (True, "Writable")
        else:
            results['token_directory'] = (False, "Not writable or missing")
        
        return results
    
    def perform_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        health_status = {
            'timestamp': time.time(),
            'overall_healthy': True,
            'checks': {}
        }
        
        # Database health
        db_path = self.config.get('database', {}).get('path', './db.sqlite3')
        db_healthy, db_message = self.check_database_health(db_path)
        health_status['checks']['database'] = {
            'healthy': db_healthy,
            'message': db_message
        }
        
        if not db_healthy:
            health_status['overall_healthy'] = False
        
        # API endpoints
        api_results = self.check_api_endpoints()
        health_status['checks']['api_endpoints'] = {}
        
        for endpoint, (healthy, message) in api_results.items():
            health_status['checks']['api_endpoints'][endpoint] = {
                'healthy': healthy,
                'message': message
            }
            if not healthy:
                health_status['overall_healthy'] = False
        
        # File system
        fs_results = self.check_file_system()
        health_status['checks']['file_system'] = {}
        
        for check, (healthy, message) in fs_results.items():
            health_status['checks']['file_system'][check] = {
                'healthy': healthy,
                'message': message
            }
            if not healthy:
                health_status['overall_healthy'] = False
        
        return health_status


class MetricsCollector:
    """Collect system and application metrics"""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.system_metrics = deque(maxlen=max_history)
        self.app_metrics = deque(maxlen=max_history)
        self.api_call_times = defaultdict(list)
        self.error_counts = defaultdict(int)
        self.processed_counts = defaultdict(int)
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
    
    def collect_system_metrics(self) -> Optional[SystemMetrics]:
        """Collect system resource metrics"""
        if not psutil:
            return None
        
        try:
            # Get load average (Unix systems)
            try:
                load_avg = os.getloadavg()[0] if hasattr(os, 'getloadavg') else 0.0
            except (AttributeError, OSError):
                load_avg = 0.0
            
            metrics = SystemMetrics(
                timestamp=time.time(),
                cpu_percent=psutil.cpu_percent(interval=0.1),
                memory_percent=psutil.virtual_memory().percent,
                disk_usage_percent=psutil.disk_usage('/').percent,
                active_connections=len(psutil.net_connections()),
                load_average=load_avg
            )
            
            with self.lock:
                self.system_metrics.append(metrics)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to collect system metrics: {e}")
            return None
    
    def collect_application_metrics(self) -> ApplicationMetrics:
        """Collect application-specific metrics"""
        with self.lock:
            # Calculate average response times
            avg_response_times = {}
            for service, times in self.api_call_times.items():
                if times:
                    avg_response_times[service] = sum(times) / len(times)
                    # Keep only recent times (last 100)
                    if len(times) > 100:
                        self.api_call_times[service] = times[-100:]
            
            # Count total API calls
            total_api_calls = sum(len(times) for times in self.api_call_times.values())
            api_calls_by_service = {
                service: len(times) for service, times in self.api_call_times.items()
            }
            
            metrics = ApplicationMetrics(
                timestamp=time.time(),
                api_calls_total=total_api_calls,
                api_calls_by_service=api_calls_by_service.copy(),
                average_response_times=avg_response_times.copy(),
                error_counts=dict(self.error_counts),
                processed_items=dict(self.processed_counts),
                active_tokens=1,  # This would be set by token manager
                failed_authentications=self.error_counts.get('auth_failure', 0)
            )
            
            self.app_metrics.append(metrics)
            return metrics
    
    def record_api_call(self, service: str, response_time: float, success: bool = True):
        """Record API call metrics"""
        with self.lock:
            self.api_call_times[service].append(response_time)
            
            if not success:
                self.error_counts[f"api_{service}_error"] += 1
    
    def record_processed_item(self, item_type: str, count: int = 1):
        """Record processed item count"""
        with self.lock:
            self.processed_counts[item_type] += count
    
    def record_error(self, error_type: str, count: int = 1):
        """Record error occurrence"""
        with self.lock:
            self.error_counts[error_type] += count
    
    def get_metrics_summary(self, hours: int = 1) -> Dict[str, Any]:
        """Get metrics summary for specified time period"""
        cutoff_time = time.time() - (hours * 3600)
        
        with self.lock:
            # Filter recent metrics
            recent_system = [m for m in self.system_metrics if m.timestamp > cutoff_time]
            recent_app = [m for m in self.app_metrics if m.timestamp > cutoff_time]
            
            summary = {
                'time_period_hours': hours,
                'system_metrics': {
                    'count': len(recent_system),
                    'avg_cpu_percent': 0,
                    'avg_memory_percent': 0,
                    'max_cpu_percent': 0,
                    'max_memory_percent': 0
                },
                'application_metrics': {
                    'total_api_calls': 0,
                    'total_errors': sum(self.error_counts.values()),
                    'total_processed_items': sum(self.processed_counts.values())
                }
            }
            
            # Calculate system metrics averages
            if recent_system:
                cpu_values = [m.cpu_percent for m in recent_system]
                memory_values = [m.memory_percent for m in recent_system]
                
                summary['system_metrics'].update({
                    'avg_cpu_percent': sum(cpu_values) / len(cpu_values),
                    'avg_memory_percent': sum(memory_values) / len(memory_values),
                    'max_cpu_percent': max(cpu_values),
                    'max_memory_percent': max(memory_values)
                })
            
            # Calculate application metrics
            if recent_app:
                api_calls = [m.api_calls_total for m in recent_app]
                summary['application_metrics']['total_api_calls'] = max(api_calls) if api_calls else 0
        
        return summary
    
    def export_metrics(self, filepath: str) -> None:
        """Export metrics to JSON file"""
        try:
            with self.lock:
                export_data = {
                    'export_timestamp': time.time(),
                    'system_metrics': [asdict(m) for m in list(self.system_metrics)],
                    'application_metrics': [asdict(m) for m in list(self.app_metrics)],
                    'summary': self.get_metrics_summary(24)  # 24-hour summary
                }
            
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2)
                
            self.logger.info(f"Metrics exported to {filepath}")
            
        except Exception as e:
            self.logger.error(f"Failed to export metrics: {e}")


class AlertManager:
    """Manage alerts and notifications"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.conditions: List[AlertCondition] = []
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.logger = logging.getLogger(__name__)
        
        # Load default alert conditions
        self._load_default_conditions()
    
    def _load_default_conditions(self):
        """Load default alert conditions"""
        default_conditions = [
            AlertCondition(
                name="high_cpu_usage",
                condition_type="threshold",
                metric_path="system_metrics.cpu_percent",
                operator=">",
                threshold=80.0,
                duration_seconds=300,  # 5 minutes
                severity="HIGH"
            ),
            AlertCondition(
                name="high_memory_usage",
                condition_type="threshold",
                metric_path="system_metrics.memory_percent",
                operator=">",
                threshold=85.0,
                duration_seconds=300,
                severity="HIGH"
            ),
            AlertCondition(
                name="low_disk_space",
                condition_type="threshold",
                metric_path="system_metrics.disk_usage_percent",
                operator=">",
                threshold=90.0,
                duration_seconds=60,
                severity="CRITICAL"
            ),
            AlertCondition(
                name="high_error_rate",
                condition_type="rate",
                metric_path="application_metrics.error_counts",
                operator=">",
                threshold=10,
                duration_seconds=900,  # 15 minutes
                severity="MEDIUM"
            ),
            AlertCondition(
                name="authentication_failures",
                condition_type="threshold",
                metric_path="application_metrics.failed_authentications",
                operator=">",
                threshold=5,
                duration_seconds=3600,  # 1 hour
                severity="HIGH"
            )
        ]
        
        self.conditions.extend(default_conditions)
    
    def add_condition(self, condition: AlertCondition):
        """Add new alert condition"""
        self.conditions.append(condition)
        self.logger.info(f"Added alert condition: {condition.name}")
    
    def evaluate_conditions(self, metrics_data: Dict[str, Any]) -> List[Alert]:
        """Evaluate all conditions against current metrics"""
        triggered_alerts = []
        
        for condition in self.conditions:
            if not condition.enabled:
                continue
            
            try:
                # Get metric value
                metric_value = self._get_metric_value(metrics_data, condition.metric_path)
                
                if metric_value is None:
                    continue
                
                # Evaluate condition
                if self._evaluate_condition(condition, metric_value):
                    alert = self._create_alert(condition, metric_value)
                    triggered_alerts.append(alert)
            
            except Exception as e:
                self.logger.error(f"Error evaluating condition {condition.name}: {e}")
        
        return triggered_alerts
    
    def _get_metric_value(self, metrics_data: Dict[str, Any], metric_path: str) -> Optional[float]:
        """Extract metric value using dot notation path"""
        keys = metric_path.split('.')
        value = metrics_data
        
        try:
            for key in keys:
                if isinstance(value, dict):
                    value = value[key]
                else:
                    return None
            
            if isinstance(value, (int, float)):
                return float(value)
            elif isinstance(value, dict):
                # For dictionary values (like error_counts), return sum
                return float(sum(value.values()) if value else 0)
            else:
                return None
                
        except (KeyError, TypeError):
            return None
    
    def _evaluate_condition(self, condition: AlertCondition, metric_value: float) -> bool:
        """Evaluate single condition"""
        if condition.operator == '>':
            return metric_value > condition.threshold
        elif condition.operator == '<':
            return metric_value < condition.threshold
        elif condition.operator == '==':
            return metric_value == condition.threshold
        elif condition.operator == '!=':
            return metric_value != condition.threshold
        else:
            return False
    
    def _create_alert(self, condition: AlertCondition, metric_value: float) -> Alert:
        """Create alert from triggered condition"""
        message = (
            f"{condition.name}: {condition.metric_path} is {metric_value} "
            f"({condition.operator} {condition.threshold})"
        )
        
        alert = Alert(
            condition_name=condition.name,
            severity=condition.severity,
            message=message,
            timestamp=time.time(),
            metric_value=metric_value
        )
        
        # Track active alert
        self.active_alerts[condition.name] = alert
        self.alert_history.append(alert)
        
        # Keep only last 1000 alerts in history
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-1000:]
        
        return alert
    
    def resolve_alert(self, condition_name: str):
        """Mark alert as resolved"""
        if condition_name in self.active_alerts:
            alert = self.active_alerts[condition_name]
            alert.resolved = True
            alert.resolved_timestamp = time.time()
            del self.active_alerts[condition_name]
            
            self.logger.info(f"Resolved alert: {condition_name}")
    
    def get_active_alerts(self) -> List[Alert]:
        """Get list of active alerts"""
        return list(self.active_alerts.values())
    
    def send_alert_notification(self, alert: Alert):
        """Send alert notification via configured channels"""
        try:
            # Log alert
            self.logger.warning(f"ALERT [{alert.severity}]: {alert.message}")
            
            # Send email notification if configured
            email_config = self.config.get('alerting', {}).get('email', {})
            if email_config.get('enabled', False):
                self._send_email_alert(alert, email_config)
                
        except Exception as e:
            self.logger.error(f"Failed to send alert notification: {e}")
    
    def _send_email_alert(self, alert: Alert, email_config: Dict[str, Any]):
        """Send alert via email"""
        try:
            msg = MIMEMultipart()
            msg['From'] = email_config['from_email']
            msg['To'] = email_config['to_email']
            msg['Subject'] = f"[{alert.severity}] System Alert: {alert.condition_name}"
            
            body = f"""
            Alert Details:
            
            Condition: {alert.condition_name}
            Severity: {alert.severity}
            Message: {alert.message}
            Timestamp: {datetime.fromtimestamp(alert.timestamp)}
            Metric Value: {alert.metric_value}
            
            Please investigate this issue.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email (this would need proper SMTP configuration)
            # For now, just log the email content
            self.logger.info(f"Email alert prepared: {msg['Subject']}")
            
        except Exception as e:
            self.logger.error(f"Failed to prepare email alert: {e}")


class SystemMonitor:
    """Main system monitoring coordinator - Phase 2 Enhanced"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.health_checker = HealthChecker(config)
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager(config)
        self.logger = logging.getLogger(__name__)
        
        self._running = False
        self._monitor_thread = None
        self._last_health_check = 0
        self._last_metrics_export = 0
        
        # Phase 2: Real-time monitoring enhancements
        self.real_time_alerts = []
        self.performance_history = deque(maxlen=1440)  # 24-hour history (1-minute intervals)
        self.collection_performance_tracker = {
            'anilist_api': {'requests': 0, 'errors': 0, 'avg_response_time': 0.0},
            'rss_feeds': {'feeds_processed': 0, 'errors': 0, 'avg_processing_time': 0.0},
            'database': {'queries': 0, 'errors': 0, 'avg_query_time': 0.0}
        }
    
    def start_monitoring(self):
        """Start continuous monitoring"""
        if self._running:
            self.logger.warning("Monitoring already started")
            return
        
        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._monitor_thread.start()
        
        self.logger.info("System monitoring started")
    
    def stop_monitoring(self):
        """Stop continuous monitoring"""
        self._running = False
        
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        
        self.logger.info("System monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self._running:
            try:
                current_time = time.time()
                
                # Collect metrics every 60 seconds
                if current_time - getattr(self, '_last_metrics_collection', 0) > 60:
                    self._collect_all_metrics()
                    self._last_metrics_collection = current_time
                
                # Health check every 5 minutes
                if current_time - self._last_health_check > 300:
                    self._perform_health_check()
                    self._last_health_check = current_time
                
                # Export metrics every hour
                if current_time - self._last_metrics_export > 3600:
                    self._export_metrics()
                    self._last_metrics_export = current_time
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _collect_all_metrics(self):
        """Collect all system and application metrics - Phase 2 Enhanced"""
        # Collect system metrics
        system_metrics = self.metrics_collector.collect_system_metrics()
        
        # Collect application metrics
        app_metrics = self.metrics_collector.collect_application_metrics()
        
        # Prepare metrics data for alert evaluation
        metrics_data = {}
        
        if system_metrics:
            metrics_data['system_metrics'] = asdict(system_metrics)
        
        if app_metrics:
            metrics_data['application_metrics'] = asdict(app_metrics)
        
        # Phase 2: Enhanced performance tracking
        performance_snapshot = {
            'timestamp': time.time(),
            'system_metrics': asdict(system_metrics) if system_metrics else {},
            'application_metrics': asdict(app_metrics) if app_metrics else {},
            'collection_performance': self.collection_performance_tracker.copy(),
            'overall_score': self._calculate_overall_performance_score(system_metrics, app_metrics)
        }
        
        self.performance_history.append(performance_snapshot)
        
        # Evaluate alert conditions
        triggered_alerts = self.alert_manager.evaluate_conditions(metrics_data)
        
        # Send notifications for new alerts
        for alert in triggered_alerts:
            self.alert_manager.send_alert_notification(alert)
            # Add to real-time alerts for dashboard
            self.add_real_time_alert(alert.message, alert.severity)
    
    def _calculate_overall_performance_score(self, system_metrics, app_metrics) -> float:
        """
        Calculate overall system performance score (0.0 to 1.0).
        
        Args:
            system_metrics: System resource metrics
            app_metrics: Application performance metrics
            
        Returns:
            Performance score from 0.0 (poor) to 1.0 (excellent)
        """
        score = 1.0
        
        # System resource penalties
        if system_metrics:
            if system_metrics.cpu_percent > 80:
                score -= 0.2
            elif system_metrics.cpu_percent > 60:
                score -= 0.1
            
            if system_metrics.memory_percent > 85:
                score -= 0.2
            elif system_metrics.memory_percent > 70:
                score -= 0.1
            
            if system_metrics.disk_usage_percent > 90:
                score -= 0.3
            elif system_metrics.disk_usage_percent > 80:
                score -= 0.15
        
        # Application performance penalties
        if app_metrics:
            if app_metrics.error_counts:
                total_errors = sum(app_metrics.error_counts.values())
                if total_errors > 10:
                    score -= 0.2
                elif total_errors > 5:
                    score -= 0.1
        
        # Collection performance penalties
        for service, metrics in self.collection_performance_tracker.items():
            total_ops = (metrics.get('requests', 0) + 
                        metrics.get('feeds_processed', 0) + 
                        metrics.get('queries', 0))
            if total_ops > 0:
                error_rate = metrics['errors'] / total_ops
                if error_rate > 0.1:
                    score -= 0.15 * error_rate
        
        return max(0.0, min(1.0, score))
    
    def _perform_health_check(self):
        """Perform comprehensive health check"""
        health_status = self.health_checker.perform_health_check()
        
        if not health_status['overall_healthy']:
            self.logger.warning(f"Health check failed: {health_status}")
        else:
            self.logger.debug("Health check passed")
    
    def _export_metrics(self):
        """Export metrics to file"""
        try:
            export_path = self.config.get('monitoring', {}).get(
                'metrics_export_path', 
                './logs/metrics.json'
            )
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(export_path), exist_ok=True)
            
            self.metrics_collector.export_metrics(export_path)
            
        except Exception as e:
            self.logger.error(f"Failed to export metrics: {e}")
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get comprehensive monitoring status - Phase 2 Enhanced"""
        return {
            'monitoring_active': self._running,
            'active_alerts': len(self.alert_manager.get_active_alerts()),
            'metrics_collected': len(self.metrics_collector.system_metrics),
            'last_health_check': datetime.fromtimestamp(self._last_health_check).isoformat() if self._last_health_check else None,
            'last_metrics_export': datetime.fromtimestamp(self._last_metrics_export).isoformat() if self._last_metrics_export else None,
            
            # Phase 2: Enhanced monitoring data
            'real_time_alerts_count': len(self.real_time_alerts),
            'performance_history_size': len(self.performance_history),
            'collection_performance': self.collection_performance_tracker.copy(),
            
            # System health overview
            'system_health_grade': self._calculate_system_health_grade(),
            'critical_issues': self._get_critical_issues(),
            'performance_trend': self._get_performance_trend(),
            
            # Monitoring uptime
            'monitoring_uptime_hours': self._get_monitoring_uptime_hours()
        }
    
    def _calculate_system_health_grade(self) -> str:
        """
        Calculate overall system health grade.
        
        Returns:
            Health grade: 'A', 'B', 'C', 'D', or 'F'
        """
        active_alerts = self.alert_manager.get_active_alerts()
        critical_alerts = [alert for alert in active_alerts if alert.severity == 'CRITICAL']
        high_alerts = [alert for alert in active_alerts if alert.severity == 'HIGH']
        
        if len(critical_alerts) > 0:
            return 'F'  # Failing - Critical issues
        elif len(high_alerts) > 2:
            return 'D'  # Poor - Multiple high-priority issues
        elif len(high_alerts) > 0:
            return 'C'  # Fair - Some high-priority issues
        elif len(active_alerts) > 3:
            return 'B'  # Good - Minor issues
        else:
            return 'A'  # Excellent - No significant issues
    
    def _get_critical_issues(self) -> List[str]:
        """
        Get list of critical issues requiring immediate attention.
        
        Returns:
            List of critical issue descriptions
        """
        critical_issues = []
        
        active_alerts = self.alert_manager.get_active_alerts()
        for alert in active_alerts:
            if alert.severity in ['CRITICAL', 'HIGH']:
                critical_issues.append(f"{alert.condition_name}: {alert.message}")
        
        # Check collection performance issues
        for service, metrics in self.collection_performance_tracker.items():
            if metrics['requests'] > 0 or metrics.get('feeds_processed', 0) > 0 or metrics.get('queries', 0) > 0:
                error_rate = metrics['errors'] / max(metrics['requests'] or metrics.get('feeds_processed', 0) or metrics.get('queries', 0), 1)
                if error_rate > 0.2:  # More than 20% error rate
                    critical_issues.append(f"{service} high error rate: {error_rate:.1%}")
        
        return critical_issues
    
    def _get_performance_trend(self) -> str:
        """
        Analyze performance trend over recent history.
        
        Returns:
            Trend description: 'improving', 'stable', 'degrading', or 'unknown'
        """
        if len(self.performance_history) < 10:
            return 'unknown'
        
        recent_performance = list(self.performance_history)[-10:]  # Last 10 data points
        older_performance = list(self.performance_history)[-20:-10]  # Previous 10 data points
        
        if len(older_performance) < 5:
            return 'unknown'
        
        recent_avg = sum(p.get('overall_score', 0.5) for p in recent_performance) / len(recent_performance)
        older_avg = sum(p.get('overall_score', 0.5) for p in older_performance) / len(older_performance)
        
        diff = recent_avg - older_avg
        
        if diff > 0.05:
            return 'improving'
        elif diff < -0.05:
            return 'degrading'
        else:
            return 'stable'
    
    def _get_monitoring_uptime_hours(self) -> float:
        """
        Calculate monitoring system uptime in hours.
        
        Returns:
            Uptime in hours
        """
        if not hasattr(self, '_start_time'):
            self._start_time = time.time()
        
        return (time.time() - self._start_time) / 3600.0
    
    def record_collection_performance(self, service: str, operation_type: str, 
                                    response_time: float, success: bool):
        """
        Record performance metrics for data collection operations.
        
        Args:
            service: Service name ('anilist_api', 'rss_feeds', 'database')
            operation_type: Type of operation ('request', 'feed_process', 'query')
            response_time: Time taken for the operation
            success: Whether the operation was successful
        """
        if service not in self.collection_performance_tracker:
            return
        
        tracker = self.collection_performance_tracker[service]
        
        # Update counters based on operation type
        if operation_type == 'request' and service == 'anilist_api':
            tracker['requests'] += 1
        elif operation_type == 'feed_process' and service == 'rss_feeds':
            tracker['feeds_processed'] += 1
        elif operation_type == 'query' and service == 'database':
            tracker['queries'] += 1
        
        # Update error counter
        if not success:
            tracker['errors'] += 1
        
        # Update average response time
        total_operations = (tracker.get('requests', 0) + 
                          tracker.get('feeds_processed', 0) + 
                          tracker.get('queries', 0))
        
        if total_operations > 0:
            current_avg = tracker.get('avg_response_time', 0.0) or tracker.get('avg_processing_time', 0.0) or tracker.get('avg_query_time', 0.0)
            new_avg = ((current_avg * (total_operations - 1)) + response_time) / total_operations
            
            if service == 'anilist_api':
                tracker['avg_response_time'] = new_avg
            elif service == 'rss_feeds':
                tracker['avg_processing_time'] = new_avg
            elif service == 'database':
                tracker['avg_query_time'] = new_avg
    
    def add_real_time_alert(self, alert_message: str, severity: str = 'INFO'):
        """
        Add real-time alert for immediate attention.
        
        Args:
            alert_message: Alert description
            severity: Alert severity level
        """
        alert = {
            'timestamp': time.time(),
            'message': alert_message,
            'severity': severity
        }
        
        self.real_time_alerts.append(alert)
        
        # Keep only last 100 real-time alerts
        if len(self.real_time_alerts) > 100:
            self.real_time_alerts = self.real_time_alerts[-100:]
        
        self.logger.info(f"Real-time alert [{severity}]: {alert_message}")


# Global monitoring instance
_system_monitor: Optional[SystemMonitor] = None

def initialize_monitoring(config: Dict[str, Any]) -> SystemMonitor:
    """Initialize global monitoring instance"""
    global _system_monitor
    _system_monitor = SystemMonitor(config)
    return _system_monitor

def get_system_monitor() -> Optional[SystemMonitor]:
    """Get global monitoring instance"""
    return _system_monitor


# Phase 2: Real-time monitoring integration functions
def record_api_performance(service: str, response_time: float, success: bool = True):
    """
    Record API performance for monitoring integration.
    
    Args:
        service: Service name ('anilist', 'rss', etc.)
        response_time: Response time in seconds
        success: Whether the operation was successful
    """
    monitor = get_system_monitor()
    if monitor:
        if service == 'anilist':
            monitor.record_collection_performance('anilist_api', 'request', response_time, success)
        elif service == 'rss':
            monitor.record_collection_performance('rss_feeds', 'feed_process', response_time, success)
        elif service == 'database':
            monitor.record_collection_performance('database', 'query', response_time, success)


def add_monitoring_alert(message: str, severity: str = 'INFO'):
    """
    Add real-time monitoring alert.
    
    Args:
        message: Alert message
        severity: Alert severity ('INFO', 'WARNING', 'ERROR', 'CRITICAL')
    """
    monitor = get_system_monitor()
    if monitor:
        monitor.add_real_time_alert(message, severity)


def get_collection_health_status() -> Dict[str, Any]:
    """
    Get current collection system health status.
    
    Returns:
        Health status dictionary
    """
    monitor = get_system_monitor()
    if monitor:
        return monitor.get_monitoring_status()
    else:
        return {
            'monitoring_active': False,
            'system_health_grade': 'unknown',
            'critical_issues': ['Monitoring system not initialized']
        }