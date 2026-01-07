import streamlit as st
from PIL import Image
import base64
import io
from openai import OpenAI

# Configuración de la página
st.set_page_config(page_title="Inmo-Redactor IA", page_icon="🏡")

# Título
st.title("🏡 Inmo-Redactor IA (Visión Pro)")
st.write("Sube una foto y completa los datos. La IA detectará el estilo y colores.")

# --- BARRA LATERAL (Clave API) ---
api_key = st.secrets.get("OPENAI_API_KEY")

if not api_key:
    st.error("⚠️ No se detectó la clave de OpenAI. Configúrala en 'Secrets'.")
    st.stop()

client = OpenAI(api_key=api_key)

# --- PASO 1: CARGA DE IMAGEN ---
st.header("1. 📸 Sube la foto")
uploaded_file = st.file_uploader("Elige una imagen principal", type=["jpg", "jpeg", "png"])

def encode_image(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Imagen cargada", use_container_width=True)
    base64_image = encode_image(image)

    # --- PASO 2: DATOS DE LA PROPIEDAD ---
    st.divider()
    st.header("2. 📝 Detalles del Inmueble")

    # Selector principal
    tipo_operacion = st.radio("💼 ¿Es Venta o Alquiler?", ["Venta", "Alquiler"], horizontal=True)

    col1, col2 = st.columns(2)

    with col1:
        tipo_inmueble = st.selectbox("🏗️ Tipo de Inmueble", ["Casa", "Departamento", "Quinta", "Terreno", "Duplex", "Oficina", "Local Comercial"])
        ubicacion = st.text_input("📍 Ubicación / Barrio", placeholder="Ej: Villa Morra")
        
        placeholder_precio = "Ej: 750.000.000 Gs" if tipo_operacion == "Venta" else "Ej: 3.500.000 Gs"
        precio = st.text_input("💰 Precio", placeholder=placeholder_precio)
        
        m2 = st.text_input("📏 Superficie", placeholder="Ej: 360 m2")
        
        # NUEVO: Campo de WhatsApp
        whatsapp = st.text_input("📞 Tu WhatsApp (sin espacios)", placeholder="Ej: 0981123456")

    with col2:
        habitaciones = st.number_input("🛏️ Habitaciones", min_value=0, value=2)
        banos = st.number_input("🚿 Baños", min_value=0, value=1)
        
        st.write("**✨ Amenities y Extras:**")
        tiene_quincho = st.checkbox("🍖 Tiene Quincho")
        tiene_piscina = st.checkbox("🏊 Tiene Piscina")
        tiene_cochera = st.checkbox("🚗 Cochera")
        amoblado = st.checkbox("🛋️ Amoblado")

        # --- SECCIÓN EXCLUSIVA PARA ALQUILER ---
        inc_agua = False
        inc_luz = False
        inc_wifi = False
        inc_cable = False
        inc_aire = False
        inc_ventilador = False

        if tipo_operacion == "Alquiler":
            st.markdown("---")
            st.write("**🔌 Incluye / Equipamiento:**")
            col_serv1, col_serv2 = st.columns(2)
            with col_serv1:
                inc_agua = st.checkbox("💧 Agua")
                inc_luz = st.checkbox("⚡ Luz")
                inc_aire = st.checkbox("❄️ Aire Acondicionado")
            with col_serv2:
                inc_wifi = st.checkbox("📶 Wifi")
                inc_cable = st.checkbox("📺 TV Cable")
                inc_ventilador = st.checkbox("💨 Ventilador")

    # Estrategia de venta
    st.write("---")
    st.write("🎯 **Enfoque:**")
    
    if tipo_operacion == "Venta":
        objetivo = st.radio("Estrategia", ["Venta Rápida", "Lujo/Prestigio", "Inversión", "Primera Vivienda"], horizontal=True, label_visibility="collapsed")
    else: 
        objetivo = st.radio("Estrategia", ["Vacacional", "Familiar Anual", "Estudiantes/Ejecutivos", "Temporal"], horizontal=True, label_visibility="collapsed")

    # --- PASO 3: GENERAR ---
    st.divider()
    
    if st.button(f"✨ Analizar Foto y Escribir"):
        
        if not ubicacion or not precio:
            st.warning("⚠️ Falta ubicación o precio.")
        else:
            with st.spinner('👀 La IA está analizando colores, materiales y estilo...'):
                try:
                    # Preparar listas
                    extras = []
                    if tiene_quincho: extras.append("Quincho")
                    if tiene_piscina: extras.append("Piscina")
                    if tiene_cochera: extras.append("Cochera")
                    if amoblado: extras.append("Amoblado")
                    
                    servicios = []
                    if tipo_operacion == "Alquiler":
                        if inc_agua: servicios.append("Agua")
                        if inc_luz: servicios.append("Luz")
                        if inc_wifi: servicios.append("Wifi")
                        if inc_aire: servicios.append("Aire Acondicionado")
                    
                    txt_extras = ", ".join(extras) if extras else "Standard"
                    txt_servicios = ", ".join(servicios) if servicios else "Sin servicios extra"

                    # Prompt "OJO DE ÁGUILA"
                    prompt_text = f"""
                    Actúa como un experto agente inmobiliario.
                    
                    TU MISIÓN PRINCIPAL: Analizar la imagen adjunta con precisión visual.
                    NO inventes descripciones genéricas. Mira la foto y detecta:
                    1. ¿De qué color es la fachada? (Blanca, ladrillo, gris, tonos tierra).
                    2. ¿Qué estilo tiene? (Minimalista, colonial, moderno, rústico, clásico).
                    3. ¿Qué materiales ves? (Piedra, madera, blindex, tejas, losa).
                    4. ¿Cómo es la iluminación o el jardín?

                    Usa esos detalles visuales REALES para escribir un anuncio de {tipo_operacion}.

                    DATOS TÉCNICOS:
                    - Inmueble: {tipo_inmueble} en {ubicacion}
                    - Precio: {precio}
                    - Superficie: {m2}
                    - {habitaciones} Habs | {banos} Baños
                    - Extras: {txt_extras}
                    - Servicios (si es alquiler): {txt_servicios}
                    - Contacto WhatsApp: {whatsapp}

                    ESTRUCTURA DEL ANUNCIO:
                    1. TÍTULO: Atractivo y con emojis.
                    2. DESCRIPCIÓN VISUAL: Aquí es donde describes lo que ves en la foto (Colores, estilo, fachada). Véndelo con emoción.
                    3. DETALLES TÉCNICOS: Lista rápida de comodidades.
                    4. SI ES ALQUILER CON MUEBLES/SERVICIOS: Destácalo.
                    5. CIERRE CON WHATSAPP: "📲 Agenda tu visita ahora: https://wa.me/595{whatsapp.lstrip('0')}" (Formatea el link para Paraguay).

                    Tono: Profesional, paraguayo y persuasivo.
                    """

                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt_text},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/jpeg;base64,{base64_image}"
                                        },
                                    },
                                ],
                            }
                        ],
                        max_tokens=700,
                    )

                    generated_text = response.choices[0].message.content
                    st.success("¡Análisis visual completado!")
                    st.text_area("Anuncio generado:", value=generated_text, height=600)
                
                except Exception as e:
                    st.error(f"Error: {e}")
