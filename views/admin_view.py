# views/admin_view.py
# Paneli i Administratorit: Dashboard, Porositë, Produktet & Inventari, Mesazhet,
# Vlerësimet dhe Cilësimet e dyqanit.
import html
import io
import os
import uuid
from datetime import date
from typing import Callable

import pandas as pd
import streamlit as st
from PIL import Image, UnidentifiedImageError

import analytics
import auth
import catalog
import checkout
import database
import theme

ImageUriFunction = Callable[[str, int, int], str]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = "uploads"
MAX_UPLOAD_MB = 5
BRANDS = ["Anua", "Beauty of Joseon", "COSRX", "K-Secret", "Skin1004", "LEBELAGE", "Round Lab",
          "Laneige", "Some By Mi", "Torriden", "I'm From", "Tjetër"]
PAGES = ["Dashboard", "Porositë", "Produktet", "Mesazhet", "Vlerësimet", "Cilësimet"]


# ==========================================
# NDIHMËS
# ==========================================
def save_product_image(uploaded_file) -> str:
    """Kontrollon foton, e zvogëlon dhe e ruan si WebP. Kthen rrugën relative (uploads/...)."""
    data = uploaded_file.getvalue()
    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        raise ValueError(f"Fotoja është më e madhe se {MAX_UPLOAD_MB} MB.")
    try:
        with Image.open(io.BytesIO(data)) as image:
            image = image.convert("RGBA" if image.mode in ("RGBA", "LA", "P") else "RGB")
            image.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
            relative_path = f"{UPLOAD_DIR}/{uuid.uuid4().hex[:12]}.webp"
            os.makedirs(os.path.join(BASE_DIR, UPLOAD_DIR), exist_ok=True)
            image.save(os.path.join(BASE_DIR, relative_path), "WEBP", quality=85, method=6)
            return relative_path
    except UnidentifiedImageError:
        raise ValueError("Skedari nuk është foto e vlefshme (PNG, JPG ose WebP).")


def invoice_html(order: dict, settings: dict, logo_uri: str) -> str:
    """Fatura A4 e printueshme. Hapet në browser dhe printohet me Ctrl+P."""
    rows = ""
    for item in analytics.order_items(order):
        line_total = item.get("price", 0) * item.get("qty", 0)
        rows += (f"<tr><td>{html.escape(item.get('name', ''))}</td><td>{item.get('qty', 0)}</td>"
                 f"<td>{item.get('price', 0):.2f} €</td><td>{line_total:.2f} €</td></tr>")
    logo = f'<img src="{logo_uri}" style="height:70px" />' if logo_uri else "<h2>Korea Pure Beauty</h2>"
    whatsapp = html.escape(settings.get("whatsapp_number", ""))
    return f"""<!doctype html><html lang="sq"><head><meta charset="utf-8"><title>Fatura #{order['id']}</title>
<style>
 @page {{ size: A4; margin: 18mm; }}
 body {{ font-family: Georgia, serif; color: #261B15; }}
 header {{ display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #D8B494; padding-bottom:12px; }}
 table {{ width:100%; border-collapse:collapse; margin-top:24px; font-family: Arial, sans-serif; font-size:14px; }}
 th, td {{ text-align:left; padding:8px; border-bottom:1px solid #EADED5; }}
 th {{ color:#AF6A4E; text-transform:uppercase; font-size:11px; letter-spacing:.12em; }}
 .total {{ text-align:right; font-size:22px; margin-top:16px; color:#AF6A4E; }}
 .muted {{ color:#6E5D53; font-family: Arial, sans-serif; font-size:13px; line-height:1.6; }}
</style></head><body onload="window.print()">
<header>{logo}<div style="text-align:right"><h2 style="margin:0">Fatura #{order['id']}</h2>
<div class="muted">Data: {str(order.get('created_at', ''))[:10]}</div></div></header>
<p class="muted"><strong>Klienti:</strong> {html.escape(order['buyer_name'])}<br>
<strong>Telefoni:</strong> {html.escape(order['phone'])}<br>
<strong>Adresa:</strong> {html.escape(order['address'])}, {html.escape(order['city'])}</p>
<table><tr><th>Produkti</th><th>Sasia</th><th>Çmimi</th><th>Totali</th></tr>{rows}</table>
<p class="total">Totali: {order['total_price']:.2f} €</p>
<p class="muted">Pagesa: {html.escape(order.get('payment_method') or 'Para në dorë')}<br>
Korea Pure Beauty · WhatsApp: +{whatsapp}</p>
</body></html>"""


