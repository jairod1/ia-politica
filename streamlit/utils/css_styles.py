"""
CSS Styles - HorizontAI
========================

Módulo centralizado para todos los estilos CSS de la aplicación.
"""

import streamlit as st

def aplicar_css_principal():
    """Aplica el CSS principal de la aplicación (sidebar, colores, botones)"""
    st.markdown("""
    <style>
    /* Sidebar - azul */
    section[data-testid="stSidebar"] {
        background-color: #2F5D81; /* Azul oscuro */
    }

    /* Texto sidebar: títulos, subtítulos, radio labels */
    section[data-testid="stSidebar"] * {
        color: #002B4E !important;
    }

    /* Leyendas específicas del sidebar */
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #FF6800 !important; /* Naranja para títulos */
        font-weight: bold;
    }

    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] .css-1d391kg {
        color: #c5e2ff !important; /* Azulado para texto descriptivo */
        font-size: 0.9em;
    }

    /* Texto de opciones seleccionadas en azul */
    div[data-baseweb="radio"] input:checked + div {
        color: #00B0F0 !important;
    }

    /* Subrayado del título principal (DEFAULT) */
    h1 {
        color: #002B4E;
        border-bottom: 2px solid #E6B800;
        padding-bottom: 0.2em;
        margin-bottom: 0.4em;
    }

    /* Título SIN línea (ESPECÍFICO) */
    .titulo-sin-linea {
        color: #002B4E !important;
        border-bottom: none !important;
        padding-bottom: 0.2em;
        margin-bottom: 0.4em;
    }

    /* Subtítulos */
    h2, h3 {
        color: #002B4E;
    }

    /* Botones mejorados con forma y colores */
    button[kind="primary"],
    .stButton > button {
        background-color: #E6B800;
        color: #002B4E;
        border: 2px solid #002B4E;
        border-radius: 8px; /* Esquinas redondeadas */
        padding: 0.5rem 1rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }

    /* Hover de botones */
    button[kind="primary"]:hover,
    .stButton > button:hover {
        background-color: #002B4E;
        color: #E6B800;
        transform: translateY(-2px); /* Efecto elevación */
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }

    /* Fondo general claro */
    body {
        background-color: #F7F6F2;
    }
    </style>
    """, unsafe_allow_html=True)

