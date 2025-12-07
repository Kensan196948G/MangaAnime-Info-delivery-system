"""
Configuration utility functions for the Flask web application.
"""

import json
from pathlib import Path
from typing import Dict, Any

# Default config path
CONFIG_PATH = "config.json"


def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    Load configuration from config.json.

    Args:
        config_path: Optional path to config file

    Returns:
        Configuration dictionary
    """
    path = config_path or CONFIG_PATH
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # Return default config if file doesn't exist
        return {
            "ng_keywords": ["エロ", "R18", "成人向け", "BL", "百合", "ボーイズラブ"],
            "ng_genres": [],
            "exclude_tags": [],
            "notify_new_season": True,
            "notify_new_episode": True,
            "notify_new_volume": True,
        }
    except json.JSONDecodeError:
        return {}


def save_config(config: Dict[str, Any], config_path: str = None) -> bool:
    """
    Save configuration to config.json.

    Args:
        config: Configuration dictionary to save
        config_path: Optional path to config file

    Returns:
        True if saved successfully
    """
    path = config_path or CONFIG_PATH
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False
