import streamlit as st
import asyncio
from playwright.async_api import async_playwright
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from urllib.parse import urlparse, parse_qs
import io
import os
import re
import time

st.set_page_config(
    page_title="Privacy & Consent Mode v2 Auditor",
    page_icon="🛡️",
    layout="wide"
)

# Estilos visuales Cybersecurity Dark Mode
st.markdown("""
<style>
.stApp {
    background-color: #0a0d14;
    color: #e2e8f0;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}
h1, h2, h3, h4 {
    color: #f8fafc !important;
    font-weight: 700;
    letter-spacing: -0.5px;
}
.cyber-panel {
    background: #111726;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 16px;
    margin-bottom: 14px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
    transition: all 0.25s ease;
}
.cyber-panel:hover {
    border-color: #00f0ff;
    box-shadow: 0 0 15px rgba(0, 240, 255, 0.15);
    transform: translateY(-2px);
}
.cyber-panel-title {
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #94a3b8;
    font-weight: 600;
    margin-bottom: 6px;
}
.cyber-panel-val {
    font-size: 1.8rem;
    font-weight: 800;
    color: #00f0ff;
    font-family: 'Courier New', Courier, monospace;
}
.cyber-badge-ok {
    display: inline-block;
    background: rgba(16, 185, 129, 0.15);
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.3);
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-top: 6px;
}
.cyber-badge-warn {
    display: inline-block;
    background: rgba(245, 158, 11, 0.15);
    color: #fbbf24;
    border: 1px solid rgba(245, 158, 11, 0.3);
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-top: 6px;
}
.cyber-console {
    background: #070a10;
    border: 1px solid #1b2438;
    border-radius: 6px;
    padding: 8px;
    font-family: 'Courier New', Courier, monospace;
    font-size: 0.75rem;
    color: #cbd5e1;
    margin-top: 8px;
    word-break: break-all;
}
.cyber-action {
    font-size: 0.7rem;
    color: #64748b;
    margin-top: 6px;
}
.stTextInput > div > div > input {
    background-color: #111726 !important;
    color: #f8fafc !important;
    border: 1px solid #23304a !important;
    border-radius: 8px !important;
    font-size: 0.95rem;
}
.stTextInput > div > div > input:focus {
    border-color: #00f0ff !important;
    box-shadow: 0 0 12px rgba(0, 240, 255, 0.25) !important;
}
.stButton > button {
    background: linear-gradient(135deg, #00f0ff 0%, #0284c7 100%) !important;
    color: #070a10 !important;
    font-weight: 800 !important;
    border: none !important;
    border-radius: 8px !important;
    box-shadow: 0 4px 15px rgba(0, 240, 255, 0.25) !important;
    transition: all 0.2s ease !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.stButton > button:hover {
    box-shadow: 0 6px 25px rgba(0, 240, 255, 0.5) !important;
    transform: translateY(-1px);
    color: #000000 !important;
}
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background-color: transparent;
    border-bottom: 1px solid #1e293b;
    margin-bottom: 16px;
}
.stTabs [data-baseweb="tab"] {
    background-color: #111726;
    border: 1px solid #1e293b;
    border-radius: 8px 8px 0 0;
    color: #94a3b8;
    padding: 10px 22px;
    font-weight: 600;
}
.stTabs [aria-selected="true"] {
    background-color: #162035 !important;
    border-color: #00f0ff !important;
    color: #00f0ff !important;
}
div[data-testid="stDataFrame"] {
    border: 1px solid #1e293b;
    border-radius: 8px;
    overflow: hidden;
}
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def ensure_playwright():
    os.system("playwright install chromium")

ensure_playwright()

# ==============================================================================
# MOTOR FORENSE DE COOKIES: BASE CANÓNICA DE PROVEEDORES Y CATEGORÍAS
# ==============================================================================

EXACT_COOKIES = {
    # --- Cloudflare (Infraestructura, Seguridad y CDN) ---
    "_cf_ob": ("Cloudflare (Always Online / Resiliencia de Servidor)", "Técnica / Necesaria"),
    "cf_ob_info": ("Cloudflare (Diagnóstico Always Online)", "Técnica / Necesaria"),
    "cf_use_ob": ("Cloudflare (Caché de contingencia Always Online)", "Técnica / Necesaria"),
    "__cf_bm": ("Cloudflare (Gestión de bots y mitigación automatizada)", "Técnica / Necesaria"),
    "cf_clearance": ("Cloudflare (Validación de desafío anti-DDoS / Captcha)", "Técnica / Necesaria"),
    "_cfuvid": ("Cloudflare (Rate Limiting por usuario único)", "Técnica / Necesaria"),
    "__cflb": ("Cloudflare (Persistencia de balanceo de carga)", "Técnica / Necesaria"),
    "__cfduid": ("Cloudflare (Identificador heredado de confianza)", "Técnica / Necesaria"),
    
    # --- Frameworks y Servidores Web (Gestión de Sesión e Idioma) ---
    "sessionid": ("Framework Django / Python (Sesión autenticada de usuario)", "Técnica / Necesaria"),
    "django_language": ("Framework Django (Preferencia de idioma del usuario)", "Técnica / Necesaria"),
    "csrftoken": ("Framework Django / Seguridad Web (Prevención de ataques CSRF)", "Técnica / Necesaria"),
    "phpsessid": ("Servidor PHP (Gestor de sesión nativa)", "Técnica / Necesaria"),
    "jsessionid": ("Servidor Java / Spring / Tomcat (Gestor de sesión)", "Técnica / Necesaria"),
    "asp.net_sessionid": ("Servidor Microsoft ASP.NET (Sesión de navegación)", "Técnica / Necesaria"),
    "xsrf-token": ("Seguridad Web (Protección CSRF en frameworks frontend)", "Técnica / Necesaria"),
    "laravel_session": ("Framework Laravel / PHP (Sesión cifrada de usuario)", "Técnica / Necesaria"),
    "connect.sid": ("Node.js / Express (Sesión Express-Session)", "Técnica / Necesaria"),
    
    # --- CMS y Tiendas Online ---
    "woocommerce_cart_hash": ("WooCommerce (Caché y cálculo del carrito de compra)", "Técnica / Necesaria"),
    "woocommerce_items_in_cart": ("WooCommerce (Contador de productos en carrito)", "Técnica / Necesaria"),
    "wp_woocommerce_session": ("WooCommerce (Persistencia del carrito de compras)", "Técnica / Necesaria"),
    "prestashop": ("PrestaShop (Sesión técnica de tienda online)", "Técnica / Necesaria"),
    "mage-cache-sessid": ("Magento / Adobe Commerce (Sesión de caché)", "Técnica / Necesaria"),
    "private_content_version": ("Magento (Control de versiones de contenido privado)", "Técnica / Necesaria"),
    
    # --- Gestores de Consentimiento (CMPs) ---
    "cookiescriptconsent": ("CookieScript (Almacenamiento de preferencias del usuario)", "Técnica / Necesaria"),
    "optanonconsent": ("OneTrust (Registro oficial de categorías aceptadas)", "Técnica / Necesaria"),
    "optanonalertboxclosed": ("OneTrust (Estado de cierre del banner de aviso)", "Técnica / Necesaria"),
    "cookieyes-consent": ("CookieYes (Estado de aceptación de categorías)", "Técnica / Necesaria"),
    "cky-consent": ("CookieYes (Hash de consentimiento y auditoría)", "Técnica / Necesaria"),
    "cookieconsent_status": ("Cookie Consent / Osano (Estado del banner)", "Técnica / Necesaria"),
    "didomi_token": ("Didomi CMP (Token de consentimiento de privacidad)", "Técnica / Necesaria"),
    "euconsent-v2": ("IAB Europe TCF v2.2 (Cadena oficial de consentimiento)", "Técnica / Necesaria"),
    
    # --- Balanceadores & CDNs ---
    "awsalb": ("Amazon Web Services (Enrutamiento de balanceador ALB)", "Técnica / Necesaria"),
    "awsalbcors": ("Amazon Web Services (Control CORS en balanceador ALB)", "Técnica / Necesaria"),
    "aka_a2": ("Akamai CDN (Optimización de velocidad y entrega de contenidos)", "Técnica / Necesaria"),
    
    # --- Analítica & Rendimiento ---
    "_ga": ("Google Analytics 4 (Identificador único de cliente / CID)", "Analítica / Rendimiento"),
    "_gid": ("Google Analytics (Identificador de sesión de 24 horas)", "Analítica / Rendimiento"),
    "_gat": ("Google Analytics (Limitador técnico de tasa de solicitudes)", "Analítica / Rendimiento"),
    "_clck": ("Microsoft Clarity (ID único de usuario para mapas de calor)", "Analítica / Rendimiento"),
    "_clsk": ("Microsoft Clarity (Registro de página vista y sesión activa)", "Analítica / Rendimiento"),
    "clid": ("Microsoft Clarity (ID de cliente analítico)", "Analítica / Rendimiento"),
    "vuid": ("Vimeo Player (Telemetría de reproducción y métricas de vídeo)", "Analítica / Rendimiento"),
    
    # --- Publicidad & Marketing ---
    "_fbp": ("Meta Pixel (Identificador de navegador para eventos publicitarios)", "Marketing / Publicidad"),
    "_fbc": ("Meta Pixel (Parámetro fbclid para atribución de anuncios)", "Marketing / Publicidad"),
    "fr": ("Meta / Facebook (Entrega de anuncios y retargeting)", "Marketing / Publicidad"),
    "ide": ("Google DoubleClick (Segmentación y remarketing cross-domain)", "Marketing / Publicidad"),
    "test_cookie": ("Google DoubleClick (Comprobación de soporte de cookies)", "Marketing / Publicidad"),
    "__gads": ("Google Ad Manager (Servicio de publicidad y frecuencia de anuncios)", "Marketing / Publicidad"),
    "__gpi": ("Google Publisher Tag (Identificador de editor de Google)", "Marketing / Publicidad"),
    "_gcl_au": ("Google AdSense / Ads (Atribución previa a la conversión)", "Marketing / Publicidad"),
    "_gcl_aw": ("Google Ads (Atribución tras clic en anuncio)", "Marketing / Publicidad"),
    "_gcl_dc": ("Google Ads / Floodlight (Medición de conversiones)", "Marketing / Publicidad"),
    "nid": ("Google LLC (Perfil publicitario personalizado en servicios Google)", "Marketing / Publicidad"),
    "muid": ("Microsoft Advertising / Bing Ads (Conversiones y perfiles de usuario)", "Marketing / Publicidad"),
    "_uetsid": ("Microsoft Advertising (ID de sesión para Universal Event Tracking)", "Marketing / Publicidad"),
    "_uetvid": ("Microsoft Advertising (ID persistente de usuario Bing Ads)", "Marketing / Publicidad"),
    "personalization_id": ("Twitter / X (Personalización y seguimiento publicitario)", "Marketing / Publicidad"),
    "guest_id": ("Twitter / X (Identificación de visitantes para anuncios)", "Marketing / Publicidad"),
    "bcookie": ("LinkedIn (Identificador de navegador para seguimiento B2B)", "Marketing / Publicidad"),
    "bscookie": ("LinkedIn (Autenticación y seguimiento de anuncios)", "Marketing / Publicidad"),
    "lidc": ("LinkedIn (Enrutamiento para optimización del píxel publicitario)", "Marketing / Publicidad"),
    "cto_bundle": ("Criteo (Retargeting dinámico cross-device)", "Marketing / Publicidad")
}

# Patrones Regex anclados con alta especificidad
REGEX_PATTERNS = [
    # Familia Cloudflare
    (r'^_?cf(_.*)?$', "Cloudflare (Infraestructura, Seguridad y CDN)", "Técnica / Necesaria"),
    
    # Propiedades GA4 (_ga_XXXXXXXXXX) y variantes
    (r'^_ga_[a-zA-Z0-9_]+$', "Google Analytics 4 (Medición de flujo web / Sesión de datos)", "Analítica / Rendimiento"),
    (r'^_gat_.*$', "Google Analytics (Regulación de peticiones)", "Analítica / Rendimiento"),
    (r'^__utm[a-z]$', "Google Analytics Universal (Métricas de tráfico heredadas)", "Analítica / Rendimiento"),
    
    # Hotjar
    (r'^_hj(Session|SessionUser|IncludedIn|AbsoluteCanonicalUrl|TLDTest|id|FirstSeen).*$', "Hotjar (Mapas de calor y comportamiento del usuario)", "Analítica / Rendimiento"),
    
    # Matomo / Piwik
    (r'^(_pk_|pk_)(id|ses|ref|cvar).*$', "Matomo / Piwik (Analítica web autohospedada)", "Analítica / Rendimiento"),
    
    # Yandex Metrica
    (r'^_ym_.*$', "Yandex Metrica (Analítica y mapas de calor)", "Analítica / Rendimiento"),
    
    # TikTok Pixel
    (r'^(tt_|ttp|_ttp).*$', "TikTok Pixel (Seguimiento de conversiones y remarketing)", "Marketing / Publicidad"),
    
    # Criteo
    (r'^cto_.*$', "Criteo (Red publicitaria y retargeting dinámico)", "Marketing / Publicidad"),
    
    # Bing / Microsoft Ads
    (r'^_uet.*$', "Microsoft Advertising (Universal Event Tracking)", "Marketing / Publicidad"),
    
    # WordPress CMS
    (r'^(wp-|wordpress_).*$', "WordPress CMS (Control de sesión de usuario y panel)", "Técnica / Necesaria"),
    (r'^(pll_|icl_).*$', "Módulo Multi-idioma (Polylang / WPML)", "Técnica / Necesaria")
]

# Identificación por dominio emisor (cuando el nombre es opaco)
DOMAIN_PATTERNS = [
    (r'cloudflare\.com$', "Cloudflare Inc.", "Técnica / Necesaria"),
    (r'doubleclick\.net$', "Google DoubleClick", "Marketing / Publicidad"),
    (r'facebook\.com$', "Meta Platforms Inc.", "Marketing / Publicidad"),
    (r'vimeo\.com$', "Vimeo Inc. (Reproductor embebido)", "Analítica / Rendimiento"),
    (r'clarity\.ms$', "Microsoft Clarity", "Analítica / Rendimiento"),
    (r'hotjar\.com$', "Hotjar Ltd.", "Analítica / Rendimiento"),
    (r'cookie-script\.com$', "CookieScript CMP", "Técnica / Necesaria"),
    (r'onetrust\.com$', "OneTrust CMP", "Técnica / Necesaria")
]

# Heurística morfológica por palabras clave
KEYWORD_PATTERNS = [
    (r'.*(sess|csrf|token|auth|security|login|nonce|checkout|cart|carrito|pedido|lang|idioma).*', "Propio (Sesión, Seguridad o Idioma)", "Técnica / Necesaria"),
    (r'.*(analy|metric|stats|pageview|visitor|tracker|heatmap).*', "Herramienta de Analítica / Estadísticas", "Analítica / Rendimiento"),
    (r'.*(pixel|banner|campaign|camp|promo|retarget|adserver|affiliate).*', "Red Publicitaria / Seguimiento", "Marketing / Publicidad")
]

def identificar_cookie_avanzada(name, domain):
    n = name.strip().lower()
    d = domain.strip().lower()
    
    # 1. Búsqueda exacta
    if n in EXACT_COOKIES:
        return EXACT_COOKIES[n]
        
    # 2. Búsqueda por patrón de nombre
    for regex, prov, cat in REGEX_PATTERNS:
        if re.match(regex, n, re.IGNORECASE):
            return prov, cat
            
    # 3. Búsqueda por dominio emisor
    for dom_regex, prov, cat in DOMAIN_PATTERNS:
        if re.search(dom_regex, d):
            return f"{prov} (Dominio de red)", cat
            
    # 4. Análisis morfológico contextual
    for kw_regex, prov, cat in KEYWORD_PATTERNS:
        if re.match(kw_regex, n, re.IGNORECASE):
            return f"{prov} ({domain})", cat
            
    return f"Propietario / Sin firma ({domain})", "Por categorizar"

def calcular_duracion(expires_unix):
    if not expires_unix or expires_unix == -1 or expires_unix <= 0:
        return "Sesión"
    diff = expires_unix - time.time()
    if diff <= 0:
        return "Expirada / Sesión"
    dias = diff / 86400
    if dias < 1:
        horas = int(diff / 3600)
        return f"{max(1, horas)} horas" if horas > 0 else "Menos de 1 h"
    elif dias < 30:
        return f"{int(dias)} días"
    elif dias < 365:
        return f"{int(dias / 30)} meses"
    else:
        anos = round(dias / 365, 1)
        return "1 año" if anos == 1.0 else f"{anos:g} años"

def enriquecer_cookie_forense(cookie, phase_key, baseline_names, analytics_new, marketing_new):
    name = cookie.get('name', '')
    domain = cookie.get('domain', '')
    expires = cookie.get('expires', -1)
    duracion = calcular_duracion(expires)
    
    prov, cat_recomendada = identificar_cookie_avanzada(name, domain)
    is_in_baseline = name in baseline_names
    
    # Cotejo diferencial: ¿cómo trata la web realmente a esta cookie?
    if is_in_baseline:
        if phase_key in ['default', 'reject']:
            cat_web = "Técnica / Exenta (Carga Previa)"
        else:
            cat_web = "Técnica / Exenta (Base persistente)"
    else:
        if name in analytics_new:
            cat_web = "Analítica / Rendimiento (Inyectada al consentir)"
        elif name in marketing_new:
            cat_web = "Marketing / Publicidad (Inyectada al consentir)"
        elif phase_key == 'accept':
            cat_web = "Consentimiento Global (Inyectada tras Aceptar)"
        else:
            cat_web = "No clasificada (Inyección anómala)"

    # Diagnóstico legal de conformidad (RGPD / Directrices AEPD)
    if phase_key in ['default', 'reject']:
        if "Analítica" in cat_recomendada or "Marketing" in cat_recomendada:
            diagnostico = "❌ Infracción (Fuga sin consentimiento previo)"
        elif cat_recomendada == "Por categorizar":
            diagnostico = "⚠️ Por verificar (Sospecha de fuga no técnica)"
        else:
            diagnostico = "✅ Conforme (Técnica autorizada)"
    elif phase_key == 'analytics':
        if "Marketing" in cat_recomendada:
            diagnostico = "❌ Infracción (Fuga de Marketing en Solo Analítica)"
        elif "Analítica" in cat_recomendada:
            diagnostico = "✅ Conforme (Analítica autorizada)"
        elif "Técnica" in cat_recomendada:
            diagnostico = "✅ Conforme (Técnica base)"
        else:
            diagnostico = "⚠️ Por verificar"
    elif phase_key == 'marketing':
        if "Analítica" in cat_recomendada:
            diagnostico = "❌ Infracción (Fuga de Analítica en Solo Marketing)"
        elif "Marketing" in cat_recomendada:
            diagnostico = "✅ Conforme (Marketing autorizado)"
        elif "Técnica" in cat_recomendada:
            diagnostico = "✅ Conforme (Técnica base)"
        else:
            diagnostico = "⚠️ Por verificar"
    else:
        diagnostico = "✅ Conforme (Consentimiento global otorgado)"

    return {
        "Nombre": name,
        "Proveedor": prov,
        "Duración": duracion,
        "Categoría en Web": cat_web,
        "Categoría Debería Ser": cat_recomendada,
        "Diagnóstico": diagnostico,
        "Dominio": domain,
        "Segura": "Sí" if cookie.get('secure') else "No"
    }

# ==============================================================================
# DECODIFICACIÓN DE PARÁMETROS CONSENT MODE V2
# ==============================================================================

def is_google_consent_ping(url_str):
    u = url_str.lower()
    return any(p in u for p in ["gcs=", "gcd=", "google-analytics.com", "analytics.google.com", "googleads", "doubleclick.net", "pagead"])

def decode_gcd_letter(letter):
    l = letter.lower()
    if l in ['r', 'u', 'v']:
        return "Granted (Concedido)", "✅", True
    elif l in ['p', 'q', 'm', 'n']:
        return "Denied (Denegado)", "❌", False
    elif l in ['s', 't']:
        return "Not set / Uninitialized", "⏳", False
    elif l == 'l':
        return "Not configured", "⚪", False
    return f"Unknown ({letter})", "❓", False

def decode_gcd(gcd_str):
    if not gcd_str or gcd_str == 'No detectado':
        return None
    m = re.match(r'^1([0-9])([a-zA-Z])([0-9])([a-zA-Z])([0-9])([a-zA-Z])([0-9])([a-zA-Z])', gcd_str)
    if not m:
        return None
        
    keys = ['ad_storage', 'analytics_storage', 'ad_user_data', 'ad_personalization']
    indices = [2, 4, 6, 8]
    result = {}
    
    for key, idx in zip(keys, indices):
        raw_char = m.group(idx)
        label, icon, granted = decode_gcd_letter(raw_char)
        result[key] = {
            'status': label,
            'icon': icon,
            'letter': raw_char,
            'is_granted': granted
        }
    return result

def extract_consent_params(pings):
    if not pings:
        return {
            'gcs': 'No detectado',
            'gcd': 'No detectado',
            'npa': 'No detectado',
            'dma': 'No detectado',
            'gcd_params': None
        }
    
    gcs = 'No detectado'
    gcd = 'No detectado'
    npa = 'No detectado'
    dma = 'No detectado'
    
    for p in reversed(pings):
        parsed = parse_qs(urlparse(p).query)
        if not parsed:
            parsed = parse_qs(p)
            
        if gcs == 'No detectado' and 'gcs' in parsed:
            gcs = parsed['gcs'][0]
        if gcd == 'No detectado' and 'gcd' in parsed:
            gcd = parsed['gcd'][0]
        if npa == 'No detectado' and 'npa' in parsed:
            npa = parsed['npa'][0]
        if dma == 'No detectado' and 'dma' in parsed:
            dma = parsed['dma'][0]
            
    gcd_decoded = decode_gcd(gcd)
    
    if gcs == 'No detectado' and gcd_decoded:
        ad_ok = gcd_decoded['ad_storage']['is_granted']
        ana_ok = gcd_decoded['analytics_storage']['is_granted']
        gcs = f"G1{1 if ad_ok else 0}{1 if ana_ok else 0}"

    return {
        'gcs': gcs,
        'gcd': gcd,
        'npa': npa,
        'dma': dma,
        'gcd_params': gcd_decoded
    }

# ==============================================================================
# INTERACCIÓN AUTOMATIZADA CON PRINCIPALES CMPS
# ==============================================================================

async def interactuar_con_cmp(page, target_action):
    js_action = """
    async (mode) => {
        // === 1. APIS NATIVAS ===
        if (window.CookieScript && window.CookieScript.instance) {
            try {
                if (mode === 'accept') { window.CookieScript.instance.acceptAllAction(); return "API CookieScript: acceptAllAction"; }
                if (mode === 'reject') { window.CookieScript.instance.rejectAllAction(); return "API CookieScript: rejectAllAction"; }
                if (mode === 'only_analytics') { window.CookieScript.instance.acceptAction(['performance']); return "API CookieScript: performance"; }
                if (mode === 'only_marketing') { window.CookieScript.instance.acceptAction(['targeting']); return "API CookieScript: targeting"; }
            } catch(e) {}
        }
        if (window.OneTrust) {
            try {
                if (mode === 'accept' && window.OneTrust.AllowAll) { window.OneTrust.AllowAll(); return "API OneTrust: AllowAll"; }
                if (mode === 'reject' && window.OneTrust.RejectAll) { window.OneTrust.RejectAll(); return "API OneTrust: RejectAll"; }
            } catch(e) {}
        }
        if (window.Didomi) {
            try {
                if (mode === 'accept' && window.Didomi.setUserAgreeToAll) { window.Didomi.setUserAgreeToAll(); return "API Didomi: setUserAgreeToAll"; }
                if (mode === 'reject' && window.Didomi.setUserDisagreeToAll) { window.Didomi.setUserDisagreeToAll(); return "API Didomi: setUserDisagreeToAll"; }
            } catch(e) {}
        }

        // === 2. BOTONES DIRECTOS (CAPA 1) ===
        if (mode === 'accept') {
            const acceptSelectors = [
                '#cookiescript_accept',
                '#onetrust-accept-btn-handler',
                '#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll', '#CybotCookiebotDialogBodyButtonAccept',
                '.cky-btn-accept', '[data-cky-tag="accept-button"]',
                '#didomi-notice-agree-button',
                'button[data-testid="uc-accept-all-button"]',
                '.iubenda-cs-accept-btn',
                '#axeptio_btn_acceptAll'
            ];
            for (let s of acceptSelectors) {
                let el = document.querySelector(s);
                if (el && el.offsetParent !== null) { el.click(); return "Selector: " + s; }
            }
            for (let b of Array.from(document.querySelectorAll('button, a, input[type="button"]'))) {
                let t = (b.innerText || b.value || '').trim().toLowerCase();
                if (['aceptar todas', 'aceptar todo', 'accept all', 'permitir todas', 'aceptar', 'accept', 'allow all'].some(term => t === term || t.includes(term))) {
                    b.click(); return "Texto: " + t;
                }
            }
        }

        if (mode === 'reject') {
            const rejectSelectors = [
                '#cookiescript_reject',
                '#onetrust-reject-all-handler',
                '#CybotCookiebotDialogBodyButtonDecline', '#CybotCookiebotDialogBodyLevelButtonLevelOptinDeclineAll',
                '.cky-btn-reject', '[data-cky-tag="reject-button"]',
                '#didomi-notice-disagree-button',
                'button[data-testid="uc-deny-all-button"]',
                '.iubenda-cs-reject-btn',
                '#axeptio_btn_refuse'
            ];
            for (let s of rejectSelectors) {
                let el = document.querySelector(s);
                if (el && el.offsetParent !== null) { el.click(); return "Selector: " + s; }
            }
            for (let b of Array.from(document.querySelectorAll('button, a, input[type="button"]'))) {
                let t = (b.innerText || b.value || '').trim().toLowerCase();
                if (['rechazar todas', 'rechazar todo', 'reject all', 'denegar', 'rechazar', 'reject', 'decline all', 'solo necesarias'].some(term => t === term || t.includes(term))) {
                    b.click(); return "Texto: " + t;
                }
            }
        }

        // === 3. SEGUNDA CAPA (GRANULAR: ANALYTICS / MARKETING) ===
        const openManageSelectors = [
            '#cookiescript_manage',
            '#onetrust-pc-btn-handler',
            '#CybotCookiebotDialogBodyLevelButtonCustomize',
            '.cky-btn-customize', '[data-cky-tag="settings-button"]',
            '#didomi-notice-learn-more-button',
            '.iubenda-cs-customize-btn'
        ];
        let panelOpened = false;
        for (let s of openManageSelectors) {
            let el = document.querySelector(s);
            if (el && el.offsetParent !== null) { el.click(); panelOpened = true; break; }
        }
        if (!panelOpened) {
            for (let b of Array.from(document.querySelectorAll('button, a, span'))) {
                let t = (b.innerText || '').trim().toLowerCase();
                if (['personalizar', 'configurar', 'preferencias', 'customize', 'settings', 'manage cookies'].some(term => t.includes(term))) {
                    b.click(); break;
                }
            }
        }
        await new Promise(r => setTimeout(r, 1000));

        // Cookiebot
        let cbStat = document.querySelector('#CybotCookiebotDialogBodyLevelButtonStatistics');
        let cbMkt = document.querySelector('#CybotCookiebotDialogBodyLevelButtonMarketing');
        if (cbStat && cbMkt) {
            if (mode === 'only_analytics') {
                if (!cbStat.checked) cbStat.click();
                if (cbMkt.checked) cbMkt.click();
            } else if (mode === 'only_marketing') {
                if (cbStat.checked) cbStat.click();
                if (!cbMkt.checked) cbMkt.click();
            }
        }

        // CookieYes
        let ckyAna = document.querySelector('input[data-cky-tag="analytics"], .cky-category-analytics input, [data-cky-tag="analytics-switch"]');
        let ckyAdv = document.querySelector('input[data-cky-tag="advertisement"], .cky-category-advertisement input, [data-cky-tag="advertisement-switch"]');
        if (ckyAna || ckyAdv) {
            if (mode === 'only_analytics') {
                if (ckyAna && !ckyAna.checked) ckyAna.click();
                if (ckyAdv && ckyAdv.checked) ckyAdv.click();
            } else if (mode === 'only_marketing') {
                if (ckyAna && ckyAna.checked) ckyAna.click();
                if (ckyAdv && !ckyAdv.checked) ckyAdv.click();
            }
        }

        // CookieScript & OneTrust
        let perfInput = document.querySelector('#cookiescript_category_performance, input[id*="ot-group-id-C0002"]');
        let targetInput = document.querySelector('#cookiescript_category_targeting, input[id*="ot-group-id-C0004"]');
        if (perfInput || targetInput) {
            if (mode === 'only_analytics') {
                if (perfInput && !perfInput.checked) perfInput.click();
                if (targetInput && targetInput.checked) targetInput.click();
            } else if (mode === 'only_marketing') {
                if (perfInput && perfInput.checked) perfInput.click();
                if (targetInput && !targetInput.checked) targetInput.click();
            }
        }

        await new Promise(r => setTimeout(r, 600));

        // Guardar selección
        const saveSelectors = [
            '#cookiescript_save',
            '.save-preference-btn-handler',
            '#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowallSelection',
            '.cky-btn-save', '[data-cky-tag="save-button"]',
            'button[data-testid="uc-save-button"]'
        ];
        for (let s of saveSelectors) {
            let el = document.querySelector(s);
            if (el && el.offsetParent !== null) { el.click(); return "Guardado: " + s; }
        }
        for (let b of Array.from(document.querySelectorAll('button, a, input[type="button"]'))) {
            let t = (b.innerText || b.value || '').trim().toLowerCase();
            if (['guardar selección', 'guardar preferencias', 'guardar', 'save', 'confirmar opciones', 'allow selection'].some(term => t.includes(term))) {
                b.click(); return "Guardado: " + t;
            }
        }
        return "Configuración completada";
    }
    """
    try:
        return await page.evaluate(js_action, target_action)
    except Exception as e:
        return f"Error: {e}"

async def auditar_fase(browser, url, action=None):
    context = await browser.new_context()
    page = await context.new_page()
    pings = []
    
    def on_req(r):
        full_req = r.url
        try:
            if r.post_data:
                full_req += f"&{r.post_data}"
        except Exception:
            pass
        if is_google_consent_ping(full_req):
            pings.append(full_req)
            
    page.on("request", on_req)
    
    try:
        await page.goto(url, timeout=25000, wait_until="domcontentloaded")
    except Exception:
        pass
    
    await asyncio.sleep(2)
    
    action_info = "Sin interacción (Default)"
    if action:
        action_info = await interactuar_con_cmp(page, action)
        await asyncio.sleep(3.5)
        
    cookies = await context.cookies()
    await context.close()
    return cookies, pings, action_info

# ==============================================================================
# GENERACIÓN DEL INFORME WORD
# ==============================================================================

def generar_documento_word(domain, audit_data, baseline_names, analytics_new, marketing_new):
    doc = Document()
    doc.add_heading('AUDITORÍA TÉCNICA PRIVACY & CONSENT MODE V2', 0)
    doc.add_paragraph('Octubre 2026')
    doc.add_heading('Introducción.', 1)
    doc.add_paragraph('Este informe audita el comportamiento técnico de cookies y el envío de señales bajo Google Consent Mode v2 según las directrices de la AEPD y el RGPD.')
    doc.add_paragraph('Dominio evaluado: ' + domain)
    
    doc.add_heading('1.- Matriz de Parámetros Google Consent Mode v2', 1)
    table = doc.add_table(rows=1, cols=6)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = table.rows[0].cells
    hdr[0].text = "Parámetro GCM v2"
    hdr[1].text = "1. Default"
    hdr[2].text = "2. Rechazar"
    hdr[3].text = "3. Aceptar Todo"
    hdr[4].text = "4. Solo Analítica"
    hdr[5].text = "5. Solo Marketing"
    
    fases = ['default', 'reject', 'accept', 'analytics', 'marketing']
    filas = [
        ("ad_storage", lambda p: p['gcd_params']['ad_storage']['status'] if p['gcd_params'] else "N/D"),
        ("analytics_storage", lambda p: p['gcd_params']['analytics_storage']['status'] if p['gcd_params'] else "N/D"),
        ("ad_user_data", lambda p: p['gcd_params']['ad_user_data']['status'] if p['gcd_params'] else "N/D"),
        ("ad_personalization", lambda p: p['gcd_params']['ad_personalization']['status'] if p['gcd_params'] else "N/D"),
        ("Señal GCS", lambda p: p['gcs']),
        ("Cadena GCD", lambda p: p['gcd']),
        ("NPA (No Personalizado)", lambda p: p['npa']),
        ("DMA", lambda p: p['dma'])
    ]
    
    for label, extractor in filas:
        row = table.add_row().cells
        row[0].text = label
        for idx, f in enumerate(fases, 1):
            params = extract_consent_params(audit_data[f]['pings'])
            row[idx].text = str(extractor(params))
            
    doc.add_heading('2.- Inventario y Clasificación Forense de Cookies', 1)
    secciones = [
        ("2.1 Cookies en Aterrizaje Inicial (Default)", 'default'),
        ("2.2 Cookies tras Rechazar Todas", 'reject'),
        ("2.3 Cookies tras Aceptar Todas", 'accept'),
        ("2.4 Cookies tras Aceptar Solo Analítica", 'analytics'),
        ("2.5 Cookies tras Aceptar Solo Marketing", 'marketing')
    ]
    for tit, k in secciones:
        doc.add_heading(tit, 2)
        cookies = audit_data[k]['cookies']
        if cookies:
            c_table = doc.add_table(rows=1, cols=6)
            c_table.alignment = WD_TABLE_ALIGNMENT.CENTER
            chdr = c_table.rows[0].cells
            chdr[0].text = "Nombre"
            chdr[1].text = "Proveedor"
            chdr[2].text = "Duración"
            chdr[3].text = "Cat. en Web"
            chdr[4].text = "Debería Ser"
            chdr[5].text = "Diagnóstico"
            
            for c in cookies:
                c_info = enriquecer_cookie_forense(c, k, baseline_names, analytics_new, marketing_new)
                r_cells = c_table.add_row().cells
                r_cells[0].text = c_info['Nombre']
                r_cells[1].text = c_info['Proveedor']
                r_cells[2].text = c_info['Duración']
                r_cells[3].text = c_info['Categoría en Web']
                r_cells[4].text = c_info['Categoría Debería Ser']
                r_cells[5].text = c_info['Diagnóstico']
        else:
            doc.add_paragraph("No se detectaron cookies registradas.")

    doc_io = io.BytesIO()
    doc.save(doc_io)
    doc_io.seek(0)
    return doc_io

# ==============================================================================
# INTERFAZ STREAMLIT
# ==============================================================================

st.markdown("<h1 style='margin-bottom: 2px;'>🛡️ Privacy & Consent Mode v2 Auditor</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #64748b; font-size: 0.95rem; margin-bottom: 24px;'>Sistema automatizado de telemetría de privacidad, clasificación forense diferencial de cookies y señales DMA / Google Consent Mode v2</p>", unsafe_allow_html=True)

if "audit_data" not in st.session_state:
    st.session_state.audit_data = None
if "domain" not in st.session_state:
    st.session_state.domain = ""

c_input, c_btn = st.columns([4, 1])
with c_input:
    target_url = st.text_input("URL a auditar:", placeholder="https://es.art-hotel-commercianti.com/", label_visibility="collapsed")
with c_btn:
    btn_start = st.button("⚡ Iniciar Auditoría", type="primary", use_container_width=True)

if btn_start:
    if not target_url.strip().startswith("http"):
        st.error("Introduce una URL completa con https:// o http://")
    else:
        st.session_state.domain = urlparse(target_url).netloc
        progreso = st.progress(0, text="Levantando sandbox en la nube...")
        
        async def ejecutar_pruebas():
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"])
                
                progreso.progress(10, text="[1/5] Fase 1: Estado Default (Cookieless pings y cookies técnicas)...")
                c_def, p_def, a_def = await auditar_fase(browser, target_url, action=None)
                
                progreso.progress(30, text="[2/5] Fase 2: Rechazar Todas (Verificando bloqueo)...")
                c_rej, p_rej, a_rej = await auditar_fase(browser, target_url, action="reject")
                
                progreso.progress(50, text="[3/5] Fase 3: Aceptar Todas (Concesión total)...")
                c_acc, p_acc, a_acc = await auditar_fase(browser, target_url, action="accept")
                
                progreso.progress(70, text="[4/5] Fase 4: Solo Analítica (Rendimiento)...")
                c_ana, p_ana, a_ana = await auditar_fase(browser, target_url, action="only_analytics")
                
                progreso.progress(90, text="[5/5] Fase 5: Solo Marketing (Publicidad)...")
                c_mkt, p_mkt, a_mkt = await auditar_fase(browser, target_url, action="only_marketing")
                
                await browser.close()
                progreso.progress(100, text="¡Telemetría finalizada con éxito!")
                
                return {
                    "default": {"cookies": c_def, "pings": p_def, "action": a_def},
                    "reject": {"cookies": c_rej, "pings": p_rej, "action": a_rej},
                    "accept": {"cookies": c_acc, "pings": p_acc, "action": a_acc},
                    "analytics": {"cookies": c_ana, "pings": p_ana, "action": a_ana},
                    "marketing": {"cookies": c_mkt, "pings": p_mkt, "action": a_mkt}
                }

        try:
            st.session_state.audit_data = asyncio.run(ejecutar_pruebas())
            progreso.empty()
        except Exception as e:
            st.error(f"Error durante el análisis: {e}")

if st.session_state.audit_data:
    data = st.session_state.audit_data
    domain = st.session_state.domain
    st.markdown(f"<div style='margin-bottom: 20px; font-weight: 600; color: #34d399;'>● Auditoría completada para: <span style='color: #f8fafc;'>{domain}</span></div>", unsafe_allow_html=True)
    
    # Análisis diferencial de cookies para cotejar cómo las maneja la web
    def_names = {c['name'] for c in data['default']['cookies']}
    rej_names = {c['name'] for c in data['reject']['cookies']}
    baseline_names = def_names.union(rej_names)
    
    analytics_new = {c['name'] for c in data['analytics']['cookies']} - baseline_names
    marketing_new = {c['name'] for c in data['marketing']['cookies']} - baseline_names
    
    t_cm, t_ck, t_doc = st.tabs(["📊 Google Consent Mode v2", "🍪 Cookies por Sección", "📄 Generar Informe Word"])
    
    with t_cm:
        st.markdown("<h3 style='margin-bottom: 16px;'>Telemetría de Señales (5 Fases)</h3>", unsafe_allow_html=True)
        cols = st.columns(5)
        fases = [
            ("1. Default", 'default', "G100"),
            ("2. Rechazar", 'reject', "G100"),
            ("3. Aceptar Todo", 'accept', "G111"),
            ("4. Solo Analítica", 'analytics', "G101"),
            ("5. Solo Marketing", 'marketing', "G110")
        ]
        
        parsed_fases = {}
        for col, (label, key, expected_gcs) in zip(cols, fases):
            with col:
                p = extract_consent_params(data[key]['pings'])
                parsed_fases[key] = p
                
                badge_html = f"<div class='cyber-badge-ok'>✓ Coincide {expected_gcs}</div>" if expected_gcs in p['gcs'] else f"<div class='cyber-badge-warn'>⚠ Esperado {expected_gcs}</div>"
                
                panel_html = f"""
                <div class="cyber-panel">
                    <div class="cyber-panel-title">{label}</div>
                    <div class="cyber-panel-val">{p['gcs']}</div>
                    {badge_html}
                    <div class="cyber-console">
                        GCD: {p['gcd']}<br>
                        NPA: {p['npa']} | DMA: {p['dma']}
                    </div>
                    <div class="cyber-action">Acción: {data[key]['action']}</div>
                </div>
                """
                st.markdown(panel_html, unsafe_allow_html=True)
                
        st.markdown("<br><h4 style='color: #cbd5e1;'>Matriz de Decodificación de Parámetros GCM v2</h4>", unsafe_allow_html=True)
        
        table_rows = []
        param_keys = [
            ("ad_storage", "Cookies publicitarias"),
            ("analytics_storage", "Cookies estadísticas/analítica"),
            ("ad_user_data", "Datos de usuario a Google Ads"),
            ("ad_personalization", "Personalización y Remarketing")
        ]
        
        for p_key, p_desc in param_keys:
            row = {"Parámetro GCM v2": f"{p_key} ({p_desc})"}
            for _, f_key, _ in fases:
                gcd_info = parsed_fases[f_key]['gcd_params']
                if gcd_info and p_key in gcd_info:
                    item = gcd_info[p_key]
                    row[f_key] = f"{item['icon']} {item['status']} ({item['letter']})"
                else:
                    row[f_key] = "⚪ N/D"
            table_rows.append(row)
            
        st.dataframe(
            table_rows,
            column_config={
                "Parámetro GCM v2": st.column_config.TextColumn("Parámetro GCM v2", width="medium"),
                "default": "1. Default",
                "reject": "2. Rechazar",
                "accept": "3. Aceptar Todo",
                "analytics": "4. Solo Analítica",
                "marketing": "5. Solo Marketing"
            },
            use_container_width=True,
            hide_index=True
        )

    with t_ck:
        st.markdown("<h3 style='margin-bottom: 16px;'>Inventario Forense Diferencial y Diagnóstico Legal</h3>", unsafe_allow_html=True)
        sec_names = {
            "default": "1. Aterrizaje Inicial (Default)",
            "reject": "2. Tras Rechazar Todas",
            "accept": "3. Tras Aceptar Todas",
            "analytics": "4. Tras Aceptar Solo Analítica",
            "marketing": "5. Tras Aceptar Solo Marketing"
        }
        sel_tab = st.selectbox("Selecciona la casuística a inspeccionar:", list(sec_names.keys()), format_func=lambda x: sec_names[x])
        c_list = data[sel_tab]['cookies']
        
        enriched_cookies = [enriquecer_cookie_forense(c, sel_tab, baseline_names, analytics_new, marketing_new) for c in c_list]
        total_infracciones = sum(1 for c in enriched_cookies if "❌" in c['Diagnóstico'])
        
        col_m1, col_m2 = st.columns([1, 4])
        with col_m1:
            st.metric("Total Cookies", len(c_list))
        with col_m2:
            if total_infracciones > 0:
                st.markdown(f"<div style='margin-top: 14px; padding: 10px; background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 8px; color: #f87171; font-weight: 600;'>⚠️ Se han detectado {total_infracciones} cookies en presunta infracción (instaladas sin el consentimiento legal exigido).</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='margin-top: 14px; padding: 10px; background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 8px; color: #34d399; font-weight: 600;'>✅ No se detectan anomalías de consentimiento en las cookies de esta fase.</div>", unsafe_allow_html=True)

        st.write("")
        if enriched_cookies:
            st.dataframe(
                enriched_cookies,
                column_config={
                    "Nombre": st.column_config.TextColumn("Nombre Cookie", width="medium"),
                    "Proveedor": st.column_config.TextColumn("Proveedor / Origen", width="medium"),
                    "Duración": st.column_config.TextColumn("Duración", width="small"),
                    "Categoría en Web": st.column_config.TextColumn("Cómo la gestiona la Web", width="medium"),
                    "Categoría Debería Ser": st.column_config.TextColumn("Categoría Canónica Recomendada", width="medium"),
                    "Diagnóstico": st.column_config.TextColumn("Diagnóstico Legal", width="medium"),
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No hay cookies guardadas en esta fase.")

    with t_doc:
        st.markdown("<h3 style='margin-bottom: 16px;'>Generación y Descarga de Informe Oficial</h3>", unsafe_allow_html=True)
        st.markdown("<p style='color: #94a3b8;'>Exporta el informe en formato Word estructurado con todas las tablas comparativas y el inventario técnico listo para enviar a cliente o adjuntar en auditoría.</p>", unsafe_allow_html=True)
        doc_bytes = generar_documento_word(domain, data, baseline_names, analytics_new, marketing_new)
        nombre_archivo = f"{domain} - Auditoría cookies y CMP.docx"
        st.download_button(
            label=f"📥 Descargar Informe Completo (.docx)",
            data=doc_bytes,
            file_name=nombre_archivo,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary",
            key="download_doc_btn"
        )
