#!/usr/bin/env python3
"""
Complete project setup script for Telegram News Detector.
This script creates the entire project structure with all necessary files.
"""

import os
import shutil
from pathlib import Path


def create_file(filepath, content):
    """Create file with content."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')
    
    print(f"📄 Created: {filepath}")


def copy_from_original(original_path, target_path):
    """Copy file from original project if it exists."""
    if os.path.exists(original_path):
        shutil.copy2(original_path, target_path)
        print(f"📋 Copied: {original_path} -> {target_path}")
        return True
    return False


def main():
    """Create complete project structure."""
    print("🚀 Creating Complete News Detector Project")
    print("=" * 60)
    
    # Ask for original project path (optional)
    original_project = input("Enter path to original project (optional, press Enter to skip): ").strip()
    if original_project and not os.path.exists(original_project):
        print(f"⚠️  Original project path not found: {original_project}")
        original_project = None
    
    print("\n📁 Creating directory structure...")
    
    # Create all __init__.py files first
    init_files = {
        "src/__init__.py": '''"""
Telegram News Detector - Core Package
"""

__version__ = "1.0.0"
__author__ = "News Detector Team"
__description__ = "Standalone Telegram news detection system for war/geopolitical content"
''',
        
        "config/__init__.py": '''"""
Configuration package for the News Detector.
"""

from .credentials import (
    API_ID, 
    API_HASH, 
    PHONE_NUMBER, 
    ADMIN_BOT_TOKEN, 
    ADMIN_BOT_USERNAME,
    validate_credentials
)

from .settings import (
    TARGET_CHANNEL_ID,
    NEW_ATTRIBUTION,
    WAR_NEWS_ONLY,
    ISRAEL_IRAN_FOCUS,
    GEOPOLITICAL_ONLY,
    NEWS_CHECK_INTERVAL,
    NEWS_CHANNEL,
    TWITTER_NEWS_CHANNEL,
    ADMIN_APPROVAL_TIMEOUT,
    OPERATION_START_HOUR,
    OPERATION_END_HOUR,
    FORCE_24_HOUR_OPERATION
)

__all__ = [
    'API_ID', 'API_HASH', 'PHONE_NUMBER', 'ADMIN_BOT_TOKEN', 'ADMIN_BOT_USERNAME',
    'validate_credentials', 'TARGET_CHANNEL_ID', 'NEW_ATTRIBUTION', 'WAR_NEWS_ONLY',
    'ISRAEL_IRAN_FOCUS', 'GEOPOLITICAL_ONLY', 'NEWS_CHECK_INTERVAL', 'NEWS_CHANNEL',
    'TWITTER_NEWS_CHANNEL', 'ADMIN_APPROVAL_TIMEOUT', 'OPERATION_START_HOUR',
    'OPERATION_END_HOUR', 'FORCE_24_HOUR_OPERATION'
]
''',
        
        "src/client/__init__.py": '''"""
Telegram client package for the News Detector.
"""

from .telegram_client import TelegramClientManager
from .bot_api import BotAPIClient

__all__ = ['TelegramClientManager', 'BotAPIClient']
''',
        
        "src/services/__init__.py": '''"""
Core services package for news detection and filtering.
"""

from .news_detector import NewsDetector
from .news_filter import NewsFilter
from .state_manager import StateManager

__all__ = ['NewsDetector', 'NewsFilter', 'StateManager']
''',
        
        "src/handlers/__init__.py": '''"""
Message and event handlers package.
"""

from .news_handler import NewsHandler

__all__ = ['NewsHandler']
''',
        
        "src/utils/__init__.py": '''"""
Utility functions and helpers package.
"""

from .logger import setup_logging
from .time_utils import (
    get_current_time,
    is_operating_hours,
    get_formatted_time,
    timestamp_to_tehran
)

__all__ = [
    'setup_logging', 
    'get_current_time', 
    'is_operating_hours', 
    'get_formatted_time', 
    'timestamp_to_tehran'
]
''',
        
        "tests/__init__.py": '''"""
