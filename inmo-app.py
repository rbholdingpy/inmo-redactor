import streamlit as st
from PIL import Image
import base64
import io
import os
from openai import OpenAI

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Inmo-Redactor IA", page_icon="🏡", layout="centered")

# --- BARRA LATERAL (SIMULADOR DE PLANES Y PAGOS) ---
with st.sidebar:
    st.header("⚙️ Tu Cuenta")
    
    # Selector simulado
    tipo_plan = st.radio("Tu Plan Actual:", ["GRATIS (Free)", "PREMIUM (Pro)"])
    
    st.divider()
    
    # BOTÓN PARA SUSCRIBIRSE
    if tipo_plan == "GRATIS (Free)":
        st.warning("🔒 Estás en modo limitado.")
        st.markdown("### 🚀 ¡Pásate a PRO!")
        st.markdown("- Fotos ilimitadas\n- Análisis Visual IA\n- Link de WhatsApp\n- Soporte Prioritario")
        
        # Botón que abre la sección de pagos en el centro
        mostrar_pagos = st.toggle("👉 Ver Formas de Pago", value=False)
    else:
        st.success("✅ Eres usuario PRO")
        mostrar_pagos = False

# --- API KEY ---
api_key = st.secrets.get("OPENAI_API_KEY")
if not api_key:
    st.error("⚠️ Falta la API Key en Secrets.")
    st.stop()
client = OpenAI(api_key=api_key)

# --- PANTALLA DE PAGOS (SOLO SI SE ACTIVA) ---
if mostrar_pagos:
    st.title("💎 Suscríbete al Plan PRO")
    st.write("Elige tu método de pago favorito. La activación es en minutos.")
    
    # SOLO 2 PESTAÑAS: QR Y TRANSFERENCIA
    tab1, tab2 = st.tabs(["📲 Pagar con QR", "🏦 Transferencia"])
    
    with tab1:
        st.subheader("Escanea y Paga (Rápido)")
        col_qr1, col_qr2 = st.columns([1, 2])
        
        with col_qr1:
            # Busca qr.jpg
            if os.path.exists("qr.jpg"):
                st.image("qr.jpg", caption="Escanea con tu App del Banco", use_container_width=True)
            else:
                st.error("⚠️ No encuentro el archivo 'qr.jpg'")
                st.info("Sube la foto del QR a GitHub con el nombre: qr.jpg")

        with col_qr2:
            st.write("1. Abre la App de tu banco (Itaú, Ueno, Familiar, Tigo).")
            st.write("2. Selecciona 'Cobrar/Pagar con QR'.")
            st.write("3. Escanea el código de la pantalla.")
            st.write("4. **Monto a pagar:** 35.000 Gs (Mensual)")
            st.divider()
            st.write("✅ **Una vez pagado:**")
            st.markdown("[📲 Enviar Comprobante por WhatsApp](https://wa.me/595981000000?text=Hola,%20ya%20pagué%20el%20plan%20PRO,%20aquí%20mi%20comprobante)")

    with tab2:
        st.subheader("Datos para Transferencia (SIPAP)")
        st.write("Puedes transferir desde cualquier banco a esta cuenta:")
        
        # --- DATOS ACTUALIZADOS DE RICARDO BLANCO ---
        st.code("""
        Banco: ITAÚ
        Titular: Ricardo Blanco
        Alias: RUC 1911221-1
        C.I: 1911221
        Nro. de Cuenta: 320595209
        """, language="text")
        
        st.info("Una vez realizada la transferencia, envía la captura al WhatsApp.")
        st.markdown("[📲 Enviar Comprobante Ahora](https://wa.me/595981000000)")

    st.divider()

# --- LÓGICA DE LA APP (Si está pagando, ocultamos la app) ---
if mostrar_pagos:
    st.info("👆 Completa el pago arriba para desbloquear las funciones.")
    st.stop() 

# =======================================================
# === APP PRINCIPAL ===
# =======================================================

# --- TÍTULO ---
st.title("🏡 Inmo-Redactor IA")
st.caption(f"Modo Actual: {tipo_plan}")

