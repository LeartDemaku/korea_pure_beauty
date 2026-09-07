# Korea Pure Beauty

A full-stack e-commerce and inventory management system designed specifically for authenticated Korean skincare products. Built with Python and Streamlit, the application features an isolated dual-portal architecture: a dedicated customer storefront (`client_app.py`) and a restricted management dashboard (`app.py`), backed by a local SQLite database, custom authentication with SMTP email verification, and an adaptive luxury UI engine.

---

## Architecture Overview

The system is designed with a strict separation of concerns between client browsing and backend administration:

```
                      +------------------------------------------+
                      |         Korea Pure Beauty System         |
                      +--------------------+---------------------+
                                           |
                  +------------------------+------------------------+
                  |                                                 |
       Port 8502 (Storefront)                            Port 8501 (Admin)
       [client_app.py]                                   [app.py]
       - Product Catalog & Filters                       - Product CRUD (Drag & Drop)
       - Shopping Cart & Checkout                        - Order Pipeline Management
       - Client Account & OTP Verification               - Inventory Metrics & Stock Alerts
       - Responsive UI & Zoom Viewer                     - Restricted Admin Access
                  |                                                 |
                  +------------------------+------------------------+
                                           |
                 +-------------------------+-------------------------+
                 |                         |                         |
          [database.py]               [auth.py]             [email_service.py]
          - SQLite Data Store         - PBKDF2 Hashing      - SMTP TLS Engine
          - Product & Order Models    - Salted Passwords    - HTML Templates
          - PRAGMA Migrations         - 6-Digit OTPs        - Verification / Receipts
```

### Dual-Port Isolation
- **Customer Storefront (`client_app.py` on port 8502)**: Optimized for shoppers. Allows guest browsing, multi-criteria filtering, cart management, checkout with local delivery data, and email verification.
- **Admin Dashboard (`app.py` on port 8501)**: Password-protected control panel for inventory stocking, image uploads, price adjustments, and customer order fulfillment tracking.

---

## How the Application Was Built (Development Lifecycle)

The project was developed in six distinct phases, prioritizing security, data integrity, and a premium visual experience.

### Phase 1: Database Architecture & Schema Migrations
- **Engine**: SQLite3 with `sqlite3.Row` factory for dictionary-like record access.
- **Tables**:
  - `products`: Tracks product names, brands, categories (Cleanser, Toner, Serum, Moisturizer, SPF, Masks), skin type suitability, prices, EU CPNP compliance flags, and image paths.
  - `users`: Manages authentication credentials, user roles (`admin` vs `client`), email addresses, verification status, and one-time registration codes.
  - `orders`: Records customer checkout submissions, delivery addresses, telephone numbers, order totals, itemized JSON manifests, and status tags (`E Re (Në Pritje)`, `Dërguar`, `Dorëzuar`).
- **Resilient Migrations**: Implemented non-destructive schema checks using `PRAGMA table_info` to ensure smooth database updates without dropping tables or losing historical data.

### Phase 2: Authentication & Security Pipeline
- **Password Security**: Uses salted SHA-256 (`hashlib.pbkdf2_hmac` / `hashlib.sha256`) with distinct hexadecimal salts per user rather than plaintext storage.
- **Email OTP Verification**: Integrated a 6-digit numeric verification code workflow for new client registrations. Codes are hashed in the database and validated before account activation.
- **Role Guarding**: Client sessions cannot elevate privileges or access administrative controls. The admin interface enforces role checks on every rerun cycle.
- **Session Continuity**: Uses Streamlit query parameter synchronization to persist sessions safely across page refreshes without re-prompting for credentials.

### Phase 3: Customer Storefront (`client_app.py`)
- **Faceted Search & Filtering**: Multi-parameter querying allows users to filter products simultaneously by keyword, category, and specific skin types (Dry, Oily, Sensitive, Acne-prone, Combination).
- **Interactive HD Zoom**: Custom JavaScript hover/touch zoom viewer enabling customers to inspect product packaging, ingredient lists, and authenticity marks at high resolution.
- **Shopping Cart State**: Dynamic in-memory cart with quantity controls, subtotal calculations, and item counts stored within `st.session_state`.
- **Cart Feedback**: Built a custom DOM notification engine displaying flying particle animations and animated toasts whenever an item is added to the cart.

### Phase 4: Administrative Operations (`app.py`)
- **Product Management**: Interface for adding new products via drag-and-drop file uploaders, automatic image sanitization into the `uploads/` directory, and real-time edits to existing catalogue entries.
- **Order Pipeline**: Order board displaying incoming orders, total revenues, delivery contacts, and inline status modification buttons (e.g., mark as Dispatched or Delivered).
- **Inventory Reporting**: Real-time metrics highlighting total inventory count, low-stock items, total order volume, and registered user metrics.

