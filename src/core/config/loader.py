import os
from pathlib import Path
from typing import Optional, Dict, Any
import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, BaseModel

class AppConfig(BaseModel):
    title: str = "RO Workstation"
    icon: str = ":bank:"
    layout: str = "wide"
    offline_mode: bool = True

class OllamaConfig(BaseModel):
    model: str = "mistral"
    host: str = "http://localhost:11434"

class SMTPConfig(BaseModel):
    host: str = "mailserver.banklan"
    port: int = 25

class Settings(BaseSettings):
    app: AppConfig = AppConfig()
    ollama: OllamaConfig = OllamaConfig()
    smtp: SMTPConfig = SMTPConfig()
    
    # Paths
    base_dir: Path = Path(__file__).parent.parent.parent
    data_dir: Path = base_dir / "data"
    mis_dir: Path = base_dir / "mis"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        extra="ignore"
    )

def load_yaml_config(file_path: Path) -> Dict[str, Any]:
    if not file_path.exists():
        return {}
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

# Global settings instance
settings = Settings()

# Helper to load specific department configs
def get_dept_config() -> Dict[str, Any]:
    path = settings.base_dir / "config" / "dept_config.yaml"
    return load_yaml_config(path)
