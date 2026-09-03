from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    taiga_url: str = ""
    taiga_username: str = ""
    taiga_password: str = ""

    kimai_url: str = ""
    kimai_token: str = ""

    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