def _status_badge(status: str) -> str:
    css = {"E Re (Në Pritje)": "warning", "Në Përpunim": "warning", "Dërguar me Postë": "",
           "E Përfunduar / Dorëzuar": "success", "E Anuluar": "danger"}.get(status, "")
    return f'<span class="kpb-badge kpb-badge--{css}">{html.escape(status)}</span>'


# ==========================================
# 1. DASHBOARD
# ==========================================
def _render_dashboard() -> None:
    orders = database.get_all_orders()
    products = database.get_all_products()
    numbers = analytics.kpis(orders, products, low_stock_threshold=database.LOW_STOCK_THRESHOLD)

    st.markdown('<h1 class="kpb-h2">Dashboard</h1>', unsafe_allow_html=True)
    row1 = st.columns(4)
    row1[0].metric("Të ardhurat totale", f"{numbers['revenue_total']:.2f} €")
    row1[1].metric("Sot", f"{numbers['revenue_today']:.2f} €")
    row1[2].metric("7 ditët e fundit", f"{numbers['revenue_week']:.2f} €")
    row1[3].metric("Ky muaj", f"{numbers['revenue_month']:.2f} €")
    row2 = st.columns(4)
    row2[0].metric("Porosi aktive", numbers["orders_active"])
    row2[1].metric("Porosi gjithsej", numbers["orders_total"])
    row2[2].metric("Vlera mesatare (AOV)", f"{numbers['aov']:.2f} €")
    row2[3].metric("Stok kritik (< 3)", numbers["low_stock"])

    chart_column, top_column = st.columns([1.6, 1], gap="large")
    with chart_column:
        st.markdown("#### Shitjet ditore (30 ditë)")
        series = analytics.daily_sales(orders)
        st.bar_chart(pd.DataFrame({"Shitjet (€)": list(series.values())}, index=list(series.keys())),
                     color=theme.PALETTE["terracotta"])
    with top_column:
        st.markdown("#### Më të shiturat")
        top = analytics.top_products(orders)
        if top:
            st.bar_chart(pd.DataFrame({"Copë": list(top.values())}, index=list(top.keys())),
                         horizontal=True, color=theme.PALETTE["gold"])
        else:
            st.caption("Ende nuk ka shitje.")

    low_stock = database.get_low_stock_products()
    if low_stock:
        st.markdown("#### Produkte me stok kritik")
        st.dataframe(pd.DataFrame([{"Produkti": p["name"], "Stoku": p["stock_qty"]} for p in low_stock]),
                     hide_index=True, use_container_width=True)


