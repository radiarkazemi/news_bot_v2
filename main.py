"""
Telegram News Detector - Complete Standalone Application
Enhanced version with full news detection, filtering, and admin approval workflow.
"""
import asyncio
import logging
import signal
import sys
import time
import argparse
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Import with error handling
try:
    from src.utils.logger import setup_logging
    from src.client.telegram_client import TelegramClientManager
    from src.handlers.news_handler import NewsHandler
    from src.utils.time_utils import is_operating_hours, get_current_time, get_formatted_time
    from config.credentials import validate_credentials
    from config.settings import (
        NEWS_CHECK_INTERVAL, NEWS_CHANNEL, TWITTER_NEWS_CHANNEL, ALL_NEWS_CHANNELS,
        FORCE_24_HOUR_OPERATION, OPERATION_START_HOUR, OPERATION_END_HOUR,
        DEBUG_MODE, TEST_MODE, HEALTH_CHECK_INTERVAL
    )
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you have copied all the required files and run from project root")
    sys.exit(1)

# Set up logging
logger = setup_logging()
logger.info("🚀 Starting Telegram News Detector...")

# Global shutdown flag
should_exit = False


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Telegram News Detector - Complete Version')
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
    return parser.parse_args()


def signal_handler(sig, frame):
    """Handle termination signals gracefully."""
    global should_exit
    logger.info(f"📡 Received signal {sig}, initiating graceful shutdown...")
    should_exit = True


# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # Termination signal


