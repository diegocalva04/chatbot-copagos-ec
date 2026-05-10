import streamlit as st

def render_intro():
    st.markdown("""
    <div class="intro-box">
        <h3>👋 Bienvenido a Ecuasalud, ¡Tu asistente de confianza!</h3>
    </div>
    """, unsafe_allow_html=True)

def render_progress_badge(remaining):
    st.markdown(f'<div class="progress-badge">💬 Preguntas restantes para respuesta automática: <strong>{remaining}</strong></div>', unsafe_allow_html=True)

def render_history_sidebar(historial, on_load_callback, on_delete_callback):
    st.header("📋 Consultas anteriores")
    if not historial:
        st.info("Tus conversaciones anteriores aparecerán aquí.")
    else:
        for idx, item in enumerate(historial):
            with st.container():
                st.markdown(f"""
                <div class="history-item">
                    <div class="history-timestamp">{item['timestamp']}</div>
                    <strong>{item['especialidad']}</strong><br>
                    Copago: {item['copago']}<br>
                    Plan: {item.get('plan_label', 'N/D')}<br>
                    <div style="margin-top: 5px; font-size: 0.8rem; color: #666;">📝 {item.get('resumen', 'Resumen no disponible')}</div>
                </div>
                """, unsafe_allow_html=True)
                col1, col2 = st.columns([1, 1], gap="small")
                with col1:
                    if st.button("Ver", key=f"view_{idx}", help="Ver conversación completa"):
                        on_load_callback(item)
                with col2:
                    if st.button("Eliminar 🗑️", key=f"del_{idx}", help="Eliminar consulta"):
                        on_delete_callback(idx)
                st.markdown("---")
    st.caption("Se guardan las últimas 10 conversaciones")