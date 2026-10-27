# views/storefront.py
# Dyqani i plotë në një faqe, i njëjtë me korea-pure-beauty.mjegulla.app:
# Njoftimi → Header → Hero → Dyqani → Rituali → Kontakti & Footer.
# Shporta hapet si sirtar në të djathtë; produkti hapet në një dritare (modal).
import html
import re
from datetime import date
from typing import Callable

import streamlit as st

import auth
import cart
import catalog
import checkout
import database
import email_service
from views import account

ImageUriFunction = Callable[[str, int, int], str]

RITUAL_STEPS = [
    ("01", "Pastrim i dyfishtë", "Pastroni", "Balsami pastrues shkrin grimin, pasuar nga xheli i butë."),
    ("02", "Ekuilibër", "Balanconi", "Toneri me çaj jeshil përgatit lëkurën dhe ngushton poret."),
    ("03", "Mëngjes · Mbrëmje", "Trajtoni", "Serumi me vitaminë C në mëngjes, me retinal në mbrëmje."),
    ("04", "Mbyllja e ritualit", "Hidratoni &amp; mbroni",
     "Kremi me mucinë kërmilli bllokon lagështinë; mbrojtës diellor çdo mëngjes."),
]
PHONE_PATTERN = re.compile(r"^\+?[0-9 ()\-]{6,20}$")

_SVG = 'xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"'
ICON_PIN = f'<svg {_SVG}><path d="M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0"/><circle cx="12" cy="10" r="3"/></svg>'
ICON_PHONE = f'<svg {_SVG}><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.91.34 1.85.57 2.81.7A2 2 0 0 1 22 16.92z"/></svg>'
ICON_MAIL = f'<svg {_SVG}><rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>'
ICON_IG = f'<svg {_SVG} width="15" height="15"><rect width="20" height="20" x="2" y="2" rx="5"/><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/><line x1="17.5" x2="17.51" y1="6.5" y2="6.5"/></svg>'
ICON_FB = f'<svg {_SVG} width="15" height="15"><path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"/></svg>'


def _esc(value) -> str:
    return html.escape(str(value or ""))


def _settings() -> dict:
    if "_kpb_settings" not in st.session_state.get("_run_cache", {}):
        st.session_state.setdefault("_run_cache", {})["_kpb_settings"] = database.get_all_settings()
    return st.session_state["_run_cache"]["_kpb_settings"]


def _logo_url() -> str:
    return _esc(_settings().get("logo_image_url"))


def _md(markup: str) -> None:
    st.markdown(markup, unsafe_allow_html=True)


# ==========================================
# 1. NJOFTIMI DHE HEADER-I
# ==========================================
def _render_announcement() -> None:
    text = _settings().get("announcement_text") or ""
    if text:
        _md(f'<p class="kpb-announce kpb-bleed"><span>{_esc(text)}</span>'
            '<span class="dot opt" aria-hidden="true">·</span><span class="opt">Produkte origjinale koreane</span></p>')


def _render_header() -> None:
    with st.container(key="kpb-header"):
        brand_column, nav_column, actions_column = st.columns([1.15, 1, 1.15], vertical_alignment="center")
        with brand_column:
            logo = _logo_url()
            logo_img = f'<img src="{logo}" alt="Logoja e Korea Pure Beauty" />' if logo else ""
            _md(f'<a class="kpb-brand" href="#kreu" target="_self" aria-label="Korea Pure Beauty, kreu">{logo_img}'
                '<span><span class="kpb-brand__name">Korea Pure</span><span class="kpb-brand__script">Beauty</span></span></a>')
        with nav_column:
            _md('<nav class="kpb-nav" aria-label="Navigimi kryesor">'
                '<a href="#dyqani" target="_self">Dyqani</a><a href="#rituali" target="_self">Rituali</a>'
                '<a href="#kontakt" target="_self">Kontakt</a></nav>')
        with actions_column:
            with st.container(key="kpb-header-actions"):
                account_column, cart_column = st.columns(2)
                with account_column:
                    signed_in = st.session_state.get("authenticated")
                    with st.popover("Llogaria" if not signed_in else "Profili"):
                        account.render_account_menu()
                with cart_column:
                    if st.button(f"Shporta ({cart.cart_item_count()})", key="kpb-open-cart",
                                 icon=":material/shopping_bag:"):
                        st.session_state.cart_step = "items"
                        cart_drawer()


