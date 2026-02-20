import pymysql
from app.config import Config

def get_db_connection():
    class DictConnection(pymysql.connections.Connection):
        def cursor(self, dictionary=False):
            if dictionary:
                return super().cursor(pymysql.cursors.DictCursor)
            return super().cursor()

    return DictConnection(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        autocommit=False
    )