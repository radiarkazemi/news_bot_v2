"""
Complete news handler with financial focus and approval workflow.
Handles news detection, filtering, approval, and publishing.
"""
import asyncio
import hashlib
import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

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
    NEWS_CHANNEL, TWITTER_NEWS_CHANNEL, CHANNEL_PROCESSING_DELAY
)

logger = logging.getLogger(__name__)

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
        
        logger.info("📰 News handler initialized with financial focus")

    async def initialize(self):
        """Initialize the news handler with Bot API."""
        try:
            self.bot_api = BotAPIClient()
            logger.info("✅ News handler initialized with Bot API")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Bot API: {e}")

    async def setup_approval_handler(self):
        """Set up the approval command handler."""
        try:
            client = self.client_manager.client
            
            @client.on(events.NewMessage(pattern=r'/submit(\w+)'))
            async def handle_approval_command(event):
                """Handle approval commands from admin bot."""
                try:
                    # Extract approval ID
                    approval_id = event.pattern_match.group(1)
                    logger.info(f"📥 Received approval command for: {approval_id}")
                    
                    # Check if we have this pending news
                    if approval_id not in self.pending_news:
                        await event.reply(f"❌ News item {approval_id} not found or already processed")
                        logger.warning(f"Approval ID {approval_id} not found in pending news")
                        return
                    
                    # Get news data
                    news_data = self.pending_news[approval_id]
                    logger.info(f"📋 Processing approval for news: {news_data['text'][:100]}...")
                    
                    # Publish the news
                    success = await self.publish_approved_news(news_data)
                    
                    if success:
                        # Success response
                        await event.reply(f"✅ News {approval_id} published successfully to channel!")
                        logger.info(f"✅ Successfully published approved news: {approval_id}")
                        
                        # Update statistics
                        self.stats['news_approved'] += 1
                        self.stats['news_published'] += 1
                        
                        # Remove from pending
                        del self.pending_news[approval_id]
                        await self.save_pending_news()
                        
                    else:
                        # Failure response
                        await event.reply(f"❌ Failed to publish news {approval_id}. Please try again or contact support.")
                        logger.error(f"❌ Failed to publish approved news: {approval_id}")
                        
                except Exception as e:
                    logger.error(f"❌ Error handling approval command for {approval_id}: {e}")
                    try:
                        await event.reply("❌ Error processing approval. Please contact support.")
                    except:
                        pass
            
            # Also handle rejection commands (optional)
            @client.on(events.NewMessage(pattern=r'/reject(\w+)'))
            async def handle_rejection_command(event):
                """Handle rejection commands from admin bot."""
                try:
                    approval_id = event.pattern_match.group(1)
                    logger.info(f"🚫 Received rejection command for: {approval_id}")
                    
                    if approval_id in self.pending_news:
                        # Remove from pending
                        news_data = self.pending_news[approval_id]
                        del self.pending_news[approval_id]
                        await self.save_pending_news()
                        
                        await event.reply(f"🚫 News {approval_id} rejected and removed from queue")
                        logger.info(f"🚫 News {approval_id} rejected and removed")
                    else:
                        await event.reply(f"❌ News item {approval_id} not found")
                        
                except Exception as e:
                    logger.error(f"Error handling rejection command: {e}")
                    try:
                        await event.reply("❌ Error processing rejection")
                    except:
                        pass
            
            logger.info("✅ News approval handler set up successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to set up approval handler: {e}")
            return False

    async def publish_approved_news(self, news_data):
        """Publish approved news to the target channel."""
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
                formatted_text = f"{formatted_text}\n\n📡 {NEW_ATTRIBUTION}"
            
            # Add timestamp if not present
            if "🕐" not in formatted_text:
                current_time = get_formatted_time()
                formatted_text = f"{formatted_text}\n🕐 {current_time}"
            
            # Publish to target channel - FIX: Properly await the async method
            logger.info(f"📤 Attempting to publish to channel {TARGET_CHANNEL_ID}")
            
            # Create async context and properly await the send_message
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
            return False

    async def process_news_messages(self, channel_username):
        """Process news messages from a channel with financial focus."""
        logger.info(f"🔍 Processing financial news from channel: {channel_username}")
        
        try:
            # Get channel entity
            if not channel_username.startswith('@'):
                channel_username = '@' + channel_username
            
            channel_entity = await self.client_manager.client.get_entity(channel_username)
            
            # Get recent messages (last 3 hours)
            # CORRECT - uses setting:
            from config.settings import MESSAGE_LOOKBACK_HOURS
            cutoff_time = datetime.now() - timedelta(hours=MESSAGE_LOOKBACK_HOURS)
            
            messages_processed = 0
            news_sent_for_approval = 0
            total_messages = 0
            
            logger.info(f"📥 Retrieving recent messages from {channel_username}")
            
            # CORRECT - uses setting:
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
                        if i == 0 and message.media:
                            media = self._extract_media_info(message, channel_username)
                        
                        # Send for approval
                        approval_id = await self.send_to_approval_bot(
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
        """Extract media information from message."""
        try:
            if isinstance(message.media, MessageMediaPhoto):
                return {
                    "type": "photo",
                    "media_id": message.media.photo.id,
                    "message_id": message.id,
                    "channel": channel_username
                }
            elif isinstance(message.media, MessageMediaDocument):
                document = message.media.document
                # Check if it's an image document
                if any(hasattr(attr, 'mime_type') and attr.mime_type.startswith('image/') 
                       for attr in document.attributes):
                    return {
                        "type": "document",
                        "media_id": document.id,
                        "message_id": message.id,
                        "channel": channel_username
                    }
        except Exception as e:
            logger.warning(f"Error extracting media info: {e}")
        
        return None

    async def send_to_approval_bot(self, news_text, media=None, source_channel=None, analysis=None):
        """Send financial news to admin bot for approval."""
        try:
            # Generate unique approval ID
            content_hash = hashlib.md5(news_text.encode()).hexdigest()[:6]
            timestamp_id = str(int(time.time() * 1000))[-6:]
            approval_id = f"{timestamp_id}{content_hash}"
            
            # Get admin bot entity
            admin_bot_entity = await self.get_admin_bot_entity()
            if not admin_bot_entity:
                logger.error("❌ Could not get admin bot entity")
                return None
            
            # Format analysis info
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
            
            # Format approval message
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
                f"➡️ <b>To approve:</b> <code>/submit{approval_id}</code>\n"
                f"➡️ <b>To reject:</b> <code>/reject{approval_id}</code>"
            )
            
            # Send to admin bot
            message = await self.client_manager.client.send_message(
                admin_bot_entity,
                approval_message,
                parse_mode='html'
            )
            
            if message:
                # Store pending news
                self.pending_news[approval_id] = {
                    'text': news_text,
                    'formatted_text': news_text,
                    'original_text': news_text,
                    'message_id': message.id,
                    'timestamp': time.time(),
                    'source_channel': source_channel,
                    'has_media': media is not None,
                    'media': media,
                    'analysis': analysis,
                    'approval_source': 'telegram',
                    'status': 'pending'
                }
                
                # Save state
                await self.save_pending_news()
                
                logger.info(f"📤 Financial news sent for approval: {approval_id}")
                return approval_id
            else:
                logger.error("❌ Failed to send message to admin bot")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error sending to approval bot: {e}")
            return None

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
        """Load pending news from state file."""
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
                             max(1, self.stats.get('messages_processed', 1))) * 100
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
                            approval_id = await self.send_to_approval_bot(
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