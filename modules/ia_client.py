import streamlit as st
from openai import OpenAI

@st.cache_resource
def get_groq():
    return OpenAI(api_key=st.secrets["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")

@st.cache_resource
def get_together():
    return OpenAI(api_key=st.secrets["TOGETHER_API_KEY"], base_url="https://api.together.xyz/v1")

def llamar_ia(messages, system_prompt, response_format=True):
    groq = get_groq()
    together = get_together()
    full_messages = [{"role": "system", "content": system_prompt}] + messages
    
    kwargs = {
        "model": "llama-3.3-70b-versatile",
        "messages": full_messages,
        "temperature": 0.3
    }
    if response_format:
        kwargs["response_format"] = {"type": "json_object"}
    
    try:
        resp = groq.chat.completions.create(**kwargs)
        return resp.choices[0].message.content.strip()
    except Exception as e:
        st.warning(f"Groq falló: {e}. Intentando con Together...")
        kwargs["model"] = "meta-llama/Llama-3.3-70B-Instruct-Turbo"
        try:
            resp = together.chat.completions.create(**kwargs)
            return resp.choices[0].message.content.strip()
        except Exception as e2:
            st.error(f"Together también falló: {e2}")
            return "{}" if response_format else ""

def generar_resumen_conversacion(mensajes):
    if not mensajes:
        return "Conversación sin contenido."
    
    textos = []
    for msg in mensajes:
        if msg["role"] == "user":
            textos.append(f"Usuario: {msg['content']}")
        elif msg["role"] == "assistant" and "Copago estimado" not in msg["content"]:
            textos.append(f"Asistente: {msg['content'][:100]}")
    
    if not textos:
        return "Consulta médica registrada."
    
    resumen_prompt = f"""
    Genera un resumen de una sola frase (máximo 20 palabras) de la siguiente conversación médico-paciente. Describe los síntomas principales y la recomendación.
    Conversación:
    {chr(10).join(textos)}
    Responde SOLO con la frase, sin comillas.
    """
    try:
        resumen = llamar_ia(
            messages=[{"role": "user", "content": resumen_prompt}],
            system_prompt="Eres un asistente que resume conversaciones médicas de forma concisa.",
            response_format=False
        )
        resumen = resumen.strip().strip('"').strip("'")
        if len(resumen) > 100:
            resumen = resumen[:97] + "..."
        return resumen
    except Exception:
        return "Consulta sobre síntomas y recomendación médica."