# ==========================================
# 2. HERO
# ==========================================
def _render_hero(product_count: int) -> None:
    hero_image = _esc(_settings().get("hero_image_url"))
    image_html = (f'<img src="{hero_image}" alt="Produkte koreane për kujdesin e lëkurës mbi sfond të ngrohtë" />'
                  if hero_image else "")
    _md(f"""
<section id="kreu" class="kpb-hero" aria-labelledby="hero-title">
  <div class="kpb-hero__glow" aria-hidden="true"></div>
  <div class="kpb-hero__grid">
    <div>
      <p class="kpb-hero__eyebrow rise" style="animation-delay:.05s">K-Secret · Premium Korean Skincare</p>
      <h1 id="hero-title" class="rise" style="animation-delay:.15s">Sekreti korean i një lëkure<span class="rose-text font-script">rrezatuese</span></h1>
      <p class="kpb-hero__lead rise" style="animation-delay:.3s">Serume, kremra dhe maska nga linja Seoul 1988 e K-Secret —
      formula me xhensen të zi, retinal dhe vitaminë C, të sjella drejtpërdrejt nga Koreja për ritualin tuaj të përditshëm.</p>
      <div class="kpb-hero__ctas rise" style="animation-delay:.45s">
        <a class="kpb-btn-primary" href="#dyqani" target="_self">Zbulo produktet</a>
        <a class="kpb-link-under" href="#rituali" target="_self">Rituali në 4 hapa<span aria-hidden="true">→</span></a>
      </div>
      <ul class="kpb-hero__stats rise" style="animation-delay:.6s">
        <li><strong>{product_count}+</strong><span class="muted">produkte</span></li>
        <li><span class="medium">100% origjinale</span></li>
        <li><span class="medium">Dërgesë 24–48 orë</span></li>
      </ul>
    </div>
    <div class="kpb-hero__visual rise" style="animation-delay:.25s">
      <div class="kpb-hero__outline" aria-hidden="true"></div>
      <div class="kpb-hero__arch">{image_html}</div>
      <div class="kpb-hero__badge"><p class="t1">100% origjinale</p><p class="t2">Prodhuar në Seul</p></div>
    </div>
  </div>
</section>""")


# ==========================================
# 3. DYQANI
# ==========================================
def _card_html(product: dict, image_uri: ImageUriFunction) -> str:
    badge = catalog.product_badge(product)
    badge_html = f'<span class="kpb-tag">{_esc(badge)}</span>' if badge else ""
    image = image_uri(product.get("image_url") or "", 600, 85)
    return (f'<div class="kpb-card__media">'
            f'<img src="{image}" alt="{_esc(product["name"])}" loading="lazy" />{badge_html}</div>'
            f'<p class="kpb-card__cat">{_esc(catalog.store_tab_of(product))}</p>')


def _price_html(product: dict) -> str:
    discount = database.discount_percent(product["price"], product.get("old_price"))
    old = f'<span class="old">{catalog.format_eur(product["old_price"])}</span>' if discount else ""
    return (f'<div class="kpb-card__price"><span><span class="p">{catalog.format_eur(product["price"])}</span>{old}</span>'
            f'<span class="s">{_esc(product.get("size_label"))}</span></div>')


