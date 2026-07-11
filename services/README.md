# AI Services Layer

**AI-Augmented SOC - LLM-Powered Security Operations**

> Intelligent automation for alert triage, threat analysis, incident correlation, and autonomous response using state-of-the-art large language models and ML classifiers.

---

## Overview

This directory contains the core AI services that power the AI-Augmented SOC platform. Each service is containerized, independently scalable, and communicates via REST APIs.

**Architecture Principles:**
- **Microservices:** Each service has a single responsibility
- **API-First:** All services expose FastAPI REST endpoints
- **Observability:** Prometheus metrics, structured logging, OpenTelemetry instrumentation
- **Security:** Input validation, prompt injection protection, API key authentication
- **Resilience:** Automatic retries, fallback models, circuit breakers

---

## Services

### 1. Alert Triage Service (`alert-triage/`)

**Purpose:** LLM-powered security alert analysis and prioritization

**Technology Stack:** FastAPI, Ollama (llama3.2:3b), Pydantic (structured outputs), async worker pool

**API Endpoints:**
- `POST /analyze` - Analyze single alert
- `POST /batch` - Batch process alerts
- `POST /analyze/async` - Async analysis with job tracking
- `GET /jobs/{job_id}` - Check async job status
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics

**Key Features:**
- Severity classification (Critical/High/Medium/Low/Info)
- IOC extraction (IPs, domains, hashes)
- MITRE ATT&CK mapping
- True/false positive detection with confidence scoring
- PII redaction before LLM processing
- Prompt injection detection
- ML-aware prompt enrichment (calls ML Inference service)

---

### 2. RAG Service (`rag-service/`)

**Purpose:** Retrieval-Augmented Generation for grounding LLM responses in verified security knowledge

**Technology Stack:** FastAPI, ChromaDB (vector database), sentence-transformers (all-MiniLM-L6-v2)

**API Endpoints:**
- `POST /retrieve` - Semantic search over knowledge base
- `POST /ingest` - Add custom documents
- `POST /ingest/mitre` - Ingest MITRE ATT&CK data
- `POST /ingest/cve` - Ingest CVE data
- `POST /ingest/runbooks` - Ingest response playbooks
- `GET /collections` - List available collections
- `GET /health` - Health check

**Knowledge Base Collections:**
- **mitre_attack:** 3000+ MITRE ATT&CK techniques
- **cve_database:** Critical vulnerabilities (CVSS >= 9.0)
- **security_runbooks:** Response playbooks (SSH brute force, ransomware, phishing, etc.)

---

### 3. Wazuh Integration (`wazuh-integration/`)

**Purpose:** Webhook receiver for Wazuh alert ingestion and enrichment pipeline

**Technology Stack:** FastAPI, httpx (async HTTP), Wazuh Manager API client

**API Endpoints:**
- `POST /webhook` - Receive Wazuh alerts
- `GET /health` - Health check

**Pipeline:** Receive alert → AI triage → Conditional RAG enrichment → Forward to correlation engine

---

### 4. Feedback Service (`feedback-service/`)

**Purpose:** Alert persistence and analyst feedback collection for model retraining

**Technology Stack:** FastAPI, PostgreSQL (asyncpg + SQLAlchemy async), multi-tenant support

**API Endpoints:**
- `POST /alerts` - Store new alerts
- `POST /feedback/{alert_id}` - Submit analyst feedback
- `GET /feedback/stats` - Feedback statistics
- `GET /roi/metrics` - ROI metrics for business value tracking

---

### 5. Correlation Engine (`correlation-engine/`)

**Purpose:** Incident grouping, kill-chain tracking, attack simulation, and risk scoring

**Technology Stack:** FastAPI, Markov chain prediction, Monte Carlo swarm simulation

**API Endpoints:**
- `POST /correlate` - Correlate alerts into incidents
- `GET /incidents` - List incidents
- `POST /simulate` - Run attack campaign simulation
- `POST /simulate/swarm/*` - Swarm simulation experiments
- `GET /risk-scores` - Per-host risk scores
- `POST /predict/*` - Markov chain next-stage prediction

**Key Features:**
- Alert-to-incident correlation (IP affinity, temporal proximity, MITRE kill chain)
- 4 attacker archetypes (opportunist, APT, ransomware, insider)
- 3 defender archetypes (SOC analyst, incident responder, threat hunter)
- Monte Carlo leader/follower swarm simulation
- Per-host risk scoring from simulation results

---

### 6. Response Orchestrator (`response-orchestrator/`)

**Purpose:** Autonomous defense planning with graduated autonomy controls

**Technology Stack:** FastAPI, D3FEND countermeasure KB, PostgreSQL persistence

**API Endpoints:**
- `POST /defend` - Generate defense plan
- `GET /plans` - List defense plans
- `POST /plans/{id}/approve` - Approve plan execution
- `GET /d3fend/countermeasures` - D3FEND knowledge base

**Key Features:**
- D3FEND countermeasure mapping
- Safety checks and blast-radius assessment
- Approval tiers: Observe, Recommend, Auto-safe, Auto-veto, Human-required
- Post-execution verification via re-simulation
- Adapter stubs for firewall, EDR, identity, and Wazuh Active Response

---

### 7. Rule Generator (`rule-generator/`)

**Purpose:** LLM-generated Sigma detection rules with back-testing

**Technology Stack:** FastAPI, Ollama, in-memory rule store

**API Endpoints:**
- `POST /generate` - Generate Sigma rule from alert
- `POST /backtest` - Back-test rule against historical alerts
- `GET /rules` - List generated rules
- `POST /rules/{id}/approve` - Approve rule

---

### 8. Retraining Pipeline (`retraining/`)

