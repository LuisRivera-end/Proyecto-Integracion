import os

class Config:
    DB_HOST = os.getenv("DB_HOST", "mariadb")
    DB_USER = os.getenv("DB_USER", "turnoadmin")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "13Demayo!")
    DB_NAME = os.getenv("DB_NAME", "TurnosUal")
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = os.getenv("PORT", 5000)
    DEBUG = os.getenv("DEBUG", True)