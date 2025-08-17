"""
Complete time utilities for the Financial News Detector.
Handles timezone conversion, operating hours, Persian calendar, and time formatting.
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

# Operating hours (Support both new and old format)
OPERATION_START_HOUR = int(os.getenv("OPERATION_START_HOUR", "8"))
OPERATION_START_MINUTE = int(os.getenv("OPERATION_START_MINUTE", "30"))
OPERATION_END_HOUR = int(os.getenv("OPERATION_END_HOUR", "22"))
OPERATION_END_MINUTE = int(os.getenv("OPERATION_END_MINUTE", "0"))

# Force 24-hour operation flag
FORCE_24_HOUR = os.getenv("FORCE_24_HOUR_OPERATION", "false").lower() == "true"

# ============================================================================
# PERSIAN CALENDAR UTILITIES
# ============================================================================

def gregorian_to_persian(gregorian_date):
    """
    Convert Gregorian date to Persian/Solar Hijri calendar.
    
    Args:
        gregorian_date: datetime object in Gregorian calendar
        
    Returns:
        tuple: (persian_year, persian_month, persian_day)
    """
    # Persian calendar conversion algorithm
    # Based on Kazimierz M. Borkowski algorithm
    
    gy = gregorian_date.year
    gm = gregorian_date.month
    gd = gregorian_date.day
    
    if gy < 1600:
        jy = 0
        gy -= 621
    else:
        jy = 979
        gy -= 1600
    
    if gm > 2:
        gy2 = gy + 1
    else:
        gy2 = gy
    
    days = (365 * gy) + ((gy2 + 3) // 4) - ((gy2 + 99) // 100) + ((gy2 + 399) // 400) - 80 + gd
    
    if gm > 2:
        days += sum([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][:gm-1])
        if ((gy % 4 == 0) and (gy % 100 != 0)) or (gy % 400 == 0):
            days += 1
    else:
        days += sum([31, 28][:gm-1])
    
    jy += 33 * (days // 12053)
    days %= 12053
    
    jy += 4 * (days // 1461)
    days %= 1461
    
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    
    if days < 186:
        jm = 1 + days // 31
        jd = 1 + (days % 31)
    else:
        jm = 7 + (days - 186) // 30
        jd = 1 + ((days - 186) % 30)
    
    return (jy, jm, jd)

def format_persian_date(dt):
    """
    Format datetime as Persian calendar date.
    
    Args:
        dt: datetime object
        
    Returns:
        str: Persian date in format YYYY-MM-DD
    """
    if dt is None:
        return ""
    
    # Ensure Tehran timezone
    if dt.tzinfo != TEHRAN_TZ:
        dt = convert_to_tehran(dt)
    
    persian_year, persian_month, persian_day = gregorian_to_persian(dt)
    return f"{persian_year:04d}-{persian_month:02d}-{persian_day:02d}"

def format_persian_time(dt):
    """
    Format time in HH:MM format (without seconds).
    
    Args:
        dt: datetime object
        
    Returns:
        str: Time in HH:MM format
    """
    if dt is None:
        return ""
    
    # Ensure Tehran timezone
    if dt.tzinfo != TEHRAN_TZ:
        dt = convert_to_tehran(dt)
    
    return dt.strftime("%H:%M")

def format_persian_datetime(dt):
    """
    Format datetime in Persian calendar with HH:MM time.
    
    Args:
        dt: datetime object
        
    Returns:
        str: Persian datetime in format YYYY-MM-DD HH:MM
    """
    if dt is None:
        return ""
    
    persian_date = format_persian_date(dt)
    persian_time = format_persian_time(dt)
    
    return f"{persian_date} {persian_time}"

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
# OPERATING HOURS FUNCTIONS (UPDATED)
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
    current_minute = current_time.minute
    
    # Convert current time to minutes since midnight
    current_minutes = current_hour * 60 + current_minute
    
    # Operating hours in minutes since midnight
    start_minutes = OPERATION_START_HOUR * 60 + OPERATION_START_MINUTE
    end_minutes = OPERATION_END_HOUR * 60 + OPERATION_END_MINUTE
    
    # Check if within operating hours
    return start_minutes <= current_minutes < end_minutes

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
    current_minute = current_time.minute
    current_minutes = current_hour * 60 + current_minute
    
    start_minutes = OPERATION_START_HOUR * 60 + OPERATION_START_MINUTE
    
    # If currently in operating hours, return current time
    if is_operating_hours(current_time):
        return current_time
    
    # Calculate next operating time
    if current_minutes < start_minutes:
        # Same day
        next_operating = current_time.replace(
            hour=OPERATION_START_HOUR, 
            minute=OPERATION_START_MINUTE, 
            second=0, 
            microsecond=0
        )
    else:
        # Next day
        next_day = current_time + timedelta(days=1)
        next_operating = next_day.replace(
            hour=OPERATION_START_HOUR,
            minute=OPERATION_START_MINUTE,
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
        return next_start.replace(
            hour=OPERATION_END_HOUR,
            minute=OPERATION_END_MINUTE
        )
    
    # Current operating period end
    return current_time.replace(
        hour=OPERATION_END_HOUR,
        minute=OPERATION_END_MINUTE,
        second=0,
        microsecond=0
    )

# ============================================================================
# FORMATTING FUNCTIONS (UPDATED)
# ============================================================================

def get_formatted_time(dt=None, format_type="persian_full"):
    """
    Get formatted time string with Persian calendar support.
    
    Args:
        dt: datetime to format (default: current time)
        format_type: Type of formatting
        
    Returns:
        str: Formatted time string
    """
    if dt is None:
        dt = get_current_time()
    
    # Ensure Tehran timezone
    if dt.tzinfo != TEHRAN_TZ:
        dt = convert_to_tehran(dt)
    
    formats = {
        "persian_full": lambda d: format_persian_datetime(d),  # 1403-05-24 12:53
        "persian_date": lambda d: format_persian_date(d),     # 1403-05-24
        "persian_time": lambda d: format_persian_time(d),     # 12:53
        "full": "%Y-%m-%d %H:%M:%S %Z",
        "short": "%Y-%m-%d %H:%M",
        "date": "%Y-%m-%d",
        "time": "%H:%M:%S",
        "iso": "%Y-%m-%dT%H:%M:%S%z",
        "log": "%Y-%m-%d %H:%M:%S",
        "filename": "%Y%m%d_%H%M%S"
    }
    
    format_func = formats.get(format_type)
    if callable(format_func):
        return format_func(dt)
    else:
        return dt.strftime(format_func)

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
        "current_time": get_formatted_time(current_time, "persian_full"),
        "current_time_gregorian": get_formatted_time(current_time, "full"),
        "is_operating": is_operating_hours(current_time),
        "is_business_day": is_business_day(current_time),
        "is_weekend": is_weekend(current_time),
        "force_24h": FORCE_24_HOUR,
        "operating_hours": f"{OPERATION_START_HOUR:02d}:{OPERATION_START_MINUTE:02d} - {OPERATION_END_HOUR:02d}:{OPERATION_END_MINUTE:02d} Tehran",
    }
    
    if status["is_operating"]:
        end_time = get_operating_end_time()
        time_left = end_time - current_time if end_time > current_time else None
        status["operation_ends_at"] = get_formatted_time(end_time, "persian_full")
        status["time_until_end"] = format_duration(time_left) if time_left else "Now"
    else:
        next_time = get_next_operating_time()
        time_until = next_time - current_time if next_time > current_time else None
        status["next_operation_at"] = get_formatted_time(next_time, "persian_full")
        status["time_until_start"] = format_duration(time_until) if time_until else "Now"
    
    return status

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

# ============================================================================
# MESSAGE TIMESTAMP FUNCTIONS
# ============================================================================

def add_timestamp_to_message(message, timestamp_format="persian_full"):
    """
    Add timestamp to a message in Persian calendar format.
    
    Args:
        message: Message text
        timestamp_format: Format for timestamp
        
    Returns:
        str: Message with timestamp
    """
    timestamp = get_formatted_time(format_type=timestamp_format)
    return f"{message}\n🕐 {timestamp}"

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
        return 900  # 15 minutes during operations (15 * 60)
    
    next_time = get_next_operating_time()
    current_time = get_current_time()
    
    if next_time <= current_time:
        return 60
    
    time_until = next_time - current_time
    
    # Don't sleep more than 15 minutes
    seconds = min(int(time_until.total_seconds()), 900)
    return max(seconds, 60)  # At least 1 minute

def log_time_status():
    """Log current time status for debugging."""
    status = get_business_hours_status()
    
    logger.info("🕐 TIME STATUS")
    logger.info("=" * 40)
    logger.info(f"Persian Time: {status['current_time']}")
    logger.info(f"Gregorian Time: {status['current_time_gregorian']}")
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

# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    # Core functions
    'get_current_time', 'get_utc_time', 'convert_to_tehran', 'convert_to_utc',
    'timestamp_to_tehran', 'tehran_to_timestamp',
    
    # Persian calendar
    'gregorian_to_persian', 'format_persian_date', 'format_persian_time', 'format_persian_datetime',
    
    # Operating hours
    'is_operating_hours', 'get_next_operating_time', 'get_operating_end_time',
    
    # Formatting
    'get_formatted_time', 'format_duration',
    
    # Business functions
    'is_weekend', 'is_business_day', 'get_business_hours_status',
    
    # Message functions
    'add_timestamp_to_message',
    
    # Utilities
    'sleep_until_next_operation', 'log_time_status',
    
    # Constants
    'TEHRAN_TZ', 'UTC_TZ', 'OPERATION_START_HOUR', 'OPERATION_START_MINUTE', 
    'OPERATION_END_HOUR', 'OPERATION_END_MINUTE'
]