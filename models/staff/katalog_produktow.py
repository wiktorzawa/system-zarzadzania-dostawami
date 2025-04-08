#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Model dla tabeli katalog produktów.
"""

from datetime import datetime
from __init__ import db
from sqlalchemy.dialects.mysql import JSON

class KatalogProduktow(db.Model):
    __tablename__ = 'katalog_produktow'

    id_product_catalog = db.Column(db.Integer, primary_key=True, autoincrement=True)
    asin_code = db.Column(db.String(100), unique=True, index=True)
    ean_code = db.Column(db.String(13), index=True)
    product_name = db.Column(db.String(255), nullable=False)
    price_market = db.Column(db.Numeric(12, 2))
    description = db.Column(JSON)
    images = db.Column(JSON)
    last_price_check_date = db.Column(db.DateTime)
    source_url = db.Column(db.String(512))
    created_by = db.Column(db.String(20), db.ForeignKey('login_table_staff.id_staff', ondelete='SET NULL'), index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Relacje
    staff = db.relationship('Staff', backref='produkty_katalog', lazy='joined')

    @classmethod
    def get_all(cls):
        """Pobiera wszystkie produkty z katalogu"""
        try:
            return cls.query.all()
        except Exception as e:
            raise Exception(f"Błąd podczas pobierania produktów z katalogu: {str(e)}")

    @classmethod
    def get_by_id(cls, product_id):
        """Pobiera produkt po ID"""
        try:
            return cls.query.get(product_id)
        except Exception as e:
            raise Exception(f"Błąd podczas pobierania produktu: {str(e)}")

    @classmethod
    def get_by_asin(cls, asin_code):
        """Pobiera produkt po kodzie ASIN"""
        try:
            return cls.query.filter_by(asin_code=asin_code).first()
        except Exception as e:
            raise Exception(f"Błąd podczas pobierania produktu po ASIN: {str(e)}")

    @classmethod
    def get_by_ean(cls, ean_code):
        """Pobiera produkt po kodzie EAN"""
        try:
            return cls.query.filter_by(ean_code=ean_code).first()
        except Exception as e:
            raise Exception(f"Błąd podczas pobierania produktu po EAN: {str(e)}")

    @classmethod
    def create(cls, asin_code, ean_code, product_name, price_market, description=None, 
               images=None, source_url=None, created_by=None):
        """Tworzy nowy produkt w katalogu"""
        try:
            product = cls(
                asin_code=asin_code,
                ean_code=ean_code,
                product_name=product_name,
                price_market=price_market,
                description=description,
                images=images,
                last_price_check_date=datetime.utcnow(),
                source_url=source_url,
                created_by=created_by
            )
            db.session.add(product)
            db.session.commit()
            return product
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Błąd podczas dodawania produktu do katalogu: {str(e)}")

    def update(self, **kwargs):
        """Aktualizuje dane produktu"""
        try:
            for key, value in kwargs.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            
            # Aktualizacja daty sprawdzenia ceny, jeśli zmieniamy cenę
            if 'price_market' in kwargs:
                self.last_price_check_date = datetime.utcnow()
                
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Błąd podczas aktualizacji produktu: {str(e)}")

    def delete(self):
        """Usuwa produkt z katalogu"""
        try:
            db.session.delete(self)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Błąd podczas usuwania produktu: {str(e)}") 