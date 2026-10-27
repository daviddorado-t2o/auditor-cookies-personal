import streamlit as st
import asyncio
from playwright.async_api import async_playwright
from docx import Document
from urllib.parse import urlparse, parse_qs
import io
import os

st.set_page_config(page_title="Privacy & Consent Mode Auditor", page_icon="🛡️", layout="wide")

# Instala Chromium dentro del contenedor Linux de Streamlit Cloud
@st.cache_resource
def ensure_playwright_installed():
    os.system("playwright install chromium")

ensure_playwright_installed()

st.title("🛡️ Privacy & Consent Mode Auditor")
st.caption("Herramienta en la nube para la auditoría técnica de cookies y Google Consent Mode v2")

col1, col2 = st.columns([3, 2])
with col1:
    target_url = st.text_input("Introduce la URL a auditar:", placeholder="https://es.bolognarthotels.it/")
with col2:
    cmp_selector = st.text_input("Selector botón Aceptar CMP (Opcional):", value="#cookiescript_accept")

def extract_consent_params(url):
    parsed = parse_qs(urlparse(url).query)
    return {
        'gcs': parsed.get('gcs', ['No detectado'])[0],
        'gcd': parsed.get('gcd', ['No detectado'])[0],
        'npa': parsed.get('npa', ['No detectado'])[0],
        'dma': parsed.get('dma', ['No detectado'])[0],
        'pscdl': parsed.get('pscdl', ['No detectado'])[0]
    }

def generar_word(domain, cookies_default, pings_default, cookies_update, pings_update):
    doc = Document()
    doc.add_heading('AUDITORÍA PRIVACY', 0)
    doc.add_paragraph('Octubre 2026')
    doc.add_heading('Introducción.', 1)
    doc.add_paragraph('Este documento pretende revisar todas cuestiones fundamentales referidas al cumplimiento de las premisas legales establecidas por el Reglamento General de Protección de Datos y las directrices de la Agencia de Protección de Datos (AEPD).')
    
    doc.add_paragraph(f'\n{domain}')
    doc.add_heading('1.- HOME', 1)
    doc.add_heading('1.2 Revisión del consentimiento', 2)
    doc.add_paragraph('Al aterrizar en la web por primera vez, las cookies detectadas son:')
    for c in cookies_default:
        doc.add_paragraph(f"- {c['name']} (Dominio: {c['domain']})", style='List Bullet')
        
    doc.add_heading('1.3 Revisión de Consent Mode', 2)
    doc.add_heading('1.3.1 Revisión previa al consentimiento (valores default)', 3)
    if pings_default:
        p = extract_consent_params(pings_default[0])
        doc.add_paragraph(f"- Señal GCS: {p['gcs']}", style='List Bullet')
        doc.add_paragraph(f"- Cadena GCD: {p['gcd']}", style='List Bullet')
        doc.add_paragraph(f"- Parámetros DMA/NPA: npa={p['npa']}, dma={p['dma']}", style='List Bullet')
        
    doc.add_heading('1.3.3 Revisión tras aceptar todas (valores update)', 3)
    if pings_update:
        p_up = extract_consent_params(pings_update[-1])
        doc.add_paragraph(f"- Señal GCS tras update: {p_up['gcs']}", style='List Bullet')
        doc.add_paragraph(f"- Cadena GCD tras update: {p_up['gcd']}", style='List Bullet')
        
    doc_io = io.BytesIO()
    doc.save(doc_io)
    doc_io.seek(0)
    return doc_io

async def auditar_web(url, selector):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
        
        # FASE 1: DEFAULT
        context = await browser.new_context()
        page = await context.new_page()
        pings_default = []
        page.on("request", lambda r: pings_default.append(r.url) if "collect" in r.url and "google" in r.url else None)
        await page.goto(url, timeout=60000)
        await asyncio.sleep(4)
        cookies_default = await context.cookies()
        await context.close()
        
        # FASE 2: UPDATE (ACEPTAR)
        context = await browser.new_context()
        page = await context.new_page()
        pings_update = []
        page.on("request", lambda r: pings_update.append(r.url) if "collect" in r.url and "google" in r.url else None)
        await page.goto(url, timeout=60000)
        await asyncio.sleep(2)
        try:
            await page.locator(selector).click(timeout=5000)
            await asyncio.sleep(3)
        except Exception:
            pass
        cookies_update = await context.cookies()
        await browser.close()
        
        return cookies_default, pings_default, cookies_update, pings_update

if st.button("🚀 Iniciar Auditoría", type="primary", use_container_width=True):
    if not target_url.startswith("http"):
        st.error("Introduce una URL completa que empiece por https:// o http://")
    else:
        domain = urlparse(target_url).netloc
        with st.spinner(f"Escaneando {domain} desde el servidor..."):
            try:
                cookies_def, pings_def, cookies_up, pings_up = asyncio.run(auditar_web(target_url, cmp_selector))
                st.success(f"¡Auditoría completada para {domain}!")
                
                tab1, tab2, tab3 = st.tabs(["📊 Consent Mode v2", "🍪 Cookies Detectadas", "📄 Descargar Auditoría"])
                
                with tab1:
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("#### Previo (Default)")
                        if pings_def:
                            params = extract_consent_params(pings_def[0])
                            st.metric("GCS (Default)", params['gcs'])
                            st.write(f"**GCD:** `{params['gcd']}`")
                            st.write(f"**NPA:** `{params['npa']}` | **DMA:** `{params['dma']}`")
                            if "G100" in params['gcs']:
                                st.success("✅ G100: Denegado por defecto")
                            else:
                                st.warning("⚠️ No se detecta G100")
                        else:
                            st.info("Sin pings collect detectados en estado inicial.")
                            
                    with c2:
                        st.markdown("#### Tras Aceptar (Update)")
                        if pings_up:
                            params = extract_consent_params(pings_up[-1])
                            st.metric("GCS (Update)", params['gcs'])
                            st.write(f"**GCD:** `{params_up['gcd']}`")
                            st.write(f"**NPA:** `{params_up['npa']}` | **DMA:** `{params_up['dma']}`")
                            if "G111" in params_up['gcs']:
                                st.success("✅ G111: Consentimiento otorgado")
                        else:
                            st.info("No se detectó el ping update.")
                            
                with tab2:
                    st.dataframe([{"Cookie": c['name'], "Dominio": c['domain'], "Expiración": c['expires']} for c in cookies_def], use_container_width=True)
                    
                with tab3:
                    doc = generar_word(domain, cookies_def, pings_def, cookies_up, pings_up)
                    file_name = f"{domain} - Auditoría cookies y CMP.docx"
                    st.download_button(
                        label=f"📥 Descargar: {file_name}",
                        data=doc,
                        file_name=file_name,
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        type="primary"
                    )
            except Exception as e:
                st.error(f"Error durante el escaneo: {e}")
