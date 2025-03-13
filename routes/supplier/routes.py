from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, send_file, session
from flask_login import login_user, logout_user, login_required, current_user
from models.supplier.supplier import Supplier
from models.MAIN.user import User
from models.supplier.delivery_file_data import DeliveryFileData
from models.supplier.delivery_general import DeliveryGeneral
from __init__ import db, csrf
import pandas as pd
import io
from datetime import datetime
from utils.lot_analyzer import LotAnalyzer
import boto3
import os
from botocore.exceptions import ClientError
from werkzeug.utils import secure_filename
from config import Config
from flask_wtf.csrf import CSRFError

supplier_bp = Blueprint('supplier', __name__)

# Konfiguracja S3
s3_client = boto3.client(
    's3',
    aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
    region_name=Config.AWS_REGION
)
S3_BUCKET = Config.S3_BUCKET

def upload_to_s3(file_obj, filename, content_type, delivery_id):
    """
    Uploaduje plik do S3 i zwraca klucz S3.
    
    Args:
        file_obj: Obiekt pliku
        filename: Nazwa pliku
        content_type: Typ MIME pliku
        delivery_id: ID dostawy
        
    Returns:
        str: Klucz S3 gdzie plik został zapisany
    """
    try:
        # Generuj unikalną ścieżkę w S3 z ID dostawcy
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        supplier_id = current_user.id_supplier if current_user else 'unknown'
        
        # Format nazwy pliku: DEL000001_20250312_140655_original_filename
        formatted_filename = f"{delivery_id}_{timestamp}_{secure_filename(filename)}"
        s3_key = f"supplier_files/{supplier_id}/{formatted_filename}"
        
        # Upload pliku
        s3_client.upload_fileobj(
            file_obj,
            S3_BUCKET,
            s3_key,
            ExtraArgs={
                'ContentType': content_type,
                'Metadata': {
                    'supplier_id': supplier_id,
                    'delivery_id': delivery_id,
                    'upload_date': timestamp,
                    'original_filename': filename
                }
            }
        )
        
        return s3_key
    except ClientError as e:
        print(f"Błąd podczas uploadu do S3: {str(e)}")
        raise ValueError(f"Nie udało się zapisać pliku: {str(e)}")

