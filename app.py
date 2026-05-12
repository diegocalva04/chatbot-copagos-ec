import streamlit as st
import json
from datetime import datetime

from modules.config import MAX_INTERACTIONS, MAX_HISTORY
from modules.database import cargar_planes, buscar_copago_y_hospitales
from modules.ia_client import llamar_ia, generar_resumen_conversacion
from modules.prompts import SYSTEM_PROMPT, FINAL_PROMPT
from modules.utils import (
    es_saludo_sin_sintomas, es_agradecimiento, respuesta_saludo,
    es_peticion_atencion, contiene_sintomas
)
from modules.ui_components import render_intro, render_progress_badge, render_history_sidebar

st.set_page_config(page_title="Ecuasalud", page_icon="⚕️", layout="wide")

with open("assets/styles.css", "r") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ========== INICIALIZACIÓN DE ESTADO ==========
if "messages" not in st.session_state:
    st.session_state.messages = []
if "interaction_count" not in st.session_state:
    st.session_state.interaction_count = 0
if "final_shown" not in st.session_state:
    st.session_state.final_shown = False
if "force_final" not in st.session_state:
    st.session_state.force_final = False
if "plan_selected_index" not in st.session_state:
    st.session_state.plan_selected_index = 0
if "historial" not in st.session_state:
    st.session_state.historial = []
if "viewing_history" not in st.session_state:
    st.session_state.viewing_history = False
if "reset_counter" not in st.session_state:
    st.session_state.reset_counter = 0

# ========== FUNCIONES DE HISTORIAL ==========
def eliminar_del_historial(idx):
    st.session_state.historial.pop(idx)
    st.rerun()

def cargar_conversacion(item):
    st.session_state.messages = item["mensajes"]
    st.session_state.interaction_count = item["interaction_count"]
    st.session_state.final_shown = True
    st.session_state.force_final = False
    st.session_state.plan_selected_index = item["plan_index"]
    st.session_state.viewing_history = True
    st.rerun()

def guardar_conversacion_en_historial(especialidad, copago, primer_sintoma, mensajes_completos, interaction_count, plan_index, plan_label, resumen):
    nuevo_item = {
        "timestamp": datetime.now().strftime("%H:%M %d/%m"),
        "sintoma": primer_sintoma[:50] + "..." if len(primer_sintoma) > 50 else primer_sintoma,
        "especialidad": especialidad,
        "copago": f"${copago:.2f}" if copago else "N/D",
        "plan_label": plan_label,
        "mensajes": mensajes_completos,
        "interaction_count": interaction_count,
        "plan_index": plan_index,
        "resumen": resumen
    }
    st.session_state.historial.insert(0, nuevo_item)
    if len(st.session_state.historial) > MAX_HISTORY:
        st.session_state.historial.pop()

