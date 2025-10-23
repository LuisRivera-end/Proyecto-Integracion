from app import create_app, socketio
from app.config import Config

app, socketio_instance = create_app()

if __name__ == '__main__':
    
    socketio_instance.run(
        app, 
        host=Config.HOST, 
        port=Config.PORT, 
        debug=Config.DEBUG,
        allow_unsafe_werkzeug=True
    )