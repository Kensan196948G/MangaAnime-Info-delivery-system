#!/usr/bin/env python3
"""
アニメ・マンガ情報配信システム セットアップスクリプト
"""

from setuptools import setup, find_packages

with open("requirements.txt", "r", encoding="utf-8") as f:
    requirements = [
        line.strip() for line in f if line.strip() and not line.startswith("#")
    ]

setup(
    name="manga-anime-info-delivery",
    version="1.0.0",
    description="アニメ・マンガの最新情報を自動収集してGmail通知・Googleカレンダー登録するシステム",
    author="ClaudeCode Development Team",
    author_email="noreply@anthropic.com",
    packages=find_packages(),
    install_requires=requirements,
    python_requires=">=3.11",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Communications :: Email",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content :: News/Diary",
        "Topic :: Multimedia :: Graphics :: Presentation",
    ],
    entry_points={
        "console_scripts": [
            "manga-anime-notifier=release_notifier:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.yaml", "*.json"],
    },
)
