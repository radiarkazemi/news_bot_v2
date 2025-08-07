"""
Enhanced time utilities for operating hours and timezone handling.
"""
import pytz
from datetime import datetime

try:
    from config.settings import TEHRAN_TZ, OPERATION_START_HOUR, OPERATION_END_HOUR
except ImportError:
    # Fallback values if settings not available
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


def get_time_until_operating_hours():
    """Get time remaining until next operating period."""
    current_time = get_current_time()
    current_hour = current_time.hour
    
    if is_operating_hours():
        # Calculate time until end of operating hours
        end_today = current_time.replace(hour=OPERATION_END_HOUR, minute=0, second=0, microsecond=0)
        if current_time < end_today:
            return (end_today - current_time).total_seconds()
        else:
            # Should not happen if is_operating_hours() returned True
            return 0
    else:
        # Calculate time until start of operating hours
        if current_hour < OPERATION_START_HOUR:
            # Start is today
            start_today = current_time.replace(hour=OPERATION_START_HOUR, minute=0, second=0, microsecond=0)
            return (start_today - current_time).total_seconds()
        else:
            # Start is tomorrow
            from datetime import timedelta
            start_tomorrow = (current_time + timedelta(days=1)).replace(
                hour=OPERATION_START_HOUR, minute=0, second=0, microsecond=0
            )
            return (start_tomorrow - current_time).total_seconds()


def format_duration(seconds):
    """Format duration in seconds to human-readable string."""
    if seconds < 60:
        return f"{int(seconds)} seconds"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        return f"{minutes} minutes"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        if minutes > 0:
            return f"{hours} hours, {minutes} minutes"
        else:
            return f"{hours} hours"


def is_weekend():
    """Check if current day is weekend (Friday or Saturday in Iran)."""
    current_time = get_current_time()
    weekday = current_time.weekday()
    # In Iran: Friday (4) and Saturday (5) are weekend
    return weekday in [4, 5]


def get_tehran_now_iso():
    """Get current Tehran time in ISO format."""
    return get_current_time().isoformat()


def parse_tehran_time(time_str):
    """Parse time string assuming Tehran timezone."""
    try:
        # Try different formats
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%H:%M:%S",
            "%H:%M"
        ]
        
        for fmt in formats:
            try:
                parsed = datetime.strptime(time_str, fmt)
                # If no date provided, use today
                if fmt in ["%H:%M:%S", "%H:%M"]:
                    today = get_current_time().date()
                    parsed = parsed.replace(year=today.year, month=today.month, day=today.day)
                
                # Localize to Tehran timezone
                localized = TEHRAN_TZ.localize(parsed)
                return localized
            except ValueError:
                continue
        
        raise ValueError(f"Could not parse time string: {time_str}")
        
    except Exception as e:
        logger.error(f"Error parsing time string '{time_str}': {e}")
        return None


def get_operating_hours_info():
    """Get information about operating hours."""
    current_time = get_current_time()
    is_operating = is_operating_hours()
    
    info = {
        'current_time': get_formatted_time(current_time),
        'current_hour': current_time.hour,
        'is_operating': is_operating,
        'operation_start': OPERATION_START_HOUR,
        'operation_end': OPERATION_END_HOUR,
        'is_weekend': is_weekend()
    }
    
    if is_operating:
        info['time_until_end'] = get_time_until_operating_hours()
        info['status'] = 'ACTIVE'
    else:
        info['time_until_start'] = get_time_until_operating_hours()
        info['status'] = 'INACTIVE'
    
    return info