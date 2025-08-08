"""
Complete credentials management for the Financial News Detector.
Loads and validates all required credentials from environment variables.
"""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables from .env file
env_file = Path(".env")
if env_file.exists():
    load_dotenv(env_file)
    logger.debug(f"📁 Loaded environment from {env_file}")
else:
    logger.warning("⚠️  No .env file found, using system environment variables only")

# ============================================================================
# TELEGRAM API CREDENTIALS
# ============================================================================

# Main Telegram API credentials (from my.telegram.org)
API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "")
PHONE_NUMBER = os.getenv("TELEGRAM_PHONE", "")

# ============================================================================
# BOT CREDENTIALS
# ============================================================================

# Main bot token (for publishing news via Bot API)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
BOT_TOKEN = TELEGRAM_BOT_TOKEN  # Alias for compatibility

# Admin bot credentials (for approval workflow)
ADMIN_BOT_TOKEN = os.getenv("ADMIN_BOT_TOKEN", "")
ADMIN_BOT_USERNAME = os.getenv("ADMIN_BOT_USERNAME", "")

# ============================================================================
# CHANNEL CONFIGURATION
# ============================================================================

# Target channel where approved news will be published
TARGET_CHANNEL_ID = os.getenv("TARGET_CHANNEL_ID", "")

# News source channels
NEWS_CHANNEL = os.getenv("NEWS_CHANNEL", "")
TWITTER_NEWS_CHANNEL = os.getenv("TWITTER_NEWS_CHANNEL", "")

# ============================================================================
# CREDENTIAL VALIDATION
# ============================================================================

def validate_credentials():
    """
    Validate that all required credentials are available and properly formatted.
    
    Raises:
        ValueError: If any required credentials are missing or invalid
    """
    missing = []
    invalid = []
    warnings = []

    # ========================================================================
    # TELEGRAM API CREDENTIALS
    # ========================================================================
    
    if API_ID == 0:
        missing.append("TELEGRAM_API_ID")
    elif API_ID < 1000:  # Basic sanity check for Telegram API ID
        invalid.append("TELEGRAM_API_ID (should be a large number from my.telegram.org)")
    
    if not API_HASH:
        missing.append("TELEGRAM_API_HASH")
    elif len(API_HASH) != 32:  # Telegram API hash is always 32 characters
        invalid.append("TELEGRAM_API_HASH (should be 32 characters from my.telegram.org)")
    
    if not PHONE_NUMBER:
        missing.append("TELEGRAM_PHONE")
    elif not PHONE_NUMBER.startswith('+'):
        invalid.append("TELEGRAM_PHONE (should include country code with +)")
    elif len(PHONE_NUMBER) < 10:
        invalid.append("TELEGRAM_PHONE (appears too short)")

    # ========================================================================
    # BOT CREDENTIALS
    # ========================================================================
    
    # Main bot token (optional for news detection, required for publishing)
    if TELEGRAM_BOT_TOKEN and not _is_valid_bot_token(TELEGRAM_BOT_TOKEN):
        invalid.append("TELEGRAM_BOT_TOKEN (should be in format 'ID:HASH' from @BotFather)")
    
    # Admin bot credentials (required for approval workflow)
    if not ADMIN_BOT_TOKEN:
        missing.append("ADMIN_BOT_TOKEN")
    elif not _is_valid_bot_token(ADMIN_BOT_TOKEN):
        invalid.append("ADMIN_BOT_TOKEN (should be in format 'ID:HASH' from @BotFather)")
    
    if not ADMIN_BOT_USERNAME:
        missing.append("ADMIN_BOT_USERNAME")
    elif not _is_valid_username(ADMIN_BOT_USERNAME):
        invalid.append("ADMIN_BOT_USERNAME (should contain only letters, numbers, and underscores)")

    # ========================================================================
    # CHANNEL CONFIGURATION
    # ========================================================================
    
    if not TARGET_CHANNEL_ID:
        missing.append("TARGET_CHANNEL_ID")
    elif not _is_valid_channel_id(TARGET_CHANNEL_ID):
        invalid.append("TARGET_CHANNEL_ID (should be a negative number for channels)")
    
    # News channels (at least one should be configured)
    if not NEWS_CHANNEL and not TWITTER_NEWS_CHANNEL:
        warnings.append("No news channels configured (NEWS_CHANNEL or TWITTER_NEWS_CHANNEL)")

    # ========================================================================
    # REPORT VALIDATION RESULTS
    # ========================================================================
    
    # Critical errors (missing credentials)
    if missing:
        error_msg = f"Missing required credentials: {', '.join(missing)}"
        logger.error(f"❌ {error_msg}")
        raise ValueError(error_msg)
    
    # Format errors (invalid credentials)
    if invalid:
        error_msg = f"Invalid credential format: {', '.join(invalid)}"
        logger.error(f"❌ {error_msg}")
        raise ValueError(error_msg)
    
    # Warnings (non-critical issues)
    if warnings:
        for warning in warnings:
            logger.warning(f"⚠️  {warning}")
    
    logger.info("✅ All credentials validated successfully")
    return True

