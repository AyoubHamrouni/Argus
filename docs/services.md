# Services

Each service is a self-contained FastAPI application with its own Dockerfile, configuration, and test suite.

## Service Overview

| Service | Port | Database | Purpose |
|---------|------|----------|---------|
| [Alert Triage](#alert-triage) | 8001 | — | LLM-powered alert analysis |
| [RAG Service](#rag-service) | 8002 | ChromaDB | Threat intelligence retrieval |
| [Feedback Service](#feedback-service) | 8003 | PostgreSQL | Analyst feedback & alert history |
| [Correlation Engine](#correlation-engine) | 8004 | PostgreSQL | Incident grouping & simulation |
| [Response Orchestrator](#response-orchestrator) | 8005 | PostgreSQL | Defense planning & execution |
| [ML Inference](#ml-inference) | 8500 | — | Network flow classification |
| [Wazuh Integration](#wazuh-integration) | 8007 | — | SIEM webhook receiver |
| [Rule Generator](#rule-generator) | 8008 | — | Sigma rule generation |
| Retraining | 8009 | — | Feedback-driven model retraining |

---

## Alert Triage

**Path:** `services/alert-triage/`

LLM-powered security alert analysis using Ollama (Foundation-Sec-8B or llama3.2:3b). Receives alerts from Wazuh integration and produces structured JSON output with severity classification, IOC extraction, and MITRE ATT&CK technique mapping.

**Key endpoints:**

```
POST /api/v1/triage/analyze          Analyze a single alert
POST /api/v1/triage/batch            Batch process multiple alerts
POST /api/v1/triage/analyze/async    Async analysis with job tracking
GET  /api/v1/triage/jobs/{job_id}    Check async job status
```

**Features:**

- Severity classification (Critical / High / Medium / Low / Informational)
- IOC extraction (IPs, domains, file hashes)
- MITRE ATT&CK technique mapping
- True/false positive detection with confidence scoring
- PII redaction before LLM processing
- Prompt injection detection
- ML-aware prompt enrichment (calls ML Inference for flow data)

---

## RAG Service

**Path:** `services/rag-service/`

Retrieval-Augmented Generation over security knowledge bases using ChromaDB and sentence-transformers. Provides semantic search to ground LLM responses in verified threat intelligence.

**Key endpoints:**

```
POST /api/v1/rag/retrieve            Semantic search over knowledge base
POST /api/v1/rag/ingest              Ingest documents into collections
GET  /api/v1/rag/collections         List available collections
POST /api/v1/rag/ingest/mitre        Ingest MITRE ATT&CK data
POST /api/v1/rag/ingest/cve          Ingest CVE data
POST /api/v1/rag/ingest/runbooks     Ingest security runbooks
```

**Knowledge sources:**

- MITRE ATT&CK (3000+ techniques and tactics)
- CVE database (critical vulnerabilities, CVSS >= 9.0)
- Security runbooks (response playbooks)

---

## Feedback Service

**Path:** `services/feedback-service/`

PostgreSQL-backed storage for alert history and analyst feedback. Enables the feedback loop: triage results are stored, analysts label them, and labels feed back into model retraining.

**Key endpoints:**

```
POST /api/v1/feedback/alerts         Store alert + triage results
GET  /api/v1/feedback/alerts         List alerts with filtering
GET  /api/v1/feedback/alerts/{id}    Get specific alert details
POST /api/v1/feedback/feedback/{id}  Submit analyst feedback
GET  /api/v1/feedback/feedback/{id}  Get feedback for an alert
GET  /api/v1/feedback/roi/metrics    ROI metrics from feedback data
```

---

## Correlation Engine

**Path:** `services/correlation-engine/`

Groups related alerts into incidents, tracks kill-chain progression, predicts next attacker moves using Markov chains, computes host risk scores, and runs attack-campaign simulations.

**Key endpoints:**

```
POST /api/v1/correlation/correlate           Correlate alerts into incidents
GET  /api/v1/correlation/incidents            List incidents
GET  /api/v1/correlation/incidents/active     List active incidents
GET  /api/v1/correlation/incidents/{id}       Get incident details
PUT  /api/v1/correlation/incidents/{id}/status  Update incident status
POST /api/v1/correlation/simulate             Run single attack simulation
POST /api/v1/correlation/simulate/swarm/start Start swarm simulation
GET  /api/v1/correlation/risk-scores          Get host risk scores
GET  /api/v1/correlation/predict/{stage}      Predict next kill-chain stage
```

---

## Response Orchestrator

**Path:** `services/response-orchestrator/`

Turns detected techniques and simulation output into candidate defensive actions. Maps ATT&CK techniques to D3FEND countermeasures, scores actions by impact and safety, and manages approval workflows.

**Key endpoints:**

```
POST /api/v1/response/defend         Generate defense plan for an incident
GET  /api/v1/response/plans          List defense plans
GET  /api/v1/response/plans/{id}     Get plan details
GET  /api/v1/response/approvals      List pending approvals
PUT  /api/v1/response/plans/{id}/actions/{action_id}/approve  Approve action
```

**Approval tiers:**

| Tier | Behavior |
|------|----------|
| Observe | Log only |
| Recommend | Analyst decides |
| Auto-safe | Low-blast action executes automatically |
| Auto-veto | Executes with a veto window |
| Human-required | Analyst approval required |

---

## ML Inference

**Path:** `services/ml_training/` (deployed as `ml-inference`)

FastAPI service for network intrusion detection using trained scikit-learn / XGBoost models. Expects exactly 77 CICIDS2017 flow features.

**Key endpoints:**

```
POST /predict          Classify a network flow (77 features)
POST /predict/batch    Batch classification
GET  /models           List available models
GET  /health           Health check
```

**Models:**

| Model | Accuracy | FPR | Size |
|-------|----------|-----|------|
| Random Forest | 99.28% | 0.25% | 2.93 MB |
| XGBoost | 99.21% | 0.09% | — |
| Decision Tree | 99.10% | 0.50% | — |

---

## Wazuh Integration

**Path:** `services/wazuh-integration/`

Webhook receiver that ingests Wazuh alerts, enriches them by calling Alert Triage and RAG Service, and forwards correlated data to the Correlation Engine.

**Key endpoints:**

```
POST /api/v1/wazuh/webhook    Receive Wazuh alerts (webhook)
GET  /api/v1/wazuh/alerts     List processed alerts
```

---

## Rule Generator

**Path:** `services/rule-generator/`

Generates Sigma detection rules from incident data and alert patterns. Supports rule approval workflows and historical back-testing.

**Key endpoints:**

```
POST /api/v1/rules/generate              Generate Sigma rule from incident
GET  /api/v1/rules/rules                 List generated rules
GET  /api/v1/rules/rules/pending         List rules pending approval
PUT  /api/v1/rules/rules/{id}/approve    Approve a rule
PUT  /api/v1/rules/rules/{id}/reject     Reject a rule
```

---

## Shared Library

**Path:** `services/common/`

Shared utilities imported by all services:

| Module | Purpose |
|--------|---------|
| `auth.py` | JWT authentication, API key management, OAuth2 token generation |
| `roles.py` | Role and scope definitions (admin / analyst / viewer) |
| `middleware.py` | Auth middleware, scope-check middleware |
| `rate_limit.py` | Sliding-window rate limiting |
| `security.py` | HTTP security headers, injection detection, PII redaction |
| `cache.py` | Redis caching with graceful degradation |
| `tracing.py` | OpenTelemetry distributed tracing setup |
| `pipeline.py` | Shared ML pipeline utilities |
| `logging_config.py` | Structured JSON logging |
