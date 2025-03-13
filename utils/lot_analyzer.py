import re
from typing import Optional, Tuple

class LotAnalyzer:
    """Klasa do analizy i walidacji numerów LOT"""
    
    # Wzorce do wyszukiwania LOT w nazwie pliku (case insensitive)
    LOT_PATTERNS = [
        r"(?:LOT|lot)[u\s_]*(?:PL|pl)?[_\s]*(\d{6,10})(?:_(\d{6}))?",    # LOTPL10021410_240506 lub LOT10021410
        r"(?:PL|pl)[_\s]*(?:LOT|lot)[_\s]*(\d{6,10})(?:_(\d{6}))?",      # PLLOT10021410_240506
    ]

    @staticmethod
    def analyze_filename(filename: str) -> Optional[Tuple[str, str]]:
        """
        Analizuje nazwę pliku w poszukiwaniu numeru LOT.
        
        Returns:
            Tuple[original_match, formatted_lot] lub None jeśli nie znaleziono
        """
        if not filename:
            return None
            
        # Usuń spacje z początku i końca
        filename = filename.strip()
        
        for pattern in LotAnalyzer.LOT_PATTERNS:
            # Szukaj wzorca w nazwie pliku
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                # Pobierz oryginalny znaleziony tekst
                original_match = match.group(0)
                
                # Pobierz numer LOT i opcjonalną datę
                lot_number = match.group(1)
                date_part = match.group(2) if len(match.groups()) > 1 else None
                
                # Walidacja długości numeru LOT
                if len(lot_number) < 6 or len(lot_number) > 10:
                    continue
                    
                # Walidacja daty jeśli istnieje
                if date_part and not LotAnalyzer._validate_date(date_part):
                    date_part = None
                
                # Sformatuj LOT
                formatted_lot = f"LOT{lot_number}"
                if date_part:
                    formatted_lot = f"{formatted_lot}_{date_part}"
                
                return original_match, formatted_lot
                
        return None

    @staticmethod
    def analyze_file_content(headers: list) -> bool:
        """
        Sprawdza czy w nagłówkach pliku znajduje się kolumna z numerem LOT.
        
        Returns:
            bool: True jeśli znaleziono kolumnę z LOT
        """
        if not headers:
            return False
            
        lot_column_patterns = [
            r'(?:^|\s)lot(?:\s|$)',
            r'numer.*partii',
            r'(?:^|\s)partia(?:\s|$)',
            r'nr.*partii',
            r'batch.*number',
            r'lot.*number'
        ]
        
        headers_str = ' '.join(str(h).lower() for h in headers if h)
        return any(re.search(pattern, headers_str, re.IGNORECASE) for pattern in lot_column_patterns)

    @staticmethod
    def analyze_lot_values(lot_values) -> dict:
        """
        Analizuje wartości w kolumnie LOT.
        
        Args:
            lot_values: Lista lub seria wartości LOT do przeanalizowania
            
        Returns:
            dict: Słownik z wynikami analizy:
                - has_valid_lots: bool, czy są jakieś poprawne numery LOT
                - valid_lots: list, lista poprawnych numerów LOT
                - all_empty: bool, czy wszystkie wartości są puste/None/NaN
        """
        if lot_values is None:
            return {
                'has_valid_lots': False,
                'valid_lots': [],
                'all_empty': True
            }

        # Konwertuj wszystkie wartości na string i usuń puste
        lot_values = [str(val).strip() if val is not None else '' for val in lot_values]
        
        # Sprawdź czy wszystkie wartości są puste/None/NaN
        all_empty = all(
            not val or 
            val.lower() == 'nan' or 
            val.lower() == 'none' or 
            val == ''
            for val in lot_values
        )
        
        # Znajdź poprawne numery LOT
        valid_lots = [
            lot for lot in lot_values 
            if lot and LotAnalyzer.validate_lot_format(lot)
        ]
        
        return {
            'has_valid_lots': bool(valid_lots),
            'valid_lots': valid_lots,
            'all_empty': all_empty
        }

    @staticmethod
    def validate_lot_format(lot_number: str) -> bool:
        """
        Sprawdza czy format numeru LOT jest prawidłowy.
        
        Akceptowane formaty:
        - LOT123456_YYMMDD
        - LOT123456
        gdzie:
        - 123456 to numer LOT (6-10 cyfr)
        - YYMMDD to opcjonalna data (6 cyfr)
        """
        if not lot_number:
            return False
            
        lot_number = lot_number.strip().upper()
        
        patterns = [
            r'^LOT\d{6,10}$',                # LOT123456
            r'^LOT\d{6,10}_\d{6}$'          # LOT123456_YYMMDD
        ]
        
        matches = any(re.match(pattern, lot_number) for pattern in patterns)
        if matches:
            # Jeśli jest data, sprawdź jej format
            if '_' in lot_number:
                date_part = lot_number.split('_')[1]
                return LotAnalyzer._validate_date(date_part)
            return True
            
        return False

    @staticmethod
    def format_lot_number(lot_number: str) -> Optional[str]:
        """
        Formatuje numer LOT do standardowego formatu.
        
        Returns:
            str: Sformatowany numer LOT lub None jeśli format jest nieprawidłowy
        """
        if not lot_number:
            return None
            
        # Usuń spacje i zamień na wielkie litery
        lot_number = lot_number.strip().upper()
        
        # Jeśli już jest w prawidłowym formacie
        if LotAnalyzer.validate_lot_format(lot_number):
            return lot_number
            
        # Próbuj wydobyć numer i opcjonalną datę
        for pattern in LotAnalyzer.LOT_PATTERNS:
            match = re.search(pattern, lot_number, re.IGNORECASE)
            if match:
                number = match.group(1)
                date = match.group(2) if len(match.groups()) > 1 else None
                
                # Walidacja długości numeru LOT
                if len(number) < 6 or len(number) > 10:
                    continue
                    
                # Walidacja daty jeśli istnieje
                if date and not LotAnalyzer._validate_date(date):
                    date = None
                
                formatted = f"LOT{number}"
                if date:
                    formatted = f"{formatted}_{date}"
                    
                return formatted
                
        return None

    @staticmethod
    def _validate_date(date_str: str) -> bool:
        """
        Sprawdza czy string jest poprawną datą w formacie YYMMDD.
        """
        if not date_str or len(date_str) != 6:
            return False
            
        try:
            yy = int(date_str[:2])
            mm = int(date_str[2:4])
            dd = int(date_str[4:])
            
            return (0 <= yy <= 99 and 1 <= mm <= 12 and 1 <= dd <= 31)
        except ValueError:
            return False 