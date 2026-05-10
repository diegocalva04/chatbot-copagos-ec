Asistente de Salud Ecuador – Estimador de Copago y Cobertura
Chatbot inteligente para pacientes en Ecuador que, a partir de la descripción de síntomas, sugiere una especialidad médica, calcula el copago según el plan de seguro y recomienda el hospital más económico dentro de la red.

Demo en vivo
https://diegocalva04-chatbot-copagos-ec-app-k5u71v.streamlit.app/

Funcionalidades principales
- Detección de síntomas por IA – Analiza lenguaje natural usando Groq (Llama 3.3) con fallback a Together AI.
- Recomendación de especialidad – Predice la especialidad más adecuada y explica el porqué.
- Cálculo de copago – Cruza la especialidad con el plan seleccionado desde una base de datos en Supabase.
- Hospital más económico en red – Ordena hospitales por costo de consulta base y muestra el más barato y alternativas.
- Límite de interacciones (3) – Evita gasto excesivo de tokens; tras 3 intercambios se genera la respuesta final automática.
- Activación anticipada – El usuario puede escribir “quiero atenderme”, “cotizar precio”, “cuánto cuesta la consulta” (y otras frases) para recibir la información final sin esperar las 3 interacciones.
- Historial de conversaciones – Guarda hasta 10 consultas completas (mensajes, especialidad, copago, plan, resumen IA) y permite cargarlas en modo solo lectura o eliminarlas.
- Modo oscuro / claro – Adaptación automática al tema del sistema operativo.
- 100% gratuito – Usa servicios free tier: Streamlit Cloud, Supabase, Groq, Together AI.

¿Cómo funciona?
1. El usuario selecciona su plan de seguro.
2. Describe sus síntomas en el chat.
3. El asistente responde con recomendaciones prácticas y hace preguntas concretas para profundizar.
4. Tras 3 interacciones (o si el usuario escribe una frase de atención), el sistema:
   - Revisa toda la conversación.
   - Determina la especialidad más probable.
   - Muestra el copago estimado.
   - Lista el hospital más económico y hasta 3 alternativas.
5. Cada conversación finalizada se guarda automáticamente en el historial lateral (últimas 10).
6. El usuario puede cargar conversaciones anteriores para revisarlas (solo lectura) o eliminarlas.

Tecnologías utilizadas
Frontend = Streamlit (Python)
IA (principal) = Groq Cloud – Llama 3.3 70B (gratuito)
IA (fallback) = Together AI – Llama 3.3 70B (crédito $25)
Base de datos = Supabase (PostgreSQL)
Despliegue = Streamlit Community Cloud
Control de versiones = Git + GitHub

Configuración local
1. Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/chatbot-copagos-ec.git
cd chatbot-copagos-ec

2. Crear entorno virtual e instalar dependencias
bash
python -m venv venv
source venv/bin/activate      # Linux/macOS
venv\Scripts\activate         # Windows
pip install -r requirements.txt

3. Configurar secretos (.streamlit/secrets.toml)
No se sube a GitHub. Crea el archivo manualmente con:
toml
SUPABASE_URL = "https://tureferencia.supabase.co"
SUPABASE_KEY = "tu_anon_key"
GROQ_API_KEY = "gsk_tu_clave"
TOGETHER_API_KEY = "tu_clave_together"

4. Inicializar la base de datos en Supabase
Ejecuta el script SQL (proporcionado en el repositorio o en la documentación) para crear las tablas:
aseguradoras, planes, especialidades, hospitales, copagos, redes_hospitales
Inserta datos de ejemplo (aseguradoras, planes, especialidades, hospitales, copagos y redes).

5. Ejecutar en local
bash
streamlit run app.py
Despliegue en Streamlit Cloud
Sube el código a GitHub (sin el archivo secrets.toml).
Ve a share.streamlit.io, conecta tu repositorio y selecciona app.py como archivo principal.
En la configuración de la app, agrega los secretos (mismo contenido de secrets.toml) en la sección Settings → Secrets.
Haz clic en Deploy. En pocos minutos tendrás tu asistente online.

Personalización avanzada
Añadir más aseguradoras, planes o especialidades → Edita la tabla correspondiente en Supabase y actualiza cargar_planes() si es necesario.
Cambiar límite de interacciones → Modifica MAX_INTERACTIONS en modules/config.py.
Ajustar prompts de IA → Edita modules/prompts.py (especialmente FINAL_PROMPT para cambiar el estilo de la explicación).
Modificar colores → Edita assets/styles.css (variables en :root y @media (prefers-color-scheme: dark)).

Contribuciones
Este proyecto fue desarrollado como parte de un concurso de programación con IA. Las contribuciones son bienvenidas (reportar issues, proponer mejoras).

Licencia
MIT – libre de usar, modificar y distribuir.

Autor
Diego Calva – GitHub
