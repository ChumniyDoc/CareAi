.PHONY: test lint

test:
	pytest --cov=src --cov-report=term-missing

lint:
	ruff check src tests
	ruff format --check src tests
