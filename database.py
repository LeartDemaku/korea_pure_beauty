# database.py
import os
import sqlite3
import json
from contextlib import contextmanager
from typing import Optional, List, Dict, Any

# Rruga absolute: baza gjendet gjithmonë pranë këtij skedari,
# pavarësisht nga cila dosje niset aplikacioni.
DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'korea_beauty.db')

# ==========================================
# KONSTANTET E SISTEMIT
# ==========================================

# Rrjedha e statuseve të porosisë (Faza 5 – Admin)
ORDER_STATUSES = [
    'E Re (Në Pritje)',
    'Në Përpunim',
    'Dërguar me Postë',
    'E Përfunduar / Dorëzuar',
    'E Anuluar',
]

# Statuset e mesazheve të kontaktit
MESSAGE_STATUSES = ['I Palexuar', 'I Përgjigjur', 'I Arkivuar']

# Pragu i stokut kritik (nën këtë numër shfaqet paralajmërim në Admin)
LOW_STOCK_THRESHOLD = 3

# Vlerat fillestare të cilësimeve të dyqanit.
# Futen vetëm nëse çelësi nuk ekziston, kështu që ndryshimet e adminit nuk humbin.
DEFAULT_SETTINGS = {
    'announcement_text': 'Transport falas në Kosovë për porosi mbi 30€',
    'whatsapp_number': '38345319619',  # numri i dyqanit (ishte i shkruar në kod)
    'shipping_fee': '2.00',
    'free_shipping_threshold': '30.00',
    'business_hours': '',
    'contact_email': '',
    # '1' = mos lejo blerje mbi stokun. Ndize te Admin pasi të futësh stokun e vërtetë.
    'enforce_stock': '0',
}

# Kolonat e reja që shtohen në tabelat ekzistuese pa humbur të dhëna.
# Formati: (emri_kolonës, definicioni SQL)
_PRODUCT_NEW_COLUMNS = [
    ('old_price', 'REAL'),
    ('stock_qty', 'INTEGER DEFAULT 0'),
    ('ingredients', "TEXT DEFAULT ''"),
    ('how_to_use', "TEXT DEFAULT ''"),
    ('is_bestseller', 'INTEGER DEFAULT 0'),
]
_ORDER_NEW_COLUMNS = [
    ('tracking_number', "TEXT DEFAULT ''"),
    ('admin_notes', "TEXT DEFAULT ''"),
    ('payment_method', "TEXT DEFAULT 'Para në dorë'"),
    ('customer_notes', "TEXT DEFAULT ''"),
    ('buyer_email', "TEXT DEFAULT ''"),
]

# Fushat e produktit që lejohen të ndryshohen nga update_product_fields().
# Lista e bardhë na mbron nga emrat e kolonave të panjohura në SQL.
_EDITABLE_PRODUCT_FIELDS = {
    'name', 'brand', 'category', 'skin_type', 'price', 'old_price', 'description',
    'eu_certified', 'is_original', 'image_url', 'stock_qty', 'ingredients',
    'how_to_use', 'is_bestseller',
}