@supplier_bp.route('/login', methods=['GET', 'POST'])
def login_supplier():
    if current_user.is_authenticated:
        return redirect(url_for('supplier.supplier_dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        auth_data = User.query.filter_by(email=email, role='supplier').first()
        if not auth_data:
            flash('Nieprawidłowy email lub hasło', 'error')
            return render_template('supplier/login_supplier.html')
            
        supplier = Supplier.query.filter_by(id_supplier=auth_data.related_id).first()
        if not supplier:
            flash('Błąd konfiguracji konta', 'error')
            return render_template('supplier/login_supplier.html')
            
        if auth_data.verify_password(password):
            auth_data.failed_login_attempts = 0
            auth_data.last_login = db.func.now()
            db.session.commit()
            
            login_user(supplier, remember=remember)
            return redirect(url_for('supplier.supplier_dashboard'))
            
        auth_data.failed_login_attempts += 1
        db.session.commit()
        flash('Nieprawidłowy email lub hasło', 'error')
    
    return render_template('supplier/login_supplier.html')

@supplier_bp.route('/logout')
@login_required
def logout_supplier():
    logout_user()
    flash('Zostałeś wylogowany', 'info')
    return redirect(url_for('supplier.login_supplier'))

@supplier_bp.route('/dashboard')
@login_required
def supplier_dashboard():
    return render_template('supplier/supplier_dashboard.html')

@supplier_bp.route('/profil')
@login_required
def supplier_profil():
    return render_template('supplier/supplier_profil.html')

@supplier_bp.route('/deliveries')
@login_required
def supplier_deliveries():
    deliveries = DeliveryGeneral.get_all_by_supplier(current_user.id_supplier)
    return render_template('supplier/supplier_deliveries.html', deliveries=deliveries)

@supplier_bp.route('/nowa-dostawa')
@login_required
def supplier_nowa_dostawa():
    return render_template('supplier/supplier_nowa_dostawa.html')

@supplier_bp.route('/dostawy_weryfikacja')
@login_required
def supplier_dostawy_weryfikacja():
    page = request.args.get('page', 1, type=int)
    per_page = 10  # liczba dostaw na stronę
    
    pagination = DeliveryGeneral.get_by_status_paginated(
        status='pending_verification',
        supplier_id=current_user.id_supplier,
        page=page,
        per_page=per_page
    )
    
    return render_template(
        'supplier/supplier_dostawy_weryfikacja.html',
        deliveries=pagination.items,
        pagination=pagination
    )

@supplier_bp.route('/negocjacje')
@login_required
def supplier_negocjacje():
    return render_template('supplier/supplier_negocjacje.html')

@supplier_bp.route('/rozliczenia')
@login_required
def supplier_rozliczenia():
    return render_template('supplier/supplier_rozliczenia.html')

@supplier_bp.route('/api/process-excel', methods=['POST'])
@login_required
@csrf.exempt
def process_excel():
    from flask_wtf.csrf import CSRFError
    
    try:
        print("Otrzymano żądanie process-excel")
        print("Files w request:", request.files)
        print("Content Type:", request.content_type)
        print("CSRF Token w formularzu:", 'csrf_token' in request.form)
        print("CSRF Token w nagłówku:", 'X-CSRFToken' in request.headers)
        
        if 'file' not in request.files:
            print("Brak pliku w request.files")
            return jsonify({'success': False, 'message': 'Nie przesłano pliku'}), 400
            
        file = request.files['file']
        print("Nazwa pliku:", file.filename)
        print("Content Type pliku:", file.content_type)
        
        if file.filename == '':
            print("Pusta nazwa pliku")
            return jsonify({'success': False, 'message': 'Nie wybrano pliku'}), 400
    
        # Utwórz tymczasowy rekord dostawy jeśli nie podano id_delivery
        delivery_id = request.form.get('delivery_id')
        if not delivery_id or delivery_id == 'TEMP':
            # Utwórz nową dostawę
            delivery = DeliveryGeneral(
                id_supplier=current_user.id_supplier,
                lot_number='TEMP',
                pallet_number='TEMP',
                delivery_category='TEMP',
                total_value=0,
                total_value_pln=0,
                delivery_value=0,
                product_class='TEMP',
                items_count=0,
                lots_count=0,
                pallets_count=0,
                vat_rate='23',
                value_percentage=100,
                currency='PLN',
                delivery_date=datetime.now().date()
            )
            
            # Używamy krótszej transakcji tylko do utworzenia dostawy
            db.session.add(delivery)
            db.session.commit()
            delivery_id = delivery.id_delivery
            print(f"Utworzono tymczasową dostawę z ID: {delivery_id}")

        # Wczytaj plik do pamięci
        file_content = file.read()
        file_obj = io.BytesIO(file_content)
        
        # Upload pliku do S3 - wykonujemy to poza transakcją bazy danych
        try:
            s3_key = upload_to_s3(io.BytesIO(file_content), file.filename, file.content_type, delivery_id)
            print(f"Plik zapisany w S3: {s3_key}")
        except Exception as e:
            print(f"Błąd podczas uploadu do S3: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Błąd podczas zapisywania pliku: {str(e)}'
            }), 500
        
        # Wczytaj dane z pliku
        file_obj.seek(0)  # Przewiń bufor na początek
        try:
            if file.filename.lower().endswith(('xlsx', 'xls')):
                print("Wczytuję plik Excel")
                df = pd.read_excel(file_obj)
                print("Kolumny w pliku Excel:", df.columns.tolist())
            else:  # CSV
                print("Wczytuję plik CSV")
                df = pd.read_csv(file_obj)
                print("Kolumny w pliku CSV:", df.columns.tolist())
        except Exception as e:
            print("Błąd podczas wczytywania pliku:", str(e))
            return jsonify({
                'success': False,
                'message': f'Błąd podczas wczytywania pliku. Upewnij się, że plik jest w prawidłowym formacie: {str(e)}'
            }), 400

        # Zachowaj oryginalne dane przed jakimikolwiek transformacjami
        original_data = df.to_dict('records')

        # Normalizuj nazwy kolumn (usuń spacje, zamień na wielkie litery)
        df.columns = [col.strip().upper() for col in df.columns]

        # Zamień NaN na None w całym DataFrame
        df = df.where(pd.notnull(df), None)

        # Mapowanie kolumn
        column_mapping = {
            'WARTOSC': 'Wartość',
            'NR LOT': 'LOT',
            'NR PALETY': 'Paleta',
            'ITEM DESC': 'Nazwa produktu',
            'EAN': 'EAN',
            'ASIN': 'ASIN',
            'ILOSC': 'Ilość',
            'CENA': 'Cena',
            'WALUTA': 'Waluta',
            'JEDNOSTKA': 'Jednostka'
        }

        # Przygotuj podsumowanie
        summary = {
            'total_rows': len(df),
            'items_count': len(df),
            'total_value': float(df['WARTOSC'].sum()) if 'WARTOSC' in df.columns else 0,
            'lots': sorted(list(set(df['NR LOT'].dropna().unique().tolist()))) if 'NR LOT' in df.columns else [],
            'pallets': sorted(list(set(df['NR PALETY'].dropna().unique().tolist()))) if 'NR PALETY' in df.columns else [],
            'mapped_columns': {
                orig: mapped for orig, mapped in column_mapping.items() 
                if orig in df.columns
            }
        }

        # Konwertuj DataFrame na słownik z obsługą None
        rows_data = []
        for _, row in df.iterrows():
            row_dict = {}
            for col in df.columns:
                val = row[col]
                if pd.isna(val):
                    row_dict[col] = None
                else:
                    row_dict[col] = val
            rows_data.append(row_dict)

        # Analiza nazwy pliku w poszukiwaniu LOT
        lot_analysis = LotAnalyzer.analyze_filename(file.filename)
        print("Analiza LOT:", lot_analysis)

        # Wyświetl pierwsze wiersze danych dla debugowania
        if not df.empty:
            print(f"Pierwszy wiersz danych: {df.iloc[0].to_dict()}")
            print(f"Typy danych w pierwszym wierszu:")
            for col, val in df.iloc[0].items():
                print(f"  {col}: {val} (typ: {type(val).__name__})")
        
        # Sprawdź, czy kolumny z cenami istnieją w pliku
        price_columns = [col for col in df.columns if any(price_term.lower() in col.lower() for price_term in ['cena', 'price', 'koszt', 'cost'])]
        if price_columns:
            print(f"Znaleziono kolumny z cenami: {price_columns}")
        else:
            print("Nie znaleziono kolumn z cenami w pliku!")
        
        # Sprawdź, czy kolumny z wartościami istnieją w pliku
        value_columns = [col for col in df.columns if any(value_term.lower() in col.lower() for value_term in ['wartość', 'wartosc', 'value', 'suma', 'total'])]
        if value_columns:
            print(f"Znaleziono kolumny z wartościami: {value_columns}")
        else:
            print("Nie znaleziono kolumn z wartościami w pliku!")

        # Przygotuj dane do zwrotu
        processed_data = {
            'headers': df.columns.tolist(),
            'rows': rows_data,
            'summary': summary,
            'original_data': original_data,
            'lot_analysis': {
                'found_in_filename': lot_analysis[1] if lot_analysis else None,
                'original_match': lot_analysis[0] if lot_analysis else None,
                'has_lot_column': 'NR LOT' in df.columns,
                'lots': summary['lots'],
                'all_empty': len(summary['lots']) == 0
            }
        }

        # Zapisz informacje o pliku w bazie danych - używamy osobnej transakcji
        try:
            file_data = DeliveryFileData(
                id_delivery=delivery_id,
                file_name=secure_filename(file.filename),
                s3_key=s3_key,
                file_type=file.content_type,
                file_size=len(file_content)
            )
            
            db.session.add(file_data)
            db.session.commit()
            
            # Aktualizuj zawartość pliku - używamy osobnej transakcji
            file_data.headers = processed_data['headers']
            file_data.data = processed_data['rows']
            file_data.file_content = processed_data
            file_data.row_count = len(rows_data)
            db.session.commit()
            
            print(f"Zapisano dane pliku w bazie, ID: {file_data.id_file_data}")
            
            # Aktualizuj dostawę z podsumowaniem - używamy osobnej transakcji
            try:
                delivery = DeliveryGeneral.query.get(delivery_id)
                if delivery:
                    # Aktualizuj wartości
                    delivery.total_value = summary['total_value']
                    delivery.items_count = summary['items_count']
                    delivery.lots_count = len(summary['lots']) if summary['lots'] else 0
                    delivery.pallets_count = len(summary['pallets']) if summary['pallets'] else 0
                    
                    # Jeśli znaleziono LOT w nazwie pliku lub w danych
                    if lot_analysis and lot_analysis[1]:
                        delivery.lot_number = lot_analysis[1]
                    elif summary['lots']:
                        delivery.lot_number = ', '.join(summary['lots'])
                    
                    # Jeśli znaleziono numery palet
                    if summary['pallets']:
                        delivery.pallet_number = ', '.join(str(p) for p in summary['pallets'])
                    
                    db.session.commit()
                    print(f"Zaktualizowano dostawę {delivery_id} z nowymi danymi")
            except Exception as e:
                print(f"Błąd podczas aktualizacji dostawy: {str(e)}")
                db.session.rollback()
            
            # Zapisz produkty do tabeli delivery_produkty_hybrid - używamy zoptymalizowanej metody bulk_create
            try:
                from models.supplier.delivery_produkty_hybrid import DeliveryProduct
                print("Próba zapisu produktów do bazy:")
                print(f"Delivery ID: {delivery_id}")
                print(f"Liczba produktów do zapisu: {len(df)}")
                
                # Mapowanie kolumn z pliku Excel na kolumny w bazie danych
                column_mapping = {
                    'lot_number': ['nr lot', 'nr_lot', 'nr-lot', 'lot', 'lot number', 'lot_number', 'lot-number', 'numer partii', 'numer_partii', 'partia'],
                    'pallet_number': ['nr palety', 'nr_palety', 'nr-palety', 'paleta', 'pallet', 'pallet number', 'pallet_number', 'pallet-number', 'numer palety'],
                    'product_name': ['item desc', 'item_desc', 'nazwa', 'nazwa produktu', 'produkt', 'product', 'product name', 'product_name', 'description', 'desc'],
                    'ean_code': ['ean', 'kod ean', 'kod_ean', 'ean code', 'ean_code', 'kod', 'code', 'barcode', 'bar code', 'bar_code'],
                    'asin_code': ['asin', 'kod asin', 'kod_asin', 'asin code', 'asin_code'],
                    'quantity': ['ilość', 'ilosc', 'ilośc', 'ilosć', 'qty', 'quantity', 'amount', 'liczba sztuk', 'liczba_sztuk'],
                    'unit': ['jednostka', 'jm', 'j.m.', 'unit', 'measure', 'unit of measure', 'uom'],
                    'price': ['cena', 'price', 'unit price', 'unit_price', 'cena jednostkowa', 'cena_jednostkowa', 'koszt', 'cost', 'preis', 'prix', 'precio', 'prezzo', 'einzelpreis', 'unit cost', 'cost per unit', 'price per unit', 'price per item'],
                    'value': ['wartość', 'wartosc', 'value', 'total', 'suma', 'total value', 'total_value', 'wert', 'valeur', 'valor', 'valore', 'gesamtwert', 'total cost', 'total price', 'sum', 'amount', 'line total', 'line value', 'line amount'],
                    'currency': ['waluta', 'currency', 'curr', 'waluty', 'währung', 'monnaie', 'moneda', 'valuta'],
                }
                
                # Normalizacja nazw kolumn (usunięcie spacji, zamiana na małe litery)
                normalized_columns = {col.lower().replace(' ', ''): col for col in df.columns}
                print(f"Znormalizowane nazwy kolumn: {normalized_columns}")
                
                # Przygotuj dane produktów
                products_data = []
                
                # Wyświetl pierwsze wiersze danych dla debugowania
                if not df.empty:
                    print(f"Pierwszy wiersz danych: {df.iloc[0].to_dict()}")
                
                for index, row in df.iterrows():
                    row_dict = row.to_dict()
                    cleaned_row = {}
                    
                    # Zapisz oryginalne dane
                    cleaned_row['original_data'] = row_dict
                    cleaned_row['mapped_fields'] = {}
                    
                    # Mapuj pola na podstawie nazw kolumn
                    for db_field, possible_names in column_mapping.items():
                        found = False
                        for col in df.columns:
                            # Normalizuj nazwę kolumny (usuń spacje, zamień na małe litery)
                            col_normalized = col.lower().replace(' ', '')
                            
                            # Sprawdź, czy znormalizowana nazwa kolumny pasuje do którejś z możliwych nazw
                            if any(possible_name.lower().replace(' ', '') == col_normalized for possible_name in possible_names):
                                cleaned_row[db_field] = row[col]
                                cleaned_row['mapped_fields'][db_field] = col
                                found = True
                                break
                        
                        # Jeśli nie znaleziono dopasowania dla ceny lub wartości, spróbuj znaleźć kolumny, które mogą zawierać te dane
                        if not found and db_field in ['price', 'value']:
                            # Sprawdź, czy istnieją kolumny z liczbami, które mogą być ceną lub wartością
                            for col in df.columns:
                                if col not in cleaned_row['mapped_fields'].values():  # Sprawdź tylko niezmapowane kolumny
                                    val = row[col]
                                    # Sprawdź, czy wartość jest liczbą
                                    if isinstance(val, (int, float)) or (isinstance(val, str) and val.replace('.', '', 1).replace(',', '', 1).isdigit()):
                                        # Jeśli to cena, wartości są zwykle mniejsze
                                        if db_field == 'price' and 'value' not in cleaned_row['mapped_fields']:
                                            try:
                                                num_val = float(str(val).replace(',', '.'))
                                                if 0 < num_val < 10000:  # Typowy zakres cen
                                                    cleaned_row[db_field] = val
                                                    cleaned_row['mapped_fields'][db_field] = col
                                                    print(f"Automatycznie zmapowano kolumnę '{col}' jako cenę, wartość: {val}")
                                                    found = True
                                                    break
                                            except (ValueError, TypeError):
                                                pass
                                        # Jeśli to wartość, wartości są zwykle większe
                                        elif db_field == 'value' and 'price' in cleaned_row['mapped_fields']:
                                            try:
                                                num_val = float(str(val).replace(',', '.'))
                                                price_val = float(str(cleaned_row['price']).replace(',', '.'))
                                                qty_val = float(str(cleaned_row.get('quantity', 1)).replace(',', '.'))
                                                # Sprawdź, czy wartość jest bliska cena * ilość
                                                if abs(num_val - (price_val * qty_val)) < 0.1 * num_val:
                                                    cleaned_row[db_field] = val
                                                    cleaned_row['mapped_fields'][db_field] = col
                                                    print(f"Automatycznie zmapowano kolumnę '{col}' jako wartość, wartość: {val}")
                                                    found = True
                                                    break
                                            except (ValueError, TypeError):
                                                pass
                        
                        if not found:
                            # Jeśli nie znaleziono dopasowania, ustaw wartość domyślną
                            cleaned_row[db_field] = None
                    
                    # Dodaj numer wiersza i ID dostawy
                    cleaned_row['row_num'] = index + 1
                    cleaned_row['id_delivery'] = delivery_id
                    
                    products_data.append(cleaned_row)
                
                # Wyświetl pierwsze zmapowane dane dla debugowania
                if products_data:
                    print(f"Pierwszy zmapowany wiersz: {products_data[0]}")
                    print(f"Mapowanie pól dla pierwszego wiersza: {products_data[0]['mapped_fields']}")
                    
                    # Sprawdź, czy cena i wartość zostały poprawnie zmapowane
                    if 'price' in products_data[0]['mapped_fields']:
                        price_col = products_data[0]['mapped_fields']['price']
                        price_val = products_data[0]['original_data'][price_col]
                        print(f"Cena zmapowana z kolumny '{price_col}', wartość: {price_val}, typ: {type(price_val).__name__}")
                    else:
                        print("Cena nie została zmapowana!")
                        
                    if 'value' in products_data[0]['mapped_fields']:
                        value_col = products_data[0]['mapped_fields']['value']
                        value_val = products_data[0]['original_data'][value_col]
                        print(f"Wartość zmapowana z kolumny '{value_col}', wartość: {value_val}, typ: {type(value_val).__name__}")
                    else:
                        print("Wartość nie została zmapowana!")
                
                # Zapisz produkty do tabeli delivery_produkty_hybrid
                products_saved = DeliveryProduct.bulk_create(products_data, delivery_id)
                print(f"Zapisano {products_saved} produktów do bazy danych")
            except Exception as e:
                print(f"Błąd podczas zapisywania produktów: {str(e)}")
                print(f"Typ błędu: {type(e)}")
                import traceback
                print("Pełny traceback:")
                print(traceback.format_exc())
                # Nie przerywamy całego procesu, jeśli nie udało się zapisać produktów
            
            # Dodaj ID dostawy do zwracanych danych
            processed_data['delivery_id'] = delivery_id
            
        except Exception as e:
            print(f"Błąd podczas zapisywania danych pliku: {str(e)}")
            # Usuń tymczasową dostawę w przypadku błędu
            if delivery_id and not request.form.get('delivery_id'):
                try:
                    DeliveryGeneral.query.filter_by(id_delivery=delivery_id).delete()
                    db.session.commit()
                except:
                    db.session.rollback()
            return jsonify({
                'success': False,
                'message': f'Błąd podczas zapisywania danych pliku: {str(e)}'
            }), 500

        return jsonify({
            'success': True,
            'data': processed_data,
            'message': 'Plik został pomyślnie przetworzony'
        })
    except CSRFError as e:
        print(f"Błąd CSRF: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Błąd CSRF: {str(e)}. Odśwież stronę i spróbuj ponownie.'
        }), 400
    except Exception as e:
        print("Błąd podczas przetwarzania pliku:", str(e))
        return jsonify({
            'success': False,
            'message': f'Błąd podczas przetwarzania pliku: {str(e)}'
        }), 400

