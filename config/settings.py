"""
Complete application settings for the Financial News Detector.
Enhanced for financial news detection with Persian calendar and media handling.
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
TARGET_CHANNEL_ID = int(os.getenv("TARGET_CHANNEL_ID", "-1002760442869"))

# News source channels
NEWS_CHANNEL = os.getenv("NEWS_CHANNEL", "goldonline2016").replace('@', '')
TWITTER_NEWS_CHANNEL = os.getenv("TWITTER_NEWS_CHANNEL", "twiier_news").replace('@', '')

# Alternative/backup news channels
BACKUP_NEWS_CHANNEL_1 = os.getenv("BACKUP_NEWS_CHANNEL_1", "").replace('@', '')
BACKUP_NEWS_CHANNEL_2 = os.getenv("BACKUP_NEWS_CHANNEL_2", "").replace('@', '')

# All news channels list
ALL_NEWS_CHANNELS = [ch for ch in [NEWS_CHANNEL, TWITTER_NEWS_CHANNEL, 
                                   BACKUP_NEWS_CHANNEL_1, BACKUP_NEWS_CHANNEL_2] if ch]

# Admin bot configuration
ADMIN_BOT_USERNAME = os.getenv("ADMIN_BOT_USERNAME", "goldnewsadminbot").replace('@', '')

# Attribution for published news
NEW_ATTRIBUTION = os.getenv("NEW_ATTRIBUTION", "@anilnewsonline")

# ============================================================================
# TIMING CONFIGURATION (UPDATED WITH PERSIAN CALENDAR SUPPORT)
# ============================================================================

# Tehran timezone
TEHRAN_TZ = pytz.timezone('Asia/Tehran')

# Operating hours (Updated to support 8:30 AM - 10:00 PM)
OPERATION_START_HOUR = int(os.getenv("OPERATION_START_HOUR", "8"))
OPERATION_START_MINUTE = int(os.getenv("OPERATION_START_MINUTE", "30"))
OPERATION_END_HOUR = int(os.getenv("OPERATION_END_HOUR", "22"))
OPERATION_END_MINUTE = int(os.getenv("OPERATION_END_MINUTE", "0"))

# Force 24-hour operation
FORCE_24_HOUR_OPERATION = os.getenv("FORCE_24_HOUR_OPERATION", "false").lower() == "true"

# Check intervals (in seconds) - OPTIMIZED
NEWS_CHECK_INTERVAL = int(os.getenv("NEWS_CHECK_INTERVAL", "900"))  # 15 minutes
HEALTH_CHECK_INTERVAL = int(os.getenv("HEALTH_CHECK_INTERVAL", "300"))  # 5 minutes
CONNECTION_RETRY_INTERVAL = int(os.getenv("CONNECTION_RETRY_INTERVAL", "30"))  # 30 seconds
HEARTBEAT_INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL", "60"))  # 1 minute

# Processing delays (in seconds) - INCREASED FOR RATE LIMITING
CHANNEL_PROCESSING_DELAY = int(os.getenv("CHANNEL_PROCESSING_DELAY", "5"))  # Increased from 2
APPROVAL_BOT_DELAY = int(os.getenv("APPROVAL_BOT_DELAY", "8"))  # New setting

# Check frequency when outside operating hours
CHECK_OUTSIDE_HOURS = 15 * 60  # 15 minutes

# ============================================================================
# FINANCIAL NEWS CONFIGURATION (ENHANCED)
# ============================================================================

# Financial focus settings - CHANGED DEFAULTS
GOLD_NEWS_PRIORITY = os.getenv("GOLD_NEWS_PRIORITY", "true").lower() == "true"
CURRENCY_NEWS_PRIORITY = os.getenv("CURRENCY_NEWS_PRIORITY", "true").lower() == "true"
IRANIAN_ECONOMY_FOCUS = os.getenv("IRANIAN_ECONOMY_FOCUS", "true").lower() == "true"
CRYPTO_NEWS_ENABLED = os.getenv("CRYPTO_NEWS_ENABLED", "true").lower() == "true"
OIL_ENERGY_NEWS = os.getenv("OIL_ENERGY_NEWS", "true").lower() == "true"
FINANCIAL_MARKETS = os.getenv("FINANCIAL_MARKETS", "true").lower() == "true"

# Economic focus areas
ECONOMIC_WAR_IMPACT = os.getenv("ECONOMIC_WAR_IMPACT", "true").lower() == "true"
IRAN_SANCTIONS_FOCUS = os.getenv("IRAN_SANCTIONS_FOCUS", "true").lower() == "true"
GEOPOLITICAL_ECONOMY = os.getenv("GEOPOLITICAL_ECONOMY", "true").lower() == "true"

# WAR NEWS SETTINGS - DISABLED FOR FINANCIAL FOCUS
WAR_NEWS_ONLY = os.getenv("WAR_NEWS_ONLY", "false").lower() == "true"
ISRAEL_IRAN_FOCUS = os.getenv("ISRAEL_IRAN_FOCUS", "false").lower() == "true"
GEOPOLITICAL_ONLY = os.getenv("GEOPOLITICAL_ONLY", "false").lower() == "true"

# Relevance scoring thresholds - FROM YOUR CONFIG
MIN_FINANCIAL_SCORE = int(os.getenv("MIN_FINANCIAL_SCORE", "3"))
HIGH_PRIORITY_FINANCIAL_SCORE = int(os.getenv("HIGH_PRIORITY_FINANCIAL_SCORE", "6"))
URGENT_FINANCIAL_SCORE = int(os.getenv("URGENT_FINANCIAL_SCORE", "10"))
CRITICAL_FINANCIAL_SCORE = int(os.getenv("CRITICAL_FINANCIAL_SCORE", "15"))

# Financial categories to monitor
MONITOR_GOLD = os.getenv("MONITOR_GOLD", "true").lower() == "true"
MONITOR_CURRENCIES = os.getenv("MONITOR_CURRENCIES", "true").lower() == "true"
MONITOR_CRYPTO = os.getenv("MONITOR_CRYPTO", "true").lower() == "true"
MONITOR_OIL = os.getenv("MONITOR_OIL", "true").lower() == "true"
MONITOR_IRANIAN_ECONOMY = os.getenv("MONITOR_IRANIAN_ECONOMY", "true").lower() == "true"
MONITOR_STOCK_MARKETS = os.getenv("MONITOR_STOCK_MARKETS", "true").lower() == "true"

# ============================================================================
# NEWS DETECTION CONFIGURATION - OPTIMIZED
# ============================================================================

# Text processing limits
MIN_NEWS_LENGTH = int(os.getenv("MIN_NEWS_LENGTH", "30"))
MAX_NEWS_LENGTH = int(os.getenv("MAX_NEWS_LENGTH", "4000"))
NEWS_SEGMENT_MIN_LENGTH = int(os.getenv("NEWS_SEGMENT_MIN_LENGTH", "50"))  # INCREASED from 20

# Duplicate detection
DUPLICATE_CHECK_WINDOW_HOURS = int(os.getenv("DUPLICATE_CHECK_WINDOW_HOURS", "24"))

# Message processing limits - REDUCED FOR VOLUME CONTROL (FROM YOUR CONFIG)
MAX_MESSAGES_PER_CHECK = int(os.getenv("MAX_MESSAGES_PER_CHECK", "30"))  # FROM YOUR CONFIG
MESSAGE_LOOKBACK_HOURS = int(os.getenv("MESSAGE_LOOKBACK_HOURS", "6"))   # FROM YOUR CONFIG

# ============================================================================
# APPROVAL SYSTEM CONFIGURATION
# ============================================================================

# Approval system settings
ENABLE_ADMIN_APPROVAL = os.getenv("ENABLE_ADMIN_APPROVAL", "true").lower() == "true"
REQUIRE_ADMIN_APPROVAL = os.getenv("REQUIRE_ADMIN_APPROVAL", "true").lower() == "true"
AUTO_PUBLISH_ENABLED = os.getenv("AUTO_PUBLISH_ENABLED", "false").lower() == "true"
BYPASS_ADMIN_APPROVAL = os.getenv("BYPASS_ADMIN_APPROVAL", "false").lower() == "true"

# Approval timeouts
ADMIN_APPROVAL_TIMEOUT = int(os.getenv("ADMIN_APPROVAL_TIMEOUT", "3600"))  # 1 hour
PENDING_NEWS_CLEANUP_HOURS = int(os.getenv("PENDING_NEWS_CLEANUP_HOURS", "24"))  # 24 hours

# Approval workflow settings
APPROVAL_CONFIRMATION_REQUIRED = os.getenv("APPROVAL_CONFIRMATION_REQUIRED", "true").lower() == "true"
REJECTION_TRACKING = os.getenv("REJECTION_TRACKING", "true").lower() == "true"

# ============================================================================
# RATE LIMITING CONFIGURATION (FROM YOUR CONFIG)
# ============================================================================

# Rate limiting settings - FROM YOUR CONFIG
MAX_APPROVALS_PER_HOUR = int(os.getenv("MAX_APPROVALS_PER_HOUR", "30"))
MAX_CONCURRENT_APPROVALS = int(os.getenv("MAX_CONCURRENT_APPROVALS", "1"))
MIN_APPROVAL_DELAY = int(os.getenv("MIN_APPROVAL_DELAY", "8"))  # seconds

# Queue management - FROM YOUR CONFIG
MAX_QUEUE_SIZE = int(os.getenv("MAX_QUEUE_SIZE", "30"))
QUEUE_CLEANUP_INTERVAL = int(os.getenv("QUEUE_CLEANUP_INTERVAL", "300"))  # 5 minutes

# Priority filtering - FROM YOUR CONFIG
PRIORITY_FILTERING_ENABLED = os.getenv("PRIORITY_FILTERING_ENABLED", "true").lower() == "true"
MIN_PRIORITY_DURING_PEAK = os.getenv("MIN_PRIORITY_DURING_PEAK", "HIGH")
PEAK_HOURS_START = int(os.getenv("PEAK_HOURS_START", "9"))
PEAK_HOURS_END = int(os.getenv("PEAK_HOURS_END", "18"))

# Retry settings - FROM YOUR CONFIG
MAX_RETRY_ATTEMPTS = int(os.getenv("MAX_RETRY_ATTEMPTS", "3"))
RETRY_DELAY_MULTIPLIER = int(os.getenv("RETRY_DELAY_MULTIPLIER", "2"))
INITIAL_RETRY_DELAY = int(os.getenv("INITIAL_RETRY_DELAY", "30"))

# Enhanced rate limiting
MAX_MESSAGES_PER_MINUTE = int(os.getenv("MAX_MESSAGES_PER_MINUTE", "10"))
FLOOD_WAIT_MAX_DELAY = int(os.getenv("FLOOD_WAIT_MAX_DELAY", "300"))

# ============================================================================
# MEDIA HANDLING CONFIGURATION (NEW)
# ============================================================================

# Media processing
ENABLE_MEDIA_PROCESSING = os.getenv("ENABLE_MEDIA_PROCESSING", "true").lower() == "true"
MAX_MEDIA_SIZE_MB = int(os.getenv("MAX_MEDIA_SIZE_MB", "20"))
MEDIA_CACHE_TIMEOUT_HOURS = int(os.getenv("MEDIA_CACHE_TIMEOUT_HOURS", "6"))

# Media directories
MEDIA_DIR = DATA_DIR / "media"
TEMP_MEDIA_DIR = MEDIA_DIR / "temp"

# Ensure media directories exist
for directory in [MEDIA_DIR, TEMP_MEDIA_DIR]:
    directory.mkdir(exist_ok=True, parents=True)

# Supported media types
SUPPORTED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
SUPPORTED_DOCUMENT_TYPES = ['application/pdf']

# Media cleanup settings
MEDIA_CLEANUP_ENABLED = os.getenv("MEDIA_CLEANUP_ENABLED", "true").lower() == "true"
MEDIA_CLEANUP_DELAY = int(os.getenv("MEDIA_CLEANUP_DELAY", "3600"))  # 1 hour in seconds

# ============================================================================
# TECHNICAL SETTINGS
# ============================================================================

# API call limits - FROM YOUR CONFIG
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAY_BASE = int(os.getenv("RETRY_DELAY_BASE", "2"))  # Base for exponential backoff
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))

# Session management - FROM YOUR CONFIG
SESSION_FILE_PATH = os.getenv("SESSION_FILE_PATH", "./data/state/telegram_session")
SESSION_FILE = Path(SESSION_FILE_PATH)

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

# Logging settings - FROM YOUR CONFIG
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "./logs/news_detector.log")
MAX_LOG_SIZE_MB = int(os.getenv("MAX_LOG_SIZE_MB", "50"))
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))

# Verbose logging options
VERBOSE_LOGGING = os.getenv("VERBOSE_LOGGING", "false").lower() == "true"
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
SAVE_RAW_MESSAGES = os.getenv("SAVE_RAW_MESSAGES", "false").lower() == "true"

# Log formatting
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# ============================================================================
# STATE MANAGEMENT CONFIGURATION
# ============================================================================

# State persistence - FROM YOUR CONFIG
STATE_FILE_PATH = os.getenv("STATE_FILE_PATH", "./data/state/news_detector_state.json")
PENDING_NEWS_BACKUP_INTERVAL = int(os.getenv("PENDING_NEWS_BACKUP_INTERVAL", "300"))  # 5 minutes

# Cache management
PROCESSED_MESSAGES_CACHE_SIZE = int(os.getenv("PROCESSED_MESSAGES_CACHE_SIZE", "10000"))
ADMIN_BOT_CACHE_TIMEOUT = int(os.getenv("ADMIN_BOT_CACHE_TIMEOUT", "3600"))  # 1 hour

# ============================================================================
# FINANCIAL RELEVANCE SCORING (ENHANCED FROM YOUR CONFIG)
# ============================================================================

# OPTIMIZED relevance thresholds for financial content - FROM YOUR CONFIG
MIN_RELEVANCE_SCORE = int(os.getenv("MIN_RELEVANCE_SCORE", "3"))  # FROM YOUR CONFIG
HIGH_PRIORITY_SCORE = int(os.getenv("HIGH_PRIORITY_SCORE", "6"))  # FROM YOUR CONFIG
URGENT_NEWS_SCORE = int(os.getenv("URGENT_NEWS_SCORE", "10"))     # FROM YOUR CONFIG

# Financial keyword weights
GOLD_KEYWORD_WEIGHT = int(os.getenv("GOLD_KEYWORD_WEIGHT", "3"))
CURRENCY_KEYWORD_WEIGHT = int(os.getenv("CURRENCY_KEYWORD_WEIGHT", "3"))
ECONOMY_KEYWORD_WEIGHT = int(os.getenv("ECONOMY_KEYWORD_WEIGHT", "2"))

# ============================================================================
# MONITORING CONFIGURATION (FROM YOUR CONFIG)
# ============================================================================

# Rate limit monitoring - FROM YOUR CONFIG
MONITOR_RATE_LIMITS = os.getenv("MONITOR_RATE_LIMITS", "true").lower() == "true"
RATE_LIMIT_WARNING_THRESHOLD = int(os.getenv("RATE_LIMIT_WARNING_THRESHOLD", "200"))  # seconds
RATE_LIMIT_ALERT_THRESHOLD = int(os.getenv("RATE_LIMIT_ALERT_THRESHOLD", "600"))    # 10 minutes

# Queue monitoring - FROM YOUR CONFIG
MONITOR_QUEUE_SIZE = os.getenv("MONITOR_QUEUE_SIZE", "true").lower() == "true"
QUEUE_SIZE_WARNING_THRESHOLD = int(os.getenv("QUEUE_SIZE_WARNING_THRESHOLD", "20"))
QUEUE_SIZE_ALERT_THRESHOLD = int(os.getenv("QUEUE_SIZE_ALERT_THRESHOLD", "25"))

# Performance monitoring - FROM YOUR CONFIG
ENABLE_PERFORMANCE_LOGGING = os.getenv("ENABLE_PERFORMANCE_LOGGING", "true").lower() == "true"
LOG_PROCESSING_TIMES = os.getenv("LOG_PROCESSING_TIMES", "true").lower() == "true"
SLOW_PROCESSING_THRESHOLD = int(os.getenv("SLOW_PROCESSING_THRESHOLD", "30"))  # seconds

# ============================================================================
# PROXY CONFIGURATION (Optional)
# ============================================================================

# Proxy settings
USE_PROXY = os.getenv("USE_PROXY", "false").lower() == "true"
PROXY_SERVER = os.getenv("PROXY_SERVER", "")
PROXY_PORT = int(os.getenv("PROXY_PORT", "1080")) if os.getenv("PROXY_PORT") else None
PROXY_USERNAME = os.getenv("PROXY_USERNAME", "")
PROXY_PASSWORD = os.getenv("PROXY_PASSWORD", "")
PROXY_TYPE = os.getenv("PROXY_TYPE", "socks5")  # socks5, socks4, http

# ============================================================================
# DEVELOPMENT & TESTING CONFIGURATION
# ============================================================================

# Development settings - FROM YOUR CONFIG
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"
DRY_RUN_MODE = os.getenv("DRY_RUN_MODE", "false").lower() == "true"
ENABLE_TEST_COMMANDS = os.getenv("ENABLE_TEST_COMMANDS", "false").lower() == "true"

# Testing parameters
TEST_CHANNEL_LIMIT = int(os.getenv("TEST_CHANNEL_LIMIT", "5"))
TEST_MESSAGE_LIMIT = int(os.getenv("TEST_MESSAGE_LIMIT", "10"))

# Debug features
ENABLE_PERFORMANCE_MONITORING = os.getenv("ENABLE_PERFORMANCE_MONITORING", "false").lower() == "true"
LOG_MESSAGE_SAMPLES = os.getenv("LOG_MESSAGE_SAMPLES", "false").lower() == "true"

# ============================================================================
# VALIDATION AND DEFAULTS
# ============================================================================

def validate_settings():
    """Validate critical settings and provide warnings."""
    warnings = []
    errors = []
    
    # Check critical settings
    if not TARGET_CHANNEL_ID:
        errors.append("TARGET_CHANNEL_ID must be set")
    
    if not ADMIN_BOT_USERNAME:
        errors.append("ADMIN_BOT_USERNAME must be set")
    
    if not ANY_NEWS_CHANNELS_CONFIGURED():
        warnings.append("No news channels configured")
    
    # Check timing settings
    if OPERATION_START_HOUR < 0 or OPERATION_START_HOUR > 23:
        errors.append("OPERATION_START_HOUR must be between 0 and 23")
    
    if OPERATION_END_HOUR < 0 or OPERATION_END_HOUR > 23:
        errors.append("OPERATION_END_HOUR must be between 0 and 23")
    
    # Check intervals
    if NEWS_CHECK_INTERVAL < 60:
        warnings.append("NEWS_CHECK_INTERVAL is very low (< 60 seconds)")
    
    # Check scoring thresholds
    if MIN_FINANCIAL_SCORE < 1:
        warnings.append("MIN_FINANCIAL_SCORE is very low")
    
    # Check rate limiting settings
    if MIN_APPROVAL_DELAY < 5:
        warnings.append("MIN_APPROVAL_DELAY is very low (< 5 seconds) - may cause rate limits")
    
    if MAX_QUEUE_SIZE > 50:
        warnings.append("MAX_QUEUE_SIZE is very high (> 50) - may cause memory issues")
    
    return warnings, errors

def ANY_NEWS_CHANNELS_CONFIGURED():
    """Check if any news channels are configured."""
    return bool(NEWS_CHANNEL or TWITTER_NEWS_CHANNEL or 
                BACKUP_NEWS_CHANNEL_1 or BACKUP_NEWS_CHANNEL_2)

def get_active_news_channels():
    """Get list of active news channels."""
    return [ch for ch in ALL_NEWS_CHANNELS if ch]

def get_settings_summary():
    """Get a summary of current settings for logging."""
    return {
        "target_channel": TARGET_CHANNEL_ID,
        "admin_bot": ADMIN_BOT_USERNAME,
        "news_channels": get_active_news_channels(),
        "operating_hours": f"{OPERATION_START_HOUR}:{OPERATION_START_MINUTE:02d}-{OPERATION_END_HOUR}:{OPERATION_END_MINUTE:02d}",
        "24h_mode": FORCE_24_HOUR_OPERATION,
        "check_interval": NEWS_CHECK_INTERVAL,
        "message_lookback_hours": MESSAGE_LOOKBACK_HOURS,
        "max_messages_per_check": MAX_MESSAGES_PER_CHECK,
        "financial_focus": {
            "gold": MONITOR_GOLD,
            "currency": MONITOR_CURRENCIES,
            "crypto": MONITOR_CRYPTO,
            "oil": MONITOR_OIL,
            "iranian_economy": MONITOR_IRANIAN_ECONOMY,
            "stock_markets": MONITOR_STOCK_MARKETS
        },
        "war_news_only": WAR_NEWS_ONLY,
        "geopolitical_only": GEOPOLITICAL_ONLY,
        "approval_system": ENABLE_ADMIN_APPROVAL,
        "min_financial_score": MIN_FINANCIAL_SCORE,
        "min_relevance_score": MIN_RELEVANCE_SCORE,
        "rate_limiting": {
            "min_delay": MIN_APPROVAL_DELAY,
            "max_queue": MAX_QUEUE_SIZE,
            "max_per_hour": MAX_APPROVALS_PER_HOUR
        },
        "media_handling": ENABLE_MEDIA_PROCESSING
    }

# ============================================================================
# LEGACY COMPATIBILITY (for original bot integration)
# ============================================================================

# Maintain compatibility with original bot settings
BOT_USERNAME = os.getenv("BOT_USERNAME", "abshdhbot")  # Not used in news bot
CURRENCY_CHANNEL = os.getenv("CURRENCY_CHANNEL", "dolar_403")  # Not used in news bot
TEHRAN_SABZA_CHANNEL = os.getenv("TEHRAN_SABZA_CHANNEL", "tahran_sabza")  # Not used in news bot

# Message templates (for original bot compatibility)
MESSAGE_TITLE = "💰 <b>اخبار مالی و اقتصادی</b>"
TIME_FORMAT = '%H:%M:%S'

# ============================================================================
# RUNTIME VALIDATION
# ============================================================================

# Validate settings on import
if __name__ != "__main__":
    try:
        warnings, errors = validate_settings()
        
        if errors:
            import logging
            logger = logging.getLogger(__name__)
            for error in errors:
                logger.error(f"Settings error: {error}")
            raise ValueError(f"Critical settings errors: {errors}")
        
        if warnings:
            import logging
            logger = logging.getLogger(__name__)
            for warning in warnings:
                logger.warning(f"Settings warning: {warning}")
                
    except Exception as e:
        # Don't fail import, but log the issue
        print(f"Settings validation failed: {e}")

# Export commonly used settings for easy import
__all__ = [
    'TARGET_CHANNEL_ID', 'NEWS_CHANNEL', 'TWITTER_NEWS_CHANNEL', 'ADMIN_BOT_USERNAME',
    'NEW_ATTRIBUTION', 'NEWS_CHECK_INTERVAL', 'OPERATION_START_HOUR', 'OPERATION_START_MINUTE',
    'OPERATION_END_HOUR', 'OPERATION_END_MINUTE', 'FORCE_24_HOUR_OPERATION', 'MIN_FINANCIAL_SCORE', 
    'ENABLE_ADMIN_APPROVAL', 'ALL_NEWS_CHANNELS', 'get_active_news_channels', 'get_settings_summary',
    'TEHRAN_TZ', 'DEBUG_MODE', 'LOG_LEVEL', 'CHANNEL_PROCESSING_DELAY',
    'MESSAGE_LOOKBACK_HOURS', 'MAX_MESSAGES_PER_CHECK', 'MIN_RELEVANCE_SCORE',
    'GOLD_NEWS_PRIORITY', 'CURRENCY_NEWS_PRIORITY', 'IRANIAN_ECONOMY_FOCUS',
    'MAX_RETRIES', 'RETRY_DELAY_BASE', 'API_TIMEOUT', 'SESSION_FILE', 'SESSION_FILE_PATH',
    'MIN_APPROVAL_DELAY', 'MAX_QUEUE_SIZE', 'MAX_APPROVALS_PER_HOUR',
    'MEDIA_DIR', 'TEMP_MEDIA_DIR', 'ENABLE_MEDIA_PROCESSING', 'MAX_MEDIA_SIZE_MB',
    'MEDIA_CLEANUP_ENABLED', 'MEDIA_CLEANUP_DELAY'
]