# store_api.py
# "Ura" mes faqes së dyqanit (JavaScript) dhe Python-it.
# 1) build_store_data() përgatit të dhënat që i dërgohen faqes.
# 2) handle_event() kryen veprimet që kërkon faqja: kyçje, regjistrim, porosi, mesazh...
# Rregull i artë: asgjë nga browser-i nuk besohet. Çmimet, stoku dhe totali llogariten këtu.
from datetime import date
from typing import Callable, Optional

import auth
import catalog
import checkout
import database
import email_service

RITUAL_SKINS = ["E Thatë", "Mikse", "E Yndyrshme", "Sensibile"]
RITUAL_STEPS = [
    {"n": "01", "label": "Pastrim i dyfishtë", "title": "Pastroni",
     "text": "Balsami pastrues shkrin grimin, pasuar nga xheli i butë."},
    {"n": "02", "label": "Ekuilibër", "title": "Balanconi",
     "text": "Toneri me çaj jeshil përgatit lëkurën dhe ngushton poret."},
    {"n": "03", "label": "Mëngjes · Mbrëmje", "title": "Trajtoni",
     "text": "Serumi me vitaminë C në mëngjes, me retinal në mbrëmje."},
    {"n": "04", "label": "Mbyllja e ritualit", "title": "Hidratoni & mbroni",
     "text": "Kremi me mucinë kërmilli bllokon lagështinë; mbrojtës diellor çdo mëngjes."},
]
MAX_QTY = 50
MAX_LINES = 40

ImageUriFunction = Callable[[str, int, int], str]


# ==========================================
# 1. TË DHËNAT PËR FAQEN
# ==========================================
def _short_text(text: str, limit: int = 160) -> str:
    text = " ".join((text or "").split())
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0] + "…"


def product_for_page(product: dict, image_uri: ImageUriFunction) -> dict:
    discount = database.discount_percent(product["price"], product.get("old_price"))
    ingredients = product.get("ingredients") or ""
    return {
        "id": product["id"],
        "name": product["name"],
        "brand": product["brand"],
        "tab": catalog.store_tab_of(product),
        "group": catalog.category_group(product.get("category", "")),
        "short": _short_text(product.get("description") or ""),
        "long": " ".join((product.get("description") or "").split()),
        "price": round(float(product["price"]), 2),
        "old_price": round(float(product["old_price"]), 2) if discount else None,
        "size": product.get("size_label") or "",
        "badge": catalog.product_badge(product),
        "image": image_uri(product.get("image_url") or "", 700, 84),
        "ingredients": ingredients,
        "ingredients_list": [part.strip() for part in ingredients.split(",") if part.strip()],
        "how_to_use": product.get("how_to_use") or "",
        "is_bestseller": bool(product.get("is_bestseller")),
        "skin_types": catalog.skin_types_of(product.get("skin_type", "")),
        "search": catalog.normalize(" ".join(str(product.get(f) or "") for f in
                                             ("name", "description", "ingredients", "category"))),
    }


def collection_title(products: list) -> str:
    only_k_secret = products and all((p.get("brand") or "").lower().replace("-", "").replace(" ", "") == "ksecret"
                                     for p in products)
    return "Koleksioni K-Secret" if only_k_secret else "Koleksioni K-Beauty"


def featured_ids(products: list, limit: int = 3) -> list:
    bestsellers = [p["id"] for p in products if p.get("is_bestseller")]
    return (bestsellers or [p["id"] for p in products])[:limit]


def public_user(user: Optional[dict]) -> Optional[dict]:
    """Vetëm fushat që i duhen faqes (kurrë hash-i i fjalëkalimit apo kodet)."""
    if not user:
        return None
    return {"name": user.get("full_name") or user.get("username") or "", "email": user.get("email") or "",
            "is_admin": user.get("role") == "admin"}


