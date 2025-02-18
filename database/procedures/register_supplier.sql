DELIMITER //

CREATE PROCEDURE register_supplier(
    -- Dane logowania
    IN p_email VARCHAR(255),
    IN p_password_hash VARCHAR(255),
    
    -- Dane firmy
    IN p_company_name VARCHAR(255),
    IN p_nip VARCHAR(10),
    IN p_regon VARCHAR(14),
    IN p_company_address TEXT,
    IN p_company_city VARCHAR(100),
    IN p_company_postal_code VARCHAR(6),
    IN p_company_phone VARCHAR(20),
    
    -- Dane osoby kontaktowej
    IN p_first_name VARCHAR(50),
    IN p_last_name VARCHAR(50),
    IN p_contact_person_position VARCHAR(100),
    
    -- Dodatkowe dane kontaktowe
    IN p_additional_email VARCHAR(255),
    IN p_additional_phone VARCHAR(20),
    IN p_preferred_contact_method ENUM('email', 'phone')
)
BEGIN
    -- Deklaracje
    DECLARE v_user_id INT;
    DECLARE CONTINUE HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    -- Rozpocznij transakcję
    START TRANSACTION;
    
    -- Utwórz konto użytkownika
    INSERT INTO login_data (email, password_hash, role, active)
    VALUES (p_email, p_password_hash, 'supplier', TRUE);
    
    -- Pobierz ID utworzonego użytkownika
    SET v_user_id = LAST_INSERT_ID();
    
    -- Utwórz wpis dostawcy
    INSERT INTO suppliers (
        user_id,
        company_name,
        nip,
        regon,
        company_address,
        company_city,
        company_postal_code,
        company_phone,
        first_name,
        last_name,
        contact_person_position,
        additional_email,
        additional_phone,
        preferred_contact_method
    ) VALUES (
        v_user_id,
        p_company_name,
        p_nip,
        p_regon,
        p_company_address,
        p_company_city,
        p_company_postal_code,
        p_company_phone,
        p_first_name,
        p_last_name,
        p_contact_person_position,
        p_additional_email,
        p_additional_phone,
        p_preferred_contact_method
    );
    
    -- Zatwierdź transakcję
    COMMIT;
END //

DELIMITER ; 