**Purpose:** Feedback-driven model retraining with champion/challenger promotion

**Technology Stack:** CLI tool, scikit-learn, XGBoost, PostgreSQL

**Usage:**
```bash
python retrain.py                    # Retrain if enough feedback
python retrain.py --force            # Force retrain
python retrain.py --evaluate-only    # Evaluate without retraining
```

---

### 9. Common Library (`common/`)

**Purpose:** Shared utilities across all services

**Modules:**
- `ollama_client.py` - Reusable Ollama API client with fallback models
- `logging_config.py` - Structured JSON logging with Wazuh integration
- `metrics.py` - Prometheus metrics wrapper
- `security.py` - Input validation, prompt injection detection, security headers
- `auth.py` - JWT/API key authentication utilities
- `rate_limit.py` - Sliding window rate limiting
- `pipeline.py` - Data pipeline utilities
- `integration.py` - Event bus and integration helpers

---

## System Architecture

### Data Flow

```
Security Events (Wazuh/Suricata/Zeek)
  → Wazuh Integration (webhook, port 8002)
    → Alert Triage (LLM analysis, port 8100)
      ↔ RAG Service (knowledge retrieval, port 8300)
      → ML Inference (network flow classification, port 8500)
      → Feedback Service (persistence, port 8400)
    → Correlation Engine (incident grouping, port 8600)
      → Swarm Simulation (attack campaigns)
      → Risk Scoring (per-host risk)
      → Response Orchestrator (autonomous defense, port 8800)
        → Rule Generator (Sigma rules, port 8700)
        → Adapter Execution (firewall/EDR/identity stubs)
        → Verification (re-simulation)
```

---

## Deployment

### Docker Compose

**File:** `docker-compose/ai-services.yml`

```bash
# Build and start all AI services
docker compose -f docker-compose/ai-services.yml up -d

# Check health
curl http://localhost:8100/health   # Alert Triage
curl http://localhost:8300/health   # RAG Service
curl http://localhost:8400/health   # Feedback Service
curl http://localhost:8500/health   # ML Inference
curl http://localhost:8600/health   # Correlation Engine
curl http://localhost:8700/health   # Rule Generator
curl http://localhost:8800/health   # Response Orchestrator

# View logs
docker compose -f docker-compose/ai-services.yml logs -f alert-triage

# Stop all services
docker compose -f docker-compose/ai-services.yml down
```

### One-Command Deploy (Full Stack)

```bash
# Linux/macOS
./deploy-ai-soc.sh

# Windows
.\deploy-ai-soc.ps1
```

---

## Local Development

### Prerequisites

- Python 3.11+
- Docker and Docker Compose v2
- Ollama (with models pulled)

### Quick Start

```bash
# Clone repository
git clone https://github.com/zhadyz/AI_SOC.git
cd AI_SOC

# Run the deploy script (starts everything)
./deploy-ai-soc.sh

# Or manually start just the AI services
docker compose -f docker-compose/ai-services.yml up -d
```

---

## Testing

### Running Tests

```bash
# Run all unit tests
make test

# Or with pytest directly
pytest tests/unit/ -v --cov=services

# Run specific test categories
pytest tests/unit/ -v                    # Unit tests
pytest tests/integration/ -v             # Integration tests (requires running services)
pytest tests/security/ -v -m security    # Security tests
pytest tests/e2e/ -v                     # End-to-end tests

# Load testing with Locust
locust -f tests/load/locustfile.py --host http://localhost:8100
```

---

## Monitoring & Observability

### Prometheus Metrics

All services expose `/metrics` endpoints. See `docker-compose/monitoring-stack.yml` for the full monitoring stack (Prometheus, Grafana, Alertmanager, Loki, Promtail).

### Grafana Dashboards

Auto-provisioned dashboards are available in `config/grafana/`. Access Grafana at `http://localhost:3000` after starting the monitoring stack.

### Structured Logging

All services emit JSON-structured logs compatible with ELK/Loki aggregation via `structlog`.

---

## Security Considerations

### Input Validation

All services validate inputs using `common/security.py`:
- Max length checks (10,000 characters)
- SQL injection detection
- Command injection detection
- Null byte filtering

### Prompt Injection Protection

LLM inputs are screened for injection attempts:
- System prompt override attempts
- Role switching ("you are now...")
- Jailbreak patterns ("DAN mode")
- Output manipulation requests

### Secrets Management

Environment variables with `.env.example` as template. Use `scripts/generate_secure_credentials.py` to generate production credentials.

**Never commit:** API keys, passwords, Ollama API tokens, TheHive API keys, SSL private keys.

---

## Troubleshooting

### Ollama Connection Failed

```bash
docker ps | grep ollama
docker logs ollama
docker exec ollama ollama list
```

### ChromaDB Initialization Failed

```bash
docker ps | grep chroma
docker compose down -v
docker compose up -d chromadb
```

### High Latency / Timeout

- Check Ollama GPU usage: `nvidia-smi`
- Reduce `max_tokens` in service config
- Use a smaller model (llama3.2:3b instead of larger alternatives)
- Enable batch processing for bulk operations

---

## References

- **Ollama API:** https://github.com/ollama/ollama/blob/main/docs/api.md
- **ChromaDB:** https://docs.trychroma.com/
- **FastAPI:** https://fastapi.tiangolo.com/
- **MITRE ATT&CK:** https://attack.mitre.org/
- **D3FEND:** https://d3fend.mitre.org/
- **Sigma Rules:** https://sigmahq.io/

---

## License

**Apache 2.0 License** - See [LICENSE](../LICENSE) file

---

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for development setup and contribution guidelines.

**GitHub:** https://github.com/zhadyz/AI_SOC