# ==========================================
# 2. POROSITË
# ==========================================
def _render_orders() -> None:
    st.markdown('<h1 class="kpb-h2">Porositë</h1>', unsafe_allow_html=True)
    orders = database.get_all_orders()
    counts = analytics.status_counts(orders)
    st.markdown(" ".join(f'{_status_badge(s)} <strong>{counts.get(s, 0)}</strong>' for s in database.ORDER_STATUSES),
                unsafe_allow_html=True)

    search_column, status_column = st.columns([2, 1])
    query = catalog.normalize(search_column.text_input("Kërko (emri, qyteti, telefoni)", key="adm_order_search"))
    status_filter = status_column.selectbox("Statusi", ["Të gjitha", *database.ORDER_STATUSES], key="adm_order_status")

    filtered = [
        o for o in orders
        if (status_filter == "Të gjitha" or o.get("status") == status_filter)
        and (not query or query in catalog.normalize(f"{o['buyer_name']} {o['city']} {o['phone']} {o['id']}"))
    ]
    if not filtered:
        st.info("Nuk ka porosi për këtë kërkim.")
        return

    settings = database.get_all_settings()
    logo_uri = theme.asset_data_uri("logo.png")
    for order in filtered:
        title = (f"#{order['id']} · {order['buyer_name']} · {order['city']} · "
                 f"{order['total_price']:.2f} € · {order.get('status')}")
        with st.expander(title):
            info_column, action_column = st.columns([1.3, 1], gap="large")
            with info_column:
                st.markdown(
                    f"**Telefoni:** {html.escape(order['phone'])}  \n"
                    f"**Adresa:** {html.escape(order['address'])}, {html.escape(order['city'])}  \n"
                    f"**Data:** {str(order.get('created_at', ''))[:16]}  \n"
                    f"**Email:** {html.escape(order.get('buyer_email') or '—')}  \n"
                    f"**Shënime nga klienti:** {html.escape(order.get('customer_notes') or '—')}"
                )
                items = analytics.order_items(order)
                if items:
                    st.dataframe(pd.DataFrame([{
                        "Produkti": i.get("name"), "Sasia": i.get("qty"),
                        "Çmimi": f"{i.get('price', 0):.2f} €",
                    } for i in items]), hide_index=True, use_container_width=True)

            with action_column:
                statuses = database.ORDER_STATUSES
                current = order.get("status")
                index = statuses.index(current) if current in statuses else 0
                with st.form(f"order_form_{order['id']}"):
                    new_status = st.selectbox("Statusi", statuses, index=index)
                    tracking = st.text_input("Numri i dërgesës (tracking)", value=order.get("tracking_number") or "")
                    notes = st.text_area("Shënime të brendshme", value=order.get("admin_notes") or "", height=70)
                    if st.form_submit_button("Ruaj ndryshimet", type="primary", use_container_width=True):
                        if new_status != current:
                            database.change_order_status(order["id"], new_status)
                        database.update_order_admin_fields(order["id"], tracking, notes)
                        st.success("U ruajt.")
                        st.rerun()

                tracking_text = f" Numri i dërgesës: {order['tracking_number']}." if order.get("tracking_number") else ""
                message = (f"Përshëndetje {order['buyer_name']}, porosia juaj me nr #{order['id']} "
                           f"u nis sot me postë.{tracking_text} Faleminderit që zgjodhët Korea Pure Beauty!")
                link = checkout.whatsapp_link(order["phone"], message)
                if link:
                    st.link_button("Njofto klientin në WhatsApp", link, use_container_width=True)
                st.download_button(
                    "Fatura (printo)", invoice_html(order, settings, logo_uri),
                    file_name=f"fatura_{order['id']}.html", mime="text/html",
                    key=f"invoice_{order['id']}", use_container_width=True,
                )
                confirm = st.checkbox("Po, dua ta fshij këtë porosi", key=f"confirm_del_{order['id']}")
                if st.button("Fshij porosinë", key=f"del_order_{order['id']}", disabled=not confirm,
                             use_container_width=True):
                    database.delete_order(order["id"])
                    st.rerun()


