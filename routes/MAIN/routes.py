from flask import Blueprint, render_template, redirect, url_for
from flask_login import logout_user

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('MAIN/index.html')

@main_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index')) 