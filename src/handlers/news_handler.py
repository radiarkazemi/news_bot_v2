"""
Complete news handler with financial focus, approval workflow, image handling, and clickable commands.
Handles news detection, filtering, approval, publishing with media support, and cleanup.
"""
import asyncio
import hashlib
import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from collections import deque

try:
    import aiofiles
    import aiohttp
    MEDIA_SUPPORT = True
except ImportError:
    MEDIA_SUPPORT = False
    logging.getLogger(__name__).warning("aiofiles/aiohttp not available - media features disabled")

from telethon import events
from telethon.errors import FloodWaitError
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument

# Import services
from src.services.news_detector import NewsDetector
from src.services.news_filter import NewsFilter
from src.client.bot_api import BotAPIClient
from src.utils.time_utils import get_current_time, get_formatted_time
from config.settings import (
    TARGET_CHANNEL_ID, ADMIN_BOT_USERNAME, NEW_ATTRIBUTION,
    NEWS_CHANNEL, TWITTER_NEWS_CHANNEL, CHANNEL_PROCESSING_DELAY,
    TEMP_MEDIA_DIR, MEDIA_CLEANUP_ENABLED, MEDIA_CLEANUP_DELAY,
    MAX_MEDIA_SIZE_MB, ENABLE_MEDIA_PROCESSING
)

logger = logging.getLogger(__name__)

class SimpleRateLimiter:
    """Simple rate limiter to prevent flood waits."""
    
    def __init__(self, min_delay=8, max_queue_size=30):
        self.min_delay = min_delay
        self.max_queue_size = max_queue_size
        self.last_send_time = 0
        self.pending_queue = deque()
        self.processing = False
    
    async def add_to_queue(self, send_func, *args, **kwargs):
        """Add a send operation to the rate-limited queue."""
        if len(self.pending_queue) >= self.max_queue_size:
            logger.warning(f"🚫 Queue full ({self.max_queue_size}), dropping message")
            return None
        
        self.pending_queue.append((send_func, args, kwargs))
        logger.info(f"📥 Added to queue (size: {len(self.pending_queue)})")
        
        # Start processing if not already running
        if not self.processing:
            asyncio.create_task(self._process_queue())
        
        return "queued"
    
    async def _process_queue(self):
        """Process queued send operations with rate limiting."""
        if self.processing:
            return
        
        self.processing = True
        
        try:
            while self.pending_queue:
                # Check if enough time has passed
                time_since_last = time.time() - self.last_send_time
                if time_since_last < self.min_delay:
                    wait_time = self.min_delay - time_since_last
                    logger.info(f"⏳ Rate limiting: waiting {wait_time:.1f}s")
                    await asyncio.sleep(wait_time)
                
                # Get next item from queue
                send_func, args, kwargs = self.pending_queue.popleft()
                
                try:
                    # Attempt to send
                    result = await send_func(*args, **kwargs)
                    self.last_send_time = time.time()
                    
                    if result:
                        logger.info("✅ Rate-limited send successful")
                    else:
                        logger.warning("⚠️ Rate-limited send failed")
                        
                except Exception as e:
                    logger.error(f"❌ Error in rate-limited send: {e}")
                
                # Brief pause between sends
                await asyncio.sleep(1)
        
        finally:
            self.processing = False

