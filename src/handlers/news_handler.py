"""
Complete News Handler for Financial News Detection and Approval Workflow
This is the FINAL, COMPLETE version with all fixes and optimizations.

Features:
- ✅ Working auto-deletion system (server optimized)
- ✅ Financial news detection with lowered thresholds  
- ✅ Persian calendar timestamps
- ✅ Media handling (images with news)
- ✅ Rate limiting protection
- ✅ Enhanced error handling
- ✅ Server environment optimizations
- ✅ Debug commands for troubleshooting
- ✅ Comprehensive logging
"""
import asyncio
import hashlib
import json
import logging
import os
import time
import re
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
from telethon.errors import FloodWaitError, ChatAdminRequiredError, MessageDeleteForbiddenError
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument

# Import services
from src.services.news_detector import NewsDetector
from src.services.news_filter import NewsFilter
from src.client.bot_api import BotAPIClient
from src.utils.time_utils import get_current_time, get_formatted_time
from config.settings import (
    TARGET_CHANNEL_ID, ADMIN_BOT_USERNAME, NEW_ATTRIBUTION,
    NEWS_CHANNEL, TWITTER_NEWS_CHANNEL, CHANNEL_PROCESSING_DELAY,
    ENABLE_MEDIA_PROCESSING
)

logger = logging.getLogger(__name__)

class SimpleRateLimiter:
    """Enhanced rate limiter for server environments."""
    
    def __init__(self, min_delay=8, max_queue_size=30):
        self.min_delay = min_delay
        self.max_queue_size = max_queue_size
        self.last_send_time = 0
        self.pending_queue = deque()
        self.processing = False
        self.stats = {
            'queued': 0,
            'sent': 0,
            'dropped': 0,
            'errors': 0
        }
    
    async def add_to_queue(self, send_func, *args, **kwargs):
        """Add a send operation to the rate-limited queue."""
        if len(self.pending_queue) >= self.max_queue_size:
            logger.warning(f"🚫 Queue full ({self.max_queue_size}), dropping message")
            self.stats['dropped'] += 1
            return None
        
        self.pending_queue.append((send_func, args, kwargs))
        self.stats['queued'] += 1
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
                        self.stats['sent'] += 1
                    else:
                        logger.warning("⚠️ Rate-limited send failed")
                        self.stats['errors'] += 1
                        
                except Exception as e:
                    logger.error(f"❌ Error in rate-limited send: {e}")
                    self.stats['errors'] += 1
                
                # Brief pause between sends
                await asyncio.sleep(1)
        
        finally:
            self.processing = False

