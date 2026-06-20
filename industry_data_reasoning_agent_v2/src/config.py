from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Settings:
    app_name: str = "Industry Data Reasoning Agent API"
    runs_dir: str = os.getenv("RUNS_DIR", "runs")
    registry_db: str = os.getenv("REGISTRY_DB", "runs/registry.db")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # Simple API keys for prototype-level RBAC.
    # In production, replace this with OAuth/Auth0/Keycloak/company SSO.
    admin_api_key: str = os.getenv("ADMIN_API_KEY", "admin-dev-key")
    analyst_api_key: str = os.getenv("ANALYST_API_KEY", "analyst-dev-key")
    viewer_api_key: str = os.getenv("VIEWER_API_KEY", "viewer-dev-key")


def get_settings() -> Settings:
    return Settings()