class NewsDetectorBot:
    """Enhanced news detector application with complete functionality."""

    def __init__(self, force_24h=False, debug_mode=False):
        """Initialize the news detector bot."""
        self.client_manager = TelegramClientManager()
        self.news_handler = NewsHandler(self.client_manager)
        self.running = False
        self.start_time = None
        self.force_24h = force_24h or FORCE_24_HOUR_OPERATION
        self.debug_mode = debug_mode or DEBUG_MODE
        
        # Background tasks
        self.health_check_task = None
        self.stats_task = None

    async def start(self):
        """Start the news detector bot with enhanced initialization."""
        logger.info("⚙️  Initializing News Detector Bot...")
        
        self.running = True
        self.start_time = time.time()

        try:
            # Validate credentials first
            logger.info("🔐 Validating credentials...")
            validate_credentials()
            logger.info("✅ Credentials validated")

            # Start the Telegram client
            logger.info("📱 Starting Telegram client...")
            if not await self.client_manager.start():
                logger.error("❌ Failed to start Telegram client. Exiting.")
                return False

            # Set up news approval handler
            logger.info("👨‍💼 Setting up news approval handler...")
            if not await self.news_handler.setup_approval_handler():
                logger.warning("⚠️  Failed to set up news approval handler. Manual approval may be required.")

            # Load existing state
            logger.info("📂 Loading application state...")
            await self.news_handler.load_pending_news()

            # Test bot API connection
            logger.info("🤖 Testing Bot API connection...")
            if self.news_handler.bot_api and hasattr(self.news_handler.bot_api, 'test_connection'):
                self.news_handler.bot_api.test_connection()

            # Start background tasks
            self.health_check_task = asyncio.create_task(self.health_check())
            self.stats_task = asyncio.create_task(self.periodic_stats())

            # Log configuration summary
            self._log_startup_info()

            logger.info("🎉 News Detector Bot started successfully!")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to start news detector bot: {e}")
            if self.debug_mode:
                import traceback
                traceback.print_exc()
            return False

    def _log_startup_info(self):
        """Log startup information and configuration."""
        logger.info("📊 Startup Configuration:")
        logger.info(f"   🕐 Operating Hours: {OPERATION_START_HOUR}:00 - {OPERATION_END_HOUR}:00 Tehran")
        logger.info(f"   ⏰ 24/7 Mode: {self.force_24h}")
        logger.info(f"   📺 News Channels: {len(ALL_NEWS_CHANNELS)}")
        for i, channel in enumerate(ALL_NEWS_CHANNELS[:3], 1):
            logger.info(f"      {i}. @{channel}")
        if len(ALL_NEWS_CHANNELS) > 3:
            logger.info(f"      ... and {len(ALL_NEWS_CHANNELS) - 3} more")
        logger.info(f"   ⏱️  Check Interval: {NEWS_CHECK_INTERVAL} seconds")
        logger.info(f"   🔍 Debug Mode: {self.debug_mode}")

    async def stop(self):
        """Stop the news detector bot gracefully."""
        logger.info("🛑 Stopping News Detector Bot...")
        
        self.running = False

        # Cancel background tasks
        tasks_to_cancel = [self.health_check_task, self.stats_task]
        for task in tasks_to_cancel:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # Save final state
        if self.news_handler:
            logger.info("💾 Saving final state...")
            await self.news_handler.save_pending_news()

        # Stop client
        if self.client_manager:
            await self.client_manager.stop()

        # Log final statistics
        if self.news_handler:
            final_stats = self.news_handler.get_statistics()
            logger.info("📈 Final Statistics:")
            logger.info(f"   Messages Processed: {final_stats.get('messages_processed', 0)}")
            logger.info(f"   News Detected: {final_stats.get('news_detected', 0)}")
            logger.info(f"   Sent for Approval: {final_stats.get('news_sent_for_approval', 0)}")
            logger.info(f"   News Approved: {final_stats.get('news_approved', 0)}")
            logger.info(f"   News Filtered: {final_stats.get('news_filtered_out', 0)}")

        logger.info("✅ News Detector Bot stopped successfully")

    async def health_check(self):
        """Enhanced periodic health check."""
        logger.info("💓 Health check monitor started")
        
        while self.running:
            try:
                # Check client connection
                connection_ok = False
                if self.client_manager.client:
                    connection_ok = self.client_manager.client.is_connected()
                
                if not connection_ok:
                    logger.warning("⚠️  Telegram client connection lost")
                
                # Calculate and log uptime
                uptime = time.time() - self.start_time
                hours = int(uptime // 3600)
                minutes = int((uptime % 3600) // 60)
                
                # Get statistics
                if self.news_handler:
                    stats = self.news_handler.get_statistics()
                    pending_count = stats.get('pending_approvals', 0)
                    processed_today = stats.get('messages_processed', 0)
                else:
                    pending_count = 0
                    processed_today = 0
                
                # Log health status
                status_icon = "🟢" if connection_ok else "🔴"
                logger.info(f"{status_icon} Health Check - Uptime: {hours}h {minutes}m | "
                          f"Pending: {pending_count} | Processed: {processed_today}")
                
                # Wait for next health check
                await asyncio.sleep(HEALTH_CHECK_INTERVAL)

            except asyncio.CancelledError:
                logger.debug("Health check cancelled")
                break
            except Exception as e:
                logger.error(f"❌ Health check error: {e}")
                await asyncio.sleep(60)

    async def periodic_stats(self):
        """Log periodic statistics."""
        while self.running:
            try:
                await asyncio.sleep(1800)  # Every 30 minutes
                
                if self.news_handler:
                    stats = self.news_handler.get_statistics()
                    from src.utils.logger import log_statistics
                    log_statistics(stats)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in stats logging: {e}")
                await asyncio.sleep(300)

    async def run_news_monitoring(self):
        """Enhanced main news monitoring loop."""
        logger.info("🔍 Starting enhanced news monitoring...")

        while self.running and not should_exit:
            try:
                # Check operating hours
                if not self.force_24h and not is_operating_hours():
                    current_time = get_formatted_time()
                    logger.info(f"🌙 Outside operating hours ({OPERATION_START_HOUR}:00-{OPERATION_END_HOUR}:00 Tehran). "
                              f"Current time: {current_time}. Sleeping...")
                    await asyncio.sleep(900)  # 15 minutes
                    continue

                logger.info("🔍 Starting news check cycle...")

                # Process each news channel
                total_processed = 0
                for channel in ALL_NEWS_CHANNELS:
                    if should_exit:
                        break
                    
                    try:
                        logger.info(f"📺 Processing channel: @{channel}")
                        result = await self.news_handler.process_news_messages(channel)
                        
                        if result:
                            logger.info(f"✅ Successfully processed news from @{channel}")
                            total_processed += 1
                        else:
                            logger.debug(f"ℹ️  No new news found in @{channel}")
                            
                        # Delay between channels to avoid rate limits
                        await asyncio.sleep(3)
                        
                    except Exception as e:
                        logger.error(f"❌ Error processing @{channel}: {e}")

                # Check for approval timeouts
                try:
                    await self.news_handler.check_approval_timeouts()
                except Exception as e:
                    logger.error(f"Error checking approval timeouts: {e}")

                # Log cycle completion
                if total_processed > 0:
                    logger.info(f"✅ News cycle complete: processed {total_processed} channels")
                else:
                    logger.debug("ℹ️  News cycle complete: no new news found")

                # Wait for next check cycle
                logger.info(f"⏳ Next news check in {NEWS_CHECK_INTERVAL} seconds "
                          f"({NEWS_CHECK_INTERVAL // 60} minutes)")
                await asyncio.sleep(NEWS_CHECK_INTERVAL)

            except Exception as e:
                logger.error(f"❌ Error in news monitoring loop: {e}")
                if self.debug_mode:
                    import traceback
                    traceback.print_exc()
                await asyncio.sleep(60)

    async def test_news_detection(self, news_text=None, channel=None):
        """Test news detection functionality with detailed output."""
        logger.info("🧪 Starting news detection test...")

        if news_text:
            # Test specific text
            print("\n" + "="*60)
            print("📝 TESTING SPECIFIC TEXT")
            print("="*60)
            
            try:
                is_news, is_relevant = await self.news_handler.test_news_detection(news_text)
                
                if is_news and is_relevant:
                    print("🎉 RESULT: Text would be sent for admin approval")
                elif is_news:
                    print("⚠️  RESULT: Text detected as news but filtered out")
                else:
                    print("❌ RESULT: Text not detected as news")
                    
            except Exception as e:
                print(f"❌ Error testing text: {e}")

        if channel:
            # Test channel processing
            print(f"\n" + "="*60)
            print(f"📺 TESTING CHANNEL: @{channel}")
            print("="*60)
            
            try:
                # Get channel info first
                channel_info = await self.news_handler.get_channel_info(channel)
                if channel_info:
                    print(f"📊 Channel Info:")
                    print(f"   Title: {channel_info.get('title', 'Unknown')}")
                    print(f"   Participants: {channel_info.get('participants_count', 0)}")
                
                # Test processing
                result = await self.news_handler.process_news_messages(channel)
                
                if result:
                    print("✅ RESULT: Found and processed news from channel")
                else:
                    print("ℹ️  RESULT: No new news found in channel")
                
                # Show pending approvals
                pending = len(self.news_handler.pending_news)
                print(f"📋 Pending Approvals: {pending}")
                
            except Exception as e:
                print(f"❌ Error testing channel: {e}")

        # Show statistics
        if self.news_handler:
            stats = self.news_handler.get_statistics()
            print(f"\n📊 Current Statistics:")
            for key, value in stats.items():
                print(f"   {key}: {value}")

        print("\n✅ News detection test complete")

    async def show_statistics(self):
        """Show current statistics and exit."""
        logger.info("📊 Retrieving current statistics...")
        
        try:
            # Start minimal setup to access state
            await self.news_handler.load_pending_news()
            
            stats = self.news_handler.get_statistics()
            
            print("\n📊 News Detector Statistics")
            print("="*50)
            print(f"📈 Messages Processed: {stats.get('messages_processed', 0)}")
            print(f"📰 News Detected: {stats.get('news_detected', 0)}")
            print(f"📤 Sent for Approval: {stats.get('news_sent_for_approval', 0)}")
            print(f"✅ News Approved: {stats.get('news_approved', 0)}")
            print(f"🚫 News Filtered Out: {stats.get('news_filtered_out', 0)}")
            print(f"❌ Errors: {stats.get('errors', 0)}")
            print(f"⏳ Pending Approvals: {stats.get('pending_approvals', 0)}")
            
            # Show pending items
            if stats.get('pending_approvals', 0) > 0:
                print(f"\n📋 Pending Approval Items:")
                for i, (approval_id, news_data) in enumerate(list(self.news_handler.pending_news.items())[:5], 1):
                    age = time.time() - news_data['timestamp']
                    age_str = f"{int(age//3600)}h {int((age%3600)//60)}m ago"
                    source = news_data.get('source_channel', 'Unknown')
                    print(f"   {i}. ID: {approval_id} | Source: @{source} | Age: {age_str}")
                
                if len(self.news_handler.pending_news) > 5:
                    remaining = len(self.news_handler.pending_news) - 5
                    print(f"   ... and {remaining} more items")
            
            # Calculate rates if we have data
            uptime_hours = stats.get('uptime_hours', 0)
            if uptime_hours > 0:
                detection_rate = stats.get('news_detected', 0) / uptime_hours
                approval_rate = stats.get('news_approved', 0) / uptime_hours
                print(f"\n📈 Hourly Rates:")
                print(f"   Detection Rate: {detection_rate:.1f} news/hour")
                print(f"   Approval Rate: {approval_rate:.1f} approved/hour")
            
        except Exception as e:
            logger.error(f"Error retrieving statistics: {e}")


async def main():
    """Enhanced main entry point."""
    args = parse_args()

    # Enable debug mode if requested
    if args.debug:
        from src.utils.logger import setup_debug_logging
        setup_debug_logging()

    # Create news detector bot
    bot = NewsDetectorBot(force_24h=args.force_24h, debug_mode=args.debug)

    try:
        # Handle different modes
        if args.stats:
            # Show statistics and exit
            await bot.show_statistics()
            return 0

        if args.test_news:
            # Test mode
            logger.info("🧪 Running in test mode")
            
            if not await bot.start():
                logger.error("❌ Failed to start bot for testing")
                return 1
            
            await bot.test_news_detection(
                news_text=args.news_text,
                channel=args.news_channel
            )
            
            await bot.stop()
            return 0

        # Normal operation mode
        logger.info("🚀 Running in normal operation mode")
        
        if not await bot.start():
            logger.error("❌ Failed to start news detector bot")
            return 1

        # Log current operating status
        if is_operating_hours():
            logger.info("🟢 Currently within operating hours - starting immediately")
        elif bot.force_24h:
            logger.info("🔵 24-hour operation enabled - starting immediately")
        else:
            logger.info(f"🟡 Outside operating hours - will activate at {OPERATION_START_HOUR}:00 Tehran time")

        # Run main monitoring loop
        await bot.run_news_monitoring()

    except KeyboardInterrupt:
        logger.info("⌨️  Received keyboard interrupt")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        return 1
    finally:
        logger.info("🔄 Performing cleanup...")
        await bot.stop()

    logger.info("👋 News Detector shutdown complete")
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 News detector stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)