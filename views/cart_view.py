# views/cart_view.py
# Shporta dhe arka me një hap: artikujt, transporti falas, të dhënat e dërgesës,
# konfirmimi me numër reference dhe lidhja e WhatsApp.
import html

import streamlit as st

import cart
import checkout
import database
import email_service
import theme
from views import components
from views.components import ImageUriFunction


def render_cart(image_uri: ImageUriFunction) -> None:
    theme.load_css("pages")
    components.section_head("Shporta", 'Shporta <span class="kpb-accent">juaj</span>')

    if st.session_state.get("last_order"):
        _render_confirmation(st.session_state.last_order)
    elif not st.session_state.cart:
        st.markdown('<div class="kpb-empty"><p>Shporta juaj është bosh</p>'
                    '<span>Zgjidhni produktet tuaja të preferuara nga Dyqani.</span></div>',
                    unsafe_allow_html=True)
        if st.button("Shko te Dyqani", key="cart_empty_shop", type="primary"):
            components.go_to("shop")
    else:
        items_column, summary_column = st.columns([1.5, 1], gap="large")
        with items_column:
            _render_items(image_uri)
        with summary_column:
            _render_summary_and_form()

    components.render_footer()


def _render_items(image_uri: ImageUriFunction) -> None:
    for key, item in list(st.session_state.cart.items()):
        with st.container(key=f"kpb-cart-row-{key.replace(':', '-')}"):
            image_column, text_column, qty_column = st.columns([0.8, 2.2, 1.2], vertical_alignment="center")
            with image_column:
                st.markdown(f'<img class="kpb-cart__img" src="{image_uri(item.get("image") or "", 160, 80)}" alt="" />',
                            unsafe_allow_html=True)
            with text_column:
                st.markdown(
                    f'<span class="kpb-pcard__brand">{html.escape(item["brand"])}</span>'
                    f'<p class="kpb-cart__name">{html.escape(item["name"])}</p>'
                    f'<span class="kpb-price">{item["price"] * item["qty"]:.2f} €</span>'
                    f' <span class="kpb-muted">({item["price"]:.2f} € / copë)</span>',
                    unsafe_allow_html=True,
                )
            with qty_column:
                new_qty = st.number_input("Sasia", min_value=0, max_value=50, value=item["qty"],
                                          key=f"cart_qty_{key}_{item['qty']}", help="Vendosni 0 për ta hequr")
                if new_qty != item["qty"]:
                    if new_qty == 0:
                        del st.session_state.cart[key]
                    else:
                        st.session_state.cart[key]["qty"] = int(new_qty)
                    st.rerun()


def _render_summary_and_form() -> None:
    settings = database.get_all_settings()
    coupon = st.session_state.get("cart_coupon", "")
    totals = checkout.calculate_totals(cart.cart_subtotal(), settings, coupon)

    shipping_text = "Falas" if totals["shipping"] == 0 else f'{totals["shipping"]:.2f} €'
    discount_row = (f'<div class="kpb-sum__row"><span>Zbritja (kupon)</span><span>−{totals["discount"]:.2f} €</span></div>'
                    if totals["discount"] else "")
    progress = min(1.0, totals["subtotal"] / totals["threshold"]) if totals["threshold"] else 1.0
    free_note = (f'Edhe <strong>{totals["missing_for_free_shipping"]:.2f} €</strong> për transport falas'
                 if totals["missing_for_free_shipping"] > 0 else "Keni fituar transport falas")

    st.markdown(f"""
    <div class="kpb-summary">
      <p class="kpb-sum__free">{free_note}</p>
      <div class="kpb-sum__bar"><span style="width:{progress * 100:.0f}%"></span></div>
      <div class="kpb-sum__row"><span>Nëntotali</span><span>{totals["subtotal"]:.2f} €</span></div>
      {discount_row}
      <div class="kpb-sum__row"><span>Transporti</span><span>{shipping_text}</span></div>
      <div class="kpb-sum__row kpb-sum__total"><span>Totali</span><span>{totals["total"]:.2f} €</span></div>
      <p class="kpb-muted kpb-sum__pay">Pagesa: me para në dorë, te korrieri.</p>
    </div>
    """, unsafe_allow_html=True)

    st.text_input("Kupon zbritjeje", key="cart_coupon", placeholder="p.sh. KOREA10")
    if coupon and not totals["discount"]:
        st.caption("Ky kupon nuk është i vlefshëm.")

    with st.form("checkout_form"):
        st.markdown('<h3 class="kpb-form-title">Të dhënat e dërgesës</h3>', unsafe_allow_html=True)
        name = st.text_input("Emri & Mbiemri *", max_chars=80)
        phone = st.text_input("Numri i telefonit *", max_chars=20, placeholder="+383 44 123 456",
                              help="Korrieri ju telefonon para dorëzimit")
        city = st.text_input("Qyteti *", max_chars=60)
        address = st.text_area("Adresa e saktë *", max_chars=300, height=80)
        notes = st.text_area("Shënime për korrierin", max_chars=300, height=70,
                             placeholder="p.sh. Telefononi kur të arrini")
        email = st.text_input("Email-i (opsional, për konfirmim)", max_chars=120)
        submitted = st.form_submit_button("Përfundo porosinë", type="primary", use_container_width=True)

    if submitted:
        _place_order(name, phone, city, address, notes, email, totals)


