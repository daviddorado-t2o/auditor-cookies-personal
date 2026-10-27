import streamlit as st
import asyncio
from playwright.async_api import async_playwright
from docx import Document
from urllib.parse import urlparse, parse_qs
import io
import os

st.set_page_config(page_title="Auditor Privacy & Consent Mode", page_icon="🛡️", layout="wide")

@st.cache_resource
def ensure_playwright():
    os.system("playwright install chromium")

ensure_playwright()

st.title("🛡️ Privacy & Consent Mode v2 Auditor")
st.caption("Auditoría técnica automatizada: Categorías de cookies, señales DMA y Consent Mode v2")

target_url = st.text_input("Introduce la URL a auditar (cualquier sitio web):", placeholder="https://es.bolognarthotels.it/")

CMP_SELECTORS = {
    "CookieScript": {
        "accept": "#cookiescript_accept",
        "reject": "#cookiescript_reject"
    },
    "OneTrust": {
        "accept": "#onetrust-accept-btn-handler",
        "reject": "#onetrust-reject-all-handler"
    },
    "Cookiebot": {
        "accept": "#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll",
        "reject": "#CybotCookiebotDialogBodyButtonDecline"
    },
    "Didomi": {
        "accept": "#didomi-notice-agree-button",
        "reject": "#didomi-notice-disagree-button"
    }
}

def extract_consent_params(url):
    parsed = parse_qs(urlparse(url).query)
    return {
        'gcs': parsed.get('gcs', ['No detectado'])[0],
        'gcd': parsed.get('gcd', ['No detectado'])[0],
        'npa': parsed.get('npa', ['No detectado'])[0],
        'dma': parsed.get('dma', ['No detectado'])[0],
        'pscdl': parsed.get('pscdl', ['No detectado'])[0]
    }

async def auto_click(page, action_type="accept"):
    for cmp_name, config in CMP_SELECTORS.items():
        selector = config.get(action_type)
        if selector:
            try:
                locator = page.locator(selector).first
                if await locator.is_visible(timeout=1500):
                    await locator.click()
                    return f"{cmp_name} ({action_type})"
            except Exception:
                pass

    patterns = {
        "accept": ["Aceptar todas", "Aceptar todo", "Accept all", "Permitir todas", "Aceptar", "Accept"],
        "reject": ["Rechazar todas", "Rechazar todo", "Reject all", "Denegar", "Rechazar", "Reject"]
    }
    for text in patterns.get(action_type, []):
        try:
            btn = page.locator(f"button:has-text('{text}'), a:has-text('{text}')").first
            if await btn.is_visible(timeout=1500):
                await btn.click()
                return f"Heurística ('{text}')"
        except Exception:
            pass

    return "No detectado"

async def ejecutar_fase(browser, url, action=None):
    context = await browser.new_context()
    page = await context.new_page()
    pings = []
    
    page.on("request", lambda r: pings.append(r.url) if ("collect" in r.url and "google" in r.url) else None)
    
    try:
        await page.goto(url, timeout=45000, wait_until="networkidle")
    except Exception:
        pass
    
    await asyncio.sleep(3)
    
    action_result = None
    if action:
        action_result = await auto_click(page, action)
        await asyncio.sleep(4)
        
    cookies = await context.cookies()
    await context.close()
    return cookies, pings, action_result

