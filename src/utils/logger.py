"""
Complete logging system for the Financial News Detector.
Provides structured, rotated, and configurable logging.
"""
import logging
import logging.handlers
import sys
import os
from pathlib import Path
from datetime import datetime

def setup_logging(
    log_level=None, 
    log_file=None, 
    max_size_mb=None, 
    backup_count=None,
    console_output=True
):
    """
    Set up comprehensive logging for the Financial News Detector.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (default: logs/news_detector.log)
        max_size_mb: Maximum log file size in MB before rotation (default: 50)
        backup_count: Number of backup log files to keep (default: 5)
        console_output: Whether to output logs to console (default: True)
    
    Returns:
        logging.Logger: Configured root logger
    """
    
    # Get configuration from environment or use defaults
    log_level = log_level or os.getenv("LOG_LEVEL", "INFO").upper()
    log_file = log_file or os.getenv("LOG_FILE_PATH", "logs/news_detector.log")
    max_size_mb = max_size_mb or int(os.getenv("MAX_LOG_SIZE_MB", "50"))
    backup_count = backup_count or int(os.getenv("LOG_BACKUP_COUNT", "5"))
    
    # Create logs directory
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Clear any existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Set root logger level
    root_logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        fmt='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # File handler with rotation
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=max_size_mb * 1024 * 1024,  # Convert MB to bytes
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)  # Log everything to file
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)
        
        # Log startup message
        root_logger.info(f"📁 Log file: {log_file}")
        root_logger.info("🚀 Logging system initialized")
        root_logger.info(f"📊 Log level: {log_level}")
        
    except Exception as e:
        print(f"❌ Failed to set up file logging: {e}")
        print("Continuing with console logging only...")
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level, logging.INFO))
        
        # Use simple format for console in production, detailed in debug
        if log_level == "DEBUG":
            console_handler.setFormatter(detailed_formatter)
        else:
            console_handler.setFormatter(simple_formatter)
        
        root_logger.addHandler(console_handler)
    
    # Configure specific loggers
    _configure_specific_loggers(log_level)
    
    # Add custom log methods
    _add_custom_log_methods(root_logger)
    
    return root_logger

def _configure_specific_loggers(log_level):
    """Configure logging for specific modules and libraries."""
    
    # Financial News Detector components
    news_loggers = [
        'src.handlers.news_handler',
        'src.services.news_detector', 
        'src.services.news_filter',
        'src.client.telegram_client',
        'src.client.bot_api'
    ]
    
    for logger_name in news_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    # Third-party library loggers (reduce verbosity)
    third_party_loggers = {
        'telethon': logging.WARNING,
        'urllib3': logging.WARNING,
        'requests': logging.WARNING,
        'asyncio': logging.WARNING,
        'aiohttp': logging.WARNING
    }
    
    for logger_name, level in third_party_loggers.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
    
    # Special handling for debug mode
    if log_level == "DEBUG":
        # Enable more verbose logging for our components in debug mode
        logging.getLogger('src').setLevel(logging.DEBUG)
        
        # But keep third-party libraries at INFO level
        for logger_name in third_party_loggers:
            logging.getLogger(logger_name).setLevel(logging.INFO)

