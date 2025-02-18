-- --------------------------------------------------------
-- Tabela: login_data
-- Opis: Podstawowa tabela do logowania i autoryzacji
-- --------------------------------------------------------

CREATE TABLE IF NOT EXISTS login_data (
    -- Klucz główny
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Dane logowania
    email VARCHAR(255) NOT NULL UNIQUE COMMENT 'Adres email służący do logowania',
    password_hash VARCHAR(255) NOT NULL COMMENT 'Zahaszowane hasło użytkownika',
    
    -- Uprawnienia i status
    role ENUM('admin', 'staff', 'supplier') NOT NULL COMMENT 'Rola użytkownika w systemie',
    active BOOLEAN DEFAULT true COMMENT 'Czy konto jest aktywne',
    
    -- Monitorowanie
    last_login TIMESTAMP NULL COMMENT 'Data ostatniego logowania',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Data utworzenia konta',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Data ostatniej aktualizacji'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Tabela przechowująca dane logowania użytkowników';

-- Indeksy
CREATE INDEX idx_login_data_email ON login_data(email) COMMENT 'Indeks przyśpieszający wyszukiwanie po emailu';

-- Komentarz do tabeli
ALTER TABLE login_data COMMENT = 'Tabela zawierająca podstawowe dane do logowania i autoryzacji użytkowników'; 