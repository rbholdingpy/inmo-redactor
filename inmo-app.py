import streamlit as st
from PIL import Image
import base64
import io
from openai import OpenAI

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Inmo-Redactor IA", page_icon="🏡", layout="centered")

# --- SIMULACIÓN DE SISTEMA DE USUARIOS (Barra Lateral) ---
with st.sidebar:
    st.header("⚙️ Panel de Control (Admin)")
    st.write("Usa esto para probar cómo lo ve tu cliente:")
    # Esto simula si el usuario pagó o no
    tipo_plan = st.radio("Simular Plan del Usuario:", ["GRATIS (Free)", "PREMIUM (Pro)"])
    
    st.divider()
    st.info("💡 **Estrategia:** En el plan GRATIS, bloqueamos funciones clave para que el usuario desee comprar el Premium.")

# --- API KEY ---
api_key = st.secrets.get("OPENAI_API_KEY")
if not api_key:
    st.error("⚠️ Falta la API Key en Secrets.")
    st.stop()
client = OpenAI(api_key=api_key)

# --- TÍTULO PRINCIPAL ---
st.title("🏡 Inmo-Redactor IA")
if tipo_plan == "GRATIS (Free)":
    st.caption("Plan Actual: 🌑 Básico (Funciones limitadas)")
else:
    st.caption("Plan Actual: 🌟 PREMIUM (Todo desbloqueado)")

# --- 1. CARGA DE IMAGEN ---
st.write("#### 1. 📸 Sube la foto del inmueble")
uploaded_file = st.file_uploader("Imagen principal", type=["jpg", "jpeg", "png"])

def encode_image(image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption="Vista previa", use_container_width=True)
    base64_image = encode_image(image)

    # --- 2. FORMULARIO DE DATOS ---
    st.divider()
    st.write("#### 2. 📝 Detalles")

    col1, col2 = st.columns(2)
    
    with col1:
        operacion = st.radio("Operación", ["Venta", "Alquiler"], horizontal=True)
        tipo = st.selectbox("Tipo", ["Casa", "Departamento", "Quinta", "Terreno"])
        ubicacion = st.text_input("Ubicación", placeholder="Ej: Villa Morra")
        precio = st.text_input("Precio", placeholder="Gs o USD")
        
        # --- ESTRATEGIA: BLOQUEO DE WHATSAPP ---
        st.write("---")
        if tipo_plan == "PREMIUM (Pro)":
            whatsapp = st.text_input("📞 Tu WhatsApp (Link automático)", placeholder="0981...")
        else:
            whatsapp = st.text_input("📞 Tu WhatsApp", placeholder="🔒 Solo usuarios PREMIUM", disabled=True)
            st.caption("🔒 *Pásate a PRO para generar links de contacto automáticos.*")

    with col2:
        habs = st.number_input("Habitaciones", 1)
        banos = st.number_input("Baños", 1)
        st.write("**Extras:**")
        quincho = st.checkbox("Quincho")
        piscina = st.checkbox("Piscina")
        
        # --- ESTRATEGIA: VISIÓN IA ---
        st.write("---")
        st.write("**👁️ Inteligencia Visual:**")
        if tipo_plan == "PREMIUM (Pro)":
            vision_mode = st.checkbox("Activar Análisis de Estilo y Materiales", value=True)
            st.caption("✅ La IA detectará colores y acabados.")
        else:
            vision_mode = st.checkbox("Análisis Visual (Estilos/Materiales)", value=False, disabled=True)
            st.caption("🔒 *Solo PRO: La IA describe lo que ve en la foto.*")

    # --- 3. BOTÓN DE ACCIÓN ---
    st.divider()
    btn_text = "✨ Generar Descripción PRO" if tipo_plan == "PREMIUM (Pro)" else "Generar Descripción Básica"
    
    if st.button(btn_text):
        if not ubicacion or not precio:
            st.warning("Faltan datos básicos (Ubicación o Precio).")
        else:
            with st.spinner('🤖 Redactando...'):
                try:
                    # PROMPT ESTRATÉGICO
                    extras_txt = "Quincho, Piscina" if quincho and piscina else "Estándar"
                    
                    if tipo_plan == "PREMIUM (Pro)":
                        # --- PROMPT PRO (CON VISIÓN) ---
                        prompt = f"""
                        Actúa como experto inmobiliario.
                        1. MIRA la foto y describe materiales, iluminación y estilo (Vision activada).
                        2. Redacta un anuncio persuasivo de {operacion} de {tipo} en {ubicacion}.
                        3. Precio: {precio}. {habs} habs, {banos} baños. Extras: {extras_txt}.
                        4. CIERRE: Crea un link directo a WhatsApp: https://wa.me/595{whatsapp}
                        5. Usa emojis y tono vendedor profesional.
                        """
                    else:
                        # --- PROMPT GRATIS (GENÉRICO) ---
                        prompt = f"""
                        Actúa como vendedor inmobiliario.
                        Escribe un anuncio breve de {operacion} de {tipo} en {ubicacion}.
                        Precio: {precio}. {habs} habs, {banos} baños.
                        NO analices la foto en detalle, usa una descripción estándar.
                        NO incluyas links de contacto (no tienes el número).
                        Al final, agrega OBLIGATORIAMENTE esta firma:
                        "🚀 Descripción creada gratis con Inmo-Redactor IA. ¡Crea la tuya aquí!"
                        """

                    response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {
                                        "type": "image_url",
                                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                                    },
                                ],
                            }
                        ],
                        max_tokens=600,
                    )
                    
                    res_text = response.choices[0].message.content
                    st.success("¡Anuncio generado!")
                    st.text_area("Copia tu texto:", value=res_text, height=500)
                    
                    if tipo_plan == "GRATIS (Free)":
                        st.info("👀 ¿Viste lo que te perdiste? Los usuarios PRO obtienen análisis visual de la foto y link de WhatsApp automático.")

                except Exception as e:
                    st.error(f"Error: {e}")
