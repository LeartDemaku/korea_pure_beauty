# app.py
import streamlit as st
import streamlit.components.v1 as components
import os
import uuid
import json
import sqlite3
import base64
import io
import mimetypes
import html
import pandas as pd
import database
import auth
import email_service
import urllib.parse

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

@st.cache_data(show_spinner=False)
def get_favicon_data_uri() -> str:
    if os.path.exists(FAVICON_PATH):
        try:
            with open(FAVICON_PATH, "rb") as f:
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



# ==========================================
# 🔑 AUTO-LOGIN PAS ÇDO REFRESH (F5)
# ==========================================
if not st.session_state.authenticated:
    if "user" in st.query_params:
        saved_username = st.query_params["user"]
        user_data = database.get_user_by_identifier(saved_username)
        if user_data and user_data.get('role') == 'admin':
            st.session_state.authenticated = True
            st.session_state.current_user = user_data
        else:
            st.query_params.clear()

# ==========================================
# 🛠️ FUNKSIONET E BAZËS SË TË DHËNAVE
# ==========================================
def fetch_product_by_id(pid):
    conn = sqlite3.connect('korea_beauty.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products WHERE id = ?', (pid,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def save_updated_product(pid, name, brand, category, skin_type, price, description, eu_cert, is_orig, img_path):
    conn = sqlite3.connect('korea_beauty.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE products 
        SET name = ?, brand = ?, category = ?, skin_type = ?, price = ?, 
            description = ?, eu_certified = ?, is_original = ?, image_url = ?
        WHERE id = ?
    ''', (name, brand, category, skin_type, price, description, 1 if eu_cert else 0, 1 if is_orig else 0, img_path, pid))
    conn.commit()
    conn.close()

# ==========================================
# 🎆 ANIMACIONI I SHPORTËS
# ==========================================
def trigger_visual_cart_animation(product_name, product_price):
    animation_html = f"""
    <div id="anim-wrapper" style="
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        pointer-events: none;
        z-index: 9999999;
    ">
        <div style="
            position: fixed;
            bottom: 35px;
            right: 35px;
            background: linear-gradient(135deg, #ff758c 0%, #7928ca 100%);
            color: white;
            padding: 16px 24px;
            border-radius: 16px;
            box-shadow: 0 15px 40px rgba(255, 117, 140, 0.7);
            font-family: 'Plus Jakarta Sans', sans-serif;
            font-size: 15px;
            font-weight: bold;
            display: flex;
            align-items: center;
            gap: 12px;
            animation: slideUpToast 3.5s forwards cubic-bezier(0.175, 0.885, 0.32, 1.275);
            border: 2px solid rgba(255, 255, 255, 0.5);
        ">
            <span style="font-size: 28px;">🌸</span>
            <div>
                <div style="font-size: 16px;">U shtua me sukses në shportë!</div>
                <div style="font-size: 13px; opacity: 0.95; font-weight: normal;">{product_name} • €{product_price:.2f}</div>
            </div>
        </div>

        <div id="flying-orb" style="
            position: fixed;
            top: 50%;
            left: 50%;
            width: 55px;
            height: 55px;
            background: radial-gradient(circle, #ffffff 10%, #ff758c 60%, #7928ca 100%);
            border-radius: 50%;
            box-shadow: 0 0 35px #ff758c, 0 0 70px #ff7eb3;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 26px;
            animation: flyToCartCurve 1.15s cubic-bezier(0.25, 1, 0.5, 1) forwards;
        ">
            🛍️
        </div>
    </div>

    <style>
        @keyframes slideUpToast {{
            0% {{ transform: translateY(100px) scale(0.8); opacity: 0; }}
            15% {{ transform: translateY(0) scale(1); opacity: 1; }}
            85% {{ transform: translateY(0) scale(1); opacity: 1; }}
            100% {{ transform: translateY(100px) scale(0.8); opacity: 0; }}
        }}

        @keyframes flyToCartCurve {{
            0% {{ top: 50%; left: 55%; transform: scale(1.6) rotate(0deg); opacity: 1; }}
            40% {{ top: 20%; left: 35%; transform: scale(1.9) rotate(180deg); box-shadow: 0 0 50px #ff758c; }}
            100% {{ top: 190px; left: 80px; transform: scale(0.2) rotate(360deg); opacity: 0; }}
        }}
    </style>

    <script>
        function createPetal() {{
            const petal = document.createElement('div');
            petal.innerHTML = ['🌸', '✨', '💖', '⭐', '🌺'][Math.floor(Math.random() * 5)];
            petal.style.position = 'fixed';
            petal.style.left = (Math.random() * 80 + 10) + 'vw';
            petal.style.top = (Math.random() * 50 + 20) + 'vh';
            petal.style.fontSize = (Math.random() * 22 + 16) + 'px';
            petal.style.opacity = '1';
            petal.style.pointerEvents = 'none';
            petal.style.transition = 'all 1.3s ease-out';
            petal.style.zIndex = '9999998';
            document.body.appendChild(petal);

            setTimeout(() => {{
                petal.style.transform = `translate(${{(Math.random()-0.5)*250}}px, ${{(Math.random()-0.5)*250}}px) scale(0)`;
                petal.style.opacity = '0';
            }}, 50);

            setTimeout(() => {{ petal.remove(); }}, 1400);
        }}

        for(let i=0; i<18; i++) {{
            setTimeout(createPetal, i * 35);
        }}
    </script>
    """
    components.html(animation_html, height=0, width=0)



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
</style>
""", unsafe_allow_html=True)



# ==========================================
# 🌿 PRODUKTE SHEMBULL
# ==========================================
def seed_sample_products():
    samples = [
        {
            "name": "Relief Sun: Rice + Probiotics (SPF50+ PA++++)",
            "brand": "Beauty of Joseon",
            "category": "Sunscreen (SPF)",
            "skin_type": "Të gjitha tipet",
            "price": 17.50,
            "description": "Krem dielli organik me 30% ekstrakt orizi dhe probiotikë që ushqejnë dhe mbrojnë lëkurën pa lënë shenja të bardha.",
            "image_url": "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=500&q=80"
        },
        {
            "name": "Advanced Snail 96 Mucin Power Essence",
            "brand": "COSRX",
            "category": "Serum / Essence",
            "skin_type": "E Thata",
            "price": 21.00,
            "description": "Me 96.3% Snail Secretion Filtrate për hidratim të thellë, riparim të indeve të dëmtuara dhe shkëlqim natyral.",
            "image_url": "https://images.unsplash.com/photo-1620916566398-39f1143ab7be?w=500&q=80"
        },
        {
            "name": "Heartleaf 77% Soothing Toner",
            "brand": "Anua",
            "category": "Toner",
            "skin_type": "Sensitive",
            "price": 19.90,
            "description": "Toneri më viral me 77% ekstrakt Heartleaf për qetësimin e skuqjes, inflamacionit dhe akneve.",
            "image_url": "https://images.unsplash.com/photo-1608248597359-2169b61d47a4?w=500&q=80"
        },
        {
            "name": "Madagascar Centella Ampoule",
            "brand": "Skin1004",
            "category": "Serum / Essence",
            "skin_type": "Me Akne / Poret",
            "price": 18.00,
            "description": "100% ekstrakt i pastër i Centella Asiatica nga Madagaskari për qetësim të lëkurës së irrituar.",
            "image_url": "https://images.unsplash.com/photo-1617897903246-719242758050?w=500&q=80"
        }
    ]
    for s in samples:
        database.create_product(
            name=s["name"],
            brand=s["brand"],
            category=s["category"],
            skin_type=s["skin_type"],
            price=s["price"],
            description=s["description"],
            eu_certified=True,
            is_original=True,
            image_url=s["image_url"]
        )


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
                    if success:
                        st.session_state.authenticated = True
                        st.session_state.current_user = res
                        st.session_state.current_page = "shop"
                        st.query_params["user"] = res['username']
                        st.success("Mirësevini!")
                        st.rerun()
                    else:
                        st.error(res)
                else:
                    st.warning("Plotësoni fushat.")

        with tab_register:
            st.subheader("Krijo Llogari Administratori")
            nu = st.text_input("Username i ri *", key="r_user", placeholder="p.sh. emri_admin")
            np = st.text_input("Fjalëkalimi i ri *", type="password", key="r_pass", placeholder="Të paktën 4 karaktere")
            np_conf = st.text_input("Konfirmo Fjalëkalimin *", type="password", key="r_pass_conf", placeholder="Rishkruani fjalëkalimin")

            if st.button("👑 Regjistrohu si Administrator", use_container_width=True, type="primary"):
                if nu and np:
                    if np != np_conf:
                        st.error("Fjalëkalimet nuk përputhen!")
                    else:
                        success, msg = auth.register_user(nu, np, role='admin')
                        if success:
                            st.success("🎉 " + msg + " 👉 Shkoni te 'Kyçu' për të hyrë si Administrator.")
                        else:
                            st.error(msg)
                else:
                    st.warning("Plotësoni të gjitha fushat.")

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


def render_interactive_zoom_viewer(image_path: str, product_name: str, height: int = 560):
    img_data_uri = get_image_data_uri(image_path, max_dim=900, quality=85)
    clean_name = html.escape(product_name or "Produkt")

    html_code = f"""
    <!DOCTYPE html>
    <html lang="sq">
    <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap');
        * {{ box-sizing: border-box; margin: 0; padding: 0; user-select: none; }}
        body {{
            background: transparent;
            font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
            overflow: hidden;
            display: flex;
            justify-content: center;
            align-items: flex-start;
            padding: 4px;
        }}
        .zoom-card {{
            width: 100%;
            background: #ffffff;
            border-radius: 18px;
            border: 1px solid rgba(255, 117, 140, 0.28);
            box-shadow: 0 8px 30px rgba(255, 117, 140, 0.12), 0 2px 10px rgba(0,0,0,0.04);
            overflow: hidden;
            display: flex;
            flex-direction: column;
            position: relative;
        }}
        .zoom-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px 16px;
            background: #fff5f7;
            border-bottom: 1px solid #ffd5dc;
        }}
        .zoom-title {{
            font-size: 13px;
            font-weight: 700;
            color: #d63031;
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .zoom-badge {{
            font-size: 12px;
            font-weight: 800;
            color: #ffffff;
            background: #ff758c;
            padding: 3px 10px;
            border-radius: 12px;
            letter-spacing: 0.5px;
        }}
        .zoom-viewport {{
            width: 100%;
            height: 410px;
            background: radial-gradient(circle at center, #ffffff 40%, #fcf8f9 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            position: relative;
            cursor: grab;
        }}
        .zoom-viewport.grabbing {{
            cursor: grabbing;
        }}
        .zoom-img {{
            max-width: 94%;
            max-height: 94%;
            width: auto;
            height: auto;
            object-fit: contain;
            transform-origin: center center;
            transition: transform 0.08s ease-out;
            pointer-events: none;
            image-rendering: -webkit-optimize-contrast;
            filter: drop-shadow(0 4px 12px rgba(0,0,0,0.06));
        }}
        .zoom-controls {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px 14px;
            background: #ffffff;
            border-top: 1px solid #ffe4e8;
            gap: 8px;
        }}
        .z-btn {{
            background: #ffffff;
            border: 1px solid #cbd5e1;
            border-radius: 9px;
            color: #334155;
            font-size: 15px;
            font-weight: 700;
            width: 36px;
            height: 36px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .z-btn:hover {{
            background: #ff758c;
            color: #ffffff;
            border-color: #ff758c;
            transform: scale(1.05);
        }}
        .z-reset-btn {{
            width: auto;
            padding: 0 10px;
            font-size: 12px;
            gap: 4px;
        }}
        .z-slider-box {{
            flex: 1;
            display: flex;
            align-items: center;
            padding: 0 6px;
        }}
        input[type="range"] {{
            width: 100%;
            height: 6px;
            accent-color: #ff758c;
            cursor: pointer;
            border-radius: 4px;
        }}
        .zoom-footer {{
            padding: 7px 12px;
            background: #f8fafc;
            border-top: 1px solid #f1f5f9;
            font-size: 11px;
            color: #64748b;
            text-align: center;
            line-height: 1.4;
        }}
    </style>
    </head>
    <body>
    <div class="zoom-card" id="zoomCard">
        <div class="zoom-header">
            <div class="zoom-title">
                <span>🔍</span>
                <span>Zmadhim HD: <strong>{clean_name}</strong></span>
            </div>
            <div class="zoom-badge" id="zoomBadge">100%</div>
        </div>

        <div class="zoom-viewport" id="zoomViewport" title="Rrotulloni mausin për zoom, tërhiqni për lëvizje">
            <img class="zoom-img" id="zoomImg" src="{img_data_uri}" alt="{clean_name}" />
        </div>

        <div class="zoom-controls">
            <button class="z-btn" id="btnMinus" title="Zvogëlo (Zoom Out)">➖</button>
            <div class="z-slider-box">
                <input type="range" id="zoomRange" min="1" max="3.5" step="0.05" value="1" title="Shkalla e zmadhimit" />
            </div>
            <button class="z-btn" id="btnPlus" title="Zmadho (Zoom In)">➕</button>
            <button class="z-btn z-reset-btn" id="btnReset" title="Rivendos madhësinë normale">↺ 100%</button>
            <button class="z-btn" id="btnFullscreen" title="Ekran i Plotë">⛶</button>
        </div>

        <div class="zoom-footer">
            💡 <em>Përdorni rrotën e mausit për Zoom In/Out. Kur është i zmadhuar, klikoni & tërhiqni foton.</em>
        </div>
    </div>

    <script>
        let scale = 1;
        let posX = 0;
        let posY = 0;
        let isDragging = false;
        let startX = 0;
        let startY = 0;

        const img = document.getElementById('zoomImg');
        const viewport = document.getElementById('zoomViewport');
        const badge = document.getElementById('zoomBadge');
        const slider = document.getElementById('zoomRange');
        const btnPlus = document.getElementById('btnPlus');
        const btnMinus = document.getElementById('btnMinus');
        const btnReset = document.getElementById('btnReset');
        const btnFs = document.getElementById('btnFullscreen');
        const card = document.getElementById('zoomCard');

        function updateTransform() {{
            img.style.transform = `translate(${{posX}}px, ${{posY}}px) scale(${{scale}})`;
            badge.textContent = Math.round(scale * 100) + '%';
            slider.value = scale;
            if (scale > 1) {{
                viewport.style.cursor = isDragging ? 'grabbing' : 'grab';
            }} else {{
                viewport.style.cursor = 'default';
            }}
        }}

        function setScale(newScale, targetX, targetY) {{
            const prevScale = scale;
            scale = Math.min(Math.max(newScale, 1), 3.5);
            if (scale === 1) {{
                posX = 0;
                posY = 0;
            }} else if (prevScale !== scale && targetX !== undefined && targetY !== undefined) {{
                const ratio = scale / prevScale;
                posX = targetX - (targetX - posX) * ratio;
                posY = targetY - (targetY - posY) * ratio;
            }}
            updateTransform();
        }}

        btnPlus.addEventListener('click', () => {{
            setScale(scale + 0.35);
        }});

        btnMinus.addEventListener('click', () => {{
            setScale(scale - 0.35);
        }});

        btnReset.addEventListener('click', () => {{
            scale = 1;
            posX = 0;
            posY = 0;
            updateTransform();
        }});

        slider.addEventListener('input', (e) => {{
            setScale(parseFloat(e.target.value));
        }});

        // Mouse Wheel Zoom
        viewport.addEventListener('wheel', (e) => {{
            e.preventDefault();
            const rect = viewport.getBoundingClientRect();
            const targetX = e.clientX - rect.left - rect.width / 2;
            const targetY = e.clientY - rect.top - rect.height / 2;
            const delta = e.deltaY < 0 ? 0.25 : -0.25;
            setScale(scale + delta, targetX, targetY);
        }}, {{ passive: false }});

        // Mouse Drag & Pan
        viewport.addEventListener('mousedown', (e) => {{
            if (scale > 1) {{
                isDragging = true;
                startX = e.clientX - posX;
                startY = e.clientY - posY;
                viewport.classList.add('grabbing');
            }}
        }});

        window.addEventListener('mousemove', (e) => {{
            if (isDragging) {{
                posX = e.clientX - startX;
                posY = e.clientY - startY;
                updateTransform();
            }}
        }});

        window.addEventListener('mouseup', () => {{
            if (isDragging) {{
                isDragging = false;
                viewport.classList.remove('grabbing');
            }}
        }});

        // Double click quick zoom
        viewport.addEventListener('dblclick', (e) => {{
            if (scale > 1.2) {{
                scale = 1;
                posX = 0;
                posY = 0;
                updateTransform();
            }} else {{
                const rect = viewport.getBoundingClientRect();
                const targetX = e.clientX - rect.left - rect.width / 2;
                const targetY = e.clientY - rect.top - rect.height / 2;
                setScale(2.2, targetX, targetY);
            }}
        }});

        // Fullscreen
        btnFs.addEventListener('click', () => {{
            if (!document.fullscreenElement) {{
                if (card.requestFullscreen) card.requestFullscreen();
            }} else {{
                if (document.exitFullscreen) document.exitFullscreen();
            }}
        }});
    </script>
    </body>
    </html>
    """
    components.html(html_code, height=height)


# ==========================================
# 🔍 FAQJA E DETAJUAR E PRODUKTIT
# ==========================================
def render_product_detail_page(product_id):
    p = fetch_product_by_id(product_id)
    if not p:
        st.error("Produkti nuk u gjet.")
        if st.button("⬅️ Kthehu te Dyqani"):
            st.session_state.selected_product_id = None
            st.rerun()
        return

    if st.button("⬅️ Kthehu te të Gjitha Produktet", type="secondary"):
        st.session_state.selected_product_id = None
        st.rerun()

    st.write("")
    col_img, col_info = st.columns([1.15, 1.35])

    with col_img:
        render_interactive_zoom_viewer(p.get('image_url'), p.get('name'), height=550)

    with col_info:
        st.markdown(f"<div class='brand-box' style='font-size: 1rem;'>{p['brand']}</div>", unsafe_allow_html=True)
        st.markdown(f"<h1 class='detail-title-text' style='margin: 4px 0 12px 0;'>{p['name']}</h1>", unsafe_allow_html=True)

        badge_str = ""
        if p['is_original']:
            badge_str += "<span class='badge-tag badge-kr'>🇰🇷 100% Origjinal nga Korea</span>"
        if p['eu_certified']:
            badge_str += "<span class='badge-tag badge-eu'>🇪🇺 Standard i BE-së (CPNP)</span>"
        badge_str += f"<span class='badge-tag badge-skin'>🧴 Lëkura: {p['skin_type']}</span>"
        st.markdown(badge_str, unsafe_allow_html=True)

        st.markdown(f"<div style='font-size: 2.2rem; font-weight: 800; color: #ff758c; margin: 12px 0;'>€{p['price']:.2f}</div>", unsafe_allow_html=True)

        st.markdown("### 📖 Përshkrimi dhe Përfitimet")
        desc_text = p['description'] if p['description'] else "Produkt i certifikuar me cilësi të lartë për kujdesin e lëkurës."
        escaped_desc = html.escape(desc_text)
        st.markdown(f"<div class='product-full-desc-container'>{escaped_desc}</div>", unsafe_allow_html=True)

        st.write("")
        st.markdown("### ✨ Detaje Shtesë")
        st.write(f"• **Kategoria:** `{p['category']}`")
        st.write(f"• **Përshtatshmëria:** `{p['skin_type']}`")

        st.write("")
        col_qty, col_add = st.columns([1, 2])
        with col_qty:
            qty_selected = st.number_input("Sasia", min_value=1, max_value=10, value=1)
        with col_add:
            st.write("")
            st.write("")
            if st.button("🛒 Shto në Shportë", use_container_width=True, type="primary"):
                pid = str(p['id'])
                if pid in st.session_state.cart:
                    st.session_state.cart[pid]['qty'] += qty_selected
                else:
                    st.session_state.cart[pid] = {
                        "name": p['name'],
                        "brand": p['brand'],
                        "price": p['price'],
                        "image": p['image_url'],
                        "qty": qty_selected
                    }
                st.session_state.animated_item = {
                    "name": p['name'],
                    "price": p['price']
                }
                st.rerun()


# ==========================================
# 🌸 APLIKACIONI KRYESOR
# ==========================================
def render_main_app():
    user = st.session_state.current_user
    is_admin = (user['role'] == 'admin')

    total_cart_items = sum(item['qty'] for item in st.session_state.cart.values())
    cart_badge = f" ({total_cart_items})" if total_cart_items > 0 else ""

    # EKZEKUTIMI I ANIMACIONIT
    if st.session_state.animated_item is not None:
        item_to_animate = st.session_state.animated_item
        trigger_visual_cart_animation(item_to_animate['name'], item_to_animate['price'])
        st.session_state.animated_item = None

    # SIDEBAR
    with st.sidebar:
        logo_uri = get_logo_data_uri()
        logo_sidebar = f'<img src="{logo_uri}" alt="Korea Pure Beauty" class="sidebar-logo-img" />' if logo_uri else '<div class="profile-title">🌸 Korea Pure Beauty</div>'
        st.markdown(f"""
        <div class="profile-card">
            {logo_sidebar}
            <div style="margin: 6px 0 8px 0;">
                <span style="background: {'#ff4757' if is_admin else '#2ed573'}; color: white; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;">
                    {'👑 ADMINISTRATOR' if is_admin else '🛍️ KLIENT'}
                </span>
            </div>
            <div class="profile-user-text">
                Përdoruesi: <strong class="profile-user-name">{user['username']}</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.caption("MENYJA KRYESORE")

        if is_admin:
            nav_buttons = [
                ("shop", "🛍️ Dyqani / Katalogu"),
                ("cart", f"🛒 Shporta{cart_badge}"),
                ("add", "➕ Shto Produkt (Drag & Drop)"),
                ("orders", "📦 Porositë e Ardhura"),
                ("inventory", "📊 Paneli i Inventarit")
            ]
        else:
            nav_buttons = [
                ("shop", "🛍️ Dyqani / Katalogu"),
                ("cart", f"🛒 Shporta{cart_badge}")
            ]

        for key_name, label in nav_buttons:
            is_active = (st.session_state.current_page == key_name)
            btn_type = "primary" if is_active else "secondary"
            if st.button(label, key=f"btn_nav_{key_name}", use_container_width=True, type=btn_type):
                st.session_state.current_page = key_name
                st.session_state.selected_product_id = None
                st.session_state.editing_product_id = None
                st.rerun()

        st.write("")
        with st.popover("🔑 Ndërro Fjalëkalimin", use_container_width=True):
            st.markdown("#### Ndrysho Fjalëkalimin")
            p_old = st.text_input("Fjalëkalimi Aktual", type="password", key="side_admin_old_p")
            p_new = st.text_input("Fjalëkalimi i Ri", type="password", key="side_admin_new_p", placeholder="Të paktën 6 karaktere")
            p_conf = st.text_input("Konfirmo Fjalëkalimin e Ri", type="password", key="side_admin_conf_p")
            if st.button("Ruaj Fjalëkalimin", key="side_btn_save_admin_p", use_container_width=True, type="primary"):
                ok, msg = auth.change_password_with_current(user['username'], p_old, p_new, p_conf)
                if ok:
                    st.success("🎉 " + msg)
                else:
                    st.error(msg)

        if st.button("🚪 Dil nga Llogaria", use_container_width=True, type="secondary"):
            st.session_state.authenticated = False
            st.session_state.current_user = None
            st.session_state.selected_product_id = None
            st.session_state.editing_product_id = None
            st.session_state.current_page = "shop"
            st.query_params.clear()
            st.rerun()

    current_page = st.session_state.current_page

    # Nëse jemi te faqja e detajuar e produktit
    if current_page == "shop" and st.session_state.selected_product_id is not None:
        render_product_detail_page(st.session_state.selected_product_id)
        return

    # ----------------------------------------------------
    # 1. DYQANI & KATALOGU
    # ----------------------------------------------------
    if current_page == "shop":
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

        all_p = database.get_all_products()
        if not all_p:
            st.info("💡 Dyqani nuk ka ende produkte.")
            if is_admin:
                if st.button("✨ Ngarko Produktet Shembull (Sample Data)", type="primary"):
                    seed_sample_products()
                    st.success("✅ Produktet u shtuan!")
                    st.rerun()
            st.stop()

        # Filtrat
        c_search, c_skin, c_cat = st.columns([2, 1, 1])
        with c_search:
            search_query = st.text_input("🔍 Kërko me emër ose markë...")
        with c_skin:
            skin_filter = st.selectbox("Lloji i Lëkurës", ["Të gjitha", "Të gjitha tipet", "E Thata", "E Yndyrshme", "Mikse (Kombinuar)", "Sensitive", "Me Akne / Poret"])
        with c_cat:
            cat_filter = st.selectbox("Kategoria", ["Të gjitha", "Cleanser (Pastrues)", "Toner", "Serum / Essence", "Moisturizer (Krem)", "Sunscreen (SPF)", "Maskë"])

        if search_query:
            products = database.search_products(search_query)
        elif skin_filter != "Të gjitha":
            products = database.get_products_by_skin_type(skin_filter)
        elif cat_filter != "Të gjitha":
            products = database.get_products_by_category(cat_filter)
        else:
            products = all_p

        st.caption(f"Po shfaqen **{len(products)}** produkte")

        cols = st.columns(3)
        for idx, p in enumerate(products):
            with cols[idx % 3]:
                with st.container(border=True, height=470, key=f"kpb_card_{p['id']}"):
                    card_img_uri = get_image_data_uri(p['image_url'], max_dim=360, quality=80)
                    clean_name = html.escape(p['name'])
                    clean_brand = html.escape(p['brand'])

                    badge_str = ""
                    if p['is_original']:
                        badge_str += "<span class='badge-tag badge-kr'>🇰🇷 100% Origjinal</span>"
                    if p['eu_certified']:
                        badge_str += "<span class='badge-tag badge-eu'>🇪🇺 BE Standard</span>"
                    badge_str += f"<span class='badge-tag badge-skin'>🧴 {p['skin_type']}</span>"

                    desc_text = p['description'] if p['description'] else "Produkt origjinal i testuar me cilësi të lartë për kujdesin ndaj lëkurës."
                    card_desc = html.escape(" ".join(desc_text.split()))

                    card_info_html = f"""
                    <div class='card-product-wrapper'>
                        <div class='card-img-wrap'>
                            <img src='{card_img_uri}' alt='{clean_name}' class='card-img-tag' />
                        </div>
                        <div class='brand-box'>{clean_brand}</div>
                        <div class='title-container'><div class='title-box'>{clean_name}</div></div>
                        <div class='desc-container'><div class='desc-box'>{card_desc}</div></div>
                        <div class='badges-box'>{badge_str}</div>
                        <div class='price-box'>€{p['price']:.2f}</div>
                    </div>
                    """
                    st.markdown(card_info_html, unsafe_allow_html=True)

                    col_b1, col_b2 = st.columns(2)
                    with col_b1:
                        if st.button("👁️ Shiko", key=f"view_{p['id']}", use_container_width=True):
                            st.session_state.selected_product_id = p['id']
                            st.rerun()
                    with col_b2:
                        if st.button("🛒 Shto", key=f"btn_cart_{p['id']}", use_container_width=True, type="primary"):
                            pid = str(p['id'])
                            if pid in st.session_state.cart:
                                st.session_state.cart[pid]['qty'] += 1
                            else:
                                st.session_state.cart[pid] = {
                                    "name": p['name'],
                                    "brand": p['brand'],
                                    "price": p['price'],
                                    "image": p['image_url'],
                                    "qty": 1
                                }
                            st.session_state.animated_item = {
                                "name": p['name'],
                                "price": p['price']
                            }
                            st.rerun()

    # ----------------------------------------------------
    # 2. SHPORTA DHE CHECKOUT
    # ----------------------------------------------------
    elif current_page == "cart":
        st.markdown("<h1 style='color: #ff758c;'>🛒 Shporta e Blerjeve</h1>", unsafe_allow_html=True)

        if not st.session_state.cart:
            st.info("Shporta juaj është bosh. Zgjidhni produkte nga Dyqani!")
        else:
            c_left, c_right = st.columns([1.7, 1.3])

            with c_left:
                st.subheader("Artikujt e zgjedhur")
                tot = 0.0
                cart_items_list = []

                for pid, item in list(st.session_state.cart.items()):
                    cart_items_list.append(item)
                    with st.container(border=True):
                        col_img, col_txt, col_act = st.columns([1, 3, 1])
                        with col_img:
                            if item['image'] and os.path.exists(item['image']):
                                st.image(item['image'], width=75)
                            elif item['image'] and item['image'].startswith("http"):
                                st.image(item['image'], width=75)
                            else:
                                st.image("https://images.unsplash.com/photo-1556228720-195a672e8a03?w=500&q=80", width=75)
                        with col_txt:
                            st.write(f"**{item['name']}**")
                            st.caption(f"{item['brand']} • €{item['price']:.2f}")
                            st.write(f"Sasia: **{item['qty']}** copë")
                        with col_act:
                            sub = item['price'] * item['qty']
                            tot += sub
                            st.write(f"**€{sub:.2f}**")
                            if st.button("Fshij 🗑️", key=f"del_cart_{pid}"):
                                del st.session_state.cart[pid]
                                st.rerun()

            with c_right:
                with st.container(border=True):
                    st.subheader("Përmbledhja e Porosisë")
                    st.write(f"Nëntotali: **€{tot:.2f}**")
                    shipping = 0.0 if tot >= 40 else 2.50
                    st.write(f"Transporti: **{'Falas (Mbi €40)' if shipping == 0 else '€2.50'}**")

                    coupon = st.text_input("Kupon Zbritjeje (KOREA10)")
                    discount = 0.0
                    if coupon.strip().upper() == "KOREA10":
                        discount = tot * 0.10
                        st.success("🎉 Zbritja 10% u llogarit!")

                    final = tot + shipping - discount
                    st.markdown(f"## Totali: <span style='color: #ff758c;'>€{final:.2f}</span>", unsafe_allow_html=True)
                    st.divider()

                    st.write("#### 🚚 Të dhënat e Dërgesës")
                    b_name = st.text_input("Emri dhe Mbiemri *")
                    b_phone = st.text_input("Numri i Telefonit *")
                    b_city = st.text_input("Qyteti *", placeholder="Shkruani qytetin tuaj (p.sh. Prishtinë, Tiranë, Ferizaj, etj.)")
                    b_addr = st.text_area("Adresa e plotë e dërgesës *")

                    if st.button("🚀 Përfundo Porosinë Tani", type="primary", use_container_width=True):
                        if not b_name.strip() or not b_phone.strip() or not b_city.strip() or not b_addr.strip():
                            st.error("Plotësoni të gjitha fushat e dërgesës (përfshirë qytetin).")
                        else:
                            order_id = database.create_order(
                                buyer_name=b_name.strip(),
                                phone=b_phone.strip(),
                                city=b_city.strip(),
                                address=b_addr.strip(),
                                items=cart_items_list,
                                total_price=final
                            )
                            # Dërgojmë njoftimin në Email
                            try:
                                email_service.send_order_notification_email(
                                    order_id=order_id,
                                    buyer_name=b_name.strip(),
                                    phone=b_phone.strip(),
                                    city=b_city.strip(),
                                    address=b_addr.strip(),
                                    items=cart_items_list,
                                    total_price=final,
                                    to_admin_email=ADMIN_NOTIFICATION_EMAIL
                                )
                            except Exception:
                                pass

                            st.balloons()
                            st.success(f"🎉 Faleminderit {b_name}! Porosia juaj #{order_id} prej €{final:.2f} u regjistrua me sukses dhe njoftimi u dërgua te administratori në `{ADMIN_NOTIFICATION_EMAIL}`!")
                            st.session_state.cart = {}

    # ----------------------------------------------------
    # 3. SHTIMI I PRODUKTIT (VETËM ADMIN)
    # ----------------------------------------------------
    elif is_admin and current_page == "add":
        st.title("➕ Shto Produkt të Ri")
        st.caption("E dukshme VETËM për Administratorët.")

        with st.form("form_add_p", clear_on_submit=True):
            col_l, col_r = st.columns([1.2, 1])
            with col_l:
                name = st.text_input("Emri i Produktit *", placeholder="p.sh. Heartleaf 77% Soothing Toner")
                brand = st.selectbox("Marka Koreane *", [
                    "Beauty of Joseon", "COSRX", "Anua", "Skin1004", "Round Lab",
                    "Laneige", "Some By Mi", "Haruharu Wonder", "I'm From", "Torriden", "Tjetër"
                ])
                if brand == "Tjetër":
                    brand = st.text_input("Shkruaj markën e re *")
                category = st.selectbox("Kategoria *", ["Cleanser (Pastrues)", "Toner", "Serum / Essence", "Moisturizer (Krem)", "Sunscreen (SPF)", "Maskë", "Eye Cream"])
                skin_type = st.selectbox("Lloji i Lëkurës *", ["Të gjitha tipet", "E Thata", "E Yndyrshme", "Mikse (Kombinuar)", "Sensitive", "Me Akne / Poret"])
                price = st.number_input("Çmimi (€) *", min_value=1.0, value=19.50, step=0.50, format="%.2f")

            with col_r:
                uploaded_img = st.file_uploader("📷 Ngarko Foton me Drag & Drop", type=["png", "jpg", "jpeg", "webp"])
                if uploaded_img is not None:
                    st.image(uploaded_img, caption="Parapamje", width=160)
                eu_cert = st.checkbox("🇪🇺 Standarde të BE-së", value=True)
                is_orig = st.checkbox("🇰🇷 100% Origjinale nga Korea", value=True)

            desc = st.text_area("Përshkrimi dhe Përbërësit e Produktit *", placeholder="Shkruaj përfitimet, përbërësit (p.sh. Centella, Rice, Niacinamide)...", height=220)

            if st.form_submit_button("💾 Publiko Produktin", type="primary", use_container_width=True):
                if not name or not brand or price <= 0:
                    st.error("Plotësoni fushat e detyrueshme.")
                else:
                    saved_path = ""
                    if uploaded_img is not None:
                        ext = uploaded_img.name.split(".")[-1]
                        unique_name = f"{uuid.uuid4().hex[:10]}.{ext}"
                        saved_path = os.path.join(UPLOAD_DIR, unique_name).replace("\\", "/")
                        with open(saved_path, "wb") as f:
                            f.write(uploaded_img.getbuffer())

                    database.create_product(name, brand, category, skin_type, price, desc, eu_cert, is_orig, saved_path)
                    st.success(f"🎉 Produkti '{name}' u publikua me sukses në dyqan!")

    # ----------------------------------------------------
    # 4. POROSITË (VETËM ADMIN)
    # ----------------------------------------------------
    elif is_admin and current_page == "orders":
        st.title("📦 Menaxhimi i Porosive të Klientëve")
        st.markdown("<p style='font-size: 0.95rem; opacity: 0.85;'>Këtu mund të shikoni, konfirmoni, ndryshoni statusin dhe fshini porositë me kujdes të veçantë.</p>", unsafe_allow_html=True)

        orders = database.get_all_orders()
        total_count = len(orders)

        pending_count = sum(1 for o in orders if "Pritje" in o.get('status', '') or "Re" in o.get('status', ''))
        confirmed_count = sum(1 for o in orders if "Konfirmuar" in o.get('status', ''))
        delivered_count = sum(1 for o in orders if "Marrë" in o.get('status', '') or "Dërguar" in o.get('status', ''))

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📦 Gjithsej Porosi", total_count)
        m2.metric("⏳ Në Pritje", pending_count)
        m3.metric("✅ Të Konfirmuara", confirmed_count)
        m4.metric("🚚 Të Marra / Dërguara", delivered_count)

        st.divider()

        f_col1, f_col2 = st.columns([2, 1.2])
        with f_col1:
            search_order = st.text_input("🔍 Kërko sipas emrit, telefonit ose qytetit...", key="admin_order_search")
        with f_col2:
            status_filter = st.selectbox(
                "Filtro sipas Statusit",
                ["Të gjitha", "⏳ Në Pritje", "✅ Të Konfirmuara", "🚚 Të Marra / Dërguara"],
                key="admin_order_filter"
            )

        filtered_orders = orders
        if search_order.strip():
            sq = search_order.strip().lower()
            filtered_orders = [
                o for o in filtered_orders
                if sq in o['buyer_name'].lower() or sq in o['phone'].lower() or sq in o['city'].lower() or sq in o['address'].lower() or str(o['id']) == sq
            ]

        if status_filter == "⏳ Në Pritje":
            filtered_orders = [o for o in filtered_orders if "Pritje" in o.get('status', '') or "Re" in o.get('status', '')]
        elif status_filter == "✅ Të Konfirmuara":
            filtered_orders = [o for o in filtered_orders if "Konfirmuar" in o.get('status', '')]
        elif status_filter == "🚚 Të Marra / Dërguara":
            filtered_orders = [o for o in filtered_orders if "Marrë" in o.get('status', '') or "Dërguar" in o.get('status', '')]

        if not filtered_orders:
            st.info("💡 Nuk u gjet asnjë porosi me këto kritere.")
        else:
            st.caption(f"Po shfaqen **{len(filtered_orders)}** porosi nga **{total_count}** gjithsej:")
            for o in filtered_orders:
                st_val = o.get('status', 'E Re (Në Pritje)')
                if "Konfirmuar" in st_val:
                    status_badge = "<span style='background: #10ac84; color: white; padding: 4px 10px; border-radius: 8px; font-size: 11px; font-weight: 700; text-transform: uppercase;'>✅ E Konfirmuar</span>"
                elif "Marrë" in st_val or "Dërguar" in st_val:
                    status_badge = "<span style='background: #2e86de; color: white; padding: 4px 10px; border-radius: 8px; font-size: 11px; font-weight: 700; text-transform: uppercase;'>🚚 E Marrë / E Dërguar</span>"
                else:
                    status_badge = "<span style='background: #f39c12; color: white; padding: 4px 10px; border-radius: 8px; font-size: 11px; font-weight: 700; text-transform: uppercase;'>⏳ Në Pritje</span>"

                expander_title = f"Porosia #{o['id']} — {o['buyer_name']} ({o['city']}) — €{o['total_price']:.2f} — [{st_val}]"
                with st.expander(expander_title):
                    st.markdown(f"<div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;'>"
                                f"<span style='font-size: 1.1rem; font-weight: 700;'>Porosia #{o['id']}</span>"
                                f"<div>{status_badge}</div>"
                                f"</div>", unsafe_allow_html=True)

                    col_det, col_items = st.columns([1.2, 1.4])
                    with col_det:
                        st.markdown("#### 👤 Të Dhënat e Klientit")
                        st.write(f"• **Emri dhe Mbiemri:** `{o['buyer_name']}`")
                        st.write(f"• **Numri i Telefonit:** `{o['phone']}`")
                        st.write(f"• **Qyteti:** `{o['city']}`")
                        st.write(f"• **Adresa e Dërgesës:** {o['address']}")
                        st.write(f"• **Data e Porosisë:** `{o['created_at']}`")

                    with col_items:
                        st.markdown("#### 🛍️ Artikujt e Porositur")
                        try:
                            items_data = json.loads(o['items_json'])
                            for itm in items_data:
                                item_total = itm.get('price', 0) * itm.get('qty', 1)
                                brand_str = f"({itm.get('brand')}) " if itm.get('brand') else ""
                                st.write(f"• **{itm.get('name')}** {brand_str}— **{itm.get('qty')}x** á €{itm.get('price', 0):.2f} = **€{item_total:.2f}**")
                        except Exception:
                            st.write(o['items_json'])
                        st.markdown(f"<div style='font-size: 1.25rem; font-weight: 800; color: #ff758c; margin-top: 10px; text-align: right;'>Totali: €{o['total_price']:.2f}</div>", unsafe_allow_html=True)

                    st.write("")
                    st.divider()
                    st.markdown("##### ⚡ Veprimet me Porosinë:")
                    act1, act2, act3, act4 = st.columns([1.3, 1.6, 1.2, 1.1])

                    with act1:
                        if st.button("✅ Konfirmo", key=f"btn_confirm_{o['id']}", use_container_width=True, type="primary" if "Konfirmuar" not in st_val else "secondary"):
                            database.update_order_status(o['id'], "E Konfirmuar")
                            st.success(f"Porosia #{o['id']} u konfirmua me sukses!")
                            st.rerun()

                    with act2:
                        if st.button("🚚 Shëno si e Marrë", key=f"btn_receive_{o['id']}", use_container_width=True, type="primary" if "Marrë" in st_val else "secondary"):
                            database.update_order_status(o['id'], "E Marrë / E Dërguar")
                            st.success(f"Porosia #{o['id']} u shënua si e marrë / dërguar!")
                            st.rerun()

                    with act3:
                        if st.button("⏳ Kthe në Pritje", key=f"btn_pending_{o['id']}", use_container_width=True, type="secondary"):
                            database.update_order_status(o['id'], "E Re (Në Pritje)")
                            st.info(f"Porosia #{o['id']} u kthye në pritje.")
                            st.rerun()

                    with act4:
                        with st.popover("🗑️ Fshij", use_container_width=True):
                            st.markdown(f"**A jeni i sigurt për fshirjen e porosisë #{o['id']}?**")
                            st.caption("⚠️ Kjo porosi do të fshihet përfundimisht nga baza e të dhënave.")
                            if st.button("Po, fshije!", key=f"btn_delete_confirm_{o['id']}", type="primary", use_container_width=True):
                                database.delete_order(o['id'])
                                st.warning(f"Porosia #{o['id']} u fshi me sukses!")
                                st.rerun()


    # ----------------------------------------------------
    # 5. INVENTARI & MODIFIKIMI (VETËM ADMIN)
    # ----------------------------------------------------
    elif is_admin and current_page == "inventory":
        st.title("📊 Paneli i Inventarit & Modifikimit")
        products = database.get_all_products()

        m1, m2, m3 = st.columns(3)
        m1.metric("📦 Produkte", len(products))
        m2.metric("💰 Vlera", f"€{sum(p['price'] for p in products):.2f}" if products else "€0.00")
        m3.metric("🇪🇺 Standard BE", f"{sum(1 for p in products if p['eu_certified'])} artikuj")

        st.divider()

        if st.session_state.editing_product_id is not None:
            p_to_edit = fetch_product_by_id(st.session_state.editing_product_id)
            if p_to_edit:
                with st.container(border=True):
                    st.subheader(f"✏️ Modifiko Produktin: '{p_to_edit['name']}'")

                    with st.form(f"edit_form_{p_to_edit['id']}"):
                        e_col1, e_col2 = st.columns([1.2, 1])

                        with e_col1:
                            edit_name = st.text_input("Emri i Produktit", value=p_to_edit['name'])
                            edit_brand = st.text_input("Marka", value=p_to_edit['brand'])

                            categories = ["Cleanser (Pastrues)", "Toner", "Serum / Essence", "Moisturizer (Krem)", "Sunscreen (SPF)", "Maskë", "Eye Cream", "Tjetër"]
                            cur_cat_idx = categories.index(p_to_edit['category']) if p_to_edit['category'] in categories else 0
                            edit_category = st.selectbox("Kategoria", categories, index=cur_cat_idx)

                            skin_types = ["Të gjitha tipet", "E Thata", "E Yndyrshme", "Mikse (Kombinuar)", "Sensitive", "Me Akne / Poret"]
                            cur_skin_idx = skin_types.index(p_to_edit['skin_type']) if p_to_edit['skin_type'] in skin_types else 0
                            edit_skin = st.selectbox("Lloji i Lëkurës", skin_types, index=cur_skin_idx)

                            edit_price = st.number_input("Çmimi (€)", min_value=0.5, value=float(p_to_edit['price']), step=0.50, format="%.2f")

                        with e_col2:
                            st.write("📷 **Foto e Produktit:**")
                            if p_to_edit['image_url']:
                                if os.path.exists(p_to_edit['image_url']):
                                    st.image(p_to_edit['image_url'], width=120, caption="Fotoja Aktuale")
                                elif p_to_edit['image_url'].startswith("http"):
                                    st.image(p_to_edit['image_url'], width=120, caption="Fotoja Aktuale")

                            new_uploaded_img = st.file_uploader("Ngarko Foto të Re (Opsionale)", type=["png", "jpg", "jpeg", "webp"])

                            edit_eu = st.checkbox("🇪🇺 Standarde të BE-së", value=bool(p_to_edit['eu_certified']))
                            edit_orig = st.checkbox("🇰🇷 100% Origjinale nga Korea", value=bool(p_to_edit['is_original']))

                        edit_desc = st.text_area("Përshkrimi & Përbërësit", value=p_to_edit['description'] if p_to_edit['description'] else "", height=220)

                        btn_c1, btn_c2 = st.columns([1, 1])
                        with btn_c1:
                            save_btn = st.form_submit_button("💾 Ruaj Ndryshimet", type="primary", use_container_width=True)
                        with btn_c2:
                            cancel_btn = st.form_submit_button("❌ Anulo", type="secondary", use_container_width=True)

                        if save_btn:
                            final_img_path = p_to_edit['image_url']
                            if new_uploaded_img is not None:
                                ext = new_uploaded_img.name.split(".")[-1]
                                unique_name = f"{uuid.uuid4().hex[:10]}.{ext}"
                                final_img_path = os.path.join(UPLOAD_DIR, unique_name).replace("\\", "/")
                                with open(final_img_path, "wb") as f:
                                    f.write(new_uploaded_img.getbuffer())

                            save_updated_product(
                                pid=p_to_edit['id'],
                                name=edit_name,
                                brand=edit_brand,
                                category=edit_category,
                                skin_type=edit_skin,
                                price=edit_price,
                                description=edit_desc,
                                eu_cert=edit_eu,
                                is_orig=edit_orig,
                                img_path=final_img_path
                            )
                            st.session_state.editing_product_id = None
                            st.success("✅ Ndryshimet u ruajtën me sukses!")
                            st.rerun()

                        if cancel_btn:
                            st.session_state.editing_product_id = None
                            st.rerun()

                st.divider()

        if products:
            for p in products:
                with st.expander(f"📦 {p['name']} ({p['brand']}) — €{p['price']:.2f}"):
                    c1, c2, c3 = st.columns([3, 1, 1])
                    with c1:
                        st.write(f"**Marka:** {p['brand']} | **Kategoria:** {p['category']} | **Lëkura:** `{p['skin_type']}`")
                        st.caption(f"BE: {'✅ Po' if p['eu_certified'] else '❌ Jo'} | Origjinale: {'✅ Po' if p['is_original'] else '❌ Jo'}")
                        if p['description']:
                            st.write(f"ℹ️ {p['description']}")
                    with c2:
                        if st.button("✏️ Modifiko", key=f"edit_btn_{p['id']}", use_container_width=True):
                            st.session_state.editing_product_id = p['id']
                            st.rerun()
                    with c3:
                        if st.button("🗑️ Fshij", key=f"inv_del_{p['id']}", use_container_width=True):
                            database.delete_product(p['id'])
                            st.warning("Produkti u fshi!")
                            st.rerun()


# ==========================================
# 🚀 NISJA
# ==========================================
if not st.session_state.authenticated:
    render_auth_page()
else:
    render_main_app()