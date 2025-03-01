from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user import User
from .auth import Auth

__all__ = ['db', 'User', 'Auth'] 