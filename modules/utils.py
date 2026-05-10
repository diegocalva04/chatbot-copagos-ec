def es_saludo_sin_sintomas(texto):
    saludos = ["hola", "buenos días", "buenas tardes", "buenas noches", "qué tal", "como estás", "saludos", "ola", "hey"]
    sintomas = [
        "dolor", "fiebre", "tos", "cabeza", "mareo", "gripe", "resfriado", "estómago", "pecho", "garganta",
        "náusea", "vómito", "diarrea", "congestión", "escalofrío", "sudor", "alergia", "erupción", "sarpullido",
        "picazón", "hinchazón", "sangrado", "dificultad respiratoria", "falta de aire", "palpitaciones",
        "muscular", "articulación", "fatiga", "cansancio", "insomnio", "mareos", "temblor", "debilidad"
    ]
    tl = texto.lower().strip()
    tiene_saludo = any(s in tl for s in saludos)
    tiene_sintoma = any(s in tl for s in sintomas)
    return tiene_saludo and not tiene_sintoma

def contiene_sintomas(texto):
    sintomas = [
        "dolor", "fiebre", "tos", "cabeza", "mareo", "gripe", "resfriado", "estómago", "pecho", "garganta",
        "náusea", "vómito", "diarrea", "congestión", "escalofrío", "sudor", "alergia", "erupción", "sarpullido",
        "picazón", "hinchazón", "sangrado", "dificultad respiratoria", "falta de aire", "palpitaciones",
        "muscular", "articulación", "fatiga", "cansancio", "insomnio", "mareos", "temblor", "debilidad"
    ]
    tl = texto.lower().strip()
    return any(s in tl for s in sintomas)

def respuesta_saludo():
    return "¡Hola! Soy tu asistente de Ecuasalud. Por favor, descríbeme tus síntomas para poder ayudarte con recomendaciones."

def es_agradecimiento(texto):
    return any(g in texto.lower() for g in ["gracias", "agradezco", "thank you", "muy amable"])

def es_peticion_atencion(texto):
    frases = [
        "atender", "cita", "consultar costo", "cuánto cuesta", "quiero ir al médico",
        "necesito especialista", "hospital más económico", "dónde puedo ir", "precio consulta",
        "copago", "atencion", "atender en hospital", "atenderme",
        "cotizar", "cotización", "cotizar precio", "precio de consulta", "valor de la cita",
        "quiero saber el costo", "cuánto cuesta la cita", "tarifa", "cuánto me sale",
        "cuánto me cuesta", "precio atención", "costo de la consulta"
    ]
    tl = texto.lower().strip()
    return any(f in tl for f in frases)