def _product_card(product: dict, image_uri: ImageUriFunction) -> None:
    pid = product["id"]
    with st.container(key=f"kpb-card-{pid}"):
        _md(_card_html(product, image_uri))
        if st.button(product["name"], key=f"kpb-title-{pid}", help="Shiko detajet"):
            st.session_state.qv_qty = 1
            product_dialog(product, image_uri)
        _md(f'<p class="kpb-card__desc">{_esc(product.get("description"))}</p>{_price_html(product)}')
        if st.button("Shto në shportë", key=f"kpb-add-{pid}", icon=":material/shopping_bag:",
                     use_container_width=True):
            cart.add_to_cart(product)
            st.session_state.open_cart = True
            st.rerun()


def _render_shop(products: list, image_uri: ImageUriFunction) -> None:
    _md('<div id="dyqani"></div>')
    with st.container(key="kpb-shop"):
        with st.container(key="kpb-shop-head"):
            title_column, tabs_column = st.columns([1, 1.15], vertical_alignment="bottom")
            all_kpop = all((p.get("brand") or "").lower().replace("-", "") == "ksecret" for p in products)
            collection = "Koleksioni K-Secret" if products and all_kpop else "Koleksioni K-Beauty"
            with title_column:
                _md(f'<p class="kpb-eyebrow">Dyqani</p><h2 class="kpb-shop-title">{collection}</h2>'
                    '<p class="kpb-shop-sub">Zgjidhni hapin që i mungon ritualit tuaj.</p>')
            with tabs_column:
                tabs = [catalog.ALL_LABEL, *catalog.STORE_TABS]
                selected = st.pills("Kategoria", tabs, default=catalog.ALL_LABEL, key="kpb-tab",
                                    label_visibility="collapsed") or catalog.ALL_LABEL
                visible = catalog.filter_by_tab(products, selected)
                word = "produkt" if len(visible) == 1 else "produkte"
                _md(f'<p class="kpb-count" aria-live="polite">{len(visible)} {word}</p>')

        with st.container(key="kpb-grid"):
            if not visible:
                _md('<p class="kpb-empty-shop">Së shpejti produkte të reja në këtë kategori.</p>')
            for start in range(0, len(visible), 4):
                row = visible[start:start + 4]
                for index, column in enumerate(st.columns(4)):
                    with column:  # kolonat bosh mbajnë gjerësinë e njëjtë të kartave
                        if index < len(row):
                            _product_card(row[index], image_uri)


# ==========================================
# 4. RITUALI
# ==========================================
def _render_ritual() -> None:
    _md('<div id="rituali"></div>')
    with st.container(key="kpb-ritual"):
        left, right = st.columns([5, 7])
        with left:
            _md('<div class="kpb-ritual-head"><div class="line"><span>Rituali</span></div>'
                '<h2>Katër hapa, një lëkurë që <span class="font-script">flet vetë</span></h2>'
                '<p>Filozofia koreane e bukurisë nuk ka të bëjë me shumë produkte, por me shtresa të lehta '
                'që punojnë së bashku. Ja si i përdorni produktet çdo ditë.</p></div>')
            if st.button("Ndërtoni ritualin tuaj  →", key="kpb-ritual-cta"):
                ritual_dialog()
        with right:
            steps = "".join(
                f'<li><span class="n" aria-hidden="true">{n}</span><div class="k"><small>{label}</small>'
                f'<h3>{title}</h3><p>{text}</p></div></li>'
                for n, label, title, text in RITUAL_STEPS
            )
            _md(f'<ol class="kpb-steps">{steps}</ol>')


# ==========================================
# 5. KONTAKTI & FOOTER
# ==========================================
def _contact_errors(name: str, email: str, phone: str, message: str) -> list[str]:
    errors = []
    if not name.strip():
        errors.append("Shkruani emrin.")
    if not email.strip() and not phone.strip():
        errors.append("Shkruani email-in ose telefonin, që t'ju përgjigjemi.")
    if email.strip() and not auth.is_valid_email(email.strip()):
        errors.append("Email-i nuk duket i saktë.")
    if phone.strip() and not PHONE_PATTERN.match(phone.strip()):
        errors.append("Numri i telefonit nuk është i saktë.")
    if not message.strip():
        errors.append("Shkruani mesazhin.")
    return errors


