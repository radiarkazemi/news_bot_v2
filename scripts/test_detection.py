# scripts/test_detection.py
"""
Test script for validating news detection system.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.client.telegram_client import TelegramClientManager
from src.handlers.news_handler import NewsHandler
from config.credentials import validate_credentials


async def test_channel_processing(channel_name):
    """Test processing news from a specific channel."""
    print(f"Testing news processing from channel: {channel_name}")
    
    try:
        # Validate credentials
        validate_credentials()
        
        # Initialize client
        client_manager = TelegramClientManager()
        if not await client_manager.start():
            print("Failed to start Telegram client")
            return
        
        # Initialize news handler
        news_handler = NewsHandler(client_manager)
        await news_handler.setup_approval_handler()
        
        # Process news from channel
        result = await news_handler.process_news_messages(channel_name)
        
        if result:
            print(f"✅ Successfully processed news from {channel_name}")
            print(f"Pending approvals: {len(news_handler.pending_news)}")
        else:
            print(f"❌ No news found or processed from {channel_name}")
        
        # Stop client
        await client_manager.stop()
        
    except Exception as e:
        print(f"Error: {e}")


async def main():
    """Main test function."""
    if len(sys.argv) > 1:
        channel = sys.argv[1]
        await test_channel_processing(channel)
    else:
        print("Usage: python test_detection.py <channel_username>")
        print("Example: python test_detection.py goldonline2016")


if __name__ == "__main__":
    asyncio.run(main())