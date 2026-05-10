import streamlit as st
from datetime import datetime
from modules.config import MAX_HISTORY

def agregar_al_historial(sintoma, especialidad, copago):
    if "historial" not in st.session_state:
        st.session_state.historial = []
    nuevo = {
        "timestamp": datetime.now().strftime("%H:%M %d/%m"),
        "sintoma": sintoma[:50] + "..." if len(sintoma) > 50 else sintoma,
        "especialidad": especialidad,
        "copago": f"${copago:.2f}" if copago else "N/D"
    }
    st.session_state.historial.insert(0, nuevo)
    if len(st.session_state.historial) > MAX_HISTORY:
        st.session_state.historial.pop()