def _render_contact() -> None:
    settings = _settings()
    whatsapp = "".join(ch for ch in settings.get("whatsapp_number", "") if ch.isdigit())
    _md('<div id="kontakt"></div>')
    with st.container(key="kpb-contact"):
        with st.container(key="kpb-contact-form-row"):
            text_column, form_column = st.columns([5, 7])
            with text_column:
                _md('<p class="kpb-eyebrow">Kontakt</p><h2 class="kpb-contact-title">Na shkruani</h2>'
                    '<p class="kpb-contact-sub">Keni pyetje për lëkurën tuaj apo për një porosi? '
                    'Konsulentet tona ju përgjigjen sa më shpejt.</p>')
            with form_column:
                with st.form("kpb-contact-form", clear_on_submit=True):
                    name_column, phone_column = st.columns(2)
                    name = name_column.text_input("Emri *", max_chars=80)
                    phone = phone_column.text_input("Telefoni", max_chars=20)
                    email = st.text_input("Email-i", max_chars=120)
                    message = st.text_area("Mesazhi *", max_chars=2000, height=110)
                    sent = st.form_submit_button("Dërgo mesazhin", type="primary", use_container_width=True)
                if sent:
                    errors = _contact_errors(name, email, phone, message)
                    for error in errors:
                        st.error(error)
                    if not errors:
                        database.create_message(name, message, email=email, phone=phone)
                        email_service.send_contact_notification_email(name, email, phone, message)
                        st.success("Faleminderit! Mesazhi u dërgua.")

        contact_items = f'<li><span class="ico">{ICON_PIN}</span>{_esc(settings.get("store_location"))}</li>' \
            if settings.get("store_location") else ""
        if whatsapp:
            contact_items += (f'<li><a href="https://wa.me/{whatsapp}" target="_blank" rel="noopener" style="display:flex;gap:.75rem;align-items:center">'
                              f'<span class="ico">{ICON_PHONE}</span><span><span style="color:var(--muted-fg)">WhatsApp/Viber:</span> +{whatsapp}</span></a></li>')
        if settings.get("contact_email"):
            mail = _esc(settings["contact_email"])
            contact_items += (f'<li><a href="mailto:{mail}" style="display:flex;gap:.75rem;align-items:center">'
                              f'<span class="ico">{ICON_MAIL}</span>{mail}</a></li>')
        social = ""
        for url_key, label, icon in (("instagram_url", "Instagram", ICON_IG), ("facebook_url", "Facebook", ICON_FB)):
            if settings.get(url_key):
                social += (f'<li><a href="{_esc(settings[url_key])}" target="_blank" rel="noopener noreferrer" '
                           f'style="display:flex;gap:.75rem;align-items:center"><span class="soc">{icon}</span>{label}</a></li>')
        social_column = f'<div><h3 class="kpb-fh">Na ndiqni</h3><ul class="kpb-flist">{social}</ul></div>' if social else "<div></div>"
        fee, threshold = checkout.shipping_rules(settings)
        logo = _logo_url()
        logo_img = f'<img src="{logo}" alt="Korea Pure Beauty" />' if logo else ""
        _md(f"""
<div class="kpb-footer-grid">
  <div>
    <a class="kpb-footer-brand" href="#kreu" target="_self">{logo_img}<span><span class="a">KOREA PURE</span><span class="b">Beauty</span></span></a>
    <p class="kpb-footer-about"><b>Premium Korean Skincare</b> — produkte origjinale koreane, të zgjedhura me kujdes për lëkurën tuaj.</p>
  </div>
  <div><h3 class="kpb-fh">Kontakt</h3><ul class="kpb-flist">{contact_items}</ul></div>
  <div><h3 class="kpb-fh">Informacion</h3><ul class="kpb-info">
    <li>Dërgesa 24–48 orë në gjithë Kosovën</li><li>Pagesa me para në dorë</li>
    <li>Dërgesë falas mbi {catalog.format_eur(threshold)}</li><li>Kthim brenda 14 ditëve</li></ul></div>
  {social_column}
</div>""")

    with st.container(key="kpb-footer-bottom"):
        copy_column, link_column = st.columns([3, 1], vertical_alignment="center")
        copy_column.markdown(f'<p class="kpb-copy">© {date.today().year} Korea Pure Beauty. '
                             'Të gjitha të drejtat e rezervuara.</p>', unsafe_allow_html=True)
        with link_column:
            if st.button("Privatësia & Kushtet", key="kpb-privacy"):
                privacy_dialog()


