"""
Health check endpoints for the Anime/Manga Information Delivery System.

Provides /health and /ready endpoints for container orchestration and monitoring.
"""

import os
import sqlite3
import time
from datetime import datetime
from flask import Blueprint, jsonify

health_bp = Bluelogger.info('health', __name__)

# Database path
DATABASE_PATH = os.environ.get('DATABASE_PATH', 'db.sqlite3')

# Application start time
APP_START_TIME = datetime.now()


def check_database_connection() -> dict:
    """Check database connectivity and return status."""
    try:
        conn = sqlite3.connect(DATABASE_PATH, timeout=5.0)
        cursor = conn.execute("SELECT 1")
        cursor.fetchone()

        # Get basic stats
        cursor = conn.execute("SELECT COUNT(*) FROM works")
        works_count = cursor.fetchone()[0]

        cursor = conn.execute("SELECT COUNT(*) FROM releases")
        releases_count = cursor.fetchone()[0]

        conn.close()

        return {
            "status": "healthy",
            "works_count": works_count,
            "releases_count": releases_count
        }
    except sqlite3.Error as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
    except Exception as e:
        return {
            "status": "unknown",
            "error": str(e)
        }


def check_config_file() -> dict:
    """Check if configuration file exists and is readable."""
    config_path = os.environ.get('CONFIG_PATH', 'config.json')
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                import json
                config = json.load(f)
            return {
                "status": "healthy",
                "config_loaded": True
            }
        else:
            return {
                "status": "degraded",
                "config_loaded": False,
                "message": "Config file not found, using defaults"
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "config_loaded": False,
            "error": str(e)
        }


def get_uptime() -> dict:
    """Calculate and return application uptime."""
    now = datetime.now()
    uptime = now - APP_START_TIME

    return {
        "started_at": APP_START_TIME.isoformat(),
        "uptime_seconds": int(uptime.total_seconds()),
        "uptime_human": str(uptime).split('.')[0]  # Remove microseconds
    }


@health_bp.route('/health', methods=['GET'])
def health_check():
    """
    Basic health check endpoint.

    Returns 200 if the application is running.
    Used for container liveness probes.
    """
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "manga-anime-info-system"
    }), 200


@health_bp.route('/health/live', methods=['GET'])
def liveness_check():
    """
    Kubernetes liveness probe endpoint.

    Returns 200 if the application process is running.
    """
    return jsonify({
        "status": "alive",
        "timestamp": datetime.now().isoformat()
    }), 200


@health_bp.route('/health/ready', methods=['GET'])
@health_bp.route('/ready', methods=['GET'])
def readiness_check():
    """
    Readiness check endpoint.

    Returns 200 if the application is ready to receive traffic.
    Checks database connectivity and configuration.
    Used for container readiness probes.
    """
    db_status = check_database_connection()
    config_status = check_config_file()
    uptime = get_uptime()

    # Determine overall status
    is_ready = (
        db_status["status"] == "healthy" and
        config_status["status"] in ["healthy", "degraded"]
    )

    response = {
        "status": "ready" if is_ready else "not_ready",
        "timestamp": datetime.now().isoformat(),
        "checks": {
            "database": db_status,
            "config": config_status
        },
        "uptime": uptime
    }

    status_code = 200 if is_ready else 503
    return jsonify(response), status_code


@health_bp.route('/health/detailed', methods=['GET'])
def detailed_health_check():
    """
    Detailed health check with all component status.

    Provides comprehensive system health information.
    """
    db_status = check_database_connection()
    config_status = check_config_file()
    uptime = get_uptime()

    # Check disk space
    try:
        statvfs = os.statvfs('.')
        disk_free_bytes = statvfs.f_frsize * statvfs.f_bavail
        disk_total_bytes = statvfs.f_frsize * statvfs.f_blocks
        disk_used_percent = round((1 - statvfs.f_bavail / statvfs.f_blocks) * 100, 2)

        disk_status = {
            "status": "healthy" if disk_used_percent < 90 else "warning",
            "free_bytes": disk_free_bytes,
            "free_human": f"{disk_free_bytes / (1024**3):.2f} GB",
            "used_percent": disk_used_percent
        }
    except Exception as e:
        disk_status = {
            "status": "unknown",
            "error": str(e)
        }

    # Check memory (basic)
    try:
        import resource
        rusage = resource.getrusage(resource.RUSAGE_SELF)
        memory_status = {
            "status": "healthy",
            "max_rss_kb": rusage.ru_maxrss,
            "max_rss_human": f"{rusage.ru_maxrss / 1024:.2f} MB"
        }
    except Exception:
        memory_status = {"status": "unknown"}

    # Determine overall health
    overall_healthy = (
        db_status["status"] == "healthy" and
        config_status["status"] in ["healthy", "degraded"] and
        disk_status["status"] != "unhealthy"
    )

    response = {
        "status": "healthy" if overall_healthy else "unhealthy",
        "timestamp": datetime.now().isoformat(),
        "version": os.environ.get('APP_VERSION', '1.0.0'),
        "environment": os.environ.get('ENVIRONMENT', 'development'),
        "uptime": uptime,
        "checks": {
            "database": db_status,
            "config": config_status,
            "disk": disk_status,
            "memory": memory_status
        }
    }

    status_code = 200 if overall_healthy else 503
    return jsonify(response), status_code


@health_bp.route('/metrics', methods=['GET'])
def prometheus_metrics():
    """
    Basic Prometheus-compatible metrics endpoint.

logger = logging.getLogger(__name__)


    Returns metrics in Prometheus text format.
    """
    db_status = check_database_connection()
    uptime = get_uptime()

    # Build metrics in Prometheus format
    metrics = []

    # Application info
    metrics.append('# HELP mangaanime_info Application information')
    metrics.append('# TYPE mangaanime_info gauge')
    metrics.append('mangaanime_info{version="1.0.0"} 1')

    # Uptime
    metrics.append('# HELP mangaanime_uptime_seconds Application uptime in seconds')
    metrics.append('# TYPE mangaanime_uptime_seconds gauge')
    metrics.append(f'mangaanime_uptime_seconds {uptime["uptime_seconds"]}')

    # Database health
    metrics.append('# HELP mangaanime_database_healthy Database health status (1=healthy, 0=unhealthy)')
    metrics.append('# TYPE mangaanime_database_healthy gauge')
    db_healthy = 1 if db_status["status"] == "healthy" else 0
    metrics.append(f'mangaanime_database_healthy {db_healthy}')

    # Works count
    if db_status["status"] == "healthy":
        metrics.append('# HELP mangaanime_works_total Total number of works in database')
        metrics.append('# TYPE mangaanime_works_total gauge')
        metrics.append(f'mangaanime_works_total {db_status["works_count"]}')

        metrics.append('# HELP mangaanime_releases_total Total number of releases in database')
        metrics.append('# TYPE mangaanime_releases_total gauge')
        metrics.append(f'mangaanime_releases_total {db_status["releases_count"]}')

    response_text = '\n'.join(metrics) + '\n'

    from flask import Response
import logging
    return Response(response_text, mimetype='text/plain; charset=utf-8')
