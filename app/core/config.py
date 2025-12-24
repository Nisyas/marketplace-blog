from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from loguru import logger


class Settings(BaseSettings):
    app_env: str = "local"
    app_debug: bool = True

    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str = "db"
    postgres_port: int = 5432
    database_url: str
    alembic_database_url: str | None = None

    rabbitmq_host: str = "rabbitmq"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "guest"
    rabbitmq_password: str = "guest"
    celery_broker_url: str
    celery_result_backend: str

    s3_endpoint_url: str
    s3_access_key: str
    s3_secret_key: str
    s3_bucket_name: str
    s3_region: str = "us-east-1"

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expires_minutes: int = 60

    smtp_host: str
    smtp_port: int = 587
    smtp_user: str
    smtp_password: str
    smtp_use_tls: bool = True
    email_from: str

    log_level: str = "DEBUG"
    log_dir: str = "logs"
    log_rotation: str = "10 MB"
    log_retention: str = "14 days"
    log_compression: str = "zip"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


def configure_logger(settings: Settings) -> None:
    logger.remove()

    log_path = Path(settings.log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    )

    logger.add(
        sink=lambda msg: print(msg, end=""),
        level=settings.log_level if settings.app_debug else "INFO",
        format=log_format,
        backtrace=settings.app_debug,
        diagnose=settings.app_debug,
    )

    logger.add(
        str(log_path / "app.log"),
        rotation=settings.log_rotation,
        retention=settings.log_retention,
        compression=settings.log_compression,
        level=settings.log_level if settings.app_debug else "INFO",
        format=log_format,
        enqueue=True,
    )


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    configure_logger(settings)
    logger.info(
        "Settings loaded: env={env}, debug={debug}",
        env=settings.app_env,
        debug=settings.app_debug,
    )
    return settings
