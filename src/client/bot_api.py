"""
Complete Telegram Bot API client for the Financial News Detector.
Handles message sending, media uploads, and API interactions.
"""
import asyncio
import aiohttp
import logging
import time
import json
from typing import Optional, Dict, Any, Union
from pathlib import Path

from config.credentials import TELEGRAM_BOT_TOKEN
from config.settings import MAX_RETRIES, RETRY_DELAY_BASE, API_TIMEOUT

logger = logging.getLogger(__name__)

class BotAPIClient:
    """
    Complete Telegram Bot API client with robust error handling and retry logic.
    """

    def __init__(self, bot_token=None, timeout=None, max_retries=None):
        """
        Initialize the Bot API client.
        
        Args:
            bot_token: Bot token (default: from config)
            timeout: Request timeout in seconds (default: from config)
            max_retries: Maximum retry attempts (default: from config)
        """
        self.bot_token = bot_token or TELEGRAM_BOT_TOKEN
        self.timeout = timeout or API_TIMEOUT
        self.max_retries = max_retries or MAX_RETRIES
        
        if not self.bot_token:
            raise ValueError("Bot token is required")
        
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.session = None
        
        # Statistics
        self.stats = {
            'requests_sent': 0,
            'requests_successful': 0,
            'requests_failed': 0,
            'retries_attempted': 0,
            'last_request_time': None,
            'rate_limit_hits': 0
        }
        
        logger.debug("🤖 Bot API client initialized")

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def _ensure_session(self):
        """Ensure aiohttp session is created."""
        if self.session is None or self.session.closed:
            connector = aiohttp.TCPConnector(
                limit=10,
                limit_per_host=5,
                keepalive_timeout=30,
                enable_cleanup_closed=True
            )
            
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={'User-Agent': 'Financial-News-Bot/1.0'}
            )

    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.debug("🔒 Bot API session closed")

    async def _make_request(self, method: str, endpoint: str, data: Dict[str, Any] = None, 
                           files: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Make a request to the Telegram Bot API with retry logic.
        
        Args:
            method: HTTP method (GET, POST)
            endpoint: API endpoint
            data: Request data
            files: Files to upload
            
        Returns:
            API response dict or None if failed
        """
        url = f"{self.base_url}/{endpoint}"
        
        await self._ensure_session()
        
        for attempt in range(self.max_retries + 1):
            try:
                self.stats['requests_sent'] += 1
                
                # Prepare request parameters
                kwargs = {}
                
                if files:
                    # Multipart form data for file uploads
                    form_data = aiohttp.FormData()
                    
                    # Add regular data
                    if data:
                        for key, value in data.items():
                            if value is not None:
                                form_data.add_field(key, str(value))
                    
                    # Add files
                    for key, file_data in files.items():
                        if isinstance(file_data, (str, Path)):
                            # File path
                            with open(file_data, 'rb') as f:
                                form_data.add_field(key, f.read(), filename=Path(file_data).name)
                        else:
                            # File-like object or bytes
                            form_data.add_field(key, file_data)
                    
                    kwargs['data'] = form_data
                else:
                    # JSON data
                    if data:
                        kwargs['json'] = data
                
                # Make request
                async with self.session.request(method, url, **kwargs) as response:
                    self.stats['last_request_time'] = time.time()
                    
                    # Read response
                    response_text = await response.text()
                    
                    # Handle different status codes
                    if response.status == 200:
                        result = json.loads(response_text)
                        
                        if result.get('ok'):
                            self.stats['requests_successful'] += 1
                            logger.debug(f"✅ Bot API request successful: {endpoint}")
                            return result
                        else:
                            error_code = result.get('error_code', 0)
                            error_desc = result.get('description', 'Unknown error')
                            
                            logger.error(f"❌ Bot API error {error_code}: {error_desc}")
                            
                            # Handle specific error codes
                            if error_code == 429:  # Too Many Requests
                                retry_after = result.get('parameters', {}).get('retry_after', 1)
                                self.stats['rate_limit_hits'] += 1
                                logger.warning(f"⏳ Rate limited, waiting {retry_after} seconds")
                                await asyncio.sleep(retry_after)
                                continue
                            elif error_code in [400, 403, 404]:
                                # Don't retry for client errors
                                self.stats['requests_failed'] += 1
                                return None
                            else:
                                # Retry for server errors
                                if attempt < self.max_retries:
                                    self.stats['retries_attempted'] += 1
                                    delay = RETRY_DELAY_BASE ** attempt
                                    logger.warning(f"🔄 Retrying in {delay} seconds (attempt {attempt + 1})")
                                    await asyncio.sleep(delay)
                                    continue
                    
                    elif response.status == 429:
                        # Rate limit without proper JSON response
                        self.stats['rate_limit_hits'] += 1
                        retry_after = int(response.headers.get('Retry-After', 1))
                        logger.warning(f"⏳ Rate limited, waiting {retry_after} seconds")
                        await asyncio.sleep(retry_after)
                        continue
                    
                    else:
                        # HTTP error
                        logger.error(f"❌ HTTP {response.status}: {response_text}")
                        
                        if response.status >= 500 and attempt < self.max_retries:
                            # Retry server errors
                            self.stats['retries_attempted'] += 1
                            delay = RETRY_DELAY_BASE ** attempt
                            logger.warning(f"🔄 Retrying in {delay} seconds (attempt {attempt + 1})")
                            await asyncio.sleep(delay)
                            continue
            
            except asyncio.TimeoutError:
                logger.warning(f"⏰ Request timeout (attempt {attempt + 1})")
                if attempt < self.max_retries:
                    self.stats['retries_attempted'] += 1
                    delay = RETRY_DELAY_BASE ** attempt
                    await asyncio.sleep(delay)
                    continue
                    
            except aiohttp.ClientError as e:
                logger.error(f"❌ Client error: {e} (attempt {attempt + 1})")
                if attempt < self.max_retries:
                    self.stats['retries_attempted'] += 1
                    delay = RETRY_DELAY_BASE ** attempt
                    await asyncio.sleep(delay)
                    continue
                    
            except Exception as e:
                logger.error(f"❌ Unexpected error: {e} (attempt {attempt + 1})")
                if attempt < self.max_retries:
                    self.stats['retries_attempted'] += 1
                    delay = RETRY_DELAY_BASE ** attempt
                    await asyncio.sleep(delay)
                    continue
            
            # If we reach here, the attempt failed
            break
        
        # All attempts failed
        self.stats['requests_failed'] += 1
        logger.error(f"❌ All {self.max_retries + 1} attempts failed for {endpoint}")
        return None

    async def send_message(self, chat_id: Union[int, str], text: str, 
                          parse_mode: str = 'HTML', disable_web_page_preview: bool = True,
                          disable_notification: bool = False, reply_to_message_id: int = None) -> Optional[Dict[str, Any]]:
        """
        Send a text message.
        
        Args:
            chat_id: Target chat ID
            text: Message text (1-4096 characters)
            parse_mode: Parse mode (HTML, Markdown, MarkdownV2)
            disable_web_page_preview: Disable link previews
            disable_notification: Send silently
            reply_to_message_id: Reply to specific message
            
        Returns:
            Message object or None if failed
        """
        # Validate input
        if not text or len(text) > 4096:
            logger.error(f"❌ Invalid message length: {len(text) if text else 0}")
            return None
        
        data = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode,
            'disable_web_page_preview': disable_web_page_preview,
            'disable_notification': disable_notification
        }
        
        if reply_to_message_id:
            data['reply_to_message_id'] = reply_to_message_id
        
        result = await self._make_request('POST', 'sendMessage', data)
        
        if result:
            logger.info(f"📤 Message sent to {chat_id}")
            return result.get('result')
        else:
            logger.error(f"❌ Failed to send message to {chat_id}")
            return None

    async def send_photo(self, chat_id: Union[int, str], photo: Union[str, Path, bytes],
                        caption: str = None, parse_mode: str = 'HTML',
                        disable_notification: bool = False) -> Optional[Dict[str, Any]]:
        """
        Send a photo.
        
        Args:
            chat_id: Target chat ID
            photo: Photo file path, bytes, or file_id
            caption: Photo caption (0-1024 characters)
            parse_mode: Parse mode for caption
            disable_notification: Send silently
            
        Returns:
            Message object or None if failed
        """
        data = {
            'chat_id': chat_id,
            'disable_notification': disable_notification
        }
        
        if caption:
            if len(caption) > 1024:
                logger.error(f"❌ Caption too long: {len(caption)}")
                return None
            data['caption'] = caption
            data['parse_mode'] = parse_mode
        
        files = None
        
        # Handle different photo types
        if isinstance(photo, (str, Path)):
            path = Path(photo)
            if path.exists():
                files = {'photo': path}
            else:
                # Assume it's a file_id or URL
                data['photo'] = str(photo)
        elif isinstance(photo, bytes):
            files = {'photo': photo}
        else:
            data['photo'] = str(photo)
        
        result = await self._make_request('POST', 'sendPhoto', data, files)
        
        if result:
            logger.info(f"📷 Photo sent to {chat_id}")
            return result.get('result')
        else:
            logger.error(f"❌ Failed to send photo to {chat_id}")
            return None

    async def send_document(self, chat_id: Union[int, str], document: Union[str, Path, bytes],
                           caption: str = None, parse_mode: str = 'HTML',
                           disable_notification: bool = False) -> Optional[Dict[str, Any]]:
        """
        Send a document.
        
        Args:
            chat_id: Target chat ID
            document: Document file path, bytes, or file_id
            caption: Document caption
            parse_mode: Parse mode for caption
            disable_notification: Send silently
            
        Returns:
            Message object or None if failed
        """
        data = {
            'chat_id': chat_id,
            'disable_notification': disable_notification
        }
        
        if caption:
            data['caption'] = caption
            data['parse_mode'] = parse_mode
        
        files = None
        
        # Handle different document types
        if isinstance(document, (str, Path)):
            path = Path(document)
            if path.exists():
                files = {'document': path}
            else:
                data['document'] = str(document)
        elif isinstance(document, bytes):
            files = {'document': document}
        else:
            data['document'] = str(document)
        
        result = await self._make_request('POST', 'sendDocument', data, files)
        
        if result:
            logger.info(f"📎 Document sent to {chat_id}")
            return result.get('result')
        else:
            logger.error(f"❌ Failed to send document to {chat_id}")
            return None

    async def edit_message_text(self, chat_id: Union[int, str], message_id: int, text: str,
                               parse_mode: str = 'HTML', disable_web_page_preview: bool = True) -> Optional[Dict[str, Any]]:
        """
        Edit a message text.
        
        Args:
            chat_id: Target chat ID
            message_id: Message ID to edit
            text: New text
            parse_mode: Parse mode
            disable_web_page_preview: Disable link previews
            
        Returns:
            Message object or None if failed
        """
        data = {
            'chat_id': chat_id,
            'message_id': message_id,
            'text': text,
            'parse_mode': parse_mode,
            'disable_web_page_preview': disable_web_page_preview
        }
        
        result = await self._make_request('POST', 'editMessageText', data)
        
        if result:
            logger.info(f"✏️ Message {message_id} edited in {chat_id}")
            return result.get('result')
        else:
            logger.error(f"❌ Failed to edit message {message_id} in {chat_id}")
            return None

    async def delete_message(self, chat_id: Union[int, str], message_id: int) -> bool:
        """
        Delete a message.
        
        Args:
            chat_id: Target chat ID
            message_id: Message ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        data = {
            'chat_id': chat_id,
            'message_id': message_id
        }
        
        result = await self._make_request('POST', 'deleteMessage', data)
        
        if result:
            logger.info(f"🗑️ Message {message_id} deleted from {chat_id}")
            return True
        else:
            logger.error(f"❌ Failed to delete message {message_id} from {chat_id}")
            return False

    async def get_me(self) -> Optional[Dict[str, Any]]:
        """
        Get bot information.
        
        Returns:
            Bot info or None if failed
        """
        result = await self._make_request('GET', 'getMe')
        
        if result:
            return result.get('result')
        else:
            return None

    async def get_chat(self, chat_id: Union[int, str]) -> Optional[Dict[str, Any]]:
        """
        Get chat information.
        
        Args:
            chat_id: Chat ID
            
        Returns:
            Chat info or None if failed
        """
        data = {'chat_id': chat_id}
        result = await self._make_request('GET', 'getChat', data)
        
        if result:
            return result.get('result')
        else:
            return None

    async def test_connection(self) -> bool:
        """
        Test the Bot API connection.
        
        Returns:
            True if connection is working, False otherwise
        """
        logger.info("🧪 Testing Bot API connection...")
        
        try:
            bot_info = await self.get_me()
            
            if bot_info:
                username = bot_info.get('username', 'Unknown')
                first_name = bot_info.get('first_name', 'Unknown')
                logger.info(f"✅ Bot API connection successful: {first_name} (@{username})")
                return True
            else:
                logger.error("❌ Bot API connection test failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Bot API connection test error: {e}")
            return False

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get client statistics.
        
        Returns:
            Statistics dictionary
        """
        stats = self.stats.copy()
        
        # Calculate success rate
        total_requests = stats['requests_sent']
        if total_requests > 0:
            stats['success_rate'] = (stats['requests_successful'] / total_requests) * 100
        else:
            stats['success_rate'] = 0
        
        # Format last request time
        if stats['last_request_time']:
            from datetime import datetime
            stats['last_request_formatted'] = datetime.fromtimestamp(
                stats['last_request_time']
            ).strftime('%Y-%m-%d %H:%M:%S')
        
        return stats

    def reset_statistics(self):
        """Reset statistics counters."""
        self.stats = {
            'requests_sent': 0,
            'requests_successful': 0,
            'requests_failed': 0,
            'retries_attempted': 0,
            'last_request_time': None,
            'rate_limit_hits': 0
        }
        logger.info("📊 Bot API statistics reset")

# Convenience functions
async def send_financial_news(chat_id: Union[int, str], news_text: str, 
                             bot_token: str = None) -> bool:
    """
    Convenience function to send financial news.
    
    Args:
        chat_id: Target chat ID
        news_text: Financial news text
        bot_token: Bot token (optional)
        
    Returns:
        True if successful, False otherwise
    """
    async with BotAPIClient(bot_token) as client:
        result = await client.send_message(chat_id, news_text)
        return result is not None

async def test_bot_api(bot_token: str = None) -> bool:
    """
    Test Bot API connectivity.
    
    Args:
        bot_token: Bot token to test (optional)
        
    Returns:
        True if successful, False otherwise
    """
    async with BotAPIClient(bot_token) as client:
        return await client.test_connection()

# Export main classes and functions
__all__ = [
    'BotAPIClient',
    'send_financial_news',
    'test_bot_api'
]