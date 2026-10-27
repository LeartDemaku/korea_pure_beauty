# views/components.py
# Pjesë që përdoren në disa faqe: navigimi, karta e produktit, dritarja Quick-View, footer-i.
import html
from datetime import date
from typing import Callable

import streamlit as st

import cart
import catalog
import database
import theme

# Funksioni që kthen një foto produkti si data URI: (rruga, madhësia_max, cilësia) -> tekst
ImageUriFunction = Callable[[str, int, int], str]


def go_to(page: str, product_id: int | None = None) -> None:
    """Kalon te një faqe tjetër pa e rifreskuar browser-in (shporta dhe kyçja ruhen)."""
    st.session_state.current_page = page
    st.session_state.selected_product_id = product_id
    st.rerun()


def section_head(overline: str, title_html: str) -> None:
    st.markdown(f"""
    <div class="kpb-section-head">
      <span class="kpb-overline">{overline}</span>
      <h2 class="kpb-h2">{title_html}</h2>
    </div>
    """, unsafe_allow_html=True)


def product_card_html(product: dict, image_uri: ImageUriFunction) -> str:
    name = html.escape(product['name'])
    brand = html.escape(product['brand'])
    image = image_uri(product.get('image_url') or '', 420, 82)

    tags = ""
    if product.get('is_bestseller'):
        tags += '<span class="kpb-badge kpb-badge--accent">Bestseller</span>'
    discount = database.discount_percent(product['price'], product.get('old_price'))
    if discount:
        tags += f'<span class="kpb-badge">-{discount}%</span>'
    old_price = f'<span class="kpb-price--old">{product["old_price"]:.2f} €</span>' if discount else ""

    # data-search përdoret nga kërkimi i menjëhershëm (JavaScript) në Dyqan
    search_text = html.escape(" ".join(str(product.get(f) or "") for f in
                                       ("name", "brand", "category", "skin_type", "description")))
    return f"""
    <div class="kpb-pcard card-product-wrapper" data-search="{search_text}">
      <div class="kpb-pcard__media">
        <img src="{image}" alt="{name}" loading="lazy" />
        <div class="kpb-pcard__tags">{tags}</div>
      </div>
      <span class="kpb-pcard__brand">{brand}</span>
      <h3 class="kpb-pcard__name">{name}</h3>
      <div class="kpb-pcard__price"><span class="kpb-price">{product['price']:.2f} €</span>{old_price}</div>
    </div>
    """


def product_card(product: dict, image_uri: ImageUriFunction, key_prefix: str) -> None:
    """Karta e plotë: foto, emri, çmimi dhe dy butonat."""
    with st.container(key=f"kpb-pcard-{key_prefix}-{product['id']}"):
        st.markdown(product_card_html(product, image_uri), unsafe_allow_html=True)
        if st.button("Shto në shportë", key=f"{key_prefix}_add_{product['id']}",
                     type="primary", use_container_width=True):
            cart.add_to_cart(product)
            st.rerun()
        if st.button("Shiko detajet", key=f"{key_prefix}_view_{product['id']}", use_container_width=True):
            quick_view(product, image_uri)


