#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Testy jednostkowe dla kalkulatora wartości dostawy
"""

import unittest
from utils.delivery_calculator import DeliveryCalculator

class TestDeliveryCalculator(unittest.TestCase):
    """
    Testy dla kalkulatora wartości dostawy
    """
    
    def test_calculate_delivery_value_simple_pln(self):
        """
        Test obliczania wartości dostawy w PLN
        """
        # Parametry
        total_value = 1000
        percentage = 50
        currency = "PLN"
        exchange_rate = 1
        vat_rate = 23
        price_type = "net"
        
        # Obliczenie
        result = DeliveryCalculator.calculate_delivery_value_simple(
            total_value, percentage, currency, exchange_rate, vat_rate, price_type
        )
        
        # Oczekiwane wartości
        expected_total_market_value = 1000
        expected_total_market_value_pln = 1000
        expected_base_value = 500  # 1000 * 50%
        expected_delivery_value = 615  # 500 * 1.23
        expected_vat_amount = 115  # 615 - 500
        
        # Asercje
        self.assertEqual(result["totalMarketValue"], expected_total_market_value)
        self.assertEqual(result["totalMarketValuePLN"], expected_total_market_value_pln)
        self.assertEqual(result["baseValue"], expected_base_value)
        self.assertEqual(result["deliveryValue"], expected_delivery_value)
        self.assertEqual(result["vatAmount"], expected_vat_amount)
    
    def test_calculate_delivery_value_simple_eur(self):
        """
        Test obliczania wartości dostawy w EUR
        """
        # Parametry
        total_value = 1000
        percentage = 50
        currency = "EUR"
        exchange_rate = 4.5
        vat_rate = 23
        price_type = "net"
        
        # Obliczenie
        result = DeliveryCalculator.calculate_delivery_value_simple(
            total_value, percentage, currency, exchange_rate, vat_rate, price_type
        )
        
        # Oczekiwane wartości
        expected_total_market_value = 1000
        expected_total_market_value_pln = 4500  # 1000 * 4.5
        expected_base_value = 2250  # 4500 * 50%
        expected_delivery_value = 2767.5  # 2250 * 1.23
        expected_vat_amount = 517.5  # 2767.5 - 2250
        
        # Asercje
        self.assertEqual(result["totalMarketValue"], expected_total_market_value)
        self.assertEqual(result["totalMarketValuePLN"], expected_total_market_value_pln)
        self.assertEqual(result["baseValue"], expected_base_value)
        self.assertEqual(result["deliveryValue"], expected_delivery_value)
        self.assertEqual(result["vatAmount"], expected_vat_amount)
    
    def test_calculate_delivery_value_simple_gross(self):
        """
        Test obliczania wartości dostawy dla cen brutto
        """
        # Parametry
        total_value = 1000
        percentage = 50
        currency = "PLN"
        exchange_rate = 1
        vat_rate = 23
        price_type = "gross"
        
        # Obliczenie
        result = DeliveryCalculator.calculate_delivery_value_simple(
            total_value, percentage, currency, exchange_rate, vat_rate, price_type
        )
        
        # Oczekiwane wartości
        expected_total_market_value = 1000
        expected_total_market_value_pln = 1000
        expected_base_value = 500  # 1000 * 50%
        expected_delivery_value = 500  # Bez VAT dla cen brutto
        expected_vat_amount = 0
        
        # Asercje
        self.assertEqual(result["totalMarketValue"], expected_total_market_value)
        self.assertEqual(result["totalMarketValuePLN"], expected_total_market_value_pln)
        self.assertEqual(result["baseValue"], expected_base_value)
        self.assertEqual(result["deliveryValue"], expected_delivery_value)
        self.assertEqual(result["vatAmount"], expected_vat_amount)
    
    def test_calculate_delivery_value_pln(self):
        """
        Test obliczania wartości dostawy na podstawie produktów w PLN
        """
        # Produkty
        products = [
            {"price": 100, "quantity": 2},
            {"price": 200, "quantity": 1}
        ]
        
        # Ustawienia
        settings = {
            "valuePercentage": 50,
            "vatRate": 23,
            "exchangeRate": 4.5,
            "priceType": "net",
            "currency": "PLN"
        }
        
        # Obliczenie
        result = DeliveryCalculator.calculate_delivery_value(products, settings)
        
        # Oczekiwane wartości
        expected_total_market_value = 400  # 100*2 + 200
        expected_total_market_value_pln = 400  # Wszystko w PLN, bez przeliczania
        expected_base_value = 200  # 400 * 50%
        expected_delivery_value = 246  # 200 * 1.23
        expected_vat_amount = 46  # 246 - 200
        
        # Asercje
        self.assertEqual(result["totalMarketValue"], expected_total_market_value)
        self.assertEqual(result["totalMarketValuePLN"], expected_total_market_value_pln)
        self.assertEqual(result["baseValue"], expected_base_value)
        self.assertEqual(result["deliveryValue"], expected_delivery_value)
        self.assertEqual(result["vatAmount"], expected_vat_amount)
    
    def test_calculate_delivery_value_eur(self):
        """
        Test obliczania wartości dostawy na podstawie produktów w EUR
        """
        # Produkty
        products = [
            {"price": 100, "quantity": 2},
            {"price": 200, "quantity": 1}
        ]
        
        # Ustawienia
        settings = {
            "valuePercentage": 50,
            "vatRate": 23,
            "exchangeRate": 4.5,
            "priceType": "net",
            "currency": "EUR"
        }
        
        # Obliczenie
        result = DeliveryCalculator.calculate_delivery_value(products, settings)
        
        # Oczekiwane wartości
        expected_total_market_value = 400  # 100*2 + 200
        expected_total_market_value_pln = 1800  # 400 * 4.5 (wszystko przeliczone na PLN)
        expected_base_value = 900  # 1800 * 50%
        expected_delivery_value = 1107  # 900 * 1.23
        expected_vat_amount = 207  # 1107 - 900
        
        # Asercje
        self.assertEqual(result["totalMarketValue"], expected_total_market_value)
        self.assertEqual(result["totalMarketValuePLN"], expected_total_market_value_pln)
        self.assertEqual(result["baseValue"], expected_base_value)
        self.assertEqual(result["deliveryValue"], expected_delivery_value)
        self.assertEqual(result["vatAmount"], expected_vat_amount)

    def test_calculate_delivery_value_simple_invalid_input(self):
        """
        Test obsługi nieprawidłowych danych wejściowych
        """
        # Test dla None wartości
        result1 = DeliveryCalculator.calculate_delivery_value_simple(
            None,
            None,
            "PLN"
        )
        self.assertEqual(result1["totalMarketValue"], 0)
        self.assertEqual(result1["deliveryValue"], 0)

        # Test dla nieprawidłowych typów
        result2 = DeliveryCalculator.calculate_delivery_value_simple(
            "1000",
            "50",
            "PLN"
        )
        self.assertEqual(result2["totalMarketValue"], 1000)
        self.assertEqual(result2["baseValue"], 500)

        # Test dla nieprawidłowej waluty
        result3 = DeliveryCalculator.calculate_delivery_value_simple(
            1000,
            50,
            "USD"
        )
        self.assertEqual(result3["totalMarketValue"], 1000)
        self.assertEqual(result3["totalMarketValuePLN"], 1000)  # Traktuje jak PLN

    def test_calculate_delivery_value_empty_products(self):
        """
        Test obliczania wartości dostawy dla pustej listy produktów
        """
        settings = {
            "valuePercentage": 50,
            "vatRate": 23,
            "exchangeRate": 4.5,
            "priceType": "net",
            "currency": "PLN"
        }

        result = DeliveryCalculator.calculate_delivery_value([], settings)
        
        self.assertEqual(result["totalMarketValue"], 0)
        self.assertEqual(result["totalMarketValuePLN"], 0)
        self.assertEqual(result["baseValue"], 0)
        self.assertEqual(result["deliveryValue"], 0)
        self.assertEqual(result["vatAmount"], 0)

    def test_calculate_delivery_value_invalid_products(self):
        """
        Test obliczania wartości dostawy dla nieprawidłowych danych produktów
        """
        products = [
            {"price": None, "quantity": 2},
            {"price": "200", "quantity": "1"}
        ]

        settings = {
            "valuePercentage": 50,
            "vatRate": 23,
            "exchangeRate": 4.5,
            "priceType": "net",
            "currency": "PLN"
        }

        result = DeliveryCalculator.calculate_delivery_value(products, settings)
        
        # Pierwszy produkt powinien być zignorowany (price None)
        # Drugi produkt powinien być przeliczony (konwersja string na float)
        self.assertEqual(result["totalMarketValue"], 200)
        self.assertEqual(result["totalMarketValuePLN"], 200)
        self.assertEqual(result["baseValue"], 100)
        self.assertEqual(result["deliveryValue"], 123)
        self.assertEqual(result["vatAmount"], 23)

if __name__ == "__main__":
    unittest.main() 