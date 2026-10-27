# client_app.py
# Dyqani për klientët (porta 8502 / Streamlit Cloud).
# Faqja vizuale është një uebfaqe e plotë (components/storefront: HTML + CSS + JS) që shfaqet
# në gjithë ekranin. Python-i jep të dhënat dhe kryen veprimet (store_api.py).
import base64
import io
import os
import traceback

import streamlit as st
import streamlit.components.v1 as components
from PIL import Image

import auth
import database
import store_api

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FAVICON_PATH = os.path.join(BASE_DIR, "assets", "favicon_badge.png")
PLACEHOLDER_IMAGE = ("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 10 10'>"
                     "<rect width='10' height='10' fill='%23F6E8E1'/></svg>")
MAX_STORED_RESULTS = 30

st.set_page_config(
    page_title="Korea Pure Beauty — Kujdes premium koreane për lëkurën",
    page_icon=Image.open(FAVICON_PATH) if os.path.exists(FAVICON_PATH) else "🌸",
    layout="wide",
    initial_sidebar_state="collapsed",
)

storefront = components.declare_component(
    "kpb_store", path=os.path.join(BASE_DIR, "components", "storefront")
)

# Uebfaqja zë gjithë dritaren; elementet e Streamlit fshihen
st.markdown("""
<style>
  header[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"],
  [data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"], [data-testid="stStatusWidget"],
  #MainMenu, footer { display: none !important; }
  html, body, .stApp { background: #FAF6F3 !important; overflow: hidden !important; }
  [data-testid="stMainBlockContainer"], .block-container { padding: 0 !important; max-width: 100% !important; }
  iframe[title*="kpb_store"], [data-testid="stCustomComponentV1"] {
    position: fixed !important; inset: 0 !important; width: 100vw !important; height: 100vh !important;
    height: 100dvh !important; border: 0 !important; z-index: 999990; background: #FAF6F3;
  }
</style>
""", unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def get_image_data_uri(image_path: str, max_dim: int = 700, quality: int = 84) -> str:
    """Fotot e produkteve si WebP i lehtë. Foto që mungon -> sfond i butë (pa gabim)."""
    if not image_path:
        return PLACEHOLDER_IMAGE
    if image_path.startswith("https://"):
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
        return PLACEHOLDER_IMAGE


def init_session() -> None:
    if "db_initialized" not in st.session_state:
        database.init_database()
        st.session_state.db_initialized = True
    for key, value in {"authenticated": False, "current_user": None, "session_token": None,
                       "store_results": {}, "handled_events": []}.items():
        st.session_state.setdefault(key, value)

    # Rikthimi i kyçjes pas F5 vetëm me token sesioni të vlefshëm
    if not st.session_state.authenticated:
        if "user" in st.query_params:
            del st.query_params["user"]  # adresat e vjetra të pasigurta
        token = st.query_params.get("session")
        user = auth.resume_session(token)
        if user:
            st.session_state.authenticated = True
            st.session_state.current_user = user
            st.session_state.session_token = token
        elif "session" in st.query_params:
            del st.query_params["session"]


def sync_session_query_param() -> None:
    """Token-i i sesionit mbahet në adresë, që kyçja të mbijetojë F5."""
    token = st.session_state.session_token if st.session_state.authenticated else None
    if token and st.query_params.get("session") != token:
        st.query_params["session"] = token
    if not token and "session" in st.query_params:
        del st.query_params["session"]


init_session()
data = store_api.build_store_data(
    get_image_data_uri,
    st.session_state.current_user if st.session_state.authenticated else None,
    st.session_state.store_results,
)
event = storefront(data=data, key="kpb_store", default=None)

# Çdo veprim kryhet vetëm një herë (Streamlit e kthen vlerën e fundit në çdo rifreskim)
if isinstance(event, dict) and event.get("id") and event["id"] not in st.session_state.handled_events:
    st.session_state.handled_events = (st.session_state.handled_events + [event["id"]])[-100:]
    try:
        result = store_api.handle_event(event, st.session_state)
    except Exception:  # gabim i papritur: shkruhet në terminal, klienti merr mesazh të qartë
        traceback.print_exc()
        result = {"ok": False, "message": "Ndodhi një gabim në server. Provoni përsëri pas pak."}
    results = dict(st.session_state.store_results)
    results[event["id"]] = result
    st.session_state.store_results = dict(list(results.items())[-MAX_STORED_RESULTS:])
    sync_session_query_param()
    st.rerun()