class NewsHandler:
    """Complete news handler for financial news detection and approval workflow."""

    def __init__(self, client_manager):
        """Initialize the news handler."""
        self.client_manager = client_manager
        self.bot_api = None
        self.news_detector = NewsDetector()
        self.pending_news = {}
        self.processed_messages = set()
        self.admin_bot_entity = None
        
        # Add rate limiter
        self.rate_limiter = SimpleRateLimiter(min_delay=8, max_queue_size=30)
        self.approval_stats = {
            'sent': 0,
            'queued': 0,
            'dropped': 0,
            'errors': 0
        }
        
        # Statistics
        self.stats = {
            'messages_processed': 0,
            'news_detected': 0,
            'news_filtered_out': 0,
            'news_sent_for_approval': 0,
            'news_approved': 0,
            'news_published': 0,
            'errors': 0,
            'session_start': time.time()
        }
        
        # State file path
        self.state_file = Path("data/state/news_handler_state.json")
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info("📰 News handler initialized with financial focus, rate limiting, and media support")

    async def initialize(self):
        """Initialize the news handler with Bot API and media cleanup."""
        try:
            self.bot_api = BotAPIClient()
            
            # Start periodic media cleanup if media support is enabled
            if MEDIA_SUPPORT and ENABLE_MEDIA_PROCESSING and MEDIA_CLEANUP_ENABLED:
                asyncio.create_task(self._periodic_media_cleanup())
                logger.info("🧹 Periodic media cleanup started")
            
            logger.info("✅ News handler initialized with Bot API and media support")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Bot API: {e}")

    async def _periodic_media_cleanup(self):
        """Periodic cleanup of old media files."""
        while True:
            try:
                await asyncio.sleep(MEDIA_CLEANUP_DELAY)  # Wait for cleanup interval
                await self.cleanup_all_temp_media()
            except asyncio.CancelledError:
                logger.info("Media cleanup task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in periodic media cleanup: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error

    async def setup_approval_handler(self):
        """Set up the approval command handler with clickable commands."""
        try:
            client = self.client_manager.client
            
            # Handle approval commands
            @client.on(events.NewMessage(pattern=r'/submit(\w+)'))
            async def handle_approval_command(event):
                """Handle approval commands from admin bot."""
                try:
                    approval_id = event.pattern_match.group(1)
                    await self._process_approval(approval_id, event)
                except Exception as e:
                    logger.error(f"❌ Error handling approval command: {e}")
            
            @client.on(events.NewMessage(pattern=r'/reject(\w+)'))
            async def handle_rejection_command(event):
                """Handle rejection commands from admin bot."""
                try:
                    approval_id = event.pattern_match.group(1)
                    await self._process_rejection(approval_id, event)
                except Exception as e:
                    logger.error(f"❌ Error handling rejection command: {e}")
            
            logger.info("✅ News approval handler set up successfully with clickable commands")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to set up approval handler: {e}")
            return False

    async def _process_approval(self, approval_id, event):
        """Process approval request."""
        logger.info(f"📥 Received approval for: {approval_id}")
        
        # Check if we have this pending news
        if approval_id not in self.pending_news:
            await event.respond(f"❌ News item {approval_id} not found or already processed")
            logger.warning(f"Approval ID {approval_id} not found in pending news")
            return
        
        # Get news data
        news_data = self.pending_news[approval_id]
        logger.info(f"📋 Processing approval for news: {news_data['text'][:100]}...")
        
        # Publish the news
        success = await self.publish_approved_news(news_data)
        
        if success:
            # Success response
            response_text = f"✅ News {approval_id} published successfully to channel!"
            await event.respond(response_text)
            
            logger.info(f"✅ Successfully published approved news: {approval_id}")
            
            # Update statistics
            self.stats['news_approved'] += 1
            self.stats['news_published'] += 1
            
            # Remove from pending
            del self.pending_news[approval_id]
            await self.save_pending_news()
            
        else:
            # Failure response
            error_text = f"❌ Failed to publish news {approval_id}. Please try again or contact support."
            await event.respond(error_text)
            
            logger.error(f"❌ Failed to publish approved news: {approval_id}")

    async def _process_rejection(self, approval_id, event):
        """Process rejection request."""
        logger.info(f"🚫 Received rejection for: {approval_id}")
        
        if approval_id in self.pending_news:
            # Remove from pending
            news_data = self.pending_news[approval_id]
            del self.pending_news[approval_id]
            await self.save_pending_news()
            
            response_text = f"🚫 News {approval_id} rejected and removed from queue"
            await event.respond(response_text)
            
            logger.info(f"🚫 News {approval_id} rejected and removed")
        else:
            await event.respond(f"❌ News item {approval_id} not found")

    async def publish_approved_news(self, news_data):
        """Publish approved news to the target channel with media support and Persian calendar format."""
        temp_media_path = None
        try:
            if not self.bot_api:
                logger.error("❌ Bot API not available for publishing")
                return False
            
            # Get formatted text
            formatted_text = news_data.get('formatted_text', news_data['text'])
            
            # Ensure proper formatting
            if not formatted_text.startswith(('💰', '💱', '🏆', '₿', '🛢️', '📈')):
                # Add appropriate financial emoji
                if any(kw in formatted_text.lower() for kw in ['طلا', 'سکه', 'gold']):
                    formatted_text = f"🏆 {formatted_text}"
                elif any(kw in formatted_text.lower() for kw in ['دلار', 'یورو', 'ارز', 'dollar', 'euro']):
                    formatted_text = f"💱 {formatted_text}"
                else:
                    formatted_text = f"📈 {formatted_text}"
            
            # Add attribution if not present
            if NEW_ATTRIBUTION and NEW_ATTRIBUTION not in formatted_text:
                formatted_text = f"{formatted_text}\n📡 {NEW_ATTRIBUTION}"
            
            # Add Persian calendar timestamp
            current_time = get_formatted_time(format_type="persian_full")
            formatted_text = f"{formatted_text}\n🕐 {current_time}"
            
            logger.info(f"📤 Attempting to publish to channel {TARGET_CHANNEL_ID}")
            
            # Handle media if present and media support is available
            media_info = news_data.get('media')
            if (MEDIA_SUPPORT and ENABLE_MEDIA_PROCESSING and 
                media_info and news_data.get('has_media')):
                
                # Download media first
                temp_media_path = await self._download_media_for_publishing(media_info)
                
                if temp_media_path and temp_media_path.exists():
                    logger.info(f"📎 Publishing with media: {temp_media_path}")
                    
                    # Publish with media using Bot API
                    async with self.bot_api as api_client:
                        if (media_info.get('type') == 'photo' or 
                            temp_media_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                            # Send as photo
                            result = await api_client.send_photo(
                                chat_id=TARGET_CHANNEL_ID,
                                photo=temp_media_path,
                                caption=formatted_text,
                                parse_mode='HTML'
                            )
                        else:
                            # Send as document
                            result = await api_client.send_document(
                                chat_id=TARGET_CHANNEL_ID,
                                document=temp_media_path,
                                caption=formatted_text,
                                parse_mode='HTML'
                            )
                    
                    if result:
                        logger.info(f"📢 Financial news with media published to channel {TARGET_CHANNEL_ID}")
                        logger.info(f"🆔 Published message ID: {result.get('message_id', 'Unknown')}")
                        
                        # Schedule media cleanup
                        if MEDIA_CLEANUP_ENABLED:
                            asyncio.create_task(self._cleanup_media_delayed(temp_media_path))
                        
                        return True
                    else:
                        logger.error("❌ Failed to publish news with media via Bot API")
                        return False
                else:
                    logger.warning("⚠️ Failed to download media, publishing text only")
                    # Fall through to text-only publishing
            
            # Publish text-only message
            async with self.bot_api as api_client:
                result = await api_client.send_message(
                    chat_id=TARGET_CHANNEL_ID,
                    text=formatted_text,
                    parse_mode='HTML'
                )
            
            if result:
                logger.info(f"📢 Financial news published to channel {TARGET_CHANNEL_ID}")
                logger.info(f"🆔 Published message ID: {result.get('message_id', 'Unknown')}")
                return True
            else:
                logger.error("❌ Failed to publish news via Bot API")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error publishing approved news: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            
            # Clean up media on error
            if temp_media_path and temp_media_path.exists() and MEDIA_CLEANUP_ENABLED:
                try:
                    temp_media_path.unlink()
                    logger.info(f"🧹 Cleaned up media after error: {temp_media_path}")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup media: {cleanup_error}")
            
            return False

    async def _download_media_for_publishing(self, media_info):
        """Download media from original message for publishing."""
        if not MEDIA_SUPPORT:
            logger.warning("Media support not available (missing aiofiles/aiohttp)")
            return None
            
        try:
            if not media_info or not media_info.get('channel') or not media_info.get('message_id'):
                logger.warning("Invalid media info for downloading")
                return None
            
            # Get the source channel and message
            channel_name = media_info['channel']
            message_id = media_info['message_id']
            
            # Ensure channel name has @
            if not channel_name.startswith('@'):
                channel_name = f"@{channel_name}"
            
            logger.info(f"📥 Downloading media from {channel_name}, message {message_id}")
            
            # Get channel entity
            channel_entity = await self.client_manager.client.get_entity(channel_name)
            
            # Get the specific message
            message = await self.client_manager.client.get_messages(channel_entity, ids=message_id)
            if not message or not message.media:
                logger.warning(f"No media found in message {message_id}")
                return None
            
            # Generate unique filename
            timestamp = int(time.time())
            media_hash = hashlib.md5(f"{channel_name}_{message_id}".encode()).hexdigest()[:8]
            
            # Determine file extension based on media type
            if isinstance(message.media, MessageMediaPhoto):
                file_extension = ".jpg"
            elif isinstance(message.media, MessageMediaDocument):
                # Try to get extension from document attributes
                file_extension = ".jpg"  # Default
                if hasattr(message.media.document, 'attributes'):
                    for attr in message.media.document.attributes:
                        if hasattr(attr, 'file_name') and attr.file_name:
                            file_extension = Path(attr.file_name).suffix or ".jpg"
                            break
                        elif hasattr(attr, 'mime_type'):
                            if 'image/jpeg' in getattr(attr, 'mime_type', ''):
                                file_extension = ".jpg"
                            elif 'image/png' in getattr(attr, 'mime_type', ''):
                                file_extension = ".png"
                            elif 'image/gif' in getattr(attr, 'mime_type', ''):
                                file_extension = ".gif"
                            elif 'image/webp' in getattr(attr, 'mime_type', ''):
                                file_extension = ".webp"
            else:
                logger.warning(f"Unsupported media type: {type(message.media)}")
                return None
            
            # Create temp file path
            temp_filename = f"news_media_{timestamp}_{media_hash}{file_extension}"
            temp_media_path = TEMP_MEDIA_DIR / temp_filename
            
            # Download media
            logger.info(f"💾 Downloading to: {temp_media_path}")
            downloaded_path = await self.client_manager.client.download_media(
                message.media,
                file=str(temp_media_path)
            )
            
            if downloaded_path and Path(downloaded_path).exists():
                # Check file size
                file_size_mb = Path(downloaded_path).stat().st_size / (1024 * 1024)
                if file_size_mb > MAX_MEDIA_SIZE_MB:
                    logger.warning(f"Media file too large: {file_size_mb:.2f}MB > {MAX_MEDIA_SIZE_MB}MB")
                    Path(downloaded_path).unlink()
                    return None
                
                logger.info(f"✅ Media downloaded successfully: {downloaded_path} ({file_size_mb:.2f}MB)")
                return Path(downloaded_path)
            else:
                logger.error("❌ Failed to download media")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error downloading media: {e}")
            return None

    async def _cleanup_media_delayed(self, media_path, delay=None):
        """Clean up media file after delay."""
        try:
            if delay is None:
                delay = MEDIA_CLEANUP_DELAY
            
            logger.info(f"⏰ Scheduling media cleanup in {delay} seconds: {media_path}")
            await asyncio.sleep(delay)
            
            if media_path.exists():
                media_path.unlink()
                logger.info(f"🧹 Cleaned up media file: {media_path}")
            else:
                logger.debug(f"Media file already removed: {media_path}")
                
        except Exception as e:
            logger.warning(f"Failed to cleanup media file {media_path}: {e}")

    async def cleanup_all_temp_media(self):
        """Clean up all temporary media files."""
        try:
            if not TEMP_MEDIA_DIR.exists():
                return
            
            cleaned_count = 0
            current_time = time.time()
            
            for media_file in TEMP_MEDIA_DIR.glob("news_media_*"):
                try:
                    # Check if file is old enough to clean (older than cleanup delay)
                    file_age = current_time - media_file.stat().st_mtime
                    if file_age > MEDIA_CLEANUP_DELAY:
                        media_file.unlink()
                        cleaned_count += 1
                        logger.debug(f"🧹 Cleaned old media: {media_file}")
                except Exception as e:
                    logger.warning(f"Error cleaning media file {media_file}: {e}")
            
            if cleaned_count > 0:
                logger.info(f"🧹 Cleaned {cleaned_count} old media files")
                
        except Exception as e:
            logger.error(f"Error in media cleanup: {e}")

    async def process_news_messages(self, channel_username):
        """Process news messages from a channel with financial focus."""
        logger.info(f"🔍 Processing financial news from channel: {channel_username}")
        
        try:
            # Get channel entity
            if not channel_username.startswith('@'):
                channel_username = '@' + channel_username
            
            channel_entity = await self.client_manager.client.get_entity(channel_username)
            
            # Get recent messages (last 6 hours from config)
            from config.settings import MESSAGE_LOOKBACK_HOURS
            cutoff_time = datetime.now() - timedelta(hours=MESSAGE_LOOKBACK_HOURS)
            
            messages_processed = 0
            news_sent_for_approval = 0
            total_messages = 0
            
            logger.info(f"📥 Retrieving recent messages from {channel_username}")
            
            # Use setting from config (30 messages)
            from config.settings import MAX_MESSAGES_PER_CHECK
            async for message in self.client_manager.client.iter_messages(channel_entity, limit=MAX_MESSAGES_PER_CHECK):
                try:
                    total_messages += 1
                    
                    # Skip if too old
                    if message.date.replace(tzinfo=None) < cutoff_time:
                        continue
                    
                    # Skip if no text
                    if not message.text or len(message.text.strip()) < 30:
                        continue
                    
                    # Check if already processed
                    message_key = f"{channel_username.replace('@', '')}:{message.id}"
                    if message_key in self.processed_messages:
                        continue
                    
                    messages_processed += 1
                    self.stats['messages_processed'] += 1
                    
                    logger.debug(f"📝 Analyzing message {message.id}: {message.text[:100]}...")
                    
                    # Step 1: Financial news detection
                    if not self.news_detector.is_news(message.text):
                        logger.debug(f"Message {message.id} not detected as financial news")
                        continue
                    
                    logger.info(f"📰 Financial news detected in message {message.id}")
                    self.stats['news_detected'] += 1
                    
                    # Step 2: Apply financial relevance filter
                    try:
                        is_relevant, score, topics = NewsFilter.is_relevant_news(message.text)
                    except Exception as filter_error:
                        logger.warning(f"NewsFilter error: {filter_error}, assuming relevant")
                        is_relevant, score, topics = True, 5, ["fallback"]
                    
                    if not is_relevant:
                        logger.info(f"Message {message.id} filtered out (financial score: {score})")
                        self.stats['news_filtered_out'] += 1
                        continue
                    
                    category = NewsFilter.get_financial_category(message.text, topics)
                    priority = NewsFilter.get_priority_level(score)
                    
                    logger.info(f"✅ Relevant financial news found: score={score}, "
                               f"category={category}, priority={priority}, topics={topics[:3]}")
                    
                    # Step 3: Handle multiple news segments if present
                    news_segments = self.news_detector.split_combined_news(message.text)
                    
                    if len(news_segments) > 1:
                        logger.info(f"📋 Split into {len(news_segments)} financial news segments")
                    
                    # Process each segment
                    for i, segment in enumerate(news_segments):
                        if len(segment.strip()) < 50:
                            continue
                        
                        # Re-check relevance for each segment
                        try:
                            seg_relevant, seg_score, seg_topics = NewsFilter.is_relevant_news(segment)
                        except:
                            seg_relevant, seg_score, seg_topics = True, 3, ["segment"]
                        
                        if not seg_relevant:
                            logger.debug(f"Segment {i+1} filtered out (score: {seg_score})")
                            continue
                        
                        # Clean and format the segment
                        cleaned_text = self.news_detector.clean_news_text(segment)
                        
                        # Handle media (only for first segment)
                        media = None
                        if i == 0 and message.media and ENABLE_MEDIA_PROCESSING:
                            media = self._extract_media_info(message, channel_username)
                        
                        # Send for approval with rate limiting
                        approval_id = await self.send_to_approval_bot_rate_limited(
                            cleaned_text, 
                            media, 
                            channel_username.replace('@', ''),
                            {
                                'score': seg_score,
                                'category': category,
                                'priority': priority,
                                'topics': seg_topics[:5]
                            }
                        )
                        
                        if approval_id:
                            news_sent_for_approval += 1
                            self.stats['news_sent_for_approval'] += 1
                            self.processed_messages.add(message_key)
                            logger.info(f"📤 Segment {i+1} sent for approval: {approval_id}")
                        
                        # Delay between segments
                        await asyncio.sleep(1)
                    
                    # Mark message as processed
                    self.processed_messages.add(message_key)
                    
                    # Delay between messages
                    await asyncio.sleep(CHANNEL_PROCESSING_DELAY)
                    
                except Exception as e:
                    logger.error(f"Error processing message {message.id}: {e}")
                    self.stats['errors'] += 1
                    continue
            
            logger.info(f"📊 Channel processing complete: {news_sent_for_approval}/{messages_processed} "
                       f"relevant items sent for approval from {total_messages} total messages")
            
            return news_sent_for_approval > 0
            
        except Exception as e:
            logger.error(f"❌ Error processing financial news from {channel_username}: {e}")
            self.stats['errors'] += 1
            return False

    def _extract_media_info(self, message, channel_username):
        """Extract comprehensive media information from message."""
        try:
            if isinstance(message.media, MessageMediaPhoto):
                return {
                    "type": "photo",
                    "media_id": message.media.photo.id,
                    "message_id": message.id,
                    "channel": channel_username.replace('@', ''),
                    "file_size": getattr(message.media.photo, 'file_size', 0),
                    "has_spoiler": getattr(message.media, 'spoiler', False)
                }
            elif isinstance(message.media, MessageMediaDocument):
                document = message.media.document
                
                # Extract file info
                file_name = None
                mime_type = None
                is_image = False
                
                if hasattr(document, 'attributes'):
                    for attr in document.attributes:
                        if hasattr(attr, 'file_name') and attr.file_name:
                            file_name = attr.file_name
                        if hasattr(attr, 'mime_type'):
                            mime_type = attr.mime_type
                            is_image = mime_type.startswith('image/')
                
                # Check if it's an image document
                if document.mime_type and document.mime_type.startswith('image/'):
                    is_image = True
                    mime_type = document.mime_type
                
                if is_image:
                    return {
                        "type": "document_image",
                        "media_id": document.id,
                        "message_id": message.id,
                        "channel": channel_username.replace('@', ''),
                        "file_name": file_name,
                        "mime_type": mime_type,
                        "file_size": getattr(document, 'size', 0),
                        "has_spoiler": getattr(message.media, 'spoiler', False)
                    }
                    
        except Exception as e:
            logger.warning(f"Error extracting media info: {e}")
        
        return None

    async def send_to_approval_bot_rate_limited(self, news_text, media=None, source_channel=None, analysis=None):
        """Rate-limited version of send_to_approval_bot."""
        try:
            # Check priority - only queue if important enough
            if analysis:
                score = analysis.get('score', 0)
                priority = analysis.get('priority', 'NORMAL')
                
                # Skip low priority during high activity
                if score < 5 and len(self.rate_limiter.pending_queue) > 10:
                    logger.info(f"🚫 Skipping low priority news (score: {score}, queue: {len(self.rate_limiter.pending_queue)})")
                    self.approval_stats['dropped'] += 1
                    return None
            
            # Generate approval ID
            content_hash = hashlib.md5(news_text.encode()).hexdigest()[:6]
            timestamp_id = str(int(time.time() * 1000))[-6:]
            approval_id = f"{timestamp_id}{content_hash}"
            
            # Add to rate-limited queue
            result = await self.rate_limiter.add_to_queue(
                self._send_approval_message,
                news_text, media, source_channel, analysis, approval_id
            )
            
            if result == "queued":
                self.approval_stats['queued'] += 1
                
                # Store pending news
                self.pending_news[approval_id] = {
                    'text': news_text,
                    'formatted_text': news_text,
                    'original_text': news_text,
                    'timestamp': time.time(),
                    'source_channel': source_channel,
                    'has_media': media is not None,
                    'media': media,
                    'analysis': analysis,
                    'approval_source': 'telegram',
                    'status': 'queued'
                }
                
                await self.save_pending_news()
                return approval_id
            else:
                self.approval_stats['dropped'] += 1
                return None
                
        except Exception as e:
            logger.error(f"❌ Error in rate-limited approval: {e}")
            self.approval_stats['errors'] += 1
            return None

    async def _send_approval_message(self, news_text, media, source_channel, analysis, approval_id):
        """Internal method to send approval message with clickable commands."""
        try:
            # Get admin bot entity
            admin_bot_entity = await self.get_admin_bot_entity()
            if not admin_bot_entity:
                logger.error("❌ Could not get admin bot entity")
                return False
            
            # Format approval message
            analysis_info = ""
            if analysis:
                category = analysis.get('category', 'UNKNOWN')
                priority = analysis.get('priority', 'NORMAL')
                score = analysis.get('score', 0)
                topics = analysis.get('topics', [])
                
                analysis_info = (f"💼 Category: {category}\n"
                               f"⚡ Priority: {priority}\n" 
                               f"📊 Score: {score}\n"
                               f"🏷️ Topics: {', '.join(topics[:3])}\n")
            
            current_time = get_formatted_time()
            approval_message = (
                f"📈 <b>FINANCIAL NEWS PENDING APPROVAL</b>\n\n"
                f"🆔 ID: <code>{approval_id}</code>\n"
                f"📡 Source: {source_channel or 'Unknown'}\n"
                f"🕐 Time: {current_time}\n"
                f"{analysis_info}"
                f"{'📎 Has Media' if media else '📝 Text Only'}\n\n"
                f"<b>Content:</b>\n"
                f"{news_text}\n\n"
                f"➡️ To approve: /submit{approval_id}\n"
                f"➡️ To reject: /reject{approval_id}"
            )
            
            # Send message without inline keyboard (clickable commands work better)
            message = await self.client_manager.client.send_message(
                admin_bot_entity,
                approval_message,
                parse_mode='html'
            )
            
            if message:
                self.approval_stats['sent'] += 1
                logger.info(f"📤 Rate-limited approval sent with clickable commands: {approval_id}")
                return True
            else:
                logger.error("❌ Failed to send approval message")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error sending approval message: {e}")
            return False

    async def get_admin_bot_entity(self):
        """Get the admin bot entity with caching."""
        if self.admin_bot_entity:
            return self.admin_bot_entity
        
        try:
            # Try different username formats
            possible_usernames = [
                ADMIN_BOT_USERNAME,
                f"@{ADMIN_BOT_USERNAME}",
                ADMIN_BOT_USERNAME.replace('@', '')
            ]
            
            for username in possible_usernames:
                try:
                    entity = await self.client_manager.client.get_entity(username)
                    self.admin_bot_entity = entity
                    logger.info(f"✅ Found admin bot: {username}")
                    return entity
                except:
                    continue
            
            logger.error(f"❌ Could not find admin bot with username: {ADMIN_BOT_USERNAME}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting admin bot entity: {e}")
            return None

    async def load_pending_news(self):
        """Load pending news from state file and cleanup old media."""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.pending_news = data.get('pending_news', {})
                    self.processed_messages = set(data.get('processed_messages', []))
                    self.stats.update(data.get('stats', {}))
                
                logger.info(f"📂 Loaded {len(self.pending_news)} pending news items")
            else:
                logger.info("📂 No existing state file found, starting fresh")
            
            # Clean up any orphaned media files on startup
            if MEDIA_SUPPORT and ENABLE_MEDIA_PROCESSING and MEDIA_CLEANUP_ENABLED:
                await self.cleanup_all_temp_media()
                logger.info("🧹 Startup media cleanup completed")
                
        except Exception as e:
            logger.error(f"❌ Error loading pending news: {e}")
            self.pending_news = {}
            self.processed_messages = set()

    async def save_pending_news(self):
        """Save pending news to state file."""
        try:
            data = {
                'pending_news': self.pending_news,
                'processed_messages': list(self.processed_messages),
                'stats': self.stats,
                'last_updated': time.time()
            }
            
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            logger.debug("💾 Pending news state saved")
            
        except Exception as e:
            logger.error(f"❌ Error saving pending news: {e}")

    async def clean_expired_pending_news(self, max_age_hours=24):
        """Clean expired pending news items."""
        try:
            current_time = time.time()
            expired_ids = []
            
            for news_id, news_data in self.pending_news.items():
                timestamp = news_data.get('timestamp', 0)
                age_hours = (current_time - timestamp) / 3600
                
                if age_hours > max_age_hours:
                    expired_ids.append(news_id)
            
            # Remove expired items
            for news_id in expired_ids:
                del self.pending_news[news_id]
            
            if expired_ids:
                logger.info(f"🧹 Cleaned {len(expired_ids)} expired pending news items")
                await self.save_pending_news()
                
        except Exception as e:
            logger.error(f"❌ Error cleaning expired pending news: {e}")

    def get_approval_stats(self):
        """Get approval processing statistics."""
        queue_size = len(self.rate_limiter.pending_queue)
        processing = self.rate_limiter.processing
        
        return {
            **self.approval_stats,
            'queue_size': queue_size,
            'processing': processing,
            'last_send_time': self.rate_limiter.last_send_time,
            'queue_full': queue_size >= self.rate_limiter.max_queue_size
        }

    def log_approval_stats(self):
        """Log approval statistics."""
        stats = self.get_approval_stats()
        
        logger.info("📊 APPROVAL STATISTICS")
        logger.info("=" * 40)
        logger.info(f"📤 Sent: {stats['sent']}")
        logger.info(f"📥 Queued: {stats['queued']}")
        logger.info(f"🚫 Dropped: {stats['dropped']}")
        logger.info(f"❌ Errors: {stats['errors']}")
        logger.info(f"📋 Current Queue: {stats['queue_size']}")
        logger.info(f"🔄 Processing: {'Yes' if stats['processing'] else 'No'}")
        logger.info("=" * 40)

    def get_statistics(self):
        """Get comprehensive statistics."""
        uptime = time.time() - self.stats.get('session_start', time.time())
        
        return {
            **self.stats,
            'pending_approvals': len(self.pending_news),
            'processed_messages_cache': len(self.processed_messages),
            'uptime_seconds': uptime,
            'uptime_hours': uptime / 3600,
            'approval_rate': (self.stats.get('news_approved', 0) / 
                            max(1, self.stats.get('news_sent_for_approval', 1))) * 100,
            'detection_rate': (self.stats.get('news_detected', 0) / 
                             max(1, self.stats.get('messages_processed', 1))) * 100,
            'media_support': MEDIA_SUPPORT and ENABLE_MEDIA_PROCESSING
        }

    async def force_process_recent_messages(self, channel_username, num_messages=5):
        """Force process recent messages for testing/debugging."""
        logger.info(f"🔧 Force processing {num_messages} recent messages from {channel_username}")
        
        try:
            if not channel_username.startswith('@'):
                channel_username = '@' + channel_username
            
            channel = await self.client_manager.client.get_entity(channel_username)
            processed_count = 0
            
            async for message in self.client_manager.client.iter_messages(channel, limit=num_messages):
                if message.text:
                    logger.info(f"📝 Force processing message {message.id}: {message.text[:100]}...")
                    
                    # Force process regardless of previous processing
                    if self.news_detector.is_news(message.text):
                        logger.info(f"   📰 Financial news detected: True")
                        
                        try:
                            is_relevant, score, topics = NewsFilter.is_relevant_news(message.text)
                        except:
                            is_relevant, score, topics = True, 3, ["force_test"]
                        
                        logger.info(f"   🎯 Relevance: {is_relevant}, Score: {score}, Topics: {topics[:3]}")
                        
                        if is_relevant:
                            # Process without duplicate checking
                            cleaned = self.news_detector.clean_news_text(message.text)
                            approval_id = await self.send_to_approval_bot_rate_limited(
                                cleaned, 
                                None, 
                                channel_username.replace('@', ''),
                                {'score': score, 'topics': topics}
                            )
                            if approval_id:
                                processed_count += 1
                                logger.info(f"   ✅ Sent for approval: {approval_id}")
                    else:
                        logger.info(f"   ❌ Not detected as financial news")
            
            logger.info(f"🔧 Force processing complete: {processed_count} items sent for approval")
            return processed_count > 0
            
        except Exception as e:
            logger.error(f"❌ Error in force processing: {e}")
            return False