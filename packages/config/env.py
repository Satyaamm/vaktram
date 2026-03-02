"""
Shared environment configuration.
Loads and validates environment variables used across all services.
"""

import os
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


@dataclass
class SupabaseConfig:
    url: str = field(default_factory=lambda: os.getenv("SUPABASE_URL", ""))
    anon_key: str = field(default_factory=lambda: os.getenv("SUPABASE_ANON_KEY", ""))
    service_role_key: str = field(default_factory=lambda: os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""))
    jwt_secret: str = field(default_factory=lambda: os.getenv("SUPABASE_JWT_SECRET", ""))

    def validate(self) -> None:
        if not self.url:
            raise ValueError("SUPABASE_URL is required")
        if not self.service_role_key:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY is required")


@dataclass
class LLMConfig:
    model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "gpt-4o-mini"))
    api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    temperature: float = field(default_factory=lambda: float(os.getenv("LLM_TEMPERATURE", "0.3")))
    max_tokens: int = field(default_factory=lambda: int(os.getenv("LLM_MAX_TOKENS", "2048")))
    base_url: Optional[str] = field(default_factory=lambda: os.getenv("LLM_BASE_URL"))


@dataclass
class BotServiceConfig:
    port: int = field(default_factory=lambda: int(os.getenv("BOT_SERVICE_PORT", "8100")))
    max_concurrent_bots: int = field(default_factory=lambda: int(os.getenv("MAX_CONCURRENT_BOTS", "10")))
    headless: bool = field(default_factory=lambda: os.getenv("HEADLESS", "true").lower() == "true")
    pulse_monitor_source: str = field(default_factory=lambda: os.getenv("PULSE_MONITOR_SOURCE", "vaktram_sink.monitor"))


@dataclass
class WorkerConfig:
    poll_interval: int = field(default_factory=lambda: int(os.getenv("POLL_INTERVAL_SECONDS", "5")))
    whisper_model: str = field(default_factory=lambda: os.getenv("WHISPER_MODEL", "large-v3"))
    compute_device: str = field(default_factory=lambda: os.getenv("COMPUTE_DEVICE", "auto"))
    hf_token: str = field(default_factory=lambda: os.getenv("HF_TOKEN", ""))


@dataclass
class AppConfig:
    env: str = field(default_factory=lambda: os.getenv("ENV", "development"))
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    api_base_url: str = field(default_factory=lambda: os.getenv("API_BASE_URL", "http://localhost:8000"))
    web_base_url: str = field(default_factory=lambda: os.getenv("WEB_BASE_URL", "http://localhost:3000"))

    supabase: SupabaseConfig = field(default_factory=SupabaseConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    bot_service: BotServiceConfig = field(default_factory=BotServiceConfig)
    worker: WorkerConfig = field(default_factory=WorkerConfig)

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    @property
    def is_development(self) -> bool:
        return self.env == "development"


# Singleton config instance
config = AppConfig()
