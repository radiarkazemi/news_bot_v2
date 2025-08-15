#!/usr/bin/env python3
"""
Debug test script to force process recent messages and see what's happening.
This bypasses some filtering to show you what messages are available.
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

async def debug_test_messages():
    """Test messages with detailed debug output."""
    
    print("🔍 DEBUG TEST - Recent Messages Analysis")
    print("=" * 60)
    
    # Create client and detector
    client_manager = TelegramClientManager()
    detector = NewsDetector()
    
    try:
        # Start client
        if not await client_manager.start():
            print("❌ Failed to start Telegram client")
            return
        
        # Test goldonline2016 channel
        channel_name = "goldonline2016"
        channel_username = f"@{channel_name}"
        
        print(f"📺 Testing channel: {channel_username}")
        
        try:
            channel_entity = await client_manager.client.get_entity(channel_username)
            print(f"✅ Connected to {channel_username}")
            
            # Get last 10 messages
            message_count = 0
            
            async for message in client_manager.client.iter_messages(channel_entity, limit=10):
                message_count += 1
                
                print(f"\n📝 MESSAGE {message_count} (ID: {message.id})")
                print(f"🕐 Date: {message.date}")
                print(f"📏 Length: {len(message.text) if message.text else 0} chars")
                
                if not message.text or len(message.text.strip()) < 30:
                    print("❌ SKIPPED: No text or too short")
                    continue
                
                # Show message preview
                preview = message.text[:200].replace('\n', ' ')
                print(f"📄 Preview: {preview}...")
                
                # Test news detection (bypass filters)
                print("\n🔍 DETAILED ANALYSIS:")
                
                # Step 1: Basic news detection
                is_news = detector.is_news(message.text)
                print(f"   📊 Basic News Detection: {'✅ YES' if is_news else '❌ NO'}")
                
                if is_news:
                    # Get category and score
                    category = detector.get_news_category(message.text)
                    score = detector.get_relevance_score(message.text)
                    print(f"   💰 Category: {category}")
                    print(f"   📈 Detector Score: {score}")
                    
                    # Test NewsFilter
                    try:
                        is_relevant, filter_score, topics = NewsFilter.is_relevant_news(message.text)
                        priority = NewsFilter.get_priority_level(filter_score)
                        
                        print(f"   🎯 NewsFilter Relevant: {'✅ YES' if is_relevant else '❌ NO'}")
                        print(f"   📊 NewsFilter Score: {filter_score}")
                        print(f"   ⚡ Priority: {priority}")
                        print(f"   🏷️ Topics: {', '.join(topics[:5])}")
                        
                        # Show why it was filtered
                        if not is_relevant:
                            print(f"   🚫 FILTERED: Score {filter_score} too low")
                        else:
                            print(f"   ✅ WOULD BE APPROVED!")
                            
                    except Exception as e:
                        print(f"   ❌ Filter Error: {e}")
                
                print("-" * 40)
                
                # Stop after first few for readability
                if message_count >= 5:
                    break
            
        except Exception as e:
            print(f"❌ Error testing channel: {e}")
        
    finally:
        await client_manager.stop()

async def test_with_sample_text():
    """Test with known financial text samples."""
    
    print("\n🧪 TESTING WITH SAMPLE FINANCIAL TEXTS")
    print("=" * 50)
    
    detector = NewsDetector()
    
    # Test messages that should definitely work
    test_messages = [
        "قیمت طلای ۱۸ عیار امروز ۲.۵ میلیون تومان اعلام شد",
        "نرخ دلار در بازار آزاد به ۵۲ هزار تومان رسید", 
        "بازار ارز تهران امروز با نوسان شدیدی همراه بود",
        "سکه طلا با افزایش ۱۰۰ هزار تومانی همراه شد",
        "یورو در مقابل تومان به ۵۵ هزار تومان رسید"
    ]
    
    for i, text in enumerate(test_messages, 1):
        print(f"\n🧪 SAMPLE {i}: {text}")
        
        # Test detection
        is_news = detector.is_news(text)
        print(f"📊 Detection: {'✅ YES' if is_news else '❌ NO'}")
        
        if is_news:
            category = detector.get_news_category(text)
            score = detector.get_relevance_score(text)
            print(f"💰 Category: {category}")
            print(f"📈 Score: {score}")
            
            try:
                is_relevant, filter_score, topics = NewsFilter.is_relevant_news(text)
                priority = NewsFilter.get_priority_level(filter_score)
                print(f"🎯 Relevant: {'✅ YES' if is_relevant else '❌ NO'}")
                print(f"📊 Filter Score: {filter_score}")
                print(f"⚡ Priority: {priority}")
            except Exception as e:
                print(f"❌ Filter Error: {e}")

async def main():
    """Main debug function."""
    print("🚀 FINANCIAL NEWS DEBUG TEST")
    print("=" * 80)
    
    # Test sample texts first
    await test_with_sample_text()
    
    # Then test actual channel messages
    await debug_test_messages()
    
    print("\n✅ DEBUG TEST COMPLETE!")
    print("\n💡 If sample texts work but channel messages don't:")
    print("   1. Lower MIN_FINANCIAL_SCORE and MIN_RELEVANCE_SCORE in .env")
    print("   2. Channel might not have recent financial news")
    print("   3. Try a different channel or time period")

if __name__ == "__main__":
    asyncio.run(main())