def generar_documento_auditoria(domain, audit_data):
    doc = Document()
    doc.add_heading('AUDITORÍA PRIVACY', 0)
    doc.add_paragraph('Octubre 2026')
    
    doc.add_heading('Introducción.', 1)
    doc.add_paragraph('Este documento pretende revisar todas las cuestiones fundamentales referidas al cumplimiento de las premisas legales establecidas por el Reglamento General de Protección de Datos y las directrices de la Agencia de Protección de Datos (AEPD).')
    
    doc.add_paragraph(f'\n{domain}')
    doc.add_heading('1.- HOME', 1)
    
    doc.add_heading('1.2 Revisión del consentimiento', 2)
    doc.add_paragraph('Cookies detectadas al aterrizar por primera vez:')
    for c in audit_data['default']['cookies']:
        doc.add_paragraph(f"- {c['name']} (Dominio: {c['domain']})", style='List Bullet')
        
    doc.add_heading('1.3 Revisión de Consent Mode', 2)
    
    # 1.3.1 DEFAULT
    doc.add_heading('1.3.1 Revisión previa al consentimiento (valores default)', 3)
    if audit_data['default']['pings']:
        p_def = extract_consent_params(audit_data['default']['pings'][0])
        doc.add_paragraph(f"- Señal GCS ({p_def['gcs']}): Confirma el estado predeterminado de almacenamiento.")
        doc.add_paragraph(f"- Cadena GCD: {p_def['gcd']}.")
        doc.add_paragraph(f"- Parámetros regulatorios: npa={p_def['npa']}, dma={p_def['dma']}.")
        if "G100" in p_def['gcs']:
            doc.add_paragraph('Diagnóstico: La inyección de señales previas al consentimiento cumple con las directrices de Google Consent Mode v2 Avanzado.')
    
    # 1.3.2 RECHAZAR TODAS
    doc.add_heading('1.3.2 Revisión tras rechazar todas (update)', 3)
    if audit_data['reject']['pings']:
        p_rej = extract_consent_params(audit_data['reject']['pings'][-1])
        doc.add_paragraph(f"- Señal GCS tras rechazo: {p_rej['gcs']}")
        doc.add_paragraph(f"- Cadena GCD: {p_rej['gcd']}")
        doc.add_paragraph(f"- Parámetros regulatorios: npa={p_rej['npa']}, dma={p_rej['dma']}")
        if "G100" in p_rej['gcs']:
            doc.add_paragraph('Diagnóstico: El comportamiento del sitio web ante el rechazo explícito cumple con las directrices de la AEPD.')

    # 1.3.3 ACEPTAR TODAS
    doc.add_heading('1.3.3 Revisión tras aceptar todas (valores update)', 3)
    if audit_data['accept']['pings']:
        p_acc = extract_consent_params(audit_data['accept']['pings'][-1])
        doc.add_paragraph(f"- Señal GCS tras aceptación: {p_acc['gcs']}")
        doc.add_paragraph(f"- Cadena GCD: {p_acc['gcd']}")
        doc.add_paragraph(f"- Parámetros regulatorios: npa={p_acc['npa']}, dma={p_acc['dma']}")
        if "G111" in p_acc['gcs']:
            doc.add_paragraph('Diagnóstico: La transición hacia el estado concedido cumple con las especificaciones de Google Consent Mode v2.')

    doc.add_heading('1.3.4 Revisión tras aceptar publicitarias (valores update)', 3)
    doc.add_paragraph('[Pendiente de validación específica según configuración del CMP]')
    
    doc.add_heading('1.3.5 Revisión tras aceptar analíticas (valores update)', 3)
    doc.add_paragraph('[Pendiente de validación específica según configuración del CMP]')
    
    doc.add_heading('2.- MOTOR DE RESERVA', 1)
    doc.add_paragraph('En este apartado se trata de observar si el consentimiento previamente dado en las distintas casuísticas se mantiene al entrar en el motor de reserva.')

    doc_io = io.BytesIO()
    doc.save(doc_io)
    doc_io.seek(0)
    return doc_io

async def ejecutar_auditoria_completa(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
        
        c_def, p_def, _ = await ejecutar_fase(browser, url, action=None)
        c_rej, p_rej, act_rej = await ejecutar_fase(browser, url, action="reject")
        c_acc, p_acc, act_acc = await ejecutar_fase(browser, url, action="accept")
        
        await browser.close()
        
        return {
            "default": {"cookies": c_def, "pings": p_def},
            "reject": {"cookies": c_rej, "pings": p_rej, "action": act_rej},
