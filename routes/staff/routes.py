from flask import Blueprint, render_template, request, redirect, url_for, flash
from ...models.MAIN import Auth

staff_bp = Blueprint('staff', __name__)

@staff_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        success, user = Auth.login_user(email, password, role='staff')
        if success:
            return redirect(url_for('staff.dashboard'))
        else:
            flash('Nieprawidłowy email lub hasło', 'error')
            
    return render_template('staff/login_staff.html')

@staff_bp.route('/dashboard')
def dashboard():
    if not Auth.is_authenticated() or not Auth.has_role('staff'):
        return redirect(url_for('staff.login'))
    return render_template('staff/staff_dashboard.html') 