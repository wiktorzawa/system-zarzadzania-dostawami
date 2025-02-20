from datetime import datetime
from .. import db

class Supplier(db.Model):
    __tablename__ = 'suppliers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('login_data.id'), nullable=False)
    company_name = db.Column(db.String(255), nullable=False)
    nip = db.Column(db.String(10), unique=True, nullable=False)
    address = db.Column(db.String(255), nullable=False)
    postal_code = db.Column(db.String(6), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    supplier_number = db.Column(db.String(10), unique=True, nullable=False)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow) 