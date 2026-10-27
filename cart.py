# cart.py
# Logjika e shportës në një vend të vetëm.
# Më parë i njëjti kod ishte kopjuar në tre vende te client_app.py.
from typing import Optional

import streamlit as st

RITUAL_DISCOUNT = 0.10  # 10% zbritje kur shtohet i gjithë rituali


def add_to_cart(product: dict, quantity: int = 1, price: Optional[float] = None,
                cart_key: Optional[str] = None, label_suffix: str = "") -> None:
    """Shton një produkt në shportë (ose rrit sasinë) dhe nis animacionin e shportës.
    price/cart_key lejojnë një rresht të veçantë me çmim tjetër (p.sh. rituali me zbritje)."""
    if quantity < 1:
        raise ValueError("Sasia duhet të jetë të paktën 1.")
    key = cart_key or str(product['id'])  # çelësat e shportës janë tekst, si në kodin ekzistues
    unit_price = round(float(product['price'] if price is None else price), 2)
    cart = st.session_state.cart
    if key in cart:
        cart[key]['qty'] += quantity
    else:
        cart[key] = {
            "product_id": product['id'],   # nevojitet për uljen e stokut pas porosisë
            "name": product['name'] + label_suffix,
            "brand": product['brand'],
            "price": unit_price,
            "image": product['image_url'],
            "size": product.get('size_label') or "",
            "qty": quantity,
        }
    st.session_state.animated_item = {"name": product['name'], "price": unit_price}


def add_ritual_to_cart(products: list) -> None:
    """Shton të gjithë ritualin me 10% zbritje, si rreshta të veçantë në shportë."""
    for product in products:
        add_to_cart(
            product,
            price=product['price'] * (1 - RITUAL_DISCOUNT),
            cart_key=f"{product['id']}:ritual",
            label_suffix=" · Rituali −10%",
        )


def cart_item_count() -> int:
    return sum(item['qty'] for item in st.session_state.get("cart", {}).values())


def cart_subtotal() -> float:
    return round(sum(item['price'] * item['qty'] for item in st.session_state.get("cart", {}).values()), 2)
