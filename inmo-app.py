import streamlit as st
from PIL import Image
import base64
import io
from openai import OpenAI

# Configuración de la página
st.set_page_config(page_title="Inmo-Redactor IA", page_icon="🏠")

# Título y Subtítulo
st.title("🏠 Inmo-Redactor IA (Versión OpenAI)")
st.write("Sube una foto y deja que la Inteligencia Artificial escriba el anuncio perfecto.")

# --- BARRA LATERAL (Clave API) ---
# Intentamos obtener la clave de los secretos de Streamlit
api_key = st.secrets.get("OPENAI_API_KEY")

if not api_key:
    st.error("⚠️ No se detectó la clave de OpenAI. Configúrala en 'Secrets'.")
    st.stop()

client = OpenAI(api_key=api_key)

# --- PASO 1: CARGA DE IMAGEN ---
st.header("1. 📸 Sube la foto del inmueble")
uploaded_file = st.file_uploader("Elige una imagen (JPG o PNG)", type=["jpg", "jpeg", "png"])

# Función para convertir imagen a base64 (necesario para OpenAI)
def encode_image(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

if uploaded_file is not None:
    # Mostrar la imagen
    image = Image.open(uploaded_file)
    st.image(image, caption="Imagen cargada", use_container_width=True)
    
    # Procesar imagen para OpenAI
    base64_image = encode_image(image)

    # --- PASO 2: DATOS BÁSICOS ---
    st.divider()
    st.header("2. 📝 Datos Básicos")

    col1, col2 = st.columns(2)
    with col1:
        ubicacion = st.text_input("📍 Ubicación / Barrio", placeholder="Ej: Villa Morra, Asunción")
        precio = st.text_input("💰 Precio", placeholder="Ej: 750.000.000 Gs")
    with col2:
        tipo_inmueble = st.selectbox("🏗️ Tipo de Inmueble", ["Casa", "Departamento", "Terreno", "Oficina", "Duplex"])
        objetivo = st.radio("🎯 Objetivo del Texto", ["Venta Rápida (Urgente)", "Lujo/Prestigio", "Oportunidad de Inversión"])

    # --- PASO 3: GENERAR ---
    st.divider()
    if st.button("✨ Generar Descripción Vendedora"):
        
        if not ubicacion or not precio:
            st.warning("⚠️ Por favor completa la ubicación y el precio.")
        else:
            with st.spinner('🤖 Analizando la foto con GPT-4o...'):
                try:
                    # El Prompt Maestro
                    prompt_text = f"""
                    Actúa como un experto copywriter inmobiliario en Paraguay.
                    Tu tarea es escribir un anuncio persuasivo para redes sociales basado en la imagen que ves y estos datos:
                    
                    - Tipo: {tipo_inmueble}
                    - Ubicación: {ubicacion}
                    - Precio: {precio}
                    - Enfoque: {objetivo}

                    INSTRUCCIONES:
                    1. Analiza visualmente la imagen (luz, piso, espacios) y úsalo en la descripción.
                    2. Usa un tono cercano pero profesional.
                    3. Estructura: Gancho atractivo, Características clave (visuales + datos), y Llamada a la acción.
                    4. Usa emojis estratégicos y hashtags relevantes para Paraguay.
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
                        max_tokens=500,
                    )

                    # Resultado
                    generated_text = response.choices[0].message.content
                    st.success("¡Descripción generada con éxito!")
                    st.text_area("Copia tu texto aquí:", value=generated_text, height=400)
                
                except Exception as e:
                    st.error(f"Ocurrió un error: {e}")
                    st.info("Nota: Verifica que tengas saldo/créditos en tu cuenta de OpenAI (Billing).")
