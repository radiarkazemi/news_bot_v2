#!/usr/bin/env python3
"""
Enhanced debug script to see exactly what's happening with message detection.
This will show you exactly why messages are being filtered out.
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
    """Debug what messages are in the channels and why they're being filtered."""
    
    print("🔍 DETAILED CHANNEL MESSAGE ANALYSIS")
    print("=" * 80)
    
    # Create client and detector
    client_manager = TelegramClientManager()
    detector = NewsDetector()
    
    try:
        # Start client
        if not await client_manager.start():
            print("❌ Failed to start Telegram client")
            return
        
        # Check both channels
        channels = ["goldonline2016", "twiier_news"]
        
        for channel_name in channels:
            print(f"\n📺 ANALYZING CHANNEL: {channel_name}")
            print("=" * 60)
            
            try:
                # Get channel entity
                channel_username = f"@{channel_name}"
                channel_entity = await client_manager.client.get_entity(channel_username)
                
                print(f"✅ Connected to {channel_username}")
                print(f"📊 Channel Title: {getattr(channel_entity, 'title', 'Unknown')}")
                print(f"👥 Members: {getattr(channel_entity, 'participants_count', 'Unknown')}")
                
                # Get recent messages - Check last 24 hours instead of 3
                cutoff_time = datetime.now() - timedelta(hours=24)
                message_count = 0
                processed_count = 0
                news_detected_count = 0
                relevant_count = 0
                
                print(f"\n📥 Analyzing last 50 messages (last 24 hours)")
                print("-" * 40)
                
                async for message in client_manager.client.iter_messages(channel_entity, limit=50):
                    message_count += 1
                    
                    # Check message age
                    message_age_hours = (datetime.now() - message.date.replace(tzinfo=None)).total_seconds() / 3600
                    
                    print(f"\n📝 MESSAGE {message_count} (ID: {message.id})")
                    print(f"🕐 Age: {message_age_hours:.1f} hours ago")
                    print(f"📏 Length: {len(message.text) if message.text else 0} chars")
                    
                    # Skip if no text
                    if not message.text:
                        print("❌ SKIPPED: No text content")
                        continue
                    
                    # Skip if too short
                    if len(message.text.strip()) < 30:
                        print("❌ SKIPPED: Too short (< 30 chars)")
                        continue
                    
                    # Skip if too old (only for the 3-hour filter the bot uses)
                    if message.date.replace(tzinfo=None) < cutoff_time:
                        print("⏰ WOULD BE SKIPPED: Outside 3-hour window (bot filter)")
                    
                    processed_count += 1
                    
                    # Show message preview
                    preview = message.text[:150].replace('\n', ' ')
                    print(f"📄 Preview: {preview}...")
                    
                    # Test financial news detection
                    print("\n🔍 DETECTION ANALYSIS:")
                    
                    # Step 1: Basic news detection
                    is_news = detector.is_news(message.text)
                    print(f"   📊 Is News: {'✅ YES' if is_news else '❌ NO'}")
                    
                    if is_news:
                        news_detected_count += 1
                        
                        # Get category and score
                        category = detector.get_news_category(message.text)
                        score = detector.get_relevance_score(message.text)
                        print(f"   💰 Category: {category}")
                        print(f"   📈 Raw Score: {score}")
                        
                        # Step 2: Relevance filtering
                        try:
                            is_relevant, filter_score, topics = NewsFilter.is_relevant_news(message.text)
                            priority = NewsFilter.get_priority_level(filter_score)
                            
                            print(f"   🎯 Relevant: {'✅ YES' if is_relevant else '❌ NO'}")
                            print(f"   📊 Filter Score: {filter_score}")
                            print(f"   ⚡ Priority: {priority}")
                            print(f"   🏷️ Topics: {', '.join(topics[:5])}")
                            
                            if is_relevant:
                                relevant_count += 1
                                print("   🎉 WOULD BE SENT FOR APPROVAL!")
                            else:
                                print("   🚫 FILTERED OUT - Not relevant enough")
                                
                        except Exception as e:
                            print(f"   ❌ Filter Error: {e}")
                    else:
                        print("   🚫 FILTERED OUT - Not detected as news")
                        
                        # Show why it wasn't detected
                        text_lower = message.text.lower()
                        
                        # Check for financial keywords
                        financial_keywords = ["طلا", "سکه", "دلار", "یورو", "ارز", "نرخ", "قیمت", "بازار"]
                        found_financial = [kw for kw in financial_keywords if kw in text_lower]
                        if found_financial:
                            print(f"   💡 Found financial keywords: {found_financial}")
                        
                        # Check for war keywords
                        war_keywords = ["جنگ", "حمله", "ایران", "اسرائیل", "تحریم"]
                        found_war = [kw for kw in war_keywords if kw in text_lower]
                        if found_war:
                            print(f"   💡 Found war keywords: {found_war}")
                    
                    print("-" * 40)
                
                print(f"\n📊 CHANNEL SUMMARY: {channel_name}")
                print("=" * 40)
                print(f"📥 Total Messages: {message_count}")
                print(f"📝 Processed (>30 chars): {processed_count}")
                print(f"📰 News Detected: {news_detected_count}")
                print(f"🎯 Relevant News: {relevant_count}")
                print(f"📈 Detection Rate: {(news_detected_count/processed_count*100):.1f}%" if processed_count > 0 else "N/A")
                print(f"🎯 Relevance Rate: {(relevant_count/news_detected_count*100):.1f}%" if news_detected_count > 0 else "N/A")
                
            except Exception as e:
                print(f"❌ Error analyzing {channel_name}: {e}")
                import traceback
                traceback.print_exc()
        
    finally:
        await client_manager.stop()

