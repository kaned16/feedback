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

# Estilos CSS avanzados con estética editorial minimalista (inspiración Apple/Notion)
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
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 48rem !important;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    h1, h2, h3 {
        color: #f9fafb !important;
        font-family: 'Inter', sans-serif;
        font-weight: 700;
    }

    /* Contenedor estético y limpio para la sección de carga de archivos */
    div[data-testid="stFileUploader"] {
        background-color: #0b0f19 !important;
        border: 2px dashed #4b5563 !important;
        border-radius: 1rem !important;
        padding: 1.5rem !important;
        text-align: center !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    
    div[data-testid="stFileUploader"]:hover {
        border-color: #8b5cf6 !important;
        background-color: #111827 !important;
    }

    /* Estilo elegante para el botón de carga interno de Streamlit */
    div[data-testid="stFileUploader"] button {
        background-color: #7c3aed !important;
        color: white !important;
        border: none !important;
        border-radius: 0.5rem !important;
        font-weight: 600 !important;
        padding: 0.5rem 1rem !important;
    }

    div[data-testid="stVideo"] {
        max-width: 260px;
        border-radius: 0.75rem;
        overflow: hidden;
        border: 1px solid #1f2937;
        margin: 0 auto;
    }
    div[data-testid="stVideo"] video {
        max-height: 150px;
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

# Título y Subtítulo
st.markdown("""
<div style="text-align: center; max-width: 44rem; margin: 0 auto 1.5rem auto;">
    <h2 style="font-size: 1.6rem; font-weight: 800; letter-spacing: -0.025em; margin-bottom: 0.5rem;">Evalua tu oratoria con precision de experto</h2>
    <p style="color: #9ca3af; font-size: 0.88rem; line-height: 1.5;">Sube un archivo, grabate directamente o ingresa un enlace de YouTube para recibir un analisis multimodal profundo.</p>
</div>
""", unsafe_allow_html=True)

# Centrar horizontalmente los botones/opciones usando columnas simétricas
_, col_center, _ = st.columns([0.5, 3, 0.5])

with col_center:
    input_option = st.pills(
        "Modo de entrada",
        options=["Subir Archivo", "Grabar Video", "YouTube"],
        default="Subir Archivo",
        label_visibility="collapsed"
    )

st.markdown("<div style='margin-bottom: 1.2rem;'></div>", unsafe_allow_html=True)

video_to_process = None

if input_option == "Subir Archivo":
    # Contenedor visualmente mejorado para la carga
    st.markdown("""
    <div style="background-color: #111827; border: 1px solid #1f2937; border-radius: 1rem; padding: 1.2rem; text-align: center; margin-bottom: 0.8rem;">
        <p style="color: #f3f4f6; font-weight: 600; font-size: 0.9rem; margin-bottom: 0.2rem;">Sube tu archivo de video</p>
        <p style="color: #9ca3af; font-size: 0.75rem;">Formatos compatibles: MP4, MOV, WEBM (Max. 200MB)</p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("", type=["mp4", "mov", "webm"], label_visibility="collapsed")
    if uploaded_file is not None:
        video_to_process = uploaded_file

elif input_option == "Grabar Video":
    st.markdown("<p style='text-align: center; color: #9ca3af; font-size: 0.85rem;'>Usa tu camara para grabar tu discurso directamente cuando estes listo.</p>", unsafe_allow_html=True)
    recorded_file = st.camera_input("Grabar discurso")
    if recorded_file is not None:
        video_to_process = recorded_file

elif input_option == "YouTube":
    st.markdown("<p style='text-align: center; color: #9ca3af; font-size: 0.85rem;'>Pega el enlace de un discurso o presentacion de YouTube:</p>", unsafe_allow_html=True)
    youtube_url = st.text_input("Enlace de YouTube", placeholder="https://www.youtube.com/watch?v=...")
    if youtube_url:
        st.info("Nota: Para un analisis multimodal optimo, te recomendamos usar la opcion de subir archivo o grabacion directa.")

if video_to_process is not None:
    st.markdown("<div style='margin-top: 1.2rem;'></div>", unsafe_allow_html=True)
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
                       - Estructura logica del mensaje y fuerza del llamado a la accion (CTA) o cierre.

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
    st.markdown("<h3 style='text-align: center; font-size: 0.95rem; color: #9ca3af; margin-bottom: 0.8rem;'>Que evaluara nuestra IA en tu intervencion?</h3>", unsafe_allow_html=True)
    
    col_i1, col_i2, col_i3, col_i4, col_i5 = st.columns(5)
    
    with col_i1:
        st.markdown("<div style='background-color: #111827; border: 1px solid #1f2937; padding: 0.4rem; border-radius: 0.5rem; text-align: center; height: 90px;'><div style='font-weight: 600; font-size: 0.65rem; color: #f9fafb;'>1. Conviccion</div><div style='font-size: 0.55rem; color: #9ca3af; margin-top: 0.2rem;'>Impacto</div></div>", unsafe_allow_html=True)
    with col_i2:
        st.markdown("<div style='background-color: #111827; border: 1px solid #1f2937; padding: 0.4rem; border-radius: 0.5rem; text-align: center; height: 90px;'><div style='font-weight: 600; font-size: 0.65rem; color: #f9fafb;'>2. Corporal</div><div style='font-size: 0.55rem; color: #9ca3af; margin-top: 0.2rem;'>Postura</div></div>", unsafe_allow_html=True)
    with col_i3:
        st.markdown("<div style='background-color: #111827; border: 1px solid #1f2937; padding: 0.4rem; border-radius: 0.5rem; text-align: center; height: 90px;'><div style='font-weight: 600; font-size: 0.65rem; color: #f9fafb;'>3. Voz</div><div style='font-size: 0.55rem; color: #9ca3af; margin-top: 0.2rem;'>Modulacion</div></div>", unsafe_allow_html=True)
    with col_i4:
        st.markdown("<div style='background-color: #111827; border: 1px solid #1f2937; padding: 0.4rem; border-radius: 0.5rem; text-align: center; height: 90px;'><div style='font-weight: 600; font-size: 0.65rem; color: #f9fafb;'>4. Pitch</div><div style='font-size: 0.55rem; color: #9ca3af; margin-top: 0.2rem;'>Persuasion</div></div>", unsafe_allow_html=True)
    with col_i5:
        st.markdown("<div style='background-color: #111827; border: 1px실; border: 1px solid #1f2937; padding: 0.4rem; border-radius: 0.5rem; text-align: center; height: 90px;'><div style='font-weight: 600; font-size: 0.65rem; color: #f9fafb;'>5. Emocion</div><div style='font-size: 0.55rem; color: #9ca3af; margin-top: 0.2rem;'>Empatia</div></div>", unsafe_allow_html=True)
