from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SOARM_", env_file=".env", extra="ignore", populate_by_name=True
    )

    # Honour the documented SOARM_API_TOKEN name rather than SOARM_TOKEN.
    token: str = Field(default="", validation_alias="SOARM_API_TOKEN")
    host: str = "127.0.0.1"
    port: int = 7860
    config_path: str = "configs/arms.yaml"
    allow_localhost_no_auth: bool = False
    cors_origins: list[str] = []


@lru_cache
def get_settings() -> Settings:
    return Settings()
