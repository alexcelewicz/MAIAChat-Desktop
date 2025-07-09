#!/usr/bin/env python3
"""
MAIAChat Desktop - Setup Configuration
Python package setup for MAIAChat Desktop application.
Created by Aleksander Celewicz
"""

from setuptools import setup, find_packages
import os
from pathlib import Path

# Import version information
try:
    from version import (
        __version__, APP_NAME, APP_DESCRIPTION, APP_AUTHOR, 
        APP_COMPANY, APP_LICENSE
    )
except ImportError:
    # Fallback values if version.py is not available
    __version__ = "1.0.0"
    APP_NAME = "MAIAChat"
    APP_DESCRIPTION = "Multi-Agent AI Assistant Desktop Application"
    APP_AUTHOR = "Aleksander Celewicz"
    APP_COMPANY = "MAIAChat.com"
    APP_LICENSE = "MIT"

# Read README for long description
def read_readme():
    """Read README.md for long description."""
    readme_path = Path(__file__).parent / "README.md"
    if readme_path.exists():
        with open(readme_path, "r", encoding="utf-8") as f:
            return f.read()
    return APP_DESCRIPTION

# Read requirements from requirements.txt
def read_requirements():
    """Read requirements from requirements.txt."""
    requirements_path = Path(__file__).parent / "requirements.txt"
    if requirements_path.exists():
        with open(requirements_path, "r", encoding="utf-8") as f:
            return [
                line.strip() 
                for line in f 
                if line.strip() and not line.startswith("#")
            ]
    return []

# Package configuration
setup(
    name="maiachat-desktop",
    version=__version__,
    author=APP_AUTHOR,
    author_email="contact@maiachat.com",
    description=APP_DESCRIPTION,
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/AleksanderCelewicz/MAIAChat-Desktop",
    project_urls={
        "Homepage": "https://maiachat.com",
        "Documentation": "https://github.com/AleksanderCelewicz/MAIAChat-Desktop/blob/main/README.md",
        "Source": "https://github.com/AleksanderCelewicz/MAIAChat-Desktop",
        "Tracker": "https://github.com/AleksanderCelewicz/MAIAChat-Desktop/issues",
        "YouTube": "https://www.youtube.com/@AIexTheAIWorkbench",
        "Tutorials": "https://www.youtube.com/@AIexTheAIWorkbench",
    },
    packages=find_packages(exclude=["tests*", "Test Files*", "build*", "dist*"]),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Communications :: Chat",
        "Topic :: Desktop Environment",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Environment :: X11 Applications :: Qt",
        "Natural Language :: English",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-qt>=4.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
        ],
        "build": [
            "pyinstaller>=5.0.0",
            "pyinstaller-hooks-contrib",
        ],
        "gpu": [
            "faiss-gpu>=1.7.4",
            "torch[cuda]>=2.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "maiachat=start_app:main",
            "maiachat-desktop=start_app:main",
        ],
        "gui_scripts": [
            "maiachat-gui=start_app:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": [
            "*.json",
            "*.txt",
            "*.md",
            "icons/*",
            "images/*",
            "ui/*.py",
            "handlers/*.py",
            "managers/*.py",
            "rag_components/*.py",
            "core/*.py",
            "api/*.py",
            "utils/*.py",
            "example_profiles/*.json",
            "model_settings/*/*.json",
        ],
    },
    exclude_package_data={
        "": [
            "config.json",
            "api_keys.json",
            ".env",
            "mcp_config/servers.json",
            "mcp_config/folder_permissions.json",
            "token_usage_history.json",
            "conversation_history/*",
            "knowledge_base/*",
            "*.log",
            "*.pyc",
            "__pycache__/*",
            ".git/*",
            ".gitignore",
            "build/*",
            "dist/*",
        ],
    },
    keywords=[
        "ai", "artificial-intelligence", "chatbot", "desktop-application", 
        "multi-agent", "conversation", "rag", "knowledge-base", "pyqt6",
        "openai", "anthropic", "google", "llm", "nlp", "assistant"
    ],
    license=APP_LICENSE,
    platforms=["Windows", "macOS", "Linux"],
    zip_safe=False,
)
