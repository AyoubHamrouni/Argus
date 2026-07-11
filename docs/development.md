# Development

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for the full contribution guide.

Quick summary:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make changes with tests
4. Run `make test` and `make lint`
5. Submit a pull request

## Development Setup

```bash
# Clone and set up
git clone https://github.com/AyoubHamrouni/Argus.git
cd Argus
python -m venv .venv
source .venv/bin/activate
pip install -r tests/requirements.txt
pip install -r requirements-alembic.txt
pip install -r requirements-redis.txt
pip install -r requirements-observability.txt

# Run pre-commit hooks
pre-commit install

# Run tests
make test

# Run linter
make lint
```

## Make Targets

| Target | Description |
|--------|-------------|
| `make test` | Run full test suite |
| `make test-unit` | Run unit tests only |
| `make test-integration` | Run integration tests |
| `make lint` | Run linter and type checker |
| `make format` | Auto-format code |
| `make build` | Build all Docker images |
| `make up` | Start all services |
| `make down` | Stop all services |
| `make logs` | Tail service logs |
| `make migrate` | Run database migrations |
| `make migrate-rollback` | Rollback last migration |
| `make health` | Check all service health endpoints |

## Project Structure

```
.
├── services/               FastAPI microservices
│   ├── alert-triage/       LLM alert analysis
│   ├── rag-service/        Threat intelligence retrieval
│   ├── feedback-service/   Analyst feedback storage
│   ├── correlation-engine/ Incident grouping & simulation
│   ├── response-orchestrator/ Defense planning
│   ├── wazuh-integration/  SIEM webhook receiver
│   ├── rule-generator/     Sigma rule generation
│   ├── retraining/         Model retraining pipeline
│   └── common/             Shared auth, caching, tracing, utilities
├── ml_training/            CICIDS2017 training & inference API
├── models/                 Trained model artifacts (.pkl)
├── datasets/               Dataset notes and validation
├── config/                 Wazuh, Grafana, Prometheus configs
├── docker-compose/         Compose stacks for all layers
├── k8s/ai-services/        Kubernetes manifests (AI services only)
├── terraform/              Multi-cloud infrastructure (AWS/Azure/GCP)
├── alembic/                Database migration scripts
├── tests/                  Unit, integration, security, e2e tests
└── docs/                   Documentation
```

## Code Style

- Python 3.10+ with type hints
- Black for formatting
- isort for import sorting
- Ruff for linting
- Pydantic for data validation
- Async/await for I/O-bound operations

## Testing

```bash
# All tests
pytest tests/

# Unit tests only
pytest tests/unit/

# Integration tests (requires running services)
TEST_DATABASE_URL=postgresql://... pytest tests/integration/

# With coverage
pytest tests/ --cov=services --cov-report=html
```

## Roadmap

- Align all tests and CI around the 77-feature model contract
- Replace stubbed response adapters with real integrations (pfSense, CrowdStrike, Microsoft Defender)
- Add multi-class IDS classification (15 attack types)
- Add adversarial robustness evaluation
- Add graph-based incident correlation
- Auto-populate simulation environments from Wazuh inventory
- Validate simulator against controlled adversary-emulation exercises
- Add stronger feedback-label validation before retraining
