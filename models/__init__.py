from .. import db

# Importy modeli
from .MAIN.user import User
from .MAIN.auth import Auth
from .supplier.supplier import Supplier
from .staff.staff import Staff

__all__ = ['User', 'Auth', 'Supplier', 'Staff']

def init_app(app):
    db.init_app(app) 