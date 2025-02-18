-- Przykładowy administrator
INSERT INTO login_data (email, password_hash, role, active) VALUES 
('admin@msbox.com', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'admin', TRUE);

-- Dane administratora w tabeli staff
INSERT INTO staff (user_id, first_name, last_name, position, department) VALUES 
(LAST_INSERT_ID(), 'Administrator', 'Systemu', 'Administrator', 'IT');

-- Przykładowy pracownik
INSERT INTO login_data (email, password_hash, role, active) VALUES 
('pracownik@msbox.com', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'staff', TRUE);

-- Dane pracownika w tabeli staff
INSERT INTO staff (user_id, first_name, last_name, position, department) VALUES 
(LAST_INSERT_ID(), 'Jan', 'Kowalski', 'Specjalista ds. Zakupów', 'Zakupy');

-- Przykładowy dostawca
CALL register_supplier(
    -- Dane logowania
    'firma@przyklad.pl',
    '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi',
    
    -- Dane firmy
    'Przykładowa Firma Sp. z o.o.',
    '1234567890',
    '123456789',
    'ul. Przykładowa 1',
    'Warszawa',
    '00-001',
    '+48 123 456 789',
    
    -- Dane osoby kontaktowej
    'Anna',
    'Nowak',
    'Dyrektor Handlowy',
    
    -- Dodatkowe dane kontaktowe
    'handlowy@przyklad.pl',
    '+48 987 654 321',
    'email'
); 