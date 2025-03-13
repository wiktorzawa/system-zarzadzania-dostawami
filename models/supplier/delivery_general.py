#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Model dla tabel związanych z dostawami.
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from __init__ import db
from .supplier import Supplier
from sqlalchemy.sql import func
from sqlalchemy import text

class DeliveryGeneral(db.Model):
    """Model dla tabeli dostawy_general."""
    
    __tablename__ = 'dostawy_general'
    
    # Klucz główny i klucz obcy
    id_delivery = db.Column(db.String(30), primary_key=True)
    id_supplier = db.Column(db.String(20), db.ForeignKey('login_table_suppliers.id_supplier'), nullable=False)
    
    # Dane identyfikacyjne dostawy
    lot_number = db.Column(db.String(100), nullable=False)
    pallet_number = db.Column(db.String(100), nullable=False)
    delivery_category = db.Column(db.String(100), nullable=False)
    other_category = db.Column(db.String(100), nullable=True)
    
    # Dane finansowe
    total_value = db.Column(db.Numeric(12, 2), nullable=False)
    total_value_pln = db.Column(db.Numeric(12, 2), nullable=False)
    delivery_value = db.Column(db.Numeric(12, 2), nullable=False)
    
    # Status i klasyfikacja
    status = db.Column(db.String(50), nullable=False, server_default='new')
    product_class = db.Column(db.String(50), nullable=False)
    
    # Dane ilościowe
    items_count = db.Column(db.Integer, nullable=False)
    lots_count = db.Column(db.Integer, nullable=False)
    pallets_count = db.Column(db.Integer, nullable=False)
    
    # Dane finansowe dodatkowe
    vat_rate = db.Column(db.String(10), nullable=False)
    value_percentage = db.Column(db.Integer, nullable=False)
    currency = db.Column(db.String(3), nullable=False)
    exchange_rate = db.Column(db.Numeric(10, 4), nullable=True)
    price_type = db.Column(db.Enum('net', 'gross', name='price_type_enum'), nullable=True)
    
    # Data dostawy
    delivery_date = db.Column(db.Date, nullable=False)
    
    # Znaczniki czasowe
    created_at = db.Column(db.TIMESTAMP, nullable=False, server_default=func.current_timestamp())
    updated_at = db.Column(db.TIMESTAMP, nullable=True, onupdate=func.current_timestamp())
    
    # Relacje
    supplier = db.relationship('Supplier', backref=db.backref('deliveries', lazy=True))
    
    @staticmethod
    def generate_delivery_id():
        """Generuje unikalny ID dostawy w formacie DELXXXXXX."""
        # Znajdź najwyższy numer
        result = db.session.execute(
            text("""
            SELECT COALESCE(
                MAX(
                    CASE 
                        WHEN id_delivery LIKE 'DEL/%' THEN CAST(SUBSTRING_INDEX(id_delivery, '/', -1) AS UNSIGNED)
                        WHEN id_delivery LIKE 'DEL%' THEN CAST(SUBSTRING(id_delivery, 4) AS UNSIGNED)
                        ELSE 0
                    END
                ), 0
            ) + 1 
            FROM dostawy_general 
            WHERE id_delivery LIKE 'DEL%'
            """)
        ).scalar()
        
        # Generuj nowy ID bez ukośnika
        return f"DEL{str(result).zfill(6)}"

    def __init__(self, **kwargs):
        """Inicjalizacja z automatycznym generowaniem ID."""
        if 'id_delivery' not in kwargs:
            kwargs['id_delivery'] = self.generate_delivery_id()
        super(DeliveryGeneral, self).__init__(**kwargs)
    
    def __repr__(self):
        return f"<DeliveryGeneral {self.id_delivery}>"
    
    def get_supplier(self):
        """Pobiera dostawcę dla tej dostawy."""
        return Supplier.query.filter_by(id_supplier=self.id_supplier).first()
    
    def to_dict(self):
        """Konwertuje obiekt dostawy na słownik."""
        supplier = None
        try:
            supplier = self.get_supplier()
        except Exception as e:
            print(f"Błąd podczas pobierania dostawcy: {str(e)}")
        
        return {
            'id_delivery': self.id_delivery,
            'id_supplier': self.id_supplier,
            'supplier_name': supplier.company_name if supplier else 'Nieznany dostawca',
            'lot_number': self.lot_number,
            'pallet_number': self.pallet_number,
            'delivery_category': self.delivery_category,
            'other_category': self.other_category,
            'total_value': float(self.total_value) if self.total_value else 0,
            'total_value_pln': float(self.total_value_pln) if self.total_value_pln else 0,
            'delivery_value': float(self.delivery_value) if self.delivery_value else 0,
            'status': self.status,
            'product_class': self.product_class,
            'items_count': self.items_count,
            'vat_rate': self.vat_rate,
            'value_percentage': self.value_percentage,
            'currency': self.currency,
            'exchange_rate': float(self.exchange_rate) if self.exchange_rate else None,
            'delivery_date': self.delivery_date.strftime('%Y-%m-%d') if self.delivery_date else None,
            'price_type': self.price_type,
            'lots_count': self.lots_count,
            'pallets_count': self.pallets_count,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }
    
    @staticmethod
    def get_all_by_supplier(supplier_id):
        """Pobiera wszystkie dostawy dla danego dostawcy."""
        return DeliveryGeneral.query.filter_by(
            id_supplier=supplier_id
        ).order_by(
            DeliveryGeneral.created_at.desc()
        ).all()
    
    @staticmethod
    def get_by_id(delivery_id):
        """Pobiera dostawę o podanym ID."""
        return DeliveryGeneral.query.get(delivery_id)
    
    @staticmethod
    def get_by_status(status):
        """Pobiera dostawy o podanym statusie."""
        return DeliveryGeneral.query.filter_by(status=status).order_by(DeliveryGeneral.created_at.desc()).all()
    
    @staticmethod
    def get_supplier_delivery_products(delivery_id, supplier_id):
        """Pobiera produkty dla dostawy danego dostawcy."""
        print(f"Szukam dostawy {delivery_id} dla dostawcy {supplier_id}")
        
        # Sprawdź, czy dostawa istnieje
        delivery = DeliveryGeneral.query.filter_by(
            id_delivery=delivery_id,
            id_supplier=supplier_id
        ).first()
        
        if not delivery:
            print(f"Nie znaleziono dostawy {delivery_id} dla dostawcy {supplier_id}")
            return None, "Nie znaleziono dostawy"
        
        # Sprawdź, czy istnieje tabela produktów
        try:
            from models.supplier.delivery_produkty_hybrid import DeliveryProduct
            
            # Sprawdź, czy tabela produktów istnieje
            if not DeliveryProduct.check_table_exists():
                print(f"Tabela produktów nie istnieje lub ma niepoprawną strukturę")
                return None, "Błąd struktury bazy danych"
            
            print(f"Szukam produktów dla dostawy {delivery_id}")
            
            # Sprawdź, czy istnieją produkty dla tej dostawy
            products_count = DeliveryProduct.query.filter_by(id_delivery=delivery_id).count()
            print(f"Liczba znalezionych produktów: {products_count}")
            
            if products_count == 0:
                print(f"Brak produktów dla dostawy {delivery_id}")
                return [], None
            
            # Pobierz produkty
            products = DeliveryProduct.query.filter_by(id_delivery=delivery_id).all()
            print(f"Znaleziono {len(products)} produktów dla dostawy {delivery_id}")
            
            # Sprawdź, czy produkty mają wszystkie wymagane pola
            for i, product in enumerate(products[:5]):  # Sprawdź tylko pierwsze 5 produktów
                print(f"Produkt {i+1}: ID={product.id_product}, Nazwa={product.product_name}, EAN={product.ean_code}")
            
            return products, None
        except Exception as e:
            print(f"Błąd podczas pobierania produktów: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return None, f"Błąd podczas pobierania produktów: {str(e)}"

    @staticmethod
    def get_by_status_paginated(status, supplier_id, page=1, per_page=10):
        """Pobiera dostawy o podanym statusie z paginacją."""
        return DeliveryGeneral.query.filter_by(
            status=status,
            id_supplier=supplier_id
        ).order_by(
            DeliveryGeneral.delivery_date.desc()
        ).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        ) 