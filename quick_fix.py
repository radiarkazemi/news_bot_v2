#!/usr/bin/env python3
"""
Quick fix script to resolve import errors and create missing files for News Detector.
Run this script to fix the syntax error and missing imports.
"""

import os
from pathlib import Path


def create_file(filepath, content):
    """Create file with content."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')
    
    print(f"✅ Created: {filepath}")


def fix_bot_api():
    """Fix the bot_api.py syntax error."""
    bot_api_content = '''"""
Bot API client for sending messages via Telegram Bot API.
"""
import logging
import time
import requests
from requests.exceptions import RequestException

from config.credentials import ADMIN_BOT_TOKEN
from config.settings import MAX_RETRIES, RETRY_DELAY_BASE

logger = logging.getLogger(__name__)


class BotAPIClient:
    """Client for Telegram Bot API interactions."""

    def __init__(self):
        """Initialize the bot API client."""
        self.base_url = f"https://api.telegram.org/bot{ADMIN_BOT_TOKEN}"

    def send_message(self, chat_id, text, parse_mode='HTML'):
        """Send a message via Bot API."""
        url = f"{self.base_url}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode
        }

        for attempt in range(MAX_RETRIES):
            try:
                response = requests.post(url, json=payload, timeout=15)
                response.raise_for_status()
                result = response.json()

                if result.get('ok'):
                    logger.debug(f"Message sent successfully to {chat_id}")
                    return result
                else:
                    logger.error(f"Bot API error: {result.get('description')}")
                    if result.get('error_code') in [400, 403]:
                        break
                    time.sleep(RETRY_DELAY_BASE ** attempt)
                    
            except Exception as e:
                logger.error(f"Error sending message (attempt {attempt + 1}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY_BASE ** attempt)

        logger.error(f"Failed to send message after {MAX_RETRIES} attempts")
        return None
'''
    
    create_file("src/client/bot_api.py", bot_api_content)


def create_missing_logger():
    """Create the logger utility."""
    logger_content = '''"""
Logging setup for the News Detector.
"""
import logging
import logging.handlers
from pathlib import Path

try:
    from config.settings import LOG_LEVEL, LOG_FILE_PATH, MAX_LOG_SIZE_MB, LOG_BACKUP_COUNT
except ImportError:
    # Fallback values if settings not available
    LOG_LEVEL = "INFO"
    LOG_FILE_PATH = "./logs/news_detector.log"
    MAX_LOG_SIZE_MB = 50
    LOG_BACKUP_COUNT = 5


def setup_logging():
    """Set up logging configuration."""
    # Create logs directory
    log_file = Path(LOG_FILE_PATH)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=MAX_LOG_SIZE_MB * 1024 * 1024,
            backupCount=LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not set up file logging: {e}")
    
    return logger
'''
    
    create_file("src/utils/logger.py", logger_content)


def create_time_utils():
    """Create time utilities."""
    time_utils_content = '''"""
Time utilities for operating hours and timezone handling.
"""
import pytz
from datetime import datetime

try:
    from config.settings import TEHRAN_TZ, OPERATION_START_HOUR, OPERATION_END_HOUR
except ImportError:
    # Fallback values
    TEHRAN_TZ = pytz.timezone('Asia/Tehran')
    OPERATION_START_HOUR = 9
    OPERATION_END_HOUR = 22


def get_current_time():
    """Get current time in Tehran timezone."""
    return datetime.now(TEHRAN_TZ)


def is_operating_hours():
    """Check if current time is within operating hours."""
    current_time = get_current_time()
    current_hour = current_time.hour
    
    return OPERATION_START_HOUR <= current_hour <= OPERATION_END_HOUR


def get_formatted_time(dt=None):
    """Get formatted time string."""
    if dt is None:
        dt = get_current_time()
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def timestamp_to_tehran(timestamp):
    """Convert timestamp to Tehran timezone."""
    utc_dt = datetime.fromtimestamp(timestamp, tz=pytz.UTC)
    return utc_dt.astimezone(TEHRAN_TZ)
'''
    
    create_file("src/utils/time_utils.py", time_utils_content)


def create_state_manager():
    """Create state manager."""
    state_manager_content = '''"""