def _is_valid_bot_token(token):
    """Validate bot token format."""
    if not token:
        return False
    
    # Bot tokens have format: NNNNNNNNNN:XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    # Where N is digits and X is alphanumeric + special chars
    parts = token.split(':')
    if len(parts) != 2:
        return False
    
    bot_id, bot_hash = parts
    
    # Bot ID should be all digits and reasonable length
    if not bot_id.isdigit() or len(bot_id) < 8 or len(bot_id) > 12:
        return False
    
    # Bot hash should be 35 characters (letters, numbers, dashes, underscores)
    if len(bot_hash) != 35:
        return False
    
    allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_')
    if not all(c in allowed_chars for c in bot_hash):
        return False
    
    return True

def _is_valid_username(username):
    """Validate Telegram username format."""
    if not username:
        return False
    
    # Remove @ if present
    username = username.replace('@', '')
    
    # Username should be 5-32 characters, alphanumeric + underscores
    if len(username) < 5 or len(username) > 32:
        return False
    
    # Should start with letter
    if not username[0].isalpha():
        return False
    
    # Should contain only letters, numbers, and underscores
    allowed_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_')
    if not all(c in allowed_chars for c in username):
        return False
    
    return True

def _is_valid_channel_id(channel_id):
    """Validate Telegram channel ID format."""
    if not channel_id:
        return False
    
    try:
        channel_id_int = int(channel_id)
        # Channels have negative IDs, usually starting with -100
        return channel_id_int < 0 and abs(channel_id_int) > 1000000000
    except (ValueError, TypeError):
        return False

def get_credential_info():
    """
    Get information about configured credentials (safe for logging).
    
    Returns:
        dict: Safe credential information for logging/debugging
    """
    def mask_token(token):
        """Mask sensitive parts of tokens."""
        if not token or len(token) < 10:
            return "***"
        return f"{token[:8]}***{token[-4:]}"
    
    def mask_phone(phone):
        """Mask phone number."""
        if not phone or len(phone) < 8:
            return "***"
        return f"{phone[:3]}***{phone[-2:]}"
    
    info = {
        "api_id": f"***{str(API_ID)[-3:]}" if API_ID else "NOT_SET",
        "api_hash": f"{API_HASH[:6]}***" if API_HASH else "NOT_SET",
        "phone": mask_phone(PHONE_NUMBER),
        "main_bot_token": mask_token(TELEGRAM_BOT_TOKEN),
        "admin_bot_token": mask_token(ADMIN_BOT_TOKEN),
        "admin_bot_username": ADMIN_BOT_USERNAME.replace('@', '') if ADMIN_BOT_USERNAME else "NOT_SET",
        "target_channel": TARGET_CHANNEL_ID if TARGET_CHANNEL_ID else "NOT_SET",
        "news_channels": {
            "primary": NEWS_CHANNEL if NEWS_CHANNEL else "NOT_SET",
            "twitter": TWITTER_NEWS_CHANNEL if TWITTER_NEWS_CHANNEL else "NOT_SET"
        }
    }
    
    return info

def check_optional_credentials():
    """
    Check optional credentials and return availability status.
    
    Returns:
        dict: Status of optional features based on available credentials
    """
    features = {
        "bot_api_publishing": bool(TELEGRAM_BOT_TOKEN),
        "admin_approval_workflow": bool(ADMIN_BOT_TOKEN and ADMIN_BOT_USERNAME),
        "primary_news_source": bool(NEWS_CHANNEL),
        "twitter_news_source": bool(TWITTER_NEWS_CHANNEL),
        "target_channel_configured": bool(TARGET_CHANNEL_ID)
    }
    
    return features

