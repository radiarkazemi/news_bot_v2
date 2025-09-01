#!/usr/bin/env python3
"""
ENHANCED main.py for Financial News Detector Bot with FREE AI Integration.
This version supports both manual and AI-powered approval modes.
"""
import asyncio
import logging
import sys
import time
import argparse
import signal
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Import modules
try:
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
logger.info("🚀 Starting Enhanced Financial News Detector Bot...")

# Global shutdown flag
should_exit = False
bot_instance = None

def parse_args():
    """Parse command line arguments with AI support."""
    parser = argparse.ArgumentParser(description='Enhanced Financial News Detector Bot')
    
    # Mode selection
    parser.add_argument('--ai-mode', choices=['free', 'manual', 'hybrid'], 
                        default=None, help='AI operation mode')
    parser.add_argument('--manual-mode', action='store_true',
                        help='Force manual approval mode')
    
    # Testing options
    parser.add_argument('--test-ai', action='store_true',
                        help='Test AI system with sample data')
    parser.add_argument('--test-news', action='store_true',
                        help='Test news detection and processing')
    parser.add_argument('--sample-news', type=str,
                        help='Test AI with specific news text')
    
    # Configuration
    parser.add_argument('--news-channel', type=str,
                        help='Channel to process news from')
    parser.add_argument('--force-24h', action='store_true',
                        help='Force 24-hour operation')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug mode')
    
    # Statistics and monitoring
    parser.add_argument('--stats', action='store_true',
                        help='Show statistics and exit')
    parser.add_argument('--ai-stats', action='store_true',
                        help='Show AI statistics and exit')
    
    # AI management
    parser.add_argument('--download-models', action='store_true',
                        help='Download AI models and exit')
    parser.add_argument('--clear-ai-cache', action='store_true',
                        help='Clear AI cache and models')
    
    return parser.parse_args()

def signal_handler(sig, frame):
    """Handle termination signals gracefully."""
    global should_exit, bot_instance
    logger.info(f"📡 Received signal {sig}, initiating graceful shutdown...")
    should_exit = True
    
    if bot_instance:
        bot_instance.request_shutdown()

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
signal.signal(signal.SIGTERM, signal_handler)  # Termination signal

