import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import os
from pathlib import Path
from datetime import datetime
import pymysql

# Ładowanie zmiennych środowiskowych
env_path = Path(__file__).parent.absolute() / '.env'
load_dotenv(dotenv_path=env_path, override=True)

def get_suppliers_from_db():
    """Pobiera listę dostawców z bazy danych"""
    try:
        # Konfiguracja połączenia z bazą danych
        connection = pymysql.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
            port=int(os.getenv('DB_PORT', 3306))
        )

        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # Pobierz dostawców z tabeli suppliers
            cursor.execute("""
                SELECT s.user_id, s.company_name, s.supplier_number
                FROM suppliers s
                JOIN login_data l ON s.user_id = l.id
                WHERE l.active = 1
            """)
            suppliers = cursor.fetchall()
            return suppliers

    except Exception as e:
        print(f"Błąd podczas pobierania dostawców z bazy: {e}")
        return []
    finally:
        if 'connection' in locals():
            connection.close()

def create_bucket_structure():
    try:
        # Konfiguracja klienta S3
        s3 = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        
        bucket_name = 'msbox-app-all'
        
        # Sprawdź czy bucket już istnieje
        try:
            s3.head_bucket(Bucket=bucket_name)
            print(f"\nBucket {bucket_name} już istnieje!")
        except ClientError as e:
            error_code = int(e.response['Error']['Code'])
            if error_code == 404:
                # Bucket nie istnieje, utworzmy go
                print(f"\nTworzenie bucketa {bucket_name}...")
                s3.create_bucket(Bucket=bucket_name)
                print(f"Bucket {bucket_name} został utworzony!")
            else:
                raise e

        # Pobierz dostawców z bazy
        suppliers = get_suppliers_from_db()
        if not suppliers:
            print("Nie znaleziono żadnych dostawców w bazie danych!")
            return

        # Aktualna data
        current_year = datetime.now().strftime('%Y')
        current_month = datetime.now().strftime('%m')
        
        # Podstawowa struktura folderów
        folders = [
            # Główny folder dla plików dostawców
            'oryginalne_pliki_dostawcow/',
            
            # Struktura dla zdjęć produktów
            'zdjecia_produktow/',
            'zdjecia_produktow/oryginalne/',
            'zdjecia_produktow/miniatury/',
            'zdjecia_produktow/full_size/',
        ]

        # Dodaj foldery dla każdego dostawcy
        for supplier in suppliers:
            supplier_folder = f"oryginalne_pliki_dostawcow/{supplier['user_id']}_{supplier['company_name']}/"
            folders.extend([
                supplier_folder,
                f"{supplier_folder}{current_year}/",
                f"{supplier_folder}{current_year}/{current_month}/",
            ])

        # Tworzenie struktury folderów
        print("\nTworzenie struktury folderów:")
        for folder in folders:
            # Zamień spacje i znaki specjalne w nazwach folderów
            safe_folder = folder.replace(' ', '_').replace('/', '/').replace('\\', '_')
            s3.put_object(Bucket=bucket_name, Key=safe_folder)
            print(f"- Utworzono folder: {safe_folder}")

        print("\nStruktura została pomyślnie utworzona!")
        
        # Wyświetl zawartość bucketa
        print("\nAktualna zawartość bucketa:")
        paginator = s3.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=bucket_name):
            if 'Contents' in page:
                for obj in page['Contents']:
                    print(f"- {obj['Key']}")

    except Exception as e:
        print(f"Wystąpił błąd: {e}")

if __name__ == '__main__':
    create_bucket_structure() 