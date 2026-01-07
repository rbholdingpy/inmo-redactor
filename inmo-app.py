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

# --- FUNCIÓN DE IMAGEN ---
def encode_image(image):
    buffered = io.BytesIO()
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# --- ESTADO INICIAL ---
if 'tutorial_visto' not in st.session_state:
    st.session_state['tutorial_visto'] = False

# Esta es la función mágica que arregla el error del botón PRO
def activar_planes():
    st.session_state.ver_planes = True

if 'ver_planes' not in st.session_state:
    st.session_state['ver_planes'] = False

# --- API KEY ---
api_key = st.secrets.get("OPENAI_API_KEY")
if not api_key:
    st.error("⚠️ Error: Falta API Key.")
    st.stop()
client = OpenAI(api_key=api_key)

# =======================================================
# === 🔐 SISTEMA DE ACCESO (GOOGLE SHEETS) ===
# =======================================================

@st.cache_data(ttl=60) # Actualiza datos cada 60 segundos
def obtener_usuarios_sheet():
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        # Lee las credenciales desde Secrets
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client_gs = gspread.authorize(creds)
        # Abre la hoja exacta "Usuarios_InmoApp"
        sheet = client_gs.open("Usuarios_InmoApp").sheet1
        return sheet.get_all_records()
    except Exception as e:
        return []

with st.sidebar:
    st.header("🔐 Área de Miembros")
    st.write("Ingresa tu código de acceso:")
    
    codigo_acceso = st.text_input("Código:", type="password", placeholder="Ej: PRUEBA1")
    
    # Valores por defecto (Gratis)
    plan_actual = "GRATIS"
    limite_fotos = 1
    es_pro = False
    
    if codigo_acceso:
        # Buscamos en Google Sheets
        usuarios_db = obtener_usuarios_sheet()
        usuario_encontrado = None
        
        if not usuarios_db:
            st.error("⚠️ Error de conexión con Base de Datos.")
        else:
            for usuario in usuarios_db:
                # Convertimos a string para comparar
                if str(usuario['codigo']).strip() == codigo_acceso.strip():
                    usuario_encontrado = usuario
                    break
            
            if usuario_encontrado:
                plan_actual = usuario_encontrado['plan']
                limite_fotos = int(usuario_encontrado['limite'])
                es_pro = True
                st.success(f"✅ ¡Hola {usuario_encontrado['cliente']}!")
                st.caption(f"Plan Activo: {plan_actual}")
            else:
                st.error("❌ Código no encontrado.")

    if not es_pro:
        st.info("Estás en modo GRATIS.")

    st.divider()
    st.markdown("¿No tienes código?")
    
    # Toggle conectado al estado 'ver_planes'
    ver_precios = st.toggle("💎 Ver Planes y Precios", key="ver_planes")
    
    st.caption("© 2026 VendeMás IA")

# =======================================================
# === ZONA DE VENTAS ===
# =======================================================
if ver_precios and not es_pro:
    st.title("💎 Desbloquea tu Potencial")
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown('<div class="plan-card"><h3>🥉 Básico</h3><h2>20.000 Gs</h2><p>10 Anuncios</p></div>', unsafe_allow_html=True)
    with c2: st.markdown('<div class="plan-card highlight-card"><h3>🥈 Estándar</h3><h2>35.000 Gs</h2><p>20 Anuncios</p></div>', unsafe_allow_html=True)
    with c3: st.markdown('<div class="plan-card"><h3>🥇 Agencia</h3><h2>80.000 Gs</h2><p>200 Mensual</p></div>', unsafe_allow_html=True)
    
    st.divider()
    cp, cw = st.columns(2)
    with cp:
        st.subheader("1. Transfiere")
        st.write("**Banco ITAÚ** | Ricardo Blanco")
        st.code("RUC 1911221-1", language="text")
        st.caption("Cta: 320595209")
    with cw:
        st.subheader("2. Activa")
        st.write("Envía comprobante para recibir tu código.")
        link = "https://wa.me/595981000000?text=Hola,%20quiero%20mi%20código%20PRO"
        st.markdown(f'<a href="{link}" target="_blank"><button style="background-color:#25D366;color:white;border:none;padding:10px;border-radius:5px;">📲 Enviar Comprobante</button></a>', unsafe_allow_html=True)
    st.divider()

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
        # BOTONES ALINEADOS
        col_espacio, col_gratis, col_pro = st.columns([0.2, 1, 1])
        with col_gratis:
             st.markdown('<div style="margin-top: 10px; text-align: center;"><span style="background-color:#F1F5F9; color:#64748B; padding:8px 12px; border-radius:20px; font-size:0.8em;">GRATIS</span></div>', unsafe_allow_html=True)
        with col_pro:
            # BOTÓN PRO CORREGIDO con on_click
            st.button("💎 SER PRO", type="primary", on_click=activar_planes, use_container_width=True)

# 1. GALERÍA
st.write("#### 1. 📸 Galería")
uploaded_files = st.file_uploader("Subir fotos", type=["jpg", "png"], accept_multiple_files=True)

