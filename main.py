#!/usr/bin/env python3
"""
FIXED main.py for Financial News Detector Bot.
This version properly handles state loading on server restart.
"""
import asyncio
import logging
import sys
import time
import argparse
import signal
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Import modules
try:
    from src.handlers.news_handler import NewsHandler
    from src.client.telegram_client import TelegramClientManager
    from src.utils.logger import setup_logging
    from src.utils.time_utils import is_operating_hours, get_current_time, log_time_status
    from config.credentials import validate_credentials
    from config.settings import (
        NEWS_CHECK_INTERVAL, NEWS_CHANNEL, TWITTER_NEWS_CHANNEL, 
        TARGET_CHANNEL_ID, OPERATION_START_HOUR, OPERATION_START_MINUTE,
        OPERATION_END_HOUR, OPERATION_END_MINUTE, ENABLE_MEDIA_PROCESSING
    )
    print("✅ All imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure all required files are in place")
    sys.exit(1)

# Set up logging
logger = setup_logging()
logger.info("🚀 Starting Financial News Detector Bot with FIXED state loading...")

# Global shutdown flag
should_exit = False
bot_instance = None

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Financial News Detector Bot')
    parser.add_argument('--test-news', action='store_true',
                        help='Test news detection and processing')
    parser.add_argument('--news-text', type=str,
                        help='Sample news text to test detection')
    parser.add_argument('--news-channel', type=str,
                        help='Channel to test news processing from')
    parser.add_argument('--force-24h', action='store_true',
                        help='Force 24-hour operation (ignore operating hours)')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug mode')
    parser.add_argument('--stats', action='store_true',
                        help='Show current statistics and exit')
    parser.add_argument('--test-persian', action='store_true',
                        help='Test Persian calendar functionality')
    parser.add_argument('--test-media', action='store_true',
                        help='Test media handling functionality')
    parser.add_argument('--test-deletion', action='store_true',
                        help='Test message deletion functionality')
    return parser.parse_args()

def signal_handler(sig, frame):
    """Handle termination signals gracefully."""
    global should_exit, bot_instance
    logger.info(f"📡 Received signal {sig}, initiating graceful shutdown...")
    should_exit = True
    
    # If we have a bot instance, signal it to stop
    if bot_instance:
        bot_instance.request_shutdown()

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # Termination signal

