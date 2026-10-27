# catalog.py
# Logjika e katalogut pa Streamlit: grupimi i kategorive, llojet e lëkurës,
# filtrimi dhe renditja. E ndarë veçmas që të testohet lehtë.
import json
import unicodedata
from typing import Dict, List, Optional

import database

ALL_LABEL = "Të gjitha"

# Grupet e kategorive që sheh klienti -> fjalë kyçe që gjenden në emrat në databazë
CATEGORY_GROUPS = {
    "Pastrues": ("pastr", "cleans", "foam", "balm"),
    "Tonerë": ("toner",),
    "Esenca & Serume": ("serum", "esenc", "essence", "ampoul"),
    "Hidratues & Kremra": ("krem", "cream", "moistur", "hidrat", "gel", "lotion"),
    "Mbrojtës Dielli (SPF)": ("spf", "sun", "diell"),
    "Maska": ("mask", "patch"),
}
OTHER_CATEGORY = "Të tjera"

SKIN_TYPES = {
    "E Thatë": ("that", "dry"),
    "E Yndyrshme": ("yndyr", "oily"),
    "Mikse": ("mikse", "kombin", "combin"),
    "Sensibile": ("sensi", "ndjeshm"),
    "Me Tendencë Akne": ("akne", "acne", "pore"),
}
_ALL_SKIN_KEYWORDS = ("gjitha", "all")

SORT_OPTIONS = ["Më të rejat", "Çmimi: ulët → lart", "Çmimi: lart → ulët", "Më të shiturat"]


def normalize(text: str) -> str:
    """Shkronja të vogla, pa theksa: 'Të Thatë' -> 'te thate' (ë -> e, ç -> c)."""
    text = unicodedata.normalize("NFKD", (text or "").lower())
    return "".join(ch for ch in text if not unicodedata.combining(ch)).strip()


def category_group(category: str) -> str:
    value = normalize(category)
    # Maskat kontrollohen të parat, që "Master Patch" mos të bjerë te kremrat
    for group in ("Maska", "Mbrojtës Dielli (SPF)", "Pastrues", "Tonerë", "Esenca & Serume", "Hidratues & Kremra"):
        if any(keyword in value for keyword in CATEGORY_GROUPS[group]):
            return group
    return OTHER_CATEGORY


def skin_types_of(skin_type: str) -> List[str]:
    """Kthen llojet e lëkurës që mbulon një produkt. 'Të gjitha tipet' i mbulon të gjitha."""
    value = normalize(skin_type)
    if any(keyword in value for keyword in _ALL_SKIN_KEYWORDS):
        return list(SKIN_TYPES)
    return [name for name, keywords in SKIN_TYPES.items() if any(k in value for k in keywords)]


def filter_products(products: List[Dict], category: str = ALL_LABEL, skin_type: str = ALL_LABEL) -> List[Dict]:
    result = []
    for product in products:
        if category != ALL_LABEL and category_group(product.get("category", "")) != category:
            continue
        if skin_type != ALL_LABEL and skin_type not in skin_types_of(product.get("skin_type", "")):
            continue
        result.append(product)
    return result


def sales_counts() -> Dict[str, int]:
    """Sa copë janë shitur nga çdo produkt (sipas emrit), nga porositë jo të anuluara."""
    counts: Dict[str, int] = {}
    for order in database.get_all_orders():
        if order.get("status") == "E Anuluar":
            continue
        try:
            items = json.loads(order.get("items_json") or "[]")
        except json.JSONDecodeError:
            continue  # porosi e dëmtuar: e anashkalojmë që të mos rrëzohet dyqani
        for item in items:
            key = str(item.get("product_id") or item.get("name", ""))
            counts[key] = counts.get(key, 0) + int(item.get("qty", 0))
    return counts


def sort_products(products: List[Dict], sort_by: str, counts: Optional[Dict[str, int]] = None) -> List[Dict]:
    if sort_by == "Çmimi: ulët → lart":
        return sorted(products, key=lambda p: p["price"])
    if sort_by == "Çmimi: lart → ulët":
        return sorted(products, key=lambda p: p["price"], reverse=True)
    if sort_by == "Më të shiturat":
        counts = counts if counts is not None else sales_counts()
        return sorted(
            products,
            key=lambda p: counts.get(str(p["id"]), 0) + counts.get(p["name"], 0),
            reverse=True,
        )
    return sorted(products, key=lambda p: (str(p.get("created_at") or ""), p["id"]), reverse=True)


