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