def _add_custom_log_methods(logger):
    """Add custom logging methods for financial news bot."""
    
    def log_financial_detection(self, text, is_detected, category=None, score=None):
        """Log financial news detection results."""
        if is_detected:
            msg = f"💰 Financial news detected: {text[:100]}..."
            if category:
                msg += f" | Category: {category}"
            if score is not None:
                msg += f" | Score: {score}"
            self.info(msg)
        else:
            self.debug(f"❌ Not financial news: {text[:50]}...")
    
    def log_approval_workflow(self, action, approval_id, details=None):
        """Log approval workflow actions."""
        emoji_map = {
            'sent': '📤',
            'approved': '✅', 
            'rejected': '🚫',
            'published': '📢',
            'expired': '⏰'
        }
        emoji = emoji_map.get(action, '📋')
        msg = f"{emoji} Approval {action}: {approval_id}"
        if details:
            msg += f" | {details}"
        self.info(msg)
    
    def log_channel_processing(self, channel, processed, total, errors=0):
        """Log channel processing results."""
        msg = f"📺 Channel {channel}: {processed}/{total} processed"
        if errors:
            msg += f", {errors} errors"
        self.info(msg)
    
    def log_statistics(self, stats_dict):
        """Log statistics in a formatted way."""
        self.info("📊 STATISTICS")
        self.info("=" * 40)
        for key, value in stats_dict.items():
            formatted_key = key.replace('_', ' ').title()
            self.info(f"📈 {formatted_key}: {value}")
        self.info("=" * 40)
    
    # Bind methods to logger class
    logging.Logger.log_financial_detection = log_financial_detection
    logging.Logger.log_approval_workflow = log_approval_workflow
    logging.Logger.log_channel_processing = log_channel_processing
    logging.Logger.log_statistics = log_statistics

def setup_debug_logging():
    """Set up debug-level logging with extra verbosity."""
    logger = setup_logging(log_level="DEBUG")
    
    # Add debug-specific configuration
    logger.debug("🐛 Debug logging enabled")
    logger.debug("🔍 Verbose logging for all components")
    
    # Enable telethon debug logging if needed
    if os.getenv("TELETHON_DEBUG", "false").lower() == "true":
        logging.getLogger('telethon').setLevel(logging.DEBUG)
        logger.debug("📡 Telethon debug logging enabled")
    
    return logger

