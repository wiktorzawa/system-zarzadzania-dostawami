from __init__ import db
from .user import User

__all__ = ['db', 'User']

def init_app():
    # Rozszerzamy __all__
    global __all__
    __all__ = ['db', 'User']
    
    return {
        'User': User
    } 