.PHONY: help install test run clean

help:
	@echo "Available commands:"
	@echo "  install  - Install dependencies"
	@echo "  test     - Run test suite"
	@echo "  run      - Start the news detector"
	@echo "  clean    - Clean temporary files"

install:
	pip install -r requirements.txt

test:
	python scripts/run_tests.py

run:
	python main.py

clean:
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +
