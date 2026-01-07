from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PORT: int
    HOST: str
    
    DATABASE_URL: str
    SECRET_KEY: str
    
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str
    S3_ENDPOINT_URL: str
    S3_BUCKET_NAME: str
    
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Scriptorium"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
settings = Settings()