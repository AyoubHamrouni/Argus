.PHONY: help install test lint format build docs clean docker-up docker-down docker-build

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install development dependencies
	pip install -r tests/requirements.txt
	pip install -r requirements-security.txt
	pre-commit install

test: ## Run all unit tests
	pytest tests/unit/ -v --tb=short --cov=services --cov-report=html

test-integration: ## Run integration tests (requires running services)
	pytest tests/integration/ -v --tb=short -m "not requires_ollama"

test-security: ## Run security tests
	pytest tests/security/ -v --tb=short -m security

test-all: test test-security ## Run all tests that don't require infrastructure

lint: ## Run all linters
	black --check services/ tests/
	isort --check-only services/ tests/
	pylint services/alert-triage/*.py services/common/*.py
	flake8 services/ --select=E9,F63,F7,F82
	bandit -r services/ -c pyproject.toml

format: ## Auto-format code
	black services/ tests/
	isort services/ tests/

typecheck: ## Run type checking
	mypy services/alert-triage/*.py services/common/*.py --ignore-missing-imports

build: ## Build all Docker images
	docker compose -f docker-compose/ai-services.yml build

docker-up: ## Start all AI services
	docker compose -f docker-compose/ai-services.yml up -d

docker-down: ## Stop all AI services
	docker compose -f docker-compose/ai-services.yml down

docker-logs: ## View logs for AI services
	docker compose -f docker-compose/ai-services.yml logs -f

monitoring-up: ## Start monitoring stack (Prometheus, Grafana, Loki)
	docker compose -f docker-compose/monitoring-stack.yml up -d

monitoring-down: ## Stop monitoring stack
	docker compose -f docker-compose/monitoring-stack.yml down

siem-up: ## Start SIEM core (Wazuh, Suricata, Zeek)
	docker compose -f docker-compose/phase1-siem-core.yml up -d

siem-down: ## Stop SIEM core
	docker compose -f docker-compose/phase1-siem-core.yml down

deploy: ## Full deployment (SIEM + AI + Monitoring)
	./deploy-ai-soc.sh

docs: ## Build documentation
	mkdocs build

docs-serve: ## Serve documentation locally
	mkdocs serve

migrate: ## Run database migrations to head
	alembic upgrade head

migrate-rollback: ## Rollback last migration
	alembic downgrade -1

migrate-status: ## Show migration status
	alembic history

migrate-generate: ## Generate a new migration (usage: make migrate-generate MSG="add new column")
	alembic revision --autogenerate -m "$(MSG)"

clean: ## Clean build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache/ htmlcov/ .coverage coverage.xml
	rm -rf build/ dist/ *.egg-info/
	rm -rf site/ docs/_build/

redis-cli: ## Connect to Redis CLI
	docker exec -it ai_soc-redis-1 redis-cli
