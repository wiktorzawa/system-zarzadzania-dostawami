# System Zarządzania Dostawami

Aplikacja webowa do zarządzania dostawami z interfejsem dla administratorów, pracowników i dostawców.

## Funkcjonalności

- Panel logowania z różnymi rolami (Administrator, Pracownik, Dostawca)
- System zarządzania dostawami
- Interfejs dostosowany do różnych ról użytkowników
- Tryb ciemny/jasny

## Technologie

- Python (Backend)
- Flask (Framework webowy)
- Tailwind CSS (Style)
- Flowbite (Komponenty UI)
- JavaScript (Interakcje po stronie klienta)

## Instalacja

1. Sklonuj repozytorium:
```bash
git clone https://github.com/TWOJA-NAZWA-UZYTKOWNIKA/system-zarzadzania-dostawami.git
cd system-zarzadzania-dostawami
```

2. Zainstaluj zależności Pythona:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# lub
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

3. Zainstaluj zależności Node.js:
```bash
npm install
```

4. Uruchom aplikację:
```bash
python app.py
```

## Struktura projektu

```
├── templates/
│   ├── base.html
│   └── MAIN/
│       └── index.html
├── static/
│   ├── css/
│   └── js/
├── app.py
├── requirements.txt
├── package.json
└── tailwind.config.js
```

## Licencja

MIT 