from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    
    # Configuración CORS
    CORS(app, 
        resources={r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }}
    )
    
    # Registrar blueprints
    from app.routes.health import bp as health_bp
    from app.routes.auth import bp as auth_bp
    from app.routes.tickets import bp as tickets_bp
    from app.routes.employees import bp as employees_bp
    from app.routes.ventanillas import bp as ventanillas_bp
    
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(tickets_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(ventanillas_bp)
    
    return app