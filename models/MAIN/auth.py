from flask import session
from .. import db
from .user import User

class Auth:
    @staticmethod
    def login_user(email, password, role=None):
        """
        Logowanie użytkownika
        Args:
            email: adres email użytkownika
            password: hasło użytkownika
            role: opcjonalna rola użytkownika do weryfikacji
        Returns:
            tuple: (bool - czy sukces, User - zalogowany użytkownik lub None)
        """
        try:
            query = User.query.filter_by(email=email)
            if role:
                query = query.filter_by(role=role)
            
            user = query.first()
            
            if user and user.verify_password(password):
                # Aktualizacja sesji
                session['user_id'] = user.id
                session['role'] = user.role
                session['email'] = user.email
                return True, user
            return False, None
        except Exception as e:
            print(f"Błąd logowania: {e}")
            return False, None

    @staticmethod
    def logout_user():
        """Wylogowanie użytkownika"""
        session.clear()

    @staticmethod
    def get_current_user():
        """
        Pobranie aktualnie zalogowanego użytkownika
        Returns:
            User or None: zalogowany użytkownik lub None
        """
        if 'user_id' in session:
            try:
                return User.query.get(session['user_id'])
            except Exception as e:
                print(f"Błąd pobierania użytkownika: {e}")
                return None
        return None

    @staticmethod
    def is_authenticated():
        """Sprawdza czy użytkownik jest zalogowany"""
        return 'user_id' in session

    @staticmethod
    def has_role(role):
        """Sprawdza czy zalogowany użytkownik ma daną rolę"""
        return session.get('role') == role 