class EnhancedFinancialNewsBot:
    """Enhanced financial news bot with AI capabilities."""

    def __init__(self, ai_mode=None, force_24h=False, debug_mode=False):
        """Initialize enhanced bot with AI support."""
        self.client_manager = TelegramClientManager()
        self.news_handler = None
        self.running = False
        self.start_time = None
        self.force_24h = force_24h
        self.debug_mode = debug_mode
        self.shutdown_requested = False
        
        # Determine AI mode
        self.ai_mode = ai_mode or os.getenv('AI_MODE', 'auto')
        self.ai_enabled = os.getenv('AI_ENABLED', 'true').lower() == 'true'
        
        # Statistics
        self.stats = {
            'total_updates': 0,
            'news_processed': 0,
            'news_sent_for_approval': 0,
            'news_approved': 0,
            'news_published': 0,
            'ai_decisions': 0,
            'human_decisions': 0,
            'errors': 0,
            'start_time': None,
            'mode': 'unknown'
        }

    def request_shutdown(self):
        """Request graceful shutdown."""
        self.shutdown_requested = True
        self.running = False

    async def start(self):
        """Start the enhanced financial news bot."""
        logger.info("⚙️ Initializing Enhanced Financial News Bot...")
        
        try:
            # Validate credentials
            logger.info("🔐 Validating credentials...")
            validate_credentials()
            logger.info("✅ Credentials validated")

            # Start Telegram client
            logger.info("📱 Starting Telegram client...")
            if not await self.client_manager.start():
                logger.error("❌ Failed to start Telegram client")
                return False

            # Initialize appropriate news handler
            await self._initialize_news_handler()

            self.running = True
            self.start_time = time.time()
            self.stats['start_time'] = self.start_time
            
            # Log startup info
            self._log_startup_info()

            logger.info("🎉 Enhanced Financial News Bot started successfully!")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to start bot: {e}")
            if self.debug_mode:
                import traceback
                traceback.print_exc()
            return False

    async def _initialize_news_handler(self):
        """Initialize appropriate news handler based on mode."""
        try:
            # Determine which handler to use
            handler_mode = await self._determine_handler_mode()
            
            if handler_mode == 'ai':
                logger.info("🤖 Initializing AI News Handler...")
                from src.handlers.ai_news_handler import AINewsHandler
                self.news_handler = AINewsHandler(self.client_manager)
                await self.news_handler.initialize()
                self.stats['mode'] = 'ai'
                logger.info("✅ AI News Handler initialized")
                
            else:
                logger.info("📝 Initializing Manual News Handler...")
                from src.handlers.news_handler import NewsHandler
                self.news_handler = NewsHandler(self.client_manager)
                
                # Initialize manual handler components
                if hasattr(self.news_handler, 'initialize'):
                    await self.news_handler.initialize()
                
                self.stats['mode'] = 'manual'
                logger.info("✅ Manual News Handler initialized")
            
            # Set up approval handler
            logger.info("👨‍💼 Setting up approval handler...")
            if hasattr(self.news_handler, 'setup_ai_approval_handler'):
                await self.news_handler.setup_ai_approval_handler()
            elif hasattr(self.news_handler, 'setup_approval_handler'):
                await self.news_handler.setup_approval_handler()
            
            logger.info("✅ Approval handler set up")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize news handler: {e}")
            raise

    async def _determine_handler_mode(self):
        """Determine which handler mode to use."""
        # Check command line argument
        if hasattr(self, 'ai_mode') and self.ai_mode:
            if self.ai_mode == 'free':
                return 'ai'
            elif self.ai_mode == 'manual':
                return 'manual'
        
        # Check environment variable
        if self.ai_enabled:
            try:
                # Test if AI components are available
                from src.handlers.ai_news_handler import AINewsHandler
                from src.ai.free_ai_engine import get_free_ai_engine
                
                # Quick availability check
                test_engine = await get_free_ai_engine()
                if test_engine:
                    return 'ai'
                    
            except ImportError:
                logger.warning("AI components not available, falling back to manual mode")
            except Exception as e:
                logger.warning(f"AI initialization failed, falling back to manual mode: {e}")
        
        return 'manual'

    def _log_startup_info(self):
        """Log startup information."""
        logger.info("=" * 70)
        logger.info("📊 ENHANCED FINANCIAL NEWS DETECTOR CONFIGURATION")
        logger.info("=" * 70)
        logger.info(f"🤖 Mode: {self.stats['mode'].upper()}")
        logger.info(f"🎯 Target Channel: {TARGET_CHANNEL_ID}")
        logger.info(f"📺 News Channels: {NEWS_CHANNEL}, {TWITTER_NEWS_CHANNEL}")
        logger.info(f"⏰ Check Interval: {NEWS_CHECK_INTERVAL}s")
        logger.info(f"🕐 Operating Hours: {OPERATION_START_HOUR:02d}:{OPERATION_START_MINUTE:02d} - {OPERATION_END_HOUR:02d}:{OPERATION_END_MINUTE:02d}")
        logger.info(f"🌐 24h Mode: {'Enabled' if self.force_24h else 'Disabled'}")
        logger.info(f"🐛 Debug Mode: {'Enabled' if self.debug_mode else 'Disabled'}")
        logger.info(f"📎 Media Processing: {'Enabled' if ENABLE_MEDIA_PROCESSING else 'Disabled'}")
        
        if self.stats['mode'] == 'ai':
            logger.info(f"🧠 AI Engine: FREE Local Models")
            logger.info(f"🎛️ AI Thresholds: Auto-tune enabled")
        
        log_time_status()
        logger.info("=" * 70)

    async def run_continuous_monitoring(self):
        """Main continuous monitoring loop with AI support."""
        logger.info("🔄 Starting continuous news monitoring...")
        logger.info(f"🤖 Running in {self.stats['mode'].upper()} mode")
        
        last_news_check = 0
        last_status_log = 0
        last_state_save = 0
        
        try:
            while self.running and not should_exit and not self.shutdown_requested:
                try:
                    current_time = time.time()
                    
                    # Check operating hours
                    if not self.force_24h and not is_operating_hours():
                        if current_time - last_status_log >= 3600:
                            logger.info("💤 Outside operating hours, monitoring in idle mode...")
                            last_status_log = current_time
                        await asyncio.sleep(300)
                        continue
                    
                    # Process news
                    if current_time - last_news_check >= NEWS_CHECK_INTERVAL:
                        await self._process_news_updates()
                        last_news_check = current_time
                        self.stats['total_updates'] += 1
                    
                    # Periodic state saving
                    if current_time - last_state_save >= 300:
                        if hasattr(self.news_handler, 'save_ai_state'):
                            await self.news_handler.save_ai_state()
                        elif hasattr(self.news_handler, 'save_pending_news'):
                            await self.news_handler.save_pending_news()
                        last_state_save = current_time
                    
                    # Status logging
                    if current_time - last_status_log >= 1800:
                        await self._log_status()
                        last_status_log = current_time
                    
                    await asyncio.sleep(60)
                    
                except asyncio.CancelledError:
                    logger.info("🛑 Monitoring loop cancelled")
                    break
                except Exception as e:
                    logger.error(f"Error in monitoring loop: {e}")
                    self.stats['errors'] += 1
                    if self.debug_mode:
                        import traceback
                        traceback.print_exc()
                    await asyncio.sleep(60)
                    
        except KeyboardInterrupt:
            logger.info("⌨️ Received keyboard interrupt")
        finally:
            await self.stop()

    async def _process_news_updates(self):
        """Process news updates using appropriate handler."""
        try:
            logger.info(f"📰 Processing news updates ({self.stats['mode']} mode)...")
            
            # Get news channels
            news_channels = []
            if NEWS_CHANNEL:
                news_channels.append(NEWS_CHANNEL)
            if TWITTER_NEWS_CHANNEL:
                news_channels.append(TWITTER_NEWS_CHANNEL)
            
            if not news_channels:
                logger.warning("No news channels configured")
                return
            
            # Process each channel
            for channel in news_channels:
                try:
                    logger.info(f"Processing news from: {channel}")
                    
                    # Use appropriate processing method
                    if self.stats['mode'] == 'ai' and hasattr(self.news_handler, 'process_news_messages_ai'):
                        result = await self.news_handler.process_news_messages_ai(channel)
                        if result:
                            self.stats['ai_decisions'] += 1
                    else:
                        result = await self.news_handler.process_news_messages(channel)
                        if result:
                            self.stats['human_decisions'] += 1
                    
                    if result:
                        self.stats['news_processed'] += 1
                        logger.info(f"✅ Successfully processed news from {channel}")
                    
                    await asyncio.sleep(5)
                    
                except Exception as channel_error:
                    logger.error(f"Error processing {channel}: {channel_error}")
                    self.stats['errors'] += 1
                    continue
            
            # Cleanup
            if hasattr(self.news_handler, 'clean_expired_pending_news'):
                await self.news_handler.clean_expired_pending_news()
            
            logger.info("✅ News processing completed")
            
        except Exception as e:
            logger.error(f"❌ Error in news processing: {e}")
            self.stats['errors'] += 1

    async def _log_status(self):
        """Log current status with AI metrics."""
        if self.start_time:
            uptime = int(time.time() - self.start_time)
            
            # Basic stats
            basic_stats = (
                f"📊 Uptime: {uptime}s | "
                f"Mode: {self.stats['mode'].upper()} | "
                f"Processed: {self.stats['news_processed']} | "
                f"Errors: {self.stats['errors']}"
            )
            
            # AI-specific stats
            if self.stats['mode'] == 'ai' and hasattr(self.news_handler, 'get_comprehensive_stats'):
                try:
                    ai_stats = self.news_handler.get_comprehensive_stats()
                    ai_info = (
                        f" | AI Approved: {ai_stats.get('ai_auto_approved', 0)} | "
                        f"Human Review: {ai_stats.get('ai_human_review', 0)} | "
                        f"Automation: {ai_stats.get('automation_rate', 0):.1f}%"
                    )
                    basic_stats += ai_info
                except Exception as e:
                    logger.debug(f"Could not get AI stats: {e}")
            
            logger.info(basic_stats)
            
            # Pending items
            pending_count = 0
            if hasattr(self.news_handler, 'pending_news'):
                pending_count = len(self.news_handler.pending_news)
            elif hasattr(self.news_handler, 'human_review_queue'):
                pending_count = len(self.news_handler.human_review_queue)
            
            if pending_count > 0:
                logger.info(f"⏳ {pending_count} items pending approval/review")

    async def test_ai_system(self, sample_text=None):
        """Test AI system functionality."""
        logger.info("🧪 Testing AI system...")
        
        if self.stats['mode'] != 'ai':
            logger.error("❌ AI mode not active")
            return False
        
        try:
            if hasattr(self.news_handler, 'ai_engine') and self.news_handler.ai_engine:
                # Test with sample or default text
                test_text = sample_text or "قیمت طلای ۱۸ عیار امروز به ۲.۵ میلیون تومان رسید"
                
                logger.info(f"🧪 Testing AI with: {test_text[:100]}...")
                
                result = await self.news_handler.ai_engine.analyze_news(test_text)
                
                logger.info(f"🎯 AI Decision: {result.decision}")
                logger.info(f"📊 Confidence: {result.confidence:.1f}/10")
                logger.info(f"💰 Financial Score: {result.financial_score:.1f}/10")
                logger.info(f"✨ Quality Score: {result.quality_score:.1f}/10")
                logger.info(f"💭 Reasoning: {result.reasoning}")
                logger.info(f"⏱️ Processing Time: {result.processing_time:.2f}s")
                
                logger.info("✅ AI test completed successfully")
                return True
            else:
                logger.error("❌ AI engine not available")
                return False
                
        except Exception as e:
            logger.error(f"❌ AI test failed: {e}")
            return False

    async def show_statistics(self):
        """Show comprehensive statistics."""
        logger.info("📊 ENHANCED FINANCIAL NEWS STATISTICS")
        logger.info("=" * 60)
        
        # Current time
        from src.utils.time_utils import get_formatted_time
        current_time = get_formatted_time(format_type="persian_full")
        logger.info(f"🗓️ Current Time: {current_time}")
        
        # Basic stats
        if self.start_time:
            uptime = int(time.time() - self.start_time)
            hours = uptime // 3600
            minutes = (uptime % 3600) // 60
            logger.info(f"⏰ Uptime: {hours}h {minutes}m")
        
        logger.info(f"🤖 Mode: {self.stats['mode'].upper()}")
        
        for key, value in self.stats.items():
            if key not in ['start_time', 'mode']:
                formatted_key = key.replace('_', ' ').title()
                logger.info(f"📈 {formatted_key}: {value}")
        
        # Handler-specific stats
        if hasattr(self.news_handler, 'get_comprehensive_stats'):
            try:
                handler_stats = self.news_handler.get_comprehensive_stats()
                
                logger.info("\n📊 HANDLER STATISTICS")
                logger.info("-" * 30)
                
                important_stats = [
                    'pending_reviews', 'automation_rate', 'human_intervention_rate',
                    'ai_auto_approved', 'ai_auto_rejected', 'ai_human_review'
                ]
                
                for stat in important_stats:
                    if stat in handler_stats:
                        value = handler_stats[stat]
                        if isinstance(value, float):
                            value = f"{value:.1f}%"
                        logger.info(f"📊 {stat.replace('_', ' ').title()}: {value}")
                        
            except Exception as e:
                logger.debug(f"Could not get handler stats: {e}")

    async def download_ai_models(self):
        """Download and cache AI models."""
        logger.info("📥 Downloading AI models...")
        
        try:
            from src.ai.free_ai_engine import FreeAIModels
            
            models = FreeAIModels()
            await models.initialize_models()
            
            logger.info("✅ AI models downloaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Model download failed: {e}")
            return False

    async def clear_ai_cache(self):
        """Clear AI cache and models."""
        logger.info("🧹 Clearing AI cache...")
        
        try:
            import shutil
            
            # Clear model cache
            models_dir = Path("models")
            if models_dir.exists():
                shutil.rmtree(models_dir)
                logger.info("🗑️ Models directory cleared")
            
            # Clear AI cache
            cache_dir = Path("ai_cache")
            if cache_dir.exists():
                shutil.rmtree(cache_dir)
                logger.info("🗑️ AI cache cleared")
            
            logger.info("✅ AI cache cleared successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Cache clearing failed: {e}")
            return False

    async def stop(self):
        """Stop the bot gracefully."""
        logger.info("🛑 Stopping Enhanced Financial News Bot...")
        self.running = False
        
        try:
            # Save handler state
            if hasattr(self.news_handler, 'save_ai_state'):
                logger.info("💾 Saving AI state...")
                await self.news_handler.save_ai_state()
            elif hasattr(self.news_handler, 'save_pending_news'):
                logger.info("💾 Saving pending news...")
                await self.news_handler.save_pending_news()
            
            # Save AI learning data
            if (hasattr(self.news_handler, 'ai_engine') and 
                self.news_handler.ai_engine and
                hasattr(self.news_handler.ai_engine, 'save_learning_data')):
                self.news_handler.ai_engine.save_learning_data()
                logger.info("📚 AI learning data saved")
            
            # Stop client
            if self.client_manager:
                await self.client_manager.stop()
                logger.info("📱 Telegram client stopped")
                
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

