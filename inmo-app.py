import streamlit as st
from PIL import Image
import base64
import io
import os
from openai import OpenAI

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Inmo-Redactor IA", page_icon="🏡", layout="centered")

# --- FUNCIÓN NECESARIA (LA QUE FALTABA) ---
def encode_image(image):
    buffered = io.BytesIO()
    # Convertimos a RGB por si acaso es PNG con transparencia
    if image.mode in ("RGBA", "P"):
        image = image.convert("RGB")
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# --- BARRA LATERAL (SIMULADOR DE ESTADOS) ---
with st.sidebar:
    st.header("⚙️ Admin: Simulador")
    st.info("Usa esto para ver lo que vería tu cliente según su plan.")
    
    # 1. Elegir el Plan del Usuario
    plan_actual = st.selectbox(
        "Plan del Usuario:", 
        ["GRATIS (Nuevo)", "Pack Básico (10 Créditos)", "Pack Estándar (20 Créditos)", "Agencia (200 Mensual)"]
    )
    
    # 2. Simular si se le acabaron los créditos
    sin_creditos = st.checkbox("Simular: Créditos Agotados (0)", value=False)
    
    st.divider()
    
    # Botón para ver la zona de pagos voluntariamente
    ver_precios = st.toggle("👉 Ver Lista de Precios", value=False)

# Lógica de visualización de pagos
mostrar_pagos = ver_precios or sin_creditos

# --- API KEY ---
api_key = st.secrets.get("OPENAI_API_KEY")
if not api_key:
    st.error("⚠️ Falta la API Key en Secrets.")
    st.stop()
client = OpenAI(api_key=api_key)

# =======================================================
# === ZONA DE VENTAS Y PAGOS ===
# =======================================================
if mostrar_pagos:
    st.title("💎 Recarga tu Inmo-Redactor")
    
    if sin_creditos:
        st.error("⛔ ¡Ups! Se agotaron tus descripciones.")
        st.write("Para seguir generando anuncios vendedores, elige un pack y recarga al instante.")
    else:
        st.write("Elige el plan que mejor se adapte a tu ritmo de ventas.")

    # --- TABLA DE PRECIOS ---
    col_p1, col_p2, col_p3 = st.columns(3)
    
    # PLAN 1: BÁSICO
    with col_p1:
        st.markdown("### 🥉 Básico")
        st.markdown("## 20.000 Gs")
        st.caption("Pack de Recarga")
        st.write("✅ **10 Descripciones**")
        st.write("✅ Fotos Ilimitadas")
        st.write("❌ Se agota al usarlo")
        if st.button("Elegir Pack 10"):
            st.session_state['plan_elegido'] = "10_desc"

    # PLAN 2: ESTÁNDAR
    with col_p2:
        st.markdown("### 🥈 Estándar")
        st.markdown("## 35.000 Gs")
        st.caption("Pack de Recarga")
        st.write("✅ **20 Descripciones**")
        st.write("✅ Fotos Ilimitadas")
        st.write("❌ Se agota al usarlo")
        if st.button("Elegir Pack 20"):
            st.session_state['plan_elegido'] = "20_desc"

    # PLAN 3: AGENCIA
    with col_p3:
        st.markdown("### 🥇 Agencia")
        st.markdown("## 80.000 Gs")
        st.caption("Pago Mensual")
        st.write("✅ **200 Descripciones**")
        st.write("✅ Prioridad Alta")
        st.write("🔄 Se renueva cada mes")
        if st.button("Elegir Mensual"):
            st.session_state['plan_elegido'] = "200_desc"

    st.divider()

    # --- DETALLES DE PAGO (QR y Transferencia) ---
    st.subheader("💳 Formas de Pago")
    
    # Mensaje dinámico para WhatsApp
    plan_seleccionado = st.session_state.get('plan_elegido', 'general')
    mensajes_wa = {
        "10_desc": "Hola, quiero el Pack de 10 descripciones por 20.000 Gs.",
        "20_desc": "Hola, quiero el Pack de 20 descripciones por 35.000 Gs.",
        "200_desc": "Hola, quiero el Plan Mensual de 200 descripciones por 80.000 Gs.",
        "general": "Hola, quiero recargar saldo en la App."
    }
    msg_wa = mensajes_wa.get(plan_seleccionado, mensajes_wa['general'])
    link_wa = f"https://wa.me/595981000000?text={msg_wa.replace(' ', '%20')}"

    tab1, tab2 = st.tabs(["📲 QR Simple", "🏦 Transferencia"])

    with tab1:
        c1, c2 = st.columns([1, 2])
        with c1:
            if os.path.exists("qr.jpg"):
                st.image("qr.jpg", width=200)
            else:
                st.warning("Falta subir qr.jpg")
        with c2:
            st.info("1. Escanea el QR.")
            st.write("2. Ingresa el monto del plan elegido.")
            st.markdown(f"3. [**👉 Enviar Comprobante por WhatsApp aquí**]({link_wa})")

    with tab2:
        st.code("""
        Banco: ITAÚ
        Titular: Ricardo Blanco
        Alias: RUC 1911221-1
        C.I: 1911221
        Nro. de Cuenta: 320595209
        """, language="text")
        st.markdown(f"Una vez transferido, [**👉 Enviar Comprobante aquí**]({link_wa})")

    # Si se quedó sin créditos, detenemos la app aquí
    if sin_creditos:
        st.stop()