# ==========================================
# 6. DIALOGËT
# ==========================================
@st.dialog("Detajet e produktit", width="large")
def product_dialog(product: dict, image_uri: ImageUriFunction) -> None:
    badge = catalog.product_badge(product)
    badge_html = f'<span class="kpb-tag">{_esc(badge)}</span>' if badge else ""
    image_column, info_column = st.columns(2, gap="large")
    with image_column:
        _md(f'<div class="kpb-qv__media"><img src="{image_uri(product.get("image_url") or "", 900, 88)}" '
            f'alt="{_esc(product["name"])}" />{badge_html}</div>')
    with info_column:
        size = f'<span class="s">· {_esc(product["size_label"])}</span>' if product.get("size_label") else ""
        description = product.get("description") or ""
        extra = ""
        if product.get("ingredients"):
            extra += f'<p class="kpb-qv__desc"><b>Përbërësit kyç:</b> {_esc(product["ingredients"])}</p>'
        if product.get("how_to_use"):
            extra += f'<p class="kpb-qv__desc"><b>Përdorimi:</b> {_esc(product["how_to_use"])}</p>'
        _md(f'<p class="kpb-qv__cat">{_esc(catalog.store_tab_of(product))}</p>'
            f'<h3 class="kpb-qv__title">{_esc(product["name"])}</h3>'
            f'<div class="kpb-qv__price"><span class="p">{catalog.format_eur(product["price"])}</span>{size}</div>'
            f'<p class="kpb-qv__desc">{_esc(description)}</p>{extra}')
        quantity = st.session_state.get("qv_qty", 1)
        with st.container(key="kpb-qv-buy"):
            qty_column, add_column = st.columns([1, 1.6])
            with qty_column:
                with st.container(key="kpb-qty-qv"):
                    minus, number, plus = st.columns(3, vertical_alignment="center")
                    if minus.button("−", key="qv-minus", disabled=quantity <= 1):
                        st.session_state.qv_qty = max(1, quantity - 1)
                        st.rerun(scope="fragment")
                    number.markdown(f'<p class="kpb-qty-n">{quantity}</p>', unsafe_allow_html=True)
                    if plus.button("+", key="qv-plus", disabled=quantity >= 20):
                        st.session_state.qv_qty = min(20, quantity + 1)
                        st.rerun(scope="fragment")
            with add_column:
                with st.container(key="kpb-qv-add"):
                    if st.button("Shto në shportë", key="qv-add", type="primary", icon=":material/shopping_bag:",
                                 use_container_width=True):
                        cart.add_to_cart(product, quantity)
                        st.session_state.qv_qty = 1
                        st.session_state.open_cart = True
                        st.rerun()
        _md('<ul class="kpb-qv__perks"><li>Produkt origjinal</li><li>Dërgesë 24–48 orë</li></ul>')


