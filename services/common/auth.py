"""
JWT Authentication System - Common Utilities
AI-Augmented SOC

JWT-based authentication with API key support and OAuth2 flows.
Provides token generation, validation, refresh, and RBAC.

Supports:
- JWT access and refresh tokens (HS256)
- API keys with aisoc_ prefix
- OAuth2 authorization code flow (via stateless JWT)
- Role-based access control via scopes
"""

import logging
import secrets
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

import jwt
from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)


class APIKeyStore(ABC):
    """Abstract interface for API key persistence."""

    @abstractmethod
    async def store_key(self, key: str, data: Dict[str, Any]) -> None: ...

    @abstractmethod
    async def get_key(self, key: str) -> Optional[Dict[str, Any]]: ...

    @abstractmethod
    async def revoke_key(self, key: str) -> bool: ...

    @abstractmethod
    async def list_keys(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]: ...


class InMemoryAPIKeyStore(APIKeyStore):
    """In-memory API key store for development."""

    def __init__(self):
        self._keys: Dict[str, Dict[str, Any]] = {}

    async def store_key(self, key: str, data: Dict[str, Any]) -> None:
        self._keys[key] = data

    async def get_key(self, key: str) -> Optional[Dict[str, Any]]:
        return self._keys.get(key)

    async def revoke_key(self, key: str) -> bool:
        if key in self._keys:
            self._keys[key]["is_active"] = False
            return True
        return False

    async def list_keys(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        keys = list(self._keys.values())
        if user_id:
            keys = [k for k in keys if k.get("user_id") == user_id]
        return keys


class JWTAuthManager:
    """
    JWT Authentication Manager.

    Handles token generation, validation, API key management,
    and password hashing for all Argus services.
    """

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7,
        api_key_store: Optional[APIKeyStore] = None,
    ):
        if len(secret_key) < 32:
            raise ValueError("Secret key must be at least 32 characters")

        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
        self.key_store = api_key_store or InMemoryAPIKeyStore()

        logger.info("JWT Auth Manager initialized (algorithm=%s)", algorithm)

    async def generate_api_key(
        self,
        user_id: str,
        scopes: Optional[List[str]] = None,
        expires_days: int = 365,
        name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate and store a new API key."""
        api_key = f"aisoc_{secrets.token_urlsafe(32)}"
        now = datetime.utcnow()

        key_data = {
            "key": api_key,
            "user_id": user_id,
            "name": name or f"key-{user_id}",
            "scopes": scopes or ["read", "write"],
            "created_at": now.isoformat(),
            "expires_at": (now + timedelta(days=expires_days)).isoformat(),
            "is_active": True,
        }

        await self.key_store.store_key(api_key, key_data)
        logger.info("Generated API key for user=%s name=%s", user_id, key_data["name"])
        return key_data

    async def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Validate an API key and return its metadata."""
        key_data = await self.key_store.get_key(api_key)
        if key_data is None:
            logger.warning("Invalid API key attempted")
            return None

        if not key_data.get("is_active", False):
            logger.warning("Inactive API key used")
            return None

        expires_at = key_data.get("expires_at")
        if expires_at and datetime.fromisoformat(expires_at) < datetime.utcnow():
            logger.warning("Expired API key used")
            return None

        return key_data

    async def revoke_api_key(self, api_key: str) -> bool:
        return await self.key_store.revoke_api_key(api_key)

    async def list_api_keys(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        return await self.key_store.list_keys(user_id)

    def create_access_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=self.access_token_expire_minutes))
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access",
        })
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create a JWT refresh token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh",
        })
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning("Invalid token: %s", e)
            return None

    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Create a new access token from a valid refresh token."""
        payload = self.verify_token(refresh_token)
        if payload is None or payload.get("type") != "refresh":
            return None
        token_data = {k: v for k, v in payload.items() if k not in ("exp", "iat", "type")}
        return self.create_access_token(token_data)

    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)


# ---------------------------------------------------------------------------
# Global singleton
# ---------------------------------------------------------------------------

auth_manager: Optional[JWTAuthManager] = None


def init_auth_manager(secret_key: str, **kwargs) -> JWTAuthManager:
    """Initialize the global auth manager. Call once at app startup."""
    global auth_manager
    auth_manager = JWTAuthManager(secret_key, **kwargs)
    return auth_manager


# ---------------------------------------------------------------------------
# FastAPI dependencies
# ---------------------------------------------------------------------------

async def verify_token_dependency(
    credentials: HTTPAuthorizationCredentials = None,
) -> Dict[str, Any]:
    """FastAPI dependency: verify JWT or API key from Authorization header."""
    if auth_manager is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication system not initialized",
        )

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # API key
    if token.startswith("aisoc_"):
        key_data = await auth_manager.validate_api_key(token)
        if key_data is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired API key",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return key_data

    # JWT
    payload = auth_manager.verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )
    return payload


def require_scopes(required_scopes: List[str]):
    """Dependency factory: require specific scopes for endpoint access."""

    async def _check(
        credentials: HTTPAuthorizationCredentials = None,
    ) -> Dict[str, Any]:
        user = await verify_token_dependency(credentials)
        user_scopes = user.get("scopes", [])

        for scope in required_scopes:
            if scope not in user_scopes:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required: {scope}",
                )
        return user

    return _check


def generate_secret_key() -> str:
    """Generate a secure random secret key. Store this securely in production."""
    return secrets.token_urlsafe(64)
