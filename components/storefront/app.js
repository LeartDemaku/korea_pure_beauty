/* =====================================================================
   Korea Pure Beauty — logjika e dyqanit në browser.
   Python (Streamlit) dërgon të dhënat; ky skedar ndërton faqen, mban shportën
   dhe i dërgon Python-it vetëm veprimet: kyçje, regjistrim, porosi, mesazh.
   ===================================================================== */
(function () {
  "use strict";

  // ---------------------------------------------------------------
  // 1. Lidhja me Streamlit (protokolli i "custom components")
  // ---------------------------------------------------------------
  function sendToStreamlit(type, extra) {
    window.parent.postMessage(Object.assign({ isStreamlitMessage: true, type: type }, extra || {}), "*");
  }
  function setFrameHeight() {
    sendToStreamlit("streamlit:setFrameHeight", { height: window.innerHeight });
  }

  const state = {
    data: null,
    ready: false,
    tab: "Të gjitha",
    pending: {},            // veprimet që presin përgjigje nga Python: id -> callback
    seenResults: {},
    cart: loadCart(),
    drawerStep: "items",    // items | checkout | done
    lastOrder: null,
    account: { view: "login", pendingEmail: "", resetIdentifier: "", testCode: "" },
    ritual: { skin: "E Thatë", goal: "", sensitive: false },
    modalProduct: null,
    modalQty: 1,
    renderedKey: "",
  };

  // Thirr një veprim në Python dhe prit përgjigjen (Promise)
  function callPython(type, payload) {
    const id = Date.now().toString(36) + Math.random().toString(36).slice(2, 10);
    return new Promise(function (resolve) {
      state.pending[id] = resolve;
      sendToStreamlit("streamlit:setComponentValue", { value: { id: id, type: type, payload: payload || {} }, dataType: "json" });
      // Nëse Python nuk përgjigjet (p.sh. lidhja ra), mos e lë butonin të ngecur
      setTimeout(function () {
        if (state.pending[id]) {
          delete state.pending[id];
          resolve({ ok: false, message: "Lidhja me serverin vonoi. Provoni përsëri." });
        }
      }, 20000);
    });
  }

  window.addEventListener("message", function (event) {
    const msg = event.data;
    if (!msg || msg.type !== "streamlit:render" || !msg.args) return;
    onData(msg.args.data || {});
  });

  function onData(data) {
    state.data = data;
    // Përgjigjet e veprimeve
    const results = data.results || {};
    Object.keys(results).forEach(function (id) {
      if (state.pending[id] && !state.seenResults[id]) {
        state.seenResults[id] = true;
        const resolve = state.pending[id];
        delete state.pending[id];
        resolve(results[id]);
      }
    });
    // Ndërtojmë faqen vetëm kur ndryshojnë produktet ose cilësimet (jo në çdo rifreskim)
    const key = JSON.stringify([data.products, data.settings]);
    if (!state.ready) {
      state.ready = true;
      state.renderedKey = key;
      renderPage();
    } else if (key !== state.renderedKey) {
      state.renderedKey = key;
      renderMain();
    }
    sanitizeCart();
    updateHeader();
    if (isDrawerOpen()) renderDrawer();
  }

  // ---------------------------------------------------------------
  // 2. Ndihmës
  // ---------------------------------------------------------------
  function esc(value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function eur(amount) {
    const fixed = (Math.round(Number(amount) * 100) / 100).toFixed(2).split(".");
    return fixed[0].replace(/\B(?=(\d{3})+(?!\d))/g, " ") + "," + fixed[1] + " €";
  }
  function $(sel, root) { return (root || document).querySelector(sel); }
  function $all(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }
  // Elementi që lëviz (scroll). Dokumenti vetë nuk lëviz brenda Streamlit.
  function scroller() { return document.getElementById("app"); }
  function lockScroll(locked) { scroller().classList.toggle("is-locked", locked); }

  function products() { return (state.data && state.data.products) || []; }
  function settings() { return (state.data && state.data.settings) || {}; }
  function productById(id) { return products().find(function (p) { return p.id === id; }); }
  function digits(value) { return String(value || "").replace(/\D/g, ""); }
  function plural(n, one, many) { return n === 1 ? one : many; }

  const ICON = {
    bag: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 2 3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4Z"/><path d="M3 6h18"/><path d="M16 10a4 4 0 0 1-8 0"/></svg>',
    user: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/></svg>',
    menu: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" aria-hidden="true"><line x1="4" x2="20" y1="7" y2="7"/><line x1="4" x2="20" y1="12" y2="12"/><line x1="4" x2="20" y1="17" y2="17"/></svg>',
    x: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" aria-hidden="true"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>',
    minus: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" aria-hidden="true"><path d="M5 12h14"/></svg>',
    plus: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" aria-hidden="true"><path d="M5 12h14"/><path d="M12 5v14"/></svg>',
    check: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6 9 17l-5-5"/></svg>',
    truck: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 18V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v11a1 1 0 0 0 1 1h2"/><path d="M15 18H9"/><path d="M19 18h2a1 1 0 0 0 1-1v-3.65a1 1 0 0 0-.22-.624l-3.48-4.35A1 1 0 0 0 17.52 8H14"/><circle cx="17" cy="18" r="2"/><circle cx="7" cy="18" r="2"/></svg>',
    shield: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/></svg>',
    heart: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/></svg>',
    pin: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0"/><circle cx="12" cy="10" r="3"/></svg>',
    phone: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.91.34 1.85.57 2.81.7A2 2 0 0 1 22 16.92z"/></svg>',
    mail: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>',
    ig: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect width="20" height="20" x="2" y="2" rx="5"/><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/><line x1="17.5" x2="17.51" y1="6.5" y2="6.5"/></svg>',
    fb: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"/></svg>',
    arrowLeft: '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" aria-hidden="true"><path d="M19 12H5"/><path d="m12 19-7-7 7-7"/></svg>',
    cash: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect width="20" height="12" x="2" y="6" rx="2"/><circle cx="12" cy="12" r="2"/><path d="M6 12h.01M18 12h.01"/></svg>',
  };

  // ---------------------------------------------------------------
  // 3. Shporta (ruhet në browser, që të mos humbasë pas rifreskimit)
  // ---------------------------------------------------------------
  function loadCart() {
    try {
      const raw = JSON.parse(window.localStorage.getItem("kpb_cart_v1") || "[]");
      return Array.isArray(raw) ? raw.filter(function (l) { return l && Number.isInteger(l.id) && l.qty > 0; }) : [];
    } catch (e) { return []; }
  }
  function saveCart() {
    try { window.localStorage.setItem("kpb_cart_v1", JSON.stringify(state.cart)); } catch (e) { /* p.sh. dritare private */ }
  }
  function sanitizeCart() {
    // Hiqen produktet që admini i ka fshirë
    const before = state.cart.length;
    state.cart = state.cart.filter(function (l) { return productById(l.id); });
    if (state.cart.length !== before) saveCart();
  }
  function unitPrice(line) {
    const p = productById(line.id);
    if (!p) return 0;
    const discount = (state.data && state.data.ritual_discount) || 0.1;
    return line.ritual ? Math.round(p.price * (1 - discount) * 100) / 100 : p.price;
  }
  function cartCount() { return state.cart.reduce(function (s, l) { return s + l.qty; }, 0); }
  function subtotal() { return Math.round(state.cart.reduce(function (s, l) { return s + unitPrice(l) * l.qty; }, 0) * 100) / 100; }
  function addToCart(id, qty, ritual) {
    const line = state.cart.find(function (l) { return l.id === id && !!l.ritual === !!ritual; });
    if (line) line.qty = Math.min(50, line.qty + qty);
    else state.cart.push({ id: id, qty: Math.min(50, qty), ritual: !!ritual });
    saveCart();
    updateHeader();
  }
  function totals() {
    const s = settings();
    const sub = subtotal();
    const fee = Number(s.shipping_fee) || 0;
    const threshold = Number(s.free_shipping_threshold) || 0;
    const shipping = sub <= 0 || sub >= threshold ? 0 : fee;
    return { subtotal: sub, shipping: shipping, total: Math.round((sub + shipping) * 100) / 100,
             missing: Math.max(0, Math.round((threshold - sub) * 100) / 100), threshold: threshold };
  }

  // ---------------------------------------------------------------
  // 4. Ndërtimi i faqes
  // ---------------------------------------------------------------
  const NAV = [["dyqani", "Dyqani"], ["produktet", "Produktet"], ["rituali", "Rituali"], ["rreth-nesh", "Rreth nesh"], ["kontakt", "Kontakt"]];

  function renderPage() {
    const app = $("#app");
    app.innerHTML =
      headerHTML() +
      '<main id="main">' + mainHTML() + "</main>" +
      footerHTML() +
      '<div class="drawer-wrap" id="drawer" aria-hidden="true"><div class="drawer-bg" data-close-drawer></div>' +
      '<aside class="drawer" role="dialog" aria-modal="true" aria-label="Shporta juaj" id="drawer-panel"></aside></div>' +
      '<div class="overlay" id="overlay" aria-hidden="true"><div class="modal" id="modal" role="dialog" aria-modal="true"></div></div>' +
      '<div class="toast" id="toast" role="status"></div>';
    bindGlobal();
    afterMainRender();
    updateHeader();
    scroller().setAttribute("tabindex", "-1");
    scroller().focus({ preventScroll: true });
  }

  function renderMain() {
    $("#main").innerHTML = mainHTML();
    afterMainRender();
  }

  function afterMainRender() {
    renderGrid();
    observeReveal();
    observeSections();
  }

  function headerHTML() {
    const s = settings();
    const logo = s.logo_image ? '<img src="' + esc(s.logo_image) + '" alt="Logoja e Korea Pure Beauty">' : "";
    const announce = s.announcement
      ? '<div class="announce"><p><span>' + esc(s.announcement) + '</span><span class="dot opt" aria-hidden="true">·</span><span class="opt">Produkte origjinale koreane</span></p></div>'
      : "";
    const links = NAV.map(function (n) { return '<li><a href="#' + n[0] + '" data-nav="' + n[0] + '">' + n[1] + "</a></li>"; }).join("");
    return '<header class="site-header">' + announce +
      '<div class="nav-bar" id="nav-bar"><div class="nav-grid">' +
      '<a href="#kreu" class="brand" aria-label="Korea Pure Beauty, kreu">' + logo +
      '<span class="brand__text"><span class="brand__a">Korea Pure</span><span class="brand__b">Beauty</span></span></a>' +
      '<nav class="main-nav" aria-label="Navigimi kryesor"><ul>' + links + "</ul></nav>" +
      '<div class="nav-actions">' +
      '<button type="button" class="icon-btn" id="account-btn" aria-label="Llogaria">' + ICON.user + "</button>" +
      '<button type="button" class="icon-btn" id="cart-btn" aria-label="Shporta">' + ICON.bag + '<span class="badge-count" id="cart-count" hidden>0</span></button>' +
      '<button type="button" class="icon-btn menu-toggle" id="menu-btn" aria-expanded="false" aria-controls="mobile-nav" aria-label="Hap menynë">' + ICON.menu + "</button>" +
      "</div></div>" +
      '<nav class="mobile-nav" id="mobile-nav" aria-label="Navigimi në celular"><ul>' + links + "</ul></nav>" +
      "</div></header>";
  }

  function mainHTML() {
    return heroHTML() + shopHTML() + focusHTML() + ritualHTML() + aboutHTML() + contactHTML();
  }

  function heroHTML() {
    const s = settings();
    const img = s.hero_image ? '<img src="' + esc(s.hero_image) + '" alt="Produkte koreane për kujdesin e lëkurës mbi sfond të ngrohtë" loading="eager">' : "";
    return '<section id="kreu" class="hero" aria-labelledby="hero-title"><div class="hero__glow" aria-hidden="true"></div>' +
      '<div class="hero__grid"><div>' +
      '<p class="hero__eyebrow rise" style="animation-delay:.05s">K-Secret · Premium Korean Skincare</p>' +
      '<h1 id="hero-title" class="rise" style="animation-delay:.15s">Sekreti korean i një lëkure<span class="rose-text font-script">rrezatuese</span></h1>' +
      '<p class="hero__lead rise" style="animation-delay:.3s">Serume, kremra dhe maska nga linja Seoul 1988 e K-Secret — formula me xhensen të zi, retinal dhe vitaminë C, të sjella drejtpërdrejt nga Koreja për ritualin tuaj të përditshëm.</p>' +
      '<div class="hero__ctas rise" style="animation-delay:.45s"><a href="#dyqani" class="btn btn--pill">Zbulo produktet</a>' +
      '<a href="#rituali" class="link-under">Rituali në 4 hapa<span aria-hidden="true">→</span></a></div>' +
      '<ul class="hero__stats rise" style="animation-delay:.6s"><li><strong>' + products().length + '+</strong><span class="muted">produkte</span></li>' +
      '<li><span class="medium">100% origjinale</span></li><li><span class="medium">Dërgesë 24–48 orë</span></li></ul>' +
      "</div>" +
      '<div class="hero__visual rise" style="animation-delay:.25s"><div class="hero__outline" aria-hidden="true"></div>' +
      '<div class="hero__arch">' + img + "</div>" +
      '<div class="hero__badge rise" style="animation-delay:.75s"><p class="t1">100% origjinale</p><p class="t2">Prodhuar në Seul</p></div></div>' +
      "</div></section>";
  }

  function shopHTML() {
    const tabs = (state.data.tabs || ["Të gjitha"]).map(function (t) {
      return '<button type="button" role="tab" class="tab" data-tab="' + esc(t) + '" aria-selected="' + (t === state.tab) + '">' + esc(t) + "</button>";
    }).join("");
    return '<section id="dyqani" class="section"><div class="container">' +
      '<div class="shop-head"><div class="reveal"><p class="eyebrow">Dyqani</p>' +
      '<h2 class="section-title">' + esc(state.data.collection_title || "Koleksioni") + "</h2>" +
      '<p class="section-sub">Zgjidhni hapin që i mungon ritualit tuaj.</p></div>' +
      '<div class="shop-tools"><div class="tabs" role="tablist" aria-label="Kategoritë">' + tabs + "</div>" +
      '<p class="count" id="count" aria-live="polite"></p></div></div>' +
      '<ul class="grid" id="grid"></ul></div></section>';
  }

  function cardHTML(p, index) {
    const tag = p.badge ? '<span class="tag">' + esc(p.badge) + "</span>" : "";
    const old = p.old_price ? '<span class="price-old">' + eur(p.old_price) + "</span>" : "";
    return '<li class="card rise" style="animation-delay:' + Math.min(index, 8) * 60 + 'ms">' +
      '<button type="button" class="card__media" data-open="' + p.id + '" aria-label="Shiko ' + esc(p.name) + '">' +
      '<img src="' + esc(p.image) + '" alt="' + esc(p.name) + '" loading="lazy">' + tag + "</button>" +
      '<p class="card__cat">' + esc(p.tab) + "</p>" +
      '<button type="button" class="card__title" data-open="' + p.id + '"><h3>' + esc(p.name) + "</h3></button>" +
      '<p class="card__desc">' + esc(p.short) + "</p>" +
      '<div class="card__price"><span><span class="price">' + eur(p.price) + "</span>" + old + '</span><span class="size">' + esc(p.size) + "</span></div>" +
      '<button type="button" class="add-btn" data-add="' + p.id + '">' + ICON.bag + "<span>Shto në shportë</span></button></li>";
  }

  function renderGrid() {
    const list = products().filter(function (p) { return state.tab === "Të gjitha" || p.tab === state.tab; });
    const grid = $("#grid");
    grid.innerHTML = list.length
      ? list.map(cardHTML).join("")
      : '<li class="empty">Së shpejti produkte të reja në këtë kategori.</li>';
    $("#count").textContent = list.length + " " + plural(list.length, "produkt", "produkte");
    $all(".tab").forEach(function (t) { t.setAttribute("aria-selected", String(t.dataset.tab === state.tab)); });
  }

  function focusHTML() {
    const featured = (state.data.featured_ids || []).map(productById).filter(Boolean);
    if (!featured.length) return "";
    const items = featured.map(function (p, i) {
      const chips = (p.ingredients_list || []).slice(0, 5).map(function (c) { return '<span class="chip">' + esc(c) + "</span>"; }).join("");
      return '<article class="focus-item reveal">' +
        '<div class="focus-item__media"><div class="focus-item__frame" aria-hidden="true"></div>' +
        '<button type="button" class="focus-item__img" data-open="' + p.id + '" aria-label="Shiko ' + esc(p.name) + '"><img src="' + esc(p.image) + '" alt="' + esc(p.name) + '" loading="lazy"></button></div>' +
        '<div><span class="focus-item__num" aria-hidden="true">0' + (i + 1) + "</span>" +
        '<p class="eyebrow" style="margin-top:1rem">' + esc(p.brand) + " · " + esc(p.tab) + "</p>" +
        "<h3>" + esc(p.name) + "</h3>" +
        '<p class="focus-item__desc">' + esc(p.long || p.short) + "</p>" +
        (chips ? '<div class="chips">' + chips + "</div>" : "") +
        '<div class="focus-item__buy"><span class="price">' + eur(p.price) + "</span>" +
        '<button type="button" class="btn btn--pill" data-add="' + p.id + '">' + ICON.bag + "<span>Shto në shportë</span></button>" +
        '<button type="button" class="link-under" data-open="' + p.id + '">Shiko detajet<span aria-hidden="true">→</span></button></div></div></article>';
    }).join("");
    return '<section id="produktet" class="section focus"><div class="container">' +
      '<div class="reveal" style="max-width:40rem"><p class="eyebrow">Produktet</p>' +
      '<h2 class="section-title">Të preferuarat e <span class="font-script rose-text" style="font-size:1.4em">ritualit</span></h2>' +
      '<p class="section-sub">Produktet që klientet tona i zgjedhin më shpesh — me përbërësit kyç dhe mënyrën e përdorimit.</p></div>' +
      '<div class="focus-list">' + items + "</div></div></section>";
  }

  function ritualHTML() {
    const steps = (state.data.ritual_steps || []).map(function (s) {
      return '<li class="step"><span class="step__n" aria-hidden="true">' + esc(s.n) + "</span>" +
        '<div class="step__body"><p class="step__label"><span class="sr-only">Hapi ' + esc(s.n) + ": </span>" + esc(s.label) + "</p>" +
        "<h3>" + esc(s.title) + "</h3><p>" + esc(s.text) + "</p></div></li>";
    }).join("");
    return '<section id="rituali" class="ritual"><div class="ritual__glow" aria-hidden="true"></div><div class="ritual__line" aria-hidden="true"></div>' +
      '<div class="ritual__grid"><div><div class="ritual__sticky reveal">' +
      '<div class="ritual__kicker"><span>Rituali</span></div>' +
      '<h2>Katër hapa, një lëkurë që <span class="font-script">flet vetë</span></h2>' +
      '<p class="ritual__lead">Filozofia koreane e bukurisë nuk ka të bëjë me shumë produkte, por me shtresa të lehta që punojnë së bashku. Ja si i përdorni produktet çdo ditë.</p>' +
      '<button type="button" class="ritual__cta" id="ritual-cta">Ndërtoni ritualin tuaj<span aria-hidden="true">→</span></button>' +
      '</div></div><ol class="steps">' + steps + "</ol></div></section>";
  }

  function aboutHTML() {
    const s = settings();
    const logo = s.logo_image ? '<img src="' + esc(s.logo_image) + '" alt="Korea Pure Beauty">' : "";
    return '<section id="rreth-nesh" class="section about"><div class="container about__grid">' +
      '<div class="about__visual reveal"><div class="about__outline" aria-hidden="true"></div><div class="about__arch">' + logo + "</div>" +
      '<p class="about__quote">Bukuria nis me kujdesin</p></div>' +
      '<div class="about__text reveal"><p class="eyebrow">Rreth nesh</p>' +
      '<h2 class="section-title">Rituali korean, i sjellë me <span class="font-script">kujdes</span></h2>' +
      "<p>Korea Pure Beauty lindi nga dashuria për rutinën koreane të kujdesit për lëkurën — një filozofi që nuk kërkon shumë produkte, por produktet e duhura, të përdorura me rregull dhe me butësi.</p>" +
      "<p>Ne përzgjedhim vetë çdo produkt, kontrollojmë origjinalitetin dhe ju ndihmojmë të gjeni hapin që i mungon ritualit tuaj. Çdo porosi paketohet me kujdes dhe arrin te dera juaj brenda 24–48 orëve.</p>" +
      '<div class="values">' +
      '<div class="value"><span class="value__icon">' + ICON.shield + "</span><h4>Origjinalitet</h4><p>Vetëm produkte origjinale koreane, në paketimin e prodhuesit.</p></div>" +
      '<div class="value"><span class="value__icon">' + ICON.heart + "</span><h4>Këshillë personale</h4><p>Ju ndihmojmë të zgjidhni sipas llojit dhe nevojave të lëkurës.</p></div>" +
      '<div class="value"><span class="value__icon">' + ICON.truck + "</span><h4>Dërgesë e shpejtë</h4><p>24–48 orë në gjithë Kosovën, me pagesë në dorëzim.</p></div></div>" +
      '<div class="about__stats"><div><strong>' + products().length + "+</strong><span>produkte</span></div>" +
      "<div><strong>24–48h</strong><span>dërgesa</span></div><div><strong>14</strong><span>ditë për kthim</span></div></div>" +
      "</div></div></section>";
  }

  function contactHTML() {
    const s = settings();
    const wa = digits(s.whatsapp);
    let list = "";
    if (s.location) list += "<li><span>" + ICON.pin + esc(s.location) + "</span></li>";
    if (wa) list += '<li><a href="https://wa.me/' + wa + '" target="_blank" rel="noopener">' + ICON.phone + '<span><span class="muted">WhatsApp/Viber:</span> +' + wa + "</span></a></li>";
    if (s.email) list += '<li><a href="mailto:' + esc(s.email) + '">' + ICON.mail + esc(s.email) + "</a></li>";
    return '<section id="kontakt" class="section contact"><div class="container contact__grid">' +
      '<div class="reveal"><p class="eyebrow">Kontakt</p><h2 class="section-title">Na shkruani</h2>' +
      '<p class="section-sub">Keni pyetje për lëkurën tuaj apo për një porosi? Konsulentet tona ju përgjigjen sa më shpejt.</p>' +
      '<ul class="contact__list">' + list + "</ul></div>" +
      '<form class="form reveal" id="contact-form" novalidate>' +
      '<div class="form-row">' + field("c-name", "Emri *", "text", "name", 80) + field("c-phone", "Telefoni", "tel", "tel", 20) + "</div>" +
      field("c-email", "Email-i", "email", "email", 120) +
      '<div class="field"><label for="c-msg">Mesazhi *</label><textarea id="c-msg" name="message" maxlength="2000" required></textarea></div>' +
      '<div id="contact-msg"></div>' +
      '<button type="submit" class="btn btn--solid">Dërgo mesazhin</button></form>' +
      "</div></section>";
  }

  function field(id, label, type, autocomplete, maxlength, value, hint) {
    return '<div class="field"><label for="' + id + '">' + label + "</label>" +
      '<input id="' + id + '" name="' + id + '" type="' + type + '" autocomplete="' + autocomplete + '" maxlength="' + maxlength + '" value="' + esc(value || "") + '">' +
      (hint ? '<span class="field__hint">' + hint + "</span>" : "") + "</div>";
  }

  function footerHTML() {
    const s = settings();
    const wa = digits(s.whatsapp);
    const logo = s.logo_image ? '<img src="' + esc(s.logo_image) + '" alt="Korea Pure Beauty">' : "";
    let contact = "";
    if (s.location) contact += "<li><span>" + ICON.pin + esc(s.location) + "</span></li>";
    if (wa) contact += '<li><a href="https://wa.me/' + wa + '" target="_blank" rel="noopener">' + ICON.phone + "<span>+" + wa + "</span></a></li>";
    if (s.email) contact += '<li><a href="mailto:' + esc(s.email) + '">' + ICON.mail + "<span>" + esc(s.email) + "</span></a></li>";
    let social = "";
    if (s.instagram) social += '<li><a href="' + esc(s.instagram) + '" target="_blank" rel="noopener noreferrer"><span class="soc">' + ICON.ig + "</span>Instagram</a></li>";
    if (s.facebook) social += '<li><a href="' + esc(s.facebook) + '" target="_blank" rel="noopener noreferrer"><span class="soc">' + ICON.fb + "</span>Facebook</a></li>";
    return '<footer class="footer"><div class="footer__inner"><div class="footer__grid">' +
      '<div><a href="#kreu" class="footer-brand">' + logo + '<span><span class="a">KOREA PURE</span><span class="b">Beauty</span></span></a>' +
      '<p class="footer__about"><b>Premium Korean Skincare</b> — produkte origjinale koreane, të zgjedhura me kujdes për lëkurën tuaj.</p></div>' +
      '<div><h3 class="fh">Kontakt</h3><ul class="flist">' + contact + "</ul></div>" +
      '<div><h3 class="fh">Informacion</h3><ul class="info"><li>Dërgesa 24–48 orë në gjithë Kosovën</li><li>Pagesa me para në dorë</li>' +
      "<li>Dërgesë falas mbi " + eur(s.free_shipping_threshold || 0) + "</li><li>Kthim brenda 14 ditëve</li></ul></div>" +
      (social ? '<div><h3 class="fh">Na ndiqni</h3><ul class="flist">' + social + "</ul></div>" : "<div></div>") +
      '</div><div class="footer__bottom"><p>© ' + new Date().getFullYear() + " Korea Pure Beauty. Të gjitha të drejtat e rezervuara.</p>" +
      '<button type="button" id="privacy-btn">Privatësia &amp; kushtet</button></div></div></footer>';
  }

  // ---------------------------------------------------------------
  // 5. Header-i (llogaria, shporta)
  // ---------------------------------------------------------------
  function updateHeader() {
    const count = cartCount();
    const badge = $("#cart-count");
    if (badge) {
      badge.textContent = count;
      badge.hidden = count === 0;
      $("#cart-btn").setAttribute("aria-label", "Shporta, " + count + " " + plural(count, "produkt", "produkte"));
    }
    const accountBtn = $("#account-btn");
    if (accountBtn) {
      const user = state.data && state.data.user;
      accountBtn.setAttribute("aria-label", user ? "Llogaria e " + user.name : "Kyçu ose krijo llogari");
      accountBtn.style.color = user ? "var(--primary)" : "";
    }
  }

  // ---------------------------------------------------------------
  // 6. Ngjarjet (klikimet)
  // ---------------------------------------------------------------
  function bindGlobal() {
    document.addEventListener("click", function (e) {
      const t = e.target;
      const tab = t.closest("[data-tab]");
      if (tab && tab.classList.contains("tab") && tab.closest(".tabs")) { state.tab = tab.dataset.tab; renderGrid(); return; }
      const open = t.closest("[data-open]");
      if (open) { openProduct(Number(open.dataset.open)); return; }
      const add = t.closest("[data-add]");
      if (add) {
        addToCart(Number(add.dataset.add), 1, false);
        flashAdded(add);
        openDrawer("items");
        return;
      }
      if (t.closest("[data-close-drawer]")) { closeDrawer(); return; }
      if (t.closest("#cart-btn")) { openDrawer("items"); return; }
      if (t.closest("#account-btn")) { openAccount(); return; }
      if (t.closest("#ritual-cta")) { openRitual(); return; }
      if (t.closest("#privacy-btn")) { openPrivacy(); return; }
      if (t.closest("#menu-btn")) { toggleMenu(); return; }
      if (t.closest("#mobile-nav a")) { toggleMenu(false); return; }
      if (t.id === "overlay") { closeModal(); return; }
    });
    document.addEventListener("keydown", function (e) {
      if (e.key !== "Escape") return;
      if ($("#overlay").classList.contains("is-open")) closeModal();
      else if (isDrawerOpen()) closeDrawer();
    });
    document.addEventListener("submit", function (e) {
      if (e.target.id === "contact-form") { e.preventDefault(); submitContact(e.target); }
    });
    scroller().addEventListener("scroll", function () {
      const bar = $("#nav-bar");
      if (bar) bar.classList.toggle("is-scrolled", scroller().scrollTop > 8);
    }, { passive: true });
    window.addEventListener("resize", setFrameHeight);
  }

  function flashAdded(button) {
    button.classList.add("is-added");
    setTimeout(function () { button.classList.remove("is-added"); }, 900);
  }

  function toggleMenu(force) {
    const nav = $("#mobile-nav");
    const open = typeof force === "boolean" ? force : !nav.classList.contains("is-open");
    nav.classList.toggle("is-open", open);
    $("#menu-btn").setAttribute("aria-expanded", String(open));
    $("#menu-btn").innerHTML = open ? ICON.x : ICON.menu;
  }

  function observeReveal() {
    const items = $all(".reveal:not(.is-in)");
    if (!("IntersectionObserver" in window)) { items.forEach(function (el) { el.classList.add("is-in"); }); return; }
    const io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add("is-in"); io.unobserve(en.target); } });
    }, { rootMargin: "0px 0px -8% 0px" });
    items.forEach(function (el) { io.observe(el); });
  }

  function observeSections() {
    if (!("IntersectionObserver" in window)) return;
    const io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        $all("[data-nav]").forEach(function (a) { a.classList.toggle("is-active", a.dataset.nav === en.target.id); });
      });
    }, { rootMargin: "-45% 0px -50% 0px" });
    NAV.forEach(function (n) { const s = document.getElementById(n[0]); if (s) io.observe(s); });
  }

  function toast(text) {
    const el = $("#toast");
    el.textContent = text;
    el.classList.add("is-on");
    clearTimeout(toast.timer);
    toast.timer = setTimeout(function () { el.classList.remove("is-on"); }, 2600);
  }

  function setBusy(button, busy, label) {
    if (!button) return;
    if (busy) {
      button.dataset.label = button.innerHTML;
      button.disabled = true;
      button.innerHTML = '<span class="spinner" aria-hidden="true"></span><span>' + (label || "Duke dërguar…") + "</span>";
    } else {
      button.disabled = false;
      if (button.dataset.label) button.innerHTML = button.dataset.label;
    }
  }

  function messageHTML(kind, text) { return '<p class="msg msg--' + kind + '" role="' + (kind === "error" ? "alert" : "status") + '">' + text + "</p>"; }

  // ---------------------------------------------------------------
  // 7. Kontakti
  // ---------------------------------------------------------------
  function submitContact(form) {
    const box = $("#contact-msg");
    const payload = { name: form["c-name"].value.trim(), phone: form["c-phone"].value.trim(), email: form["c-email"].value.trim(), message: form.message.value.trim() };
    const errors = [];
    if (!payload.name) errors.push("Shkruani emrin.");
    if (!payload.email && !payload.phone) errors.push("Shkruani email-in ose telefonin, që t'ju përgjigjemi.");
    if (!payload.message) errors.push("Shkruani mesazhin.");
    if (errors.length) { box.innerHTML = messageHTML("error", errors.map(esc).join("<br>")); return; }
    const button = form.querySelector("button[type=submit]");
    setBusy(button, true);
    callPython("contact", payload).then(function (res) {
      setBusy(button, false);
      if (res.ok) { form.reset(); box.innerHTML = messageHTML("ok", "Faleminderit! Mesazhi u dërgua. Do t'ju përgjigjemi sa më shpejt."); }
      else box.innerHTML = messageHTML("error", (res.errors || [res.message]).map(esc).join("<br>"));
    });
  }

  // ---------------------------------------------------------------
  // 8. Dritaret: produkti, llogaria, rituali, privatësia
  // ---------------------------------------------------------------
  let lastFocus = null;
  function openModal(html, size) {
    lastFocus = document.activeElement;
    const modal = $("#modal");
    modal.className = "modal" + (size ? " modal--" + size : "");
    modal.innerHTML = '<button type="button" class="modal__close" data-close-modal aria-label="Mbyll">' + ICON.x + "</button>" + html;
    modal.querySelector("[data-close-modal]").addEventListener("click", closeModal);
    const overlay = $("#overlay");
    overlay.classList.add("is-open");
    overlay.setAttribute("aria-hidden", "false");
    lockScroll(true);
    modal.scrollTop = 0;
    setTimeout(function () { const f = modal.querySelector("input, .btn, button:not(.modal__close)"); if (f) f.focus({ preventScroll: true }); }, 60);
  }
  function closeModal() {
    const overlay = $("#overlay");
    overlay.classList.remove("is-open");
    overlay.setAttribute("aria-hidden", "true");
    if (!isDrawerOpen()) lockScroll(false);
    if (lastFocus && lastFocus.focus) lastFocus.focus({ preventScroll: true });
  }

  function openProduct(id) {
    const p = productById(id);
    if (!p) return;
    state.modalProduct = p;
    state.modalQty = 1;
    const tag = p.badge ? '<span class="tag">' + esc(p.badge) + "</span>" : "";
    const size = p.size ? '<span class="muted" style="font-size:.875rem">· ' + esc(p.size) + "</span>" : "";
    const old = p.old_price ? '<span class="price-old">' + eur(p.old_price) + "</span>" : "";
    let extra = "";
    if (p.ingredients) extra += '<p class="pm__extra"><b>Përbërësit kyç:</b> ' + esc(p.ingredients) + "</p>";
    if (p.how_to_use) extra += '<p class="pm__extra"><b>Përdorimi:</b> ' + esc(p.how_to_use) + "</p>";
    openModal(
      '<div class="pm"><div class="pm__media"><img src="' + esc(p.image) + '" alt="' + esc(p.name) + '">' + tag + "</div>" +
      '<div class="pm__body"><p class="pm__cat">' + esc(p.tab) + "</p><h3>" + esc(p.name) + "</h3>" +
      '<div class="pm__price"><span class="price">' + eur(p.price) + "</span>" + old + size + "</div>" +
      '<p class="pm__desc">' + esc(p.long || p.short) + "</p>" + extra +
      '<div class="pm__buy"><div class="pm__row"><div class="qty">' +
      '<button type="button" id="pm-minus" aria-label="Pakëso sasinë" disabled>' + ICON.minus + "</button>" +
      '<span id="pm-qty" aria-live="polite">1</span>' +
      '<button type="button" id="pm-plus" aria-label="Shto sasinë">' + ICON.plus + "</button></div>" +
      '<button type="button" class="btn btn--dark" id="pm-add">' + ICON.bag + "Shto në shportë</button></div>" +
      '<ul class="perks"><li>' + ICON.check + "Produkt origjinal</li><li>" + ICON.check + "Dërgesë 24–48 orë</li></ul></div></div></div>"
    );
    function syncQty() {
      $("#pm-qty").textContent = state.modalQty;
      $("#pm-minus").disabled = state.modalQty <= 1;
      $("#pm-plus").disabled = state.modalQty >= 20;
    }
    $("#pm-minus").addEventListener("click", function () { state.modalQty = Math.max(1, state.modalQty - 1); syncQty(); });
    $("#pm-plus").addEventListener("click", function () { state.modalQty = Math.min(20, state.modalQty + 1); syncQty(); });
    $("#pm-add").addEventListener("click", function () {
      addToCart(p.id, state.modalQty, false);
      closeModal();
      openDrawer("items");
    });
  }

  // --- Llogaria ---
  function openAccount(view) {
    if (view) state.account.view = view;
    const user = state.data && state.data.user;
    if (user) {
      openModal('<div class="dlg"><p class="eyebrow">Llogaria</p><h2>Përshëndetje, ' + esc(user.name) + "</h2>" +
        '<p class="dlg__sub">' + esc(user.email) + "</p>" +
        (user.is_admin ? '<p class="msg msg--info" style="margin-top:1.25rem">Paneli i administratorit hapet me Hap_Admin.bat.</p>' : "") +
        '<div style="margin-top:1.75rem;display:grid;gap:.75rem"><button type="button" class="btn btn--solid" id="acc-shop">Vazhdo blerjet</button>' +
        '<button type="button" class="btn btn--outline" id="acc-logout">Dil nga llogaria</button></div></div>', "narrow");
      $("#acc-shop").addEventListener("click", closeModal);
      $("#acc-logout").addEventListener("click", function (e) {
        setBusy(e.currentTarget, true, "Duke dalë…");
        callPython("logout", {}).then(function () { closeModal(); toast("Dolët nga llogaria."); });
      });
      return;
    }
    const a = state.account;
    let body = "";
    if (a.view === "verify") {
      body = '<h2>Verifikoni email-in</h2><p class="dlg__sub">Kodi 6-shifror u dërgua te <b>' + esc(a.pendingEmail) + "</b>.</p>" +
        testCodeHTML() +
        '<form id="acc-form" data-action="verify" novalidate>' + field("a-code", "Kodi", "text", "one-time-code", 6) +
        '<div id="acc-msg"></div><button type="submit" class="btn btn--solid">Aktivizo llogarinë</button>' +
        '<button type="button" class="linkish" id="acc-resend">Ridërgo kodin</button></form>';
    } else if (a.view === "reset_confirm") {
      body = '<h2>Fjalëkalim i ri</h2><p class="dlg__sub">Shkruani kodin që morët në email.</p>' + testCodeHTML() +
        '<form id="acc-form" data-action="reset_confirm" novalidate>' + field("a-code", "Kodi", "text", "one-time-code", 6) +
        field("a-pass", "Fjalëkalimi i ri", "password", "new-password", 128) + field("a-pass2", "Konfirmo fjalëkalimin", "password", "new-password", 128) +
        '<div id="acc-msg"></div><button type="submit" class="btn btn--solid">Ruaj fjalëkalimin</button></form>';
    } else {
      const seg = [["login", "Hyr"], ["register", "Regjistrohu"], ["reset", "Fjalëkalimi"]].map(function (s) {
        return '<button type="button" data-acc-view="' + s[0] + '" aria-selected="' + (a.view === s[0]) + '">' + s[1] + "</button>";
      }).join("");
      let form = "";
      if (a.view === "register") {
        form = field("a-name", "Emri dhe mbiemri", "text", "name", 80) + field("a-email", "Email-i", "email", "email", 120) +
          field("a-pass", "Fjalëkalimi", "password", "new-password", 128, "", "Të paktën 6 karaktere") +
          field("a-pass2", "Konfirmo fjalëkalimin", "password", "new-password", 128) +
          '<div id="acc-msg"></div><button type="submit" class="btn btn--solid">Krijo llogarinë</button>';
      } else if (a.view === "reset") {
        form = field("a-email", "Email-i i llogarisë", "email", "email", 120) +
          '<div id="acc-msg"></div><button type="submit" class="btn btn--solid">Dërgo kodin</button>';
      } else {
        form = field("a-email", "Email-i", "email", "username", 120) + field("a-pass", "Fjalëkalimi", "password", "current-password", 128) +
          '<div id="acc-msg"></div><button type="submit" class="btn btn--solid">Hyr</button>';
      }
      body = '<p class="eyebrow">Korea Pure Beauty</p><h2 style="margin-top:.5rem">Llogaria juaj</h2>' +
        '<p class="dlg__sub">Kyçuni për porosi më të shpejta dhe për të ndjekur blerjet tuaja.</p>' +
        '<div class="seg" role="tablist">' + seg + "</div>" +
        '<form id="acc-form" data-action="' + a.view + '" novalidate>' + form + "</form>";
    }
    openModal('<div class="dlg">' + body + "</div>", "narrow");
    $all("[data-acc-view]").forEach(function (b) { b.addEventListener("click", function () { openAccount(b.dataset.accView); }); });
    const resend = $("#acc-resend");
    if (resend) resend.addEventListener("click", function () {
      callPython("resend_code", { email: a.pendingEmail }).then(function (res) {
        if (res.test_code) state.account.testCode = res.test_code;
        $("#acc-msg").innerHTML = messageHTML(res.ok ? "ok" : "info", esc(res.ok ? "Kodi i ri u dërgua." : res.message));
      });
    });
    $("#acc-form").addEventListener("submit", function (e) { e.preventDefault(); submitAccount(e.target); });
  }

  function testCodeHTML() {
    return state.account.testCode
      ? '<p class="msg msg--info" style="margin-top:1rem">Email-i nuk është konfiguruar në server. Kodi i testimit: <b>' + esc(state.account.testCode) + "</b></p>"
      : "";
  }

  function value(id) { const el = document.getElementById(id); return el ? el.value.trim() : ""; }

  function submitAccount(form) {
    const action = form.dataset.action;
    const box = $("#acc-msg");
    const button = form.querySelector("button[type=submit]");
    const a = state.account;
    let payload;
    if (action === "login") payload = { identifier: value("a-email"), password: document.getElementById("a-pass").value };
    else if (action === "register") payload = { name: value("a-name"), email: value("a-email"), password: document.getElementById("a-pass").value, confirm: document.getElementById("a-pass2").value };
    else if (action === "reset") payload = { identifier: value("a-email") };
    else if (action === "verify") payload = { email: a.pendingEmail, code: value("a-code") };
    else if (action === "reset_confirm") payload = { identifier: a.resetIdentifier, code: value("a-code"), password: document.getElementById("a-pass").value, confirm: document.getElementById("a-pass2").value };
    setBusy(button, true, "Një moment…");
    callPython(action, payload).then(function (res) {
      setBusy(button, false);
      if (res.test_code) state.account.testCode = res.test_code;
      if (action === "register" && res.ok) { a.pendingEmail = res.pending_email; openAccount("verify"); return; }
      if (action === "login" && res.unverified_email) { a.pendingEmail = res.unverified_email; openAccount("verify"); return; }
      if (action === "reset" && res.ok) { a.resetIdentifier = payload.identifier; openAccount("reset_confirm"); return; }
      if (action === "reset_confirm" && res.ok) { a.testCode = ""; openAccount("login"); $("#acc-msg").innerHTML = messageHTML("ok", esc(res.message)); return; }
      if ((action === "login" || action === "verify") && res.ok) {
        a.testCode = ""; a.view = "login"; closeModal();
        toast("Mirë se vini, " + (res.user && res.user.name ? res.user.name : "") + "!");
        return;
      }
      box.innerHTML = messageHTML("error", esc(res.message || "Diçka shkoi keq. Provoni përsëri."));
    });
  }

  // --- Rituali ---
  function openRitual() {
    const d = state.data;
    if (!state.ritual.goal) state.ritual.goal = (d.ritual_goals || [""])[0];
    function opts(name, list, current) {
      return list.map(function (o) {
        return '<button type="button" class="tab" data-q="' + name + '" data-v="' + esc(o) + '" aria-selected="' + (o === current) + '">' + esc(o) + "</button>";
      }).join("");
    }
    function draw() {
      const r = state.ritual;
      const routine = buildRitual(r.skin, r.goal, r.sensitive);
      const chosen = routine.filter(function (s) { return s.product; });
      const rows = routine.map(function (s) {
        const p = s.product;
        return '<li><span class="n" aria-hidden="true">' + esc(s.n) + "</span>" +
          (p ? '<img src="' + esc(p.image) + '" alt="">' : '<span class="ph"></span>') +
          "<div><small>" + esc(s.label) + "</small><p>" + (p ? esc(p.name) : "Së shpejti") + "</p></div></li>";
      }).join("");
      const full = chosen.reduce(function (sum, s) { return sum + s.product.price; }, 0);
      const disc = d.ritual_discount || 0.1;
      $("#ritual-body").innerHTML =
        '<div class="quiz"><div><p class="quiz__q">1. Lloji i lëkurës</p><div class="quiz__opts">' + opts("skin", d.ritual_skins || [], r.skin) + "</div></div>" +
        '<div><p class="quiz__q">2. Synimi kryesor</p><div class="quiz__opts">' + opts("goal", d.ritual_goals || [], r.goal) + "</div></div>" +
        '<div><p class="quiz__q">3. Lëkurë e ndjeshme ndaj aromave?</p><div class="quiz__opts">' + opts("sens", ["Jo", "Po"], r.sensitive ? "Po" : "Jo") + "</div></div></div>" +
        '<ol class="routine">' + rows + "</ol>" +
        (chosen.length
          ? '<div class="routine__total"><span class="muted">Rituali i plotë (−' + Math.round(disc * 100) + '%)</span><span><span class="price-old">' + eur(full) + '</span> <span class="price">' + eur(full * (1 - disc)) + "</span></span></div>" +
            '<button type="button" class="btn btn--solid" id="ritual-add">Shto ritualin në shportë</button>'
          : '<p class="msg msg--info" style="margin-top:1.25rem">Së shpejti produkte për këtë ritual.</p>');
      $all("[data-q]").forEach(function (b) {
        b.addEventListener("click", function () {
          if (b.dataset.q === "skin") r.skin = b.dataset.v;
          if (b.dataset.q === "goal") r.goal = b.dataset.v;
          if (b.dataset.q === "sens") r.sensitive = b.dataset.v === "Po";
          draw();
        });
      });
      const add = $("#ritual-add");
      if (add) add.addEventListener("click", function () {
        chosen.forEach(function (s) { addToCart(s.product.id, 1, true); });
        closeModal();
        openDrawer("items");
      });
    }
    openModal('<div class="dlg"><p class="eyebrow">Rituali</p><h2 style="margin-top:.5rem">Ndërtoni ritualin tuaj</h2>' +
      '<p class="dlg__sub">Tri pyetje — ne zgjedhim nga dyqani një rutinë me katër hapa.</p><div id="ritual-body"></div></div>', "mid");
    draw();
  }

  // E njëjta logjikë si catalog.build_ritual në Python
  function buildRitual(skin, goal, sensitive) {
    const d = state.data;
    const keywords = (d.goal_keywords || {})[goal] || [];
    const used = {};
    return (d.ritual_plan || []).map(function (step) {
      let best = null, bestScore = -1;
      products().forEach(function (p) {
        if (used[p.id] || step.groups.indexOf(p.group) < 0) return;
        let score = 0;
        if (p.skin_types.indexOf(skin) >= 0) score += 3;
        if (sensitive && p.skin_types.indexOf("Sensibile") >= 0) score += 2;
        keywords.forEach(function (k) { if (p.search.indexOf(k) >= 0) score += 2; });
        if (p.is_bestseller) score += 1;
        if (score > bestScore) { best = p; bestScore = score; }
      });
      if (best) used[best.id] = true;
      return { n: step.n, label: step.label, product: best };
    });
  }

  function openPrivacy() {
    const s = settings();
    openModal('<div class="dlg legal"><p class="eyebrow">Dokumente</p><h2 style="margin-top:.5rem">Privatësia &amp; kushtet</h2>' +
      "<h4>Të dhënat personale</h4><p>Emrin, telefonin, qytetin dhe adresën i përdorim vetëm për ta realizuar dhe dërguar porosinë tuaj. Nuk ua shesim palëve të treta; i ndajmë vetëm me korrierin që e dorëzon porosinë. Mund të kërkoni në çdo kohë t'i shihni, korrigjoni ose fshini. Fjalëkalimet ruhen të koduara.</p>" +
      "<h4>Dërgesat</h4><p>24–48 orë në gjithë Kosovën. Dërgesa kushton " + eur(s.shipping_fee || 0) + " dhe është falas mbi " + eur(s.free_shipping_threshold || 0) + ". Pagesa bëhet me para në dorë.</p>" +
      "<h4>Kthimi dhe ndërrimi</h4><p>Brenda 14 ditëve, për produkte të pahapura në paketimin origjinal. Produktet e hapura nuk kthehen për arsye higjiene, përveç kur kanë ardhur të dëmtuara ose të gabuara.</p>" +
      "<h4>Origjinaliteti</h4><p>Shesim vetëm produkte origjinale koreane, në paketimin e prodhuesit.</p></div>", "mid");
  }

  // ---------------------------------------------------------------
  // 9. Shporta anësore dhe porosia
  // ---------------------------------------------------------------
  function isDrawerOpen() { const d = $("#drawer"); return !!d && d.classList.contains("is-open"); }
  function openDrawer(step) {
    state.drawerStep = step || "items";
    renderDrawer();
    const d = $("#drawer");
    d.classList.add("is-open");
    d.setAttribute("aria-hidden", "false");
    lockScroll(true);
    toggleMenu(false);
  }
  function closeDrawer() {
    const d = $("#drawer");
    d.classList.remove("is-open");
    d.setAttribute("aria-hidden", "true");
    if (!$("#overlay").classList.contains("is-open")) lockScroll(false);
    if (state.drawerStep === "done") { state.drawerStep = "items"; state.lastOrder = null; }
  }

  function renderDrawer() {
    const panel = $("#drawer-panel");
    if (!panel) return;
    const count = cartCount();
    const head = '<header class="drawer__head"><div><p class="eyebrow">Korea Pure Beauty</p><h2>Shporta juaj<span>(' + count + " " + plural(count, "artikull", "artikuj") + ")</span></h2></div>" +
      '<button type="button" class="drawer__close" data-close-drawer aria-label="Mbyll shportën">' + ICON.x + "</button></header>";
    if (state.drawerStep === "done" && state.lastOrder) { panel.innerHTML = head + doneHTML(state.lastOrder); bindDone(); return; }
    if (!state.cart.length) {
      panel.innerHTML = head + '<div class="drawer-empty">' + ICON.bag + "<h3>Shporta është bosh</h3>" +
        "<p>Zgjidhni serumin, kremin apo maskën që i përshtatet ritualit tuaj të përditshëm.</p>" +
        '<button type="button" class="btn btn--outline" data-close-drawer>Vazhdo blerjet →</button></div>';
      return;
    }
    if (state.drawerStep === "checkout") { panel.innerHTML = head + checkoutHTML(); bindCheckout(); return; }

    const lines = state.cart.map(function (l, i) {
      const p = productById(l.id);
      const unit = unitPrice(l);
      return '<li class="line"><div class="line__img"><img src="' + esc(p.image) + '" alt="' + esc(p.name) + '"></div>' +
        '<div class="line__main"><div class="line__top"><p class="n">' + esc(p.name) + (l.ritual ? ' <span class="muted">· Rituali</span>' : "") + "</p>" +
        '<p class="p">' + eur(unit * l.qty) + "</p></div>" +
        '<p class="line__meta">' + esc(p.size || p.brand) + " · " + eur(unit) + "</p>" +
        '<div class="line__actions"><div class="qty qty--sm">' +
        '<button type="button" data-dec="' + i + '" aria-label="Ul sasinë">' + ICON.minus + "</button>" +
        '<span aria-live="polite">' + l.qty + "</span>" +
        '<button type="button" data-inc="' + i + '" aria-label="Rrit sasinë"' + (l.qty >= 50 ? " disabled" : "") + ">" + ICON.plus + "</button></div>" +
        '<button type="button" class="line__remove" data-remove="' + i + '">Hiq</button></div></div></li>';
    }).join("");
    panel.innerHTML = head + '<div class="drawer__body"><ul class="lines">' + lines + "</ul></div>" +
      '<footer class="drawer__foot">' + summaryHTML() +
      '<button type="button" class="btn btn--solid" id="go-checkout">Vazhdo me porosinë →</button></footer>';
    $all("[data-dec]", panel).forEach(function (b) { b.addEventListener("click", function () { changeQty(Number(b.dataset.dec), -1); }); });
    $all("[data-inc]", panel).forEach(function (b) { b.addEventListener("click", function () { changeQty(Number(b.dataset.inc), 1); }); });
    $all("[data-remove]", panel).forEach(function (b) { b.addEventListener("click", function () { state.cart.splice(Number(b.dataset.remove), 1); saveCart(); updateHeader(); renderDrawer(); }); });
    $("#go-checkout").addEventListener("click", function () { state.drawerStep = "checkout"; renderDrawer(); });
  }

  function changeQty(index, delta) {
    const line = state.cart[index];
    if (!line) return;
    line.qty += delta;
    if (line.qty <= 0) state.cart.splice(index, 1);
    line.qty = Math.min(50, line.qty);
    saveCart(); updateHeader(); renderDrawer();
  }

  function summaryHTML() {
    const t = totals();
    const pct = t.threshold ? Math.min(100, (t.subtotal / t.threshold) * 100) : 100;
    const free = t.missing > 0
      ? "<span>Edhe <strong>" + eur(t.missing) + "</strong> për dërgesë falas</span>"
      : "<span>Dërgesa juaj është <strong>falas</strong></span>";
    return '<div class="free">' + ICON.truck + free + "</div>" +
      '<div class="bar"><span style="width:' + pct.toFixed(1) + '%"></span></div>' +
      '<dl class="sum"><div><dt>Nëntotali</dt><dd>' + eur(t.subtotal) + "</dd></div>" +
      "<div><dt>Dërgesa</dt><dd>" + (t.shipping ? eur(t.shipping) : "Falas") + "</dd></div>" +
      '<div class="tot"><dt>Totali</dt><dd>' + eur(t.total) + "</dd></div></dl>";
  }

  function checkoutHTML() {
    const user = (state.data && state.data.user) || {};
    return '<div class="drawer__body"><form class="checkout" id="checkout-form" novalidate>' +
      '<button type="button" class="back" id="back-cart">' + ICON.arrowLeft + "Kthehu te shporta</button>" +
      "<h3>Të dhënat e dërgesës</h3>" +
      field("o-name", "Emri & mbiemri *", "text", "name", 80, user.name) +
      field("o-phone", "Telefoni *", "tel", "tel", 20, "", "Korrieri ju telefonon para dorëzimit") +
      '<div class="form-row">' + field("o-city", "Qyteti *", "text", "address-level2", 60) + field("o-coupon", "Kupon", "text", "off", 20) + "</div>" +
      '<div class="field"><label for="o-address">Adresa e saktë *</label><textarea id="o-address" maxlength="300" autocomplete="street-address" style="min-height:80px"></textarea></div>' +
      field("o-notes", "Shënime për korrierin", "text", "off", 300) +
      field("o-email", "Email-i (për konfirmim)", "email", "email", 120, user.email) +
      '<p class="pay-note">' + ICON.cash + "Pagesa me para në dorë, kur ta merrni porosinë.</p>" +
      '<div id="order-msg"></div></form></div>' +
      '<footer class="drawer__foot">' + summaryHTML() +
      '<button type="submit" form="checkout-form" class="btn btn--solid" id="place-order">Përfundo porosinë</button></footer>';
  }

  function bindCheckout() {
    $("#back-cart").addEventListener("click", function () { state.drawerStep = "items"; renderDrawer(); });
    $("#checkout-form").addEventListener("submit", function (e) {
      e.preventDefault();
      const box = $("#order-msg");
      const payload = {
        name: value("o-name"), phone: value("o-phone"), city: value("o-city"), address: value("o-address"),
        notes: value("o-notes"), email: value("o-email"), coupon: value("o-coupon"),
        items: state.cart.map(function (l) { return { id: l.id, qty: l.qty, ritual: !!l.ritual }; }),
      };
      const errors = [];
      if (payload.name.length < 3) errors.push("Shkruani emrin dhe mbiemrin.");
      if (!/^\+?[0-9 ()\-]{6,20}$/.test(payload.phone)) errors.push("Numri i telefonit nuk është i saktë (p.sh. +383 44 123 456).");
      if (payload.city.length < 2) errors.push("Shkruani qytetin.");
      if (payload.address.length < 5) errors.push("Shkruani adresën e plotë.");
      $all("#checkout-form input, #checkout-form textarea").forEach(function (el) { el.removeAttribute("aria-invalid"); });
      if (errors.length) {
        box.innerHTML = messageHTML("error", errors.map(esc).join("<br>"));
        box.scrollIntoView({ block: "nearest", behavior: "smooth" });
        return;
      }
      const button = $("#place-order");
      setBusy(button, true, "Duke dërguar porosinë…");
      callPython("place_order", payload).then(function (res) {
        setBusy(button, false);
        if (!res.ok) {
          box.innerHTML = messageHTML("error", (res.errors || [res.message]).map(esc).join("<br>"));
          box.scrollIntoView({ block: "nearest", behavior: "smooth" });
          return;
        }
        state.cart = []; saveCart(); updateHeader();
        state.lastOrder = res.order;
        state.drawerStep = "done";
        renderDrawer();
      });
    });
  }

  function doneHTML(order) {
    const emailLine = order.email_sent ? "Konfirmimi u dërgua në <b>" + esc(order.email) + "</b>. " : "";
    const wa = digits(settings().whatsapp);
    const waText = encodeURIComponent("Përshëndetje! Jam " + order.name + ". Sapo bëra porosinë #" + order.id + " me vlerë " + eur(order.total) + " te Korea Pure Beauty. Ju lutem ma konfirmoni.");
    return '<div class="drawer-done"><span class="done-icon">' + ICON.check + "</span>" +
      '<p class="script">Faleminderit!</p><h3>Porosia juaj u regjistrua.</h3>' +
      '<p>Numri i referencës: <span class="ref">#' + esc(order.id) + "</span><br>Totali: " + eur(order.total) +
      " · pagesë me para në dorë.<br>" + emailLine + "Do t'ju telefonojmë në <b>" + esc(order.phone) + "</b> për ta konfirmuar dërgesën.</p>" +
      '<div class="done-actions">' +
      (wa ? '<a class="btn btn--wa" href="https://wa.me/' + wa + "?text=" + waText + '" target="_blank" rel="noopener">Konfirmo në WhatsApp</a>' : "") +
      '<button type="button" class="btn btn--solid" data-close-drawer>Mbyll</button></div></div>';
  }
  function bindDone() { /* butoni "Mbyll" përdor data-close-drawer */ }

  // ---------------------------------------------------------------
  // 10. Nisja
  // ---------------------------------------------------------------
  sendToStreamlit("streamlit:componentReady", { apiVersion: 1 });
  setFrameHeight();
})();
