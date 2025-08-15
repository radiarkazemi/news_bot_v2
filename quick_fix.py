#!/usr/bin/env python3
"""
Quick fix for missing imports in config/settings.py
"""

def fix_settings_imports():
    """Add missing constants to settings.py"""
    
    from pathlib import Path
    
    settings_file = Path("config/settings.py")
    
    if not settings_file.exists():
        print("❌ config/settings.py not found")
        return False
    
    # Read current settings
    with open(settings_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add missing constants if they don't exist
    missing_constants = {
        'MAX_RETRIES': 'MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))',
        'RETRY_DELAY_BASE': 'RETRY_DELAY_BASE = int(os.getenv("RETRY_DELAY_BASE", "2"))',
        'API_TIMEOUT': 'API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))',
        'CHANNEL_PROCESSING_DELAY': 'CHANNEL_PROCESSING_DELAY = int(os.getenv("CHANNEL_PROCESSING_DELAY", "2"))',
        'SESSION_FILE': 'SESSION_FILE = Path(os.getenv("SESSION_FILE_PATH", str(SESSION_DIR / "telegram_session")))',
        'MESSAGE_LOOKBACK_HOURS': 'MESSAGE_LOOKBACK_HOURS = int(os.getenv("MESSAGE_LOOKBACK_HOURS", "12"))',
        'MAX_MESSAGES_PER_CHECK': 'MAX_MESSAGES_PER_CHECK = int(os.getenv("MAX_MESSAGES_PER_CHECK", "50"))'
    }
    
    # Check which constants are missing
    added_constants = []
    for const_name, const_line in missing_constants.items():
        if const_name not in content:
            # Add before the validation section
            if "# VALIDATION AND DEFAULTS" in content:
                content = content.replace(
                    "# ============================================================================\n# VALIDATION AND DEFAULTS",
                    f"{const_line}\n\n# ============================================================================\n# VALIDATION AND DEFAULTS"
                )
            else:
                # Add at the end
                content += f"\n{const_line}\n"
            added_constants.append(const_name)
    
    # Write back the file
    with open(settings_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    if added_constants:
        print(f"✅ Added missing constants: {', '.join(added_constants)}")
    else:
        print("✅ All constants already present")
    
    return True

def fix_telegram_client_imports():
    """Fix imports in telegram_client.py if needed"""
    
    from pathlib import Path
    
    client_file = Path("src/client/telegram_client.py")
    
    if not client_file.exists():
        print("❌ src/client/telegram_client.py not found")
        return False
    
    # Read current client file
    with open(client_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix common import issues
    fixes_applied = []
    
    # Fix SESSION_FILE import
    if "SESSION_FILE" in content and "from config.settings import" in content:
        if "SESSION_FILE" not in content.split("from config.settings import")[1].split("\n")[0]:
            # Add SESSION_FILE to imports
            old_import = content.split("from config.settings import")[1].split("\n")[0]
            new_import = old_import + ", SESSION_FILE"
            content = content.replace(
                f"from config.settings import{old_import}",
                f"from config.settings import{new_import}"
            )
            fixes_applied.append("Added SESSION_FILE import")
    
    # Write back if changes made
    if fixes_applied:
        with open(client_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Fixed telegram_client.py: {', '.join(fixes_applied)}")
    
    return True

def add_minimal_settings():
    """Add minimal working settings to config/settings.py"""
    
    from pathlib import Path
    
    settings_file = Path("config/settings.py")
    
    # Backup existing file
    if settings_file.exists():
        import shutil
        import time
        backup_file = Path(f"config/settings.py.backup.{int(time.time())}")
        shutil.copy2(settings_file, backup_file)
        print(f"✅ Backed up settings to {backup_file}")
    
    # Minimal working settings
    minimal_settings = '''"""
Complete application settings for the Financial News Detector.
"""
import os
import pytz
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================================================
# PROJECT CONFIGURATION
# ============================================================================

# Project base directory
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR

# Data directories
DATA_DIR = BASE_DIR / "data"
STATE_DIR = DATA_DIR / "state"
LOGS_DIR = BASE_DIR / "logs"
SESSION_DIR = DATA_DIR / "session"

# Ensure directories exist
for directory in [DATA_DIR, STATE_DIR, LOGS_DIR, SESSION_DIR]:
    directory.mkdir(exist_ok=True, parents=True)

# ============================================================================
# TELEGRAM CONFIGURATION
# ============================================================================

# Target channel for approved news
TARGET_CHANNEL_ID = int(os.getenv("TARGET_CHANNEL_ID", "-1002481901026"))

# News source channels
NEWS_CHANNEL = os.getenv("NEWS_CHANNEL", "goldonline2016").replace('@', '')
TWITTER_NEWS_CHANNEL = os.getenv("TWITTER_NEWS_CHANNEL", "twiier_news").replace('@', '')

# All news channels list
ALL_NEWS_CHANNELS = [ch for ch in [NEWS_CHANNEL, TWITTER_NEWS_CHANNEL] if ch]

# Admin bot configuration
ADMIN_BOT_USERNAME = os.getenv("ADMIN_BOT_USERNAME", "goldnewsadminbot").replace('@', '')

# Attribution for published news
NEW_ATTRIBUTION = os.getenv("NEW_ATTRIBUTION", "@anilgoldgallerynews")

# ============================================================================
# TIMING CONFIGURATION
# ============================================================================

# Tehran timezone
TEHRAN_TZ = pytz.timezone('Asia/Tehran')

# Operating hours (Tehran time)
OPERATION_START_HOUR = int(os.getenv("OPERATION_START_HOUR", "9"))
OPERATION_END_HOUR = int(os.getenv("OPERATION_END_HOUR", "22"))

# Force 24-hour operation
FORCE_24_HOUR_OPERATION = os.getenv("FORCE_24_HOUR_OPERATION", "false").lower() == "true"

# Check intervals (in seconds)
NEWS_CHECK_INTERVAL = int(os.getenv("NEWS_CHECK_INTERVAL", "900"))

# ============================================================================
# FINANCIAL NEWS CONFIGURATION
# ============================================================================

# Financial focus settings
GOLD_NEWS_PRIORITY = os.getenv("GOLD_NEWS_PRIORITY", "true").lower() == "true"
CURRENCY_NEWS_PRIORITY = os.getenv("CURRENCY_NEWS_PRIORITY", "true").lower() == "true"
IRANIAN_ECONOMY_FOCUS = os.getenv("IRANIAN_ECONOMY_FOCUS", "true").lower() == "true"

# War news settings - DISABLED for financial focus
WAR_NEWS_ONLY = os.getenv("WAR_NEWS_ONLY", "false").lower() == "true"
ISRAEL_IRAN_FOCUS = os.getenv("ISRAEL_IRAN_FOCUS", "false").lower() == "true"
GEOPOLITICAL_ONLY = os.getenv("GEOPOLITICAL_ONLY", "false").lower() == "true"

# Relevance scoring thresholds - LOWERED for financial
MIN_FINANCIAL_SCORE = int(os.getenv("MIN_FINANCIAL_SCORE", "0"))
MIN_RELEVANCE_SCORE = int(os.getenv("MIN_RELEVANCE_SCORE", "0"))
HIGH_PRIORITY_SCORE = int(os.getenv("HIGH_PRIORITY_SCORE", "3"))

# ============================================================================
# NEWS DETECTION CONFIGURATION
# ============================================================================

# Message processing - ENHANCED for financial
MESSAGE_LOOKBACK_HOURS = int(os.getenv("MESSAGE_LOOKBACK_HOURS", "24"))
MAX_MESSAGES_PER_CHECK = int(os.getenv("MAX_MESSAGES_PER_CHECK", "50"))

# Text processing limits
MIN_NEWS_LENGTH = int(os.getenv("MIN_NEWS_LENGTH", "30"))
MAX_NEWS_LENGTH = int(os.getenv("MAX_NEWS_LENGTH", "4000"))

# ============================================================================
# APPROVAL SYSTEM CONFIGURATION
# ============================================================================

# Approval system settings
ENABLE_ADMIN_APPROVAL = os.getenv("ENABLE_ADMIN_APPROVAL", "true").lower() == "true"
REQUIRE_ADMIN_APPROVAL = os.getenv("REQUIRE_ADMIN_APPROVAL", "true").lower() == "true"
ADMIN_APPROVAL_TIMEOUT = int(os.getenv("ADMIN_APPROVAL_TIMEOUT", "3600"))

# ============================================================================
# TECHNICAL SETTINGS
# ============================================================================

# API call limits
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAY_BASE = int(os.getenv("RETRY_DELAY_BASE", "2"))
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))

# Processing delays
CHANNEL_PROCESSING_DELAY = int(os.getenv("CHANNEL_PROCESSING_DELAY", "2"))

# Session management
SESSION_FILE_PATH = os.getenv("SESSION_FILE_PATH", str(SESSION_DIR / "telegram_session"))
SESSION_FILE = Path(SESSION_FILE_PATH)

# State management
STATE_FILE_PATH = os.getenv("STATE_FILE_PATH", str(STATE_DIR / "news_detector_state.json"))

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

# Logging settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", str(LOGS_DIR / "news_detector.log"))
MAX_LOG_SIZE_MB = int(os.getenv("MAX_LOG_SIZE_MB", "50"))
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))

# Debug settings
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_active_news_channels():
    """Get list of active news channels."""
    return [ch for ch in ALL_NEWS_CHANNELS if ch]

def get_settings_summary():
    """Get a summary of current settings for logging."""
    return {
        "target_channel": TARGET_CHANNEL_ID,
        "admin_bot": ADMIN_BOT_USERNAME,
        "news_channels": get_active_news_channels(),
        "message_lookback_hours": MESSAGE_LOOKBACK_HOURS,
        "max_messages_per_check": MAX_MESSAGES_PER_CHECK,
        "war_news_only": WAR_NEWS_ONLY,
        "financial_focus": {
            "gold": GOLD_NEWS_PRIORITY,
            "currency": CURRENCY_NEWS_PRIORITY,
            "iranian_economy": IRANIAN_ECONOMY_FOCUS
        },
        "min_financial_score": MIN_FINANCIAL_SCORE,
        "min_relevance_score": MIN_RELEVANCE_SCORE
    }

# Export commonly used settings
__all__ = [
    'TARGET_CHANNEL_ID', 'NEWS_CHANNEL', 'TWITTER_NEWS_CHANNEL', 'ADMIN_BOT_USERNAME',
    'NEW_ATTRIBUTION', 'NEWS_CHECK_INTERVAL', 'OPERATION_START_HOUR', 'OPERATION_END_HOUR',
    'FORCE_24_HOUR_OPERATION', 'MIN_FINANCIAL_SCORE', 'ENABLE_ADMIN_APPROVAL',
    'ALL_NEWS_CHANNELS', 'get_active_news_channels', 'get_settings_summary',
    'TEHRAN_TZ', 'DEBUG_MODE', 'LOG_LEVEL', 'CHANNEL_PROCESSING_DELAY',
    'MESSAGE_LOOKBACK_HOURS', 'MAX_MESSAGES_PER_CHECK', 'MIN_RELEVANCE_SCORE',
    'GOLD_NEWS_PRIORITY', 'CURRENCY_NEWS_PRIORITY', 'IRANIAN_ECONOMY_FOCUS',
    'MAX_RETRIES', 'RETRY_DELAY_BASE', 'API_TIMEOUT', 'SESSION_FILE', 'SESSION_FILE_PATH'
]
'''
    
    # Write minimal settings
    with open(settings_file, 'w', encoding='utf-8') as f:
        f.write(minimal_settings)
    
    print("✅ Created minimal working settings.py")

def main():
    """Fix import issues."""
    
    print("🔧 FIXING IMPORT ISSUES")
    print("=" * 40)
    
    # Try to fix existing settings first
    if fix_settings_imports():
        print("✅ Fixed existing settings.py")
    else:
        # Create minimal settings if fix failed
        print("🔧 Creating minimal settings.py...")
        add_minimal_settings()
    
    # Fix telegram client imports
    fix_telegram_client_imports()
    
    print("\n🧪 TEST THE FIX:")
    print("=" * 30)
    print("python main.py --test-news --news-channel goldonline2016")

if __name__ == "__main__":
    main()