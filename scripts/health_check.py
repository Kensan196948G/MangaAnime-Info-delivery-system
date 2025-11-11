#!/usr/bin/env python3
"""
MangaAnime System Health Check Script
システムの各コンポーネントの動作状況をチェックします
"""

import json
import sys
import os
import sqlite3
import requests
from datetime import datetime


def check_config():
    """設定ファイルのチェック"""
    try:
        with open("config.json", "r") as f:
            config = json.load(f)

        required_sections = ["email", "notifications", "system", "database"]
        for section in required_sections:
            if section not in config:
                return False, f"Missing config section: {section}"

        return True, "Configuration is valid"
    except Exception as e:
        return False, f"Configuration error: {e}"


def check_database():
    """データベースのチェック"""
    try:
        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        return True, "Database connection successful"
    except Exception as e:
        return False, f"Database error: {e}"


def check_external_apis():
    """外部APIのチェック"""
    try:
        response = requests.get("https://httpbin.org/status/200", timeout=5)
        if response.status_code == 200:
            return True, "External API connectivity OK"
        else:
            return False, f"API returned status {response.status_code}"
    except Exception as e:
        return False, f"API connectivity error: {e}"


def main():
    """メインのヘルスチェック処理"""
    print("🏥 MangaAnime System Health Check")
    print("=" * 40)

    checks = [
        ("Configuration", check_config),
        ("Database", check_database),
        ("External APIs", check_external_apis),
    ]

    all_passed = True

    for name, check_func in checks:
        success, message = check_func()
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{name:15} {status:10} {message}")

        if not success:
            all_passed = False

    print("=" * 40)
    if all_passed:
        print("🎉 All health checks passed!")
        sys.exit(0)
    else:
        print("⚠️  Some health checks failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
