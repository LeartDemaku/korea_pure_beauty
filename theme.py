# theme.py
# "Theme Engine": lexon skedarët CSS nga dosja styles/ dhe i fut në faqen e Streamlit.
# Përdorimi në çdo view:   import theme;  theme.load_css("main", "hero")
import base64
import mimetypes
import os

import streamlit as st

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STYLES_DIR = os.path.join(BASE_DIR, "styles")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

# E njëjta paletë si në styles/main.css, për vendet ku na duhet ngjyra në Python
# (p.sh. grafikët e Admin-it në Fazën 5).
PALETTE = {
    "nude": "#FAF6F2",
    "terracotta": "#AF6A4E",
    "espresso": "#261B15",
    "gold": "#D8B494",
    "sand": "#EADED5",
    "white": "#FFFFFF",
    "emerald": "#2ECC71",
    "amber": "#F39C12",
}


@st.cache_data(show_spinner=False)
def _read_css(path: str, modified_time: float) -> str:
    # modified_time është pjesë e çelësit të cache-it: kur e ruan skedarin CSS,
    # koha ndryshon dhe Streamlit e lexon sërish (pa e rinisur aplikacionin).
    with open(path, encoding="utf-8") as css_file:
        return css_file.read()


def load_css(*names: str) -> None:
    """Fut një ose më shumë skedarë CSS (pa prapashtesën .css) në faqe."""
    css_parts = []
    for name in names:
        path = os.path.join(STYLES_DIR, f"{name}.css")
        if not os.path.exists(path):
            # Gabim i qartë në vend që stilet të mungojnë në heshtje
            raise FileNotFoundError(f"Skedari i stileve nuk u gjet: {path}")
        css_parts.append(_read_css(path, os.path.getmtime(path)))
    st.markdown(f"<style>{''.join(css_parts)}</style>", unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def _read_asset_as_data_uri(path: str, modified_time: float) -> str:
    # Disa versione të Windows nuk e njohin .webp, ndaj e shtojmë vetë
    mime_type = "image/webp" if path.lower().endswith(".webp") else mimetypes.guess_type(path)[0]
    mime_type = mime_type or "application/octet-stream"
    with open(path, "rb") as asset_file:
        encoded = base64.b64encode(asset_file.read()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def asset_data_uri(filename: str) -> str:
    """Kthen një imazh nga dosja assets/ si data URI, që të futet direkt në HTML.
    Kthen tekst bosh nëse skedari mungon, që faqja të mos rrëzohet."""
    path = os.path.join(ASSETS_DIR, filename)
    if not os.path.exists(path):
        return ""
    return _read_asset_as_data_uri(path, os.path.getmtime(path))
