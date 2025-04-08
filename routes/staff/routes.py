from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from flask_principal import Identity, AnonymousIdentity, identity_changed
from models.staff.staff import Staff
from models.MAIN.user import User
from __init__ import db, staff_permission, logger, csrf
import logging
from flask import jsonify
from datetime import datetime, timedelta
from models.supplier import DeliveryGeneral, DeliveryProduct
from models.staff.weryfikacja_produktow import WeryfikacjaProduktow, ProductSize, ProductCondition, IntendedUse
import os
from werkzeug.utils import secure_filename
import json

staff_bp = Blueprint('staff', __name__)

# Obsługa błędu 403 (Forbidden)
@staff_bp.errorhandler(403)
def handle_forbidden(e):
    # Logowanie próby dostępu
    logger.warning(f"Próba dostępu do zasobu bez uprawnień: {request.path}, Użytkownik: {current_user.get_id() if current_user.is_authenticated else 'Anonimowy'}")
    
    # Wyloguj użytkownika, aby przerwać pętlę przekierowań
    if current_user.is_authenticated:
        # Wyloguj użytkownika
        logout_user()
        # Wyczyść sesję
        session.clear()
        # Usunięcie tożsamości w Flask-Principal
        identity_changed.send(current_app._get_current_object(),
                            identity=AnonymousIdentity())
        flash('Nie masz uprawnień do dostępu do panelu pracownika. Zostałeś wylogowany.', 'warning')
    else:
        flash('Nie masz uprawnień do dostępu do tej strony.', 'warning')
    
    # Przekieruj do strony głównej
    return redirect(url_for('main.index'))

@staff_bp.route('/login', methods=['GET', 'POST'])
def login_staff():
    # Sprawdź, czy użytkownik jest już zalogowany
    if current_user.is_authenticated:
        # Jeśli użytkownik jest pracownikiem, przekieruj do panelu pracownika
        if hasattr(current_user, 'id_staff'):
            return redirect(url_for('staff.staff_dashboard'))
        # Jeśli użytkownik jest zalogowany, ale nie jest pracownikiem, wyloguj go
        else:
            logger.warning(f"Użytkownik {current_user.get_id()} próbuje uzyskać dostęp do panelu pracownika, ale nie jest pracownikiem")
            logout_user()
            session.clear()
            # Usunięcie tożsamości w Flask-Principal
            identity_changed.send(current_app._get_current_object(),
                                identity=AnonymousIdentity())
            flash('Wylogowano z poprzedniej sesji. Zaloguj się jako pracownik.', 'warning')
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        logger.info(f"Próba logowania pracownika: {email}")
        
        auth_data = User.query.filter_by(email=email).filter(User.role.in_(['admin', 'staff'])).first()
        if not auth_data:
            logger.warning(f"Nieudane logowanie pracownika - nieprawidłowy email: {email}")
            flash('Nieprawidłowy email lub hasło', 'error')
            return render_template('staff/login_staff.html')
            
        staff = Staff.query.filter_by(id_staff=auth_data.related_id).first()
        if not staff:
            logger.warning(f"Nieudane logowanie pracownika - brak powiązanego pracownika dla: {email}")
            flash('Błąd konfiguracji konta', 'error')
            return render_template('staff/login_staff.html')
            
        if auth_data.verify_password(password):
            auth_data.failed_login_attempts = 0
            auth_data.last_login = db.func.now()
            db.session.commit()
            
            # Logowanie użytkownika w Flask-Login
            login_user(staff, remember=remember)
            logger.info(f"Pracownik zalogowany pomyślnie: {email}, ID: {staff.id_staff}")
            
            # Ustawienie tożsamości w Flask-Principal
            identity = Identity(staff.id_staff)
            identity_changed.send(current_app._get_current_object(),
                                identity=identity)
            logger.info(f"Tożsamość Flask-Principal ustawiona dla pracownika: {staff.id_staff}")
            
            return redirect(url_for('staff.staff_dashboard'))
            
        auth_data.failed_login_attempts += 1
        db.session.commit()
        logger.warning(f"Nieudane logowanie pracownika - nieprawidłowe hasło: {email}")
        flash('Nieprawidłowy email lub hasło', 'error')
    
    return render_template('staff/login_staff.html')

@staff_bp.route('/logout')
@login_required
def logout_staff():
    logger.info(f"Wylogowanie pracownika: {current_user.id_staff if hasattr(current_user, 'id_staff') else 'Unknown'}")
    
    # Wylogowanie użytkownika z Flask-Login
    logout_user()
    
    # Usunięcie tożsamości w Flask-Principal
    identity_changed.send(current_app._get_current_object(),
                        identity=AnonymousIdentity())
    logger.info("Tożsamość Flask-Principal zresetowana")
    
    # Czyszczenie całej sesji
    session.clear()
    logger.info("Sesja wyczyszczona")
    
    flash('Zostałeś wylogowany', 'info')
    return redirect(url_for('main.index'))

@staff_bp.route('/dashboard')
@login_required
@staff_permission.require(http_exception=403)
def staff_dashboard():
    logger.info(f"Dostęp do panelu pracownika: {current_user.id_staff if hasattr(current_user, 'id_staff') else 'Unknown'}")
    
    # Pobierz statystyki produktów z ostatnich 7 dni
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    # Pobierz statystyki dzienne
    daily_products = db.session.query(
        db.func.date(DeliveryProduct.created_at).label('date'),
        db.func.count(DeliveryProduct.id_product).label('count')
    ).filter(
        DeliveryProduct.created_at.between(start_date, end_date)
    ).group_by(
        db.func.date(DeliveryProduct.created_at)
    ).all()
    
    # Przygotuj dane dla wykresu
    dates = [(start_date + timedelta(days=x)).strftime('%Y-%m-%d') for x in range(8)]
    daily_counts = {date: 0 for date in dates}
    for date, count in daily_products:
        daily_counts[date.strftime('%Y-%m-%d')] = count
    
    # Pobierz statystyki statusów dostaw
    product_statuses = db.session.query(
        DeliveryGeneral.status,
        db.func.count(DeliveryGeneral.id_delivery).label('count')
    ).group_by(DeliveryGeneral.status).all()
    
    # Pobierz top 5 najdroższych produktów
    top_products = DeliveryProduct.query.order_by(DeliveryProduct.price.desc()).limit(5).all()
    
    # Pobierz dodatkowe statystyki
    total_products = DeliveryProduct.query.count()
    new_products = DeliveryProduct.query.filter(
        DeliveryProduct.created_at >= (datetime.now() - timedelta(days=1))
    ).count()
    
    # Pobierz statystyki wartości dostaw
    delivery_values = db.session.query(
        db.func.sum(DeliveryGeneral.total_value).label('total_value'),
        DeliveryGeneral.currency
    ).group_by(DeliveryGeneral.currency).all()
    
    return render_template('staff/staff_dashboard.html',
                         daily_counts=daily_counts,
                         dates=dates,
                         product_statuses=product_statuses,
                         top_products=top_products,
                         total_products=total_products,
                         new_products=new_products,
                         delivery_values=delivery_values)

