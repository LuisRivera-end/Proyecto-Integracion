import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DB_HOST = os.getenv("DB_HOST", "mariadb")
    DB_USER = os.getenv("MARIADB_USER")
    DB_PASSWORD = os.getenv("MARIADB_PASSWORD")
    DB_NAME = os.getenv("MARIADB_DATABASE")
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = os.getenv("PORT", 5000)
    DEBUG = os.getenv("DEBUG", True)
    API_BASE_URL = os.getenv("API_BASE_URL", "https://[IP_ADDRESS]")