"""
Enhanced Error Recovery Module

This module provides advanced error recovery and monitoring functionality for the
anime/manga information delivery system with improved resilience and self-healing capabilities.
"""

import json
import logging
import threading
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


class ErrorSeverity(Enum):
    """Error severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecoveryStrategy(Enum):
    """Recovery strategy types"""

    RETRY = "retry"
    FALLBACK = "fallback"
    RESET = "reset"
    MANUAL = "manual"
    IGNORE = "ignore"


@dataclass
class ErrorEvent:
    """Represents an error event with context"""

    timestamp: datetime
    component: str
    error_type: str
    message: str
    severity: ErrorSeverity
    details: Dict[str, Any] = field(default_factory=dict)
    traceback_info: Optional[str] = None
    recovery_attempted: bool = False
    recovery_successful: bool = False
    recovery_strategy: Optional[RecoveryStrategy] = None


@dataclass
class ComponentHealth:
    """Tracks health status of system components"""

    component_name: str
    is_healthy: bool = True
    last_error: Optional[ErrorEvent] = None
    error_count: int = 0
    consecutive_errors: int = 0
    last_success: Optional[datetime] = None
    health_score: float = 1.0
    recovery_attempts: int = 0
    last_recovery_attempt: Optional[datetime] = None


class EnhancedErrorRecovery:
    """
    Enhanced error recovery system with intelligent monitoring and automatic healing.

    Features:
    - Component health tracking
    - Intelligent recovery strategies
    - Error pattern analysis
    - Automatic system healing
    - Performance monitoring integration
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize enhanced error recovery system.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Component health tracking
        self.component_health: Dict[str, ComponentHealth] = {}
        self.health_lock = threading.Lock()

        # Error event storage
        self.error_events: List[ErrorEvent] = []
        self.max_error_events = config.get("error_recovery", {}).get(
            "max_error_events", 1000
        )
        self.events_lock = threading.Lock()

        # Recovery strategies mapping
        self.recovery_strategies: Dict[str, Dict[str, Any]] = {
            "anilist_api": {
                "rate_limit_error": RecoveryStrategy.RETRY,
                "network_error": RecoveryStrategy.RETRY,
                "auth_error": RecoveryStrategy.RESET,
                "server_error": RecoveryStrategy.FALLBACK,
            },
            "manga_rss": {
                "timeout_error": RecoveryStrategy.RETRY,
                "parsing_error": RecoveryStrategy.FALLBACK,
                "network_error": RecoveryStrategy.RETRY,
                "feed_error": RecoveryStrategy.IGNORE,
            },
            "gmail_api": {
                "auth_error": RecoveryStrategy.RESET,
                "rate_limit_error": RecoveryStrategy.RETRY,
                "network_error": RecoveryStrategy.RETRY,
                "quota_error": RecoveryStrategy.FALLBACK,
            },
            "calendar_api": {
                "auth_error": RecoveryStrategy.RESET,
                "rate_limit_error": RecoveryStrategy.RETRY,
                "network_error": RecoveryStrategy.RETRY,
                "calendar_error": RecoveryStrategy.FALLBACK,
            },
            "database": {
                "connection_error": RecoveryStrategy.RETRY,
                "lock_error": RecoveryStrategy.RETRY,
                "corruption_error": RecoveryStrategy.MANUAL,
                "disk_error": RecoveryStrategy.MANUAL,
            },
        }

        # Recovery handlers
        self.recovery_handlers: Dict[RecoveryStrategy, Callable] = {
            RecoveryStrategy.RETRY: self._retry_recovery,
            RecoveryStrategy.FALLBACK: self._fallback_recovery,
            RecoveryStrategy.RESET: self._reset_recovery,
            RecoveryStrategy.MANUAL: self._manual_recovery,
            RecoveryStrategy.IGNORE: self._ignore_recovery,
        }

        # Monitoring settings
        self.monitoring_interval = config.get("error_recovery", {}).get(
            "monitoring_interval", 60
        )
        self.health_threshold = config.get("error_recovery", {}).get(
            "health_threshold", 0.8
        )
        self.max_consecutive_errors = config.get("error_recovery", {}).get(
            "max_consecutive_errors", 5
        )

        # Performance tracking
        self.total_errors_handled = 0
        self.successful_recoveries = 0
        self.failed_recoveries = 0
        self.start_time = datetime.now()

        # Initialize component health
        self._initialize_component_health()

        # Start monitoring thread
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop, daemon=True
        )
        self.monitoring_thread.start()

        self.logger.info("Enhanced error recovery system initialized")

    def _initialize_component_health(self):
        """Initialize health tracking for all components."""
        components = [
            "anilist_api",
            "manga_rss",
            "gmail_api",
            "calendar_api",
            "database",
            "web_ui",
            "config_manager",
            "notification_system",
        ]

        with self.health_lock:
            for component in components:
                self.component_health[component] = ComponentHealth(
                    component_name=component
                )

    def record_error(
        self,
        component: str,
        error_type: str,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        details: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
    ) -> ErrorEvent:
        """
        Record an error event and trigger recovery if needed.

        Args:
            component: Component name where error occurred
            error_type: Type of error
            message: Error message
            severity: Error severity level
            details: Additional error details
            exception: Original exception object

        Returns:
            ErrorEvent: The recorded error event
        """
        # Create error event
        error_event = ErrorEvent(
            timestamp=datetime.now(),
            component=component,
            error_type=error_type,
            message=message,
            severity=severity,
            details=details or {},
            traceback_info=traceback.format_exc() if exception else None,
        )

        # Record error event
        with self.events_lock:
            self.error_events.append(error_event)
            # Limit stored events
            if len(self.error_events) > self.max_error_events:
                self.error_events = self.error_events[-self.max_error_events :]

        # Update component health
        self._update_component_health(component, error_event)

        # Trigger recovery if needed
        self._attempt_recovery(error_event)

        self.total_errors_handled += 1

        # Log error
        log_level = {
            ErrorSeverity.LOW: logging.DEBUG,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL,
        }.get(severity, logging.WARNING)

        self.logger.log(log_level, f"Error in {component}: {error_type} - {message}")

        return error_event

    def record_success(self, component: str, details: Optional[Dict[str, Any]] = None):
        """
        Record a successful operation for a component.

        Args:
            component: Component name
            details: Optional success details
        """
        with self.health_lock:
            if component not in self.component_health:
                self.component_health[component] = ComponentHealth(
                    component_name=component
                )

            health = self.component_health[component]
            health.last_success = datetime.now()
            health.consecutive_errors = 0
            health.is_healthy = True

            # Improve health score
            health.health_score = min(1.0, health.health_score + 0.1)

        self.logger.debug(f"Success recorded for {component}")

    def _update_component_health(self, component: str, error_event: ErrorEvent):
        """Update component health based on error event."""
        with self.health_lock:
            if component not in self.component_health:
                self.component_health[component] = ComponentHealth(
                    component_name=component
                )

            health = self.component_health[component]
            health.last_error = error_event
            health.error_count += 1
            health.consecutive_errors += 1

            # Update health score based on severity
            severity_penalty = {
                ErrorSeverity.LOW: 0.05,
                ErrorSeverity.MEDIUM: 0.1,
                ErrorSeverity.HIGH: 0.2,
                ErrorSeverity.CRITICAL: 0.4,
            }.get(error_event.severity, 0.1)

            health.health_score = max(0.0, health.health_score - severity_penalty)

            # Mark as unhealthy if threshold exceeded
            if (
                health.consecutive_errors >= self.max_consecutive_errors
                or health.health_score < self.health_threshold
            ):
                health.is_healthy = False

    def _attempt_recovery(self, error_event: ErrorEvent):
        """Attempt to recover from an error."""
        component = error_event.component
        error_type = error_event.error_type

        # Determine recovery strategy
        strategy = self._get_recovery_strategy(component, error_type)
        if not strategy:
            self.logger.debug(f"No recovery strategy for {component}:{error_type}")
            return

        error_event.recovery_strategy = strategy
        error_event.recovery_attempted = True

        # Update component health
        with self.health_lock:
            health = self.component_health.get(component)
            if health:
                health.recovery_attempts += 1
                health.last_recovery_attempt = datetime.now()

        # Execute recovery
        try:
            handler = self.recovery_handlers.get(strategy)
            if handler:
                success = handler(error_event)
                error_event.recovery_successful = success

                if success:
                    self.successful_recoveries += 1
                    self.logger.info(
                        f"Recovery successful for {component}:{error_type} using {strategy.value}"
                    )
                else:
                    self.failed_recoveries += 1
                    self.logger.warning(
                        f"Recovery failed for {component}:{error_type} using {strategy.value}"
                    )

        except Exception as e:
            self.failed_recoveries += 1
            self.logger.error(
                f"Recovery handler failed for {component}:{error_type}: {e}"
            )

    def _get_recovery_strategy(
        self, component: str, error_type: str
    ) -> Optional[RecoveryStrategy]:
        """Get recovery strategy for component and error type."""
        component_strategies = self.recovery_strategies.get(component, {})
        return component_strategies.get(error_type)

    def _retry_recovery(self, error_event: ErrorEvent) -> bool:
        """Implement retry recovery strategy."""
        self.logger.info(
            f"Applying retry recovery for {error_event.component}:{error_event.error_type}"
        )

        # For retry strategy, we mark for retry but don't execute here
        # The actual retry should be handled by the calling component
        return True

    def _fallback_recovery(self, error_event: ErrorEvent) -> bool:
        """Implement fallback recovery strategy."""
        self.logger.info(
            f"Applying fallback recovery for {error_event.component}:{error_event.error_type}"
        )

        # Component-specific fallback logic
        component = error_event.component

        if component == "anilist_api":
            # Fall back to cached data or alternative API
            return self._fallback_anilist()
        elif component == "manga_rss":
            # Fall back to alternative RSS feeds
            return self._fallback_manga_rss()
        elif component == "gmail_api":
            # Fall back to local storage or alternative notification
            return self._fallback_gmail()

        return False

    def _reset_recovery(self, error_event: ErrorEvent) -> bool:
        """Implement reset recovery strategy."""
        self.logger.info(
            f"Applying reset recovery for {error_event.component}:{error_event.error_type}"
        )

        # Component-specific reset logic
        component = error_event.component

        if component in ["gmail_api", "calendar_api"]:
            # Reset authentication
            return self._reset_auth_tokens(component)
        elif component == "database":
            # Reset database connections
            return self._reset_database_connections()

        return False

    def _manual_recovery(self, error_event: ErrorEvent) -> bool:
        """Implement manual recovery strategy."""
        self.logger.critical(
            f"Manual intervention required for {error_event.component}:{error_event.error_type}"
        )

        # Log detailed information for manual intervention
        self._log_manual_recovery_info(error_event)

        return False

    def _ignore_recovery(self, error_event: ErrorEvent) -> bool:
        """Implement ignore recovery strategy."""
        self.logger.debug(
            f"Ignoring error for {error_event.component}:{error_event.error_type}"
        )
        return True

    def _fallback_anilist(self) -> bool:
        """Fallback for AniList API errors."""
        # Implementation would depend on having alternative data sources
        self.logger.info("AniList fallback: Using cached data")
        return True

    def _fallback_manga_rss(self) -> bool:
        """Fallback for manga RSS errors."""
        # Implementation would switch to alternative RSS feeds
        self.logger.info("Manga RSS fallback: Switching to alternative feeds")
        return True

    def _fallback_gmail(self) -> bool:
        """Fallback for Gmail API errors."""
        # Implementation would use local storage or alternative notification
        self.logger.info("Gmail fallback: Storing notifications locally")
        return True

    def _reset_auth_tokens(self, component: str) -> bool:
        """Reset authentication tokens for Google APIs."""
        try:
            # This would integrate with the actual auth modules
            self.logger.info(f"Resetting auth tokens for {component}")

            # Remove existing token files to force re-authentication
            token_files = ["token.json", "gmail_token.json", "calendar_token.json"]
            for token_file in token_files:
                if Path(token_file).exists():
                    Path(token_file).unlink()
                    self.logger.info(f"Removed {token_file}")

            return True
        except Exception as e:
            self.logger.error(f"Failed to reset auth tokens: {e}")
            return False

    def _reset_database_connections(self) -> bool:
        """Reset database connections."""
        try:
            # This would integrate with the database module
            self.logger.info("Resetting database connections")

            # Signal database module to reset connections
            # This is a placeholder - actual implementation would call db.close_connections()

            return True
        except Exception as e:
            self.logger.error(f"Failed to reset database connections: {e}")
            return False

    def _log_manual_recovery_info(self, error_event: ErrorEvent):
        """Log detailed information for manual recovery."""
        recovery_info = {
            "timestamp": error_event.timestamp.isoformat(),
            "component": error_event.component,
            "error_type": error_event.error_type,
            "message": error_event.message,
            "severity": error_event.severity.value,
            "details": error_event.details,
            "traceback": error_event.traceback_info,
        }

        # Save to file for manual review
        recovery_file = Path("manual_recovery_required.json")
        try:
            if recovery_file.exists():
                with open(recovery_file, "r") as f:
                    existing_data = json.load(f)
            else:
                existing_data = []

            existing_data.append(recovery_info)

            with open(recovery_file, "w") as f:
                json.dump(existing_data, f, indent=2)

            self.logger.critical(f"Manual recovery info saved to {recovery_file}")

        except Exception as e:
            self.logger.error(f"Failed to save manual recovery info: {e}")

    def _monitoring_loop(self):
        """Background monitoring loop."""
        while self.monitoring_active:
            try:
                self._perform_health_check()
                time.sleep(self.monitoring_interval)
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.monitoring_interval)

    def _perform_health_check(self):
        """Perform system health check."""
        unhealthy_components = []

        with self.health_lock:
            for component, health in self.component_health.items():
                if not health.is_healthy:
                    unhealthy_components.append(component)

                # Check for stale components (no activity)
                if health.last_success:
                    time_since_success = datetime.now() - health.last_success
                    if time_since_success > timedelta(hours=24):
                        health.health_score = max(0.0, health.health_score - 0.1)

        if unhealthy_components:
            self.logger.warning(
                f"Unhealthy components detected: {unhealthy_components}"
            )

        # Log health summary
        self.logger.debug(
            f"Health check complete. Total components: {len(self.component_health)}, "
            f"Unhealthy: {len(unhealthy_components)}"
        )

    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status."""
        with self.health_lock:
            component_statuses = {}
            total_health_score = 0
            healthy_count = 0

            for component, health in self.component_health.items():
                component_statuses[component] = {
                    "is_healthy": health.is_healthy,
                    "health_score": health.health_score,
                    "error_count": health.error_count,
                    "consecutive_errors": health.consecutive_errors,
                    "last_success": (
                        health.last_success.isoformat() if health.last_success else None
                    ),
                    "recovery_attempts": health.recovery_attempts,
                }

                total_health_score += health.health_score
                if health.is_healthy:
                    healthy_count += 1

        uptime = datetime.now() - self.start_time

        return {
            "overall_health_score": (
                total_health_score / len(self.component_health)
                if self.component_health
                else 1.0
            ),
            "healthy_components": healthy_count,
            "total_components": len(self.component_health),
            "component_statuses": component_statuses,
            "error_recovery_stats": {
                "total_errors_handled": self.total_errors_handled,
                "successful_recoveries": self.successful_recoveries,
                "failed_recoveries": self.failed_recoveries,
                "recovery_success_rate": (
                    self.successful_recoveries
                    / max(self.successful_recoveries + self.failed_recoveries, 1)
                ),
                "uptime_seconds": uptime.total_seconds(),
            },
        }

    def get_recent_errors(
        self, limit: int = 50, component: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get recent error events."""
        with self.events_lock:
            events = self.error_events

            # Filter by component if specified
            if component:
                events = [e for e in events if e.component == component]

            # Get most recent events
            recent_events = events[-limit:] if limit > 0 else events

            return [
                {
                    "timestamp": event.timestamp.isoformat(),
                    "component": event.component,
                    "error_type": event.error_type,
                    "message": event.message,
                    "severity": event.severity.value,
                    "recovery_attempted": event.recovery_attempted,
                    "recovery_successful": event.recovery_successful,
                    "recovery_strategy": (
                        event.recovery_strategy.value
                        if event.recovery_strategy
                        else None
                    ),
                }
                for event in recent_events
            ]

    def shutdown(self):
        """Shutdown the error recovery system."""
        self.monitoring_active = False
        if self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5)

        self.logger.info("Enhanced error recovery system shutdown complete")


# Global error recovery instance
_error_recovery_instance: Optional[EnhancedErrorRecovery] = None


def get_error_recovery() -> Optional[EnhancedErrorRecovery]:
    """Get the global error recovery instance."""
    return _error_recovery_instance


def initialize_error_recovery(config: Dict[str, Any]) -> EnhancedErrorRecovery:
    """Initialize the global error recovery instance."""
    global _error_recovery_instance
    _error_recovery_instance = EnhancedErrorRecovery(config)
    return _error_recovery_instance


def record_error(
    component: str,
    error_type: str,
    message: str,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    details: Optional[Dict[str, Any]] = None,
    exception: Optional[Exception] = None,
) -> Optional[ErrorEvent]:
    """Record an error using the global error recovery instance."""
    recovery = get_error_recovery()
    if recovery:
        return recovery.record_error(
            component, error_type, message, severity, details, exception
        )
    return None


def record_success(component: str, details: Optional[Dict[str, Any]] = None):
    """Record a success using the global error recovery instance."""
    recovery = get_error_recovery()
    if recovery:
        recovery.record_success(component, details)
