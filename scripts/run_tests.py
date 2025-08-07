# scripts/run_tests.py
"""
Test runner script for the News Detector.
"""
import unittest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def run_all_tests():
    """Run all test suites."""
    print("🧪 Running News Detector Test Suite")
    print("=" * 50)
    
    # Discover and run all tests
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent.parent / 'tests'
    suite = loader.discover(str(start_dir), pattern='test_*.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        return 1


def run_specific_test(test_name):
    """Run a specific test module."""
    try:
        module = __import__(f'tests.{test_name}', fromlist=[''])
        loader = unittest.TestLoader()
        suite = loader.loadTestsFromModule(module)
        
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return 0 if result.wasSuccessful() else 1
    except ImportError:
        print(f"❌ Test module '{test_name}' not found")
        return 1


def main():
    """Main test runner function."""
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        return run_specific_test(test_name)
    else:
        return run_all_tests()


if __name__ == "__main__":
    sys.exit(main())