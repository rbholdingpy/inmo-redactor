with st.sidebar:
    st.header("🔐 Área de Miembros")
    st.write("Ingresa tu código de acceso:")
    
    # Usamos un callback (on_change) para que la app reaccione al ingresar el código
    codigo_acceso = st.text_input("Código:", type="password", placeholder="Ej: MARIA2026", key="input_codigo")
    
    plan_actual = "GRATIS"
    limite_fotos = 1
    es_pro = False
    
    if codigo_acceso:
        usuarios_db = obtener_usuarios_sheet()
        usuario_encontrado = None
        
        for usuario in usuarios_db:
            if str(usuario['codigo']).strip() == codigo_acceso.strip():
                usuario_encontrado = usuario
                break
        
        if usuario_encontrado:
            plan_actual = usuario_encontrado['plan']
            limite_fotos = int(usuario_encontrado['limite'])
            es_pro = True
            
            # --- MEJORA: SI EL CÓDIGO ES VÁLIDO, OCULTAMOS LOS PRECIOS AUTOMÁTICAMENTE ---
            st.session_state.ver_planes = False 
            
            st.success(f"✅ ¡Hola {usuario_encontrado['cliente']}!")
            st.info(f"🚀 Acceso PRO nivel: {plan_actual}")
            
            if st.button("🔓 Cerrar Sesión"):
                st.session_state.input_codigo = ""
                st.rerun()
        else:
            st.error("❌ Código inválido.")

    st.divider()
    # Mantenemos el toggle, pero ahora su estado puede ser cambiado por el código
    ver_precios = st.toggle("💎 Ver Planes y Precios", key="ver_planes")
