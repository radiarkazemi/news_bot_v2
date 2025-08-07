"""
Complete news handler for processing and managing news with admin approval workflow.
"""
import logging
import asyncio
import json
import time
import re
import hashlib
from datetime import datetime, timedelta
from telethon import events
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
from telethon.errors import FloodWaitError, UserNotParticipantError

logger = logging.getLogger(__name__)

try:
    from src.client.bot_api import BotAPIClient
    from src.services.news_detector import NewsDetector
    from src.services.news_filter import NewsFilter
    from src.services.state_manager import StateManager
    from config.settings import (
        TARGET_CHANNEL_ID, ADMIN_BOT_USERNAME, NEW_ATTRIBUTION,
        ADMIN_APPROVAL_TIMEOUT, ENABLE_MEDIA_PROCESSING, CHANNEL_PROCESSING_DELAY
    )
except ImportError as e:
    logger.error(f"Import error in news_handler: {e}")
    # Fallback values
    TARGET_CHANNEL_ID = -1002481901026
    ADMIN_BOT_USERNAME = "goldnewsadminbot" 
    NEW_ATTRIBUTION = "@anilgoldgallerynews"
    ADMIN_APPROVAL_TIMEOUT = 3600
    ENABLE_MEDIA_PROCESSING = True
    CHANNEL_PROCESSING_DELAY = 2


