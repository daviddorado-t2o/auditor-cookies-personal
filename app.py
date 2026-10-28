import streamlit as st
import asyncio
from playwright.async_api import async_playwright
from docx import Document
from urllib.parse import urlparse, parse_qs
import io
import os

st.set_page_config(page_title="Auditor Privacy & Consent Mode v2", page_icon="🛡️", layout="wide")

@st.cache_resource
def ensure_playwright():
    os.system("playwright install chromium")

ensure_playwright()

def is_google_consent_ping(url):
    u = url.lower()
    if "gcs=" in u or "gcd=" in u:
        return True
    if ("google-analytics.com" in u or "analytics.google.com" in u) and "collect" in u:
        return True
    if ("googleads" in u or "doubleclick.net" in u or "google.com/pagead" in u):
        return True
    return False

def extract_consent_params(pings):
    if not pings:
        return {
            'gcs': 'No detectado',
            'gcd': 'No detectado',
            'npa': 'No detectado',
            'dma': 'No detectado',
            'pscdl': 'No detectado'
        }
    
    # Priorizar el ping más reciente que contenga gcs o gcd
    valid_pings = [p for p in pings if ("gcs=" in p.lower() or "gcd=" in p.lower())]
    target_url = valid_pings[-1] if valid_pings else pings[-1]
    
    parsed = parse_qs(urlparse(target_url).query)
    return {
        'gcs': parsed.get('gcs', ['No detectado'])[0],
        'gcd': parsed.get('gcd', ['No detectado'])[0],
        'npa': parsed.get('npa', ['No detectado'])[0],
        'dma': parsed.get('dma', ['No detectado'])[0],
        'pscdl': parsed.get('pscdl', ['No detectado'])[0]
    }