@supplier_bp.route('/api/save-delivery', methods=['POST'])
@login_required
def save_delivery():
    try:
        # Sprawdzenie czy użytkownik jest zalogowany jako dostawca
        if not isinstance(current_user, Supplier):
            return jsonify({
                'success': False,
                'message': 'Brak uprawnień'
            }), 403
            
        # Pobierz dane z żądania
        data = request.get_json()
        delivery_id = data.get('delivery_id')
        
        print(f"Próba zapisu dostawy. ID: {delivery_id}, Dane:", data)
        
        # Pobierz istniejącą dostawę
        delivery = DeliveryGeneral.query.filter_by(id_delivery=delivery_id).first()
        if not delivery:
            return jsonify({
                'success': False,
                'message': f'Nie znaleziono dostawy o ID: {delivery_id}'
            }), 404
            
        # Aktualizuj podstawowe dane dostawy
        delivery.lot_number = data.get('lot_number')
        delivery.pallet_number = data.get('pallet_number')
        delivery.delivery_category = data.get('delivery_category')
        delivery.other_category = data.get('other_category')
        delivery.product_class = data.get('product_class')
        delivery.items_count = data.get('items_count', 0)
        delivery.lots_count = data.get('lots_count', 0)
        delivery.pallets_count = data.get('pallets_count', 0)
        
        # Ustaw parametry finansowe przed obliczeniami
        delivery.value_percentage = data.get('value_percentage')
        delivery.currency = data.get('currency')
        delivery.exchange_rate = data.get('exchange_rate')
        delivery.price_type = data.get('price_type')
        delivery.vat_rate = data.get('vat_rate')
        delivery.delivery_date = datetime.strptime(data.get('delivery_date'), '%Y-%m-%d').date()
        
        # Pobierz sumę wartości produktów z bazy danych
        try:
            from models.supplier.delivery_produkty_hybrid import DeliveryProduct
            from sqlalchemy import func
            
            # Oblicz sumę wartości produktów
            total_value_sum = db.session.query(func.sum(DeliveryProduct.value)).filter(
                DeliveryProduct.id_delivery == delivery_id
            ).scalar() or 0
            
            print(f"Obliczona suma wartości produktów: {total_value_sum}")
            
            # Jeśli suma wartości produktów jest większa od 0, użyj jej jako podstawy do obliczeń
            if float(total_value_sum) > 0:
                # Pobierz procent wartości i stawkę VAT z formularza
                value_percentage = float(data.get('value_percentage', 100))
                vat_rate = float(data.get('vat_rate', 23))
                
                print(f"Procent wartości: {value_percentage}%, Stawka VAT: {vat_rate}%")
                
                # Oblicz wartość dostawy na podstawie procentu wartości
                base_value = float(total_value_sum) * (value_percentage / 100)
                
                # Oblicz wartość z VAT
                delivery_value_with_vat = base_value * (1 + vat_rate / 100)
                
                # Ustaw wartości w dostawie
                delivery.total_value = float(total_value_sum)  # Pełna wartość produktów (cena rynkowa)
                delivery.delivery_value = round(delivery_value_with_vat, 2)  # Wartość do zapłaty (z VAT)
                
                print(f"Ustawiono total_value (wartość rynkowa): {delivery.total_value}")
                print(f"Ustawiono delivery_value (do zapłaty z VAT): {delivery.delivery_value}")
                print(f"Obliczenia: {total_value_sum} * {value_percentage}% = {base_value}, z VAT {vat_rate}% = {delivery_value_with_vat}")
            else:
                delivery.total_value = data.get('total_value', 0)
                delivery.delivery_value = data.get('delivery_value', 0)
                print(f"Suma wartości produktów wynosi 0, ustawiono wartości z formularza: total_value={delivery.total_value}, delivery_value={delivery.delivery_value}")
        except Exception as e:
            print(f"Błąd podczas obliczania wartości dostawy: {str(e)}")
            # W przypadku błędu, użyj wartości z formularza
            delivery.total_value = data.get('total_value', 0)
            delivery.delivery_value = data.get('delivery_value', 0)
            print(f"Z powodu błędu, ustawiono total_value z formularza: {delivery.total_value}")
            print(f"Z powodu błędu, ustawiono delivery_value z formularza: {delivery.delivery_value}")
        
        # Oblicz total_value_pln na podstawie kursu wymiany
        exchange_rate = float(data.get('exchange_rate', 1))
        delivery.total_value_pln = float(delivery.total_value) * exchange_rate
        print(f"Obliczono total_value_pln: {delivery.total_value_pln} (total_value: {delivery.total_value} * kurs: {exchange_rate})")
        
        # Ustaw status dostawy
        delivery.status = 'pending_verification'  # Zmień status na oczekujący na weryfikację
        
        print(f"Aktualizacja dostawy {delivery_id} zakończona sukcesem")
        
        # Zapisz zmiany
        db.session.commit()
            
        return jsonify({
            'success': True,
            'message': 'Dostawa została zapisana pomyślnie',
            'delivery_id': delivery.id_delivery
        })
    except Exception as e:
        print(f"Błąd podczas zapisywania dostawy: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Błąd podczas zapisywania dostawy: {str(e)}'
        }), 500

