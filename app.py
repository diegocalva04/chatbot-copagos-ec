import streamlit as st
from supabase import create_client, Client
from openai import OpenAI
import json
import re

st.set_page_config(page_title="Asistente de Salud Ecuador", page_icon="🏥", layout="centered")

# CSS para botón verde
st.markdown("""
<style>
button[kind="secondary"][data-testid="baseButton-secondary"] {
    background-color: #4CAF50 !important;
    color: white !important;
    border: none !important;
    font-weight: bold !important;
}
button[kind="secondary"][data-testid="baseButton-secondary"]:hover {
    background-color: #45a049 !important;
}
</style>
""", unsafe_allow_html=True)

# ========== CACHE ==========
@st.cache_resource
def init_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

@st.cache_resource
def init_groq():
    return OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")

@st.cache_resource
def init_together():
    return OpenAI(api_key=st.secrets["TOGETHER_API_KEY"], base_url="https://api.together.xyz/v1")

supabase = init_supabase()
groq_client = init_groq()
together_client = init_together()

GROQ_MODEL = "llama-3.3-70b-versatile"
TOGETHER_MODEL = "meta-llama/Llama-3.3-70B-Instruct-Turbo"

# Prompt para recomendaciones personalizadas
SYSTEM_PROMPT = """
Eres un asistente médico virtual experto en Ecuador. Analiza los síntomas del paciente y ofrece recomendaciones preventivas específicas para esos síntomas. No des diagnósticos. Responde SOLO en JSON:

{
    "recomendaciones": "Consejos prácticos detallados (60-100 palabras) basados directamente en los síntomas mencionados. Ejemplo: si dice 'dolor de cabeza', sugiere reposo en lugar oscuro, hidratación, evitar pantallas; si dice 'dolor de garganta', recomienda líquidos tibios, reposo vocal, evitar irritantes. Sé empático y útil.",
    "pregunta_adicional": "Haz una pregunta concreta para obtener más información relevante sobre los síntomas (ej. '¿El dolor es punzante o sordo?', '¿Tiene fiebre asociada?'). Si no es necesario, cadena vacía."
}

Reglas:
- No uses un tono alarmante. Sé tranquilizador y práctico.
- Si los síntomas son graves (dificultad respiratoria, dolor en pecho intenso, pérdida de conciencia), recomienda acudir a emergencias.
- No menciones especialidades, copagos ni hospitales.
"""

FINAL_PROMPT = """
Eres un asistente médico virtual experto en Ecuador. Con base en toda la conversación, determina:

1. La especialidad médica más adecuada.
2. Una breve razón (máximo 20 palabras).
3. Recomendaciones preventivas finales (máximo 30 palabras).

Responde SOLO en JSON:
{
    "especialidad": "nombre exacto",
    "razon": "explicación breve",
    "recomendaciones": "consejos preventivos"
}

Especialidades válidas:
Medicina General, Cardiología, Dermatología, Ginecología, Pediatría, Traumatología, Oftalmología, Otorrinolaringología, Neurología, Psicología, Urología, Neumología, Reumatología, Endocrinología, Gastroenterología, Oncología, Nefrología, Hematología, Infectología, Geriatría, Cirugía General, Nutrición Clínica.
"""

# ========== UTILIDADES ==========
def es_saludo_sin_sintomas(texto):
    texto_limpio = texto.lower().strip()
    saludos = ["hola", "buenos días", "buenas tardes", "buenas noches", "saludos", "qué tal", "como estás", "buen día", "ola"]
    sintomas_keywords = ["dolor", "fiebre", "tos", "cabeza", "estómago", "gripe", "resfriado", "mareo", "náusea", "vómito", "diarrea", "congestión", "garganta", "pecho", "espalda", "muscular", "articulación", "fatiga", "cansancio", "escalofrío", "sudor", "alergia", "erupción", "sarpullido", "picazón", "hinchazón", "sangrado", "dificultad respiratoria", "falta de aire", "palpitaciones"]
    es_saludo = any(saludo in texto_limpio for saludo in saludos)
    tiene_sintomas = any(sintoma in texto_limpio for sintoma in sintomas_keywords)
    return es_saludo and not tiene_sintomas

def es_agradecimiento(texto):
    palabras = texto.lower().strip()
    gracias = ["gracias", "agradezco", "thank you", "thanks", "muy amable", "excelente atención"]
    return any(g in palabras for g in gracias)

