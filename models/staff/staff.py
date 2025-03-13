from datetime import datetime
from flask_login import UserMixin
from __init__ import db

class Staff(db.Model, UserMixin):
    """
    Model reprezentujący dane pracownika w tabeli login_table_staff.
    
    Relacje:
    - id_staff jest powiązane z login_auth_data.related_id dla użytkowników z rolą 'admin' lub 'staff'
    """
    __tablename__ = 'login_table_staff'
    
    id_staff = db.Column(db.String(20), primary_key=True)
    first_name = db.Column(db.String(50), nullable=False, comment='Imię pracownika')
    last_name = db.Column(db.String(50), nullable=False, comment='Nazwisko pracownika')
    role = db.Column(db.Enum('admin', 'staff'), nullable=False, comment='Rola pracownika w systemie')
    email = db.Column(db.String(255), unique=True, nullable=False, comment='Adres email służbowy')
    phone = db.Column(db.String(20), nullable=True, comment='Numer telefonu')
    created_at = db.Column(db.TIMESTAMP, nullable=True, server_default=db.text('CURRENT_TIMESTAMP'), comment='Data utworzenia rekordu')
    updated_at = db.Column(db.TIMESTAMP, nullable=True, server_default=db.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), comment='Data aktualizacji rekordu')
    
    def get_id(self):
        """Wymagane przez Flask-Login"""
        return str(self.id_staff)
    
    def get_auth_data(self):
        """Pobiera dane logowania powiązane z tym pracownikiem"""
        from models.MAIN.user import User
        return User.query.filter_by(related_id=self.id_staff, role=self.role).first() 