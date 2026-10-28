import streamlit as st
import asyncio
from playwright.async_api import async_playwright
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from urllib.parse import urlparse, parse_qs
import urllib.request
import csv
import io
import os
import re
import time

st.set_page_config(
    page_title="Privacy & Google Consent Mode Auditor",
    page_icon="🛡️",
    layout="wide"
)

# Estilos visuales Cybersecurity Dark Mode con Alto Contraste
st.markdown("""
<style>
/* Fondo general y tipografía */
.stApp {
    background-color: #07090e;
    color: #e2e8f0;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Encabezados y títulos con máximo contraste */
h1, h2, h3, h4 {
    color: #ffffff !important;
    font-weight: 700;
    letter-spacing: -0.5px;
}

/* Tarjetas Cybersecurity */
.cyber-panel {
    background: #0f1626;
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
    font-weight: 700;
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
    background: rgba(16, 185, 129, 0.18);
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.4);
    border-radius: 4px;
    padding: 3px 8px;
    font-size: 0.75rem;
    font-weight: 700;
    margin-top: 6px;
}
.cyber-badge-warn {
    display: inline-block;
    background: rgba(245, 158, 11, 0.18);
    color: #fbbf24;
    border: 1px solid rgba(245, 158, 11, 0.4);
    border-radius: 4px;
    padding: 3px 8px;
    font-size: 0.75rem;
    font-weight: 700;
    margin-top: 6px;
}
.cyber-console {
    background: #05070b;
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
    font-size: 0.72rem;
    color: #8194ad;
    margin-top: 6px;
}

/* Tarjeta de Diagnóstico Ejecutiva */
.diag-container {
    background: #0f1626;
    border: 1px solid #1e293b;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 24px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
}
.diag-title {
    font-size: 1rem;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 12px;
}
.diag-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 6px;
    font-size: 0.85rem;
    font-weight: 800;
    margin-bottom: 10px;
}

/* Banner de Recomendación Estratégica */
.rec-box {
    background: linear-gradient(135deg, rgba(0, 240, 255, 0.08) 0%, rgba(2, 132, 199, 0.12) 100%);
    border: 1px solid #00f0ff;
    border-radius: 12px;
    padding: 18px 22px;
    margin-top: 18px;
    margin-bottom: 24px;
    box-shadow: 0 0 20px rgba(0, 240, 255, 0.15);
}

/* Inputs de texto */
.stTextInput > div > div > input {
    background-color: #0f1626 !important;
    color: #ffffff !important;
    border: 1px solid #23304a !important;
    border-radius: 8px !important;
    font-size: 0.95rem;
}
.stTextInput > div > div > input:focus {
    border-color: #00f0ff !important;
    box-shadow: 0 0 12px rgba(0, 240, 255, 0.25) !important;
}

/* Botón Neón */
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

/* Sistema de Pestañas persistente con st.radio */
div[data-testid="stRadio"] > label {
    display: none !important;
}
div[data-testid="stRadio"] > div {
    display: flex;
    flex-direction: row;
    gap: 12px;
    border-bottom: 1px solid #1e293b;
    padding-bottom: 14px;
    margin-bottom: 24px;
    background: transparent;
}
div[data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child {
    display: none !important;
}
div[data-testid="stRadio"] div[role="radiogroup"] > label {
    background-color: #0f1626 !important;
    border: 1px solid #1e293b !important;
    border-radius: 8px !important;
    padding: 10px 24px !important;
    cursor: pointer !important;
    transition: all 0.25s ease !important;
    margin: 0 !important;
    display: flex !important;
    align-items: center !important;
}
div[data-testid="stRadio"] div[role="radiogroup"] > label:hover {
    border-color: #00f0ff !important;
    background-color: #162035 !important;
}
div[data-testid="stRadio"] div[role="radiogroup"] > label:hover p {
    color: #00f0ff !important;
}
div[data-testid="stRadio"] div[role="radiogroup"] > label p {
    color: #e2e8f0 !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    margin: 0 !important;
    letter-spacing: 0.3px !important;
}
div[data-testid="stRadio"] div[role="radiogroup"] > label[data-checked="true"],
div[data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) {
    background-color: #162035 !important;
    border: 1px solid #00f0ff !important;
    box-shadow: 0 0 16px rgba(0, 240, 255, 0.3) !important;
}
div[data-testid="stRadio"] div[role="radiogroup"] > label[data-checked="true"] p,
div[data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) p {
    color: #00f0ff !important;
}

/* Selectbox */
div[data-testid="stSelectbox"] label p {
    color: #cbd5e1 !important;
    font-size: 0.9rem !important;
    font-weight: 600 !important;
}
div[data-testid="stSelectbox"] > div > div {
    background-color: #0f1626 !important;
    border: 1px solid #23304a !important;
    color: #ffffff !important;
    border-radius: 8px !important;
}
div[data-testid="stSelectbox"] svg {
    fill: #00f0ff !important;
}

/* Dataframe */
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

# Base canónica pre-cargada con descripciones en español
BUILTIN_DB = {
    "__cf_ob": ("Cloudflare", "Técnica / Necesaria", "Always Online: Ofrece copia en caché del sitio si el servidor web no responde."),
    "_cf_ob": ("Cloudflare", "Técnica / Necesaria", "Always Online: Resiliencia del sitio ante caídas del servidor de origen."),
    "cf_ob_info": ("Cloudflare", "Técnica / Necesaria", "Diagnóstico de respuesta y caché de contingencia Always Online."),
    "cf_use_ob": ("Cloudflare", "Técnica / Necesaria", "Control de redirección hacia la copia estática Always Online."),
    "__cf_bm": ("Cloudflare", "Técnica / Necesaria", "Bot Management: Gestiona el tráfico entrante para bloquear bots maliciosos."),
    "_cf_bm": ("Cloudflare", "Técnica / Necesaria", "Bot Management: Mitigación de scraping y peticiones automáticas."),
    "cf_clearance": ("Cloudflare", "Técnica / Necesaria", "Almacena la validación de haber superado un desafío Captcha o control de seguridad."),
    "_cfuvid": ("Cloudflare", "Técnica / Necesaria", "Rate Limiting: Protección contra ataques por denegación de servicio a nivel de usuario."),
    "__cflb": ("Cloudflare", "Técnica / Necesaria", "Balanceo de carga: Asigna el usuario al mismo servidor en sesiones activas."),
    "sessionid": ("Framework Django / Python", "Técnica / Necesaria", "Identificador de sesión autenticada y navegación segura del usuario."),
    "django_language": ("Framework Django", "Técnica / Necesaria", "Almacena la selección de idioma preferido por el visitante."),
    "csrftoken": ("Seguridad Web", "Técnica / Necesaria", "Token de protección criptográfica contra ataques Cross-Site Request Forgery."),
    "phpsessid": ("Servidor PHP", "Técnica / Necesaria", "Conserva las variables de sesión del usuario en el servidor."),
    "jsessionid": ("Servidor Java / Spring", "Técnica / Necesaria", "Vincula al usuario con su sesión activa en el servidor de aplicaciones."),
    "asp.net_sessionid": ("Servidor Microsoft ASP.NET", "Técnica / Necesaria", "Mantiene la sesión de usuario activa entre peticiones HTTP."),
    "cookiescriptconsent": ("CookieScript (CMP)", "Técnica / Necesaria", "Registra las categorías de cookies que el usuario ha autorizado."),
    "optanonconsent": ("OneTrust (CMP)", "Técnica / Necesaria", "Almacena el estado granular del consentimiento del usuario."),
    "optanonalertboxclosed": ("OneTrust (CMP)", "Técnica / Necesaria", "Indica si el usuario ha interactuado y cerrado el aviso de cookies."),
    "cookieyes-consent": ("CookieYes (CMP)", "Técnica / Necesaria", "Guarda el registro de consentimiento para auditoría de privacidad."),
    "didomi_token": ("Didomi (CMP)", "Técnica / Necesaria", "Token de consentimiento cifrado según el estándar IAB TCF v2.2."),
    "_ga": ("Google Analytics 4", "Analítica / Rendimiento", "Asigna un ID pseudo-anónimo único para distinguir usuarios e interacciones."),
    "_gid": ("Google Analytics", "Analítica / Rendimiento", "Registra un identificador temporal de 24 horas para métricas de sesión."),
    "_gat": ("Google Analytics", "Analítica / Rendimiento", "Limita el porcentaje de solicitudes para evitar la saturación de datos."),
    "_clck": ("Microsoft Clarity", "Analítica / Rendimiento", "Identificador de usuario para análisis de navegación y mapas de calor."),
    "_clsk": ("Microsoft Clarity", "Analítica / Rendimiento", "Agrupa las páginas vistas de un mismo usuario dentro de una única sesión."),
    "vuid": ("Vimeo Player", "Analítica / Rendimiento", "Mide el rendimiento del reproductor de vídeo y estadísticas de visualización."),
    "_fbp": ("Meta Pixel (Facebook)", "Marketing / Publicidad", "Registra visitas entre sitios web para entregar anuncios dirigidos en redes de Meta."),
    "_fbc": ("Meta Pixel (Facebook)", "Marketing / Publicidad", "Almacena el identificador del clic publicitario (fbclid) para atribución."),
    "ide": ("Google DoubleClick", "Marketing / Publicidad", "Registra y reporta las acciones del usuario tras ver o hacer clic en anuncios."),
    "test_cookie": ("Google DoubleClick", "Marketing / Publicidad", "Comprueba si el navegador del usuario tiene habilitada la escritura de cookies."),
    "__gads": ("Google Ad Manager", "Marketing / Publicidad", "Controla la frecuencia de los anuncios y la eficacia de las campañas."),
    "__gpi": ("Google Publisher Tag", "Marketing / Publicidad", "Identificador de editor de Google para personalización y frecuencia."),
    "_gcl_au": ("Google AdSense / Ads", "Marketing / Publicidad", "Medición de conversiones y pruebas de eficacia de la red publicitaria."),
    "_gcl_aw": ("Google Ads", "Marketing / Publicidad", "Atribuye la conversión generada por un usuario tras hacer clic en un anuncio."),
    "nid": ("Google LLC", "Marketing / Publicidad", "Construye un perfil de intereses del usuario para mostrar anuncios personalizados."),
    "muid": ("Microsoft Advertising (Bing)", "Marketing / Publicidad", "Sincroniza el ID de usuario entre dominios de Microsoft para campañas.")
}

CATEGORY_MAP = {
    'functional': 'Técnica / Necesaria',
    'analytics': 'Analítica / Rendimiento',
    'marketing': 'Marketing / Publicidad',
    'security': 'Técnica / Necesaria',
    'personalization': 'Personalización / Funcional'
}

@st.cache_data(ttl=86400, show_spinner=False)
def obtener_base_datos_global():
    exact_db = dict(BUILTIN_DB)
    wildcard_list = [
        ("_{0,2}cf.*", "Cloudflare", "Técnica / Necesaria", "Infraestructura, mitigación de bots y aceleración de red CDN."),
        ("_ga_.*", "Google Analytics 4", "Analítica / Rendimiento", "Almacena el estado de sesión y flujo de eventos en la propiedad GA4."),
        ("_gat_.*", "Google Analytics", "Analítica / Rendimiento", "Regulación técnica de peticiones al endpoint de analítica."),
        ("_hj.*", "Hotjar", "Analítica / Rendimiento", "Mapas de calor y análisis de interacción del usuario en la interfaz."),
        ("_pk_.*", "Matomo / Piwik", "Analítica / Rendimiento", "Analítica web autoalojada y seguimiento de visitas."),
        ("_uet.*", "Microsoft Advertising", "Marketing / Publicidad", "Universal Event Tracking para seguimiento de conversiones en Bing."),
        ("tt_.*", "TikTok Pixel", "Marketing / Publicidad", "Seguimiento publicitario y optimización de campañas de TikTok."),
        ("cto_.*", "Criteo", "Marketing / Publicidad", "Retargeting publicitario dinámico y entrega de anuncios."),
        ("wp-.*", "WordPress CMS", "Técnica / Necesaria", "Gestión de sesión administrativa y preferencias de la interfaz WordPress."),
        ("woocommerce_.*", "WooCommerce", "Técnica / Necesaria", "Persistencia de productos y cálculo del carrito de compra."),
        ("pll_.*", "Polylang", "Técnica / Necesaria", "Mantenimiento del idioma activo durante la navegación.")
    ]
    
    url = "https://raw.githubusercontent.com/jkwakman/Open-Cookie-Database/master/open-cookie-database.csv"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=6) as response:
            content = response.read().decode('utf-8')
            reader = csv.DictReader(io.StringIO(content))
            for row in reader:
                c_name = row.get('Cookie / Data Key name', '').strip()
                if not c_name:
                    continue
                platform = row.get('Platform', 'Proveedor Web').strip()
                raw_cat = row.get('Category', 'Functional').strip().lower()
                cat = CATEGORY_MAP.get(raw_cat, 'Técnica / Necesaria')
                desc = row.get('Description', '').strip() or 'Finalidad técnica estándar registrada en Open Cookie Database.'
                is_wildcard = row.get('Wildcard', '0').strip() == '1' or c_name.endswith('*')
                
                clean = c_name.rstrip('*').lower()
                if is_wildcard:
                    wildcard_list.append((f"^{clean}.*", platform, cat, desc))
                else:
                    if clean not in exact_db:
                        exact_db[clean] = (platform, cat, desc)
    except Exception:
        pass
        
    return exact_db, wildcard_list

def consultar_proposito_cookie(name, domain, exact_db, wildcard_list):
    n = name.strip().lower()
    d = domain.strip().lower()
    
    if n in exact_db:
        return exact_db[n]
        
    for pattern, prov, cat, desc in wildcard_list:
        if re.match(pattern, n, re.IGNORECASE):
            return prov, cat, desc
            
    domain_rules = [
        (r'cloudflare\.com$', "Cloudflare Inc.", "Técnica / Necesaria", "Seguridad perimetral y entrega de contenidos en red CDN."),
        (r'doubleclick\.net$', "Google DoubleClick", "Marketing / Publicidad", "Publicidad programática y optimización de pujas."),
        (r'facebook\.com$', "Meta Platforms Inc.", "Marketing / Publicidad", "Píxel de seguimiento social y optimización de audiencias."),
        (r'vimeo\.com$', "Vimeo Inc.", "Analítica / Rendimiento", "Métricas del reproductor embebido de vídeo."),
        (r'clarity\.ms$', "Microsoft Clarity", "Analítica / Rendimiento", "Telemetría y análisis de experiencia de usuario.")
    ]
    for dom_regex, prov, cat, desc in domain_rules:
        if re.search(dom_regex, d):
            return prov, cat, desc
            
    if re.search(r'(sess|csrf|token|auth|security|login|nonce|checkout|cart|carrito|pedido|lang|idioma)', n):
        return f"Propio ({domain})", "Técnica / Necesaria", "Sesión de usuario, seguridad de formularios o preferencia lingüística."
    if re.search(r'(analy|metric|stats|pageview|visitor|tracker|heatmap)', n):
        return f"Tercero Analítico ({domain})", "Analítica / Rendimiento", "Medición de audiencia y analítica de navegación."
    if re.search(r'(pixel|banner|campaign|camp|promo|retarget|adserver|affiliate)', n):
        return f"Red Publicitaria ({domain})", "Marketing / Publicidad", "Seguimiento publicitario y medición de campañas."

    return f"Propietario / Sin firma ({domain})", "Por categorizar", "Finalidad específica no indexada en repositorios públicos."

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

def enriquecer_cookie_forense(cookie, phase_key, baseline_names, analytics_new, marketing_new, exact_db, wildcard_list):
    name = cookie.get('name', '')
    domain = cookie.get('domain', '')
    expires = cookie.get('expires', -1)
    duracion = calcular_duracion(expires)
    
    prov, cat_recomendada, proposito = consultar_proposito_cookie(name, domain, exact_db, wildcard_list)
    is_in_baseline = name in baseline_names
    
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

    if phase_key in ['default', 'reject']:
        if "Analítica" in cat_recomendada or "Marketing" in cat_recomendada:
            diagnostico = "❌ Infracción (Fuga sin consentimiento previo)"
        elif cat_recomendada == "Por categorizar":
            diagnostico = "⚠️ Por verificar (Sospecha de fuga)"
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
        "Propósito / Finalidad": proposito,
        "Duración": duracion,
        "Categoría en Web": cat_web,
        "Categoría Debería Ser": cat_recomendada,
        "Diagnóstico": diagnostico,
        "Dominio": domain,
        "Segura": "Sí" if cookie.get('secure') else "No"
    }

# ==============================================================================
# AUDITORÍA DE IMPLEMENTACIÓN Y ORDEN DE SCRIPTS DE CMP
# ==============================================================================

def analizar_implementacion_cmp(cmp_data, raw_html):
    detected_cmp = cmp_data.get('detectedCmp', 'No detectado')
    cmp_src = cmp_data.get('cmpScriptSrc', '')
    gtm_ids = cmp_data.get('gtmIds', [])
    cmp_loc = cmp_data.get('cmpLocation', 'No localizado')
    has_consent_script = cmp_data.get('hasConsentDefaultScript', False)
    order = cmp_data.get('order', {})
    
    pos_consent = order.get('posConsent', -1)
    pos_cmp = order.get('posCmp', -1)
    pos_gtm = order.get('posGtm', -1)
    
    # Comprobar si está en el código fuente HTML original
    is_hardcoded = False
    if cmp_src and cmp_src in raw_html:
        is_hardcoded = True
    elif detected_cmp != "No detectado / Banner a medida" and any(k in raw_html.lower() for k in ['cookie-script.com', 'cookielaw.org', 'cookiebot.com', 'cookieyes.com', 'didomi.io', 'usercentrics']):
        is_hardcoded = True
        
    if is_hardcoded:
        metodo = "Código Fuente (Hardcoded en HTML)"
        metodo_badge = "Código Fuente"
        metodo_color = "#38bdf8"
    elif len(gtm_ids) > 0 and (detected_cmp != "No detectado / Banner a medida"):
        metodo = "Google Tag Manager (GTM) o Inyección Dinámica"
        metodo_badge = "Vía GTM"
        metodo_color = "#34d399"
    else:
        metodo = "No identificado con certeza"
        metodo_badge = "Indeterminado"
        metodo_color = "#94a3b8"

    orden_items = []
    
    # 1. Consent Mode Default vs CMP
    if pos_consent != -1 and pos_cmp != -1:
        if pos_consent < pos_cmp:
            orden_items.append(("✅ Secuencia Correcta", "#34d399", f"Consent Mode Default (Script #{pos_consent + 1}) se ejecuta antes del script del CMP (Script #{pos_cmp + 1})."))
        else:
            orden_items.append(("❌ Riesgo de Carrera", "#ef4444", f"El CMP (Script #{pos_cmp + 1}) carga antes de la declaración default de Consent Mode (Script #{pos_consent + 1}). Puede provocar discrepancias en los primeros pings de telemetría."))
    elif pos_consent == -1 and is_hardcoded:
        orden_items.append(("⚠️ Sin Default en Código", "#fbbf24", "No se detecta la llamada gtag('consent', 'default') en el código fuente HTML previo al CMP."))
        
    # 2. Consent Mode Default vs GTM
    if pos_consent != -1 and pos_gtm != -1:
        if pos_consent < pos_gtm:
            orden_items.append(("✅ Secuencia Correcta", "#34d399", f"Consent Mode Default se inicializa antes del contenedor de GTM ({', '.join(gtm_ids) or 'GTM'})."))
        else:
            orden_items.append(("❌ Infracción / Riesgo Crítico", "#ef4444", f"GTM se carga antes de que Consent Mode fije el estado Default. Las etiquetas de analítica y marketing podrían dispararse sin respetar los estados denegados."))

    # 3. CMP vs GTM
    if pos_cmp != -1 and pos_gtm != -1:
        if pos_cmp < pos_gtm:
            orden_items.append(("ℹ️ Ubicación", "#00f0ff", f"El script del CMP se ubica antes de GTM en {cmp_loc}."))
        else:
            orden_items.append(("ℹ️ Ubicación", "#a855f7", f"GTM se ubica antes del script del CMP en {cmp_loc}."))

    if not orden_items:
        orden_items.append(("ℹ️ Diagnóstico", "#94a3b8", "No se han detectado scripts simultáneos de Consent Mode, CMP y GTM en el HTML base para auditar la secuencia."))

    recomendacion = (
        "La recomendación técnica principal SIEMPRE es centralizar toda la gestión en Google Tag Manager (GTM). "
        "Tanto la integración del CMP como la inicialización y actualización de Google Consent Mode deben articularse "
        "preferentemente mediante la plantilla comunitaria oficial del CMP en GTM. Esto evita discrepancias de orden en el código fuente, "
        "sincroniza los disparadores con el evento de consentimiento y facilita el mantenimiento unificado de etiquetas."
    )

    return {
        "detected_cmp": detected_cmp,
        "metodo": metodo,
        "metodo_badge": metodo_badge,
        "metodo_color": metodo_color,
        "gtm_ids": gtm_ids if gtm_ids else ["No detectado"],
        "cmp_loc": cmp_loc,
        "orden_items": orden_items,
        "recomendacion": recomendacion
    }

# ==============================================================================
# DIAGNÓSTICO Y TELEMETRÍA GOOGLE CONSENT MODE
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

def diagnosticar_consent_mode(audit_data):
    p_def = audit_data.get('default', {}).get('pings', [])
    p_rej = audit_data.get('reject', {}).get('pings', [])
    p_acc = audit_data.get('accept', {}).get('pings', [])
    p_ana = audit_data.get('analytics', {}).get('pings', [])
    p_mkt = audit_data.get('marketing', {}).get('pings', [])

    all_pings = p_def + p_rej + p_acc + p_ana + p_mkt

    has_gcs = False
    has_valid_gcd = False
    gcd_sample = None
    v_param = None

    for ping in all_pings:
        parsed = parse_qs(urlparse(ping).query)
        if not parsed:
            parsed = parse_qs(ping)
        if 'gcs' in parsed:
            has_gcs = True
        if 'v' in parsed and not v_param:
            v_param = parsed['v'][0]
        if 'gcd' in parsed:
            raw_gcd = parsed['gcd'][0]
            if raw_gcd and raw_gcd != '-' and not raw_gcd.startswith('--'):
                if re.match(r'^1[0-9][a-zA-Z]', raw_gcd):
                    has_valid_gcd = True
                    gcd_sample = raw_gcd

    # 1. Determinación de Versión (v1 vs v2)
    if has_valid_gcd or v_param == '2':
        version = "Google Consent Mode v2"
        badge_ver = "v2 (Vigente)"
        badge_ver_color = "#34d399"
        if has_valid_gcd:
            desc_ver = f"Se detecta la cadena de consentimiento regulatoria de la DMA ('gcd': {gcd_sample}) y protocolo de medición v={v_param or '2'}. Transmite de forma granular los parámetros obligatorios (ad_storage, analytics_storage, ad_user_data, ad_personalization)."
        else:
            desc_ver = f"Se detecta el protocolo de telemetría v={v_param} compatible con Google Analytics 4."
    elif has_gcs:
        version = "Google Consent Mode v1"
        badge_ver = "v1 (Obsoleto)"
        badge_ver_color = "#fbbf24"
        desc_ver = "El parámetro 'gcd' no está presente o se transmite con guiones en lugar de valores. Solo se envían señales heredadas 'gcs'. La web no cumple con los requisitos exigidos por la Digital Markets Act (DMA)."
    else:
        version = "No detectado"
        badge_ver = "Sin señales"
        badge_ver_color = "#ef4444"
        desc_ver = "No se han detectado llamadas de red de Google con parámetros de consentimiento ('gcs' ni 'gcd')."

    # 2. Determinación de Tipo (Básico vs Avanzado)
    default_has_pings = len(p_def) > 0
    default_has_g100 = any(('gcs=G100' in p or 'gcs=G10' in p) for p in p_def)

    if default_has_pings and (default_has_g100 or has_valid_gcd):
        tipo = "Consent Mode Avanzado (Advanced)"
        badge_tipo = "Avanzado"
        badge_tipo_color = "#00f0ff"
        desc_tipo = "En el aterrizaje inicial (Fase Default, previo a cualquier clic), las etiquetas se cargan y disparan pings de modelado en modo cookieless transmitiendo 'G100' y valores de denegación predeterminada (letras 'p' o 'q')."
    elif len(p_acc) > 0 and not default_has_pings:
        tipo = "Consent Mode Básico (Basic)"
        badge_tipo = "Básico"
        badge_tipo_color = "#a855f7"
        desc_tipo = "Las etiquetas de Google se encuentran totalmente bloqueadas a nivel de disparador antes del consentimiento (cero llamadas collect en fase Default y Rechazo). Solo disparan peticiones tras la aceptación expresa ('G111')."
    elif default_has_pings:
        tipo = "Consent Mode Avanzado (Telemetría previa activa)"
        badge_tipo = "Avanzado"
        badge_tipo_color = "#00f0ff"
        desc_tipo = "Se registran llamadas de red previas al consentimiento sin que el usuario haya interactuado con el banner."
    else:
        tipo = "No determinado"
        badge_tipo = "Indeterminado"
        badge_tipo_color = "#94a3b8"
        desc_tipo = "Sin datos de tráfico suficientes en la fase Default para confirmar el tipo de implementación."

    return {
        "version": version,
        "badge_ver": badge_ver,
        "badge_ver_color": badge_ver_color,
        "desc_ver": desc_ver,
        "tipo": tipo,
        "badge_tipo": badge_tipo,
        "badge_tipo_color": badge_tipo_color,
        "desc_tipo": desc_tipo
    }

async def interactuar_con_cmp(page, target_action):
    js_action = """
    async (mode) => {
        // 1. APIS NATIVAS
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

        // 2. BOTONES DIRECTOS (CAPA 1)
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

        // 3. SEGUNDA CAPA (CONFIGURACIÓN GRANULAR)
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

async def auditar_fase(browser, url, action=None, inspect_cmp=False):
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
    
    cmp_tech_info = None
    raw_html = ""
    if inspect_cmp:
        try:
            raw_html = await page.content()
            js_inspect = """
            () => {
                const cmpSignatures = [
                    { name: "CookieScript", global: "CookieScript", pattern: /cdn\\.cookie-script\\.com/i },
                    { name: "OneTrust", global: "OneTrust", pattern: /(cdn\\.cookielaw\\.org|onetrust\\.com)/i },
                    { name: "Cookiebot", global: "Cookiebot", pattern: /consent\\.cookiebot\\.com/i },
                    { name: "CookieYes", global: "cookieyes", pattern: /cdn-cookieyes\\.com/i },
                    { name: "Didomi", global: "Didomi", pattern: /didomi\\.io/i },
                    { name: "Usercentrics", global: "UC_UI", pattern: /app\\.usercentrics\\.eu/i },
                    { name: "Axeptio", global: "axeptioSDK", pattern: /axept\\.io/i },
                    { name: "Iubenda", global: "_iub", pattern: /iubenda_cs/i }
                ];

                let detectedCmp = "No detectado / Banner a medida";
                let cmpScriptSrc = null;
                let cmpElement = null;

                for (const cmp of cmpSignatures) {
                    if (window[cmp.global]) {
                        detectedCmp = cmp.name;
                        break;
                    }
                }

                const scripts = Array.from(document.querySelectorAll('script'));
                scripts.forEach(s => {
                    const src = s.src || '';
                    for (const cmp of cmpSignatures) {
                        if (cmp.pattern.test(src)) {
                            detectedCmp = cmp.name;
                            cmpScriptSrc = src;
                            cmpElement = s;
                        }
                    }
                });

                const gtmScripts = scripts.filter(s => (s.src || '').includes('googletagmanager.com/gtm.js'));
                const gtmIds = [];
                gtmScripts.forEach(s => {
                    const m = (s.src || '').match(/[?&]id=(GTM-[A-Z0-9]+)/);
                    if (m && !gtmIds.includes(m[1])) gtmIds.push(m[1]);
                });
                if (window.google_tag_manager) {
                    Object.keys(window.google_tag_manager).forEach(k => {
                        if (k.startsWith('GTM-') && !gtmIds.includes(k)) gtmIds.push(k);
                    });
                }

                let consentScript = null;
                scripts.forEach(s => {
                    const txt = s.innerText || s.textContent || '';
                    if (txt.includes('consent') && txt.includes('default')) {
                        consentScript = s;
                    }
                });

                const posConsent = consentScript ? scripts.indexOf(consentScript) : -1;
                const posCmp = cmpElement ? scripts.indexOf(cmpElement) : -1;
                const posGtm = gtmScripts.length > 0 ? scripts.indexOf(gtmScripts[0]) : -1;

                let cmpLocation = "No localizado en scripts";
                if (cmpElement) {
                    cmpLocation = document.head.contains(cmpElement) ? "<head>" : "<body>";
                }

                return {
                    detectedCmp,
                    cmpScriptSrc,
                    cmpLocation,
                    gtmIds,
                    hasConsentDefaultScript: posConsent !== -1,
                    order: {
                        posConsent,
                        posCmp,
                        posGtm,
                        totalScripts: scripts.length
                    }
                };
            }
            """
            cmp_tech_info = await page.evaluate(js_inspect)
        except Exception:
            pass

    action_info = "Sin interacción (Default)"
    if action:
        action_info = await interactuar_con_cmp(page, action)
        await asyncio.sleep(3.5)
        
    cookies = await context.cookies()
    await context.close()
    
    if inspect_cmp:
        return cookies, pings, action_info, cmp_tech_info, raw_html
    return cookies, pings, action_info

# ==============================================================================
# GENERACIÓN DE DOCUMENTO WORD
# ==============================================================================

def generar_documento_word(domain, audit_data, baseline_names, analytics_new, marketing_new, exact_db, wildcard_list, cmp_audit):
    doc = Document()
    doc.add_heading('AUDITORÍA TÉCNICA PRIVACY & GOOGLE CONSENT MODE', 0)
    doc.add_paragraph('Octubre 2026')
    doc.add_heading('Introducción.', 1)
    doc.add_paragraph('Este informe audita el comportamiento técnico de cookies, la implementación del CMP y el envío de señales bajo Google Consent Mode según las directrices de la AEPD y el RGPD.')
    doc.add_paragraph('Dominio evaluado: ' + domain)
    
    # 1. Auditoría del CMP
    doc.add_heading('1.- Implementación del CMP y Contenedores', 1)
    doc.add_paragraph(f"- Plataforma CMP detectada: {cmp_audit['detected_cmp']}")
    doc.add_paragraph(f"- Método de implementación: {cmp_audit['metodo']}")
    doc.add_paragraph(f"- Ubicación en el documento: {cmp_audit['cmp_loc']}")
    doc.add_paragraph(f"- Contenedor(es) Google Tag Manager: {', '.join(cmp_audit['gtm_ids'])}")
    
    doc.add_heading('1.1 Auditoría del orden de carga de scripts en código fuente', 2)
    for estado, _, detalle in cmp_audit['orden_items']:
        doc.add_paragraph(f"[{estado}] {detalle}")
        
    doc.add_heading('1.2 Dictamen y Recomendación Técnica', 2)
    doc.add_paragraph(cmp_audit['recomendacion'])
    
    # 2. Diagnóstico de Google Consent Mode
    diag = diagnosticar_consent_mode(audit_data)
    doc.add_heading('2.- Google Consent Mode', 1)
    doc.add_heading('2.1 Diagnóstico de Versión y Tipo de Implementación', 2)
    doc.add_paragraph(f"- Versión detectada: {diag['version']}")
    doc.add_paragraph(f"  Detalle técnico: {diag['desc_ver']}")
    doc.add_paragraph(f"- Modalidad de implementación: {diag['tipo']}")
    doc.add_paragraph(f"  Detalle técnico: {diag['desc_tipo']}")
    
    doc.add_heading('2.2 Matriz de Parámetros de Consentimiento', 2)
    table = doc.add_table(rows=1, cols=6)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = table.rows[0].cells
    hdr[0].text = "Parámetro GCM"
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
            
    # 3. Inventario de Cookies
    doc.add_heading('3.- Inventario y Clasificación Forense de Cookies', 1)
    secciones = [
        ("3.1 Cookies en Aterrizaje Inicial (Default)", 'default'),
        ("3.2 Cookies tras Rechazar Todas", 'reject'),
        ("3.3 Cookies tras Aceptar Todas", 'accept'),
        ("3.4 Cookies tras Aceptar Solo Analítica", 'analytics'),
        ("3.5 Cookies tras Aceptar Solo Marketing", 'marketing')
    ]
    for tit, k in secciones:
        doc.add_heading(tit, 2)
        cookies = audit_data[k]['cookies']
        if cookies:
            c_table = doc.add_table(rows=1, cols=7)
            c_table.alignment = WD_TABLE_ALIGNMENT.CENTER
            chdr = c_table.rows[0].cells
            chdr[0].text = "Nombre"
            chdr[1].text = "Proveedor"
            chdr[2].text = "Propósito / Finalidad"
            chdr[3].text = "Duración"
            chdr[4].text = "Cat. en Web"
            chdr[5].text = "Debería Ser"
            chdr[6].text = "Diagnóstico"
            
            for c in cookies:
                c_info = enriquecer_cookie_forense(c, k, baseline_names, analytics_new, marketing_new, exact_db, wildcard_list)
                r_cells = c_table.add_row().cells
                r_cells[0].text = c_info['Nombre']
                r_cells[1].text = c_info['Proveedor']
                r_cells[2].text = c_info['Propósito / Finalidad']
                r_cells[3].text = c_info['Duración']
                r_cells[4].text = c_info['Categoría en Web']
                r_cells[5].text = c_info['Categoría Debería Ser']
                r_cells[6].text = c_info['Diagnóstico']
        else:
            doc.add_paragraph("No se detectaron cookies registradas.")

    doc_io = io.BytesIO()
    doc.save(doc_io)
    doc_io.seek(0)
    return doc_io

# ==============================================================================
# INTERFAZ DE USUARIO STREAMLIT
# ==============================================================================

st.markdown("<h1 style='margin-bottom: 2px;'>🛡️ Privacy & Google Consent Mode Auditor</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #94a3b8; font-size: 0.95rem; margin-bottom: 24px;'>Sistema automatizado de telemetría de privacidad, clasificación forense mediante Open Cookie Database y señales Google Consent Mode</p>", unsafe_allow_html=True)

exact_db, wildcard_list = obtener_base_datos_global()

if "audit_data" not in st.session_state:
    st.session_state.audit_data = None
if "domain" not in st.session_state:
    st.session_state.domain = ""
if "cmp_audit" not in st.session_state:
    st.session_state.cmp_audit = None
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "🛠️ Implementación CMP"

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
                
                progreso.progress(10, text="[1/5] Fase 1: Estado Default, detección de CMP y orden de scripts...")
                c_def, p_def, a_def, cmp_info, raw_html = await auditar_fase(browser, target_url, action=None, inspect_cmp=True)
                
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
                
                cmp_audit_result = analizar_implementacion_cmp(cmp_info or {}, raw_html)
                
                return {
                    "default": {"cookies": c_def, "pings": p_def, "action": a_def},
                    "reject": {"cookies": c_rej, "pings": p_rej, "action": a_rej},
                    "accept": {"cookies": c_acc, "pings": p_acc, "action": a_acc},
                    "analytics": {"cookies": c_ana, "pings": p_ana, "action": a_ana},
                    "marketing": {"cookies": c_mkt, "pings": p_mkt, "action": a_mkt}
                }, cmp_audit_result

        try:
            audit_res, cmp_res = asyncio.run(ejecutar_pruebas())
            st.session_state.audit_data = audit_res
            st.session_state.cmp_audit = cmp_res
            progreso.empty()
        except Exception as e:
            st.error(f"Error durante el análisis: {e}")

if st.session_state.audit_data and st.session_state.cmp_audit:
    data = st.session_state.audit_data
    domain = st.session_state.domain
    cmp_audit = st.session_state.cmp_audit
    
    st.markdown(f"<div style='margin-bottom: 20px; font-weight: 600; color: #34d399;'>● Auditoría completada para: <span style='color: #ffffff;'>{domain}</span></div>", unsafe_allow_html=True)
    
    # Análisis diferencial de cookies
    def_names = {c['name'] for c in data['default']['cookies']}
    rej_names = {c['name'] for c in data['reject']['cookies']}
    baseline_names = def_names.union(rej_names)
    
    analytics_new = {c['name'] for c in data['analytics']['cookies']} - baseline_names
    marketing_new = {c['name'] for c in data['marketing']['cookies']} - baseline_names
    
    # Diagnóstico global de Consent Mode
    diag = diagnosticar_consent_mode(data)
    
    # Selector de pestañas persistente de alto contraste (4 Secciones completas)
    tab_options = ["🛠️ Implementación CMP", "📊 Google Consent Mode", "🍪 Cookies por Sección", "📄 Generar Informe Word"]
    selected_tab = st.radio(
        "Navegación:",
        tab_options,
        index=tab_options.index(st.session_state.active_tab) if st.session_state.active_tab in tab_options else 0,
        horizontal=True,
        label_visibility="collapsed",
        key="active_tab"
    )
    
    # ==========================================================================
    # PESTAÑA 1: IMPLEMENTACIÓN Y ORDEN DE SCRIPTS DE CMP
    # ==========================================================================
    if selected_tab == "🛠️ Implementación CMP":
        st.markdown("<h3 style='margin-bottom: 14px;'>Detección y Arquitectura Técnica del CMP</h3>", unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""
            <div class="cyber-panel">
                <div class="cyber-panel-title">Plataforma CMP</div>
                <div class="cyber-panel-val" style="font-size: 1.5rem;">{cmp_audit['detected_cmp']}</div>
                <div class="cyber-badge-ok">● Detectado en ejecución</div>
                <div class="cyber-action">Ubicación script: {cmp_audit['cmp_loc']}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with c2:
            st.markdown(f"""
            <div class="cyber-panel">
                <div class="cyber-panel-title">Método de Integración</div>
                <div class="cyber-panel-val" style="font-size: 1.35rem; color: {cmp_audit['metodo_color']};">{cmp_audit['metodo_badge']}</div>
                <div class="cyber-badge-warn" style="color: {cmp_audit['metodo_color']}; border-color: {cmp_audit['metodo_color']};">
                    {cmp_audit['metodo']}
                </div>
                <div class="cyber-action">Inspección DOM / HTML fuente</div>
            </div>
            """, unsafe_allow_html=True)
            
        with c3:
            gtm_display = ", ".join(cmp_audit['gtm_ids'])
            st.markdown(f"""
            <div class="cyber-panel">
                <div class="cyber-panel-title">Google Tag Manager</div>
                <div class="cyber-panel-val" style="font-size: 1.4rem; color: #34d399;">{gtm_display}</div>
                <div class="cyber-badge-ok">● Contenedor Activo</div>
                <div class="cyber-action">Telemetría de contenedor gtm.js</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<h4 style='color: #ffffff; margin-top: 14px;'>Auditoría de Orden de Carga de Scripts</h4>", unsafe_allow_html=True)
        for estado, color, detalle in cmp_audit['orden_items']:
            st.markdown(f"""
            <div style="background: #0f1626; border-left: 4px solid {color}; border-top: 1px solid #1e293b; border-right: 1px solid #1e293b; border-bottom: 1px solid #1e293b; border-radius: 6px; padding: 12px 18px; margin-bottom: 10px;">
                <span style="color: {color}; font-weight: 700; margin-right: 8px;">{estado}:</span>
                <span style="color: #e2e8f0; font-size: 0.92rem;">{detalle}</span>
            </div>
            """, unsafe_allow_html=True)
            
        # Banner de Recomendación Estratégica (SIEMPRE centralizar en GTM)
        st.markdown(f"""
        <div class="rec-box">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                <span style="font-size: 1.3rem;">💡</span>
                <span style="color: #00f0ff; font-weight: 800; font-size: 1rem; text-transform: uppercase; letter-spacing: 0.5px;">
                    Recomendación Principal de Auditoría (Estándar AEPD / Google)
                </span>
            </div>
            <p style="color: #f1f5f9; font-size: 0.92rem; line-height: 1.6; margin: 0;">
                {cmp_audit['recomendacion']}
            </p>
        </div>
        """, unsafe_allow_html=True)

    # ==========================================================================
    # PESTAÑA 2: GOOGLE CONSENT MODE
    # ==========================================================================
    elif selected_tab == "📊 Google Consent Mode":
        st.markdown("<h3 style='margin-bottom: 14px;'>Diagnóstico Global de Consent Mode</h3>", unsafe_allow_html=True)
        
        c_diag1, c_diag2 = st.columns(2)
        with c_diag1:
            st.markdown(f"""
            <div class="diag-container">
                <div class="diag-title">Versión de Google Consent Mode</div>
                <div class="diag-badge" style="background: rgba(52, 211, 153, 0.18); color: {diag['badge_ver_color']}; border: 1px solid {diag['badge_ver_color']};">
                    ● {diag['version']} ({diag['badge_ver']})
                </div>
                <p style="color: #cbd5e1; font-size: 0.88rem; line-height: 1.55; margin: 0;">
                    {diag['desc_ver']}
                </p>
            </div>
            """, unsafe_allow_html=True)
            
        with c_diag2:
            st.markdown(f"""
            <div class="diag-container">
                <div class="diag-title">Modo de Implementación</div>
                <div class="diag-badge" style="background: rgba(0, 240, 255, 0.18); color: {diag['badge_tipo_color']}; border: 1px solid {diag['badge_tipo_color']};">
                    ● {diag['tipo']}
                </div>
                <p style="color: #cbd5e1; font-size: 0.88rem; line-height: 1.55; margin: 0;">
                    {diag['desc_tipo']}
                </p>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<h3 style='margin-bottom: 14px;'>Telemetría de Señales (5 Fases)</h3>", unsafe_allow_html=True)
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
                
        st.markdown("<br><h4 style='color: #ffffff;'>Matriz de Decodificación de Parámetros GCM</h4>", unsafe_allow_html=True)
        
        table_rows = []
        param_keys = [
            ("ad_storage", "Cookies publicitarias"),
            ("analytics_storage", "Cookies estadísticas/analítica"),
            ("ad_user_data", "Datos de usuario a Google Ads"),
            ("ad_personalization", "Personalización y Remarketing")
        ]
        
        for p_key, p_desc in param_keys:
            row = {"Parámetro GCM": f"{p_key} ({p_desc})"}
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
                "Parámetro GCM": st.column_config.TextColumn("Parámetro GCM", width="medium"),
                "default": "1. Default",
                "reject": "2. Rechazar",
                "accept": "3. Aceptar Todo",
                "analytics": "4. Solo Analítica",
                "marketing": "5. Solo Marketing"
            },
            use_container_width=True,
            hide_index=True
        )

    # ==========================================================================
    # PESTAÑA 3: COOKIES POR SECCIÓN
    # ==========================================================================
    elif selected_tab == "🍪 Cookies por Sección":
        st.markdown("<h3 style='margin-bottom: 14px;'>Inventario Forense Diferencial y Diagnóstico Legal</h3>", unsafe_allow_html=True)
        sec_names = {
            "default": "1. Aterrizaje Inicial (Default)",
            "reject": "2. Tras Rechazar Todas",
            "accept": "3. Tras Aceptar Todas",
            "analytics": "4. Tras Aceptar Solo Analítica",
            "marketing": "5. Tras Aceptar Solo Marketing"
        }
        sel_tab = st.selectbox(
            "Selecciona la casuística a inspeccionar:", 
            list(sec_names.keys()), 
            format_func=lambda x: sec_names[x],
            key="cookie_category_filter"
        )
        c_list = data[sel_tab]['cookies']
        
        enriched_cookies = [enriquecer_cookie_forense(c, sel_tab, baseline_names, analytics_new, marketing_new, exact_db, wildcard_list) for c in c_list]
        total_infracciones = sum(1 for c in enriched_cookies if "❌" in c['Diagnóstico'])
        
        col_m1, col_m2 = st.columns([1, 4])
        with col_m1:
            st.markdown(f"""
            <div style="background: #0f1626; border: 1px solid #1e293b; border-radius: 10px; padding: 12px 18px; box-shadow: 0 4px 15px rgba(0,0,0,0.4);">
                <div style="color: #94a3b8; font-size: 0.78rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 2px;">Total Cookies</div>
                <div style="color: #00f0ff; font-size: 2.2rem; font-weight: 800; font-family: 'Courier New', monospace; line-height: 1.1;">{len(c_list)}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col_m2:
            if total_infracciones > 0:
                st.markdown(f"""
                <div style="padding: 14px 18px; background: rgba(239, 68, 68, 0.14); border: 1px solid #ef4444; border-radius: 10px; color: #fca5a5; font-weight: 600; font-size: 0.92rem; display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 1.2rem;">⚠️</span> Se han detectado {total_infracciones} cookies en presunta infracción (instaladas sin el consentimiento legal exigido).
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="padding: 14px 18px; background: rgba(16, 185, 129, 0.14); border: 1px solid #10b981; border-radius: 10px; color: #6ee7b7; font-weight: 600; font-size: 0.92rem; display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 1.2rem;">✅</span> No se detectan anomalías de consentimiento en las cookies de esta fase.
                </div>
                """, unsafe_allow_html=True)

        st.write("")
        if enriched_cookies:
            st.dataframe(
                enriched_cookies,
                column_config={
                    "Nombre": st.column_config.TextColumn("Nombre Cookie", width="medium"),
                    "Proveedor": st.column_config.TextColumn("Proveedor / Origen", width="medium"),
                    "Propósito / Finalidad": st.column_config.TextColumn("Propósito Registrado", width="large"),
                    "Duración": st.column_config.TextColumn("Duración", width="small"),
                    "Categoría en Web": st.column_config.TextColumn("Cómo la gestiona la Web", width="medium"),
                    "Categoría Debería Ser": st.column_config.TextColumn("Categoría Canónica", width="medium"),
                    "Diagnóstico": st.column_config.TextColumn("Diagnóstico Legal", width="medium"),
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No hay cookies guardadas en esta fase.")

    # ==========================================================================
    # PESTAÑA 4: GENERAR INFORME WORD
    # ==========================================================================
    elif selected_tab == "📄 Generar Informe Word":
        st.markdown("<h3 style='margin-bottom: 14px;'>Generación y Descarga de Informe Oficial</h3>", unsafe_allow_html=True)
        st.markdown("<p style='color: #cbd5e1; font-size: 0.95rem; line-height: 1.6;'>Exporta el informe en formato Word (.docx) estructurado según el estándar oficial de auditoría de privacidad: incluye la arquitectura técnica del CMP, el orden de scripts en código fuente, la telemetría de Consent Mode y la matriz forense diferencial de cookies.</p>", unsafe_allow_html=True)
        doc_bytes = generar_documento_word(domain, data, baseline_names, analytics_new, marketing_new, exact_db, wildcard_list, cmp_audit)
        nombre_archivo = f"{domain} - Auditoría cookies y CMP.docx"
        st.download_button(
            label=f"📥 Descargar Informe Completo (.docx)",
            data=doc_bytes,
            file_name=nombre_archivo,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary",
            key="download_doc_btn"
        )
