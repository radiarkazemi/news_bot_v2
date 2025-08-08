"""
Complete time utilities for the Financial News Detector.
Handles timezone conversion, operating hours, and time formatting.
"""
import pytz
from datetime import datetime, timedelta
import os
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# TIMEZONE CONFIGURATION
# ============================================================================

# Tehran timezone (Iran Standard Time)
TEHRAN_TZ = pytz.timezone('Asia/Tehran')
UTC_TZ = pytz.UTC

# Operating hours (from environment or defaults)
OPERATION_START_HOUR = int(os.getenv("OPERATION_START_HOUR", "9"))
OPERATION_END_HOUR = int(os.getenv("OPERATION_END_HOUR", "22"))

# Force 24-hour operation flag
FORCE_24_HOUR = os.getenv("FORCE_24_HOUR_OPERATION", "false").lower() == "true"

# ============================================================================
# CORE TIME FUNCTIONS
# ============================================================================

def get_current_time():
    """
    Get current time in Tehran timezone.
    
    Returns:
        datetime: Current time in Tehran timezone
    """
    return datetime.now(TEHRAN_TZ)

def get_utc_time():
    """
    Get current UTC time.
    
    Returns:
        datetime: Current time in UTC
    """
    return datetime.now(UTC_TZ)

def convert_to_tehran(dt):
    """
    Convert datetime to Tehran timezone.
    
    Args:
        dt: datetime object (can be naive or aware)
        
    Returns:
        datetime: datetime in Tehran timezone
    """
    if dt is None:
        return None
    
    # If naive, assume UTC
    if dt.tzinfo is None:
        dt = UTC_TZ.localize(dt)
    
    # Convert to Tehran time
    return dt.astimezone(TEHRAN_TZ)

def convert_to_utc(dt):
    """
    Convert datetime to UTC.
    
    Args:
        dt: datetime object (can be naive or aware)
        
    Returns:
        datetime: datetime in UTC
    """
    if dt is None:
        return None
    
    # If naive, assume Tehran time
    if dt.tzinfo is None:
        dt = TEHRAN_TZ.localize(dt)
    
    # Convert to UTC
    return dt.astimezone(UTC_TZ)

def timestamp_to_tehran(timestamp):
    """
    Convert Unix timestamp to Tehran time.
    
    Args:
        timestamp: Unix timestamp (seconds since epoch)
        
    Returns:
        datetime: datetime in Tehran timezone
    """
    if timestamp is None:
        return None
    
    # Create UTC datetime from timestamp
    utc_dt = datetime.fromtimestamp(timestamp, tz=UTC_TZ)
    
    # Convert to Tehran time
    return utc_dt.astimezone(TEHRAN_TZ)

def tehran_to_timestamp(dt):
    """
    Convert Tehran datetime to Unix timestamp.
    
    Args:
        dt: datetime object in Tehran timezone
        
    Returns:
        float: Unix timestamp
    """
    if dt is None:
        return None
    
    # Ensure it's in Tehran timezone
    if dt.tzinfo is None:
        dt = TEHRAN_TZ.localize(dt)
    elif dt.tzinfo != TEHRAN_TZ:
        dt = dt.astimezone(TEHRAN_TZ)
    
    return dt.timestamp()

# ============================================================================
# OPERATING HOURS FUNCTIONS
# ============================================================================

def is_operating_hours(current_time=None):
    """
    Check if current time is within operating hours.
    
    Args:
        current_time: datetime to check (default: current time)
        
    Returns:
        bool: True if within operating hours
    """
    # If force 24-hour mode is enabled, always return True
    if FORCE_24_HOUR:
        return True
    
    if current_time is None:
        current_time = get_current_time()
    
    # Ensure we're working with Tehran time
    if current_time.tzinfo != TEHRAN_TZ:
        current_time = convert_to_tehran(current_time)
    
    current_hour = current_time.hour
    
    # Check if within operating hours
    return OPERATION_START_HOUR <= current_hour < OPERATION_END_HOUR

def get_next_operating_time():
    """
    Get the next time when operations should start.
    
    Returns:
        datetime: Next operating time in Tehran timezone
    """
    if FORCE_24_HOUR:
        return get_current_time()  # Always operating
    
    current_time = get_current_time()
    current_hour = current_time.hour
    
    # If currently in operating hours, return current time
    if is_operating_hours(current_time):
        return current_time
    
    # Calculate next operating time
    if current_hour < OPERATION_START_HOUR:
        # Same day
        next_operating = current_time.replace(
            hour=OPERATION_START_HOUR, 
            minute=0, 
            second=0, 
            microsecond=0
        )
    else:
        # Next day
        next_day = current_time + timedelta(days=1)
        next_operating = next_day.replace(
            hour=OPERATION_START_HOUR,
            minute=0,
            second=0,
            microsecond=0
        )
    
    return next_operating