class NewsHandler:
    """Complete news handler with full detection, filtering, and approval workflow."""

    def __init__(self, client_manager):
        """Initialize the news handler."""
        self.client_manager = client_manager
        
        # Initialize services with fallback
        try:
            self.bot_api = BotAPIClient()
            self.news_detector = NewsDetector()
            self.state_manager = StateManager()
        except Exception as e:
            logger.error(f"Error initializing services: {e}")
            # Create minimal fallbacks
            self.bot_api = None
            self.news_detector = None
            self.state_manager = None
        
        self.pending_news = {}
        
        # Track processed messages to avoid duplicates
        self.processed_messages = set()
        
        # Cache for channel entities to avoid repeated lookups
        self.channel_cache = {}
        
        # Statistics tracking
        self.stats = {
            'messages_processed': 0,
            'news_detected': 0,
            'news_sent_for_approval': 0,
            'news_approved': 0,
            'news_filtered_out': 0,
            'errors': 0,
            'session_start': time.time()
        }

    async def setup_approval_handler(self):
        """Set up the approval command handler for admin bot."""
        try:
            if not self.client_manager.client:
                logger.error("Client not available for setting up approval handler")
                return False

            @self.client_manager.client.on(events.NewMessage(pattern=r'/submit(\d+)'))
            async def approval_handler(event):
                """Handle approval commands from admin."""
                try:
                    approval_id = event.pattern_match.group(1)
                    logger.info(f"📝 Received approval command for ID: {approval_id}")
                    await self.handle_approval_command(approval_id, event)
                except Exception as e:
                    logger.error(f"Error in approval handler: {e}")
                    try:
                        await event.reply("❌ Error processing approval command.")
                    except:
                        pass

            logger.info("✅ News approval handler set up successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set up approval handler: {e}")
            return False

    async def handle_approval_command(self, approval_id, event):
        """Handle news approval command from admin."""
        try:
            if approval_id not in self.pending_news:
                await event.reply(f"❌ News item {approval_id} not found or already processed.")
                logger.warning(f"Approval ID {approval_id} not found in pending news")
                return

            news_data = self.pending_news[approval_id]
            
            # Publish the approved news
            logger.info(f"📤 Publishing approved news: {approval_id}")
            success = await self.publish_approved_news(news_data)
            
            if success:
                await event.reply(f"✅ News {approval_id} approved and published!")
                # Remove from pending
                del self.pending_news[approval_id]
                await self.save_pending_news()
                
                # Update statistics
                self.stats['news_approved'] += 1
                logger.info(f"✅ Successfully published approved news {approval_id}")
            else:
                await event.reply(f"❌ Failed to publish news {approval_id}. Please try again.")
                logger.error(f"Failed to publish approved news {approval_id}")
                
        except Exception as e:
            logger.error(f"Error handling approval command for {approval_id}: {e}")
            try:
                await event.reply("❌ Error processing approval. Please contact support.")
            except:
                pass

    async def publish_approved_news(self, news_data):
        """Publish approved news to the target channel."""
        try:
            if not self.bot_api:
                logger.error("Bot API not available")
                return False
                
            formatted_text = news_data.get('formatted_text', news_data['text'])
            
            # Use Bot API to send message
            result = self.bot_api.send_message(
                chat_id=TARGET_CHANNEL_ID,
                text=formatted_text,
                parse_mode='HTML'
            )
            
            if result:
                logger.info(f"📢 News published to channel {TARGET_CHANNEL_ID}")
                return True
            else:
                logger.error("Failed to publish news via Bot API")
                return False
                
        except Exception as e:
            logger.error(f"Error publishing approved news: {e}")
            return False

    async def process_news_messages(self, channel_username):
        """Process recent news messages from a channel with full detection."""
        logger.info(f"🔍 Processing news messages from channel: {channel_username}")
        
        try:
            # Get recent messages from the channel
            messages = await self.get_recent_news_messages(channel_username)
            
            if not messages:
                logger.debug(f"No new messages found in {channel_username}")
                return False

            success_count = 0
            total_processed = 0
            
            for msg_id, text, timestamp, media in messages:
                try:
                    total_processed += 1
                    self.stats['messages_processed'] += 1
                    
                    # Create unique message key to avoid duplicates
                    message_key = f"{channel_username}:{msg_id}"
                    if message_key in self.processed_messages:
                        logger.debug(f"Skipping already processed message: {msg_id}")
                        continue
                    
                    # Step 1: Detect if it's news content
                    if not self.news_detector or not self.news_detector.is_news(text):
                        logger.debug(f"Message {msg_id} not detected as news")
                        continue
                    
                    self.stats['news_detected'] += 1
                    logger.info(f"📰 News detected in message {msg_id}")
                    
                    # Step 2: Check if it contains multiple news items
                    news_segments = self.news_detector.split_combined_news(text) if self.news_detector else [text]
                    
                    if len(news_segments) > 1:
                        logger.info(f"📋 Split into {len(news_segments)} news segments")
                    
                    # Step 3: Process each segment
                    for i, segment in enumerate(news_segments):
                        if len(segment.strip()) < 50:  # Skip very short segments
                            continue
                        
                        # Check relevance using our war/geopolitical filter
                        try:
                            from src.services.news_filter import NewsFilter
                            is_relevant, score, topics = NewsFilter.is_relevant_news(segment)
                        except:
                            # Fallback simple check
                            is_relevant, score, topics = True, 1, ["fallback"]
                        
                        if not is_relevant:
                            logger.debug(f"Segment {i+1} filtered out (score: {score})")
                            self.stats['news_filtered_out'] += 1
                            continue
                        
                        # Process the relevant news segment
                        success = await self.process_single_news_item(
                            segment, 
                            media if i == 0 else None,  # Only attach media to first segment
                            channel_username,
                            msg_id
                        )
                        
                        if success:
                            success_count += 1
                            self.processed_messages.add(message_key)
                            logger.info(f"✅ Processed segment {i+1} with score {score}, topics: {topics[:3]}")
                        
                        # Small delay between segments
                        await asyncio.sleep(1)
                
                except Exception as e:
                    logger.error(f"Error processing message {msg_id}: {e}")
                    self.stats['errors'] += 1
                    continue
                
                # Delay between messages to avoid rate limits
                await asyncio.sleep(CHANNEL_PROCESSING_DELAY)
            
            logger.info(f"📊 Channel processing complete: {success_count}/{total_processed} messages processed from {channel_username}")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error processing news from {channel_username}: {e}")
            self.stats['errors'] += 1
            return False

    async def process_single_news_item(self, text, media, source_channel, msg_id):
        """Process a single news item through the complete pipeline."""
        try:
            # Clean and format the news text
            if self.news_detector:
                cleaned_text = self.news_detector.clean_news_text(text)
            else:
                cleaned_text = text  # Fallback
            
            if not cleaned_text:
                logger.debug("News text cleaning resulted in empty content")
                return False
            
            # Extract metadata for better processing
            if self.news_detector:
                metadata = self.news_detector.extract_news_metadata(text)
                logger.debug(f"News metadata: {metadata}")
            
            # Send to approval bot
            approval_id = await self.send_to_approval_bot(cleaned_text, media, source_channel)
            
            if approval_id:
                self.stats['news_sent_for_approval'] += 1
                logger.info(f"📤 Sent news for approval: {approval_id} (from {source_channel})")
                return True
            else:
                logger.error("Failed to send news to approval bot")
                return False
                
        except Exception as e:
            logger.error(f"Error processing single news item: {e}")
            return False

    async def send_to_approval_bot(self, news_text, media=None, source_channel=None):
        """Send news to admin bot for approval with enhanced formatting."""
        try:
            # Generate unique approval ID
            content_hash = hashlib.md5(news_text.encode()).hexdigest()[:4]
            timestamp_id = str(int(time.time() * 1000))[-6:]
            approval_id = f"{timestamp_id}{content_hash}"
            
            # Get admin bot entity
            admin_bot_entity = await self.get_admin_bot_entity()
            if not admin_bot_entity:
                logger.error("Could not get admin bot entity")
                return None
            
            # Format message for approval
            try:
                from src.utils.time_utils import get_formatted_time
                current_time = get_formatted_time()
            except:
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            approval_message = (
                f"📰 <b>NEWS ITEM PENDING APPROVAL</b>\n"
                f"🆔 ID: <code>{approval_id}</code>\n"
                f"📡 Source: {source_channel or 'Unknown'}\n"  
                f"🕐 Time: {current_time}\n"
                f"{'📎 Has Media' if media else '📝 Text Only'}\n\n"
                f"<b>Content:</b>\n"
                f"{news_text}\n\n"
                f"➡️ <b>To approve, send:</b> <code>/submit{approval_id}</code>"
            )
            
            # Send to admin bot
            message = await self.client_manager.client.send_message(
                admin_bot_entity,
                approval_message,
                parse_mode='html'
            )
            
            if message:
                # Store pending news with comprehensive data
                self.pending_news[approval_id] = {
                    'text': news_text,
                    'formatted_text': news_text,
                    'original_text': news_text,
                    'message_id': message.id,
                    'timestamp': time.time(),
                    'source_channel': source_channel,
                    'has_media': media is not None,
                    'media': media,
                    'approval_source': 'telegram',
                    'status': 'pending'
                }
                
                # Save state
                await self.save_pending_news()
                
                logger.info(f"📤 Sent news for approval: {approval_id}")
                return approval_id
            else:
                logger.error("Failed to send message to admin bot")
                return None
                
        except Exception as e:
            logger.error(f"Error sending to approval bot: {e}")
            return None

    async def get_admin_bot_entity(self):
        """Get the admin bot entity with caching."""
        try:
            if 'admin_bot' not in self.channel_cache:
                self.channel_cache['admin_bot'] = await self.client_manager.client.get_entity(
                    ADMIN_BOT_USERNAME
                )
            return self.channel_cache['admin_bot']
        except Exception as e:
            logger.error(f"Error getting admin bot entity: {e}")
            return None

    async def get_recent_news_messages(self, channel_username, limit=20):
        """Get recent messages from a news channel with enhanced filtering."""
        try:
            # Normalize channel username
            if not channel_username.startswith('@'):
                channel_username = '@' + channel_username
            
            # Get channel entity with caching
            if channel_username not in self.channel_cache:
                try:
                    self.channel_cache[channel_username] = await self.client_manager.client.get_entity(channel_username)
                except UserNotParticipantError:
                    logger.error(f"Bot is not a member of channel {channel_username}")
                    return []
                except Exception as e:
                    logger.error(f"Error getting channel entity for {channel_username}: {e}")
                    return []
            
            channel = self.channel_cache[channel_username]
            messages = []
            
            # Get state to track last processed message
            state_key = f"last_message_{channel_username.replace('@', '')}"
            if self.state_manager:
                current_state = self.state_manager.load_state()
                last_processed_id = current_state.get(state_key, 0)
            else:
                last_processed_id = 0
            
            new_last_processed_id = last_processed_id
            
            # Get recent messages
            async for message in self.client_manager.client.iter_messages(channel, limit=limit):
                if not message.text:
                    continue
                
                # Skip if we've already processed this message
                if message.id <= last_processed_id:
                    break
                
                # Update the newest message ID we've seen
                if message.id > new_last_processed_id:
                    new_last_processed_id = message.id
                
                # Prepare media info if present
                media_info = None
                if ENABLE_MEDIA_PROCESSING and message.media:
                    if isinstance(message.media, (MessageMediaPhoto, MessageMediaDocument)):
                        media_info = {
                            'type': type(message.media).__name__,
                            'media_id': message.id,
                            'file_id': getattr(message.media.photo, 'id', None) if hasattr(message.media, 'photo') else None
                        }
                
                messages.append((
                    message.id,
                    message.text,
                    message.date,
                    media_info
                ))
            
            # Update last processed message ID in state
            if self.state_manager and new_last_processed_id > last_processed_id:
                current_state = self.state_manager.load_state()
                current_state[state_key] = new_last_processed_id
                self.state_manager.save_state(current_state)
                logger.debug(f"Updated last processed message ID for {channel_username}: {new_last_processed_id}")
            
            logger.info(f"📥 Retrieved {len(messages)} new messages from {channel_username}")
            return messages
            
        except Exception as e:
            logger.error(f"Error getting messages from {channel_username}: {e}")
            return []

    async def check_approval_timeouts(self):
        """Check and handle approval timeouts with enhanced logging."""
        current_time = time.time()
        expired_items = []
        
        for approval_id, news_data in self.pending_news.items():
            age = current_time - news_data['timestamp']
            if age > ADMIN_APPROVAL_TIMEOUT:
                expired_items.append((approval_id, age))
        
        if expired_items:
            logger.info(f"⏰ Found {len(expired_items)} expired approval items")
            
            for approval_id, age in expired_items:
                hours = int(age // 3600)
                minutes = int((age % 3600) // 60)
                logger.info(f"⏰ Expired approval {approval_id} (age: {hours}h {minutes}m)")
                
                # Optionally notify admin about timeout
                try:
                    admin_bot = await self.get_admin_bot_entity()
                    if admin_bot:
                        timeout_msg = f"⏰ News approval {approval_id} has timed out ({hours}h {minutes}m old)"
                        await self.client_manager.client.send_message(admin_bot, timeout_msg)
                except Exception as e:
                    logger.error(f"Error sending timeout notification: {e}")
                
                del self.pending_news[approval_id]
            
            await self.save_pending_news()

    async def save_pending_news(self):
        """Save pending news to state with error handling."""
        try:
            if self.state_manager:
                state_data = {
                    'pending_news': self.pending_news,
                    'stats': self.stats,
                    'last_save': time.time()
                }
                self.state_manager.save_state(state_data)
                logger.debug(f"💾 Saved state with {len(self.pending_news)} pending items")
        except Exception as e:
            logger.error(f"Error saving pending news: {e}")

    async def load_pending_news(self):
        """Load pending news from state with error handling."""
        try:
            if self.state_manager:
                state = self.state_manager.load_state()
                self.pending_news = state.get('pending_news', {})
                saved_stats = state.get('stats', {})
                self.stats.update(saved_stats)
                
                # Clean up very old pending items (older than 24 hours)
                current_time = time.time()
                old_items = []
                for approval_id, news_data in self.pending_news.items():
                    if current_time - news_data['timestamp'] > 86400:  # 24 hours
                        old_items.append(approval_id)
                
                for approval_id in old_items:
                    del self.pending_news[approval_id]
                    logger.info(f"🗑️  Cleaned up old pending item: {approval_id}")
                
                if old_items:
                    await self.save_pending_news()
                
                logger.info(f"📂 Loaded {len(self.pending_news)} pending news items")
            
        except Exception as e:
            logger.error(f"Error loading pending news: {e}")
            self.pending_news = {}

    async def get_channel_info(self, channel_username):
        """Get information about a channel."""
        try:
            if not channel_username.startswith('@'):
                channel_username = '@' + channel_username
            
            channel = await self.client_manager.client.get_entity(channel_username)
            
            return {
                'id': channel.id,
                'title': getattr(channel, 'title', 'Unknown'),
                'username': getattr(channel, 'username', channel_username),
                'participants_count': getattr(channel, 'participants_count', 0)
            }
        except Exception as e:
            logger.error(f"Error getting info for {channel_username}: {e}")
            return None

    def get_statistics(self):
        """Get current processing statistics."""
        uptime = time.time() - self.stats.get('session_start', time.time())
        return {
            **self.stats,
            'pending_approvals': len(self.pending_news),
            'processed_messages_cache': len(self.processed_messages),
            'uptime_seconds': uptime,
            'uptime_hours': uptime / 3600
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
                    logger.info(f"📝 Processing message {message.id}: {message.text[:100]}...")
                    
                    # Force process regardless of previous processing
                    if self.news_detector:
                        is_news = self.news_detector.is_news(message.text)
                        logger.info(f"   📰 News detection: {is_news}")
                        
                        if is_news:
                            try:
                                from src.services.news_filter import NewsFilter
                                is_relevant, score, topics = NewsFilter.is_relevant_news(message.text)
                            except:
                                is_relevant, score, topics = True, 1, ["test"]
                            
                            logger.info(f"   🎯 Relevance: {is_relevant}, Score: {score}, Topics: {topics[:3]}")
                            
                            if is_relevant:
                                # Process without duplicate checking
                                cleaned = self.news_detector.clean_news_text(message.text)
                                approval_id = await self.send_to_approval_bot(cleaned, None, channel_username)
                                if approval_id:
                                    processed_count += 1
                                    logger.info(f"   ✅ Sent for approval: {approval_id}")
            
            logger.info(f"🔧 Force processing complete: {processed_count} items sent for approval")
            return processed_count > 0
            
        except Exception as e:
            logger.error(f"Error in force processing: {e}")
            return False

    async def test_news_detection(self, text):
        """Test news detection on specific text with detailed output."""
        print("🧪 Testing News Detection")
        print("=" * 50)
        print(f"📝 Text: {text[:200]}{'...' if len(text) > 200 else ''}")
        print(f"📏 Length: {len(text)} characters")
        
        # Test detection
        if self.news_detector:
            is_news = self.news_detector.is_news(text)
            print(f"📰 Detected as news: {is_news}")
            
            if is_news:
                # Test cleaning
                cleaned = self.news_detector.clean_news_text(text)
                print(f"🧹 Cleaned text: {cleaned[:300]}{'...' if len(cleaned) > 300 else ''}")
                
                # Test filtering
                try:
                    from src.services.news_filter import NewsFilter
                    is_relevant, score, topics = NewsFilter.is_relevant_news(cleaned)
                except:
                    is_relevant, score, topics = True, 1, ["test"]
                    
                print(f"🎯 Relevant: {is_relevant}")
                print(f"📊 Score: {score}")
                print(f"🏷️  Topics: {topics[:5]}")
                
                # Test segmentation
                segments = self.news_detector.split_combined_news(text)
                if len(segments) > 1:
                    print(f"📋 Split into {len(segments)} segments")
                
                # Test metadata extraction
                metadata = self.news_detector.extract_news_metadata(text)
                print(f"📋 Metadata: {metadata}")
                
                if is_relevant:
                    print("✅ This news would be sent for admin approval")
                else:
                    print("❌ This news would be filtered out")
                    
                return is_news, is_relevant
        else:
            print("❌ News detector not available")
            
        return False, False