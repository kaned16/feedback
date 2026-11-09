# -*- coding: utf-8 -*-
import os
import time
import streamlit as st
from google import genai
from google.genai import types

# Configuracion de la pagina, titulo y favicon oficial de Cuarto Espacio
st.set_page_config(
    page_title="Cuarto Espacio | Simulador de Oratoria",
    page_icon="https://cuartoespacio.co/wp-content/uploads/2021/04/cropped-favicon-1-32x32.png",
    layout="wide"
)

# Estilos CSS avanzados (Forzando la fila horizontal para los botones en movil y desktop)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .stApp {
        background-color: #030712;
        color: #f3f4f6;
        font-family: 'Inter', sans-serif;
    }
    
    .block-container {
        padding-top: 1.5rem !important;
        max-width: 55rem !important;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    h1, h2, h3 {
        color: #f9fafb !important;
        font-family: 'Inter', sans-serif;
        font-weight: 700;
    }
    
    /* Forzar que las 3 columnas de los botones esten siempre en una sola fila horizontal */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        gap: 0.5rem;
    }
    
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
        width: 33.33% !important;
        flex: 1 !important;
        min-width: 0 !important;
    }
    
    div.stButton > button {
        background-color: #111827 !important;
        color: #9ca3af !important;
        border: 1px solid #1f2937 !important;
        border-radius: 0.75rem !important;
        font-weight: 600 !important;
        padding: 0.5rem 0.25rem !important;
        font-size: 0.8rem !important;
        box-shadow: none !important;
        transition: all 0.2s ease !important;
        width: 100%;
        white-space: nowrap;
    }
    
    div.stButton > button:hover {
        background-color: #1f2937 !important;
        color: #ffffff !important;
        border-color: #374151 !important;
    }

    div[data-testid="stFileUploader"] {
        background-color: #111827;
        border: 2px dashed #374151;
        border-radius: 1rem;
        padding: 1rem;
        text-align: center;
    }
    div[data-testid="stFileUploader"]:hover {
        border-color: #8b5cf6;
    }

    div[data-testid="stVideo"] {
        max-width: 240px;
        border-radius: 0.75rem;
        overflow: hidden;
        border: 1px solid #1f2937;
    }
    div[data-testid="stVideo"] video {
        max-height: 140px;
        object-fit: cover;
    }
</style>
""", unsafe_allow_html=True)

# CARGA SEGURA DE LA API KEY DESDE LOS SECRETS DE STREAMLIT
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=API_KEY)
except Exception:
    client = None
    st.error("Error: Configura tu GEMINI_API_KEY en los Secrets de Streamlit Cloud.")

# Titulo y Subtitulo
st.markdown("""
<div style="text-align: center; max-width: 48rem; margin: 0 auto 1.5rem auto;">
    <h2 style="font-size: 2.0rem; font-weight: 800; letter-spacing: -0.025em; margin-bottom: 0.5rem;">Evalua tu oratoria con precision de experto</h2>
    <p style="color: #9ca3af; font-size: 0.95rem;">Sube un archivo, grabate directamente o ingresa un enlace de YouTube para recibir un analisis multimodal profundo.</p>
