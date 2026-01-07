import streamlit as st
import google.generativeai as genai
from PIL import Image
import os

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Inmo-Redactor IA",
    page_icon="🏠",
    layout="centered"
)

# --- GESTIÓN DE LA CLAVE DE SUSCRIPCIÓN ---
# Esta es la contraseña que le darás a tus clientes que paguen.
# Cámbiala cada mes (ej. "FEBRERO2026")
CLAVE_MAESTRA = "INICIO2025" 

def verificar_acceso():
    """Función para bloquear la app con contraseña"""
    if "acceso_concedido" not in st.session_state:
        st.session_state["acceso_concedido"] = False

    if not st.session_state["acceso_concedido"]:
        st.markdown("## 🔒 Acceso Privado para Agentes")
        clave_ingresada = st.text_input("Introduce tu Clave de Suscriptor:", type="password")
        
        if st.button("Ingresar"):
            if clave_ingresada == CLAVE_MAESTRA:
                st.session_state["acceso_concedido"] = True
                st.rerun() # Recarga la página para mostrar la app
            else:
                st.error("🚫 Clave incorrecta. Contacta a soporte para renovar tu suscripción.")
        return False
    else:
        return True

# --- LÓGICA DE LA APLICACIÓN ---
if verificar_acceso():
    
    # Título y Cabecera
    st.title("🏠 Inmo-Redactor IA")
    st.markdown("""
    **Transforma fotos en dinero.** Sube la imagen de tu propiedad y obtén 
    descripciones persuasivas en segundos.
    """)
    st.markdown("---")

    # Intentamos obtener la API Key de los "Secretos" de Streamlit
    # Si estás probando en tu PC, asegúrate de configurar esto.
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
        api_lista = True
    except:
        st.error("⚠️ Error de Configuración: No se encontró la API Key en el sistema.")
        st.info("Nota para el dueño: Configura 'GOOGLE_API_KEY' en los Secrets de Streamlit Cloud.")
        api_lista = False

    if api_lista:
        # COLUMNA 1: LA FOTO
        st.subheader("1. 📸 La Propiedad")
        archivo_foto = st.file_uploader("Sube la foto aquí (JPG/PNG)", type=["jpg", "jpeg", "png"])
        
        if archivo_foto:
            imagen = Image.open(archivo_foto)
            st.image(imagen, caption="Imagen cargada", use_column_width=True)

        st.markdown("---")

        # COLUMNA 2: LOS DATOS
        st.subheader("2. 📝 Datos Básicos")
        col1, col2 = st.columns(2)
        
        with col1:
            ubicacion = st.text_input("📍 Ubicación / Barrio", placeholder="Ej: Villa Morra, Asunción")
            precio = st.text_input("💰 Precio", placeholder="Ej: 150.000 USD")
        
        with col2:
            tipo = st.selectbox("🏗️ Tipo de Inmueble", ["Casa", "Departamento", "Terreno", "Oficina/Comercial"])
            objetivo = st.radio("🎯 Objetivo del Texto", ["Venta Rápida (Urgente)", "Lujo/Prestigio", "Oportunidad de Inversión"])

        # BOTÓN DE ACCIÓN
        st.markdown("###")
        if st.button("✨ Generar Descripción Vendedora", type="primary"):
            if not archivo_foto:
                st.warning("✋ Por favor sube una foto primero.")
            else:
                with st.spinner('🤖 La IA está analizando la foto y escribiendo el copy...'):
                    try:
                        # Configuración del modelo (Gemini 1.5 Flash es rápido y barato)
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        
                        prompt = f"""
                        Eres un experto copywriter inmobiliario con 20 años de experiencia.
                        Tu objetivo es escribir un anuncio para redes sociales (Instagram/Facebook) y portales web.

                        DATOS DEL INMUEBLE:
                        - Tipo: {tipo}
                        - Ubicación: {ubicacion}
                        - Precio: {precio}
                        - Enfoque de venta: {objetivo}

                        INSTRUCCIONES:
                        1. Analiza la imagen adjunta visualmente. Describe lo que ves (iluminación, suelo, espacios, calidad).
                        2. Combina lo visual con los datos proporcionados.
                        3. Usa un tono persuasivo, profesional pero cercano.
                        4. Usa emojis estratégicos.
                        5. Incluye 3 hashtags relevantes para Paraguay.
                        6. El texto debe estar listo para copiar y pegar.
                        """
                        
                        response = model.generate_content([prompt, imagen])
                        
                        st.success("✅ ¡Descripción Generada con Éxito!")
                        st.text_area("Copia tu texto aquí:", value=response.text, height=350)
                        
                    except Exception as e:

                        st.error(f"Ocurrió un error al conectar con Google: {e}")


