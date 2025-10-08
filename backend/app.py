# backend/app.py
from flask import Flask
import mysql.connector
import os

app = Flask(__name__)

conn = mysql.connector.connect(
    host=os.getenv("DB_HOST", "mariadb"),
    user=os.getenv("DB_USER", "turnoadmin"),
    password=os.getenv("DB_PASSWORD", "13Demayo!"),
    database=os.getenv("DB_NAME", "TurnosUal")
)

@app.route('/')
def hello_world():
    return '¡Backend de Python Funcionando!'

if __name__ == '__main__':
    # Es posible que tu Dockerfile inicie la app con Gunicorn/Waitress, 
    # pero este código es suficiente para la lógica
    app.run(host='0.0.0.0', port=5000)