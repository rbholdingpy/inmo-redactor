import streamlit as st
from PIL import Image
import base64
import io
import os
import time
from openai import OpenAI

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="VendeMás IA",
    page_icon="🚀",
    layout="centered",
    initial_sidebar_state="expanded"
)

# --- ESTILOS CSS PERSONALIZADOS (LOOK PREMIUM) ---
st.markdown("""
    <style>
    .main {
        background-color: #F3F4F6;
    }
    h1 {
        color: #111827;
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 800;
    }
    h2, h3, h4 {
        color: #1F2937;
    }
    .stButton>button {
        background-color: #2563EB; /* Azul Royal */
        color: white;
        border-radius: 8px;
        border: none;
        padding: 12px 24px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #1D4ED8;
        transform: scale(1.02);
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
    }
    /* Tarjetas de Planes */
    .plan-card {
        background-color: white;
        padding: 25px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        text-align: center;
        border: 1px solid #E5E7EB;
        transition: transform 0.2s;
    }
    .plan-card:hover {
        transform: translateY(-5px);
        border-color: #2563EB;
    }
    /* Tutorial Box */
    .tutorial-box {
        background-color: #EFF6FF; /* Azul muy claro */
        border-left: 5px solid #2563EB;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 20px;
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

# --- INICIALIZAR ESTADO (Tutorial y Planes) ---
if 'plan_elegido' not in st.session_state:
    st.session_state['plan_elegido'] = "10_desc"
if 'tutorial_visto' not in st.session_state:
    st.session_state['tutorial_visto'] = False

# --- BARRA LATERAL (SIMULADOR) ---
with st.sidebar:
    st.header("⚙️ Admin: Simulador")
    opcion_plan = st.selectbox("Plan Usuario:", ["GRATIS", "Pack Básico", "Pack Estándar", "Agencia"])
    
    limites = {
        "GRATIS": 1,
        "Pack Básico": 3,
        "Pack Estándar": 7,
        "Agencia": 12
    }
    limite_fotos = limites[opcion_plan]
    
    sin_creditos = st.checkbox("Simular: Sin Créditos", value=False)
    
    # Botón para resetear tutorial (solo para que tú pruebes)
    if st.button("🔄 Resetear Tutorial"):
        st.session_state['tutorial_visto'] = False
        st.rerun()
        
    st.divider()
    ver_precios = st.toggle("👉 Ver Lista de Precios", value=False)

mostrar_pagos = ver_precios or sin_creditos

# --- API KEY ---
api_key = st.secrets.get("OPENAI_API_KEY")
if not api_key:
    st.error("⚠️ Falta API Key.")
    st.stop()
client = OpenAI(api_key=api_key)

# =======================================================
# === ZONA DE VENTAS (MANTENIDA) ===
# =======================================================
if mostrar_pagos:
    st.title("💎 Recarga tu VendeMás IA")
    st.markdown("Elige el pack que mejor se adapte a tu volumen de ventas.")
    
    if sin_creditos:
        st.error("⛔ ¡Tus créditos se han agotado! Recarga para continuar.")

    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("""
        <div class="plan-card">
            <h3>🥉 Básico</h3>
            <h2>20.000 Gs</h2>
            <p>10 Anuncios</p>
            <p>Max 3 Fotos</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Elegir Pack 10", use_container_width=True):
            st.session_state['plan_elegido'] = "10_desc"
            st.rerun()

    with c2:
        st.markdown("""
        <div class="plan-card" style="border: 2px solid #2563EB;">
            <h3>🥈 Estándar</h3>
            <h2>35.000 Gs</h2>
            <p>20 Anuncios</p>
            <p>Max 7 Fotos</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Elegir Pack 20", use_container_width=True):
            st.session_state['plan_elegido'] = "20_desc"
            st.rerun()

    with c3:
        st.markdown("""
        <div class="plan-card">
            <h3>🥇 Agencia</h3>
            <h2>80.000 Gs</h2>
            <p>200 Mensual</p>
            <p>Max 12 Fotos</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Elegir Mensual", use_container_width=True):
            st.session_state['plan_elegido'] = "200_desc"
            st.rerun()

    st.divider()

    plan = st.session_state['plan_elegido']
    datos_plan = {
        "10_desc":  {"nombre": "Pack Básico",   "monto": "20.000 Gs"},
        "20_desc":  {"nombre": "Pack Estándar", "monto": "35.000 Gs"},
        "200_desc": {"nombre": "Plan Agencia",  "monto": "80.000 Gs"}
    }
    info = datos_plan[plan]
    
    st.info(f"👇 **Instrucciones para activar tu {info['nombre']}:**")
    
    c_datos, c_info = st.columns([1, 1])
    
    with c_datos:
        st.subheader("🏦 Transferencia SIPAP")
        st.write("Copia el Alias y transfiere el monto exacto.")
        st.code("RUC 1911221-1", language="text") 
        st.caption(f"Titular: Ricardo Blanco | C.I: 1911221 | Itaú: 320595209")
        st.markdown(f"**Monto:** # {info['monto']}")

    with c_info:
        msg_wa = f"Hola, ya transferí {info['monto']} por el {info['nombre']}. Aquí está mi comprobante."
        link_wa = f"https://wa.me/595981000000?text={msg_wa.replace(' ', '%20')}"
        
        st.write("---")
        st.write("📸 **Paso final:**")
        st.markdown(f"""
        <a href="{link_wa}" target="_blank" style="
            display: inline-block;
            background-color: #25D366;
            color: white;
            padding: 15px 30px;
            text-decoration: none;
            border-radius: 50px;
            font-weight: bold;
            font-size: 18px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        ">
            📲 Enviar Comprobante
        </a>
        """, unsafe_allow_html=True)

    if sin_creditos:
        st.stop()

# =======================================================
# === APP PRINCIPAL ===
# =======================================================

st.title("🚀 VendeMás IA")
st.caption("Tu redactor inmobiliario experto en cierres.")

# --- LÓGICA DEL TUTORIAL DE PRIMERA VEZ ---
if not st.session_state['tutorial_visto']:
    st.markdown("""
    <div class="tutorial-box">
        <h3>👋 ¡Bienvenido a tu Asistente de Ventas!</h3>
        <p>Sigue estos 3 pasos para crear tu primer anuncio viral:</p>
    </div>
    """, unsafe_allow_html=True)
    
    col_t1, col_t2, col_t3 = st.columns(3)
    with col_t1:
        st.info("1️⃣ **Sube Fotos**\n\nCarga la fachada y los interiores. La IA los analizará.")
    with col_t2:
        st.warning("2️⃣ **Detalles**\n\nCompleta ubicación, precio y extras. Cuanto más datos, mejor.")
    with col_t3:
        st.success("3️⃣ **¡Genera!**\n\nPresiona el botón mágico y obtén tu texto vendedor.")
    
    if st.button("¡Entendido, Empezar! 🚀"):
        st.session_state['tutorial_visto'] = True
        st.rerun()
    
    st.divider() # Separa el tutorial de la app real

# --- BARRA DE ESTADO ---
col_estado, col_limite = st.columns([3, 1])
with col_estado:
    if opcion_plan == "GRATIS":
        st.warning("PLAN: GRATIS (Prueba)")
    else:
        st.success(f"PLAN: {opcion_plan.upper()}")
with col_limite:
    st.metric("Límite Fotos", f"{limite_fotos}")

# --- 1. FOTOS ---
st.write("#### 1. 📸 Galería de Imágenes")
uploaded_files = st.file_uploader(
    "Sube las fotos aquí", 
    type=["jpg", "png"], 
    accept_multiple_files=True,
    help=f"Sube fotos de la fachada, interior y patio. Tu plan permite {limite_fotos} fotos."
)

if uploaded_files:
    cant = len(uploaded_files)
    
    # Validación Límites
    if cant > limite_fotos:
        st.error(f"⚠️ **Has subido {cant} fotos. Tu plan {opcion_plan} permite máximo {limite_fotos}.**")
        st.info("💡 Consejo: Elimina fotos o mejora tu plan en la barra lateral.")
        st.stop()
        
    st.success(f"✅ {cant}/{limite_fotos} fotos cargadas.")
    
    with st.expander("👁️ Ver fotos cargadas", expanded=True):
        cols = st.columns(4)
        for i, file in enumerate(uploaded_files):
            with cols[i % 4]:
                image = Image.open(file)
                st.image(image, use_container_width=True)
    
    # --- 2. DATOS ---
    st.divider()
    st.write("#### 2. 📝 Datos de la Propiedad")
    
    c1, c2 = st.columns(2)
    with c1:
        operacion = st.radio("Operación", ["Venta", "Alquiler"], horizontal=True, help="Elige si vendes o alquilas.")
        tipo = st.selectbox("Tipo de Inmueble", ["Casa", "Departamento", "Terreno", "Quinta", "Estancia", "Local Comercial", "Duplex", "Penthouse"], help="Define la estructura del texto.")
        ubicacion = st.text_input("Ubicación", placeholder="Ej: Villa Morra, Asunción", help="Barrio y Ciudad.")
        precio = st.text_input("Precio", placeholder="Gs / USD", help="Incluye la moneda.")
        
        if opcion_plan != "GRATIS":
            whatsapp = st.text_input("WhatsApp", placeholder="0981...", help="Número sin espacios para el link directo.")
        else:
            whatsapp = st.text_input("WhatsApp", placeholder="🔒 Solo Planes Pagos", disabled=True, help="Mejora tu plan para habilitar esto.")

    with c2:
        habs = st.number_input("Habitaciones", 1, help="Dormitorios.")
        banos = st.number_input("Baños", 1, help="Sanitarios.")
        
        st.write("**Extras:**")
        quincho = st.checkbox("Quincho", help="Zona de asado techada.")
        piscina = st.checkbox("Piscina", help="Pileta.")
        cochera = st.checkbox("Cochera", help="Estacionamiento.")
        
        txt_servicios = ""
        if operacion == "Alquiler":
            st.write("---")
            st.write("**🔌 Servicios Incluidos:**")
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                if st.checkbox("💧 Agua"): txt_servicios += "Agua corriente, "
                if st.checkbox("⚡ Luz"): txt_servicios += "Energía eléctrica, "
                if st.checkbox("❄️ Aire A.A."): txt_servicios += "Aire Acondicionado, "
            with col_s2:
                if st.checkbox("📶 Wifi"): txt_servicios += "Internet Wifi, "
                if st.checkbox("💨 Ventilador"): txt_servicios += "Ventiladores de techo, "

    # --- 3. GENERAR ---
    st.divider()
    
    if uploaded_files:
        st.info("👁️ **Vision IA Activada:** Analizando materiales, iluminación y espacios...")

    if st.button("✨ Redactar Anuncio Vendedor", help="Generar descripción con IA."):
        if not ubicacion or not precio:
            st.warning("⚠️ Faltan datos básicos (Ubicación o Precio).")
        else:
            with st.spinner('🤖 La IA está escribiendo tu anuncio...'):
                try:
                    prompt = f"""
                    Actúa como copywriter inmobiliario senior.
                    TAREA VISUAL: Analiza las {cant} imágenes. Describe pisos, luz, estilo, fachada.
                    TAREA REDACCIÓN: Anuncio persuasivo {operacion} {tipo} en {ubicacion}.
                    DATOS: Precio {precio}. {habs} habs, {banos} baños. Extras: Quincho={quincho}, Piscina={piscina}, Cochera={cochera}.
                    {f'Servicios: {txt_servicios}' if operacion == 'Alquiler' else ''}
                    CIERRE: Llamado a la acción. {f'Link: https://wa.me/595{whatsapp}' if whatsapp else ''}
                    """
                    
                    content = [{"type": "text", "text": prompt}]
                    for file in uploaded_files:
                        img = Image.open(file)
                        b64 = encode_image(img)
                        content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
                        
                    response = client.chat.completions.create(
                         model="gpt-4o-mini",
                         messages=[{"role": "user", "content": content}],
                         max_tokens=900
                    )
                    st.success("¡Anuncio listo!")
                    st.text_area("Tu descripción:", value=response.choices[0].message.content, height=600)

                except Exception as e:
                    st.error(f"Error: {e}")
