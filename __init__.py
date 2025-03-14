# Plik inicjalizacyjny pakietu
# Może pozostać pusty, ponieważ cała logika inicjalizacji jest w app.py 

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_principal import Principal, Permission, RoleNeed
from config import config
import logging
from sqlalchemy import event
import locale
import math

# Ustawienie locale na polski
try:
    locale.setlocale(locale.LC_ALL, 'pl_PL.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'Polish_Poland.1250')
    except:
        locale.setlocale(locale.LC_ALL, '')

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
principals = Principal()

# Definiowanie uprawnień
supplier_permission = Permission(RoleNeed('supplier'))
staff_permission = Permission(RoleNeed('staff'))
admin_permission = Permission(RoleNeed('admin'))

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
    principals.init_app(app)
    
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
    
    # Konfiguracja Flask-Principal
    from flask_login import current_user
    from flask_principal import identity_loaded, UserNeed, RoleNeed
    
    @identity_loaded.connect_via(app)
    def on_identity_loaded(sender, identity):
        # Dodaj logi do śledzenia procesu
        logger.info(f"Identity loaded: {identity.id}")
        
        # Dodaj UserNeed do tożsamości
        if hasattr(current_user, 'get_id') and current_user.get_id() is not None:
            identity.provides.add(UserNeed(current_user.get_id()))
            logger.info(f"Added UserNeed: {current_user.get_id()}")
        
        # Dodaj RoleNeed na podstawie typu użytkownika
        if hasattr(current_user, 'id_supplier'):
            identity.provides.add(RoleNeed('supplier'))
            logger.info("Added RoleNeed: supplier")
        elif hasattr(current_user, 'id_staff'):
            # Sprawdź, czy to pracownik czy administrator
            from models.MAIN.user import User
            user_auth = User.query.filter_by(related_id=current_user.id_staff).first()
            if user_auth and user_auth.role == 'admin':
                identity.provides.add(RoleNeed('admin'))
                logger.info("Added RoleNeed: admin")
            else:
                identity.provides.add(RoleNeed('staff'))
                logger.info("Added RoleNeed: staff")
        
        # Wypisz wszystkie uprawnienia
        logger.info(f"All permissions: {identity.provides}")
    
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
    
    # Dodanie filtrów Jinja2
    @app.template_filter('format_number')
    def format_number_filter(value):
        """Formatuje liczbę w formacie polskim z dwoma miejscami po przecinku."""
        if value is None:
            return '0,00'
        try:
            # Najpierw konwertujemy na string i czyścimy
            str_value = str(value).replace(' ', '').replace(',', '.')
            # Konwertujemy na float i formatujemy
            num_value = float(str_value)
            # Używamy format zamiast locale.format_string dla większej kontroli
            formatted = '{:,.2f}'.format(num_value)
            # Zamieniamy separatory na format polski
            return formatted.replace(',', ' ').replace('.', ',')
        except (ValueError, TypeError, AttributeError) as e:
            print(f"Błąd formatowania liczby {value}: {str(e)}")
            return '0,00'
    
    @app.template_filter('format_exchange_rate')
    def format_exchange_rate_filter(value):
        """Formatuje kurs wymiany w formacie polskim z czterema miejscami po przecinku."""
        if value is None:
            return '0,0000'
        try:
            # Najpierw konwertujemy na string i czyścimy
            str_value = str(value).replace(' ', '').replace(',', '.')
            # Konwertujemy na float i formatujemy
            num_value = float(str_value)
            # Używamy format zamiast locale.format_string dla większej kontroli
            formatted = '{:,.4f}'.format(num_value)
            # Zamieniamy separatory na format polski
            return formatted.replace(',', ' ').replace('.', ',')
        except (ValueError, TypeError, AttributeError) as e:
            print(f"Błąd formatowania kursu {value}: {str(e)}")
            return '0,0000'
    
    @app.template_filter('format_currency')
    def format_currency_filter(value, currency='PLN'):
        """Formatuje kwotę w formacie polskim z symbolem waluty."""
        if value is None:
            return '0,00 zł' if currency == 'PLN' else '0,00 €'
        try:
            # Konwertujemy na float
            num_value = float(str(value).replace(' ', '').replace(',', '.'))
            if math.isnan(num_value):
                return '0,00 zł' if currency == 'PLN' else '0,00 €'
            
            # Formatujemy liczbę w polskim stylu
            locale.setlocale(locale.LC_ALL, 'pl_PL.UTF-8')
            formatted = locale.format_string('%.2f', num_value, grouping=True)
            
            # Dodajemy symbol waluty zgodnie z polskim formatem
            if currency == 'PLN':
                return f'{formatted} zł'
            elif currency == 'EUR':
                return f'{formatted} €'
            else:
                return f'{formatted} {currency}'
        except (ValueError, TypeError, AttributeError) as e:
            print(f"Błąd formatowania waluty {value}: {str(e)}")
            return '0,00 zł' if currency == 'PLN' else '0,00 €'
    
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