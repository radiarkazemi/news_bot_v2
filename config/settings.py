"""
Complete application settings for the News Detector.
All configurable values loaded from environment variables with proper defaults.
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

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
STATE_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# ================================
# CORE TELEGRAM SETTINGS
# ================================
TARGET_CHANNEL_ID = int(os.getenv("TARGET_CHANNEL_ID", "-1002481901026"))
NEW_ATTRIBUTION = os.getenv("NEW_ATTRIBUTION", "@anilgoldgallerynews")

# Admin bot settings
ADMIN_BOT_USERNAME = os.getenv("ADMIN_BOT_USERNAME", "goldnewsadminbot")

# Session file
SESSION_FILE_PATH = os.getenv("SESSION_FILE_PATH", str(STATE_DIR / "telegram_session"))
SESSION_FILE = Path(SESSION_FILE_PATH)

# ================================
# OPERATING HOURS (TEHRAN TIME)
# ================================
OPERATION_START_HOUR = int(os.getenv("OPERATION_START_HOUR", "9"))
OPERATION_END_HOUR = int(os.getenv("OPERATION_END_HOUR", "22"))
FORCE_24_HOUR_OPERATION = os.getenv("FORCE_24_HOUR_OPERATION", "false").lower() == "true"

# Timezone settings
TEHRAN_TZ = pytz.timezone('Asia/Tehran')
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# ================================
# NEWS DETECTION SETTINGS
# ================================
WAR_NEWS_ONLY = os.getenv("WAR_NEWS_ONLY", "true").lower() == "true"
ISRAEL_IRAN_FOCUS = os.getenv("ISRAEL_IRAN_FOCUS", "true").lower() == "true"
GEOPOLITICAL_ONLY = os.getenv("GEOPOLITICAL_ONLY", "true").lower() == "true"
ECONOMIC_WAR_IMPACT = os.getenv("ECONOMIC_WAR_IMPACT", "true").lower() == "true"

# News processing settings
MIN_NEWS_LENGTH = int(os.getenv("MIN_NEWS_LENGTH", "50"))
MAX_NEWS_LENGTH = int(os.getenv("MAX_NEWS_LENGTH", "4000"))
NEWS_SEGMENT_MIN_LENGTH = int(os.getenv("NEWS_SEGMENT_MIN_LENGTH", "30"))

# Relevance scoring thresholds
MIN_RELEVANCE_SCORE = int(os.getenv("MIN_RELEVANCE_SCORE", "2"))
HIGH_PRIORITY_SCORE = int(os.getenv("HIGH_PRIORITY_SCORE", "5"))
URGENT_NEWS_SCORE = int(os.getenv("URGENT_NEWS_SCORE", "8"))

# ================================
# ADMIN APPROVAL SYSTEM
# ================================
ENABLE_ADMIN_APPROVAL = os.getenv("ENABLE_ADMIN_APPROVAL", "true").lower() == "true"
REQUIRE_ADMIN_APPROVAL = os.getenv("REQUIRE_ADMIN_APPROVAL", "true").lower() == "true"
AUTO_PUBLISH_ENABLED = os.getenv("AUTO_PUBLISH_ENABLED", "false").lower() == "true"
BYPASS_ADMIN_APPROVAL = os.getenv("BYPASS_ADMIN_APPROVAL", "false").lower() == "true"
ADMIN_APPROVAL_TIMEOUT = int(os.getenv("ADMIN_APPROVAL_TIMEOUT", "3600"))

# ================================
# NEWS MONITORING
# ================================
NEWS_CHECK_INTERVAL = int(os.getenv("NEWS_CHECK_INTERVAL", "1800"))  # 30 minutes
NEWS_CHANNEL = os.getenv("NEWS_CHANNEL", "goldonline2016")
TWITTER_NEWS_CHANNEL = os.getenv("TWITTER_NEWS_CHANNEL", "twiier_news")

# Additional news channels
BACKUP_NEWS_CHANNELS = [
    ch for ch in [
        os.getenv("BACKUP_NEWS_CHANNEL_1", ""),
        os.getenv("BACKUP_NEWS_CHANNEL_2", ""),
        os.getenv("BACKUP_NEWS_CHANNEL_3", "")
    ] if ch
]

# All news channels combined
ALL_NEWS_CHANNELS = [ch for ch in [NEWS_CHANNEL, TWITTER_NEWS_CHANNEL] + BACKUP_NEWS_CHANNELS if ch]

# ================================
# TECHNICAL SETTINGS
# ================================
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_DELAY_BASE = int(os.getenv("RETRY_DELAY_BASE", "2"))

# Rate limiting settings
MAX_MESSAGES_PER_MINUTE = int(os.getenv("MAX_MESSAGES_PER_MINUTE", "10"))
CHANNEL_PROCESSING_DELAY = int(os.getenv("CHANNEL_PROCESSING_DELAY", "2"))
APPROVAL_BOT_DELAY = int(os.getenv("APPROVAL_BOT_DELAY", "1"))
MESSAGE_BATCH_SIZE = int(os.getenv("MESSAGE_BATCH_SIZE", "20"))

# Connection settings
CONNECTION_TIMEOUT = int(os.getenv("CONNECTION_TIMEOUT", "30"))
READ_TIMEOUT = int(os.getenv("READ_TIMEOUT", "60"))

# ================================
# MEDIA HANDLING
# ================================
ENABLE_MEDIA_PROCESSING = os.getenv("ENABLE_MEDIA_PROCESSING", "true").lower() == "true"
MAX_MEDIA_SIZE_MB = int(os.getenv("MAX_MEDIA_SIZE_MB", "20"))
MEDIA_CACHE_TIMEOUT_HOURS = int(os.getenv("MEDIA_CACHE_TIMEOUT_HOURS", "6"))
SUPPORTED_MEDIA_TYPES = ['photo', 'document', 'video']

# ================================
# PERSISTENCE SETTINGS
# ================================
STATE_FILE_PATH = os.getenv("STATE_FILE_PATH", str(STATE_DIR / "news_detector_state.json"))
PENDING_NEWS_BACKUP_INTERVAL = int(os.getenv("PENDING_NEWS_BACKUP_INTERVAL", "300"))
DUPLICATE_CHECK_WINDOW_HOURS = int(os.getenv("DUPLICATE_CHECK_WINDOW_HOURS", "24"))
STATE_BACKUP_COUNT = int(os.getenv("STATE_BACKUP_COUNT", "5"))

# ================================
# MONITORING & HEALTH
# ================================
HEALTH_CHECK_INTERVAL = int(os.getenv("HEALTH_CHECK_INTERVAL", "300"))
CONNECTION_RETRY_INTERVAL = int(os.getenv("CONNECTION_RETRY_INTERVAL", "30"))
HEARTBEAT_INTERVAL = int(os.getenv("HEARTBEAT_INTERVAL", "60"))
STATS_LOG_INTERVAL = int(os.getenv("STATS_LOG_INTERVAL", "1800"))

# ================================
# LOGGING CONFIGURATION
# ================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", str(LOGS_DIR / "news_detector.log"))
MAX_LOG_SIZE_MB = int(os.getenv("MAX_LOG_SIZE_MB", "50"))
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))

# Enhanced logging options
VERBOSE_LOGGING = os.getenv("VERBOSE_LOGGING", "false").lower() == "true"
LOG_TELEGRAM_EVENTS = os.getenv("LOG_TELEGRAM_EVENTS", "false").lower() == "true"
LOG_RAW_MESSAGES = os.getenv("LOG_RAW_MESSAGES", "false").lower() == "true"

# ================================
# DEBUG & DEVELOPMENT
# ================================
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"
SAVE_RAW_MESSAGES = os.getenv("SAVE_RAW_MESSAGES", "false").lower() == "true"
DRY_RUN_MODE = os.getenv("DRY_RUN_MODE", "false").lower() == "true"

# Development shortcuts
SKIP_DUPLICATE_CHECK = os.getenv("SKIP_DUPLICATE_CHECK", "false").lower() == "true"
FORCE_PROCESS_ALL = os.getenv("FORCE_PROCESS_ALL", "false").lower() == "true"

# ================================
# PROXY SETTINGS
# ================================
USE_PROXY = os.getenv("USE_PROXY", "false").lower() == "true"
PROXY_SERVER = os.getenv("PROXY_SERVER", "")
PROXY_USERNAME = os.getenv("PROXY_USERNAME", "")
PROXY_PASSWORD = os.getenv("PROXY_PASSWORD", "")

# Proxy configuration for Telethon
PROXY_CONFIG = None
if USE_PROXY and PROXY_SERVER:
    import socks
    if PROXY_SERVER.startswith("socks5://"):
        proxy_url = PROXY_SERVER.replace("socks5://", "")
        if ":" in proxy_url:
            proxy_host, proxy_port = proxy_url.split(":", 1)
            PROXY_CONFIG = (socks.SOCKS5, proxy_host, int(proxy_port))

# ================================
# MESSAGE FORMATTING
# ================================
MESSAGE_MAX_LENGTH = int(os.getenv("MESSAGE_MAX_LENGTH", "4096"))
ATTRIBUTION_FORMAT = os.getenv("ATTRIBUTION_FORMAT", "📡 {attribution}")
TIMESTAMP_FORMAT = os.getenv("TIMESTAMP_FORMAT", "🕐 {timestamp}")

# News formatting templates
NEWS_URGENT_PREFIX = os.getenv("NEWS_URGENT_PREFIX", "🔴")
NEWS_IMPORTANT_PREFIX = os.getenv("NEWS_IMPORTANT_PREFIX", "🔶") 
NEWS_NORMAL_PREFIX = os.getenv("NEWS_NORMAL_PREFIX", "📰")
NEWS_WAR_PREFIX = os.getenv("NEWS_WAR_PREFIX", "⚡")

# ================================
# SECURITY SETTINGS
# ================================
ENABLE_FLOOD_PROTECTION = os.getenv("ENABLE_FLOOD_PROTECTION", "true").lower() == "true"
MAX_PENDING_APPROVALS = int(os.getenv("MAX_PENDING_APPROVALS", "50"))
APPROVAL_ID_LENGTH = int(os.getenv("APPROVAL_ID_LENGTH", "8"))

# ================================
# PERFORMANCE SETTINGS
# ================================
MEMORY_CACHE_SIZE = int(os.getenv("MEMORY_CACHE_SIZE", "1000"))
PROCESSED_MESSAGES_CACHE_SIZE = int(os.getenv("PROCESSED_MESSAGES_CACHE_SIZE", "10000"))
CHANNEL_CACHE_TIMEOUT = int(os.getenv("CHANNEL_CACHE_TIMEOUT", "3600"))

# ================================
# FEATURE FLAGS
# ================================
ENABLE_NEWS_DETECTION = os.getenv("ENABLE_NEWS_DETECTION", "true").lower() == "true"
ENABLE_NEWS_FILTERING = os.getenv("ENABLE_NEWS_FILTERING", "true").lower() == "true"
ENABLE_NEWS_SEGMENTATION = os.getenv("ENABLE_NEWS_SEGMENTATION", "true").lower() == "true"
ENABLE_METADATA_EXTRACTION = os.getenv("ENABLE_METADATA_EXTRACTION", "true").lower() == "true"
ENABLE_STATISTICS_TRACKING = os.getenv("ENABLE_STATISTICS_TRACKING", "true").lower() == "true"

# ================================
# VALIDATION FUNCTIONS
# ================================

def validate_settings():
    """Validate all settings for consistency."""
    issues = []
    
    # Validate operating hours
    if not (0 <= OPERATION_START_HOUR <= 23):
        issues.append(f"OPERATION_START_HOUR ({OPERATION_START_HOUR}) must be 0-23")
    
    if not (0 <= OPERATION_END_HOUR <= 23):
        issues.append(f"OPERATION_END_HOUR ({OPERATION_END_HOUR}) must be 0-23")
    
    if OPERATION_START_HOUR >= OPERATION_END_HOUR:
        issues.append("OPERATION_START_HOUR must be less than OPERATION_END_HOUR")
    
    # Validate intervals
    if NEWS_CHECK_INTERVAL < 60:
        issues.append("NEWS_CHECK_INTERVAL should be at least 60 seconds")
    
    if ADMIN_APPROVAL_TIMEOUT < 300:
        issues.append("ADMIN_APPROVAL_TIMEOUT should be at least 300 seconds (5 minutes)")
    
    # Validate thresholds
    if MIN_RELEVANCE_SCORE < 0:
        issues.append("MIN_RELEVANCE_SCORE cannot be negative")
    
    if HIGH_PRIORITY_SCORE <= MIN_RELEVANCE_SCORE:
        issues.append("HIGH_PRIORITY_SCORE must be greater than MIN_RELEVANCE_SCORE")
    
    # Validate file sizes
    if MAX_LOG_SIZE_MB < 1:
        issues.append("MAX_LOG_SIZE_MB must be at least 1")
    
    if MAX_MEDIA_SIZE_MB < 1:
        issues.append("MAX_MEDIA_SIZE_MB must be at least 1")
    
    # Validate channels
    if not ALL_NEWS_CHANNELS:
        issues.append("At least one news channel must be configured")
    
    if issues:
        import logging
        logger = logging.getLogger(__name__)
        for issue in issues:
            logger.error(f"❌ Configuration issue: {issue}")
        raise ValueError(f"Configuration validation failed: {len(issues)} issues found")


def get_settings_summary():
    """Get a summary of current settings."""
    return {
        'operating_hours': f"{OPERATION_START_HOUR}:00 - {OPERATION_END_HOUR}:00 Tehran",
        'news_channels': len(ALL_NEWS_CHANNELS),
        'check_interval': f"{NEWS_CHECK_INTERVAL} seconds",
        'approval_timeout': f"{ADMIN_APPROVAL_TIMEOUT} seconds",
        'war_news_only': WAR_NEWS_ONLY,
        'israel_iran_focus': ISRAEL_IRAN_FOCUS,
        'min_relevance_score': MIN_RELEVANCE_SCORE,
        'high_priority_score': HIGH_PRIORITY_SCORE,
        'media_processing': ENABLE_MEDIA_PROCESSING,
        'proxy_enabled': USE_PROXY,
        'debug_mode': DEBUG_MODE,
        'log_level': LOG_LEVEL
    }


def log_configuration():
    """Log current configuration summary."""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info("⚙️  News Detector Configuration:")
    summary = get_settings_summary()
    
    for key, value in summary.items():
        logger.info(f"   {key}: {value}")


# Auto-validate settings on import
try:
    validate_settings()
except Exception as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"⚠️  Settings validation warning: {e}")

# ================================
# ENVIRONMENT-SPECIFIC OVERRIDES
# ================================

# Development environment overrides
if DEBUG_MODE:
    # More verbose logging in debug mode
    if LOG_LEVEL == "INFO":
        LOG_LEVEL = "DEBUG"
    
    # Shorter intervals for testing
    if NEWS_CHECK_INTERVAL > 300:
        NEWS_CHECK_INTERVAL = 300  # 5 minutes in debug mode
    
    # Enable raw message logging
    SAVE_RAW_MESSAGES = True
    VERBOSE_LOGGING = True

# Test mode overrides
if TEST_MODE:
    # Very short intervals for testing
    NEWS_CHECK_INTERVAL = 60  # 1 minute
    ADMIN_APPROVAL_TIMEOUT = 300  # 5 minutes
    HEALTH_CHECK_INTERVAL = 60  # 1 minute
    
    # Skip duplicate checking in test mode
    SKIP_DUPLICATE_CHECK = True

# Production optimizations
if not DEBUG_MODE and not TEST_MODE:
    # Optimize for production
    MEMORY_CACHE_SIZE = min(MEMORY_CACHE_SIZE, 500)  # Limit memory usage
    LOG_BACKUP_COUNT = min(LOG_BACKUP_COUNT, 3)  # Limit log files