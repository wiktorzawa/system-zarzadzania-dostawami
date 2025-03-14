/**
 * Testy jednostkowe dla kalkulatora wartości dostawy
 */
import { DeliveryCalculator } from './delivery-calculator';
describe('DeliveryCalculator', () => {
    test('calculateDeliveryValueSimple dla PLN', () => {
        // Parametry
        const totalValue = 1000;
        const percentage = 50;
        const currency = "PLN";
        const exchangeRate = 1;
        const vatRate = 23;
        const priceType = "net";
        // Obliczenie
        const result = DeliveryCalculator.calculateDeliveryValueSimple(totalValue, percentage, currency, exchangeRate, vatRate, priceType);
        // Oczekiwane wartości
        const expectedTotalMarketValue = 1000;
        const expectedTotalMarketValuePLN = 1000;
        const expectedBaseValue = 500; // 1000 * 50%
        const expectedDeliveryValue = 615; // 500 * 1.23
        const expectedVatAmount = 115; // 615 - 500
        // Asercje
        expect(result.totalMarketValue).toBe(expectedTotalMarketValue);
        expect(result.totalMarketValuePLN).toBe(expectedTotalMarketValuePLN);
        expect(result.baseValue).toBe(expectedBaseValue);
        expect(result.deliveryValue).toBe(expectedDeliveryValue);
        expect(result.vatAmount).toBe(expectedVatAmount);
    });
    test('calculateDeliveryValueSimple dla EUR', () => {
        // Parametry
        const totalValue = 1000;
        const percentage = 50;
        const currency = "EUR";
        const exchangeRate = 4.5;
        const vatRate = 23;
        const priceType = "net";
        // Obliczenie
        const result = DeliveryCalculator.calculateDeliveryValueSimple(totalValue, percentage, currency, exchangeRate, vatRate, priceType);
        // Oczekiwane wartości
        const expectedTotalMarketValue = 1000;
        const expectedTotalMarketValuePLN = 4500; // 1000 * 4.5
        const expectedBaseValue = 2250; // 4500 * 50%
        const expectedDeliveryValue = 2767.5; // 2250 * 1.23
        const expectedVatAmount = 517.5; // 2767.5 - 2250
        // Asercje
        expect(result.totalMarketValue).toBe(expectedTotalMarketValue);
        expect(result.totalMarketValuePLN).toBe(expectedTotalMarketValuePLN);
        expect(result.baseValue).toBe(expectedBaseValue);
        expect(result.deliveryValue).toBe(expectedDeliveryValue);
        expect(result.vatAmount).toBe(expectedVatAmount);
    });
    test('calculateDeliveryValueSimple dla cen brutto', () => {
        // Parametry
        const totalValue = 1000;
        const percentage = 50;
        const currency = "PLN";
        const exchangeRate = 1;
        const vatRate = 23;
        const priceType = "gross";
        // Obliczenie
        const result = DeliveryCalculator.calculateDeliveryValueSimple(totalValue, percentage, currency, exchangeRate, vatRate, priceType);
        // Oczekiwane wartości
        const expectedTotalMarketValue = 1000;
        const expectedTotalMarketValuePLN = 1000;
        const expectedBaseValue = 500; // 1000 * 50%
        const expectedDeliveryValue = 500; // Bez VAT dla cen brutto
        const expectedVatAmount = 0;
        // Asercje
        expect(result.totalMarketValue).toBe(expectedTotalMarketValue);
        expect(result.totalMarketValuePLN).toBe(expectedTotalMarketValuePLN);
        expect(result.baseValue).toBe(expectedBaseValue);
        expect(result.deliveryValue).toBe(expectedDeliveryValue);
        expect(result.vatAmount).toBe(expectedVatAmount);
    });
    test('calculateDeliveryValue dla produktów w PLN', () => {
        // Produkty
        const products = [
            { price: 100, quantity: 2 },
            { price: 200, quantity: 1 }
        ];
        // Ustawienia
        const settings = {
            valuePercentage: 50,
            vatRate: 23,
            exchangeRate: 4.5,
            priceType: "net",
            currency: "PLN"
        };
        // Obliczenie
        const result = DeliveryCalculator.calculateDeliveryValue(products, settings);
        // Oczekiwane wartości
        const expectedTotalMarketValue = 400; // 100*2 + 200
        const expectedTotalMarketValuePLN = 400; // Wszystko w PLN, bez przeliczania
        const expectedBaseValue = 200; // 400 * 50%
        const expectedDeliveryValue = 246; // 200 * 1.23
        const expectedVatAmount = 46; // 246 - 200
        // Asercje
        expect(result.totalMarketValue).toBe(expectedTotalMarketValue);
        expect(result.totalMarketValuePLN).toBe(expectedTotalMarketValuePLN);
        expect(result.baseValue).toBe(expectedBaseValue);
        expect(result.deliveryValue).toBe(expectedDeliveryValue);
        expect(result.vatAmount).toBe(expectedVatAmount);
    });
    test('calculateDeliveryValue dla produktów w EUR', () => {
        // Produkty
        const products = [
            { price: 100, quantity: 2 },
            { price: 200, quantity: 1 }
        ];
        // Ustawienia
        const settings = {
            valuePercentage: 50,
            vatRate: 23,
            exchangeRate: 4.5,
            priceType: "net",
            currency: "EUR"
        };
        // Obliczenie
        const result = DeliveryCalculator.calculateDeliveryValue(products, settings);
        // Oczekiwane wartości
        const expectedTotalMarketValue = 400; // 100*2 + 200
        const expectedTotalMarketValuePLN = 1800; // 400 * 4.5 (wszystko przeliczone na PLN)
        const expectedBaseValue = 900; // 1800 * 50%
        const expectedDeliveryValue = 1107; // 900 * 1.23
        const expectedVatAmount = 207; // 1107 - 900
        // Asercje
        expect(result.totalMarketValue).toBe(expectedTotalMarketValue);
        expect(result.totalMarketValuePLN).toBe(expectedTotalMarketValuePLN);
        expect(result.baseValue).toBe(expectedBaseValue);
        expect(result.deliveryValue).toBe(expectedDeliveryValue);
        expect(result.vatAmount).toBe(expectedVatAmount);
    });
    test('calculateDeliveryValueSimple obsługa nieprawidłowych danych wejściowych', () => {
        // Test dla undefined/null wartości
        const result1 = DeliveryCalculator.calculateDeliveryValueSimple(undefined, undefined, "PLN");
        expect(result1.totalMarketValue).toBe(0);
        expect(result1.deliveryValue).toBe(0);
        // Test dla nieprawidłowych typów
        const result2 = DeliveryCalculator.calculateDeliveryValueSimple("1000", "50", "PLN");
        expect(result2.totalMarketValue).toBe(1000);
        expect(result2.baseValue).toBe(500);
        // Test dla nieprawidłowej waluty
        const result3 = DeliveryCalculator.calculateDeliveryValueSimple(1000, 50, "USD");
        expect(result3.totalMarketValue).toBe(1000);
        expect(result3.totalMarketValuePLN).toBe(1000); // Traktuje jak PLN
    });
    test('calculateDeliveryValue obsługa pustej listy produktów', () => {
        const settings = {
            valuePercentage: 50,
            vatRate: 23,
            exchangeRate: 4.5,
            priceType: "net",
            currency: "PLN"
        };
        const result = DeliveryCalculator.calculateDeliveryValue([], settings);
        expect(result.totalMarketValue).toBe(0);
        expect(result.totalMarketValuePLN).toBe(0);
        expect(result.baseValue).toBe(0);
        expect(result.deliveryValue).toBe(0);
        expect(result.vatAmount).toBe(0);
    });
    test('calculateDeliveryValue obsługa nieprawidłowych danych produktów', () => {
        const products = [
            { price: undefined, quantity: 2 },
            { price: "200", quantity: "1" }
        ];
        const settings = {
            valuePercentage: 50,
            vatRate: 23,
            exchangeRate: 4.5,
            priceType: "net",
            currency: "PLN"
        };
        const result = DeliveryCalculator.calculateDeliveryValue(products, settings);
        // Pierwszy produkt powinien być zignorowany (price undefined)
        // Drugi produkt powinien być przeliczony (konwersja string na number)
        expect(result.totalMarketValue).toBe(200);
        expect(result.totalMarketValuePLN).toBe(200);
        expect(result.baseValue).toBe(100);
        expect(result.deliveryValue).toBe(123);
        expect(result.vatAmount).toBe(23);
    });
});
//# sourceMappingURL=delivery-calculator.test.js.map