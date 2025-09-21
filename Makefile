.PHONY: help install install-dev test lint format clean build docs
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install package in development mode
	uv pip install -e .

install-dev: ## Install package with development dependencies (uv)
	uv sync
	uv pip install -e ".[dev]"

test: ## Run tests with pytest
	uv run pytest

test-cov: ## Run tests with coverage
	uv run pytest --cov=src/gangimg --cov-report=term-missing --cov-report=html

lint: ## Run linting checks
	uv run flake8 src tests
	uv run mypy src

format: ## Format code with black and isort
	uv run black src tests
	uv run isort src tests

format-check: ## Check code formatting
	uv run black --check src tests
	uv run isort --check-only src tests

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

sample: ## create sample gang image
	@[ -d samples ] || mkdir samples
	uv run python scripts/create_simple_sample.py

example: ## Run example analysis
	uv run python -m gangimg.cli samples/simple_test.bin
	uv run python -m gangimg.cli samples/simple_gang.bin

example-help: ## Show CLI help
	uv run python -m gangimg.cli --help

install-hooks: ## Install pre-commit hooks
	uv run pre-commit install

# Development workflow
dev-setup: install-dev install-hooks ## Set up development environment
	@echo "Development environment ready!"

check-all: format-check lint test ## Run all checks (format, lint, test)
