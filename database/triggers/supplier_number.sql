DELIMITER //

CREATE TRIGGER generate_supplier_number
BEFORE INSERT ON suppliers
FOR EACH ROW
BEGIN
    DECLARE year VARCHAR(4);
    DECLARE next_number INT;
    
    -- Pobierz aktualny rok
    SET year = YEAR(CURRENT_DATE());
    
    -- Znajdź najwyższy numer dla danego roku
    SELECT IFNULL(MAX(CAST(SUBSTRING_INDEX(supplier_number, '/', -1) AS UNSIGNED)), 0) + 1
    INTO next_number
    FROM suppliers
    WHERE supplier_number LIKE CONCAT('SUPL/', year, '/%');
    
    -- Ustaw nowy numer dostawcy
    SET NEW.supplier_number = CONCAT('SUPL/', year, '/', LPAD(next_number, 4, '0'));
END //

DELIMITER ; 