def build_store_data(image_uri: ImageUriFunction, user: Optional[dict], results: dict) -> dict:
    settings = database.get_all_settings()
    fee, threshold = checkout.shipping_rules(settings)
    raw_products = database.get_all_products()
    return {
        "products": [product_for_page(p, image_uri) for p in raw_products],
        "featured_ids": featured_ids(raw_products),
        "collection_title": collection_title(raw_products),
        "tabs": [catalog.ALL_LABEL, *catalog.STORE_TABS],
        "settings": {
            "announcement": settings.get("announcement_text", ""),
            "whatsapp": settings.get("whatsapp_number", ""),
            "location": settings.get("store_location", ""),
            "email": settings.get("contact_email", ""),
            "instagram": settings.get("instagram_url", ""),
            "facebook": settings.get("facebook_url", ""),
            "hero_image": settings.get("hero_image_url", ""),
            "logo_image": settings.get("logo_image_url", ""),
            "shipping_fee": fee,
            "free_shipping_threshold": threshold,
        },
        "user": public_user(user),
        "results": results,
        "ritual_steps": RITUAL_STEPS,
        "ritual_plan": [{"n": label[:2], "label": label[5:], "groups": list(groups)}
                        for label, groups in catalog.RITUAL_STEP_GROUPS],
        "ritual_goals": catalog.RITUAL_GOALS,
        "ritual_skins": RITUAL_SKINS,
        "goal_keywords": {goal: list(words) for goal, words in catalog.GOAL_KEYWORDS.items()},
        "ritual_discount": 0.10,
        "year": date.today().year,
    }


# ==========================================
# 2. VEPRIMET
# ==========================================
def _text(payload: dict, key: str, limit: int = 300) -> str:
    value = payload.get(key, "")
    return str(value).strip()[:limit] if isinstance(value, (str, int, float)) else ""


def _test_code(code: str) -> str:
    # Kodi shfaqet vetëm kur email-i NUK është konfiguruar fare (zhvillim lokal)
    return code if code and not email_service.is_smtp_configured() else ""


def validate_contact(name: str, email: str, phone: str, message: str) -> list:
    errors = []
    if not name:
        errors.append("Shkruani emrin.")
    if not email and not phone:
        errors.append("Shkruani email-in ose telefonin, që t'ju përgjigjemi.")
    if email and not auth.is_valid_email(email):
        errors.append("Email-i nuk duket i saktë.")
    if phone and not checkout.PHONE_PATTERN.match(phone):
        errors.append("Numri i telefonit nuk është i saktë.")
    if not message:
        errors.append("Shkruani mesazhin.")
    return errors


def priced_items(raw_items) -> tuple[list, list]:
    """Kthen (artikujt me çmime nga databaza, gabimet). Injoron çmimet që vijnë nga browser-i."""
    if not isinstance(raw_items, list) or not raw_items:
        return [], ["Shporta është bosh."]
    if len(raw_items) > MAX_LINES:
        return [], ["Shporta ka shumë artikuj."]
    items, errors = [], []
    for raw in raw_items:
        try:
            product_id = int(raw.get("id"))
            quantity = int(raw.get("qty"))
        except (TypeError, ValueError, AttributeError):
            return [], ["Shporta përmban të dhëna të pavlefshme. Rifreskoni faqen."]
        if not 1 <= quantity <= MAX_QTY:
            return [], [f"Sasia duhet të jetë nga 1 deri në {MAX_QTY}."]
        product = database.get_product_by_id(product_id)
        if not product:
            errors.append("Një produkt në shportë nuk ekziston më. Hiqeni nga shporta.")
            continue
        ritual = bool(raw.get("ritual"))
        price = round(product["price"] * (1 - 0.10), 2) if ritual else round(product["price"], 2)
        items.append({
            "product_id": product["id"],
            "name": product["name"] + (" · Rituali −10%" if ritual else ""),
            "brand": product["brand"],
            "price": price,
            "image": product.get("image_url") or "",
            "size": product.get("size_label") or "",
            "qty": quantity,
        })
    return items, errors