@staff_bp.route('/profile')
@login_required
@staff_permission.require(http_exception=403)
def staff_profile():
    logger.info(f"Dostęp do profilu pracownika: {current_user.id_staff if hasattr(current_user, 'id_staff') else 'Unknown'}")
    return render_template('staff/staff_profile.html')

@staff_bp.route('/deliveries')
@login_required
@staff_permission.require(http_exception=403)
def staff_deliveries():
    logger.info(f"Dostęp do dostaw pracownika: {current_user.id_staff if hasattr(current_user, 'id_staff') else 'Unknown'}")
    return render_template('staff/staff_deliveries.html')

@staff_bp.route('/suppliers')
@login_required
@staff_permission.require(http_exception=403)
def staff_suppliers():
    logger.info(f"Dostęp do dostawców: {current_user.id_staff if hasattr(current_user, 'id_staff') else 'Unknown'}")
    return render_template('staff/staff_suppliers.html')

@staff_bp.route('/reports')
@login_required
@staff_permission.require(http_exception=403)
def staff_reports():
    logger.info(f"Dostęp do raportów: {current_user.id_staff if hasattr(current_user, 'id_staff') else 'Unknown'}")
    return render_template('staff/staff_reports.html')

@staff_bp.route('/ecommerce_products')
@login_required
@staff_permission.require(http_exception=403)
def ecommerce_products():
    logger.info(f"Dostęp do e-commerce: {current_user.id_staff if hasattr(current_user, 'id_staff') else 'Unknown'}")
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Pobierz produkty z paginacją
    products = DeliveryProduct.query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Pobierz statystyki
    total_products = DeliveryProduct.query.count()
    new_products = DeliveryProduct.query.filter(DeliveryProduct.created_at >= (datetime.now() - timedelta(days=7))).count()
    
    return render_template('staff/staff_ecommerce_products.html',
                         products=products,
                         total_products=total_products,
                         new_products=new_products,
                         sold_products=0,  # TODO: Dodać logikę dla sprzedanych produktów
                         returned_products=0)  # TODO: Dodać logikę dla zwróconych produktów

# Dodane funkcje dla obsługi nowych dostaw
@staff_bp.route('/nowe-dostawy')
@login_required
@staff_permission.require(http_exception=403)
def staff_nowe_dostawy():
    """
    Widok dostaw z możliwością filtrowania i sortowania.
    """
    logger.info(f"Dostęp do nowych dostaw: {current_user.id_staff}")
    
    from models.supplier.delivery_general import DeliveryGeneral
    from models.supplier.supplier import Supplier
    
    # Pobierz parametry filtrowania i sortowania
    sort_param = request.args.get('sort', '')
    direction = request.args.get('direction', 'asc')
    supplier_filter = request.args.get('supplier', '')
    date_filter = request.args.get('date', '')
    category_filter = request.args.get('category', '')
    status_filter = request.args.get('status', '')
    
    logger.info(f"Parametry filtrowania: sort={sort_param}, direction={direction}, supplier={supplier_filter}, " +
               f"date={date_filter}, category={category_filter}, status={status_filter}")
    
    # Zbuduj zapytanie bazowe
    query = DeliveryGeneral.query
    
    # Filtrowanie po dostawcy
    if supplier_filter:
        query = query.filter(DeliveryGeneral.id_supplier == supplier_filter)
    
    # Filtrowanie po dacie
    today = datetime.now().date()
    
    if date_filter == 'today':
        query = query.filter(DeliveryGeneral.delivery_date == today)
    elif date_filter == 'yesterday':
        yesterday = today - timedelta(days=1)
        query = query.filter(DeliveryGeneral.delivery_date == yesterday)
    elif date_filter == 'week':
        week_ago = today - timedelta(days=7)
        query = query.filter(DeliveryGeneral.delivery_date >= week_ago)
    elif date_filter == 'month':
        month_ago = today - timedelta(days=30)
        query = query.filter(DeliveryGeneral.delivery_date >= month_ago)
    
    # Filtrowanie po kategorii
    if category_filter:
        query = query.filter(DeliveryGeneral.delivery_category == category_filter)
    
    # Filtrowanie po statusie
    if status_filter:
        query = query.filter(DeliveryGeneral.status == status_filter)
        logger.info(f"Filtrowanie po statusie: {status_filter}")
    else:
        # Domyślnie pokazuj nowe dostawy (zmiana z 'new' na 'pending_verification')
        query = query.filter(DeliveryGeneral.status == 'pending_verification')
        logger.info("Filtrowanie po statusie domyślnym: 'pending_verification'")
    
    # Debugowanie - sprawdź ile dostaw pasuje do zapytania
    matching_deliveries = query.all()
    logger.info(f"Liczba dostaw pasujących do filtrów: {len(matching_deliveries)}")
    
    if len(matching_deliveries) > 0:
        logger.info(f"Przykładowa dostawa: ID={matching_deliveries[0].id_delivery}, Status={matching_deliveries[0].status}")
    
    # Sortowanie
    if sort_param:
        if sort_param == 'id_delivery':
            if direction == 'asc':
                query = query.order_by(DeliveryGeneral.id_delivery.asc())
            else:
                query = query.order_by(DeliveryGeneral.id_delivery.desc())
        elif sort_param == 'supplier':
            if direction == 'asc':
                query = query.join(Supplier).order_by(Supplier.supplier_name.asc())
            else:
                query = query.join(Supplier).order_by(Supplier.supplier_name.desc())
        elif sort_param == 'delivery_date':
            if direction == 'asc':
                query = query.order_by(DeliveryGeneral.delivery_date.asc())
            else:
                query = query.order_by(DeliveryGeneral.delivery_date.desc())
        elif sort_param == 'category':
            if direction == 'asc':
                query = query.order_by(DeliveryGeneral.delivery_category.asc())
            else:
                query = query.order_by(DeliveryGeneral.delivery_category.desc())
        elif sort_param == 'lot':
            if direction == 'asc':
                query = query.order_by(DeliveryGeneral.lot_number.asc())
            else:
                query = query.order_by(DeliveryGeneral.lot_number.desc())
        elif sort_param == 'value':
            if direction == 'asc':
                query = query.order_by(DeliveryGeneral.total_value.asc())
            else:
                query = query.order_by(DeliveryGeneral.total_value.desc())
        elif sort_param == 'status':
            if direction == 'asc':
                query = query.order_by(DeliveryGeneral.status.asc())
            else:
                query = query.order_by(DeliveryGeneral.status.desc())
    else:
        # Domyślne sortowanie po dacie malejąco
        query = query.order_by(DeliveryGeneral.delivery_date.desc())
    
    # Paginacja
    page = request.args.get('page', 1, type=int)
    per_page = 20
    deliveries = query.paginate(page=page, per_page=per_page)
    
    # Pobierz wszystkich dostawców do filtra
    suppliers_list = Supplier.query.all()
    
    # Utwórz słownik dostawców dla łatwiejszego dostępu po id_supplier
    suppliers_dict = {}
    for supplier in suppliers_list:
        suppliers_dict[supplier.id_supplier] = supplier
    
    # Pobierz wszystkie kategorie do filtra
    categories = db.session.query(DeliveryGeneral.delivery_category).distinct().all()
    categories = [category[0] for category in categories if category[0]]
    
    logger.info(f"Wyświetlanie {deliveries.total} dostaw na stronie {page}")
    
    return render_template('staff/staff_nowe_dostawy.html', 
                           deliveries=deliveries, 
                           suppliers=suppliers_list,
                           suppliers_dict=suppliers_dict,
                           categories=categories,
                           current_filters={
                               'sort': sort_param,
                               'direction': direction,
                               'supplier': supplier_filter,
                               'date': date_filter,
                               'category': category_filter,
                               'status': status_filter
                           })

