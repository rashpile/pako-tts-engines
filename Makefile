.PHONY: install dev test lint format typecheck run clean check

# Install dependencies
install:
	uv sync

# Install with dev dependencies
dev:
	uv sync --all-extras

# Run tests
test:
	uv run pytest

# Run tests with coverage
test-coverage:
	uv run pytest --cov=src --cov-report=html

# Run linter
lint:
	uv run ruff check src tests

# Format code
format:
	uv run ruff format src tests
	uv run ruff check --fix src tests

# Type checking
typecheck:
	uv run mypy src

# Run the application
run:
	uv run pako-tts-engines

# Clean build artifacts
clean:
	rm -rf .venv __pycache__ .pytest_cache .mypy_cache .ruff_cache
	rm -rf dist build *.egg-info
	rm -rf htmlcov .coverage coverage.xml
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# All checks before commit
check: format lint typecheck test

# Build package
build:
	uv build

# Docker build
docker-build:
	docker build -t pako-tts-engines:latest .

# Docker run
docker-run:
	docker run -p 8000:8000 pako-tts-engines:latest
