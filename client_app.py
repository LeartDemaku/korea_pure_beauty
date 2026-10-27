# client_app.py
# Dyqani për klientët (porta 8502 / Streamlit Cloud).
# I gjithë dizajni ndodhet te views/storefront.py dhe styles/store.css.
import base64
import io
import os

import streamlit as st
from PIL import Image

import auth
import database
import theme
from views import storefront

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FAVICON_PATH = os.path.join(BASE_DIR, "assets", "favicon_badge.png")
PLACEHOLDER_IMAGE = ("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 10 10'>"
                     "<rect width='10' height='10' fill='%23F6E8E1'/></svg>")

st.set_page_config(
    page_title="Korea Pure Beauty — Kujdes premium koreane për lëkurën",
    page_icon=Image.open(FAVICON_PATH) if os.path.exists(FAVICON_PATH) else "🌸",
    layout="wide",
    initial_sidebar_state="collapsed",
)


@st.cache_data(show_spinner=False)
def get_image_data_uri(image_path: str, max_dim: int = 600, quality: int = 85) -> str:
    """Fotot e produkteve si WebP i lehtë brenda faqes. Pa foto -> sfond i butë."""
    if not image_path:
        return PLACEHOLDER_IMAGE
    if image_path.startswith(("http://", "https://")):
        return image_path
    full_path = os.path.join(BASE_DIR, image_path.replace("\\", "/"))
    try:
        with Image.open(full_path) as image:
            image = image.convert("RGBA" if image.mode in ("RGBA", "LA", "P") else "RGB")
            image.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
            buffer = io.BytesIO()
            image.save(buffer, format="WEBP", quality=quality)
        return "data:image/webp;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")
    except (OSError, ValueError):
        # Foto që mungon ose është e dëmtuar: shfaqim sfondin, jo gabim
        return PLACEHOLDER_IMAGE


def init_session() -> None:
    if "db_initialized" not in st.session_state:
        database.init_database()
        st.session_state.db_initialized = True
    defaults = {"authenticated": False, "current_user": None, "cart": {}, "cart_step": "items",
                "last_order": None, "pending_verification_email": None}
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)

    # Rikthimi i kyçjes pas F5 vetëm me token sesioni të vlefshëm
    if not st.session_state.authenticated:
        if "user" in st.query_params:
            del st.query_params["user"]  # adresat e vjetra të pasigurta
        user = auth.resume_session(st.query_params.get("session"))
        if user:
            st.session_state.authenticated = True
            st.session_state.current_user = user
        elif "session" in st.query_params:
            del st.query_params["session"]


init_session()
theme.load_css("store")
storefront.render_store(get_image_data_uri)
