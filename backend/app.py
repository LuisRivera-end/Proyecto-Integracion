# backend/app.py
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello_world():
    return '¡Backend de Python Funcionando!'

if __name__ == '__main__':
    # Es posible que tu Dockerfile inicie la app con Gunicorn/Waitress, 
    # pero este código es suficiente para la lógica
    app.run(host='0.0.0.0', port=5000)