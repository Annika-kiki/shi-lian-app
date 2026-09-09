from dataclasses import dataclass
import os
import re
from urllib.parse import quote_plus, urlparse
from dotenv import load_dotenv

load_dotenv()


def database_url_from_env() -> str:
    explicit_url = os.getenv("DATABASE_URL", "").strip()
    if explicit_url:
        return explicit_url
    address = os.getenv("MYSQL_ADDRESS", "").strip()
    username = os.getenv("MYSQL_USERNAME", "").strip()
    password = os.getenv("MYSQL_PASSWORD", "")
    database = os.getenv("MYSQL_DATABASE", "tcb").strip()
    host, separator, port = address.rpartition(":")
    if address and username and password and database and separator and host and port.isdigit():
        return (
            f"mysql+pymysql://{quote_plus(username)}:{quote_plus(password)}@"
            f"{host}:{port}/{quote_plus(database)}?charset=utf8mb4"
        )
    return "sqlite:///./shi_lian.db"


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "development").lower()
    database_url: str = database_url_from_env()
    cors_origins: str = os.getenv("CORS_ORIGINS", "*")
    allowed_hosts: str = os.getenv("ALLOWED_HOSTS", "*")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    auth_mode: str = os.getenv("AUTH_MODE", "wechat_api").lower()
    wechat_app_id: str = os.getenv("WECHAT_APP_ID", "")
    wechat_app_secret: str = os.getenv("WECHAT_APP_SECRET", "")
    wechat_cloud_env_id: str = os.getenv("WECHAT_CLOUD_ENV_ID", "")
    session_secret: str = os.getenv("SESSION_SECRET", "development-only-change-me")
    session_ttl_seconds: int = int(os.getenv("SESSION_TTL_SECONDS", "604800"))
    sensitive_rate_limit_per_minute: int = int(os.getenv("SENSITIVE_RATE_LIMIT_PER_MINUTE", "30"))

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_deployed(self) -> bool:
        return self.app_env in {"staging", "production"}


settings = Settings()

VALID_APP_ENVS = {"development", "staging", "production"}
VALID_LOG_LEVELS = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}
VALID_AUTH_MODES = {"wechat_api", "cloud_headers"}
WECHAT_APP_ID_PATTERN = re.compile(r"^wx[0-9a-f]{16}$")
WECHAT_CLOUD_ENV_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{2,63}$")


def _csv_values(raw: str) -> list[str]:
    return [value.strip() for value in raw.split(",") if value.strip()]


def validate_production_settings(value: Settings = settings) -> None:
    if value.app_env not in VALID_APP_ENVS:
        raise RuntimeError(f"Invalid APP_ENV: {value.app_env}")
    if value.log_level.upper() not in VALID_LOG_LEVELS:
        raise RuntimeError(f"Invalid LOG_LEVEL: {value.log_level}")
    if value.auth_mode not in VALID_AUTH_MODES:
        raise RuntimeError(f"Invalid AUTH_MODE: {value.auth_mode}")
    if not 300 <= value.session_ttl_seconds <= 2_592_000:
        raise RuntimeError("SESSION_TTL_SECONDS must be between 300 and 2592000")
    if not 1 <= value.sensitive_rate_limit_per_minute <= 600:
        raise RuntimeError("SENSITIVE_RATE_LIMIT_PER_MINUTE must be between 1 and 600")
    if not value.is_deployed:
        return
    errors = []
    if len(value.session_secret) < 32 or value.session_secret == "development-only-change-me":
        errors.append("SESSION_SECRET must be a unique value of at least 32 characters")
    if not WECHAT_APP_ID_PATTERN.fullmatch(value.wechat_app_id):
        errors.append("WECHAT_APP_ID must be a valid mini program AppID")
    if value.auth_mode == "wechat_api" and len(value.wechat_app_secret) < 16:
        errors.append("WECHAT_APP_SECRET is required for AUTH_MODE=wechat_api and appears too short")
    if value.auth_mode == "cloud_headers" and not WECHAT_CLOUD_ENV_PATTERN.fullmatch(value.wechat_cloud_env_id):
        errors.append("WECHAT_CLOUD_ENV_ID is required for AUTH_MODE=cloud_headers")
    if not value.database_url.startswith("mysql+pymysql://"):
        errors.append("deployed DATABASE_URL must use mysql+pymysql")

    cors_origins = _csv_values(value.cors_origins)
    if not cors_origins or any(
        origin == "*"
        or (parsed := urlparse(origin)).scheme != "https"
        or not parsed.netloc
        or parsed.path not in {"", "/"}
        or parsed.params
        or parsed.query
        or parsed.fragment
        for origin in cors_origins
    ):
        errors.append("deployed CORS_ORIGINS must contain only HTTPS origins without paths")

    allowed_hosts = _csv_values(value.allowed_hosts)
    if not allowed_hosts or any(
        "*" in host
        or "://" in host
        or "/" in host
        or any(character.isspace() for character in host)
        for host in allowed_hosts
    ):
        errors.append("deployed ALLOWED_HOSTS must contain hostnames without wildcards, schemes or paths")
    if errors:
        raise RuntimeError("Unsafe deployed configuration: " + "; ".join(errors))
