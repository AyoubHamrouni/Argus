"""
Configuration - Correlation Engine Service
AI-Augmented SOC

Environment-based configuration for alert correlation and incident management.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Service Identity
    service_name: str = "correlation-engine"
    service_version: str = "1.0.0"

    # Database
    database_url: str = "postgresql+asyncpg://argus:argus_password@postgres:5432/argus"

    # Correlation Tuning
    temporal_window_minutes: int = 15
    correlation_threshold: float = 0.6
    incident_auto_close_minutes: int = 60

    # Attack Campaign Simulator
    simulator_enabled: bool = True
    simulator_ollama_host: str = "http://ollama:11434"
    simulator_ollama_model: str = "llama3.2:3b"
    simulator_default_timesteps: int = 3
    simulator_default_concurrency: int = 3
    simulator_environment_config: str = ""

    # Wazuh Environment Auto-Population
    wazuh_api_url: str = "https://wazuh-manager:55000"
    wazuh_api_username: str = "wazuh-wui"
    wazuh_api_password: str = ""  # From CORRELATION_WAZUH_API_PASSWORD
    wazuh_api_verify_ssl: bool = False

    # Response Orchestrator Integration
    response_orchestrator_url: str = "http://response-orchestrator:8000"
    auto_defend_enabled: bool = True
    auto_defend_min_severity: str = "high"  # Minimum severity to trigger defense

    # Security
    api_key_enabled: bool = True
    api_key: str | None = None

    # Logging / Server
    log_level: str = "INFO"
    host: str = "0.0.0.0"
    port: int = 8000

    class Config:
        env_prefix = "CORRELATION_"


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()
