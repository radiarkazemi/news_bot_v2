#!/usr/bin/env python3
"""
Debug script to see what messages are in the channels and test detection.
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from src.client.telegram_client import TelegramClientManager
from src.services.news_detector import NewsDetector
from src.services.news_filter import NewsFilter

async def debug_channel_messages():
    """Debug what messages are in the channels and test detection."""
    
    print("🔍 DEBUGGING CHANNEL MESSAGES")
    print("=" * 60)
    
    # Create client and detector
    client_manager = TelegramClientManager()
    detector = NewsDetector()
    
    try:
        # Start client
        if not await client_manager.start():
            print("❌ Failed to start Telegram client")
            return
        
        # Channels to check
        channels = ["goldonline2016", "twiier_news"]
        
        for channel_name in channels:
            print(f"\n📺 CHECKING CHANNEL: {channel_name}")
            print("-" * 50)
            
            try:
                # Get channel entity
                channel_username = f"@{channel_name}"
                channel_entity = await client_manager.client.get_entity(channel_username)
                
                # Get recent messages (last 3 hours)
                cutoff_time = datetime.now() - timedelta(hours=3)
                message_count = 0
                news_count = 0
                
                print(f"📥 Retrieving messages from {channel_username} (last 3 hours)")
                
                async for message in client_manager.client.iter_messages(channel_entity, limit=10):
                    message_count += 1
                    
                    # Skip if too old
                    if message.date.replace(tzinfo=None) < cutoff_time:
                        continue
                    
                    # Skip if no text
                    if not message.text or len(message.text.strip()) < 30:
                        continue
                    
                    print(f"\n📝 MESSAGE {message_count} (ID: {message.id})")
                    print(f"🕐 Time: {message.date}")
                    print(f"📄 Text: {message.text[:200]}...")
                    
                    # Test detection
                    is_news = detector.is_news(message.text)
                    print(f"📊 Is News: {'✅ YES' if is_news else '❌ NO'}")
                    
                    if is_news:
                        news_count += 1
                        
                        # Test relevance
                        try:
                            is_relevant, score, topics = NewsFilter.is_relevant_news(message.text)
                            priority = NewsFilter.get_priority_level(score)
                            
                            print(f"🎯 Relevant: {'✅ YES' if is_relevant else '❌ NO'}")
                            print(f"📈 Score: {score}")
                            print(f"⚡ Priority: {priority}")
                            print(f"🏷️ Topics: {', '.join(topics[:3])}")
                            
                        except Exception as e:
                            print(f"❌ Filter Error: {e}")
                    
                    print("-" * 30)
                
                print(f"\n📊 CHANNEL SUMMARY: {channel_name}")
                print(f"📥 Total Messages Checked: {message_count}")
                print(f"📰 News Detected: {news_count}")
                print(f"📈 Detection Rate: {(news_count/message_count*100):.1f}%" if message_count > 0 else "No messages")
                
            except Exception as e:
                print(f"❌ Error checking {channel_name}: {e}")
        
    finally:
        await client_manager.stop()

async def test_specific_message():
    """Test detection on a specific message."""
    
    print("\n🧪 TESTING SPECIFIC MESSAGES")
    print("=" * 50)
    
    detector = NewsDetector()
    
    # Test messages (add your examples here)
    test_messages = [
        "ترامپ دوباره ایران را به حمله تهدید کرد",
        "قیمت طلای ۱۸ عیار امروز به ۲.۵ میلیون تومان رسید", 
        "بازار ارز امروز با نوسان همراه بود",
        "نرخ دلار در صرافی ها ۵۲ هزار تومان شد"
    ]
    
    for i, text in enumerate(test_messages, 1):
        print(f"\n🧪 TEST {i}: {text}")
        
        is_news = detector.is_news(text)
        print(f"📊 Detection: {'✅ YES' if is_news else '❌ NO'}")
        
        if is_news:
            try:
                is_relevant, score, topics = NewsFilter.is_relevant_news(text)
                print(f"🎯 Relevant: {'✅ YES' if is_relevant else '❌ NO'}")
                print(f"📈 Score: {score}")
                print(f"🏷️ Topics: {', '.join(topics[:3])}")
            except Exception as e:
                print(f"❌ Filter Error: {e}")

async def main():
    """Main debug function."""
    await test_specific_message()
    await debug_channel_messages()

if __name__ == "__main__":
    asyncio.run(main())