@st.dialog("Shporta juaj")
def cart_drawer() -> None:
    _md('<span class="kpb-drawer-mark"></span>')
    step = st.session_state.get("cart_step", "items")
    items = st.session_state.cart
    count = cart.cart_item_count()
    word = "artikull" if count == 1 else "artikuj"
    _md(f'<div class="kpb-drawer-head"><p class="kpb-eyebrow">Korea Pure Beauty</p>'
        f'<p class="t">Shporta juaj<span>({count} {word})</span></p></div>')

    if step == "done" and st.session_state.get("last_order"):
        _render_order_done(st.session_state.last_order)
        return
    if not items:
        _md('<div class="kpb-drawer-empty"><p class="t">Shporta është bosh</p>'
            '<p class="d">Zgjidhni serumin, kremin apo maskën që i përshtatet ritualit tuaj të përditshëm.</p></div>')
        if st.button("Vazhdo blerjet  →", key="drawer-continue"):
            st.rerun()
        return
    if step == "checkout":
        _render_checkout_form()
        return

    for key, item in list(items.items()):
        safe_key = re.sub(r"[^a-zA-Z0-9]", "-", key)
        with st.container(key=f"kpb-line-{safe_key}"):
            image_column, info_column = st.columns([1, 4])
            image_column.markdown(f'<div class="kpb-line-img"><img src="{_cart_image(item)}" alt="" /></div>',
                                  unsafe_allow_html=True)
            with info_column:
                _md(f'<div class="kpb-line-top"><p class="n">{_esc(item["name"])}</p>'
                    f'<p class="p">{catalog.format_eur(item["price"] * item["qty"])}</p></div>'
                    f'<p class="kpb-line-meta">{_esc(item.get("size") or item.get("brand"))} · {catalog.format_eur(item["price"])}</p>')
                qty_column, remove_column = st.columns([1.3, 1], vertical_alignment="center")
                with qty_column:
                    with st.container(key=f"kpb-qty-{safe_key}"):
                        minus, number, plus = st.columns(3, vertical_alignment="center")
                        if minus.button("−", key=f"dec-{safe_key}"):
                            if item["qty"] <= 1:
                                del items[key]
                            else:
                                item["qty"] -= 1
                            st.rerun(scope="fragment")
                        number.markdown(f'<p class="kpb-qty-n">{item["qty"]}</p>', unsafe_allow_html=True)
                        if plus.button("+", key=f"inc-{safe_key}", disabled=item["qty"] >= 50):
                            item["qty"] += 1
                            st.rerun(scope="fragment")
                with remove_column:
                    if st.button("Hiq", key=f"kpb-remove-{safe_key}"):
                        del items[key]
                        st.rerun(scope="fragment")

    totals = checkout.calculate_totals(cart.cart_subtotal(), _settings())
    _render_summary(totals)
    if st.button("Vazhdo me porosinë  →", key="drawer-checkout", type="primary", use_container_width=True):
        st.session_state.cart_step = "checkout"
        st.rerun(scope="fragment")


_cart_image_function: ImageUriFunction | None = None


def _cart_image(item: dict) -> str:
    return _cart_image_function(item.get("image") or "", 200, 80) if _cart_image_function else ""


def _render_summary(totals: dict) -> None:
    progress = min(100.0, totals["subtotal"] / totals["threshold"] * 100) if totals["threshold"] else 100.0
    free = (f'Edhe <strong>{catalog.format_eur(totals["missing_for_free_shipping"])}</strong> për dërgesë falas'
            if totals["missing_for_free_shipping"] > 0 else "Dërgesa juaj është <strong>falas</strong>")
    shipping = "Falas" if totals["shipping"] == 0 else catalog.format_eur(totals["shipping"])
    discount = (f'<div><dt>Zbritja</dt><dd>−{catalog.format_eur(totals["discount"])}</dd></div>'
                if totals["discount"] else "")
    _md(f'<div class="kpb-sum"><p class="kpb-sum__free">{free}</p>'
        f'<div class="kpb-sum__bar"><span style="width:{progress:.1f}%"></span></div>'
        f'<dl><div><dt>Nëntotali</dt><dd>{catalog.format_eur(totals["subtotal"])}</dd></div>{discount}'
        f'<div><dt>Dërgesa</dt><dd>{shipping}</dd></div>'
        f'<div class="tot"><dt>Totali</dt><dd>{catalog.format_eur(totals["total"])}</dd></div></dl></div>')


