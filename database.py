# database.py
import sqlite3
import json
from typing import Optional, List, Dict

DATABASE_PATH = 'korea_beauty.db'

def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

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

# ===== PRODUCTS =====
def create_product(name: str, brand: str, category: str, skin_type: str,
                   price: float, description: str = '', eu_certified: bool = True,
                   is_original: bool = True, image_url: str = '') -> int:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO products (name, brand, category, skin_type, price, description, eu_certified, is_original, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, brand, category, skin_type, price, description, eu_certified, is_original, image_url))
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
def create_order(buyer_name: str, phone: str, city: str, address: str, items: list, total_price: float) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        items_str = json.dumps(items)
        cursor.execute('''
            INSERT INTO orders (buyer_name, phone, city, address, items_json, total_price)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (buyer_name, phone, city, address, items_str, total_price))
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

if __name__ == '__main__':
    init_database()