# =======================================================
# === APP PRINCIPAL ===
# =======================================================

st.title("🏡 Inmo-Redactor IA")

# Mostrar estado actual
if plan_actual == "GRATIS (Nuevo)":
    st.warning("Estás en el plan de prueba GRATIS.")
elif "Pack" in plan_actual:
    st.info(f"Plan Activo: {plan_actual}. Recuerda que al terminar tu cupo puedes recargar.")
else:
    st.success("Plan Activo: AGENCIA (Mensual).")

# --- 1. CARGA DE IMAGENES ---
st.write("#### 1. 📸 Fotos del Inmueble")
uploaded_files = st.file_uploader("Sube tus fotos", type=["jpg", "png"], accept_multiple_files=True)

if uploaded_files:
    cant = len(uploaded_files)
    # Validar límite para plan GRATIS
    if plan_actual == "GRATIS (Nuevo)" and cant > 1:
        st.error("🔒 El plan GRATIS solo permite 1 foto. Pásate a un Pack para subir galería completa.")
        st.stop()
        
    st.success(f"✅ {cant} foto(s) cargada(s).")
    
    # --- 2. DATOS ---
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        operacion = st.radio("Operación", ["Venta", "Alquiler"], horizontal=True)
        tipo = st.selectbox("Tipo", ["Casa", "Departamento", "Terreno", "Quinta", "Estancia", "Local Comercial", "Duplex", "Penthouse"])
        ubicacion = st.text_input("Ubicación", placeholder="Ej: Villa Morra")
        precio = st.text_input("Precio")
        
        if plan_actual != "GRATIS (Nuevo)":
            whatsapp = st.text_input("Tu WhatsApp (Link automático)", placeholder="0981...")
        else:
            whatsapp = st.text_input("Tu WhatsApp", placeholder="🔒 Solo Planes Pagos", disabled=True)

    with col2:
        habs = st.number_input("Habitaciones", 1)
        banos = st.number_input("Baños", 1)
        st.write("**Extras:**")
        quincho = st.checkbox("Quincho")
        piscina = st.checkbox("Piscina")
        cochera = st.checkbox("Cochera")
        
        # Servicios Alquiler
        txt_servicios = ""
        if operacion == "Alquiler":
            st.write("---")
            agua = st.checkbox("Agua"); luz = st.checkbox("Luz"); aire = st.checkbox("Aire A.A.")
            if agua: txt_servicios += "Agua, "
            if luz: txt_servicios += "Luz, "
            if aire: txt_servicios += "Aire Acondicionado"

    # --- 3. GENERAR ---
    st.divider()
    if st.button("✨ Generar Anuncio"):
        if not ubicacion or not precio:
            st.warning("Faltan datos.")
        else:
            with st.spinner('🤖 Trabajando...'):
                try:
                    # Preparar Prompt
                    prompt = f"""
                    Actúa como experto inmobiliario.
                    Crea anuncio de {operacion} de {tipo} en {ubicacion}.
                    Precio: {precio}. {habs} habs, {banos} baños.
                    Extras: Quincho={quincho}, Piscina={piscina}.
                    {f'Servicios incluidos: {txt_servicios}' if operacion == 'Alquiler' else ''}
                    {f'Link WhatsApp: https://wa.me/595{whatsapp}' if whatsapp else ''}
                    Analiza las imágenes adjuntas y describe los detalles visuales.
                    """
                    
                    # Llamada API
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
                    
                    if "Pack" in plan_actual:
                        st.info("💡 Tip: Si te quedan pocas descripciones, puedes recargar tu pack en el menú lateral.")

                except Exception as e:
                    st.error(f"Error: {e}")