# ==========================================
# 3. PRODUKTET & INVENTARI
# ==========================================
def _product_form(form_key: str, product: dict | None = None) -> dict | None:
    """Formulari i produktit. Kthen të dhënat e kontrolluara, ose None nëse s'u dërgua/ka gabime."""
    product = product or {}
    categories = list(catalog.CATEGORY_GROUPS)
    skin_types = ["Të gjitha tipet", *catalog.SKIN_TYPES]
    current_category = catalog.category_group(product.get("category", "")) if product else categories[0]
    with st.form(form_key, clear_on_submit=not product):
        left, right = st.columns([1.3, 1], gap="large")
        with left:
            name = st.text_input("Emri i produktit *", value=product.get("name", ""), max_chars=150)
            brand_default = product.get("brand", BRANDS[0])
            brand = st.selectbox("Marka *", BRANDS if brand_default in BRANDS else [brand_default, *BRANDS],
                                 index=(BRANDS.index(brand_default) if brand_default in BRANDS else 0))
            new_brand = st.text_input("Marka e re (nëse zgjodhët “Tjetër”)")
            category = st.selectbox("Kategoria *", categories,
                                    index=categories.index(current_category) if current_category in categories else 0)
            skin = product.get("skin_type", skin_types[0])
            skin_type = st.selectbox("Lloji i lëkurës *", skin_types if skin in skin_types else [skin, *skin_types])
            price_column, old_column, stock_column = st.columns(3)
            price = price_column.number_input("Çmimi (€) *", min_value=0.5, value=float(product.get("price", 19.5)),
                                              step=0.5, format="%.2f")
            old_price = old_column.number_input("Çmimi i vjetër (€)", min_value=0.0,
                                                value=float(product.get("old_price") or 0.0), step=0.5, format="%.2f",
                                                help="Lëreni 0 nëse s'ka zbritje")
            stock = stock_column.number_input("Stoku (copë)", min_value=0, value=int(product.get("stock_qty") or 0))
            size_label = st.text_input("Paketimi (p.sh. 30 ml, 70 copë)", value=product.get("size_label") or "",
                                       max_chars=30)
        with right:
            image = st.file_uploader("Fotoja (Drag & Drop, ruhet si WebP)", type=["png", "jpg", "jpeg", "webp"])
            description = st.text_area("Përshkrimi", value=product.get("description") or "", height=90)
            ingredients = st.text_area("Përbërësit kryesorë", value=product.get("ingredients") or "", height=70)
            how_to_use = st.text_area("Mënyra e përdorimit", value=product.get("how_to_use") or "", height=70)
            is_bestseller = st.checkbox("Bestseller (shfaqet në Ballinë)", value=bool(product.get("is_bestseller")))
            eu_certified = st.checkbox("Standarde të BE-së", value=bool(product.get("eu_certified", True)))
            is_original = st.checkbox("100% origjinale", value=bool(product.get("is_original", True)))
        submitted = st.form_submit_button("Ruaj produktin", type="primary", use_container_width=True)

    if not submitted:
        return None
    final_brand = new_brand.strip() if brand == "Tjetër" else brand
    errors = []
    if len(name.strip()) < 2:
        errors.append("Shkruani emrin e produktit.")
    if not final_brand:
        errors.append("Shkruani markën e re.")
    if old_price and old_price <= price:
        errors.append("Çmimi i vjetër duhet të jetë më i madh se çmimi aktual (ose 0).")
    image_path = product.get("image_url", "")
    if image is not None and not errors:
        try:
            image_path = save_product_image(image)
        except ValueError as error:
            errors.append(str(error))
    for error in errors:
        st.error(error)
    if errors:
        return None
    return {
        "name": name.strip(), "brand": final_brand, "category": category, "skin_type": skin_type,
        "price": round(price, 2), "old_price": round(old_price, 2) if old_price else None,
        "stock_qty": int(stock), "description": description.strip(), "ingredients": ingredients.strip(),
        "how_to_use": how_to_use.strip(), "is_bestseller": int(is_bestseller), "size_label": size_label.strip(),
        "eu_certified": int(eu_certified), "is_original": int(is_original), "image_url": image_path,
    }


