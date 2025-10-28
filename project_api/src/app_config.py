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

    

    
    def dsn_async(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_pass}@{self.db_host}:{self.db_port}/{self.db_name}"

settings = Settings()