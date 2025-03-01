import pymysql
import time

def test_connection():
    try:
        conn = pymysql.connect(
            host='flask-app-msbox.chqqwymic43o.us-east-1.rds.amazonaws.com',
            user='admin',
            password='1Nieporet!',
            database='msbox_db',
            connect_timeout=10
        )
        print("Połączenie udane!")
        
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            print(f"Test zapytania: {result}")
            
        conn.close()
        print("Połączenie zamknięte poprawnie")
        
    except Exception as e:
        print(f"Błąd połączenia: {e}")

if __name__ == "__main__":
    print("Próba połączenia z bazą danych...")
    test_connection() 