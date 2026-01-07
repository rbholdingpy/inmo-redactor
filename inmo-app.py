import streamlit as st
from PIL import Image
import base64
import io
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from openai import OpenAI

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="VendeMás IA",
    page_icon="🚀",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .main { background-color: #F8FAFC; }
    h1 { color: #0F172A; font-family: 'Helvetica Neue', sans-serif; font-weight: 800; }
    h2, h3 { color: #334155; }
    .stButton>button {
        background-color: #2563EB; color: white; border-radius: 8px; border: none;
        padding: 12px 24px; font-weight: bold; transition: all 0.3s ease; width: 100%;
    }
    .stButton>button:hover {
        background-color: #1D4ED8; transform: translateY(-2px); box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
    }
    .plan-card {
        background-color: white; padding: 20px; border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center; border: 1px solid #E2E8F0; margin-bottom: 10px;
    }
    .highlight-card {
        border: 2px solid #2563EB; background-color: #EFF6FF;
    }
    .vision-blocked {
        background-color: #FEF3C7; border-left: 5px solid #D97706; padding: 15px; border-radius: 5px; color: #92400E; font-size: 0.9em; margin-bottom: 15px;
    }
    .pro-badge {
        background-color: #DCFCE7; color: #166534; padding: 5px 10px; border-radius: 20px; font-weight: bold; font-size: 0.8em;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIONES DE APOYO ---
def encode_image(image):
    buffered = io.BytesIO()
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def activar_planes():
    st.session_state.ver_planes = True

def cerrar_planes():
    st.session_state.ver_planes = False

# --- ESTADO DE SESIÓN ---
if 'ver_planes' not in st.session_state:
    st.session_state['ver_planes'] = False

# --- API KEY ---
api_key = st.secrets.get("OPENAI_API_KEY")
if not api_key:
    st.error("⚠️ Error: Falta API Key de OpenAI.")
    st.stop()
client = OpenAI(api_key=api_key)

# =======================================================
# === 🔐 SISTEMA DE ACCESO (GOOGLE SHEETS) ===
# =======================================================

@st.cache_data(ttl=60) 
def obtener_usuarios_sheet():
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client_gs = gspread.authorize(creds)
        sheet = client_gs.open("Usuarios_InmoApp").sheet1
        return sheet.get_all_records()
    except Exception as e:
        return []

with st.sidebar:
    st.header("🔐 Área de Miembros")
    codigo_acceso = st.text_input("Código de Acceso:", type="password", placeholder="Ej: PRUEBA1", key="input_codigo")
    
    plan_actual = "GRATIS"
    limite_fotos = 1
    es_pro = False
    
    if codigo_acceso:
        usuarios_db = obtener_usuarios_sheet()
        usuario_encontrado = next((u for u in usuarios_db if str(u['codigo']).strip() == codigo_acceso.strip()), None)
        
        if usuario_encontrado:
            plan_actual = usuario_encontrado['plan']
            limite_fotos = int(usuario_encontrado['limite'])
            es_pro = True
            st.session_state.ver_planes = False # Oculta precios si ya es PRO
            st.success(f"✅ ¡Hola {usuario_encontrado['cliente']}!")
            if st.button("🔓 Cerrar Sesión"):
                st.session_state.input_codigo = ""
                st.rerun()
        else:
            st.error("❌ Código no válido.")

    st.divider()
    ver_precios = st.toggle("💎 Ver Planes y Precios", key="ver_planes")
    st.caption("© 2026 VendeMás IA")

# =======================================================
# === ZONA DE VENTAS ===
# =======================================================
if st.session_state.ver_planes and not es_pro:
    st.title("💎 Desbloquea tu Potencial")
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown('<div class="plan-card"><h3>🥉 Básico</h3><h2>20.000 Gs</h2><p>10 Anuncios</p></div>', unsafe_allow_html=True)
    with c2: st.markdown('<div class="plan-card highlight-card"><h3>🥈 Estándar</h3><h2>35.000 Gs</h2><p>20 Anuncios</p></div>', unsafe_allow_html=True)
    with c3: st.markdown('<div class="plan-card"><h3>🥇 Agencia</h3><h2>80.000 Gs</h2><p>200 Mensual</p></div>', unsafe_allow_html=True)
    
    st.divider()
    cp, cw = st.columns(2)
    with cp:
        st.subheader("1. Transfiere")
        st.markdown("""
        **Banco:** ITAÚ  
        **Titular:** Ricardo Blanco  
        **C.I.:** 1911221  
        **Cuenta Nro:** 320595209  
        **RUC:** 1911221-1
        """)
    with cw:
        st.subheader("2. Activa")
        link = "https://wa.me/595981000000?text=Hola,%20adjunto%20comprobante%20para%20activar%20mi%20código%20PRO"
        st.markdown(f'<a href="{link}" target="_blank"><button style="background-color:#25D366;color:white;border:none;padding:12px;border-radius:8px;width:100%;font-weight:bold;cursor:pointer;">📲 Enviar Comprobante</button></a>', unsafe_allow_html=True)
    
    if st.button("❌ Volver a la App (Modo Gratis)", on_click=cerrar_planes):
        st.rerun()
    st.stop()

# =======================================================
# === APP PRINCIPAL ===
# =======================================================
c_title, c_badge = st.columns([2, 1])
with c_title:
    st.title("🚀 VendeMás IA")
    st.caption("Experto en Neuroventas Inmobiliarias.")

with c_badge:
    if es_pro:
        st.markdown(f'<div style="text-align:right"><span class="pro-badge">PLAN {plan_actual.upper()}</span></div>', unsafe_allow_html=True)
    else:
        col_g, col_p = st.columns(2)
        col_g.markdown('<div style="margin-top:10px;"><span style="background-color:#F1F5F9; color:#64748B; padding:8px 12px; border-radius:20px; font-size:0.8em;">GRATIS</span></div>', unsafe_allow_html=True)
        col_p.button("💎 SER PRO", type="primary", on_click=activar_planes)

st.write("#### 1. 📸 Galería")
uploaded_files = st.file_uploader("Subir fotos", type=["jpg", "png", "jpeg"], accept_multiple_files=True)

if uploaded_files:
    if len(uploaded_files) > limite_fotos:
        st.error(f"⛔ Tu plan permite {limite_fotos} fotos. Tienes {len(uploaded_files)}.")
        st.stop()
    
    with st.expander("👁️ Ver fotos"):
        cols = st.columns(4)
        for i, f in enumerate(uploaded_files):
            with cols[i%4]: st.image(Image.open(f), use_container_width=True)

    st.divider()
    st.write("#### 2. 📝 Datos de la Propiedad")
    c1, c2 = st.columns(2)
    with c1:
        oper = st.radio("Operación", ["Venta", "Alquiler"], horizontal=True)
        tipo = st.selectbox("Tipo", ["Casa", "Departamento", "Terreno", "Local", "Duplex"])
        enfoque = st.selectbox("🎯 Estrategia", ["Equilibrado", "🔥 Urgencia", "🔑 Primera Casa", "💎 Lujo", "💰 Inversión"] if es_pro else ["🔒 Bloqueado (Solo PRO)"], disabled=not es_pro)
        ubicacion = st.text_input("Ubicación")
        
        if oper == "Alquiler":
            cp, cf = st.columns([2, 1])
            precio_val = cp.text_input("Precio")
            frec = cf.selectbox("Periodo", ["Mensual", "Semestral", "Anual"])
            texto_precio = f"{precio_val} ({frec})"
        else:
            texto_precio = st.text_input("Precio")
            
        whatsapp = st.text_input("WhatsApp (Solo números)") if es_pro else st.text_input("WhatsApp", placeholder="🔒 Solo PRO", disabled=True)

    with c2:
        habs = st.number_input("Habitaciones", 1)
        banos = st.number_input("Baños", 1)
        st.write("**Extras:**")
        q = st.checkbox("Quincho")
        p = st.checkbox("Piscina")
        c = st.checkbox("Cochera")

    st.divider()
    if es_pro: st.info("🧠 **Neuro-Vision Activa:** Analizando fotos...")
    else: st.warning("⚠️ Vision IA Desactivada. Actualiza a PRO.")
    
    if st.button("✨ Generar Estrategia", type="primary"):
        if not ubicacion or not texto_precio:
            st.warning("⚠️ Completa Ubicación y Precio.")
        else:
            with st.spinner('Redactando...'):
                try:
                    prompt = f"""Experto en Neuroventas. Genera 3 opciones para {oper} de {tipo} en {ubicacion}.
                    1. Storytelling emotivo ({enfoque}). 2. AIDA directo (sin etiquetas). 3. Instagram.
                    Precio: {texto_precio}. Extras: Q={q}, P={p}, C={c}. Link: https://wa.me/595{whatsapp}. No Markdown.""" if es_pro else f"Redactor básico. 1 descripción para {oper} de {tipo} en {ubicacion}. Precio {texto_precio}."
                    
                    content = [{"type": "text", "text": prompt}]
                    for f in uploaded_files:
                        content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(Image.open(f))}"}})
                    
                    res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": content}])
                    st.success("¡Listo!")
                    st.text_area("Resultado:", value=res.choices[0].message.content, height=400)
                except Exception as e:
                    st.error(f"Error: {e}")
