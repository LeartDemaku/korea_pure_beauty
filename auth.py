# auth.py
import re
import random
import bcrypt
import database
import email_service

def hash_password(plain_password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(plain_password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def is_valid_email(email: str) -> bool:
    """Verifikon nëse formati i email-it është i vlefshëm."""
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return bool(re.match(pattern, email.strip()))

def generate_verification_code() -> str:
    """Gjeneron një kod 6-shifror të rastësishëm."""
    return f"{random.randint(100000, 999999)}"

def register_client(full_name: str, email: str, password: str, confirm_password: str) -> tuple[bool, str, str]:
    """
    Regjistron një klient të ri me hapat e kërkuar:
    1. Emri dhe Mbiemri
    2. Email
    3. Password
    4. Konfirmo Password
    Gjeneron dhe dërgon kodin 6-shifror në email.
    Kthen (sukses, mesazh, kodi_i_gjeneruar).
    """
    full_name = full_name.strip()
    email = email.strip().lower()
    password = password.strip()
    confirm_password = confirm_password.strip()

    if not full_name:
        return False, "Ju lutem shkruani Emrin dhe Mbiemrin.", ""
    if not email:
        return False, "Ju lutem shkruani adresën tuaj të email-it.", ""
    if not is_valid_email(email):
        return False, "Formati i email-it nuk është i saktë (p.sh. emri@gmail.com).", ""
    if not password:
        return False, "Ju lutem shkruani fjalëkalimin.", ""
    if len(password) < 6:
        return False, "Fjalëkalimi duhet të ketë të paktën 6 karaktere.", ""
    if password != confirm_password:
        return False, "Fjalëkalimet nuk përputhen! Ju lutem rishkruajini me kujdes.", ""

    # Kontrollo nëse ekziston përdoruesi
    existing_user = database.get_user_by_email(email)
    code = generate_verification_code()
    hashed = hash_password(password)

    if existing_user:
        if existing_user.get('is_verified', 1) == 1:
            return False, "Një llogari me këtë email ekziston tashmë! Mund të kyçeni te 'Hyr në Llogari'.", ""
        else:
            # Përdoruesi ekziston por nuk është verifikuar ende -> përditësojmë fjalëkalimin dhe kodin
            conn = database.get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    UPDATE users 
                    SET full_name = ?, password_hash = ?, verification_code = ?
                    WHERE id = ?
                ''', (full_name, hashed, code, existing_user['id']))
                conn.commit()
            finally:
                conn.close()
    else:
        database.create_client_user(full_name=full_name, email=email, password_hash=hashed, verification_code=code)

    # Dërgimi i email-it
    email_sent, email_msg = email_service.send_verification_email(email, full_name, code)
    if email_sent:
        return True, "Kodi i verifikimit iu dërgua me sukses në email!", code
    else:
        # Nëse konfigurimi SMTP mungon në .env ose dështon, njoftojmë por e kthejmë kodin për lehtësi testimi
        return True, f"Llogaria u krijua! ({email_msg})", code

def verify_client_code(email: str, code: str) -> tuple[bool, str]:
    """Verifikon kodin dhe aktivizon llogarinë."""
    return database.verify_user_code(email, code)

def resend_client_code(email: str) -> tuple[bool, str, str]:
    """Ridërgon një kod të ri verifikimi në email."""
    email = email.strip().lower()
    user = database.get_user_by_email(email)
    if not user:
        return False, "Ky email nuk u gjet.", ""
    
    new_code = generate_verification_code()
    database.update_user_verification_code(email, new_code)

    name = user.get('full_name') or "Klient"
    sent, msg = email_service.send_verification_email(email, name, new_code)
    return sent, msg, new_code

def register_user(username: str, password: str, role: str = 'client') -> tuple[bool, str]:
    """Regjistrim bazë/admin (përputhshmëri me app.py)."""
    username = username.strip()
    password = password.strip()

    if not username or not password:
        return False, "Plotësoni username dhe fjalëkalimin."
    if len(password) < 4:
        return False, "Fjalëkalimi duhet të ketë të paktën 4 karaktere."

    if database.get_user_by_username(username):
        return False, "Ky emër përdoruesi ekziston tashmë!"

    hashed = hash_password(password)
    database.create_user(username=username, password_hash=hashed, role=role, is_verified=1)
    return True, "Llogaria u krijua me sukses!"

def login_user(identifier: str, password: str) -> tuple[bool, dict | str]:
    """
    Hyrje në llogari me Email OSE Username.
    Kontrollon gjithashtu nëse llogaria është verifikuar.
    """
    identifier = identifier.strip()
    password = password.strip()

    if not identifier or not password:
        return False, "Plotësoni të gjitha fushat."

    user = database.get_user_by_identifier(identifier)
    if not user:
        return False, "Nuk u gjet asnjë llogari me këtë email/username."

    if not verify_password(password, user['password_hash']):
        return False, "Fjalëkalimi është i pasaktë."

    # Kontrollo nëse llogaria është e verifikuar
    if user.get('is_verified', 1) == 0:
        return False, f"UNVERIFIED:{user['email']}"

    return True, user

def change_password_with_current(identifier: str, old_password: str, new_password: str, confirm_password: str) -> tuple[bool, str]:
    """Ndryshon fjalëkalimin duke verifikuar fjalëkalimin aktual."""
    identifier = identifier.strip()
    old_password = old_password.strip()
    new_password = new_password.strip()
    confirm_password = confirm_password.strip()

    if not identifier or not old_password or not new_password or not confirm_password:
        return False, "Ju lutem plotësoni të gjitha fushat."

    if len(new_password) < 6:
        return False, "Fjalëkalimi i ri duhet të ketë të paktën 6 karaktere."

    if new_password != confirm_password:
        return False, "Fjalëkalimet e reja nuk përputhen!"

    user = database.get_user_by_identifier(identifier)
    if not user:
        return False, "Përdoruesi nuk u gjet."

    if not verify_password(old_password, user['password_hash']):
        return False, "Fjalëkalimi aktual është i pasaktë."

    new_hash = hash_password(new_password)
    database.update_user_password(user['id'], new_hash)
    return True, "Fjalëkalimi u ndryshua me sukses! Tani mund të kyçeni me fjalëkalimin e ri."

def request_password_reset_code(identifier: str) -> tuple[bool, str, str, str]:
    """
    Gjeneron dhe dërgon kodin e rivendosjes së fjalëkalimit në email.
    Kthen (sukses, mesazh, email, code).
    """
    identifier = identifier.strip()
    if not identifier:
        return False, "Ju lutem shkruani email-in ose username-in tuaj.", "", ""

    code = generate_verification_code()
    success, msg, user = database.set_password_reset_code(identifier, code)
    if not success or not user:
        return False, msg, "", ""

    email = user.get('email')
    name = user.get('full_name') or user.get('username') or "Përdorues"

    sent, mail_msg = email_service.send_password_reset_email(email, name, code)
    if sent:
        return True, f"Kodi i sigurisë u dërgua me sukses te {email}!", email, code
    else:
        return True, f"Kodi u gjenerua! ({mail_msg})", email, code

def confirm_password_reset_code(identifier: str, code: str, new_password: str, confirm_password: str) -> tuple[bool, str]:
    """Verifikon kodin dhe cakton fjalëkalimin e ri."""
    identifier = identifier.strip()
    code = code.strip()
    new_password = new_password.strip()
    confirm_password = confirm_password.strip()

    if not identifier or not code or not new_password or not confirm_password:
        return False, "Ju lutem plotësoni të gjitha fushat."

    if len(new_password) < 6:
        return False, "Fjalëkalimi i ri duhet të ketë të paktën 6 karaktere."

    if new_password != confirm_password:
        return False, "Fjalëkalimet e reja nuk përputhen!"

    new_hash = hash_password(new_password)
    return database.reset_password_with_code(identifier, code, new_hash)