def _render_products(image_uri: ImageUriFunction) -> None:
    st.markdown('<h1 class="kpb-h2">Produktet & Inventari</h1>', unsafe_allow_html=True)
    inventory_tab, add_tab, edit_tab = st.tabs(["Inventari", "Shto produkt", "Ndrysho / Fshij"])

    with inventory_tab:
        products = database.get_all_products()
        if not products:
            st.info("Nuk ka produkte ende.")
        else:
            st.caption("Ndryshoni çmimin, stokun ose bestseller direkt në tabelë dhe shtypni “Ruaj tabelën”.")
            frame = pd.DataFrame([{
                "id": p["id"], "Produkti": p["name"], "Marka": p["brand"], "Çmimi (€)": p["price"],
                "Çmimi i vjetër (€)": p.get("old_price") or 0.0, "Stoku": p.get("stock_qty") or 0,
                "Bestseller": bool(p.get("is_bestseller")),
                "Gjendja": "Pa stok" if not p.get("stock_qty") else
                           ("Stok kritik" if p["stock_qty"] < database.LOW_STOCK_THRESHOLD else "Në stok"),
            } for p in products])
            edited = st.data_editor(
                frame, hide_index=True, use_container_width=True, key="inventory_editor",
                disabled=["id", "Produkti", "Marka", "Gjendja"],
                column_config={
                    "Çmimi (€)": st.column_config.NumberColumn(min_value=0.5, step=0.5, format="%.2f"),
                    "Çmimi i vjetër (€)": st.column_config.NumberColumn(min_value=0.0, step=0.5, format="%.2f"),
                    "Stoku": st.column_config.NumberColumn(min_value=0, step=1),
                },
            )
            if st.button("Ruaj tabelën", type="primary", key="save_inventory"):
                problems = 0
                for row in edited.to_dict("records"):
                    old_price = float(row["Çmimi i vjetër (€)"] or 0)
                    if old_price and old_price <= float(row["Çmimi (€)"]):
                        problems += 1
                        old_price = 0.0  # zbritje e pavlefshme: e heqim
                    database.update_product_fields(
                        int(row["id"]), price=round(float(row["Çmimi (€)"]), 2),
                        old_price=round(old_price, 2) or None, stock_qty=int(row["Stoku"]),
                        is_bestseller=int(bool(row["Bestseller"])),
                    )
                if problems:
                    st.warning(f"{problems} çmime të vjetra ishin më të vogla se çmimi aktual dhe u hoqën.")
                st.success("Inventari u përditësua.")
                st.rerun()

    with add_tab:
        data = _product_form("add_product_form")
        if data:
            database.create_product(**data)
            st.success(f"“{data['name']}” u shtua në dyqan.")

    with edit_tab:
        products = database.get_all_products()
        if not products:
            st.info("Nuk ka produkte ende.")
            return
        labels = {f"#{p['id']} · {p['name']}": p for p in products}
        selected = labels[st.selectbox("Zgjidhni produktin", list(labels), key="edit_product_select")]
        st.markdown(f'<img class="kpb-cart__img" src="{image_uri(selected.get("image_url") or "", 160, 80)}" />',
                    unsafe_allow_html=True)
        data = _product_form(f"edit_product_form_{selected['id']}", selected)
        if data:
            database.update_product_fields(selected["id"], **data)
            st.success("Produkti u përditësua.")
            st.rerun()
        confirm = st.checkbox("Po, dua ta fshij këtë produkt përgjithmonë", key=f"confirm_del_p_{selected['id']}")
        if st.button("Fshij produktin", key=f"del_product_{selected['id']}", disabled=not confirm):
            database.delete_product(selected["id"])
            st.rerun()


