import streamlit as st
from PIL import Image
import base64
import io
from openai import OpenAI

# Configuración de la página
st.set_page_config(page_title="Inmo-Redactor IA", page_icon="🏡")

# Título
st.title("🏡 Inmo-Redactor IA (Pro)")
st.write("Sube una foto y completa los datos para generar el anuncio perfecto.")

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
        ubicacion = st.text_input("📍 Ubicación / Barrio", placeholder="Ej: Villa Morra / San Bernardino")
        
        # Placeholder dinámico según operación
        placeholder_precio = "Ej: 750.000.000 Gs" if tipo_operacion == "Venta" else "Ej: 3.500.000 Gs (IVA Incluido)"
        precio = st.text_input("💰 Precio", placeholder=placeholder_precio)
        
        m2 = st.text_input("📏 Superficie (m2)", placeholder="Ej: 200 m2 propios")

    with col2:
        habitaciones = st.number_input("🛏️ Habitaciones", min_value=0, value=2, step=1)
        banos = st.number_input("🚿 Baños", min_value=0, value=1, step=1)
        
        st.write("**✨ Amenities y Extras:**")
        tiene_quincho = st.checkbox("🍖 Tiene Quincho")
        tiene_piscina = st.checkbox("🏊 Tiene Piscina")
        tiene_cochera = st.checkbox("🚗 Cochera/Garage")
        amoblado = st.checkbox("🛋️ Amoblado")

        # --- SECCIÓN EXCLUSIVA PARA ALQUILER ---
        inc_agua = False
        inc_luz = False
        inc_wifi = False
        inc_cable = False

        if tipo_operacion == "Alquiler":
            st.markdown("---")
            st.write("**🔌 Servicios Incluidos en el precio:**")
            col_serv1, col_serv2 = st.columns(2)
            with col_serv1:
                inc_agua = st.checkbox("💧 Agua")
                inc_luz = st.checkbox("⚡ Luz")
            with col_serv2:
                inc_wifi = st.checkbox("📶 Wifi")
                inc_cable = st.checkbox("📺 TV Cable")

    # Estrategia de venta
    st.write("---")
    st.write("🎯 **Enfoque del anuncio:**")
    
    if tipo_operacion == "Venta":
        objetivo = st.radio("Estrategia", 
                            ["Venta Rápida (Urgente)", "Lujo y Exclusividad", "Oportunidad de Inversión", "Ideal Primera Vivienda"],
                            horizontal=True, label_visibility="collapsed")
    else: # Alquiler
        objetivo = st.radio("Estrategia", 
                            ["Alquiler Vacacional/Fin de Semana", "Alquiler Anual Familiar", "Para Estudiantes/Ejecutivos", "Todo Incluido (Temporal)"],
                            horizontal=True, label_visibility="collapsed")

    # --- PASO 3: GENERAR ---
    st.divider()
    
    if st.button(f"✨ Redactar Anuncio de {tipo_operacion}"):
        
        if not ubicacion or not precio:
            st.warning("⚠️ Por favor completa ubicación y precio.")
        else:
            with st.spinner('🤖 La IA está creando tu anuncio...'):
                try:
                    # Recopilamos Extras Generales
                    extras = []
                    if tiene_quincho: extras.append("Quincho con parrilla")
                    if tiene_piscina: extras.append("Piscina")
                    if tiene_cochera: extras.append("Cochera")
                    if amoblado: extras.append("Amoblado")
                    
                    # Recopilamos Servicios (Solo si es alquiler)
                    servicios = []
                    if tipo_operacion == "Alquiler":
                        if inc_agua: servicios.append("Agua")
                        if inc_luz: servicios.append("Luz")
                        if inc_wifi: servicios.append("Internet Wifi")
                        if inc_cable: servicios.append("TV Cable")
                    
                    texto_extras = ", ".join(extras) if extras else "No especificado"
                    texto_servicios = ", ".join(servicios) if servicios else "No incluye servicios extra"

                    # Prompt Dinámico
                    prompt_text = f"""
                    Actúa como un copywriter inmobiliario experto en Paraguay.
                    Escribe un anuncio para Instagram/Facebook para: {tipo_operacion.upper()}.

                    DATOS:
                    - Inmueble: {tipo_inmueble}
                    - Ubicación: {ubicacion}
                    - Precio: {precio}
                    - Dimensiones: {m2}
                    - Habitaciones: {habitaciones} | Baños: {banos}
                    - Amenities: {texto_extras}
                    - SERVICIOS INCLUIDOS: {texto_servicios} (Si la lista no está vacía, DESTÁCALO como un gran beneficio de ahorro).
                    - Enfoque: {objetivo}

                    INSTRUCCIONES:
                    1. Si incluye servicios (Luz, Agua, Wifi), véndelo como "Olvídate de pagar facturas extra" o "Entra a vivir ya".
                    2. Estructura visual: Título gancho, Descripción emotiva, Lista de beneficios con emojis, Precio y Contacto.
                    3. Tono paraguayo profesional (cercano).
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
                        max_tokens=650,
                    )

                    generated_text = response.choices[0].message.content
                    st.success("¡Anuncio generado!")
                    st.text_area("Copia tu texto aquí:", value=generated_text, height=550)
                
                except Exception as e:
                    st.error(f"Error: {e}")