if uploaded_files:
    cant = len(uploaded_files)
    if cant > limite_fotos:
        st.error(f"⛔ Tu plan {plan_actual} permite máximo {limite_fotos} fotos.")
        if not es_pro: st.info("💡 Desbloquea más fotos comprando un plan.")
        st.stop()
    st.success(f"✅ {cant}/{limite_fotos} fotos cargadas.")
    with st.expander("👁️ Ver fotos"):
        cols = st.columns(4)
        for i, f in enumerate(uploaded_files):
            with cols[i%4]: st.image(Image.open(f), use_container_width=True)

    # 2. DATOS
    st.divider()
    st.write("#### 2. 📝 Datos de la Propiedad")
    c1, c2 = st.columns(2)
    with c1:
        operacion = st.radio("Operación", ["Venta", "Alquiler"], horizontal=True)
        nombre_agencia, tipo_gestion = "", ""
        if operacion == "Alquiler":
            tipo_gestion = st.radio("Gestión:", ["Propietario Directo", "Agencia"], horizontal=True)
            if tipo_gestion == "Agencia": nombre_agencia = st.text_input("Nombre Agencia")
        
        tipo = st.selectbox("Tipo", ["Casa", "Departamento", "Terreno", "Local", "Duplex"])
        
        if es_pro:
            enfoque = st.selectbox("🎯 Estrategia Neuroventas", ["Equilibrado", "🔥 Urgencia", "🔑 Primera Casa", "💎 Lujo", "💰 Inversión", "❤️ Familiar"])
        else:
            enfoque = "Básico"
            st.selectbox("🎯 Estrategia", ["🔒 Bloqueado (Solo PRO)"], disabled=True)
        
        ubicacion = st.text_input("Ubicación")
        
        if operacion == "Alquiler":
            cp, cf = st.columns([2, 1])
            precio = cp.text_input("Precio")
            frecuencia = cf.selectbox("Periodo", ["Mensual", "Semestral", "Anual"])
            texto_precio = f"{precio} ({frecuencia})"
        else:
            precio = st.text_input("Precio")
            texto_precio = precio
            
        whatsapp = st.text_input("WhatsApp") if es_pro else st.text_input("WhatsApp", placeholder="🔒 Solo PRO", disabled=True)

    with c2:
        habs = st.number_input("Habitaciones", 1)
        banos = st.number_input("Baños", 1)
        st.write("**Extras:**")
        quincho = st.checkbox("Quincho")
        piscina = st.checkbox("Piscina")
        cochera = st.checkbox("Cochera")
        
        txt_servicios = ""
        if operacion == "Alquiler":
            st.write("**Servicios:**")
            cs1, cs2 = st.columns(2)
            if cs1.checkbox("💧 Agua"): txt_servicios += "Agua, "
            if cs1.checkbox("⚡ Luz"): txt_servicios += "Luz, "
            if cs1.checkbox("❄️ Aire"): txt_servicios += "Aire A.A., "
            if cs2.checkbox("📶 Wifi"): txt_servicios += "Wifi, "

    # 3. GENERAR
    st.divider()
    if uploaded_files:
        if es_pro: st.info("🧠 **Neuro-Vision Activa:** Analizando emociones visuales...")
        else: st.markdown('<div class="vision-blocked">⚠️ Vision IA Desactivada. Actualiza a PRO.</div>', unsafe_allow_html=True)
    
    if st.button("✨ Generar Estrategia", type="primary"):
        if not ubicacion or not precio:
            st.warning("⚠️ Faltan datos.")
        else:
            with st.spinner('Procesando...'):
                try:
                    info_gestion = ""
                    if operacion == "Alquiler":
                        if tipo_gestion == "Propietario Directo": info_gestion = "Trato directo."
                        elif tipo_gestion == "Agencia": info_gestion = f"Gestión: {nombre_agencia}."
                    
                    if es_pro:
                        prompt = f"""
                        Actúa como EXPERTO EN NEUROVENTAS. VISION IA: Analiza las fotos.
                        Genera 3 OPCIONES para {operacion} de {tipo} en {ubicacion}:
                        1. STORYTELLING (Deseo de {enfoque})
                        2. VENTA DIRECTA (AIDA implícito, sin etiquetas, urgencia).
                        3. INSTAGRAM (Emojis, corto).
                        Datos: {texto_precio}, {habs} habs, {banos} baños. Extras: Q={quincho}, P={piscina}.
                        {f'Servicios: {txt_servicios}' if operacion=='Alquiler' else ''} Gestión: {info_gestion}
                        Link: https://wa.me/595{whatsapp}
                        NO MARKDOWN. Solo Emojis.
                        """
                    else:
                        prompt = f"""
                        Redactor básico. 1 descripción simple para {operacion} {tipo} en {ubicacion}.
                        Precio {texto_precio}. {habs} habs. NO Markdown. Solo Emojis.
                        """

                    content = [{"type": "text", "text": prompt}]
                    for f in uploaded_files:
                        img = Image.open(f)
                        b64 = encode_image(img)
                        content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
                        
                    response = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": content}], max_tokens=1000)
                    
                    st.success("¡Listo!")
                    st.text_area("Resultado:", value=response.choices[0].message.content, height=600)
                    if not es_pro: st.info("🔒 Desbloquea las 3 Estrategias Virales activando tu PACK.")

                except Exception as e:
                    st.error(f"Error: {e}")
