from enum import Enum
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, model_validator


class BaseConfig(BaseSettings):
    """Базовая модель конфига"""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


class TelegramConfig(BaseConfig):
    """Конфиг телеграма"""

    class Webhook(BaseConfig):
        path: Optional[str] = None
        base_url: Optional[str] = None
        ssl_cert: Optional[str] = None
        ssl_priv: Optional[str] = None

        model_config = SettingsConfigDict(env_prefix="TG_WEBHOOK_")

        @property
        def url(self):
            return f"{self.base_url}{self.path}"

    webhook: Webhook = Field(default_factory=Webhook)
    use_webhook: Optional[bool] = Field(default=False)
    bot_token: str = Field(..., pattern=r"^\d{8,10}:[A-Za-z0-9_-]{35}$")

    model_config = SettingsConfigDict(env_prefix="TG_")

    @model_validator(mode="after")
    def model_validate(self):
        if self.use_webhook and not self.webhook:
            raise ValueError("webhook data must be specified when use_webhook=True")
        return self


class BrokerConfig(BaseConfig):
    scheme: Optional[str] = Field(default="redis")
    host: Optional[str] = Field(default="localhost")
    port: Optional[int] = Field(default=6379)
    vhost: Optional[str] = Field(default="")
    db: Optional[int] = Field(default=0)

    @property
    def url(self) -> str:
        if self.scheme == "redis":
            return f"redis://{self.host}:{self.port}/{self.db}"
        elif self.scheme == "amqp":
            return f"amqp://{self.host}:{self.port}/{self.vhost}"
        raise ValueError("Неподдерживаемый брокер")


class RedisConfig(BrokerConfig):
    """Конфиг Redis"""

    prefix: Optional[str] = Field(default="sub_bot:user:chat_id")

    model_config = SettingsConfigDict(env_prefix="REDIS_")


class CeleryConfig(BaseConfig):
    """Конфиг Celery"""

    class Broker(BrokerConfig):
        model_config = SettingsConfigDict(env_prefix="CELERY_BROKER_")

    broker: Broker = Field(default_factory=Broker)

    model_config = SettingsConfigDict(env_prefix="CELERY_")


class SentryConfig(BaseConfig):
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

    model_config = SettingsConfigDict(env_prefix="SENTRY_")

    @model_validator(mode="after")
    def validate_model(self):
        if self.turned_on and not self.dsn:
            raise ValueError("SENTRY_DSN required when SENTRY_TURNED_ON=True")
        return self


class DBConfig(BaseConfig):
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

    model_config = SettingsConfigDict(env_prefix="DB_")


class Config(BaseConfig):
    telegram: TelegramConfig = Field(default_factory=TelegramConfig)
    celery: CeleryConfig = Field(default_factory=CeleryConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    sentry: SentryConfig = Field(default_factory=SentryConfig)
    db: DBConfig = Field(default_factory=DBConfig)
    debug: Optional[bool] = Field(default=False)


config = Config()
