# views/home_view.py
# Faqja kryesore (Ballina): Hero, Rituali, Koleksioni i përzgjedhur,
# Pse Korea Pure Beauty, Vlerësimet dhe Footer-i.
import html
from datetime import date
from typing import Callable

import streamlit as st

import cart
import database
import theme

# Funksioni që kthen një foto produkti si data URI: (rruga, madhësia_max, cilësia) -> tekst
ImageUriFunction = Callable[[str, int, int], str]

RITUAL_STEPS = [
    {
        "number": "01",
        "action": "Pastroni",
        "title": "Pastrim i dyfishtë",
        "text": "Balsami pastrues shkrin kremin mbrojtës dhe papastërtitë. "
                "Pastaj xheli i butë pastron porët pa e tharë lëkurën.",
    },
    {
        "number": "02",
        "action": "Balanconi",
        "title": "Ekuilibër",
        "text": "Toneri me çaj jeshil e qetëson lëkurën dhe e përgatit "
                "që të thithë më mirë hapat e trajtimit.",
    },
    {
        "number": "03",
        "action": "Trajtoni",
        "title": "Mëngjes · Mbrëmje",
        "text": "Vitamina C në mëngjes për shkëlqim. Retinali në mbrëmje "
                "për rinovim dhe teksturë më të lëmuar.",
    },
    {
        "number": "04",
        "action": "Hidratoni & mbroni",
        "title": "Mbyllja e ritualit",
        "text": "Mucina e kërmillit mbyll hidratimin. SPF-ja çdo mëngjes "
                "i mbron rezultatet nga dielli.",
    },
]

# Ikona të thjeshta me vija (SVG), që marrin ngjyrën nga CSS (currentColor)
_ICON_ATTRS = 'width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"'
TRUST_POINTS = [
    {
        "icon": f'<svg {_ICON_ATTRS}><path d="M2.5 19h19"/><path d="M3.5 13.5 8 15l9-6.5c1-.7 2.4-.6 3 .3.4.7.1 1.6-.6 2L8.6 17.6 4.3 16.4z"/></svg>',
        "title": "Import direkt nga Seuli",
        "text": "Produktet vijnë direkt nga Koreja e Jugut, pa ndërmjetës.",
    },
    {
        "icon": f'<svg {_ICON_ATTRS}><path d="M12 3 4.5 6v5.5c0 4.6 3.2 8.3 7.5 9.5 4.3-1.2 7.5-4.9 7.5-9.5V6z"/><path d="m8.8 12.2 2.2 2.2 4.3-4.6"/></svg>',
        "title": "Formulime origjinale",
        "text": "100% K-Beauty origjinale, me paketimin dhe etiketat e prodhuesit.",
    },
    {
        "icon": f'<svg {_ICON_ATTRS}><path d="M3 7h11v9H3z"/><path d="M14 10h4l3 3v3h-7"/><circle cx="7" cy="17.5" r="1.6"/><circle cx="17" cy="17.5" r="1.6"/></svg>',
        "title": "Dërgesa 24–48 orë",
        "text": "Në Kosovë, Shqipëri dhe Maqedoni të Veriut.",
    },
    {
        "icon": f'<svg {_ICON_ATTRS}><rect x="3" y="6" width="18" height="12" rx="2"/><circle cx="12" cy="12" r="2.5"/><path d="M6.5 9.5v5M17.5 9.5v5"/></svg>',
        "title": "Pagesë në dorëzim",
        "text": "Paguani me para në dorë kur ta merrni porosinë.",
    },
]


def _go_to(page: str, product_id: int | None = None) -> None:
    """Kalon te një faqe tjetër pa e rifreskuar browser-in (shporta dhe kyçja ruhen)."""
    st.session_state.current_page = page
    st.session_state.selected_product_id = product_id
    st.rerun()


