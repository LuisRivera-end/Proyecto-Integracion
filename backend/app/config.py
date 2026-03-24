from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    DB_HOST: str = "127.0.0.1"
    MARIADB_USER: str
    MARIADB_PASSWORD: str
    MARIADB_DATABASE: str
    
    HOST: str = "0.0.0.0"
    PORT: int = 5000
    DEBUG: bool = True
    
    SECRET_KEY: str
    SESSION_RESET_PIN: str = "00000"
    
    model_config = ConfigDict(env_file=("../.env", ".env"), extra="ignore")

settings = Settings()

# Construir URL de SQLAlchemy
DATABASE_URL = f"mysql+asyncmy://{settings.MARIADB_USER}:{settings.MARIADB_PASSWORD}@{settings.DB_HOST}/{settings.MARIADB_DATABASE}"