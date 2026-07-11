# Contributing to AI-SOC

Thank you for your interest in contributing to AI-Augmented Security Operations Center! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)
- [Testing Requirements](#testing-requirements)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/AI_SOC.git`
3. Create a feature branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Run tests and linting
6. Commit your changes
7. Push to your fork and submit a pull request

## Development Setup

### Prerequisites

- Python 3.11+
- Docker and Docker Compose v2
- Git

### Local Setup

```bash
# Clone the repository
git clone https://github.com/zhadyz/AI_SOC.git
cd AI_SOC

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install development dependencies
pip install -r tests/requirements.txt

# Install pre-commit hooks
pre-commit install

# Start the development environment
docker compose -f docker-compose/dev-environment.yml up -d
```

### Running Tests

```bash
# Run all unit tests
make test

# Or with pytest directly
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ -v --cov=services --cov-report=html
```

## Coding Standards

### Code Style

- **Formatter:** Black (line-length=120)
- **Import Sorting:** isort (profile="black")
- **Linter:** Pylint (max-line-length=120, max-complexity=15)
- **Type Checker:** MyPy (Python 3.11 target)
- **Security Linter:** Bandit

Run all checks before committing:

```bash
make lint
make format
```

### Python Style Guide

- Use type hints for all function signatures
- Follow PEP 8 naming conventions (enforced by Black/isort)
- Write docstrings for public functions and classes
- Keep functions focused and under 50 lines where possible
- Use `async/await` for I/O-bound operations

### Example

```python
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class AlertRequest(BaseModel):
    """Request model for alert analysis."""
    alert_id: str
    source: str
    description: str

class AlertResponse(BaseModel):
    """Response model for alert analysis."""
    alert_id: str
    severity: str
    confidence: float

@router.post("/analyze", response_model=AlertResponse)
async def analyze_alert(request: AlertRequest) -> AlertResponse:
    """Analyze a security alert using LLM triage.

    Args:
        request: The alert to analyze.

    Returns:
        Analysis result with severity and confidence.
    """
    # Implementation here
    ...
```

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

### Types

- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Changes that do not affect the meaning of the code
- `refactor`: A code change that neither fixes a bug nor adds a feature
- `test`: Adding missing tests or correcting existing tests
- `chore`: Changes to the build process or auxiliary tools

### Examples

```
feat(alert-triage): add batch processing endpoint

fix(correlation-engine): resolve race condition in incident grouping

docs(readme): update deployment instructions

test(ml-inference): add edge case tests for feature validation
```

## Pull Request Process

1. **Ensure your code follows the coding standards** (`make lint` passes)
2. **Add tests** for new functionality
3. **Update documentation** if your change affects user-facing behavior
4. **Fill out the PR template** completely
5. **Request review** from a maintainer
6. **Address review feedback** promptly

### PR Title

Use the same Conventional Commits format as commit messages:

```
feat(correlation-engine): add MITRE kill-chain correlation
```

### PR Description

The PR template will guide you through providing:
- Summary of changes
- Related issue(s)
- Type of change
- Testing performed
- Checklist verification

## Testing Requirements

### Unit Tests

- All new functions must have unit tests
- Aim for >70% code coverage on new code
- Tests should be fast (<100ms per test)

```bash
pytest tests/unit/ -v --cov=services
```

### Integration Tests

- Test service-to-service communication
- Mark tests that require running infrastructure

```bash
pytest tests/integration/ -v -m "not requires_ollama"
```

### Security Tests

- Test for OWASP Top 10 vulnerabilities
- Verify input validation and prompt injection protection

```bash
pytest tests/security/ -v -m security
```

## Reporting Bugs

Use the [Bug Report](https://github.com/zhadyz/AI_SOC/issues/new?template=bug_report.md) template. Include:

- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version, Docker version)
- Relevant logs or screenshots

## Suggesting Features

Use the [Feature Request](https://github.com/zhadyz/AI_SOC/issues/new?template=feature_request.md) template. Include:

- Problem statement
- Proposed solution
- Alternatives considered
- Additional context

## Questions?

Open a [Discussion](https://github.com/zhadyz/AI_SOC/discussions) or reach out to the maintainers.

---

Thank you for contributing to AI-SOC!
