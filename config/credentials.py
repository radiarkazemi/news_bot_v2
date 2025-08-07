"""
Enhanced credentials management for the News Detector.
Loads configuration from environment variables with validation.
"""
import os
import logging
from dotenv import load_dotenv
from pathlib import Path

logger = logging.getLogger(__name__)

# Load environment variables from .env file
env_file = Path(".env")
if env_file.exists():
    load_dotenv()
    logger.debug(f"📁 Loaded environment from {env_file}")
else:
    logger.warning("⚠️  No .env file found, using system environment variables only")

# Telegram API credentials
API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "")
PHONE_NUMBER = os.getenv("TELEGRAM_PHONE", "")

# Admin bot credentials
ADMIN_BOT_TOKEN = os.getenv("ADMIN_BOT_TOKEN", "")
ADMIN_BOT_USERNAME = os.getenv("ADMIN_BOT_USERNAME", "")

# Optional: Main bot token (if needed for certain operations)
MAIN_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")


def validate_credentials():
    """Validate that all required credentials are available."""
    missing = []
    invalid = []

    # Check required credentials
    if API_ID == 0:
        missing.append("TELEGRAM_API_ID")
    elif API_ID < 1000:  # Basic sanity check
        invalid.append("TELEGRAM_API_ID (should be a large number from my.telegram.org)")
    
    if not API_HASH:
        missing.append("TELEGRAM_API_HASH")
    elif len(API_HASH) != 32:  # Telegram API hash is always 32 characters
        invalid.append("TELEGRAM_API_HASH (should be 32 characters from my.telegram.org)")
    
    if not PHONE_NUMBER:
        missing.append("TELEGRAM_PHONE")
    elif not PHONE_NUMBER.startswith('+'):
        invalid.append("TELEGRAM_PHONE (should include country code with +)")
    
    if not ADMIN_BOT_TOKEN:
        missing.append("ADMIN_BOT_TOKEN")
    elif not ADMIN_BOT_TOKEN.count(':') == 1:  # Bot tokens have format: ID:HASH
        invalid.append("ADMIN_BOT_TOKEN (should be in format 'ID:HASH' from @BotFather)")
    
    if not ADMIN_BOT_USERNAME:
        missing.append("ADMIN_BOT_USERNAME")
    elif not ADMIN_BOT_USERNAME.isalnum():  # Basic username validation
        invalid.append("ADMIN_BOT_USERNAME (should contain only letters and numbers)")

    # Report issues
    if missing:
        error_msg = f"Missing required credentials: {', '.join(missing)}"
        logger.error(f"❌ {error_msg}")
        raise ValueError(error_msg)
    
    if invalid:
        error_msg = f"Invalid credential format: {', '.join(invalid)}"
        logger.error(f"❌ {error_msg}")
        raise ValueError(error_msg)
    
    logger.info("✅ All credentials validated successfully")


def get_credential_info():
    """Get information about configured credentials (safe for logging)."""
    info = {
        'api_id_configured': API_ID != 0,
        'api_hash_configured': bool(API_HASH),
        'phone_configured': bool(PHONE_NUMBER),
        'admin_bot_token_configured': bool(ADMIN_BOT_TOKEN),
        'admin_bot_username_configured': bool(ADMIN_BOT_USERNAME),
        'main_bot_token_configured': bool(MAIN_BOT_TOKEN)
    }
    
    # Add safe partial information for debugging
    if PHONE_NUMBER:
        info['phone_country_code'] = PHONE_NUMBER[:3] if PHONE_NUMBER.startswith('+') else 'Unknown'
    
    if ADMIN_BOT_USERNAME:
        info['admin_bot_username'] = ADMIN_BOT_USERNAME
    
    if API_ID:
        info['api_id'] = str(API_ID)
    
    return info


def test_credentials():
    """Test credentials without exposing sensitive information."""
    try:
        validate_credentials()
        info = get_credential_info()
        
        logger.info("🔐 Credential Test Results:")
        for key, value in info.items():
            if isinstance(value, bool):
                status = "✅" if value else "❌"
                logger.info(f"   {status} {key}: {value}")
            else:
                logger.info(f"   ℹ️  {key}: {value}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Credential test failed: {e}")
        return False


def mask_sensitive_value(value, show_chars=4):
    """Mask sensitive values for safe logging."""
    if not value:
        return "Not configured"
    
    if len(value) <= show_chars:
        return "*" * len(value)
    
    return value[:show_chars] + "*" * (len(value) - show_chars)


def log_configuration_summary():
    """Log a summary of the configuration (safely)."""
    logger.info("🔧 Configuration Summary:")
    logger.info(f"   API ID: {API_ID if API_ID else 'Not configured'}")
    logger.info(f"   API Hash: {mask_sensitive_value(API_HASH)}")
    logger.info(f"   Phone: {mask_sensitive_value(PHONE_NUMBER, 3)}")
    logger.info(f"   Admin Bot: @{ADMIN_BOT_USERNAME if ADMIN_BOT_USERNAME else 'Not configured'}")
    logger.info(f"   Admin Token: {mask_sensitive_value(ADMIN_BOT_TOKEN)}")


# Validate credentials on import if all environment variables are set
if all([API_ID, API_HASH, PHONE_NUMBER, ADMIN_BOT_TOKEN, ADMIN_BOT_USERNAME]):
    try:
        validate_credentials()
        logger.debug("✅ Credentials auto-validated on import")
    except Exception as e:
        logger.warning(f"⚠️  Credential validation warning on import: {e}")
else:
    logger.debug("⚠️  Not all credentials configured, skipping auto-validation")