async def ejecutar_fase_semantica(browser, url, action=None):
    context = await browser.new_context()
    page = await context.new_page()
    pings = []
    
    page.on("request", lambda r: pings.append(r.url) if is_google_consent_ping(r.url) else None)
    
    try:
        await page.goto(url, timeout=25000, wait_until="domcontentloaded")
    except Exception:
        pass
    
    await asyncio.sleep(2.5)
    
    action_info = "Default (Sin interacción)"
    
    if action in ["accept", "reject"]:
        js_simple = """
        (mode) => {
            const acceptPatterns = ['aceptar todas', 'aceptar todo', 'accept all', 'permitir todas', 'aceptar', 'accept'];
            const rejectPatterns = ['rechazar todas', 'rechazar todo', 'reject all', 'denegar', 'rechazar', 'reject'];
            const patterns = (mode === 'accept') ? acceptPatterns : rejectPatterns;
            
            // 1. IDs comunes
            const ids = (mode === 'accept') 
                ? ['#cookiescript_accept', '#onetrust-accept-btn-handler', '#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll', '#didomi-notice-agree-button']
                : ['#cookiescript_reject', '#onetrust-reject-all-handler', '#CybotCookiebotDialogBodyButtonDecline', '#didomi-notice-disagree-button'];
            
            for (let id of ids) {
                let el = document.querySelector(id);
                if (el && el.offsetParent !== null) {
                    el.click();
                    return "Selector directo: " + id;
                }
            }
            
            // 2. Búsqueda por texto en botones/enlaces
            const clickable = Array.from(document.querySelectorAll('button, a, div[role="button"], input[type="button"]'));
            for (let el of clickable) {
                let txt = (el.innerText || el.value || '').trim().toLowerCase();
                if (patterns.some(p => txt === p || txt.includes(p))) {
                    el.click();
                    return "Heurística: " + txt;
                }
            }
            return "No encontrado";
        }
        """
        action_info = await page.evaluate(js_simple, action)
        await asyncio.sleep(3.5)
        
    elif action in ["only_analytics", "only_marketing"]:
        js_granular = """
        (targetMode) => {
            // 1. Abrir panel de preferencias/ajustes si no está visible
            const openPatterns = ['personalizar', 'configurar', 'gestionar', 'preferencias', 'ajustes', 'opciones', 'customize', 'manage', 'settings', 'preferences'];
            const openIds = ['#cookiescript_manage', '#onetrust-pc-btn-handler', '#CybotCookiebotDialogBodyLevelButtonCustomize', '#didomi-notice-learn-more-button'];
            
            for (let id of openIds) {
                let el = document.querySelector(id);
                if (el && el.offsetParent !== null) {
                    el.click();
                    break;
                }
            }
            
            const clickables = Array.from(document.querySelectorAll('button, a, span, div[role="button"]'));
            for (let el of clickables) {
                let txt = (el.innerText || '').trim().toLowerCase();
                if (openPatterns.some(p => txt.includes(p)) && el.offsetParent !== null) {
                    el.click();
                    break;
                }
            }
            
            // Pequeña pausa síncrona visual en el DOM para despliegue de categorías
            return new Promise((resolve) => {
                setTimeout(() => {
                    const anaKeywords = ['analítica', 'analitica', 'analytics', 'rendimiento', 'performance', 'estadística', 'estadistica', 'medición', 'medicion', 'tráfico', 'trafico'];
                    const mktKeywords = ['marketing', 'publicidad', 'publicitaria', 'publicitarias', 'anuncios', 'ads', 'targeting', 'segmentación', 'segmentacion', 'comercial'];
                    const necKeywords = ['necesaria', 'necesarias', 'técnica', 'tecnica', 'strict', 'strictly', 'esencial'];

                    // Buscar todos los bloques o checkboxes dentro del banner
                    const allInputs = Array.from(document.querySelectorAll('input[type="checkbox"], [role="checkbox"], [role="switch"]'));
                    
                    allInputs.forEach(input => {
                        // Buscar el contenedor contextual más cercano (hasta 5 niveles arriba)
                        let container = input.closest('.cookiescript_checkbox, .ot-cat-item, tr, li, div') || input.parentElement;
                        let contextText = (container ? container.innerText : '').toLowerCase();

                        // Clasificación semántica por descripción y título
                        let isNecessary = necKeywords.some(k => contextText.includes(k));
                        let isAnalytics = !isNecessary && anaKeywords.some(k => contextText.includes(k));
                        let isMarketing = !isNecessary && mktKeywords.some(k => contextText.includes(k));

                        let desiredState = false;
                        if (targetMode === 'only_analytics' && isAnalytics) desiredState = true;
                        if (targetMode === 'only_marketing' && isMarketing) desiredState = true;

                        // Aplicar estado si no es necesaria
                        if (!isNecessary && (isAnalytics || isMarketing)) {
                            if (input.tagName === 'INPUT') {
                                if (input.checked !== desiredState) {
                                    input.checked = desiredState;
                                    input.dispatchEvent(new Event('change', { bubbles: true }));
                                    input.dispatchEvent(new Event('input', { bubbles: true }));
                                    // Si tiene un label o switch visual asociado, hacer click
                                    if (input.id) {
                                        let lbl = document.querySelector(`label[for="${input.id}"]`);
                                        if (lbl) lbl.click();
                                    }
                                }
                            } else {
                                // Elementos ARIA role=checkbox/switch
                                let isAriaChecked = input.getAttribute('aria-checked') === 'true';
                                if (isAriaChecked !== desiredState) {
                                    input.click();
                                }
                            }
                        }
                    });

                    // 3. Guardar selección
                    setTimeout(() => {
                        const savePatterns = ['guardar selección', 'guardar seleccion', 'guardar preferencias', 'guardar', 'confirmar mis opciones', 'confirmar opciones', 'save', 'allow selection', 'confirm choices'];
                        const saveIds = ['#cookiescript_save', '.save-preference-btn-handler', '#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowallSelection'];
                        
                        for (let sId of saveIds) {
                            let sEl = document.querySelector(sId);
                            if (sEl && sEl.offsetParent !== null) {
                                sEl.click();
                                resolve("Guardado por ID: " + sId);
                                return;
                            }
                        }
                        
                        for (let el of Array.from(document.querySelectorAll('button, a, input[type="button"]'))) {
                            let txt = (el.innerText || el.value || '').trim().toLowerCase();
                            if (savePatterns.some(p => txt === p || txt.includes(p)) && el.offsetParent !== null) {
                                el.click();
                                resolve("Guardado por texto: " + txt);
                                return;
                            }
                        }
                        resolve("Selección aplicada (intento guardado genérico)");
                    }, 800);
                }, 1200);
            });
        }
        """
        try:
            action_info = await page.evaluate(js_granular, action)
        except Exception as e:
            action_info = f"Error interacción: {e}"
            
        await asyncio.sleep(4.0)

    cookies = await context.cookies()
    await context.close()
    return cookies, pings, action_info

