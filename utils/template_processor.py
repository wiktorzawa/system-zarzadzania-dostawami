#import re
#from bs4 import BeautifulSoup
#
#class TemplateProcessor:
#    def __init__(self, mapping):
#        self.mapping = mapping
#        
#    def process_html(self, html_content):
#        """Przetwarza zawartość HTML, zamieniając przykładowe dane na własne"""
#        # Używamy BeautifulSoup do parsowania HTML
#        soup = BeautifulSoup(html_content, 'html.parser')
#        
#        # Zamiana tekstów w nagłówkach tabel
#        for th in soup.find_all('th'):
#            text = th.get_text(strip=True)
#            if text in self.mapping:
#                th.string = self.mapping[text]
#        
#        # Zamiana przykładowych danych w komórkach
#        for td in soup.find_all('td'):
#            text = td.get_text(strip=True)
#            if text in self.mapping:
#                td.string = self.mapping[text]
#        
#        # Zamiana tekstów w etykietach
#        for label in soup.find_all('label'):
#            text = label.get_text(strip=True)
#            if text in self.mapping:
#                label.string = self.mapping[text]
#        
#        # Zamiana placeholderów w inputach
#        for input_tag in soup.find_all('input'):
#            placeholder = input_tag.get('placeholder', '')
#            if placeholder in self.mapping:
#                input_tag['placeholder'] = self.mapping[placeholder]
#        
#        return str(soup)
#
## Przykład użycia:
#FLOWBITE_MAPPING = {
#    # Mapowanie nagłówków tabel
#    'Product name': 'Nazwa produktu',
#    'Category': 'Kategoria',
#    'Price': 'Cena',
#    
#    # Mapowanie przykładowych danych
#    'Apple MacBook Pro 17"': 'Dostawa #12345',
#    'Laptop': 'Elektronika',
#    '$2999': '2999 PLN',
#    
#    # Mapowanie placeholderów
#    'Search for items': 'Szukaj produktów',
#    'Enter email': 'Wprowadź email',
#    
#    # Mapowanie etykiet formularzy
#    'Email address': 'Adres email',
#    'Password': 'Hasło'
#}
#
#def process_template_file(input_file, output_file, mapping=None):
#    """Przetwarza plik szablonu i zapisuje wynik"""
#    if mapping is None:
#        mapping = FLOWBITE_MAPPING
#        
#    processor = TemplateProcessor(mapping)
#    
#    with open(input_file, 'r', encoding='utf-8') as f:
#        content = f.read()
#    
#    processed_content = processor.process_html(content)
#    
#    with open(output_file, 'w', encoding='utf-8') as f:
#        f.write(processed_content)
#
## Funkcja pomocnicza do ekstrakcji przykładowych danych z szablonu
#def extract_sample_data(html_file):
#    """Wyciąga przykładowe dane z szablonu Flowbite"""
#    with open(html_file, 'r', encoding='utf-8') as f:
#        content = f.read()
#    
#    soup = BeautifulSoup(content, 'html.parser')
#    sample_data = set()
#    
#    # Zbieramy teksty z różnych elementów
#    for element in soup.find_all(['th', 'td', 'label', 'input', 'button', 'a']):
#        if element.name == 'input':
#            placeholder = element.get('placeholder')
#            if placeholder:
#                sample_data.add(placeholder)
#        else:
#            text = element.get_text(strip=True)
#            if text:
#                sample_data.add(text)
#    
#    return sorted(list(sample_data)) 