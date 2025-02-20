from flask import Blueprint, render_template, request, redirect, url_for, flash
from ...models.MAIN import Auth

supplier_bp = Blueprint('supplier', __name__)

@supplier_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        success, user = Auth.login_user(email, password, role='supplier')
        if success:
            return redirect(url_for('supplier.dashboard'))
        else:
            flash('Nieprawidłowy email lub hasło', 'error')
            
    return render_template('supplier/login_supplier.html')

@supplier_bp.route('/dashboard')
def dashboard():
    if not Auth.is_authenticated() or not Auth.has_role('supplier'):
        return redirect(url_for('supplier.login'))
    return render_template('supplier/supplier_dashboard.html')

@supplier_bp.route('/nowa_dostawa', methods=['GET', 'POST'])
def nowa_dostawa():
    if not Auth.is_authenticated() or not Auth.has_role('supplier'):
        return redirect(url_for('supplier.login'))
    
    if request.method == 'POST':
        # Pobieranie danych z formularza
        delivery_date = request.form.get('delivery_date')
        delivery_time = request.form.get('delivery_time')
        vehicle_type = request.form.get('vehicle_type')
        packages_count = request.form.get('packages_count')
        total_weight = request.form.get('total_weight')
        special_requirements = request.form.get('special_requirements')
        notes = request.form.get('notes')
        
        # TODO: Dodać zapis do bazy danych
        
        flash('Dostawa została pomyślnie zarejestrowana', 'success')
        return redirect(url_for('supplier.dashboard'))
        
    return render_template('supplier/supplier_nowa_dostawa.html')

@supplier_bp.route('/dostawy_weryfikacja')
def dostawy_weryfikacja():
    if not Auth.is_authenticated() or not Auth.has_role('supplier'):
        return redirect(url_for('supplier.login'))
    return render_template('supplier/supplier_dostawy_weryfikacja.html')

@supplier_bp.route('/negocjacje')
def negocjacje():
    if not Auth.is_authenticated() or not Auth.has_role('supplier'):
        return redirect(url_for('supplier.login'))
    return render_template('supplier/supplier_negocjacje.html')

@supplier_bp.route('/rozliczenia')
def rozliczenia():
    if not Auth.is_authenticated() or not Auth.has_role('supplier'):
        return redirect(url_for('supplier.login'))
    return render_template('supplier/supplier_rozliczenia.html')

@supplier_bp.route('/profil')
def profil():
    if not Auth.is_authenticated() or not Auth.has_role('supplier'):
        return redirect(url_for('supplier.login'))
    return render_template('supplier/supplier_profil.html') 