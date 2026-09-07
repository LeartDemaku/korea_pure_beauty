# email_service.py
import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

# Ngarko të dhënat nga skedari .env
load_dotenv(override=True)

def get_smtp_config():
    """Rikthen konfigurimin aktual të SMTP nga variablat e mjedisit."""
    load_dotenv(override=True)
    return {
        "server": os.getenv("SMTP_SERVER", "smtp.gmail.com").strip(),
        "port": int(os.getenv("SMTP_PORT", "587")),
        "user": os.getenv("SMTP_USER", "").strip(),
        "password": os.getenv("SMTP_PASSWORD", "").strip(),
        "from_name": os.getenv("SMTP_FROM_NAME", "Korea Pure Beauty").strip()
    }

def is_smtp_configured() -> bool:
    """Kontrollon nëse kredencialet SMTP janë të plotësuara në .env."""
    config = get_smtp_config()
    return bool(config["user"] and config["password"])

def send_verification_email(to_email: str, client_name: str, code: str) -> tuple[bool, str]:
    """
    Dërgon kodin 6-shifror të verifikimit në email-in e klientit.
    Kthen (True, 'Mesazhi') në rast suksesi, ose (False, 'Arsyeja') në rast dështimi.
    """
    to_email = to_email.strip()
    client_name = client_name.strip() if client_name else "Klient"

    config = get_smtp_config()
    if not is_smtp_configured():
        return False, "Kredencialet e email-it nuk janë konfiguruar ende në skedarin .env."

    try:
        msg = EmailMessage()
        msg['Subject'] = f"🌸 Kodi juaj i Verifikimit: {code} - Korea Pure Beauty"
        msg['From'] = f"{config['from_name']} <{config['user']}>"
        msg['To'] = to_email

        # Përmbajtja me tekst të thjeshtë (fallback)
        plain_content = f"""Përshëndetje {client_name},

Faleminderit që u regjistruat në Korea Pure Beauty!
Kodi juaj i verifikimit për aktivizimin e llogarisë është:

{code}

Vendoseni këtë kod në faqen e dyqanit për të përfunduar regjistrimin tuaj.

Me respekt,
Ekipi i Korea Pure Beauty
"""
        msg.set_content(plain_content)

        # Përmbajtja e pasur me HTML
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #faf6f8;
            margin: 0;
            padding: 30px 10px;
            color: #1e293b;
        }}
        .email-container {{
            max-width: 520px;
            margin: 0 auto;
            background: #ffffff;
            border-radius: 18px;
            overflow: hidden;
            box-shadow: 0 10px 25px rgba(255, 117, 140, 0.12);
            border: 1px solid #ffd5dc;
        }}
        .header {{
            background: linear-gradient(135deg, #ff758c 0%, #ff7eb3 50%, #7928ca 100%);
            padding: 30px 20px;
            text-align: center;
            color: #ffffff;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
            font-weight: 800;
            letter-spacing: 0.5px;
        }}
        .header p {{
            margin: 6px 0 0 0;
            font-size: 13px;
            opacity: 0.95;
        }}
        .content {{
            padding: 30px 25px;
            text-align: center;
        }}
        .greeting {{
            font-size: 18px;
            font-weight: 700;
            color: #0f172a;
            margin-bottom: 12px;
        }}
        .desc {{
            font-size: 14px;
            color: #475569;
            line-height: 1.6;
            margin-bottom: 25px;
        }}
        .code-box {{
            background: #fff0f3;
            border: 2px dashed #ff758c;
            border-radius: 14px;
            padding: 16px 20px;
            font-size: 32px;
            font-weight: 800;
            letter-spacing: 8px;
            color: #ff758c;
            display: inline-block;
            margin: 0 auto 25px auto;
        }}
        .notice {{
            font-size: 12px;
            color: #94a3b8;
            margin-top: 20px;
            border-top: 1px solid #f1f5f9;
            padding-top: 18px;
        }}
        .footer {{
            background: #f8fafc;
            padding: 16px;
            text-align: center;
            font-size: 11px;
            color: #94a3b8;
            border-top: 1px solid #e2e8f0;
        }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <h1>🌸 Korea Pure Beauty</h1>
            <p>Dyqani Zyrtar për Kujdesin ndaj Lëkurës Koreane</p>
        </div>
        <div class="content">
            <div class="greeting">Përshëndetje, {client_name}! ✨</div>
            <div class="desc">
                Faleminderit për zgjedhjen e <strong>Korea Pure Beauty</strong>. Për të aktivizuar llogarinë tuaj dhe për të filluar blerjet e produkteve 100% origjinale, ju lutem përdorni kodin e mëposhtëm të verifikimit:
            </div>
            <div class="code-box">{code}</div>
            <div class="desc" style="font-size: 13px; margin-bottom: 10px;">
                Vendoseni këtë kod në fushën e verifikimit në faqen e dyqanit.
            </div>
            <div class="notice">
                Nëse nuk e keni kërkuar ju këtë regjistrim, ju lutem injorojeni këtë email.
            </div>
        </div>
        <div class="footer">
            © 2026 Korea Pure Beauty | Të gjitha të drejtat e rezervuara.
        </div>
    </div>
</body>
</html>
"""
        msg.add_alternative(html_content, subtype='html')

        # Dërgimi me SMTP
        port = config["port"]
        if port == 465:
            with smtplib.SMTP_SSL(config["server"], port, timeout=12) as server:
                server.login(config["user"], config["password"])
                server.send_message(msg)
        else:
            with smtplib.SMTP(config["server"], port, timeout=12) as server:
                server.starttls()
                server.login(config["user"], config["password"])
                server.send_message(msg)

        return True, "Kodi i verifikimit u dërgua me sukses në email!"

    except smtplib.SMTPAuthenticationError:
        return False, "Dështoi autentifikimi me serverin e email-it. Ju lutem kontrolloni fjalëkalimin e aplikacionit (App Password) te skedari .env."
    except Exception as e:
        return False, f"Gabim gjatë dërgimit të email-it: {str(e)}"

def send_password_reset_email(to_email: str, client_name: str, code: str) -> tuple[bool, str]:
    """
    Dërgon kodin 6-shifror për ndërrimin/rivendosjen e fjalëkalimit në email.
    """
    to_email = to_email.strip()
    client_name = client_name.strip() if client_name else "Përdorues"

    config = get_smtp_config()
    if not is_smtp_configured():
        return False, "Kredencialet e email-it nuk janë konfiguruar ende në skedarin .env."

    try:
        msg = EmailMessage()
        msg['Subject'] = f"🔐 Kodi për Rivendosjen e Fjalëkalimit: {code} - Korea Pure Beauty"
        msg['From'] = f"{config['from_name']} <{config['user']}>"
        msg['To'] = to_email

        plain_content = f"""Përshëndetje {client_name},

Keni kërkuar ndërrimin e fjalëkalimit për llogarinë tuaj në Korea Pure Beauty.
Kodi juaj i sigurisë është:

{code}

Vendoseni këtë kod në fushën përkatëse për të caktuar fjalëkalimin tuaj të ri.
Nëse nuk e keni kërkuar ju këtë veprim, llogaria juaj është e sigurt dhe mund ta injoroni këtë email.

Me respekt,
Ekipi i Korea Pure Beauty
"""
        msg.set_content(plain_content)

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #faf6f8;
            margin: 0;
            padding: 30px 10px;
            color: #1e293b;
        }}
        .email-container {{
            max-width: 520px;
            margin: 0 auto;
            background: #ffffff;
            border-radius: 18px;
            overflow: hidden;
            box-shadow: 0 10px 25px rgba(255, 117, 140, 0.12);
            border: 1px solid #ffd5dc;
        }}
        .header {{
            background: linear-gradient(135deg, #ff758c 0%, #ff7eb3 50%, #7928ca 100%);
            padding: 30px 20px;
            text-align: center;
            color: #ffffff;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
            font-weight: 800;
        }}
        .header p {{
            margin: 6px 0 0 0;
            font-size: 13px;
            opacity: 0.95;
        }}
        .content {{
            padding: 30px 25px;
            text-align: center;
        }}
        .greeting {{
            font-size: 18px;
            font-weight: 700;
            color: #0f172a;
            margin-bottom: 12px;
        }}
        .desc {{
            font-size: 14px;
            color: #475569;
            line-height: 1.6;
            margin-bottom: 25px;
        }}
        .code-box {{
            background: #fff0f3;
            border: 2px dashed #ff758c;
            border-radius: 14px;
            padding: 16px 20px;
            font-size: 32px;
            font-weight: 800;
            letter-spacing: 8px;
            color: #ff758c;
            display: inline-block;
            margin: 0 auto 25px auto;
        }}
        .notice {{
            font-size: 12px;
            color: #94a3b8;
            margin-top: 20px;
            border-top: 1px solid #f1f5f9;
            padding-top: 18px;
        }}
        .footer {{
            background: #f8fafc;
            padding: 16px;
            text-align: center;
            font-size: 11px;
            color: #94a3b8;
            border-top: 1px solid #e2e8f0;
        }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <h1>🌸 Korea Pure Beauty</h1>
            <p>Rivendosja e Fjalëkalimit</p>
        </div>
        <div class="content">
            <div class="greeting">Përshëndetje, {client_name}! 🔐</div>
            <div class="desc">
                Kemi marrë një kërkesë për të ndërruar fjalëkalimin e llogarisë tuaj. Kodi juaj 6-shifror i konfirmimit është:
            </div>
            <div class="code-box">{code}</div>
            <div class="desc" style="font-size: 13px; margin-bottom: 10px;">
                Shkruani këtë kod së bashku me fjalëkalimin tuaj të ri në faqen e dyqanit.
            </div>
            <div class="notice">
                Nëse nuk e keni kërkuar ju këtë ndryshim, llogaria juaj mbetet e pandryshuar dhe e sigurt.
            </div>
        </div>
        <div class="footer">
            © 2026 Korea Pure Beauty | Të gjitha të drejtat e rezervuara.
        </div>
    </div>
</body>
</html>
"""
        msg.add_alternative(html_content, subtype='html')

        port = config["port"]
        if port == 465:
            with smtplib.SMTP_SSL(config["server"], port, timeout=12) as server:
                server.login(config["user"], config["password"])
                server.send_message(msg)
        else:
            with smtplib.SMTP(config["server"], port, timeout=12) as server:
                server.starttls()
                server.login(config["user"], config["password"])
                server.send_message(msg)

        return True, "Kodi për rivendosjen e fjalëkalimit u dërgua me sukses në email!"

    except smtplib.SMTPAuthenticationError:
        return False, "Dështoi autentifikimi me serverin e email-it. Ju lutem kontrolloni fjalëkalimin e aplikacionit te .env."
    except Exception as e:
        return False, f"Gabim gjatë dërgimit të email-it: {str(e)}"

