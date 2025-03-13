from datetime import datetime
from flask_login import UserMixin
from __init__ import db

class Supplier(db.Model, UserMixin):
    """
    Model reprezentujący dane dostawcy w tabeli login_table_suppliers.
    
    Relacje:
    - id_supplier jest powiązane z login_auth_data.related_id dla użytkowników z rolą 'supplier'
    
    Uwaga: Identyfikator id_supplier jest generowany automatycznie przez trigger w bazie danych,
    który używa funkcji generate_supplier_id().
    """
    __tablename__ = 'login_table_suppliers'
    
    id_supplier = db.Column(db.String(20), primary_key=True)
    company_name = db.Column(db.String(255), nullable=False, comment='Nazwa firmy')
    first_name = db.Column(db.String(50), nullable=False, comment='Imię osoby kontaktowej')
    last_name = db.Column(db.String(50), nullable=False, comment='Nazwisko osoby kontaktowej')
    nip = db.Column(db.String(20), unique=True, nullable=False, comment='Numer NIP')
    email = db.Column(db.String(255), unique=True, nullable=False, comment='Adres email')
    phone = db.Column(db.String(20), nullable=False, comment='Numer telefonu')
    website = db.Column(db.String(255), nullable=True, comment='Strona internetowa')
    address_street = db.Column(db.String(100), nullable=False, comment='Ulica')
    address_building = db.Column(db.String(10), nullable=False, comment='Numer budynku')
    address_apartment = db.Column(db.String(10), nullable=True, comment='Numer lokalu')
    address_city = db.Column(db.String(100), nullable=False, comment='Miejscowość')
    address_postal_code = db.Column(db.String(10), nullable=False, comment='Kod pocztowy')
    address_country = db.Column(db.String(50), nullable=False, comment='Kraj')
    created_at = db.Column(db.TIMESTAMP, nullable=True, server_default=db.text('CURRENT_TIMESTAMP'), comment='Data utworzenia rekordu')
    updated_at = db.Column(db.TIMESTAMP, nullable=True, server_default=db.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), comment='Data aktualizacji rekordu')
    
    def get_id(self):
        """Wymagane przez Flask-Login"""
        return str(self.id_supplier)
    
    def get_auth_data(self):
        """Pobiera dane logowania powiązane z tym dostawcą"""
        from models.MAIN.user import User
        return User.query.filter_by(related_id=self.id_supplier, role='supplier').first() 