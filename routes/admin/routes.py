from flask import Blueprint, render_template, request, redirect, url_for, flash
from ...models.MAIN import Auth

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        success, user = Auth.login_user(email, password, role='admin')
        if success:
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Nieprawidłowy email lub hasło', 'error')
        
    return render_template('admin/login_admin.html')

@admin_bp.route('/dashboard')
def dashboard():
    if not Auth.is_authenticated() or not Auth.has_role('admin'):
        return redirect(url_for('admin.login'))
    return render_template('admin/admin_dashboard.html') 