# ==========================================
# 4. MESAZHET
# ==========================================
def _render_messages() -> None:
    st.markdown('<h1 class="kpb-h2">Mesazhet e kontaktit</h1>', unsafe_allow_html=True)
    status_filter = st.radio("Shfaq", ["I Palexuar", "I Përgjigjur", "I Arkivuar", "Të gjitha"], horizontal=True)
    messages = database.get_all_messages(None if status_filter == "Të gjitha" else status_filter)
    if not messages:
        st.info("Nuk ka mesazhe këtu.")
    for message in messages:
        with st.container(border=True):
            st.markdown(
                f"**{html.escape(message['name'])}** · {str(message['created_at'])[:16]} · "
                f"{_status_badge(message['status'])}  \n"
                f"{html.escape(message['email'] or '')} {html.escape(message['phone'] or '')}",
                unsafe_allow_html=True,
            )
            st.write(message["message"])
            columns = st.columns(4)
            if message["email"]:
                columns[0].link_button("Përgjigju me email", f"mailto:{message['email']}", use_container_width=True)
            link = checkout.whatsapp_link(message["phone"] or "", f"Përshëndetje {message['name']}, ")
            if link:
                columns[1].link_button("Përgjigju në WhatsApp", link, use_container_width=True)
            if columns[2].button("Shëno si të përgjigjur", key=f"msg_done_{message['id']}", use_container_width=True):
                database.update_message_status(message["id"], "I Përgjigjur")
                st.rerun()
            if columns[3].button("Arkivo", key=f"msg_arch_{message['id']}", use_container_width=True):
                database.update_message_status(message["id"], "I Arkivuar")
                st.rerun()


# ==========================================
# 5. VLERËSIMET
# ==========================================
def _render_testimonials() -> None:
    st.markdown('<h1 class="kpb-h2">Vlerësimet e klientëve</h1>', unsafe_allow_html=True)
    st.caption("Shtoni vetëm vlerësime të vërteta që ju kanë dhënë klientët (me lejen e tyre).")
    with st.form("add_testimonial", clear_on_submit=True):
        name_column, city_column, rating_column = st.columns([1.2, 1, 0.8])
        name = name_column.text_input("Emri i klientes *", max_chars=60)
        city = city_column.text_input("Qyteti", max_chars=40)
        rating = rating_column.select_slider("Yjet", options=[1, 2, 3, 4, 5], value=5)
        text = st.text_area("Vlerësimi *", max_chars=400)
        if st.form_submit_button("Shto vlerësimin", type="primary"):
            try:
                database.create_testimonial(name, text, rating, city)
                st.success("U shtua.")
            except ValueError as error:
                st.error(str(error))

    for item in database.get_all_testimonials():
        with st.container(border=True):
            text_column, visible_column, delete_column = st.columns([4, 1, 1], vertical_alignment="center")
            text_column.markdown(f"{'★' * item['rating']} **{html.escape(item['customer_name'])}** — "
                                 f"{html.escape(item['text'])}")
            visible = visible_column.toggle("I dukshëm", value=bool(item["is_visible"]), key=f"t_vis_{item['id']}")
            if visible != bool(item["is_visible"]):
                database.set_testimonial_visibility(item["id"], visible)
                st.rerun()
            if delete_column.button("Fshij", key=f"t_del_{item['id']}"):
                database.delete_testimonial(item["id"])
                st.rerun()