@st.dialog("Detajet e produktit", width="large")
def quick_view(product: dict, image_uri: ImageUriFunction) -> None:
    """Dritarja Quick-View: hapet mbi faqe pa e humbur vendin ku ishte klienti."""
    image_column, info_column = st.columns([1, 1.1], gap="large")
    with image_column:
        st.markdown(
            f'<div class="kpb-qv__media"><img src="{image_uri(product.get("image_url") or "", 720, 88)}" '
            f'alt="{html.escape(product["name"])}" /></div>',
            unsafe_allow_html=True,
        )
    with info_column:
        discount = database.discount_percent(product['price'], product.get('old_price'))
        old_price = f'<span class="kpb-price--old">{product["old_price"]:.2f} €</span>' if discount else ""
        st.markdown(f"""
        <span class="kpb-pcard__brand">{html.escape(product['brand'])}</span>
        <h2 class="kpb-qv__name">{html.escape(product['name'])}</h2>
        <div class="kpb-qv__price"><span class="kpb-price">{product['price']:.2f} €</span>{old_price}</div>
        <div class="kpb-qv__meta">
          <span class="kpb-badge">{html.escape(catalog.category_group(product.get('category', '')))}</span>
          <span class="kpb-badge">{html.escape(product.get('skin_type') or '')}</span>
        </div>
        <p class="kpb-qv__desc">{html.escape(product.get('description') or '')}</p>
        """, unsafe_allow_html=True)
        if product.get('ingredients'):
            st.markdown(f"**Përbërësit kyç:** {html.escape(product['ingredients'])}")
        if product.get('how_to_use'):
            st.markdown(f"**Mënyra e përdorimit:** {html.escape(product['how_to_use'])}")

        quantity = st.number_input("Sasia", min_value=1, max_value=20, value=1, key=f"qv_qty_{product['id']}")
        if st.button("Shto në shportë", key=f"qv_add_{product['id']}", type="primary", use_container_width=True):
            cart.add_to_cart(product, int(quantity))
            st.rerun()  # mbyll dritaren dhe përditëson numrin e shportës


def render_footer() -> None:
    theme.load_css("pages")
    settings = database.get_all_settings()
    logo = theme.asset_data_uri("logo.png")
    logo_html = f'<img class="kpb-footer__logo" src="{logo}" alt="Korea Pure Beauty" />' if logo else \
        '<span class="kpb-footer__wordmark">Korea Pure Beauty</span>'

    whatsapp_digits = "".join(ch for ch in settings.get('whatsapp_number', '') if ch.isdigit())
    contact_items = ""
    if whatsapp_digits:
        contact_items += f'<li><a href="https://wa.me/{whatsapp_digits}" target="_blank" rel="noopener">WhatsApp: +{whatsapp_digits}</a></li>'
    if settings.get('contact_email'):
        email = html.escape(settings['contact_email'])
        contact_items += f'<li><a href="mailto:{email}">{email}</a></li>'
    if settings.get('business_hours'):
        contact_items += f"<li>{html.escape(settings['business_hours'])}</li>"
    if not contact_items:
        contact_items = "<li>Na shkruani te faqja e Kontaktit</li>"

    threshold = html.escape(settings.get('free_shipping_threshold', ''))
    free_shipping_html = f"<li>Transport falas mbi {threshold} €</li>" if threshold else ""

    st.markdown(f"""
    <footer class="kpb-footer">
      <div class="kpb-footer__grid">
        <div class="kpb-footer__brand">
          {logo_html}
          <p>Kujdes origjinal korean për lëkurën, i përzgjedhur me dashuri dhe i dërguar
          te dera juaj.</p>
        </div>
        <div>
          <h4>Dyqani</h4>
          <ul><li>Pastrues</li><li>Tonerë</li><li>Esenca &amp; Serume</li><li>Hidratues &amp; Kremra</li><li>Mbrojtës dielli</li></ul>
        </div>
        <div>
          <h4>Shërbimi</h4>
          <ul><li>Dërgesa 24–48 orë</li><li>Pagesë në dorëzim</li>{free_shipping_html}<li>Kthim brenda 14 ditëve</li></ul>
        </div>
        <div>
          <h4>Kontakt</h4>
          <ul>{contact_items}</ul>
        </div>
      </div>
      <div class="kpb-footer__bottom">© {date.today().year} Korea Pure Beauty. Të gjitha të drejtat e rezervuara.</div>
    </footer>
    """, unsafe_allow_html=True)

    with st.container(key="kpb-footer-links"):
        left, middle, right = st.columns(3)
        with left:
            if st.button("Kontakt & FAQ", key="footer_contact", use_container_width=True):
                go_to("contact")
        with middle:
            if st.button("Privatësia & Kushtet", key="footer_privacy", use_container_width=True):
                go_to("privacy")
        with right:
            if st.button("Ndërtoni ritualin", key="footer_ritual", use_container_width=True):
                go_to("ritual")
