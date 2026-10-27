# cart.py
# Logjika e shportës në një vend të vetëm.
# Më parë i njëjti kod ishte kopjuar në tre vende te client_app.py.
import streamlit as st


def add_to_cart(product: dict, quantity: int = 1) -> None:
    """Shton një produkt në shportë (ose rrit sasinë) dhe nis animacionin e shportës."""
    if quantity < 1:
        raise ValueError("Sasia duhet të jetë të paktën 1.")
    product_key = str(product['id'])  # çelësat e shportës janë tekst, si në kodin ekzistues
    cart = st.session_state.cart
    if product_key in cart:
        cart[product_key]['qty'] += quantity
    else:
        cart[product_key] = {
            "name": product['name'],
            "brand": product['brand'],
            "price": product['price'],
            "image": product['image_url'],
            "qty": quantity,
        }
    st.session_state.animated_item = {"name": product['name'], "price": product['price']}


def cart_item_count() -> int:
    return sum(item['qty'] for item in st.session_state.get("cart", {}).values())
