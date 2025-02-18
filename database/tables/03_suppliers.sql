-- --------------------------------------------------------
-- Tabela: suppliers
-- Opis: Tabela przechowująca dane firm dostawców
-- --------------------------------------------------------

CREATE TABLE IF NOT EXISTS suppliers (
    -- Klucz główny
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Powiązanie z kontem użytkownika
    user_id INT NOT NULL UNIQUE COMMENT 'ID z tabeli login_data - relacja jeden do jednego',
    
    -- Numer dostawcy
    supplier_number VARCHAR(20) NOT NULL UNIQUE COMMENT 'Unikalny numer dostawcy (np. SUPL/2024/0001)',
    
    -- Dane firmy
    company_name VARCHAR(255) NOT NULL COMMENT 'Nazwa firmy',
    nip VARCHAR(10) NOT NULL UNIQUE COMMENT 'Numer NIP',
    regon VARCHAR(14) COMMENT 'Numer REGON',
    
    -- Adres firmy
    company_address TEXT NOT NULL COMMENT 'Adres siedziby',
    company_city VARCHAR(100) NOT NULL COMMENT 'Miasto',
    company_postal_code VARCHAR(6) NOT NULL COMMENT 'Kod pocztowy',
    company_phone VARCHAR(20) NOT NULL COMMENT 'Telefon firmowy',
    
    -- Dane osoby kontaktowej
    first_name VARCHAR(50) NOT NULL COMMENT 'Imię osoby kontaktowej',
    last_name VARCHAR(50) NOT NULL COMMENT 'Nazwisko osoby kontaktowej',
    contact_person_position VARCHAR(100) COMMENT 'Stanowisko osoby kontaktowej',
    
    -- Dodatkowe dane kontaktowe
    additional_email VARCHAR(255) COMMENT 'Dodatkowy adres email',
    additional_phone VARCHAR(20) COMMENT 'Dodatkowy numer telefonu',
    preferred_contact_method ENUM('email', 'phone') DEFAULT 'email' COMMENT 'Preferowana metoda kontaktu',
    
    -- Dodatkowe informacje
    notes TEXT COMMENT 'Dodatkowe uwagi i notatki',
    
    -- Status weryfikacji
    verification_status ENUM('pending', 'verified', 'rejected') DEFAULT 'pending' COMMENT 'Status weryfikacji dostawcy',
    verification_date TIMESTAMP NULL COMMENT 'Data weryfikacji',
    verified_by INT NULL COMMENT 'ID pracownika który zweryfikował',
    
    -- Znaczniki czasowe
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Data utworzenia wpisu',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Data ostatniej aktualizacji',
    
    -- Klucze obce
    FOREIGN KEY (user_id) REFERENCES login_data(id) ON DELETE RESTRICT ON UPDATE CASCADE,
    FOREIGN KEY (verified_by) REFERENCES staff(id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Tabela przechowująca dane firm dostawców';

-- Indeksy
CREATE INDEX idx_suppliers_number ON suppliers(supplier_number) COMMENT 'Indeks do wyszukiwania po numerze dostawcy';
CREATE INDEX idx_suppliers_nip ON suppliers(nip) COMMENT 'Indeks do wyszukiwania po NIP';
CREATE INDEX idx_suppliers_status ON suppliers(verification_status) COMMENT 'Indeks do filtrowania po statusie weryfikacji';
CREATE INDEX idx_suppliers_company ON suppliers(company_name) COMMENT 'Indeks do wyszukiwania po nazwie firmy';

-- Komentarz do tabeli
ALTER TABLE suppliers COMMENT = 'Tabela zawierająca szczegółowe dane firm dostawców wraz z danymi kontaktowymi'; 