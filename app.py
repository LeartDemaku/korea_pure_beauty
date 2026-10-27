# app.py
import streamlit as st
import os
import base64
import io
import mimetypes
import database
import auth
import email_service
from views import admin_view

# 1. Konfigurimi Kryesor
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(BASE_DIR, "assets", "logo.png")
BANNER_PATH = os.path.join(BASE_DIR, "assets", "banner.png")
FAVICON_PATH = os.path.join(BASE_DIR, "assets", "favicon_badge.png")

try:
    page_icon_obj = Image.open(FAVICON_PATH) if os.path.exists(FAVICON_PATH) else "🌸"
except Exception:
    page_icon_obj = FAVICON_PATH if os.path.exists(FAVICON_PATH) else "🌸"

st.set_page_config(
    page_title="Korea Pure Beauty | Luxury Skincare",
    page_icon=page_icon_obj,
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data(show_spinner=False)
def get_logo_data_uri() -> str:
    if os.path.exists(LOGO_PATH):
        try:
            with Image.open(LOGO_PATH) as img:
                img = img.copy()
                img.thumbnail((300, 300), Image.Resampling.LANCZOS)
                buf = io.BytesIO()
                img.save(buf, format="WEBP", quality=85)
                b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
                return f"data:image/webp;base64,{b64}"
        except Exception:
            try:
                with open(LOGO_PATH, "rb") as f:
                    return f"data:image/png;base64,{base64.b64encode(f.read()).decode('utf-8')}"
            except Exception:
                pass
    return ""

@st.cache_data(show_spinner=False)
def get_banner_data_uri() -> str:
    if os.path.exists(BANNER_PATH):
        try:
            with Image.open(BANNER_PATH) as img:
                img = img.copy()
                img.thumbnail((700, 250), Image.Resampling.LANCZOS)
                buf = io.BytesIO()
                img.save(buf, format="WEBP", quality=85)
                b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
                return f"data:image/webp;base64,{b64}"
        except Exception:
            try:
                with open(BANNER_PATH, "rb") as f:
                    return f"data:image/png;base64,{base64.b64encode(f.read()).decode('utf-8')}"
            except Exception:
                pass
    return ""

ADMIN_NOTIFICATION_EMAIL = "leart.demaku2006@gmail.com"
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Inicjalizojmë bazën vetëm një herë për sesion
if "db_initialized" not in st.session_state:
    database.init_database()
    st.session_state.db_initialized = True

# Session State
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "cart" not in st.session_state:
    st.session_state.cart = {}
if "selected_product_id" not in st.session_state:
    st.session_state.selected_product_id = None
if "editing_product_id" not in st.session_state:
    st.session_state.editing_product_id = None
if "current_page" not in st.session_state:
    st.session_state.current_page = "shop"
if "animated_item" not in st.session_state:
    st.session_state.animated_item = None



# Tema e çelur gjithmonë (në përputhje me .streamlit/config.toml)
st.markdown("<style>:root { color-scheme: light !important; }</style>", unsafe_allow_html=True)

# ==========================================
# 🔑 AUTO-LOGIN PAS ÇDO REFRESH (F5)
# ==========================================
if not st.session_state.authenticated:
    # Rikthimi i kyçjes pas F5 bëhet vetëm me token sesioni të vlefshëm.
    # (Më parë mjaftonte ?user=emri, që lejonte këdo të hynte si admin pa fjalëkalim.)
    if "user" in st.query_params:
        del st.query_params["user"]  # pastrojmë adresat e vjetra të pasigurta
    session_user = auth.resume_session(st.query_params.get("session"))
    if session_user and session_user.get('role') == 'admin':
        st.session_state.authenticated = True
        st.session_state.current_user = session_user
    elif "session" in st.query_params:
        del st.query_params["session"]

# ==========================================
# 💎 DIZAJNI ADAPTIV (LIGHT & DARK THEME)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    :root {
        color-scheme: light dark;
    }

    @media (prefers-color-scheme: dark) {
        :root {
            color-scheme: dark;
        }
    }

    .stApp, p, h1, h2, h3, h4, h5, h6, label {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }

    header[data-testid="stHeader"] {
        background: transparent !important;
    }

    /* ================================================= */
    /* 1. SIDEBAR (NAVBAR I MAJTË) ADAPTIV               */
    /* ================================================= */
    [data-testid="stSidebar"] {
        background-color: light-dark(#ffffff, #11121c) !important;
        border-right: 1px solid light-dark(#ffd1dc, rgba(255, 117, 140, 0.18)) !important;
        box-shadow: light-dark(2px 0 20px rgba(255, 117, 140, 0.08), none) !important;
        padding-top: 15px;
    }
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p {
        color: light-dark(#1e293b, #e2e8f0) !important;
    }
    [data-testid="stSidebar"] .stCaption,
    [data-testid="stSidebar"] small {
        color: light-dark(#64748b, #8892b0) !important;
        font-weight: 700;
        letter-spacing: 1px;
    }

    /* Sinkronizim me data-theme */
    html[data-theme="light"] [data-testid="stSidebar"],
    body[data-theme="light"] [data-testid="stSidebar"],
    .stApp[data-theme="light"] [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #ffd1dc !important;
        box-shadow: 2px 0 20px rgba(255, 117, 140, 0.08) !important;
    }
    html[data-theme="light"] [data-testid="stSidebar"] p,
    html[data-theme="light"] [data-testid="stSidebar"] span,
    html[data-theme="light"] [data-testid="stSidebar"] label {
        color: #1e293b !important;
    }
    html[data-theme="dark"] [data-testid="stSidebar"],
    body[data-theme="dark"] [data-testid="stSidebar"],
    .stApp[data-theme="dark"] [data-testid="stSidebar"] {
        background-color: #11121c !important;
        border-right: 1px solid rgba(255, 117, 140, 0.18) !important;
        box-shadow: none !important;
    }
    html[data-theme="dark"] [data-testid="stSidebar"] p,
    html[data-theme="dark"] [data-testid="stSidebar"] span,
    html[data-theme="dark"] [data-testid="stSidebar"] label {
        color: #e2e8f0 !important;
    }

    /* ================================================= */
    /* 2. PROFILE CARD                                   */
    /* ================================================= */
    .profile-card {
        background: light-dark(#fff0f3, rgba(255, 255, 255, 0.04)) !important;
        border: 1px solid light-dark(#ffb8c6, rgba(255, 117, 140, 0.25)) !important;
        box-shadow: light-dark(0 4px 15px rgba(255, 117, 140, 0.12), 0 8px 20px rgba(0,0,0,0.35)) !important;
        padding: 16px 12px;
        border-radius: 18px;
        text-align: center;
        margin-bottom: 15px;
        transition: all 0.3s ease;
    }
    html[data-theme="light"] .profile-card {
        background: #fff0f3 !important;
        border: 1px solid #ffb8c6 !important;
        box-shadow: 0 4px 15px rgba(255, 117, 140, 0.12) !important;
    }
    html[data-theme="dark"] .profile-card {
        background: rgba(255, 255, 255, 0.04) !important;
        border: 1px solid rgba(255, 117, 140, 0.25) !important;
        box-shadow: 0 8px 20px rgba(0,0,0,0.35) !important;
    }

    .profile-user-text {
        font-size: 13px;
        color: light-dark(#64748b, #a4b0be) !important;
        margin-top: 6px;
    }
    html[data-theme="light"] .profile-user-text { color: #64748b !important; }
    html[data-theme="dark"] .profile-user-text { color: #a4b0be !important; }

    .profile-user-name {
        color: light-dark(#1e293b, #ffffff) !important;
        font-weight: 700;
    }
    html[data-theme="light"] .profile-user-name { color: #1e293b !important; }
    html[data-theme="dark"] .profile-user-name { color: #ffffff !important; }

    .profile-title {
        font-size: 1.25rem;
        font-weight: 800;
        color: #ff758c !important;
        margin-bottom: 4px;
    }

    .sidebar-logo-img {
        max-width: 200px;
        width: 88%;
        height: auto;
        display: block;
        margin: 2px auto 8px auto;
        transition: transform 0.3s ease, filter 0.3s ease;
    }
    .sidebar-logo-img:hover {
        transform: scale(1.03);
    }
    html[data-theme="dark"] .sidebar-logo-img {
        filter: drop-shadow(0 0 10px rgba(255, 184, 198, 0.32)) brightness(1.08);
    }
    html[data-theme="light"] .sidebar-logo-img {
        filter: drop-shadow(0 2px 8px rgba(255, 117, 140, 0.12));
    }

    .hero-logo-box {
        display: inline-block;
        background: rgba(255, 255, 255, 0.94);
        backdrop-filter: blur(10px);
        padding: 12px 32px;
        border-radius: 20px;
        margin-bottom: 12px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.12);
        border: 1px solid rgba(255, 255, 255, 0.85);
        transition: transform 0.3s ease;
    }
    .hero-logo-box:hover {
        transform: scale(1.02);
    }
    .hero-logo-box img {
        max-width: 280px;
        width: 100%;
        height: auto;
        display: block;
    }

    .kpb-hero-banner {
        max-width: 580px;
        margin: 0 auto 20px auto;
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid light-dark(#ffd1dc, rgba(255, 117, 140, 0.22));
        background: light-dark(linear-gradient(135deg, #ffffff 0%, #fff5f7 100%), rgba(255, 255, 255, 0.03));
        box-shadow: light-dark(0 6px 20px rgba(255, 117, 140, 0.12), 0 8px 24px rgba(0, 0, 0, 0.35));
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .kpb-hero-banner:hover {
        transform: translateY(-2px);
        box-shadow: light-dark(0 10px 28px rgba(255, 117, 140, 0.20), 0 12px 30px rgba(0, 0, 0, 0.40));
    }
    .kpb-hero-banner img {
        width: 100%;
        max-height: 155px;
        height: auto;
        display: block;
        object-fit: contain;
        margin: 0 auto;
    }

    /* ================================================= */
    /* 3. KARTAT E PRODUKTEVE ME MADHËSI 100% TË BARABARTË */
    /* ================================================= */
    div[class*="st-key-kpb_card_"] {
        background-color: light-dark(#ffffff, rgba(26, 27, 38, 0.90)) !important;
        border: 1px solid light-dark(#ffd5dc, rgba(255, 255, 255, 0.08)) !important;
        border-radius: 16px !important;
        box-shadow: light-dark(0 4px 16px rgba(255, 117, 140, 0.1), 0 4px 16px rgba(0,0,0,0.3)) !important;
        transition: all 0.3s ease !important;
        height: 470px !important;
        min-height: 470px !important;
        max-height: 470px !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: space-between !important;
        box-sizing: border-box !important;
        padding: 10px 12px 12px 12px !important;
        overflow: hidden !important;
    }
    html[data-theme="light"] div[class*="st-key-kpb_card_"] {
        background-color: #ffffff !important;
        border: 1px solid #ffd5dc !important;
        box-shadow: 0 6px 20px rgba(255, 117, 140, 0.1) !important;
    }
    html[data-theme="dark"] div[class*="st-key-kpb_card_"] {
        background-color: rgba(26, 27, 38, 0.90) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        box-shadow: 0 6px 18px rgba(0,0,0,0.3) !important;
    }

    div[class*="st-key-kpb_card_"]:hover {
        border-color: light-dark(#ff758c, rgba(255, 117, 140, 0.6)) !important;
        box-shadow: 0 12px 30px rgba(255, 117, 140, 0.25) !important;
        transform: translateY(-4px) !important;
    }

    /* Blloku i përmbajtjes brenda kartës */
    .card-product-wrapper {
        display: flex !important;
        flex-direction: column !important;
        width: 100% !important;
    }

    /* Imazhi i produktit në kartë */
    .card-img-wrap {
        width: 100% !important;
        height: 160px !important;
        min-height: 160px !important;
        max-height: 160px !important;
        margin-bottom: 6px !important;
        border-radius: 12px !important;
        overflow: hidden !important;
        background: #ffffff !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06) !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    .card-img-tag {
        height: 100% !important;
        max-height: 160px !important;
        width: 100% !important;
        object-fit: contain !important;
        background: #ffffff !important;
        border-radius: 12px !important;
        padding: 4px !important;
        transition: transform 0.35s ease !important;
        image-rendering: -webkit-optimize-contrast !important;
    }
    div[class*="st-key-kpb_card_"]:hover .card-img-tag,
    div:has(.card-product-wrapper):hover .card-img-tag {
        transform: scale(1.05) !important;
    }

    /* Brendi */
    .brand-box {
        color: #ff758c !important;
        font-size: 0.72rem !important;
        font-weight: 800 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.8px !important;
        height: 16px !important;
        min-height: 16px !important;
        max-height: 16px !important;
        line-height: 16px !important;
        margin-top: 1px !important;
        margin-bottom: 2px !important;
        overflow: hidden !important;
        white-space: nowrap !important;
        text-overflow: ellipsis !important;
    }

    /* Titulli i produktit */
    .title-container {
        height: 38px !important;
        min-height: 38px !important;
        max-height: 38px !important;
        margin-bottom: 2px !important;
        overflow: hidden !important;
        display: flex !important;
        align-items: flex-start !important;
    }
    .title-box {
        font-size: 0.88rem !important;
        font-weight: 700 !important;
        color: light-dark(#0f172a, #ffffff) !important;
        line-height: 1.3 !important;
        overflow: hidden !important;
        display: -webkit-box !important;
        -webkit-line-clamp: 2 !important;
        -webkit-box-orient: vertical !important;
        width: 100% !important;
    }
    html[data-theme="light"] .title-box { color: #0f172a !important; }
    html[data-theme="dark"] .title-box { color: #ffffff !important; }

    /* Përshkrimi i produktit */
    .desc-container {
        height: 30px !important;
        min-height: 30px !important;
        max-height: 30px !important;
        margin-bottom: 4px !important;
        overflow: hidden !important;
        display: flex !important;
        align-items: flex-start !important;
    }
    .desc-box {
        font-size: 0.75rem !important;
        color: light-dark(#475569, #c8d6e5) !important;
        line-height: 1.3 !important;
        overflow: hidden !important;
        display: -webkit-box !important;
        -webkit-line-clamp: 2 !important;
        -webkit-box-orient: vertical !important;
        width: 100% !important;
    }
    html[data-theme="light"] .desc-box { color: #475569 !important; }
    html[data-theme="dark"] .desc-box { color: #c8d6e5 !important; }

    /* Bexhet (Badges) */
    .badges-box {
        height: 24px !important;
        min-height: 24px !important;
        max-height: 24px !important;
        overflow: hidden !important;
        display: flex !important;
        flex-wrap: nowrap !important;
        gap: 3px !important;
        align-items: center !important;
        margin-bottom: 4px !important;
    }

    .badge-tag {
        display: inline-flex !important;
        align-items: center !important;
        padding: 2px 6px !important;
        border-radius: 4px !important;
        font-size: 0.63rem !important;
        font-weight: 800 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.3px !important;
        margin: 0 !important;
        white-space: nowrap !important;
    }
    .badge-kr { background-color: #10ac84 !important; color: #ffffff !important; }
    .badge-eu { background-color: #2e86de !important; color: #ffffff !important; }
    .badge-skin { background-color: #ee5253 !important; color: #ffffff !important; }

    /* Çmimi */
    .price-box {
        font-size: 1.20rem !important;
        font-weight: 800 !important;
        color: #ff758c !important;
        height: 26px !important;
        min-height: 26px !important;
        max-height: 26px !important;
        line-height: 26px !important;
        display: flex !important;
        align-items: center !important;
        margin-bottom: 4px !important;
    }

    .detail-title-text {
        color: light-dark(#0f172a, #ffffff) !important;
    }
    html[data-theme="light"] .detail-title-text { color: #0f172a !important; }
    html[data-theme="dark"] .detail-title-text { color: #ffffff !important; }

    /* ================================================= */
    /* 4. BUTONAT                                        */
    /* ================================================= */
    button[kind="secondary"] {
        background: light-dark(#ffffff, rgba(255, 255, 255, 0.05)) !important;
        border: 1px solid light-dark(#ffd1dc, rgba(255, 255, 255, 0.16)) !important;
        border-radius: 12px !important;
        color: light-dark(#1e293b, #e2e8f0) !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    html[data-theme="light"] button[kind="secondary"] {
        background: #ffffff !important;
        border: 1px solid #ffd1dc !important;
        color: #1e293b !important;
    }
    html[data-theme="dark"] button[kind="secondary"] {
        background: rgba(255, 255, 255, 0.05) !important;
        border: 1px solid rgba(255, 255, 255, 0.16) !important;
        color: #e2e8f0 !important;
    }

    button[kind="secondary"]:hover {
        background: light-dark(#fff0f3, rgba(255, 117, 140, 0.15)) !important;
        border-color: #ff758c !important;
        color: #ff758c !important;
    }

    button[kind="primary"] {
        background: linear-gradient(135deg, #ff758c 0%, #ff7eb3 100%) !important;
        border: none !important;
        color: white !important;
        font-weight: 700 !important;
        border-radius: 12px !important;
        padding: 10px 16px !important;
        box-shadow: 0 4px 14px rgba(255, 117, 140, 0.4) !important;
        transition: all 0.2s ease !important;
    }
    button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 22px rgba(255, 117, 140, 0.6) !important;
    }

    /* ================================================= */
    /* 5. EXPANDERS & METRIKA                            */
    /* ================================================= */
    div[data-testid="stExpander"] {
        background-color: light-dark(#ffffff, rgba(26, 27, 38, 0.75)) !important;
        border: 1px solid light-dark(#ffd5dc, rgba(255, 255, 255, 0.09)) !important;
        border-radius: 14px !important;
        margin-bottom: 12px !important;
    }
    html[data-theme="light"] div[data-testid="stExpander"] {
        background-color: #ffffff !important;
        border: 1px solid #ffd5dc !important;
    }
    html[data-theme="dark"] div[data-testid="stExpander"] {
        background-color: rgba(26, 27, 38, 0.75) !important;
        border: 1px solid rgba(255, 255, 255, 0.09) !important;
    }

    div[data-testid="stExpander"] summary {
        color: light-dark(#0f172a, #ffffff) !important;
        font-weight: 700 !important;
    }
    html[data-theme="light"] div[data-testid="stExpander"] summary { color: #0f172a !important; }
    html[data-theme="dark"] div[data-testid="stExpander"] summary { color: #ffffff !important; }

    div[data-testid="stExpander"] details {
        border-radius: 14px !important;
    }

    div[data-testid="stMetric"] {
        background: light-dark(#ffffff, rgba(26, 27, 38, 0.75)) !important;
        border: 1px solid light-dark(#ffd5dc, rgba(255, 255, 255, 0.09)) !important;
        border-radius: 14px !important;
        padding: 14px 18px !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.04) !important;
    }
    html[data-theme="light"] div[data-testid="stMetric"] {
        background: #ffffff !important;
        border: 1px solid #ffd5dc !important;
    }
    html[data-theme="dark"] div[data-testid="stMetric"] {
        background: rgba(26, 27, 38, 0.75) !important;
        border: 1px solid rgba(255, 255, 255, 0.09) !important;
    }

    div[data-testid="stMetric"] label {
        color: light-dark(#64748b, #a4b0be) !important;
        font-weight: 600 !important;
    }
    html[data-theme="light"] div[data-testid="stMetric"] label { color: #64748b !important; }
    html[data-theme="dark"] div[data-testid="stMetric"] label { color: #a4b0be !important; }

    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #ff758c !important;
        font-weight: 800 !important;
    }

    /* ================================================= */
    /* 6. HEROBANNER & MEDIA                             */
    /* ================================================= */
    .hero-banner {
        background: linear-gradient(135deg, #ff758c 0%, #ff7eb3 40%, #7928ca 100%);
        padding: 26px 20px;
        border-radius: 20px;
        color: white !important;
        text-align: center;
        margin-bottom: 22px;
        box-shadow: 0 12px 30px rgba(255, 117, 140, 0.3);
    }
    .hero-banner * {
        color: white !important;
    }
    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        margin-bottom: 4px;
    }

    /* ================================================= */
    /* 📱 7. MOBILE RESPONSIVE ENGINE (MAX-WIDTH: 768px) */
    /* ================================================= */
    @media (max-width: 768px) {
        /* 1. Global Viewport & Container Spacing */
        .stApp {
            overflow-x: hidden !important;
        }
        .main .block-container {
            padding-top: 1.2rem !important;
            padding-bottom: 2.5rem !important;
            padding-left: 0.65rem !important;
            padding-right: 0.65rem !important;
            max-width: 100% !important;
        }

        /* 2. Prevent iOS Safari auto-zoom on input focus */
        input, select, textarea, [data-baseweb="input"] input {
            font-size: 16px !important;
        }

        /* 3. Touch-friendly Minimum Heights (44px) */
        button, 
        .stButton > button,
        button[kind="primary"],
        button[kind="secondary"],
        div[data-baseweb="select"] > div {
            min-height: 44px !important;
            font-size: 0.92rem !important;
        }

        /* 4. Streamlit Column Stacking on Mobile */
        div[data-testid="stHorizontalBlock"] {
            flex-direction: column !important;
            gap: 0.75rem !important;
        }
        div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
            width: 100% !important;
            min-width: 100% !important;
            max-width: 100% !important;
            flex: 1 1 100% !important;
        }

        /* Exception: keep 2-button action rows side by side on product cards */
        div[class*="st-key-kpb_card_"] div[data-testid="stHorizontalBlock"] {
            flex-direction: row !important;
            gap: 0.5rem !important;
        }
        div[class*="st-key-kpb_card_"] div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
            width: 50% !important;
            min-width: 50% !important;
            max-width: 50% !important;
            flex: 1 1 50% !important;
        }

        /* Exception: keep cart item image, text, and delete button horizontal */
        div[data-testid="stVerticalBlockBorderWrapper"]:has(button[key^="del_cart_"]) div[data-testid="stHorizontalBlock"] {
            flex-direction: row !important;
            align-items: center !important;
            gap: 0.5rem !important;
        }
        div[data-testid="stVerticalBlockBorderWrapper"]:has(button[key^="del_cart_"]) div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(1) {
            width: 22% !important;
            min-width: 65px !important;
            max-width: 80px !important;
            flex: 0 0 auto !important;
        }
        div[data-testid="stVerticalBlockBorderWrapper"]:has(button[key^="del_cart_"]) div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(2) {
            width: 52% !important;
            flex: 1 1 auto !important;
        }
        div[data-testid="stVerticalBlockBorderWrapper"]:has(button[key^="del_cart_"]) div[data-testid="stHorizontalBlock"] > div[data-testid="column"]:nth-child(3) {
            width: 26% !important;
            flex: 0 0 auto !important;
            text-align: right !important;
        }

        /* Exception: Admin Order Action Buttons 2x2 grid on mobile */
        div[data-testid="stHorizontalBlock"]:has(button[key^="btn_confirm_"]) {
            flex-direction: row !important;
            flex-wrap: wrap !important;
            gap: 8px !important;
        }
        div[data-testid="stHorizontalBlock"]:has(button[key^="btn_confirm_"]) > div[data-testid="column"] {
            width: calc(50% - 4px) !important;
            min-width: calc(50% - 4px) !important;
            max-width: calc(50% - 4px) !important;
            flex: 1 1 calc(50% - 4px) !important;
            margin-bottom: 4px !important;
        }

        /* Exception: Admin Product Form Save/Cancel 50/50 buttons */
        div[data-testid="stHorizontalBlock"]:has(button:has-text("Ruaj")) {
            flex-direction: row !important;
            gap: 8px !important;
        }
        div[data-testid="stHorizontalBlock"]:has(button:has-text("Ruaj")) > div[data-testid="column"] {
            width: 50% !important;
            min-width: 50% !important;
            max-width: 50% !important;
            flex: 1 1 50% !important;
        }

        /* 5. Mobile Product Cards */
        div[class*="st-key-kpb_card_"] {
            height: auto !important;
            min-height: 420px !important;
            max-height: none !important;
            padding: 12px 14px 14px 14px !important;
            margin-bottom: 12px !important;
            border-radius: 16px !important;
        }
        .card-img-wrap {
            height: 175px !important;
            min-height: 175px !important;
            max-height: 175px !important;
        }
        .card-img-tag {
            max-height: 175px !important;
        }
        .title-container {
            height: auto !important;
            min-height: 38px !important;
            max-height: 48px !important;
        }
        .title-box {
            font-size: 0.95rem !important;
            line-height: 1.35 !important;
        }
        .desc-container {
            height: auto !important;
            min-height: 28px !important;
            max-height: 40px !important;
        }
        .desc-box {
            font-size: 0.80rem !important;
        }
        .badges-box {
            flex-wrap: wrap !important;
            height: auto !important;
            min-height: 26px !important;
            gap: 4px !important;
        }
        .price-box {
            font-size: 1.35rem !important;
            height: 30px !important;
            margin: 6px 0 !important;
        }

        /* 6. Top Header Bar & Branding */
        .top-header-brand-wrap {
            flex-direction: column !important;
            align-items: flex-start !important;
            gap: 6px !important;
            margin-bottom: 8px !important;
        }
        .kpb-hero-banner {
            max-width: 100% !important;
            border-radius: 12px !important;
            margin: 0 0 14px 0 !important;
        }
        .kpb-hero-banner img {
            max-height: 120px !important;
            object-fit: cover !important;
        }

        /* 7. Metric Cards Grid */
        div[data-testid="stMetric"] {
            padding: 10px 14px !important;
            margin-bottom: 8px !important;
        }
        div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
            font-size: 1.4rem !important;
        }

        /* 8. Tabs on Mobile */
        button[data-baseweb="tab"] {
            padding: 8px 12px !important;
            font-size: 0.88rem !important;
        }

        /* 9. Popovers & Dialogs */
        div[data-baseweb="popover"] {
            max-width: 96vw !important;
        }

        /* 10. Login / Register page centered column expands to 100% on mobile */
        div[data-testid="stHorizontalBlock"]:has([key="l_user"]) > div[data-testid="column"]:nth-child(1),
        div[data-testid="stHorizontalBlock"]:has([key="l_user"]) > div[data-testid="column"]:nth-child(3) {
            display: none !important;
        }
        div[data-testid="stHorizontalBlock"]:has([key="l_user"]) > div[data-testid="column"]:nth-child(2) {
            width: 100% !important;
            min-width: 100% !important;
            max-width: 100% !important;
        }
    }

    @media (max-width: 480px) {
        /* Extra small devices (iPhone SE, small Androids) */
        .main .block-container {
            padding-left: 0.4rem !important;
            padding-right: 0.4rem !important;
        }
        .card-img-wrap {
            height: 160px !important;
            min-height: 160px !important;
            max-height: 160px !important;
        }
        .card-img-tag {
            max-height: 160px !important;
        }
        div[class*="st-key-kpb_card_"] {
            padding: 10px 10px 12px 10px !important;
            min-height: 400px !important;
        }
        .hero-title {
            font-size: 1.6rem !important;
        }
    }
</style>
""", unsafe_allow_html=True)



# ==========================================
# 🚪 AUTENTIKIMI
# ==========================================
def render_auth_page():
    logo_uri = get_logo_data_uri()
    with st.sidebar:
        logo_sidebar = f'<img src="{logo_uri}" alt="Korea Pure Beauty" class="sidebar-logo-img" />' if logo_uri else '<div class="profile-title">🌸 Korea Pure Beauty</div>'
        st.markdown(f"""
        <div class="profile-card">
            {logo_sidebar}
            <div class="profile-user-text" style="font-weight: 700; color: #ff758c !important; letter-spacing: 0.5px;">Sistemi i Menaxhimit</div>
        </div>
        """, unsafe_allow_html=True)

    banner_uri = get_banner_data_uri()
    if banner_uri:
        st.markdown(
            f'<div class="kpb-hero-banner">'
            f'<img src="{banner_uri}" alt="Korea Pure Beauty" />'
            f'</div>',
            unsafe_allow_html=True
        )
    elif os.path.exists(BANNER_PATH):
        st.image(BANNER_PATH, use_container_width=True)
    else:
        st.markdown("""
        <div class="hero-banner">
            <div class="hero-title">🌸 Korea Pure Beauty</div>
            <div style="font-size: 1.05rem; opacity: 0.98; font-weight: 500;">Produktet 100% Origjinale nga Korea e Jugut | Standarde të BE-së (CPNP)</div>
        </div>
        """, unsafe_allow_html=True)


    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        tab_login, tab_register, tab_reset = st.tabs(["🔑 Kyçu (Login)", "✨ Krijo Llogari", "🔄 Ndërro Fjalëkalimin"])

        with tab_login:
            st.subheader("Hyrje në Dyqan")
            u = st.text_input("Emri i përdoruesit ose Email", key="l_user", placeholder="username ose email")
            p = st.text_input("Fjalëkalimi", type="password", key="l_pass")
            if st.button("Hyr Tani", use_container_width=True, type="primary"):
                if u and p:
                    success, res = auth.login_user(u, p)
                    if success and res.get('role') != 'admin':
                        # Paneli i adminit pranon vetëm administratorë
                        st.error("⛔ Ky panel është vetëm për administratorët. Klientët kyçen te dyqani.")
                    elif success:
                        st.session_state.authenticated = True
                        st.session_state.current_user = res
                        st.session_state.current_page = "shop"
                        st.query_params["session"] = auth.start_session(res)
                        st.success("Mirësevini!")
                        st.rerun()
                    else:
                        st.error(res)
                else:
                    st.warning("Plotësoni fushat.")

        with tab_register:
            st.subheader("Llogaritë e Administratorit")
            # Regjistrimi publik i administratorëve u çaktivizua për siguri:
            # kushdo që hapte këtë faqe mund të bëhej admin.
            st.info(
                "🔒 Për siguri, llogaritë e reja të administratorit krijohen vetëm nga "
                "kompjuteri i dyqanit, me komandën:\n\n`python create_admin.py`"
            )

        with tab_reset:
            st.subheader("🔄 Ndërro Fjalëkalimin")
            a_reset_mode = st.radio(
                "Mënyra e ndërrimit:",
                ["✉️ Me Kod në Email (Kam harruar fjalëkalimin)", "🔑 Me Fjalëkalimin Aktual"],
                key="admin_reset_mode",
                horizontal=True
            )

            if "Me Kod në Email" in a_reset_mode:
                if "a_reset_sent" not in st.session_state:
                    st.session_state.a_reset_sent = False
                if "a_reset_target" not in st.session_state:
                    st.session_state.a_reset_target = ""

                if not st.session_state.a_reset_sent:
                    a_ident = st.text_input("Email ose Username", key="a_reset_ident_inp", placeholder="p.sh. koreapurebeauty_admin")
                    if st.button("📩 Dërgo Kodin e Sigurisë", key="a_btn_send_reset", use_container_width=True, type="primary"):
                        if a_ident:
                            ok, msg, target_email, code = auth.request_password_reset_code(a_ident)
                            if ok:
                                st.session_state.a_reset_sent = True
                                st.session_state.a_reset_target = a_ident
                                st.session_state.a_reset_code_test = code
                                st.success(f"Kodi u dërgua te: {target_email}!")
                                st.rerun()
                            else:
                                st.error(msg)
                        else:
                            st.warning("Shkruani email-in ose username-in.")
                else:
                    a_target = st.session_state.a_reset_target
                    st.info(f"Kodi i sigurisë iu dërgua llogarisë: **{a_target}**")
                    a_test_c = st.session_state.get("a_reset_code_test")
                    if not email_service.is_smtp_configured() and a_test_c:
                        st.caption(f"💡 *Kodi lokal i testimit:* `{a_test_c}`")

                    a_code = st.text_input("Kodi 6-shifror nga Email-i", max_chars=6, key="a_reset_code_inp", placeholder="p.sh. 123456")
                    a_new_p = st.text_input("Fjalëkalimi i Ri", type="password", key="a_reset_new_p", placeholder="Të paktën 6 karaktere")
                    a_conf_p = st.text_input("Konfirmo Fjalëkalimin e Ri", type="password", key="a_reset_conf_p", placeholder="Rishkruani fjalëkalimin")

                    ab1, ab2 = st.columns([1.5, 1])
                    with ab1:
                        if st.button("💾 Ruaj Fjalëkalimin", key="a_btn_save_reset", use_container_width=True, type="primary"):
                            r_ok, r_msg = auth.confirm_password_reset_code(a_target, a_code, a_new_p, a_conf_p)
                            if r_ok:
                                st.session_state.a_reset_sent = False
                                st.session_state.a_reset_target = ""
                                st.success("🎉 Fjalëkalimi u ndryshua me sukses! Mund të kyçeni te 'Kyçu'.")
                                st.rerun()
                            else:
                                st.error(r_msg)
                    with ab2:
                        if st.button("⬅️ Kthehu", key="a_btn_back_reset", use_container_width=True, type="secondary"):
                            st.session_state.a_reset_sent = False
                            st.session_state.a_reset_target = ""
                            st.rerun()

            else:
                a_curr_id = st.text_input("Email ose Username", key="a_chg_ident_inp", placeholder="p.sh. koreapurebeauty_admin")
                a_curr_old = st.text_input("Fjalëkalimi Aktual", type="password", key="a_chg_old_p")
                a_curr_new = st.text_input("Fjalëkalimi i Ri", type="password", key="a_chg_new_p", placeholder="Të paktën 6 karaktere")
                a_curr_conf = st.text_input("Konfirmo Fjalëkalimin e Ri", type="password", key="a_chg_conf_p", placeholder="Rishkruani fjalëkalimin")

                if st.button("💾 Përditëso Fjalëkalimin", key="a_btn_update_direct", use_container_width=True, type="primary"):
                    chg_ok, chg_msg = auth.change_password_with_current(a_curr_id, a_curr_old, a_curr_new, a_curr_conf)
                    if chg_ok:
                        st.success("🎉 " + chg_msg)
                    else:
                        st.error(chg_msg)


# ==========================================
# 🔍 INTERACTIVE HD ZOOM VIEWER & IMAGE OPTIMIZATION
# ==========================================
@st.cache_data(show_spinner=False)
def get_image_data_uri(image_path: str, max_dim: int = 400, quality: int = 82) -> str:
    if not image_path:
        return "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=800&q=90"
    if image_path.startswith("http://") or image_path.startswith("https://"):
        return image_path
    image_path = image_path.replace("\\", "/")
    if os.path.exists(image_path):
        try:
            with Image.open(image_path) as img:
                img = img.copy()
                if img.width > max_dim or img.height > max_dim:
                    img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
                buf = io.BytesIO()
                img.save(buf, format="WEBP", quality=quality)
                b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
                return f"data:image/webp;base64,{b64}"
        except Exception:
            try:
                mime, _ = mimetypes.guess_type(image_path)
                if not mime:
                    mime = "image/png" if image_path.lower().endswith(".png") else "image/jpeg"
                with open(image_path, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode("utf-8")
                return f"data:{mime};base64,{b64}"
            except Exception:
                return "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=800&q=90"
    return "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=800&q=90"


# ==========================================
# 🚀 NISJA
# ==========================================
if not st.session_state.authenticated:
    render_auth_page()
else:
    admin_view.render_admin(st.session_state.current_user, get_image_data_uri)