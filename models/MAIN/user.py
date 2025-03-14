from datetime import datetime
import bcrypt
from werkzeug.security import generate_password_hash, check_password_hash
from . import db

class User(db.Model):
    __tablename__ = 'login_auth_data'
    
    id_login = db.Column(db.String(20), primary_key=True, comment='Identyfikator logowania')
    related_id = db.Column(db.String(20), unique=True, nullable=False, comment='Powiązany identyfikator użytkownika')
    email = db.Column(db.String(255), unique=True, nullable=False, comment='Adres email')
    password_hash = db.Column(db.String(255), nullable=False, comment='Zahaszowane hasło')
    role = db.Column(db.Enum('admin', 'staff', 'supplier'), nullable=False, comment='Rola użytkownika')
    failed_login_attempts = db.Column(db.Integer, default=0, comment='Liczba nieudanych prób logowania')
    locked_until = db.Column(db.TIMESTAMP, nullable=True, comment='Zablokowane do')
    last_login = db.Column(db.TIMESTAMP, nullable=True, comment='Ostatnie logowanie')
    created_at = db.Column(db.TIMESTAMP, nullable=True, server_default=db.text('CURRENT_TIMESTAMP'), comment='Data utworzenia')
    updated_at = db.Column(db.TIMESTAMP, nullable=True, server_default=db.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), comment='Data aktualizacji')

    def set_password(self, password):
        """Ustawia zahaszowane hasło użytkownika"""
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        """Weryfikuje hasło z uwzględnieniem różnych formatów haszowania"""
        try:
            print(f"Weryfikacja hasła dla użytkownika {self.email}")  # Debug
            print(f"Format hasła w bazie: {self.password_hash[:50]}...")  # Debug
            
            if self.password_hash.startswith('$2'):
                print("Używam weryfikacji bcrypt")  # Debug
                # Format bcrypt
                return bcrypt.checkpw(password.encode('utf-8'), 
                                    self.password_hash.encode('utf-8'))
            else:
                print("Używam standardowej weryfikacji Flask")  # Debug
                # Standardowa weryfikacja
                result = check_password_hash(self.password_hash, password)
                print(f"Wynik weryfikacji: {result}")  # Debug
                return result
        except Exception as e:
            print(f"Błąd weryfikacji hasła: {e}")  # Debug
            return False

    def get_profile(self):
        """Zwraca odpowiedni profil użytkownika na podstawie roli"""
        if self.role == 'supplier':
            from ..supplier.supplier import Supplier
            return Supplier.query.filter_by(id_supplier=self.related_id).first()
        elif self.role in ['admin', 'staff']:
            from ..staff.staff import Staff
            return Staff.query.filter_by(id_staff=self.related_id).first()
        return None 