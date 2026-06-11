from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

# 进行配置的集中管理
class Settings(BaseSettings):
    service_name: str = "enterprise-rag-copilot"
    service_version: str = "0.1.0"
    environment: str = "development"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="APP_",
        extra="ignore",
    )

# 只创建一次
@lru_cache
def get_settings() -> Settings:
    return Settings()
