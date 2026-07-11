# Configuration

## Environment Variables

All services are configured via environment variables. Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

### Core Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `development` | Deployment environment |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `DEPLOY_ENV` | `development` | Deployment environment for tracing |

### Database

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_HOST` | `postgres` | PostgreSQL hostname |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |
| `POSTGRES_DB` | `argus` | Database name |
| `POSTGRES_USER` | `aisoc_admin` | Database user |
| `POSTGRES_PASSWORD` | `argus_password` | Database password |

### Authentication

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_SECRET_KEY` | — | Secret key for JWT signing (required) |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `JWT_EXPIRY_HOURS` | `24` | Token expiration time |

### Per-Service API Keys

Each service has its own API key for inter-service authentication:

| Variable | Default | Service |
|----------|---------|---------|
| `TRIAGE_API_KEY` | `aisoc_change_me_in_production` | Alert Triage |
| `RAG_API_KEY` | `aisoc_change_me_in_production` | RAG Service |
| `FEEDBACK_API_KEY` | `aisoc_change_me_in_production` | Feedback Service |
| `ORCHESTRATOR_API_KEY` | `aisoc_change_me_in_production` | Response Orchestrator |
| `CORRELATION_API_KEY` | `aisoc_change_me_in_production` | Correlation Engine |
| `WAZUH_API_KEY` | `aisoc_change_me_in_production` | Wazuh Integration |
| `RULES_API_KEY` | `aisoc_change_me_in_production` | Rule Generator |

Auth is enabled by default. Set `*_API_KEY_ENABLED=false` only for local development.

### LLM Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_MODEL` | `llama3.2:3b` | Ollama model for local inference |
| `OLLAMA_BASE_URL` | `http://ollama:11434` | Ollama API endpoint |
| `LITELLM_MODEL` | `gpt-4o-mini` | LiteLLM model alias |
| `OPENAI_API_KEY` | — | OpenAI API key (if using cloud LLM) |

### Redis

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection URL |
| `REDIS_PASSWORD` | — | Redis password (if auth enabled) |
| `REDIS_MAX_MEMORY` | `256mb` | Redis memory limit |

### Observability

| Variable | Default | Description |
|----------|---------|-------------|
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://otel-collector:4317` | OTLP collector endpoint |
| `OTEL_CONSOLE_EXPORT` | `false` | Enable console trace export |
| `PROMETHEUS_PORT` | `9090` | Prometheus scrape port |

### Wazuh Integration

| Variable | Default | Description |
|----------|---------|-------------|
| `WAZUH_API_URL` | `http://wazuh:55000` | Wazuh API endpoint |
| `WAZUH_API_USER` | `admin` | Wazuh API username |
| `WAZUH_API_PASSWORD` | `admin` | Wazuh API password |

## Service Configuration

Each service also reads from its own `config.py` which maps environment variables to typed settings. Services using Pydantic `BaseSettings` automatically pick up `.env` values.

### Alert Triage

| Variable | Default | Description |
|----------|---------|-------------|
| `TRIAGE_PORT` | `8100` | Service port |
| `TRIAGE_LOG_LEVEL` | `INFO` | Service-specific log level |
| `MAX_CONCURRENT_REQUESTS` | `10` | Max concurrent LLM requests |
| `WORKER_COUNT` | `4` | Async worker pool size |

### ML Inference

| Variable | Default | Description |
|----------|---------|-------------|
| `ML_PORT` | `8500` | Service port |
| `MODEL_DIR` | `models/` | Directory containing .pkl artifacts |
| `DEFAULT_MODEL` | `random_forest` | Default model for predictions |

### Correlation Engine

| Variable | Default | Description |
|----------|---------|-------------|
| `CORRELATION_PORT` | `8600` | Service port |
| `SIMULATION_ENDPOINT` | — | External simulation API |
| `MAX_SIMULATION_AGENTS` | `500` | Max agents in swarm simulation |

## Docker Compose Overrides

Create a `docker-compose.override.yml` to customize the deployment without editing the base files:

```yaml
version: "3.8"
services:
  alert-triage:
    environment:
      - LOG_LEVEL=DEBUG
      - MAX_CONCURRENT_REQUESTS=20
    deploy:
      resources:
        limits:
          memory: 2G
```

## Configuration File Locations

| Path | Purpose |
|------|---------|
| `.env` | Environment variables (not committed) |
| `.env.example` | Template for `.env` |
| `config/wazuh/` | Wazuh manager configuration |
| `config/grafana/` | Grafana dashboards and datasources |
| `config/prometheus/` | Prometheus scrape targets |
| `otel-collector-config.yaml` | OpenTelemetry collector pipeline |
