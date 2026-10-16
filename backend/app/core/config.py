from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "EvalAI"
    database_url: str = "sqlite:///./evalai.db"
    mock_mode: bool = True
    cors_origins: str = "http://localhost:5173"
    max_concurrency: int = 8
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def origins(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()

