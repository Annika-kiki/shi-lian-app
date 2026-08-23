from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./shi_lian.db")
    cors_origins: str = os.getenv("CORS_ORIGINS", "*")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    wechat_app_id: str = os.getenv("WECHAT_APP_ID", "")
    wechat_app_secret: str = os.getenv("WECHAT_APP_SECRET", "")


settings = Settings()
