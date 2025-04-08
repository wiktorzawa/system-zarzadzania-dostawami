#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Model dla tabeli weryfikacji produktów.
"""

from datetime import datetime
from enum import Enum
from uuid import uuid4
from __init__ import db
from models.supplier.delivery_produkty_hybrid import DeliveryProduct
from models.supplier.delivery_general import DeliveryGeneral
from models.staff.staff import Staff

class ProductSize(str, Enum):
    S = 'S'
    M = 'M'
    L = 'L'
    XL = 'XL'
    LONG = 'LONG'

class ProductCondition(str, Enum):
    A = 'A'
    B = 'B'
    C = 'C'
    E = 'E'

class IntendedUse(str, Enum):
    MYSTERY_BOX = 'mystery_box'
    DETAL = 'detal'
    ZOSTAJE_NA_MAG = 'zostaje_na_mag'
    BRAK = 'brak'
    NADWYZKA = 'nadwyzka'

    @classmethod
    def _missing_(cls, value):
        # Obsługa starych wartości z polskimi znakami
        if value == 'nadwyżka':
            return cls.NADWYZKA
        return None

class WeryfikacjaProduktow(db.Model):
    __tablename__ = 'weryfikacja_produktow'

    id_weryfikacja = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    id_delivery = db.Column(db.String(30), db.ForeignKey('dostawy_general.id_delivery', ondelete='CASCADE'), nullable=False)
    id_product = db.Column(db.String(36), db.ForeignKey('delivery_produkty_hybrid.id_product', ondelete='CASCADE'), nullable=False)
    pallet_number = db.Column(db.String(100))
    lpn_number = db.Column(db.String(20))
    asin_code = db.Column(db.String(100))
    ean_code = db.Column(db.String(13))
    product_name = db.Column(db.String(255), nullable=False)
    price_verified = db.Column(db.Numeric(12, 2))
    product_size = db.Column(db.Enum(ProductSize))
    total_quantity_verified = db.Column(db.Integer, nullable=False, default=0)
    location = db.Column(db.String(20))
    product_condition = db.Column(db.Enum(ProductCondition))
    intended_use = db.Column(db.String(20))
    total_quantity = db.Column(db.Integer, nullable=False, default=0)
    price = db.Column(db.Numeric(12, 2))
    total_price = db.Column(db.Numeric(12, 2))
    images = db.Column(db.JSON)
    verification_status = db.Column(db.String(20), default='pending')
    verification_date = db.Column(db.DateTime)
    source_url = db.Column(db.String(512))
    verified_by = db.Column(db.String(20), db.ForeignKey('login_table_staff.id_staff', ondelete='SET NULL'))
    verification_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Relacje
    delivery = db.relationship('DeliveryGeneral', backref='weryfikacje', lazy='joined')
    product = db.relationship('DeliveryProduct', backref='weryfikacje', lazy='joined')
    staff = db.relationship('Staff', backref='weryfikacje', lazy='joined')

    @classmethod
    def create_from_product(cls, product, delivery):
        """Tworzy nowy rekord weryfikacji na podstawie produktu z dostawy"""
        try:
            print(f"Tworzenie weryfikacji dla produktu: {product.id_product}")
            print(f"Dane produktu: {vars(product)}")
            verification = cls(
                id_delivery=delivery.id_delivery,
                id_product=product.id_product,
                pallet_number=product.pallet_number,
                asin_code=product.asin_code,
                ean_code=product.ean_code,
                product_name=product.product_name,
                total_quantity=product.quantity,
                price=product.price,
                total_price=product.value,
                verification_status='pending'
            )
            print(f"Utworzony obiekt weryfikacji: {vars(verification)}")
            db.session.add(verification)
            db.session.commit()
            return verification
        except Exception as e:
            db.session.rollback()
            print(f"Szczegóły błędu: {str(e)}")
            raise Exception(f"Błąd podczas tworzenia weryfikacji: {str(e)}")

    @classmethod
    def get_by_delivery(cls, id_delivery: str):
        """Pobiera wszystkie rekordy weryfikacji dla danej dostawy"""
        try:
            return cls.query.filter_by(id_delivery=id_delivery).all()
        except Exception as e:
            raise Exception(f"Błąd podczas pobierania weryfikacji: {str(e)}")

    def verify(self, staff_id: str, quantity: int, price: float, condition: ProductCondition, 
               size: ProductSize, intended_use: str, location: str, notes: str = None):
        """Weryfikuje produkt"""
        try:
            self.total_quantity_verified = quantity
            self.price_verified = price
            self.product_condition = condition
            self.product_size = size
            self.intended_use = intended_use
            self.location = location
            self.verification_status = 'completed'
            self.verification_date = datetime.utcnow()
            self.verified_by = staff_id
            if notes:
                self.verification_notes = notes
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Błąd podczas weryfikacji produktu: {str(e)}")

    def reject(self, staff_id: str, reason: str):
        """Odrzuca produkt"""
        try:
            self.verification_status = 'rejected'
            self.verification_date = datetime.utcnow()
            self.verified_by = staff_id
            self.rejection_reason = reason
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Błąd podczas odrzucania produktu: {str(e)}")

    def request_correction(self, staff_id: str, correction_details: str):
        """Żąda korekty produktu"""
        try:
            self.verification_status = 'needs_correction'
            self.verification_date = datetime.utcnow()
            self.verified_by = staff_id
            self.correction_needed = correction_details
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Błąd podczas żądania korekty: {str(e)}")