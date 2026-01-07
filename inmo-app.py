import streamlit as st
from PIL import Image
import base64
import io
from openai import OpenAI

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Inmo-Redactor IA", page_icon="🏡", layout="centered")

# --- BARRA LATERAL (SIMULADOR DE PLANES) ---
with st.sidebar:
    st.header("⚙️ Panel de Control")
    tipo_plan = st.radio("Simular Plan del Usuario:", ["GRATIS (Free)", "PREMIUM (Pro)"])
    
    st.divider()
    if tipo_plan == "GRATIS (Free)":
        st.warning("🔒 Límite: 1 Foto. Sin análisis de servicios.")
    else:
        st.success("🔓 Modo PRO: Galería de fotos + WhatsApp + Análisis Completo.")

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

# --- 1. CARGA DE IMAGENES ---
st.write("#### 1. 📸 Fotos del Inmueble")

if tipo_plan == "PREMIUM (Pro)":
    uploaded_files = st.file_uploader("Sube la galería completa (Fachada, Interior, Patio)", type=["jpg", "png"], accept_multiple_files=True)
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
    
    # --- COLUMNA 1: DATOS GENERALES ---
    with col1:
        operacion = st.radio("Operación", ["Venta", "Alquiler"], horizontal=True)
        
        # === LISTA DE TIPOS AMPLIADA ===
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
        
        # WhatsApp (Lógica Pro)
        st.write("---")
        if tipo_plan == "PREMIUM (Pro)":
            whatsapp = st.text_input("📞 WhatsApp (Link automático)", placeholder="0981...")
        else:
            whatsapp = st.text_input("📞 WhatsApp", placeholder="🔒 Solo PREMIUM", disabled=True)

    # --- COLUMNA 2: AMENITIES Y SERVICIOS ---
    with col2:
        habs = st.number_input("Habitaciones", 1)
        banos = st.number_input("Baños", 1)
        
        st.write("**Extras Generales:**")
        quincho = st.checkbox("Quincho")
        piscina = st.checkbox("Piscina")
        cochera = st.checkbox("Cochera")

        # --- SECCIÓN SERVICIOS DE ALQUILER ---
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
        
        # Visión IA info
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
            st.warning("⚠️ Faltan datos básicos (Ubicación o Precio).")
        else:
            with st.spinner('🤖 Analizando fotos y redactando...'):
                try:
                    # PREPARAR DATOS PARA EL PROMPT
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
                        if inc_aire: servicios_list.append("Aire Acondicionado (A.A.)")
                        if inc_ventilador: servicios_list.append("Ventiladores")
                    txt_servicios = ", ".join(servicios_list) if servicios_list else "No especificado"

                    # 1. TEXTO DEL PROMPT
                    prompt_text = f"""
                    Actúa como experto copywriter inmobiliario en Paraguay.
                    
                    TAREA:
                    1. Analiza TODAS las imágenes adjuntas. Describe estilo, pisos, iluminación y detalles visuales reales.
                    2. Escribe un anuncio persuasivo para {operacion} de {tipo} en {ubicacion}.
                    3. DATOS: Precio {precio}. {habs} habs, {banos} baños. Extras: {txt_extras}.
                    4. { 'SERVICIOS INCLUIDOS / CLIMA: ' + txt_servicios if operacion == "Alquiler" else '' }
                    5. { 'LINK WHATSAPP: https://wa.me/595' + whatsapp if tipo_plan == "PREMIUM (Pro)" else 'NO pongas link de WhatsApp.' }
                    
                    ESTRUCTURA:
                    - Título Gancho con emojis.
                    - Cuerpo del texto (Mezcla la descripción visual de las fotos con los datos técnicos).
                    - { 'Si tiene A.A. o incluye luz/agua, ¡DESTÁCALO!' if operacion == "Alquiler" else '' }
                    - { 'Si es PENTHOUSE o ESTANCIA, usa un tono de alto lujo/exclusividad.' if tipo in ["Penthouse", "Estancia"] else '' }
                    - Cierre fuerte.
                    """

                    # 2. CONSTRUIR MENSAJE (TEXTO + IMÁGENES)
                    content_content = [{"type": "text", "text": prompt_text}]
                    
                    for file in uploaded_files:
                        img = Image.open(file)
                        b64 = encode_image(img)
                        content_content.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
                        })

                    # 3. LLAMADA A LA API
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
