# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x     | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability within AI-SOC, please report it through [GitHub Security Advisories](https://github.com/zhadyz/AI_SOC/security/advisories/new). All security vulnerabilities will be promptly addressed.

**Please do NOT report security vulnerabilities through public GitHub issues.**

### What to Include

When reporting a vulnerability, please include:

- A description of the vulnerability
- Steps to reproduce the issue
- Potential impact
- Suggested fix (if any)

### Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial assessment**: Within 1 week
- **Fix or mitigation**: Depends on severity, typically 1-4 weeks

### Scope

The following are in scope for security reports:

- Authentication/authorization bypass
- Remote code execution
- SQL injection
- Cross-site scripting (XSS)
- Server-side request forgery (SSRF)
- Prompt injection attacks that could lead to data exfiltration
- Path traversal vulnerabilities
- Deserialization vulnerabilities (especially related to pickle files)

### Out of Scope

- Denial of service attacks
- Social engineering
- Issues in third-party dependencies (report these to the respective maintainers)

## Security Best Practices

When deploying AI-SOC, follow these security guidelines:

1. **Never commit secrets** - Use environment variables and the `.env.example` template
2. **Enable authentication** - Set `API_KEY_ENABLED=true` in production
3. **Use TLS** - Configure SSL certificates for all inter-service communication
4. **Run containers as non-root** - All Dockerfiles are configured for this
5. **Scan for vulnerabilities** - Use Trivy and Snyk for dependency scanning
6. **Keep dependencies updated** - Enable Dependabot for automated updates
7. **Limit network access** - Use Docker networks to isolate service tiers
8. **Monitor logs** - Use the Prometheus/Grafana stack for anomaly detection

## Security Features

AI-SOC includes several built-in security features:

- **Input validation** on all API endpoints (`services/common/security.py`)
- **Prompt injection detection** for LLM inputs
- **PII redaction** before LLM processing
- **API key authentication** (configurable per service)
- **Rate limiting** with sliding window algorithm
- **Security headers** (CSP, HSTS, X-Frame-Options, etc.)
- **Structured logging** with sensitive data sanitization
- **Bandit** security linting in CI pipeline
- **Trivy** container vulnerability scanning

## Acknowledgments

We thank security researchers who responsibly disclose vulnerabilities. Your efforts help make AI-SOC safer for everyone.
