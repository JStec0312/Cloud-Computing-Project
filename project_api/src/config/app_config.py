from pydantic_settings import BaseSettings, SettingsConfigDict
import os
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)
    db_user: str 
    db_pass: str
    db_name: str
    db_host: str 
    db_port: int 
    app_port: int
    # JWT Settings
    jwt_secret: str
    jwt_algorithm: str
    jwt_expiration_minutes: int 
    jwt_refresh_expiration_days: int
    token_pepper: str
    #cookies
    refresh_cookie_name: str = "refresh_token"
    httponly_cookie: bool = True
    secure_cookie: bool = False
    samesite_cookie: str = "Lax"

    cookie_refresh_path: str = "/auth/refresh"

    max_age_cookie: int = 30 * 24 * 60 * 60  # 30 days in seconds

    # Local storage path
    local_storage_path:str = "./local_storage_data"
    max_file_upload_size_mb: int = 500  # 500 MB

    # Rate limiting
    STANDARD_RATE_LIMIT: str = "5/minute"

    def dsn_async(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_pass}@{self.db_host}:{self.db_port}/{self.db_name}"

settings = Settings()