### Phase 5: Transactional Email Notifications (`email_service.py`)
- **SMTP Protocol**: Configured through Python's standard `smtplib` and `email.mime` modules using TLS encryption (port 587).
- **Responsive HTML Templates**: Styled transactional emails for verification codes, password resets, and purchase confirmations featuring official brand headers and clean typographic styling.
- **Offline / Development Fallback**: When external SMTP credentials are not yet configured in `.env`, the system automatically surfaces generated test codes directly in the local interface so development and testing proceed without interruptions.

### Phase 6: Luxury UI Design System & Desktop Integration
- **Adaptive Theming**: Custom CSS engine coupled with a lightweight JavaScript observer that tracks Streamlit's theme changes in the parent DOM. It automatically applies CSS `light-dark()` tokens and data-theme attributes so typography, cards, and borders match seamlessly in both Light and Dark modes.
- **Brand Assets**: Custom rose-gold metallic palette (`#ff758c`, `#d49b82`, `#11121c`), high-resolution transparent hero banners, circular badges, and SVG/PNG favicons.
- **Desktop Launcher**: Included Windows shortcut creator (`Krijo_Ikone_Desktop.py`), VBScript launcher (`launch_client.vbs`), and batch launchers (`launch_client.bat`, `Hap_Admin.bat`) that assign a multi-resolution `.ico` file to the Windows desktop shortcut.

---

## Tech Stack

| Component | Technology | Rationale |
| :--- | :--- | :--- |
| **Language** | Python 3.10+ | Clean syntax, robust standard library, rapid iteration. |
| **Framework** | Streamlit | Fast web interface prototyping with reactive state management. |
| **Database** | SQLite3 | Zero-configuration, serverless, file-backed data store with ACID compliance. |
| **Styling** | Custom CSS3 + JavaScript | Advanced responsive layouts, adaptive theme tokens, DOM injection. |
| **Imaging** | Pillow (PIL) | Dynamic asset cropping, Lanczos resampling, multi-size `.ico` generation. |
| **Security** | Python `hashlib` & `secrets` | Cryptographically secure random tokens and salted password hashing. |
| **Mailing** | `smtplib` / `email.mime` | Native SMTP protocol handler with TLS support. |
| **OS Automation** | `pywin32` (WScript.Shell) | Windows desktop shortcut and shell integration. |

---

## Project Structure

```
korea_pure_beauty/
│
├── app.py                     # Administrative dashboard & inventory portal
├── client_app.py              # Customer-facing storefront and checkout
├── database.py                # Database initialization, queries, and migrations
├── auth.py                    # Password hashing, user authentication, and OTP logic
├── email_service.py           # SMTP mailer and HTML email templates
│
├── assets/                    # Optimized brand identity assets
│   ├── logo.png               # Official transparent brand logo
│   ├── banner.png             # Full-width luxury product banner
│   ├── favicon_badge.png      # High-resolution browser tab icon
│   ├── favicon.ico            # Standard multi-resolution favicon
│   └── app_icon.ico           # Windows application desktop icon
│
├── uploads/                   # Local storage for uploaded product images
├── korea_beauty.db            # SQLite database file (gitignored)
├── .env                       # Secret environment variables (gitignored)
├── .env.example               # Template for environment variables
├── .gitignore                 # Exclusion rules for secrets, cache, and db files
│
├── Hap_Admin.bat              # Batch launcher for Admin panel (Port 8501)
├── launch_client.bat          # Batch launcher for Client storefront (Port 8502)
├── launch_client.vbs          # Silent background launcher for client store
└── Krijo_Ikone_Desktop.py     # Script to generate a desktop shortcut with brand icon
```

---

## Setup and Installation

### 1. Prerequisites
- Python 3.10 or higher installed on your system.
- Git installed.

### 2. Clone the Repository
```bash
git clone https://github.com/LeartDemaku/korea_pure_beauty.git
cd korea_pure_beauty
```

### 3. Create a Virtual Environment
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install streamlit pandas pillow pywin32
```

### 5. Environment Configuration
Create a `.env` file in the project root (you can reference `.env.example`):
```ini
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_gmail_app_password
SMTP_FROM_NAME=Korea Pure Beauty
```
> **Note**: If SMTP credentials are not provided, the application will automatically fall back to local test mode, allowing full functionality and printing OTP codes directly to the UI.

---

## Running the Applications

### Customer Storefront (Port 8502)
```bash
python -m streamlit run client_app.py --server.port 8502
```
Or simply double-click **`launch_client.bat`** (or use the created Desktop shortcut).

### Admin Management Panel (Port 8501)
```bash
python -m streamlit run app.py --server.port 8501
```
Or double-click **`Hap_Admin.bat`**.

---

## Security Notes
- The `.env` file containing SMTP passwords and credentials is strictly excluded from version control via `.gitignore`.
- Database files (`korea_beauty.db`, `*.sqlite`) and local product uploads (`uploads/*`) are excluded from public commits to safeguard production data.
- Passwords are never stored in plain text; all authentication runs through salted PBKDF2 hashing routines.

---

## License
This project is proprietary and maintained for **Korea Pure Beauty**. All brand assets, product images, and documentation are reserved.