async def main():
    """Enhanced main entry point."""
    global bot_instance
    
    args = parse_args()
    
    # Enable debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("🐛 Debug mode enabled")
    
    # Handle special operations
    if args.clear_ai_cache:
        bot_instance = EnhancedFinancialNewsBot()
        success = await bot_instance.clear_ai_cache()
        return 0 if success else 1
    
    if args.download_models:
        bot_instance = EnhancedFinancialNewsBot()
        success = await bot_instance.download_ai_models()
        return 0 if success else 1
    
    # Create bot instance
    ai_mode = args.ai_mode or ('manual' if args.manual_mode else 'auto')
    bot_instance = EnhancedFinancialNewsBot(
        ai_mode=ai_mode,
        force_24h=args.force_24h, 
        debug_mode=args.debug
    )
    
    try:
        # Start the bot
        if not await bot_instance.start():
            logger.error("❌ Failed to start bot")
            return 1

        # Handle different modes
        if args.stats or args.ai_stats:
            await bot_instance.show_statistics()
            return 0

        if args.test_ai:
            success = await bot_instance.test_ai_system(args.sample_news)
            return 0 if success else 1

        if args.sample_news:
            success = await bot_instance.test_ai_system(args.sample_news)
            return 0 if success else 1

        # Normal operation
        logger.info(f"🚀 Running in {bot_instance.stats['mode'].upper()} mode")
        
        # Log current status
        if is_operating_hours():
            logger.info("🟢 Within operating hours - active monitoring")
        elif bot_instance.force_24h:
            logger.info("🔵 24-hour operation - active monitoring")
        else:
            logger.info("🟡 Outside operating hours - idle monitoring")

        # Run continuous monitoring
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

    logger.info("👋 Enhanced Financial News Detector shutdown complete")
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)