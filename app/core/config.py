import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # Telegram Bot Configuration
    telegram_bot_token: str = Field(..., env="TELEGRAM_BOT_TOKEN")
    webhook_url: Optional[str] = Field(None, env="WEBHOOK_URL")

    # Database Configuration
    database_url: Optional[str] = Field(None, env="DATABASE_URL")
    db_host: str = Field(default="mysql", env="DB_HOST")
    db_port: int = Field(default=3306, env="DB_PORT")
    db_name: str = Field(default="telegram_bot", env="DB_NAME")
    db_user: str = Field(default="root", env="DB_USER")
    db_password: str = Field(default="root", env="DB_PASSWORD")

    # Application Configuration
    app_name: str = "Telefonchi.UZ Bot"
    app_version: str = "2.0.0"
    debug: bool = Field(default=False, env="DEBUG")

    # Business Configuration
    advertisement_price: int = Field(default=30000, env="AD_PRICE")
    payment_card_number: str = Field(default="1234 5678 9012 3456", env="PAYMENT_CARD")

    # Mini App Configuration
    mini_app_url: str = Field(default="https://your-miniapp-domain.com", env="MINI_APP_URL")

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # File Upload
    upload_dir: str = Field(default="uploads", env="UPLOAD_DIR")
    max_file_size: int = Field(default=10 * 1024 * 1024, env="MAX_FILE_SIZE")  # 10MB

    @property
    def database_url_async(self) -> str:
        return f"mysql+aiomysql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()