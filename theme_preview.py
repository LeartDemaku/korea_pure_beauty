# theme_preview.py
# Faqe kontrolli për Fazën 1: shfaq ngjyrat, fontet dhe komponentët bazë.
# Nisja:  python -m streamlit run theme_preview.py --server.port 8503
import streamlit as st

import database
import theme

st.set_page_config(page_title="KPB · Sistemi i Dizajnit", page_icon="🌸", layout="wide")
theme.load_css("main")

# Migrimi i Fazës 1 ekzekutohet këtu (i sigurt edhe kur niset shumë herë)
database.init_database()

# --- 1. Tipografia ---
st.markdown("""
<span class="kpb-overline">K-Secret · Premium Korean Skincare</span>
<h1 class="kpb-display">Sekreti korean i një<br>lëkure <span class="kpb-accent">rrezatuese</span></h1>
<p class="kpb-lead">Kjo është faqja e kontrollit të sistemit të dizajnit. Këtu shihen fontet,
ngjyrat dhe komponentët që do të përdoren në të gjitha faqet e dyqanit.</p>
<div style="display:flex;gap:1.5rem;align-items:center;flex-wrap:wrap;margin:1.5rem 0;">
  <a class="kpb-btn" href="#">Zbulo produktet</a>
  <a class="kpb-link-arrow" href="#">Rituali në 4 hapa →</a>
  <span class="kpb-badge"><span class="kpb-badge__dot"></span>100% origjinale · Prodhuar në Seul</span>
</div>
<p class="kpb-script" style="font-size:3rem;margin:0;">Beauty</p>
<hr class="kpb-divider">
""", unsafe_allow_html=True)

# --- 2. Paleta e ngjyrave ---
st.markdown('<h2 class="kpb-h2">Paleta e ngjyrave</h2>', unsafe_allow_html=True)
swatch_columns = st.columns(len(theme.PALETTE))
for column, (color_name, hex_code) in zip(swatch_columns, theme.PALETTE.items()):
    column.markdown(
        f'<div style="height:72px;border-radius:12px;background:{hex_code};'
        f'border:1px solid var(--kpb-sand);"></div>'
        f'<p style="margin:.4rem 0 0;font-weight:600;">{color_name}</p>'
        f'<p class="kpb-muted" style="margin:0;font-size:.8rem;">{hex_code}</p>',
        unsafe_allow_html=True,
    )

# --- 3. Kartë produkti dhe badges të statusit ---
st.markdown('<hr class="kpb-divider">', unsafe_allow_html=True)
card_column, status_column = st.columns([1, 2])
with card_column:
    discount = database.discount_percent(17.0, 20.0)
    st.markdown(f"""
    <div class="kpb-card">
      <span class="kpb-badge kpb-badge--accent">Bestseller</span>
      <h3 style="margin:1rem 0 .3rem;">Glow Deep Serum</h3>
      <p class="kpb-muted" style="margin:0 0 .6rem;">Beauty of Joseon · Esenca &amp; Serume</p>
      <span class="kpb-price">17.00 €</span><span class="kpb-price--old">20.00 €</span>
      <span class="kpb-badge" style="margin-left:.5rem;">-{discount}%</span>
    </div>
    """, unsafe_allow_html=True)
    st.button("Shto në shportë", type="primary", use_container_width=True)
    st.button("Shiko detajet", use_container_width=True)
with status_column:
    st.markdown("""
    <h3>Treguesit e Admin-it</h3>
    <div style="display:flex;gap:.6rem;flex-wrap:wrap;">
      <span class="kpb-badge kpb-badge--success">Në stok</span>
      <span class="kpb-badge kpb-badge--warning">Stok kritik</span>
      <span class="kpb-badge kpb-badge--danger">Pa stok</span>
    </div>
    """, unsafe_allow_html=True)

# --- 4. Seksioni i errët (pamje paraprake e Ritualit) ---
steps = [
    ("01", "Pastrim i Dyfishtë"),
    ("02", "Ekuilibër"),
    ("03", "Mëngjes · Mbrëmje"),
    ("04", "Mbyllja e Ritualit"),
]
steps_html = "".join(
    f'<div><div class="kpb-step-number">{number}</div><p style="margin:.6rem 0 0;">{title}</p></div>'
    for number, title in steps
)
st.markdown(f"""
<hr class="kpb-divider">
<section class="kpb-section-dark">
  <h2 class="kpb-h2">Katër hapa, një lëkurë që <span class="kpb-accent">flet vetë</span></h2>
  <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:2rem;margin-top:2rem;">
    {steps_html}
  </div>
</section>
""", unsafe_allow_html=True)

# --- 5. Gjendja e bazës së të dhënave pas migrimit ---
st.markdown('<hr class="kpb-divider"><h2 class="kpb-h2">Baza e të dhënave</h2>', unsafe_allow_html=True)
settings = database.get_all_settings()
metric_columns = st.columns(3)
metric_columns[0].metric("Produkte", len(database.get_all_products()))
metric_columns[1].metric("Mesazhe të palexuara", database.count_unread_messages())
metric_columns[2].metric("Transport falas mbi", f"{settings.get('free_shipping_threshold', '—')} €")
