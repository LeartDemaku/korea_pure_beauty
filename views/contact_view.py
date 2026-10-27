# views/contact_view.py
# Kontakti: formulari (ruhet në databazë), WhatsApp, orari dhe pyetjet e shpeshta (FAQ).
import html
import re

import streamlit as st

import auth
import database
import email_service
import theme
from views import components

MAX_MESSAGE_LENGTH = 2000
PHONE_PATTERN = re.compile(r"^\+?[0-9 ()\-]{6,20}$")


def validate_contact_form(name: str, email: str, phone: str, message: str) -> list[str]:
    """Kthen listën e gabimeve. Listë bosh = formulari është në rregull."""
    errors = []
    if not name.strip():
        errors.append("Shkruani emrin.")
    if not email.strip() and not phone.strip():
        errors.append("Shkruani email-in ose numrin e telefonit, që t'ju përgjigjemi.")
    if email.strip() and not auth.is_valid_email(email.strip()):
        errors.append("Email-i nuk duket i saktë.")
    if phone.strip() and not PHONE_PATTERN.match(phone.strip()):
        errors.append("Numri i telefonit duhet të ketë vetëm shifra, hapësira, +, ( ) ose -.")
    if not message.strip():
        errors.append("Shkruani mesazhin.")
    elif len(message) > MAX_MESSAGE_LENGTH:
        errors.append(f"Mesazhi është shumë i gjatë (maksimumi {MAX_MESSAGE_LENGTH} karaktere).")
    return errors


def faq_items(settings: dict) -> list[tuple[str, str]]:
    fee = settings.get("shipping_fee", "")
    threshold = settings.get("free_shipping_threshold", "")
    shipping_cost = f"Transporti kushton {fee} €" if fee else "Kostoja e transportit llogaritet në arkë"
    free = f", dhe është falas për porosi mbi {threshold} €." if threshold else "."
    return [
        ("Si mund të di nëse produktet janë 100% origjinale?",
         "Të gjitha produktet importohen direkt nga Koreja e Jugut dhe vijnë me paketimin, etiketat "
         "dhe kodet origjinale të prodhuesit. Na shkruani nëse doni informacion për një produkt të caktuar."),
        ("Sa zgjat dërgesa dhe sa kushton?",
         f"Dërgesa zgjat 24–48 orë në Kosovë, Shqipëri dhe Maqedoni të Veriut. {shipping_cost}{free}"),
        ("A mund të paguaj me para në dorë (Cash on Delivery)?",
         "Po. Paguani me para në dorë te korrieri, në momentin që e merrni porosinë."),
        ("A mund ta ndërroj produktin nëse nuk më përshtatet?",
         "Po, brenda 14 ditëve, për produkte të pahapura dhe në paketimin origjinal. "
         "Shihni faqen “Privatësia & Kushtet” për detajet."),
    ]


def render_contact() -> None:
    theme.load_css("pages")
    settings = database.get_all_settings()
    components.section_head("Kontakt", 'Jemi këtu për <span class="kpb-accent">lëkurën tuaj</span>')

    form_column, info_column = st.columns([1.4, 1], gap="large")
    with form_column:
        with st.form("contact_form", clear_on_submit=True):
            name = st.text_input("Emri *", max_chars=80)
            email = st.text_input("Email-i", max_chars=120)
            phone = st.text_input("Numri i telefonit", max_chars=20)
            message = st.text_area("Mesazhi *", max_chars=MAX_MESSAGE_LENGTH, height=150)
            sent = st.form_submit_button("Dërgo mesazhin", type="primary", use_container_width=True)

        if sent:
            errors = validate_contact_form(name, email, phone, message)
            if errors:
                for error in errors:
                    st.error(error)
            else:
                database.create_message(name, message, email=email, phone=phone)
                email_service.send_contact_notification_email(name, email, phone, message)
                st.success("Faleminderit! Mesazhi u dërgua. Do t'ju përgjigjemi sa më shpejt.")

    with info_column:
        whatsapp_digits = "".join(ch for ch in settings.get("whatsapp_number", "") if ch.isdigit())
        blocks = ""
        if whatsapp_digits:
            blocks += (f'<a class="kpb-btn kpb-btn--block" href="https://wa.me/{whatsapp_digits}" '
                       f'target="_blank" rel="noopener">Na shkruani në WhatsApp</a>')
        if settings.get("business_hours"):
            blocks += f'<h4>Orari</h4><p>{html.escape(settings["business_hours"])}</p>'
        if settings.get("contact_email"):
            email_value = html.escape(settings["contact_email"])
            blocks += f'<h4>Email</h4><p><a href="mailto:{email_value}">{email_value}</a></p>'
        blocks += ('<h4>Dërgesa</h4><p>24–48 orë në Kosovë, Shqipëri dhe Maqedoni të Veriut. '
                   'Pagesa bëhet me para në dorë.</p>')
        st.markdown(f'<div class="kpb-info-card">{blocks}</div>', unsafe_allow_html=True)

    components.section_head("Pyetjet e shpeshta", 'Përgjigje të <span class="kpb-accent">shpejta</span>')
    with st.container(key="kpb-faq"):
        for question, answer in faq_items(settings):
            with st.expander(question):
                st.write(answer)

    components.render_footer()
