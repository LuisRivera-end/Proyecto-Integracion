import gevent.monkey
gevent.monkey.patch_all()

from flask import Flask
from .extensions import socketio  # <--- Esto trae el objeto ya creado
from flask_cors import CORS
from flask_session import Session
from werkzeug.middleware.proxy_fix import ProxyFix

# Importar Blueprints
from app.routes.health import bp as health_bp
from app.routes.auth import bp as auth_bp
from app.routes.tickets import bp as tickets_bp
from app.routes.employees import bp as employees_bp
from app.routes.ventanillas import bp as ventanillas_bp

from app.websocket.print_handlers import register_socket_handlers

# ELIMINA LA LÍNEA: socketio = SocketIO(...) 
# No la necesitas aquí porque ya la importaste arriba desde .extensions

def create_app():
    app = Flask(__name__)
    
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    app.config['SECRET_KEY'] = 'B7v!q9#pLz2&XkR8@fH4$yT1*mN6^sD0'
    app.config['SESSION_TYPE'] = 'filesystem'
    Session(app)
    
    # Configuración CORS
    CORS(app, 
        resources={r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }}
    )
    
    # Inicializar el socket con la app
    socketio.init_app(app)
    
    # Registrar handlers y obtener la función de impresión
    send_print_job = register_socket_handlers(socketio)
    
    # Hacer disponible la función para otros módulos
    app.config['SEND_PRINT_JOB'] = send_print_job
    
    # Registrar blueprints    
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(tickets_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(ventanillas_bp)
    
    return app, socketio