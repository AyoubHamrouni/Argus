"""
Common Utilities - AI-Augmented SOC Services

Shared functionality across all AI services:
- Authentication and authorization (JWT, API keys, RBAC)
- Rate limiting
- Security utilities (input validation, prompt injection, security headers)
- Ollama client interface
- Logging configuration
- Prometheus metrics
- OpenTelemetry tracing
- Redis caching
"""

__version__ = "1.0.0"

from .ollama_client import OllamaClient
from .logging_config import setup_logging, get_logger
from .metrics import ServiceMetrics
from .security import validate_input, sanitize_log, detect_prompt_injection
from .auth import (
    auth_manager,
    init_auth_manager,
    verify_token_dependency,
    require_scopes,
    generate_secret_key,
    JWTAuthManager,
)
from .roles import Role, Scope, ROLE_SCOPES, has_required_scope
from .middleware import AuthMiddleware, ScopeCheckMiddleware
from .rate_limit import RateLimitMiddleware, create_rate_limit_middleware
from .cache import (
    init_redis,
    close_redis,
    get_redis,
    make_cache_key,
    cache_get,
    cache_set,
    cache_delete,
    cached,
)

__all__ = [
    # Core
    "OllamaClient",
    "setup_logging",
    "get_logger",
    "ServiceMetrics",
    # Security
    "validate_input",
    "sanitize_log",
    "detect_prompt_injection",
    # Auth
    "auth_manager",
    "init_auth_manager",
    "verify_token_dependency",
    "require_scopes",
    "generate_secret_key",
    "JWTAuthManager",
    # Roles
    "Role",
    "Scope",
    "ROLE_SCOPES",
    "has_required_scope",
    # Middleware
    "AuthMiddleware",
    "ScopeCheckMiddleware",
    "RateLimitMiddleware",
    "create_rate_limit_middleware",
    # Cache
    "init_redis",
    "close_redis",
    "get_redis",
    "make_cache_key",
    "cache_get",
    "cache_set",
    "cache_delete",
    "cached",
]
