"""
Unified Auth Middleware - Common Utilities
AI-Augmented SOC

Centralized authentication middleware supporting JWT tokens, API keys,
and OAuth2 flows. Replaces per-service local auth implementations.
"""

import logging
from typing import Optional, List, Callable

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from .auth import auth_manager, verify_token, validate_api_key
from .roles import Scope, has_required_scope

logger = logging.getLogger(__name__)

# Paths that bypass authentication
DEFAULT_EXEMPT_PATHS = {
    "/health",
    "/metrics",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/",
}


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Unified authentication middleware for all services.

    Supports:
    - JWT Bearer tokens
    - API keys (aisoc_ prefix)
    - Path-based exemptions (health, metrics, docs)
    """

    def __init__(
        self,
        app,
        service_name: str = "unknown",
        exempt_paths: Optional[List[str]] = None,
    ):
        super().__init__(app)
        self.service_name = service_name
        self.exempt_paths = set(exempt_paths or []) | DEFAULT_EXEMPT_PATHS

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        path = request.url.path

        # Allow exempt paths without authentication
        if path in self.exempt_paths or any(path.startswith(p) for p in self.exempt_paths if p.endswith("/")):
            return await call_next(request)

        # Allow CORS preflight
        if request.method == "OPTIONS":
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")

        if not auth_header:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing Authorization header"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            scheme, token = auth_header.split(" ", 1)
        except ValueError:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid Authorization header format"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        if scheme.lower() != "bearer":
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid authentication scheme. Use Bearer."},
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Try API key first (aisoc_ prefix)
        if token.startswith("aisoc_"):
            key_data = validate_api_key(token)
            if key_data is None:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid or expired API key"},
                    headers={"WWW-Authenticate": "Bearer"},
                )
            request.state.user = key_data
            request.state.auth_method = "api_key"
            return await call_next(request)

        # Try JWT token
        payload = verify_token(token)
        if payload is None:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid or expired token"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        if payload.get("type") != "access":
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid token type"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        request.state.user = payload
        request.state.auth_method = "jwt"
        return await call_next(request)


class ScopeCheckMiddleware(BaseHTTPMiddleware):
    """
    Scope-based authorization middleware.

    Must be applied AFTER AuthMiddleware. Checks that the authenticated
    user has the required scopes for the requested endpoint.
    """

    def __init__(
        self,
        app,
        route_scopes: Optional[dict] = None,
    ):
        super().__init__(app)
        self.route_scopes = route_scopes or {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip if no user (auth middleware handles unauthenticated)
        user = getattr(request.state, "user", None)
        if user is None:
            return await call_next(request)

        path = request.url.path
        method = request.method.upper()

        # Check if this route requires specific scopes
        required_scope = self.route_scopes.get(f"{method}:{path}")
        if required_scope is None:
            return await call_next(request)

        user_scopes = user.get("scopes", [])
        if isinstance(required_scope, str):
            required_scope = [required_scope]

        for scope in required_scope:
            if not has_required_scope(user_scopes, Scope(scope)):
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": f"Insufficient permissions. Required: {scope}"},
                )

        return await call_next(request)
