"""
Enhanced Telegram client manager for the News Detector.
Handles connection management, reconnection, and error recovery.
"""
import asyncio
import logging
import time
from pathlib import Path
from telethon import TelegramClient
from telethon.errors import (
    SessionPasswordNeededError, AuthKeyError, PhoneCodeInvalidError,
    FloodWaitError, NetworkError, TimeoutError
)

logger = logging.getLogger(__name__)

try:
    from config.credentials import API_ID, API_HASH, PHONE_NUMBER
    from config.settings import (
        SESSION_FILE, MAX_RETRIES, RETRY_DELAY_BASE, 
        CONNECTION_TIMEOUT, PROXY_CONFIG, DEBUG_MODE
    )
except ImportError:
    # Fallback values
    from pathlib import Path
    API_ID = 0
    API_HASH = ""
    PHONE_NUMBER = ""
    SESSION_FILE = Path("./data/state/telegram_session")
    MAX_RETRIES = 3
    RETRY_DELAY_BASE = 2
    CONNECTION_TIMEOUT = 30
    PROXY_CONFIG = None
    DEBUG_MODE = False


class TelegramClientManager:
    """Enhanced Telegram client manager with robust connection handling."""

    def __init__(self):
        """Initialize the client manager."""
        self.client = None
        self.is_running = False
        self._reconnect_task = None
        self._heartbeat_task = None
        self._connection_attempts = 0
        self._last_connection_time = 0

    async def start(self):
        """Start the Telegram client with enhanced error handling."""
        if self.client and self.client.is_connected():
            logger.warning("⚠️  Client already connected")
            return True

        logger.info("🚀 Starting Telegram client...")
        
        # Validate credentials before attempting connection
        if not self._validate_credentials():
            return False

        # Create session directory
        SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize client with proxy support
        client_kwargs = {}
        if PROXY_CONFIG:
            client_kwargs['proxy'] = PROXY_CONFIG
            logger.info(f"🌐 Using proxy: {PROXY_CONFIG}")

        self.client = TelegramClient(
            str(SESSION_FILE), 
            API_ID, 
            API_HASH,
            **client_kwargs
        )

        # Attempt connection with retry logic
        for attempt in range(MAX_RETRIES):
            try:
                self._connection_attempts += 1
                logger.info(f"🔗 Connection attempt {attempt + 1}/{MAX_RETRIES}")
                
                # Start the client
                await self.client.start(phone=PHONE_NUMBER)
                
                # Verify connection
                if not self.client.is_connected():
                    raise ConnectionError("Client failed to connect despite successful start")
                
                # Test the connection with a simple API call
                try:
                    me = await self.client.get_me()
                    logger.info(f"✅ Connected successfully as: {me.first_name} (@{me.username})")
                except Exception as test_error:
                    logger.warning(f"⚠️  Connection test failed: {test_error}")
                    # Continue anyway as this might be a minor issue

                self.is_running = True
                self._last_connection_time = time.time()
                
                # Start monitoring tasks
                self._start_monitoring_tasks()
                
                logger.info("🎉 Telegram client started successfully")
                return True

            except SessionPasswordNeededError:
                logger.error("❌ Two-factor authentication is enabled")
                logger.error("   Please disable 2FA temporarily or implement 2FA handling")
                return False
                
            except PhoneCodeInvalidError:
                logger.error("❌ Invalid phone code entered")
                logger.error("   Please restart and enter the correct verification code")
                return False
                
            except AuthKeyError:
                logger.warning("⚠️  Authentication key error, clearing session...")
                # Remove session files to force re-authentication
                self._clear_session_files()
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY_BASE ** attempt)
                    continue
                else:
                    return False
                    
            except (NetworkError, TimeoutError, ConnectionError) as e:
                logger.warning(f"🌐 Network error (attempt {attempt + 1}): {e}")
                if attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_DELAY_BASE ** attempt
                    logger.info(f"⏳ Waiting {wait_time} seconds before retry...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error("❌ Max connection attempts reached")
                    return False
                    
            except FloodWaitError as e:
                logger.warning(f"⏳ Rate limited, waiting {e.seconds} seconds...")
                await asyncio.sleep(e.seconds)
                continue
                
            except Exception as e:
                logger.error(f"❌ Unexpected error starting client: {e}")
                if DEBUG_MODE:
                    import traceback
                    traceback.print_exc()
                
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY_BASE ** attempt)
                    continue
                else:
                    return False

        logger.error("❌ Failed to start Telegram client after all attempts")
        return False

    def _validate_credentials(self):
        """Validate credentials before connection attempt."""
        try:
            from config.credentials import validate_credentials
            validate_credentials()
            return True
        except Exception as e:
            logger.error(f"❌ Credential validation failed: {e}")
            return False

    def _clear_session_files(self):
        """Clear session files to force re-authentication."""
        try:
            session_files = [
                SESSION_FILE.with_suffix('.session'),
                SESSION_FILE.with_suffix('.session-journal')
            ]
            
            for session_file in session_files:
                if session_file.exists():
                    session_file.unlink()
                    logger.info(f"🗑️  Removed session file: {session_file}")
                    
        except Exception as e:
            logger.error(f"Error clearing session files: {e}")

    def _start_monitoring_tasks(self):
        """Start background monitoring tasks."""
        try:
            # Connection monitor
            if not self._reconnect_task or self._reconnect_task.done():
                self._reconnect_task = asyncio.create_task(self._connection_monitor())
            
            # Heartbeat monitor
            if not self._heartbeat_task or self._heartbeat_task.done():
                self._heartbeat_task = asyncio.create_task(self._heartbeat_monitor())
                
            logger.debug("🔍 Started monitoring tasks")
            
        except Exception as e:
            logger.error(f"Error starting monitoring tasks: {e}")

    async def stop(self):
        """Stop the client and cleanup resources."""
        logger.info("🛑 Stopping Telegram client...")
        
        self.is_running = False

        # Cancel monitoring tasks
        tasks_to_cancel = [self._reconnect_task, self._heartbeat_task]
        for task in tasks_to_cancel:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # Disconnect client
        if self.client and self.client.is_connected():
            try:
                await self.client.disconnect()
                logger.info("✅ Telegram client disconnected")
            except Exception as e:
                logger.error(f"Error disconnecting client: {e}")

    async def _connection_monitor(self):
        """Monitor connection status and reconnect if needed."""
        logger.info("🔍 Connection monitor started")
        
        while self.is_running:
            try:
                if self.client and not self.client.is_connected():
                    logger.warning("⚠️  Connection lost, attempting to reconnect...")
                    
                    # Try to reconnect
                    success = await self._attempt_reconnection()
                    if success:
                        logger.info("✅ Reconnection successful")
                    else:
                        logger.error("❌ Reconnection failed, will retry...")
                
                # Check every 30 seconds
                await asyncio.sleep(30)
                
            except asyncio.CancelledError:
                logger.debug("Connection monitor cancelled")
                break
            except Exception as e:
                logger.error(f"Error in connection monitor: {e}")
                await asyncio.sleep(60)

    async def _attempt_reconnection(self):
        """Attempt to reconnect the client."""
        for attempt in range(MAX_RETRIES):
            try:
                if self.client:
                    await self.client.connect()
                    
                    if self.client.is_connected():
                        logger.info(f"✅ Reconnected on attempt {attempt + 1}")
                        return True
                
                if attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_DELAY_BASE ** attempt
                    logger.info(f"⏳ Waiting {wait_time}s before retry...")
                    await asyncio.sleep(wait_time)
                    
            except Exception as e:
                logger.error(f"Reconnection attempt {attempt + 1} failed: {e}")
                
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY_BASE ** attempt)

        logger.error("❌ All reconnection attempts failed")
        return False

    async def _heartbeat_monitor(self):
        """Send periodic heartbeat to maintain connection."""
        logger.info("💓 Heartbeat monitor started")
        
        while self.is_running:
            try:
                if self.client and self.client.is_connected():
                    # Simple ping to keep connection alive
                    try:
                        await self.client.get_me()
                        logger.debug("💓 Heartbeat successful")
                    except Exception as e:
                        logger.warning(f"💔 Heartbeat failed: {e}")
                
                # Heartbeat every 5 minutes
                await asyncio.sleep(300)
                
            except asyncio.CancelledError:
                logger.debug("Heartbeat monitor cancelled")
                break
            except Exception as e:
                logger.error(f"Error in heartbeat monitor: {e}")
                await asyncio.sleep(60)

    async def get_connection_info(self):
        """Get information about the current connection."""
        info = {
            'is_connected': False,
            'is_running': self.is_running,
            'connection_attempts': self._connection_attempts,
            'last_connection_time': self._last_connection_time,
            'session_file_exists': SESSION_FILE.with_suffix('.session').exists()
        }
        
        if self.client:
            info['is_connected'] = self.client.is_connected()
            
            if info['is_connected']:
                try:
                    me = await self.client.get_me()
                    info['user_id'] = me.id
                    info['username'] = getattr(me, 'username', None)
                    info['first_name'] = getattr(me, 'first_name', 'Unknown')
                except Exception as e:
                    info['connection_error'] = str(e)
        
        return info

    async def test_connection(self):
        """Test the current connection."""
        logger.info("🧪 Testing Telegram connection...")
        
        if not self.client:
            logger.error("❌ Client not initialized")
            return False
        
        if not self.client.is_connected():
            logger.error("❌ Client not connected")
            return False
        
        try:
            # Test with get_me call
            me = await self.client.get_me()
            logger.info(f"✅ Connection test successful: {me.first_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Connection test failed: {e}")
            return False

    def force_disconnect(self):
        """Force disconnect without cleanup (emergency use)."""
        try:
            if self.client:
                self.client.disconnect()
            self.is_running = False
            logger.warning("⚠️  Forced disconnect completed")
        except Exception as e:
            logger.error(f"Error in force disconnect: {e}")

    async def restart_connection(self):
        """Restart the connection (stop and start)."""
        logger.info("🔄 Restarting Telegram connection...")
        
        await self.stop()
        await asyncio.sleep(5)  # Wait a bit before reconnecting
        
        success = await self.start()
        if success:
            logger.info("✅ Connection restart successful")
        else:
            logger.error("❌ Connection restart failed")
        
        return success