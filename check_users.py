from app import app, db
import pymysql
from dotenv import load_dotenv
import os

def check_tables():
    load_dotenv()
    
    try:
        conn = pymysql.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
            connect_timeout=10
        )
        
        with conn.cursor() as cursor:
            print("\nSprawdzam tabelę login_data:")
            cursor.execute("SELECT * FROM login_data")
            login_data = cursor.fetchall()
            if login_data:
                for user in login_data:
                    print(f"ID: {user[0]}")
                    print(f"Email: {user[1]}")
                    print(f"Rola: {user[3]}")
                    print("-" * 30)
            else:
                print("Tabela login_data jest pusta")
            
            print("\nSprawdzam tabelę login_auth_data:")
            cursor.execute("SELECT * FROM login_auth_data")
            auth_data = cursor.fetchall()
            if auth_data:
                for auth in auth_data:
                    print(f"ID: {auth[0]}")
                    print(f"Email: {auth[1]}")
                    print(f"Hasło: {auth[2][:20]}...")  # Pokazujemy tylko początek hasła
                    print("-" * 30)
            else:
                print("Tabela login_auth_data jest pusta")
        
        conn.close()
        
    except Exception as e:
        print(f"Błąd podczas sprawdzania tabel: {e}")

if __name__ == "__main__":
    check_tables() 