@supplier_bp.route('/api/refresh-session', methods=['GET'])
@login_required
def refresh_session():
    # Sprawdzenie czy użytkownik jest zalogowany jako dostawca
    if not isinstance(current_user, Supplier):
        return jsonify({
            'success': False,
            'message': 'Brak uprawnień'
        }), 403
        
    try:
        # Aktualizacja last_login
        auth_data = current_user.get_auth_data()
        if auth_data:
            auth_data.last_login = datetime.utcnow()
            db.session.commit()
            
        return jsonify({
            'success': True,
            'message': 'Sesja odświeżona pomyślnie'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Błąd podczas odświeżania sesji: {str(e)}'
        }), 500

@supplier_bp.route('/api/delivery-products/<path:delivery_id>')
@login_required
def get_delivery_products(delivery_id):
    """
    Pobiera produkty dla danej dostawy
    """
    try:
        # Pobierz ID dostawcy z obiektu current_user
        supplier_id = current_user.id_supplier
        if not supplier_id:
            return jsonify({
                'success': False,
                'message': 'Nie jesteś zalogowany jako dostawca'
            }), 401
            
        print(f"Pobieranie produktów dla dostawy ID: {delivery_id}, Dostawca ID: {supplier_id}")
        
        # Pobierz produkty dla dostawy - funkcja zwraca krotkę (products, error_message)
        products, error_message = DeliveryGeneral.get_supplier_delivery_products(delivery_id, supplier_id)
        
        if error_message:
            print(f"Błąd: {error_message}")
            return jsonify({
                'success': False,
                'message': error_message
            }), 404
            
        if not products or len(products) == 0:
            print(f"Nie znaleziono produktów dla dostawy ID: {delivery_id}")
            return jsonify({
                'success': False,
                'message': f'Nie znaleziono produktów dla dostawy ID: {delivery_id}'
            }), 404
            
        print(f"Znaleziono {len(products)} produktów dla dostawy ID: {delivery_id}")
        
        # Sprawdź ceny i wartości pierwszych 5 produktów
        if products and len(products) > 0:
            print("Szczegóły pierwszych 5 produktów:")
            for i, product in enumerate(products[:min(5, len(products))]):
                print(f"Produkt {i+1} - ID: {product.id_product}, Nazwa: {product.product_name}")
                print(f"  Cena: {product.price}, Wartość: {product.value}, Waluta: {product.currency}")
                if hasattr(product, 'original_data') and product.original_data:
                    print(f"  Mapowanie: {product.original_data}")
        
        # Pobierz informacje o dostawie
        delivery = DeliveryGeneral.query.filter_by(id_delivery=delivery_id).first()
        delivery_currency = delivery.currency if delivery else None
        delivery_exchange_rate = float(delivery.exchange_rate) if delivery and delivery.exchange_rate else None
        
        # Przygotuj dane produktów do zwrócenia
        products_data = []
        for product in products:
            product_data = {
                'id_product': product.id_product,
                'id_delivery': product.id_delivery,
                'product_name': product.product_name,
                'ean_code': product.ean_code,
                'asin_code': product.asin_code,
                'quantity': float(product.quantity) if product.quantity else None,
                'unit': product.unit,
                'price': float(product.price) if product.price else None,
                'value': float(product.value) if product.value else None,
                'currency': product.currency or delivery_currency or 'EUR',
                'lot_number': product.lot_number,
                'pallet_number': product.pallet_number,
                'row_num': product.row_num
            }
            products_data.append(product_data)
            
        return jsonify({
            'success': True,
            'products': products_data,
            'delivery_currency': delivery_currency,
            'delivery_exchange_rate': delivery_exchange_rate
        })
    except Exception as e:
        print(f"Błąd podczas pobierania produktów: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'Wystąpił błąd: {str(e)}'
        }), 500