State management for persisting application state.
"""
import json
import logging
from pathlib import Path

try:
    from config.settings import STATE_FILE_PATH
except ImportError:
    STATE_FILE_PATH = "./data/state/news_detector_state.json"

logger = logging.getLogger(__name__)


class StateManager:
    """Manages application state persistence."""

    def __init__(self):
        """Initialize state manager."""
        self.state_file = Path(STATE_FILE_PATH)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

    def save_state(self, state_data):
        """Save state data to file."""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, ensure_ascii=False, indent=2)
            logger.debug("State saved successfully")
        except Exception as e:
            logger.error(f"Error saving state: {e}")

    def load_state(self):
        """Load state data from file."""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading state: {e}")
            return {}

    def get_state_value(self, key, default=None):
        """Get a specific value from state."""
        state = self.load_state()
        return state.get(key, default)

    def set_state_value(self, key, value):
        """Set a specific value in state."""
        state = self.load_state()
        state[key] = value
        self.save_state(state)
'''
    
    create_file("src/services/state_manager.py", state_manager_content)


def create_minimal_telegram_client():
    """Create minimal telegram client."""
    telegram_client_content = '''"""
Telegram client manager for the News Detector.
"""
import asyncio
import logging
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, AuthKeyError

from config.credentials import API_ID, API_HASH, PHONE_NUMBER
from config.settings import SESSION_FILE, MAX_RETRIES, RETRY_DELAY_BASE

logger = logging.getLogger(__name__)


class TelegramClientManager:
    """Manages Telegram client connection and interactions."""

    def __init__(self):
        """Initialize the client manager."""
        self.client = None
        self.is_running = False

    async def start(self):
        """Start the Telegram client."""
        if self.client and self.client.is_connected():
            logger.warning("Client already connected")
            return True

        # Create session directory
        SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize client
        self.client = TelegramClient(str(SESSION_FILE), API_ID, API_HASH)

        try:
            logger.info("Starting Telegram client...")
            
            retries = 0
            while retries < MAX_RETRIES:
                try:
                    await self.client.start(phone=PHONE_NUMBER)
                    break
                except (ConnectionError, AuthKeyError) as e:
                    retries += 1
                    if retries >= MAX_RETRIES:
                        raise
                    logger.warning(f"Connection error (attempt {retries}): {e}")
                    await asyncio.sleep(RETRY_DELAY_BASE ** retries)

            if not self.client.is_connected():
                logger.error("Failed to connect client")
                return False

            self.is_running = True
            logger.info("Telegram client connected successfully")
            return True

        except SessionPasswordNeededError:
            logger.error("Two-factor authentication enabled. Please disable or implement 2FA handling.")
            return False
        except Exception as e:
            logger.error(f"Failed to start client: {e}")
            return False

    async def stop(self):
        """Stop the Telegram client."""
        self.is_running = False
        
        if self.client and self.client.is_connected():
            logger.info("Disconnecting Telegram client...")
            await self.client.disconnect()
            logger.info("Client disconnected")
'''
    
    create_file("src/client/telegram_client.py", telegram_client_content)


def create_minimal_news_handler():
    """Create minimal news handler to avoid import errors."""
    news_handler_content = '''"""
Minimal news handler to avoid import errors.
This is a basic implementation - replace with full version later.
"""
import logging
import asyncio
import json
import time
from pathlib import Path

logger = logging.getLogger(__name__)


class NewsHandler:
    """Basic news handler to avoid import errors."""

    def __init__(self, client_manager):
        """Initialize the news handler."""
        self.client_manager = client_manager
        self.pending_news = {}
        
        # Import services with fallback
        try:
            from src.services.news_detector import NewsDetector
            from src.services.news_filter import NewsFilter
            from src.services.state_manager import StateManager
            
            self.news_detector = NewsDetector()
            self.state_manager = StateManager()
        except ImportError as e:
            logger.warning(f"Could not import all services: {e}")
            self.news_detector = None
            self.state_manager = None

    async def setup_approval_handler(self):
        """Set up approval handler (placeholder)."""
        logger.info("News approval handler setup (placeholder)")
        return True

    async def load_pending_news(self):
        """Load pending news (placeholder)."""
        logger.info("Loading pending news (placeholder)")
        if self.state_manager:
            try:
                state = self.state_manager.load_state()
                self.pending_news = state.get('pending_news', {})
            except:
                self.pending_news = {}

    async def save_pending_news(self):
        """Save pending news (placeholder)."""
        if self.state_manager:
            try:
                self.state_manager.save_state({'pending_news': self.pending_news})
            except Exception as e:
                logger.error(f"Error saving pending news: {e}")

    async def process_news_messages(self, channel_username):
        """Process news messages (placeholder)."""
        logger.info(f"Processing news from {channel_username} (placeholder)")
        return False

    async def check_approval_timeouts(self):
        """Check approval timeouts (placeholder)."""
        pass
'''
    
    create_file("src/handlers/news_handler.py", news_handler_content)


def create_basic_news_detector():
    """Create basic news detector to avoid import errors."""
    news_detector_content = '''"""