def get_operating_end_time():
    """
    Get the end time of current operating period.
    
    Returns:
        datetime: End time of current operating period
    """
    if FORCE_24_HOUR:
        return get_current_time() + timedelta(days=1)  # Never ends
    
    current_time = get_current_time()
    
    # If not in operating hours, get next operating period end
    if not is_operating_hours(current_time):
        next_start = get_next_operating_time()
        return next_start.replace(hour=OPERATION_END_HOUR)
    
    # Current operating period end
    return current_time.replace(
        hour=OPERATION_END_HOUR,
        minute=0,
        second=0,
        microsecond=0
    )

def time_until_next_operation():
    """
    Get time remaining until next operation starts.
    
    Returns:
        timedelta: Time until next operation, or None if currently operating
    """
    if is_operating_hours():
        return None  # Currently operating
    
    current_time = get_current_time()
    next_time = get_next_operating_time()
    
    return next_time - current_time

def time_until_operation_ends():
    """
    Get time remaining until current operation ends.
    
    Returns:
        timedelta: Time until operation ends, or None if not operating
    """
    if not is_operating_hours():
        return None  # Not currently operating
    
    current_time = get_current_time()
    end_time = get_operating_end_time()
    
    return end_time - current_time

# ============================================================================
# FORMATTING FUNCTIONS
# ============================================================================

def get_formatted_time(dt=None, format_type="full"):
    """
    Get formatted time string.
    
    Args:
        dt: datetime to format (default: current time)
        format_type: Type of formatting ("full", "short", "date", "time", "iso")
        
    Returns:
        str: Formatted time string
    """
    if dt is None:
        dt = get_current_time()
    
    # Ensure Tehran timezone
    if dt.tzinfo != TEHRAN_TZ:
        dt = convert_to_tehran(dt)
    
    formats = {
        "full": "%Y-%m-%d %H:%M:%S %Z",
        "short": "%Y-%m-%d %H:%M",
        "date": "%Y-%m-%d",
        "time": "%H:%M:%S",
        "iso": "%Y-%m-%dT%H:%M:%S%z",
        "persian_date": "%Y/%m/%d",
        "persian_time": "%H:%M",
        "log": "%Y-%m-%d %H:%M:%S",
        "filename": "%Y%m%d_%H%M%S"
    }
    
    return dt.strftime(formats.get(format_type, formats["full"]))

def format_duration(td):
    """
    Format timedelta as human-readable string.
    
    Args:
        td: timedelta object
        
    Returns:
        str: Human-readable duration string
    """
    if td is None:
        return "Unknown"
    
    total_seconds = int(td.total_seconds())
    
    if total_seconds < 0:
        return "Past"
    
    # Calculate components
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    # Build string
    parts = []
    
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds > 0 and days == 0:  # Only show seconds if less than a day
        parts.append(f"{seconds}s")
    
    if not parts:
        return "0s"
    
    return " ".join(parts)

