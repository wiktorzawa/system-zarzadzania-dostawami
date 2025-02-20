from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from .config import config

db = SQLAlchemy()

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Konfiguracja aplikacji
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Inicjalizacja bazy danych
    db.init_app(app)

    # Konfiguracja CSP
    @app.after_request
    def add_security_headers(response):
        if response.mimetype == 'text/html':
            response.headers['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: blob:; "
                "font-src 'self' data:; "
                "connect-src 'self'"
            )
        return response
    
    # Tworzenie tabel w kontekście aplikacji
    with app.app_context():
        from .models.MAIN.user import User
        from .models.supplier.supplier import Supplier
        from .models.staff.staff import Staff
        
        db.create_all()
    
    # Inicjalizacja routingu
    from .routes import init_app as init_routes
    init_routes(app)
    
    return app 