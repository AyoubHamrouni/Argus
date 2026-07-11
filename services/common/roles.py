"""
Roles and Scopes - Common Utilities
AI-Augmented SOC

Defines roles, scopes, and permission mappings for the RBAC system.
"""

from enum import Enum
from typing import Dict, Set


class Role(str, Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


class Scope(str, Enum):
    TRIAGE_READ = "triage:read"
    TRIAGE_WRITE = "triage:write"
    RAG_READ = "rag:read"
    RAG_WRITE = "rag:write"
    CORRELATE_READ = "correlate:read"
    CORRELATE_WRITE = "correlate:write"
    DEFEND_READ = "defend:read"
    DEFEND_WRITE = "defend:write"
    RULES_READ = "rules:read"
    RULES_WRITE = "rules:write"
    FEEDBACK_READ = "feedback:read"
    FEEDBACK_WRITE = "feedback:write"
    ML_READ = "ml:read"
    ML_WRITE = "ml:write"
    ADMIN_ACCESS = "admin:access"
    METRICS = "metrics:read"


ROLE_SCOPES: Dict[Role, Set[Scope]] = {
    Role.ADMIN: {
        Scope.TRIAGE_READ, Scope.TRIAGE_WRITE,
        Scope.RAG_READ, Scope.RAG_WRITE,
        Scope.CORRELATE_READ, Scope.CORRELATE_WRITE,
        Scope.DEFEND_READ, Scope.DEFEND_WRITE,
        Scope.RULES_READ, Scope.RULES_WRITE,
        Scope.FEEDBACK_READ, Scope.FEEDBACK_WRITE,
        Scope.ML_READ, Scope.ML_WRITE,
        Scope.ADMIN_ACCESS, Scope.METRICS,
    },
    Role.ANALYST: {
        Scope.TRIAGE_READ, Scope.TRIAGE_WRITE,
        Scope.RAG_READ,
        Scope.CORRELATE_READ, Scope.CORRELATE_WRITE,
        Scope.DEFEND_READ, Scope.DEFEND_WRITE,
        Scope.RULES_READ, Scope.RULES_WRITE,
        Scope.FEEDBACK_READ, Scope.FEEDBACK_WRITE,
        Scope.ML_READ,
        Scope.METRICS,
    },
    Role.VIEWER: {
        Scope.TRIAGE_READ,
        Scope.RAG_READ,
        Scope.CORRELATE_READ,
        Scope.DEFEND_READ,
        Scope.RULES_READ,
        Scope.FEEDBACK_READ,
        Scope.ML_READ,
        Scope.METRICS,
    },
}

SERVICE_SCOPES: Dict[str, Set[Scope]] = {
    "alert-triage": {Scope.TRIAGE_READ, Scope.TRIAGE_WRITE},
    "rag-service": {Scope.RAG_READ, Scope.RAG_WRITE},
    "correlation-engine": {Scope.CORRELATE_READ, Scope.CORRELATE_WRITE},
    "response-orchestrator": {Scope.DEFEND_READ, Scope.DEFEND_WRITE},
    "rule-generator": {Scope.RULES_READ, Scope.RULES_WRITE},
    "feedback-service": {Scope.FEEDBACK_READ, Scope.FEEDBACK_WRITE},
    "ml-inference": {Scope.ML_READ, Scope.ML_WRITE},
    "wazuh-integration": {Scope.TRIAGE_READ, Scope.CORRELATE_WRITE},
}


def get_scopes_for_role(role: Role) -> Set[Scope]:
    return ROLE_SCOPES.get(role, set())


def has_required_scope(user_scopes: list, required: Scope) -> bool:
    return required.value in user_scopes


def get_default_scopes_for_service(service_name: str) -> Set[Scope]:
    return SERVICE_SCOPES.get(service_name, set())
