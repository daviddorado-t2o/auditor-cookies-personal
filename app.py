import streamlit as st
import asyncio
from playwright.async_api import async_playwright
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from urllib.parse import urlparse, parse_qs
import io
import os
import re

st.set_page_config(page_title="Auditor Privacy & Consent Mode v2", page_icon="🛡️", layout="wide")

@st.cache_resource
def ensure_playwright():
    os.system("playwright install chromium")

ensure_playwright()

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
    
    # Formato GCD estándar: 1<sep><ad_storage><sep><analytics_storage><sep><ad_user_data><sep><ad_personalization>
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
    
    # Rastrear todos los pings de la fase (del más reciente al más antiguo)
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
    
    # Deducción matemática de GCS si el ping de red no lo envió explícitamente
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

async def interactuar_con_cmp(page, target_action):
    js_action = """
    async (mode) => {
        // 1. Integración directa con API oficial de CookieScript
        if (window.CookieScript && window.CookieScript.instance) {
            try {
                if (mode === 'accept') {
                    window.CookieScript.instance.acceptAllAction();
                    return "CookieScript API: acceptAllAction()";
                } else if (mode === 'reject') {
                    window.CookieScript.instance.rejectAllAction();
                    return "CookieScript API: rejectAllAction()";
                } else if (mode === 'only_analytics') {
                    window.CookieScript.instance.acceptAction(['performance']);
                    return "CookieScript API: acceptAction(['performance'])";
                } else if (mode === 'only_marketing') {
                    window.CookieScript.instance.acceptAction(['targeting']);
                    return "CookieScript API: acceptAction(['targeting'])";
                }
            } catch (err) {
                console.error(err);
            }
        }

        // 2. Interacción estándar vía botones de 1ª capa (Aceptar / Rechazar)
        if (mode === 'accept') {
            const acceptSelectors = ['#cookiescript_accept', '#onetrust-accept-btn-handler', '#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll', '#didomi-notice-agree-button'];
            for (let s of acceptSelectors) {
                let el = document.querySelector(s);
                if (el && el.offsetParent !== null) { el.click(); return "Selector: " + s; }
            }
            for (let b of Array.from(document.querySelectorAll('button, a, input[type="button"]'))) {
                let t = (b.innerText || b.value || '').trim().toLowerCase();
                if (['aceptar todas', 'aceptar todo', 'accept all', 'permitir todas', 'aceptar'].some(term => t === term || t.includes(term))) {
                    b.click();
                    return "Texto: " + t;
                }
            }
        }

        if (mode === 'reject') {
            const rejectSelectors = ['#cookiescript_reject', '#onetrust-reject-all-handler', '#CybotCookiebotDialogBodyButtonDecline', '#didomi-notice-disagree-button'];
            for (let s of rejectSelectors) {
                let el = document.querySelector(s);
                if (el && el.offsetParent !== null) { el.click(); return "Selector: " + s; }
            }
            for (let b of Array.from(document.querySelectorAll('button, a, input[type="button"]'))) {
                let t = (b.innerText || b.value || '').trim().toLowerCase();
                if (['rechazar todas', 'rechazar todo', 'reject all', 'denegar', 'rechazar'].some(term => t === term || t.includes(term))) {
                    b.click();
                    return "Texto: " + t;
                }
            }
        }

        // 3. Configuración granular en 2ª capa
        const openManageSelectors = ['#cookiescript_manage', '#onetrust-pc-btn-handler', '#CybotCookiebotDialogBodyLevelButtonCustomize', '#didomi-notice-learn-more-button'];
        for (let s of openManageSelectors) {
            let el = document.querySelector(s);
            if (el && el.offsetParent !== null) { el.click(); break; }
        }
        await new Promise(r => setTimeout(r, 900));

        // Manipulación de casillas por IDs directos
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

        // Guardar configuración
        const saveSelectors = ['#cookiescript_save', '.save-preference-btn-handler', '#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowallSelection'];
        for (let s of saveSelectors) {
            let el = document.querySelector(s);
            if (el && el.offsetParent !== null) { el.click(); return "Guardado: " + s; }
        }
        for (let b of Array.from(document.querySelectorAll('button, a, input[type="button"]'))) {
            let t = (b.innerText || b.value || '').trim().toLowerCase();
            if (['guardar selección', 'guardar preferencias', 'guardar', 'save', 'confirmar'].some(term => t.includes(term))) {
                b.click();
                return "Guardado: " + t;
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

def generar_documento_word(domain, audit_data):
    doc = Document()
    doc.add_heading('AUDITORÍA TÉCNICA PRIVACY & CONSENT MODE V2', 0)
    doc.add_paragraph('Octubre 2026')
    doc.add_heading('Introducción.', 1)
    doc.add_paragraph('Este informe audita el comportamiento técnico de cookies y el envío de señales bajo Google Consent Mode v2 según las directrices de la AEPD y el RGPD.')
    doc.add_paragraph(f'\nDominio evaluado: {domain}')
    
    # 1. Matriz Resumen de Consent Mode v2
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
            
    doc.add_heading('2.- Inventario de Cookies por Sección', 1)
    secciones = [
        ("2.1 Cookies en Aterrizaje Inicial (Default)", 'default'),
        ("2.2 Cookies tras Rechazar Todas", 'reject'),
        ("2.3 Cookies tras Aceptar Todas", 'accept'),
        ("2.4 Cookies tras Aceptar Solo Analítica", 'analytics'),
        ("2.5 Cookies tras Aceptar Solo Marketing", 'marketing')
