import pymysql
from dotenv import load_dotenv
import os

# Ładowanie zmiennych środowiskowych
load_dotenv()

# Konfiguracja połączenia
db_config = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
    'port': int(os.getenv('DB_PORT', 3306))
}

try:
    # Próba połączenia
    connection = pymysql.connect(**db_config)
    print("Połączenie z bazą danych udane!")
    
    # Test zapytania
    with connection.cursor() as cursor:
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print("\nDostępne tabele:")
        for table in tables:
            print(f"- {table[0]}")
            
except Exception as e:
    print(f"Błąd połączenia z bazą danych: {e}")
finally:
    if 'connection' in locals():
        connection.close()
        print("\nPołączenie zamknięte.") 