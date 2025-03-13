#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Modele dla tabel związanych z produktami w dostawach.
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid
import json
from decimal import Decimal, InvalidOperation
from __init__ import db
from models.supplier.delivery_general import DeliveryGeneral

class DeliveryProduct(db.Model):
    """
    Model reprezentujący produkt w dostawie z dodatkowymi danymi w formacie JSON.
    Tabela przechowuje zarówno podstawowe dane produktu jak i dodatkowe informacje w polach JSON.
    """
    __tablename__ = 'delivery_produkty_hybrid'
    
    id_product = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_delivery = db.Column(db.String(20), db.ForeignKey('dostawy_general.id_delivery', ondelete='CASCADE'), nullable=False)
    product_name = db.Column(db.String(255), nullable=True)
    ean_code = db.Column(db.String(100), nullable=True, comment='Kod EAN produktu')
    asin_code = db.Column(db.String(100), nullable=True, comment='Kod ASIN produktu')
    quantity = db.Column(db.Numeric(12,2), nullable=False, default=1.00)
    unit = db.Column(db.String(20), nullable=True)
    price = db.Column(db.Numeric(12,2), nullable=True)
    value = db.Column(db.Numeric(12,2), nullable=True)
    currency = db.Column(db.String(3), nullable=True)
    lot_number = db.Column(db.String(100), nullable=True)
    pallet_number = db.Column(db.String(100), nullable=True)
    row_num = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.TIMESTAMP, nullable=False, server_default=db.text('CURRENT_TIMESTAMP'))
    
    # Pola JSON do przechowywania dodatkowych danych
    original_data = db.Column(db.JSON, nullable=True)
    mapped_fields = db.Column(db.JSON, nullable=True)
   
    # Relacja z tabelą główną
    delivery = db.relationship('DeliveryGeneral', backref=db.backref('products', lazy=True))

    def __repr__(self):
        return f"<DeliveryProduct {self.id_product}: {self.product_name}>"
    
    def to_dict(self):
        """
        Konwertuje obiekt na słownik.
        """
        return {
            'id_product': self.id_product,
            'id_delivery': self.id_delivery,
            'product_name': self.product_name,
            'ean_code': self.ean_code,
            'asin_code': self.asin_code,
            'quantity': float(self.quantity) if self.quantity else None,
            'unit': self.unit,
            'price': float(self.price) if self.price else None,
            'value': float(self.value) if self.value else None,
            'currency': self.currency,
            'lot_number': self.lot_number,
            'pallet_number': self.pallet_number,
            'row_num': self.row_num,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'original_data': self.original_data,
            'mapped_fields': self.mapped_fields,
            'additional_data': self.additional_data
        }
    
    @staticmethod
    def get_by_delivery_id(delivery_id, page=1, per_page=50):
        """Pobiera produkty dla danej dostawy z paginacją."""
        return DeliveryProduct.query.filter_by(id_delivery=delivery_id).paginate(page=page, per_page=per_page, error_out=False)
    
    @staticmethod
    def get_by_id(product_id):
        """Pobiera produkt po ID."""
        return DeliveryProduct.query.get(product_id)
    
    @staticmethod
    def bulk_create(products_data, delivery_id):
        """Tworzy wiele produktów dla dostawy."""
        total_products = 0
        batch_size = 100  # Rozmiar wsadu - zapisujemy po 100 produktów na raz
        
        print(f"Rozpoczynam bulk_create dla {len(products_data)} produktów, delivery_id: {delivery_id}")
        
        # Sprawdź, jakie pola są dostępne w pierwszym produkcie
        if products_data:
            print("Dostępne pola w pierwszym produkcie:")
            for field, value in products_data[0].items():
                if field not in ['original_data', 'mapped_fields', 'additional_data']:
                    print(f"  {field}: {value}")
            
            # Sprawdź mapowanie pól
            if 'mapped_fields' in products_data[0]:
                print("Mapowanie pól dla pierwszego produktu:")
                for db_field, excel_field in products_data[0]['mapped_fields'].items():
                    print(f"  {db_field} <- {excel_field}")
        
        for i in range(0, len(products_data), batch_size):
            batch = products_data[i:i+batch_size]
            products = []
            
            print(f"Przetwarzam wsad {i//batch_size + 1}/{(len(products_data) + batch_size - 1)//batch_size}, liczba produktów: {len(batch)}")
            
            for data in batch:
                # Sprawdź, czy wymagane pola są obecne
                if 'product_name' not in data or data['product_name'] is None:
                    print(f"Uwaga: Brak nazwy produktu w danych. Dostępne pola: {list(data.keys())}")
                    if 'mapped_fields' in data:
                        print(f"Mapowanie pól dla tego produktu: {data['mapped_fields']}")
                    if 'original_data' in data:
                        print(f"Oryginalne dane: {list(data['original_data'].keys())}")
                
                # Konwersja wartości pieniężnych na Decimal
                if 'price' in data:
                    try:
                        if data['price'] is not None:
                            data['price'] = Decimal(str(data['price']))
                        else:
                            data['price'] = Decimal('0')
                    except (ValueError, TypeError, InvalidOperation) as e:
                        print(f"Błąd konwersji ceny '{data.get('price')}': {str(e)}")
                        data['price'] = Decimal('0')
                
                if 'value' in data:
                    try:
                        if data['value'] is not None:
                            data['value'] = Decimal(str(data['value']))
                        else:
                            data['value'] = Decimal('0')
                    except (ValueError, TypeError, InvalidOperation) as e:
                        print(f"Błąd konwersji wartości '{data.get('value')}': {str(e)}")
                        data['value'] = Decimal('0')
                
                if 'quantity' in data:
                    try:
                        if data['quantity'] is not None:
                            data['quantity'] = Decimal(str(data['quantity']))
                        else:
                            data['quantity'] = Decimal('1')
                    except (ValueError, TypeError, InvalidOperation) as e:
                        print(f"Błąd konwersji ilości '{data.get('quantity')}': {str(e)}")
                        data['quantity'] = Decimal('1')
                
                # Upewnij się, że id_delivery jest ustawione
                data['id_delivery'] = delivery_id
                
                # Utwórz produkt
                try:
                    product = DeliveryProduct(**data)
                    products.append(product)
                except Exception as e:
                    print(f"Błąd podczas tworzenia produktu: {str(e)}")
                    print(f"Dane produktu: {data}")
            
            try:
                db.session.bulk_save_objects(products)
                db.session.commit()
                total_products += len(products)
                print(f"Zapisano wsad {i//batch_size + 1}, łącznie zapisano {total_products} produktów")
            except Exception as e:
                db.session.rollback()
                print(f"Błąd podczas zapisywania wsadu produktów: {str(e)}")
                import traceback
                print(traceback.format_exc())
                # Kontynuuj z następnym wsadem zamiast przerywać cały proces
        
        print(f"Zakończono bulk_create, łącznie zapisano {total_products} produktów")
        return total_products
    
    @staticmethod
    def create_from_row_data(row_data, delivery_id, mapping=None):
        """Tworzy produkt na podstawie danych wiersza z pliku."""
        # Domyślne mapowanie pól
        default_mapping = {
            'product_name': ['nazwa', 'name', 'produkt', 'product', 'item desc', 'item_desc', 'description', 'desc'],
            'ean_code': ['kod', 'code', 'symbol', 'sku', 'ean', 'kod ean', 'ean code', 'barcode'],
            'asin_code': ['kod', 'code', 'symbol', 'sku', 'asin', 'kod asin', 'asin code'],
            'quantity': ['ilość', 'ilosc', 'quantity', 'qty', 'amount', 'liczba sztuk'],
            'unit': ['jednostka', 'unit', 'jm', 'j.m.', 'miara', 'uom'],
            'price': ['cena', 'price', 'koszt', 'cost', 'unit price', 'cena jednostkowa', 'preis', 'prix', 'precio', 'prezzo', 'einzelpreis', 'unit cost', 'cost per unit', 'price per unit', 'price per item'],
            'value': ['wartość', 'wartosc', 'value', 'suma', 'total', 'total value', 'wert', 'valeur', 'valor', 'valore', 'gesamtwert', 'total cost', 'total price', 'sum', 'amount', 'line total', 'line value', 'line amount'],
            'currency': ['waluta', 'currency', 'curr', 'waluty', 'währung', 'monnaie', 'moneda', 'valuta'],
            'lot_number': ['lot', 'partia', 'batch', 'nr lot', 'numer partii', 'lot number'],
            'pallet_number': ['paleta', 'pallet', 'nr palety', 'nr_palety', 'pallet number', 'numer palety']
        }
        
        # Użyj dostarczonego mapowania lub domyślnego
        field_mapping = mapping or default_mapping
        
        # Zachowaj oryginalne dane
        original_data = dict(row_data)
        
        # Przygotuj dane produktu i śledź mapowane pola
        product_data = {
            'id_delivery': delivery_id,
            'original_data': original_data,
            'mapped_fields': {},
            'additional_data': {}
        }
        
        # Normalizuj klucze w row_data (usuń spacje, zamień na małe litery)
        normalized_keys = {key.lower().replace(' ', ''): key for key in row_data.keys()}
        
        # Mapuj pola z danych wiersza na pola relacyjne
        mapped_keys = set()
        for field, keywords in field_mapping.items():
            found = False
            for keyword in keywords:
                # Normalizuj słowo kluczowe
                keyword_normalized = keyword.lower().replace(' ', '')
                
                # Sprawdź, czy znormalizowane słowo kluczowe pasuje do któregoś z kluczy
                if keyword_normalized in normalized_keys:
                    original_key = normalized_keys[keyword_normalized]
                    value = row_data[original_key]
                    
                    # Konwersja wartości liczbowych
                    if field in ['quantity', 'price', 'value']:
                        try:
                            if value is not None:
                                product_data[field] = Decimal(str(value).replace(',', '.'))
                            else:
                                # Ustaw wartości domyślne dla pól liczbowych
                                if field == 'quantity':
                                    product_data[field] = Decimal('1')
                                else:  # price, value
                                    product_data[field] = Decimal('0')
                        except (ValueError, TypeError, InvalidOperation):
                            # Ustaw wartości domyślne w przypadku błędu
                            if field == 'quantity':
                                product_data[field] = Decimal('1')
                            else:  # price, value
                                product_data[field] = Decimal('0')
                    else:
                        product_data[field] = str(value).strip() if value else None
                    
                    # Zapisz informację o mapowaniu
                    product_data['mapped_fields'][field] = original_key
                    mapped_keys.add(original_key)
                    found = True
                    break
            
            # Jeśli nie znaleziono dopasowania, ustaw wartość domyślną
            if not found:
                product_data[field] = None
        
        # Dodaj niezmapowane pola do additional_data
        product_data['additional_data'] = {
            key: value for key, value in row_data.items() 
            if key not in mapped_keys
        }
        
        # Utwórz i zapisz produkt
        try:
            product = DeliveryProduct(**product_data)
            db.session.add(product)
            db.session.commit()
            return product
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Błąd podczas tworzenia produktu: {str(e)}")
    
    @staticmethod
    def check_table_exists():
        """Sprawdza, czy tabela produktów istnieje i ma poprawną strukturę."""
        try:
            # Sprawdź, czy tabela istnieje, wykonując prostą operację
            count = DeliveryProduct.query.count()
            print(f"Tabela delivery_produkty_hybrid istnieje. Liczba rekordów: {count}")
            return True
        except Exception as e:
            print(f"Błąd podczas sprawdzania tabeli delivery_produkty_hybrid: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return False 
    
    @staticmethod
    def print_product_details(product_id):
        """Wyświetla szczegóły produktu o podanym ID."""
        try:
            product = DeliveryProduct.query.get(product_id)
            if not product:
                print(f"Nie znaleziono produktu o ID {product_id}")
                return
            
            print(f"Szczegóły produktu {product_id}:")
            print(f"  ID dostawy: {product.id_delivery}")
            print(f"  Nazwa produktu: {product.product_name}")
            print(f"  Kod EAN: {product.ean_code}")
            print(f"  Kod ASIN: {product.asin_code}")
            print(f"  Ilość: {product.quantity}")
            print(f"  Jednostka: {product.unit}")
            print(f"  Cena: {product.price}")
            print(f"  Wartość: {product.value}")
            print(f"  Waluta: {product.currency}")
            print(f"  Numer LOT: {product.lot_number}")
            print(f"  Numer palety: {product.pallet_number}")
            print(f"  Numer wiersza: {product.row_num}")
            print(f"  Data utworzenia: {product.created_at}")
            
            if product.original_data:
                print("  Oryginalne dane:")
                for key, value in product.original_data.items():
                    print(f"    {key}: {value}")
            
            if product.mapped_fields:
                print("  Mapowanie pól:")
                for db_field, excel_field in product.mapped_fields.items():
                    print(f"    {db_field} <- {excel_field}")
            
            return product
        except Exception as e:
            print(f"Błąd podczas wyświetlania szczegółów produktu: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return None 