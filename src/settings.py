from enum import Enum
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, model_validator, BaseModel


class TelegramConfig(BaseModel):
    """Конфиг телеграма"""

    class Webhook(BaseModel):
        path: Optional[str] = None
        base_url: Optional[str] = None
        ssl_cert: Optional[str] = None
        ssl_priv: Optional[str] = None

        model_config = SettingsConfigDict(env_prefix="TG_WEBHOOK_")

        @property
        def url(self) -> str:
            return f"{self.base_url}{self.path}"

    webhook: Webhook = Field(default_factory=Webhook)
    use_webhook: Optional[bool] = Field(default=False)
    bot_token: str = Field(..., pattern=r"^\d{8,10}:[A-Za-z0-9_-]{35}$")

    model_config = SettingsConfigDict(env_prefix="TG_")

    @model_validator(mode="after")
    def validate_webhook(self) -> "TelegramConfig":
        if self.use_webhook and not self.webhook:
            raise ValueError("webhook data must be specified when use_webhook=True")
        return self


class RedisConfig(BaseModel):
    """Конфиг Redis"""

    host: Optional[str] = Field(default="localhost")
    port: Optional[int] = Field(default=6379)
    db: Optional[int] = Field(default=0)

    prefix: Optional[str] = Field(default="sub_bot:user:chat_id")

    @property
    def url(self) -> str:
        return f"redis://{self.host}:{self.port}/{self.db}"


class SentryConfig(BaseModel):
    """Конфиг Sentry"""

    class SentryEnvironment(str, Enum):
        production = "production"
        development = "development"

    turned_on: Optional[bool] = Field(default=True)

    dsn: Optional[str] = None
    environment: Optional[SentryEnvironment] = Field(default=SentryEnvironment.production)
    traces_sample_rate: Optional[float] = Field(default=0.0)
    profiles_sample_rate: Optional[float] = Field(default=0.0)
    sample_rate: Optional[float] = Field(default=1.0)

    @model_validator(mode="after")
    def validate_dsn(self) -> "SentryConfig":
        if self.turned_on and not self.dsn:
            raise ValueError("SENTRY_DSN required when SENTRY_TURNED_ON=True")
        return self


class DBConfig(BaseModel):
    """Конфиг базы данных"""

    engine: Optional[str] = Field(default="postgresql+asyncpg")
    user: str
    password: str
    host: Optional[str] = Field(default="localhost")
    port: Optional[int] = Field(default=5432)
    database: str

    @property
    def url(self) -> str:
        return (
            f"{self.engine}://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
        )


class Config(BaseSettings):
    telegram: TelegramConfig = Field(default_factory=TelegramConfig) # type: ignore[arg-type]
    redis: RedisConfig = Field(default_factory=RedisConfig)
    sentry: SentryConfig = Field(default_factory=SentryConfig)
    db: DBConfig = Field(default_factory=DBConfig) # type: ignore[arg-type]
    debug: Optional[bool] = Field(default=False)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_nested_delimiter="__",
    )


config = Config()