# ==========================================
# KUISI I RITUALIT
# ==========================================
RITUAL_GOALS = ["Shkëlqim & Glow", "Trajtim Aknesh", "Anti-Rrudhë / Retinal", "Hidratim i Thellë"]
GOAL_KEYWORDS = {
    "Shkëlqim & Glow": ("vitamin", "glow", "niacin", "rice", "bright"),
    "Trajtim Aknesh": ("akne", "acne", "bha", "salicyl", "patch", "centella", "cica", "tea tree"),
    "Anti-Rrudhë / Retinal": ("retin", "peptide", "collagen", "ginseng", "age"),
    "Hidratim i Thellë": ("hyalur", "snail", "mucin", "ceramide", "moistur", "hidrat", "aloe", "avocado"),
}
RITUAL_STEP_GROUPS = [
    ("01 · Pastroni", ("Pastrues",)),
    ("02 · Balanconi", ("Tonerë",)),
    ("03 · Trajtoni", ("Esenca & Serume", "Maska")),
    ("04 · Hidratoni & mbroni", ("Hidratues & Kremra", "Mbrojtës Dielli (SPF)")),
]


def _ritual_score(product: Dict, skin_type: str, goal: str, sensitive: bool) -> int:
    text = normalize(" ".join(str(product.get(f) or "") for f in ("name", "description", "ingredients", "category")))
    covered = skin_types_of(product.get("skin_type", ""))
    score = 0
    if skin_type in covered:
        score += 3
    if sensitive and "Sensibile" in covered:
        score += 2
    score += sum(2 for keyword in GOAL_KEYWORDS.get(goal, ()) if keyword in text)
    if product.get("is_bestseller"):
        score += 1
    return score


def build_ritual(products: List[Dict], skin_type: str, goal: str, sensitive: bool) -> List[Dict]:
    """Zgjedh produktin më të përshtatshëm për secilin nga 4 hapat.
    Kthen listë me {'step': ..., 'product': dict ose None}."""
    routine = []
    used_ids = set()
    for step_label, groups in RITUAL_STEP_GROUPS:
        candidates = [
            p for p in products
            if category_group(p.get("category", "")) in groups and p["id"] not in used_ids
        ]
        best = max(candidates, key=lambda p: _ritual_score(p, skin_type, goal, sensitive), default=None)
        if best:
            used_ids.add(best["id"])
        routine.append({"step": step_label, "product": best})
    return routine


# ==========================================
# SKEDAT E DYQANIT (si në dizajnin e ri)
# ==========================================
STORE_TABS = {
    "Serume": ("Esenca & Serume",),
    "Kremra": ("Hidratues & Kremra",),
    "Pastrim & Toner": ("Pastrues", "Tonerë"),
    "Mbrojtje Dielli": ("Mbrojtës Dielli (SPF)",),
    "Maska": ("Maska",),
}


def store_tab_of(product: Dict) -> str:
    group = category_group(product.get("category", ""))
    for tab, groups in STORE_TABS.items():
        if group in groups:
            return tab
    return "Të tjera"


def filter_by_tab(products: List[Dict], tab: str) -> List[Dict]:
    if tab == ALL_LABEL:
        return products
    return [p for p in products if store_tab_of(p) == tab]


def format_eur(amount: float) -> str:
    """21.9 -> '21,90 €' (presje dhjetore, si në shqip)."""
    return f"{amount:,.2f}".replace(",", " ").replace(".", ",") + " €"


def product_badge(product: Dict, today=None) -> str:
    """'Më i shituri', '-15%', 'I ri' (30 ditët e fundit) ose tekst bosh."""
    from datetime import date, datetime, timedelta
    if product.get("is_bestseller"):
        return "Më i shituri"
    discount = database.discount_percent(product["price"], product.get("old_price"))
    if discount:
        return f"-{discount}%"
    today = today or date.today()
    try:
        created = datetime.strptime(str(product.get("created_at") or "")[:10], "%Y-%m-%d").date()
    except ValueError:
        return ""
    return "I ri" if today - created <= timedelta(days=30) else ""
