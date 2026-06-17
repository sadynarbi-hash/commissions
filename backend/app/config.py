from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/nma_primes"

    SAP_DB_TYPE: str = "sqlserver"
    SAP_SERVER: Optional[str] = None
    SAP_DATABASE: Optional[str] = None
    SAP_USERNAME: Optional[str] = None
    SAP_PASSWORD: Optional[str] = None
    SAP_PORT: int = 1433
    SAP_DRIVER: str = "ODBC Driver 18 for SQL Server"
    SAP_HANA_HOST: Optional[str] = None
    SAP_HANA_PORT: int = 39015
    SAP_HANA_USER: Optional[str] = None
    SAP_HANA_PASSWORD: Optional[str] = None

    SF_CLIENT_ID: Optional[str] = None
    SF_CLIENT_SECRET: Optional[str] = None
    SF_DOMAIN: str = "login"

    APP_SECRET_KEY: str = "dev-secret-key"
    ENVIRONMENT: str = "development"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
