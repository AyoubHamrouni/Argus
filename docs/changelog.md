# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- CI pipeline with enforced quality gates (Black, isort, Pylint, MyPy, Bandit)
- Unit test coverage enforcement (minimum 50%)
- CONTRIBUTING.md with development guidelines
- CODE_OF_CONDUCT.md (Contributor Covenant v2.1)
- SECURITY.md with vulnerability disclosure policy
- CHANGELOG.md for tracking project changes
- .pre-commit-config.yaml for automated code quality checks
- Makefile with common development targets
- GitHub issue and pull request templates
- Dependabot configuration for automated dependency updates
- JWT + API key authentication across all services
- OAuth2-compatible token generation
- Role-based access control (admin / analyst / viewer)
- Scoped access per service
- API versioning with APIRouter (`/api/v1/{service}/`)
- Rate limiting middleware on all services
- Alembic database migrations
- Redis caching layer with graceful degradation
- OpenTelemetry distributed tracing
- Kubernetes manifests for AI services
- Terraform modules (AWS, Azure, GCP)
- Unified documentation site (MkDocs Material)

### Changed
- Enforced quality gates in CI (removed `|| true` patterns)
- Feature count corrected from 78 to 77 across codebase
- Services README rewritten to reflect actual implementation
- Auth defaults: `api_key_enabled=True` for all services in production
- Exception handling improved: 38 bare `except Exception:` blocks replaced with specific types
- Test quality: reduced `pytest.skip` calls from 48 to 9

### Fixed
- Duplicate lifespan startup lines in response-orchestrator
- Duplicate `detect_prompt_injection` function in alert-triage
- License mismatch (was MIT, corrected to Apache 2.0)
- Missing `models/*.pkl` in `.gitignore`

## [0.1.0] - 2025-10-13

### Added
- ML inference API (Random Forest, XGBoost, Decision Tree)
- Alert triage service with LLM analysis
- RAG service with ChromaDB
- Wazuh integration webhook
- Feedback service with PostgreSQL
- Correlation engine with incident grouping
- Swarm simulation framework
- Response orchestrator with D3FEND mapping
- Rule generator prototype
- Monitoring stack (Prometheus, Grafana, Alertmanager)
- Docker Compose deployment scripts