Basic news detector to avoid import errors.
"""
import logging
import re

logger = logging.getLogger(__name__)


class NewsDetector:
    """Basic news detector."""
    
    FINANCIAL_NEWS_KEYWORDS = [
        "جنگ", "حمله", "موشک", "اسرائیل", "ایران", "تحریم", "دلار", "طلا",
        "war", "attack", "missile", "israel", "iran", "sanctions", "nuclear"
    ]
    
    NON_NEWS_KEYWORDS = [
        "تبلیغ", "فروش", "رستوران", "ورزش", "موسیقی",
        "advertisement", "sale", "restaurant", "sports", "music"
    ]

    @classmethod
    def is_news(cls, text):
        """Basic news detection."""
        if not text or len(text.strip()) < 20:
            return False
        
        text_lower = text.lower()
        
        # Count relevant keywords
        relevant_count = sum(1 for kw in cls.FINANCIAL_NEWS_KEYWORDS if kw in text_lower)
        non_news_count = sum(1 for kw in cls.NON_NEWS_KEYWORDS if kw in text_lower)
        
        return relevant_count >= 1 and non_news_count == 0

    @classmethod
    def clean_news_text(cls, text):
        """Basic text cleaning."""
        if not text:
            return ""
        
        # Basic cleaning
        cleaned = text.strip()
        cleaned = re.sub(r'@\\w+', '', cleaned)  # Remove handles
        cleaned = re.sub(r'https?://\\S+', '', cleaned)  # Remove URLs
        
        return cleaned


class NewsFilter:
    """Basic news filter."""
    
    @classmethod
    def is_relevant_news(cls, text):
        """Basic relevance check."""
        if not text:
            return False, 0, []
        
        # Basic war/geopolitical keywords
        war_keywords = ["جنگ", "حمله", "اسرائیل", "ایران", "تحریم", "war", "israel", "iran"]
        
        text_lower = text.lower()
        matches = [kw for kw in war_keywords if kw in text_lower]
        
        relevance_score = len(matches)
        is_relevant = relevance_score >= 1
        
        return is_relevant, relevance_score, matches
'''
    
    create_file("src/services/news_detector.py", news_detector_content)


def create_minimal_credentials():
    """Create minimal credentials file."""
    credentials_content = '''"""
Credentials management for the News Detector.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Telegram API credentials
API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "")
PHONE_NUMBER = os.getenv("TELEGRAM_PHONE", "")

# Admin bot credentials
ADMIN_BOT_TOKEN = os.getenv("ADMIN_BOT_TOKEN", "")
ADMIN_BOT_USERNAME = os.getenv("ADMIN_BOT_USERNAME", "")

def validate_credentials():
    """Validate that all required credentials are available."""
    missing = []

    if API_ID == 0:
        missing.append("TELEGRAM_API_ID")
    if not API_HASH:
        missing.append("TELEGRAM_API_HASH")
    if not PHONE_NUMBER:
        missing.append("TELEGRAM_PHONE")
    if not ADMIN_BOT_TOKEN:
        missing.append("ADMIN_BOT_TOKEN")
    if not ADMIN_BOT_USERNAME:
        missing.append("ADMIN_BOT_USERNAME")

    if missing:
        raise ValueError(f"Missing required credentials: {', '.join(missing)}")
