from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_app(app):
    db.init_app(app)
    
    # Importy modeli
    from .MAIN.user import User
    from .MAIN.auth import Auth
    from .supplier.supplier import Supplier
    from .staff.staff import Staff
    
    # Tworzenie tabel
    with app.app_context():
        db.create_all()

__all__ = ['User', 'Auth', 'Supplier', 'Staff'] 