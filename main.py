#!/usr/bin/env python3
"""
Complete main.py for Financial News Detector Bot.
Updated with Persian calendar, media handling, and new schedule (8:30 AM - 10:00 PM).
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
logger.info("🚀 Starting Financial News Detector Bot with Persian Calendar Support...")

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
    """Complete financial news detector bot with Persian calendar and media support."""

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
        """Start the financial news bot."""
        logger.info("⚙️ Initializing Financial News Bot with Persian Calendar...")
        
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
            
            # Initialize the news handler with Bot API and media support
            if hasattr(self.news_handler, 'initialize'):
                await self.news_handler.initialize()

            # Set up news approval handler - CRITICAL for approval workflow
            logger.info("👨‍💼 Setting up news approval handler...")
            if not await self.news_handler.setup_approval_handler():
                logger.warning("⚠️ Failed to set up news approval handler")
                
            # Load existing state
            logger.info("📂 Loading application state...")
            if hasattr(self.news_handler, 'load_pending_news'):
                await self.news_handler.load_pending_news()

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
        logger.info("=" * 60)

    async def run_continuous_monitoring(self):
        """Main continuous monitoring loop with Persian calendar support."""
        logger.info("🔄 Starting continuous news monitoring...")
        logger.info("💡 The bot will now keep running to handle approval commands")
        logger.info("💡 Use Ctrl+C to stop the bot gracefully")
        
        last_news_check = 0
        last_status_log = 0
        
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

    async def test_persian_calendar(self):
        """Test Persian calendar functionality."""
        logger.info("🗓️ Testing Persian Calendar Functionality...")
        
        from src.utils.time_utils import (
            get_current_time, get_formatted_time, format_persian_date,
            format_persian_time, format_persian_datetime
        )
        
        current_time = get_current_time()
        
        logger.info(f"Current Tehran Time: {current_time}")
        logger.info(f"Persian Full Format: {get_formatted_time(current_time, 'persian_full')}")
        logger.info(f"Persian Date: {format_persian_date(current_time)}")
        logger.info(f"Persian Time: {format_persian_time(current_time)}")
        logger.info(f"Persian DateTime: {format_persian_datetime(current_time)}")
        
        # Test message format
        test_message = "📈 تست خبر مالی"
        from src.utils.time_utils import add_timestamp_to_message
        formatted_message = add_timestamp_to_message(test_message)
        
        logger.info("Sample formatted message:")
        logger.info("-" * 30)
        logger.info(formatted_message)
        logger.info("-" * 30)

    async def test_media_functionality(self):
        """Test media handling functionality."""
        logger.info("📎 Testing Media Functionality...")
        
        if not ENABLE_MEDIA_PROCESSING:
            logger.warning("❌ Media processing is disabled in configuration")
            return
        
        try:
            # Test media directory creation
            from config.settings import MEDIA_DIR, TEMP_MEDIA_DIR
            logger.info(f"Media Directory: {MEDIA_DIR}")
            logger.info(f"Temp Media Directory: {TEMP_MEDIA_DIR}")
            logger.info(f"Media Dir Exists: {'✅' if MEDIA_DIR.exists() else '❌'}")
            logger.info(f"Temp Media Dir Exists: {'✅' if TEMP_MEDIA_DIR.exists() else '❌'}")
            
            # Test write permissions
            test_file = TEMP_MEDIA_DIR / "test_write.txt"
            try:
                test_file.write_text("test")
                test_file.unlink()
                logger.info("Write Permission: ✅")
            except Exception as e:
                logger.error(f"Write Permission: ❌ ({e})")
            
            # Test media cleanup
            if hasattr(self.news_handler, 'cleanup_all_temp_media'):
                await self.news_handler.cleanup_all_temp_media()
                logger.info("✅ Media cleanup test completed")
            
        except Exception as e:
            logger.error(f"❌ Media functionality test failed: {e}")

    async def test_financial_news_detection(self, news_text=None, channel=None):
        """Test financial news detection functionality."""
        logger.info("🧪 Testing financial news detection...")
        
        # If no specific test provided, run default financial tests
        if not news_text and not channel:
            logger.info("No specific test provided, running default financial tests...")
            
            # Test 1: Gold news (should detect)
            gold_news = "قیمت طلای ۱۸ عیار امروز به ۲ میلیون و ۵۰۰ هزار تومان رسید و سکه طلا نیز افزایش یافت"
            await self._test_single_news_text(gold_news, "Gold News Test")
            
            # Test 2: Currency news (should detect)
            currency_news = "نرخ دلار در بازار آزاد به ۵۲ هزار تومان رسید و یورو نیز ۵۵ هزار تومان شد"
            await self._test_single_news_text(currency_news, "Currency News Test")
            
            # Test 3: Iranian economy news (should detect)
            economy_news = "بانک مرکزی نرخ سود بانکی را ۲۲ درصد اعلام کرد و تورم به ۴۰ درصد رسید"
            await self._test_single_news_text(economy_news, "Iranian Economy Test")
            
            # Test 4: Non-financial content (should not detect)
            non_financial = "تیم فوتبال پرسپولیس امشب مقابل استقلال بازی دارد و موسیقی زیبایی پخش خواهد شد"
            await self._test_single_news_text(non_financial, "Non-Financial Test")
            
            # Test 5: Channel processing
            if NEWS_CHANNEL:
                logger.info(f"Testing channel processing: {NEWS_CHANNEL}")
                try:
                    result = await self.news_handler.process_news_messages(NEWS_CHANNEL)
                    logger.info(f"✅ Channel processing result: {result}")
                except Exception as e:
                    logger.error(f"❌ Channel processing error: {e}")
            
            return
        
        if news_text:
            await self._test_single_news_text(news_text, "Provided Text")
        
        if channel:
            logger.info(f"Testing channel processing: {channel}")
            try:
                result = await self.news_handler.process_news_messages(channel)
                logger.info(f"Channel processing result: {result}")
            except Exception as e:
                logger.error(f"Channel processing error: {e}")

    async def _test_single_news_text(self, news_text, test_name):
        """Test a single news text for financial content."""
        logger.info(f"🧪 Testing {test_name}...")
        logger.info(f"📝 Text: {news_text[:100]}...")
        
        if self.news_handler and self.news_handler.news_detector:
            is_news = self.news_handler.news_detector.is_news(news_text)
            logger.info(f"📊 Financial news detection result: {is_news}")
            
            if is_news:
                # Get financial category
                category = self.news_handler.news_detector.get_financial_category(news_text)
                logger.info(f"💰 Financial category: {category}")
                
                cleaned = self.news_handler.news_detector.clean_news_text(news_text)
                logger.info(f"🧹 Cleaned text length: {len(cleaned)}")
                logger.info(f"🧹 Cleaned preview: {cleaned[:150]}...")
                
                # Test relevance filtering
                try:
                    from src.services.news_filter import NewsFilter
                    is_relevant, score, topics = NewsFilter.is_relevant_news(cleaned)
                    logger.info(f"🎯 Relevance: {is_relevant}, Score: {score}, Topics: {topics[:5]}")
                except Exception as e:
                    logger.warning(f"NewsFilter test failed: {e}")
                    is_relevant, score = True, 3
                
                if is_relevant:
                    # Test sending to approval bot with Persian calendar
                    logger.info("📤 Testing approval bot sending with Persian calendar...")
                    approval_id = await self.news_handler.send_to_approval_bot_rate_limited(
                        cleaned, None, "test_channel",
                        {'score': score, 'topics': topics[:3]}
                    )
                    if approval_id:
                        logger.info(f"✅ Financial news sent for approval with ID: {approval_id}")
                        logger.info(f"💡 To approve, send to your admin bot: /submit{approval_id}")
                        self.stats['news_sent_for_approval'] += 1
                        
                        # Show how it will look when published (with Persian calendar)
                        from src.utils.time_utils import get_formatted_time
                        persian_time = get_formatted_time(format_type="persian_full")
                        sample_published = f"{cleaned}\n📡 @anilnewsonline\n🕐 {persian_time}"
                        
                        logger.info("📢 Sample published format:")
                        logger.info("-" * 30)
                        logger.info(sample_published)
                        logger.info("-" * 30)
                    else:
                        logger.error("❌ Failed to send financial news for approval")
                else:
                    logger.info("❌ Financial news was filtered out due to low relevance")
            else:
                logger.info("❌ Text was not detected as financial news (expected for non-financial content)")
        else:
            logger.error("❌ News detector not available")

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
            if hasattr(self.news_handler, 'cleanup_all_temp_media'):
                logger.info("🧹 Media cleanup: Available")

    async def stop(self):
        """Stop the bot gracefully."""
        logger.info("🛑 Stopping Financial News Bot...")
        self.running = False
        
        try:
            # Save news state
            if self.news_handler and hasattr(self.news_handler, 'save_pending_news'):
                await self.news_handler.save_pending_news()
                logger.info("💾 News state saved")
            
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
    """Main entry point."""
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

        if args.test_persian:
            # Test Persian calendar functionality
            await bot_instance.test_persian_calendar()
            return 0

        if args.test_media:
            # Test media functionality
            await bot_instance.test_media_functionality()
            return 0

        if args.test_news:
            # Test mode
            logger.info("🧪 Running in test mode")
            await bot_instance.test_financial_news_detection(
                news_text=args.news_text,
                channel=args.news_channel
            )
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