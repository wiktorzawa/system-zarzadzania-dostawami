from flask import Flask
from dotenv import load_dotenv
import os
from models.MAIN import db, Auth
import routes
import sys
from pathlib import Path

# Dodaj katalog główny do ścieżki Pythona
sys.path.append(str(Path(__file__).parent))

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default-secret-key')

# Konfiguracja SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', 3306)}/{os.getenv('DB_NAME')}?charset=utf8mb4"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_timeout': 30,  # timeout połączenia w sekundach
    'pool_recycle': 1800,  # odśwież połączenie po 30 minutach
    'pool_pre_ping': True,  # sprawdź połączenie przed użyciem
    'connect_args': {
        'connect_timeout': 10  # timeout dla nowych połączeń
    }
}

# Inicjalizacja bazy danych
db.init_app(app)

# Inicjalizacja routingu
routes.init_app(app)

if __name__ == '__main__':
	app.run(debug=True)