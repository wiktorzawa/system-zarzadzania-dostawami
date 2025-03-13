import os
import sys
from pathlib import Path

# Dodaj katalog główny do ścieżki Pythona
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from __init__ import create_app

app = create_app(os.getenv('FLASK_ENV', 'default'))

if __name__ == '__main__':
    app.run(debug=True, port=5002)  # Zmieniam port na 5002, bo 5000 i 5001 są zajęte