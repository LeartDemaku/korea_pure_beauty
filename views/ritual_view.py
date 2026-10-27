# views/ritual_view.py
# Kuisi interaktiv me 3 pyetje që ndërton një rutinë me 4 hapa nga produktet e dyqanit.
import html

import streamlit as st

import cart
import catalog
import database
import theme
from views import components
from views.components import ImageUriFunction

SKIN_CHOICES = ["E Thatë", "Mikse", "E Yndyrshme", "Sensibile"]


def render_ritual(image_uri: ImageUriFunction) -> None:
    theme.load_css("shop", "pages")
    components.section_head("Rituali", 'Ndërtoni ritualin tuaj në <span class="kpb-accent">3 pyetje</span>')
    st.markdown(
        '<p class="kpb-lead">Përgjigjuni tri pyetjeve dhe ne zgjedhim nga dyqani një rutinë me katër hapa, '
        'të përshtatur për lëkurën tuaj.</p>',
        unsafe_allow_html=True,
    )

    with st.form("ritual_quiz"):
        with st.container(key="kpb-quiz"):
            skin_type = st.radio("1. Cili është lloji i lëkurës suaj?", SKIN_CHOICES, horizontal=True)
            goal = st.radio("2. Cili është synimi juaj kryesor?", catalog.RITUAL_GOALS, horizontal=True)
            fragrance_sensitive = st.radio(
                "3. A keni lëkurë të ndjeshme ndaj aromave?", ["Jo", "Po"], horizontal=True
            ) == "Po"
        submitted = st.form_submit_button("Krijo ritualin tim", type="primary", use_container_width=True)

    if submitted:
        st.session_state.ritual_answers = (skin_type, goal, fragrance_sensitive)

    answers = st.session_state.get("ritual_answers")
    if answers:
        _render_result(image_uri, *answers)

    components.render_footer()


def _render_result(image_uri: ImageUriFunction, skin_type: str, goal: str, sensitive: bool) -> None:
    routine = catalog.build_ritual(database.get_all_products(), skin_type, goal, sensitive)
    chosen = [step["product"] for step in routine if step["product"]]

    components.section_head(
        "Rezultati",
        f'Rituali juaj për lëkurë <span class="kpb-accent">{html.escape(skin_type.lower())}</span>',
    )
    if sensitive:
        st.caption("Për lëkurë të ndjeshme kemi dhënë përparësi produkteve për lëkurë sensibile. "
                   "Kontrolloni gjithmonë listën e përbërësve dhe provoni produktin në një zonë të vogël.")

    for column, step in zip(st.columns(4, gap="medium"), routine):
        with column:
            st.markdown(f'<span class="kpb-overline">{step["step"]}</span>', unsafe_allow_html=True)
            if step["product"]:
                components.product_card(step["product"], image_uri, "ritual")
            else:
                st.markdown(
                    '<div class="kpb-empty kpb-empty--small"><p>Së shpejti</p>'
                    '<span>Ky hap do të plotësohet me produktet e reja.</span></div>',
                    unsafe_allow_html=True,
                )

    if chosen:
        full_price = sum(p["price"] for p in chosen)
        ritual_price = full_price * (1 - cart.RITUAL_DISCOUNT)
        st.markdown(
            f'<p class="kpb-ritual-total">Rituali i plotë: <span class="kpb-price--old">{full_price:.2f} €</span> '
            f'<span class="kpb-price">{ritual_price:.2f} €</span></p>',
            unsafe_allow_html=True,
        )
        if st.button(f"Shto të gjithë ritualin në shportë me 10% zbritje ({len(chosen)} produkte)",
                     key="ritual_add_all", type="primary", use_container_width=True):
            cart.add_ritual_to_cart(chosen)
            st.rerun()
