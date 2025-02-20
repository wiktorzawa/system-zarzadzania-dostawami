from flask import Blueprint, render_template, redirect, url_for
from ...models.MAIN import Auth

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@main_bp.route('/index')
def index():
    return render_template('MAIN/index.html')

@main_bp.route('/logout')
def logout():
    Auth.logout_user()
    return redirect(url_for('main.index')) 