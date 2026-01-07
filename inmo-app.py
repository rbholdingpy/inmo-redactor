import streamlit as st
from PIL import Image
import base64
import io
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from openai import OpenAI
import time

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="VendeMás IA",
    page_icon="🚀",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .main { background-color: #F8FAFC; }
    h1 { color: #0F172A; font-family: 'Helvetica Neue', sans-serif; font-weight: 800; }
    .stButton>button {
        background-color: #2563EB; color: white; border-radius: 8px; border: none;
        padding: 12px; font-weight: bold; width: 100%;
    }
    .stButton>button:hover { background-color: #1D4ED8; }
    .pro-badge { background-color: #DCFCE7; color: #166534; padding: 5px 10px; border-radius: 20px; font-weight: bold; font-size: 0.8em; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIONES DE APOYO ---
def encode_image(image):
    buffered = io.BytesIO()
    if image.mode in ("RGBA", "P"): image = image.convert("RGB")
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def limpiar_formulario():
    # Borra los campos pero MANTIENE la sesión
    keys_a_borrar = ['input_ubicacion', 'input_precio', 'input_whatsapp', 'generated_result']
    for key in keys_a_borrar:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state['uploader_key'] += 1
    st.rerun()

def cerrar_sesion():
    st.session_state['usuario_activo'] = None
    st.rerun()

# --- INICIALIZACIÓN DE ESTADO ---
if 'uploader_key' not in st.session_state: st.session_state['uploader_key'] = 0
if 'usuario_activo' not in st.session_state: st.session_state['usuario_activo'] = None
if 'ver_planes' not in st.session_state: st.session_state['ver_planes'] = False

# --- API KEY (OPENAI) ---
api_key = st.secrets.get("OPENAI_API_KEY")
if not api_key:
    st.error("⚠️ Error: Falta API Key de OpenAI en Secrets.")
    st.stop()
client = OpenAI(api_key=api_key)

# =======================================================
# === 🔐 CONEXIÓN GOOGLE SHEETS (LECTURA Y ESCRITURA) ===
# =======================================================
def get_gspread_client():
    creds_info = dict(st.secrets["gcp_service_account"])
    if "private_key" in creds_info:
        creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
    client_gs = gspread.authorize(creds)
    return client_gs

def obtener_usuarios_sheet():
    try:
        client_gs = get_gspread_client()
        archivo = client_gs.open("Usuarios_InmoApp")
        sheet = archivo.get_worksheet(0)
        return sheet.get_all_records()
    except Exception:
        return []

def descontar_credito(codigo_usuario):
    """Busca al usuario en el Excel y resta 1 crédito"""
    try:
        client_gs = get_gspread_client()
        sheet = client_gs.open("Usuarios_InmoApp").get_worksheet(0)
        
        # 1. Buscar la celda donde está el código del usuario
        cell = sheet.find(str(codigo_usuario))
        
        if cell:
            # 2. Encontrar la columna 'limite'
            # (Asumimos que está en la fila 1, buscamos su índice)
            headers = sheet.row_values(1)
            try:
                col_limite = headers.index('limite') + 1 # +1 porque gspread empieza en 1
            except ValueError:
                return False # No encontró la columna limite
            
            # 3. Obtener valor actual y restar
            valor_actual = sheet.cell(cell.row, col_limite).value
            if valor_actual and int(valor_actual) > 0:
                nuevo_saldo = int(valor_actual) - 1
                sheet.update_cell(cell.row, col_limite, nuevo_saldo)
                return True
    except Exception as e:
        print(f"Error al descontar: {e}")
        return False
    return False

# =======================================================
# === 🏗️ BARRA LATERAL (LOGIN CON BOTÓN) ===
# =======================================================
with st.sidebar:
    st.header("🔐 Área de Miembros")
    
    if not st.session_state['usuario_activo']:
        with st.form("login_form"):
            codigo_input = st.text_input("Ingresa tu Código:", type="password", placeholder="Ej: PRUEBA1")
            submit_login = st.form_submit_button("🔓 Entrar")
            
        if submit_login and codigo_input:
            usuarios_db = obtener_usuarios_sheet()
            usuario_encontrado = next((u for u in usuarios_db if str(u.get('codigo', '')).strip().upper() == codigo_input.strip().upper()), None)
            
            if usuario_encontrado:
                st.session_state['usuario_activo'] = usuario_encontrado
                st.session_state['ver_planes'] = False
                st.rerun()
            else:
                st.error("❌ Código incorrecto.")
    
    else:
        user = st.session_state['usuario_activo']
        plan_actual = user.get('plan', 'GRATIS')
        # Nos aseguramos de leer el límite actualizado si es posible, o usamos el de sesión
        limite_raw = user.get('limite', 1)
        limite_fotos = int(limite_raw) if limite_raw != "" else 1
        
        st.success(f"✅ ¡Hola {user.get('cliente', 'Usuario')}!")
        
        # Color del badge según créditos
        color_cred = "blue" if limite_fotos > 0 else "red"
        st.markdown(f":{color_cred}[**🪙 Créditos: {limite_fotos}**]")
        
        if st.button("🔒 Cerrar Sesión"):
            cerrar_sesion()

    st.divider()
    if st.toggle("💎 Ver Planes y Precios", key="toggle_planes"):
        st.session_state.ver_planes = True
    else:
        st.session_state.ver_planes = False
        
    st.caption("© 2026 VendeMás IA")

# =======================================================
# === ZONA DE VENTAS (PLANES) ===
# =======================================================
if st.session_state.ver_planes and (not st.session_state['usuario_activo'] or st.session_state['usuario_activo'].get('plan') == 'GRATIS'):
    st.title("💎 Desbloquea tu Potencial")
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown('<div class="plan-card"><h3>🥉 Básico</h3><h2>20.000 Gs</h2><p>10 Anuncios</p></div>', unsafe_allow_html=True)
    with c2: st.markdown('<div class="plan-card highlight-card"><h3>🥈 Estándar</h3><h2>35.000 Gs</h2><p>20 Anuncios</p></div>', unsafe_allow_html=True)
    with c3: st.markdown('<div class="plan-card"><h3>🥇 Agencia</h3><h2>80.000 Gs</h2><p>200 Mensual</p></div>', unsafe_allow_html=True)
    st.stop()

# =======================================================
# === APP PRINCIPAL ===
# =======================================================
c_title, c_badge = st.columns([2, 1])
with c_title:
    st.title("🚀 VendeMás IA")
    st.caption("Experto en Neuroventas Inmobiliarias.")

with c_badge:
    if st.session_state['usuario_activo']:
        plan = st.session_state['usuario_activo'].get('plan', 'GRATIS')
        st.markdown(f'<div style="text-align:right"><span class="pro-badge">PLAN {plan.upper()}</span></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="text-align:right"><span style="background-color:#F1F5F9; color:#64748B; padding:5px; border-radius:10px;">🔒 INICIA SESIÓN</span></div>', unsafe_allow_html=True)

if not st.session_state['usuario_activo']:
    st.info("👈 Ingresa tu código en la barra lateral y pulsa 'Entrar' para comenzar.")
    st.stop()

# --- DATOS DEL USUARIO LOGUEADO ---
user = st.session_state['usuario_activo']
limite_fotos = int(user.get('limite', 1) if user.get('limite') != "" else 0)

# BLOQUEO SI NO HAY CRÉDITOS
if limite_fotos <= 0:
    st.error("⛔ **¡Te has quedado sin créditos!**")
    st.warning("Por favor contacta al administrador o recarga tu plan para seguir generando.")
    st.stop()

st.write("#### 1. 📸 Galería")
uploaded_files = st.file_uploader("Subir fotos", type=["jpg", "png", "jpeg"], accept_multiple_files=True, key=f"uploader_{st.session_state['uploader_key']}")

if uploaded_files:
    # (Opcional) Puedes limitar fotos por subida, pero aquí limitamos por crédito de generación
    pass 
    
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
        
        opciones_estrategia = ["Equilibrado", "🔥 Urgencia", "🔑 Primera Casa", "💎 Lujo", "💰 Inversión"]
        enfoque = st.selectbox("🎯 Estrategia", opciones_estrategia)
        
        ubicacion = st.text_input("Ubicación", key="input_ubicacion")
        
        if oper == "Alquiler":
            cp, cf = st.columns([2, 1])
            precio_val = cp.text_input("Precio", key="input_precio")
            frec = cf.selectbox("Periodo", ["Mensual", "Semestral", "Anual"])
            texto_precio = f"{precio_val} ({frec})"
        else:
            texto_precio = st.text_input("Precio", key="input_precio")
            
        whatsapp = st.text_input("WhatsApp (Solo números)", key="input_whatsapp")

    with c2:
        habs = st.number_input("Habitaciones", 1)
        banos = st.number_input("Baños", 1)
        st.write("**Extras:**")
        q = st.checkbox("Quincho")
        p = st.checkbox("Piscina")
        c = st.checkbox("Cochera")

    st.divider()
    st.info(f"🧠 **Neuro-Vision Activa:** Analizando fotos... (Te costará 1 crédito)")
    
    # --- BOTÓN DE GENERACIÓN ---
    if st.button("✨ Generar Estrategia (-1 Crédito)", type="primary"):
        if not ubicacion or not texto_precio:
            st.warning("⚠️ Completa Ubicación y Precio.")
        else:
            with st.spinner('🧠 Escribiendo y descontando crédito...'):
                try:
                    # 1. GENERAR CON IA
                    prompt = f"""Actúa como copywriter inmobiliario. 
                    OPCIÓN 1: Storytelling ({enfoque}).
                    OPCIÓN 2: Venta Directa (Sin AIDA).
                    OPCIÓN 3: Instagram (Corto + Hashtags).
                    Datos: {oper} {tipo} en {ubicacion}. Precio: {texto_precio}. Extras: Q={q}, P={p}, C={c}. Hab:{habs}, Baños:{banos}.
                    WhatsApp: https://wa.me/595{whatsapp}.
                    REGLAS: NO uses Markdown (#, **). Usa EMOJIS al inicio de items. Línea divisoria entre opciones."""
                    
                    content = [{"type": "text", "text": prompt}]
                    for f in uploaded_files:
                        f.seek(0)
                        content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(Image.open(f))}"}})
                    
                    res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": content}])
                    generated_text = res.choices[0].message.content

                    # Limpieza
                    cleaned_text = generated_text.replace("###", "🔹").replace("##", "🏘️").replace("#", "🚀")
                    cleaned_text = cleaned_text.replace("**", "").replace("* ", "▪️ ").replace("- ", "▪️ ")
                    
                    # 2. DESCONTAR CRÉDITO EN GOOGLE SHEETS
                    exito_descuento = descontar_credito(user['codigo'])
                    
                    if exito_descuento:
                        # Actualizamos la sesión local para que el usuario vea el cambio ya
                        st.session_state['usuario_activo']['limite'] = limite_fotos - 1
                        st.toast("✅ Crédito descontado correctamente", icon="🪙")
                    else:
                        st.warning("⚠️ Hubo un error actualizando tu saldo, pero aquí tienes tu texto.")

                    # Guardamos resultado
                    st.session_state['generated_result'] = cleaned_text
                    
                except Exception as e:
                    st.error(f"Error: {e}")

    # --- MOSTRAR RESULTADO ---
    if 'generated_result' in st.session_state:
        st.success("¡Estrategia lista! Copia el texto abajo.")
        st.write(st.session_state['generated_result'])
        
        st.divider()
        st.caption("📸 Fotos utilizadas:")
        cols_out = st.columns(4)
        for i, f in enumerate(uploaded_files):
             f.seek(0)
             with cols_out[i%4]: st.image(Image.open(f), use_container_width=True)
        
        st.markdown("---")
        st.subheader("¿Terminaste con esta propiedad?")
        if st.button("🔄 Analizar Otra Propiedad (Limpiar Pantalla)", type="secondary"):
            limpiar_formulario()
