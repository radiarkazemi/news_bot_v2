# scripts/debug_news.py
"""
Debug script for testing news detection functionality.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.news_detector import NewsDetector
from src.services.news_filter import NewsFilter


def test_news_detection(text):
    """Test news detection on sample text."""
    print("=" * 80)
    print("NEWS DETECTION TEST")
    print("=" * 80)
    
    detector = NewsDetector()
    
    print(f"Text length: {len(text)} characters")
    print(f"Sample: {text[:200]}...")
    print("-" * 40)
    
    # Test detection
    is_news = detector.is_news(text)
    print(f"Detected as news: {is_news}")
    
    if is_news:
        # Test cleaning
        cleaned = detector.clean_news_text(text)
        print(f"Cleaned text: {cleaned[:300]}...")
        
        # Test filtering
        is_relevant, score, topics = NewsFilter.is_relevant_news(cleaned)
        print(f"Relevant for war/geopolitical: {is_relevant}")
        print(f"Relevance score: {score}")
        print(f"Matching topics: {topics[:5]}")
        
        if is_relevant:
            print("✅ This news would be sent for approval")
        else:
            print("❌ This news would be filtered out")
    else:
        print("❌ Not detected as news content")


# Sample news texts for testing
SAMPLE_TEXTS = [
    # War news (should pass)
    """
    فوری: حمله موشکی اسرائیل به مواضع ایران در سوریه
    بر اساس گزارش منابع محلی، جنگنده‌های اسرائیلی چندین موشک به پایگاه‌های نظامی ایران در حومه دمشق شلیک کردند.
    """,
    
    # Economic war news (should pass)
    """
    تحریم‌های جدید آمریکا علیه ایران اعلام شد
    وزارت خزانه‌داری آمریکا فهرست جدیدی از تحریم‌ها علیه بخش نفت و گاز ایران اعلام کرد که قیمت نفت را تحت تأثیر قرار خواهد داد.
    """,
    
    # Non-news content (should be filtered)
    """
    رستوران جدید در شهر باز شد
    بهترین غذاهای محلی را در رستوران ما تجربه کنید. تخفیف ویژه برای مشتریان جدید.
    """,
    
    # Sports news (should be filtered)
    """
    تیم ملی فوتبال ایران برنده شد
    در بازی دیشب، تیم ملی فوتبال ایران موفق به پیروزی 2-1 مقابل حریف خود شد.
    """
]


async def main():
    """Main testing function."""
    if len(sys.argv) > 1:
        # Test custom text
        test_text = " ".join(sys.argv[1:])
        test_news_detection(test_text)
    else:
        # Test sample texts
        for i, text in enumerate(SAMPLE_TEXTS, 1):
            print(f"\n\nTEST {i}:")
            test_news_detection(text.strip())
            
    print("\n" + "=" * 80)
    print("Testing complete!")


if __name__ == "__main__":
    asyncio.run(main())