@staff_bp.route('/process-deliveries', methods=['POST'])
@login_required
@staff_permission.require(http_exception=403)
def process_deliveries():
    """
    Endpoint API do przetwarzania (zmiany statusu) wybranych dostaw.
    """
    from models.supplier.delivery_general import DeliveryGeneral
    import json
    
    logger.info(f"Próba zmiany statusu dostaw przez pracownika: {current_user.id_staff}")
    
    try:
        data = request.get_json()
        id_deliveries = data.get('id_deliveries', [])
        
        if not id_deliveries:
            return json.dumps({'success': False, 'message': 'Nie wybrano żadnych dostaw'}), 400, {'ContentType': 'application/json'}
        
        # Zaktualizuj status dostaw
        for id_delivery in id_deliveries:
            delivery = DeliveryGeneral.query.get(id_delivery)
            if delivery:
                delivery.status = 'processing'
                delivery.updated_at = db.func.now()
                
        db.session.commit()
        logger.info(f"Zmieniono status {len(id_deliveries)} dostaw na 'processing'")
        
        return json.dumps({'success': True, 'message': f'Pomyślnie zmieniono status {len(id_deliveries)} dostaw'}), 200, {'ContentType': 'application/json'}
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Błąd podczas zmiany statusu dostaw: {str(e)}")
        return json.dumps({'success': False, 'message': f'Wystąpił błąd: {str(e)}'}), 500, {'ContentType': 'application/json'}

@staff_bp.route('/export-deliveries-excel')
@login_required
@staff_permission.require(http_exception=403)
def export_deliveries_excel():
    """
    Endpoint do generowania i pobierania pliku Excel z wybranymi dostawami.
    """
    from models.supplier.delivery_general import DeliveryGeneral
    from models.supplier.delivery_produkty_hybrid import DeliveryProduct
    from models.supplier.supplier import Supplier
    from io import BytesIO
    import pandas as pd
    from flask import send_file
    
    logger.info(f"Próba eksportu dostaw do Excel przez pracownika: {current_user.id_staff}")
    
    try:
        ids = request.args.get('ids', '')
        if not ids:
            flash('Nie wybrano żadnych dostaw do eksportu', 'warning')
            return redirect(url_for('staff.staff_nowe_dostawy'))
        
        id_deliveries = ids.split(',')
        
        # Pobierz dostawy
        deliveries = []
        for id_delivery in id_deliveries:
            delivery = DeliveryGeneral.query.get(id_delivery)
            if delivery:
                delivery_dict = delivery.to_dict()
                # Dodaj nazwę dostawcy
                supplier = Supplier.query.get(delivery.id_supplier)
                delivery_dict['supplier_name'] = supplier.company_name if supplier else 'Nieznany'
                
                # Pobierz produkty dla dostawy
                products_count = DeliveryProduct.query.filter_by(id_delivery=id_delivery).count()
                delivery_dict['products_count'] = products_count
                
                deliveries.append(delivery_dict)
        
        if not deliveries:
            flash('Nie znaleziono wybranych dostaw', 'warning')
            return redirect(url_for('staff.staff_nowe_dostawy'))
        
        # Utwórz DataFrame
        df = pd.DataFrame(deliveries)
        
        # Wybierz kolumny do eksportu
        columns_to_export = [
            'id_delivery', 'supplier_name', 'delivery_date', 'delivery_category',
            'lot_number', 'total_value', 'currency', 'status', 'products_count'
        ]
        
        # Zmień nazwy kolumn na polskie
        column_names = {
            'id_delivery': 'ID Dostawy',
            'supplier_name': 'Dostawca',
            'delivery_date': 'Data dostawy',
            'delivery_category': 'Kategoria',
            'lot_number': 'LOT',
            'total_value': 'Wartość',
            'currency': 'Waluta',
            'status': 'Status',
            'products_count': 'Liczba produktów'
        }
        
        # Wybierz tylko potrzebne kolumny i zmień ich nazwy
        export_df = df[columns_to_export].rename(columns=column_names)
        
        # Utwórz plik Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            export_df.to_excel(writer, sheet_name='Dostawy', index=False)
            
            # Dostosuj szerokość kolumn
            worksheet = writer.sheets['Dostawy']
            for i, col in enumerate(export_df.columns):
                max_width = max(export_df[col].astype(str).map(len).max(), len(col)) + 2
                worksheet.set_column(i, i, max_width)
        
        output.seek(0)
        
        # Wygeneruj nazwę pliku
        filename = f"dostawy_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        logger.info(f"Wygenerowano plik Excel z {len(deliveries)} dostawami")
        
        # Wyślij plik do pobrania
        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        logger.error(f"Błąd podczas eksportu dostaw do Excel: {str(e)}")
        flash(f'Wystąpił błąd podczas generowania pliku Excel: {str(e)}', 'error')
        return redirect(url_for('staff.staff_nowe_dostawy'))

@staff_bp.route('/dostawa-szczegoly/<id_delivery>')
@login_required
@staff_permission.require(http_exception=403)
def staff_dostawa_szczegoly(id_delivery):
    """
    Wyświetla szczegóły dostawy o podanym ID.
    """
    from models.supplier.delivery_general import DeliveryGeneral
    from models.supplier.delivery_produkty_hybrid import DeliveryProduct
    from models.supplier.supplier import Supplier
    from models.supplier.delivery_file_data import DeliveryFileData
    
    logger.info(f"Dostęp do szczegółów dostawy {id_delivery} przez pracownika: {current_user.id_staff}")
    
    # Pobierz dostawę
    delivery = DeliveryGeneral.query.get_or_404(id_delivery)
    
    # Pobierz dostawcę
    supplier = Supplier.query.get(delivery.id_supplier)
    
    # Pobierz produkty z paginacją
    page = request.args.get('page', 1, type=int)
    products = DeliveryProduct.query.filter_by(id_delivery=id_delivery).paginate(
        page=page, per_page=50, error_out=False
    )
    
    # Pobierz pliki
    files = DeliveryFileData.query.filter_by(id_delivery=id_delivery).all()
    
    return render_template(
        'staff/staff_dostawa_szczegoly.html',
        delivery=delivery,
        supplier=supplier,
        products=products,
        files=files
    )

@staff_bp.route('/dostawa-raport')
@login_required
@staff_permission.require(http_exception=403)
def staff_dostawa_raport():
    """
    Generuje raport z dostaw.
    """
    logger.info(f"Dostęp do raportu dostaw przez pracownika: {current_user.id_staff}")
    
    # Tutaj implementacja generowania raportu
    # ...
    
    return render_template('staff/staff_dostawa_raport.html')

