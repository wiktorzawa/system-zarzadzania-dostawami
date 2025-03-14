#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Kalkulator wartości dostawy - wersja Python
Implementacja identyczna z wersją TypeScript
"""
from typing import List, Dict, Union, TypedDict

class DeliveryProduct(TypedDict, total=False):
    price: float
    quantity: float
    currency: str

class DeliverySettings(TypedDict):
    valuePercentage: float
    vatRate: float
    exchangeRate: float
    priceType: str
    currency: str

class DeliveryCalculationResult(TypedDict):
    totalMarketValue: float
    totalMarketValuePLN: float
    baseValue: float
    deliveryValue: float
    vatAmount: float

class DeliveryCalculator:
    """
    Kalkulator wartości dostawy
    """
    
    @staticmethod
    def calculate_delivery_value(
        products: List[DeliveryProduct],
        settings: DeliverySettings
    ) -> DeliveryCalculationResult:
        """
        Oblicza wartość dostawy na podstawie produktów i ustawień
        
        Args:
            products: Lista produktów (każdy z ceną, ilością i opcjonalnie walutą)
            settings: Słownik z ustawieniami dostawy
                - valuePercentage: Procent wartości (0-100)
                - vatRate: Stawka VAT (np. 23)
                - exchangeRate: Kurs wymiany dla EUR
                - priceType: Typ ceny (net lub gross)
                - currency: Globalna waluta dla wszystkich produktów (PLN, EUR)
                
        Returns:
            DeliveryCalculationResult: Wyniki obliczeń
        """
        # Konwersja typów na liczby
        value_percentage = float(settings.get('valuePercentage', 0)) or 0
        vat_rate = float(settings.get('vatRate', 23)) or 23
        exchange_rate = float(settings.get('exchangeRate', 1)) or 1
        global_currency = settings.get('currency', 'PLN')
        
        # Obliczenie sumy wartości produktów
        total_market_value = 0.0
        total_market_value_pln = 0.0
        
        for product in products:
            price = float(product.get('price', 0) or 0)
            quantity = float(product.get('quantity', 0) or 0)
            
            # Wartość produktu
            product_value = price * quantity
            
            # Dodaj do sumy w oryginalnej walucie
            total_market_value += product_value
            
            # Wartość w PLN zależy od globalnej waluty
            if global_currency == "EUR":
                total_market_value_pln += product_value * exchange_rate
            else:
                total_market_value_pln += product_value
        
        # Obliczenie wartości bazowej (procent wartości rynkowej)
        base_value = total_market_value_pln * (value_percentage / 100)
        
        # Obliczenie wartości końcowej z VAT
        final_value = base_value
        vat_amount = 0.0
        
        if settings.get('priceType') == "net":
            final_value = base_value * (1 + vat_rate / 100)
            vat_amount = final_value - base_value
        
        # Zaokrąglenie do 2 miejsc po przecinku
        final_value = round(final_value, 2)
        vat_amount = round(vat_amount, 2)
        
        return {
            "totalMarketValue": total_market_value,
            "totalMarketValuePLN": total_market_value_pln,
            "baseValue": base_value,
            "deliveryValue": final_value,
            "vatAmount": vat_amount
        }
    
    @staticmethod
    def calculate_delivery_value_simple(
        total_value: float,
        percentage: float,
        currency: str,
        exchange_rate: float = 1.0,
        vat_rate: float = 23.0,
        price_type: str = "net"
    ) -> DeliveryCalculationResult:
        """
        Oblicza wartość dostawy na podstawie parametrów
        (Wersja kompatybilna z istniejącym kodem)
        
        Args:
            total_value: Całkowita wartość rynkowa produktów
            percentage: Procent wartości (0-100)
            currency: Waluta (PLN lub EUR)
            exchange_rate: Kurs wymiany dla EUR
            vat_rate: Stawka VAT (np. 23)
            price_type: Typ ceny (net lub gross)
            
        Returns:
            DeliveryCalculationResult: Wyniki obliczeń
        """
        # Konwersja typów na liczby
        total_value = float(total_value or 0)
        percentage = float(percentage or 0)
        exchange_rate = float(exchange_rate or 1)
        vat_rate = float(vat_rate or 23)
        
        # Obliczenie wartości w PLN
        total_market_value_pln = total_value * exchange_rate if currency == "EUR" else total_value
        
        # Obliczenie wartości bazowej (procent wartości rynkowej)
        base_value = total_market_value_pln * (percentage / 100)
        
        # Obliczenie wartości końcowej z VAT
        final_value = base_value
        vat_amount = 0.0
        
        if price_type == "net":
            final_value = base_value * (1 + vat_rate / 100)
            vat_amount = final_value - base_value
        
        # Zaokrąglenie do 2 miejsc po przecinku
        final_value = round(final_value, 2)
        vat_amount = round(vat_amount, 2)
        
        return {
            "totalMarketValue": total_value,
            "totalMarketValuePLN": total_market_value_pln,
            "baseValue": base_value,
            "deliveryValue": final_value,
            "vatAmount": vat_amount
        } 