from flask import session
from . import db
import pymysql
from dotenv import load_dotenv
import os
from werkzeug.security import check_password_hash

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
            tuple: (bool - czy sukces, dict - dane użytkownika lub None)
        """
        try:
            load_dotenv()
            print(f"Próba logowania - email: {email}, rola: {role}")  # Debug
            
            conn = pymysql.connect(
                host=os.getenv('DB_HOST'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                database=os.getenv('DB_NAME'),
                connect_timeout=10
            )
            
            with conn.cursor() as cursor:
                # Sprawdzamy czy użytkownik istnieje w tabeli login_auth_data
                sql = "SELECT * FROM login_auth_data WHERE email = %s"
                if role:
                    sql += " AND role = %s"
                    cursor.execute(sql, (email, role))
                else:
                    cursor.execute(sql, (email,))
                    
                user = cursor.fetchone()
                print(f"Znaleziony użytkownik: {user}")  # Debug
                
                if user:
                    # Kolumny: id_login, related_id, email, password_hash, role, failed_login_attempts, locked_until, last_login, created_at, updated_at
                    user_id = user[0]  # id_login
                    related_id = user[1]  # related_id
                    user_email = user[2]  # email
                    stored_hash = user[3]  # password_hash
                    user_role = user[4]  # role
                    
                    print(f"Sprawdzam hasło dla użytkownika: {user_email}")  # Debug
                    print(f"Hash hasła w bazie: {stored_hash[:50]}...")  # Debug
                    
                    # Weryfikacja zahaszowanego hasła
                    if check_password_hash(stored_hash, password):
                        print(f"Hasło poprawne, aktualizuję sesję")  # Debug
                        
                        # Aktualizacja last_login
                        update_sql = "UPDATE login_auth_data SET last_login = CURRENT_TIMESTAMP WHERE id_login = %s"
                        cursor.execute(update_sql, (user_id,))
                        conn.commit()
                        
                        # Aktualizacja sesji
                        session['user_id'] = user_id
                        session['related_id'] = related_id
                        session['email'] = user_email
                        session['role'] = user_role
                        
                        # Pobierz dodatkowe dane użytkownika w zależności od roli
                        additional_data = {}
                        if user_role == 'supplier':
                            cursor.execute("SELECT * FROM login_table_suppliers WHERE id_supplier = %s", (related_id,))
                            supplier_data = cursor.fetchone()
                            if supplier_data:
                                additional_data = {
                                    'company_name': supplier_data[1],
                                    'first_name': supplier_data[2],
                                    'last_name': supplier_data[3]
                                }
                        elif user_role in ['admin', 'staff']:
                            cursor.execute("SELECT * FROM login_table_staff WHERE id_staff = %s", (related_id,))
                            staff_data = cursor.fetchone()
                            if staff_data:
                                additional_data = {
                                    'first_name': staff_data[1],
                                    'last_name': staff_data[2]
                                }
                        
                        conn.close()
                        return True, {
                            'id_login': user_id,
                            'related_id': related_id,
                            'email': user_email,
                            'role': user_role,
                            **additional_data
                        }
                    else:
                        # Aktualizacja liczby nieudanych prób logowania
                        update_sql = "UPDATE login_auth_data SET failed_login_attempts = failed_login_attempts + 1 WHERE id_login = %s"
                        cursor.execute(update_sql, (user_id,))
                        conn.commit()
                        print(f"Nieprawidłowe hasło")  # Debug
                
                conn.close()
                return False, None
                
        except Exception as e:
            print(f"Błąd logowania: {e}")  # Debug
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
            dict or None: dane zalogowanego użytkownika lub None
        """
        if 'user_id' in session:
            try:
                load_dotenv()
                conn = pymysql.connect(
                    host=os.getenv('DB_HOST'),
                    user=os.getenv('DB_USER'),
                    password=os.getenv('DB_PASSWORD'),
                    database=os.getenv('DB_NAME'),
                    connect_timeout=10
                )
                
                with conn.cursor() as cursor:
                    sql = "SELECT * FROM login_auth_data WHERE id_login = %s"
                    cursor.execute(sql, (session['user_id'],))
                    user = cursor.fetchone()
                    
                    if user:
                        user_data = {
                            'id_login': user[0],
                            'related_id': user[1],
                            'email': user[2],
                            'role': user[4]
                        }
                        
                        # Pobierz dodatkowe dane użytkownika w zależności od roli
                        if user[4] == 'supplier':  # role
                            cursor.execute("SELECT * FROM login_table_suppliers WHERE id_supplier = %s", (user[1],))
                            supplier_data = cursor.fetchone()
                            if supplier_data:
                                user_data.update({
                                    'company_name': supplier_data[1],
                                    'first_name': supplier_data[2],
                                    'last_name': supplier_data[3]
                                })
                        elif user[4] in ['admin', 'staff']:
                            cursor.execute("SELECT * FROM login_table_staff WHERE id_staff = %s", (user[1],))
                            staff_data = cursor.fetchone()
                            if staff_data:
                                user_data.update({
                                    'first_name': staff_data[1],
                                    'last_name': staff_data[2]
                                })
                        
                        conn.close()
                        return user_data
                
                conn.close()
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