async def test_sample_messages():
    """Test detection on sample gold/financial messages."""
    
    print("\n🧪 TESTING SAMPLE FINANCIAL MESSAGES")
    print("=" * 50)
    
    detector = NewsDetector()
    
    # Sample messages that should be detected
    test_messages = [
        "قیمت طلای ۱۸ عیار امروز ۲ میلیون و ۵۰۰ هزار تومان اعلام شد",
        "نرخ دلار در بازار آزاد به ۵۲ هزار تومان رسید",
        "سکه طلا امروز با افزایش ۱۰۰ هزار تومانی همراه بود",
        "بازار ارز امروز با نوسان شدیدی همراه بود",
        "یورو در مقابل تومان به ۵۵ هزار تومان رسید",
        "بورس تهران امروز با رشد ۲ درصدی بسته شد",
        "تحریم های جدید آمریکا بر اقتصاد ایران تاثیر گذاشت",
        "تحلیل بازار طلا: انتظار افزایش قیمت تا پایان هفته",
        "شاخص دلار جهانی امروز کاهش یافت",
        "قیمت نفت برنت به ۷۰ دلار رسید"
    ]
    
    for i, text in enumerate(test_messages, 1):
        print(f"\n🧪 TEST {i}: {text}")
        
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
                print(f"🏷️ Topics: {', '.join(topics[:3])}")
            except Exception as e:
                print(f"❌ Filter Error: {e}")
        
        print("-" * 30)

async def main():
    """Main debug function."""
    print("🚀 FINANCIAL NEWS DETECTION DEBUG TOOL")
    print("=" * 80)
    
    # Test sample messages first
    await test_sample_messages()
    
    # Then analyze actual channels
    await debug_channel_messages()
    
    print("\n✅ DEBUG ANALYSIS COMPLETE!")
    print("\n💡 RECOMMENDATIONS:")
    print("1. If financial messages aren't being detected, the keywords may need adjustment")
    print("2. If messages are detected but filtered out, the scoring thresholds are too high")
    print("3. Check your .env settings - WAR_NEWS_ONLY should be false for financial news")

if __name__ == "__main__":
    asyncio.run(main())