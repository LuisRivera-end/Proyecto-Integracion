from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    DB_HOST: str = "mariadb"
    MARIADB_USER: str = "root"
    MARIADB_PASSWORD: str = ""
    MARIADB_DATABASE: str = "ual_db"
    
    HOST: str = "0.0.0.0"
    PORT: int = 5000
    DEBUG: bool = True
    
    SECRET_KEY: str = "B7v!q9#pLz2&XkR8@fH4$yT1*mN6^sD0"
    
    model_config = ConfigDict(env_file=".env", extra="ignore")

settings = Settings()

# Construir URL de SQLAlchemy
DATABASE_URL = f"mysql+asyncmy://{settings.MARIADB_USER}:{settings.MARIADB_PASSWORD}@{settings.DB_HOST}/{settings.MARIADB_DATABASE}"