def format_relative_time(dt):
    """
    Format datetime as relative time (e.g., "2 hours ago", "in 30 minutes").
    
    Args:
        dt: datetime to format
        
    Returns:
        str: Relative time string
    """
    if dt is None:
        return "Unknown time"
    
    current = get_current_time()
    
    # Ensure both are in Tehran timezone
    if dt.tzinfo != TEHRAN_TZ:
        dt = convert_to_tehran(dt)
    
    diff = current - dt
    total_seconds = diff.total_seconds()
    
    # Future time
    if total_seconds < 0:
        future_diff = dt - current
        return f"in {format_duration(future_diff)}"
    
    # Past time
    if total_seconds < 60:
        return "just now"
    elif total_seconds < 3600:
        minutes = int(total_seconds // 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif total_seconds < 86400:
        hours = int(total_seconds // 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    else:
        days = int(total_seconds // 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"

# ============================================================================
# BUSINESS TIME FUNCTIONS
# ============================================================================

def is_weekend(dt=None):
    """
    Check if given date is weekend (Friday in Iran).
    
    Args:
        dt: datetime to check (default: current time)
        
    Returns:
        bool: True if weekend
    """
    if dt is None:
        dt = get_current_time()
    
    # Ensure Tehran timezone
    if dt.tzinfo != TEHRAN_TZ:
        dt = convert_to_tehran(dt)
    
    # In Iran, Friday is weekend (weekday 4, where Monday is 0)
    return dt.weekday() == 4

def is_business_day(dt=None):
    """
    Check if given date is a business day.
    
    Args:
        dt: datetime to check (default: current time)
        
    Returns:
        bool: True if business day
    """
    return not is_weekend(dt)

def get_business_hours_status():
    """
    Get comprehensive status of business/operating hours.
    
    Returns:
        dict: Status information
    """
    current_time = get_current_time()
    
    status = {
        "current_time": get_formatted_time(current_time),
        "is_operating": is_operating_hours(current_time),
        "is_business_day": is_business_day(current_time),
        "is_weekend": is_weekend(current_time),
        "force_24h": FORCE_24_HOUR,
        "operating_hours": f"{OPERATION_START_HOUR:02d}:00 - {OPERATION_END_HOUR:02d}:00 Tehran",
    }
    
    if status["is_operating"]:
        end_time = get_operating_end_time()
        time_left = time_until_operation_ends()
        status["operation_ends_at"] = get_formatted_time(end_time)
        status["time_until_end"] = format_duration(time_left) if time_left else "Unknown"
    else:
        next_time = get_next_operating_time()
        time_until = time_until_next_operation()
        status["next_operation_at"] = get_formatted_time(next_time)
        status["time_until_start"] = format_duration(time_until) if time_until else "Unknown"
    
    return status

# ============================================================================
# MESSAGE TIMESTAMP FUNCTIONS
# ============================================================================

def add_timestamp_to_message(message, timestamp_format="short"):
    """
    Add timestamp to a message.
    
    Args:
        message: Message text
        timestamp_format: Format for timestamp
        
    Returns:
        str: Message with timestamp
    """
    timestamp = get_formatted_time(format_type=timestamp_format)
    return f"{message}\n🕐 {timestamp}"

def extract_timestamp_from_message(message):
    """
    Extract timestamp from a message (if present).
    
    Args:
        message: Message text
        
    Returns:
        datetime or None: Extracted timestamp
    """
    import re
    
    # Look for timestamp pattern
    patterns = [
        r'🕐 (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})',
        r'🕐 (\d{4}-\d{2}-\d{2} \d{2}:\d{2})',
        r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, message)
        if match:
            try:
                time_str = match.group(1)
                # Try different formats
                for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"]:
                    try:
                        dt = datetime.strptime(time_str, fmt)
                        return TEHRAN_TZ.localize(dt)
                    except ValueError:
                        continue
            except Exception:
                continue
    
    return None

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def sleep_until_next_operation():
    """
    Calculate how long to sleep until next operation starts.
    
    Returns:
        int: Seconds to sleep (max 15 minutes if not operating)
    """
    if is_operating_hours():
        return 60  # Check every minute during operations
    
    time_until = time_until_next_operation()
    if time_until is None:
        return 60
    
    # Don't sleep more than 15 minutes
    seconds = min(int(time_until.total_seconds()), 900)
    return max(seconds, 60)  # At least 1 minute

def log_time_status():
    """Log current time status for debugging."""
    status = get_business_hours_status()
    
    logger.info("🕐 TIME STATUS")
    logger.info("=" * 40)
    logger.info(f"Current Time: {status['current_time']}")
    logger.info(f"Operating: {'✅ Yes' if status['is_operating'] else '❌ No'}")
    logger.info(f"Business Day: {'✅ Yes' if status['is_business_day'] else '❌ No (Weekend)'}")
    logger.info(f"24h Mode: {'✅ Enabled' if status['force_24h'] else '❌ Disabled'}")
    logger.info(f"Operating Hours: {status['operating_hours']}")
    
    if status['is_operating']:
        logger.info(f"Ends At: {status.get('operation_ends_at', 'Unknown')}")
        logger.info(f"Time Left: {status.get('time_until_end', 'Unknown')}")
    else:
        logger.info(f"Next Start: {status.get('next_operation_at', 'Unknown')}")
        logger.info(f"Time Until: {status.get('time_until_start', 'Unknown')}")
    
    logger.info("=" * 40)

def create_time_report():
    """Create a comprehensive time report."""
    current = get_current_time()
    
    report = {
        "timestamp": get_formatted_time(current, "iso"),
        "tehran_time": get_formatted_time(current, "full"),
        "utc_time": get_formatted_time(get_utc_time(), "full"),
        "status": get_business_hours_status(),
        "timezone_info": {
            "tehran_offset": current.strftime("%z"),
            "tehran_dst": current.dst() != timedelta(0),
        }
    }
    
    return report

# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    # Core functions
    'get_current_time', 'get_utc_time', 'convert_to_tehran', 'convert_to_utc',
    'timestamp_to_tehran', 'tehran_to_timestamp',
    
    # Operating hours
    'is_operating_hours', 'get_next_operating_time', 'get_operating_end_time',
    'time_until_next_operation', 'time_until_operation_ends',
    
    # Formatting
    'get_formatted_time', 'format_duration', 'format_relative_time',
    
    # Business functions
    'is_weekend', 'is_business_day', 'get_business_hours_status',
    
    # Message functions
    'add_timestamp_to_message', 'extract_timestamp_from_message',
    
    # Utilities
    'sleep_until_next_operation', 'log_time_status', 'create_time_report',
    
    # Constants
    'TEHRAN_TZ', 'UTC_TZ', 'OPERATION_START_HOUR', 'OPERATION_END_HOUR'
]