def place_order(payload: dict) -> dict:
    items, errors = priced_items(payload.get("items"))
    if errors:
        return {"ok": False, "errors": errors}
    name, phone = _text(payload, "name", 80), _text(payload, "phone", 20)
    city, address = _text(payload, "city", 60), _text(payload, "address", 300)
    notes, email = _text(payload, "notes", 300), _text(payload, "email", 120)
    errors = checkout.validate_delivery(name, phone, city, address, email) + checkout.stock_problems(items)
    if errors:
        return {"ok": False, "errors": errors}

    subtotal = round(sum(item["price"] * item["qty"] for item in items), 2)
    totals = checkout.calculate_totals(subtotal, database.get_all_settings(), _text(payload, "coupon", 20))
    order_id = database.create_order(buyer_name=name, phone=phone, city=city, address=address, items=items,
                                     total_price=totals["total"], customer_notes=notes, buyer_email=email)
    for item in items:
        database.reduce_stock_after_order(item["product_id"], item["qty"])

    # Email-et: nëse dështojnë, porosia mbetet e ruajtur (admini e sheh në panel)
    email_service.send_order_notification_email(
        order_id=order_id, buyer_name=name, phone=phone, city=city, address=address, items=items,
        total_price=totals["total"], to_admin_email=email_service.admin_email(),
    )
    email_sent = False
    if email:
        email_sent, _ = email_service.send_order_confirmation_to_customer(email, order_id, name, items, totals["total"])
    return {"ok": True, "order": {"id": order_id, "name": name, "phone": phone, "email": email,
                                  "email_sent": bool(email_sent), "total": totals["total"],
                                  "discount": totals["discount"]}}


def handle_event(event: dict, session) -> dict:
    """Kryen një veprim nga faqja. `session` është st.session_state (ose një dict në teste)."""
    action = event.get("type")
    payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}

    if action == "contact":
        name, email = _text(payload, "name", 80), _text(payload, "email", 120)
        phone, message = _text(payload, "phone", 20), _text(payload, "message", 2000)
        errors = validate_contact(name, email, phone, message)
        if errors:
            return {"ok": False, "errors": errors}
        database.create_message(name, message, email=email, phone=phone)
        email_service.send_contact_notification_email(name, email, phone, message)
        return {"ok": True}

    if action == "place_order":
        return place_order(payload)

    if action == "login":
        ok, result = auth.login_user(_text(payload, "identifier", 120), str(payload.get("password", ""))[:128])
        if ok:
            _sign_in(session, result)
            return {"ok": True, "user": public_user(result)}
        if isinstance(result, str) and result.startswith("UNVERIFIED:"):
            return {"ok": False, "unverified_email": result.split(":", 1)[1],
                    "message": "Llogaria nuk është verifikuar ende."}
        return {"ok": False, "message": result}

    if action == "register":
        ok, message, code = auth.register_client(_text(payload, "name", 80), _text(payload, "email", 120),
                                                 str(payload.get("password", ""))[:128], str(payload.get("confirm", ""))[:128])
        result = {"ok": ok, "message": message}
        if ok:
            result.update(pending_email=_text(payload, "email", 120).lower(), test_code=_test_code(code))
        return result

    if action == "verify":
        email = _text(payload, "email", 120)
        ok, message = auth.verify_client_code(email, _text(payload, "code", 6))
        if ok:
            user = database.get_user_by_email(email)
            _sign_in(session, user)
            return {"ok": True, "user": public_user(user)}
        return {"ok": False, "message": message}

    if action == "resend_code":
        ok, message, code = auth.resend_client_code(_text(payload, "email", 120))
        return {"ok": ok, "message": message, "test_code": _test_code(code)}

    if action == "reset":
        ok, message, _, code = auth.request_password_reset_code(_text(payload, "identifier", 120))
        return {"ok": ok, "message": message, "test_code": _test_code(code) if ok else ""}

    if action == "reset_confirm":
        ok, message = auth.confirm_password_reset_code(_text(payload, "identifier", 120), _text(payload, "code", 6),
                                                       str(payload.get("password", ""))[:128],
                                                       str(payload.get("confirm", ""))[:128])
        return {"ok": ok, "message": message}

    if action == "logout":
        auth.end_session(session.get("session_token"))
        session["authenticated"] = False
        session["current_user"] = None
        session["session_token"] = None
        return {"ok": True}

    return {"ok": False, "message": "Veprim i panjohur."}


def _sign_in(session, user: dict) -> None:
    session["authenticated"] = True
    session["current_user"] = user
    session["session_token"] = auth.start_session(user)
