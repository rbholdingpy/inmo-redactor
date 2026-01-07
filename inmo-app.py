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

# --- ESTILOS CSS (Diseño limpio) ---
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
    .pro-badge {
        background-color: #DCFCE7; color: #166534; padding: 5px 10px; border-radius: 20px; font-weight: bold; font-size: 0.8em;
    }
    /* Texto generado más grande y legible */
    .stMarkdown p { font-size: 1.1em; line-height: 1.6; color: #1E293B; }
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

# --- API KEY (OPENAI) ---
api_key = st.secrets.get("OPENAI_API_KEY")
if not api_key:
    st.error("⚠️ Error: Falta API Key de OpenAI en Secrets.")
    st.stop()
client = OpenAI(api_key=api_key)

# =======================================================
# === 🔐 SISTEMA DE ACCESO (GOOGLE SHEETS) BLINDADO ===
# =======================================================

def obtener_usuarios_sheet():
    try:
        # 1. Cargamos los secretos
        creds_info = dict(st.secrets["gcp_service_account"])
        
        # Corrección de la llave para evitar error de padding
        if "private_key" in creds_info:
            creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
            
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
        client_gs = gspread.authorize(creds)
        
        # 2. Abrimos el archivo por su nombre EXACTO
        archivo = client_gs.open("Usuarios_InmoApp")
        
        # 3. Tomamos la PRIMERA hoja (índice 0)
        sheet = archivo.get_worksheet(0)
        
        return sheet.get_all_records()

    except Exception as e:
        return []

with st.sidebar:
    st.header("🔐 Área de Miembros")
    codigo_acceso = st.text_input("Código de Acceso:", type="password", placeholder="Ej: PRUEBA1", key="input_codigo")
    
    plan_actual = "GRATIS"
    limite_fotos = 1
    es_pro = False
    usuario_nombre = ""
    creditos_disponibles = 0
    
    if codigo_acceso:
        usuarios_db = obtener_usuarios_sheet()
        usuario_encontrado = next((u for u in usuarios_db if str(u.get('codigo', '')).strip().upper() == codigo_acceso.strip().upper()), None)
        
        if usuario_encontrado:
            plan_actual = usuario_encontrado.get('plan', 'GRATIS')
            # Leemos el límite del Excel
            limite_raw = usuario_encontrado.get('limite', 1)
            limite_fotos = int(limite_raw) if limite_raw != "" else 1
            creditos_disponibles = limite_fotos
            
            usuario_nombre = usuario_encontrado.get('cliente', 'Usuario')
            es_pro = True
            st.session_state.ver_planes = False 
            
            st.success(f"✅ ¡Hola {usuario_nombre}!")
            # --- NUEVO: MOSTRAR CRÉDITOS ---
            st.info(f"🪙 Créditos: {creditos_disponibles}")
            
            if st.button("🔒 Cerrar Sesión"):
                st.session_state.input_codigo = ""
                st.rerun()
        else:
            if usuarios_db: 
                st.error("❌ Código no válido.")
            else:
                st.warning("⚠️ Conectando...")

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
        st.error(f"⛔ Tu límite es de {limite_fotos} fotos/créditos. Has subido {len(uploaded_files)}. Elimina algunas para continuar.")
        st.stop()
    
    with st.expander("👁️ Ver fotos cargadas", expanded=True):
        cols = st.columns(4)
        for i, f in enumerate(uploaded_files):
            with cols[i%4]: st.image(Image.open(f), use_container_width=True)

    st.divider()
    st.write("#### 2. 📝 Datos de la Propiedad")
    c1, c2 = st.columns(2)
    with c1:
        oper = st.radio("Operación", ["Venta", "Alquiler"], horizontal=True)
        tipo = st.selectbox("Tipo", ["Casa", "Departamento", "Terreno", "Local", "Duplex"])
        
        # Estrategias
        opciones_estrategia = ["Equilibrado", "🔥 Urgencia", "🔑 Primera Casa", "💎 Lujo", "💰 Inversión"]
        if not es_pro:
            opciones_estrategia = ["🔒 Bloqueado (Solo PRO)"]
        
        enfoque = st.selectbox("🎯 Estrategia", opciones_estrategia, disabled=not es_pro)
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
    if es_pro: 
        st.info("🧠 **Neuro-Vision Activa:** Analizando fotos...")
        
        # --- BOTÓN DE GENERACIÓN ---
        if st.button("✨ Generar Estrategia", type="primary"):
            if not ubicacion or not texto_precio:
                st.warning("⚠️ Completa Ubicación y Precio.")
            else:
                with st.spinner('🧠 Redactando estrategia ganadora...'):
                    try:
                        # PROMPT MODIFICADO: SIN AIDA, SIN MARKDOWN
                        prompt = f"""Actúa como copywriter inmobiliario experto. Crea 3 opciones de texto para {oper} de {tipo} en {ubicacion}.
                        
                        OPCIÓN 1: Storytelling emotivo ({enfoque}).
                        OPCIÓN 2: Venta Directa y Persuasiva (Sé breve y contundente).
                        OPCIÓN 3: Formato Instagram (Corto + Hashtags).
                        
                        Datos: Precio: {texto_precio}. Extras: Quincho={q}, Piscina={p}, Cochera={c}. Hab: {habs}. Baños: {banos}.
                        Link WhatsApp: https://wa.me/595{whatsapp}.
                        
                        REGLAS DE FORMATO OBLIGATORIAS:
                        1. NO uses símbolos de Markdown como #, ##, ***, **.
                        2. Usa EMOJIS al principio de cada título o punto importante.
                        3. Separa las opciones con una línea divisoria."""
                        
                        content = [{"type": "text", "text": prompt}]
                        for f in uploaded_files:
                            f.seek(0)
                            content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(Image.open(f))}"}})
                        
                        res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": content}])
                        generated_text = res.choices[0].message.content

                        # --- LIMPIEZA DE CÓDIGO (Reemplazo forzado de símbolos) ---
                        cleaned_text = generated_text.replace("### ", "🔹 ").replace("###", "🔹")
                        cleaned_text = cleaned_text.replace("## ", "🏘️ ").replace("##", "🏘️")
                        cleaned_text = cleaned_text.replace("# ", "🚀 ").replace("#", "🚀")
                        cleaned_text = cleaned_text.replace("**", "") # Elimina negritas
                        cleaned_text = cleaned_text.replace("* ", "▪️ ").replace("- ", "▪️ ")
                        cleaned_text = cleaned_text.replace("___", "〰️〰️〰️").replace("---", "〰️〰️〰️")

                        st.success("¡Estrategia lista! Copia el texto abajo.")
                        
                        # Mostramos el texto limpio
                        st.write(cleaned_text)
                        
                        # --- MOSTRAMOS LAS FOTOS AL FINAL ---
                        st.divider()
                        st.caption("📸 Fotos utilizadas:")
                        cols_out = st.columns(4)
                        for i, f in enumerate(uploaded_files):
                             f.seek(0)
                             with cols_out[i%4]: st.image(Image.open(f), use_container_width=True)

                    except Exception as e:
                        st.error(f"Error al generar: {e}")
                        if "401" in str(e):
                            st.error("⚠️ Error de Llave: Verifica tu API KEY de OpenAI en Secrets.")

    else: 
        st.warning("⚠️ Vision IA Desactivada. Actualiza a PRO para generar.")
