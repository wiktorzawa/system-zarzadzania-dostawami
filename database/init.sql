-- Usuwanie starej bazy danych
DROP DATABASE IF EXISTS msbox_db;

-- Tworzenie bazy danych z określonym kodowaniem
CREATE DATABASE msbox_db
    CHARACTER SET = 'utf8mb4'
    COLLATE = 'utf8mb4_unicode_ci';

USE msbox_db;

-- Ustawienie domyślnego kodowania dla sesji
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;
SET collation_connection = utf8mb4_unicode_ci;

-- Importowanie tabel (w kolejności zależności)
SOURCE tables/01_login_data.sql;   -- Tabela danych logowania (podstawowa)
SOURCE tables/02_staff.sql;        -- Tabela pracowników (zależy od login_data)
SOURCE tables/03_suppliers.sql;     -- Tabela dostawców (zależy od login_data i staff)

-- Importowanie triggerów
SOURCE triggers/supplier_number.sql;  -- Generator numerów dostawców

-- Importowanie procedur
SOURCE procedures/register_supplier.sql;  -- Procedura rejestracji dostawcy

-- Importowanie danych przykładowych (na końcu)
SOURCE data/sample_data.sql;  -- Przykładowe dane (admin, pracownik) 