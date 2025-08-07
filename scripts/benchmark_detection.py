
# scripts/benchmark_detection.py
"""
Benchmark script for news detection performance.
"""
import time
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.news_detector import NewsDetector
from src.services.news_filter import NewsFilter


# Sample news texts for benchmarking
BENCHMARK_TEXTS = [
    """فوری: حمله موشکی اسرائیل به مواضع ایران در سوریه - بر اساس گزارش منابع محلی، جنگنده‌های اسرائیلی چندین موشک به پایگاه‌های نظامی ایران در حومه دمشق شلیک کردند. این حمله در پی تنش‌های اخیر بین دو کشور صورت گرفته است.""",
    
    """تحریم‌های جدید آمریکا علیه ایران اعلام شد - وزارت خزانه‌داری آمریکا فهرست جدیدی از تحریم‌ها علیه بخش نفت و گاز ایران اعلام کرد که قیمت نفت در بازارهای جهانی را تحت تأثیر قرار خواهد داد.""",
    
    """قیمت طلا با تنش‌های ژئوپلیتیک افزایش یافت - اونس طلا در بازارهای جهانی با افزایش تنش‌ها در خاورمیانه و احتمال درگیری نظامی بین اسرائیل و ایران به ۲۱۰۰ دلار رسید.""",
    
    """نتانیاهو: آماده حمله به تاسیسات هسته‌ای ایران هستیم - نخست وزیر اسرائیل در کنفرانس خبری گفت که اسرائیل تمام گزینه‌ها را برای جلوگیری از دستیابی ایران به سلاح هسته‌ای روی میز دارد.""",
    
    """بازار ارز با اخبار جنگ دچار نوسان شد - دلار در بازار تهران پس از انتشار اخبار احتمال درگیری نظامی در منطقه با جهش ۲۰۰ تومانی روبرو شد و به ۶۸ هزار تومان رسید.""",
]


def benchmark_detection_speed():
    """Benchmark news detection speed."""
    print("⚡ Benchmarking News Detection Speed")
    print("-" * 40)
    
    detector = NewsDetector()
    
    # Warm up
    for text in BENCHMARK_TEXTS[:2]:
        detector.is_news(text)
    
    # Benchmark detection
    start_time = time.time()
    iterations = 1000
    
    for i in range(iterations):
        for text in BENCHMARK_TEXTS:
            detector.is_news(text)
    
    end_time = time.time()
    total_time = end_time - start_time
    avg_time_per_detection = (total_time / (iterations * len(BENCHMARK_TEXTS))) * 1000
    
    print(f"Total detections: {iterations * len(BENCHMARK_TEXTS)}")
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Average per detection: {avg_time_per_detection:.2f} ms")
    print(f"Detections per second: {(iterations * len(BENCHMARK_TEXTS)) / total_time:.0f}")


def benchmark_filtering_speed():
    """Benchmark news filtering speed."""
    print("\n⚡ Benchmarking News Filtering Speed")
    print("-" * 40)
    
    # Warm up
    for text in BENCHMARK_TEXTS[:2]:
        NewsFilter.is_relevant_news(text)
    
    # Benchmark filtering
    start_time = time.time()
    iterations = 1000
    
    for i in range(iterations):
        for text in BENCHMARK_TEXTS:
            NewsFilter.is_relevant_news(text)
    
    end_time = time.time()
    total_time = end_time - start_time
    avg_time_per_filter = (total_time / (iterations * len(BENCHMARK_TEXTS))) * 1000
    
    print(f"Total filterings: {iterations * len(BENCHMARK_TEXTS)}")
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Average per filtering: {avg_time_per_filter:.2f} ms")
    print(f"Filterings per second: {(iterations * len(BENCHMARK_TEXTS)) / total_time:.0f}")


def benchmark_text_cleaning():
    """Benchmark text cleaning speed."""
    print("\n⚡ Benchmarking Text Cleaning Speed")
    print("-" * 40)
    
    detector = NewsDetector()
    
    # Warm up
    for text in BENCHMARK_TEXTS[:2]:
        detector.clean_news_text(text)
    
    # Benchmark cleaning
    start_time = time.time()
    iterations = 1000
    
    for i in range(iterations):
        for text in BENCHMARK_TEXTS:
            detector.clean_news_text(text)
    
    end_time = time.time()
    total_time = end_time - start_time
    avg_time_per_clean = (total_time / (iterations * len(BENCHMARK_TEXTS))) * 1000
    
    print(f"Total cleanings: {iterations * len(BENCHMARK_TEXTS)}")
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Average per cleaning: {avg_time_per_clean:.2f} ms")
    print(f"Cleanings per second: {(iterations * len(BENCHMARK_TEXTS)) / total_time:.0f}")


def test_accuracy():
    """Test detection and filtering accuracy."""
    print("\n🎯 Testing Detection Accuracy")
    print("-" * 40)
    
    detector = NewsDetector()
    
    # All benchmark texts should be detected as news
    correct_detections = 0
    for text in BENCHMARK_TEXTS:
        if detector.is_news(text):
            correct_detections += 1
    
    detection_accuracy = (correct_detections / len(BENCHMARK_TEXTS)) * 100
    print(f"News detection accuracy: {detection_accuracy:.1f}% ({correct_detections}/{len(BENCHMARK_TEXTS)})")
    
    # All benchmark texts should be relevant
    relevant_detections = 0
    for text in BENCHMARK_TEXTS:
        is_relevant, score, topics = NewsFilter.is_relevant_news(text)
        if is_relevant:
            relevant_detections += 1
    
    relevance_accuracy = (relevant_detections / len(BENCHMARK_TEXTS)) * 100
    print(f"Relevance filtering accuracy: {relevance_accuracy:.1f}% ({relevant_detections}/{len(BENCHMARK_TEXTS)})")


def main():
    """Main benchmark function."""
    print("🏁 News Detector Performance Benchmark")
    print("=" * 50)
    
    benchmark_detection_speed()
    benchmark_filtering_speed()
    benchmark_text_cleaning()
    test_accuracy()
    
    print("\n✅ Benchmark complete!")


if __name__ == "__main__":
    main()