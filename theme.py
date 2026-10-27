# theme.py
# "Theme Engine": lexon skedarët CSS nga dosja styles/ dhe i fut në faqen e Streamlit.
# Përdorimi në çdo view:   import theme;  theme.load_css("main", "hero")
import os

import streamlit as st

STYLES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "styles")

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