def aplicar_fondo_inicio():
    """Aplica la imagen de fondo desde GitHub solo en la página de Inicio - CORREGIDO PARA MÓVILES"""
    
    imagen_url = "https://raw.githubusercontent.com/jairod1/ia-politica/master/streamlit/images/Logotipo-HorizontAI.png"
    
    st.markdown(f"""
    <style>
    /* ELIMINAR TODOS LOS FONDOS BLANCOS SUPERIORES */
    [data-testid="stHeader"] {{
        background-color: transparent !important;
        display: none !important;
    }}

    /* Header principal de Streamlit */
    .stApp > header {{
        background-color: transparent !important;
        display: none !important;
    }}

    /* Contenedor principal del viewport */
    .main > div:first-child {{
        background-color: transparent !important;
    }}

    /* Forzar transparencia en TODOS los elementos superiores */
    [data-testid="stAppViewContainer"] > section:first-child,
    [data-testid="stAppViewContainer"] > div:first-child {{
        background-color: transparent !important;
    }}

    /* Si hay un banner o header específico */
    .stApp > div:first-child {{
        background-color: transparent !important;
    }}
    
    /* 🔧 FONDO CORREGIDO: USAR LAS MISMAS CONFIGURACIONES QUE LAS OTRAS IMÁGENES */
    [data-testid="stAppViewContainer"] {{
        background-image: linear-gradient(rgba(0, 0, 0, 0.15), rgba(0, 0, 0, 0.25)), 
                        url('{imagen_url}');
        background-size: cover;  /* 🔧 CAMBIO: cover como las otras imágenes */
        background-position: center center;  /* 🔧 CAMBIO: center como las otras */
        background-repeat: no-repeat;
        background-attachment: fixed;
        min-height: 100vh;
    }}
    
    /* Contenedor principal con fondo semi-transparente OSCURO para texto blanco */
    .main .block-container {{
        background-color: rgba(0, 0, 0, 0.25) !important;
        backdrop-filter: blur(5px);
        border-radius: 15px;
        padding: 2rem;
        margin: 1rem auto;
        max-width: 100%;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }}
    
    /* FORZAR TEXTO BLANCO - MÁS ESPECÍFICO */
    .main .block-container h1,
    .main .block-container h1 *,
    .stMarkdown h1,
    [data-testid="stMarkdownContainer"] h1 {{
        color: #ffffff !important;
        text-shadow: 2px 2px 6px rgba(0, 0, 0, 0.8) !important;
        font-weight: bold !important;
        text-align: center !important;
        margin-bottom: 1.5rem !important;
        font-size: 2.5rem !important;
    }}
    
    /* TODOS LOS TÍTULOS Y SUBTÍTULOS EN BLANCO */
    .main .block-container h2,
    .main .block-container h2 *,
    .main .block-container h3,
    .main .block-container h3 *,
    .main .block-container h4,
    .main .block-container h4 *,
    .stMarkdown h2,
    .stMarkdown h3,
    .stMarkdown h4,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3,
    [data-testid="stMarkdownContainer"] h4 {{
        color: #ffffff !important;
        text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.8) !important;
        font-weight: 600 !important;
    }}
    
    /* PÁRRAFOS Y TEXTO NORMAL EN BLANCO */
    .main .block-container p,
    .main .block-container p *,
    .main .block-container li,
    .main .block-container li *,
    .main .block-container div,
    .main .block-container span,
    .stMarkdown p,
    .stMarkdown li,
    .stMarkdown div,
    .stMarkdown span,
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li,
    [data-testid="stMarkdownContainer"] div,
    [data-testid="stMarkdownContainer"] span,
    [data-testid="stMarkdownContainer"] {{
        color: #ffffff !important;
        text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.8) !important;
        line-height: 1.6 !important;
    }}
    
    /* TEXTO FUERTE Y EM EN BLANCO */
    .main .block-container strong,
    .main .block-container b,
    .main .block-container em,
    .main .block-container i,
    .stMarkdown strong,
    .stMarkdown b,
    .stMarkdown em,
    .stMarkdown i {{
        color: #ffffff !important;
        text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.8) !important;
    }}
    
    /* ALERTAS Y CAJAS CON FONDO OSCURO */
    .main .block-container [data-testid="stAlert"],
    [data-testid="stAlert"] {{
        background-color: rgba(0, 0, 0, 0.4) !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        backdrop-filter: blur(3px) !important;
        border-radius: 10px !important;
        color: #ffffff !important;
    }}
    
    /* TEXTO DENTRO DE ALERTAS TAMBIÉN BLANCO */
    .main .block-container [data-testid="stAlert"] *,
    [data-testid="stAlert"] * {{
        color: #ffffff !important;
        text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.8) !important;
    }}
    
    /* COLUMNAS CON MEJOR ESPACIADO */
    .main .block-container [data-testid="column"] {{
        padding: 0 1rem;
    }}
    
    /* FORZAR BLANCO EN MARKDOWN Y OTROS CONTENEDORES */
    .element-container div,
    .element-container p,
    .element-container span,
    .css-1offfwp p,
    .css-1offfwp div,
    .css-1offfwp span {{
        color: #ffffff !important;
        text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.8) !important;
    }}
    
    /* CAPTION Y TEXTOS PEQUEÑOS */
    .main .block-container .caption,
    .stCaption,
    [data-testid="stCaptionContainer"] {{
        color: #ffffff !important;
        text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.8) !important;
    }}
    
    /* SUCCESS, WARNING, INFO BOXES */
    .stSuccess,
    .stWarning, 
    .stInfo,
    .stError {{
        background-color: rgba(0, 0, 0, 0.4) !important;
        color: #ffffff !important;
        border-radius: 10px !important;
    }}
    
    .stSuccess *,
    .stWarning *,
    .stInfo *,
    .stError * {{
        color: #ffffff !important;
        text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.8) !important;
    }}

        """, unsafe_allow_html=True)

