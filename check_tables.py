import pymysql
from dotenv import load_dotenv
import os

def check_tables_structure():
    load_dotenv()
    
    try:
        conn = pymysql.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
            connect_timeout=10
        )
        
        tables = [
            'login_auth_data',
            'login_data',
            'login_history_data',
            'login_table_staff',
            'login_table_suppliers'
        ]
        
        with conn.cursor() as cursor:
            for table in tables:
                print(f"\nStruktura tabeli {table}:")
                cursor.execute(f"DESCRIBE {table}")
                columns = cursor.fetchall()
                for col in columns:
                    print(f"{col[0]}: {col[1]}")
                print("-" * 50)
                
                print(f"\nPrzykładowe dane z tabeli {table}:")
                cursor.execute(f"SELECT * FROM {table} LIMIT 1")
                data = cursor.fetchone()
                if data:
                    print(data)
                else:
                    print("Brak danych")
                print("=" * 50)
        
        conn.close()
        
    except Exception as e:
        print(f"Błąd podczas sprawdzania struktury tabel: {e}")

if __name__ == "__main__":
    check_tables_structure() 