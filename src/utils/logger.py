"""
Enhanced logging setup for the News Detector.
"""
import logging
import logging.handlers
import sys
from pathlib import Path

try:
    from config.settings import LOG_LEVEL, LOG_FILE_PATH, MAX_LOG_SIZE_MB, LOG_BACKUP_COUNT, VERBOSE_LOGGING
except ImportError:
    # Fallback values if settings not available
    LOG_LEVEL = "INFO"
    LOG_FILE_PATH = "./logs/news_detector.log"
    MAX_LOG_SIZE_MB = 50
    LOG_BACKUP_COUNT = 5
    VERBOSE_LOGGING = False


def setup_logging():
    """Set up enhanced logging configuration."""
    # Create logs directory
    log_file = Path(LOG_FILE_PATH)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    
    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatters
    if VERBOSE_LOGGING:
        console_format = '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        file_format = '%(asctime)s - %(name)s - %(levelname)s - %(module)s.%(funcName)s:%(lineno)d - %(message)s'
    else:
        console_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        file_format = '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    
    console_formatter = logging.Formatter(console_format)
    file_formatter = logging.Formatter(file_format)
    
    # Console handler with color support
    console_handler = ColoredConsoleHandler()
    console_handler.setFormatter(console_formatter)
    
    # Set console level (can be different from file level)
    console_level = LOG_LEVEL
    if LOG_LEVEL == "DEBUG":
        console_level = "INFO"  # Reduce console noise in debug mode
    console_handler.setLevel(getattr(logging, console_level, logging.INFO))
    
    logger.addHandler(console_handler)
    
    # File handler with rotation
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=MAX_LOG_SIZE_MB * 1024 * 1024,
            backupCount=LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
        logger.addHandler(file_handler)
        
        logger.info(f"📁 Log file: {log_file}")
        
    except Exception as e:
        print(f"Warning: Could not set up file logging: {e}")
        # Continue with console logging only
    
    # Add custom log level for news events
    logging.addLevelName(25, "NEWS")
    
    def news(self, message, *args, **kwargs):
        if self.isEnabledFor(25):
            self._log(25, message, args, **kwargs)
    
    logging.Logger.news = news
    
    # Set up third-party library log levels to reduce noise
    logging.getLogger('telethon').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    
    logger.info("🚀 Logging system initialized")
    logger.info(f"📊 Log level: {LOG_LEVEL}")
    logger.info(f"📁 Log file: {log_file}")
    
    return logger


class ColoredConsoleHandler(logging.StreamHandler):
    """Console handler with color support for different log levels."""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green  
        'NEWS': '\033[35m',     # Magenta
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[41m', # Red background
        'RESET': '\033[0m'      # Reset
    }
    
    def __init__(self):
        super().__init__(sys.stdout)
        # Check if terminal supports colors
        self.use_colors = (
            hasattr(sys.stdout, 'isatty') and 
            sys.stdout.isatty() and 
            sys.platform != 'win32'  # Basic Windows check
        )
    
    def format(self, record):
        """Format log record with colors."""
        formatted = super().format(record)
        
        if self.use_colors and record.levelname in self.COLORS:
            color = self.COLORS[record.levelname]
            reset = self.COLORS['RESET']
            
            # Color just the level name
            formatted = formatted.replace(
                f" - {record.levelname} - ",
                f" - {color}{record.levelname}{reset} - "
            )
        
        return formatted


def get_logger(name):
    """Get a logger with the specified name."""
    return logging.getLogger(name)


def log_news_event(message, level="NEWS"):
    """Log a news-specific event."""
    logger = logging.getLogger("news_detector")
    
    if level == "NEWS":
        logger.log(25, f"📰 {message}")
    elif level == "APPROVAL":
        logger.info(f"👨‍💼 {message}")
    elif level == "PUBLISH":
        logger.info(f"📢 {message}")
    elif level == "FILTER":
        logger.debug(f"🔍 {message}")
    else:
        logger.info(message)


def log_statistics(stats_dict):
    """Log statistics in a formatted way."""
    logger = logging.getLogger("news_detector.stats")
    
    logger.info("📊 Current Statistics:")
    for key, value in stats_dict.items():
        if isinstance(value, float):
            logger.info(f"   {key}: {value:.2f}")
        else:
            logger.info(f"   {key}: {value}")


def setup_debug_logging():
    """Set up debug-level logging for troubleshooting."""
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # Enable debug for Telethon as well
    logging.getLogger('telethon').setLevel(logging.DEBUG)
    
    logger.debug("🔍 Debug logging enabled")


def log_system_info():
    """Log system information at startup."""
    import platform
    import sys
    
    logger = logging.getLogger("news_detector")
    
    logger.info("🖥️  System Information:")
    logger.info(f"   Python: {sys.version.split()[0]}")
    logger.info(f"   Platform: {platform.system()} {platform.release()}")
    logger.info(f"   Architecture: {platform.machine()}")
    
    # Log package versions if available
    try:
        import telethon
        logger.info(f"   Telethon: {telethon.__version__}")
    except:
        pass
    
    try:
        import requests
        logger.info(f"   Requests: {requests.__version__}")
    except:
        pass