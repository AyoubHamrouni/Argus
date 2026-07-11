# API Reference

All services expose OpenAPI docs at `/docs` (Swagger UI) and `/openapi.json` when running. This page provides a quick reference for the main endpoints.

## Authentication

Every endpoint except `/health` and `/metrics` requires authentication:

```bash
# API Key
curl -H "X-API-Key: your-key" http://localhost:8100/api/v1/triage/analyze

# JWT Bearer token
curl -H "Authorization: Bearer <jwt-token>" http://localhost:8100/api/v1/triage/analyze
```

## Alert Triage — `:8100`

### POST `/api/v1/triage/analyze`

Analyze a single security alert.

**Request:**

```json
{
  "alert_id": "alert-001",
  "rule_description": "SSH brute force attack detected",
  "rule_level": 10,
  "source_ip": "203.0.113.42",
  "dest_ip": "10.0.1.50",
  "dest_port": 22,
  "raw_log": "Failed password for root from 203.0.113.42 port 45678 ssh2"
}
```

**Response:**

```json
{
  "alert_id": "alert-001",
  "severity": "high",
  "category": "intrusion_attempt",
  "confidence": 0.92,
  "summary": "SSH brute force activity from 203.0.113.42",
  "is_true_positive": true,
  "iocs": [
    {"ioc_type": "ip", "value": "203.0.113.42", "confidence": 0.95}
  ],
  "mitre_techniques": ["T1110.001"],
  "recommendations": [
    {
      "action": "Block source IP at the perimeter firewall",
      "priority": 1,
      "rationale": "Prevents continued brute-force attempts"
    }
  ]
}
```

### POST `/api/v1/triage/batch`

Analyze multiple alerts in a single request. Accepts an array of alert objects.

### POST `/api/v1/triage/analyze/async`

Submit alerts for async processing. Returns a `job_id` for polling.

### GET `/api/v1/triage/jobs/{job_id}`

Check async job status and retrieve results when complete.

---

## RAG Service — `:8300`

### POST `/api/v1/rag/retrieve`

Semantic search over security knowledge base.

**Request:**

```json
{
  "query": "credential dumping LSASS memory",
  "collection": "mitre_attack",
  "top_k": 3
}
```

**Response:** Array of matching documents with relevance scores.

### POST `/api/v1/rag/ingest`

Ingest documents into a specified collection.

### POST `/api/v1/rag/ingest/mitre`

Ingest MITRE ATT&CK techniques and tactics.

### POST `/api/v1/rag/ingest/cve`

Ingest CVE vulnerability data.

### POST `/api/v1/rag/ingest/runbooks`

Ingest security response runbooks.

### GET `/api/v1/rag/collections`

List all available collections with document counts.

---

## ML Inference — `:8500`

### POST `/predict`

Classify a network flow using trained ML models.

**Request:**

```json
{
  "features": [0.0, 0.0, 0.0, ...],
  "model_name": "random_forest"
}
```

The `features` array must contain exactly 77 values in the trained feature order (see `models/feature_names.pkl`).

**Response:**

```json
{
  "prediction": "BENIGN",
  "confidence": 0.97,
  "model_used": "random_forest",
  "latency_ms": 0.8
}
```

### POST `/predict/batch`

Batch classification for multiple flow vectors.

### GET `/models`

List available models and their metadata.

---

## Correlation Engine — `:8600`

### POST `/api/v1/correlation/correlate`

Submit alerts for incident correlation and grouping.

### GET `/api/v1/correlation/incidents`

List all incidents with filtering and pagination.

### GET `/api/v1/correlation/incidents/active`

List currently active (open) incidents.

### GET `/api/v1/correlation/incidents/{incident_id}`

Get full incident details including related alerts and kill-chain state.

### POST `/api/v1/correlation/simulate`

Run a single attack campaign simulation.

**Query parameters:** `timesteps` (default: 5)

### POST `/api/v1/correlation/simulate/swarm/start`

Start a Monte Carlo swarm simulation.

**Query parameters:** `swarm_size`, `monte_carlo_runs`, `timesteps`

### GET `/api/v1/correlation/simulate/swarm/{swarm_id}/status`

Poll swarm simulation status.

### GET `/api/v1/correlation/simulate/swarm/{swarm_id}/result`

Fetch completed swarm simulation results.

### GET `/api/v1/correlation/risk-scores`

Get risk scores for all known hosts.

### GET `/api/v1/correlation/risk-scores/{host_ip}`

Get risk score for a specific host.

### GET `/api/v1/correlation/predict/{kill_chain_stage}`

Predict likely next attacker moves from a given kill-chain stage.

---

## Feedback Service — `:8400`

### POST `/api/v1/feedback/alerts`

Store alert and triage results.

### GET `/api/v1/feedback/alerts`

List stored alerts with filtering.

### GET `/api/v1/feedback/alerts/{alert_id}`

Get specific alert details.

### POST `/api/v1/feedback/feedback/{alert_id}`

Submit analyst feedback for an alert.

**Request:**

```json
{
  "analyst_id": "analyst1",
  "is_false_positive": false,
  "true_label": "ATTACK",
  "notes": "Confirmed brute-force source"
}
```

### GET `/api/v1/feedback/feedback/{alert_id}`

Get feedback for a specific alert.

### GET `/api/v1/feedback/roi/metrics`

Get ROI metrics derived from feedback data.

---

## Response Orchestrator — `:8800`

### POST `/api/v1/response/defend`

Generate a defense plan for an incident.

**Request:**

```json
{
  "incident_id": "INC-20250324-ab12",
  "auto_execute": false,
  "dry_run": true
}
```

### GET `/api/v1/response/plans`

List all defense plans.

### GET `/api/v1/response/plans/{plan_id}`

Get plan details including scored actions and approval status.

### GET `/api/v1/response/approvals`

List actions pending approval.

### PUT `/api/v1/response/plans/{plan_id}/actions/{action_id}/approve`

Approve a specific action for execution.

---

## Wazuh Integration — `:8002`

### POST `/api/v1/wazuh/webhook`

Receive Wazuh alerts via webhook. This is the primary ingestion point for the SIEM.

### GET `/api/v1/wazuh/alerts`

List processed and enriched alerts.

---

## Rule Generator — `:8700`

### POST `/api/v1/rules/generate`

Generate a Sigma detection rule from incident data.

### GET `/api/v1/rules/rules`

List all generated rules.

### GET `/api/v1/rules/rules/pending`

List rules pending approval.

### PUT `/api/v1/rules/rules/{rule_id}/approve`

Approve a rule for deployment.

### PUT `/api/v1/rules/rules/{rule_id}/reject`

Reject a rule.

---

## Health & Metrics

Every service exposes:

```
GET /health       Health check (returns {"status": "healthy"})
GET /metrics      Prometheus metrics
```

These endpoints do not require authentication.
