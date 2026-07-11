"""
Configuration - Feedback Service
AI-Augmented SOC
"""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    service_name: str = "feedback-service"
    service_version: str = "1.0.0"
    database_url: str = "postgresql+asyncpg://argus:argus_password@postgres:5432/argus"
    log_level: str = "INFO"
    host: str = "0.0.0.0"
    port: int = 8000

    # Pagination defaults
    default_page_size: int = 50
    max_page_size: int = 200

    # Security
    api_key_enabled: bool = True
    api_key: str | None = None

    class Config:
        env_prefix = "FEEDBACK_"
        env_file = ".env"
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Support Docker secrets via _FILE suffix
        for field_name in self.model_fields.keys():
            env_var = f"{self.Config.env_prefix}{field_name.upper()}_FILE"
            if os.getenv(env_var):
                try:
                    with open(os.getenv(env_var), 'r') as f:
                        setattr(self, field_name, f.read().strip())
                except Exception as e:
                    pass
