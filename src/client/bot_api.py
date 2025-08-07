"""
Bot API client for sending messages via Telegram Bot API.
Fixed version without async/await syntax errors.
"""
import logging
import time
import requests
from requests.exceptions import RequestException, Timeout

logger = logging.getLogger(__name__)

try:
    from config.credentials import ADMIN_BOT_TOKEN
    from config.settings import MAX_RETRIES, RETRY_DELAY_BASE
except ImportError:
    # Fallback values
    ADMIN_BOT_TOKEN = ""
    MAX_RETRIES = 3
    RETRY_DELAY_BASE = 2


class BotAPIClient:
    """Client for Telegram Bot API interactions."""

    def __init__(self):
        """Initialize the bot API client."""
        if not ADMIN_BOT_TOKEN:
            logger.warning("ADMIN_BOT_TOKEN not configured")
            self.base_url = None
        else:
            self.base_url = f"https://api.telegram.org/bot{ADMIN_BOT_TOKEN}"

    def send_message(self, chat_id, text, parse_mode='HTML'):
        """
        Send a message via Bot API.
        
        Args:
            chat_id: Target chat ID
            text: Message text
            parse_mode: Message formatting (HTML, Markdown, etc.)
            
        Returns:
            dict: API response on success, None on failure
        """
        if not self.base_url:
            logger.error("Bot API not configured - missing ADMIN_BOT_TOKEN")
            return None
            
        url = f"{self.base_url}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode
        }

        for attempt in range(MAX_RETRIES):
            try:
                response = requests.post(url, json=payload, timeout=15)
                response.raise_for_status()
                result = response.json()

                if result.get('ok'):
                    logger.debug(f"Message sent successfully to {chat_id}")
                    return result
                else:
                    error_desc = result.get('description', 'Unknown error')
                    error_code = result.get('error_code', 0)
                    logger.error(f"Bot API error: {error_desc} (Code: {error_code})")

                    # Don't retry for certain error codes
                    if error_code in [400, 403, 404]:
                        logger.error(f"Permanent error {error_code}, not retrying")
                        break

                    # Exponential backoff for retryable errors
                    if attempt < MAX_RETRIES - 1:
                        sleep_time = RETRY_DELAY_BASE ** attempt
                        logger.info(f"Retrying in {sleep_time} seconds...")
                        time.sleep(sleep_time)
                        
            except Timeout:
                logger.warning(f"Request timeout (Attempt {attempt + 1}/{MAX_RETRIES})")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY_BASE ** attempt)
                    
            except RequestException as e:
                logger.error(f"HTTP Error: {e} (Attempt {attempt + 1}/{MAX_RETRIES})")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY_BASE ** attempt)
                    
            except Exception as e:
                logger.error(f"Unexpected error sending message: {e}")
                break

        logger.error(f"Failed to send message to {chat_id} after {MAX_RETRIES} attempts")
        return None

    def send_photo(self, chat_id, photo, caption=None, parse_mode='HTML'):
        """
        Send a photo via Bot API.
        
        Args:
            chat_id: Target chat ID
            photo: Photo file or file_id
            caption: Photo caption
            parse_mode: Caption formatting
            
        Returns:
            dict: API response on success, None on failure
        """
        if not self.base_url:
            logger.error("Bot API not configured")
            return None
            
        url = f"{self.base_url}/sendPhoto"
        payload = {
            'chat_id': chat_id,
            'photo': photo,
            'parse_mode': parse_mode
        }
        
        if caption:
            payload['caption'] = caption

        for attempt in range(MAX_RETRIES):
            try:
                response = requests.post(url, json=payload, timeout=30)
                response.raise_for_status()
                result = response.json()

                if result.get('ok'):
                    logger.debug(f"Photo sent successfully to {chat_id}")
                    return result
                else:
                    error_desc = result.get('description', 'Unknown error')
                    logger.error(f"Bot API error sending photo: {error_desc}")
                    
                    if result.get('error_code') in [400, 403, 404]:
                        break
                        
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_DELAY_BASE ** attempt)
                        
            except Exception as e:
                logger.error(f"Error sending photo (attempt {attempt + 1}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY_BASE ** attempt)

        logger.error(f"Failed to send photo to {chat_id} after {MAX_RETRIES} attempts")
        return None

    def get_me(self):
        """Get bot information."""
        if not self.base_url:
            return None
            
        url = f"{self.base_url}/getMe"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if result.get('ok'):
                return result.get('result')
            else:
                logger.error(f"Error getting bot info: {result.get('description')}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting bot info: {e}")
            return None

    def test_connection(self):
        """Test Bot API connection."""
        logger.info("Testing Bot API connection...")
        
        bot_info = self.get_me()
        if bot_info:
            logger.info(f"✅ Bot API connection successful")
            logger.info(f"   Bot: @{bot_info.get('username', 'unknown')}")
            logger.info(f"   Name: {bot_info.get('first_name', 'Unknown')}")
            return True
        else:
            logger.error("❌ Bot API connection failed")
            return False