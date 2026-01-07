# [ ... el resto del código hacia arriba sigue igual ... ]

    if st.button("✨ Generar Estrategia", type="primary"):
        if not ubicacion or not texto_precio:
            st.warning("⚠️ Para generar, completa al menos Ubicación y Precio.")
        else:
            with st.spinner('🧠 La IA está analizando las fotos y redactando...'):
                try:
                    # 1. MODIFICACIÓN DEL PROMPT: Quitamos "AIDA" y pedimos formato limpio
                    prompt = f"""Actúa como experto copywriter inmobiliario. Genera 3 opciones de texto para {oper} de {tipo} en {ubicacion}.
                    OPCIÓN 1: Storytelling emotivo enfocado en ({enfoque}).
                    OPCIÓN 2: Descripción de Venta Directa y persuasiva (sin usar terminología técnica de marketing).
                    OPCIÓN 3: Formato corto para Instagram/TikTok con hashtags.
                    Datos: Precio: {texto_precio}. Extras: Quincho={q}, Piscina={p}, Cochera={c}. Habitaciones: {habs}. Baños: {banos}.
                    Contacto: WhatsApp https://wa.me/595{whatsapp}.
                    IMPORTANTE: No uses formato Markdown tradicional (no uses # ni **). Usa emojis elegantes al inicio de los títulos y párrafos clave.""" if es_pro else f"Redactor básico. Crea 1 descripción sencilla para {oper} de {tipo} en {ubicacion}. Precio {texto_precio}. Contacto: {whatsapp}."
                    
                    # Preparamos el contenido para OpenAI con las imágenes
                    content = [{"type": "text", "text": prompt}]
                    for f in uploaded_files:
                        # Aseguramos que el puntero del archivo esté al inicio antes de leer
                        f.seek(0) 
                        content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(Image.open(f))}"}})
                    
                    # Llamada a la IA
                    res = client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": content}])
                    generated_text = res.choices[0].message.content

                    # 2. LIMPIEZA DE TEXTO (Post-procesamiento)
                    # Aunque pedimos no usar Markdown, a veces se escapa. Esto asegura la limpieza.
                    cleaned_text = generated_text.replace("###", "🔹").replace("##", "🏘️").replace("#", "🚀")
                    cleaned_text = cleaned_text.replace("**", "") # Elimina negritas para texto plano limpio
                    cleaned_text = cleaned_text.replace("* ", "▪️ ").replace("- ", "▪️ ") # Reemplaza viñetas por emojis

                    st.success("¡Estrategia lista! Copia el texto abajo.")
                    
                    # Usamos st.write en lugar de text_area para que se vean los emojis bien
                    st.write(cleaned_text)
                    
                    # 3. VISUALIZACIÓN DE FOTOS AL FINAL
                    st.divider()
                    st.caption("📸 Fotos analizadas para esta estrategia:")
                    cols_out = st.columns(4)
                    for i, f in enumerate(uploaded_files):
                         # Reseteamos el puntero de nuevo para poder mostrar la imagen
                         f.seek(0)
                         with cols_out[i%4]: st.image(Image.open(f), use_container_width=True)

                except Exception as e:
                    st.error(f"Error al generar: {e}")
                    st.info("Intenta con menos fotos o fotos más ligeras si el error persiste.")