def llamar_ia(messages, prompt_type="initial"):
    providers = [
        (groq_client, GROQ_MODEL, "Groq"),
        (together_client, TOGETHER_MODEL, "Together AI")
    ]
    system_prompt = SYSTEM_PROMPT if prompt_type == "initial" else FINAL_PROMPT
    full_messages = [{"role": "system", "content": system_prompt}] + messages
    
    for client, model, name in providers:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=full_messages,
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            raw = response.choices[0].message.content.strip()
            if raw.startswith("```json"):
                raw = raw[7:]
            if raw.endswith("```"):
                raw = raw[:-3]
            data = json.loads(raw)
            if prompt_type == "initial":
                return data.get("recomendaciones", ""), data.get("pregunta_adicional", "")
            else:
                return data.get("especialidad", "Medicina General"), data.get("razon", ""), data.get("recomendaciones", "")
        except Exception as e:
            st.warning(f"{name} falló: {e}")
            continue
    st.error("Todos los proveedores de IA fallaron.")
    if prompt_type == "initial":
        return "Consulta a un médico si los síntomas persisten. Mantén reposo, hidrátate y evita automedicarte.", ""
    else:
        return "Medicina General", "No se pudo analizar.", "Reposo e hidratación."

def buscar_copago_y_hospitales(especialidad, plan_id):
    try:
        esp = supabase.table("especialidades").select("id").eq("nombre", especialidad).execute()
        if not esp.data:
            return None, []
        esp_id = esp.data[0]["id"]
        copago_res = supabase.table("copagos").select("valor_copago").eq("plan_id", plan_id).eq("especialidad_id", esp_id).execute()
        copago = copago_res.data[0]["valor_copago"] if copago_res.data else None
        red_res = supabase.table("redes_hospitales").select("hospital_id").eq("plan_id", plan_id).execute()
        hospital_ids = [h["hospital_id"] for h in red_res.data] if red_res.data else []
        if hospital_ids:
            hosp_res = supabase.table("hospitales").select("nombre, ciudad, costo_consulta_base").in_("id", hospital_ids).execute()
            hospitales = hosp_res.data if hosp_res.data else []
            hospitales.sort(key=lambda x: x["costo_consulta_base"])
            return copago, hospitales
        return copago, []
    except Exception as e:
        st.error(f"Error en base de datos: {e}")
        return None, []

def cargar_planes():
    ase = supabase.table("aseguradoras").select("id, nombre").execute()
    ase_dict = {a["id"]: a["nombre"] for a in ase.data}
    planes = supabase.table("planes").select("id, nombre, aseguradora_id").execute()
    options = {}
    for p in planes.data:
        options[f"{ase_dict.get(p['aseguradora_id'], 'Desconocida')} - {p['nombre']}"] = p["id"]
    return options

# ========== INTERFAZ ==========
st.title("Asistente de Salud - Copagos Ecuador")
st.markdown("Describe tus síntomas para recibir recomendaciones personalizadas. Cuando estés listo para atenderte, usa el botón en la barra lateral.")

