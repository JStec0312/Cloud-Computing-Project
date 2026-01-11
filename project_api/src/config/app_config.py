from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional
import os
MODE = "production"
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)
    db_user: str 
    db_pass: str
    db_name: str
    db_host: str 
    db_port: int 
    app_port: int
    db_url:str
    db_url_sync: str 
    # JWT Settings
    jwt_secret: str
    jwt_algorithm: str
    jwt_expiration_minutes: int 
    jwt_refresh_expiration_days: int
    token_pepper: str
    #AWS
    storage_type:str
    s3_bucket: str
    s3_region: str | None = None
    aws_access_key_id: str
    aws_secret_access_key: str

    #cookies
    refresh_cookie_name: str = "refresh_token"
    httponly_cookie: bool = True
    secure_cookie: bool = True if MODE == "production" else False
    samesite_cookie: str = "None" if MODE == "production" else "lax"

    cookie_refresh_path: str = "/auth/refresh"

    max_age_cookie: int = 30 * 24 * 60 * 60  # 30 days in seconds

    # Local storage path
    local_storage_path:str = "./local_storage_data"
    max_file_upload_size_mb: int = 500  # 500 MB

    # Rate limiting
    STANDARD_RATE_LIMIT: str = "2000/minute" # Adjusted for local testing change in dev


    def dsn_async(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_pass}@{self.db_host}:{self.db_port}/{self.db_name}" if not self.db_url else self.db_url
    
    def dsn_sync(self) -> str:
        return self.db_url_sync or (
            f"postgresql://{self.db_user}:{self.db_pass}@{self.db_host}:{self.db_port}/{self.db_name}"
        )
settings = Settings()