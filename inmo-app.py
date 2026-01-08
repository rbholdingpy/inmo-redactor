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

    /* --- NUCLEAR: ELIMINAR EFECTOS DE CARGA --- */
    .stApp, [data-testid="stAppViewContainer"] {
        opacity: 1 !important; filter: none !important; transition: none !important; will-change: auto !important;
    }
    [data-testid="stStatusWidget"] { display: none !important; }
    [data-testid="InputInstructions"] { display: none !important; }
    
    /* ESTILOS VIDEO REEL */
    .video-container {
        background-color: #000; border-radius: 20px; padding: 10px; 
        box-shadow: 0 10px 25px rgba(0,0,0,0.2); max-width: 350px; margin: 0 auto; 
    }
    .agency-badge { background-color: #F59E0B; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.7em; font-weight: bold; vertical-align: middle; }

    /* UPLOADER ESPAÑOL */
    [data-testid='stFileUploaderDropzoneInstructions'] > div:first-child { display: none; }
    [data-testid='stFileUploaderDropzoneInstructions']::before {
        content: "Arrastra tus fotos aquí"; visibility: visible; display: block; text-align: center; font-weight: bold;
    }
    [data-testid='stFileUploaderDropzoneInstructions']::after {
        content: "Se optimizarán automáticamente • JPG, PNG"; visibility: visible; display: block; font-size: 0.8em; color: #64748B; text-align: center;
    }
    [data-testid='stFileUploader'] button::after { content: "📂 Explorar"; color: #333; position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%); font-weight: bold; font-size: 14px; }
    [data-testid='stFileUploader'] button { color: transparent !important; position: relative; }

    /* BOTÓN FLOTANTE MENÚ */
    [data-testid="stSidebarCollapsedControl"] {
        background-color: #2563EB !important; color: white !important; border-radius: 8px !important; padding: 5px !important;
    }
    [data-testid="stSidebarCollapsedControl"] svg { fill: white !important; color: white !important; }

    /* TARJETAS PLANES */
    .plan-basic, .plan-standard, .plan-agency { text-align: left !important; padding: 20px; border-radius: 12px; margin-bottom: 10px; height: 100%; }
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

# --- FUNCIONES DE APOYO (AHORA CON COMPRESIÓN) ---
def comprimir_imagen(image_file):
    """Redimensiona y comprime la imagen para optimizar memoria."""
    try:
        img = Image.open(image_file)
        if img.mode in ("RGBA", "P"): img = img.convert("RGB")
        
        # Redimensionar a max 1080px de ancho (Suficiente para HD)
        max_width = 1080
        if img.width > max_width:
            ratio = max_width / float(img.width)
            new_height = int(float(img.height) * ratio)
            img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
        # Comprimir a JPEG calidad 85
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85, optimize=True)
        buffer.seek(0)
        return buffer
    except Exception as e:
        return image_file # Si falla, devolver original

def encode_image(image_file):
    """Codifica la imagen comprimida a base64."""
    # Usamos la imagen comprimida directamente
    return base64.b64encode(image_file.getvalue()).decode('utf-8')

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

# --- FUNCIÓN GENERADORA DE VIDEO REEL (USANDO IMÁGENES COMPRIMIDAS) ---
def crear_reel_vertical(imagenes_uploaded, textos_clave):
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
            # OPTIMIZACIÓN: Usar la imagen ya comprimida (si es posible) o comprimirla al vuelo
            # Para moviepy necesitamos guardar el archivo físico
            img_file.seek(0)
            img = Image.open(img_file).convert("RGB")
            
            # Redimensionar para video
            img = ImageOps.fit(img, (W, H), method=Image.Resampling.LANCZOS)
            
            overlay = Image.new('RGBA', (W, H), (0, 0, 0, 80))
            img.paste(overlay, (0, 0), overlay)
            draw = ImageDraw.Draw(img)
            texto_actual = textos_clave[i % len(textos_clave)] if textos_clave else "AppyProp IA"
            draw.text((W/2, H*0.8), texto_actual, font=font, fill="white", anchor="mm", align="center")
            draw.text((W/2, H*0.95), "Generado con AppyProp IA 🚀", fill="#cccccc", anchor="mm", font=font)
            
            temp_img_path = os.path.join(temp_dir, f"temp_frame_{i}.jpg")
            # Guardar con compresión para que MoviePy no sufra
            img.save(temp_img_path, quality=85)
            
            clip = ImageClip(temp_img_path).set_duration(duracion_por_foto)
            clips.append(clip)
        except Exception as e:
            print(f"Error procesando imagen {i}: {e}")
            continue

    if not clips:
        try: shutil.rmtree(temp_dir)
        except: pass
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
# === 💎 ZONA DE
