# Getting Started

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| RAM | 16 GB | 32 GB |
| Disk | 20 GB free | 50 GB free |
| CPU | 4 cores | 8 cores |
| OS | Linux (full SIEM), macOS/Windows (AI services only) | Linux |

**Required software:**

- Docker Engine 23+ with Compose v2
- Python 3.10+ (for local development only)
- Git

## Installation

### 1. Clone and configure

```bash
git clone https://github.com/zhadyz/AI_SOC.git
cd AI_SOC
cp .env.example .env
```

Edit `.env` and set at minimum:

```bash
# Change these from defaults before any non-local use
JWT_SECRET_KEY=<random-secret>
TRIAGE_API_KEY=<random-key>
RAG_API_KEY=<random-key>
OPENAI_API_KEY=<your-ollama-or-api-key>
```

### 2. Deploy with the script

Linux/macOS:

```bash
chmod +x deploy-ai-soc.sh
./deploy-ai-soc.sh
```

Windows PowerShell:

```powershell
.\deploy-ai-soc.ps1
```

The script runs three phases:

1. Starts Wazuh SIEM core
2. Builds and starts AI services
3. Starts the monitoring stack (Prometheus, Grafana, Alertmanager)

It also creates `.env` from `.env.example` if missing, pulls the configured Ollama model, and triggers RAG knowledge-base ingestion.

### 3. Verify

```bash
# Check all services are healthy
curl http://localhost:8100/health  # Alert Triage
curl http://localhost:8500/health  # ML Inference
curl http://localhost:8600/health  # Correlation Engine
```

Open Grafana at `http://localhost:3000` (default: `admin` / `admin`).

## Manual Deployment

```bash
# SIEM core
docker compose -f docker-compose/phase1-siem-core.yml up -d

# AI services
docker compose -f docker-compose/ai-services.yml up -d --build

# Monitoring
docker compose -f docker-compose/monitoring-stack.yml up -d
```

On Windows or macOS without native Wazuh support:

```bash
docker compose -f docker-compose/phase1-siem-core-windows.yml up -d
```

## Stopping the Stack

```bash
./deploy-ai-soc.sh --stop
```

Or manually:

```bash
docker compose -f docker-compose/monitoring-stack.yml down
docker compose -f docker-compose/ai-services.yml down
docker compose -f docker-compose/phase1-siem-core.yml down
```

## Local Development

```bash
# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r services/common/requirements.txt
pip install -r tests/requirements.txt

# Run a specific service locally
cd services/alert-triage
uvicorn main:app --reload --port 8001
```

Each service can run independently as long as its dependencies (PostgreSQL, Redis, Ollama) are available.

## Docker Compose Files

| File | Purpose |
|------|---------|
| `phase1-siem-core.yml` | Wazuh SIEM, indexer, dashboard |
| `phase1-siem-core-windows.yml` | Windows/macOS SIEM variant |
| `ai-services.yml` | All AI microservices + Redis + otel-collector |
| `monitoring-stack.yml` | Prometheus, Grafana, Alertmanager, Loki |
| `integrated-stack.yml` | Experimental — not the canonical deployment path |
