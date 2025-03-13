# Plik inicjalizacyjny pakietu
# Może pozostać pusty, ponieważ cała logika inicjalizacji jest w app.py 

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import config
import logging
from sqlalchemy import event

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Inicjalizacja rozszerzeń
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

# Funkcje obsługi zdarzeń SQLAlchemy
def checkout_listener(dbapi_connection, connection_record, connection_proxy):
    """Monitoruje pobranie połączenia z puli."""
    logger.debug("Połączenie pobrane z puli")

def checkin_listener(dbapi_connection, connection_record):
    """Monitoruje zwrot połączenia do puli."""
    logger.debug("Połączenie zwrócone do puli")

def connect_listener(dbapi_connection, connection_record):
    """Monitoruje utworzenie nowego połączenia."""
    logger.debug("Nowe połączenie utworzone")

def close_listener(dbapi_connection, connection_record):
    """Monitoruje zamknięcie połączenia."""
    logger.debug("Połączenie zamknięte")

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Konfiguracja aplikacji
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Inicjalizacja rozszerzeń
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # Konfiguracja CSRF
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_CHECK_DEFAULT'] = True
    app.config['WTF_CSRF_METHODS'] = ['POST', 'PUT', 'PATCH', 'DELETE']
    
    # Konfiguracja Flask-Login
    login_manager.login_view = 'supplier.login_supplier'
    login_manager.login_message = 'Proszę się zalogować, aby uzyskać dostęp.'
    login_manager.login_message_category = 'warning'
    
    @login_manager.user_loader
    def load_user(user_id):
        # Sprawdzamy najpierw, czy ID zaczyna się od 'SUP/' (dostawca)
        if user_id.startswith('SUP/'):
            from models.supplier.supplier import Supplier
            return Supplier.query.get(user_id)
        # Sprawdzamy czy ID zaczyna się od 'STF/' lub 'ADM/' (pracownik lub administrator)
        elif user_id.startswith(('STF/', 'ADM/')):
            from models.staff.staff import Staff
            return Staff.query.get(user_id)
        # Jeśli nie, sprawdzamy czy to użytkownik auth_data
        else:
            from models.MAIN.user import User
            return User.query.get(user_id)
    
    # Konfiguracja CSP
    @app.after_request
    def add_security_headers(response):
        if response.mimetype == 'text/html':
            response.headers['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: blob: https://flowbite.s3.amazonaws.com; "
                "font-src 'self' data:; "
                "connect-src 'self'"
            )
        return response
    
    with app.app_context():
        # Import modeli
        from models.MAIN.user import User
        from models.supplier.supplier import Supplier
        from models.staff.staff import Staff
        
        # Inicjalizacja bazy danych
        db.create_all()
        
        # Rejestracja obsługi zdarzeń SQLAlchemy
        event.listen(db.engine, 'checkout', checkout_listener)
        event.listen(db.engine, 'checkin', checkin_listener)
        event.listen(db.engine, 'connect', connect_listener)
        event.listen(db.engine, 'close', close_listener)
    
    # Rejestracja blueprintów
    from routes.MAIN.routes import main_bp
    app.register_blueprint(main_bp)
    
    try:
        from routes.admin.routes import admin_bp
        app.register_blueprint(admin_bp, url_prefix='/admin')
    except ImportError:
        pass
        
    try:
        from routes.staff.routes import staff_bp
        app.register_blueprint(staff_bp, url_prefix='/staff')
    except ImportError:
        pass
        
    try:
        from routes.supplier.routes import supplier_bp
        app.register_blueprint(supplier_bp, url_prefix='/supplier')
    except ImportError:
        pass
    
    return app 