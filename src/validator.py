"""
ElectroPOS - Input Validator
Validates user inputs for the POS system.
"""

import re


def validate_email(email: str) -> bool:
    if not email:
        return True  # Optional field
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    if not phone:
        return True  # Optional field
    cleaned = re.sub(r'[\s\-\(\)\+]', '', phone)
    return cleaned.isdigit() and 7 <= len(cleaned) <= 15


def validate_pin(pin: str) -> bool:
    return pin.isdigit() and len(pin) >= 4


def validate_price(price) -> bool:
    try:
        p = float(price)
        return p >= 0
    except (ValueError, TypeError):
        return False


def validate_quantity(qty) -> bool:
    try:
        q = int(qty)
        return q > 0
    except (ValueError, TypeError):
        return False


def validate_sku(sku: str) -> bool:
    if not sku:
        return False
    return bool(re.match(r'^[A-Za-z0-9_-]{3,20}$', sku))


def validate_barcode(barcode: str) -> bool:
    if not barcode:
        return True  # Optional
    return barcode.isdigit() and 8 <= len(barcode) <= 14


def validate_discount_percent(percent) -> bool:
    try:
        p = float(percent)
        return 0 <= p <= 100
    except (ValueError, TypeError):
        return False


def validate_name(name: str) -> bool:
    return bool(name) and len(name.strip()) >= 1


def sanitize_string(s: str) -> str:
    return s.strip()