Test suite for the Telegram News Detector.
"""
'''
    }
    
    # Create all __init__.py files
    for filepath, content in init_files.items():
        create_file(filepath, content)
    
    # Create placeholder files for empty directories
    placeholder_files = {
        "data/state/.gitkeep": "# Telegram session files and state data",
        "logs/.gitkeep": "# Application log files", 
        "scripts/.gitkeep": "# Utility and maintenance scripts",
        "systemd/.gitkeep": "# System service configuration files"
    }
    
    for filepath, content in placeholder_files.items():
        create_file(filepath, content)
    
    # Create requirements.txt
    requirements_content = '''telethon>=1.31.1
python-dotenv>=1.0.0
requests>=2.31.0
pytz>=2023.3

# Development dependencies (optional)
pytest>=7.4.0
pytest-asyncio>=0.21.0
black>=23.7.0
flake8>=6.0.0
'''
    
    create_file("requirements.txt", requirements_content)
    
    # Create .env.example
    env_example_content = '''# Telegram News Detector - Environment Configuration Template
# Copy this file to .env and fill in your actual values

# TELEGRAM API CREDENTIALS
TELEGRAM_API_ID=your_api_id_here
TELEGRAM_API_HASH="your_api_hash_here"
TELEGRAM_PHONE="+your_phone_number"

# ADMIN BOT FOR NEWS APPROVAL
ADMIN_BOT_TOKEN="your_admin_bot_token"
ADMIN_BOT_USERNAME=your_admin_bot_username

# TARGET CHANNEL FOR APPROVED NEWS
TARGET_CHANNEL_ID=-your_target_channel_id
NEW_ATTRIBUTION=@your_news_attribution

# OPERATING HOURS - 9 AM TO 10 PM TEHRAN TIME
OPERATION_START_HOUR=9
OPERATION_END_HOUR=22
FORCE_24_HOUR_OPERATION=false

# ADMIN APPROVAL SYSTEM
ENABLE_ADMIN_APPROVAL=true
REQUIRE_ADMIN_APPROVAL=true
ADMIN_APPROVAL_TIMEOUT=3600

# WAR NEWS FOCUS SETTINGS
WAR_NEWS_ONLY=true
ISRAEL_IRAN_FOCUS=true
GEOPOLITICAL_ONLY=true
ECONOMIC_WAR_IMPACT=true

# NEWS MONITORING SETTINGS
NEWS_CHECK_INTERVAL=1800
NEWS_CHANNEL=your_primary_news_channel
TWITTER_NEWS_CHANNEL=your_twitter_news_channel
'''
    
    create_file(".env.example", env_example_content)
    
    # Create .gitignore
    gitignore_content = '''# Environment and credentials
.env
*.env

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
venv/
env/
ENV/

# Application data
data/
logs/
*.log
*.session
*.session-journal

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Temporary files
tmp/
temp/
*.tmp
'''
    
    create_file(".gitignore", gitignore_content)
    
    # Create README.md stub
    readme_content = '''# Telegram News Detector

A standalone news detection system focused on war, geopolitical, and economic warfare content.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. **Validate configuration:**
   ```bash
   python scripts/validate_config.py
   ```

4. **Run the detector:**
   ```bash
   python main.py
   ```

## Features

- 🔍 Smart news detection for war/geopolitical content
- 👨‍💼 Admin approval workflow via Telegram bot
- ⏰ Configurable operating hours (Tehran timezone)
- 📊 Comprehensive monitoring and logging
- 🧪 Full test suite included

For complete documentation, see the detailed README in the project artifacts.
'''
    
    create_file("README.md", readme_content)
    
    # Try to copy .env from original project
    if original_project:
        print(f"\n📋 Attempting to copy configuration from: {original_project}")
        original_env = os.path.join(original_project, ".env")
        if copy_from_original(original_env, ".env"):
            print("✅ Configuration copied from original project")
        else:
            print("⚠️  No .env file found in original project")
            print("💡 Use .env.example as template")
    else:
        print("\n💡 No original project specified")
        print("📝 Copy .env.example to .env and configure your settings")
    
    # Create a simple Makefile
    makefile_content = '''.PHONY: help install test run clean

help:
	@echo "Available commands:"
	@echo "  install  - Install dependencies"
	@echo "  test     - Run test suite"
	@echo "  run      - Start the news detector"
	@echo "  clean    - Clean temporary files"

install:
	pip install -r requirements.txt

test:
	python scripts/run_tests.py

run:
	python main.py

clean:
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +
'''
    
    create_file("Makefile", makefile_content)
    
    print("\n✅ Project structure created successfully!")
    print("\n📦 Created project structure:")
    print("├── 📄 .env.example")
    print("├── 📄 .gitignore") 
    print("├── 📄 requirements.txt")
    print("├── 📄 README.md")
    print("├── 📄 Makefile")
    print("├── 📁 config/")
    print("│   └── 📄 __init__.py")
    print("├── 📁 src/")
    print("│   ├── 📄 __init__.py")
    print("│   ├── 📁 client/")
    print("│   │   └── 📄 __init__.py")
    print("│   ├── 📁 services/")
    print("│   │   └── 📄 __init__.py")
    print("│   ├── 📁 handlers/")
    print("│   │   └── 📄 __init__.py")
    print("│   └── 📁 utils/")
    print("│       └── 📄 __init__.py")
    print("├── 📁 tests/")
    print("│   └── 📄 __init__.py")
    print("├── 📁 scripts/")
    print("├── 📁 data/")
    print("│   └── 📁 state/")
    print("├── 📁 logs/")
    print("└── 📁 systemd/")
    
    print("\n🎯 Next steps:")
    print("1. Copy the main source files from the artifacts to their directories:")
    print("   - main.py (root)")
    print("   - config/credentials.py & config/settings.py")
    print("   - src/client/telegram_client.py & src/client/bot_api.py") 
    print("   - src/services/*.py")
    print("   - src/handlers/news_handler.py")
    print("   - src/utils/*.py")
    print("   - scripts/*.py")
    print("   - tests/*.py")
    
    if not os.path.exists(".env"):
        print("\n2. Configure your environment:")
        print("   cp .env.example .env")
        print("   # Edit .env with your Telegram credentials")
    
    print("\n3. Install dependencies:")
    print("   pip install -r requirements.txt")
    
    print("\n4. Validate setup:")
    print("   python scripts/validate_config.py")
    
    print("\n5. Run the news detector:")
    print("   python main.py")
    
    print(f"\n🎉 Project setup complete in: {os.getcwd()}")


if __name__ == "__main__":
    main()