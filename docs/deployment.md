# Deployment

## Deployment Options

| Method | Best For | SIEM Support |
|--------|----------|--------------|
| Deploy script (`deploy-ai-soc.sh`) | Quick start, full stack | Full (Linux) |
| Docker Compose (manual) | Custom configurations | Full (Linux), partial (macOS/Windows) |
| Kubernetes | AI services in production | SIEM runs outside cluster |
| Terraform | Cloud infrastructure | Provisioned separately |

## One-Command Deployment

```bash
git clone https://github.com/zhadyz/AI_SOC.git
cd AI_SOC
cp .env.example .env   # Edit with your values
./deploy-ai-soc.sh
```

The script deploys three stacks in order:

1. **SIEM Core** — Wazuh manager, indexer, dashboard
2. **AI Services** — All microservices, Redis, OpenTelemetry collector
3. **Monitoring** — Prometheus, Grafana, Alertmanager

## Docker Compose Files

| File | Containers | Purpose |
|------|------------|---------|
| `phase1-siem-core.yml` | Wazuh manager, indexer, dashboard | Core SIEM (Linux) |
| `phase1-siem-core-windows.yml` | Wazuh (limited) | SIEM for macOS/Windows |
| `ai-services.yml` | 7 AI services, Redis, otel-collector | AI layer |
| `monitoring-stack.yml` | Prometheus, Grafana, Alertmanager, Loki | Observability |

## Kubernetes

AI services can be deployed to Kubernetes using the manifests in `k8s/ai-services/`:

```bash
# Deploy all AI services
kubectl apply -k k8s/ai-services/

# Check status
kubectl get pods -n ai-soc
kubectl get svc -n ai-soc
```

**Resources included:**

- Namespace `ai-soc`
- ConfigMap and Secret templates
- Deployments with health checks and resource limits
- Services (ClusterIP) for internal communication
- HorizontalPodAutoscalers (2-4 replicas, 70% CPU target)
- Redis deployment

**Security:**

- All containers run as non-root (UID 1000)
- Read-only root filesystem
- No privilege escalation
- Resource limits enforced

## Terraform

Multi-cloud infrastructure provisioning in `terraform/`:

```bash
cd terraform/aws    # or azure/ or gcp
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
terraform init
terraform plan
terraform apply
```

**Provisioned resources:**

- VPC/VNet with public and private subnets
- Managed PostgreSQL (RDS / Azure Database / Cloud SQL)
- Kubernetes cluster (EKS / AKS / GKE)

See [terraform/README.md](../terraform/README.md) for provider-specific instructions.

## Environment Configuration

All services are configured through environment variables. Copy `.env.example` to `.env` and set values:

```bash
cp .env.example .env
```

Key variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_HOST` | `postgres` | PostgreSQL host |
| `POSTGRES_PASSWORD` | `ai_soc_password` | PostgreSQL password (change in production) |
| `JWT_SECRET_KEY` | — | Secret for JWT token signing (required) |
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection URL |
| `OLLAMA_MODEL` | `llama3.2:3b` | Ollama model for LLM inference |
| `LITELLM_MODEL` | `gpt-4o-mini` | LiteLLM model alias |
| `*_API_KEY` | `aisoc_change_me_in_production` | Per-service API keys |

See [configuration.md](configuration.md) for the full list.

## Production Hardening

Before deploying outside a lab environment:

1. Change all default passwords and API keys in `.env`
2. Enable TLS for inter-service communication
3. Configure firewall rules and network segmentation
4. Set up proper log aggregation and alerting
5. Enable deletion protection on PostgreSQL
6. Review container security contexts
7. Configure backup schedules for databases

## Monitoring

The monitoring stack provides:

- **Prometheus**: Metrics collection from all services (`:9090`)
- **Grafana**: Dashboards and visualization (`:3000`)
- **Alertmanager**: Alert routing and notifications (`:9093`)
- **Loki**: Log aggregation
- **OTel Collector**: Distributed trace collection (`:4317` gRPC, `:4318` HTTP)
