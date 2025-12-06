"""
Flask Blueprint routes for the web application.

This package contains modular route definitions organized by functionality:
- pages: Main page routes (dashboard, releases, calendar, etc.)
- api_releases: Release information API endpoints
- api_collection: Data collection management API
- api_sources: Data source management API
- api_calendar: Calendar sync and events API
- api_notification: Notification and testing API
- api_settings: Settings management API
"""

from flask import Blueprint

# Note: Blueprints are defined in their respective modules
# and registered in web_app.py

__all__ = []
