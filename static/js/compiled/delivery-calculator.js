/**
 * Kalkulator wartości dostawy
 */
export class DeliveryCalculator {
    /**
     * Oblicza wartość dostawy na podstawie produktów i ustawień
     *
     * @param products - Lista produktów
     * @param settings - Ustawienia dostawy
     * @returns Wyniki obliczeń
     */
    static calculateDeliveryValue(products, settings) {
        // Konwersja typów na liczby
        const valuePercentage = Number(settings.valuePercentage) || 0;
        const vatRate = Number(settings.vatRate) || 23;
        const exchangeRate = Number(settings.exchangeRate) || 1;
        const globalCurrency = settings.currency || "PLN";
        // Obliczenie sumy wartości produktów
        let totalMarketValue = 0;
        let totalMarketValuePLN = 0;
        for (const product of products) {
            const price = Number(product.price) || 0;
            const quantity = Number(product.quantity) || 0;
            // Wartość produktu
            const productValue = price * quantity;
            // Dodaj do sumy w oryginalnej walucie
            totalMarketValue += productValue;
            // Wartość w PLN zależy od globalnej waluty
            if (globalCurrency === "EUR") {
                totalMarketValuePLN += productValue * exchangeRate;
            }
            else {
                totalMarketValuePLN += productValue;
            }
        }
        // Obliczenie wartości bazowej (procent wartości rynkowej)
        const baseValue = totalMarketValuePLN * (valuePercentage / 100);
        // Obliczenie wartości końcowej z VAT
        let finalValue = baseValue;
        let vatAmount = 0;
        if (settings.priceType === "net") {
            finalValue = baseValue * (1 + vatRate / 100);
            vatAmount = finalValue - baseValue;
        }
        // Zaokrąglenie do 2 miejsc po przecinku
        finalValue = Math.round(finalValue * 100) / 100;
        vatAmount = Math.round(vatAmount * 100) / 100;
        return {
            totalMarketValue,
            totalMarketValuePLN,
            baseValue,
            deliveryValue: finalValue,
            vatAmount
        };
    }
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
    static calculateDeliveryValueSimple(totalValue, percentage, currency, exchangeRate = 1, vatRate = 23, priceType = "net") {
        // Konwersja typów na liczby
        totalValue = Number(totalValue) || 0;
        percentage = Number(percentage) || 0;
        exchangeRate = Number(exchangeRate) || 1;
        vatRate = Number(vatRate) || 23;
        // Obliczenie wartości w PLN
        const totalMarketValuePLN = currency === "EUR" ? totalValue * exchangeRate : totalValue;
        // Obliczenie wartości bazowej (procent wartości rynkowej)
        const baseValue = totalMarketValuePLN * (percentage / 100);
        // Obliczenie wartości końcowej z VAT
        let finalValue = baseValue;
        let vatAmount = 0;
        if (priceType === "net") {
            finalValue = baseValue * (1 + vatRate / 100);
            vatAmount = finalValue - baseValue;
        }
        // Zaokrąglenie do 2 miejsc po przecinku
        finalValue = Math.round(finalValue * 100) / 100;
        vatAmount = Math.round(vatAmount * 100) / 100;
        return {
            totalMarketValue: totalValue,
            totalMarketValuePLN: totalMarketValuePLN,
            baseValue: baseValue,
            deliveryValue: finalValue,
            vatAmount: vatAmount
        };
    }
}
//# sourceMappingURL=delivery-calculator.js.map