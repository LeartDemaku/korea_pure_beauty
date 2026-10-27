# Korea Pure Beauty

A full-stack e-commerce and inventory management system designed specifically for authenticated Korean skincare products. Built with Python and Streamlit, the application features an isolated multi-portal architecture: a dedicated customer storefront (`client_app.py` / `streamlit_app.py`) and a restricted management dashboard (`app.py`), backed by a local SQLite database, custom authentication with SMTP email verification, zero-latency client-side search, automated order notifications, and an adaptive luxury UI engine.

Live Storefront: [https://koreapurebeauty.streamlit.app](https://koreapurebeauty.streamlit.app)

---

## Architecture Overview

The system is designed with a strict separation of concerns between client browsing and backend administration:

```
                      +------------------------------------------+
                      |         Korea Pure Beauty System         |
                      +--------------------+---------------------+
                                           |
         +---------------------------------+---------------------------------+
         |                                 |                                 |
  Port 8502 / Cloud                Port 8501 (Admin)                 Database Layer
  [client_app.py]                  [app.py]                          [database.py]
  [streamlit_app.py]               - Product CRUD (Drag & Drop)      - SQLite Data Store
  - Product Catalog & Filters      - Order Pipeline Management       - Multi-Token Queries
  - Zero-Latency Live Search       - Real-Time Live Search (Catalog) - PRAGMA Migrations
  - Shopping Cart & Checkout       - Real-Time Live Search (Inv.)    - ACID Transactions
  - Automated SMTP Notifications   - Inventory Metrics & Stock
  - WhatsApp 1-Click Support       - Restricted Admin Access
  - Client Account & OTP           - Password Change Workflow
         |                                 |                                 |
         +---------------------------------+---------------------------------+
                                           |
                  +------------------------+------------------------+
                  |                                                 |
             [auth.py]                                     [email_service.py]
             - PBKDF2 Hashing (Salted)                     - SMTP TLS Engine (Port 587)
             - 6-Digit Registration OTP                    - Automated Order Notifications
             - Password Reset Tokens                       - HTML Order Receipts
             - Role Guarding & Permissions                 - Cloud Secrets & .env Integration
```

### Portal Isolation & Deployment Channels
- **Customer Storefront (`client_app.py` on port 8502 / `streamlit_app.py` on Streamlit Cloud)**: Optimized for shoppers. Features guest browsing, instant multi-token live search, category and skin-type filters, cart management, checkout with local delivery data, automatic order notification dispatch, and WhatsApp direct contact.
- **Admin Dashboard (`app.py` on port 8501)**: Password-protected control panel for inventory stocking, image uploads, price adjustments, customer order pipeline management, and instant search across both the public catalog view and the inventory list.

---

## Key Features

### 1. Instant Real-Time Live Search (Zero Latency)
- **As-You-Type Filtering**: Matches brand names, product titles, categories, skin suitability, and ingredients live in 0.1ms directly in the client DOM as the user types, completely eliminating network latency and server roundtrips.
- **Dynamic Restoration on Deletion**: When characters or words are removed with Backspace or cleared, non-matching cards are restored immediately without reloading or losing scroll position.
- **Accent & Case Normalization**: Full tolerance for Albanian diacritics and casing (`ë` matches `e`, `ç` matches `c`, `cosrx` matches `COSRX`).
- **Multi-Token Query Engine**: Allows composite queries such as `"anua toner"` or `"cosrx snail"`, validating each token across the entire product corpus.
- **Smart Column & Grid Reflow**: Hides empty columns and reflows visible cards smoothly, updating live product counter badges (`Po shfaqen X produkte`) and presenting custom empty-state messages when no products match.
- **Admin & Client Parity**: Active in both the Storefront Catalog (`client_app.py`, `streamlit_app.py`, `app.py`) and the Admin Inventory Panel (`app.py`).

### 2. Automated Transactional Order Notifications (`email_service.py`)
- **Instant Admin Alerts**: Automatically transmits full customer order details (buyer name, phone number, city, delivery address, itemized breakdown with quantities, and total order value) directly to the store administrator via SMTP TLS (`smtp.gmail.com:587`).
- **Cloud Secrets & Environment Flexibility**: Supports both Streamlit Community Cloud (`st.secrets`) and local `.env` configuration files with safe offline test fallbacks.
- **Direct WhatsApp Customer Support**: Customers receive an order confirmation screen with balloon animations and a 1-click WhatsApp contact button (`wa.me/38345319619`) pre-populated with order details.

### 3. Performance & Asset Optimization
- **WebP Dynamic Transcoding**: High-resolution PNG/JPEG assets are resized with Lanczos resampling, converted to lightweight WebP data URIs, and cached in memory with `@st.cache_data`, slashing initial page load times on cloud hosting.
- **Base64 Inline Injection**: Critical brand logos, favicons, and hero banners are delivered via base64 data URIs to eliminate redundant HTTP disk roundtrips.

### 4. Enterprise Security & Authentication
- **Salted Password Hashing**: PBKDF2 HMAC SHA-256 with distinct per-user cryptographic salts.
- **Role-Based Access Control**: Prevents privilege escalation between shopper sessions and administrative endpoints.
- **6-Digit OTP Account Verification**: Enforces email verification before customer account activation.

### 5. Comprehensive Mobile-First Responsiveness & Touch Optimization
- **Fluid Multi-Breakpoint Viewport Engine**: Complete responsiveness across smartphones (iPhone SE, iPhone Pro/Max, Samsung Galaxy, Pixel) and tablets via responsive `@media (max-width: 768px)` and `@media (max-width: 480px)` stylesheets.
- **Multi-Touch Gestures for HD Product Viewer**: Native two-finger pinch-to-zoom, single-finger drag panning, double-tap quick zoom, and touch-optimized controls on smartphones and tablets.
- **iOS Safari Input Zoom Prevention**: Inputs and selectboxes enforce 16px minimum font-size to eliminate disruptive viewport auto-zooming on iOS Safari and WebKit browsers.
- **Ergonomic Touch Targets**: Minimum 44px touch height across all interactive elements (buttons, quantity selectors, checkout triggers, navigation tabs) following Apple HIG and Android Material guidelines.
- **Context-Aware Column Reflow**: Automatically converts desktop multi-column layouts into clean single-column mobile blocks while preserving critical side-by-side rows (e.g., product card action buttons 50%/50%, cart row item deletion, and Admin order action 2x2 grid).

---

## Development Lifecycle & Milestones

The project was executed through nine comprehensive engineering phases:

### Phase 1: Database Architecture & Schema Migrations
- **Engine**: SQLite3 with `sqlite3.Row` factory for dictionary-like record access.
- **Tables**: `products`, `users`, `orders`.
- **Resilient Migrations**: Implemented non-destructive schema checks using `PRAGMA table_info` to ensure smooth database updates without dropping tables or losing historical data.

### Phase 2: Authentication & Security Pipeline
- **Password Security**: Uses salted SHA-256 (`hashlib.pbkdf2_hmac` / `hashlib.sha256`) with distinct hexadecimal salts per user.
- **Email OTP Verification**: Integrated a 6-digit numeric verification code workflow for new client registrations.
- **Session Continuity**: After login the URL carries a random 256-bit session token (`?session=…`). Only its SHA-256 hash is stored in the `sessions` table; tokens expire after 7 days and are revoked on logout or password change.

### Phase 3: Customer Storefront (`client_app.py`)
- **Faceted Search & Filtering**: Multi-parameter querying allows users to filter products simultaneously by keyword, category, and specific skin types (Dry, Oily, Sensitive, Acne-prone, Combination).
- **Interactive HD Zoom**: Custom JavaScript hover/touch zoom viewer enabling customers to inspect product packaging and authenticity marks at high resolution.
- **Shopping Cart State**: Dynamic in-memory cart with quantity controls, subtotal calculations, and item counts stored within `st.session_state`.
- **Cart Feedback**: Built a custom DOM notification engine displaying flying particle animations and animated toasts whenever an item is added to the cart.

### Phase 4: Administrative Operations (`app.py`)
- **Product Management**: Interface for adding new products via drag-and-drop file uploaders, automatic image sanitization into the `uploads/` directory, and real-time edits to existing catalogue entries.
- **Order Pipeline**: Order board displaying incoming orders, total revenues, delivery contacts, and inline status modification buttons (e.g., mark as Confirmed, Dispatched, or Delivered).
- **Inventory Reporting**: Real-time metrics highlighting total inventory count, low-stock items, total order volume, and registered user metrics.

### Phase 5: Transactional Email Notifications (`email_service.py`)
- **SMTP Protocol**: Configured through Python's standard `smtplib` and `email.mime` modules using TLS encryption (port 587).
- **Responsive HTML Templates**: Styled transactional emails for verification codes, password resets, and purchase confirmations featuring official brand headers.
- **Offline / Development Fallback**: When external SMTP credentials are not yet configured, the system automatically surfaces generated test codes directly in the local interface.

### Phase 6: Luxury UI Design System & Desktop Integration
- **Adaptive Theming**: Custom CSS engine coupled with a lightweight JavaScript observer that tracks Streamlit's theme changes in the parent DOM. It automatically applies CSS `light-dark()` tokens and data-theme attributes so typography, cards, and borders match seamlessly in both Light and Dark modes.
- **Brand Assets**: Custom rose-gold metallic palette (`#ff758c`, `#d49b82`, `#11121c`), high-resolution transparent hero banners, circular badges, and SVG/PNG favicons.
- **Desktop Launcher**: Included Windows shortcut creator (`Krijo_Ikone_Desktop.py`), VBScript launcher (`launch_client.vbs`), and batch launchers (`launch_client.bat`, `Hap_Admin.bat`).

### Phase 7: Automated Order Dispatch & Cloud Deployment
- **Cloud Entrypoint**: Deployed standalone client application via `streamlit_app.py` for cloud hosting at `koreapurebeauty.streamlit.app`.
- **Instant Admin Email Alerts**: Connected the order checkout pipeline to send automated order notifications with line items, quantities, and customer details directly to `leart.demaku2006@gmail.com`.
- **CRM / WhatsApp Linkage**: Added direct 1-click WhatsApp customer support link (`wa.me/38345319619`) upon successful order placement.
- **Open-Ended Delivery City Field**: Replaced dropdown city selector with a flexible text input field to support deliveries to any city or region.

### Phase 8: Zero-Latency Client-Side Search Engine
- **In-Memory DOM Live Search**: Engineered high-performance JavaScript search engine executing in 0.1ms upon `input`, `keyup`, and `paste` events.
- **Dual-Portal Integration**: Integrated into both Client storefront and Admin portal (Shop catalog and Inventory expanders).
- **Multi-Token Albanian Normalization**: Strips diacritics and matches partial tokens across all product attributes.
- **Database Multi-Field Querying**: Updated `database.search_products()` to execute multi-token SQL queries across `name`, `brand`, `category`, `skin_type`, and `description`.

### Phase 9: Comprehensive Mobile Responsiveness & Multi-Touch Gestures
- **System-Wide Responsive CSS Engine**: Engineered custom multi-device CSS injected across `client_app.py`, `streamlit_app.py`, and `app.py`, enforcing fluid container scaling, overflow prevention, and mobile padding.
- **Touch Gesture Suite for HD Product Inspection**: Added 2-finger pinch-to-zoom calculation, 1-finger drag panning, double-tap zoom triggers, and responsive control bars to the interactive HD zoom viewer.
- **Mobile-First Layout Reflows**: Transformed desktop grids into clean vertical stacks while maintaining intentional horizontal sub-layouts (side-by-side product card action buttons, cart rows, and 2x2 Admin order action grids).
- **Mobile Form Ergonomics**: Standardized inputs to 16px to prevent iOS Safari auto-zooming, and expanded mobile touch targets to a minimum of 44px for effortless one-handed smartphone operation.
- **Zero-Exception Component Script Isolation**: Eliminated `Minified React error #231` by migrating DOM script execution from markdown inline event handlers to isolated `components.html` runtime with safe cross-frame DOM traversal, achieving a 100% clean browser console.

---

### Phase 10: Ultra-Modern Transformation (Master Plan)
- **Design system**: Porcelain Nude / Terracotta / Dark Espresso / Champagne Gold palette, Cormorant Garamond + Playfair Display + Plus Jakarta Sans.
- **Storefront**: new home page (arch hero, dark ritual section), shop with filters and Quick-View, ritual quiz, contact + FAQ, privacy & terms, one-step checkout with free-shipping progress.
- **Admin**: KPI dashboard, order workflow with stock restore on cancel, printable invoices, inline inventory editing, WebP uploads, inbox, testimonials and store settings.
- **Security**: random session tokens instead of `?user=`, no public admin sign-up, no secrets in code.

## Tech Stack

| Component | Technology | Rationale |
| :--- | :--- | :--- |
| **Language** | Python 3.10+ | Clean syntax, robust standard library, rapid iteration. |
| **Framework** | Streamlit 1.40+ | Fast web interface prototyping with reactive state management. |
| **Hosting** | Streamlit Community Cloud | Continuous deployment from GitHub with automated builds. |
| **Database** | SQLite3 | Zero-configuration, serverless, file-backed data store with ACID compliance. |
| **Styling & DOM** | Custom CSS3 + JavaScript | Advanced responsive layouts, adaptive theme tokens, DOM live search engine. |
| **Imaging** | Pillow (PIL) | Dynamic asset cropping, Lanczos resampling, WebP compression. |
| **Security** | Python `hashlib` & `secrets` | Cryptographically secure random tokens and salted password hashing. |
| **Mailing** | `smtplib` / `email.mime` | Native SMTP protocol handler with TLS encryption (Port 587). |
| **OS Automation** | `pywin32` (WScript.Shell) | Windows desktop shortcut and shell integration. |

---

## Project Structure

```
korea_pure_beauty/
├── client_app.py        # Storefront entry point (Port 8502): navbar, routing, auth popover
├── streamlit_app.py     # Streamlit Cloud entry point (runs client_app.py)
├── app.py               # Admin entry point (Port 8501): login + admin panel
├── views/
│   ├── storefront.py    # One-page store (same design as korea-pure-beauty.mjegulla.app): announcement,
│   │                    # sticky header, arch hero, shop with category pills, dark ritual section,
│   │                    # contact form + footer, product modal, cart side-drawer with checkout
│   ├── account.py       # Login, sign-up with e-mail code, password reset (header popover)
│   └── admin_view.py    # Dashboard, orders, products & inventory, inbox, testimonials, settings
├── database.py          # SQLite schema, safe migrations (PRAGMA table_info), CRUD
├── auth.py              # bcrypt passwords, session tokens, OTP codes
├── email_service.py     # SMTP notifications (credentials only from .env / st.secrets)
├── cart.py              # Cart logic (one place)
├── catalog.py           # Category groups, skin types, filtering, sorting, ritual builder
├── checkout.py          # Shipping, coupon, delivery validation, WhatsApp links
├── analytics.py         # Admin KPIs and chart data
├── theme.py             # Loads styles/*.css and assets into Streamlit
├── create_admin.py      # The only way to create an admin account
├── styles/              # store.css (storefront: Marcellus / Jost / Allura), main + pages + admin (.css)
├── assets/              # logo, hero_arch.webp, favicons
├── uploads/             # product photos (new uploads are saved as WebP)
├── tests/               # python -m unittest discover tests
└── .streamlit/config.toml  # light theme with the brand palette
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
pip install -r requirements.txt
```

### 5. Environment Configuration
Create a `.env` file in the project root (reference `.env.example`):
```ini
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_gmail_app_password
SMTP_FROM_NAME=Korea Pure Beauty
ADMIN_NOTIFICATION_EMAIL=where_admin_alerts_go@example.com   # optional, defaults to SMTP_USER
```

#### Streamlit Cloud Secrets Configuration
For Streamlit Community Cloud deployment, configure secrets in the dashboard settings under **Secrets**:
```toml
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "your_email@gmail.com"
SMTP_PASSWORD = "your_gmail_app_password"
SMTP_FROM_NAME = "Korea Pure Beauty"
ADMIN_NOTIFICATION_EMAIL = "leart.demaku2006@gmail.com"
```

> **Note**: If SMTP credentials are not configured, the application will automatically fall back to local test mode, allowing full functionality and logging generated OTP codes safely.

---

## Running the Applications

### Customer Storefront (Port 8502)
```bash
python -m streamlit run client_app.py --server.port 8502
```
Or double-click **`launch_client.bat`** (or use the created Desktop shortcut).

### Admin Management Panel (Port 8501)
```bash
python -m streamlit run app.py --server.port 8501
```
Or double-click **`Hap_Admin.bat`**.

### Creating an Admin Account
Admin accounts can no longer be created from the web interface. Run this on the store computer:
```bash
python create_admin.py
```

### Running the Tests
```bash
python -m unittest discover tests
```

### Design System Preview
```bash
python -m streamlit run theme_preview.py --server.port 8503
```

---

## Security Notes
- Secret configuration files (`.env`, `.streamlit/secrets.toml`) are strictly excluded from version control via `.gitignore`.
- `korea_beauty.db` is currently committed so the cloud deployment starts with the product catalog. It contains user emails and bcrypt password hashes, so it should be moved out of the public repository once the cloud app has its own persistent database.
- Passwords are never stored in plain text; they are hashed with bcrypt (salted).
- Sessions use random tokens stored only as SHA-256 hashes; the old `?user=<name>` auto-login (which allowed login without a password) has been removed.
- Admin self-registration from the web panel is disabled; admins are created only with `create_admin.py` and need at least 8 characters in their password.
- The admin panel rejects non-admin accounts at login.

---

## License
This project is proprietary and maintained for **Korea Pure Beauty**. All brand assets, product images, and documentation are reserved.
