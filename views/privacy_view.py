# views/privacy_view.py
# Politika e privatësisë dhe kushtet e blerjes.
# Shënim: ky tekst është model. Para publikimit, kontrollojeni me një jurist sipas ligjit në fuqi.
import streamlit as st

import database
import theme
from views import components

LAST_UPDATED = "27 tetor 2026"


def render_privacy() -> None:
    theme.load_css("pages")
    settings = database.get_all_settings()
    fee = settings.get("shipping_fee", "")
    threshold = settings.get("free_shipping_threshold", "")
    shipping_line = ""
    if fee:
        shipping_line = f"Transporti kushton {fee} €"
        shipping_line += f" dhe është falas për porosi mbi {threshold} €." if threshold else "."

    components.section_head("Dokumente ligjore", 'Privatësia & <span class="kpb-accent">kushtet</span>')
    st.markdown(f"""
    <article class="kpb-legal">
      <p class="kpb-muted">Përditësuar më: {LAST_UPDATED}</p>

      <h3>1. Mbrojtja e të dhënave personale</h3>
      <p>Kur bëni një porosi, ne mbledhim emrin, numrin e telefonit, qytetin dhe adresën e dërgesës.
      Këto të dhëna përdoren <strong>vetëm</strong> për të realizuar dhe dërguar porosinë tuaj dhe për t'ju
      kontaktuar për të. Nuk i shesim dhe nuk ua japim palëve të treta, përveç kompanisë postare që e dorëzon porosinë.</p>
      <p>Mesazhet nga formulari i kontaktit ruhen që t'ju përgjigjemi. Mund të kërkoni në çdo kohë
      të shihni, korrigjoni ose fshini të dhënat tuaja duke na shkruar te faqja e Kontaktit.</p>
      <p>Fjalëkalimet e llogarive ruhen të koduara (hash) dhe askush nga stafi nuk mund t'i lexojë.</p>

      <h3>2. Dërgesat</h3>
      <p>Porositë dërgohen brenda 24–48 orëve në Kosovë, Shqipëri dhe Maqedoni të Veriut, përmes kompanive
      postare partnere. {shipping_line} Pagesa bëhet me para në dorë në momentin e dorëzimit.</p>

      <h3>3. Kthimi dhe ndërrimi</h3>
      <p>Produktet mund të kthehen ose ndërrohen brenda <strong>14 ditëve</strong> nga dorëzimi, me kusht që
      të jenë të pahapura dhe në paketimin origjinal. Për arsye higjiene, produktet e hapura nuk mund të kthehen,
      përveç rasteve kur produkti ka ardhur i dëmtuar ose i gabuar. Na kontaktoni para se ta dërgoni produktin.</p>

      <h3>4. Origjinaliteti dhe siguria</h3>
      <p>Të gjitha produktet importohen direkt nga Koreja e Jugut dhe shiten në paketimin origjinal të
      prodhuesit. Për çdo produkt mund të kërkoni informacion mbi origjinën dhe dokumentet shoqëruese.</p>

      <h3>5. Kontakti</h3>
      <p>Për çdo pyetje rreth këtyre kushteve, na shkruani te faqja e Kontaktit.</p>
    </article>
    """, unsafe_allow_html=True)

    components.render_footer()