def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def _db():
    """Hap lidhjen, bën commit nëse gjithçka shkoi mirë, dhe e mbyll gjithmonë."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _add_missing_columns(cursor, table: str, columns: list) -> None:
    """Migrim i sigurt: shton vetëm kolonat që mungojnë (PRAGMA table_info)."""
    cursor.execute(f"PRAGMA table_info({table})")
    existing = {row[1] for row in cursor.fetchall()}
    for col_name, col_def in columns:
        if col_name not in existing:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_def}")

def init_database():
    conn = get_connection()
    cursor = conn.cursor()

    # Tabela users
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            full_name TEXT,
            email TEXT,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'client',
            is_verified INTEGER DEFAULT 1,
            verification_code TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Migrimi automatik për bazën ekzistuese të të dhënave
    cursor.execute("PRAGMA table_info(users)")
    existing_cols = [c[1] for c in cursor.fetchall()]

    if 'full_name' not in existing_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN full_name TEXT")
    if 'email' not in existing_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
    if 'is_verified' not in existing_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN is_verified INTEGER DEFAULT 1")
    if 'verification_code' not in existing_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN verification_code TEXT")

    # Tabela products
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            brand TEXT NOT NULL,
            category TEXT NOT NULL,
            skin_type TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT,
            eu_certified BOOLEAN DEFAULT 1,
            is_original BOOLEAN DEFAULT 1,
            image_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Tabela orders
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            buyer_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            city TEXT NOT NULL,
            address TEXT NOT NULL,
            items_json TEXT NOT NULL,
            total_price REAL NOT NULL,
            status TEXT DEFAULT 'E Re (Në Pritje)',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # --- Faza 1: zgjerimi i tabelave ekzistuese ---
    _add_missing_columns(cursor, 'products', _PRODUCT_NEW_COLUMNS)
    _add_missing_columns(cursor, 'orders', _ORDER_NEW_COLUMNS)

    # Tabela e re: mesazhet nga faqja e Kontaktit
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            message TEXT NOT NULL,
            status TEXT DEFAULT 'I Palexuar',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Tabela e re: cilësimet e dyqanit (çelës -> vlerë)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS store_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL DEFAULT ''
        )
    ''')
    cursor.executemany(
        'INSERT OR IGNORE INTO store_settings (key, value) VALUES (?, ?)',
        list(DEFAULT_SETTINGS.items())
    )
    # Bazat e krijuara në Fazën 1 e kishin numrin bosh: e plotësojmë një herë
    cursor.execute(
        "UPDATE store_settings SET value = ? WHERE key = 'whatsapp_number' AND value = ''",
        (DEFAULT_SETTINGS['whatsapp_number'],)
    )

    # Tabela e re: vlerësimet e klientëve (vetëm vlerësime të vërteta, të shtuara nga admini)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS testimonials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            city TEXT DEFAULT '',
            text TEXT NOT NULL,
            rating INTEGER NOT NULL DEFAULT 5 CHECK (rating BETWEEN 1 AND 5),
            is_visible INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Tabela e re: sesionet e kyçjes (zëvendëson ?user=emri, i cili ishte i pasigurt).
    # Ruajmë vetëm hash-in e token-it, kurrë vetë token-in.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            token_hash TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()

# ===== USERS =====
def create_user(username: str, password_hash: str, role: str = 'client', full_name: str = '', email: str = '', is_verified: int = 1, verification_code: str = '') -> int:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO users (username, full_name, email, password_hash, role, is_verified, verification_code)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (username, full_name, email, password_hash, role, is_verified, verification_code))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def create_client_user(full_name: str, email: str, password_hash: str, verification_code: str) -> int:
    """Krijon një klient të ri me status të paverifikuar derisa të konfirmojë kodin."""
    conn = get_connection()
    cursor = conn.cursor()
    email_clean = email.strip().lower()
    full_name_clean = full_name.strip()
    try:
        cursor.execute('''
            INSERT INTO users (username, full_name, email, password_hash, role, is_verified, verification_code)
            VALUES (?, ?, ?, ?, 'client', 0, ?)
        ''', (email_clean, full_name_clean, email_clean, password_hash, verification_code))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def get_user_by_username(username: str) -> Optional[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM users WHERE LOWER(username) = LOWER(?)', (username.strip(),))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def get_user_by_email(email: str) -> Optional[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM users WHERE LOWER(email) = LOWER(?) OR LOWER(username) = LOWER(?)', (email.strip(), email.strip()))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def get_user_by_identifier(identifier: str) -> Optional[Dict]:
    """Kërkon përdoruesin sipas username ose email-it."""
    conn = get_connection()
    cursor = conn.cursor()
    val = identifier.strip().lower()
    try:
        cursor.execute('SELECT * FROM users WHERE LOWER(username) = ? OR LOWER(email) = ?', (val, val))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def verify_user_code(email: str, code: str) -> tuple[bool, str]:
    """Verifikon kodin e dërguar në email dhe aktivizon llogarinë."""
    conn = get_connection()
    cursor = conn.cursor()
    email_clean = email.strip().lower()
    code_clean = code.strip()
    try:
        cursor.execute('SELECT * FROM users WHERE LOWER(email) = ? OR LOWER(username) = ?', (email_clean, email_clean))
        row = cursor.fetchone()
        if not row:
            return False, "Përdoruesi nuk u gjet."
        
        user = dict(row)
        if user.get('is_verified', 1) == 1:
            return True, "Llogaria është tashmë e verifikuar!"
        
        if str(user.get('verification_code', '')).strip() == code_clean:
            cursor.execute('UPDATE users SET is_verified = 1, verification_code = "" WHERE id = ?', (user['id'],))
            conn.commit()
            return True, "Llogaria u verifikua me sukses!"
        else:
            return False, "Kodi i verifikimit është i pasaktë. Ju lutem provoni përsëri."
    finally:
        conn.close()

def update_user_verification_code(email: str, new_code: str) -> bool:
    """Përditëson kodin e verifikimit për ridërgim."""
    conn = get_connection()
    cursor = conn.cursor()
    email_clean = email.strip().lower()
    try:
        cursor.execute('UPDATE users SET verification_code = ? WHERE LOWER(email) = ? OR LOWER(username) = ?', (new_code.strip(), email_clean, email_clean))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()

def update_user_password(user_id: int, new_password_hash: str) -> bool:
    """Përditëson fjalëkalimin e një përdoruesi me ID."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_password_hash, user_id))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()

