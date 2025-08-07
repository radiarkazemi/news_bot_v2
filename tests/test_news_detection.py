
# tests/test_news_detection.py
"""
Unit tests for news detection functionality.
"""
import unittest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.news_detector import NewsDetector
from src.services.news_filter import NewsFilter


class TestNewsDetection(unittest.TestCase):
    """Test cases for news detection."""

    def setUp(self):
        """Set up test fixtures."""
        self.detector = NewsDetector()

    def test_war_news_detection(self):
        """Test detection of war-related news."""
        war_news = """
        فوری: حمله موشکی اسرائیل به مواضع ایران در سوریه
        بر اساس گزارش منابع محلی، جنگنده‌های اسرائیلی چندین موشک به پایگاه‌های نظامی ایران شلیک کردند.
        """
        
        self.assertTrue(self.detector.is_news(war_news))
        cleaned = self.detector.clean_news_text(war_news)
        self.assertIsNotNone(cleaned)
        self.assertTrue(len(cleaned) > 0)

    def test_economic_war_news_detection(self):
        """Test detection of economic warfare news."""
        economic_news = """
        تحریم‌های جدید آمریکا علیه ایران اعلام شد
        وزارت خزانه‌داری آمریکا فهرست جدیدی از تحریم‌ها علیه بخش نفت و گاز ایران اعلام کرد.
        """
        
        self.assertTrue(self.detector.is_news(economic_news))

    def test_non_news_content(self):
        """Test rejection of non-news content."""
        non_news = """
        رستوران جدید در شهر باز شد
        بهترین غذاهای محلی را در رستوران ما تجربه کنید. تخفیف ویژه برای مشتریان جدید.
        """
        
        self.assertFalse(self.detector.is_news(non_news))

    def test_sports_content_rejection(self):
        """Test rejection of sports content."""
        sports_news = """
        تیم ملی فوتبال ایران برنده شد
        در بازی دیشب، تیم ملی فوتبال ایران موفق به پیروزی 2-1 مقابل حریف خود شد.
        """
        
        # Should be detected as news format but filtered out by relevance
        self.assertFalse(self.detector.is_news(sports_news))

    def test_short_content_rejection(self):
        """Test rejection of very short content."""
        short_text = "سلام"
        self.assertFalse(self.detector.is_news(short_text))

    def test_text_cleaning(self):
        """Test news text cleaning functionality."""
        dirty_text = """
        فوری: خبر مهم
        
        
        این یک خبر تست است @testchannel https://t.me/test
        
        
        🔥🔥🔥🔥🔥
        """
        
        cleaned = self.detector.clean_news_text(dirty_text)
        
        # Should remove excessive whitespace, handles, and emojis
        self.assertNotIn("@testchannel", cleaned)
        self.assertNotIn("https://t.me/test", cleaned)
        self.assertNotIn("🔥🔥🔥🔥🔥", cleaned)


class TestNewsFiltering(unittest.TestCase):
    """Test cases for news filtering."""

    def test_israel_iran_content(self):
        """Test Israel-Iran content prioritization."""
        israel_iran_news = """
        تنش بین اسرائیل و ایران بالا گرفت
        نتانیاهو درباره برنامه هسته‌ای ایران هشدار داد
        """
        
        is_relevant, score, topics = NewsFilter.is_relevant_news(israel_iran_news)
        
        self.assertTrue(is_relevant)
        self.assertGreater(score, 2)
        self.assertTrue(any('اسرائیل' in topic or 'ایران' in topic for topic in topics))

    def test_nuclear_content_high_priority(self):
        """Test nuclear content gets high priority."""
        nuclear_news = """
        ایران غنی‌سازی اورانیوم را افزایش داد
        آژانس اتمی گزارش جدیدی درباره برنامه هسته‌ای ایران منتشر کرد
        """
        
        is_relevant, score, topics = NewsFilter.is_relevant_news(nuclear_news)
        
        self.assertTrue(is_relevant)
        self.assertGreater(score, 3)

    def test_irrelevant_content_filtering(self):
        """Test filtering of irrelevant content."""
        irrelevant_news = """
        جشنواره فیلم کن امسال
        بازیگران مشهور در فرش قرمز حضور یافتند
        """
        
        is_relevant, score, topics = NewsFilter.is_relevant_news(irrelevant_news)
        
        self.assertFalse(is_relevant)

    def test_economic_warfare_content(self):
        """Test economic warfare content detection."""
        economic_warfare = """
        قیمت نفت پس از تحریم‌های جدید جهش کرد
        بازار طلا با تنش‌های ژئوپلیتیک صعودی شد
        """
        
        is_relevant, score, topics = NewsFilter.is_relevant_news(economic_warfare)
        
        self.assertTrue(is_relevant)
        self.assertGreater(score, 1)


class TestNewsSegmentation(unittest.TestCase):
    """Test cases for news segmentation."""

    def test_segment_splitting(self):
        """Test splitting of multi-news segments."""
        from src.handlers.news_handler import NewsHandler
        
        # Mock client manager for testing
        class MockClientManager:
            pass
        
        handler = NewsHandler(MockClientManager())
        
        multi_news = """
        خبر اول: حمله به پایگاه نظامی
        ---
        خبر دوم: تحریم‌های جدید اعلام شد
        ===
        خبر سوم: قیمت طلا افزایش یافت
        """
        
        segments = handler.split_news_segments(multi_news)
        
        self.assertEqual(len(segments), 3)
        self.assertIn("خبر اول", segments[0])
        self.assertIn("خبر دوم", segments[1])
        self.assertIn("خبر سوم", segments[2])

    def test_single_news_no_splitting(self):
        """Test that single news items aren't split unnecessarily."""
        from src.handlers.news_handler import NewsHandler
        
        class MockClientManager:
            pass
        
        handler = NewsHandler(MockClientManager())
        
        single_news = "این یک خبر ساده است بدون جداکننده"
        segments = handler.split_news_segments(single_news)
        
        self.assertEqual(len(segments), 1)
        self.assertEqual(segments[0], single_news)


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)