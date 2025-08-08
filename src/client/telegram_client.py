"""
Complete Telegram client manager for the Financial News Detector.
Handles connection, authentication, and session management.
"""
import asyncio
import logging
import os
import signal
from pathlib import Path
from telethon import TelegramClient, errors
from telethon.sessions import StringSession

from config.credentials import API_ID, API_HASH, PHONE_NUMBER, validate_credentials

logger = logging.getLogger(__name__)

class TelegramClientManager:
    """
    Complete Telegram client manager with robust connection handling.
    """

    def __init__(self, session_name=None, use_string_session=False):
        """
        Initialize the Telegram client manager.
        
        Args:
            session_name: Name for session file (default: from settings)
            use_string_session: Whether to use string sessions instead of file sessions
        """
        self.client = None
        self.connected = False
        self.authenticated = False
        self.user_info = None
        self.connection_attempts = 0
        self.max_connection_attempts = 3
        self.use_string_session = use_string_session
        
        # Session configuration
        if session_name is None:
            session_name = os.getenv("SESSION_FILE_PATH", "data/session/telegram_session")
        
        self.session_name = session_name
        self.session_dir = Path(session_name).parent
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        # Connection monitoring
        self.connection_monitor_task = None
        self.heartbeat_task = None
        self.last_heartbeat = None
        
        # Event handlers
        self.disconnect_handlers = []
        
        logger.info("🚀 Starting Telegram client...")

    async def start(self):
        """
        Start the Telegram client with robust error handling.
        
        Returns:
            bool: True if successfully started and authenticated
        """
        try:
            # Validate credentials first
            validate_credentials()
            logger.info("✅ Credentials validated successfully")
            
            # Initialize client
            await self._initialize_client()
            
            # Connect and authenticate
            if await self._connect_and_authenticate():
                # Start monitoring tasks
                await self._start_monitoring()
                
                logger.info("🎉 Telegram client started successfully")
                return True
            else:
                logger.error("❌ Failed to connect and authenticate")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to start Telegram client: {e}")
            await self._cleanup()
            return False

    async def _initialize_client(self):
        """Initialize the Telegram client with appropriate session."""
        try:
            # Create session
            if self.use_string_session:
                # Try to load existing string session
                session_str = os.getenv("TELEGRAM_STRING_SESSION", "")
                session = StringSession(session_str)
            else:
                # Use file session
                session = self.session_name
            
            # Initialize client
            self.client = TelegramClient(
                session,
                API_ID,
                API_HASH,
                device_model="Financial News Bot",
                system_version="1.0",
                app_version="1.0",
                lang_code='en',
                system_lang_code='en'
            )
            
            # Set up proxy if configured
            await self._setup_proxy()
            
            logger.debug("📱 Telegram client initialized")
            
        except Exception as e:
            logger.error(f"❌ Error initializing client: {e}")
            raise

    async def _setup_proxy(self):
        """Set up proxy if configured."""
        use_proxy = os.getenv("USE_PROXY", "false").lower() == "true"
        
        if not use_proxy:
            return
        
        try:
            proxy_server = os.getenv("PROXY_SERVER")
            proxy_port = int(os.getenv("PROXY_PORT", "1080"))
            proxy_username = os.getenv("PROXY_USERNAME", "")
            proxy_password = os.getenv("PROXY_PASSWORD", "")
            proxy_type = os.getenv("PROXY_TYPE", "socks5")
            
            if proxy_server:
                from telethon import connection
                
                if proxy_type.lower() == "socks5":
                    import socks
                    proxy = (socks.SOCKS5, proxy_server, proxy_port, True, proxy_username, proxy_password)
                elif proxy_type.lower() == "http":
                    proxy = (proxy_server, proxy_port, proxy_username, proxy_password)
                else:
                    logger.warning(f"Unsupported proxy type: {proxy_type}")
                    return
                
                self.client._connection = connection.ConnectionTcpMTProxyRandomizedIntermediate
                self.client._proxy = proxy
                
                logger.info(f"🌐 Proxy configured: {proxy_type}://{proxy_server}:{proxy_port}")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to set up proxy: {e}")

    async def _connect_and_authenticate(self):
        """Connect to Telegram and authenticate."""
        for attempt in range(1, self.max_connection_attempts + 1):
            try:
                logger.info(f"🔗 Connection attempt {attempt}/{self.max_connection_attempts}")
                
                # Connect
                await self.client.connect()
                
                if not await self.client.is_user_authorized():
                    # Need to authenticate
                    logger.info("🔐 User not authorized, starting authentication...")
                    await self._authenticate_user()
                
                # Verify connection
                if await self.client.is_user_authorized():
                    self.connected = True
                    self.authenticated = True
                    
                    # Get user info
                    self.user_info = await self.client.get_me()
                    username = getattr(self.user_info, 'username', 'No username')
                    first_name = getattr(self.user_info, 'first_name', 'Unknown')
                    
                    logger.info(f"✅ Connected successfully as: {first_name} (@{username})")
                    
                    # Save string session if using string sessions
                    if self.use_string_session:
                        session_str = self.client.session.save()
                        logger.debug("💾 String session saved")
                    
                    return True
                else:
                    logger.error("❌ Authentication failed")
                    
            except errors.FloodWaitError as e:
                logger.warning(f"⏳ Flood wait: {e.seconds} seconds")
                await asyncio.sleep(e.seconds)
                continue
                
            except errors.PhoneNumberInvalidError:
                logger.error("❌ Invalid phone number format")
                return False
                
            except errors.ApiIdInvalidError:
                logger.error("❌ Invalid API ID or API Hash")
                return False
                
            except Exception as e:
                logger.error(f"❌ Connection attempt {attempt} failed: {e}")
                
                if attempt < self.max_connection_attempts:
                    wait_time = attempt * 5  # Exponential backoff
                    logger.info(f"⏳ Waiting {wait_time} seconds before retry...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("❌ All connection attempts failed")
                    return False
        
        return False

    async def _authenticate_user(self):
        """Authenticate user with phone number and code."""
        try:
            # Send code request
            sent_code = await self.client.send_code_request(PHONE_NUMBER)
            logger.info(f"📱 Verification code sent to {PHONE_NUMBER}")
            
            # Get code from user input
            code = input("Enter the verification code: ").strip()
            
            try:
                # Sign in with code
                await self.client.sign_in(PHONE_NUMBER, code)
                logger.info("✅ Successfully authenticated with code")
                
            except errors.SessionPasswordNeededError:
                # Two-factor authentication required
                logger.info("🔒 Two-factor authentication required")
                password = input("Enter your 2FA password: ").strip()
                await self.client.sign_in(password=password)
                logger.info("✅ Successfully authenticated with 2FA")
                
        except Exception as e:
            logger.error(f"❌ Authentication failed: {e}")
            raise

    async def _start_monitoring(self):
        """Start connection monitoring tasks."""
        try:
            # Start connection monitor
            self.connection_monitor_task = asyncio.create_task(self._connection_monitor())
            logger.info("🔍 Connection monitor started")
            
            # Start heartbeat
            self.heartbeat_task = asyncio.create_task(self._heartbeat_monitor())
            logger.info("💓 Heartbeat monitor started")
            
        except Exception as e:
            logger.error(f"❌ Failed to start monitoring: {e}")

    async def _connection_monitor(self):
        """Monitor connection status and reconnect if needed."""
        reconnect_attempts = 0
        max_reconnect_attempts = 5
        
        while self.connected:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                if not self.client.is_connected():
                    logger.warning("⚠️ Connection lost, attempting to reconnect...")
                    
                    try:
                        await self.client.connect()
                        reconnect_attempts = 0
                        logger.info("✅ Reconnected successfully")
                        
                    except Exception as e:
                        reconnect_attempts += 1
                        logger.error(f"❌ Reconnection attempt {reconnect_attempts} failed: {e}")
                        
                        if reconnect_attempts >= max_reconnect_attempts:
                            logger.error("❌ Max reconnection attempts reached")
                            self.connected = False
                            break
                        
                        await asyncio.sleep(reconnect_attempts * 10)  # Exponential backoff
                
            except asyncio.CancelledError:
                logger.debug("Connection monitor cancelled")
                break
            except Exception as e:
                logger.error(f"Error in connection monitor: {e}")
                await asyncio.sleep(60)

    async def _heartbeat_monitor(self):
        """Send periodic heartbeats to maintain connection."""
        while self.connected:
            try:
                await asyncio.sleep(300)  # Every 5 minutes
                
                if self.client.is_connected():
                    # Simple ping to keep connection alive
                    await self.client.get_me()
                    self.last_heartbeat = asyncio.get_event_loop().time()
                    logger.debug("💓 Heartbeat successful")
                
            except asyncio.CancelledError:
                logger.debug("Heartbeat monitor cancelled")
                break
            except Exception as e:
                logger.warning(f"Heartbeat failed: {e}")
                await asyncio.sleep(60)

    async def get_entity(self, entity_id):
        """
        Get entity with error handling and caching.
        
        Args:
            entity_id: Username, ID, or phone number
            
        Returns:
            Entity object or None if not found
        """
        try:
            entity = await self.client.get_entity(entity_id)
            return entity
            
        except errors.UsernameNotOccupiedError:
            logger.error(f"❌ Username not found: {entity_id}")
            return None
            
        except errors.UsernameInvalidError:
            logger.error(f"❌ Invalid username format: {entity_id}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting entity {entity_id}: {e}")
            return None

    async def send_message(self, entity, message, **kwargs):
        """
        Send message with error handling.
        
        Args:
            entity: Target entity
            message: Message text
            **kwargs: Additional arguments for send_message
            
        Returns:
            Message object or None if failed
        """
        try:
            sent_message = await self.client.send_message(entity, message, **kwargs)
            logger.debug(f"📤 Message sent to {entity}")
            return sent_message
            
        except errors.FloodWaitError as e:
            logger.warning(f"⏳ Flood wait: {e.seconds} seconds for {entity}")
            await asyncio.sleep(e.seconds)
            return None
            
        except errors.ChatWriteForbiddenError:
            logger.error(f"❌ Cannot write to chat: {entity}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error sending message to {entity}: {e}")
            return None

    def add_disconnect_handler(self, handler):
        """Add handler to be called on disconnect."""
        self.disconnect_handlers.append(handler)

    def remove_disconnect_handler(self, handler):
        """Remove disconnect handler."""
        if handler in self.disconnect_handlers:
            self.disconnect_handlers.remove(handler)

    async def _handle_disconnect(self):
        """Handle disconnect event."""
        logger.warning("🔌 Client disconnected")
        
        # Call disconnect handlers
        for handler in self.disconnect_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler()
                else:
                    handler()
            except Exception as e:
                logger.error(f"Error in disconnect handler: {e}")

    def is_connected(self):
        """Check if client is connected."""
        return self.connected and self.client and self.client.is_connected()

    def is_authenticated(self):
        """Check if client is authenticated."""
        return self.authenticated

    def get_user_info(self):
        """Get current user information."""
        return self.user_info

    async def get_dialogs(self, limit=None):
        """Get user dialogs."""
        try:
            dialogs = []
            async for dialog in self.client.iter_dialogs(limit=limit):
                dialogs.append(dialog)
            return dialogs
        except Exception as e:
            logger.error(f"Error getting dialogs: {e}")
            return []

    async def get_chat_members(self, chat, limit=None):
        """Get chat members."""
        try:
            members = []
            async for user in self.client.iter_participants(chat, limit=limit):
                members.append(user)
            return members
        except Exception as e:
            logger.error(f"Error getting chat members: {e}")
            return []

    async def _cleanup(self):
        """Clean up resources."""
        try:
            # Cancel monitoring tasks
            if self.connection_monitor_task:
                self.connection_monitor_task.cancel()
                try:
                    await self.connection_monitor_task
                except asyncio.CancelledError:
                    pass
            
            if self.heartbeat_task:
                self.heartbeat_task.cancel()
                try:
                    await self.heartbeat_task
                except asyncio.CancelledError:
                    pass
            
            # Call disconnect handlers
            await self._handle_disconnect()
            
            logger.debug("🧹 Client cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    async def stop(self):
        """Stop the Telegram client gracefully."""
        logger.info("🛑 Stopping Telegram client...")
        
        try:
            self.connected = False
            self.authenticated = False
            
            # Cleanup monitoring
            await self._cleanup()
            
            # Disconnect client
            if self.client:
                if self.client.is_connected():
                    await self.client.disconnect()
                    logger.info("✅ Telegram client disconnected")
                else:
                    logger.info("📱 Client was already disconnected")
            
        except Exception as e:
            logger.error(f"❌ Error stopping client: {e}")

    def get_connection_stats(self):
        """Get connection statistics."""
        return {
            "connected": self.is_connected(),
            "authenticated": self.is_authenticated(),
            "connection_attempts": self.connection_attempts,
            "last_heartbeat": self.last_heartbeat,
            "user_info": {
                "id": self.user_info.id if self.user_info else None,
                "username": getattr(self.user_info, 'username', None) if self.user_info else None,
                "first_name": getattr(self.user_info, 'first_name', None) if self.user_info else None,
            } if self.user_info else None
        }

    def __del__(self):
        """Destructor to ensure cleanup."""
        try:
            if self.client and self.client.is_connected():
                # Can't use await in destructor, so just try to disconnect
                asyncio.create_task(self.stop())
        except Exception:
            pass  # Ignore errors in destructor

# Convenience functions
async def create_client(session_name=None, use_string_session=False):
    """
    Create and start a Telegram client.
    
    Args:
        session_name: Session name/path
        use_string_session: Use string sessions
        
    Returns:
        TelegramClientManager: Started client manager
    """
    client_manager = TelegramClientManager(session_name, use_string_session)
    
    if await client_manager.start():
        return client_manager
    else:
        raise Exception("Failed to start Telegram client")

async def test_connection():
    """Test Telegram connection."""
    logger.info("🧪 Testing Telegram connection...")
    
    try:
        client_manager = await create_client()
        
        # Test basic functionality
        user_info = client_manager.get_user_info()
        logger.info(f"✅ Connection test successful: {user_info.first_name}")
        
        await client_manager.stop()
        return True
        
    except Exception as e:
        logger.error(f"❌ Connection test failed: {e}")
        return False

# Export main classes and functions
__all__ = [
    'TelegramClientManager',
    'create_client',
    'test_connection'
]