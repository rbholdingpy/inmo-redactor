if codigo_acceso:
        # Buscamos en Google Sheets
        usuarios_db = obtener_usuarios_sheet()
        usuario_encontrado = None
        
        if not usuarios_db:
            st.error("⚠️ Error de conexión o la hoja está vacía.")
        else:
            # Limpiamos el código ingresado (quitar espacios y pasar a mayúsculas)
            codigo_limpio = codigo_acceso.strip().upper()
            
            for usuario in usuarios_db:
                # Extraemos el valor de la columna 'codigo' del Excel
                # Usamos .get() para evitar errores si la columna no existe
                db_cod = str(usuario.get('codigo', '')).strip().upper()
                
                if db_cod == codigo_limpio:
                    usuario_encontrado = usuario
                    break
            
            if usuario_encontrado:
                # Si lo encuentra, extraemos los datos
                plan_actual = usuario_encontrado.get('plan', 'basico')
                # Si 'limite' está vacío en el Excel, usamos 1 por defecto
                limite_fotos = int(usuario_encontrado.get('limite', 1))
                es_pro = True
                st.session_state.ver_planes = False 
                st.success(f"✅ ¡Hola {usuario_encontrado.get('cliente', 'Usuario')}!")
            else:
                st.error("❌ Código no válido.")