def get_missing_optional_credentials():
    """
    Get list of missing optional credentials and their impact.
    
    Returns:
        list: List of missing optional credentials with descriptions
    """
    missing = []
    
    if not TELEGRAM_BOT_TOKEN:
        missing.append({
            "credential": "TELEGRAM_BOT_TOKEN",
            "impact": "Cannot publish approved news automatically via Bot API",
            "required_for": "Auto-publishing feature"
        })
    
    if not NEWS_CHANNEL:
        missing.append({
            "credential": "NEWS_CHANNEL", 
            "impact": "No primary news source configured",
            "required_for": "Primary news monitoring"
        })
    
    if not TWITTER_NEWS_CHANNEL:
        missing.append({
            "credential": "TWITTER_NEWS_CHANNEL",
            "impact": "No Twitter news source configured", 
            "required_for": "Twitter news monitoring"
        })
    
    return missing

def validate_environment():
    """
    Comprehensive environment validation including credentials and dependencies.
    
    Returns:
        dict: Validation results with status and recommendations
    """
    results = {
        "status": "unknown",
        "credentials": {"valid": False, "errors": [], "warnings": []},
        "features": {},
        "recommendations": []
    }
    
    try:
        # Validate credentials
        validate_credentials()
        results["credentials"]["valid"] = True
        results["status"] = "ready"
        
    except ValueError as e:
        results["credentials"]["valid"] = False
        results["credentials"]["errors"].append(str(e))
        results["status"] = "error"
    
    # Check feature availability
    results["features"] = check_optional_credentials()
    
    # Generate recommendations
    missing_optional = get_missing_optional_credentials()
    for item in missing_optional:
        results["recommendations"].append(
            f"Consider setting {item['credential']} for {item['required_for']}"
        )
    
    # Check for common issues
    if API_ID and API_ID < 10000:
        results["credentials"]["warnings"].append(
            "API_ID seems unusually low, verify it's from my.telegram.org"
        )
    
    if PHONE_NUMBER and not PHONE_NUMBER.startswith('+'):
        results["credentials"]["warnings"].append(
            "PHONE_NUMBER should include country code with +"
        )
    
    return results

def log_credential_status():
    """Log the current credential configuration status."""
    try:
        info = get_credential_info()
        features = check_optional_credentials()
        
        logger.info("🔐 CREDENTIAL STATUS SUMMARY")
        logger.info("=" * 50)
        logger.info(f"📱 Telegram API: {'✅ Configured' if API_ID and API_HASH else '❌ Missing'}")
        logger.info(f"📞 Phone Number: {'✅ Set' if PHONE_NUMBER else '❌ Missing'}")
        logger.info(f"🤖 Admin Bot: {'✅ Configured' if features['admin_approval_workflow'] else '❌ Missing'}")
        logger.info(f"📺 Target Channel: {'✅ Set' if features['target_channel_configured'] else '❌ Missing'}")
        logger.info(f"📰 News Sources: {sum([features['primary_news_source'], features['twitter_news_source']])}/2 configured")
        logger.info(f"🚀 Bot API: {'✅ Available' if features['bot_api_publishing'] else '⚠️  Not configured'}")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"Error logging credential status: {e}")

# ============================================================================
# INITIALIZATION
# ============================================================================

# Log credential status when module is imported (in development/debug mode)
if os.getenv("DEBUG_MODE", "false").lower() == "true":
    try:
        log_credential_status()
    except Exception as e:
        logger.warning(f"Could not log credential status: {e}")

# Export main credentials for easy access
__all__ = [
    'API_ID', 'API_HASH', 'PHONE_NUMBER', 
    'TELEGRAM_BOT_TOKEN', 'BOT_TOKEN',
    'ADMIN_BOT_TOKEN', 'ADMIN_BOT_USERNAME',
    'TARGET_CHANNEL_ID', 'NEWS_CHANNEL', 'TWITTER_NEWS_CHANNEL',
    'validate_credentials', 'get_credential_info', 'check_optional_credentials',
    'validate_environment', 'log_credential_status'
]