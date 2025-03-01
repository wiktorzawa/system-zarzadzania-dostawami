from datetime import datetime
import bcrypt
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from ..supplier.supplier import Supplier
from ..staff.staff import Staff

class User(db.Model):
    __tablename__ = 'login_auth_data'
    
    id = db.Column(db.String(20), primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum('admin', 'staff', 'supplier'), nullable=False)
    active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.TIMESTAMP, nullable=True)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relacje
    supplier_profile = db.relationship('Supplier', backref='user', uselist=False)
    staff_profile = db.relationship('Staff', backref='user', uselist=False)

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
            return self.supplier_profile
        elif self.role in ['admin', 'staff']:
            return self.staff_profile
        return None 