@supplier_bp.route('/api/product-details/<product_id>')
@login_required
def get_product_details(product_id):
    print(f"Pobieranie szczegółów produktu {product_id}")
    
    try:
        from models.supplier.delivery_produkty_hybrid import DeliveryProduct
        
        # Pobierz produkt
        product = DeliveryProduct.query.get(product_id)
        if not product:
            return jsonify({
                'success': False,
                'message': f"Nie znaleziono produktu o ID {product_id}"
            }), 404
        
        # Sprawdź, czy użytkownik ma dostęp do tego produktu
        if current_user.id_supplier != product.delivery.id_supplier:
            return jsonify({
                'success': False,
                'message': "Brak uprawnień do wyświetlenia tego produktu"
            }), 403
        
        # Pobierz informacje o dostawie
        delivery = product.delivery
        delivery_exchange_rate = float(delivery.exchange_rate) if delivery and delivery.exchange_rate else None
        
        # Przygotuj dane produktu
        product_data = {
            'id_product': product.id_product,
            'id_delivery': product.id_delivery,
            'product_name': product.product_name,
            'ean_code': product.ean_code,
            'asin_code': product.asin_code,
            'quantity': float(product.quantity) if product.quantity else None,
            'unit': product.unit,
            'price': float(product.price) if product.price else None,
            'value': float(product.value) if product.value else None,
            'currency': product.currency,
            'lot_number': product.lot_number,
            'pallet_number': product.pallet_number,
            'row_num': product.row_num,
            'created_at': product.created_at.isoformat() if product.created_at else None,
            'original_data': product.original_data,
            'mapped_fields': product.mapped_fields
        }
        
        # Dodaj oryginalne dane i mapowanie pól, jeśli są dostępne
        if hasattr(product, 'original_data') and product.original_data:
            product_data['original_data'] = product.original_data
            
        if hasattr(product, 'mapped_fields') and product.mapped_fields:
            product_data['mapped_fields'] = product.mapped_fields
            
        return jsonify({
            'success': True,
            'product': product_data,
            'delivery_exchange_rate': delivery_exchange_rate
        })
    except Exception as e:
        print(f"Błąd podczas pobierania szczegółów produktu: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f"Błąd podczas pobierania szczegółów produktu: {str(e)}"
        }), 500 