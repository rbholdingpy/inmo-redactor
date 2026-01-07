import streamlit as st
from PIL import Image
import base64
import io
from openai import OpenAI

# Configuración de la página
st.set_page_config(page_title="Inmo-Redactor IA", page_icon="🏠")

# Título y Subtítulo
st.title("🏠 Inmo-Redactor IA (Versión Pro)")
st.write("Sube una foto y completa los detalles para crear el anuncio perfecto.")

# --- BARRA LATERAL (Clave API) ---
api_key = st.secrets.get("OPENAI_API_KEY")

if not api_key:
    st.error("⚠️ No se detectó la clave de OpenAI. Configúrala en 'Secrets'.")
    st.stop()

client = OpenAI(api_key=api_key)

# --- PASO 1: CARGA DE IMAGEN ---
st.header("1. 📸 Sube la foto del inmueble")
uploaded_file = st.file_uploader("Elige una imagen principal", type=["jpg", "jpeg", "png"])

def encode_image(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Imagen cargada", use_container_width=True)
    base64_image = encode_image(image)

    # --- PASO 2: DATOS BÁSICOS ---
    st.divider()
    st.header("2. 📝 Detalles de la Propiedad")

    # Columnas para organizar mejor los datos
    col1, col2 = st.columns(2)

    with col1:
        ubicacion = st.text_input("📍 Ubicación / Barrio", placeholder="Ej: Villa Morra, Asunción")
        precio = st.text_input("💰 Precio", placeholder="Ej: 750.000.000 Gs")
        tipo_inmueble = st.selectbox("🏗️ Tipo de Inmueble", ["Casa", "Departamento", "Terreno", "Duplex", "Oficina"])
        m2 = st.text_input("📏 Superficie (m2)", placeholder="Ej: 360 m2 terreno / 200 m2 construidos")

    with col2:
        habitaciones = st.number_input("🛏️ Habitaciones", min_value=0, value=3, step=1)
        banos = st.number_input("🚿 Baños", min_value=0, value=2, step=1)
        st.write("**✨ Amenities / Extras:**")
        tiene_quincho = st.checkbox("🍖 Tiene Quincho")
        tiene_piscina = st.checkbox("🏊 Tiene Piscina")
        tiene_cochera = st.checkbox("🚗 Tiene Cochera/Garage")

    # Objetivo de venta (fuera de las columnas para destacar)
    st.write("---")
    objetivo = st.radio("🎯 Estrategia de Venta", 
                        ["Venta Rápida (Urgente)", "Lujo y Exclusividad", "Oportunidad de Inversión", "Ideal Primera Vivienda"],
                        horizontal=True)

    # --- PASO 3: GENERAR ---
    st.divider()
    if st.button("✨ Generar Descripción Vendedora"):
        
        if not ubicacion or not precio:
            st.warning("⚠️ Por favor completa al menos la ubicación y el precio.")
        else:
            with st.spinner('🤖 La IA está redactando tu anuncio...'):
                try:
                    # Preparamos el texto de los extras
                    extras = []
                    if tiene_quincho: extras.append("Quincho con parrilla")
                    if tiene_piscina: extras.append("Piscina")
                    if tiene_cochera: extras.append("Estacionamiento")
                    lista_extras = ", ".join(extras) if extras else "No especificado"

                    # El Prompt Actualizado con los nuevos datos
                    prompt_text = f"""
                    Actúa como un copywriter inmobiliario experto en el mercado de Paraguay.
                    Escribe un anuncio para Instagram/Facebook altamente persuasivo.

                    DATOS DEL INMUEBLE:
                    - Tipo: {tipo_inmueble}
                    - Ubicación: {ubicacion}
                    - Precio: {precio}
                    - Dimensiones: {m2}
                    - Habitaciones: {habitaciones}
                    - Baños: {banos}
                    - Extras importantes: {lista_extras}
                    - Enfoque de venta: {objetivo}

                    INSTRUCCIONES DE REDACCIÓN:
                    1. GANCHO: Empieza con una frase corta que impacte o una pregunta.
                    2. CUERPO: Describe la propiedad integrando lo que ves en la foto (luz, estilo) con los datos técnicos (habitaciones, quincho, etc.). NO hagas una simple lista aburrida, cuenta una historia de cómo se vive ahí.
                    3. Si tiene QUINCHO o PISCINA, destácalo mucho (es clave en Paraguay).
                    4. CIERRE: Llamada a la acción clara para agendar visita.
                    5. FORMATO: Usa emojis, párrafos cortos y una lista de características al final para lectura rápida.
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
                    st.success("¡Anuncio listo para copiar!")
                    st.text_area("Copia tu texto aquí:", value=generated_text, height=500)
                
                except Exception as e:
                    st.error(f"Error: {e}")