def set_password_reset_code(identifier: str, code: str) -> tuple[bool, str, Optional[Dict]]:
    """Vendos kodin e rivendosjes për përdoruesin dhe kthen të dhënat e tij."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        user = get_user_by_identifier(identifier)
        if not user:
            return False, "Nuk u gjet asnjë llogari me këtë email ose username.", None

        email = user.get('email')
        if not email:
            return False, "Kjo llogari nuk ka një adresë email të lidhur.", None

        cursor.execute("UPDATE users SET verification_code = ? WHERE id = ?", (code.strip(), user['id']))
        conn.commit()
        return True, "Kodi u caktua me sukses.", user
    finally:
        conn.close()

def reset_password_with_code(identifier: str, code: str, new_password_hash: str) -> tuple[bool, str]:
    """Rivendos fjalëkalimin me kodin e marrë në email."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        user = get_user_by_identifier(identifier)
        if not user:
            return False, "Përdoruesi nuk u gjet."

        saved_code = str(user.get('verification_code') or '').strip()
        if not saved_code or saved_code != code.strip():
            return False, "Kodi i sigurisë është i pasaktë ose ka skaduar."

        cursor.execute("UPDATE users SET password_hash = ?, verification_code = '' WHERE id = ?", (new_password_hash, user['id']))
        conn.commit()
        return True, "Fjalëkalimi u ndryshua me sukses! Tani mund të kyçeni."
    finally:
        conn.close()

def count_admins() -> int:
    with _db() as conn:
        return conn.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'").fetchone()[0]


# ===== SESSIONS (kyçja e sigurt pas rifreskimit të faqes) =====
def create_session(user_id: int, token_hash: str, valid_days: int) -> None:
    with _db() as conn:
        # Pastrojmë sesionet e skaduara sa herë krijohet një i ri
        conn.execute("DELETE FROM sessions WHERE expires_at <= datetime('now')")
        conn.execute(
            "INSERT INTO sessions (token_hash, user_id, expires_at) "
            "VALUES (?, ?, datetime('now', ?))",
            (token_hash, user_id, f'+{int(valid_days)} days')
        )


def get_user_by_session(token_hash: str) -> Optional[Dict]:
    """Kthen përdoruesin vetëm nëse sesioni ekziston dhe nuk ka skaduar."""
    with _db() as conn:
        row = conn.execute(
            "SELECT users.* FROM sessions JOIN users ON users.id = sessions.user_id "
            "WHERE sessions.token_hash = ? AND sessions.expires_at > datetime('now')",
            (token_hash,)
        ).fetchone()
        return dict(row) if row else None


