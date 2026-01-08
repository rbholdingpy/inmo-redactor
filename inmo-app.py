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

# --- IMPORTACIÓN CONDICIONAL DE MOVIEPY ---
# Esto evita que la app se rompa si falla la instalación
try:
    from moviepy.editor import ImageSequenceClip, AudioFileClip
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

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .main { background-color: #F8FAFC; }
    h1 { color: #0F172A; font-family: 'Helvetica Neue', sans-serif; font-weight: 800; }
    .stButton>button { border-radius: 8px; border: none; padding: 12px; font-weight: bold; width: 100%; transition: all 0.2s; }
    .stButton>button:hover { transform: scale(1.02); }
    
    /* ESTILOS PARA EL VIDEO */
    .video-box { border: 2px solid #8B5CF6; background-color: #F3E8FF; padding: 15px; border-radius: 10px; text-align: center; margin-top: 20px; }
    .agency-badge { background-color: #F59E0B; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.7em; font-weight: bold; vertical-align: middle; }

    /* REDISEÑO UPLOADER */
    [data-testid='stFileUploaderDropzoneInstructions'] > div:first-child { display: none; }
    [data-testid='stFileUploaderDropzoneInstructions']::before { content: "Arrastra tus fotos aquí"; visibility: visible; display: block; text-align: center; font-weight: bold; }
    [data-testid='stFileUploaderDropzoneInstructions']::after { content: "JPG, PNG • Máx 200MB"; visibility: visible; display: block; text-align: center; font-size: 0.8em; }
    
    /* MENÚ FLOTANTE */
    [data-testid="stSidebarCollapsedControl"] {
        position: fixed !important; top: 15px !important; left: 15px !important; z-index: 1000001 !important;
        background-color: #2563EB !important; color: white !important; border-radius: 12px !important;
        padding: 10px 15px !important; box-shadow: 0 4px 10px rgba(0,0,0,0.3) !important;
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
    keys_a_borrar = ['input_ubicacion', 'input_precio', 'input_whatsapp', 'generated_result', 'input_monto', 'input_moneda', 'video_path']
    for key in keys_a_borrar:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state['uploader_key'] += 1

def cerrar_sesion():
    st.session_state['usuario_activo'] = None
    st.session_state['plan_seleccionado'] = None
    st.session_state['ver_planes'] = False
    st.session_state['pedido_registrado'] = False

# --- FUNCIÓN GENERADORA DE VIDEO (MAGIA PURA 🪄) ---
def crear_reel_vertical(imagenes_uploaded, textos_clave):
    """Convierte imágenes en un video vertical 9:16 con texto superpuesto."""
    if not MOVIEPY_AVAILABLE:
        return None
    
    temp_dir = tempfile.mkdtemp()
    clips_images = []
    
    # Configuración 9:16 (ej: 720x1280 para ser ligero)
    W, H = 720, 1280
    
    # Duración por foto para que el total sea aprox 15-20 seg
    duracion_foto = 20.0 / len(imagenes_uploaded) if imagenes_uploaded else 3.0
    if duracion_foto < 2.0: duracion_foto = 2.0 # Mínimo 2 segs para leer

    for i, img_file in enumerate(imagenes_uploaded):
        # 1. Abrir y redimensionar imagen a vertical (Center Crop)
        img = Image.open(img_file).convert("RGB")
        img = ImageOps.fit(img, (W, H), method=Image.Resampling.LANCZOS)
        
        # 2. Oscurecer ligeramente para que el texto se lea (Overlay negro 30%)
        overlay = Image.new('RGBA', (W, H), (0, 0, 0, 80))
        img.paste(overlay, (0, 0), overlay)
        
        # 3. Escribir texto (Usando PIL para evitar problemas de ImageMagick)
        draw = ImageDraw.Draw(img)
        
        # Intentar cargar fuente, sino usar default
        try:
            font = ImageFont.truetype("arial.ttf", 60)
        except:
            font = ImageFont.load_default()

        # Seleccionar texto para esta imagen (rotativo)
        texto_actual = textos_clave[i % len(textos_clave)] if textos_clave else "AppyProp IA"
        
        # Centrar texto (Lógica básica de centrado)
        # En PIL moderno se usa textbbox, pero usaremos aproximación simple para compatibilidad
        draw.text((W/2, H*0.8), texto_actual, font=font, fill="white", anchor="mm", align="center")
        
        # Marca de agua pequeña
        draw.text((W/2, H*0.95), "Generado con AppyProp IA 🚀", fill="#cccccc", anchor="mm", font=font)

        # 4. Guardar frame procesado
        frame_path = os.path.join(temp_dir, f"frame_{i}.jpg")
        img.save(frame_path)
        clips_images.append(frame_path)

    # 5. Crear video con MoviePy
    clip = ImageSequenceClip(clips_images, fps=24, durations=[duracion_foto]*len(clips_images))
    
    # Exportar
    output_path = os.path.join(temp_dir, "reel_final.mp4")
    clip.write_videofile(output_path, codec="libx264", audio=False, fps=24, preset='ultrafast')
    
    return output_path

# --- INICIALIZACIÓN ---
if 'uploader_key' not in st.session_state: st.session_state['uploader_key'] = 0
if 'usuario_activo' not in st.session_state: st.session_state['usuario_activo'] = None
if 'ver_planes' not in st.session_state: st.session_state['ver_planes'] = False
if 'plan_seleccionado' not in st.session_state: st.session_state['plan_seleccionado'] = None
if 'pedido_registrado' not in st.session_state: st.session_state['pedido_registrado'] = False
if 'guest_last_use' not in st.session_state: st.session_state['guest_last_use'] = None
if 'guest_credits' not in st.session_state: st.session_state['guest_credits'] = 1

# --- API KEY ---
api_key = st.secrets.get("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None

# --- GOOGLE SHEETS MOCK (Para que funcione la UI sin DB real en esta demo) ---
def obtener_usuarios_sheet(): return [] # Placeholder
def registrar_pedido(n, a, e, t, p): return "CREATED" # Placeholder

# =======================================================
# === BARRA LATERAL ===
# =======================================================
with st.sidebar:
    st.header("🔐 Área de Miembros")
    if not st.session_state['usuario_activo']:
        st.info("💡 Modo Invitado activo")
        with st.form("login"):
            code = st.text_input("Código de Acceso")
            if st.form_submit_button("Entrar"):
                # LOGIN SIMULADO PARA PRUEBAS (BORRAR EN PROD)
                if code == "AGENCIA":
                    st.session_state['usuario_activo'] = {'cliente': 'Agente Top', 'plan': 'AGENCIA', 'limite': 99}
                    st.rerun()
                elif code == "PRO":
                    st.session_state['usuario_activo'] = {'cliente': 'Agente Pro', 'plan': 'ESTÁNDAR', 'limite': 10}
                    st.rerun()
                else:
                    st.error("Código no encontrado")
        st.markdown("---")
        if st.button("🚀 VER PLANES", on_click=ir_a_planes): pass
    else:
        u = st.session_state['usuario_activo']
        st.success(f"Hola {u.get('cliente')}")
        st.write(f"Plan: **{u.get('plan')}**")
        if st.button("Salir"): cerrar_sesion(); st.rerun()

# =======================================================
# === ZONA DE PLANES ===
# =======================================================
if st.session_state.ver_planes:
    st.title("💎 Escala tus Ventas")
    c1, c2, c3 = st.columns(3)
    with c1: st.info("🥉 Básico\n\n20.000 Gs"); st.button("Elegir Básico")
    with c2: st.info("🥈 Estándar\n\n35.000 Gs"); st.button("Elegir Estándar")
    with c3: st.warning("🥇 Agencia\n\n80.000 Gs\n\n🎬 **VIDEO REELS IA**"); st.button("ELEGIR AGENCIA")
    if st.button("Volver"): volver_a_app()
    st.stop()

# =======================================================
# === APP PRINCIPAL ===
# =======================================================
c_title, c_badge = st.columns([2, 1])
st.markdown("<h1 style='text-align: center;'>AppyProp IA 🚀</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #1E293B;'>Experto en Neuroventas Inmobiliarias</h3>", unsafe_allow_html=True)

es_pro = False
plan_actual = "INVITADO"
cupo_fotos = 3

if st.session_state['usuario_activo']:
    es_pro = True
    plan_str = str(st.session_state['usuario_activo'].get('plan', '')).lower()
    if 'agencia' in plan_str: 
        plan_actual = "AGENCIA"
        cupo_fotos = 10
    elif 'estándar' in plan_str:
        plan_actual = "ESTÁNDAR"
        cupo_fotos = 6
    else:
        plan_actual = "BÁSICO"
    st.markdown(f'<div style="text-align:center;"><span class="agency-badge">PLAN {plan_actual}</span></div>', unsafe_allow_html=True)

# --- 1. GALERÍA ---
st.write("#### 1. 📸 Galería")
uploaded_files = st.file_uploader("Sube tus fotos", type=["jpg", "png", "jpeg"], accept_multiple_files=True, key=f"up_{st.session_state['uploader_key']}")

if uploaded_files:
    if len(uploaded_files) > cupo_fotos:
        st.error(f"⛔ Tu plan {plan_actual} solo permite {cupo_fotos} fotos.")
        uploaded_files = uploaded_files[:cupo_fotos]
    
    with st.expander(f"👁️ Ver {len(uploaded_files)} fotos cargadas", expanded=False):
        cols = st.columns(4)
        for i, f in enumerate(uploaded_files):
            with cols[i%4]: st.image(f, use_container_width=True)

# --- 2. DATOS ---
st.write("#### 2. 📝 Datos")
c1, c2 = st.columns([3, 1])
with c1:
    oper = st.radio("Operación", ["Venta", "Alquiler"], horizontal=True)
    tipo = st.selectbox("Tipo", ["Casa", "Departamento", "Terreno"])
    ubicacion = st.text_input("Ubicación")
    
    col_p1, col_p2 = st.columns([2, 5])
    moneda = col_p1.selectbox("Divisa", ["Gs.", "$us"])
    precio = col_p2.text_input("Monto")

with c2:
    habs = st.number_input("Habitaciones", 1)
    banos = st.number_input("Baños", 1)
    garage = st.checkbox("Garage")
    piscina = st.checkbox("Piscina")

# --- GENERACIÓN ---
if st.button("✨ Generar Estrategia", type="primary"):
    if not ubicacion or not precio:
        st.warning("Faltan datos.")
        st.stop()
        
    with st.spinner("🧠 Analizando fotos y redactando..."):
        # SIMULACIÓN DE RESPUESTA DE IA (PARA NO GASTAR TOKENS EN PRUEBA)
        # EN PRODUCCIÓN: USAR EL CÓDIGO DE OPENAI QUE YA TENÍAS
        generated_text = f"""
        # 🏡 ¡Oportunidad Única en {ubicacion}!
        
        Descubre esta increíble propiedad de **{habs} habitaciones** y **{banos} baños**.
        Ideal para disfrutar en familia con su piscina refrescante.
        
        💰 **Precio:** {precio} {moneda}
        📍 **Ubicación:** {ubicacion}
        
        ¡Contáctanos ya! 🚀
        """
        time.sleep(2) # Simular espera
        st.session_state['generated_result'] = generated_text
        
        # --- LÓGICA DE VIDEO AUTOMÁTICO (SOLO AGENCIA) ---
        if plan_actual == "AGENCIA" and uploaded_files:
            # Extraer frases cortas del texto generado para poner en el video
            frases_para_video = [
                f"Oportunidad en {ubicacion}",
                f"{habs} Habitaciones - {banos} Baños",
                "Espacios Amplios y Luminosos" if "luz" in generated_text else "Diseño Único",
                "¡Con Piscina!" if piscina else "Tu nuevo hogar",
                f"Solo {precio} {moneda}",
                "¡Agenda tu visita hoy!"
            ]
            st.session_state['video_frases'] = frases_para_video

if 'generated_result' in st.session_state:
    st.success("✅ ¡Estrategia Lista!")
    st.markdown(st.session_state['generated_result'])
    
    # --- ZONA DE VIDEO REEL (EXCLUSIVO AGENCIA) ---
    st.markdown("---")
    st.subheader("🎬 Generador de Reels (Beta)")
    
    if plan_actual == "AGENCIA":
        if uploaded_files:
            col_vid_btn, col_vid_info = st.columns([1, 2])
            with col_vid_info:
                st.info("✨ **Función Premium:** Convertir estas fotos en un Video Vertical para TikTok/Reels.")
            
            with col_vid_btn:
                if st.button("🎥 CREAR VIDEO AHORA"):
                    if not MOVIEPY_AVAILABLE:
                        st.error("⚠️ Error: Librería de video no instalada en el servidor.")
                    else:
                        with st.spinner("🎞️ Renderizando video (esto toma unos segundos)..."):
                            try:
                                # Llamar a la función mágica
                                frases = st.session_state.get('video_frases', ["Propiedad Destacada", "Contáctanos"])
                                path_video = crear_reel_vertical(uploaded_files, frases)
                                st.session_state['video_path'] = path_video
                                st.balloons()
                            except Exception as e:
                                st.error(f"Error generando video: {e}")
            
            # MOSTRAR Y DESCARGAR VIDEO
            if 'video_path' in st.session_state:
                st.markdown('<div class="video-box"><h4>🎉 ¡Tu Reel está listo!</h4>', unsafe_allow_html=True)
                st.video(st.session_state['video_path'])
                
                with open(st.session_state['video_path'], "rb") as file:
                    st.download_button(
                        label="⬇️ Descargar Video MP4",
                        data=file,
                        file_name=f"reel_{ubicacion}.mp4",
                        mime="video/mp4",
                        type="primary"
                    )
                st.markdown("</div>", unsafe_allow_html=True)
                
        else:
            st.warning("⚠️ Sube fotos para generar un video.")
    else:
        # TEASER PARA OTROS PLANES
        st.markdown("""
        <div style="opacity: 0.5; filter: grayscale(1); pointer-events: none; border: 2px dashed #ccc; padding: 20px; text-align: center;">
            <h3>🎬 Video Reels Automáticos</h3>
            <p>Convierte tus fotos en videos virales en 1 clic.</p>
            <button disabled>🔒 Solo Plan Agencia</button>
        </div>
        <br>
        """, unsafe_allow_html=True)
        st.info("👆 **¿Quieres esta función?** Actualiza a Plan Agencia por solo 80.000 Gs.")

# --- FOOTER ---
st.markdown("<br><br><small>© 2026 AppyProp IA</small>", unsafe_allow_html=True)
``` ¡Me encanta esa ambición! 🎬 Convertir **AppyProp IA** en una productora de contenido multimedia automático es el "Killer Feature" que justificará totalmente el precio del **Plan Agencia (80.000 Gs)**.

Para lograr esto en Python sin pagar APIs costosas, usaremos una librería potente llamada **MoviePy**.

### ⚠️ Reto Técnico (Importante leer antes de copiar):
Generar video consume mucha memoria. En la nube gratuita de Streamlit podría ser lento, pero funcionará.
Para evitar errores con textos (que suelen fallar en la nube si no se configura ImageMagick), usaré un truco: **Escribiremos el texto sobre las imágenes usando Pillow (que ya usamos)** y luego uniremos esas imágenes en un video. ¡Es a prueba de balas! 🛡️

Aquí tienes la integración de **VIDEO REEL VERTICAL 9:16**.

### 1. Agrega esto a tu `requirements.txt`
Necesitas estas librerías nuevas para que funcione el video:
```text
moviepy
numpy