class NewsHandler:
    """Complete news handler for financial news detection and approval workflow."""

    def __init__(self, client_manager):
        """Initialize the news handler with all features."""
        self.client_manager = client_manager
        self.bot_api = None
        self.news_detector = NewsDetector()
        self.pending_news = {}
        self.processed_messages = set()
        self.admin_bot_entity = None
        
        # Track admin message IDs for deletion
        self.admin_messages = {}  # approval_id -> message_info
        
        # Rate limiter with server-optimized settings
        self.rate_limiter = SimpleRateLimiter(min_delay=8, max_queue_size=30)
        
        # Statistics
        self.stats = {
            'messages_processed': 0,
            'news_detected': 0,
            'news_filtered_out': 0,
            'news_sent_for_approval': 0,
            'news_approved': 0,
            'news_published': 0,
            'errors': 0,
            'session_start': time.time(),
            'media_processed': 0,
            'deletions_attempted': 0,
            'deletions_successful': 0
        }
        
        # State file path
        self.state_file = Path("data/state/news_handler_state.json")
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Media directories
        if ENABLE_MEDIA_PROCESSING and MEDIA_SUPPORT:
            self.media_dir = Path("data/media")
            self.temp_media_dir = self.media_dir / "temp"
            self.media_dir.mkdir(exist_ok=True)
            self.temp_media_dir.mkdir(exist_ok=True)
        
        # Start periodic cleanup task
        asyncio.create_task(self._periodic_cleanup_task())
        
        logger.info("📰 Complete News Handler initialized with all features")

    async def initialize(self):
        """Initialize the news handler with Bot API and media cleanup."""
        try:
            # Initialize Bot API
            self.bot_api = BotAPIClient()
            
            # Start periodic media cleanup if enabled
            if MEDIA_SUPPORT and ENABLE_MEDIA_PROCESSING:
                asyncio.create_task(self._periodic_media_cleanup())
                logger.info("🧹 Periodic media cleanup started")
            
            logger.info("✅ News handler fully initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize news handler: {e}")

    async def _periodic_cleanup_task(self):
        """Periodic task to clean up processed messages."""
        while True:
            try:
                await asyncio.sleep(1800)  # Run every 30 minutes
                logger.info("🧹 Running periodic message cleanup...")
                await self.cleanup_all_processed_messages()
            except asyncio.CancelledError:
                logger.info("Periodic cleanup task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in periodic cleanup task: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error

    async def _periodic_media_cleanup(self):
        """Periodic cleanup of old media files."""
        while True:
            try:
                await asyncio.sleep(3600)  # Every hour
                await self.cleanup_old_media_files()
            except asyncio.CancelledError:
                logger.info("Media cleanup task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in periodic media cleanup: {e}")
                await asyncio.sleep(300)

    async def setup_approval_handler(self):
        """Set up the approval command handler with all debug commands."""
        try:
            client = self.client_manager.client
            
            # Main approval commands
            @client.on(events.NewMessage(pattern=r'/submit(\w+)'))
            async def handle_approval_command(event):
                """Handle approval commands from admin bot."""
                try:
                    approval_id = event.pattern_match.group(1)
                    logger.info(f"📥 Approval command received: /submit{approval_id}")
                    await self._process_approval(approval_id, event)
                except Exception as e:
                    logger.error(f"❌ Error handling approval command: {e}")
            
            @client.on(events.NewMessage(pattern=r'/reject(\w+)'))
            async def handle_rejection_command(event):
                """Handle rejection commands from admin bot."""
                try:
                    approval_id = event.pattern_match.group(1)
                    logger.info(f"🚫 Rejection command received: /reject{approval_id}")
                    await self._process_rejection(approval_id, event)
                except Exception as e:
                    logger.error(f"❌ Error handling rejection command: {e}")
            
            # Debug commands for troubleshooting
            @client.on(events.NewMessage(pattern=r'/test_deletion'))
            async def handle_test_deletion_command(event):
                """Test deletion functionality."""
                try:
                    logger.info(f"🧪 Test deletion command received from user {event.sender_id}")
                    
                    await event.respond("🧪 Testing admin bot connection and deletion...")
                    
                    test_result = await self.test_admin_bot_connection()
                    
                    if test_result:
                        await event.respond("✅ Admin bot connection test passed!")
                        logger.info("✅ Admin bot test passed")
                    else:
                        await event.respond("❌ Admin bot connection test failed! Check logs for details.")
                        logger.error("❌ Admin bot test failed")
                    
                except Exception as e:
                    logger.error(f"Error in test deletion command: {e}")
                    await event.respond(f"❌ Test error: {e}")

            @client.on(events.NewMessage(pattern=r'/force_delete (\w+)'))
            async def handle_force_delete_command(event):
                """Force delete messages for a specific approval ID."""
                try:
                    approval_id = event.pattern_match.group(1)
                    logger.info(f"🗑️ Force delete command received for: {approval_id}")
                    
                    await event.respond(f"🗑️ Force deleting messages for approval: {approval_id}")
                    
                    success = await self._delete_messages_for_approval_enhanced(approval_id)
                    
                    if success:
                        await event.respond(f"✅ Force deletion completed for {approval_id}")
                        logger.info(f"✅ Force deletion succeeded for {approval_id}")
                    else:
                        await event.respond(f"❌ Force deletion failed for {approval_id} - check logs")
                        logger.error(f"❌ Force deletion failed for {approval_id}")
                    
                except Exception as e:
                    logger.error(f"Error in force delete command: {e}")
                    await event.respond(f"❌ Force delete error: {e}")

            @client.on(events.NewMessage(pattern=r'/show_pending'))
            async def handle_show_pending_command(event):
                """Show current pending approvals."""
                try:
                    logger.info(f"📋 Show pending command received")
                    
                    pending_count = len(self.pending_news)
                    if pending_count == 0:
                        await event.respond("📋 No pending approvals")
                    else:
                        pending_list = list(self.pending_news.keys())[:10]  # Show first 10
                        pending_text = "\n".join([f"• {approval_id}" for approval_id in pending_list])
                        message = f"📋 Pending approvals ({pending_count}):\n{pending_text}"
                        if pending_count > 10:
                            message += f"\n... and {pending_count - 10} more"
                        await event.respond(message)
                    
                except Exception as e:
                    logger.error(f"Error in show pending command: {e}")
                    await event.respond(f"❌ Error: {e}")

            @client.on(events.NewMessage(pattern=r'/stats'))
            async def handle_stats_command(event):
                """Show bot statistics."""
                try:
                    logger.info(f"📊 Stats command received")
                    
                    stats_text = f"📊 **Bot Statistics**\n\n"
                    stats_text += f"📝 Messages Processed: {self.stats['messages_processed']}\n"
                    stats_text += f"📰 News Detected: {self.stats['news_detected']}\n"
                    stats_text += f"📤 Sent for Approval: {self.stats['news_sent_for_approval']}\n"
                    stats_text += f"✅ Approved: {self.stats['news_approved']}\n"
                    stats_text += f"📢 Published: {self.stats['news_published']}\n"
                    stats_text += f"📎 Media Processed: {self.stats['media_processed']}\n"
                    stats_text += f"🗑️ Deletions: {self.stats['deletions_successful']}/{self.stats['deletions_attempted']}\n"
                    stats_text += f"❌ Errors: {self.stats['errors']}\n"
                    stats_text += f"📋 Pending: {len(self.pending_news)}\n"
                    
                    # Rate limiter stats
                    rate_stats = self.rate_limiter.stats
                    stats_text += f"\n📊 **Rate Limiter**\n"
                    stats_text += f"📥 Queued: {rate_stats['queued']}\n"
                    stats_text += f"📤 Sent: {rate_stats['sent']}\n"
                    stats_text += f"🚫 Dropped: {rate_stats['dropped']}\n"
                    
                    # Uptime
                    uptime = time.time() - self.stats['session_start']
                    hours = int(uptime // 3600)
                    minutes = int((uptime % 3600) // 60)
                    stats_text += f"\n⏰ Uptime: {hours}h {minutes}m"
                    
                    await event.respond(stats_text)
                    
                except Exception as e:
                    logger.error(f"Error in stats command: {e}")
                    await event.respond(f"❌ Error: {e}")

            @client.on(events.NewMessage(pattern=r'/cleanup'))
            async def handle_cleanup_command(event):
                """Manual cleanup of old approval messages."""
                try:
                    logger.info(f"🧹 Cleanup command received")
                    
                    await event.respond("🧹 Starting cleanup of processed messages...")
                    
                    await self.cleanup_all_processed_messages()
                    
                    await event.respond("✅ Cleanup complete!")
                    
                except Exception as e:
                    logger.error(f"Error in cleanup command: {e}")
                    await event.respond(f"❌ Cleanup error: {e}")
            
            logger.info("✅ News approval handler set up successfully with all debug commands")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to set up approval handler: {e}")
            return False

    async def test_admin_bot_connection(self):
        """Enhanced test method to verify admin bot connection and permissions."""
        try:
            logger.info("🧪 Testing admin bot connection with enhanced checks...")
            
            admin_bot = await self.get_admin_bot_entity()
            if not admin_bot:
                logger.error("❌ TEST FAILED: Cannot get admin bot entity")
                return False
            
            logger.info(f"✅ Admin bot found: {admin_bot.username if hasattr(admin_bot, 'username') else admin_bot.id}")
            
            # Test 1: Check if we can read messages
            message_count = 0
            try:
                async for message in self.client_manager.client.iter_messages(admin_bot, limit=5):
                    message_count += 1
                    logger.info(f"📝 Test message {message.id}: {message.text[:50] if message.text else 'No text'}...")
            except Exception as read_error:
                logger.error(f"❌ Cannot read messages: {read_error}")
                return False
            
            logger.info(f"✅ Can read {message_count} messages from admin bot")
            
            # Test 2: Check if we can send and delete messages
            try:
                test_msg = await self.client_manager.client.send_message(
                    admin_bot, 
                    "🧪 Enhanced test message - will be deleted in 3 seconds"
                )
                logger.info(f"✅ Test message sent: {test_msg.id}")
                
                await asyncio.sleep(3)
                
                # Check if message is outgoing before deletion
                if test_msg.out:
                    await test_msg.delete()
                    logger.info(f"✅ Test message deleted successfully")
                else:
                    logger.warning("⚠️ Test message is not outgoing, skipping deletion")
                
                return True
                
            except Exception as test_error:
                logger.error(f"❌ Cannot send/delete test messages: {test_error}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Admin bot connection test failed: {e}")
            return False

    async def _process_approval(self, approval_id, event):
        """Process approval request with enhanced deletion."""
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
            # Success response (will be deleted shortly)
            response_text = f"✅ News {approval_id} published successfully to channel!"
            response_msg = await event.respond(response_text)
            
            logger.info(f"✅ Successfully published approved news: {approval_id}")
            
            # Update statistics
            self.stats['news_approved'] += 1
            self.stats['news_published'] += 1
            
            # Remove from pending
            del self.pending_news[approval_id]
            await self.save_pending_news()
            
            # 🚨 FIX: Call the correct deletion method
            logger.info(f"🗑️ Starting deletion process for approval {approval_id}")
            deletion_success = await self._delete_messages_for_approval_enhanced(approval_id)
            
            if deletion_success:
                logger.info(f"✅ Successfully deleted all messages for {approval_id}")
                self.stats['deletions_successful'] = self.stats.get('deletions_successful', 0) + 1
            else:
                logger.warning(f"⚠️ Some issues occurred during deletion for {approval_id}")
            
            self.stats['deletions_attempted'] = self.stats.get('deletions_attempted', 0) + 1
            
            # Delete the success response after showing it briefly
            await asyncio.sleep(3)
            try:
                await response_msg.delete()
                logger.info(f"🗑️ Deleted success response for {approval_id}")
            except Exception as e:
                logger.warning(f"Could not delete success response: {e}")
        else:
            # Failure response
            error_text = f"❌ Failed to publish news {approval_id}. Please try again or contact support."
            await event.respond(error_text)
            
            logger.error(f"❌ Failed to publish approved news: {approval_id}")

    async def _process_rejection(self, approval_id, event):
        """Process rejection request with enhanced deletion."""
        logger.info(f"🚫 Received rejection for: {approval_id}")
        
        response_msg = None
        
        if approval_id in self.pending_news:
            # Remove from pending
            news_data = self.pending_news[approval_id]
            del self.pending_news[approval_id]
            await self.save_pending_news()
            
            response_text = f"🚫 News {approval_id} rejected and removed from queue"
            response_msg = await event.respond(response_text)
            
            logger.info(f"🚫 News {approval_id} rejected and removed")
        else:
            response_msg = await event.respond(f"❌ News item {approval_id} not found")
        
        # 🚨 FIX: Call the correct deletion method
        logger.info(f"🗑️ Starting deletion process for rejection {approval_id}")
        deletion_success = await self._delete_messages_for_approval_enhanced(approval_id)
        
        if deletion_success:
            logger.info(f"✅ Successfully deleted all messages for {approval_id}")
            self.stats['deletions_successful'] = self.stats.get('deletions_successful', 0) + 1
        else:
            logger.warning(f"⚠️ Some issues occurred during deletion for {approval_id}")
        
        self.stats['deletions_attempted'] = self.stats.get('deletions_attempted', 0) + 1
        
        # Delete the rejection response after showing it briefly
        if response_msg:
            await asyncio.sleep(3)
            try:
                await response_msg.delete()
                logger.info(f"🗑️ Deleted rejection response for {approval_id}")
            except Exception as e:
                logger.warning(f"Could not delete rejection response: {e}")

    async def _delete_messages_for_approval_enhanced(self, approval_id):
        """
        ENHANCED VERSION: Delete ALL messages related to an approval ID.
        Fixed for server compatibility - removes 'from_user' parameter issue.
        """
        try:
            logger.info(f"🗑️ [ENHANCED] Starting deletion process for approval {approval_id}")
            
            # Get admin bot entity
            admin_bot = await self.get_admin_bot_entity()
            if not admin_bot:
                logger.error(f"❌ [ENHANCED] Cannot delete messages: admin bot entity not found")
                return False
            
            logger.info(f"✅ [ENHANCED] Admin bot found: {admin_bot.username if hasattr(admin_bot, 'username') else admin_bot.id}")
            
            deleted_count = 0
            found_messages = []
            
            logger.info(f"🔍 [ENHANCED] Searching for messages containing approval ID: {approval_id}")
            
            # Enhanced search with comprehensive error handling
            try:
                search_count = 0
                
                # FIX: Remove 'from_user' parameter for better server compatibility
                # Instead, check if message is outgoing (sent by us)
                async for message in self.client_manager.client.iter_messages(
                    admin_bot,
                    limit=200  # Reasonable limit
                ):
                    search_count += 1
                    
                    # Skip if not our message (outgoing)
                    if not message.out:
                        continue
                    
                    # Skip if no text
                    if not message.text:
                        continue
                    
                    # Check if this message is related to our approval
                    should_delete = False
                    delete_reason = ""
                    
                    # Comprehensive message type detection
                    if approval_id in message.text:
                        if any(phrase in message.text for phrase in [
                            "FINANCIAL NEWS PENDING APPROVAL",
                            "📈 <b>FINANCIAL NEWS PENDING APPROVAL</b>",
                            f"🆔 ID: <code>{approval_id}</code>"
                        ]):
                            should_delete = True
                            delete_reason = "approval message"
                        
                        elif any(phrase in message.text for phrase in [
                            f"/submit{approval_id}",
                            f"/reject{approval_id}",
                            f"➡️ To approve: /submit{approval_id}",
                            f"➡️ To reject: /reject{approval_id}"
                        ]):
                            should_delete = True
                            delete_reason = "command message"
                        
                        elif any(phrase in message.text for phrase in [
                            "published successfully",
                            "rejected and removed",
                            "not found or already processed",
                            f"News {approval_id} published",
                            f"News {approval_id} rejected"
                        ]):
                            should_delete = True
                            delete_reason = "response message"
                    
                    if should_delete:
                        found_messages.append((message, delete_reason))
                        logger.info(f"📝 [ENHANCED] Found {delete_reason} to delete: Message ID {message.id}")
                
                logger.info(f"📊 [ENHANCED] Searched {search_count} messages, found {len(found_messages)} to delete")
            
            except Exception as search_error:
                logger.error(f"❌ [ENHANCED] Error searching messages: {search_error}")
                return False
            
            # Enhanced deletion with comprehensive error handling
            if found_messages:
                for message, reason in found_messages:
                    try:
                        # Try to delete the message
                        await message.delete()
                        deleted_count += 1
                        logger.info(f"🗑️ [ENHANCED] Deleted {reason}: Message ID {message.id}")
                        
                        # Adaptive delay based on environment
                        await asyncio.sleep(1.5)
                        
                    except Exception as delete_error:
                        logger.warning(f"⚠️ [ENHANCED] Could not delete message {message.id} ({reason}): {delete_error}")
                        continue
            else:
                logger.warning(f"⚠️ [ENHANCED] No messages found to delete for approval {approval_id}")
            
            # Clean up tracking
            if approval_id in self.admin_messages:
                del self.admin_messages[approval_id]
                logger.debug(f"🧹 [ENHANCED] Removed {approval_id} from tracking")
            
            # Final report
            if deleted_count > 0:
                logger.info(f"✅ [ENHANCED] SUCCESS: Deleted {deleted_count}/{len(found_messages)} messages for {approval_id}")
                return True
            else:
                logger.warning(f"⚠️ [ENHANCED] PARTIAL: Found {len(found_messages)} messages but deleted 0")
                return False
                
        except Exception as main_error:
            logger.error(f"❌ [ENHANCED] CRITICAL ERROR in deletion for {approval_id}: {main_error}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return False


    async def cleanup_all_processed_messages(self):
        """Clean up all messages for processed approvals - Fixed version."""
        try:
            admin_bot = await self.get_admin_bot_entity()
            if not admin_bot:
                logger.warning("Cannot cleanup: admin bot entity not available")
                return
            
            # Get current pending approval IDs
            current_pending = set(self.pending_news.keys())
            logger.info(f"🧹 Starting cleanup. Current pending: {len(current_pending)} items")
            
            deleted_count = 0
            checked_count = 0
            
            # FIX: Remove 'from_user' parameter and check message.out instead
            async for message in self.client_manager.client.iter_messages(
                admin_bot,
                limit=300  # Check more messages
            ):
                checked_count += 1
                
                # Skip if not our message
                if not message.out:
                    continue
                
                if not message.text:
                    continue
                
                # Look for approval messages
                if "FINANCIAL NEWS PENDING APPROVAL" in message.text:
                    # Extract approval ID from message
                    import re
                    match = re.search(r'ID: <code>(\w+)</code>', message.text)
                    if match:
                        found_approval_id = match.group(1)
                        
                        # If this approval is no longer pending, delete the message
                        if found_approval_id not in current_pending:
                            try:
                                await message.delete()
                                deleted_count += 1
                                logger.debug(f"🗑️ Cleaned processed message for {found_approval_id}")
                                await asyncio.sleep(0.5)  # Rate limit protection
                            except Exception as e:
                                logger.warning(f"Could not delete processed message: {e}")
            
            if deleted_count > 0:
                logger.info(f"🧹 Cleanup complete: deleted {deleted_count} processed messages (checked {checked_count})")
            else:
                logger.info(f"🧹 Cleanup complete: no processed messages found (checked {checked_count})")
                
        except Exception as e:
            logger.error(f"Error in cleanup_all_processed_messages: {e}")

    async def cleanup_old_media_files(self):
        """Clean up old media files."""
        try:
            if not hasattr(self, 'temp_media_dir') or not self.temp_media_dir.exists():
                return
            
            cleaned_count = 0
            current_time = time.time()
            max_age = 3600  # 1 hour
            
            for media_file in self.temp_media_dir.glob("news_media_*"):
                try:
                    file_age = current_time - media_file.stat().st_mtime
                    if file_age > max_age:
                        media_file.unlink()
                        cleaned_count += 1
                        logger.debug(f"🧹 Cleaned old media: {media_file}")
                except Exception as e:
                    logger.warning(f"Error cleaning media file {media_file}: {e}")
            
            if cleaned_count > 0:
                logger.info(f"🧹 Cleaned {cleaned_count} old media files")
                
        except Exception as e:
            logger.error(f"Error in media cleanup: {e}")

    async def publish_approved_news(self, news_data):
        """Publish approved news to the target channel with Persian calendar timestamp."""
        try:
            # Get formatted text
            formatted_text = news_data.get('formatted_text', news_data['text'])
            
            # Ensure proper financial emoji formatting
            if not formatted_text.startswith(('💰', '💱', '🏆', '₿', '🛢️', '📈')):
                # Add appropriate financial emoji based on content
                text_lower = formatted_text.lower()
                if any(kw in text_lower for kw in ['طلا', 'سکه', 'gold']):
                    formatted_text = f"🏆 {formatted_text}"
                elif any(kw in text_lower for kw in ['دلار', 'یورو', 'ارز', 'dollar', 'euro']):
                    formatted_text = f"💱 {formatted_text}"
                elif any(kw in text_lower for kw in ['بیت‌کوین', 'bitcoin', 'crypto']):
                    formatted_text = f"₿ {formatted_text}"
                elif any(kw in text_lower for kw in ['نفت', 'گاز', 'oil', 'gas']):
                    formatted_text = f"🛢️ {formatted_text}"
                else:
                    formatted_text = f"📈 {formatted_text}"
            
            # Add attribution if not present
            if NEW_ATTRIBUTION and NEW_ATTRIBUTION not in formatted_text:
                formatted_text = f"{formatted_text}\n📡 {NEW_ATTRIBUTION}"
            
            # Add Persian calendar timestamp
            current_time = get_formatted_time(format_type="persian_full")
            formatted_text = f"{formatted_text}\n🕐 {current_time}"
            
            logger.info(f"📤 Attempting to publish to channel {TARGET_CHANNEL_ID}")
            
            # Try to publish with media if available
            media_info = news_data.get('media')
            published = False
            
            if media_info and news_data.get('has_media'):
                try:
                    # Get the source channel and message
                    channel_name = media_info['channel']
                    message_id = media_info['message_id']
                    
                    if not channel_name.startswith('@'):
                        channel_name = f"@{channel_name}"
                    
                    logger.info(f"📥 Getting media from {channel_name}, message {message_id}")
                    
                    # Get channel entity and original message
                    channel_entity = await self.client_manager.client.get_entity(channel_name)
                    original_message = await self.client_manager.client.get_messages(
                        channel_entity, 
                        ids=message_id
                    )
                    
                    if original_message and original_message.media:
                        # Send to target channel with media
                        result = await self.client_manager.client.send_message(
                            TARGET_CHANNEL_ID,
                            formatted_text,
                            parse_mode='html',
                            file=original_message.media
                        )
                        
                        if result:
                            logger.info(f"📢 Financial news with media published to channel {TARGET_CHANNEL_ID}")
                            logger.info(f"🆔 Published message ID: {result.id}")
                            published = True
                            self.stats['media_processed'] += 1
                        
                except Exception as media_error:
                    logger.error(f"Error publishing with media: {media_error}")
            
            # If not published with media, try text-only
            if not published:
                try:
                    # Try with Telethon first
                    result = await self.client_manager.client.send_message(
                        TARGET_CHANNEL_ID,
                        formatted_text,
                        parse_mode='html'
                    )
                    
                    if result:
                        logger.info(f"📢 Financial news published to channel (text-only)")
                        logger.info(f"🆔 Published message ID: {result.id}")
                        published = True
                except Exception as telethon_error:
                    logger.warning(f"Telethon send failed: {telethon_error}")
                    
                    # Try Bot API as fallback
                    if self.bot_api:
                        try:
                            async with self.bot_api as api_client:
                                result = await api_client.send_message(
                                    chat_id=TARGET_CHANNEL_ID,
                                    text=formatted_text,
                                    parse_mode='HTML'
                                )
                            
                            if result:
                                logger.info(f"📢 News published via Bot API (fallback)")
                                published = True
                        except Exception as bot_error:
                            logger.error(f"Bot API also failed: {bot_error}")
            
            return published
                
        except Exception as e:
            logger.error(f"❌ Error publishing approved news: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return False

    async def process_news_messages(self, channel_username):
        """Process news messages from a channel with enhanced financial detection."""
        logger.info(f"🔍 Processing financial news from channel: {channel_username}")
        
        try:
            # Get channel entity
            if not channel_username.startswith('@'):
                channel_username = '@' + channel_username
            
            channel_entity = await self.client_manager.client.get_entity(channel_username)
            
            # Get recent messages (configurable lookback)
            from config.settings import MESSAGE_LOOKBACK_HOURS, MAX_MESSAGES_PER_CHECK
            cutoff_time = datetime.now() - timedelta(hours=MESSAGE_LOOKBACK_HOURS)
            
            messages_processed = 0
            news_sent_for_approval = 0
            total_messages = 0
            
            logger.info(f"📥 Retrieving recent messages from {channel_username}")
            
            async for message in self.client_manager.client.iter_messages(channel_entity, limit=MAX_MESSAGES_PER_CHECK):
                try:
                    total_messages += 1
                    
                    # Skip if too old
                    if message.date.replace(tzinfo=None) < cutoff_time:
                        continue
                    
                    # Skip if no text or too short
                    if not message.text or len(message.text.strip()) < 30:
                        continue
                    
                    # Check if already processed
                    message_key = f"{channel_username.replace('@', '')}:{message.id}"
                    if message_key in self.processed_messages:
                        continue
                    
                    messages_processed += 1
                    self.stats['messages_processed'] += 1
                    
                    logger.debug(f"📝 Analyzing message {message.id}: {message.text[:100]}...")
                    
                    # Enhanced financial news detection
                    if not self.news_detector.is_news(message.text):
                        logger.debug(f"Message {message.id} not detected as financial news")
                        continue
                    
                    logger.info(f"📰 Financial news detected in message {message.id}")
                    self.stats['news_detected'] += 1
                    
                    # Enhanced relevance filtering with lower thresholds
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
                               f"category={category}, priority={priority}")
                    
                    # Handle multiple news segments if present
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
                
                # Check if it's an image document
                if document.mime_type and document.mime_type.startswith('image/'):
                    return {
                        "type": "document_image",
                        "media_id": document.id,
                        "message_id": message.id,
                        "channel": channel_username.replace('@', ''),
                        "mime_type": document.mime_type,
                        "file_size": getattr(document, 'size', 0),
                        "has_spoiler": getattr(message.media, 'spoiler', False)
                    }
                    
        except Exception as e:
            logger.warning(f"Error extracting media info: {e}")
        
        return None

    async def send_to_approval_bot_rate_limited(self, news_text, media=None, source_channel=None, analysis=None):
        """Rate-limited version of send_to_approval_bot."""
        try:
            # Check priority - prioritize higher scores
            if analysis:
                score = analysis.get('score', 0)
                priority = analysis.get('priority', 'NORMAL')
                
                # Skip very low priority during high activity
                if score < 2 and len(self.rate_limiter.pending_queue) > 15:
                    logger.info(f"🚫 Skipping very low priority news (score: {score}, queue: {len(self.rate_limiter.pending_queue)})")
                    self.rate_limiter.stats['dropped'] += 1
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
                return None
                
        except Exception as e:
            logger.error(f"❌ Error in rate-limited approval: {e}")
            self.rate_limiter.stats['errors'] += 1
            return None

    async def _send_approval_message(self, news_text, media, source_channel, analysis, approval_id):
        """Internal method to send approval message with media and clickable commands."""
        try:
            # Get admin bot entity
            admin_bot_entity = await self.get_admin_bot_entity()
            if not admin_bot_entity:
                logger.error("❌ Could not get admin bot entity")
                return False
            
            # Format approval message with enhanced information
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
            
            current_time = get_formatted_time(format_type='persian_full')
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
            
            # Send message with media if available
            message = None
            
            if media and media.get('channel') and media.get('message_id'):
                try:
                    # Get the source channel and message
                    channel_name = media['channel']
                    if not channel_name.startswith('@'):
                        channel_name = f"@{channel_name}"
                    
                    # Get channel entity and original message
                    channel_entity = await self.client_manager.client.get_entity(channel_name)
                    original_message = await self.client_manager.client.get_messages(
                        channel_entity, 
                        ids=media['message_id']
                    )
                    
                    if original_message and original_message.media:
                        # Send message with media
                        message = await self.client_manager.client.send_message(
                            admin_bot_entity,
                            approval_message,
                            parse_mode='html',
                            file=original_message.media
                        )
                        
                        if message:
                            logger.info(f"✅ Approval sent with media: {approval_id}")
                        
                except Exception as media_error:
                    logger.warning(f"Could not send media with approval: {media_error}")
            
            # Send text-only message if media failed or not available
            if not message:
                message = await self.client_manager.client.send_message(
                    admin_bot_entity,
                    approval_message,
                    parse_mode='html'
                )
            
            if message:
                logger.info(f"📤 Approval sent with ID: {approval_id}, Message ID: {message.id}")
                
                # Store message info for deletion tracking
                self.admin_messages[approval_id] = {
                    'chat_id': admin_bot_entity.id,
                    'message_id': message.id,
                    'timestamp': time.time(),
                    'text_preview': approval_message[:50]
                }
                
                # Also store in pending news for persistence
                if approval_id in self.pending_news:
                    self.pending_news[approval_id]['admin_message_id'] = message.id
                    self.pending_news[approval_id]['admin_chat_id'] = admin_bot_entity.id
                
                # Save state immediately
                await self.save_pending_news()
                
                return True
            else:
                logger.error("❌ Failed to send approval message")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error sending approval message: {e}")
            return False

    async def get_admin_bot_entity(self):
        """Get the admin bot entity with caching and enhanced error handling."""
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
        """Load pending news and message tracking from state file."""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.pending_news = data.get('pending_news', {})
                    self.processed_messages = set(data.get('processed_messages', []))
                    
                    # Load statistics
                    saved_stats = data.get('stats', {})
                    for key, value in saved_stats.items():
                        if key in self.stats:
                            self.stats[key] = value
                    
                    # Load admin messages tracking
                    self.admin_messages = data.get('admin_messages', {})
                
                logger.info(f"📂 Loaded {len(self.pending_news)} pending news items")
                logger.info(f"📋 Tracking {len(self.admin_messages)} admin messages")
                logger.info(f"📊 Loaded statistics: {len(saved_stats)} items")
            else:
                logger.info("📂 No existing state file found, starting fresh")
                
        except Exception as e:
            logger.error(f"❌ Error loading pending news: {e}")
            self.pending_news = {}
            self.processed_messages = set()
            self.admin_messages = {}

    async def save_pending_news(self):
        """Save pending news and message tracking to state file."""
        try:
            data = {
                'pending_news': self.pending_news,
                'processed_messages': list(self.processed_messages),
                'stats': self.stats,
                'admin_messages': self.admin_messages,
                'last_updated': time.time(),
                'version': '2.0'
            }
            
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            logger.debug("💾 Complete state saved with message tracking")
            
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
                # Also remove from message map
                if news_id in self.admin_messages:
                    del self.admin_messages[news_id]
            
            if expired_ids:
                logger.info(f"🧹 Cleaned {len(expired_ids)} expired pending news items")
                await self.save_pending_news()
                
        except Exception as e:
            logger.error(f"❌ Error cleaning expired pending news: {e}")

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
                            
                            # Extract media if present
                            media = None
                            if message.media:
                                media = self._extract_media_info(message, channel_username)
                            
                            approval_id = await self.send_to_approval_bot_rate_limited(
                                cleaned, 
                                media, 
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

    def get_comprehensive_stats(self):
        """Get comprehensive statistics."""
        uptime = time.time() - self.stats.get('session_start', time.time())
        
        return {
            **self.stats,
            'pending_approvals': len(self.pending_news),
            'processed_messages_cache': len(self.processed_messages),
            'admin_messages_tracked': len(self.admin_messages),
            'uptime_seconds': uptime,
            'uptime_hours': uptime / 3600,
            'approval_rate': (self.stats.get('news_approved', 0) / 
                            max(1, self.stats.get('news_sent_for_approval', 1))) * 100,
            'detection_rate': (self.stats.get('news_detected', 0) / 
                             max(1, self.stats.get('messages_processed', 1))) * 100,
            'deletion_success_rate': (self.stats.get('deletions_successful', 0) / 
                                    max(1, self.stats.get('deletions_attempted', 1))) * 100,
            'media_support': MEDIA_SUPPORT and ENABLE_MEDIA_PROCESSING,
            'rate_limiter_stats': self.rate_limiter.stats,
            'queue_size': len(self.rate_limiter.pending_queue)
        }

    def log_comprehensive_stats(self):
        """Log comprehensive statistics."""
        stats = self.get_comprehensive_stats()
        
        logger.info("📊 COMPREHENSIVE NEWS HANDLER STATISTICS")
        logger.info("=" * 60)
        logger.info(f"📝 Messages Processed: {stats['messages_processed']}")
        logger.info(f"📰 News Detected: {stats['news_detected']} ({stats['detection_rate']:.1f}%)")
        logger.info(f"📤 Sent for Approval: {stats['news_sent_for_approval']}")
        logger.info(f"✅ Approved: {stats['news_approved']} ({stats['approval_rate']:.1f}%)")
        logger.info(f"📢 Published: {stats['news_published']}")
        logger.info(f"📎 Media Processed: {stats['media_processed']}")
        logger.info(f"🗑️ Deletions: {stats['deletions_successful']}/{stats['deletions_attempted']} ({stats['deletion_success_rate']:.1f}%)")
        logger.info(f"📋 Pending: {stats['pending_approvals']}")
        logger.info(f"📊 Queue Size: {stats['queue_size']}")
        logger.info(f"⏰ Uptime: {stats['uptime_hours']:.1f}h")
        logger.info(f"❌ Errors: {stats['errors']}")
        logger.info("=" * 60)