class FinancialNewsBot:
    """Complete financial news detector bot with FIXED state management."""

    def __init__(self, force_24h=False, debug_mode=False):
        """Initialize the financial news bot."""
        self.client_manager = TelegramClientManager()
        self.news_handler = None
        self.running = False
        self.start_time = None
        self.force_24h = force_24h
        self.debug_mode = debug_mode
        self.shutdown_requested = False
        
        # Statistics
        self.stats = {
            'total_updates': 0,
            'news_processed': 0,
            'news_sent_for_approval': 0,
            'news_approved': 0,
            'news_published': 0,
            'media_processed': 0,
            'errors': 0,
            'start_time': None
        }

    def request_shutdown(self):
        """Request graceful shutdown."""
        self.shutdown_requested = True
        self.running = False

    async def start(self):
        """Start the financial news bot with FIXED initialization."""
        logger.info("⚙️ Initializing Financial News Bot...")
        
        try:
            # Validate credentials first
            logger.info("🔐 Validating credentials...")
            validate_credentials()
            logger.info("✅ Credentials validated")

            # Start the Telegram client
            logger.info("📱 Starting Telegram client...")
            if not await self.client_manager.start():
                logger.error("❌ Failed to start Telegram client")
                return False

            # Initialize news handler
            logger.info("📰 Initializing news handler...")
            self.news_handler = NewsHandler(self.client_manager)
            
            # CRITICAL: Load state BEFORE setting up handlers
            logger.info("📂 Loading previous state...")
            await self.news_handler.load_pending_news()
            
            # Log loaded state info
            pending_count = len(self.news_handler.pending_news)
            logger.info(f"📋 Loaded {pending_count} pending news items from previous session")
            
            if pending_count > 0:
                # Show some example pending IDs
                sample_ids = list(self.news_handler.pending_news.keys())[:3]
                logger.info(f"📝 Sample pending IDs: {sample_ids}")

            # Initialize the news handler with Bot API and media support
            if hasattr(self.news_handler, 'initialize'):
                await self.news_handler.initialize()

            # Set up news approval handler - AFTER state loading
            logger.info("👨‍💼 Setting up news approval handler...")
            if not await self.news_handler.setup_approval_handler():
                logger.warning("⚠️ Failed to set up news approval handler")
            else:
                logger.info("✅ News approval handler set up successfully")
            
            # Test admin bot connection immediately
            logger.info("🧪 Testing admin bot connection...")
            admin_test_result = await self.news_handler.test_admin_bot_connection()
            if admin_test_result:
                logger.info("✅ Admin bot connection test passed")
            else:
                logger.warning("⚠️ Admin bot connection test failed - deletion may not work")

            self.running = True
            self.start_time = time.time()
            self.stats['start_time'] = self.start_time
            
            # Log startup info
            self._log_startup_info()

            logger.info("🎉 Financial News Bot started successfully!")
            logger.info("🔄 Bot is now running and ready to handle approval commands...")
            logger.info("📅 Persian calendar timestamps enabled")
            if ENABLE_MEDIA_PROCESSING:
                logger.info("📎 Media handling enabled")
            
            return True

        except Exception as e:
            logger.error(f"❌ Failed to start financial news bot: {e}")
            if self.debug_mode:
                import traceback
                traceback.print_exc()
            return False

    def _log_startup_info(self):
        """Log startup information."""
        logger.info("=" * 60)
        logger.info("📊 FINANCIAL NEWS DETECTOR CONFIGURATION")
        logger.info("=" * 60)
        logger.info(f"🎯 Target Channel: {TARGET_CHANNEL_ID}")
        logger.info(f"📺 News Channels: {NEWS_CHANNEL}, {TWITTER_NEWS_CHANNEL}")
        logger.info(f"⏰ Check Interval: {NEWS_CHECK_INTERVAL}s ({NEWS_CHECK_INTERVAL//60} minutes)")
        logger.info(f"🕐 Operating Hours: {OPERATION_START_HOUR:02d}:{OPERATION_START_MINUTE:02d} - {OPERATION_END_HOUR:02d}:{OPERATION_END_MINUTE:02d} Tehran")
        logger.info(f"🗓️ Persian Calendar: Enabled")
        logger.info(f"📎 Media Processing: {'Enabled' if ENABLE_MEDIA_PROCESSING else 'Disabled'}")
        logger.info(f"🌐 24h Mode: {'Enabled' if self.force_24h else 'Disabled'}")
        logger.info(f"🐛 Debug Mode: {'Enabled' if self.debug_mode else 'Disabled'}")
        logger.info(f"💰 Focus: Gold, Currencies, Iranian Economy, Oil, Crypto")
        
        # Log current time status
        log_time_status()
        
        # Log pending news status
        if self.news_handler:
            pending_count = len(self.news_handler.pending_news)
            logger.info(f"📋 Pending Approvals: {pending_count}")
        
        logger.info("=" * 60)

    async def run_continuous_monitoring(self):
        """Main continuous monitoring loop with proper state management."""
        logger.info("🔄 Starting continuous news monitoring...")
        logger.info("💡 The bot will now keep running to handle approval commands")
        logger.info("💡 Use Ctrl+C to stop the bot gracefully")
        
        last_news_check = 0
        last_status_log = 0
        last_state_save = 0
        
        try:
            while self.running and not should_exit and not self.shutdown_requested:
                try:
                    current_time = time.time()
                    
                    # Check if we're in operating hours (unless force 24h)
                    if not self.force_24h and not is_operating_hours():
                        if current_time - last_status_log >= 3600:  # Log every hour when outside hours
                            logger.info("💤 Outside operating hours, bot is idle but ready for approvals...")
                            logger.info("🕐 Use Persian calendar format for timestamps")
                            last_status_log = current_time
                        await asyncio.sleep(300)  # Check every 5 minutes when outside hours
                        continue
                    
                    # News processing
                    if current_time - last_news_check >= NEWS_CHECK_INTERVAL:
                        await self._process_news_updates()
                        last_news_check = current_time
                        self.stats['total_updates'] += 1
                    
                    # Periodic state saving (every 5 minutes)
                    if current_time - last_state_save >= 300:
                        if self.news_handler:
                            await self.news_handler.save_pending_news()
                            logger.debug("💾 Periodic state save completed")
                        last_state_save = current_time
                    
                    # Log status every 30 minutes during active hours
                    if current_time - last_status_log >= 1800:
                        await self._log_status()
                        last_status_log = current_time
                    
                    # Sleep for a short interval (this allows approval commands to be processed)
                    await asyncio.sleep(60)  # Check every minute
                    
                except asyncio.CancelledError:
                    logger.info("🛑 Monitoring loop cancelled")
                    break
                except Exception as e:
                    logger.error(f"Error in monitoring loop: {e}")
                    self.stats['errors'] += 1
                    if self.debug_mode:
                        import traceback
                        traceback.print_exc()
                    await asyncio.sleep(60)  # Wait before retrying
                    
        except KeyboardInterrupt:
            logger.info("⌨️ Received keyboard interrupt in monitoring loop")
        finally:
            await self.stop()

    async def _process_news_updates(self):
        """Process news updates from configured channels."""
        try:
            logger.info("📰 Processing financial news updates...")
            
            # Get news channels
            news_channels = []
            if NEWS_CHANNEL:
                news_channels.append(NEWS_CHANNEL)
            if TWITTER_NEWS_CHANNEL:
                news_channels.append(TWITTER_NEWS_CHANNEL)
            
            if not news_channels:
                logger.warning("No news channels configured")
                return
            
            # Process news from each channel
            for channel in news_channels:
                try:
                    logger.info(f"Processing financial news from: {channel}")
                    result = await self.news_handler.process_news_messages(channel)
                    if result:
                        self.stats['news_processed'] += 1
                        logger.info(f"✅ Successfully processed financial news from {channel}")
                    else:
                        logger.debug(f"No new financial news found in {channel}")
                        
                    # Small delay between channels
                    await asyncio.sleep(5)
                    
                except Exception as channel_error:
                    logger.error(f"Error processing news from {channel}: {channel_error}")
                    self.stats['errors'] += 1
                    continue
            
            # Clean expired pending news
            if hasattr(self.news_handler, 'clean_expired_pending_news'):
                await self.news_handler.clean_expired_pending_news()
            
            logger.info("✅ Financial news processing completed")
            
        except Exception as e:
            logger.error(f"❌ Error in news processing: {e}")
            self.stats['errors'] += 1

    async def _log_status(self):
        """Log current bot status with Persian calendar."""
        if self.start_time:
            uptime = int(time.time() - self.start_time)
            pending_count = len(self.news_handler.pending_news) if self.news_handler else 0
            
            # Get current Persian time
            from src.utils.time_utils import get_formatted_time
            persian_time = get_formatted_time(format_type="persian_full")
            
            logger.info(f"📊 STATUS - Persian Time: {persian_time}")
            logger.info(f"📊 Uptime: {uptime}s | News Processed: {self.stats['news_processed']} | "
                       f"Pending Approvals: {pending_count} | Errors: {self.stats['errors']}")
            
            if pending_count > 0:
                logger.info(f"⏳ {pending_count} news items waiting for approval")
            
            if ENABLE_MEDIA_PROCESSING:
                logger.info(f"📎 Media processed: {self.stats.get('media_processed', 0)}")

    async def test_deletion_functionality(self):
        """Test the deletion functionality."""
        logger.info("🧪 Testing deletion functionality...")
        
        if not self.news_handler:
            logger.error("❌ News handler not initialized")
            return False
        
        # Test admin bot connection
        test_result = await self.news_handler.test_admin_bot_connection()
        
        if test_result:
            logger.info("✅ Deletion functionality test passed")
            return True
        else:
            logger.error("❌ Deletion functionality test failed")
            return False

    async def show_statistics(self):
        """Show current statistics."""
        logger.info("📊 CURRENT FINANCIAL NEWS STATISTICS")
        logger.info("=" * 50)
        
        # Show current Persian time
        from src.utils.time_utils import get_formatted_time
        persian_time = get_formatted_time(format_type="persian_full")
        logger.info(f"🗓️ Current Persian Time: {persian_time}")
        
        if self.start_time:
            uptime = int(time.time() - self.start_time)
            hours = uptime // 3600
            minutes = (uptime % 3600) // 60
            logger.info(f"⏰ Uptime: {hours}h {minutes}m ({uptime}s)")
        
        for key, value in self.stats.items():
            if key != 'start_time':
                logger.info(f"📈 {key.replace('_', ' ').title()}: {value}")
        
        if self.news_handler and hasattr(self.news_handler, 'pending_news'):
            pending_count = len(self.news_handler.pending_news)
            logger.info(f"⏳ Pending News: {pending_count}")
            
            if pending_count > 0:
                logger.info("📋 Pending news items:")
                for i, (news_id, news_data) in enumerate(list(self.news_handler.pending_news.items())[:3]):
                    text_preview = news_data.get('text', '')[:80]
                    logger.info(f"   {i+1}. ID: {news_id} - {text_preview}...")
        
        # Show media statistics if enabled
        if ENABLE_MEDIA_PROCESSING:
            logger.info(f"📎 Media Processing: Enabled")

    async def stop(self):
        """Stop the bot gracefully with proper state saving."""
        logger.info("🛑 Stopping Financial News Bot...")
        self.running = False
        
        try:
            # Save news state - CRITICAL on server
            if self.news_handler and hasattr(self.news_handler, 'save_pending_news'):
                logger.info("💾 Saving pending news state...")
                await self.news_handler.save_pending_news()
                pending_count = len(self.news_handler.pending_news)
                logger.info(f"💾 Saved {pending_count} pending news items")
            
            # Clean up media files
            if (self.news_handler and hasattr(self.news_handler, 'cleanup_all_temp_media') 
                and ENABLE_MEDIA_PROCESSING):
                await self.news_handler.cleanup_all_temp_media()
                logger.info("🧹 Media cleanup completed")
            
            # Stop client
            if self.client_manager:
                await self.client_manager.stop()
                logger.info("📱 Telegram client stopped")
                
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

