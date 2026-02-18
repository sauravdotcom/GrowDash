import os
from typing import List

from dotenv import load_dotenv


load_dotenv()


class Settings:
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/growdash",
    )
    api_v1_prefix: str = os.getenv("API_V1_PREFIX", "/api/v1")
    cors_origins: List[str] = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:4000,http://127.0.0.1:4000").split(",")
        if origin.strip()
    ]
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


settings = Settings()
