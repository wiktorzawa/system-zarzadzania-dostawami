from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
from flask_login import login_user, logout_user, login_required, current_user
from flask_principal import Identity, AnonymousIdentity, identity_changed
from models.staff.staff import Staff
from models.MAIN.user import User
from __init__ import db, admin_permission, logger
import logging

admin_bp = Blueprint('admin', __name__)

# Obsługa błędu 403 (Forbidden)
@admin_bp.errorhandler(403)
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
        flash('Nie masz uprawnień do dostępu do panelu administratora. Zostałeś wylogowany.', 'warning')
    else:
        flash('Nie masz uprawnień do dostępu do tej strony.', 'warning')
    
    # Przekieruj do strony głównej
    return redirect(url_for('main.index'))

@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    # Sprawdź, czy użytkownik jest już zalogowany
    if current_user.is_authenticated:
        # Jeśli użytkownik jest administratorem, przekieruj do panelu administratora
        if hasattr(current_user, 'id_staff') and User.query.filter_by(related_id=current_user.id_staff, role='admin').first():
            return redirect(url_for('admin.admin_dashboard'))
        # Jeśli użytkownik jest zalogowany, ale nie jest administratorem, wyloguj go
        else:
            logger.warning(f"Użytkownik {current_user.get_id()} próbuje uzyskać dostęp do panelu administratora, ale nie jest administratorem")
            logout_user()
            session.clear()
            # Usunięcie tożsamości w Flask-Principal
            identity_changed.send(current_app._get_current_object(),
                                identity=AnonymousIdentity())
            flash('Wylogowano z poprzedniej sesji. Zaloguj się jako administrator.', 'warning')
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        logger.info(f"Próba logowania administratora: {email}")
        
        auth_data = User.query.filter_by(email=email, role='admin').first()
        if not auth_data:
            logger.warning(f"Nieudane logowanie administratora - nieprawidłowy email: {email}")
            flash('Nieprawidłowy email lub hasło', 'error')
            return render_template('admin/login_admin.html')
            
        staff = Staff.query.filter_by(id_staff=auth_data.related_id).first()
        if not staff:
            logger.warning(f"Nieudane logowanie administratora - brak powiązanego pracownika dla: {email}")
            flash('Błąd konfiguracji konta', 'error')
            return render_template('admin/login_admin.html')
            
        if auth_data.verify_password(password):
            auth_data.failed_login_attempts = 0
            auth_data.last_login = db.func.now()
            db.session.commit()
            
            # Logowanie użytkownika w Flask-Login
            login_user(staff, remember=remember)
            logger.info(f"Administrator zalogowany pomyślnie: {email}, ID: {staff.id_staff}")
            
            # Ustawienie tożsamości w Flask-Principal
            identity = Identity(staff.id_staff)
            identity_changed.send(current_app._get_current_object(),
                                identity=identity)
            logger.info(f"Tożsamość Flask-Principal ustawiona dla administratora: {staff.id_staff}")
            
            return redirect(url_for('admin.admin_dashboard'))
            
        auth_data.failed_login_attempts += 1
        db.session.commit()
        logger.warning(f"Nieudane logowanie administratora - nieprawidłowe hasło: {email}")
        flash('Nieprawidłowy email lub hasło', 'error')
    
    return render_template('admin/login_admin.html')

@admin_bp.route('/dashboard')
@login_required
@admin_permission.require(http_exception=403)
def admin_dashboard():
    logger.info(f"Dostęp do panelu administratora: {current_user.id_staff if hasattr(current_user, 'id_staff') else 'Unknown'}")
    return render_template('admin/admin_dashboard.html') 