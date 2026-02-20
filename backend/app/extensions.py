# app/extensions.py
from flask_socketio import SocketIO

# Al dejar async_mode=None o quitarlo, Flask-SocketIO detectará 
# que estás usando el worker de gevent de Gunicorn automáticamente.
socketio = SocketIO(cors_allowed_origins="*", async_mode='gevent', manage_session=False)