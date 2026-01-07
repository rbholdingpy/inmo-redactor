import streamlit as st
from PIL import Image
import base64
import io
from openai import OpenAI

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Inmo-Redactor IA", page_icon="🏡", layout="centered")

# --- SIMULACIÓN DE SISTEMA DE USUARIOS (Barra Lateral) ---
with st.sidebar:
    st.header("⚙️ Panel de Control")
    tipo_plan = st.radio("Simular Plan del Usuario:", ["GRATIS (Free)", "PREMIUM (Pro)"])
    
    st.divider()
    if tipo_plan == "GRATIS (Free)":
        st.warning("🔒 Límite: 1 Foto por anuncio.")
    else:
        st.success("🔓 Modo Galería: Múltiples fotos activado.")

# --- API KEY ---
api_key = st.secrets.get("OPENAI_API_KEY")
if not api_key:
    st.error("⚠️ Falta la API Key en Secrets.")
    st.stop()
client = OpenAI(api_key=api_key)

# --- TÍTULO ---
st.title("🏡 Inmo-Redactor IA")
st.caption(f"Modo Actual: {tipo_plan}")

# --- FUNCIÓN PARA CODIFICAR IMÁGENES ---
def encode_image(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# --- 1. CARGA DE IMAGENES (Lógica Diferenciada) ---
st.write("#### 1. 📸 Fotos del Inmueble")

if tipo_plan == "PREMIUM (Pro)":
    uploaded_files = st.file_uploader("Sube todas las fotos (Fachada, Interior, Patio)", type=["jpg", "png"], accept_multiple_files=True)
else:
    uploaded_files = st.file_uploader("Sube la foto principal (Fachada)", type=["jpg", "png"], accept_multiple_files=False)
    # Si sube una, la convertimos en lista para que el código de abajo funcione igual
    if uploaded_files:
        uploaded_files = [uploaded_files] 

# Mostrar vista previa
if uploaded_files:
    cant = len(uploaded_files)
    st.info(f"✅ {cant} foto(s) cargada(s) para análisis.")
    
    # Mostramos las primeras 3 como ejemplo visual
    cols = st.columns(3)
    for i, file in enumerate(uploaded_files[:3]):
        with cols[i]:
            image = Image.open(file)
            st.image(image, use_container_width=True)

    # --- 2. FORMULARIO DE DATOS ---
    st.divider()
    st.write("#### 2. 📝 Detalles")

    col1, col2 = st.columns(2)
    
    with col1:
        operacion = st.radio("Operación", ["Venta", "Alquiler"], horizontal=True)
        tipo = st.selectbox("Tipo", ["Casa", "Departamento", "Quinta", "Terreno"])
        ubicacion = st.text_input("Ubicación", placeholder="Ej: Villa Morra")
        precio = st.text_input("Precio", placeholder="Gs o USD")
        
        # WhatsApp (Solo PRO)
        if tipo_plan == "PREMIUM (Pro)":
            whatsapp = st.text_input("📞 WhatsApp (Link automático)", placeholder="0981...")
        else:
            whatsapp = st.text_input("📞 WhatsApp", placeholder="🔒 Solo PREMIUM", disabled=True)

    with col2:
        habs = st.number_input("Habitaciones", 1)
        banos = st.number_input("Baños", 1)
        st.write("**Extras:**")
        quincho = st.checkbox("Quincho")
        piscina = st.checkbox("Piscina")
        
        # Visión IA (Información visual)
        if tipo_plan == "PREMIUM (Pro)":
            st.success(f"👁️ **Visión PRO activada:** La IA analizará las {cant} fotos para describir ambientes y materiales.")
        else:
            st.warning("👁️ **Visión Limitada:** La IA solo ve la fachada. Pásate a PRO para análisis de interiores.")

    # --- 3. BOTÓN DE ACCIÓN ---
    st.divider()
    btn_text = "✨ Redactar Anuncio Completo" if tipo_plan == "PREMIUM (Pro)" else "Generar Descripción Simple"
    
    if st.button(btn_text):
        if not ubicacion or not precio:
            st.warning("Faltan datos básicos.")
        else:
            with st.spinner('🤖 Analizando galería de fotos y redactando...'):
                try:
                    # PREPARAR EL MENSAJE PARA LA API
                    # 1. Texto del Prompt
                    prompt_text = f"""
                    Actúa como experto copywriter inmobiliario.
                    
                    TAREA:
                    1. Analiza TODAS las imágenes proporcionadas. Integra detalles de la fachada, el interior (pisos, luces, cocina) y el patio.
                    2. Escribe un anuncio persuasivo de {operacion} de {tipo} en {ubicacion}.
                    3. Precio: {precio}. {habs} habs, {banos} baños.
                    4. { 'Crea link de WhatsApp: https://wa.me/595' + whatsapp if tipo_plan == "PREMIUM (Pro)" else 'NO incluyas link de WhatsApp.' }
                    
                    ESTRUCTURA:
                    - Título Gancho (con Emojis).
                    - Descripción Emocional (Menciona lo que ves en las fotos: "Cocina con mesada de granito...", "Amplio patio con...").
                    - Lista de Características.
                    - Cierre.
                    """

                    # 2. Construir el contenido del mensaje (Texto + Lista de Imágenes)
                    content_content = [{"type": "text", "text": prompt_text}]
                    
                    # Recorremos cada foto subida, la codificamos y la agregamos al mensaje
                    for file in uploaded_files:
                        img = Image.open(file)
                        b64 = encode_image(img)
                        content_content.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
                        })

                    # 3. Llamada a la API
                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {
                                "role": "user",
                                "content": content_content
                            }
                        ],
                        max_tokens=800,
                    )
                    
                    res_text = response.choices[0].message.content
                    st.success("¡Anuncio generado con éxito!")
                    st.text_area("Copia tu texto:", value=res_text, height=600)
                    
                    if tipo_plan == "GRATIS (Free)":
                        st.info("💡 Consejo: Con el plan PRO podrías subir fotos de la cocina y los baños para que la IA los describa automáticamente.")

                except Exception as e:
                    st.error(f"Error: {e}")
