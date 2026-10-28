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
    ]
    for tit, k in secciones:
        doc.add_heading(tit, 2)
        cookies = audit_data[k]['cookies']
        if cookies:
            doc.add_paragraph(f"Total registradas: {len(cookies)}")
            for c in cookies:
                doc.add_paragraph(f"- {c['name']} (Dominio: {c['domain']})", style='List Bullet')
        else:
            doc.add_paragraph("No se detectaron cookies registradas.")

    doc_io = io.BytesIO()
    doc.save(doc_io)
    doc_io.seek(0)
    return doc_io

# INTERFAZ STREAMLIT
st.title("🛡️ Privacy & Consent Mode v2 Auditor")
st.caption("Auditoría técnica automatizada: Matriz completa de consentimientos y desglose DMA / Google Consent Mode v2")

if "audit_data" not in st.session_state:
    st.session_state.audit_data = None
if "domain" not in st.session_state:
    st.session_state.domain = ""

c_input, c_btn = st.columns([4, 1])
with c_input:
    target_url = st.text_input("Introduce la URL a auditar:", placeholder="https://es.art-hotel-commercianti.com/")
with c_btn:
    st.write("")
    st.write("")
    btn_start = st.button("🚀 Iniciar Auditoría", type="primary", use_container_width=True)

if btn_start:
    if not target_url.strip().startswith("http"):
        st.error("Introduce una URL completa con https:// o http://")
    else:
        st.session_state.domain = urlparse(target_url).netloc
        progreso = st.progress(0, text="Iniciando navegador...")
        
        async def ejecutar_pruebas():
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"])
                
                progreso.progress(10, text="[1/5] Fase 1: Estado Default...")
                c_def, p_def, a_def = await auditar_fase(browser, target_url, action=None)
                
                progreso.progress(30, text="[2/5] Fase 2: Rechazar Todas...")
                c_rej, p_rej, a_rej = await auditar_fase(browser, target_url, action="reject")
                
                progreso.progress(50, text="[3/5] Fase 3: Aceptar Todas...")
                c_acc, p_acc, a_acc = await auditar_fase(browser, target_url, action="accept")
                
                progreso.progress(70, text="[4/5] Fase 4: Solo Analítica (Rendimiento)...")
                c_ana, p_ana, a_ana = await auditar_fase(browser, target_url, action="only_analytics")
                
                progreso.progress(90, text="[5/5] Fase 5: Solo Marketing (Publicidad)...")
                c_mkt, p_mkt, a_mkt = await auditar_fase(browser, target_url, action="only_marketing")
                
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
            st.session_state.audit_data = asyncio.run(ejecutar_pruebas())
            progreso.empty()
        except Exception as e:
            st.error(f"Error durante el análisis: {e}")

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
        
        parsed_fases = {}
        for col, (label, key, expected_gcs) in zip(cols, fases):
            with col:
                st.markdown(f"**{label}**")
                p = extract_consent_params(data[key]['pings'])
                parsed_fases[key] = p
                st.metric("GCS", p['gcs'])
                
                if expected_gcs in p['gcs']:
                    st.caption(f"✅ Coincide con {expected_gcs}")
                else:
                    st.caption(f"⚠️ Esperado: {expected_gcs}")
                    
                st.code(f"GCD: {p['gcd']}\nNPA: {p['npa']} | DMA: {p['dma']}", language="text")
                st.caption(f"Acción: {data[key]['action']}")
                
        st.divider()
        st.markdown("### 📋 Desglose detallado por Parámetros (Consent Mode v2)")
        
        table_rows = []
        param_keys = [
            ("ad_storage", "Cookies publicitarias"),
            ("analytics_storage", "Cookies estadísticas/analítica"),
            ("ad_user_data", "Envío de datos de usuario a Google Ads"),
            ("ad_personalization", "Personalización y Remarketing")
        ]
        
        for p_key, p_desc in param_keys:
            row = {"Parámetro": f"{p_key} ({p_desc})"}
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
                "Parámetro": st.column_config.TextColumn("Parámetro GCM v2", width="medium"),
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
        sec_names = {
            "default": "1. Aterrizaje Inicial (Default)",
            "reject": "2. Tras Rechazar Todas",
            "accept": "3. Tras Aceptar Todas",
            "analytics": "4. Tras Aceptar Solo Analítica",
            "marketing": "5. Tras Aceptar Solo Marketing"
        }
        sel_tab = st.selectbox("Selecciona la casuística a inspeccionar:", list(sec_names.keys()), format_func=lambda x: sec_names[x])
        c_list = data[sel_tab]['cookies']
        st.write(f"Total cookies presentes: **{len(c_list)}**")
        if c_list:
            st.dataframe([{"Nombre": c['name'], "Dominio": c['domain'], "Expiración (Unix)": c['expires'], "Segura": c['secure']} for c in c_list], use_container_width=True)
        else:
            st.info("No hay cookies guardadas en esta fase.")

    with t_doc:
        doc_bytes = generar_documento_word(domain, data)
        nombre_archivo = f"{domain} - Auditoría cookies y CMP.docx"
        st.download_button(
            label=f"📥 Descargar: {nombre_archivo}",
            data=doc_bytes,
            file_name=nombre_archivo,
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary",
            key="download_doc_btn"
        )
