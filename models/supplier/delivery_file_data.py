#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Model dla tabeli przechowującej dane plików dostaw.
"""

from datetime import datetime
import os
import uuid
import json
from werkzeug.utils import secure_filename
from __init__ import db
from sqlalchemy.sql import func
import pandas as pd

class DeliveryFileData(db.Model):
    """
    Model reprezentujący dane pliku dostawy w tabeli dostawy_dane_pliku.
    
    Tabela przechowuje informacje o plikach przesłanych przez dostawców,
    w tym dane o lokalizacji pliku w S3, jego zawartości i statusie przetwarzania.
    """
    __tablename__ = 'dostawy_dane_pliku'
    __table_args__ = (
        db.Index('idx_dostawy_dane_pliku_delivery', 'id_delivery'),
        db.Index('idx_dostawy_dane_pliku_processed', 'is_processed'),
        db.Index('idx_dostawy_dane_pliku_file_size', 'file_size'),
        {
            'mysql_engine': 'InnoDB',
            'mysql_charset': 'utf8mb4',
            'mysql_collate': 'utf8mb4_unicode_ci'
        }
    )
    
    # Klucz główny
    id_file_data = db.Column(db.String(36), primary_key=True)
    
    # Klucz obcy do dostawy
    id_delivery = db.Column(
        db.String(30),  # Zmienione z 20 na 30 dla zgodności z dostawy_general
        db.ForeignKey('dostawy_general.id_delivery', ondelete='CASCADE'),
        nullable=False
    )
    
    # Dane pliku
    file_name = db.Column(db.String(255), nullable=False)
    s3_key = db.Column(db.String(512), nullable=False)
    file_type = db.Column(db.String(100), nullable=False)
    file_size = db.Column(
        db.BigInteger,
        nullable=False,
        default=0,
        comment='Rozmiar pliku w bajtach'
    )
    
    # Dane zawartości
    headers = db.Column(db.JSON, nullable=True)
    data = db.Column(db.JSON, nullable=True)
    file_content = db.Column(
        db.JSON,
        nullable=True,
        comment='Zawartość pliku w formacie JSON'
    )
    
    # Dane przetwarzania
    row_count = db.Column(db.Integer, nullable=False, default=0)
    is_processed = db.Column(db.Boolean, nullable=False, default=False)
    processed_at = db.Column(db.TIMESTAMP, nullable=True)
    created_at = db.Column(
        db.TIMESTAMP,
        nullable=False,
        server_default=func.current_timestamp()
    )
    
    # Relacja z dostawą
    delivery = db.relationship(
        'DeliveryGeneral',
        backref=db.backref('files', lazy=True, cascade='all, delete-orphan')
    )
    
    def __init__(self, **kwargs):
        """Inicjalizacja obiektu z automatycznym generowaniem id_file_data."""
        if 'id_file_data' not in kwargs:
            kwargs['id_file_data'] = str(uuid.uuid4())
        super(DeliveryFileData, self).__init__(**kwargs)
    
    def update_file_content(self, processed_data):
        """
        Aktualizuje zawartość pliku na podstawie przetworzonych danych.
        
        Args:
            processed_data: Słownik z przetworzonymi danymi
        """
        self.headers = processed_data.get('headers', [])
        self.data = processed_data.get('rows', [])
        self.file_content = processed_data
        self.row_count = len(processed_data.get('rows', []))
        self.is_processed = True
        self.processed_at = datetime.now()
    
    @staticmethod
    def create_from_file(file, delivery_id, s3_key):
        """
        Tworzy nowy rekord na podstawie przesłanego pliku.
        
        Args:
            file: Obiekt pliku z request.files
            delivery_id: ID dostawy
            s3_key: Klucz S3 gdzie plik został zapisany
            
        Returns:
            DeliveryFileData: Utworzony obiekt
        """
        file.seek(0, 2)  # Przesuń na koniec pliku
        file_size = file.tell()  # Pobierz pozycję (rozmiar)
        file.seek(0)  # Wróć na początek
        
        if file.filename.lower().endswith(('xlsx', 'xls')):
            df = pd.read_excel(file)
        else:  # CSV
            df = pd.read_csv(file)
        
        file_data = DeliveryFileData(
            id_delivery=delivery_id,
            file_name=secure_filename(file.filename),
            s3_key=s3_key,
            file_type=file.content_type,
            file_size=file_size
        )
        
        db.session.add(file_data)
        db.session.commit()
        
        return file_data
    
    def to_dict(self):
        """Konwertuje obiekt na słownik."""
        return {
            'id_file_data': self.id_file_data,
            'id_delivery': self.id_delivery,
            'file_name': self.file_name,
            's3_key': self.s3_key,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'headers': self.headers,
            'data': self.data,
            'file_content': self.file_content,
            'row_count': self.row_count,
            'is_processed': bool(self.is_processed),
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @staticmethod
    def get_by_delivery_id(delivery_id):
        """Pobiera wszystkie pliki dla danej dostawy."""
        return DeliveryFileData.query.filter_by(id_delivery=delivery_id).all()
    
    @staticmethod
    def get_by_id(file_data_id):
        """Pobiera plik o podanym ID."""
        return DeliveryFileData.query.get(file_data_id) 