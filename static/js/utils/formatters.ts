export interface FormatOptions {
    currency?: string;
    decimals?: number;
    useGrouping?: boolean;
}

/**
 * Formatuje wartość walutową zgodnie z polskim formatem
 * @param value - wartość do sformatowania
 * @param options - opcje formatowania
 * @returns sformatowany string w formacie polskim
 */
export function formatCurrency(value: number | string | null | undefined, options: FormatOptions = {}): string {
    const {
        currency = 'PLN',
        decimals = 2,
        useGrouping = true
    } = options;

    // Obsługa wartości null/undefined/pustych
    if (value === null || value === undefined || value === '') {
        return currency === 'PLN' ? '0,00 zł' : '0,00 €';
    }

    try {
        // Konwersja na liczbę
        const numValue = typeof value === 'string' 
            ? parseFloat(value.replace(/\s/g, '').replace(',', '.'))
            : value;

        // Sprawdzenie czy liczba jest poprawna
        if (isNaN(numValue)) {
            return currency === 'PLN' ? '0,00 zł' : '0,00 €';
        }

        // Formatowanie w stylu polskim
        const formatted = new Intl.NumberFormat('pl-PL', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals,
            useGrouping: useGrouping
        }).format(numValue);

        // Dodanie symbolu waluty
        switch (currency) {
            case 'PLN':
                return `${formatted} zł`;
            case 'EUR':
                return `${formatted} €`;
            default:
                return `${formatted} ${currency}`;
        }
    } catch (error) {
        console.error('Błąd formatowania waluty:', error);
        return currency === 'PLN' ? '0,00 zł' : '0,00 €';
    }
}

/**
 * Formatuje kurs wymiany zgodnie z polskim formatem
 * @param value - wartość do sformatowania
 * @returns sformatowany string w formacie polskim
 */
export function formatExchangeRate(value: number | string | null | undefined): string {
    return formatCurrency(value, { decimals: 4, useGrouping: false }).replace(/[^0-9,]/g, '');
} 