# Sidebar con selector de plan sin valor por defecto
with st.sidebar:
    st.header("Opciones")
    if st.button("Nueva consulta", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pending_attention = False
        st.session_state.plan_seleccionado = None
        st.rerun()
    st.markdown("---")
    
    plan_options = cargar_planes()
    plan_list = ["-- Selecciona tu plan --"] + list(plan_options.keys())
    selected_label = st.selectbox("Plan de seguro", plan_list, index=0)
    if selected_label == "-- Selecciona tu plan --":
        plan_id = None
        st.warning("⚠️ Por favor, selecciona tu plan de seguro para continuar.")
    else:
        plan_id = plan_options[selected_label]
        st.session_state.plan_seleccionado = plan_id
        st.success("Plan seleccionado correctamente.")
    
    st.markdown("---")
    if st.button("Quiero atenderme", type="secondary", use_container_width=True):
        if plan_id is None:
            st.error("Primero debes seleccionar tu plan de seguro arriba.")
        else:
            st.session_state.pending_attention = True
            st.rerun()
    st.caption("Consulta siempre a un profesional. Sistema estimador.")

# Inicializar estado
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_attention" not in st.session_state:
    st.session_state.pending_attention = False
if "plan_seleccionado" not in st.session_state:
    st.session_state.plan_seleccionado = None

# Mostrar historial
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Procesar atención pendiente (solo si hay plan seleccionado)
if st.session_state.pending_attention and plan_id is not None:
    if not (st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant" and "Copago estimado" in st.session_state.messages[-1]["content"]):
        with st.chat_message("assistant"):
            with st.spinner("Preparando información de tu cobertura..."):
                history_for_final = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages if not (m["role"] == "assistant" and "Copago estimado" in m["content"])]
                especialidad, razon, recomendaciones = llamar_ia(history_for_final, prompt_type="final")
                copago, hospitales = buscar_copago_y_hospitales(especialidad, plan_id)
                
                respuesta = f"**Especialidad sugerida:** {especialidad}\n\n"
                respuesta += f"**Justificación:** {razon}\n\n"
                if recomendaciones:
                    respuesta += f"**Recomendaciones:** {recomendaciones}\n\n"
                if copago:
                    respuesta += f"**Copago estimado:** ${copago:.2f} USD\n\n"
                else:
                    respuesta += "**Copago:** No registrado. Verifica con tu aseguradora.\n\n"
                if hospitales:
                    mejor = hospitales[0]
                    respuesta += f"**Hospital más económico en tu red:** {mejor['nombre']} ({mejor['ciudad']}) - ${mejor['costo_consulta_base']:.2f}\n\n"
                    if len(hospitales) > 1:
                        respuesta += "Otras opciones:\n" + "\n".join([f"- {h['nombre']} ({h['ciudad']}) - ${h['costo_consulta_base']:.2f}" for h in hospitales[1:4]]) + "\n\n"
                else:
                    respuesta += "**Hospitales en red:** No se encontraron.\n\n"
                st.markdown(respuesta)
                st.session_state.messages.append({"role": "assistant", "content": respuesta})
                st.session_state.pending_attention = False
                st.rerun()

# Entrada del usuario
user_input = st.chat_input("Ejemplo: 'Tengo dolor de cabeza y fiebre'")
if user_input:
    # Verificar plan seleccionado
    if plan_id is None:
        with st.chat_message("assistant"):
            st.warning("Por favor, selecciona tu plan de seguro en la barra lateral antes de comenzar.")
    else:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # --- Agradecimientos ---
        if es_agradecimiento(user_input):
            final_respondida = any("Copago estimado" in msg["content"] for msg in st.session_state.messages if msg["role"] == "assistant")
            if final_respondida:
                respuesta = "Ha sido un placer ayudarle. Cuide su salud y que tenga un excelente día. ¡Hasta pronto!"
            else:
                respuesta = "De nada, estamos para servirle. ¿Puedo ayudarle con algo más sobre sus síntomas?"
            with st.chat_message("assistant"):
                st.markdown(respuesta)
            st.session_state.messages.append({"role": "assistant", "content": respuesta})
        elif es_saludo_sin_sintomas(user_input):
            with st.chat_message("assistant"):
                respuesta = "Buenos días. Soy su asistente de salud. Por favor, descríbame sus síntomas para poder ofrecerle recomendaciones adecuadas."
                st.markdown(respuesta)
                st.session_state.messages.append({"role": "assistant", "content": respuesta})
        else:
            # Detectar si quiere atenderse por texto
            if any(phrase in user_input.lower() for phrase in ["atender", "cita", "consultar costo", "cuánto cuesta", "quiero ir al médico", "necesito especialista"]):
                st.session_state.pending_attention = True
                st.rerun()
            
            # Procesar síntomas
            with st.chat_message("assistant"):
                with st.spinner("Analizando tus síntomas..."):
                    history_for_initial = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages if not (m["role"] == "assistant" and "Copago estimado" in m["content"])]
                    recomendaciones, pregunta = llamar_ia(history_for_initial, prompt_type="initial")
                    respuesta = f"**Recomendaciones:** {recomendaciones}"
                    if pregunta:
                        respuesta += f"\n\n**Para ayudarte mejor:** {pregunta}"
                    respuesta += "\n\n*Cuando estés listo para conocer los costos y la especialidad, presiona el botón 'Quiero atenderme' en la barra lateral.*"
                    st.markdown(respuesta)
                    st.session_state.messages.append({"role": "assistant", "content": respuesta})