def aplicar_fondo_comentarios_especifico(imagen_nombre_con_extension):
    """🎨 NUEVA FUNCIÓN: Aplica fondo específico para análisis de comentarios"""
    
    imagen_url = f"https://raw.githubusercontent.com/jairod1/ia-politica/master/streamlit/images/{imagen_nombre_con_extension}"
    
    zoom_porcentual = "100%"         
    posicion_horizontal = "center"     
    posicion_vertical = "center"       

    st.markdown(f"""
    <style>
    /* ELIMINAR TODOS LOS FONDOS BLANCOS SUPERIORES */
    [data-testid="stHeader"] {{
        background-color: transparent !important;
        display: none !important;
    }}

    /* Header principal de Streamlit */
    .stApp > header {{
        background-color: transparent !important;
        display: none !important;
    }}

    /* Contenedor principal del viewport */
    .main > div:first-child {{
        background-color: transparent !important;
    }}

    /* Forzar transparencia en TODOS los elementos superiores */
    [data-testid="stAppViewContainer"] > section:first-child,
    [data-testid="stAppViewContainer"] > div:first-child {{
        background-color: transparent !important;
    }}

    /* Si hay un banner o header específico */
    .stApp > div:first-child {{
        background-color: transparent !important;
    }}
    
    /* Fondo de la aplicación */
    [data-testid="stAppViewContainer"] {{
        background-image: linear-gradient(rgba(0, 0, 0, 0.15), rgba(0, 0, 0, 0.25)), 
                        url('{imagen_url}');
        background-size: cover;
        background-position: {posicion_horizontal} {posicion_vertical};
        background-repeat: no-repeat;
        background-attachment: fixed;
        min-height: 100vh;
    }}
    
    /* Contenedor principal con fondo semi-transparente OSCURO para texto blanco */
    .main .block-container {{
        background-color: rgba(0, 0, 0, 0.3) !important;
        backdrop-filter: blur(5px);
        border-radius: 15px;
        padding: 2rem;
        margin: 1rem auto;
        max-width: 100%;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.2);
    }}
    
    /* FORZAR TEXTO BLANCO - MÁS ESPECÍFICO */
    .main .block-container h1,
    .main .block-container h1 *,
    .stMarkdown h1,
    [data-testid="stMarkdownContainer"] h1 {{
        color: #ffffff !important;
        text-shadow: 2px 2px 6px rgba(0, 0, 0, 0.9) !important;
        font-weight: bold !important;
        text-align: center !important;
        margin-bottom: 1.5rem !important;
        font-size: 2.5rem !important;
    }}
    
    /* TODOS LOS TÍTULOS Y SUBTÍTULOS EN BLANCO */
    .main .block-container h2,
    .main .block-container h2 *,
    .main .block-container h3,
    .main .block-container h3 *,
    .main .block-container h4,
    .main .block-container h4 *,
    .stMarkdown h2,
    .stMarkdown h3,
    .stMarkdown h4,
    [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3,
    [data-testid="stMarkdownContainer"] h4 {{
        color: #ffffff !important;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.9) !important;
        font-weight: 600 !important;
    }}
    
    /* PÁRRAFOS Y TEXTO NORMAL EN BLANCO */
    .main .block-container p,
    .main .block-container p *,
    .main .block-container li,
    .main .block-container li *,
    .main .block-container div,
    .main .block-container span,
    .stMarkdown p,
    .stMarkdown li,
    .stMarkdown div,
    .stMarkdown span,
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] li,
    [data-testid="stMarkdownContainer"] div,
    [data-testid="stMarkdownContainer"] span,
    [data-testid="stMarkdownContainer"] {{
        color: #ffffff !important;
        text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.9) !important;
        line-height: 1.6 !important;
    }}
    
    /* TEXTO FUERTE Y EM EN BLANCO */
    .main .block-container strong,
    .main .block-container b,
    .main .block-container em,
    .main .block-container i,
    .stMarkdown strong,
    .stMarkdown b,
    .stMarkdown em,
    .stMarkdown i {{
        color: #ffffff !important;
        text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.9) !important;
    }}
    
    /* ALERTAS Y CAJAS CON FONDO OSCURO */
    .main .block-container [data-testid="stAlert"],
    [data-testid="stAlert"] {{
        background-color: rgba(0, 0, 0, 0.5) !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        backdrop-filter: blur(3px) !important;
        border-radius: 10px !important;
        color: #ffffff !important;
    }}
    
    /* TEXTO DENTRO DE ALERTAS TAMBIÉN BLANCO */
    .main .block-container [data-testid="stAlert"] *,
    [data-testid="stAlert"] * {{
        color: #ffffff !important;
        text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.9) !important;
    }}
    
    /* COLUMNAS CON MEJOR ESPACIADO */
    .main .block-container [data-testid="column"] {{
        padding: 0 1rem;
    }}
    
    /* FORZAR BLANCO EN MARKDOWN Y OTROS CONTENEDORES */
    .element-container div,
    .element-container p,
    .element-container span,
    .css-1offfwp p,
    .css-1offfwp div,
    .css-1offfwp span {{
        color: #ffffff !important;
        text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.9) !important;
    }}
    
    /* CAPTION Y TEXTOS PEQUEÑOS */
    .main .block-container .caption,
    .stCaption,
    [data-testid="stCaptionContainer"] {{
        color: #ffffff !important;
        text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.9) !important;
    }}
    
    /* SUCCESS, WARNING, INFO BOXES */
    .stSuccess,
    .stWarning, 
    .stInfo,
    .stError {{
        background-color: rgba(0, 0, 0, 0.5) !important;
        color: #ffffff !important;
        border-radius: 10px !important;
    }}
    
    .stSuccess *,
    .stWarning *,
    .stInfo *,
    .stError * {{
        color: #ffffff !important;
        text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.9) !important;
    }}
    
    /* TABS Y COMPONENTES ADICIONALES EN BLANCO */
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {{
        color: #ffffff !important;
        text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.9) !important;
    }}
    
    .stTabs [data-baseweb="tab-panel"] {{
        background-color: rgba(0, 0, 0, 0.2) !important;
        border-radius: 10px !important;
        padding: 1rem !important;
    }}
    
    /* TABLAS Y DATAFRAMES */
    .stDataFrame,
    .stTable {{
        background-color: rgba(0, 0, 0, 0.3) !important;
        border-radius: 10px !important;
    }}
    
    .stDataFrame *,
    .stTable * {{
        color: #ffffff !important;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.8) !important;
    }}
    </style>
    """, unsafe_allow_html=True)

def eliminar_fondo_inicio():
    """Remueve el fondo personalizado para otras páginas"""
    st.markdown("""
    <style>
    /* Restaurar fondo normal para otras páginas */
    .main > div {
        background-image: none !important;
        background-color: #F7F6F2 !important;
    }
    
    .main .block-container {
        background-color: transparent !important;
        backdrop-filter: none !important;
        border-radius: 0 !important;
        padding: 1rem !important;
        margin-top: 0 !important;
        box-shadow: none !important;
        border: none !important;
        max-width: 100% !important;
    }
    
    /* Restaurar estilos de texto normales */
    .main .block-container h1,
    .main .block-container h2,
    .main .block-container h3,
    .main .block-container h4,
    .main .block-container p,
    .main .block-container li {
        text-shadow: none !important;
        text-align: left !important;
        font-size: inherit !important;
    }
    </style>
    """, unsafe_allow_html=True)