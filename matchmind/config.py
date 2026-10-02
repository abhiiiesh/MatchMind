"""Configuration management for MatchMind platform."""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    """Application settings with environment variable overrides."""
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # General
    app_name: str = "MatchMind"
    environment: str = "development"
    log_level: str = "INFO"
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    # Storage Paths
    base_dir: Path = BASE_DIR
    data_dir: Path = BASE_DIR / "data"
    cache_dir: Path = BASE_DIR / "data" / "cache"

    # Simulation & Streaming
    stream_interval_seconds: float = 1.0
    default_match_id: str = "3869685"  # Sample match ID (e.g. World Cup / historic PL)

    # Azure OpenAI
    azure_openai_endpoint: Optional[str] = None
    azure_openai_api_key: Optional[str] = None
    azure_openai_api_version: str = "2024-08-01-preview"
    azure_openai_gpt4o_deployment: str = "gpt-4o"
    azure_openai_gpt4o_mini_deployment: str = "gpt-4o-mini"

    # Azure Cosmos DB
    azure_cosmos_endpoint: Optional[str] = None
    azure_cosmos_key: Optional[str] = None
    azure_cosmos_database: str = "matchmind"

    # Azure AI Speech
    azure_speech_key: Optional[str] = None
    azure_speech_region: str = "eastus"

    # Azure AI Translator
    azure_translator_key: Optional[str] = None
    azure_translator_region: str = "eastus"
    azure_translator_endpoint: str = "https://api.cognitive.microsofttranslator.com/"

    @property
    def has_azure_openai(self) -> bool:
        """Check if Azure OpenAI credentials are configured."""
        return bool(self.azure_openai_endpoint and self.azure_openai_api_key)

    @property
    def has_azure_cosmos(self) -> bool:
        """Check if Azure Cosmos credentials are configured."""
        return bool(self.azure_cosmos_endpoint and self.azure_cosmos_key)

settings = Settings()
# Ensure cache directory exists
settings.cache_dir.mkdir(parents=True, exist_ok=True)
