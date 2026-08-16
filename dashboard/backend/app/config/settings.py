import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "SarmayaSaaz API"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    DATA_MODE: str = os.getenv("DATA_MODE", "mock")
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001"
    ]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
