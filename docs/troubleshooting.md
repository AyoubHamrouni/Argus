# Argus Troubleshooting Guide

Common issues, error messages, and how to fix them.

---

## 1. Docker Issues

### "Docker not found" / "Docker daemon is not running"

**Error from quickstart.sh:**
```
ERROR: Docker not found. Please install Docker and try again.
ERROR: Docker daemon is not running. Please start Docker.
```

**Fix:**

```bash
# Check if Docker is installed
docker --version

# If not installed:
# Ubuntu/Debian
sudo apt-get update && sudo apt-get install -y docker.io docker-compose-plugin
sudo systemctl enable --now docker

# macOS
# Install Docker Desktop from https://www.docker.com/products/docker-desktop/

# Start Docker if installed but not running
sudo systemctl start docker

# Verify it's running
docker info
```

### "permission denied" — User not in docker group

```bash
# Add your user to the docker group
sudo usermod -aG docker $USER

# Log out and back in, or run:
newgrp docker

# Verify
docker ps
```

### "port already in use"

```bash
# Find what's using port 443, 8300, or 8500
sudo lsof -i :443
sudo lsof -i :8300
sudo lsof -i :8500

# Kill the conflicting process
sudo kill $(sudo lsof -t -i :443)

# Or use a different port by editing .env:
# Change GRAFANA_PORT=443 to GRAFANA_PORT=444
```

---

## 2. Memory Issues

### "Cannot allocate memory"

**Symptom:** Containers fail to start, OOM errors in logs.

```bash
# Check available memory
free -h

# Check per-container memory usage
docker stats --no-stream

# Close other applications, then retry
docker compose -f docker-compose/ai-services.yml down
docker compose -f docker-compose/phase1-siem-core.yml down
./quickstart.sh
```

### "OOMKilled" — Container memory limit too low

```bash
# Check if a container was OOMKilled
docker inspect <container_name> | grep -A 5 OOMKilled

# Increase memory limit in docker-compose yml:
# Under the service, add or increase:
#   deploy:
#     resources:
#       limits:
#         memory: 4G   # increase from default
```

**Minimum requirements:** 8GB RAM, 2 CPU cores for quickstart deployment.

---

## 3. Service Issues

### "Service unhealthy"

```bash
# Check container health status
docker ps --format 'table {{.Names}}\t{{.Status}}'

# Check logs for the unhealthy container
docker logs <container_name> --tail 100

# Restart the unhealthy service
docker compose -f docker-compose/ai-services.yml restart <service_name>
docker compose -f docker-compose/phase1-siem-core.yml restart <service_name>
```

**Common causes:**
- Service hasn't finished initializing (wait 2-3 minutes after first deploy)
- Dependency service not ready (e.g., Wazuh Manager waiting on Indexer)
- Insufficient memory
- Incorrect environment variables in `.env`

### Ollama model download fails

```bash
# Check network connectivity
curl -I https://ollama.com

# Pull the model manually
docker exec ollama ollama pull llama3.2

# If behind a proxy, set proxy env in .env:
# HTTP_PROXY=http://proxy:port
# HTTPS_PROXY=http://proxy:port
```

### ChromaDB won't start

```bash
# Check disk space
df -h

# Check volume permissions
docker volume ls
docker volume inspect <volume_name>

# If disk is full, prune Docker resources
docker system prune -a --volumes

# Check ChromaDB logs
docker logs chromadb --tail 100
```

---

## 4. Network Issues

### Can't connect to services from host

```bash
# Check which ports are exposed
docker ps --format 'table {{.Names}}\t{{.Ports}}'

# Verify port bindings
netstat -tlnp | grep -E '443|8300|8500'

# Test connectivity
curl -k https://localhost:443        # Wazuh Dashboard
curl http://localhost:8500/docs      # ML Inference API
curl http://localhost:8300/health    # RAG Service
```

### Docker network conflicts

```bash
# List Docker networks
docker network ls

# Check subnet ranges in .env
grep -E 'SUBNET' .env

# If subnets conflict with host networks, change them:
# BACKEND_SUBNET=172.20.0.0/16   →  172.25.0.0/16
# FRONTEND_SUBNET=172.21.0.0/16  →  172.26.0.0/16

# Recreate networks after changing
docker compose -f docker-compose/ai-services.yml down
docker compose -f docker-compose/ai-services.yml up -d
```

---

## 5. Wazuh Integration

### "Connection refused" to Wazuh Manager

```bash
# Check if Wazuh Manager is running
docker ps | grep wazuh-manager

# Check manager logs
docker logs wazuh-manager --tail 100

# Verify SSL certificates exist
ls -la scripts/certs/

# Regenerate certificates
bash scripts/generate-certs.sh

# Check port 1514 (agent) and 1515 (registration)
netstat -tlnp | grep -E '1514|1515'
```

