from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path
from typing import Optional


class Settings(BaseSettings):
    """Application configuration using environment variables."""

    GITHUB_TOKEN: Optional[str] = Field(None, env="GITHUB_TOKEN")
    OPENAI_API_KEY: Optional[str] = Field(None, env="OPENAI_API_KEY")
    REPO_BASE_PATH: Path = Field(Path("./repos"), env="REPO_BASE_PATH")
    CLONE_TIMEOUT: int = Field(60, env="CLONE_TIMEOUT")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