@staff_bp.route('/check-new-deliveries')
@login_required
@staff_permission.require(http_exception=403)
def check_new_deliveries():
    """
    Endpoint API do sprawdzania liczby nowych dostaw.
    """
    from models.supplier.delivery_general import DeliveryGeneral
    import json
    
    logger.debug(f"Sprawdzanie nowych dostaw przez pracownika: {current_user.id_staff}")
    
    try:
        # Debugowanie - sprawdź wszystkie dostawy i ich statusy
        all_deliveries = DeliveryGeneral.query.all()
        logger.info(f"Łączna liczba dostaw w systemie: {len(all_deliveries)}")
        
        # Zbierz informacje o statusach
        status_counts = {}
        for delivery in all_deliveries:
            status = delivery.status
            if status in status_counts:
                status_counts[status] += 1
            else:
                status_counts[status] = 1
        
        logger.info(f"Statusy dostaw w systemie: {status_counts}")
        
        # Pobierz liczbę nowych dostaw - zmieniamy na pending_verification
        new_deliveries = DeliveryGeneral.query.filter_by(status='pending_verification').all()
        count = len(new_deliveries)
        
        # Wypisz szczegóły o nowych dostawach
        for i, delivery in enumerate(new_deliveries[:5]):  # Pokaż pierwsze 5 dostaw
            logger.info(f"Nowa dostawa {i+1}: ID={delivery.id_delivery}, Status={delivery.status}")
        
        return json.dumps({'count': count}), 200, {'ContentType': 'application/json'}
        
    except Exception as e:
        logger.error(f"Błąd podczas sprawdzania nowych dostaw: {str(e)}")
        return json.dumps({'count': 0, 'error': str(e)}), 500, {'ContentType': 'application/json'}