def delete_session(token_hash: str) -> None:
    with _db() as conn:
        conn.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))


def delete_user_sessions(user_id: int) -> None:
    """Del nga të gjitha pajisjet (p.sh. pas ndryshimit të fjalëkalimit)."""
    with _db() as conn:
        conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))


# ===== PRODUCTS =====
def create_product(name: str, brand: str, category: str, skin_type: str,
                   price: float, description: str = '', eu_certified: bool = True,
                   is_original: bool = True, image_url: str = '',
                   old_price: Optional[float] = None, stock_qty: int = 0,
                   ingredients: str = '', how_to_use: str = '',
                   is_bestseller: bool = False) -> int:
    # Fushat e reja kanë vlera të paracaktuara, ndaj thirrjet e vjetra
    # në app.py dhe client_app.py vazhdojnë të funksionojnë pa ndryshim.
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO products (name, brand, category, skin_type, price, description,
                                  eu_certified, is_original, image_url,
                                  old_price, stock_qty, ingredients, how_to_use, is_bestseller)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, brand, category, skin_type, price, description, eu_certified, is_original, image_url,
              old_price, max(0, int(stock_qty)), ingredients, how_to_use, int(bool(is_bestseller))))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def get_product_by_id(product_id: int) -> Optional[Dict]:
    """Merr një produkt të vetëm sipas ID-së për faqen e detajuar."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def get_all_products() -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM products ORDER BY created_at DESC')
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

def search_products(query: str) -> List[Dict]:
    if not query or not query.strip():
        return get_all_products()
    tokens = [t.strip() for t in query.strip().split() if t.strip()]
    if not tokens:
        return get_all_products()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        clauses = []
        params = []
        for t in tokens:
            clauses.append("(name LIKE ? OR brand LIKE ? OR category LIKE ? OR skin_type LIKE ? OR description LIKE ?)")
            p = f'%{t}%'
            params.extend([p, p, p, p, p])
        where_sql = " AND ".join(clauses)
        cursor.execute(f'SELECT * FROM products WHERE {where_sql} ORDER BY created_at DESC', tuple(params))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

def get_products_by_category(category: str) -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM products WHERE category = ? ORDER BY created_at DESC', (category,))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

def get_products_by_skin_type(skin_type: str) -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM products WHERE skin_type = ? ORDER BY created_at DESC', (skin_type,))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

def delete_product(product_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()

# ===== ORDERS =====
def create_order(buyer_name: str, phone: str, city: str, address: str, items: list, total_price: float,
                 customer_notes: str = '', buyer_email: str = '', payment_method: str = 'Para në dorë') -> int:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        items_str = json.dumps(items, ensure_ascii=False)
        cursor.execute('''
            INSERT INTO orders (buyer_name, phone, city, address, items_json, total_price,
                                customer_notes, buyer_email, payment_method)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (buyer_name, phone, city, address, items_str, total_price,
              customer_notes.strip(), buyer_email.strip().lower(), payment_method))
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()

def get_all_orders() -> List[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM orders ORDER BY created_at DESC')
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

def get_order_by_id(order_id: int) -> Optional[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM orders WHERE id = ?', (order_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def update_order_status(order_id: int, new_status: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('UPDATE orders SET status = ? WHERE id = ?', (new_status, order_id))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()

def delete_order(order_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM orders WHERE id = ?', (order_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()

# ===== PRODUCTS: FAZA 1 (stoku, zbritjet, bestsellers) =====
def update_product_fields(product_id: int, **fields: Any) -> bool:
    """Përditëson vetëm fushat e dhëna, p.sh. update_product_fields(5, price=16.9, stock_qty=12)."""
    unknown = set(fields) - _EDITABLE_PRODUCT_FIELDS
    if unknown:
        raise ValueError(f"Fusha të panjohura për produktin: {', '.join(sorted(unknown))}")
    if not fields:
        return False
    # Emrat e kolonave vijnë nga lista e bardhë; vlerat kalojnë si parametra (?)
    set_sql = ', '.join(f"{col} = ?" for col in fields)
    with _db() as conn:
        cur = conn.execute(f"UPDATE products SET {set_sql} WHERE id = ?", (*fields.values(), product_id))
        return cur.rowcount > 0


def set_product_stock(product_id: int, stock_qty: int) -> bool:
    return update_product_fields(product_id, stock_qty=max(0, int(stock_qty)))


def decrement_stock(product_id: int, quantity: int) -> bool:
    """Ul stokun pas një blerjeje. Kthen False nëse nuk ka stok të mjaftueshëm."""
    if quantity <= 0:
        raise ValueError("Sasia duhet të jetë më e madhe se 0.")
    with _db() as conn:
        # Kushti 'stock_qty >= ?' bën që stoku të mos bjerë kurrë nën zero,
        # edhe nëse dy klientë blejnë të njëjtin produkt në të njëjtën kohë.
        cur = conn.execute(
            "UPDATE products SET stock_qty = stock_qty - ? WHERE id = ? AND stock_qty >= ?",
            (quantity, product_id, quantity)
        )
        return cur.rowcount > 0


def reduce_stock_after_order(product_id: int, quantity: int) -> None:
    """Ul stokun pas porosisë; nuk zbret nën zero (stoku mund të mos jetë futur ende)."""
    with _db() as conn:
        conn.execute(
            "UPDATE products SET stock_qty = MAX(stock_qty - ?, 0) WHERE id = ?",
            (max(0, int(quantity)), product_id)
        )


def get_bestsellers(limit: int = 8) -> List[Dict]:
    with _db() as conn:
        rows = conn.execute(
            "SELECT * FROM products WHERE is_bestseller = 1 ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_low_stock_products(threshold: int = LOW_STOCK_THRESHOLD) -> List[Dict]:
    with _db() as conn:
        rows = conn.execute(
            "SELECT * FROM products WHERE stock_qty < ? ORDER BY stock_qty ASC, name ASC", (threshold,)
        ).fetchall()
        return [dict(r) for r in rows]


def discount_percent(price: float, old_price: Optional[float]) -> int:
    """Llogarit përqindjen e zbritjes për badge-in (p.sh. -15%). Kthen 0 nëse s'ka zbritje."""
    if not old_price or old_price <= price or old_price <= 0:
        return 0
    return round((old_price - price) / old_price * 100)


