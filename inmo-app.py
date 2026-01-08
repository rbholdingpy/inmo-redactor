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

# --- ESTILOS CSS (MODO MÓVIL BLINDADO) ---
st.markdown("""
    <style>
    .main { background-color: #F8FAFC; }
    h1 { color: #0F172A; font-family: 'Helvetica Neue', sans-serif; font-weight: 800; }
    
    .stButton>button {
        border-radius: 8px; border: none; padding: 12px; font-weight: bold; width: 100%; transition: all 0.2s;
    }
    .stButton>button:hover { transform: scale(1.02); }

    /* --- ESCUDO ANTI-MENSAJES MOLESTOS (NUCLEAR) --- */
    
    /* 1. Ocultar el texto "Press Enter to apply" */
    [data-testid="InputInstructions"] {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        opacity: 0 !important;
    }
    
    /* 2. Ocultar tooltips nativos que puedan estorbar */
    div[data-baseweb="tooltip"] {
        display: none !important;
    }

    /* 3. Evitar que la pantalla se ponga gris/translúcida al cargar */
    [data-testid="stAppViewContainer"] {
        will-change: auto !important;
        transition: none !important;
        opacity: 1 !important;
        filter: none !important;
    }
    
    /* 4. Limpieza visual de inputs */
    .stTextInput > div > div {
        box-shadow: none !important;
    }
    /* ---------------------------------------------------- */

    /* ESTILOS VIDEO REEL */
    .video-container {
        background-color: #000; 
        border-radius: 20px; 
        padding: 10px; 
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        max-width: 350px; 
        margin: 0 auto; 
    }
    .video-box { 
        border: 2px solid #8B5CF6; 
        background-color: #F3E8FF; 
        padding: 20px; 
        border-radius: 15px; 
        text-align: center; 
        margin-top: 30px; 
    }
    .agency-badge { background-color: #F59E0B; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.7em; font-weight: bold; vertical-align: middle; }

    /* UPLOADER ESPAÑOL */
    [data-testid='stFileUploaderDropzoneInstructions'] > div:first-child { display: none; }
    [data-testid='stFileUploaderDropzoneInstructions']::before {
        content: "Arrastra y suelta tus fotos aquí"; visibility: visible;
        font-size: 1.1rem; font-weight: bold; display: block;
        text-align: center; color: #333; margin-bottom: 5px;
    }
    [data-testid='stFileUploaderDropzoneInstructions'] > small { display: none; }
    [data-testid='stFileUploaderDropzoneInstructions']::after {
        content: "Límite 200MB por archivo • JPG, PNG"; visibility: visible;
        display: block; font-size: 0.8em; color: #64748B;
        text-align: center; margin-top: 5px;
    }
    [data-testid='stFileUploader'] button { color: transparent !important; position: relative; }
    [data-testid='stFileUploader'] button::after {
        content: "📂 Explorar"; color: #333; position: absolute;
        left: 50%; top: 50%; transform: translate(-50%, -50%);
        font-weight: bold; font-size: 14px;
    }

    /* BOTÓN FLOTANTE MENÚ */
    [data-testid="stSidebarCollapsedControl"] {
        background-color: #2563EB !important; color: white !important;
        border-radius: 8px !important; padding: 5px !important;
    }
    [data-testid="stSidebarCollapsedControl"] svg { fill: white !important; color: white !important; }

    /* TARJETAS PLANES */
    .plan-basic, .plan-standard, .plan-agency {
        text-align: left !important; padding: 20px; border-radius: 12px; margin-bottom: 10px; height: 100%;
    }
    .plan-basic { background-color: #F8FAFC; border: 2px solid #475569; color: #334155; }
    .plan-standard { background-color: white; border: 2px solid #3B82F6; color: #0F172A; box-shadow: 0 4px 6px rgba(59, 130, 246, 0.1); }
    .plan-agency { background: linear-gradient(135deg, #FFFBEB 0%, #FFFFFF 100%); border: 2px solid #F59E0B; color: #0F172A; box-shadow: 0 10px 25px rgba(245, 158, 11, 0.25); transform: scale(1.03); position: relative; z-index: 10; }

    .feature-list { list-style-type: none; padding: 0; margin: 15px 0; }
    .feature-list li { margin-bottom: 8px; font-size: 0.85em; display: flex; align-items: center; gap: 8px; line-height: 1.3; }
    .check-icon { color: #16a34a; font-weight: bold; min-width: 20px; font-size: 1.1em; } 
    .cross-icon { color: #dc2626; opacity: 0.6; min-width: 20px; font-size: 1.1em; }
    .feature-locked { opacity: 0.5; text-decoration: line-through; color: #64748B; }
    .plan-title-center { text-align: center; margin-bottom: 5px; font-weight: 800; font-size: 1.3em; }
    .price-tag { font-size: 1.4em; font-weight: 800; margin: 10px 0; text-align: center; }
    .agency-badge-container { text-align: center; margin-bottom: 5px; }
    
    .pro-badge { background-color: #DCFCE7; color: #166534; padding: 5px 10px; border-radius: 20px; font-weight: bold; font-size: 0.8em; }
    .launch-badge { background: linear-gradient(90deg, #F59E0B, #EF4444); color: white; padding: 5px 15px; border-radius: 20px; font-weight: bold; font-size: 0.9em; box-shadow: 0 2px 5px rgba(0,0,0,0.2); animation: pulse 2s infinite; }
    .free-badge { background-color: #F1F5F9; color: #64748B; padding: 5px 10px; border-radius: 20px; font-weight: bold; font-size: 0.8em; }
    @keyframes pulse { 0% { opacity: 1; } 50% { opacity: 0.8; } 100% { opacity: 1; } }
    
    .photo-limit-box { background-color: #E0F2FE; border: 2px solid #0284C7; color: #0369A1; padding: 15px; border-radius: 10px; text-align: center; font-size: 1.1em; font-weight: bold; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .output-box { background-color: white; padding: 25px; border-radius: 10px; border: 1px solid #cbd5e1; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .legal-text { font-size: 0.85em; color: #64748B; text-align: justify; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIONES DE APOYO ---
def encode_image(image):
    buffered = io.BytesIO()
    if image.mode in ("RGBA", "P"): image = image.convert("RGB")
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

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
def crear_reel_vertical(imagenes_uploaded, textos_clave):
    """Convierte imágenes en un video vertical 9:16 concatenando clips."""
    if not MOVIEPY_AVAILABLE or not imagenes_uploaded:
        return None
    
    num_fotos = len(imagenes_uploaded)
    duracion_por_foto = 20.0 / num_fotos
    if duracion_por_foto < 2.0: duracion_por_foto = 2.0 

    clips = []
    W, H = 720, 1280
    font = ImageFont.load_default()
    temp_dir = tempfile.mkdtemp()

    for i, img_file in enumerate(imagenes_uploaded):
        try:
            img_file.seek(0)
            img = Image.open(img_file).convert("RGB")
            img = ImageOps.fit(img, (W, H), method=Image.Resampling.LANCZOS)
            overlay = Image.new('RGBA', (W, H), (0, 0, 0, 100))
            img.paste(overlay, (0, 0), overlay)
            draw = ImageDraw.Draw(img)
            texto_actual = textos_clave[i % len(textos_clave)] if textos_clave else "AppyProp IA"
            draw.text((W/2, H*0.8), texto_actual, font=font, fill="white", anchor="mm", align="center")
            draw.text((W/2, H*0.95), "Generado con AppyProp IA 🚀", fill="#cccccc", anchor="mm", font=font)
            temp_img_path = os.path.join(temp_dir, f"temp_frame_{i}.jpg")
            img.save(temp_img_path)
            clip = ImageClip(temp_img_path).set_duration(duracion_por_foto)
            clips.append(clip)
        except Exception as e:
            print(f"Error procesando imagen {i}: {e}")
            continue

    if not clips:
        try: 
            shutil.rmtree(temp_dir)
        except: 
            pass
        return None

    final_clip = concatenate_videoclips(clips, method="compose")
    if final_clip.duration > 20.0:
         final_clip = final_clip.subclip(0, 20.0)

    tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    output_path = tfile.name
    tfile.close()

    final_clip.write_videofile(
        output_path, codec="libx264", audio=False, fps=24, preset='ultrafast',
        ffmpeg_params=['-pix_fmt', 'yuv420p'], threads=1, logger=None
    )
    
    try: 
        shutil.rmtree(temp_dir)
    except: 
        pass
        
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
        # LOGICA MODO LANZAMIENTO
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
# === 💎 ZONA DE VENTAS (REDISEÑADA CON LISTAS) ===
# =======================================================
if st.session_state.ver_planes:
    st.title("💎 Escala tus Ventas")
    
    plan_usuario_actual = ""
    if st.session_state['usuario_activo']:
        plan_usuario_actual = str(st.session_state['usuario_activo'].get('plan', '')).lower()

    if st.session_state.plan_seleccionado is None:
        st.write("Elige la potencia que necesita tu negocio.")
        c1, c2, c3 = st.columns(3)
        
        # --- PLAN BÁSICO ---
        with c1:
            st.markdown("""
            <div class="plan-basic">
                <h3 class="plan-title-center">🥉 Básico</h3>
                <div class="price-tag">20.000 Gs</div>
                <ul class="feature-list">
                    <li><span class="check-icon">✅</span> 10 Créditos</li>
                    <li><span class="check-icon">✅</span> Operación</li>
                    <li><span class="check-icon">✅</span> Tipo de Propiedad</li>
                    <li><span class="check-icon">✅</span> Ubicación</li>
                    <li><span class="check-icon">✅</span> Detalles de Precio</li>
                    <li><span class="check-icon">✅</span> Servicios Extras</li>
                    <li><span class="check-icon">✅</span> Max 3 Fotos (Visión IA)</li>
                    <li class="feature-locked"><span class="cross-icon">❌</span> Estrategia de Venta</li>
                    <li class="feature-locked"><span class="cross-icon">❌</span> Tono de Voz</li>
                    <li class="feature-locked"><span class="cross-icon">❌</span> Link WhatsApp</li>
                    <li class="feature-locked"><span class="cross-icon">❌</span> Generador de Video</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            if 'basico' in plan_usuario_actual or 'básico' in plan_usuario_actual:
                st.button("✅ Tu Plan Actual", disabled=True, key="btn_basico_dis")
            else:
                st.button("Elegir Básico", key="btn_basico", on_click=seleccionar_plan, args=("Básico",))

        # --- PLAN ESTÁNDAR ---
        with c2:
            st.markdown("""
            <div class="plan-standard">
                <h3 class="plan-title-center">🥈 Estándar</h3>
                <div class="price-tag" style="color:#2563EB;">35.000 Gs</div>
                <ul class="feature-list">
                    <li><span class="check-icon">✅</span> <b>20 Créditos</b></li>
                    <li><span class="check-icon">✅</span> Operación</li>
                    <li><span class="check-icon">✅</span> Tipo de Propiedad</li>
                    <li><span class="check-icon">✅</span> <b>Estrategia de Venta</b></li>
                    <li><span class="check-icon">✅</span> <b>Tono de Voz</b></li>
                    <li><span class="check-icon">✅</span> Ubicación</li>
                    <li><span class="check-icon">✅</span> Detalles de Precio</li>
                    <li><span class="check-icon">✅</span> <b>Link WhatsApp</b></li>
                    <li><span class="check-icon">✅</span> Servicios Extras</li>
                    <li><span class="check-icon">✅</span> <b>Max 6 Fotos</b> (Visión IA)</li>
                    <li class="feature-locked"><span class="cross-icon">❌</span> Generador de Video</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            if 'estándar' in plan_usuario_actual or 'standar' in plan_usuario_actual:
                st.button("✅ Tu Plan Actual", disabled=True, key="btn_estandar_dis")
            else:
                st.button("Elegir Estándar", key="btn_estandar", type="primary", on_click=seleccionar_plan, args=("Estándar",))

        # --- PLAN AGENCIA ---
        with c3:
            st.markdown("""
            <div class="plan-agency">
                <div class="agency-badge-container"><span class="agency-badge">🔥 MEJOR OPCIÓN</span></div>
                <h3 class="plan-title-center" style="color:#B45309;">🥇 Agencia</h3>
                <div class="price-tag" style="color:#D97706;">80.000 Gs</div>
                <ul class="feature-list">
                    <li><span class="check-icon">✅</span> <b>80 Créditos</b></li>
                    <li><span class="check-icon">✅</span> Operación</li>
                    <li><span class="check-icon">✅</span> Tipo de Propiedad</li>
                    <li><span class="check-icon">✅</span> <b>Estrategia de Venta</b></li>
                    <li><span class="check-icon">✅</span> <b>Tono de Voz</b></li>
                    <li><span class="check-icon">✅</span> Ubicación</li>
                    <li><span class="check-icon">✅</span> Detalles de Precio</li>
                    <li><span class="check-icon">✅</span> <b>Link WhatsApp</b></li>
                    <li><span class="check-icon">✅</span> Servicios Extras</li>
                    <li><span class="check-icon">✅</span> <b>Max 10 Fotos</b> (Visión IA)</li>
                    <li><span class="check-icon">✅</span> 🎬 <b>Video 9:16 (Opcional)</b></li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            if 'agencia' in plan_usuario_actual:
                st.button("✅ Tu Plan Actual", disabled=True, key="btn_agencia_dis")
            else:
                st.button("👑 ELEGIR AGENCIA", key="btn_agencia", type="primary", on_click=seleccionar_plan, args=("Agencia",))
        
        st.divider()
        st.button("⬅️ Volver a la App", on_click=volver_a_app)

    else:
        # PANTALLA DE PAGO
        st.info(f"🚀 Excelente elección: **Plan {st.session_state.plan_seleccionado}**")
        
        if not st.session_state.pedido_registrado:
            st.write("### 📝 Paso 1: Tus Datos")
            
            def_nombre = ""
            def_email = ""
            def_tel = ""
            if st.session_state['usuario_activo']:
                u = st.session_state['usuario_activo']
                try: def_nombre = u.get('cliente', '').split(' ')[0]
                except: pass
                def_email = u.get('correo', '')
                def_tel = str(u.get('telefono', ''))

            with st.form("form_registro_pedido"):
                c_nom, c_ape = st.columns(2)
                nombre = c_nom.text_input("Nombre", value=def_nombre)
                apellido = c_ape.text_input("Apellido")
                email = st.text_input("Correo Electrónico (Para tu código de acceso)", value=def_email)
                telefono = st.text_input("Número de WhatsApp", value=def_tel)
                
                submitted = st.form_submit_button("✅ Confirmar y Ver Datos de Pago", type="primary")
                
                if submitted:
                    if nombre and apellido and email and telefono:
                        with st.spinner("Verificando datos..."):
                            status = registrar_pedido(nombre, apellido, email, telefono, st.session_state.plan_seleccionado)
                            if status == "SAME_PLAN":
                                st.error("⛔ Ya tienes este plan activo.")
                            elif status == "ERROR":
                                st.error("Error de conexión.")
                            else:
                                st.session_state.pedido_registrado = True
                                st.session_state['temp_nombre'] = f"{nombre} {apellido}"
                                st.session_state['tipo_pedido'] = "CAMBIO" if status == "UPDATED" else "NUEVO"
                                st.rerun()
                    else:
                        st.warning("⚠️ Completa todos los campos.")
            st.button("🔙 Volver atrás", on_click=cancelar_seleccion)

        else:
            tipo = st.session_state.get('tipo_pedido', 'PEDIDO')
            st.success("✅ **¡Datos recibidos!** Realiza el pago para activar.")

            st.write("### 💳 Paso 2: Realiza el Pago")
            col_bank, col_wa = st.columns(2)
            with col_bank:
                st.markdown("""
                <div style="background-color:white; padding:15px; border-radius:10px; border:1px solid #ddd; color: #333;">
                <b>Banco:</b> ITAÚ <br>
                <b>Titular:</b> Ricardo Blanco <br>
                <b>Cuenta:</b> 320595209 <br>
                <b>Alias:</b> RUC 1911221-1 <br>
                <b>C.I.:</b> 1911221 <br>
                <b>RUC:</b> 1911221-1
                </div>
                """, unsafe_allow_html=True)
            with col_wa:
                nombre_cliente = st.session_state.get('temp_nombre', 'Nuevo Cliente')
                mensaje_wp = f"Hola, soy *{nombre_cliente}*. Adjunto comprobante para *Plan {st.session_state.plan_seleccionado}*."
                mensaje_wp_url = mensaje_wp.replace(" ", "%20").replace("\n", "%0A")
                link_wp = f"https://wa.me/{ADMIN_WHATSAPP}?text={mensaje_wp_url}"
                
                st.markdown(f'<a href="{link_wp}" target="_blank" style="text-decoration:none;"><button style="background-color:#25D366; color:white; border:none; padding:15px; border-radius:8px; width:100%; font-weight:bold; cursor:pointer; font-size:1.1em; margin-top:10px; box-shadow: 0 4px 6px rgba(37, 211, 102, 0.3);">📲 Enviar Comprobante por WhatsApp</button></a>', unsafe_allow_html=True)
            st.divider()
            if st.button("🏁 Finalizar y Volver al Inicio"):
                volver_a_app()
    st.stop()

# =======================================================
# === APP PRINCIPAL ===
# =======================================================
c_title, c_badge = st.columns([2, 1])
# --- TITULO PRINCIPAL CENTRADO ---
st.markdown("<h1 style='text-align: center; margin-bottom: 0;'>AppyProp IA 🚀</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #1E293B; font-weight: 600; margin-top: 0; font-size: 1.2rem;'>Experto en Neuroventas Inmobiliarias</h3>", unsafe_allow_html=True)

# --- SECCIÓN: ¿QUÉ ES APPYPROP IA? ---
with st.expander("ℹ️ ¿Qué es AppyProp IA? (Click para desplegar)"):
    st.markdown("""
    ### 🏠 Tu Copiloto Experto en Neuroventas Inmobiliarias
    **AppyProp IA** no es solo una herramienta; es la evolución de cómo se venden propiedades. Una plataforma inteligente que combina **Visión Artificial** con **Psicología de Ventas**.

    ---
    #### 💎 ¿En qué te beneficia?
    1.  **👁️ Ojos que Ven, Cerebro que Vende:** La IA "mira" tus fotos, detecta acabados e iluminación, e integra esos detalles para enamorar al cliente.
    2.  **⚡ Velocidad Supersónica:** De 30 minutos a **10 segundos**. Genera descripciones, guiones y posts virales en un clic.
    3.  **🎯 Estrategia Total:** No es solo texto. Recibes **Storytelling** (emoción), **Venta Directa** (datos) y **Formato Viral** (redes).

    ---
    #### 🚀 ¿Por qué utilizarlo?
    * **Adiós al bloqueo creativo:** Nunca más una pantalla en blanco.
    * **Ahorro:** Tu propia agencia de marketing de bolsillo.
    * **Profesionalismo:** Textos persuasivos y sin errores.

    ---
    #### 🤖 El Factor Diferencial
    **AppyProp IA es un hito tecnológico: Una aplicación 100% creada con Inteligencia Artificial.** Innovación pura, eficiencia y evolución constante para el mercado inmobiliario.
    """)

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
    elif 'básico' in plan_str or 'basico' in plan_str:
        cupo_fotos = 3
        plan_actual = "BÁSICO"
    else:
        cupo_fotos = 3
        plan_actual = "MIEMBRO"

    creditos_disponibles = int(user.get('limite', 0) if user.get('limite') != "" else 0)
    # BADGE CENTRADO
    st.markdown(f'<div style="text-align:center; margin-top: 10px;"><span class="pro-badge">PLAN {plan_actual}</span></div>', unsafe_allow_html=True)
else:
    # LÓGICA DE INVITADO / MODO LANZAMIENTO
    es_pro = False
    creditos_disponibles = st.session_state['guest_credits']
    if MODO_LANZAMIENTO:
        plan_actual = "INVITADO VIP"
        cupo_fotos = 10
        puede_video = True # Invitados tienen video
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

# Permitir carga si es PRO o está en MODO LANZAMIENTO
if es_pro or MODO_LANZAMIENTO:
    if creditos_disponibles <= 0:
        st.error("⛔ **Sin créditos.** Recarga tu plan para usar la IA.")
        st.stop()
    
    st.markdown(f"""<div class="photo-limit-box">📸 Potencia {plan_actual}: Puedes subir hasta <span style="font-size:1.3em; color:#0284C7;">{cupo_fotos} FOTOS</span> por análisis.</div>""", unsafe_allow_html=True)
    uploaded_files = st.file_uploader("Subir fotos", type=["jpg", "png", "jpeg"], accept_multiple_files=True, key=f"uploader_{st.session_state['uploader_key']}")
    if uploaded_files:
        if len(uploaded_files) > cupo_fotos:
            st.error(f"⛔ **¡Demasiadas fotos!** Tu plan {plan_actual} solo permite {cupo_fotos} imágenes.")
            st.stop()
        with st.expander("👁️ Vista Previa de Imágenes Seleccionadas", expanded=True):
            cols = st.columns(4)
            for i, f in enumerate(uploaded_files):
                with cols[i%4]: st.image(Image.open(f), use_container_width=True)
else:
    st.info("🔒 **La carga de fotos y Visión IA es exclusiva para Miembros.**")
    st.markdown('<div style="opacity:0.6; pointer-events:none; border: 2px dashed #ccc; padding: 20px; text-align: center; border-radius: 10px;">📂 Subir fotos (Bloqueado)</div>', unsafe_allow_html=True)

st.divider()

# =======================================================
# === 2. DATOS ===
# =======================================================
st.write("#### 2. 📝 Datos de la Propiedad")
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
        "🛠️ Potencial de Reforma (Flipping)",
        "🌿 Vida Natural & Relax (Green Living)",
        "🏢 Comercial & Corporativo",
        "🌍 Airbnb/Alquiler Temporal",
        "💑 Recién Casados (Inicio Ideal)",       
        "🔒 Barrio Cerrado/Condominio (Seguridad)", 
        "🎒 Estudiantes/Universitario",           
        "💼 Ejecutivo/Nómada Digital"             
    ]

    # Desbloquear estrategias si es PRO o MODO LANZAMIENTO
    if es_pro or MODO_LANZAMIENTO:
        enfoque = st.selectbox("🎯 Estrategia de Venta", opciones_estrategia)
    else:
        enfoque = st.selectbox("🎯 Estrategia de Venta", ["🔒 Estándar (Solo PRO)"], disabled=True)
        enfoque = "Venta Estándar"

    # Desbloquear tono si es Plan Alto o MODO LANZAMIENTO
    if (es_pro and plan_actual in ["ESTÁNDAR", "AGENCIA"]) or MODO_LANZAMIENTO:
        tono = st.selectbox("🗣️ Tono de Voz", ["Amable y Cercano", "Profesional y Serio", "Persuasivo y Energético", "Sofisticado y Elegante", "Urgente (Oportunidad)"])
    else:
        msg_bloqueo = "🔒 Neutro (Requiere Plan Estándar)" if es_pro else "🔒 Neutro (Solo PRO Estándar)"
        tono = st.selectbox("🗣️ Tono de Voz", [msg_bloqueo], disabled=True)
        tono = "Neutro y Descriptivo"

    ubicacion = st.text_input("Ubicación", key="input_ubicacion")
    
    st.write("💰 **Detalles de Precio:**")
    if oper == "Alquiler":
        col_p1, col_p2, col_p3 = st.columns([15, 35, 50])
        with col_p1:
            moneda = st.selectbox("Divisa", ["Gs.", "$us"], label_visibility="collapsed", key="input_moneda")
        with col_p2:
            precio_val = st.text_input("Monto", placeholder="Monto", label_visibility="collapsed", key="input_monto")
        with col_p3:
            frec = st.selectbox("Frecuencia", ["Mensual", "Diario", "Semanal", "Semestral", "Anual"], label_visibility="collapsed")
        texto_precio = f"{precio_val} {moneda} ({frec})"
    else:
        col_p1, col_p2 = st.columns([20, 80])
        with col_p1:
            moneda = st.selectbox("Divisa", ["Gs.", "$us"], label_visibility="collapsed", key="input_moneda")
        with col_p2:
            precio_val = st.text_input("Monto", placeholder="Monto Total", label_visibility="collapsed", key="input_monto")
        texto_precio = f"{precio_val} {moneda}"
        
    # Desbloquear WhatsApp si es PRO o MODO LANZAMIENTO
    if es_pro or MODO_LANZAMIENTO:
        whatsapp = st.text_input("WhatsApp (Solo números)", key="input_whatsapp")
    else:
        whatsapp = st.text_input("WhatsApp", placeholder="🔒 Solo Miembros PRO", disabled=True)

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

st.divider()

if es_pro or MODO_LANZAMIENTO:
    cant_fotos = len(uploaded_files) if uploaded_files else 0
    st.info(f"🧠 **Neuro-Vision Activa:** Analizando {cant_fotos} fotos con potencia {plan_actual}... (Costo: 1 crédito)")
else:
    if st.session_state['guest_credits'] > 0:
        st.success(f"🎁 **Modo Invitado:** Tienes {st.session_state['guest_credits']} generación gratis hoy.")
    else:
        st.warning("⏳ **Has usado tu crédito diario.** Vuelve mañana o hazte PRO.")

# =======================================================
# === GENERACIÓN ===
# =======================================================
# CAMBIO DE NOMBRE DEL BOTÓN AQUÍ 👇
if st.button("✨ Generar Redacción Estratégica", type="primary"):
    if not ubicacion or not precio_val:
        st.warning("⚠️ Completa Ubicación y Precio.")
        st.stop()
        
    permitido = False
    if es_pro and creditos_disponibles > 0: permitido = True
    elif not es_pro and st.session_state['guest_credits'] > 0: permitido = True
    else:
        st.error("⛔ Sin créditos suficientes. Hazte Miembro para continuar.")
        st.stop()

    if permitido:
        with st.spinner('🧠 Redactando estrategia...'):
            try:
                # Prompt con Geo-Inteligencia Paraguaya
                instrucciones_estrategia = {
                    "⚖️ Equilibrado (Balanceado)": "Destaca características y beneficios por igual. Tono seguro y confiable.",
                    "🔥 Urgencia (Oportunidad Flash)": "Usa gatillos de escasez (Tiempo limitado, precio rebajado). Frases cortas.",
                    "🔑 Primera Vivienda (Sueño Familiar)": "Enfócate en seguridad, futuro, espacio para niños. Tono emotivo y cálido.",
                    "💎 Lujo & Exclusividad (High-Ticket)": "Usa palabras de poder (Exquisito, Premium). Vende estatus y privacidad.",
                    "💰 Inversión & Rentabilidad (ROI)": "Habla de números: Plusvalía, retorno de inversión. Tono racional y de negocios.",
                    "🛠️ Potencial de Reforma (Flipping)": "Vende la visión futura. 'Lienzo en blanco', 'Oportunidad'.",
                    "🌿 Vida Natural & Relax (Green Living)": "Vende paz, desconexión, aire puro. Tono zen y relajado.",
                    "🏢 Comercial & Corporativo": "Prioriza ubicación estratégica, tráfico de personas y éxito comercial.",
                    "🌍 Airbnb/Alquiler Temporal": "Destaca amenities, wifi, cercanía a turismo y comodidad total.",
                    "💑 Recién Casados (Inicio Ideal)": "Enfócate en 'el comienzo de una historia', intimidad, espacio práctico y acogedor.",
                    "🔒 Barrio Cerrado/Condominio (Seguridad)": "Vende tranquilidad total, vigilancia 24/7, amenities compartidos y vida social segura.",
                    "🎒 Estudiantes/Universitario": "Destaca cercanía a universidades, transporte público, bajo mantenimiento y wifi.",
                    "💼 Ejecutivo/Nómada Digital": "Enfócate en conectividad, escritorio/home office, cercanía al centro financiero y estilo moderno."
                }
                
                directriz_seleccionada = instrucciones_estrategia.get(enfoque, "Descripción estándar atractiva.")

                base_prompt = f"""Eres un Copywriter Inmobiliario de Élite.
                DATOS TÉCNICOS:
                - {oper} {tipo} en {ubicacion}.
                - Precio: {texto_precio}.
                - {habs} Habitaciones, {banos} Baños.
                - Extras: Garage={gar}, Quincho={qui}, Piscina={pis}, AA={aa}, Ventilador={vent}, Wifi={wifi}, TV={tv}, Agua={agua}, Luz={luz}."""
                
                prompt_avanzado = f"""
                TUS INSTRUCCIONES MAESTRAS:
                PASO 1: ANÁLISIS VISUAL (OBLIGATORIO)
                Si recibes fotos, ACTÚA COMO UN INSPECTOR. No inventes.
                - Mira el suelo: ¿Es madera, porcelanato, cerámica? Menciónalo.
                - Mira la luz: ¿Entra luz natural? ¿Es cálida?
                - Mira la cocina/baños: Describe los materiales (granito, moderno, clásico).
                - ¡SI NO MENCIONAS DETALLES VISUALES ESPECÍFICOS DE LAS FOTOS, EL TRABAJO ESTÁ MAL HECHO!
                
                PASO EXTRA: INTELIGENCIA GEOGRÁFICA (PARAGUAY)
                Analiza la ubicación ingresada: "{ubicacion}".
                - Si es un barrio/ciudad conocido de Paraguay, NO solo lo menciones.
                - BUSCA EN TU CONOCIMIENTO: ¿Qué caracteriza a esa zona? (Ej: "La histórica ciudad de Piribebuy", "El exclusivo Barrio Carmelitas cerca del eje corporativo", "La tranquilidad de San Bernardino").
                - Menciona 1 dato de valor sobre la zona (historia, naturaleza, seguridad o conveniencia) para elevar el valor percibido.

                PASO 2: APLICAR ESTRATEGIA DE VENTA
                Tu objetivo es vender/alquilar usando esta estrategia específica: "{enfoque}".
                Instrucción de Tono y Enfoque: {directriz_seleccionada}
                
                PASO 3: REDACCIÓN (OUTPUT)
                Escribe 3 opciones distintas:
                OPCIÓN 1: Storytelling Emotivo.
                OPCIÓN 2: Venta Directa (Datos duros).
                OPCIÓN 3: Formato Viral (Instagram/TikTok).
                
                REGLAS DE FORMATO:
                - Usa Markdown (**negritas**).
                - Incluye Link a WhatsApp: https://wa.me/595{whatsapp}
                - Incluye 10 hashtags en Opción 3.
                
                TONO DE VOZ SOLICITADO: {tono}
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
                                "detail": "high"
                            }
                        })

                res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": content}], temperature=0.8) 
                generated_text = res.choices[0].message.content

                cleaned_text = generated_text.replace("###", "🔹").replace("##", "🏘️")
                cleaned_text = cleaned_text.replace("# ", "🚀 ") 
                cleaned_text = cleaned_text.replace("* ", "▪️ ").replace("- ", "▪️ ")
                
                # --- LÓGICA DE EXTRACCIÓN DE FRASES PARA VIDEO ---
                frases_video = []
                # Si tiene acceso a video (Agencia o Lanzamiento)
                if puede_video:
                    try:
                        lines = cleaned_text.split('\n')
                        for l in lines:
                            l = l.strip().replace("*", "").replace("#", "").replace("🔹", "").replace("🚀", "")
                            if 10 < len(l) < 40 and not l.startswith("http"):
                                frases_video.append(l)
                        if len(frases_video) < 3:
                            frases_video = ["Propiedad Destacada", f"Ubicación: {ubicacion}", "Contáctanos"]
                        st.session_state['video_frases'] = frases_video[:6]
                    except:
                        st.session_state['video_frases'] = ["AppyProp IA", "Oportunidad", "Contactar"]

                # --- DESCUENTO DE CRÉDITOS ---
                if es_pro:
                    exito = descontar_credito(user['codigo'])
                    if exito:
                        st.session_state['usuario_activo']['limite'] = creditos_disponibles - 1
                        st.toast("✅ Crédito PRO descontado", icon="🪙")
                else:
                    st.session_state['guest_credits'] = 0
                    st.session_state['guest_last_use'] = datetime.now()
                    st.toast("✅ Crédito gratuito usado", icon="🎁")

                st.session_state['generated_result'] = cleaned_text
            except Exception as e:
                st.error(f"Error: {e}")

if 'generated_result' in st.session_state:
    st.markdown('<div class="output-box">', unsafe_allow_html=True)
    st.subheader("🎉 Estrategia Generada:")
    st.markdown(st.session_state['generated_result'])
    st.markdown('</div>', unsafe_allow_html=True)
    
    # --- ZONA VIDEO REEL ---
    # Se muestra si el usuario tiene permiso (Agencia o Lanzamiento) Y subió fotos
    if puede_video and uploaded_files:
        st.markdown("---")
        st.subheader("🎬 Video Reel Automático")
        
        st.markdown("""
        <div style="background-color:#F3E8FF; padding:15px; border-radius:10px; margin-bottom:15px;">
        <h4 style="margin:0; color:#6B21A8;">¿Te gustaría que genere un video con tus fotos para tus redes sociales? 🎥</h4>
        <p style="margin:5px 0 0 0; font-size:0.9em;">Crea un Reel vertical automático de 20 segundos listo para TikTok o Instagram.</p>
        </div>
        """, unsafe_allow_html=True)

        if 'video_path' not in st.session_state:
            if st.button("🎥 SÍ, GENERAR VIDEO REEL"):
                if not MOVIEPY_AVAILABLE:
                    st.error("⚠️ Librería MoviePy no instalada. Revisa requirements.txt")
                else:
                    with st.spinner("🎞️ Renderizando video (aprox. 20s)..."):
                        try:
                            frases = st.session_state.get('video_frases', ["AppyProp IA"])
                            path_video = crear_reel_vertical(uploaded_files, frases)
                            if path_video:
                                st.session_state['video_path'] = path_video
                            else:
                                st.warning("⚠️ No se pudo generar el video (quizás pocas fotos).")
                        except Exception as e:
                            st.error(f"Error video: {e}")

        if 'video_path' in st.session_state:
            st.success("✅ Video Reel generado con éxito.")
            
            c_video_center = st.columns([1, 2, 1])
            with c_video_center[1]:
                st.markdown('<div class="video-container">', unsafe_allow_html=True)
                st.video(st.session_state['video_path'])
                st.markdown('</div>', unsafe_allow_html=True)
                
                with open(st.session_state['video_path'], "rb") as file:
                    st.download_button("⬇️ Descargar Video (MP4)", file, "reel_appyprop.mp4", "video/mp4", type="primary")

    st.markdown("---")
    st.subheader("¿Terminaste?")
    if st.button("🔄 Nueva Propiedad (Limpiar) ", type="secondary"):
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