def _place_order(name, phone, city, address, notes, email, totals) -> None:
    items = list(st.session_state.cart.values())
    errors = checkout.validate_delivery(name, phone, city, address, email) + checkout.stock_problems(items)
    if errors:
        for error in errors:
            st.error(error)
        return

    order_id = database.create_order(
        buyer_name=name.strip(), phone=phone.strip(), city=city.strip(), address=address.strip(),
        items=items, total_price=totals["total"], customer_notes=notes, buyer_email=email,
    )
    for item in items:
        if item.get("product_id"):
            database.reduce_stock_after_order(item["product_id"], item["qty"])

    # Njoftimet me email: nëse SMTP nuk është konfiguruar, porosia ruhet gjithsesi
    email_service.send_order_notification_email(
        order_id=order_id, buyer_name=name.strip(), phone=phone.strip(), city=city.strip(),
        address=address.strip(), items=items, total_price=totals["total"],
        to_admin_email=email_service.admin_email(),
    )
    if email.strip():
        email_service.send_order_confirmation_to_customer(email, order_id, name.strip(), items, totals["total"])

    st.session_state.cart = {}
    st.session_state.last_order = {"id": order_id, "name": name.strip(), "total": totals["total"]}
    st.rerun()


def _render_confirmation(order: dict) -> None:
    whatsapp_number = database.get_setting("whatsapp_number")
    message = (f"Përshëndetje! Jam {order['name']}. Sapo bëra porosinë #{order['id']} "
               f"me vlerë {order['total']:.2f} € te Korea Pure Beauty. Ju lutem ma konfirmoni.")
    link = checkout.whatsapp_link(whatsapp_number, message)

    st.markdown(f"""
    <div class="kpb-confirm">
      <span class="kpb-overline">Porosia u pranua</span>
      <h2 class="kpb-h2">Faleminderit, <span class="kpb-accent">{html.escape(order['name'])}</span></h2>
      <p>Numri i referencës: <strong class="kpb-confirm__ref">#{order['id']}</strong></p>
      <p class="kpb-muted">Totali: {order['total']:.2f} € · Pagesë me para në dorë.<br>
      Do t'ju telefonojmë për ta konfirmuar dërgesën.</p>
    </div>
    """, unsafe_allow_html=True)

    whatsapp_column, shop_column = st.columns(2)
    with whatsapp_column:
        if link:
            st.link_button("Konfirmo në WhatsApp", link, use_container_width=True)
    with shop_column:
        if st.button("Vazhdo blerjet", key="confirm_continue", type="primary", use_container_width=True):
            st.session_state.last_order = None
            components.go_to("shop")
