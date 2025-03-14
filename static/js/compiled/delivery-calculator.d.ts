/**
 * Interfejs dla danych produktu
 */
export interface DeliveryProductData {
    price: number;
    quantity: number;
    currency?: string;
}
/**
 * Interfejs dla ustawień dostawy
 */
export interface DeliverySettings {
    valuePercentage: number;
    vatRate: number;
    exchangeRate: number;
    priceType: 'net' | 'gross';
    currency: string;
}
/**
 * Interfejs dla wyników obliczeń dostawy
 */
export interface DeliveryCalculationResult {
    totalMarketValue: number;
    totalMarketValuePLN: number;
    baseValue: number;
    deliveryValue: number;
    vatAmount: number;
}
/**
 * Kalkulator wartości dostawy
 */
export declare class DeliveryCalculator {
    /**
     * Oblicza wartość dostawy na podstawie produktów i ustawień
     *
     * @param products - Lista produktów
     * @param settings - Ustawienia dostawy
     * @returns Wyniki obliczeń
     */
    static calculateDeliveryValue(products: DeliveryProductData[], settings: DeliverySettings): DeliveryCalculationResult;
    /**
     * Oblicza wartość dostawy na podstawie parametrów
     * (Wersja kompatybilna z istniejącym kodem)
     *
     * @param totalValue - Całkowita wartość rynkowa produktów
     * @param percentage - Procent wartości (0-100)
     * @param currency - Waluta (PLN lub EUR)
     * @param exchangeRate - Kurs wymiany dla EUR
     * @param vatRate - Stawka VAT (np. 23)
     * @param priceType - Typ ceny (net lub gross)
     * @returns Wyniki obliczeń
     */
    static calculateDeliveryValueSimple(totalValue: number, percentage: number, currency: string, exchangeRate?: number, vatRate?: number, priceType?: string): DeliveryCalculationResult;
}
