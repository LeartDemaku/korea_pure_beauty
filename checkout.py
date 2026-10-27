# checkout.py
# Llogaritjet dhe kontrollet e arkës, pa Streamlit, që të testohen lehtë.
import re
from typing import Dict, List

import database

PHONE_PATTERN = re.compile(r"^\+?[0-9 ()\-]{6,20}$")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
COUPONS = {"KOREA10": 0.10}  # kodi ekzistues i dyqanit


def _to_float(value: str, default: float) -> float:
    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return default


def shipping_rules(settings: Dict[str, str]) -> tuple[float, float]:
    """Kthen (çmimi_i_transportit, pragu_për_transport_falas) nga cilësimet e dyqanit."""
    return (_to_float(settings.get("shipping_fee", ""), 2.0),
            _to_float(settings.get("free_shipping_threshold", ""), 30.0))


def calculate_totals(subtotal: float, settings: Dict[str, str], coupon: str = "") -> Dict[str, float]:
    fee, threshold = shipping_rules(settings)
    discount_rate = COUPONS.get(coupon.strip().upper(), 0.0)
    discount = round(subtotal * discount_rate, 2)
    shipping = 0.0 if subtotal <= 0 or subtotal >= threshold else fee
    return {
        "subtotal": round(subtotal, 2),
        "discount": discount,
        "shipping": round(shipping, 2),
        "total": round(subtotal - discount + shipping, 2),
        "missing_for_free_shipping": round(max(0.0, threshold - subtotal), 2),
        "threshold": threshold,
    }


def validate_delivery(name: str, phone: str, city: str, address: str, email: str = "") -> List[str]:
    errors = []
    if len(name.strip()) < 3:
        errors.append("Shkruani emrin dhe mbiemrin.")
    if not PHONE_PATTERN.match(phone.strip()):
        errors.append("Numri i telefonit nuk është i saktë (p.sh. +383 44 123 456).")
    if len(city.strip()) < 2:
        errors.append("Shkruani qytetin.")
    if len(address.strip()) < 5:
        errors.append("Shkruani adresën e plotë të dërgesës.")
    if email.strip() and not EMAIL_PATTERN.match(email.strip()):
        errors.append("Email-i nuk duket i saktë.")
    return errors


def stock_problems(cart_items: List[dict]) -> List[str]:
    """Kontrollon stokun vetëm kur admini e ka ndezur 'enforce_stock'."""
    if database.get_setting("enforce_stock", "0") != "1":
        return []
    needed: Dict[int, int] = {}
    for item in cart_items:
        if item.get("product_id"):
            needed[item["product_id"]] = needed.get(item["product_id"], 0) + item["qty"]
    problems = []
    for product_id, quantity in needed.items():
        product = database.get_product_by_id(product_id)
        if not product:
            problems.append("Një produkt në shportë nuk ekziston më. Hiqeni nga shporta.")
        elif (product.get("stock_qty") or 0) < quantity:
            problems.append(f"{product['name']}: kanë mbetur vetëm {product.get('stock_qty') or 0} copë.")
    return problems


def whatsapp_link(number: str, message: str) -> str:
    from urllib.parse import quote
    digits = "".join(ch for ch in number if ch.isdigit())
    return f"https://wa.me/{digits}?text={quote(message)}" if digits else ""