# ===== ORDERS: FAZA 1 (tracking, shënime) =====
def update_order_admin_fields(order_id: int, tracking_number: Optional[str] = None,
                              admin_notes: Optional[str] = None) -> bool:
    updates = {}
    if tracking_number is not None:
        updates['tracking_number'] = tracking_number.strip()
    if admin_notes is not None:
        updates['admin_notes'] = admin_notes.strip()
    if not updates:
        return False
    set_sql = ', '.join(f"{col} = ?" for col in updates)
    with _db() as conn:
        cur = conn.execute(f"UPDATE orders SET {set_sql} WHERE id = ?", (*updates.values(), order_id))
        return cur.rowcount > 0


# ===== MESSAGES (Inbox i Kontaktit) =====
def create_message(name: str, message: str, email: str = '', phone: str = '') -> int:
    name, message = name.strip(), message.strip()
    if not name or not message:
        raise ValueError("Emri dhe mesazhi janë të detyrueshëm.")
    with _db() as conn:
        cur = conn.execute(
            "INSERT INTO messages (name, email, phone, message) VALUES (?, ?, ?, ?)",
            (name, email.strip().lower(), phone.strip(), message)
        )
        return cur.lastrowid


def get_all_messages(status: Optional[str] = None) -> List[Dict]:
    with _db() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM messages WHERE status = ? ORDER BY created_at DESC, id DESC", (status,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM messages ORDER BY created_at DESC, id DESC").fetchall()
        return [dict(r) for r in rows]


def update_message_status(message_id: int, status: str) -> bool:
    if status not in MESSAGE_STATUSES:
        raise ValueError(f"Status i pavlefshëm: {status}")
    with _db() as conn:
        cur = conn.execute("UPDATE messages SET status = ? WHERE id = ?", (status, message_id))
        return cur.rowcount > 0


