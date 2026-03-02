"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from pydantic import AliasChoices, Field, field_validator
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings backed by environment variables."""

    # App
    app_name: str = "Vaktram API"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = Field(default="development", description="development | staging | production")

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database (Supabase Postgres)
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/vaktram",
        description="Async SQLAlchemy database URL",
        validation_alias=AliasChoices("DATABASE_URL", "SUPABASE_DB_URL"),
    )
    @field_validator("database_url", mode="after")
    @classmethod
    def _ensure_async_driver(cls, v: str) -> str:
        """Ensure the URL uses the asyncpg driver."""
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    database_pool_size: int = 20
    database_max_overflow: int = 10

    # Supabase
    supabase_url: str = Field(
        default="",
        description="Supabase project URL",
        validation_alias=AliasChoices("SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_URL"),
    )
    supabase_anon_key: str = Field(
        default="",
        description="Supabase anonymous/public key",
        validation_alias=AliasChoices("SUPABASE_ANON_KEY", "NEXT_PUBLIC_SUPABASE_ANON_KEY"),
    )
    supabase_service_role_key: str = Field(default="", description="Supabase service role key")
    supabase_jwt_secret: str = Field(default="", description="Supabase JWT secret for verification")

    # Upstash Redis
    upstash_redis_url: str = Field(default="", description="Upstash Redis REST URL")
    upstash_redis_token: str = Field(default="", description="Upstash Redis REST token")

    # LLM / AI
    default_llm_provider: str = Field(default="gemini", description="Default LLM provider")
    default_llm_model: str = Field(
        default="gemini/gemini-2.0-flash", description="Default LLM model"
    )
    openai_api_key: str = Field(default="", description="OpenAI API key (fallback)")
    google_ai_api_key: str = Field(default="", description="Google AI API key for Gemini")

    # Encryption
    encryption_key: str = Field(default="", description="Fernet encryption key for API key storage")

    # CORS
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:5173",
        description="Comma-separated allowed origins",
    )

    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, description="Requests per minute per user")

    # Bot / Recording
    recall_api_key: str = Field(default="", description="Recall.ai API key for bot control")

    # Calendar
    google_client_id: str = ""
    google_client_secret: str = ""

    # URLs (for OAuth redirect flows)
    api_base_url: str = "http://localhost:8000"
    frontend_base_url: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    model_config = {
        "env_file": (".env", "../../.env"),
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
