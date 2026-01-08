import streamlit as st
from PIL import Image
import base64
import io
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from openai import OpenAI
import time
from datetime import datetime, timedelta
import urllib.parse 

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="VendeMás IA",
    page_icon="🚀",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- TU NÚMERO DE ADMINISTRADOR ---
ADMIN_WHATSAPP = "595961871700" 

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .main { background-color: #F8FAFC; }
    h1 { color: #0F172A; font-family: 'Helvetica Neue', sans-serif; font-weight: 800; }
    
    .stButton>button {
        border-radius: 8px; border: none; padding: 12px; font-weight: bold; width: 100%; transition: all 0.2s;
    }
    .stButton>button:hover { transform: scale(1.02); }

    /* BOTÓN FLOTANTE MENÚ */
    [data-testid="stSidebarCollapsedControl"] {
        position: fixed !important; top: 15px !important; left: 15px !important; z-index: 1000001 !important;
        background-color: #2563EB !important; color: white !important;
        border: 2px solid white !important; border-radius: 12px !important;
        padding: 10px 15px !important; box-shadow: 0 4px 10px rgba(0,0,0,0.3) !important;
        width: auto !important; height: auto !important;
        display: flex !important; align-items: center !important; gap: 5px !important;
    }
    [data-testid="stSidebarCollapsedControl"] svg { fill: white !important; color: white !important; width: 24px !important; height: 24px !important; }
    [data-testid="stSidebarCollapsedControl"]::after { content: "MENÚ"; font-weight: 800; font-size: 16px; color: white; letter-spacing: 1px; }
    @keyframes pulse-blue {
        0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(37, 99, 235, 0.7); }
        70% { transform: scale(1.05); box-shadow: 0 0 0 10px rgba(37, 99, 235, 0); }
        100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(37, 99, 235, 0); }
    }
    [data-testid="stSidebarCollapsedControl"] { animation: pulse-blue 2s infinite; }

    /* TARJETAS PLANES */
    .plan-basic { background-color: #F8FAFC; border: 2px solid #475569; color: #334155; padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 10px; }
    .plan-standard { background-color: white; border: 2px solid #3B82F6; color: #0F172A; padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 10px; box-shadow: 0 4px 6px rgba(59, 130, 246, 0.1); }
    .plan-agency { background: linear-gradient(135deg, #FFFBEB 0%, #FFFFFF 100%); border: 2px solid #F59E0B; color: #0F172A; padding: 25px 20px; border-radius: 15px; text-align: center; margin-bottom: 10px; box-shadow: 0 10px 25px rgba(245, 158, 11, 0.25); transform: scale(1.05); position: relative; z-index: 10; }
    
    .price-tag { font-size: 1.5em; font-weight: 800; margin: 10px 0; }
    .pro-badge { background-color: #DCFCE7; color: #166534; padding: 5px 10px; border-radius: 20px; font-weight: bold; font-size: 0.8em; }
    .free-badge { background-color: #F1F5F9; color: #64748B; padding: 5px 10px; border-radius: 20px; font-weight: bold; font-size: 0.8em; }
    
    .photo-limit-box { background-color: #E0F2FE; border: 2px solid #0284C7; color: #0369A1; padding: 15px; border-radius: 10px; text-align: center; font-size: 1.1em; font-weight: bold; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .social-area { background-color: #ffffff; border: 1px solid #e2e8f0; padding: 20px; border-radius: 10px; margin-top: 20px; text-align: center; }
    .social-title { font-size: 1.2em; font-weight: bold; color: #1E293B; margin-bottom: 15px; }
    .output-box { background-color: white; padding: 25px; border-radius: 10px; border: 1px solid #cbd5e1; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    
    .legal-text { font-size: 0.85em; color: #64748B; text-align: justify; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIONES DE APOYO ---
def encode_image(image):
    buffered = io.BytesIO()
    if image.mode in ("RGBA", "P"): image = image.convert("RGB")
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def limpiar_formulario():
    keys_a_borrar = ['input_ubicacion', 'input_precio', 'input_whatsapp', 'generated_result']
    for key in keys_a_borrar:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state['uploader_key'] += 1

def cerrar_sesion():
    st.session_state['usuario_activo'] = None
    st.session_state['plan_seleccionado'] = None
    st.session_state['ver_planes'] = False
    st.session_state['pedido_registrado'] = False

# --- CALLBACKS ---
def ir_a_planes():
    st.session_state.ver_planes = True
    st.session_state.plan_seleccionado = None
    st.session_state.pedido_registrado = False

def seleccionar_plan(nombre_plan):
    st.session_state.plan_seleccionado = nombre_plan
    st.session_state.ver_planes = True
    st.session_state.pedido_registrado = False

def volver_a_app():
    st.session_state.ver_planes = False
    st.session_state.plan_seleccionado = None
    st.session_state.pedido_registrado = False

def cancelar_seleccion():
    st.session_state.plan_seleccionado = None
    st.session_state.ver_planes = True
    st.session_state.pedido_registrado = False

# --- INICIALIZACIÓN ---
if 'uploader_key' not in st.session_state: st.session_state['uploader_key'] = 0
if 'usuario_activo' not in st.session_state: st.session_state['usuario_activo'] = None
if 'ver_planes' not in st.session_state: st.session_state['ver_planes'] = False
if 'plan_seleccionado' not in st.session_state: st.session_state['plan_seleccionado'] = None
if 'pedido_registrado' not in st.session_state: st.session_state['pedido_registrado'] = False

if 'guest_last_use' not in st.session_state: st.session_state['guest_last_use'] = None
if 'guest_credits' not in st.session_state: st.session_state['guest_credits'] = 1

if st.session_state['guest_last_use']:
    tiempo_pasado = datetime.now() - st.session_state['guest_last_use']
    if tiempo_pasado > timedelta(days=1):
        st.session_state['guest_credits'] = 1
        st.session_state['guest_last_use'] = None

# --- API KEY ---
api_key = st.secrets.get("OPENAI_API_KEY")
if not api_key:
    st.error("⚠️ Error: Falta API Key de OpenAI en Secrets.")
    st.stop()
client = OpenAI(api_key=api_key)

# =======================================================
# === 🔐 CONEXIÓN GOOGLE SHEETS ===
# =======================================================
def get_gspread_client():
    creds_info = dict(st.secrets["gcp_service_account"])
    if "private_key" in creds_info:
        creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
    client_gs = gspread.authorize(creds)
    return client_gs

def obtener_usuarios_sheet():
    try:
        client_gs = get_gspread_client()
        archivo = client_gs.open("Usuarios_InmoApp")
        sheet = archivo.get_worksheet(0)
        return sheet.get_all_records()
    except Exception:
        return []

def descontar_credito(codigo_usuario):
    try:
        client_gs = get_gspread_client()
        sheet = client_gs.open("Usuarios_InmoApp").get_worksheet(0)
        cell = sheet.find(str(codigo_usuario))
        if cell:
            headers = sheet.row_values(1)
            col_limite = headers.index('limite') + 1 
            valor_actual = sheet.cell(cell.row, col_limite).value
            if valor_actual and int(valor_actual) > 0:
                nuevo_saldo = int(valor_actual) - 1
                sheet.update_cell(cell.row, col_limite, nuevo_saldo)
                return True
    except Exception:
        return False
    return False

# --- LÓGICA DE REGISTRO BLINDADA (SIN DUPLICADOS) ---
def registrar_pedido(nombre, apellido, email, telefono, nuevo_plan):
    try:
        client_gs = get_gspread_client()
        sheet = client_gs.open("Usuarios_InmoApp").get_worksheet(0)
        
        # 1. NORMALIZACIÓN DE DATOS (Minúsculas y sin espacios para comparar bien)
        email_input_clean = str(email).strip().lower()
        
        # Obtener toda la columna de correos (Columna F es la 6)
        lista_correos_raw = sheet.col_values(6)
        
        # Convertir lista del sheet a formato limpio para buscar
        lista_correos_clean = [str(e).strip().lower() for e in lista_correos_raw]
        
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
        nombre_completo = f"{nombre} {apellido}"
        
        # A. SI EL CORREO YA EXISTE
        if email_input_clean in lista_correos_clean:
            # Encontrar el índice real (sumamos 1 porque gspread es base 1)
            # Nota: .index() encuentra la primera coincidencia
            row_index = lista_correos_clean.index(email_input_clean) + 1
            
            # Obtener el plan que ya tiene (Columna C es la 3)
            plan_actual_sheet = str(sheet.cell(row_index, 3).value).strip().lower()
            nuevo_plan_check = str(nuevo_plan).strip().lower()
            
            # Verificar si intenta comprar LO MISMO (Básico == Básico)
            # Usamos "in" por si el plan en excel dice "Plan Básico" y el nuevo es "Básico"
            if nuevo_plan_check in plan_actual_sheet or plan_actual_sheet in nuevo_plan_check:
                return "SAME_PLAN" # ERROR: Ya tiene este plan
            
            # Si es diferente, ACTUALIZAMOS la fila existente (Cambio de Plan)
            else:
                sheet.update_cell(row_index, 3, nuevo_plan) # Actualizar Plan
                sheet.update_cell(row_index, 5, telefono)   # Actualizar Tel
                sheet.update_cell(row_index, 7, "SOLICITUD CAMBIO PLAN") # Estado
                sheet.update_cell(row_index, 8, fecha)      # Fecha
                return "UPDATED"

        # B. SI EL CORREO NO EXISTE (NUEVO USUARIO)
        else:
            # [Codigo, Cliente, Plan, Limite, Telefono, Correo, Estado, Fecha]
            nueva_fila = ["PENDIENTE", nombre_completo, nuevo_plan, 0, telefono, email, "NUEVO PEDIDO", fecha]
            sheet.append_row(nueva_fila)
            return "CREATED"
            
    except Exception as e:
        print(f"Error en registro: {e}")
        return "ERROR"

# =======================================================
# === 🏗️ BARRA LATERAL ===
# =======================================================
with st.sidebar:
    st.header("🔐 Área de Miembros")
    
    if not st.session_state['usuario_activo']:
        st.markdown("""<div style="background-color:#F1F5F9; padding:10px; border-radius:8px; margin-bottom:15px;"><small>Estado actual:</small><br><b>👤 Invitado (Freemium)</b><br><span style="color:#64748B; font-size:0.8em;">1 Generación / 24hs</span></div>""", unsafe_allow_html=True)
        with st.form("login_form"):
            codigo_input = st.text_input("¿Tienes Código?", type="password", placeholder="Ej: PRUEBA1")
            submit_login = st.form_submit_button("🔓 Entrar como Miembro")
        if submit_login and codigo_input:
            usuarios_db = obtener_usuarios_sheet()
            usuario_encontrado = next((u for u in usuarios_db if str(u.get('codigo', '')).strip().upper() == codigo_input.strip().upper()), None)
            if usuario_encontrado:
                st.session_state['usuario_activo'] = usuario_encontrado
                st.session_state['ver_planes'] = False
                st.rerun()
            else:
                st.error("❌ Código incorrecto.")
        st.markdown("---")
        st.info("💡 **Los Invitados tienen funciones limitadas.**")
        st.button("🚀 VER PLANES PRO", on_click=ir_a_planes)
    else:
        user = st.session_state['usuario_activo']
        creditos_disponibles = int(user.get('limite', 0) if user.get('limite') != "" else 0)
        st.success(f"✅ ¡Hola {user.get('cliente', 'Usuario')}!")
        color_cred = "blue" if creditos_disponibles > 0 else "red"
        st.markdown(f":{color_cred}[**🪙 Créditos: {creditos_disponibles}**]")
        
        st.markdown("---")
        st.markdown("### 🛠️ Gestión Rápida")
        if st.button("🔄 Nueva Propiedad (Limpiar)", type="secondary"):
            limpiar_formulario()
            
        st.markdown("---")
        st.button("🚀 SUBE DE NIVEL\nAprovecha más", type="primary", on_click=ir_a_planes)
        st.markdown("---")
        if st.button("🔒 Cerrar Sesión"):
            cerrar_sesion()
            st.rerun()
    st.caption("© 2026 VendeMás IA")

# =======================================================
# === 💎 ZONA DE VENTAS ===
# =======================================================
if st.session_state.ver_planes:
    st.title("💎 Escala tus Ventas")
    
    # DETECTAR PLAN ACTUAL
    plan_usuario_actual = ""
    if st.session_state['usuario_activo']:
        plan_usuario_actual = str(st.session_state['usuario_activo'].get('plan', '')).lower()

    if st.session_state.plan_seleccionado is None:
        st.write("Elige la potencia que necesita tu negocio.")
        c1, c2, c3 = st.columns(3)
        
        with c1:
            st.markdown('<div class="plan-basic"><h3>🥉 Básico</h3><div class="price-tag">20.000 Gs</div><p class="feature-text">10 Estrategias</p><p style="font-size:0.8em">Máx 3 Fotos</p></div>', unsafe_allow_html=True)
            # Bloquear si ya tiene este plan
            if 'basico' in plan_usuario_actual or 'básico' in plan_usuario_actual:
                st.button("✅ Tu Plan Actual", disabled=True, key="btn_basico_dis")
            else:
                st.button("Elegir Básico", key="btn_basico", on_click=seleccionar_plan, args=("Básico",))

        with c2:
            st.markdown('<div class="plan-standard"><h3>🥈 Estándar</h3><div class="price-tag" style="color:#2563EB;">35.000 Gs</div><p class="feature-text"><b>20 Estrategias</b></p><p style="font-size:0.8em">Máx 6 Fotos</p></div>', unsafe_allow_html=True)
            if 'estándar' in plan_usuario_actual or 'standar' in plan_usuario_actual:
                st.button("✅ Tu Plan Actual", disabled=True, key="btn_estandar_dis")
            else:
                st.button("Elegir Estándar", key="btn_estandar", type="primary", on_click=seleccionar_plan, args=("Estándar",))

        with c3:
            st.markdown('<div class="plan-agency"><div style="background:#F59E0B; color:white; font-size:0.7em; font-weight:bold; padding:2px 8px; border-radius:10px; display:inline-block; margin-bottom:5px;">🔥 MEJOR OPCIÓN</div><h3 style="color:#B45309;">🥇 Agencia</h3><div class="price-tag" style="color:#D97706;">80.000 Gs</div><p class="feature-text"><b>200 Estrategias</b></p><p style="font-size:0.8em">Máx 10 Fotos</p></div>', unsafe_allow_html=True)
            if 'agencia' in plan_usuario_actual:
                st.button("✅ Tu Plan Actual", disabled=True, key="btn_agencia_dis")
            else:
                st.button("👑 ELEGIR AGENCIA", key="btn_agencia", type="primary", on_click=seleccionar_plan, args=("Agencia",))
        
        st.divider()
        st.button("⬅️ Volver a la App", on_click=volver_a_app)

    else:
        st.info(f"🚀 Excelente elección: **Plan {st.session_state.plan_seleccionado}**")
        
        if not st.session_state.pedido_registrado:
            st.write("### 📝 Paso 1: Tus Datos")
            
            def_nombre = ""
            def_email = ""
            def_tel = ""
            if st.session_state['usuario_activo']:
                u = st.session_state['usuario_activo']
                try: def_nombre = u.get('cliente', '').split(' ')[0]
                except: pass
                def_email = u.get('correo', '')
                def_tel = str(u.get('telefono', ''))

            with st.form("form_registro_pedido"):
                c_nom, c_ape = st.columns(2)
                nombre = c_nom.text_input("Nombre", value=def_nombre)
                apellido = c_ape.text_input("Apellido")
                email = st.text_input("Correo Electrónico (Para tu código de acceso)", value=def_email)
                telefono = st.text_input("Número de WhatsApp", value=def_tel)
                
                submitted = st.form_submit_button("✅ Confirmar y Ver Datos de Pago", type="primary")
                
                if submitted:
                    if nombre and apellido and email and telefono:
                        with st.spinner("Verificando datos..."):
                            status = registrar_pedido(nombre, apellido, email, telefono, st.session_state.plan_seleccionado)
                            
                            if status == "SAME_PLAN":
                                st.error(f"⛔ **¡Atención!** El correo {email} ya tiene activo el plan **{st.session_state.plan_seleccionado}**. No puedes comprar el mismo plan.")
                                st.warning("Si necesitas más créditos, contacta a soporte.")
                            
                            elif status == "UPDATED":
                                st.session_state.pedido_registrado = True
                                st.session_state['temp_nombre'] = f"{nombre} {apellido}"
                                st.session_state['tipo_pedido'] = "CAMBIO DE PLAN"
                                st.rerun()
                                
                            elif status == "CREATED":
                                st.session_state.pedido_registrado = True
                                st.session_state['temp_nombre'] = f"{nombre} {apellido}"
                                st.session_state['tipo_pedido'] = "NUEVO ALTA"
                                st.rerun()
                            else:
                                st.error("Hubo un error de conexión. Intenta de nuevo.")
                    else:
                        st.warning("⚠️ Completa todos los campos.")
            st.button("🔙 Volver atrás", on_click=cancelar_seleccion)

        else:
            tipo = st.session_state.get('tipo_pedido', 'PEDIDO')
            if tipo == "CAMBIO DE PLAN":
                st.success("✅ **¡Cambio de Plan Detectado!** Tu cuenta se actualizará tras el pago.")
            else:
                st.success("✅ **¡Datos recibidos!** Tu cuenta está lista para activarse.")

            st.write("### 💳 Paso 2: Realiza el Pago")
            col_bank, col_wa = st.columns(2)
            with col_bank:
                st.markdown("""
                <div style="background-color:white; padding:15px; border-radius:10px; border:1px solid #ddd; color: #333;">
                <b>Banco:</b> ITAÚ <br>
                <b>Titular:</b> Ricardo Blanco <br>
                <b>Cuenta:</b> 320595209 <br>
                <b>Alias:</b> RUC 1911221-1 <br>
                <b>C.I.:</b> 1911221 <br>
                <b>RUC:</b> 1911221-1
                </div>
                """, unsafe_allow_html=True)
            with col_wa:
                nombre_cliente = st.session_state.get('temp_nombre', 'Nuevo Cliente')
                if tipo == "CAMBIO DE PLAN":
                    mensaje_wp = f"Hola, soy *{nombre_cliente}*. Quiero cambiar mi cuenta actual al *Plan {st.session_state.plan_seleccionado}*. Adjunto comprobante."
                else:
                    mensaje_wp = f"Hola, soy *{nombre_cliente}*. Nuevo registro para el *Plan {st.session_state.plan_seleccionado}*. Adjunto comprobante."
                
                mensaje_wp_url = mensaje_wp.replace(" ", "%20").replace("\n", "%0A")
                link_wp = f"https://wa.me/{ADMIN_WHATSAPP}?text={mensaje_wp_url}"
                
                st.markdown(f'<a href="{link_wp}" target="_blank" style="text-decoration:none;"><button style="background-color:#25D366; color:white; border:none; padding:15px; border-radius:8px; width:100%; font-weight:bold; cursor:pointer; font-size:1.1em; margin-top:10px; box-shadow: 0 4px 6px rgba(37, 211, 102, 0.3);">📲 Enviar Comprobante por WhatsApp</button></a>', unsafe_allow_html=True)
            st.divider()
            if st.button("🏁 Finalizar y Volver al Inicio"):
                volver_a_app()
    st.stop()

# =======================================================
# === APP PRINCIPAL ===
# =======================================================
c_title, c_badge = st.columns([2, 1])
with c_title:
    st.title("🚀 VendeMás IA")
    st.caption("Experto en Neuroventas Inmobiliarias.")

es_pro = False
plan_actual = "INVITADO"
creditos_disponibles = 0
cupo_fotos = 0

if st.session_state['usuario_activo']:
    es_pro = True
    user = st.session_state['usuario_activo']
    plan_str = str(user.get('plan', '')).lower()
    
    if 'agencia' in plan_str:
        cupo_fotos = 10
        plan_actual = "AGENCIA"
    elif 'estándar' in plan_str or 'standar' in plan_str:
        cupo_fotos = 6
        plan_actual = "ESTÁNDAR"
    elif 'básico' in plan_str or 'basico' in plan_str:
        cupo_fotos = 3
        plan_actual = "BÁSICO"
    else:
        cupo_fotos = 3
        plan_actual = "MIEMBRO"

    creditos_disponibles = int(user.get('limite', 0) if user.get('limite') != "" else 0)
    with c_badge:
        st.markdown(f'<div style="text-align:right"><span class="pro-badge">PLAN {plan_actual}</span></div>', unsafe_allow_html=True)
else:
    es_pro = False
    with c_badge:
        st.markdown('<div style="text-align:right"><span class="free-badge">MODO FREEMIUM</span></div>', unsafe_allow_html=True)

# --- AVISO PARA ABRIR MENÚ EN MÓVIL ---
if not es_pro:
    st.info("👈 **¿Ya eres miembro?** Toca el botón azul **'MENÚ'** arriba a la izquierda para iniciar sesión.")

# --- GUÍA ---
with st.expander("📘 ¿Cómo funciona? (Guía Rápida)", expanded=False):
    st.markdown("""
    <div class="step-box"><b>1. Sube tus Fotos (Solo PRO):</b> La IA analiza las imágenes.</div>
    <div class="step-box"><b>2. Rellena Datos:</b> Indica precio, ubicación y características.</div>
    <div class="step-box"><b>3. Genera:</b> Obtén una estrategia de venta persuasiva.</div>
    """, unsafe_allow_html=True)

# =======================================================
# === 1. GALERÍA ===
# =======================================================
st.write("#### 1. 📸 Galería")
uploaded_files = []

if es_pro:
    if creditos_disponibles <= 0:
        st.error("⛔ **Sin créditos.** Recarga tu plan para usar la IA.")
        st.stop()
    
    st.markdown(f"""<div class="photo-limit-box">📸 Potencia {plan_actual}: Puedes subir hasta <span style="font-size:1.3em; color:#0284C7;">{cupo_fotos} FOTOS</span> por análisis.</div>""", unsafe_allow_html=True)
    uploaded_files = st.file_uploader("Subir fotos", type=["jpg", "png", "jpeg"], accept_multiple_files=True, key=f"uploader_{st.session_state['uploader_key']}")
    if uploaded_files:
        if len(uploaded_files) > cupo_fotos:
            st.error(f"⛔ **¡Demasiadas fotos!** Tu plan {plan_actual} solo permite {cupo_fotos} imágenes.")
            st.stop()
        # VISTA PREVIA
        with st.expander("👁️ Vista Previa de Imágenes Seleccionadas", expanded=True):
            cols = st.columns(4)
            for i, f in enumerate(uploaded_files):
                with cols[i%4]: st.image(Image.open(f), use_container_width=True)
else:
    st.info("🔒 **La carga de fotos y Visión IA es exclusiva para Miembros.**")
    st.markdown('<div style="opacity:0.6; pointer-events:none; border: 2px dashed #ccc; padding: 20px; text-align: center; border-radius: 10px;">📂 Subir fotos (Bloqueado)</div>', unsafe_allow_html=True)

st.divider()

# =======================================================
# === 2. DATOS ===
# =======================================================
st.write("#### 2. 📝 Datos de la Propiedad")
c1, c2 = st.columns(2)

with c1:
    oper = st.radio("Operación", ["Venta", "Alquiler"], horizontal=True)
    tipo = st.selectbox("Tipo", ["Casa", "Departamento", "Terreno", "Local", "Duplex"])
    
    if es_pro:
        enfoque = st.selectbox("🎯 Estrategia", ["Equilibrado", "🔥 Urgencia", "🔑 Primera Casa", "💎 Lujo", "💰 Inversión"])
    else:
        enfoque = st.selectbox("🎯 Estrategia", ["🔒 Estándar (Solo PRO)"], disabled=True)
        enfoque = "Venta Estándar"

    if es_pro and plan_actual in ["ESTÁNDAR", "AGENCIA"]:
        tono = st.selectbox("🗣️ Tono de Voz", ["Amable y Cercano", "Profesional y Serio", "Persuasivo y Energético", "Sofisticado y Elegante", "Urgente (Oportunidad)"])
    else:
        msg_bloqueo = "🔒 Neutro (Requiere Plan Estándar)" if es_pro else "🔒 Neutro (Solo PRO Estándar)"
        tono = st.selectbox("🗣️ Tono de Voz", [msg_bloqueo], disabled=True)
        tono = "Neutro y Descriptivo"

    ubicacion = st.text_input("Ubicación", key="input_ubicacion")
    
    if oper == "Alquiler":
        cp, cf = st.columns([2, 1])
        precio_val = cp.text_input("Precio", key="input_precio")
        frec = cf.selectbox("Periodo", ["Mensual", "Semestral", "Anual"])
        texto_precio = f"{precio_val} ({frec})"
    else:
        texto_precio = st.text_input("Precio", key="input_precio")
        
    if es_pro:
        whatsapp = st.text_input("WhatsApp (Solo números)", key="input_whatsapp")
    else:
        whatsapp = st.text_input("WhatsApp", placeholder="🔒 Solo Miembros PRO", disabled=True)

with c2:
    habs = st.number_input("Habitaciones", 1)
    banos = st.number_input("Baños", 1)
    st.write("**Servicios y Extras:**")
    col_ex1, col_ex2 = st.columns(2)
    with col_ex1:
        gar = st.checkbox("Garage")
        qui = st.checkbox("Quincho")
        pis = st.checkbox("Piscina")
        aa = st.checkbox("Aire Acond.")
        vent = st.checkbox("Ventilador")
    with col_ex2:
        wifi = st.checkbox("Wifi")
        tv = st.checkbox("TV Cable")
        agua = st.checkbox("Agua")
        luz = st.checkbox("Luz")

st.divider()

if es_pro:
    cant_fotos = len(uploaded_files) if uploaded_files else 0
    st.info(f"🧠 **Neuro-Vision Activa:** Analizando {cant_fotos} fotos con potencia {plan_actual}... (Costo: 1 crédito)")
else:
    creditos_guest = st.session_state['guest_credits']
    if creditos_guest > 0:
        st.success(f"🎁 **Modo Invitado:** Tienes {creditos_guest} generación gratis hoy.")
    else:
        st.warning("⏳ **Has usado tu crédito diario.** Vuelve mañana o hazte PRO.")

# =======================================================
# === GENERACIÓN ===
# =======================================================
if st.button("✨ Generar Estrategia", type="primary"):
    if not ubicacion or not texto_precio:
        st.warning("⚠️ Completa Ubicación y Precio.")
        st.stop()
        
    puede_generar = False
    if es_pro:
        if creditos_disponibles > 0: puede_generar = True
    else:
        if st.session_state['guest_credits'] > 0: puede_generar = True
        else:
            st.error("⛔ Límite diario alcanzado. Hazte Miembro para continuar.")
            st.stop()

    if puede_generar:
        with st.spinner('🧠 Redactando estrategia...'):
            try:
                base_prompt = f"""Actúa como copywriter inmobiliario experto.
                Datos: {oper} {tipo} en {ubicacion}. Precio: {texto_precio}. 
                Características: Hab:{habs}, Baños:{banos}.
                Extras: Garage={gar}, Quincho={qui}, Piscina={pis}, AA={aa}, Ventilador={vent}, Wifi={wifi}, TV={tv}, Agua={agua}, Luz={luz}."""
                
                instrucciones_visuales = """
                INSTRUCCIONES VISUALES (CRÍTICO):
                1. 👁️ ANÁLISIS DE FOTOS: Si recibes imágenes, OBSERVA DETENIDAMENTE y menciona al menos 3 detalles visuales específicos que veas (ej: tipo de piso, color de paredes, estilo de cocina, iluminación). ¡Demuestra que las has visto!
                2. FORMATO: Usa Markdown (**negritas**) para resaltar Títulos, Precio y Llamadas a la Acción.
                3. ESTRUCTURA: Usa listas verticales con emojis para características. Párrafos cortos.
                4. HASHTAGS: Al final de la opción 3, incluye 10 hashtags relevantes.
                """

                if es_pro:
                    full_prompt = base_prompt + f""" 
                    TONO: {tono}.
                    Genera 3 opciones:
                    1. Storytelling Emotivo ({enfoque}).
                    2. Venta Directa (Datos y Lista).
                    3. Instagram (Viral + Hashtags).
                    Link WhatsApp: https://wa.me/595{whatsapp}.
                    {instrucciones_visuales}
                    """
                    content = [{"type": "text", "text": full_prompt}]
                    
                    if uploaded_files and len(uploaded_files) <= cupo_fotos:
                        for f in uploaded_files:
                            f.seek(0)
                            content.append({
                                "type": "image_url", 
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{encode_image(Image.open(f))}",
                                    "detail": "high"
                                }
                            })
                else:
                    full_prompt = base_prompt + f"""Genera 1 Descripción básica. {instrucciones_visuales}"""
                    content = [{"type": "text", "text": full_prompt}]

                res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": content}])
                generated_text = res.choices[0].message.content

                cleaned_text = generated_text.replace("###", "🔹").replace("##", "🏘️")
                cleaned_text = cleaned_text.replace("# ", "🚀 ") 
                cleaned_text = cleaned_text.replace("* ", "▪️ ").replace("- ", "▪️ ")
                
                if es_pro:
                    exito = descontar_credito(user['codigo'])
                    if exito:
                        st.session_state['usuario_activo']['limite'] = creditos_disponibles - 1
                        st.toast("✅ Crédito PRO descontado", icon="🪙")
                else:
                    st.session_state['guest_credits'] = 0
                    st.session_state['guest_last_use'] = datetime.now()
                    st.toast("✅ Crédito gratuito usado", icon="🎁")

                st.session_state['generated_result'] = cleaned_text
            except Exception as e:
                st.error(f"Error: {e}")

if 'generated_result' in st.session_state:
    st.markdown('<div class="output-box">', unsafe_allow_html=True)
    st.subheader("🎉 Estrategia Generada:")
    st.markdown(st.session_state['generated_result'])
    st.markdown('</div>', unsafe_allow_html=True)
    
    with st.expander("📋 Ver Texto sin Formato (Para Copiar)"):
        st.code(st.session_state['generated_result'], language=None)
    
    st.markdown('<div class="social-area"><div class="social-title">🚀 Acciones Rápidas (Postea Ya):</div>', unsafe_allow_html=True)
    c_wa, c_ig, c_fb = st.columns(3)
    texto_encoded = urllib.parse.quote(st.session_state['generated_result'])
    link_wa = f"https://wa.me/?text={texto_encoded}"
    
    with c_wa: st.link_button("📲 Enviar a WhatsApp", link_wa)
    with c_ig: st.link_button("📸 Abrir Instagram", "https://www.instagram.com/")
    with c_fb: st.link_button("📘 Abrir Facebook", "https://www.facebook.com/")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("¿Terminaste?")
    if st.button("🔄 Nueva Propiedad (Limpiar) ", type="secondary"):
        limpiar_formulario()

# =======================================================
# === ⚖️ AVISO LEGAL ===
# =======================================================
st.markdown("<br><br>", unsafe_allow_html=True)
with st.expander("⚖️ Aviso Legal y Privacidad (Importante)"):
    st.markdown("""
    <div class="legal-text">
    <b>1. Protección de Datos y Privacidad:</b><br>
    VendeMás IA es una herramienta de procesamiento en tiempo real. Queremos informarle que:
    <ul>
        <li><b>Eliminación Automática:</b> Todas las fotos, números de teléfono y datos ingresados se eliminan automáticamente de la memoria del sistema al cerrar o recargar la página.</li>
        <li><b>Sin Base de Datos de Respaldo:</b> No guardamos copias de seguridad de sus fotos o descripciones generadas.</li>
        <li><b>Responsabilidad:</b> Guarde sus textos generados antes de salir, ya que no podrán recuperarse.</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)