def count_unread_messages() -> int:
    with _db() as conn:
        return conn.execute("SELECT COUNT(*) FROM messages WHERE status = 'I Palexuar'").fetchone()[0]


# ===== TESTIMONIALS (vlerësimet e klientëve) =====
def create_testimonial(customer_name: str, text: str, rating: int = 5, city: str = '') -> int:
    customer_name, text = customer_name.strip(), text.strip()
    if not customer_name or not text:
        raise ValueError("Emri dhe teksti i vlerësimit janë të detyrueshëm.")
    rating = int(rating)
    if not 1 <= rating <= 5:
        raise ValueError("Vlerësimi duhet të jetë nga 1 deri në 5 yje.")
    with _db() as conn:
        cur = conn.execute(
            "INSERT INTO testimonials (customer_name, city, text, rating) VALUES (?, ?, ?, ?)",
            (customer_name, city.strip(), text, rating)
        )
        return cur.lastrowid


def get_visible_testimonials(limit: int = 6) -> List[Dict]:
    with _db() as conn:
        rows = conn.execute(
            "SELECT * FROM testimonials WHERE is_visible = 1 ORDER BY created_at DESC, id DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_featured_products(limit: int = 4) -> List[Dict]:
    """Bestsellers për faqen kryesore; nëse admini s'ka shënuar asnjë, merr më të rejat."""
    featured = get_bestsellers(limit)
    if featured:
        return featured
    with _db() as conn:
        rows = conn.execute("SELECT * FROM products ORDER BY created_at DESC, id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]


def get_all_testimonials() -> List[Dict]:
    with _db() as conn:
        rows = conn.execute("SELECT * FROM testimonials ORDER BY created_at DESC, id DESC").fetchall()
        return [dict(r) for r in rows]


def set_testimonial_visibility(testimonial_id: int, visible: bool) -> bool:
    with _db() as conn:
        cur = conn.execute("UPDATE testimonials SET is_visible = ? WHERE id = ?", (int(bool(visible)), testimonial_id))
        return cur.rowcount > 0


def delete_testimonial(testimonial_id: int) -> bool:
    with _db() as conn:
        cur = conn.execute("DELETE FROM testimonials WHERE id = ?", (testimonial_id,))
        return cur.rowcount > 0


def change_order_status(order_id: int, new_status: str) -> bool:
    """Ndryshon statusin. Kur porosia anulohet, stoku kthehet; kur riaktivizohet, zbritet sërish."""
    if new_status not in ORDER_STATUSES:
        raise ValueError(f"Status i pavlefshëm: {new_status}")
    order = get_order_by_id(order_id)
    if not order:
        return False
    was_cancelled = order.get('status') == 'E Anuluar'
    is_cancelled = new_status == 'E Anuluar'
    if was_cancelled != is_cancelled:
        try:
            items = json.loads(order.get('items_json') or '[]')
        except json.JSONDecodeError:
            items = []
        with _db() as conn:
            for item in items:
                if item.get('product_id'):
                    change = int(item.get('qty', 0)) * (1 if is_cancelled else -1)
                    conn.execute(
                        "UPDATE products SET stock_qty = MAX(stock_qty + ?, 0) WHERE id = ?",
                        (change, item['product_id'])
                    )
    return update_order_status(order_id, new_status)


# ===== STORE SETTINGS =====
def get_setting(key: str, default: str = '') -> str:
    with _db() as conn:
        row = conn.execute("SELECT value FROM store_settings WHERE key = ?", (key,)).fetchone()
        return row['value'] if row else default


def get_all_settings() -> Dict[str, str]:
    with _db() as conn:
        rows = conn.execute("SELECT key, value FROM store_settings").fetchall()
        return {r['key']: r['value'] for r in rows}


def set_setting(key: str, value: str) -> None:
    with _db() as conn:
        conn.execute(
            "INSERT INTO store_settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, str(value).strip())
        )


if __name__ == '__main__':
    init_database()