# ==========================================
# 1. HERO
# ==========================================
def _render_hero() -> None:
    with st.container(key="kpb-hero"):
        text_column, image_column = st.columns([1.05, 1], gap="large", vertical_alignment="center")

        with text_column:
            st.markdown("""
            <div class="kpb-hero__text">
              <span class="kpb-overline">K-Secret · Premium Korean Skincare</span>
              <h1 class="kpb-display">Sekreti korean i një lëkure <span class="kpb-accent">rrezatuese</span></h1>
              <p class="kpb-lead">Linja Seoul 1988 bashkon xhensenin e zi, retinalin dhe vitaminën C
              në formula të lehta që e ushqejnë lëkurën shtresë pas shtrese, për një shkëlqim
              të natyrshëm, ditë pas dite.</p>
            </div>
            """, unsafe_allow_html=True)

            with st.container(key="kpb-hero-actions"):
                button_column, link_column = st.columns([1, 1.1], vertical_alignment="center")
                with button_column:
                    if st.button("Zbulo produktet", key="hero_cta_shop", type="primary", use_container_width=True):
                        _go_to("shop")
                with link_column:
                    # Lidhje brenda së njëjtës faqe (#rituali): nuk e rifreskon faqen
                    st.markdown(
                        '<a class="kpb-link-arrow" href="#rituali" target="_self">Rituali në 4 hapa →</a>',
                        unsafe_allow_html=True,
                    )

        with image_column:
            hero_image = theme.asset_data_uri("hero_arch.webp")
            image_html = (
                f'<img src="{hero_image}" alt="Serume dhe kremra luksoze koreane" />' if hero_image else ""
            )
            st.markdown(f"""
            <figure class="kpb-hero__visual">
              <div class="kpb-hero__arch">{image_html}</div>
              <span class="kpb-badge kpb-hero__tag"><span class="kpb-badge__dot"></span>100% origjinale · Prodhuar në Seul</span>
            </figure>
            """, unsafe_allow_html=True)


# ==========================================
# 2. RITUALI (sfond Dark Espresso)
# ==========================================
def _render_ritual() -> None:
    steps_html = "".join(
        f"""
        <article class="kpb-ritual__step">
          <div class="kpb-step-number">{step['number']}</div>
          <span class="kpb-ritual__action">{step['action']}</span>
          <h3 class="kpb-ritual__title">{step['title']}</h3>
          <p class="kpb-ritual__text">{step['text']}</p>
        </article>"""
        for step in RITUAL_STEPS
    )
    st.markdown(f"""
    <section id="rituali" class="kpb-section-dark kpb-ritual" aria-labelledby="rituali-titulli">
      <div class="kpb-ritual__head">
        <div>
          <span class="kpb-overline kpb-overline--gold">Rituali korean</span>
          <h2 id="rituali-titulli" class="kpb-h2">Katër hapa, një lëkurë që <span class="kpb-accent">flet vetë</span></h2>
        </div>
        <p class="kpb-lead">Filozofia koreane nuk kërkon produkte të rënda, por shtresa të lehta
        që punojnë së bashku. Çdo hap e përgatit lëkurën për hapin tjetër.</p>
      </div>
      <div class="kpb-ritual__steps">{steps_html}</div>
    </section>
    """, unsafe_allow_html=True)


# ==========================================
# 3. KOLEKSIONI I PËRZGJEDHUR
# ==========================================
def _product_card_html(product: dict, image_uri: ImageUriFunction) -> str:
    name = html.escape(product['name'])
    brand = html.escape(product['brand'])
    image = image_uri(product.get('image_url') or '', 420, 82)

    tags = ""
    if product.get('is_bestseller'):
        tags += '<span class="kpb-badge kpb-badge--accent">Bestseller</span>'
    discount = database.discount_percent(product['price'], product.get('old_price'))
    if discount:
        tags += f'<span class="kpb-badge">-{discount}%</span>'

    old_price = (
        f'<span class="kpb-price--old">{product["old_price"]:.2f} €</span>' if discount else ""
    )
    return f"""
    <div class="kpb-pcard">
      <div class="kpb-pcard__media">
        <img src="{image}" alt="{name}" loading="lazy" />
        <div class="kpb-pcard__tags">{tags}</div>
      </div>
      <span class="kpb-pcard__brand">{brand}</span>
      <h3 class="kpb-pcard__name">{name}</h3>
      <div class="kpb-pcard__price"><span class="kpb-price">{product['price']:.2f} €</span>{old_price}</div>
    </div>
    """


