import streamlit as st
from PIL import Image
import base64
import io
from openai import OpenAI

# Configuración de la página
st.set_page_config(page_title="Inmo-Redactor IA", page_icon="🏡")

# Título
st.title("🏡 Inmo-Redactor IA (Pro)")
st.write("Sube una foto y completa los datos para generar el anuncio.")

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

    # NUEVO: Tipo de Operación (Venta o Alquiler)
    tipo_operacion = st.radio("💼 ¿Es Venta o Alquiler?", ["Venta", "Alquiler"], horizontal=True)

    col1, col2 = st.columns(2)

    with col1:
        # Agregamos "Quinta" a la lista
        tipo_inmueble = st.selectbox("🏗️ Tipo de Inmueble", ["Casa", "Departamento", "Quinta", "Terreno", "Duplex", "Oficina", "Local Comercial"])
        ubicacion = st.text_input("📍 Ubicación / Barrio", placeholder="Ej: San Bernardino, Zona Alta")
        
        # El precio cambia el placeholder según si es venta o alquiler
        placeholder_precio = "Ej: 750.000.000 Gs" if tipo_operacion == "Venta" else "Ej: 3.500.000 Gs mensuales"
        precio = st.text_input("💰 Precio", placeholder=placeholder_precio)
        
        m2 = st.text_input("📏 Superficie (m2)", placeholder="Ej: 2.000 m2 de terreno")

    with col2:
        habitaciones = st.number_input("🛏️ Habitaciones", min_value=0, value=3, step=1)
        banos = st.number_input("🚿 Baños", min_value=0, value=2, step=1)
        
        st.write("**✨ Amenities / Extras:**")
        tiene_quincho = st.checkbox("🍖 Tiene Quincho")
        tiene_piscina = st.checkbox("🏊 Tiene Piscina")
        tiene_cochera = st.checkbox("🚗 Tiene Cochera/Garage")
        amoblado = st.checkbox("🛋️ Está Amoblado")

    # Estrategia según la operación
    st.write("---")
    st.write("🎯 **Enfoque del anuncio:**")
    
    if tipo_operacion == "Venta":
        objetivo = st.radio("Estrategia de Venta", 
                            ["Venta Rápida (Urgente)", "Lujo y Exclusividad", "Oportunidad de Inversión", "Ideal Primera Vivienda"],
                            horizontal=True, label_visibility="collapsed")
    else: # Alquiler
        objetivo = st.radio("Estrategia de Alquiler", 
                            ["Alquiler Vacacional/Fin de Semana", "Alquiler Anual Familiar", "Para Estudiantes/Ejecutivos", "Lujo Temporal"],
                            horizontal=True, label_visibility="collapsed")

    # --- PASO 3: GENERAR ---
    st.divider()
    texto_boton = f"✨ Redactar Anuncio de {tipo_operacion}"
    
    if st.button(texto_boton):
        
        if not ubicacion or not precio:
            st.warning("⚠️ Por favor completa la ubicación y el precio.")
        else:
            with st.spinner('🤖 La IA está escribiendo el copy...'):
                try:
                    # Preparar extras
                    extras = []
                    if tiene_quincho: extras.append("Quincho con parrilla")
                    if tiene_piscina: extras.append("Piscina")
                    if tiene_cochera: extras.append("Estacionamiento")
                    if amoblado: extras.append("Totalmente amoblado")
                    lista_extras = ", ".join(extras) if extras else "No especificado"

                    # Prompt Dinámico
                    prompt_text = f"""
                    Actúa como un copywriter inmobiliario experto en Paraguay.
                    Escribe un anuncio persuasivo para redes sociales para una operación de: {tipo_operacion.upper()}.

                    DATOS:
                    - Inmueble: {tipo_inmueble}
                    - Ubicación: {ubicacion}
                    - Precio: {precio}
                    - Dimensiones: {m2}
                    - Habitaciones: {habitaciones} | Baños: {banos}
                    - Extras: {lista_extras}
                    - Enfoque: {objetivo}

                    INSTRUCCIONES:
                    1. Adapta el tono: Si es 'Venta', enfócate en la propiedad y la inversión. Si es 'Alquiler', enfócate en la experiencia de vivir ahí o vacacionar.
                    2. Si es QUINTA: Destaca el relax, la naturaleza y el espacio al aire libre.
                    3. Usa estructura: Gancho emocional, Descripción detallada (visual + datos), y Llamada a la acción.
                    4. Incluye emojis y hashtags de Paraguay (#BienesRaicesPy, etc).
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
                        max_tokens=600,
                    )

                    generated_text = response.choices[0].message.content
                    st.success("¡Anuncio generado!")
                    st.text_area("Copia tu texto aquí:", value=generated_text, height=500)
                
                except Exception as e:
                    st.error(f"Error: {e}")