# ==========================================
# 6. CILËSIMET
# ==========================================
def _render_settings() -> None:
    st.markdown('<h1 class="kpb-h2">Cilësimet e dyqanit</h1>', unsafe_allow_html=True)
    settings = database.get_all_settings()
    with st.form("store_settings"):
        announcement = st.text_input("Shiriti i njoftimeve (lart në faqe)", value=settings.get("announcement_text", ""),
                                     max_chars=120)
        whatsapp = st.text_input("Numri i WhatsApp (me prefiks shteti, p.sh. 38344123456)",
                                 value=settings.get("whatsapp_number", ""), max_chars=20)
        fee_column, threshold_column = st.columns(2)
        fee = fee_column.number_input("Çmimi i transportit (€)", min_value=0.0, step=0.5, format="%.2f",
                                      value=checkout.shipping_rules(settings)[0])
        threshold = threshold_column.number_input("Transport falas mbi (€)", min_value=0.0, step=1.0, format="%.2f",
                                                  value=checkout.shipping_rules(settings)[1])
        hours = st.text_input("Orari i shërbimit", value=settings.get("business_hours", ""), max_chars=80,
                              placeholder="p.sh. E hënë – E shtunë, 09:00–20:00")
        contact_email = st.text_input("Email-i i kontaktit", value=settings.get("contact_email", ""), max_chars=120)
        location = st.text_input("Vendndodhja (në footer)", value=settings.get("store_location", ""), max_chars=60)
        instagram = st.text_input("Instagram (lidhja e plotë)", value=settings.get("instagram_url", ""), max_chars=200)
        facebook = st.text_input("Facebook (lidhja e plotë)", value=settings.get("facebook_url", ""), max_chars=200)
        hero_url = st.text_input("Fotoja e Hero-s (URL https)", value=settings.get("hero_image_url", ""), max_chars=300)
        logo_url = st.text_input("Logoja (URL https)", value=settings.get("logo_image_url", ""), max_chars=300)
        enforce = st.checkbox("Mos lejo porosi mbi stokun (ndizeni pasi të keni futur stokun e vërtetë)",
                              value=settings.get("enforce_stock") == "1")
        saved = st.form_submit_button("Ruaj cilësimet", type="primary")

    if saved:
        digits = "".join(ch for ch in whatsapp if ch.isdigit())
        if whatsapp.strip() and not 8 <= len(digits) <= 15:
            st.error("Numri i WhatsApp duhet të ketë 8–15 shifra.")
        elif contact_email.strip() and not checkout.EMAIL_PATTERN.match(contact_email.strip()):
            st.error("Email-i i kontaktit nuk duket i saktë.")
        elif any(url.strip() and not url.strip().startswith("https://")
                 for url in (instagram, facebook, hero_url, logo_url)):
            st.error("Lidhjet duhet të fillojnë me https://")
        else:
            for key, value in {
                "announcement_text": announcement, "whatsapp_number": digits,
                "shipping_fee": f"{fee:.2f}", "free_shipping_threshold": f"{threshold:.2f}",
                "business_hours": hours, "contact_email": contact_email, "enforce_stock": "1" if enforce else "0",
                "store_location": location, "instagram_url": instagram.strip(), "facebook_url": facebook.strip(),
                "hero_image_url": hero_url.strip(), "logo_image_url": logo_url.strip(),
            }.items():
                database.set_setting(key, value)
            st.success("Cilësimet u ruajtën.")


# ==========================================
# PIKA HYRËSE
# ==========================================
def render_admin(user: dict, image_uri: ImageUriFunction) -> None:
    theme.load_css("main", "pages", "admin")
    unread = database.count_unread_messages()
    with st.sidebar:
        logo = theme.asset_data_uri("logo.png")
        if logo:
            st.markdown(f'<img class="kpb-admin-logo" src="{logo}" alt="Korea Pure Beauty" />', unsafe_allow_html=True)
        st.markdown(f'<p class="kpb-muted">Administratori: <strong>{html.escape(user.get("full_name") or user["username"])}</strong>'
                    f'<br>{date.today().strftime("%d.%m.%Y")}</p>', unsafe_allow_html=True)
        labels = {page: (f"{page} ({unread})" if page == "Mesazhet" and unread else page) for page in PAGES}
        page = st.radio("Menyja", PAGES, format_func=labels.get, key="admin_page", label_visibility="collapsed")
        st.divider()
        if st.button("Dil nga llogaria", use_container_width=True):
            auth.end_session(st.query_params.get("session"))
            st.query_params.clear()
            st.session_state.authenticated = False
            st.session_state.current_user = None
            st.rerun()

    if page == "Dashboard":
        _render_dashboard()
    elif page == "Porositë":
        _render_orders()
    elif page == "Produktet":
        _render_products(image_uri)
    elif page == "Mesazhet":
        _render_messages()
    elif page == "Vlerësimet":
        _render_testimonials()
    else:
        _render_settings()