def generar_documento_auditoria(domain, audit_data):
    doc = Document()
    doc.add_heading('AUDITORÍA PRIVACY', 0)
    doc.add_paragraph('Octubre 2026')
    doc.add_heading('Introducción.', 1)
    doc.add_paragraph('Este documento pretende revisar todas las cuestiones fundamentales referidas al cumplimiento de las premisas legales establecidas por el RGPD y las directrices de la Agencia Española de Protección de Datos (AEPD).')
    
    doc.add_paragraph(f'\n{domain}')
    doc.add_heading('1.- HOME', 1)
    doc.add_heading('1.2 Revisión del consentimiento e inventario de cookies', 2)
    
    secciones = [
        ("1.2.1 Aterrizaje previo (Valores Default)", 'default'),
        ("1.2.2 Tras Rechazar Todas las cookies", 'reject'),
        ("1.2.3 Tras Aceptar Todas las cookies", 'accept'),
        ("1.2.4 Tras Aceptar Solo cookies Analíticas", 'analytics'),
        ("1.2.5 Tras Aceptar Solo cookies de Marketing / Publicitarias", 'marketing')
    ]
    for tit, k in secciones:
        doc.add_heading(tit, 3)
        cookies = audit_data[k]['cookies']
        if cookies:
            doc.add_paragraph(f"Total cookies detectadas: {len(cookies)}")
            for c in cookies:
                doc.add_paragraph(f"- {c['name']} (Dominio: {c['domain']})", style='List Bullet')
        else:
            doc.add_paragraph("No se detectaron cookies registradas.")
            
    doc.add_heading('1.3 Revisión de Consent Mode', 2)
    
    def add_cm_section(subtit, key, expected):
        doc.add_heading(subtit, 3)
        p = extract_consent_params(audit_data[key]['pings'])
        if p['gcs'] != 'No detectado' or p['gcd'] != 'No detectado':
            doc.add_paragraph(f"- Señal GCS: {p['gcs']}")
            doc.add_paragraph(f"- Cadena GCD: {p['gcd']}")
            doc.add_paragraph(f"- Señales DMA y NPA: npa={p['npa']}, dma={p['dma']}")
            if expected in p['gcs']:
                doc.add_paragraph(f"Diagnóstico: Señal esperada ({expected}) transmitida correctamente.")
            else:
                doc.add_paragraph(f"Diagnóstico: Señal observada ({p['gcs']}). Verificar correspondencia con {expected}.")
        else:
            doc.add_paragraph("Sin llamadas collect o pings de Consent Mode detectados.")

    add_cm_section('1.3.1 Revisión previa al consentimiento (valores default)', 'default', 'G100')
    add_cm_section('1.3.2 Revisión tras rechazar todas (update)', 'reject', 'G100')
    add_cm_section('1.3.3 Revisión tras aceptar todas (valores update)', 'accept', 'G111')
    add_cm_section('1.3.4 Revisión tras aceptar publicitarias (valores update)', 'marketing', 'G110')
    add_cm_section('1.3.5 Revisión tras aceptar analíticas (valores update)', 'analytics', 'G101')

    doc.add_heading('2.- MOTOR DE RESERVA', 1)
    doc.add_paragraph('En este apartado se trata de observar si el consentimiento previamente dado se mantiene en el motor de reserva.')
    
    doc_io = io.BytesIO()
    doc.save(doc_io)
    doc_io.seek(0)
    return doc_io

# Interfaz Principal
st.title("🛡️ Privacy & Consent Mode v2 Auditor")
st.caption("Auditoría técnica automatizada: Matriz semántica de cookies y señales Google Consent Mode v2")

if "audit_data" not in st.session_state:
    st.session_state.audit_data = None
if "domain" not in st.session_state:
    st.session_state.domain = ""

col_in, col_btn = st.columns([4, 1])
with col_in:
    target_url = st.text_input("Introduce la URL a auditar:", placeholder="https://es.art-hotel-commercianti.com/")
with col_btn:
    st.write("")
    st.write("")
    btn_auditar = st.button("🚀 Iniciar Auditoría", type="primary", use_container_width=True)

