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
        transition: transform 0.2s;
    }
    .stButton>button:hover { 
        background-color: #1D4ED8; 
        transform: scale(1.02);
    }
    .pro-badge { background-color: #DCFCE7; color: #166534; padding: 5px 10px; border-radius: 20px; font-weight: bold; font-size: 0.8em; }
    .plan-card {
        background-color: white; padding: 20px; border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center; border: 1px solid #E2E8F0; margin-bottom: 10px;
    }
    .highlight-card {
        border: 2px solid #2563EB; background-color: #EFF6FF;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIONES DE APOYO ---
def encode_image(image):
    buffered = io.BytesIO()
    if image.mode in ("RGBA", "P"): image = image.convert("RGB")
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def limpiar_formulario():
    keys_a_borrar = ['input_ubicacion', 'input_precio', 'input_whatsapp', 'generated_result']
    for key in keys_a_borrar:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state['uploader_key'] += 1
    # No es necesario rerun aquí si se llama desde un botón, pero por seguridad:
    # st.rerun() 

def cerrar_sesion():
    st.session_state['usuario_activo'] = None
    st.session_state['plan_seleccionado'] = None
    st.session_state['ver_planes'] = False
    # st.rerun()

# --- FUNCIONES CALLBACK (SOLUCIÓN AL ERROR DE SALTO) ---
def ir_a_planes():
    st.session_state.ver_planes = True
    st.session_state.plan_seleccionado = None

def seleccionar_plan(nombre_plan):
    st.session_state.plan_seleccionado = nombre_plan
    # Forzamos que ver_planes siga siendo True para que no se salga de la pantalla
    st.session_state.ver_planes = True

def volver_a_app():
    st.session_state.ver_planes = False
    st.session_state.plan_seleccionado = None

def cancelar_seleccion():
    st.session_state.plan_seleccionado = None
    st.session_state.ver_planes = True

# --- INICIALIZACIÓN DE ESTADO ---
if 'uploader_key' not in st.session_state: st.session_state['uploader_key'] = 0
if 'usuario_activo' not in st.session_state: st.session_state['usuario_activo'] = None
if 'ver_planes' not in st.session_state: st.session_state['ver_planes'] = False
if 'plan_seleccionado' not in st.session_state: st.session_state['plan_seleccionado'] = None

# --- API KEY (OPENAI) ---
api_key = st.secrets.get("OPENAI_API_KEY")
if not api_key:
    st.error("⚠️ Error: Falta API Key de OpenAI en Secrets.")
    st.stop()
client = OpenAI(api_key=api_key)

# =======================================================
# === 🔐 CONEXIÓN GOOGLE SHEETS ===
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
    try:
        client_gs = get_gspread_client()
        sheet = client_gs.open("Usuarios_InmoApp").get_worksheet(0)
        cell = sheet.find(str(codigo_usuario))
        if cell:
            headers = sheet.row_values(1)
            try:
                col_limite = headers.index('limite') + 1 
            except ValueError:
                return False
            
            valor_actual = sheet.cell(cell.row, col_limite).value
            if valor_actual and int(valor_actual) > 0:
                nuevo_saldo = int(valor_actual) - 1
                sheet.update_cell(cell.row, col_limite, nuevo_saldo)
                return True
    except Exception:
        return False
    return False

# =======================================================
# === 🏗️ BARRA LATERAL ===
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
                # Aseguramos estado inicial al loguearse
                st.session_state['ver_planes'] = False
                st.rerun()
            else:
                st.error("❌ Código incorrecto.")
    
    else:
        user = st.session_state['usuario_activo']
        limite_raw = user.get('limite', 1)
        limite_fotos = int(limite_raw) if limite_raw != "" else 1
        
        st.success(f"✅ ¡Hola {user.get('cliente', 'Usuario')}!")
        
        color_cred = "blue" if limite_fotos > 0 else "red"
        st.markdown(f":{color_cred}[**🪙 Créditos: {limite_fotos}**]")
        
        st.markdown("---")
        # Usamos on_click para estabilidad
        st.button("🚀 SUBE DE NIVEL\nAprovecha más", type="primary", on_click=ir_a_planes)

        st.markdown("---")
        if st.button("🔒 Cerrar Sesión"):
            cerrar_sesion()
            st.rerun()

    st.caption("© 2026 VendeMás IA")

# =======================================================
# === 💎 ZONA DE VENTAS (CONTROLADA POR VER_PLANES) ===
# =======================================================
if st.session_state.ver_planes:
    st.title("💎 Elige tu Nivel")
    
    # PASO 1: MOSTRAR PLANES (Si no hay selección)
    if st.session_state.plan_seleccionado is None:
        c1, c2, c3 = st.columns(3)
        
        with c1:
            st.markdown('<div class="plan-card"><h3>🥉 Básico</h3><h2>20.000 Gs</h2><p>10 Anuncios</p></div>', unsafe_allow_html=True)
            # USAMOS ON_CLICK + ARGS -> Esto evita que la app se resetee al hacer clic
            st.button("Elegir Básico", key="btn_basico", on_click=seleccionar_plan, args=("Básico (20.000 Gs)",))

        with c2:
            st.markdown('<div class="plan-card highlight-card"><h3>🥈 Estándar</h3><h2>35.000 Gs</h2><p>20 Anuncios</p></div>', unsafe_allow_html=True)
            st.button("Elegir Estándar", key="btn_estandar", type="primary", on_click=seleccionar_plan, args=("Estándar (35.000 Gs)",))

        with c3:
            st.markdown('<div class="plan-card"><h3>🥇 Agencia</h3><h2>80.000 Gs</h2><p>200 Mensual</p></div>', unsafe_allow_html=True)
            st.button("Elegir Agencia", key="btn_agencia", on_click=seleccionar_plan, args=("Agencia (80.000 Gs)",))
        
        st.divider()
        st.button("⬅️ Volver a la App", on_click=volver_a_app)

    # PASO 2: MOSTRAR DATOS DE PAGO (Si ya seleccionó)
    else:
        st.info(f"🚀 Has seleccionado: **Plan {st.session_state.plan_seleccionado}**")
        
        col_bank, col_wa = st.columns(2)
        
        with col_bank:
            st.subheader("1. Transfiere Aquí")
            st.markdown("""
            <div style="background-color:white; padding:15px; border-radius:10px; border:1px solid #ddd; color: #333;">
            <b>Banco:</b> ITAÚ <br>
            <b>Titular:</b> Ricardo Blanco <br>
            <b>C.I.:</b> 1911221 <br>
            <b>Cuenta:</b> 320595209 <br>
            <b>RUC:</b> 1911221-1
            </div>
            """, unsafe_allow_html=True)
            
        with col_wa:
            st.subheader("2. Activa tu Plan")
            st.write("Envía el comprobante para cargar tus créditos.")
            
            codigo_usuario = st.session_state['usuario_activo'].get('codigo', 'N/A') if st.session_state['usuario_activo'] else "Nuevo"
            mensaje_wp = f"Hola, realicé la transferencia para el *Plan {st.session_state.plan_seleccionado}*. Mi código es: *{codigo_usuario}*."
            # Codificamos espacios para URL
            mensaje_wp_url = mensaje_wp.replace(" ", "%20").replace("\n", "%0A")
            link_wp = f"https://wa.me/595981000000?text={mensaje_wp_url}"
            
            st.markdown(f"""
            <a href="{link_wp}" target="_blank" style="text-decoration:none;">
                <button style="background-color:#25D366; color:white; border:none; padding:15px; border-radius:8px; width:100%; font-weight:bold; cursor:pointer; font-size:1.1em; margin-top:10px;">
                📲 Enviar Comprobante por WhatsApp
                </button>
            </a>
            """, unsafe_allow_html=True)
            
        st.divider()
        c_back, c_cancel = st.columns(2)
        with c_back:
            st.button("🔙 Elegir otro plan", on_click=cancelar_seleccion)
        with c_cancel:
            st.button("❌ Cancelar y Volver", on_click=volver_a_app)

    st.stop() # DETIENE LA EJECUCIÓN AQUÍ PARA NO MOSTRAR EL RESTO

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
    st.warning("Pulsa el botón 'SUBE DE NIVEL' en la barra lateral para recargar.")
    st.stop()

st.write("#### 1. 📸 Galería")
uploaded_files = st.file_uploader("Subir fotos", type=["jpg", "png", "jpeg"], accept_multiple_files=True, key=f"uploader_{st.session_state['uploader_key']}")

if uploaded_files:
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

                    cleaned_text = generated_text.replace("###", "🔹").replace("##", "🏘️").replace("#", "🚀")
                    cleaned_text = cleaned_text.replace("**", "").replace("* ", "▪️ ").replace("- ", "▪️ ")
                    
                    exito_descuento = descontar_credito(user['codigo'])
                    
                    if exito_descuento:
                        st.session_state['usuario_activo']['limite'] = limite_fotos - 1
                        st.toast("✅ Crédito descontado correctamente", icon="🪙")
                    else:
                        st.warning("⚠️ Hubo un error actualizando tu saldo, pero aquí tienes tu texto.")

                    st.session_state['generated_result'] = cleaned_text
                    
                except Exception as e:
                    st.error(f"Error: {e}")

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
        if st.button("🔄 Analizar Otra Propiedad (Limpiar Pantalla)", type="secondary", on_click=limpiar_formulario):
             pass
