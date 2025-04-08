import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import random
from flask import render_template

# Dodaj katalog główny do ścieżki Pythona
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from __init__ import create_app

app = create_app(os.getenv('FLASK_ENV', 'default'))

# Tymczasowa trasa do przeglądania szablonów Flowbite Pro
@app.route('/preview-template/<path:template_path>')
def preview_template(template_path):
    try:
        # Konstruuje pełną ścieżkę do pliku szablonu
        full_path = os.path.join('static/js/vendor/flowbite-pro/content', template_path)
        
        # Sprawdza, czy plik istnieje
        if not os.path.isfile(full_path):
            return f"Szablon '{template_path}' nie istnieje.", 404
        
        # Odczytuje zawartość pliku
        with open(full_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Zastępuje relatywne ścieżki do zasobów statycznych
        content = content.replace('../../', '/static/js/vendor/flowbite-pro/')
        
        return content
    except Exception as e:
        return f"Błąd podczas ładowania szablonu: {str(e)}", 500

# Tymczasowa trasa do testowania skopiowanego szablonu Flowbite
@app.route('/test-flowbite-template')
def test_flowbite_template():
    return render_template('staff/flowbite_products.html')

# Trasy testowe dla nowych szablonów Flowbite Pro
@app.route('/flowbite/login')
def flowbite_login():
    return render_template('staff/login_staff_flowbite.html')

@app.route('/flowbite/dashboard')
def flowbite_dashboard():
    # Przykładowe dane
    dostawy_count = 153
    weryfikacje_count = 28
    mystery_boxes = 423
    
    return render_template('staff/staff_dashboard_flowbite.html', 
                           dostawy_count=dostawy_count,
                           weryfikacje_count=weryfikacje_count,
                           mystery_boxes=mystery_boxes)

@app.route('/flowbite/dostawy')
def flowbite_dostawy():
    # Przykładowe dostawy
    dostawy = []
    for i in range(10):
        dostawy.append({
            'id': f'DEL00{i+1}',
            'supplier': ['Amazon', 'IKEA', 'Media Saturn', 'Samsung', 'LG Electronics'][i % 5],
            'created_at': datetime.now() - timedelta(days=i),
            'status': ['new', 'pending_verification', 'processing'][i % 3],
            'items': [{'id': j} for j in range(random.randint(5, 25))]
        })
    
    return render_template('staff/staff_nowe_dostawy_flowbite.html', dostawy=dostawy)

@app.route('/flowbite/weryfikacja')
def flowbite_weryfikacja():
    return render_template('staff/staff_weryfikacja_flowbite.html')

@app.route('/katalog_produktow_flowbite')
def katalog_produktow_flowbite():
    return render_template('staff/katalog_produktow_flowbite.html')

if __name__ == '__main__':
    app.run(debug=True, port=5002)  # Zmieniam port na 5002, bo 5000 i 5001 są zajęte