def _render_checkout_form() -> None:
    user = st.session_state.get("current_user") or {}
    coupon = st.session_state.get("kpb_coupon", "")
    totals = checkout.calculate_totals(cart.cart_subtotal(), _settings(), coupon)
    _render_summary(totals)
    with st.form("kpb-checkout"):
        name = st.text_input("Emri & mbiemri *", value=user.get("full_name") or "", max_chars=80)
        phone = st.text_input("Telefoni *", max_chars=20, placeholder="+383 44 123 456",
                              help="Korrieri ju telefonon para dorëzimit")
        city = st.text_input("Qyteti *", max_chars=60)
        address = st.text_area("Adresa e saktë *", max_chars=300, height=70)
        notes = st.text_input("Shënime për korrierin", max_chars=300)
        email = st.text_input("Email-i (për konfirmim)", value=user.get("email") or "", max_chars=120)
        coupon_value = st.text_input("Kupon zbritjeje", value=coupon, max_chars=20)
        submitted = st.form_submit_button("Përfundo porosinë", type="primary", use_container_width=True)
    if st.button("←  Kthehu te shporta", key="drawer-back"):
        st.session_state.cart_step = "items"
        st.rerun(scope="fragment")
    if not submitted:
        return
    if coupon_value != coupon:
        st.session_state.kpb_coupon = coupon_value
        totals = checkout.calculate_totals(cart.cart_subtotal(), _settings(), coupon_value)
    items = list(st.session_state.cart.values())
    errors = checkout.validate_delivery(name, phone, city, address, email) + checkout.stock_problems(items)
    for error in errors:
        st.error(error)
    if errors:
        return
    order_id = database.create_order(
        buyer_name=name.strip(), phone=phone.strip(), city=city.strip(), address=address.strip(),
        items=items, total_price=totals["total"], customer_notes=notes, buyer_email=email,
    )
    for item in items:
        if item.get("product_id"):
            database.reduce_stock_after_order(item["product_id"], item["qty"])
    email_service.send_order_notification_email(
        order_id=order_id, buyer_name=name.strip(), phone=phone.strip(), city=city.strip(),
        address=address.strip(), items=items, total_price=totals["total"], to_admin_email=email_service.admin_email(),
    )
    email_sent = False
    if email.strip():
        email_sent, _ = email_service.send_order_confirmation_to_customer(
            email, order_id, name.strip(), items, totals["total"])
    st.session_state.cart = {}
    st.session_state.kpb_coupon = ""
    st.session_state.last_order = {"id": order_id, "name": name.strip(), "phone": phone.strip(),
                                   "total": totals["total"], "email": email.strip(), "email_sent": email_sent}
    st.session_state.cart_step = "done"
    st.rerun(scope="fragment")


def _render_order_done(order: dict) -> None:
    email_line = (f"Konfirmimi u dërgua në <b>{_esc(order['email'])}</b>. " if order.get("email_sent") else "")
    _md(f'<div class="kpb-done"><div class="ic">✓</div><p class="s">Faleminderit!</p>'
        f'<p class="t">Porosia juaj u regjistrua.</p>'
        f'<p class="d">Numri i referencës: <span class="ref">#{order["id"]}</span><br>'
        f'Totali: {catalog.format_eur(order["total"])} · pagesë me para në dorë.<br>'
        f'{email_line}Do t\'ju telefonojmë në <b>{_esc(order["phone"])}</b> për ta konfirmuar dërgesën.</p></div>')
    message = (f"Përshëndetje! Jam {order['name']}. Sapo bëra porosinë #{order['id']} "
               f"me vlerë {catalog.format_eur(order['total'])} te Korea Pure Beauty. Ju lutem ma konfirmoni.")
    link = checkout.whatsapp_link(_settings().get("whatsapp_number", ""), message)
    if link:
        st.link_button("Konfirmo në WhatsApp", link, use_container_width=True)
    if st.button("Mbyll", key="drawer-close", type="primary", use_container_width=True):
        st.session_state.last_order = None
        st.session_state.cart_step = "items"
        st.rerun()


