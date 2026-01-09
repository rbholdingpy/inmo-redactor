import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps
import base64
import io
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from openai import OpenAI
import time
from datetime import datetime, timedelta
import urllib.parse
import os
import tempfile
import numpy as np
import shutil 
import re 

# ==========================================
# 🚀 CONFIGURACIÓN DE LANZAMIENTO
# ==========================================
MODO_LANZAMIENTO = True 

# --- IMPORTACIÓN CONDICIONAL DE MOVIEPY ---
try:
    from moviepy.editor import ImageClip, concatenate_videoclips
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="AppyProp IA", 
    page_icon="🚀",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- TU NÚMERO DE ADMINISTRADOR ---
ADMIN_WHATSAPP = "595961871700" 

# --- ESTILOS CSS (MODO EXPERIENCIA PERFECTA) ---
st.markdown("""
    <style>
    .main { background-color: #F8FAFC; }
    h1 { color: #0F172A; font-family: 'Helvetica Neue', sans-serif; font-weight: 800; }
    
    .stButton>button {
        border-radius: 8px; border: none; padding: 12px; font-weight: bold; width: 100%; transition: all 0.2s;
    }
    .stButton>button:hover { transform: scale(1.02); }
    
    /* Botón deshabilitado */
    .stButton>button:disabled {
        background-color: #CBD5E1; color: #64748B; cursor: not-allowed;
    }

    /* --- 1. STATUS FLOTANTE EN EL CENTRO (EL RELOJ) --- */
    div[data-testid="stStatusWidget"] {
        position: fixed !important;
        top: 50% !important;
        left: 50% !important;
        transform: translate(-50%, -50%) !important;
        z-index: 999999 !important;
        background-color: white !important;
        padding: 25px !important;
        border-radius: 15px !important;
        box-shadow: 0 0 0 100vmax rgba(0,0,0,0.6) !important; /* Fondo oscuro */
        border: 2px solid #2563EB !important;
        width: 85% !important;
        max-width: 350px !important;
        text-align: center !important;
    }

    /* --- 2. ELIMINAR EFECTOS DE CARGA NATIVOS --- */
    .stApp, [data-testid="stAppViewContainer"] {
        opacity: 1 !important; filter: none !important; transition: none !important; will-change: auto !important;
    }
    [data-testid="InputInstructions"] { display: none !important; }
    /* ------------------------------------------- */

    .video-container { background-color: #000; border-radius: 20px; padding: 10px; box-shadow: 0 10px 25px rgba(0,0,0,0.2); max-width: 350px; margin: 0 auto; }
    
    /* UPLOADER */
    [data-testid='stFileUploaderDropzoneInstructions'] > div:first-child { display: none; }
    [data-testid='stFileUploaderDropzoneInstructions']::before { content: "📸 Toca para subir fotos"; visibility: visible; display: block; text-align: center; font-weight: bold; font-size: 1.2em; color: #2563EB; }
    [data-testid='stFileUploaderDropzoneInstructions']::after { content: "Máx 10 fotos"; visibility: visible; display: block; text-align: center; font-size: 0.8em; }
    [data-testid='stFileUploader'] button { color: transparent !important; position: relative; }
    [data-testid='stFileUploader'] button::after { content: "📂 Galería"; color: #333; position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%); font-weight: bold; font-size: 14px; }

    /* BOTÓN FLOTANTE */
    [data-testid="stSidebarCollapsedControl"] { background-color: #2563EB !important; color: white !important; border-radius: 8px !important; padding: 5px !important; }
    [data-testid="stSidebarCollapsedControl"] svg { fill: white !important; color: white !important; }

    /* Ocultar flechas de los campos numéricos (PRECIO y WHATSAPP) */
    input[type=number]::-webkit-inner-spin-button, 
    input[type=number]::-webkit-outer-spin-button { 
        -webkit-appearance: none; 
        margin: 0; 
    }
    input[type=number] { -moz-appearance: textfield; }

    .output-box { background-color: white; padding: 25px; border-radius: 10px; border: 1px solid #cbd5e1; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    
    /* Botones Sociales */
    .social-btn {
        display: block; width: 100%; padding: 12px; margin: 8px 0; border-radius: 8px; text-align: center; text-decoration: none; font-weight: bold; color: white !important; box-shadow: 0 2px 5px rgba(0,0,0,0.2); transition: transform 0.1s;
    }
    .social-btn:active { transform: scale(0.98); }
    .btn-wp { background-color: #25D366; }
    .btn-ig { background: linear-gradient(45deg, #f09433 0%,#e6683c 25%,#dc2743 50%,#cc2366 75%,#bc1888 100%); }
    .btn-fb { background-color: #1877F2; }
    .btn-tk { background-color: #000000; }
    
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIONES DE APOYO ---
def encode_image(image):
    buffered = io.BytesIO()
    if image.mode in ("RGBA", "P"): image = image.convert("RGB")
    image.thumbnail((800, 800))
    image.save(buffered, format="JPEG", quality=70)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def format_price_display(value):
    """Formatea con puntos de miles para mostrar"""
    if not value: return ""
    try:
        return "{:,}".format(int(value)).replace(",", ".")
    except:
        return value

def limpiar_formulario():
    keys_a_borrar = ['input_ubicacion', 'input_precio', 'input_whatsapp', 'generated_result', 'input_monto', 'input_moneda', 'video_path', 'video_frases']
    for key in keys_a_borrar:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state['uploader_key'] += 1

def cerrar_sesion():
    st.session_state['usuario_activo'] = None
    st.session_state['plan_seleccionado'] = None
    st.session_state['ver_planes'] = False
    st.session_state['pedido_registrado'] = False

# --- CALLBACKS ---
def ir_a_planes():
    st.session_state.ver_planes = True
    st.session_state.plan_seleccionado = None
    st.session_state.pedido_registrado = False

def seleccionar_plan(nombre_plan):
    st.session_state.plan_seleccionado = nombre_plan
    st.session_state.ver_planes = True
    st.session_state.pedido_registrado = False

def volver_a_app():
    st.session_state.ver_planes = False
    st.session_state.plan_seleccionado = None
    st.session_state.pedido_registrado = False

def cancelar_seleccion():
    st.session_state.plan_seleccionado = None
    st.session_state.ver_planes = True
    st.session_state.pedido_registrado = False

# --- FUNCIÓN GENERADORA DE VIDEO REEL ---
def crear_reel_vertical(imagenes_uploaded, textos_clave, status_container=None):
    if not MOVIEPY_AVAILABLE or not imagenes_uploaded: return None
    
    num_fotos = len(imagenes_uploaded)
    duracion_por_foto = 20.0 / num_fotos
    if duracion_por_foto < 2.0: duracion_por_foto = 2.0 

    clips = []
    W, H = 720, 1280 
    font = ImageFont.load_default()
    temp_dir = tempfile.mkdtemp()

    for i, img_file in enumerate(imagenes_uploaded):
        try:
            if status_container: status_container.update(label=f"🎞️ Procesando foto {i+1}/{num_fotos}...")
            
            img_file.seek(0)
            img = Image.open(img_file).convert("RGB")
            img.thumbnail((1200, 1200)) 
            img = ImageOps.fit(img, (W, H), method=Image.Resampling.LANCZOS)
            overlay = Image.new('RGBA', (W, H), (0, 0, 0, 80))
            img.paste(overlay, (0, 0), overlay)
            draw = ImageDraw.Draw(img)
            
            texto_actual = textos_clave[i % len(textos_clave)] if textos_clave else "AppyProp IA"
            draw.text((W/2, H*0.8), texto_actual, font=font, fill="white", anchor="mm", align="center")
            draw.text((W/2, H*0.95), "Generado con AppyProp IA 🚀", fill="#cccccc", anchor="mm", font=font)
            
            temp_img_path = os.path.join(temp_dir, f"temp_frame_{i}.jpg")
            img.save(temp_img_path, quality=70, optimize=True)
            clip = ImageClip(temp_img_path).set_duration(duracion_por_foto)
            clips.append(clip)

        except Exception as e:
            print(f"Error procesando imagen {i}: {e}")
            continue

    if not clips:
        try: shutil.rmtree(temp_dir)
        except: pass
        return None

    if status_container: status_container.update(label="🎞️ Renderizando video final...")
    
    final_clip = concatenate_videoclips(clips, method="compose")
    if final_clip.duration > 20.0: final_clip = final_clip.subclip(0, 20.0)

    tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    output_path = tfile.name
    tfile.close()

    final_clip.write_videofile(
        output_path, codec="libx264", audio=False, fps=15, preset='ultrafast',
        ffmpeg_params=['-pix_fmt', 'yuv420p'], threads=1, logger=None
    )
    
    try: shutil.rmtree(temp_dir)
    except: pass
        
    return output_path

# --- INICIALIZACIÓN ---
if 'uploader_key' not in st.session_state: st.session_state['uploader_key'] = 0
if 'usuario_activo' not in st.session_state: st.session_state['usuario_activo'] = None
if 'ver_planes' not in st.session_state: st.session_state['ver_planes'] = False
if 'plan_seleccionado' not in st.session_state: st.session_state['plan_seleccionado'] = None
if 'pedido_registrado' not in st.session_state: st.session_state['pedido_registrado'] = False

if 'guest_last_use' not in st.session_state: st.session_state['guest_last_use'] = None
if 'guest_credits' not in st.session_state: st.session_state['guest_credits'] = 1

if st.session_state['guest_last_use']:
    tiempo_pasado = datetime.now() - st.session_state['guest_last_use']
    if tiempo_pasado > timedelta(days=1):
        st.session_state['guest_credits'] = 1
        st.session_state['guest_last_use'] = None

# --- API KEY ---
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
            col_limite = headers.index('limite') + 1 
            valor_actual = sheet.cell(cell.row, col_limite).value
            if valor_actual and int(valor_actual) > 0:
                nuevo_saldo = int(valor_actual) - 1
                sheet.update_cell(cell.row, col_limite, nuevo_saldo)
                return True
    except Exception:
        return False
    return False

def registrar_pedido(nombre, apellido, email, telefono, nuevo_plan):
    try:
        client_gs = get_gspread_client()
        sheet = client_gs.open("Usuarios_InmoApp").get_worksheet(0)
        email_input_clean = str(email).strip().lower()
        lista_correos_raw = sheet.col_values(6)
        lista_correos_clean = [str(e).strip().lower() for e in lista_correos_raw]
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
        nombre_completo = f"{nombre} {apellido}"
        
        if email_input_clean in lista_correos_clean:
            row_index = lista_correos_clean.index(email_input_clean) + 1
            plan_actual_sheet = str(sheet.cell(row_index, 3).value).strip().lower()
            nuevo_plan_check = str(nuevo_plan).strip().lower()
            if nuevo_plan_check in plan_actual_sheet or plan_actual_sheet in nuevo_plan_check:
                return "SAME_PLAN"
            else:
                sheet.update_cell(row_index, 3, nuevo_plan) 
                sheet.update_cell(row_index, 5, telefono)   
                sheet.update_cell(row_index, 7, "SOLICITUD CAMBIO PLAN") 
                sheet.update_cell(row_index, 8, fecha)      
                return "UPDATED"
        else:
            nueva_fila = ["PENDIENTE", nombre_completo, nuevo_plan, 0, telefono, email, "NUEVO PEDIDO", fecha]
            sheet.append_row(nueva_fila)
            return "CREATED"
    except Exception as e:
        return "ERROR"

# =======================================================
# === 🏗️ BARRA LATERAL ===
# =======================================================
with st.sidebar:
    st.header("🔐 Área de Miembros")
    
    if not st.session_state['usuario_activo']:
        if MODO_LANZAMIENTO:
            st.markdown("""<div style="background-color:#FEF3C7; padding:10px; border-radius:8px; margin-bottom:15px; border:1px solid #F59E0B;"><small>Estado actual:</small><br><b>🚀 INVITADO VIP</b><br><span style="color:#B45309; font-size:0.8em;">Acceso Total (1 Crédito de Regalo)</span></div>""", unsafe_allow_html=True)
        else:
            st.markdown("""<div style="background-color:#F1F5F9; padding:10px; border-radius:8px; margin-bottom:15px;"><small>Estado actual:</small><br><b>👤 Invitado (Freemium)</b><br><span style="color:#64748B; font-size:0.8em;">1 Generación / 24hs</span></div>""", unsafe_allow_html=True)
            
        with st.form("login_form"):
            codigo_input = st.text_input("¿Tienes Código?", type="password", placeholder="Ej: PRUEBA1")
            submit_login = st.form_submit_button("🔓 Entrar como Miembro")
        if submit_login and codigo_input:
            usuarios_db = obtener_usuarios_sheet()
            usuario_encontrado = next((u for u in usuarios_db if str(u.get('codigo', '')).strip().upper() == codigo_input.strip().upper()), None)
            if usuario_encontrado:
                st.session_state['usuario_activo'] = usuario_encontrado
                st.session_state['ver_planes'] = False
                st.rerun()
            else:
                st.error("❌ Código incorrecto.")
        st.markdown("---")
        st.info("💡 **Los Invitados tienen funciones limitadas.**")
        st.button("🚀 VER PLANES PRO", on_click=ir_a_planes)
    else:
        user = st.session_state['usuario_activo']
        creditos_disponibles = int(user.get('limite', 0) if user.get('limite') != "" else 0)
        st.success(f"✅ ¡Hola {user.get('cliente', 'Usuario')}!")
        color_cred = "blue" if creditos_disponibles > 0 else "red"
        st.markdown(f":{color_cred}[**🪙 Créditos: {creditos_disponibles}**]")
        
        st.markdown("---")
        st.markdown("### 🛠️ Gestión Rápida")
        if st.button("🔄 Nueva Propiedad (Limpiar)", type="secondary"):
            limpiar_formulario()
            
        st.markdown("---")
        st.button("🚀 SUBE DE NIVEL\nAprovecha más", type="primary", on_click=ir_a_planes)
        st.markdown("---")
        if st.button("🔒 Cerrar Sesión"):
            cerrar_sesion()
            st.rerun()
    st.caption("© 2026 AppyProp IA")

# =======================================================
# === 💎 ZONA DE VENTAS ===
# =======================================================
if st.session_state.ver_planes:
    st.title("💎 Escala tus Ventas")
    st.write("Elige la potencia que necesita tu negocio.")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("""<div style="background-color:#F8FAFC; border:2px solid #475569; padding:15px; border-radius:10px; height:100%;"><h3 style="text-align:center;">🥉 Básico</h3><div style="text-align:center; font-size:1.4em; font-weight:bold;">20.000 Gs</div><ul style="padding-left:20px; font-size:0.9em;"><li>✅ 10 Créditos</li><li>❌ Video Reel</li><li>❌ Estrategias</li></ul></div>""", unsafe_allow_html=True)
        st.button("Elegir Básico", key="btn_basico", on_click=seleccionar_plan, args=("Básico",))

    with c2:
        st.markdown("""<div style="background-color:white; border:2px solid #3B82F6; padding:15px; border-radius:10px; height:100%;"><h3 style="text-align:center;">🥈 Estándar</h3><div style="text-align:center; font-size:1.4em; font-weight:bold; color:#2563EB;">35.000 Gs</div><ul style="padding-left:20px; font-size:0.9em;"><li>✅ 20 Créditos</li><li>✅ Estrategias</li><li>❌ Video Reel</li></ul></div>""", unsafe_allow_html=True)
        st.button("Elegir Estándar", key="btn_estandar", type="primary", on_click=seleccionar_plan, args=("Estándar",))

    with c3:
        st.markdown("""<div style="background: linear-gradient(135deg, #FFFBEB 0%, #FFFFFF 100%); border:2px solid #F59E0B; padding:15px; border-radius:10px; height:100%; box-shadow:0 4px 10px rgba(0,0,0,0.1);"><div style="text-align:center; background:#F59E0B; color:white; border-radius:5px; font-size:0.7em; font-weight:bold; width:fit-content; margin:0 auto;">🔥 RECOMENDADO</div><h3 style="text-align:center; color:#B45309;">🥇 Agencia</h3><div style="text-align:center; font-size:1.4em; font-weight:bold; color:#D97706;">80.000 Gs</div><ul style="padding-left:20px; font-size:0.9em;"><li>✅ 80 Créditos</li><li>✅ Estrategias</li><li>✅ 🎬 Video Reel</li></ul></div>""", unsafe_allow_html=True)
        st.button("👑 ELEGIR AGENCIA", key="btn_agencia", type="primary", on_click=seleccionar_plan, args=("Agencia",))
    
    st.divider()
    st.button("⬅️ Volver a la App", on_click=volver_a_app)
    
    if st.session_state.plan_seleccionado:
        st.info("Contacta al admin para activar.")
        st.button("🔙 Atrás", on_click=cancelar_seleccion)
    st.stop()

# =======================================================
# === APP PRINCIPAL ===
# =======================================================
c_title, c_badge = st.columns([2, 1])
st.markdown("<h1 style='text-align: center; margin-bottom: 0;'>AppyProp IA 🚀</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #1E293B; font-weight: 600; margin-top: 0; font-size: 1.2rem;'>Experto en Neuroventas Inmobiliarias</h3>", unsafe_allow_html=True)

es_pro = False
plan_actual = "INVITADO"
cupo_fotos = 0
puede_video = False

if st.session_state['usuario_activo']:
    es_pro = True
    user = st.session_state['usuario_activo']
    plan_str = str(user.get('plan', '')).lower()
    
    if 'agencia' in plan_str:
        cupo_fotos = 10
        plan_actual = "AGENCIA"
        puede_video = True
    elif 'estándar' in plan_str or 'standar' in plan_str:
        cupo_fotos = 6
        plan_actual = "ESTÁNDAR"
    else:
        cupo_fotos = 3
        plan_actual = "BÁSICO"

    creditos_disponibles = int(user.get('limite', 0) if user.get('limite') != "" else 0)
    st.markdown(f'<div style="text-align:center; margin-top: 10px;"><span class="pro-badge">PLAN {plan_actual}</span></div>', unsafe_allow_html=True)
else:
    es_pro = False
    creditos_disponibles = st.session_state['guest_credits']
    if MODO_LANZAMIENTO:
        plan_actual = "INVITADO VIP"
        cupo_fotos = 10
        puede_video = True 
        st.markdown('<div style="text-align:center; margin-top: 10px;"><span class="launch-badge">🚀 MODO LANZAMIENTO: ACCESO TOTAL</span></div>', unsafe_allow_html=True)
    else:
        plan_actual = "INVITADO"
        cupo_fotos = 0
        puede_video = False
        st.markdown('<div style="text-align:center; margin-top: 10px;"><span class="free-badge">MODO FREEMIUM</span></div>', unsafe_allow_html=True)

if not es_pro and not MODO_LANZAMIENTO:
    st.info("👈 **¿Ya eres miembro?** Toca el botón azul **'MENÚ'** arriba a la izquierda para iniciar sesión.")

# =======================================================
# === 1. GALERÍA ===
# =======================================================
st.write("#### 1. 📸 Galería")
uploaded_files = []

if es_pro or MODO_LANZAMIENTO:
    if creditos_disponibles <= 0:
        st.error("⛔ **Sin créditos.** Recarga tu plan para usar la IA.")
        st.stop()
    
    uploaded_files = st.file_uploader("Subir fotos", type=["jpg", "png", "jpeg"], accept_multiple_files=True, key=f"uploader_{st.session_state['uploader_key']}")
    
    if uploaded_files:
        if len(uploaded_files) > cupo_fotos:
            st.error(f"⛔ **¡Demasiadas fotos!** Tu plan {plan_actual} solo permite {cupo_fotos} imágenes.")
            st.stop()
        
        st.success(f"✅ {len(uploaded_files)} fotos cargadas correctamente.")
        
        with st.expander("👁️ Ver fotos cargadas", expanded=False):
            cols = st.columns(4)
            for i, f in enumerate(uploaded_files):
                with cols[i%4]: st.image(Image.open(f), use_container_width=True)
else:
    st.info("🔒 **La carga de fotos y Visión IA es exclusiva para Miembros.**")

st.divider()

# =======================================================
# === 2. DATOS (FORMULARIO ESTÁTICO) ===
# =======================================================
st.write("#### 2. 📝 Datos de la Propiedad")

with st.form("formulario_propiedad"):
    c1, c2 = st.columns([3, 1])

    with c1:
        oper = st.radio("Operación", ["Venta", "Alquiler"], horizontal=True)
        tipo = st.selectbox("Tipo", ["Casa", "Departamento", "Terreno", "Local", "Duplex"])
        
        opciones_estrategia = [
            "⚖️ Equilibrado (Balanceado)",
            "🔥 Urgencia (Oportunidad Flash)",
            "🔑 Primera Vivienda (Sueño Familiar)",
            "💎 Lujo & Exclusividad (High-Ticket)",
            "💰 Inversión & Rentabilidad (ROI)",
            "🌿 Vida Natural & Relax (Green Living)",
            "🏢 Comercial & Corporativo",
            "🌍 Airbnb/Alquiler Temporal",
            "💑 Recién Casados (Inicio Ideal)",       
            "🔒 Barrio Cerrado/Condominio"             
        ]

        if es_pro or MODO_LANZAMIENTO:
            enfoque = st.selectbox("🎯 Estrategia de Venta", opciones_estrategia)
        else:
            enfoque = st.selectbox("🎯 Estrategia de Venta", ["🔒 Estándar (Solo PRO)"], disabled=True)
            enfoque = "Venta Estándar"

        if (es_pro and plan_actual in ["ESTÁNDAR", "AGENCIA"]) or MODO_LANZAMIENTO:
            tono = st.selectbox("🗣️ Tono de Voz", ["Amable y Cercano", "Profesional y Serio", "Persuasivo y Energético", "Sofisticado y Elegante", "Urgente (Oportunidad)"])
        else:
            tono = st.selectbox("🗣️ Tono de Voz", ["Neutro y Descriptivo"], disabled=True)
            tono = "Neutro y Descriptivo"

        ubicacion = st.text_input("Ubicación", key="input_ubicacion")
        
        st.write("💰 **Detalles de Precio:**")
        col_p1, col_p2, col_p3 = st.columns([2, 4, 3])
        moneda = col_p1.selectbox("Divisa", ["Gs.", "$us"])
        
        # VALIDACIÓN: number_input (Imposible letras)
        precio_val = col_p2.number_input("Monto (Sin puntos)", min_value=0, step=100000, format="%d")
        
        # SELECTOR DE PERIODO (VISIBLE SI ES ALQUILER)
        periodo_texto = ""
        if oper == "Alquiler":
            periodo = col_p3.selectbox("Periodo", ["Mensual", "Diario", "Semanal", "Anual"])
            periodo_texto = f"({periodo})"
        else:
            col_p3.empty() 
            
        if es_pro or MODO_LANZAMIENTO:
            st.write("📱 **WhatsApp:**")
            wc1, wc2 = st.columns([3, 7])
            # Selector de País
            pais_code = wc1.selectbox("País", ["🇵🇾 +595", "🇦🇷 +54", "🇧🇷 +55", "🇺🇸 +1", "🇪🇸 +34"])
            
            # VALIDACIÓN: number_input (Imposible letras en el número)
            # value=None permite que empiece vacío
            whatsapp_num = wc2.number_input("N° Celular (Sin 0 inicial)", min_value=0, step=1, format="%d", value=None, placeholder="Ej: 961123456")
            
            # Construcción del número completo para la IA
            code_val = pais_code.split(" ")[1] # +595
            if whatsapp_num:
                whatsapp_full = f"{code_val}{int(whatsapp_num)}"
            else:
                whatsapp_full = ""
        else:
            whatsapp_full = ""
            st.text_input("WhatsApp", placeholder="🔒 Solo Miembros PRO", disabled=True)

    with c2:
        habs = st.number_input("Habitaciones", 1)
        banos = st.number_input("Baños", 1)
        st.write("**Servicios:**")
        gar = st.checkbox("Garage")
        qui = st.checkbox("Quincho")
        pis = st.checkbox("Piscina")
        aa = st.checkbox("Aire Acond.")
        vent = st.checkbox("Ventilador")
        wifi = st.checkbox("Wifi")
        tv = st.checkbox("TV Cable")
        agua = st.checkbox("Agua")
        luz = st.checkbox("Luz")

    # BLOQUEO BOTÓN
    deshabilitar_boton = False
    if (es_pro or MODO_LANZAMIENTO) and not uploaded_files:
        deshabilitar_boton = True
        st.warning("⚠️ **El botón se activará cuando subas fotos.**")
    
    submitted = st.form_submit_button("✨ Generar Redacción Estratégica", type="primary", disabled=deshabilitar_boton)

# =======================================================
# === GENERACIÓN ===
# =======================================================
if submitted:
    if not ubicacion or precio_val == 0:
        st.warning("⚠️ Completa Ubicación y Precio (mayor a 0).")
        st.stop()
        
    permitido = False
    if es_pro and creditos_disponibles > 0: permitido = True
    elif not es_pro and st.session_state['guest_credits'] > 0: permitido = True
    else:
        st.error("⛔ Sin créditos suficientes.")
        st.stop()

    if permitido:
        # === STATUS CENTRADO (MODAL) ===
        estado_ia = st.status("⏳ Iniciando...", expanded=True)
        
        try:
            # Formatear precio
            precio_fmt = format_price_display(precio_val)
            texto_precio_final = f"{precio_fmt} {moneda} {periodo_texto}"

            # 1. VISIÓN
            estado_ia.write("👁️ **La IA está escaneando tus fotos...**")
            
            # 2. GEO
            estado_ia.write("🌍 **Detectando datos de la zona (Barrio, Ciudad)...**")
            time.sleep(1) 
            
            # 3. REDACCIÓN
            estado_ia.write("✍️ **Redactando estrategia con Neuroventas...**")

            # PROMPT
            instrucciones_estrategia = {
                "⚖️ Equilibrado (Balanceado)": "Destaca características y beneficios.",
                "🔥 Urgencia (Oportunidad Flash)": "Usa gatillos de escasez.",
                "🔑 Primera Vivienda (Sueño Familiar)": "Enfócate en seguridad y futuro.",
                "💎 Lujo & Exclusividad (High-Ticket)": "Usa palabras de poder y estatus.",
                "💰 Inversión & Rentabilidad (ROI)": "Habla de números y retorno.",
                "🌿 Vida Natural & Relax (Green Living)": "Vende paz y aire puro.",
                "🏢 Comercial & Corporativo": "Prioriza ubicación estratégica.",
                "🌍 Airbnb/Alquiler Temporal": "Destaca amenities y turismo.",
                "💑 Recién Casados (Inicio Ideal)": "Enfócate en intimidad y comienzo.",
                "🔒 Barrio Cerrado/Condominio (Seguridad)": "Vende tranquilidad total."
            }
            directriz = instrucciones_estrategia.get(enfoque, "Descripción estándar.")

            base_prompt = f"""Eres un Copywriter Inmobiliario de Élite.
            DATOS TÉCNICOS:
            - {oper} en {ubicacion}.
            - Precio: {texto_precio_final}.
            - {habs} Habitaciones, {banos} Baños.
            - Extras: Garage={gar}, Quincho={qui}, Piscina={pis}, AA={aa}, Ventilador={vent}, Wifi={wifi}, TV={tv}, Agua={agua}, Luz={luz}."""
            
            prompt_avanzado = f"""
            TUS INSTRUCCIONES MAESTRAS (OBLIGATORIO):
            
            1. 👁️ ANÁLISIS VISUAL DE ESTRUCTURA:
               - Mira las fotos y DETECTA: ¿Es Mansión, Casa, Chalet, Departamento, Monoambiente, Terreno o Salón Comercial?
               - Usa el término CORRECTO en la descripción.
               - Describe materiales visibles (suelos, luz, acabados).

            2. 🌍 INTELIGENCIA GEOGRÁFICA (CRÍTICO):
               - Analiza la ubicación: "{ubicacion}".
               - BUSCA EN TU CONOCIMIENTO: ¿Qué caracteriza a esta zona/ciudad/barrio? (Ej: "San Bernardino" = Lago Ypacaraí, Verano; "Villa Morra" = Centro Financiero).
               - INTEGRA ESOS DATOS: "Ubicado en el corazón de [Zona], conocida por [Dato de valor]". Vende el entorno.

            3. 🎯 ESTRATEGIA DE VENTA:
               - Enfoque: "{enfoque}" ({directriz}).
               - Tono: {tono}.
            
            OUTPUT (Genera 3 opciones):
            Opción 1: Storytelling Emotivo.
            Opción 2: Venta Directa (Datos duros).
            Opción 3: Formato Viral (Estructura de Instagram/TikTok).
            
            REGLAS:
            - Usa Markdown (**negritas**).
            - Link WhatsApp: https://wa.me/{whatsapp_full.replace("+","")}
            - Incluye 10 hashtags relevantes.
            - PRECIO: Muestra siempre "{texto_precio_final}".
            
            {base_prompt}
            """

            content = [{"type": "text", "text": prompt_avanzado}]
            
            if (es_pro or MODO_LANZAMIENTO) and uploaded_files and len(uploaded_files) <= cupo_fotos:
                for f in uploaded_files:
                    f.seek(0)
                    content.append({
                        "type": "image_url", 
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{encode_image(Image.open(f))}",
                            "detail": "low"
                        }
                    })

            res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": content}], temperature=0.8) 
            generated_text = res.choices[0].message.content

            cleaned_text = generated_text.replace("###", "🔹").replace("##", "🏘️").replace("# ", "🚀 ")
            
            # --- LOGICA VIDEO ---
            frases_video = []
            if puede_video:
                try:
                    lines = cleaned_text.split('\n')
                    for l in lines:
                        l = l.strip().replace("*", "").replace("#", "").replace("🔹", "").replace("🚀", "")
                        if 10 < len(l) < 40: frases_video.append(l)
                    if len(frases_video) < 3:
                        frases_video = ["Propiedad Destacada", f"Ubicación: {ubicacion}", "Contáctanos"]
                    st.session_state['video_frases'] = frases_video[:6]
                except:
                    st.session_state['video_frases'] = ["AppyProp IA", "Oportunidad", "Contactar"]

            if es_pro:
                exito = descontar_credito(user['codigo'])
                if exito: st.session_state['usuario_activo']['limite'] = creditos_disponibles - 1
            else:
                st.session_state['guest_credits'] = 0
                st.session_state['guest_last_use'] = datetime.now()

            st.session_state['generated_result'] = cleaned_text
            estado_ia.update(label="✅ ¡Terminado!", state="complete", expanded=False)
            time.sleep(1) 
            estado_ia.empty() 
            
        except Exception as e:
            st.error(f"Error: {e}")
            estado_ia.update(label="❌ Error", state="error")

if 'generated_result' in st.session_state:
    st.markdown('<div class="output-box">', unsafe_allow_html=True)
    st.subheader("🎉 Estrategia Generada:")
    st.markdown(st.session_state['generated_result'])
    
    # --- FOOTER DE ACCIONES REDES SOCIALES ---
    st.markdown("---")
    st.write("### 🚀 Publicar Ahora:")
    
    c_copy, c_wa = st.columns(2)
    with c_copy:
        st.code(st.session_state['generated_result'], language=None)
        st.caption("👆 Toca la esquina para copiar todo")
    
    with c_wa:
        # Codificar texto para URL de WhatsApp
        msg_url = urllib.parse.quote(st.session_state['generated_result'])
        st.markdown(f'''<a href="https://wa.me/?text={msg_url}" target="_blank" class="social-btn btn-wp">📲 Enviar a WhatsApp</a>''', unsafe_allow_html=True)
        st.markdown(f'''<a href="https://instagram.com" target="_blank" class="social-btn btn-ig">📸 Abrir Instagram</a>''', unsafe_allow_html=True)
        st.markdown(f'''<a href="https://facebook.com" target="_blank" class="social-btn btn-fb">📘 Abrir Facebook</a>''', unsafe_allow_html=True)
        st.markdown(f'''<a href="https://tiktok.com" target="_blank" class="social-btn btn-tk">🎵 Abrir TikTok</a>''', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # --- ZONA VIDEO (SI APLICA) ---
    if puede_video and uploaded_files:
        st.markdown("<br>", unsafe_allow_html=True)
        st.info("🎬 **Video Reel**")
        if 'video_path' not in st.session_state:
            if st.button("🎥 GENERAR VIDEO AHORA"):
                if not MOVIEPY_AVAILABLE:
                    st.error("⚠️ Error librería video.")
                else:
                    st_video = st.status("🎞️ Renderizando video...", expanded=True)
                    try:
                        frases = st.session_state.get('video_frases', ["AppyProp IA"])
                        path_video = crear_reel_vertical(uploaded_files, frases, st_video)
                        if path_video:
                            st.session_state['video_path'] = path_video
                            st_video.update(label="✅ Video Listo", state="complete", expanded=False)
                            time.sleep(1)
                            st_video.empty()
                        else:
                            st.warning("⚠️ Error al generar video.")
                    except Exception as e:
                        st.error(f"Error video: {e}")
        
        if 'video_path' in st.session_state:
            st.video(st.session_state['video_path'])
            with open(st.session_state['video_path'], "rb") as file:
                st.download_button("⬇️ Descargar Video", file, "reel_appyprop.mp4", "video/mp4", type="primary")

    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("🔄 Nueva Propiedad (Limpiar)", type="secondary"):
        limpiar_formulario()

# =======================================================
# === ⚖️ AVISO LEGAL ===
# =======================================================
st.markdown("<br><br>", unsafe_allow_html=True)
with st.expander("⚖️ Aviso Legal y Privacidad (Importante)"):
    st.markdown("""
    <div class="legal-text">
    <b>1. Protección de Datos y Privacidad:</b><br>
    AppyProp IA es una herramienta de procesamiento en tiempo real. Queremos informarle que:
    <ul>
        <li><b>Eliminación Automática:</b> Todas las fotos, números de teléfono y datos ingresados se eliminan automáticamente de la memoria del sistema al cerrar o recargar la página.</li>
        <li><b>Sin Base de Datos de Respaldo:</b> No guardamos copias de seguridad de sus fotos o descripciones generadas.</li>
        <li><b>Responsabilidad:</b> Guarde sus textos generados antes de salir, ya que no podrán recuperarse.</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
