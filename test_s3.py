import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import os
from pathlib import Path

# Ładowanie zmiennych środowiskowych
env_path = Path(__file__).parent.absolute() / '.env'
print(f"\nŁadowanie zmiennych środowiskowych z: {env_path}")

if not env_path.exists():
    print(f"BŁĄD: Plik .env nie istnieje w lokalizacji: {env_path}")
    exit(1)

load_dotenv(dotenv_path=env_path, override=True)

# Sprawdź zmienne przed testem
print("\nZmienne środowiskowe:")
print(f"AWS_ACCESS_KEY_ID: {'*' * len(os.getenv('AWS_ACCESS_KEY_ID')) if os.getenv('AWS_ACCESS_KEY_ID') else 'Brak'}")
print(f"AWS_SECRET_ACCESS_KEY: {'*' * len(os.getenv('AWS_SECRET_ACCESS_KEY')) if os.getenv('AWS_SECRET_ACCESS_KEY') else 'Brak'}")
print(f"AWS_REGION: {os.getenv('AWS_REGION', 'us-east-1')}")
print(f"S3_BUCKET: {os.getenv('S3_BUCKET', '')}")

def test_s3_connection():
    try:
        # Konfiguracja klienta S3
        s3 = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        
        # Próba listowania bucketów
        response = s3.list_buckets()
        print("\nPołączenie z S3 udane!")
        print("\nDostępne buckety:")
        for bucket in response['Buckets']:
            print(f"- {bucket['Name']}")
            
        # Sprawdzenie konfiguracji bucketa aplikacji
        bucket_name = os.getenv('S3_BUCKET')
        if not bucket_name:
            print("\nUWAGA: Zmienna S3_BUCKET nie jest ustawiona w pliku .env")
            return
            
        try:
            s3.head_bucket(Bucket=bucket_name)
            print(f"\nBucket {bucket_name} istnieje i masz do niego dostęp!")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                print(f"\nBucket {bucket_name} nie istnieje!")
            elif error_code == '403':
                print(f"\nBrak dostępu do bucketa {bucket_name}!")
            else:
                print(f"\nBłąd podczas sprawdzania bucketa: {e}")
                
    except Exception as e:
        print(f"Błąd połączenia z S3: {e}")

if __name__ == '__main__':
    test_s3_connection() 