@staff_bp.route('/api/delivery/<id_delivery>/products')
@login_required
@staff_permission.require(http_exception=403)
def staff_delivery_products(id_delivery):
    """
    Endpoint API do pobierania produktów dla konkretnej dostawy.
    """
    from models.supplier.delivery_general import DeliveryGeneral
    from models.supplier.delivery_produkty_hybrid import DeliveryProduct
    import json
    from flask import jsonify
    
    logger.info(f"Pobieranie produktów dla dostawy: {id_delivery}")
    
    try:
        # Sprawdź czy dostawa istnieje
        delivery = DeliveryGeneral.query.get(id_delivery)
        if not delivery:
            logger.warning(f"Nie znaleziono dostawy o ID: {id_delivery}")
            return jsonify({"error": "Nie znaleziono dostawy", "products": []}), 404
        
        # Pobierz produkty
        products = DeliveryProduct.query.filter_by(id_delivery=id_delivery).all()
        logger.info(f"Znaleziono {len(products)} produktów dla dostawy {id_delivery}")
        
        # Przygotuj dane produktów
        products_data = []
        for product in products:
            product_dict = {
                "id_product": product.id_product,
                "lot_number": product.lot_number,
                "pallet_number": product.pallet_number,
                "product_name": product.product_name,
                "quantity": float(product.quantity) if product.quantity else 0,
                "unit": product.unit,
                "value": float(product.value) if product.value else 0,
                "currency": product.currency,
                "ean_code": product.ean_code,
                "asin_code": product.asin_code,
                "country": product.original_data.get('country') if product.original_data else "N/A"
            }
            products_data.append(product_dict)
        
        return jsonify({"products": products_data})
    except Exception as e:
        logger.error(f"Błąd podczas pobierania produktów: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({"error": f"Wystąpił błąd: {str(e)}", "products": []}), 500

@staff_bp.route('/api/start-verification/<id_delivery>', methods=['POST'])
@login_required
@staff_permission.require(http_exception=403)
@csrf.exempt
def start_verification(id_delivery):
    """Rozpoczyna proces weryfikacji dla dostawy"""
    try:
        # Pobierz dostawę
        delivery = DeliveryGeneral.query.get(id_delivery)
        if not delivery:
            return jsonify({'success': False, 'error': 'Dostawa nie została znaleziona'}), 404
            
        # Sprawdź status dostawy
        if delivery.status != 'pending_verification':
            return jsonify({'success': False, 'error': 'Dostawa nie jest gotowa do weryfikacji'}), 400
            
        # Pobierz wszystkie produkty z dostawy
        products = DeliveryProduct.query.filter_by(id_delivery=id_delivery).all()
        if not products:
            return jsonify({'success': False, 'error': 'Nie znaleziono produktów w dostawie'}), 404
            
        # Utwórz rekordy weryfikacji dla każdego produktu
        for product in products:
            verification = WeryfikacjaProduktow.create_from_product(product, delivery)
            if not verification:
                db.session.rollback()
                return jsonify({'success': False, 'error': 'Błąd podczas tworzenia rekordów weryfikacji'}), 500
            
        # Aktualizuj status dostawy
        delivery.status = 'processing'
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Rozpoczęto weryfikację dostawy',
            'id_delivery': id_delivery,
            'products_count': len(products),
            'redirect_url': url_for('staff.staff_weryfikacja')
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Błąd podczas rozpoczynania weryfikacji: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@staff_bp.route('/w-trakcie-weryfikacji')
@login_required
@staff_permission.require(http_exception=403)
def staff_weryfikacja():
    """Wyświetla listę dostaw w trakcie weryfikacji"""
    try:
        # Pobierz dostawy w trakcie weryfikacji
        deliveries = DeliveryGeneral.query.filter_by(status='processing').all()
        
        # Przygotuj dane dla szablonu
        delivery_data = []
        for delivery in deliveries:
            # Pobierz dane dostawcy
            supplier = delivery.supplier
            
            # Pobierz weryfikacje dla dostawy
            verifications = WeryfikacjaProduktow.query.filter_by(id_delivery=delivery.id_delivery).all()
            
            # Oblicz statystyki weryfikacji
            total_products = len(verifications)
            verified_count = sum(1 for v in verifications if v.verification_status == 'completed')
            rejected_count = sum(1 for v in verifications if v.verification_status == 'rejected')
            pending_count = sum(1 for v in verifications if v.verification_status == 'pending')
            
            # Oblicz postęp weryfikacji
            progress = (verified_count / total_products * 100) if total_products > 0 else 0
            
            delivery_data.append({
                'delivery': delivery,
                'supplier': supplier,
                'verifications': verifications,
                'stats': {
                    'total': total_products,
                    'verified': verified_count,
                    'rejected': rejected_count,
                    'pending': pending_count,
                    'progress': progress
                }
            })
            
        return render_template('staff/staff_weryfikacja.html', 
                             title='Dostawy w trakcie weryfikacji',
                             delivery_data=delivery_data)
                             
    except Exception as e:
        print(f"Błąd podczas pobierania danych weryfikacji: {str(e)}")
        flash('Wystąpił błąd podczas pobierania danych weryfikacji', 'error')
        return redirect(url_for('staff.staff_dashboard'))

@staff_bp.route('/api/delivery/<id_delivery>/details')
@login_required
def get_delivery_details(id_delivery):
    try:
        # Pobierz dostawę
        delivery = DeliveryGeneral.query.get(id_delivery)
        if not delivery:
            return jsonify({'success': False, 'error': 'Nie znaleziono dostawy'}), 404
            
        # Pobierz weryfikacje
        verifications = WeryfikacjaProduktow.query.filter_by(id_delivery=id_delivery).all()
        
        # Oblicz statystyki
        total_products = len(verifications)
        verified_products = sum(1 for v in verifications if v.verification_status == 'completed')
        rejected_products = sum(1 for v in verifications if v.verification_status == 'rejected')
        pending_products = sum(1 for v in verifications if v.verification_status == 'pending')
        
        # Przygotuj historię weryfikacji
        verification_history = []
        for verification in verifications:
            if verification.verification_date:
                verification_history.append({
                    'id': verification.id_weryfikacja,
                    'product_name': verification.product_name,
                    'status': verification.verification_status,
                    'date': verification.verification_date.strftime('%Y-%m-%d %H:%M:%S'),
                    'verified_by': verification.verified_by
                })
        
        return jsonify({
            'success': True,
            'delivery': {
                'id': delivery.id_delivery,
                'delivery_date': delivery.delivery_date.strftime('%Y-%m-%d') if delivery.delivery_date else None,
                'lot_number': delivery.lot_number,
                'status': delivery.status,
                'total_products': total_products,
                'verified_products': verified_products,
                'rejected_products': rejected_products,
                'pending_products': pending_products,
                'verification_history': verification_history
            }
        })
    except Exception as e:
        print(f"Błąd podczas pobierania szczegółów dostawy: {str(e)}")
        return jsonify({'success': False, 'error': 'Wystąpił błąd podczas pobierania szczegółów'}), 500

@staff_bp.route('/verify-delivery/<id_delivery>')
@login_required
@staff_permission.require(http_exception=403)
def verify_delivery(id_delivery):
    """Wyświetla formularz weryfikacji dostawy"""
    try:
        # Pobierz dostawę
        delivery = DeliveryGeneral.query.get(id_delivery)
        if not delivery:
            return jsonify({'success': False, 'error': 'Nie znaleziono dostawy'}), 404
        
        # Pobierz weryfikacje
        verifications = WeryfikacjaProduktow.query.filter_by(id_delivery=id_delivery).all()
        
        # Przekształć obiekty weryfikacji w serializowalne słowniki
        serialized_verifications = []
        for v in verifications:
            serialized_verifications.append({
                'id_weryfikacja': v.id_weryfikacja,
                'product_name': v.product_name,
                'ean_code': v.ean_code,
                'asin_code': v.asin_code,
                'total_quantity': v.total_quantity,
                'price': float(v.price) if v.price else None,
                'total_price': float(v.total_price) if v.total_price else None,
                'verification_status': v.verification_status
            })
        
        # Pobierz dane dostawcy
        supplier = delivery.supplier
        
        return render_template('staff/staff_weryfikacja_produkty.html',
                             delivery=delivery,
                             supplier=supplier,
                             verifications=serialized_verifications)
                             
    except Exception as e:
        logger.error(f"Błąd podczas pobierania danych weryfikacji: {str(e)}")
        flash('Wystąpił błąd podczas pobierania danych weryfikacji', 'error')
        return redirect(url_for('staff.staff_weryfikacja'))

@staff_bp.route('/api/verify-product/<verification_id>', methods=['POST'])
@login_required
@staff_permission.require(http_exception=403)
@csrf.exempt
def verify_product(verification_id):
    """Weryfikuje pojedynczy produkt"""
    try:
        # Pobierz weryfikację
        verification = WeryfikacjaProduktow.query.get_or_404(verification_id)
        
        # Pobierz dane z żądania
        data = request.get_json()
        status = data.get('verification_status')
        notes = data.get('notes', '')
        
        if not status:
            return jsonify({'success': False, 'error': 'Nie podano statusu weryfikacji'}), 400
            
        # Aktualizuj weryfikację
        verification.verification_status = status
        verification.verification_notes = notes
        verification.verification_date = datetime.now()
        verification.verified_by = current_user.id_staff
        
        # Dodaj pozostałe dane
        verification.total_quantity_verified = data.get('total_quantity_verified')
        verification.price_verified = data.get('price_verified')
        verification.product_condition = data.get('product_condition')
        verification.product_size = data.get('product_size')
        verification.intended_use = data.get('intended_use')
        verification.location = data.get('location')
        verification.pallet_number = data.get('pallet_number')
        verification.lpn_number = data.get('lpn_number')
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Produkt został zweryfikowany',
            'verification_id': verification_id,
            'status': status
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Błąd podczas weryfikacji produktu: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@staff_bp.route('/api/verify-product-with-images/<verification_id>', methods=['POST'])
@login_required
@staff_permission.require(http_exception=403)
@csrf.exempt
def verify_product_with_images(verification_id):
    """Weryfikuje pojedynczy produkt wraz z przesłanymi zdjęciami"""
    try:
        # Pobierz weryfikację
        verification = WeryfikacjaProduktow.query.get_or_404(verification_id)
        
        # Pobierz dane weryfikacji z JSON
        verification_data = json.loads(request.form.get('verification_data', '{}'))
        status = verification_data.get('verification_status')
        notes = verification_data.get('notes', '')
        
        if not status:
            return jsonify({'success': False, 'error': 'Nie podano statusu weryfikacji'}), 400
            
        # Aktualizuj weryfikację
        verification.verification_status = status
        verification.verification_notes = notes
        verification.verification_date = datetime.now()
        verification.verified_by = current_user.id_staff
        
        # Dodaj pozostałe dane
        verification.total_quantity_verified = verification_data.get('total_quantity_verified')
        verification.price_verified = verification_data.get('price_verified')
        verification.product_condition = verification_data.get('product_condition')
        verification.product_size = verification_data.get('product_size')
        verification.intended_use = verification_data.get('intended_use')
        verification.location = verification_data.get('location')
        verification.pallet_number = verification_data.get('pallet_number')
        verification.lpn_number = verification_data.get('lpn_number')
        
        # Obsługa przesłanych zdjęć
        if 'images' in request.files:
            uploaded_images = request.files.getlist('images')
            saved_images = []
            
            # Utwórz folder, jeśli nie istnieje
            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads/verifications')
            verification_folder = f"{upload_folder}/{verification_id}"
            os.makedirs(verification_folder, exist_ok=True)
            
            # Zapisz każde zdjęcie
            for i, image_file in enumerate(uploaded_images):
                if image_file and allowed_file(image_file.filename):
                    # Bezpieczna nazwa pliku
                    filename = secure_filename(image_file.filename)
                    # Dodaj timestamp, aby uniknąć duplikatów
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                    new_filename = f"{timestamp}_{i}_{filename}"
                    file_path = os.path.join(verification_folder, new_filename)
                    
                    # Zapisz plik
                    image_file.save(file_path)
                    
                    # Dodaj ścieżkę do listy zapisanych zdjęć
                    saved_images.append(f"/uploads/verifications/{verification_id}/{new_filename}")
            
            # Zapisz ścieżki do zdjęć w rekordzie weryfikacji (jako JSON)
            if saved_images:
                # Jeśli już istnieją zdjęcia, dodaj nowe
                existing_images = verification.images or []
                if isinstance(existing_images, str):
                    try:
                        existing_images = json.loads(existing_images)
                    except:
                        existing_images = []
                
                verification.images = existing_images + saved_images
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Produkt został zweryfikowany wraz ze zdjęciami',
            'verification_id': verification_id,
            'status': status
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Błąd podczas weryfikacji produktu ze zdjęciami: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

def allowed_file(filename):
    """Sprawdza, czy plik ma dozwolone rozszerzenie"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@staff_bp.route('/api/reject-product/<verification_id>', methods=['POST'])
@login_required
def reject_product(verification_id):
    try:
        data = request.get_json()
        verification = WeryfikacjaProduktow.query.get(verification_id)
        
        if not verification:
            return jsonify({'success': False, 'error': 'Nie znaleziono weryfikacji'}), 404
            
        verification.rejection_reason = data.get('reason')
        verification.verification_status = 'rejected'
        verification.verified_at = datetime.utcnow()
        verification.verified_by = current_user.id
        
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        print(f"Błąd podczas odrzucania produktu: {str(e)}")
        return jsonify({'success': False, 'error': 'Wystąpił błąd podczas odrzucania produktu'}), 500

@staff_bp.route('/api/request-correction/<verification_id>', methods=['POST'])
@login_required
def request_correction(verification_id):
    try:
        data = request.get_json()
        verification = WeryfikacjaProduktow.query.get(verification_id)
        
        if not verification:
            return jsonify({'success': False, 'error': 'Nie znaleziono weryfikacji'}), 404
            
        verification.correction_needed = data.get('details')
        verification.verification_status = 'needs_correction'
        verification.verified_at = datetime.utcnow()
        verification.verified_by = current_user.id
        
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        print(f"Błąd podczas żądania korekty: {str(e)}")
        return jsonify({'success': False, 'error': 'Wystąpił błąd podczas żądania korekty'}), 500

@staff_bp.route('/api/product-verification/<verification_id>/details')
@login_required
def get_verification_details(verification_id):
    try:
        verification = WeryfikacjaProduktow.query.get(verification_id)
        
        if not verification:
            return jsonify({'success': False, 'error': 'Nie znaleziono weryfikacji'}), 404
            
        product_data = {
            'product_name': verification.product_name,
            'ean_code': verification.ean_code,
            'asin_code': verification.asin_code,
            'total_quantity': verification.total_quantity,
            'price': verification.price,
            'total_price': verification.total_price,
            'pallet_number': verification.pallet_number,
            'lpn_number': verification.lpn_number
        }
        
        verification_data = {
            'status': verification.verification_status,
            'total_quantity_verified': verification.total_quantity_verified,
            'price_verified': verification.price_verified,
            'product_size': verification.product_size,
            'product_condition': verification.product_condition,
            'intended_use': verification.intended_use,
            'location': verification.location,
            'verification_date': verification.verification_date.strftime('%Y-%m-%d %H:%M:%S') if verification.verification_date else None,
            'verified_by': verification.verified_by
        }
        
        return jsonify({
            'success': True,
            'product': product_data,
            'verification': verification_data
        })
    except Exception as e:
        print(f"Błąd podczas pobierania szczegółów weryfikacji: {str(e)}")
        return jsonify({'success': False, 'error': 'Wystąpił błąd podczas pobierania szczegółów'}), 500

@staff_bp.route('/katalog-produktow')
@login_required
@staff_permission.require(http_exception=403)
def katalog_produktow():
    """
    Widok bazy produktów z możliwością filtrowania, wyszukiwania i sortowania.
    """
    logger.info(f"Dostęp do bazy produktów przez pracownika: {current_user.id_staff}")
    
    from models.supplier.delivery_produkty_hybrid import DeliveryProduct
    from models.supplier.delivery_general import DeliveryGeneral
    from models.supplier.supplier import Supplier
    
    # Pobierz parametry filtrowania i sortowania
    search_query = request.args.get('query', '')
    sort_param = request.args.get('sort', '')
    direction = request.args.get('direction', 'asc')
    supplier_filter = request.args.get('supplier', '')
    status_filter = request.args.get('status', '')
    
    # Zbuduj zapytanie bazowe
    query = DeliveryProduct.query
    
    # Dodaj wyszukiwanie
    if search_query:
        query = query.filter(
            db.or_(
                DeliveryProduct.product_name.ilike(f'%{search_query}%'),
                DeliveryProduct.ean_code.ilike(f'%{search_query}%'),
                DeliveryProduct.asin_code.ilike(f'%{search_query}%')
            )
        )
    
    # Filtrowanie po dostawcy
    if supplier_filter:
        query = query.join(
            DeliveryGeneral, 
            DeliveryProduct.id_delivery == DeliveryGeneral.id_delivery
        ).filter(DeliveryGeneral.id_supplier == supplier_filter)
    
    # Filtrowanie po statusie dostawy
    if status_filter:
        query = query.join(
            DeliveryGeneral, 
            DeliveryProduct.id_delivery == DeliveryGeneral.id_delivery
        ).filter(DeliveryGeneral.status == status_filter)
    
    # Sortowanie
    if sort_param:
        if sort_param == 'product_name':
            if direction == 'asc':
                query = query.order_by(DeliveryProduct.product_name.asc())
            else:
                query = query.order_by(DeliveryProduct.product_name.desc())
        elif sort_param == 'ean_code':
            if direction == 'asc':
                query = query.order_by(DeliveryProduct.ean_code.asc())
            else:
                query = query.order_by(DeliveryProduct.ean_code.desc())
        elif sort_param == 'quantity':
            if direction == 'asc':
                query = query.order_by(DeliveryProduct.quantity.asc())
            else:
                query = query.order_by(DeliveryProduct.quantity.desc())
        elif sort_param == 'created_at':
            if direction == 'asc':
                query = query.order_by(DeliveryProduct.created_at.asc())
            else:
                query = query.order_by(DeliveryProduct.created_at.desc())
    else:
        # Domyślne sortowanie po dacie dodania malejąco
        query = query.order_by(DeliveryProduct.created_at.desc())
    
    # Paginacja
    page = request.args.get('page', 1, type=int)
    per_page = 20
    products = query.paginate(page=page, per_page=per_page)
    
    # Pobierz wszystkich dostawców do filtra
    suppliers_list = Supplier.query.all()
    
    # Utwórz słownik dostawców dla łatwiejszego dostępu po id_supplier
    suppliers_dict = {}
    for supplier in suppliers_list:
        suppliers_dict[supplier.id_supplier] = supplier
    
    # Pobierz wszystkie statusy dostaw do filtra
    statuses = db.session.query(DeliveryGeneral.status).distinct().all()
    statuses = [status[0] for status in statuses if status[0]]
    
    logger.info(f"Wyświetlanie {products.total} produktów na stronie {page}")
    
    return render_template('staff/staff_katalog produktow.html', 
                           products=products,
                           suppliers=suppliers_list,
                           suppliers_dict=suppliers_dict,
                           statuses=statuses,
                           current_filters={
                               'query': search_query,
                               'sort': sort_param,
                               'direction': direction,
                               'supplier': supplier_filter,
                               'status': status_filter
                           })

@staff_bp.route('/api/product/<id_product>/details')
@login_required
@staff_permission.require(http_exception=403)
def get_product_details(id_product):
    """
    Endpoint API do pobierania szczegółów produktu.
    """
    from models.supplier.delivery_produkty_hybrid import DeliveryProduct
    from flask import jsonify
    
    logger.info(f"Pobieranie szczegółów produktu: {id_product}")
    
    try:
        # Znajdź produkt
        product = DeliveryProduct.query.get(id_product)
        if not product:
            logger.warning(f"Nie znaleziono produktu o ID: {id_product}")
            return jsonify({"error": "Nie znaleziono produktu"}), 404
        
        # Pobierz dostawę produktu
        delivery = product.delivery
        
        # Przygotuj dane produktu
        product_data = product.to_dict()
        
        # Dodaj informacje o dostawie
        product_data['delivery'] = {
            'id_delivery': delivery.id_delivery,
            'delivery_date': delivery.delivery_date.strftime('%Y-%m-%d') if delivery.delivery_date else None,
            'status': delivery.status
        }
        
        logger.info(f"Znaleziono szczegóły produktu {id_product}")
        
        return jsonify({"success": True, "product": product_data})
        
    except Exception as e:
        logger.error(f"Błąd podczas pobierania szczegółów produktu: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@staff_bp.route('/api/get-verification-status/<id_product>')
@login_required
@staff_permission.require(http_exception=403)
def get_verification_status(id_product):
    """
    Endpoint API do sprawdzania statusu weryfikacji produktu.
    """
    from models.staff.weryfikacja_produktow import WeryfikacjaProduktow
    from flask import jsonify
    
    logger.info(f"Sprawdzanie statusu weryfikacji produktu: {id_product}")
    
    try:
        # Sprawdź, czy produkt ma już weryfikację
        verification = WeryfikacjaProduktow.query.filter_by(id_product=id_product).first()
        
        if verification:
            return jsonify({
                "success": True, 
                "verified": True,
                "verification_id": verification.id_weryfikacja,
                "status": verification.verification_status
            })
        else:
            return jsonify({"success": True, "verified": False})
        
    except Exception as e:
        logger.error(f"Błąd podczas sprawdzania statusu weryfikacji produktu: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@staff_bp.route('/api/search-products')
@login_required
@staff_permission.require(http_exception=403)
def search_products():
    """Wyszukiwanie produktów po EAN, ASIN lub nazwie"""
    try:
        query = request.args.get('query', '')
        delivery_id = request.args.get('delivery_id', '')
        
        if not query or len(query) < 3:
            return jsonify({
                'success': True,
                'products': []
            })
        
        # Przygotuj zapytanie do bazy danych
        search_query = f"%{query}%"
        products_query = WeryfikacjaProduktow.query
        
        # Jeśli podano id_delivery, ograniczamy wyniki tylko do tej dostawy
        if delivery_id:
            products_query = products_query.filter_by(id_delivery=delivery_id)
            
        # Wyszukiwanie po EAN, ASIN lub nazwie produktu
        products = products_query.filter(
            db.or_(
                WeryfikacjaProduktow.product_name.ilike(search_query),
                WeryfikacjaProduktow.ean_code.ilike(search_query),
                WeryfikacjaProduktow.asin_code.ilike(search_query)
            )
        ).all()
        
        # Znajdź duplikaty z różnymi cenami
        duplicates_with_price_diff = {}
        
        # Grupuj produkty według ASIN
        asin_groups = {}
        for product in products:
            if product.asin_code:
                if product.asin_code not in asin_groups:
                    asin_groups[product.asin_code] = []
                asin_groups[product.asin_code].append(product)
        
        # Sprawdź, które grupy mają różne ceny
        for asin, prod_list in asin_groups.items():
            if len(prod_list) > 1:
                # Sprawdź, czy ceny są różne
                prices = set(float(p.price) if p.price else 0 for p in prod_list)
                if len(prices) > 1:
                    duplicates_with_price_diff[asin] = {
                        'count': len(prod_list),
                        'prices': [f"{float(p.price):.2f} {prod_list[0].delivery.currency}" if p.price else "brak ceny" for p in prod_list],
                        'products': [p.id_weryfikacja for p in prod_list]
                    }
        
        # Ogranicz wyniki do limitu
        products = products[:20]
        
        # Przygotuj dane do zwrócenia
        products_data = []
        for product in products:
            product_data = {
                'id_weryfikacja': product.id_weryfikacja,
                'product_name': product.product_name,
                'ean_code': product.ean_code,
                'asin_code': product.asin_code,
                'total_quantity': product.total_quantity,
                'price': float(product.price) if product.price else None,
                'total_price': float(product.total_price) if product.total_price else None,
                'verification_status': product.verification_status,
                'pallet_number': product.pallet_number
            }
            
            # Dodaj informację o duplikatach z różnymi cenami, jeśli istnieją
            if product.asin_code and product.asin_code in duplicates_with_price_diff:
                product_data['price_mismatches'] = duplicates_with_price_diff[product.asin_code]
                
            products_data.append(product_data)
        
        return jsonify({
            'success': True,
            'products': products_data,
            'duplicates_with_price_diff': duplicates_with_price_diff
        })
        
    except Exception as e:
        logger.error(f"Błąd podczas wyszukiwania produktów: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@staff_bp.route('/api/consolidate-duplicates/<id_delivery>', methods=['POST'])
@login_required
@staff_permission.require(http_exception=403)
@csrf.exempt
def consolidate_duplicates(id_delivery):
    """Konsolidacja duplikatów produktów dla danej dostawy po numerze ASIN"""
    try:
        logger.info(f"Rozpoczynam konsolidację duplikatów dla dostawy {id_delivery}")
        
        # Znajdź wszystkie produkty dla danej dostawy
        products = WeryfikacjaProduktow.query.filter_by(id_delivery=id_delivery).all()
        
        if not products:
            return jsonify({
                'success': False,
                'error': 'Nie znaleziono produktów dla tej dostawy'
            }), 404
            
        # Słownik do grupowania produktów po ASIN
        grouped_products = {}
        
        # Grupowanie produktów po ASIN
        for product in products:
            if product.asin_code:  # Tylko produkty z kodem ASIN
                key = product.asin_code
                if key not in grouped_products:
                    grouped_products[key] = []
                grouped_products[key].append(product)
                logger.info(f"Produkt {product.id_weryfikacja} ({product.product_name}) dodany do grupy {key}")
        
        # Statystyki
        duplicates_found = False
        consolidated_count = 0
        price_mismatch_count = 0
        price_mismatch_products = {}
        
        # Przetwarzanie grup produktów
        for asin, products_list in grouped_products.items():
            if len(products_list) > 1:
                logger.info(f"Znaleziono {len(products_list)} produktów z ASIN {asin}")
                duplicates_found = True
                
                # Sprawdź zgodność cen
                base_price = products_list[0].price
                same_price = all(abs(float(p.price or 0) - float(base_price or 0)) < 0.01 for p in products_list)
                
                if same_price:
                    # Konsoliduj produkty
                    main_product = products_list[0]
                    total_quantity = sum(p.total_quantity for p in products_list)
                    total_price = float(base_price) * total_quantity if base_price else 0
                    
                    logger.info(f"Konsoliduję produkty z ASIN {asin}:")
                    logger.info(f"- Suma ilości: {total_quantity}")
                    logger.info(f"- Cena jednostkowa: {base_price}")
                    logger.info(f"- Wartość całkowita: {total_price}")
                    
                    # Zapisz informacje o konsolidacji
                    consolidated_info = {
                        'consolidated_at': datetime.now().isoformat(),
                        'consolidated_by': current_user.id_staff,
                        'original_quantity': main_product.total_quantity,
                        'new_quantity': total_quantity,
                        'consolidated_products': [{
                            'id_weryfikacja': p.id_weryfikacja,
                            'product_name': p.product_name,
                            'asin_code': p.asin_code,
                            'ean_code': p.ean_code,
                            'total_quantity': p.total_quantity,
                            'price': float(p.price) if p.price else None
                        } for p in products_list[1:]]
                    }
                    
                    # Aktualizuj główny produkt
                    main_product.total_quantity = total_quantity
                    main_product.total_price = total_price
                    
                    # Dodaj notatkę o konsolidacji
                    try:
                        current_notes = json.loads(main_product.verification_notes) if main_product.verification_notes else []
                        if not isinstance(current_notes, list):
                            current_notes = []
                    except:
                        current_notes = []
                    
                    current_notes.append({
                        'type': 'consolidation',
                        'data': consolidated_info
                    })
                    main_product.verification_notes = json.dumps(current_notes)
                    
                    # Usuń pozostałe duplikaty
                    for dup_product in products_list[1:]:
                        logger.info(f"Usuwam duplikat {dup_product.id_weryfikacja}")
                        db.session.delete(dup_product)
                    
                    consolidated_count += len(products_list) - 1
                else:
                    # Produkty z różnymi cenami
                    logger.warning(f"Znaleziono różne ceny dla ASIN {asin}")
                    prices = sorted(set([float(p.price) for p in products_list if p.price]))
                    price_mismatch_products[asin] = {
                        'count': len(products_list),
                        'prices': [f"{price:.2f} {products_list[0].delivery.currency}" for price in prices],
                        'products': [p.id_weryfikacja for p in products_list]
                    }
                    price_mismatch_count += len(products_list)
        
        # Zapisz zmiany
        if duplicates_found and consolidated_count > 0:
            db.session.commit()
            logger.info(f"Skonsolidowano {consolidated_count} duplikatów")
        
        return jsonify({
            'success': True,
            'duplicates_found': duplicates_found,
            'consolidated_count': consolidated_count,
            'price_mismatch_count': price_mismatch_count,
            'price_mismatch_products': price_mismatch_products,
            'message': f'Skonsolidowano {consolidated_count} duplikatów. {price_mismatch_count} produktów z różnymi cenami pozostawiono bez zmian.'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Błąd podczas konsolidacji duplikatów: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@staff_bp.route('/api/undo-consolidation/<id_delivery>', methods=['POST'])
@login_required
@staff_permission.require(http_exception=403)
@csrf.exempt
def undo_consolidation(id_delivery):
    """Dzieli skonsolidowane produkty na pojedyncze rekordy"""
    try:
        # Pobierz produkty dla dostawy
        products = WeryfikacjaProduktow.query.filter_by(id_delivery=id_delivery).all()
        
        if not products:
            return jsonify({
                'success': False,
                'message': 'Nie znaleziono produktów dla tej dostawy'
            }), 404
        
        # Licznik podziałów
        splits_made = 0
        
        # Znajdź produkty, które mają ilość większą niż 1
        for product in products:
            # Sprawdź czy produkt ma ilość większą niż 1
            if product.total_quantity > 1:
                # Pozyskaj oryginalne dane
                product_name = product.product_name
                asin_code = product.asin_code
                ean_code = product.ean_code
                price = product.price
                total_quantity = product.total_quantity
                
                # Ustaw ilość na 1 dla głównego produktu
                product.total_quantity = 1
                product.total_price = float(price) if price else 0
                
                # Utwórz nowe rekordy dla pozostałej ilości
                for i in range(total_quantity - 1):
                    new_product = WeryfikacjaProduktow(
                        id_delivery=id_delivery,
                        id_product=product.id_product,
                        product_name=product_name,
                        asin_code=asin_code,
                        ean_code=ean_code,
                        price=price,
                        total_quantity=1,
                        total_price=float(price) if price else 0,
                        verification_status='pending',
                        pallet_number=product.pallet_number,
                        lpn_number=product.lpn_number
                    )
                    
                    db.session.add(new_product)
                    splits_made += 1
        
        # Zapisz zmiany
        db.session.commit()
        
        if splits_made > 0:
            return jsonify({
                'success': True,
                'products_restored': splits_made,
                'message': f'Podzielono produkty na pojedyncze sztuki. Utworzono {splits_made} nowych rekordów.'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Nie znaleziono produktów do podziału.'
            }), 400
            
    except Exception as e:
        db.session.rollback()
        logger.error(f"Błąd podczas dzielenia produktów: {str(e)}")
        return jsonify({
            'success': False, 
            'message': f'Wystąpił błąd podczas dzielenia produktów: {str(e)}'
        }), 500

@staff_bp.route('/calendar')
@login_required
@staff_permission.require(http_exception=403)
def calendar():
    return render_template('staff/calendar.html')

@staff_bp.route('/meeting-room')
@login_required
@staff_permission.require(http_exception=403)
def meeting_room():
    return render_template('staff/meeting_room.html')

@staff_bp.route('/text-editor')
@login_required
@staff_permission.require(http_exception=403)
def text_editor():
    return render_template('staff/text_editor.html')

@staff_bp.route('/chat')
@login_required
@staff_permission.require(http_exception=403)
def chat():
    return render_template('staff/chat.html')

@staff_bp.route('/datatables')
@login_required
@staff_permission.require(http_exception=403)
def datatables():
    return render_template('staff/datatables.html')

@staff_bp.route('/kanban')
@login_required
@staff_permission.require(http_exception=403)
def kanban():
    return render_template('staff/kanban.html')

@staff_bp.route('/inbox')
@login_required
@staff_permission.require(http_exception=403)
def inbox():
    return render_template('staff/inbox.html')

@staff_bp.route('/tickets')
@login_required
@staff_permission.require(http_exception=403)
def tickets():
    return render_template('staff/tickets.html')

@staff_bp.route('/api')
@login_required
@staff_permission.require(http_exception=403)
def api():
    return render_template('staff/api.html') 