'''
    
    create_file("config/credentials.py", credentials_content)


def main():
    """Main fix function."""
    print("🔧 Quick Fix for News Detector Import Errors")
    print("=" * 60)
    
    # Create all __init__.py files
    init_files = {
        "src/__init__.py": '''"""Telegram News Detector - Core Package"""''',
        "config/__init__.py": '''"""Configuration package"""''',
        "src/client/__init__.py": '''"""Telegram client package"""''',
        "src/services/__init__.py": '''"""Core services package"""''',
        "src/handlers/__init__.py": '''"""Message handlers package"""''',
        "src/utils/__init__.py": '''"""Utility functions package"""''',
    }
    
    for filepath, content in init_files.items():
        create_file(filepath, content)
    
    # Fix the main issues
    print("\n🔧 Fixing specific errors...")
    
    fix_bot_api()
    create_missing_logger()
    create_time_utils()
    create_state_manager()
    create_minimal_telegram_client()
    create_minimal_news_handler()
    create_basic_news_detector()
    create_minimal_credentials()
    
    # Create settings.py from your .env
    settings_content = '''"""
Application settings for the News Detector.
"""
import os
from pathlib import Path
import pytz
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
STATE_DIR = DATA_DIR / "state"
LOGS_DIR = BASE_DIR / "logs"

# Create directories
DATA_DIR.mkdir(exist_ok=True)
STATE_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Core settings
TARGET_CHANNEL_ID = int(os.getenv("TARGET_CHANNEL_ID", "-1002481901026"))
NEW_ATTRIBUTION = os.getenv("NEW_ATTRIBUTION", "@anilgoldgallerynews")
ADMIN_BOT_USERNAME = os.getenv("ADMIN_BOT_USERNAME", "goldnewsadminbot")

# Session file
SESSION_FILE = STATE_DIR / "telegram_session"

# Operating hours
OPERATION_START_HOUR = int(os.getenv("OPERATION_START_HOUR", "9"))
OPERATION_END_HOUR = int(os.getenv("OPERATION_END_HOUR", "22"))
FORCE_24_HOUR_OPERATION = os.getenv("FORCE_24_HOUR_OPERATION", "false").lower() == "true"

# Timezone
TEHRAN_TZ = pytz.timezone('Asia/Tehran')

# News settings
WAR_NEWS_ONLY = os.getenv("WAR_NEWS_ONLY", "true").lower() == "true"
ISRAEL_IRAN_FOCUS = os.getenv("ISRAEL_IRAN_FOCUS", "true").lower() == "true"
GEOPOLITICAL_ONLY = os.getenv("GEOPOLITICAL_ONLY", "true").lower() == "true"

# Intervals and timeouts
NEWS_CHECK_INTERVAL = int(os.getenv("NEWS_CHECK_INTERVAL", "1800"))
ADMIN_APPROVAL_TIMEOUT = int(os.getenv("ADMIN_APPROVAL_TIMEOUT", "3600"))

# News channels
NEWS_CHANNEL = os.getenv("NEWS_CHANNEL", "goldonline2016")
TWITTER_NEWS_CHANNEL = os.getenv("TWITTER_NEWS_CHANNEL", "twiier_news")

# Technical settings
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAY_BASE = int(os.getenv("RETRY_DELAY_BASE", "2"))

# Relevance scoring
MIN_RELEVANCE_SCORE = int(os.getenv("MIN_RELEVANCE_SCORE", "2"))
HIGH_PRIORITY_SCORE = int(os.getenv("HIGH_PRIORITY_SCORE", "5"))

# Media settings
ENABLE_MEDIA_PROCESSING = os.getenv("ENABLE_MEDIA_PROCESSING", "true").lower() == "true"

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", str(LOGS_DIR / "news_detector.log"))
MAX_LOG_SIZE_MB = int(os.getenv("MAX_LOG_SIZE_MB", "50"))
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))

# State
STATE_FILE_PATH = os.getenv("STATE_FILE_PATH", str(STATE_DIR / "news_detector_state.json"))
'''
    
    create_file("config/settings.py", settings_content)
    
    # Create requirements.txt if it doesn't exist
    if not os.path.exists("requirements.txt"):
        requirements_content = '''telethon>=1.31.1
python-dotenv>=1.0.0
requests>=2.31.0
pytz>=2023.3
'''
        create_file("requirements.txt", requirements_content)
    
    print("\n✅ All fixes applied!")
    print("\n🎯 Your project should now run without import errors.")
    print("\n📋 Next steps:")
    print("1. Make sure you have your .env file configured")
    print("2. Install dependencies: pip install -r requirements.txt")
    print("3. Try running again: python main.py")
    
    print("\n🔍 If you still get errors:")
    print("- Check that your .env file has all required values")
    print("- Make sure you're running from the project root directory")
    print("- Check the logs in the logs/ directory")


if __name__ == "__main__":
    main()