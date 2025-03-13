from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models.staff.staff import Staff
from models.MAIN.user import User
from __init__ import db

staff_bp = Blueprint('staff', __name__)

@staff_bp.route('/login', methods=['GET', 'POST'])
def login_staff():
    if current_user.is_authenticated:
        return redirect(url_for('staff.staff_dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        auth_data = User.query.filter_by(email=email).filter(User.role.in_(['admin', 'staff'])).first()
        if not auth_data:
            flash('Nieprawidłowy email lub hasło', 'error')
            return render_template('staff/login_staff.html')
            
        staff = Staff.query.filter_by(id_staff=auth_data.related_id).first()
        if not staff:
            flash('Błąd konfiguracji konta', 'error')
            return render_template('staff/login_staff.html')
            
        if auth_data.verify_password(password):
            auth_data.failed_login_attempts = 0
            auth_data.last_login = db.func.now()
            db.session.commit()
            
            login_user(staff, remember=remember)
            return redirect(url_for('staff.staff_dashboard'))
            
        auth_data.failed_login_attempts += 1
        db.session.commit()
        flash('Nieprawidłowy email lub hasło', 'error')
    
    return render_template('staff/login_staff.html')

@staff_bp.route('/logout')
@login_required
def logout_staff():
    logout_user()
    flash('Zostałeś wylogowany', 'info')
    return redirect(url_for('staff.login_staff'))

@staff_bp.route('/dashboard')
@login_required
def staff_dashboard():
    if not current_user.is_authenticated or current_user.role not in ['admin', 'staff']:
        flash('Brak dostępu do tej sekcji', 'error')
        return redirect(url_for('staff.login_staff'))
    return render_template('staff/staff_dashboard.html')

@staff_bp.route('/profile')
@login_required
def staff_profile():
    if not current_user.is_authenticated or current_user.role not in ['admin', 'staff']:
        flash('Brak dostępu do tej sekcji', 'error')
        return redirect(url_for('staff.login_staff'))
    return render_template('staff/staff_profile.html')

@staff_bp.route('/deliveries')
@login_required
def staff_deliveries():
    if not current_user.is_authenticated or current_user.role not in ['admin', 'staff']:
        flash('Brak dostępu do tej sekcji', 'error')
        return redirect(url_for('staff.login_staff'))
    return render_template('staff/staff_deliveries.html')

@staff_bp.route('/suppliers')
@login_required
def staff_suppliers():
    if not current_user.is_authenticated or current_user.role not in ['admin', 'staff']:
        flash('Brak dostępu do tej sekcji', 'error')
        return redirect(url_for('staff.login_staff'))
    return render_template('staff/staff_suppliers.html')

@staff_bp.route('/reports')
@login_required
def staff_reports():
    if not current_user.is_authenticated or current_user.role not in ['admin', 'staff']:
        flash('Brak dostępu do tej sekcji', 'error')
        return redirect(url_for('staff.login_staff'))
    return render_template('staff/staff_reports.html') 