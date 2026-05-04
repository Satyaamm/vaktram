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

    # Database (Postgres)
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/vaktram",
        description="Async SQLAlchemy database URL",
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

    # Auth / JWT
    jwt_secret: str = Field(
        default="",
        description="Secret key for signing JWTs",
        validation_alias=AliasChoices("JWT_SECRET", "SUPABASE_JWT_SECRET"),
    )

    @field_validator("jwt_secret", mode="after")
    @classmethod
    def _validate_jwt_secret(cls, v: str) -> str:
        # In dev we tolerate empty (auto-generated below); in prod we refuse
        # to boot without an explicit, sufficiently long secret.
        import os

        env = os.getenv("ENVIRONMENT", "development").lower()
        if not v:
            if env == "production":
                raise ValueError(
                    "JWT_SECRET must be set in production. Generate with: "
                    "python -c 'import secrets; print(secrets.token_urlsafe(64))'"
                )
            # Dev fallback: deterministic-per-process random so tokens issued
            # this run remain valid, but they won't survive a restart. This
            # avoids mysterious 401s during local dev without weakening prod.
            import secrets as _s
            return _s.token_urlsafe(64)
        if len(v) < 32:
            raise ValueError(
                f"JWT_SECRET is too short ({len(v)} chars). Use at least 32."
            )
        return v

    # Upstash Redis
    upstash_redis_url: str = Field(default="", description="Upstash Redis REST URL")
    upstash_redis_token: str = Field(default="", description="Upstash Redis REST token")

    # Groq (Whisper transcription)
    groq_api_key: str = Field(default="", description="Groq API key for Whisper transcription")

    # QStash (job queue)
    qstash_token: str = Field(default="", description="Upstash QStash token")
    qstash_current_signing_key: str = Field(default="", description="QStash current signing key")
    qstash_next_signing_key: str = Field(default="", description="QStash next signing key")

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
    bot_service_url: str = Field(default="http://localhost:8001", description="Bot service URL")
    bot_shared_secret: str = Field(
        default="",
        description="Shared secret sent in X-Bot-Auth on every bot-service request",
    )
    diarization_service_url: str = Field(default="http://localhost:8002", description="Diarization service URL")

    # Calendar
    google_client_id: str = ""
    google_client_secret: str = ""

    # URLs (for OAuth redirect flows)
    api_base_url: str = "http://localhost:8000"
    frontend_base_url: str = "http://localhost:3000"

    # Observability
    sentry_dsn: str = Field(default="", description="Sentry DSN; empty disables Sentry")
    sentry_traces_sample_rate: float = 0.1
    otel_exporter_endpoint: str = Field(
        default="",
        description="OTLP/HTTP traces endpoint; empty disables OTel",
    )

    # Billing (Stripe)
    stripe_api_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_pro: str = ""
    stripe_price_team: str = ""
    stripe_price_business: str = ""

    # Email (Resend)
    resend_api_key: str = ""
    resend_from_email: str = "no-reply@vaktram.com"

    # NOTE: Embeddings + LLM are pure BYOM — no platform keys. The user's
    # provider/key is loaded from `user_ai_configs` at request time.

    # Enterprise SSO (WorkOS)
    workos_api_key: str = ""
    workos_client_id: str = ""

    # Region & residency
    region: str = Field(default="us-east-1", description="Deployment region for this instance")
    storage_bucket: str = Field(default="vaktram-audio", description="Object-storage bucket")

    # Compliance
    audit_export_bucket: str = ""  # S3 bucket for hourly audit-log export
    default_retention_days: int = 365  # org may override

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
