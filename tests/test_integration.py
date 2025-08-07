# tests/test_integration.py
"""
Integration tests for the News Detector system.
"""
import unittest
import asyncio
import tempfile
import shutil
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.state_manager import StateManager
from src.utils.time_utils import get_current_time, is_operating_hours


class TestStateManager(unittest.TestCase):
    """Test cases for state management."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.state_file = Path(self.temp_dir) / "test_state.json"
        
        # Create a state manager with custom path
        self.state_manager = StateManager()
        self.state_manager.state_file = self.state_file

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_save_and_load_state(self):
        """Test saving and loading state data."""
        test_data = {
            'pending_news': {'12345': {'text': 'test news', 'timestamp': 1234567890}},
            'last_check': 1234567890
        }
        
        self.state_manager.save_state(test_data)
        loaded_data = self.state_manager.load_state()
        
        self.assertEqual(loaded_data, test_data)

    def test_get_set_state_value(self):
        """Test getting and setting individual state values."""
        self.state_manager.set_state_value('test_key', 'test_value')
        value = self.state_manager.get_state_value('test_key')
        
        self.assertEqual(value, 'test_value')

    def test_get_nonexistent_key_with_default(self):
        """Test getting non-existent key returns default."""
        value = self.state_manager.get_state_value('nonexistent', 'default')
        self.assertEqual(value, 'default')


class TestTimeUtils(unittest.TestCase):
    """Test cases for time utilities."""

    def test_get_current_time(self):
        """Test getting current time in Tehran timezone."""
        current_time = get_current_time()
        self.assertIsNotNone(current_time)
        self.assertEqual(current_time.tzinfo.zone, 'Asia/Tehran')

    def test_operating_hours_check(self):
        """Test operating hours validation."""
        # This test depends on current time, so we just check it doesn't crash
        result = is_operating_hours()
        self.assertIsInstance(result, bool)


class TestAsyncIntegration(unittest.IsolatedAsyncioTestCase):
    """Async integration tests."""

    async def test_news_handler_initialization(self):
        """Test news handler can be initialized without errors."""
        from src.handlers.news_handler import NewsHandler
        
        # Mock client manager
        class MockClientManager:
            def __init__(self):
                self.client = None
        
        handler = NewsHandler(MockClientManager())
        self.assertIsNotNone(handler)
        self.assertIsNotNone(handler.news_detector)
        self.assertIsNotNone(handler.state_manager)

    async def test_news_detection_pipeline(self):
        """Test the complete news detection pipeline."""
        from src.services.news_detector import NewsDetector
        from src.services.news_filter import NewsFilter
        
        detector = NewsDetector()
        
        test_news = """
        فوری: حمله موشکی اسرائیل به مواضع ایران
        بر اساس گزارش منابع امنیتی، جنگنده‌های اسرائیلی موشک‌هایی به پایگاه‌های نظامی ایران در سوریه شلیک کردند.
        """
        
        # Step 1: Detection
        is_news = detector.is_news(test_news)
        self.assertTrue(is_news)
        
        # Step 2: Cleaning
        cleaned_text = detector.clean_news_text(test_news)
        self.assertIsNotNone(cleaned_text)
        self.assertTrue(len(cleaned_text) > 0)
        
        # Step 3: Filtering
        is_relevant, score, topics = NewsFilter.is_relevant_news(cleaned_text)
        self.assertTrue(is_relevant)
        self.assertGreater(score, 0)
        self.assertTrue(len(topics) > 0)


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)