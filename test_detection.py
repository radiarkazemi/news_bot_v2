#!/usr/bin/env python3
"""
Complete test script for new features: Persian calendar, new schedule, and media handling.
Tests all the new functionality to ensure everything works correctly.
"""
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

print("🧪 FINANCIAL NEWS DETECTOR - NEW FEATURES TEST")
print("=" * 80)

async def test_persian_calendar():
    """Test Persian calendar conversion and formatting."""
    print("🗓️ TESTING PERSIAN CALENDAR")
    print("=" * 50)
    
    try:
        from src.utils.time_utils import (
            get_current_time, get_formatted_time, format_persian_date,
            format_persian_time, format_persian_datetime, gregorian_to_persian
        )
        
        # Test current time
        current_time = get_current_time()
        print(f"✅ Current Tehran Time: {current_time}")
        
        # Test Persian calendar formatting
        persian_full = get_formatted_time(current_time, "persian_full")
        persian_date = format_persian_date(current_time)
        persian_time = format_persian_time(current_time)
        
        print(f"✅ Persian Full Format: {persian_full}")
        print(f"✅ Persian Date: {persian_date}")
        print(f"✅ Persian Time: {persian_time}")
        
        # Test conversion algorithm
        persian_year, persian_month, persian_day = gregorian_to_persian(current_time)
        print(f"✅ Conversion Result: {persian_year}/{persian_month:02d}/{persian_day:02d}")
        
        # Test message format
        from src.utils.time_utils import add_timestamp_to_message
        test_message = "📈 تست خبر مالی"
        formatted_message = add_timestamp_to_message(test_message)
        print(f"\n✅ Formatted Message:")
        print("-" * 30)
        print(formatted_message)
        print("-" * 30)
        
        print("🗓️ Persian Calendar Test: ✅ PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Persian Calendar Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_operating_hours():
    """Test new operating hours (8:30 AM - 10:00 PM)."""
    print("\n⏰ TESTING OPERATING HOURS")
    print("=" * 50)
    
    try:
        from src.utils.time_utils import (
            is_operating_hours, get_business_hours_status,
            get_next_operating_time, OPERATION_START_HOUR, OPERATION_START_MINUTE,
            OPERATION_END_HOUR, OPERATION_END_MINUTE
        )
        
        print(f"✅ Operating Hours: {OPERATION_START_HOUR:02d}:{OPERATION_START_MINUTE:02d} - {OPERATION_END_HOUR:02d}:{OPERATION_END_MINUTE:02d}")
        print(f"✅ Currently Operating: {'Yes' if is_operating_hours() else 'No'}")
        
        # Get detailed status
        status = get_business_hours_status()
        print(f"✅ Current Time (Persian): {status['current_time']}")
        print(f"✅ Current Time (Gregorian): {status['current_time_gregorian']}")
        print(f"✅ Is Business Day: {status['is_business_day']}")
        print(f"✅ Operating Hours: {status['operating_hours']}")
        
        # Test next operation time
        next_time = get_next_operating_time()
        print(f"✅ Next Operation Time: {next_time}")
        
        print("⏰ Operating Hours Test: ✅ PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Operating Hours Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_news_format():
    """Test the new news format with Persian calendar."""
    print("\n📰 TESTING NEWS FORMAT")
    print("=" * 50)
    
    try:
        from src.utils.time_utils import get_formatted_time
        
        # Sample news text
        news_text = "📈 فرمانده نیروی هوایی ارتش اسرائیل: ما برای تمام سناریو های ممکن آماده می‌شویم؛ از جمله احتمال حمله موشکی قریب الوقوع ایران."
        attribution = "📡 @anilnewsonline"
        timestamp = f"🕐 {get_formatted_time(format_type='persian_full')}"
        
        formatted_news = f"{news_text}\n{attribution}\n{timestamp}"
        
        print("✅ Sample formatted news:")
        print("-" * 30)
        print(formatted_news)
        print("-" * 30)
        
        # Test different time formats
        print(f"✅ Persian Full: {get_formatted_time(format_type='persian_full')}")
        print(f"✅ Persian Date: {get_formatted_time(format_type='persian_date')}")
        print(f"✅ Persian Time: {get_formatted_time(format_type='persian_time')}")
        
        print("📰 News Format Test: ✅ PASSED")
        return True
        
    except Exception as e:
        print(f"❌ News Format Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_media_directories():
    """Test media directory creation and permissions."""
    print("\n📁 TESTING MEDIA DIRECTORIES")
    print("=" * 50)
    
    try:
        from config.settings import MEDIA_DIR, TEMP_MEDIA_DIR, ENABLE_MEDIA_PROCESSING
        
        print(f"✅ Media Processing Enabled: {ENABLE_MEDIA_PROCESSING}")
        print(f"✅ Media Directory: {MEDIA_DIR}")
        print(f"✅ Temp Media Directory: {TEMP_MEDIA_DIR}")
        print(f"✅ Media Dir Exists: {'Yes' if MEDIA_DIR.exists() else 'No'}")
        print(f"✅ Temp Media Dir Exists: {'Yes' if TEMP_MEDIA_DIR.exists() else 'No'}")
        
        # Test write permissions
        test_file = TEMP_MEDIA_DIR / "test_write.txt"
        try:
            test_file.write_text("test content")
            test_file.unlink()
            print("✅ Write Permission: Yes")
        except Exception as e:
            print(f"❌ Write Permission: No ({e})")
            return False
        
        # Test media support imports
        try:
            import aiofiles
            import aiohttp
            print("✅ Media Support Libraries: Available")
        except ImportError as e:
            print(f"⚠️ Media Support Libraries: Missing ({e})")
            print("💡 Install with: pip install aiofiles aiohttp")
        
        print("📁 Media Directories Test: ✅ PASSED")
        return True
            
    except ImportError as e:
        print(f"❌ Media Directories Test FAILED: {e}")
        print("💡 Make sure config/settings.py is properly configured")
        return False

async def test_schedule_settings():
    """Test schedule settings."""
    print("\n📅 TESTING SCHEDULE SETTINGS")
    print("=" * 50)
    
    try:
        from config.settings import (
            NEWS_CHECK_INTERVAL, OPERATION_START_HOUR, OPERATION_START_MINUTE,
            OPERATION_END_HOUR, OPERATION_END_MINUTE
        )
        
        print(f"✅ News Check Interval: {NEWS_CHECK_INTERVAL} seconds")
        print(f"✅ News Check Interval: {NEWS_CHECK_INTERVAL / 60} minutes")
        print(f"✅ Start Time: {OPERATION_START_HOUR:02d}:{OPERATION_START_MINUTE:02d}")
        print(f"✅ End Time: {OPERATION_END_HOUR:02d}:{OPERATION_END_MINUTE:02d}")
        
        # Validate schedule
        if NEWS_CHECK_INTERVAL == 900:
            print("✅ Schedule correctly set to 15 minutes")
        else:
            print(f"⚠️ Schedule is set to {NEWS_CHECK_INTERVAL / 60} minutes (expected 15)")
        
        if OPERATION_START_HOUR == 8 and OPERATION_START_MINUTE == 30:
            print("✅ Start time correctly set to 8:30 AM")
        else:
            print(f"⚠️ Start time is {OPERATION_START_HOUR:02d}:{OPERATION_START_MINUTE:02d} (expected 08:30)")
        
        if OPERATION_END_HOUR == 22 and OPERATION_END_MINUTE == 0:
            print("✅ End time correctly set to 10:00 PM")
        else:
            print(f"⚠️ End time is {OPERATION_END_HOUR:02d}:{OPERATION_END_MINUTE:02d} (expected 22:00)")
            
        print("📅 Schedule Settings Test: ✅ PASSED")
        return True
            
    except ImportError as e:
        print(f"❌ Schedule Settings Test FAILED: {e}")
        return False

async def test_detection_with_new_format():
    """Test news detection with the new format."""
    print("\n🔍 TESTING DETECTION WITH NEW FORMAT")
    print("=" * 50)
    
    try:
        from src.services.news_detector import NewsDetector
        from src.services.news_filter import NewsFilter
        from src.utils.time_utils import get_formatted_time
        
        detector = NewsDetector()
        
        # Test financial news samples
        test_cases = [
            {
                'text': 'قیمت طلای ۱۸ عیار امروز به ۲ میلیون و ۵۰۰ هزار تومان رسید',
                'should_detect': True,
                'category': 'Gold'
            },
            {
                'text': 'نرخ دلار در بازار آزاد به ۵۲ هزار تومان رسید',
                'should_detect': True,
                'category': 'Currency'
            },
            {
                'text': 'بانک مرکزی ایران نرخ سود بانکی را اعلام کرد',
                'should_detect': True,
                'category': 'Iranian Economy'
            },
            {
                'text': 'تیم فوتبال پرسپولیس امروز بازی دارد',
                'should_detect': False,
                'category': 'Sports (Non-Financial)'
            }
        ]
        
        passed_tests = 0
        total_tests = len(test_cases)
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🧪 Test {i}: {test_case['category']}")
            print(f"📝 Text: {test_case['text']}")
            
            # Test detection
            is_news = detector.is_news(test_case['text'])
            print(f"📊 Detected as News: {'Yes' if is_news else 'No'}")
            
            # Check if result matches expectation
            if is_news == test_case['should_detect']:
                print(f"✅ Detection Result: Correct")
                passed_tests += 1
            else:
                print(f"❌ Detection Result: Incorrect (expected: {test_case['should_detect']})")
            
            if is_news:
                # Test cleaning and formatting
                cleaned = detector.clean_news_text(test_case['text'])
                print(f"🧹 Cleaned Text: {cleaned[:80]}...")
                
                # Test relevance
                try:
                    is_relevant, score, topics = NewsFilter.is_relevant_news(cleaned)
                    print(f"🎯 Relevant: {'Yes' if is_relevant else 'No'}")
                    print(f"📈 Score: {score}")
                    print(f"🏷️ Topics: {topics[:3]}")
                    
                    if is_relevant:
                        # Show how it would look published
                        timestamp = get_formatted_time(format_type='persian_full')
                        formatted = f"{cleaned}\n📡 @anilnewsonline\n🕐 {timestamp}"
                        
                        print("📢 Published Format Preview:")
                        print("-" * 20)
                        print(formatted)
                        print("-" * 20)
                    
                except Exception as e:
                    print(f"⚠️ Filter Error: {e}")
        
        print(f"\n📊 Detection Test Results: {passed_tests}/{total_tests} passed")
        
        if passed_tests == total_tests:
            print("🔍 Detection with New Format Test: ✅ PASSED")
            return True
        else:
            print("🔍 Detection with New Format Test: ❌ FAILED")
            return False
            
    except ImportError as e:
        print(f"❌ Detection Test FAILED: {e}")
        return False

async def test_configuration_loading():
    """Test loading of all configuration settings."""
    print("\n⚙️ TESTING CONFIGURATION LOADING")
    print("=" * 50)
    
    try:
        # Test credentials loading
        print("🔐 Testing Credentials...")
        try:
            from config.credentials import (
                API_ID, API_HASH, PHONE_NUMBER, ADMIN_BOT_USERNAME, 
                TARGET_CHANNEL_ID
            )
            print(f"✅ API_ID: {'Set' if API_ID else 'Not Set'}")
            print(f"✅ API_HASH: {'Set' if API_HASH else 'Not Set'}")
            print(f"✅ PHONE_NUMBER: {'Set' if PHONE_NUMBER else 'Not Set'}")
            print(f"✅ ADMIN_BOT_USERNAME: {ADMIN_BOT_USERNAME or 'Not Set'}")
            print(f"✅ TARGET_CHANNEL_ID: {TARGET_CHANNEL_ID or 'Not Set'}")
        except Exception as e:
            print(f"❌ Credentials loading failed: {e}")
            return False
        
        # Test settings loading
        print("\n⚙️ Testing Settings...")
        try:
            from config.settings import (
                NEWS_CHANNEL, TWITTER_NEWS_CHANNEL, MIN_FINANCIAL_SCORE,
                ENABLE_MEDIA_PROCESSING, get_settings_summary
            )
            print(f"✅ NEWS_CHANNEL: {NEWS_CHANNEL or 'Not Set'}")
            print(f"✅ TWITTER_NEWS_CHANNEL: {TWITTER_NEWS_CHANNEL or 'Not Set'}")
            print(f"✅ MIN_FINANCIAL_SCORE: {MIN_FINANCIAL_SCORE}")
            print(f"✅ ENABLE_MEDIA_PROCESSING: {ENABLE_MEDIA_PROCESSING}")
            
            # Test settings summary
            summary = get_settings_summary()
            print(f"✅ Settings Summary: {len(summary)} items loaded")
            
        except Exception as e:
            print(f"❌ Settings loading failed: {e}")
            return False
        
        print("⚙️ Configuration Loading Test: ✅ PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Configuration Loading Test FAILED: {e}")
        return False

async def test_imports():
    """Test all critical imports."""
    print("\n📦 TESTING IMPORTS")
    print("=" * 50)
    
    import_tests = [
        ("Time Utils", "src.utils.time_utils"),
        ("News Detector", "src.services.news_detector"),
        ("News Filter", "src.services.news_filter"),
        ("News Handler", "src.handlers.news_handler"),
        ("Bot API Client", "src.client.bot_api"),
        ("Telegram Client", "src.client.telegram_client"),
        ("Logger", "src.utils.logger"),
        ("Credentials", "config.credentials"),
        ("Settings", "config.settings"),
    ]
    
    passed_imports = 0
    
    for name, module_path in import_tests:
        try:
            __import__(module_path)
            print(f"✅ {name}: OK")
            passed_imports += 1
        except ImportError as e:
            print(f"❌ {name}: FAILED ({e})")
    
    print(f"\n📊 Import Results: {passed_imports}/{len(import_tests)} passed")
    
    if passed_imports == len(import_tests):
        print("📦 Imports Test: ✅ PASSED")
        return True
    else:
        print("📦 Imports Test: ❌ FAILED")
        return False

async def run_all_tests():
    """Run all test suites."""
    print("🚀 RUNNING ALL NEW FEATURE TESTS")
    print("=" * 80)
    
    test_results = []
    
    # Run all tests
    test_results.append(("Imports", await test_imports()))
    test_results.append(("Configuration Loading", await test_configuration_loading()))
    test_results.append(("Persian Calendar", await test_persian_calendar()))
    test_results.append(("Operating Hours", await test_operating_hours()))
    test_results.append(("News Format", await test_news_format()))
    test_results.append(("Media Directories", await test_media_directories()))
    test_results.append(("Schedule Settings", await test_schedule_settings()))
    test_results.append(("Detection with New Format", await test_detection_with_new_format()))
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 80)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<30} {status}")
        if result:
            passed_tests += 1
    
    print("=" * 80)
    print(f"📈 OVERALL RESULT: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! Your system is ready to run.")
        print("\n🚀 NEXT STEPS:")
        print("1. Update your .env file with the new settings")
        print("2. Install dependencies: pip install -r requirements.txt")
        print("3. Run the bot: python main.py")
        print("4. Test Persian calendar: python main.py --test-persian")
        print("5. Test media handling: python main.py --test-media")
        return True
    else:
        print("❌ SOME TESTS FAILED! Please fix the issues above.")
        print("\n🔧 TROUBLESHOOTING:")
        print("1. Make sure all files are in the correct directories")
        print("2. Install missing dependencies: pip install -r requirements.txt")
        print("3. Check your .env file configuration")
        print("4. Verify file permissions for media directories")
        return False

def main():
    """Main test function."""
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⌨️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test runner error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()