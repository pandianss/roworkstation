from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from src.core.paths import project_path


class AppSettings(BaseModel):
    environment: str = Field(default="development")
    app_title: str = Field(default="RO Workstation")
    app_description: str = Field(
        default="Offline-first regional office banking workstation for MIS analytics, operations, compliance returns, document generation, and knowledge management."
    )
    app_keywords: str = Field(
        default="regional office banking workstation, MIS analytics, compliance returns, office note generator, bank operations dashboard"
    )
    public_url: str = Field(default="")
    offline_mode: bool = Field(default=True)
    admin_password: str = Field(default="admin")
    max_tasks_displayed: int = Field(default=100)
    region_code: str = Field(default="3933")
    session_timeout_hours: int = Field(default=4)


def _load_json_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def get_app_settings() -> AppSettings:
    """Load environment-aware settings from data config and env vars."""
    data = _load_json_file(project_path("data", "config.json"))
    env_aliases = {
        "RO_ENVIRONMENT": "environment",
        "RO_APP_TITLE": "app_title",
        "RO_APP_DESCRIPTION": "app_description",
        "RO_APP_KEYWORDS": "app_keywords",
        "RO_PUBLIC_URL": "public_url",
        "RO_OFFLINE_MODE": "offline_mode",
        "RO_ADMIN_PASSWORD": "admin_password",
        "RO_MAX_TASKS_DISPLAYED": "max_tasks_displayed",
        "RO_REGION_CODE": "region_code",
        "RO_SESSION_TIMEOUT_HOURS": "session_timeout_hours",
    }
    env_path = project_path(".env")
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if "=" not in line or line.strip().startswith("#"):
                continue
            key, value = line.split("=", 1)
            env_key = key.strip()
            config_key = env_aliases.get(env_key.upper(), env_key.lower())
            data[config_key] = value.strip()

    for env_key, config_key in env_aliases.items():
        if env_key in os.environ:
            data[config_key] = os.environ[env_key]

    normalized = {
        "environment": data.get("environment", data.get("env", "development")),
        "app_title": data.get("app_title", "RO Workstation"),
        "app_description": data.get(
            "app_description",
            "Offline-first regional office banking workstation for MIS analytics, operations, compliance returns, document generation, and knowledge management.",
        ),
        "app_keywords": data.get(
            "app_keywords",
            "regional office banking workstation, MIS analytics, compliance returns, office note generator, bank operations dashboard",
        ),
        "public_url": data.get("public_url", ""),
        "offline_mode": str(data.get("offline_mode", "true")).lower() == "true",
        "admin_password": data.get("admin_password", "admin"),
        "max_tasks_displayed": int(data.get("max_tasks_displayed", 100)),
        "region_code": str(data.get("region_code", "3933")),
        "session_timeout_hours": int(data.get("session_timeout_hours", 4)),
    }
    return AppSettings.model_validate(normalized)


@lru_cache(maxsize=16)
def load_yaml_config(name: str) -> dict[str, Any]:
    """Load and cache YAML configuration from the config directory."""
    path = project_path("src", "config", name)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, dict):
        raise ValueError(f"Expected mapping config in {path}")
    return loaded


def load_yaml(path: str) -> dict[str, Any]:
    """Compatibility wrapper for load_yaml_config."""
    name = path.split("/")[-1]
    return load_yaml_config(name)