def log_system_info():
    """Log system information for debugging."""
    logger = logging.getLogger(__name__)
    
    try:
        import platform
        import sys
        
        logger.info("🖥️  SYSTEM INFORMATION")
        logger.info("=" * 50)
        logger.info(f"🐍 Python: {sys.version}")
        logger.info(f"💻 Platform: {platform.platform()}")
        logger.info(f"🏗️  Architecture: {platform.architecture()[0]}")
        logger.info(f"📁 Working Directory: {os.getcwd()}")
        logger.info(f"🕐 Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Log environment info
        debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"
        test_mode = os.getenv("TEST_MODE", "false").lower() == "true"
        
        logger.info(f"🐛 Debug Mode: {'Enabled' if debug_mode else 'Disabled'}")
        logger.info(f"🧪 Test Mode: {'Enabled' if test_mode else 'Disabled'}")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.warning(f"Could not log system info: {e}")

def log_startup_banner():
    """Log a startup banner for the Financial News Detector."""
    logger = logging.getLogger(__name__)
    
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║                    FINANCIAL NEWS DETECTOR                    ║
║                                                               ║
║  🏆 Gold • 💱 Currencies • 📈 Iranian Economy • ₿ Crypto    ║
║                                                               ║
║           Automated Financial News Detection System           ║
╚═══════════════════════════════════════════════════════════════╝
    """
    
    for line in banner.strip().split('\n'):
        logger.info(line)

def create_performance_logger():
    """Create a separate logger for performance monitoring."""
    perf_logger = logging.getLogger('performance')
    perf_logger.setLevel(logging.INFO)
    
    # Create performance log file
    perf_log_path = Path("logs/performance.log")
    perf_log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Performance file handler
    perf_handler = logging.handlers.RotatingFileHandler(
        filename=perf_log_path,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=3,
        encoding='utf-8'
    )
    
    perf_formatter = logging.Formatter(
        '%(asctime)s - PERF - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    perf_handler.setFormatter(perf_formatter)
    perf_logger.addHandler(perf_handler)
    
    return perf_logger

def create_audit_logger():
    """Create a separate logger for audit trail (approvals, publications, etc.)."""
    audit_logger = logging.getLogger('audit')
    audit_logger.setLevel(logging.INFO)
    
    # Create audit log file
    audit_log_path = Path("logs/audit.log")
    audit_log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Audit file handler (never rotate audit logs)
    audit_handler = logging.FileHandler(
        filename=audit_log_path,
        encoding='utf-8'
    )
    
    audit_formatter = logging.Formatter(
        '%(asctime)s - AUDIT - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    audit_handler.setFormatter(audit_formatter)
    audit_logger.addHandler(audit_handler)
    
    return audit_logger

def log_environment_variables():
    """Log relevant environment variables (safe for debugging)."""
    logger = logging.getLogger(__name__)
    
    if os.getenv("DEBUG_MODE", "false").lower() != "true":
        return  # Only log in debug mode
    
    safe_env_vars = [
        'LOG_LEVEL', 'DEBUG_MODE', 'TEST_MODE', 'FORCE_24_HOUR_OPERATION',
        'NEWS_CHECK_INTERVAL', 'OPERATION_START_HOUR', 'OPERATION_END_HOUR',
        'ENABLE_ADMIN_APPROVAL', 'MIN_FINANCIAL_SCORE', 'NEWS_CHANNEL',
        'TWITTER_NEWS_CHANNEL', 'TARGET_CHANNEL_ID'
    ]
    
    logger.debug("🔧 ENVIRONMENT CONFIGURATION")
    logger.debug("=" * 40)
    
    for var in safe_env_vars:
        value = os.getenv(var, 'NOT_SET')
        logger.debug(f"⚙️  {var}: {value}")
    
    logger.debug("=" * 40)

def get_log_file_info():
    """Get information about current log files."""
    log_info = []
    
    logs_dir = Path("logs")
    if logs_dir.exists():
        for log_file in logs_dir.glob("*.log"):
            try:
                stat = log_file.stat()
                size_mb = stat.st_size / (1024 * 1024)
                modified = datetime.fromtimestamp(stat.st_mtime)
                
                log_info.append({
                    'file': log_file.name,
                    'size_mb': round(size_mb, 2),
                    'modified': modified.strftime('%Y-%m-%d %H:%M:%S'),
                    'path': str(log_file)
                })
            except Exception as e:
                log_info.append({
                    'file': log_file.name,
                    'error': str(e)
                })
    
    return log_info

def cleanup_old_logs(days_to_keep=30):
    """Clean up log files older than specified days."""
    logger = logging.getLogger(__name__)
    
    try:
        logs_dir = Path("logs")
        if not logs_dir.exists():
            return
        
        from datetime import datetime, timedelta
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        cleaned_count = 0
        for log_file in logs_dir.glob("*.log.*"):  # Rotated log files
            try:
                if datetime.fromtimestamp(log_file.stat().st_mtime) < cutoff_date:
                    log_file.unlink()
                    cleaned_count += 1
            except Exception as e:
                logger.warning(f"Could not clean log file {log_file}: {e}")
        
        if cleaned_count > 0:
            logger.info(f"🧹 Cleaned {cleaned_count} old log files")
            
    except Exception as e:
        logger.error(f"Error cleaning old logs: {e}")

# Initialize performance and audit loggers if needed
def initialize_specialized_loggers():
    """Initialize specialized loggers based on configuration."""
    specialized_loggers = {}
    
    if os.getenv("ENABLE_PERFORMANCE_MONITORING", "false").lower() == "true":
        specialized_loggers['performance'] = create_performance_logger()
    
    if os.getenv("ENABLE_AUDIT_LOGGING", "true").lower() == "true":
        specialized_loggers['audit'] = create_audit_logger()
    
    return specialized_loggers

# Convenience function for quick setup
def quick_setup():
    """Quick logging setup with sensible defaults."""
    logger = setup_logging()
    
    # Log startup information
    if os.getenv("LOG_STARTUP_INFO", "true").lower() == "true":
        log_startup_banner()
        log_system_info()
        log_environment_variables()
    
    # Clean old logs
    if os.getenv("CLEANUP_OLD_LOGS", "true").lower() == "true":
        cleanup_old_logs()
    
    return logger

# Export main functions
__all__ = [
    'setup_logging', 'setup_debug_logging', 'quick_setup',
    'log_system_info', 'log_startup_banner', 'log_environment_variables',
    'create_performance_logger', 'create_audit_logger',
    'get_log_file_info', 'cleanup_old_logs', 'initialize_specialized_loggers'
]