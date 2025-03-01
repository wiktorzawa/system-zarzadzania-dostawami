import os
import sys
from pathlib import Path

# Dodaj katalog główny do ścieżki Pythona
sys.path.append(str(Path(__file__).parent))

from app import app

if __name__ == '__main__':
    app.run() 