### "Authentication failed"

```bash
# Verify credentials in .env match Wazuh config
grep -E 'USERNAME|PASSWORD' .env

# Default credentials (quickstart):
# INDEXER_USERNAME=admin
# INDEXER_PASSWORD=SecurePass123!
# API_USERNAME=wazuh-wui
# API_PASSWORD=SecurePass456!

# Test Wazuh API authentication
curl -k -u wazuh-wui:SecurePass456! https://localhost:55000/security/user/authenticate
```

### Alerts not appearing

```bash
# Check ossec.conf integration block on agents
docker exec wazuh-manager cat /var/ossec/etc/ossec.conf | grep -A 20 integration

# Verify the integration section includes:
# <integration>
#   <name>custom-ai-soc</name>
#   <hook_url>http://ml-inference:8500/api/v1/alerts</hook_url>
#   <level>12</level>
#   <alert_format>json</alert_format>
# </integration>

# Check agent connectivity
docker exec wazuh-manager /var/ossec/bin/agent_control -l
```

---

## 6. ML Inference

### Models not loading

```bash
# Check models directory exists and has content
ls -la models/

# Check disk space (models can be several GB)
df -h .

# Check ML inference logs
docker logs ml-inference --tail 100

# Restart ML inference service
docker compose -f docker-compose/ai-services.yml restart ml-inference
```

### Slow inference

```bash
# Check if GPU is available
docker exec ml-inference nvidia-smi 2>/dev/null || echo "No GPU detected"

# CPU-only mode is slower but works
# To enable GPU passthrough, add to docker-compose:
#   deploy:
#     resources:
#       reservations:
#         devices:
#           - driver: nvidia
#             count: 1
#             capabilities: [gpu]

# Consider using smaller models for CPU:
# Change model in .env: ML_MODEL_SIZE=small
```

---

## 7. Database Issues

### PostgreSQL won't start

```bash
# Check if POSTGRES_PASSWORD is set in .env
grep POSTGRES_PASSWORD .env

# If missing, add it:
echo "POSTGRES_PASSWORD=your_secure_password" >> .env

# Check PostgreSQL logs
docker logs postgres --tail 100

# Verify volume permissions
docker volume inspect argus_postgres_data
```

### Alembic migration fails

```bash
# Check database connection string
grep DATABASE_URL .env

# Verify PostgreSQL is healthy
docker ps | grep postgres

# Run migrations manually
docker exec -it alembic alembic upgrade head

# Check migration status
docker exec -it alembic alembic current
```

---

## 8. Reset Everything

### Full cleanup — nuclear option

```bash
# Stop all containers and remove volumes
docker compose -f docker-compose/ai-services.yml down -v --remove-orphans
docker compose -f docker-compose/phase1-siem-core.yml down -v --remove-orphans
docker compose -f docker-compose/phase2-soar-stack.yml down -v --remove-orphans
docker compose -f docker-compose/monitoring-stack.yml down -v --remove-orphans
docker compose -f docker-compose/network-analysis-stack.yml down -v --remove-orphans
docker compose -f docker-compose/dev-environment.yml down -v --remove-orphans
docker compose -f docker-compose/integrated-stack.yml down -v --remove-orphans

# Prune all Docker resources
docker system prune -a --volumes

# Remove .env to regenerate fresh
rm -f .env docker-compose/.env

# Remove generated certificates
rm -rf scripts/certs/

# Remove logs
rm -rf logs/

# Start fresh
./quickstart.sh
```

### Quick restart without full reset

```bash
# Just restart the failed stack
docker compose -f docker-compose/ai-services.yml restart
docker compose -f docker-compose/phase1-siem-core.yml restart

# Check status
docker ps --format 'table {{.Names}}\t{{.Status}}'
```

---

## Quick Reference: Service Ports

| Service            | Port | URL                              |
|--------------------|------|----------------------------------|
| Wazuh Dashboard    | 443  | https://localhost:443            |
| ML Inference API   | 8500 | http://localhost:8500/docs       |
| RAG Service        | 8300 | http://localhost:8300/health     |
| Wazuh API          | 55000| https://localhost:55000          |
| PostgreSQL         | 5432 | localhost:5432                   |
| Redis              | 6379 | localhost:6379                   |
| ChromaDB           | 8000 | http://localhost:8000            |
| Grafana            | 3000 | http://localhost:3000            |

## Quick Reference: Useful Commands

```bash
# View all running containers
docker ps

# View all containers (including stopped)
docker ps -a

# Follow logs for a service
docker compose -f docker-compose/ai-services.yml logs -f

# Check resource usage
docker stats --no-stream

# Restart a specific service
docker compose -f docker-compose/phase1-siem-core.yml restart wazuh-manager

# Enter a running container
docker exec -it <container_name> /bin/bash
```
