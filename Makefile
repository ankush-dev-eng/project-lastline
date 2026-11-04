.PHONY: help install lint format test benchmark safety clean

help:
	@echo "PROJECT LASTLINE - Build & Verification Targets"
	@echo "  make install    - Install Python backend dependencies in editable mode"
	@echo "  make lint       - Run Ruff linter"
	@echo "  make format     - Run Ruff code formatting"
	@echo "  make test       - Run pytest test suite"
	@echo "  make safety     - Run read-only architectural safety test"
	@echo "  make benchmark  - Run benchmark harness and regenerate BENCHMARKS.md"
	@echo "  make clean      - Clean temporary files and caches"

install:
	pip install -e ".[dev]"

lint:
	ruff check .

format:
	ruff format .

test:
	pytest -v

safety:
	pytest tests/test_safety_boundary.py -v

benchmark:
	python -m benchmarks.run_all

clean:
	rm -rf .pytest_cache .ruff_cache htmlcov .coverage