if btn_auditar:
    if not target_url.strip().startswith("http"):
        st.error("Introduce una URL completa que comience por https:// o http://")
    else:
        st.session_state.domain = urlparse(target_url).netloc
        progreso = st.progress(0, text="Iniciando navegador...")
        
        async def ejecutar_matriz():
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
                )
                
                progreso.progress(10, text="[1/5] Fase 1: Aterrizaje Default...")
                c_def, p_def, a_def = await ejecutar_fase_semantica(browser, target_url, action=None)
                
                progreso.progress(30, text="[2/5] Fase 2: Rechazar Todas...")
                c_rej, p_rej, a_rej = await ejecutar_fase_semantica(browser, target_url, action="reject")
                
                progreso.progress(50, text="[3/5] Fase 3: Aceptar Todas...")
                c_acc, p_acc, a_acc = await ejecutar_fase_semantica(browser, target_url, action="accept")
                
                progreso.progress(70, text="[4/5] Fase 4: Solo Analítica (Rendimiento/Estadísticas)...")
                c_ana, p_ana, a_ana = await ejecutar_fase_semantica(browser, target_url, action="only_analytics")
                
                progreso.progress(90, text="[5/5] Fase 5: Solo Marketing (Publicidad/Targeting)...")
                c_mkt, p_mkt, a_mkt = await ejecutar_fase_semantica(browser, target_url, action="only_marketing")
                
                await browser.close()
                progreso.progress(100, text="¡Completado con éxito!")
                
                return {
                    "default": {"cookies": c_def, "pings": p_def, "action": a_def},
                    "reject": {"cookies": c_rej, "pings": p_rej, "action": a_rej},
                    "accept": {"cookies": c_acc, "pings": p_acc, "action": a_acc},
                    "analytics": {"cookies": c_ana, "pings": p_ana, "action": a_ana},
                    "marketing": {"cookies": c_mkt, "pings": p_mkt, "action": a_mkt}
                }

        try:
            st.session_state.audit_data = asyncio.run(ejecutar_matriz())
            progreso.empty()
        except Exception as e:
            st.error(f"Error durante el escaneo: {e}")

if st.session_state.audit_data:
    data = st.session_state.audit_data
    domain = st.session_state.domain
    
    st.success(f"¡Auditoría finalizada para {domain}!")
    
    t_cm, t_ck, t_doc = st.tabs(["📊 Google Consent Mode v2", "🍪 Cookies por Sección", "📄 Generar Informe Word"])
    
    with t_cm:
        st.markdown("### Señales recolectadas en las 5 fases")
        cols = st.columns(5)
        fases = [
            ("1. Default", 'default', "G100"),
            ("2. Rechazar", 'reject', "G100"),
            ("3. Aceptar Todo", 'accept', "G111"),
            ("4. Solo Analítica", 'analytics', "G101"),
            ("5. Solo Marketing", 'marketing', "G110")
        ]
        for col, (label, key, expected_gcs) in zip(cols, fases):
            with col:
                st.markdown(f"**{label}**")
                p = extract_consent_params(data[key]['pings'])
                st.metric("GCS", p['gcs'])
                if expected_gcs in p['gcs']:
                    st.caption(f"✅ Esperado: {expected_gcs}")
                else:
                    st.caption(f"⚠️ Esperado: {expected_gcs}")
                st.code(f"GCD: {p['gcd']}\nNPA: {p['npa']}\nDMA: {p['dma']}", language="text")
                st.caption(f"Acción: {data[key]['action']}")
    
    with t_ck:
        st.markdown("### Inventario de cookies por cada casuística")
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
            key="selected_cookie_category"
        )
        c_list = data[sel_tab]['cookies']
        st.write(f"Total cookies presentes: **{len(c_list)}**")
        if c_list:
            st.dataframe([{"Nombre": c['name'], "Dominio": c['domain'], "Expiración (Unix)": c['expires'], "Segura": c['secure']} for c in c_list], use_container_width=True)
        else:
            st.info("No hay cookies guardadas en esta fase.")

    with t_doc:
        st.markdown("### Descarga del documento oficial")
        doc_bytes = generar_documento_auditoria(domain, data)
        nombre_archivo = f"{domain} - Auditoría cookies y CMP.docx"
        st.download_button(
            label=f"📥 Descargar: {nombre_archivo}",
            data=doc_bytes,
            file_name=nombre_archivo,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary",
            key="download_doc_btn"
        )
