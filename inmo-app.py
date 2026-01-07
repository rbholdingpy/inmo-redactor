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

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .main { background-color: #F3F4F6; }
    h1 { color: #111827; font-family: 'Helvetica Neue', sans-serif; font-weight: 800; }
    h2, h3, h4 { color: #1F2937; }
    .stButton>button {
        background-color: #2563EB; color: white; border-radius: 8px; border: none;
        padding: 12px 24px; font-weight: bold; transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #1D4ED8; transform: scale(1.02); box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
    }
    .plan-card {
        background-color: white; padding: 25px; border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-align: center; border: 1px solid #E5E7EB;
    }
    .tutorial-box {
        background-color: #EFF6FF; border-left: 5px solid #2563EB; padding: 20px; border-radius: 8px; margin-bottom: 20px;
    }
    /* Estilo para caja de Vision IA en Gratis */
    .vision-blocked {
        background-color: #FEF3C7; border-left: 5px solid #D97706; padding: 15px; border-radius: 5px; color: #92400E; font-size: 0.9em; margin-bottom: 15px;
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

# --- INICIALIZAR ESTADO ---
if 'plan_elegido' not in st.session_state:
    st.session_state['plan_elegido'] = "10_desc"
if 'tutorial_visto' not in st.session_state:
    st.session_state['tutorial_visto'] = False

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("⚙️ Admin: Simulador")
    opcion_plan = st.selectbox("Plan Usuario:", ["GRATIS", "Pack Básico", "Pack Estándar", "Agencia"])
    
    limites = { "GRATIS": 1, "Pack Básico": 3, "Pack Estándar": 7, "Agencia": 12 }
    limite_fotos = limites[opcion_plan]
    
    sin_creditos = st.checkbox("Simular: Sin Créditos", value=False)
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
# === ZONA DE VENTAS ===
# =======================================================
if mostrar_pagos:
    st.title("💎 Recarga tu VendeMás IA")
    if sin_creditos: st.error("⛔ ¡Tus créditos se han agotado!")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="plan-card"><h3>🥉 Básico</h3><h2>20.000 Gs</h2><p>10 Anuncios</p></div>', unsafe_allow_html=True)
        if st.button("Elegir Pack 10", use_container_width=True):
            st.session_state['plan_elegido'] = "10_desc"; st.rerun()
    with c2:
        st.markdown('<div class="plan-card"><h3>🥈 Estándar</h3><h2>35.000 Gs</h2><p>20 Anuncios</p></div>', unsafe_allow_html=True)
        if st.button("Elegir Pack 20", use_container_width=True):
            st.session_state['plan_elegido'] = "20_desc"; st.rerun()
    with c3:
        st.markdown('<div class="plan-card"><h3>🥇 Agencia</h3><h2>80.000 Gs</h2><p>200 Mensual</p></div>', unsafe_allow_html=True)
        if st.button("Elegir Mensual", use_container_width=True):
            st.session_state['plan_elegido'] = "200_desc"; st.rerun()
    
    st.divider()
    plan = st.session_state['plan_elegido']
    datos = {"10_desc": {"n":"Pack Básico", "m":"20.000 Gs"}, "20_desc": {"n":"Pack Estándar", "m":"35.000 Gs"}, "200_desc": {"n":"Plan Agencia", "m":"80.000 Gs"}}
    info = datos[plan]
    
    c_d, c_i = st.columns(2)
    with c_d:
        st.subheader("🏦 Transferencia SIPAP")
        st.code("RUC 1911221-1", language="text")
        st.write(f"**Monto:** {info['m']}")
    with c_i:
        msg = f"Hola, pagué {info['m']} por {info['n']}. Comprobante adjunto."
        link = f"https://wa.me/595981000000?text={msg.replace(' ', '%20')}"
        st.markdown(f'<br><a href="{link}" target="_blank" style="background-color:#25D366;color:white;padding:15px;border-radius:30px;text-decoration:none;font-weight:bold;">📲 Enviar Comprobante</a>', unsafe_allow_html=True)
    
    if sin_creditos: st.stop()

# =======================================================
# === APP PRINCIPAL ===
# =======================================================

st.title("🚀 VendeMás IA")
st.caption("Tu redactor inmobiliario experto en cierres.")

# Tutorial
if not st.session_state['tutorial_visto']:
    st.markdown('<div class="tutorial-box"><h3>👋 ¡Bienvenido!</h3><p>Sigue los pasos para vender más.</p></div>', unsafe_allow_html=True)
    if st.button("¡Entendido! 🚀"):
        st.session_state['tutorial_visto'] = True
        st.rerun()

# Estado
c_st, c_lim = st.columns([3, 1])
if opcion_plan != "GRATIS":
    c_st.success(f"PLAN: {opcion_plan.upper()}")
else:
    c_st.warning("PLAN: GRATIS (Modo Básico)")
c_lim.metric("Límite", f"{limite_fotos} Fotos")

# 1. FOTOS
st.write("#### 1. 📸 Galería")
uploaded_files = st.file_uploader("Subir fotos", type=["jpg", "png"], accept_multiple_files=True)

if uploaded_files:
    cant = len(uploaded_files)
    if cant > limite_fotos:
        st.error(f"⚠️ Has subido {cant} fotos. Tu plan permite {limite_fotos}."); st.stop()
    st.success(f"✅ {cant}/{limite_fotos} fotos listas.")
    with st.expander("Ver fotos"):
        cols = st.columns(4)
        for i, f in enumerate(uploaded_files):
            with cols[i%4]: st.image(Image.open(f), use_container_width=True)

    # 2. DATOS
    st.divider()
    st.write("#### 2. 📝 Datos de la Propiedad")
    c1, c2 = st.columns(2)
    
    with c1:
        operacion = st.radio("Operación", ["Venta", "Alquiler"], horizontal=True)
        
        # GESTIÓN
        nombre_agencia = ""
        tipo_gestion = ""
        if operacion == "Alquiler":
            tipo_gestion = st.radio("¿Quién alquila?", ["Propietario Directo", "Agencia/Inmobiliaria"], horizontal=True)
            if tipo_gestion == "Agencia/Inmobiliaria":
                nombre_agencia = st.text_input("Nombre de la Agencia", placeholder="Ej: Century 21")
        
        tipo = st.selectbox("Tipo", ["Casa", "Departamento", "Terreno", "Quinta", "Estancia", "Local Comercial", "Duplex", "Penthouse"])
        
        # --- ENFOQUE DE VENTA (Bloqueo en Gratis) ---
        if opcion_plan != "GRATIS":
            enfoque = st.selectbox(
                "🎯 Enfoque de Venta", 
                ["Normal (Equilibrado)", "🔥 Oportunidad / Oferta", "🔑 Tu Primera Casa", "💎 Lujo / Exclusivo", "💰 Ideal Inversionistas", "❤️ Ideal Parejas"],
                help="Define la psicología del anuncio."
            )
        else:
            enfoque = "Normal (Básico)"
            st.selectbox("🎯 Enfoque de Venta", ["🔒 Bloqueado (Solo PRO)"], disabled=True, help="🔒 Pásate a PRO para usar estrategias psicológicas de venta (Lujo, Urgencia, Inversión).")
        
        ubicacion = st.text_input("Ubicación", placeholder="Ej: Villa Morra")
        precio = st.text_input("Precio", placeholder="Gs / USD")
        
        if opcion_plan != "GRATIS":
            whatsapp = st.text_input("WhatsApp", placeholder="0981...")
        else:
            whatsapp = st.text_input("WhatsApp", placeholder="🔒 Solo Planes Pagos", disabled=True)

    with c2:
        habs = st.number_input("Habitaciones", 1)
        banos = st.number_input("Baños", 1)
        st.write("**Extras:**")
        quincho = st.checkbox("Quincho")
        piscina = st.checkbox("Piscina")
        cochera = st.checkbox("Cochera")
        
        txt_servicios = ""
        if operacion == "Alquiler":
            st.write("**🔌 Servicios:**")
            c_s1, c_s2 = st.columns(2)
            if c_s1.checkbox("💧 Agua"): txt_servicios += "Agua, "
            if c_s1.checkbox("⚡ Luz"): txt_servicios += "Luz, "
            if c_s1.checkbox("❄️ Aire A.A."): txt_servicios += "Aire A.A., "
            if c_s2.checkbox("📶 Wifi"): txt_servicios += "Wifi, "
            if c_s2.checkbox("💨 Ventilador"): txt_servicios += "Ventilador, "

    # 3. GENERAR
    st.divider()
    
    # --- MENSAJES DE VISION IA (DETALLADOS) ---
    if uploaded_files:
        if opcion_plan == "GRATIS":
            st.markdown("""
            <div class="vision-blocked">
                <strong>⚠️ Vision IA DESACTIVADA (Modo Ciego)</strong><br>
                La IA NO analizará tus fotos en el plan gratis.
                <br><em>Te pierdes: Detección de materiales (pisos, mesadas), análisis de iluminación natural, descripción de estilo arquitectónico y detalles premium.</em>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("👁️ **Vision IA Activa:** Escaneando texturas de pisos, calidad de iluminación natural, terminaciones y distribución de espacios...")
    
    if st.button("✨ Redactar Anuncio Vendedor"):
        if not ubicacion or not precio:
            st.warning("⚠️ Faltan datos (Ubicación o Precio).")
        else:
            with st.spinner('🤖 Redactando estrategia...'):
                try:
                    # GESTIÓN
                    info_gestion = ""
                    if operacion == "Alquiler":
                        if tipo_gestion == "Propietario Directo": info_gestion = "Trato directo con el propietario (sin comisiones)."
                        elif tipo_gestion == "Agencia/Inmobiliaria" and nombre_agencia: info_gestion = f"Gestión profesional a cargo de {nombre_agencia}."
                        else: info_gestion = "Gestión profesional."

                    # LÓGICA DEL PROMPT (PRO vs GRATIS)
                    prompt_vision = ""
                    if opcion_plan != "GRATIS":
                        prompt_vision = "TAREA VISUAL (IMPORTANTE): Analiza DETALLADAMENTE las imágenes. Describe pisos, iluminación, materiales y sensaciones."
                    else:
                        prompt_vision = "TAREA VISUAL: (IGNORA detalles profundos de las fotos, haz una descripción genérica basada solo en los datos de texto)."

                    prompt = f"""
                    Actúa como copywriter inmobiliario senior.
                    
                    FORMATO DE SALIDA (ESTRICTO):
                    1. NO USES MARKDOWN. Prohibido usar #, ##, ***, -. 
                    2. USA SOLO EMOJIS como viñetas.
                    
                    ESTRATEGIA: "{enfoque}"
                    {prompt_vision}
                    
                    REDACCIÓN PARA: {operacion} de {tipo} en {ubicacion}.
                    DATOS: Precio {precio}. {habs} habs, {banos} baños. Extras: Quincho={quincho}, Piscina={piscina}, Cochera={cochera}.
                    {f'Servicios: {txt_servicios}' if operacion == 'Alquiler' else ''}
                    Gestión: {info_gestion}
                    
                    CIERRE: Link: https://wa.me/595{whatsapp} (Si está vacío no poner).
                    """
                    
                    content = [{"type": "text", "text": prompt}]
                    for f in uploaded_files:
                        img = Image.open(f)
                        b64 = encode_image(img)
                        content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
                        
                    response = client.chat.completions.create(
                         model="gpt-4o-mini", messages=[{"role": "user", "content": content}], max_tokens=900
                    )
                    st.success("¡Anuncio listo!")
                    st.text_area("Copia y pega:", value=response.choices[0].message.content, height=600)

                except Exception as e:
                    st.error(f"Error: {e}")
