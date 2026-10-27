# views/shop_view.py
# Dyqani: kërkim i menjëhershëm, filtra sipas kategorisë dhe llojit të lëkurës, renditje,
# kartat e produkteve dhe dritarja Quick-View.
from typing import Callable

import streamlit as st

import catalog
import database
import theme
from views import components
from views.components import ImageUriFunction

COLUMNS = 3


def render_shop(image_uri: ImageUriFunction, inject_live_search: Callable[[], None]) -> None:
    theme.load_css("shop", "pages")

    components.section_head("Dyqani", 'Koleksioni i <span class="kpb-accent">plotë</span>')

    with st.container(key="kpb-shop-filters"):
        search_column, category_column, skin_column, sort_column = st.columns([1.6, 1, 1, 1])
        with search_column:
            # Kërkimi filtron kartat menjëherë në browser, pa rifreskim (shih inject_live_search_script)
            st.text_input(
                "Kërko",
                key="kpb_live_search_input",
                placeholder="Kërko me emër ose markë, p.sh. Anua, COSRX…",
            )
        with category_column:
            category = st.selectbox("Kategoria", [catalog.ALL_LABEL, *catalog.CATEGORY_GROUPS, catalog.OTHER_CATEGORY],
                                    key="shop_category")
        with skin_column:
            skin_type = st.selectbox("Lloji i lëkurës", [catalog.ALL_LABEL, *catalog.SKIN_TYPES], key="shop_skin")
        with sort_column:
            sort_by = st.selectbox("Rendit sipas", catalog.SORT_OPTIONS, key="shop_sort")

    products = catalog.sort_products(
        catalog.filter_products(database.get_all_products(), category, skin_type), sort_by
    )

    st.markdown(
        f'<p id="kpb-product-count" class="kpb-muted">Po shfaqen <strong>{len(products)}</strong> produkte</p>'
        '<div id="no-live-products-msg" class="kpb-empty" style="display:none;">'
        '<p id="no-live-products-text">Nuk u gjet asnjë produkt për këtë kërkim.</p>'
        '<span>Provoni një emër tjetër ose pastroni kërkimin.</span></div>',
        unsafe_allow_html=True,
    )

    if not products:
        st.markdown(
            '<div class="kpb-empty"><p>Nuk ka produkte për këta filtra.</p>'
            '<span>Zgjidhni “Të gjitha” për të parë gjithë koleksionin.</span></div>',
            unsafe_allow_html=True,
        )
    else:
        # Rreshta me nga 3 karta: kartat e fshehura nga kërkimi nuk lënë vrima të mëdha
        for row_start in range(0, len(products), COLUMNS):
            row = products[row_start:row_start + COLUMNS]
            for column, product in zip(st.columns(COLUMNS, gap="medium"), row):
                with column:
                    components.product_card(product, image_uri, "shop")

    inject_live_search()
    components.render_footer()