# ========== SIDEBAR ==========
with st.sidebar:
    # Encabezado estilizado
    st.markdown("""
    <div style="text-align: center; margin-bottom: 25px;">
        <div style="font-size: 2.8rem; line-height: 1;">⚕️</div>
        <h1 style="font-family: 'Segoe UI', 'Roboto', 'Helvetica Neue', sans-serif; 
                   color: #00A8FF; 
                   font-weight: 700; 
                   font-size: 2.2rem; 
                   margin: 0; 
                   letter-spacing: -0.5px;">
            Ecuasalud
        </h1>
        <p style="font-family: monospace; 
                  color: #4A5568; 
                  font-size: 0.75rem; 
                  margin-top: -5px;">
            asistente médico inteligente
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Nueva consulta", use_container_width=True):
        st.session_state.messages = []
        st.session_state.interaction_count = 0
        st.session_state.final_shown = False
        st.session_state.force_final = False
        st.session_state.plan_selected_index = 0
        st.session_state.viewing_history = False
        st.session_state.reset_counter += 1
        st.rerun()
    st.markdown("---")
    
    # Mostrar historial de conversaciones
    render_history_sidebar(st.session_state.historial, cargar_conversacion, eliminar_del_historial)
    
    st.caption("Sistema estimador - Siempre consulta a un profesional.")

# ========== INTERFAZ PRINCIPAL ==========
render_intro()

# Guía de uso emergente
with st.expander("¿Cómo obtener la información de atención más rápido?"):
    st.markdown("""
    Con **Ecuasalud** puedes obtener la especialidad, copago y hospital más económico sin esperar las 3 interacciones.
    Solo escribe frases como:
    - **"quiero atenderme"**
    - **"cotizar precio"**
    - **"cuánto cuesta la consulta"**
    - **"necesito especialista"**
    - **"hospital más económico"**
    - **"precio de la cita"**
    
    Siempre que ya hayas descrito tus síntomas (en el mismo mensaje o en conversaciones previas).
    """)

plan_options = cargar_planes()
plan_list = ["-- Selecciona tu plan --"] + list(plan_options.keys())
plan_disabled = st.session_state.viewing_history
selected_label = st.selectbox(
    "Plan de seguro",
    plan_list,
    index=st.session_state.plan_selected_index,
    key=f"plan_selector_{st.session_state.reset_counter}",
    disabled=plan_disabled
)
if selected_label != plan_list[st.session_state.plan_selected_index] and not plan_disabled:
    st.session_state.plan_selected_index = plan_list.index(selected_label)
    st.session_state.messages = []
    st.session_state.interaction_count = 0
    st.session_state.final_shown = False
    st.session_state.force_final = False
    st.rerun()

if selected_label == "-- Selecciona tu plan --":
    plan_id = None
    if not st.session_state.viewing_history:
        st.warning("⚠️ Selecciona tu plan para continuar")
else:
    plan_id = plan_options[selected_label]
    if not st.session_state.viewing_history:
        st.success("✅ Plan activo")

if st.session_state.viewing_history:
    st.info("Estás viendo una conversación anterior (solo lectura). Usa 'Nueva consulta' para iniciar una nueva.")

if not st.session_state.viewing_history and not st.session_state.final_shown and plan_id:
    remaining = max(0, MAX_INTERACTIONS - st.session_state.interaction_count)
    render_progress_badge(remaining)
elif not st.session_state.viewing_history and st.session_state.final_shown:
    st.info("✅ Ya recibiste la información completa. Usa 'Nueva consulta' para empezar de nuevo.")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

def mostrar_respuesta_final():
    with st.chat_message("assistant"):
        with st.spinner("Preparando tu información personalizada..."):
            history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages 
                       if not (m["role"] == "assistant" and "Copago estimado" in m["content"])]
            respuesta_json = llamar_ia(history, FINAL_PROMPT, response_format=True)
            try:
                data = json.loads(respuesta_json)
                especialidad = data.get("especialidad", "Medicina General")
                razon_tecnica = data.get("razon_tecnica", "")
                explicacion = data.get("explicacion_paciente", "Basado en tus síntomas, esta es la especialidad más adecuada.")
                rec = data.get("recomendaciones", "Consulta a un médico si los síntomas persisten.")
            except Exception:
                especialidad, razon_tecnica, explicacion, rec = "Medicina General", "", "No se pudo analizar en detalle.", "Consulta a un médico."
            
            copago, hospitales = buscar_copago_y_hospitales(especialidad, plan_id)
            primer_sintoma = next((m["content"] for m in st.session_state.messages if m["role"] == "user"), "tus síntomas")
            if len(primer_sintoma) > 80:
                primer_sintoma = primer_sintoma[:80] + "..."
            
            plan_info = selected_label
            
            respuesta = f"**🔍 Especialidad sugerida:** {especialidad}\n\n"
            respuesta += f"**📋 ¿Por qué?** {explicacion}\n\n"
            if razon_tecnica:
                respuesta += f"*({razon_tecnica.lower()})*\n\n"
            respuesta += f"**💊 Recomendación final:** {rec}\n\n"
            respuesta += f"**📄 Plan de seguro seleccionado:** {plan_info}\n\n"
            
            #if copago:
                #respuesta += f"**💰 Copago estimado:** ${copago:.2f} USD\n\n"
            #else:
                #respuesta += "**💰 Copago:** No registrado para este plan. Verifica con tu aseguradora.\n\n"
            
            if hospitales:
                mejor = hospitales[0]
                costo_base = mejor['costo_consulta_base']
                
                respuesta += f"**🏥 Hospital más económico en tu red:**\n"
                respuesta += f"    {mejor['nombre']} – {mejor['ciudad']}\n"
                #respuesta += f"     \n Costo de consulta base en este hospital: ${costo_base:.2f}\n\n"
                
                # Desglose de costos (si hay copago)
                if copago:
                    ahorro = costo_base - copago
                    respuesta += f"\n**💰 Desglose financiero:**\n"
                    respuesta += f"  \n• Costo total consulta: ${costo_base:.2f}\n"
                    respuesta += f"  \n• Copago a su cargo: ${copago:.2f}\n"
                    respuesta += f"  \n• Su seguro paga: ${ahorro:.2f}\n\n"
                
                if len(hospitales) > 1:
                    respuesta += f"**🏥 Otras opciones (Hospitales) afiliados a su seguro:**\n"
                    for h in hospitales[1:4]:
                        respuesta += f"   \n• {h['nombre']} – {h['ciudad']} – ${h['costo_consulta_base']:.2f}\n"
                    respuesta += "\n"
            else:
                respuesta += "**🏥 Hospitales en red:** No se encontraron para esta especialidad. Contacta a tu aseguradora.\n\n"
            
            respuesta += "---\n✅ **Próximo paso:** Agenda una cita en el hospital recomendado. Lleva tu documento y carnet.\n"
            respuesta += "*Herramienta informativa. Siempre consulta a un profesional.*"
            
            st.markdown(respuesta)
            st.session_state.messages.append({"role": "assistant", "content": respuesta})
            st.session_state.final_shown = True
            st.session_state.force_final = False
            
            # Generar resumen de la conversación
            resumen = generar_resumen_conversacion(st.session_state.messages)
            
            guardar_conversacion_en_historial(
                especialidad, copago, primer_sintoma,
                st.session_state.messages.copy(),
                st.session_state.interaction_count,
                st.session_state.plan_selected_index,
                selected_label,
                resumen
            )
            st.rerun()
            
            # Generar resumen de la conversación
            resumen = generar_resumen_conversacion(st.session_state.messages)
            
            guardar_conversacion_en_historial(
                especialidad, copago, primer_sintoma,
                st.session_state.messages.copy(),
                st.session_state.interaction_count,
                st.session_state.plan_selected_index,
                selected_label,
                resumen
            )
            st.rerun()

if not st.session_state.viewing_history and (st.session_state.force_final or st.session_state.interaction_count >= MAX_INTERACTIONS) and not st.session_state.final_shown and plan_id:
    mostrar_respuesta_final()
    st.stop()

input_disabled = (plan_id is None) or st.session_state.viewing_history or st.session_state.final_shown
user_input = st.chat_input(
    "Describe tus síntomas...",
    disabled=input_disabled,
    key=f"chat_input_{st.session_state.reset_counter}"
)

if user_input and not st.session_state.viewing_history and not st.session_state.final_shown and plan_id:
    if not user_input.strip():
        st.warning("🔍 Por favor, describe tus síntomas. Ejemplo: 'Tengo dolor de cabeza'.")
    else:
        if es_saludo_sin_sintomas(user_input):
            saludo_resp = respuesta_saludo()
            st.session_state.messages.append({"role": "assistant", "content": saludo_resp})
            with st.chat_message("assistant"):
                st.markdown(saludo_resp)
            st.rerun()
        else:
            tiene_sintomas = contiene_sintomas(user_input)
            if es_peticion_atencion(user_input):
                # Añadir el mensaje del usuario al historial ANTES de activar la respuesta final
                st.session_state.messages.append({"role": "user", "content": user_input})
                with st.chat_message("user"):
                    st.markdown(user_input)
                
                if tiene_sintomas or st.session_state.interaction_count > 0:
                    st.session_state.force_final = True
                    st.rerun()
                else:
                    respuesta = "Para poder recomendarte el hospital y el costo, primero necesito que me describas tus síntomas."
                    st.session_state.messages.append({"role": "assistant", "content": respuesta})
                    with st.chat_message("assistant"):
                        st.markdown(respuesta)
                    st.rerun()
            else:
                if not es_agradecimiento(user_input):
                    st.session_state.interaction_count += 1
                st.session_state.messages.append({"role": "user", "content": user_input})
                with st.chat_message("user"):
                    st.markdown(user_input)
                with st.chat_message("assistant"):
                    with st.spinner("Analizando..."):
                        history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages 
                                   if not (m["role"] == "assistant" and "Copago estimado" in m["content"])]
                        respuesta_json = llamar_ia(history, SYSTEM_PROMPT, response_format=True)
                        try:
                            data = json.loads(respuesta_json)
                            rec = data.get("recomendaciones", "")
                            pregunta = data.get("pregunta_adicional", "")
                        except:
                            rec, pregunta = "No se pudo obtener recomendación.", ""
                        respuesta = f"**🩺 Recomendación:** {rec}"
                        # Mostrar pregunta solo si no es la última interacción
                        if pregunta and st.session_state.interaction_count < MAX_INTERACTIONS:
                            respuesta += f"\n\n**❓ Para ayudarte mejor:** {pregunta}"
                        st.markdown(respuesta)
                        st.session_state.messages.append({"role": "assistant", "content": respuesta})
                st.rerun()