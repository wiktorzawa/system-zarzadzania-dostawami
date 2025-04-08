#!/usr/bin/env python3
import os
from pathlib import Path
import http.server
import socketserver
import webbrowser
import shutil
import sys
import re

# Konfiguracja ścieżek
FLOWBITE_DIR = Path('static/js/vendor/flowbite-pro')
CONTENT_DIR = FLOWBITE_DIR / 'content'
TEMPLATES_DIR = Path('templates')

# Konfiguracja serwera
PORT = 8080
PREVIEW_URL = f"http://localhost:{PORT}/static/js/vendor/flowbite-pro/content"

def clear_screen():
    """Czyści ekran terminala"""
    os.system('cls' if os.name == 'nt' else 'clear')

def list_templates():
    """Zwraca listę wszystkich szablonów HTML z katalogu content"""
    templates = []
    for root, _, files in os.walk(CONTENT_DIR):
        for file in files:
            if file.endswith('.html'):
                rel_path = os.path.relpath(os.path.join(root, file), CONTENT_DIR)
                templates.append(rel_path)
    return sorted(templates)

def list_templates_by_category():
    """Grupuje szablony według kategorii"""
    templates = list_templates()
    templates_by_category = {}
    
    for template in templates:
        category = template.split('/')[0] if '/' in template else 'other'
        if category not in templates_by_category:
            templates_by_category[category] = []
        templates_by_category[category].append(template)
    
    return templates_by_category

def display_templates():
    """Wyświetla listę wszystkich szablonów pogrupowanych według kategorii"""
    templates_by_category = list_templates_by_category()
    
    print("Dostępne szablony Flowbite Pro:\n")
    
    for i, (category, templates) in enumerate(sorted(templates_by_category.items()), 1):
        print(f"{i}. {category.upper()} ({len(templates)} szablonów)")
        
        for j, template in enumerate(sorted(templates), 1):
            print(f"   {i}.{j}. {template}")
        
        print()
    
    return templates_by_category

