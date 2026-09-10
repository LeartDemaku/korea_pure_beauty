# email_service.py
import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

# Ngarko të dhënat nga skedari .env
load_dotenv(override=True)

def get_smtp_config():
    """Rikthen konfigurimin aktual të SMTP nga variablat e mjedisit ose secrets."""
    load_dotenv(override=True)
    user = os.getenv("SMTP_USER", "").strip() or "leart.demaku2006@gmail.com"
    password = os.getenv("SMTP_PASSWORD", "").strip() or "lbmp fusa okut hgfi"
    return {
        "server": os.getenv("SMTP_SERVER", "smtp.gmail.com").strip(),
        "port": int(os.getenv("SMTP_PORT", "587")),
        "user": user,
        "password": password,
        "from_name": os.getenv("SMTP_FROM_NAME", "Korea Pure Beauty").strip()
    }

def is_smtp_configured() -> bool:
    """Kontrollon nëse kredencialet SMTP janë të plotësuara."""
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


def send_order_notification_email(order_id: int, buyer_name: str, phone: str, city: str, address: str, items: list, total_price: float, to_admin_email: str = "leart.demaku2006@gmail.com") -> tuple[bool, str]:
    """
    Dërgon njoftimin e plotë të porosisë në email-in e administratorit.
    """
    config = get_smtp_config()
    if not is_smtp_configured():
        return False, "Kredencialet SMTP nuk janë konfiguruar."

    try:
        msg = EmailMessage()
        msg['Subject'] = f"🛍️ Porosi e Re #{order_id} nga {buyer_name} (€{total_price:.2f}) - Korea Pure Beauty"
        msg['From'] = f"{config['from_name']} <{config['user']}>"
        msg['To'] = to_admin_email

        items_text = ""
        items_html = ""
        for itm in items:
            sub = itm.get('price', 0) * itm.get('qty', 1)
            brand_str = f"({itm.get('brand')}) " if itm.get('brand') else ""
            items_text += f"- {itm.get('name')} {brand_str}x{itm.get('qty', 1)}: €{sub:.2f}\n"
            items_html += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #f1f5f9; font-weight: 600; color: #1e293b;">{itm.get('name')}<br><small style="color: #ff758c; font-weight: 700;">{itm.get('brand', '')}</small></td>
                <td style="padding: 10px; border-bottom: 1px solid #f1f5f9; text-align: center; color: #64748b; font-weight: 700;">{itm.get('qty', 1)}x</td>
                <td style="padding: 10px; border-bottom: 1px solid #f1f5f9; text-align: right; font-weight: 700; color: #1e293b;">€{sub:.2f}</td>
            </tr>
            """

        plain_content = f"""🌸 POROSI E RE #{order_id} NË KOREA PURE BEAUTY!

👤 TË DHËNAT E BLERËSIT:
- Emri dhe Mbiemri: {buyer_name}
- Numri i Telefonit: {phone}
- Qyteti: {city}
- Adresa e Plotë: {address}

🛍️ PRODUKTET E POROSITURA:
{items_text}
TOTALI: €{total_price:.2f}

Hapni Panelin e Administratorit për të parë detajet ose për të kontaktuar klientin.
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
            max-width: 560px;
            margin: 0 auto;
            background: #ffffff;
            border-radius: 18px;
            overflow: hidden;
            box-shadow: 0 10px 25px rgba(255, 117, 140, 0.12);
            border: 1px solid #ffd5dc;
        }}
        .header {{
            background: linear-gradient(135deg, #ff758c 0%, #ff7eb3 50%, #7928ca 100%);
            padding: 26px 20px;
            text-align: center;
            color: #ffffff;
        }}
        .content {{
            padding: 25px 24px;
        }}
        .box {{
            background: #fff5f7;
            border: 1px solid #ffd1dc;
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 20px;
        }}
        .table-items {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }}
        .total-box {{
            font-size: 20px;
            font-weight: 800;
            color: #ff758c;
            text-align: right;
            margin-top: 15px;
            padding-top: 15px;
            border-top: 2px solid #ffd1dc;
        }}
        .footer {{
            background: #f8fafc;
            padding: 14px;
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
            <h1 style="margin: 0; font-size: 22px; font-weight: 800;">🌸 Porosi e Re #{order_id}!</h1>
            <p style="margin: 4px 0 0 0; font-size: 13px; opacity: 0.95;">Korea Pure Beauty — Dyqani Online</p>
        </div>
        <div class="content">
            <div class="box">
                <h3 style="margin: 0 0 10px 0; font-size: 15px; color: #ff758c;">📦 Të Dhënat e Dërgesës:</h3>
                <p style="margin: 4px 0; font-size: 14px;"><strong>Klienti:</strong> {buyer_name}</p>
                <p style="margin: 4px 0; font-size: 14px;"><strong>Telefoni:</strong> <a href="tel:{phone}" style="color: #2e86de; font-weight: 700;">{phone}</a></p>
                <p style="margin: 4px 0; font-size: 14px;"><strong>Qyteti:</strong> {city}</p>
                <p style="margin: 4px 0; font-size: 14px;"><strong>Adresa:</strong> {address}</p>
            </div>

            <h3 style="margin: 0 0 10px 0; font-size: 15px; color: #1e293b;">🛍️ Artikujt e Porositur:</h3>
            <table class="table-items">
                <thead>
                    <tr style="background: #f8fafc;">
                        <th style="padding: 8px 10px; text-align: left; font-size: 12px; color: #64748b; border-bottom: 2px solid #e2e8f0;">Produkti</th>
                        <th style="padding: 8px 10px; text-align: center; font-size: 12px; color: #64748b; border-bottom: 2px solid #e2e8f0;">Sasia</th>
                        <th style="padding: 8px 10px; text-align: right; font-size: 12px; color: #64748b; border-bottom: 2px solid #e2e8f0;">Çmimi</th>
                    </tr>
                </thead>
                <tbody>
                    {items_html}
                </tbody>
            </table>

            <div class="total-box">
                Totali i Porosisë: €{total_price:.2f}
            </div>
        </div>
        <div class="footer">
            Njoftim automatik nga sistemi i Korea Pure Beauty.
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

        return True, "Email-i i njoftimit për porosinë u dërgua me sukses te administratori!"

    except Exception as e:
        return False, f"Dështoi dërgimi i email-it: {str(e)}"


