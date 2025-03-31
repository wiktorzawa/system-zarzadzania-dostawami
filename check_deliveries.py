#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Skrypt do sprawdzenia dostaw w bazie danych.
"""

from app import app
from models.supplier.delivery_general import DeliveryGeneral
from flask import current_app

with app.app_context():
    all_deliveries = DeliveryGeneral.query.all()
    print(f'Łączna liczba dostaw: {len(all_deliveries)}')
    
    # Pobierz statusy
    statuses = {}
    for delivery in all_deliveries:
        status = delivery.status
        if status in statuses:
            statuses[status] += 1
        else:
            statuses[status] = 1
    
    print('Statusy dostaw:')
    for status, count in statuses.items():
        print(f'- {status}: {count}')
    
    if all_deliveries:
        print('\nPrzykładowe dostawy:')
        for d in all_deliveries[:5]:
            print(f'ID: {d.id_delivery}, Status: {d.status}, Data: {d.delivery_date}') 