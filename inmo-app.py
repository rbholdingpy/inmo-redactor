# =======================================================
# === APP PRINCIPAL ===
# =======================================================
c_title, c_badge = st.columns([2, 1]) # Ajusté un poco el ancho para que quepan los dos botones

with c_title:
    st.title("🚀 VendeMás IA")
    st.caption("Experto en Neuroventas Inmobiliarias.")

with c_badge:
    if es_pro:
        # Si ya es PRO, solo mostramos su plan actual en verde
        st.markdown(f'<div style="text-align:right"><span class="pro-badge">PLAN {plan_actual.upper()}</span></div>', unsafe_allow_html=True)
    else:
        # Si es GRATIS, mostramos los DOS botones juntos
        st.markdown("""
        <div style="text-align:right; white-space:nowrap;">
            <span style="background-color:#F1F5F9; color:#64748B; padding:6px 12px; border-radius:20px; font-size:0.8em; margin-right:5px;">MODO GRATIS</span>
            <span style="background-color:#EFF6FF; color:#2563EB; border:1px solid #2563EB; padding:6px 12px; border-radius:20px; font-size:0.8em; font-weight:bold;">💎 PRO</span>
        </div>
        """, unsafe_allow_html=True)

# 1. GALERÍA
# ... (el resto del código sigue igual hacia abajo)
