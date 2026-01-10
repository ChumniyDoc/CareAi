.PHONY: test lint test-integration admin-selftest smoke

test:
	pytest --cov=src --cov-report=term-missing

lint:
	ruff check src tests
	ruff format --check src tests

test-integration:
	pytest tests/integration

admin-selftest:
	curl -X POST -u $${ADMIN_USER:-admin}:$${ADMIN_PASSWORD:-admin} http://localhost:8080/admin/selftest

smoke:
	bash scripts/smoke.sh