def _render_featured(image_uri: ImageUriFunction) -> None:
    products = database.get_featured_products(limit=4)
    if not products:
        return  # Pa produkte në databazë, seksioni nuk shfaqet

    st.markdown("""
    <div class="kpb-section-head">
      <div>
        <span class="kpb-overline">Koleksioni i përzgjedhur</span>
        <h2 class="kpb-h2">Të zgjedhura për <span class="kpb-accent">lëkurën tuaj</span></h2>
      </div>
    </div>
    """, unsafe_allow_html=True)

    columns = st.columns(4, gap="medium")
    for column, product in zip(columns, products):
        with column:
            with st.container(key=f"kpb-pcard-{product['id']}"):
                st.markdown(_product_card_html(product, image_uri), unsafe_allow_html=True)
                if st.button("Shto në shportë", key=f"home_add_{product['id']}",
                             type="primary", use_container_width=True):
                    cart.add_to_cart(product)
                    st.rerun()
                if st.button("Shiko detajet", key=f"home_view_{product['id']}", use_container_width=True):
                    _go_to("shop", product['id'])

    _, center_column, _ = st.columns([1, 1, 1])
    with center_column:
        if st.button("Shiko të gjitha produktet →", key="home_all_products", use_container_width=True):
            _go_to("shop")


# ==========================================
# 4. PSE KOREA PURE BEAUTY
# ==========================================
def _render_trust() -> None:
    items_html = "".join(
        f"""
        <div class="kpb-trust__item">
          <span class="kpb-trust__icon">{point['icon']}</span>
          <h3 class="kpb-trust__title">{point['title']}</h3>
          <p class="kpb-trust__text">{point['text']}</p>
        </div>"""
        for point in TRUST_POINTS
    )
    st.markdown(f"""
    <section class="kpb-trust" aria-label="Pse Korea Pure Beauty">
      {items_html}
    </section>
    """, unsafe_allow_html=True)


# ==========================================
# 5. VLERËSIMET E KLIENTEVE
# Shfaqen vetëm vlerësime të vërteta nga databaza. Pa vlerësime, seksioni fshihet.
# ==========================================
def _render_testimonials() -> None:
    testimonials = database.get_visible_testimonials(limit=3)
    if not testimonials:
        return

    cards_html = ""
    for item in testimonials:
        stars = "★" * item['rating'] + "☆" * (5 - item['rating'])
        city = f" · {html.escape(item['city'])}" if item.get('city') else ""
        cards_html += f"""
        <figure class="kpb-testimonial">
          <div class="kpb-testimonial__stars" aria-label="{item['rating']} nga 5 yje">{stars}</div>
          <blockquote>“{html.escape(item['text'])}”</blockquote>
          <figcaption>{html.escape(item['customer_name'])}{city}</figcaption>
        </figure>"""

    st.markdown(f"""
    <div class="kpb-section-head">
      <div>
        <span class="kpb-overline">Vlerësimet</span>
        <h2 class="kpb-h2">Çfarë thonë <span class="kpb-accent">klientet</span></h2>
      </div>
    </div>
    <div class="kpb-testimonials">{cards_html}</div>
    """, unsafe_allow_html=True)


# ==========================================
# 6. FOOTER (i përbashkët; faqet e tjera do ta përdorin në Fazën 3)
# ==========================================
def render_footer() -> None:
    settings = database.get_all_settings()
    logo = theme.asset_data_uri("logo.png")
    logo_html = f'<img class="kpb-footer__logo" src="{logo}" alt="Korea Pure Beauty" />' if logo else \
        '<span class="kpb-footer__wordmark">Korea Pure Beauty</span>'

    whatsapp_digits = "".join(ch for ch in settings.get('whatsapp_number', '') if ch.isdigit())
    whatsapp_html = (
        f'<li><a href="https://wa.me/{whatsapp_digits}" target="_blank" rel="noopener">WhatsApp: +{whatsapp_digits}</a></li>'
        if whatsapp_digits else '<li>Na shkruani përmes faqes së Kontaktit</li>'
    )
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
          <ul><li>Dërgesa 24–48 orë</li><li>Pagesë në dorëzim</li>{free_shipping_html}</ul>
        </div>
        <div>
          <h4>Kontakt</h4>
          <ul>{whatsapp_html}</ul>
        </div>
      </div>
      <div class="kpb-footer__bottom">© {date.today().year} Korea Pure Beauty. Të gjitha të drejtat e rezervuara.</div>
    </footer>
    """, unsafe_allow_html=True)


# ==========================================
# PIKA HYRËSE E FAQES
# ==========================================
def render_home(image_uri: ImageUriFunction) -> None:
    theme.load_css("hero", "ritual", "shop", "home")
    _render_hero()
    _render_ritual()
    _render_featured(image_uri)
    _render_trust()
    _render_testimonials()
    render_footer()