def copy_template(template_path, destination=None):
    """Kopiuje szablon do katalogu templates"""
    source_path = CONTENT_DIR / template_path
    
    if destination is None:
        # Automatycznie wybierz docelowy katalog na podstawie kategorii
        if '/' in template_path:
            category = template_path.split('/')[0]
            # Mapuj kategorie Flowbite na nasze kategorie projektu
            category_map = {
                'authentication': 'auth',
                'e-commerce': 'staff',
                'homepages': 'main',
                'pages': 'staff',
                'project-management': 'staff'
            }
            target_dir = TEMPLATES_DIR / category_map.get(category, 'staff')
        else:
            target_dir = TEMPLATES_DIR / 'staff'
    else:
        target_dir = TEMPLATES_DIR / destination
    
    # Upewnij się, że katalog docelowy istnieje
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Utwórz nazwę pliku docelowego
    filename = os.path.basename(template_path)
    base_name = os.path.splitext(filename)[0]
    target_path = target_dir / f"flowbite_{base_name}.html"
    
    # Wczytaj zawartość szablonu źródłowego
    with open(source_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Przetwórz zawartość szablonu - zastąp ścieżki, dodaj strukturę Jinja itp.
    content = content.replace('../../', '/static/js/vendor/flowbite-pro/')
    
    # Usuń część frontmatter (jeśli istnieje)
    content = re.sub(r'^---\n.*?---\n', '', content, flags=re.DOTALL)
    
    # Dodaj odpowiednie rozszerzenie Jinja2
    if 'staff' in str(target_dir):
        content = '{% extends "staff/staff_base_flowbite.html" %}\n\n{% block staff_content %}\n' + content + '\n{% endblock %}'
    elif 'auth' in str(target_dir):
        content = '{% extends "base.html" %}\n\n{% block content %}\n' + content + '\n{% endblock %}'
    else:
        content = '{% extends "base.html" %}\n\n{% block content %}\n' + content + '\n{% endblock %}'
    
    # Zapisz do pliku docelowego
    with open(target_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\nSkopiowano szablon do: {target_path}")
    print(f"UWAGA: Przed użyciem szablonu może być konieczne dostosowanie go do wymagań projektu.")
    
    return target_path

def preview_template(template_path):
    """Otwiera przeglądarkę z podglądem wybranego szablonu"""
    url = f"{PREVIEW_URL}/{template_path}"
    print(f"Otwieranie: {url}")
    webbrowser.open(url)

def start_server():
    """Uruchamia prosty serwer HTTP"""
    class QuietHTTPHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            # Wycisz logi serwera HTTP
            pass
    
    # Uruchom serwer w osobnym wątku
    handler = QuietHTTPHandler
    httpd = socketserver.TCPServer(("", PORT), handler)
    
    print(f"Serwer uruchomiony na porcie {PORT}")
    print("Naciśnij Ctrl+C, aby zakończyć\n")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Zatrzymywanie serwera...")
        httpd.server_close()
        sys.exit(0)

def interactive_menu():
    """Interaktywne menu do przeglądania i kopiowania szablonów"""
    import threading
    
    # Uruchom serwer HTTP w tle
    server_thread = threading.Thread(target=start_server)
    server_thread.daemon = True
    server_thread.start()
    
    try:
        while True:
            clear_screen()
            print("=" * 80)
            print("FLOWBITE PRO - PRZEGLĄDARKA SZABLONÓW".center(80))
            print("=" * 80)
            
            templates_by_category = display_templates()
            categories = sorted(templates_by_category.keys())
            
            print("\nDostępne opcje:")
            print("1-N. Wybierz kategorię")
            print("p. Podgląd szablonu")
            print("c. Kopiuj szablon")
            print("q. Wyjście")
            
            choice = input("\nWybór: ").strip().lower()
            
            if choice == 'q':
                print("Zamykanie przeglądarki...")
                break
            
            elif choice == 'p':
                template_path = input("Podaj ścieżkę szablonu do podglądu: ")
                if template_path:
                    preview_template(template_path)
                    input("\nNaciśnij Enter, aby kontynuować...")
            
            elif choice == 'c':
                template_path = input("Podaj ścieżkę szablonu do skopiowania: ")
                if template_path:
                    dest = input("Podaj folder docelowy (staff, auth, main) [domyślnie: staff]: ").strip() or "staff"
                    copy_template(template_path, dest)
                    input("\nNaciśnij Enter, aby kontynuować...")
            
            elif choice.isdigit() and 1 <= int(choice) <= len(categories):
                category_idx = int(choice) - 1
                category = categories[category_idx]
                templates = templates_by_category[category]
                
                clear_screen()
                print(f"Kategoria: {category.upper()}\n")
                
                for i, template in enumerate(templates, 1):
                    print(f"{i}. {template}")
                
                print("\nDostępne opcje:")
                print("1-N. Wybierz szablon do podglądu")
                print("c N. Kopiuj szablon numer N")
                print("b. Powrót")
                
                sub_choice = input("\nWybór: ").strip().lower()
                
                if sub_choice == 'b':
                    continue
                
                elif sub_choice.startswith('c ') and sub_choice[2:].isdigit():
                    template_idx = int(sub_choice[2:]) - 1
                    if 0 <= template_idx < len(templates):
                        dest = input("Podaj folder docelowy (staff, auth, main) [domyślnie: staff]: ").strip() or "staff"
                        copy_template(templates[template_idx], dest)
                        input("\nNaciśnij Enter, aby kontynuować...")
                
                elif sub_choice.isdigit() and 1 <= int(sub_choice) <= len(templates):
                    template_idx = int(sub_choice) - 1
                    preview_template(templates[template_idx])
                    input("\nNaciśnij Enter, aby kontynuować...")
    
    except KeyboardInterrupt:
        print("\nZamykanie przeglądarki...")
    
    sys.exit(0)

if __name__ == "__main__":
    if not FLOWBITE_DIR.exists():
        print(f"Błąd: Nie znaleziono katalogu {FLOWBITE_DIR}")
        print("Upewnij się, że skrypt jest uruchamiany z głównego katalogu projektu.")
        sys.exit(1)
    
    interactive_menu() 