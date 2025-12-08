"""
Jinja2 template filters for the Flask web application.
"""

import os
import time
from datetime import date, datetime

from flask import Flask


def register_filters(app: Flask):
    """
    Register all custom Jinja2 filters with the Flask app.

    Args:
        app: Flask application instance
    """

    @app.template_filter("file_mtime")
    def file_mtime_filter(filepath):
        """Get file modification time as timestamp for cache busting"""
        try:
            static_path = os.path.join(app.static_folder, filepath)
            return int(os.path.getmtime(static_path))
        except Exception:
            return int(time.time())

    @app.template_filter("strptime")
    def strptime_filter(date_string, format="%Y-%m-%d"):
        """文字列を日付オブジェクトに変換するフィルター"""
        try:
            return datetime.strptime(date_string, format)
        except (ValueError, TypeError):
            return None

    @app.template_filter("datetime_format")
    def datetime_format_filter(value, format="%Y-%m-%d"):
        """日付/日時を指定フォーマットで文字列化するフィルター"""
        if value is None:
            return "-"
        try:
            if isinstance(value, str):
                # 文字列の場合、まずパースを試みる
                for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d"]:
                    try:
                        value = datetime.strptime(value, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    return value  # パース失敗時は元の文字列を返す
            if isinstance(value, (datetime, date)):
                return value.strftime(format)
            return str(value)
        except (ValueError, TypeError):
            return str(value) if value else "-"

    @app.template_filter("work_type_label")
    def work_type_label_filter(value):
        """作品タイプを日本語ラベルに変換するフィルター"""
        labels = {
            "anime": "アニメ",
            "manga": "マンガ",
            "novel": "小説",
            "movie": "映画",
            "ova": "OVA",
            "special": "スペシャル",
        }
        return labels.get(value, value if value else "-")

    @app.template_filter("release_type_label")
    def release_type_label_filter(value):
        """リリースタイプを日本語ラベルに変換するフィルター"""
        labels = {"episode": "話", "volume": "巻", "chapter": "章", "season": "期"}
        return labels.get(value, value if value else "")
