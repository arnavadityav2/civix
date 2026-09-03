import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    civix_database_url: str = ""
    civix_jwt_secret: str = ""
    
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

if not settings.civix_database_url:
    raise ValueError("CIVIX_DATABASE_URL environment variable is missing. Halting API startup.")

if not settings.civix_database_url.startswith("postgresql+asyncpg://"):
    raise ValueError("CIVIX_DATABASE_URL must use the postgresql+asyncpg driver.")

if not settings.civix_jwt_secret:
    raise ValueError("CIVIX_JWT_SECRET environment variable is missing. Halting API startup.")
