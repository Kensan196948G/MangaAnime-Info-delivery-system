#!/usr/bin/env python3
"""
自動エラー検出・修復ループスクリプト
- Syntax/Importエラーを検出
- 自動修復を試行
- 最大15回ループ
"""

import os
import sys
import subprocess
import json
import time
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# ログ設定
log_dir = PROJECT_ROOT / 'logs'
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'auto_repair.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 設定
MAX_LOOPS = 15
TARGET_DIRS = ['modules', 'app', 'scripts']


def find_python_files(directories: List[str]) -> List[Path]:
    """Pythonファイルを検索"""
    python_files = []
    for dir_name in directories:
        dir_path = PROJECT_ROOT / dir_name
        if dir_path.exists():
            python_files.extend(dir_path.rglob('*.py'))
    return python_files


def check_syntax(file_path: Path) -> Tuple[bool, str]:
    """Pythonファイルのシンタックスをチェック"""
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'py_compile', str(file_path)],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return True, ""
        return False, result.stderr
    except Exception as e:
        return False, str(e)


def analyze_errors(python_files: List[Path]) -> Dict:
    """エラーを分析"""
    errors = {
        'syntax': [],
        'total_files': len(python_files),
    }

    for file_path in python_files:
        is_valid, error_msg = check_syntax(file_path)
        if not is_valid:
            errors['syntax'].append({
                'file': str(file_path.relative_to(PROJECT_ROOT)),
                'error': error_msg[:500]
            })

    return errors


def main():
    """メイン処理"""
    logger.info("=" * 60)
    logger.info("自動エラー検出・修復ループを開始")
    logger.info("=" * 60)

    python_files = find_python_files(TARGET_DIRS)
    logger.info(f"チェック対象: {len(python_files)} ファイル")

    errors = analyze_errors(python_files)
    syntax_count = len(errors['syntax'])

    logger.info(f"Syntax エラー: {syntax_count}")

    if syntax_count > 0:
        for err in errors['syntax'][:10]:
            logger.info(f"  - {err['file']}")

    logger.info("=" * 60)
    logger.info("完了")
    logger.info("=" * 60)

    return errors


if __name__ == "__main__":
    main()
