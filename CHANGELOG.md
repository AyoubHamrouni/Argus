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
- CI and Codecov badges in README

### Fixed
- Feature count mismatch (78 vs 77) across tests, docs, and source code
- Scaffolding language removed from services/README.md
- License reference corrected from MIT to Apache 2.0 in services/README.md
- Docker build matrix updated to reference actual existing services

### Changed
- CI pipeline no longer silently swallows failures via `|| true`
- `.gitignore` now excludes `.pkl` model files (security + repo size)

## [1.0.0] - 2025-01-13

### Added
- ML Inference API (Random Forest, XGBoost, Decision Tree) trained on CICIDS2017
- Alert Triage service with LLM-powered analysis via Ollama
- RAG Service with ChromaDB for MITRE ATT&CK, CVE, and runbook retrieval
- Wazuh Integration service for webhook-based alert ingestion
- Feedback Service for analyst feedback and ROI metrics
- Correlation Engine with incident grouping, kill-chain tracking, and swarm simulation
- Response Orchestrator with D3FEND mapping and graduated autonomy controls
- Rule Generator for LLM-generated Sigma detection rules
- Retraining Pipeline with champion/challenger model promotion
- Common library with shared utilities (auth, metrics, security, rate limiting)
- Flask dashboard for centralized service management
- Docker Compose deployment (SIEM core, AI services, monitoring, SOAR)
- One-command deploy scripts (bash and PowerShell)
- MkDocs documentation site with 55+ pages
- Prometheus + Grafana monitoring stack
- GitHub Actions CI/CD pipelines
- Pre-trained model artifacts (77 features)
- 8 security runbooks (SSH brute force, ransomware, phishing, etc.)
- OWASP Top 10 security test suite
- Load testing framework with Locust
