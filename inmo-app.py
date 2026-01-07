import streamlit as st
from PIL import Image
import base64
import io
import os
from openai import OpenAI

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Inmo-Redactor IA", page_icon="🏡", layout="centered")

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

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("⚙️ Admin")
    plan_actual = st.selectbox("Plan Usuario:", ["GRATIS", "Pack Básico", "Pack Estándar", "Agencia"])
    sin_creditos = st.checkbox("Simular: Sin Créditos", value=False)
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
# === ZONA DE VENTAS (SOLO TRANSFERENCIA) ===
# =======================================================
if mostrar_pagos:
    st.title("💎 Recarga tu Inmo-Redactor")
    
    if sin_creditos:
        st.error("⛔ ¡Se agotaron tus descripciones!")
    
    st.write("Selecciona un plan para ver los datos de pago:")

    # BOTONES DE SELECCIÓN
    c1, c2, c3 = st.columns(3)
    with c1:
        st.info("🥉 **BÁSICO**\n\n**20.000 Gs**\n\n10 Anuncios")
        if st.button("Pack 10", use_container_width=True):
            st.session_state['plan_elegido'] = "10_desc"
            st.rerun()
    with c2:
        st.warning("🥈 **ESTÁNDAR**\n\n**35.000 Gs**\n\n20 Anuncios")
        if st.button("Pack 20", use_container_width=True):
            st.session_state['plan_elegido'] = "20_desc"
            st.rerun()
    with c3:
        st.success("🥇 **AGENCIA**\n\n**80.000 Gs**\n\n200 Mensual")
        if st.button("Mensual", use_container_width=True):
            st.session_state['plan_elegido'] = "200_desc"
            st.rerun()

    st.divider()

    # --- LÓGICA DE DATOS ---
    plan = st.session_state['plan_elegido']
    datos_plan = {
        "10_desc":  {"nombre": "Pack Básico",   "monto": "20.000 Gs"},
        "20_desc":  {"nombre": "Pack Estándar", "monto": "35.000 Gs"},
        "200_desc": {"nombre": "Plan Agencia",  "monto": "80.000 Gs"}
    }
    info = datos_plan[plan]
    
    # CARTEL GRANDE DE MONTO
    st.markdown(f"""
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center; border: 1px solid #ddd; margin-bottom: 20px;">
        <h4 style="margin:0; color: #555;">Plan Seleccionado: {info['nombre']}</h4>
        <h1 style="color: #28a745; font-size: 45px; margin: 10px 0;">{info['monto']}</h1>
        <p style="color: #666;">Realiza la transferencia y envía el comprobante.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # --- ZONA DE DATOS BANCARIOS ---
    st.subheader("🏦 Datos para Transferencia (SIPAP)")
    
    # Usamos st.code para el Alias porque Streamlit pone un botón de "copiar" automáticamente
    st.write("👇 **Copia el Alias para transferir rápido:**")
    st.code("RUC 1911221-1", language="text") 
    
    st.write("**Detalles de la cuenta:**")
    st.text(f"""
    Banco:      ITAÚ
    Titular:    Ricardo Blanco
    C.I:        1911221
    Cuenta Nro: 320595209
    """)

    # Link WhatsApp
    msg_wa = f"Hola, ya transferí {info['monto']} por el {info['nombre']}. Aquí está mi comprobante."
    link_wa = f"https://wa.me/595981000000?text={msg_wa.replace(' ', '%20')}"
    
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center;">
        <a href="{link_wa}" target="_blank" style="background-color: #25D366; color: white; padding: 15px 25px; text-decoration: none; border-radius: 30px; font-weight: bold; font-size: 18px;">
            📲 Enviar Comprobante por WhatsApp
        </a>
    </div>
    """, unsafe_allow_html=True)

    if sin_creditos:
        st.stop()

# =======================================================
# === APP PRINCIPAL (RESTO IGUAL) ===
# =======================================================

st.title("🏡 Inmo-Redactor IA")

if plan_actual == "GRATIS":
    st.warning("Plan: GRATIS")
elif "Pack" in plan_actual:
    st.info(f"Plan: {plan_actual}")
else:
    st.success("Plan: AGENCIA")

# --- 1. FOTOS ---
st.write("#### 1. 📸 Fotos")
uploaded_files = st.file_uploader("Sube fotos", type=["jpg", "png"], accept_multiple_files=True)

if uploaded_files:
    cant = len(uploaded_files)
    if plan_actual == "GRATIS" and cant > 1:
        st.error("🔒 Gratis = Solo 1 foto.")
        st.stop()
        
    st.success(f"✅ {cant} fotos.")
    
    # --- 2. DATOS ---
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        operacion = st.radio("Operación", ["Venta", "Alquiler"], horizontal=True)
        tipo = st.selectbox("Tipo", ["Casa", "Departamento", "Terreno", "Quinta", "Local", "Duplex"])
        ubicacion = st.text_input("Ubicación")
        precio = st.text_input("Precio")
        
        if plan_actual != "GRATIS":
            whatsapp = st.text_input("WhatsApp (Auto Link)", placeholder="0981...")
        else:
            whatsapp = st.text_input("WhatsApp", placeholder="🔒 Solo Pagos", disabled=True)

    with c2:
        habs = st.number_input("Habitaciones", 1)
        banos = st.number_input("Baños", 1)
        st.write("Extras:")
        quincho = st.checkbox("Quincho")
        piscina = st.checkbox("Piscina")
        
        txt_servicios = ""
        if operacion == "Alquiler":
            st.write("---")
            if st.checkbox("Incluye Agua/Luz"): txt_servicios += "Agua y Luz, "
            if st.checkbox("Aire Acond."): txt_servicios += "Aire A.A."

    # --- 3. GENERAR ---
    st.divider()
    if st.button("✨ Generar Anuncio"):
        if not ubicacion or not precio:
            st.warning("Faltan datos.")
        else:
            with st.spinner('Procesando...'):
                try:
                    prompt = f"Anuncio {operacion} {tipo} en {ubicacion}. Precio {precio}. {habs} habs. {txt_servicios}."
                    
                    content = [{"type": "text", "text": prompt}]
                    for file in uploaded_files:
                        img = Image.open(file)
                        b64 = encode_image(img)
                        content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
                        
                    response = client.chat.completions.create(
                         model="gpt-4o-mini",
                         messages=[{"role": "user", "content": content}],
                         max_tokens=700
                    )
                    st.text_area("Resultado:", value=response.choices[0].message.content, height=500)

                except Exception as e:
                    st.error(f"Error: {e}")