@st.dialog("Ndërtoni ritualin tuaj", width="large")
def ritual_dialog() -> None:
    _md('<p class="kpb-qv__desc" style="margin-top:0">Tri pyetje dhe ne zgjedhim nga dyqani një rutinë me katër hapa.</p>')
    skin = st.radio("1. Lloji i lëkurës", ["E Thatë", "Mikse", "E Yndyrshme", "Sensibile"], horizontal=True)
    goal = st.radio("2. Synimi kryesor", catalog.RITUAL_GOALS, horizontal=True)
    sensitive = st.radio("3. Lëkurë e ndjeshme ndaj aromave?", ["Jo", "Po"], horizontal=True) == "Po"
    routine = catalog.build_ritual(database.get_all_products(), skin, goal, sensitive)
    chosen = [step["product"] for step in routine if step["product"]]
    rows = "".join(
        f'<li><span class="n" style="font-size:2.5rem">{step["step"][:2]}</span><div class="k" style="padding-top:.3rem">'
        f'<small style="color:var(--muted-fg)">{_esc(step["step"][5:])}</small>'
        f'<p style="margin:.3rem 0 0;color:var(--fg)">{_esc(step["product"]["name"]) if step["product"] else "Së shpejti"}</p></div></li>'
        for step in routine
    )
    _md(f'<ol class="kpb-steps" style="border-color:var(--border)">{rows}</ol>')
    if chosen:
        full = sum(p["price"] for p in chosen)
        if st.button(f"Shto ritualin me 10% zbritje · {catalog.format_eur(full * (1 - cart.RITUAL_DISCOUNT))}",
                     key="ritual-add", type="primary", use_container_width=True):
            cart.add_ritual_to_cart(chosen)
            st.session_state.open_cart = True
            st.rerun()


@st.dialog("Privatësia & Kushtet", width="large")
def privacy_dialog() -> None:
    fee, threshold = checkout.shipping_rules(_settings())
    _md(f"""<div class="kpb-legal">
<h4>Të dhënat personale</h4><p>Emrin, telefonin, qytetin dhe adresën i përdorim vetëm për ta realizuar dhe dërguar
porosinë tuaj. Nuk ua shesim palëve të treta; i ndajmë vetëm me korrierin që e dorëzon porosinë. Mund të kërkoni në çdo kohë
t'i shihni, korrigjoni ose fshini, duke na shkruar te Kontakti. Fjalëkalimet ruhen të koduara.</p>
<h4>Dërgesat</h4><p>24–48 orë në Kosovë. Dërgesa kushton {catalog.format_eur(fee)} dhe është falas mbi
{catalog.format_eur(threshold)}. Pagesa bëhet me para në dorë.</p>
<h4>Kthimi dhe ndërrimi</h4><p>Brenda 14 ditëve, për produkte të pahapura në paketimin origjinal. Produktet e hapura
nuk kthehen për arsye higjiene, përveç kur kanë ardhur të dëmtuara ose të gabuara.</p>
<h4>Origjinaliteti</h4><p>Produktet importohen direkt nga Koreja e Jugut dhe shiten në paketimin origjinal të prodhuesit.</p>
</div>""")


# ==========================================
# PIKA HYRËSE
# ==========================================
def render_store(image_uri: ImageUriFunction) -> None:
    global _cart_image_function
    _cart_image_function = image_uri
    st.session_state["_run_cache"] = {}  # cilësimet lexohen një herë për çdo rifreskim
    products = database.get_all_products()

    _render_announcement()
    _render_header()
    _render_hero(len(products))
    _render_shop(products, image_uri)
    _render_ritual()
    _render_contact()

    # Pas "Shto në shportë", shporta hapet vetë (si në dizajnin origjinal)
    if st.session_state.pop("open_cart", False):
        st.session_state.cart_step = "items"
        cart_drawer()
