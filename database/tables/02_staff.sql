-- --------------------------------------------------------
-- Tabela: staff
-- Opis: Tabela przechowująca dane pracowników (admin i staff)
-- --------------------------------------------------------

CREATE TABLE IF NOT EXISTS staff (
    -- Klucz główny
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Powiązanie z kontem użytkownika
    user_id INT NOT NULL UNIQUE COMMENT 'ID z tabeli login_data - relacja jeden do jednego',
    
    -- Dane osobowe
    first_name VARCHAR(50) NOT NULL COMMENT 'Imię pracownika',
    last_name VARCHAR(50) NOT NULL COMMENT 'Nazwisko pracownika',
    
    -- Dane służbowe
    position VARCHAR(100) COMMENT 'Stanowisko pracownika',
    department VARCHAR(100) COMMENT 'Dział/jednostka organizacyjna',
    internal_phone VARCHAR(20) COMMENT 'Numer telefonu wewnętrznego',
    
    -- Dodatkowe informacje
    notes TEXT COMMENT 'Dodatkowe uwagi i notatki',
    
    -- Klucz obcy
    FOREIGN KEY (user_id) REFERENCES login_data(id) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Tabela przechowująca dane pracowników systemu';

-- Indeksy
CREATE INDEX idx_staff_names ON staff(last_name, first_name) COMMENT 'Indeks do wyszukiwania po nazwisku i imieniu';

-- Komentarz do tabeli
ALTER TABLE staff COMMENT = 'Tabela zawierająca szczegółowe dane pracowników (administratorów i personelu)'; 