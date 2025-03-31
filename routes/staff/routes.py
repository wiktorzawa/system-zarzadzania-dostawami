from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_user, logout_user, login_required, current_user
from flask_principal import Identity, AnonymousIdentity, identity_changed
from models.staff.staff import Staff
from models.MAIN.user import User
from __init__ import db, staff_permission, logger
import logging

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
    return render_template('staff/staff_dashboard.html')

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
    import datetime
    today = datetime.datetime.now().date()
    
    if date_filter == 'today':
        query = query.filter(DeliveryGeneral.delivery_date == today)
    elif date_filter == 'yesterday':
        yesterday = today - datetime.timedelta(days=1)
        query = query.filter(DeliveryGeneral.delivery_date == yesterday)
    elif date_filter == 'week':
        week_ago = today - datetime.timedelta(days=7)
        query = query.filter(DeliveryGeneral.delivery_date >= week_ago)
    elif date_filter == 'month':
        month_ago = today - datetime.timedelta(days=30)
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
        delivery_ids = data.get('delivery_ids', [])
        
        if not delivery_ids:
            return json.dumps({'success': False, 'message': 'Nie wybrano żadnych dostaw'}), 400, {'ContentType': 'application/json'}
        
        # Zaktualizuj status dostaw
        for delivery_id in delivery_ids:
            delivery = DeliveryGeneral.query.get(delivery_id)
            if delivery:
                delivery.status = 'processing'
                delivery.updated_at = db.func.now()
                
        db.session.commit()
        logger.info(f"Zmieniono status {len(delivery_ids)} dostaw na 'processing'")
        
        return json.dumps({'success': True, 'message': f'Pomyślnie zmieniono status {len(delivery_ids)} dostaw'}), 200, {'ContentType': 'application/json'}
        
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
        
        delivery_ids = ids.split(',')
        
        # Pobierz dostawy
        deliveries = []
        for delivery_id in delivery_ids:
            delivery = DeliveryGeneral.query.get(delivery_id)
            if delivery:
                delivery_dict = delivery.to_dict()
                # Dodaj nazwę dostawcy
                supplier = Supplier.query.get(delivery.id_supplier)
                delivery_dict['supplier_name'] = supplier.company_name if supplier else 'Nieznany'
                
                # Pobierz produkty dla dostawy
                products_count = DeliveryProduct.query.filter_by(id_delivery=delivery_id).count()
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
        from datetime import datetime
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

@staff_bp.route('/dostawa-szczegoly/<delivery_id>')
@login_required
@staff_permission.require(http_exception=403)
def staff_dostawa_szczegoly(delivery_id):
    """
    Wyświetla szczegóły dostawy o podanym ID.
    """
    from models.supplier.delivery_general import DeliveryGeneral
    from models.supplier.delivery_produkty_hybrid import DeliveryProduct
    from models.supplier.supplier import Supplier
    from models.supplier.delivery_file_data import DeliveryFileData
    
    logger.info(f"Dostęp do szczegółów dostawy {delivery_id} przez pracownika: {current_user.id_staff}")
    
    # Pobierz dostawę
    delivery = DeliveryGeneral.query.get_or_404(delivery_id)
    
    # Pobierz dostawcę
    supplier = Supplier.query.get(delivery.id_supplier)
    
    # Pobierz produkty z paginacją
    page = request.args.get('page', 1, type=int)
    products = DeliveryProduct.query.filter_by(id_delivery=delivery_id).paginate(
        page=page, per_page=50, error_out=False
    )
    
    # Pobierz pliki
    files = DeliveryFileData.query.filter_by(id_delivery=delivery_id).all()
    
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

@staff_bp.route('/api/delivery/<delivery_id>/products')
@login_required
@staff_permission.require(http_exception=403)
def staff_delivery_products(delivery_id):
    """
    Endpoint API do pobierania produktów dla konkretnej dostawy.
    """
    from models.supplier.delivery_general import DeliveryGeneral
    from models.supplier.delivery_produkty_hybrid import DeliveryProduct
    import json
    from flask import jsonify
    
    logger.info(f"Pobieranie produktów dla dostawy: {delivery_id}")
    
    try:
        # Sprawdź czy dostawa istnieje
        delivery = DeliveryGeneral.query.filter_by(id_delivery=delivery_id).first()
        if not delivery:
            logger.warning(f"Nie znaleziono dostawy o ID: {delivery_id}")
            return jsonify({"error": "Nie znaleziono dostawy", "products": []}), 404
        
        # Pobierz produkty
        products = DeliveryProduct.query.filter_by(id_delivery=delivery_id).all()
        logger.info(f"Znaleziono {len(products)} produktów dla dostawy {delivery_id}")
        
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