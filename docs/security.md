# Security

## Authentication & Authorization

All service endpoints (except `/health` and `/metrics`) require authentication.

### JWT Tokens

```bash
# Obtain a token
curl -X POST http://localhost:8100/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "changeme"}'

# Use the token
curl -H "Authorization: Bearer <token>" http://localhost:8100/api/v1/triage/analyze
```

### API Keys

Each service accepts API key authentication via the `X-API-Key` header:

```bash
curl -H "X-API-Key: your-key" http://localhost:8100/api/v1/triage/analyze
```

### Roles

| Role | Permissions |
|------|-------------|
| `admin` | Full access to all services |
| `analyst` | Read/write on triage, feedback, correlation |
| `viewer` | Read-only access |

### Scopes

Scoped access controls which services a token can reach:

| Scope | Services |
|-------|----------|
| `triage:read`, `triage:write` | Alert Triage |
| `rag:read`, `rag:ingest` | RAG Service |
| `ml:read`, `ml:predict` | ML Inference |
| `correlation:read`, `correlation:write` | Correlation Engine |
| `response:read`, `response:write` | Response Orchestrator |
| `feedback:read`, `feedback:write` | Feedback Service |

## Rate Limiting

All services use sliding-window rate limiting (100 requests per 60 seconds by default). LLM-heavy endpoints use stricter limits.

Rate limit headers are included in responses:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## Input Validation

- All API inputs are validated against Pydantic models
- SQL injection protection via parameterized queries
- Prompt injection detection on LLM-facing endpoints
- PII redaction before LLM processing

## HTTP Security Headers

Every response includes security headers:

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
```

## Secrets Management

- `.env` files are gitignored — never commit secrets
- JWT signing keys should be randomly generated and unique per environment
- Database credentials should use strong, unique passwords
- API keys should be rotated periodically
- In production, use a secrets manager (Vault, AWS Secrets Manager, etc.)

## Container Security

Kubernetes deployments enforce:

- Non-root containers (UID 1000)
- Read-only root filesystem
- No privilege escalation
- Resource limits on CPU and memory
- Network policies restricting inter-service communication

## Production Checklist

Before deploying outside a lab environment:

- [ ] Change all default passwords in `.env`
- [ ] Generate a unique `JWT_SECRET_KEY`
- [ ] Set unique API keys for each service
- [ ] Enable TLS for external-facing endpoints
- [ ] Configure firewall rules
- [ ] Enable PostgreSQL deletion protection
- [ ] Set up automated backups
- [ ] Configure log aggregation
- [ ] Review container security contexts
- [ ] Validate LLM output before automated actions