async def main():
    """Main entry point with proper error handling."""
    global bot_instance
    
    args = parse_args()
    
    # Enable debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("🐛 Debug mode enabled")
    
    # Create bot instance
    bot_instance = FinancialNewsBot(force_24h=args.force_24h, debug_mode=args.debug)
    
    try:
        # Start the bot
        if not await bot_instance.start():
            logger.error("❌ Failed to start financial news bot")
            return 1

        # Handle different modes
        if args.stats:
            # Show statistics and exit
            await bot_instance.show_statistics()
            return 0

        if args.test_deletion:
            # Test deletion functionality
            success = await bot_instance.test_deletion_functionality()
            return 0 if success else 1

        if args.test_news:
            # Test mode
            logger.info("🧪 Running in test mode")
            # Add your test functionality here
            return 0

        # Normal operation mode - KEEP RUNNING
        logger.info("🚀 Running in normal operation mode")
        logger.info("🔄 Bot will keep running to handle approval commands...")
        
        # Log current operating status
        if is_operating_hours():
            logger.info("🟢 Currently within operating hours - active monitoring")
        elif bot_instance.force_24h:
            logger.info("🔵 24-hour operation enabled - active monitoring")
        else:
            logger.info(f"🟡 Outside operating hours - idle but ready for approvals")

        # Run continuous monitoring loop (keeps running until interrupted)
        await bot_instance.run_continuous_monitoring()

    except KeyboardInterrupt:
        logger.info("⌨️ Received keyboard interrupt")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1
    finally:
        logger.info("🔄 Performing cleanup...")
        if bot_instance:
            await bot_instance.stop()

    logger.info("👋 Financial News Detector shutdown complete")
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Financial news bot stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)