# --- FUNCIÓN PARA CODIFICAR IMÁGENES ---
def encode_image(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# --- 1. CARGA DE IMAGENES ---
st.write("#### 1. 📸 Fotos del Inmueble")

if tipo_plan == "PREMIUM (Pro)":
    uploaded_files = st.file_uploader("Sube la galería completa", type=["jpg", "png"], accept_multiple_files=True)
else:
    uploaded_files = st.file_uploader("Sube la foto principal", type=["jpg", "png"], accept_multiple_files=False)
    if uploaded_files:
        uploaded_files = [uploaded_files] # Convertir a lista

# Vista previa
if uploaded_files:
    cant = len(uploaded_files)
    st.info(f"✅ {cant} foto(s) lista(s) para análisis.")
    
    cols = st.columns(3)
    for i, file in enumerate(uploaded_files[:3]):
        with cols[i]:
            image = Image.open(file)
            st.image(image, use_container_width=True)

    # --- 2. DATOS DEL INMUEBLE ---
    st.divider()
    st.write("#### 2. 📝 Detalles")

    col1, col2 = st.columns(2)
    
    # --- COLUMNA 1 ---
    with col1:
        operacion = st.radio("Operación", ["Venta", "Alquiler"], horizontal=True)
        
        lista_tipos = [
            "Casa", "Departamento", "Duplex", 
            "Terreno", "Quinta", "Estancia",
            "Penthouse", "Loft", "Monoambiente",
            "Oficina", "Local Comercial", "Galpón/Depósito", "Edificio"
        ]
        tipo = st.selectbox("Tipo de Propiedad", lista_tipos)
        
        ubicacion = st.text_input("Ubicación", placeholder="Ej: Villa Morra")
        placeholder_precio = "Gs mensuales" if operacion == "Alquiler" else "Gs / USD"
        precio = st.text_input("Precio", placeholder=placeholder_precio)
        
        st.write("---")
        if tipo_plan == "PREMIUM (Pro)":
            whatsapp = st.text_input("📞 WhatsApp (Link automático)", placeholder="0981...")
        else:
            whatsapp = st.text_input("📞 WhatsApp", placeholder="🔒 Solo PREMIUM", disabled=True)

    # --- COLUMNA 2 ---
    with col2:
        habs = st.number_input("Habitaciones", 1)
        banos = st.number_input("Baños", 1)
        
        st.write("**Extras Generales:**")
        quincho = st.checkbox("Quincho")
        piscina = st.checkbox("Piscina")
        cochera = st.checkbox("Cochera")

        inc_agua = False; inc_luz = False; inc_wifi = False; inc_aire = False; inc_ventilador = False

        if operacion == "Alquiler":
            st.write("---")
            st.write("**🔌 Incluye / Climatización:**")
            col_serv1, col_serv2 = st.columns(2)
            with col_serv1:
                inc_agua = st.checkbox("💧 Agua")
                inc_luz = st.checkbox("⚡ Luz")
                inc_aire = st.checkbox("❄️ Aire A.A.")
            with col_serv2:
                inc_wifi = st.checkbox("📶 Wifi")
                inc_ventilador = st.checkbox("💨 Ventilador")
        
        st.write("---")
        if tipo_plan == "PREMIUM (Pro)":
            st.caption("✅ **Visión PRO:** Analizando todas las fotos.")
        else:
            st.caption("⚠️ **Visión Básica:** Solo analiza la fachada.")

    # --- 3. BOTÓN GENERAR ---
    st.divider()
    btn_text = "✨ Redactar Anuncio Completo" if tipo_plan == "PREMIUM (Pro)" else "Generar Descripción Simple"
    
    if st.button(btn_text):
        if not ubicacion or not precio:
            st.warning("⚠️ Faltan datos básicos.")
        else:
            with st.spinner('🤖 Analizando fotos y redactando...'):
                try:
                    extras_list = []
                    if quincho: extras_list.append("Quincho")
                    if piscina: extras_list.append("Piscina")
                    if cochera: extras_list.append("Cochera")
                    txt_extras = ", ".join(extras_list) if extras_list else "Estándar"

                    servicios_list = []
                    if operacion == "Alquiler":
                        if inc_agua: servicios_list.append("Agua")
                        if inc_luz: servicios_list.append("Luz")
                        if inc_wifi: servicios_list.append("Internet Wifi")
                        if inc_aire: servicios_list.append("Aire A.A.")
                        if inc_ventilador: servicios_list.append("Ventiladores")
                    txt_servicios = ", ".join(servicios_list) if servicios_list else "No especificado"

                    prompt_text = f"""
                    Actúa como experto copywriter inmobiliario.
                    TAREA: Analiza las imágenes. Escribe anuncio de {operacion} de {tipo} en {ubicacion}.
                    Precio {precio}. {habs} habs, {banos} baños. Extras: {txt_extras}.
                    { 'Servicios: ' + txt_servicios if operacion == "Alquiler" else '' }
                    { 'LINK WHATSAPP: https://wa.me/595' + whatsapp if tipo_plan == "PREMIUM (Pro)" else '' }
                    Estructura: Título, Descripción Emocional Visual, Datos, Cierre.
                    """

                    content_content = [{"type": "text", "text": prompt_text}]
                    for file in uploaded_files:
                        img = Image.open(file)
                        b64 = encode_image(img)
                        content_content.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
                        })

                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": content_content}],
                        max_tokens=800,
                    )
                    
                    res_text = response.choices[0].message.content
                    st.success("¡Anuncio generado!")
                    st.text_area("Copia tu texto:", value=res_text, height=600)

                except Exception as e:
                    st.error(f"Error: {e}")