</div>
""", unsafe_allow_html=True)

if "input_mode" not in st.session_state:
    st.session_state["input_mode"] = "upload"

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Subir Archivo", key="btn_upload"):
        st.session_state["input_mode"] = "upload"
        st.rerun()

with col2:
    if st.button("Grabar Video", key="btn_record"):
        st.session_state["input_mode"] = "record"
        st.rerun()

with col3:
    if st.button("YouTube", key="btn_youtube"):
        st.session_state["input_mode"] = "youtube"
        st.rerun()

st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)

video_to_process = None

if st.session_state["input_mode"] == "upload":
    uploaded_file = st.file_uploader("Sube tu archivo de video (.mp4, .mov, .webm)", type=["mp4", "mov", "webm"])
    if uploaded_file is not None:
        video_to_process = uploaded_file

elif st.session_state["input_mode"] == "record":
    st.markdown("<p style='text-align: center; color: #9ca3af; font-size: 0.9rem;'>Usa tu camara para grabar tu discurso directamente cuando estes listo.</p>", unsafe_allow_html=True)
    recorded_file = st.camera_input("Grabar discurso")
    if recorded_file is not None:
        video_to_process = recorded_file

elif st.session_state["input_mode"] == "youtube":
    st.markdown("<p style='text-align: center; color: #9ca3af; font-size: 0.9rem;'>Pega el enlace de un discurso o presentacion de YouTube:</p>", unsafe_allow_html=True)
    youtube_url = st.text_input("Enlace de YouTube", placeholder="https://www.youtube.com/watch?v=...")
    if youtube_url:
        st.info("Nota: Para un analisis multimodal optimo, te recomendamos usar la opcion de subir archivo o grabacion directa.")

if video_to_process is not None:
    st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)
    col_vid, col_btn = st.columns([1, 2])
    
    with col_vid:
        st.video(video_to_process)
        
    with col_btn:
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        if st.button("Iniciar Analisis con IA", key="btn_analizar"):
            with st.spinner("Subiendo video y analizando a profundidad con Gemini..."):
                remote_file = None
                try:
                    raw_name = getattr(video_to_process, "name", "video_grabado.mp4")
                    safe_filename = "".join(c for c in raw_name if ord(c) < 128 and c not in '/\\?%*:|"<>')
                    if not safe_filename:
                        safe_filename = "video_grabado.mp4"
                        
                    temp_path = os.path.join("/tmp", safe_filename)
                    with open(temp_path, "wb") as f:
                        f.write(video_to_process.getbuffer())

                    remote_file = client.files.upload(file=temp_path)
                    
                    while remote_file.state.name == "PROCESSING":
                        time.sleep(2)
                        remote_file = client.files.get(name=remote_file.name)
                        
                    if remote_file.state.name != "ACTIVE":
                        raise Exception("El archivo no pudo ser procesado.")

                    prompt = """
                    Actua como un estricto, riguroso y experto coach de oratoria ejecutiva de Cuarto Espacio. 
                    Realiza un analisis multimodal exhaustivo y profesional de este video. Tu evaluacion debe estar estructurada exactamente con los siguientes apartados:

                    1. Nivel de Conviccion Global y Calificacion General:
                       - Da una valoracion directa sobre que tan convincente y persuasivo es el orador en general.
                       - Nivel de impacto percibido (escala de 1 a 10).

                    2. Lenguaje Corporal, Gestos y Postura:
                       - Evaluacion de la apertura de hombros, postura corporal y firmeza ejecutiva.
                       - Analisis de la expresividad facial y los gestos de las manos (aportan dinamismo o son distractores).

                    3. Voz, Entonacion y Contrastes Vocales:
                       - Modulacion, ritmo, volumen y proyeccion vocal.
                       - Uso de contrastes vocales (velocidad, enfasis, silencios y pausas estrategicas).

                    4. Estructura del Pitch, Discurso y Nivel de Persuasiuon:
                       - Como arranca el gancho inicial? Atrapa la atencion?
                       - Estructura logica del mensaje y fuerza del llamado a la acción (CTA) o cierre.

                    5. Conexion Emocional:
                       - Nivel de empatia, autenticidad y resonancia con la audiencia.
                    """
                    
                    response = client.models.generate_content(
                        model='gemini-3.8-flash',
                        contents=[remote_file, prompt]
                    )
                    
                    st.markdown("### Reporte Completo del Coach de Oratoria")
                    st.markdown(response.text)
                    
                except Exception as e:
                    error_str = str(e)
                    clean_error = "".join(c if ord(c) < 128 else ' ' for c in error_str)
                    st.error(f"Error de procesamiento: {clean_error}")
                    
                finally:
                    if remote_file:
                        try:
                            client.files.delete(name=remote_file.name)
                        except:
                            pass

else:
    # 5 ITEMS PRINCIPALES
    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; font-size: 1.1rem; color: #9ca3af; margin-bottom: 1rem;'>Que evaluara nuestra IA en tu intervencion?</h3>", unsafe_allow_html=True)
    
    col_i1, col_i2, col_i3, col_i4, col_i5 = st.columns(5)
    
    with col_i1:
        st.markdown("<div style='background-color: #111827; border: 1px solid #1f2937; padding: 1rem; border-radius: 0.75rem; text-align: center; height: 110px;'><div style='font-weight: 600; font-size: 0.85rem; color: #f9fafb;'>1. Conviccion Global</div><div style='font-size: 0.7rem; color: #9ca3af; margin-top: 0.4rem;'>Nivel de impacto general</div></div>", unsafe_allow_html=True)
    with col_i2:
        st.markdown("<div style='background-color: #111827; border: 1px solid #1f2937; padding: 1rem; border-radius: 0.75rem; text-align: center; height: 110px;'><div style='font-weight: 600; font-size: 0.85rem; color: #f9fafb;'>2. Lenguaje Corporal</div><div style='font-size: 0.7rem; color: #9ca3af; margin-top: 0.4rem;'>Postura y gestos de manos</div></div>", unsafe_allow_html=True)
    with col_i3:
        st.markdown("<div style='background-color: #111827; border: 1px solid #1f2937; padding: 1rem; border-radius: 0.75rem; text-align: center; height: 110px;'><div style='font-weight: 600; font-size: 0.85rem; color: #f9fafb;'>3. Voz y Tonalidad</div><div style='font-size: 0.7rem; color: #9ca3af; margin-top: 0.4rem;'>Modulacion y silencios</div></div>", unsafe_allow_html=True)
    with col_i4:
        st.markdown("<div style='background-color: #111827; border: 1px solid #1f2937; padding: 1rem; border-radius: 0.75rem; text-align: center; height: 110px;'><div style='font-weight: 600; font-size: 0.85rem; color: #f9fafb;'>4. Estructura Pitch</div><div style='font-size: 0.7rem; color: #9ca3af; margin-top: 0.4rem;'>Gancho y persuasion</div></div>", unsafe_allow_html=True)
    with col_i5:
        st.markdown("<div style='background-color: #111827; border: 1px solid #1f2937; padding: 1rem; border-radius: 0.75rem; text-align: center; height: 110px;'><div style='font-weight: 600; font-size: 0.85rem; color: #f9fafb;'>5. Conexion Emocional</div><div style='font-size: 0.7rem; color: #9ca3af; margin-top: 0.4rem;'>Empatia y resonancia</div></div>", unsafe_allow_html=True)
