"""
HorizontAI - Análisis Político Local de Marín (CORREGIDO - CRITERIOS UNIFICADOS + FONDOS ESPECÍFICOS)
=================================================================================

🔧 CORRECCIÓN FINAL: Unificar criterios para artículos polémicos entre análisis
con y sin sentimientos para obtener resultados consistentes.

🎨 NUEVO: Fondos específicos para análisis de comentarios y visualizaciones.
📁 SOPORTE: Imágenes en formato .jpg y .png según disponibilidad.
🔄 AMPLIADO: Partidos/políticos funcionan en comentarios Y visualizaciones.
📈 INCLUIDO: Artículos más Populares con fondo Popularidad.png.
"""

import streamlit as st
import pandas as pd
import nest_asyncio
import os
nest_asyncio.apply()
os.environ["STREAMLIT_USE_WATCHMAN"] = "false"

# Importar módulos utils
try:
    from utils.data_loaders import cargar_metricas, cargar_datos_comentarios, cargar_datos_comentarios_morrazo, cargar_datos_comentarios_marin
    from utils.data_processors import (
        procesar_articulos_polemicos, 
        procesar_articulos_polemicos_UNIFICADO,  # 🔧 FUNCIÓN UNIFICADA
        procesar_comentarios_populares, 
        procesar_comentarios_impopulares, 
        aplicar_filtros_temporales,
        obtener_articulos_polemicos_unificado  # 🔧 FUNCIÓN BASE UNIFICADA
    )
    from utils.political_comment_processors import (
        filtrar_comentarios_por_partidos_general,
        filtrar_comentarios_por_psoe,
        filtrar_comentarios_por_pp,
        filtrar_comentarios_por_bng,
        filtrar_comentarios_por_politicos_general,
        filtrar_comentarios_por_manuel_pazos,
        filtrar_comentarios_por_maria_ramallo,
        filtrar_comentarios_por_lucia_santos,
        procesar_comentarios_politicos_populares,
        procesar_comentarios_politicos_impopulares,
        procesar_articulos_politicos_polemicos
    )
    from utils.comment_sentiment_processors import (
        extraer_comentarios_para_analisis,
        resumir_sentimientos_por_articulo
    )
    from utils.sentiment_integration import (
        cargar_analizador_sentimientos, 
        inicializar_analizador,
        aplicar_analisis_sentimientos,
        mostrar_analisis_sentimientos_compacto,
    )
    from utils.visualizers import (
        mostrar_tabla_con_detalles_y_sentimientos,  # 🔧 PARA VISUALIZACIONES
        mostrar_tabla_articulos_polemicos, 
        mostrar_tabla_comentarios,
        mostrar_seccion_temporal,
        mostrar_seccion_comentarios_temporal,
        mostrar_tabla_comentarios_con_sentimientos,
        mostrar_explicacion_parametros,
        mostrar_tabla_articulos_agregados_con_sentimientos
    )
    # 🎨 NUEVO: Importar módulo CSS
    from utils.css_styles import (
        aplicar_css_principal,
        aplicar_fondo_inicio,
        aplicar_fondo_comentarios_especifico,
        eliminar_fondo_inicio
    )
except ImportError as e:
    st.error(f"❌ Error importando módulos: {e}")
    st.error("🔧 Asegúrate de que todos los archivos están en la carpeta 'utils/'")
    st.stop()

def obtener_fondo_segun_opcion(tipo_analisis, partido_especifico=None, politico_especifico=None):
    """Determina qué fondo aplicar según las opciones seleccionadas"""
    
    if tipo_analisis == "📊 Análisis General":
        return "Analisis.png"                     # Todos los archivos son PNG
    
    elif tipo_analisis == "🗳️ Comentarios sobre Partidos Políticos":
        mapeo_fondos_partidos = {
            "Todos los partidos": "Todos-partidos.png",    
            "🌹PSdeG-PSOE de Marín": "PSOE-Partido.png",     
            "🔵Partido Popular de Marín": "PP-Partido.jpg",  
            "🌀BNG - Marín": "BNG-Partido.png"               
        }
        return mapeo_fondos_partidos.get(partido_especifico)
    
    elif tipo_analisis == "👥 Comentarios sobre Políticos Locales":
        mapeo_fondos_politicos = {
            "Todos los políticos": "Todos-candidatos.png",   
            "🌹Manuel Pazos": "PSOE-Partido.png",              
            "🔵María Ramallo": "PP-Partido.jpg",               
            "🌀Lucía Santos": "BNG-Partido.png"                
        }
        return mapeo_fondos_politicos.get(politico_especifico)
    
    # Fondos para Análisis de Visualizaciones - Todos los archivos son PNG
    elif tipo_analisis == "📈 Artículos más Populares":
        return "Popularidad.png"                            
    
    elif tipo_analisis == "🏛️ Artículos sobre Partidos Políticos":
        mapeo_fondos_partidos_vis = {
            "Todos los partidos": "Todos-partidos.png",    
            "🌹PSdeG-PSOE de Marín": "PSOE-Partido.png",     
            "🔵Partido Popular de Marín": "PP-Partido.jpg",  
            "🌀BNG - Marín": "BNG-Partido.png"               
        }
        return mapeo_fondos_partidos_vis.get(partido_especifico)
    
    elif tipo_analisis == "👥 Artículos sobre Políticos Locales":
        mapeo_fondos_politicos_vis = {
            "Todos los políticos": "Todos-candidatos.png",  
            "🌹Manuel Pazos": "PSOE-Partido.png",             
            "🔵María Ramallo": "PP-Partido.jpg",              
            "🌀Lucía Santos": "BNG-Partido.png"               
        }
        return mapeo_fondos_politicos_vis.get(politico_especifico)
    
    return None

# Configuración de la página
st.set_page_config(
    page_title="HorizontAI",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🎨 MODULARIZADO: Aplicar CSS principal
aplicar_css_principal()

# Inicialización de variables globales
SENTIMENTS_AVAILABLE = False
AnalizadorArticulosMarin = None
analizar_articulos_marin = None
mensaje_carga = ""

# Cargar analizador de sentimientos al inicio
try:
    with st.spinner("🧠 Cargando sistema de análisis de sentimientos..."):
        AnalizadorArticulosMarin, analizar_articulos_marin, mensaje_carga = cargar_analizador_sentimientos()
        SENTIMENTS_AVAILABLE = (AnalizadorArticulosMarin is not None)
except Exception as e:
    SENTIMENTS_AVAILABLE = False
    mensaje_carga = f"❌ Error cargando analizador: {e}"

# Inicializar session_state para analizador global
if 'analizador_global' not in st.session_state:
    st.session_state.analizador_global = None

def get_analizador_global():
    """Obtiene el analizador global reutilizable"""
    if not SENTIMENTS_AVAILABLE:
        return None
        
    if st.session_state.analizador_global is None:
        try:
            with st.spinner("🧠 Inicializando analizador de sentimientos..."):
                st.session_state.analizador_global = inicializar_analizador(AnalizadorArticulosMarin)
                if st.session_state.analizador_global is None:
                    st.error("❌ Error inicializando analizador global")
                    return None
        except Exception as e:
            st.error(f"❌ Error inicializando analizador: {e}")
            return None
    
    return st.session_state.analizador_global


def procesar_comentarios_con_sentimientos_directo(df, analizador, top_n=20, filtro_popularidad=None):
    """
    🔧 VERSIÓN UNIFICADA CORREGIDA: Usa exactamente la misma lógica que la función sin analizador
    """
    
    if analizador is None:
        st.warning("⚠️ Analizador no disponible")
        return pd.DataFrame(), None, pd.DataFrame()
    
    # 🔧 CLAVE: Usar función unificada para obtener artículos polémicos
    if filtro_popularidad is None:  # Solo para artículos polémicos
        # Usar EXACTAMENTE la misma lógica que la función sin analizador
        df_articulos_polemicos = obtener_articulos_polemicos_unificado(df, top_n)
        
        if len(df_articulos_polemicos) == 0:
            st.warning("⚠️ No se encontraron artículos polémicos")
            return pd.DataFrame(), None, pd.DataFrame()
        
        # Extraer comentarios SOLO de estos artículos polémicos
        df_comentarios_completos = extraer_comentarios_para_analisis(df_articulos_polemicos)
        
        # Para artículos polémicos, usar TODOS los comentarios de los artículos seleccionados
        df_comentarios_filtrados = df_comentarios_completos.copy()
        
    else:
        # Para comentarios populares/impopulares, usar lógica anterior
        df_comentarios_completos = extraer_comentarios_para_analisis(df)
        
        if len(df_comentarios_completos) == 0:
            st.warning("⚠️ No se encontraron comentarios para analizar")
            return pd.DataFrame(), None, pd.DataFrame()

        # Aplicar filtros de popularidad
        df_comentarios_filtrados = df_comentarios_completos.copy()
        
        if filtro_popularidad == 'popular':
            df_comentarios_filtrados = df_comentarios_filtrados[df_comentarios_filtrados['likes'] > df_comentarios_filtrados['dislikes']]
            df_comentarios_filtrados = df_comentarios_filtrados.sort_values('net_score', ascending=False)
        elif filtro_popularidad == 'impopular':
            df_comentarios_filtrados = df_comentarios_filtrados[df_comentarios_filtrados['dislikes'] > df_comentarios_filtrados['likes']]
            df_comentarios_filtrados = df_comentarios_filtrados.sort_values('net_score', ascending=True)
        
        # Limitar a top_n comentarios
        df_comentarios_filtrados = df_comentarios_filtrados.head(top_n)
    
    # Verificar que hay comentarios filtrados para analizar
    if len(df_comentarios_filtrados) == 0:
        st.warning(f"⚠️ No hay comentarios {filtro_popularidad} para analizar")
        return pd.DataFrame(), None, df_comentarios_completos
    
    # Aplicar análisis de sentimientos
    try:
        df_analizado, reporte = aplicar_analisis_sentimientos(df_comentarios_filtrados, analizador)
        if df_analizado is None or len(df_analizado) == 0:
            st.error("❌ El análisis de sentimientos no devolvió datos")
            return df_comentarios_filtrados, None, df_comentarios_completos
                
        # Resumir por artículo
        df_resumido = resumir_sentimientos_por_articulo(df_analizado)
        
        # 🔧 ASEGURAR ORDENAMIENTO FINAL por número de comentarios (igual que sin analizador)
        if len(df_resumido) > 0 and filtro_popularidad is None:
            # Añadir información de número de comentarios del df original
            if hasattr(df_articulos_polemicos, '__len__') and len(df_articulos_polemicos) > 0:
                try:
                    mapping_comentarios = dict(zip(df_articulos_polemicos['title'], df_articulos_polemicos['n_comments']))
                    df_resumido['n_comments'] = df_resumido['title'].map(mapping_comentarios).fillna(0)
                    # Ordenar por número de comentarios descendente (mismo criterio)
                    df_resumido = df_resumido.sort_values('n_comments', ascending=False)
                except:
                    # Si el mapeo falla, mantener orden existente
                    pass
        
        return df_resumido, reporte, df_comentarios_completos
        
    except Exception as e:
        st.error(f"❌ Error aplicando análisis de sentimientos: {e}")
        return df_comentarios_filtrados, None, df_comentarios_completos
            
def procesar_comentarios_individuales_con_sentimientos(df, analizador, top_n=20, filtro_popularidad=None):
    """
    NUEVA FUNCIÓN: Para comentarios individuales con análisis de sentimientos completo
    
    Procesa comentarios individuales y genera tabla con análisis detallado para cada comentario.
    NO agrega por artículo - mantiene comentarios separados con su análisis individual.
    
    Args:
        df: DataFrame con artículos y comentarios
        analizador: Instancia del analizador de sentimientos
        top_n: Número de comentarios top para análisis
        filtro_popularidad: 'popular', 'impopular' o None
        
    Returns:
        tuple: (df_comentarios_analizados, reporte)
            - df_comentarios_analizados: DataFrame con comentarios y análisis individual
            - reporte: Reporte de análisis de sentimientos
    """
    if analizador is None:
        st.warning("⚠️ Analizador no disponible")
        return pd.DataFrame(), None
    
    # 1. Extraer TODOS los comentarios individuales
    df_comentarios = extraer_comentarios_para_analisis(df)
    
    if len(df_comentarios) == 0:
        st.warning("⚠️ No se encontraron comentarios para analizar")
        return pd.DataFrame(), None
    
    # 2. Aplicar filtros de popularidad
    if filtro_popularidad == 'popular':
        df_comentarios = df_comentarios[df_comentarios['likes'] > df_comentarios['dislikes']]
        df_comentarios = df_comentarios.sort_values('net_score', ascending=False)
    elif filtro_popularidad == 'impopular':
        df_comentarios = df_comentarios[df_comentarios['dislikes'] > df_comentarios['likes']]
        df_comentarios = df_comentarios.sort_values('net_score', ascending=True)
    else:
        # Para artículos polémicos: ordenar por valor absoluto del net_score
        df_comentarios['abs_net_score'] = abs(df_comentarios['net_score'])
        df_comentarios = df_comentarios.sort_values('abs_net_score', ascending=False)
    
    # 3. Limitar a top_n comentarios
    df_comentarios = df_comentarios.head(top_n)
    
    if len(df_comentarios) == 0:
        st.warning(f"⚠️ No hay comentarios {filtro_popularidad} para analizar")
        return pd.DataFrame(), None
    
    # 4. Aplicar análisis de sentimientos a comentarios individuales
    try:
        df_analizado, reporte = aplicar_analisis_sentimientos(df_comentarios, analizador)
        
        if df_analizado is None or len(df_analizado) == 0:
            st.error("❌ El análisis de sentimientos no devolvió datos")
            return df_comentarios, None
        
        # 5. Preparar tabla final con columnas específicas solicitadas
        df_tabla_final = df_analizado.copy()
        
        # PRESERVAR TEXTO ORIGINAL ANTES DE TRUNCAR
        df_tabla_final['texto_completo_original'] = df_tabla_final['title'].copy()

        # Columna: Vista previa del comentario (texto truncado)
        df_tabla_final['vista_previa_comentario'] = df_tabla_final['title'].apply(
            lambda x: str(x)[:20] + "..." if len(str(x)) > 20 else str(x)
        )
        
        # Columna: Fecha en formato AAAA-MM-DD
        if 'date' in df_tabla_final.columns:
            df_tabla_final['fecha_formateada'] = pd.to_datetime(df_tabla_final['date']).dt.strftime('%Y-%m-%d')
        else:
            df_tabla_final['fecha_formateada'] = 'No disponible'
        
        # Columna: Ubicación del comentario
        df_tabla_final['ubicacion_comentario'] = df_tabla_final.get('comment_location', 'No especificada')
        
        # Columnas de análisis de sentimientos (verificar que existen)
        columnas_sentimientos = ['idioma', 'tono_general', 'emocion_principal', 'intensidad_emocional', 'confianza_analisis']
        for col in columnas_sentimientos:
            if col not in df_tabla_final.columns:
                st.warning(f"⚠️ Columna {col} no encontrada en el análisis")
                df_tabla_final[col] = 'No disponible'
        
        # Columnas de métricas del comentario
        df_tabla_final['likes_comentario'] = df_tabla_final.get('likes', 0)
        df_tabla_final['dislikes_comentario'] = df_tabla_final.get('dislikes', 0)
        
        # Columna: Fuente del artículo
        df_tabla_final['fuente_articulo'] = df_tabla_final.get('source', 'No disponible')
        
        # Columna: Enlace del artículo
        df_tabla_final['enlace_articulo'] = df_tabla_final.get('link', '')
        
        if 'title_original' in df_tabla_final.columns:
            df_tabla_final['titulo_articulo_original'] = df_tabla_final['title_original']
        else:
            df_tabla_final['titulo_articulo_original'] = 'No disponible'

        # Y MODIFICAR columnas_finales para incluir el título del artículo:
        columnas_finales = [
            'vista_previa_comentario',    # Vista previa del comentario
            'texto_completo_original',    # Texto completo del comentario
            'comment_author',             # Autor del comentario
            'titulo_articulo_original',   # Título del artículo
            'fecha_formateada',           # Fecha (AAAA-MM-DD)
            'ubicacion_comentario',       # Ubicación
            'idioma',                     # Idioma
            'tono_general',               # Tono general
            'emocion_principal',          # Emoción dominante
            'intensidad_emocional',       # Intensidad
            'tematica',                   # Temática del comentario
            'likes_comentario',           # Likes
            'dislikes_comentario',        # Dislikes
            'confianza_analisis',         # Confianza en el análisis (0-1)
            'fuente_articulo',            # Fuente
            'enlace_articulo'             # Enlace
        ]
        
        # Verificar que todas las columnas existen (permitir que falte temática)
        columnas_existentes = [col for col in columnas_finales if col in df_tabla_final.columns]

        # 🔧 NUEVO: Manejo especial para temática
        if 'tematica' not in df_tabla_final.columns:
            st.warning("⚠️ Columna temática no disponible en el análisis")
            columnas_existentes = [col for col in columnas_existentes if col != 'tematica']

        if len(columnas_existentes) < len(columnas_finales) - 1:  # -1 para permitir que falte temática
            columnas_faltantes = set(columnas_finales) - set(columnas_existentes)
            st.warning(f"⚠️ Algunas columnas no están disponibles: {columnas_faltantes}")

        # 7. Crear DataFrame final con solo las columnas disponibles
        df_resultado = df_tabla_final[columnas_existentes].copy()
        
        return df_resultado, reporte
        
    except Exception as e:
        st.error(f"❌ Error aplicando análisis de sentimientos: {e}")
        return df_comentarios, None
    
# Header principal
st.markdown('<h1 class="titulo-sin-linea">🏛️HorizontAI🏛️</h1>', unsafe_allow_html=True)
st.markdown('<h1 class="titulo-sin-linea">Analizador IA de sentimientos políticos</h1>', unsafe_allow_html=True)

# Sidebar con opciones principales
st.sidebar.title("🧭 Menú principal ↙️")

opciones_principales = [
    "🏠 Inicio", 
    "🏘️ Visión General del Municipio", 
    "📊 Análisis de Visualizaciones", 
    "💬 Análisis de Comentarios", 
    "📞 Info. Técnica y Contacto"
]

opcion = st.sidebar.radio(
    label="Seleccione una opción:",
    options=opciones_principales,
    format_func=lambda x: x
)

# Configurar submenús según la opción seleccionada
analizador = None

if opcion == "📊 Análisis de Visualizaciones":
    st.sidebar.divider()
    st.sidebar.subheader("🔍 Tipo de Análisis")
    
    sub_opcion = st.sidebar.radio(
        label="Selecciona:",
        options=[
            "📈 Artículos más Populares", 
            "🏛️ Artículos sobre Partidos Políticos", 
            "👥 Artículos sobre Políticos Locales"
        ]
    )
        
    if SENTIMENTS_AVAILABLE:
        mostrar_sentimientos = st.toggle(
            "🎭 Activar análisis de sentimientos y emociones",
            value=False,
            help="Incluye análisis completo: tono, emociones, idioma, temática, contexto"
        )
        
        if mostrar_sentimientos:
            analizador = get_analizador_global()
            if analizador is None:
                st.error("❌ Error con analizador")
                mostrar_sentimientos = False
    else:
        mostrar_sentimientos = False
        st.info("⚠️ Análisis de sentimientos no disponible")
    
    # Submenús específicos
    if sub_opcion == "🏛️ Artículos sobre Partidos Políticos":
        st.sidebar.subheader("🗳️ Partido Específico")
        partido_especifico = st.sidebar.radio(
            label="Selecciona:",
            options=[
                "Todos los partidos", 
                "🌹PSdeG-PSOE de Marín", 
                "🔵Partido Popular de Marín", 
                "🌀BNG - Marín"
            ]
        )
    
    if sub_opcion == "👥 Artículos sobre Políticos Locales":
        st.sidebar.subheader("👤 Político Específico")
        politico_especifico = st.sidebar.radio(
            label="Selecciona:",
            options=[
                "Todos los políticos", 
                "🌹Manuel Pazos", 
                "🔵María Ramallo", 
                "🌀Lucía Santos"
            ]
        )

elif opcion == "💬 Análisis de Comentarios":
    st.sidebar.divider()
    st.sidebar.subheader("🗺️ Ubicación Geográfica")
    ubicacion_comentarios = st.sidebar.radio(
        label="Selecciona región:",
        options=[
            "🌍 Comentarios Globales", 
            "🏛️ Comentarios de O Morrazo y Pontevedra",
            "📍 Comentarios de Marín"
        ]
    )
    
    st.sidebar.subheader("🔍 Tipo de Análisis")
    tipo_analisis_comentarios = st.sidebar.radio(
        label="Selecciona análisis:",
        options=[
            "📊 Análisis General",
            "🗳️ Comentarios sobre Partidos Políticos",
            "👥 Comentarios sobre Políticos Locales"
        ]
    )
    
    if SENTIMENTS_AVAILABLE:
        mostrar_sentimientos = st.toggle(
            "🎭 Activar análisis de sentimientos y emociones",
            value=False,
            help="Incluye análisis emocional de cada comentario individual"
        )
        
        if mostrar_sentimientos:
            analizador = get_analizador_global()
            if analizador is None:
                st.error("❌ Error con analizador")
                mostrar_sentimientos = False
    else:
        mostrar_sentimientos = False
        st.info("⚠️ Análisis de sentimientos no disponible")

    # DEFINIR VARIABLES POR DEFECTO
    partido_comentarios = "Todos los partidos"
    politico_comentarios = "Todos los políticos"

    if tipo_analisis_comentarios == "🗳️ Comentarios sobre Partidos Políticos":
        st.sidebar.subheader("🗳️ Partido Específico")
        partido_comentarios = st.sidebar.radio(
            label="Selecciona:",
            options=[
                "Todos los partidos", 
                "🌹PSdeG-PSOE de Marín", 
                "🔵Partido Popular de Marín", 
                "🌀BNG - Marín"
            ]
        )

    if tipo_analisis_comentarios == "👥 Comentarios sobre Políticos Locales":
        st.sidebar.subheader("👤 Político Específico")
        politico_comentarios = st.sidebar.radio(
            label="Selecciona:",
            options=[
                "Todos los políticos", 
                "🌹Manuel Pazos", 
                "🔵María Ramallo", 
                "🌀Lucía Santos"
            ]
        )

# Función auxiliar para mostrar análisis de comentarios
def mostrar_analisis_comentarios_con_filtros(datos_comentarios, titulo_ubicacion, ubicacion_key, mostrar_sentimientos, analizador, tipo_analisis_comentarios, partido_comentarios=None, politico_comentarios=None):    
    """🔧 FUNCIÓN CORREGIDA: Usar criterios unificados para artículos polémicos"""
    
    if mostrar_sentimientos:
        st.success("""
        🧠 **Análisis avanzado de sentimientos en comentarios activado**
        
        Se analizará el contenido emocional de cada comentario individual.
        """)

        st.info("""
        ↖️ **Para visualizar mejor todas las columnas del análisis, cierra el menú principal**.
        """)
    
    if tipo_analisis_comentarios == "📊 Análisis General":
        st.title(f"💬 {titulo_ubicacion} - 📊 Análisis General")
        st.markdown(f"""
        **Análisis completo de comentarios** de {titulo_ubicacion.lower()}
        
        📊 Incluye artículos polémicos, comentarios populares e impopulares.
        """)
        
        try:
            comentarios_mayo_2025, comentarios_anio_2025, comentarios_historico = aplicar_filtros_temporales(datos_comentarios)
        except Exception as e:
            st.error(f"❌ Error aplicando filtros temporales: {e}")
            return
        
        tab1, tab2, tab3 = st.tabs(["🔥 Artículos polémicos", "👍 Comentarios populares", "👎 Comentarios impopulares"])
        
        with tab1:
            st.subheader(f"🔥 Artículos más polémicos - {titulo_ubicacion}")
            
            subtab1, subtab2, subtab3 = st.tabs(["📅 Último mes", "📆 Año en curso", "🗳️ Desde elecciones 2023"])
            
            with subtab1:
                if mostrar_sentimientos and analizador is not None:
                    df_resumido, reporte, df_comentarios_originales = procesar_comentarios_con_sentimientos_directo(
                        comentarios_mayo_2025, analizador, top_n=20, filtro_popularidad=None
                    )
                    mostrar_tabla_articulos_agregados_con_sentimientos(
                        df_resumido, 
                        f"Artículos polémicos - mayo 2025 ({titulo_ubicacion})", 
                        df_comentarios_originales=df_comentarios_originales,
                        reporte=reporte
                    )
                else:
                    # 🔧 USAR LA MISMA FUNCIÓN BASE
                    datos_polemicos = procesar_articulos_polemicos_UNIFICADO(comentarios_mayo_2025)
                    mostrar_tabla_articulos_polemicos(
                        datos_polemicos, 
                        f"mayo de 2025 ({titulo_ubicacion})",
                        key_suffix=f"polemicos_{ubicacion_key}_mes"
                    )
            
            with subtab2:
                if mostrar_sentimientos and analizador is not None:
                    df_resumido, reporte, df_comentarios_originales = procesar_comentarios_con_sentimientos_directo(
                        comentarios_anio_2025, analizador, top_n=20, filtro_popularidad=None
                    )
                    mostrar_tabla_articulos_agregados_con_sentimientos(
                        df_resumido, 
                        f"Artículos polémicos - año 2025 ({titulo_ubicacion})", 
                        df_comentarios_originales=df_comentarios_originales,
                        reporte=reporte
                    )
                else:
                    # 🔧 USAR LA MISMA FUNCIÓN BASE
                    datos_polemicos = procesar_articulos_polemicos_UNIFICADO(comentarios_anio_2025)
                    mostrar_tabla_articulos_polemicos(
                        datos_polemicos, 
                        f"año 2025 ({titulo_ubicacion})",
                        key_suffix=f"polemicos_{ubicacion_key}_anio"
                    )
            
            with subtab3:
                if mostrar_sentimientos and analizador is not None:
                    df_resumido, reporte, df_comentarios_originales = procesar_comentarios_con_sentimientos_directo(
                        comentarios_historico, analizador, top_n=20, filtro_popularidad=None
                    )
                    mostrar_tabla_articulos_agregados_con_sentimientos(
                        df_resumido, 
                        f"Artículos polémicos - histórico ({titulo_ubicacion})", 
                        df_comentarios_originales=df_comentarios_originales,
                        reporte=reporte
                    )
                else:
                    # 🔧 USAR LA MISMA FUNCIÓN BASE
                    datos_polemicos = procesar_articulos_polemicos_UNIFICADO(comentarios_historico)
                    mostrar_tabla_articulos_polemicos(
                        datos_polemicos, 
                        f"histórico ({titulo_ubicacion})",
                        key_suffix=f"polemicos_{ubicacion_key}_total"
                    )
        
        with tab2:
            st.subheader(f"👍 Comentarios más populares - {titulo_ubicacion}")
            
            subtab1, subtab2, subtab3 = st.tabs(["📅 Último mes", "📆 Año en curso", "🗳️ Desde elecciones 2023"])
            
            with subtab1:
                if mostrar_sentimientos and analizador is not None:
                    df_comentarios_analizados, reporte = procesar_comentarios_individuales_con_sentimientos(
                        comentarios_mayo_2025, analizador, top_n=20, filtro_popularidad='popular'
                        )
                    mostrar_tabla_comentarios_con_sentimientos(
                        df_comentarios_analizados, 
                        f"Comentarios populares - mayo 2025 ({titulo_ubicacion})",
                        mostrar_sentimientos=True,
                        reporte=reporte
                        )
                else:
                    mostrar_seccion_comentarios_temporal(
                        "📅 Mayo 2025",
                        f"Comentarios populares {titulo_ubicacion.lower()} de mayo de 2025",
                        comentarios_mayo_2025,
                        f"mayo de 2025 ({titulo_ubicacion})",
                        procesar_comentarios_populares,
                        lambda df, titulo, key_suffix, table_height=600: mostrar_tabla_comentarios(df, titulo, es_popular=True, key_suffix=key_suffix, table_height=table_height),
                        f"populares_{ubicacion_key}_mes"
                    )
            
            with subtab2:
                if mostrar_sentimientos and analizador is not None:
                    df_comentarios_analizados, reporte = procesar_comentarios_individuales_con_sentimientos(
                        comentarios_anio_2025, analizador, top_n=20, filtro_popularidad='popular'
                        )
                    mostrar_tabla_comentarios_con_sentimientos(
                        df_comentarios_analizados, 
                        f"Comentarios populares - año 2025 ({titulo_ubicacion})",
                        mostrar_sentimientos=True,
                        reporte=reporte
                        )
                else:
                    mostrar_seccion_comentarios_temporal(
                        "📆 Año 2025",
                        f"Comentarios populares {titulo_ubicacion.lower()} de 2025",
                        comentarios_anio_2025,
                        f"año 2025 ({titulo_ubicacion})",
                        procesar_comentarios_populares,
                        lambda df, titulo, key_suffix, table_height=600: mostrar_tabla_comentarios(df, titulo, es_popular=True, key_suffix=key_suffix, table_height=table_height),
                        f"populares_{ubicacion_key}_anio"
                    )
            
            with subtab3:
                if mostrar_sentimientos and analizador is not None:
                    df_comentarios_analizados, reporte = procesar_comentarios_individuales_con_sentimientos(
                        comentarios_historico, analizador, top_n=20, filtro_popularidad='popular'
                        )
                    mostrar_tabla_comentarios_con_sentimientos(
                        df_comentarios_analizados, 
                        f"Comentarios populares - histórico ({titulo_ubicacion})",
                        mostrar_sentimientos=True,
                        reporte=reporte
                        )
                else:
                    mostrar_seccion_comentarios_temporal(
                        "🗳️ Desde las elecciones locales del 28 de mayo de 2023",
                        f"Todos los comentarios populares históricos {titulo_ubicacion.lower()}",
                        comentarios_historico,
                        f"período histórico ({titulo_ubicacion})",
                        procesar_comentarios_populares,
                        lambda df, titulo, key_suffix, table_height=600: mostrar_tabla_comentarios(df, titulo, es_popular=True, key_suffix=key_suffix, table_height=table_height),
                        f"populares_{ubicacion_key}_total"
                    )
        
        with tab3:
            st.subheader(f"👎 Comentarios más impopulares - {titulo_ubicacion}")
            
            subtab1, subtab2, subtab3 = st.tabs(["📅 Último mes", "📆 Año en curso", "🗳️ Desde elecciones 2023"])
            
            with subtab1:
                if mostrar_sentimientos and analizador is not None:
                    df_comentarios_analizados, reporte = procesar_comentarios_individuales_con_sentimientos(
                        comentarios_mayo_2025, analizador, top_n=20, filtro_popularidad='impopular'
                    )
                    mostrar_tabla_comentarios_con_sentimientos(
                        df_comentarios_analizados, 
                        f"Comentarios impopulares - mayo 2025 ({titulo_ubicacion})",
                        mostrar_sentimientos=True,
                        reporte=reporte
                    )
                else:
                    mostrar_seccion_comentarios_temporal(
                        "📅 Mayo 2025",
                        f"Comentarios impopulares {titulo_ubicacion.lower()} de mayo de 2025",
                        comentarios_mayo_2025,
                        f"mayo de 2025 ({titulo_ubicacion})",
                        procesar_comentarios_impopulares,
                        lambda df, titulo, key_suffix, table_height=600: mostrar_tabla_comentarios(df, titulo, es_popular=False, key_suffix=key_suffix, table_height=table_height),
                        f"impopulares_{ubicacion_key}_mes"
                    )
            
            with subtab2:
                if mostrar_sentimientos and analizador is not None:
                    df_comentarios_analizados, reporte = procesar_comentarios_individuales_con_sentimientos(
                        comentarios_anio_2025, analizador, top_n=20, filtro_popularidad='impopular'
                    )
                    mostrar_tabla_comentarios_con_sentimientos(
                        df_comentarios_analizados, 
                        f"Comentarios impopulares - año 2025 ({titulo_ubicacion})",
                        mostrar_sentimientos=True,
                        reporte=reporte
                    )
                else:
                    mostrar_seccion_comentarios_temporal(
                        "📆 Año 2025",
                        f"Comentarios impopulares {titulo_ubicacion.lower()} de 2025",
                        comentarios_anio_2025,
                        f"año 2025 ({titulo_ubicacion})",
                        procesar_comentarios_impopulares,
                        lambda df, titulo, key_suffix, table_height=600: mostrar_tabla_comentarios(df, titulo, es_popular=False, key_suffix=key_suffix, table_height=table_height),
                        f"impopulares_{ubicacion_key}_anio"
                    )
            
            with subtab3:
                if mostrar_sentimientos and analizador is not None:
                    df_comentarios_analizados, reporte = procesar_comentarios_individuales_con_sentimientos(
                        comentarios_historico, analizador, top_n=20, filtro_popularidad='impopular'
                    )
                    mostrar_tabla_comentarios_con_sentimientos(
                        df_comentarios_analizados, 
                        f"Comentarios impopulares - histórico ({titulo_ubicacion})",
                        mostrar_sentimientos=True,
                        reporte=reporte
                    )
                else:
                    mostrar_seccion_comentarios_temporal(
                        "🗳️ Desde las elecciones locales del 28 de mayo de 2023",
                        f"Todos los comentarios impopulares históricos {titulo_ubicacion.lower()}",
                        comentarios_historico,
                        f"período histórico ({titulo_ubicacion})",
                        procesar_comentarios_impopulares,
                        lambda df, titulo, key_suffix, table_height=600: mostrar_tabla_comentarios(df, titulo, es_popular=False, key_suffix=key_suffix, table_height=table_height),
                        f"impopulares_{ubicacion_key}_total"
                    )
    
    elif tipo_analisis_comentarios == "🗳️ Comentarios sobre Partidos Políticos":
        filtros_partidos = {
            "Todos los partidos": ("🏛️ Partidos Políticos", filtrar_comentarios_por_partidos_general),
            "🌹PSdeG-PSOE de Marín": ("🌹 PSdeG-PSOE", filtrar_comentarios_por_psoe),
            "🔵Partido Popular de Marín": ("🔵 Partido Popular", filtrar_comentarios_por_pp),
            "🌀BNG - Marín": ("🌀 BNG", filtrar_comentarios_por_bng)
        }
        
        titulo_partido, funcion_filtro = filtros_partidos[partido_comentarios]
        
        st.title(f"💬 {titulo_ubicacion} - {titulo_partido}")
        st.markdown(f"""
        **Análisis de comentarios** {titulo_ubicacion.lower()} que mencionan {partido_comentarios.lower()}
        """)
        
        try:
            with st.spinner("💬 Filtrando comentarios políticos..."):
                datos_filtrados = funcion_filtro(datos_comentarios["filtered_data"])
                
                if len(datos_filtrados) == 0:
                    st.warning(f"⚠️ No se encontraron comentarios sobre {partido_comentarios} en {titulo_ubicacion}")
                    return
                
                st.success(f"✅ Encontrados {len(datos_filtrados)} artículos con comentarios sobre {partido_comentarios}")
        except Exception as e:
            st.error(f"❌ Error filtrando comentarios: {e}")
            return
        
        try:
            comentarios_mayo_2025, comentarios_anio_2025, comentarios_historico = aplicar_filtros_temporales({"filtered_data": datos_filtrados})
        except Exception as e:
            st.error(f"❌ Error aplicando filtros temporales: {e}")
            return
        
        tab1, tab2, tab3 = st.tabs(["🔥 Artículos polémicos", "👍 Comentarios populares", "👎 Comentarios impopulares"])
        
        with tab1:
            st.subheader(f"🔥 Artículos más polémicos - {titulo_ubicacion} + {partido_comentarios}")
            
            subtab1, subtab2, subtab3 = st.tabs(["📅 Último mes", "📆 Año en curso", "🗳️ Desde elecciones 2023"])
            
            for subtab, datos, periodo in zip([subtab1, subtab2, subtab3], 
                                            [comentarios_mayo_2025, comentarios_anio_2025, comentarios_historico],
                                            ["Mayo 2025", "Año 2025", "Histórico"]):
                with subtab:
                    if mostrar_sentimientos and analizador is not None:
                        # ✅ USAR FUNCIÓN CON SENTIMIENTOS
                        df_resumido, reporte, df_comentarios_originales = procesar_comentarios_con_sentimientos_directo(
                            datos, analizador, top_n=20, filtro_popularidad=None
                        )
                        mostrar_tabla_articulos_agregados_con_sentimientos(
                            df_resumido, 
                            f"Artículos polémicos sobre {partido_comentarios} - {periodo} ({titulo_ubicacion})", 
                            df_comentarios_originales=df_comentarios_originales,
                            reporte=reporte,
                            table_height=300
                        )
                    else:
                        # Versión sin sentimientos
                        mostrar_seccion_comentarios_temporal(
                            f"📅 {periodo}",
                            f"Artículos polémicos con comentarios sobre {partido_comentarios}",
                            datos,
                            f"{periodo.lower()} ({titulo_ubicacion} - {partido_comentarios})",
                            procesar_articulos_politicos_polemicos,
                            mostrar_tabla_articulos_polemicos,
                            f"polemicos_{ubicacion_key}_{partido_comentarios.lower().replace(' ', '_')}_{periodo.lower().replace(' ', '_')}",
                            table_height=300
                        )
        
        with tab2:
            st.subheader(f"👍 Comentarios más populares sobre {partido_comentarios}")
            
            subtab1, subtab2, subtab3 = st.tabs(["📅 Último mes", "📆 Año en curso", "🗳️ Desde elecciones 2023"])
            
            for subtab, datos, periodo in zip([subtab1, subtab2, subtab3], 
                                            [comentarios_mayo_2025, comentarios_anio_2025, comentarios_historico],
                                            ["mayo 2025", "año 2025", "histórico"]):
                with subtab:
                    if mostrar_sentimientos and analizador is not None:
                        df_comentarios_analizados, reporte = procesar_comentarios_individuales_con_sentimientos(
                            datos, analizador, top_n=20, filtro_popularidad='popular'
                        )
                        mostrar_tabla_comentarios_con_sentimientos(
                            df_comentarios_analizados, 
                            f"Comentarios populares sobre {partido_comentarios} - {periodo} ({titulo_ubicacion})",
                            mostrar_sentimientos=True,
                            reporte=reporte
                        )
                    else:
                        mostrar_seccion_comentarios_temporal(
                            f"📅 {periodo.title()}",
                            f"Comentarios populares sobre {partido_comentarios}",
                            datos,
                            f"{periodo} ({titulo_ubicacion} - {partido_comentarios})",
                            procesar_comentarios_politicos_populares,
                            lambda df, titulo, key_suffix, table_height=600: mostrar_tabla_comentarios(df, titulo, es_popular=True, key_suffix=key_suffix, table_height=table_height),
                            f"populares_{ubicacion_key}_{partido_comentarios.lower().replace(' ', '_')}_{periodo.replace(' ', '_')}",
                            table_height=300
                        )
        
        with tab3:
            st.subheader(f"👎 Comentarios más impopulares sobre {partido_comentarios}")
            
            subtab1, subtab2, subtab3 = st.tabs(["📅 Último mes", "📆 Año en curso", "🗳️ Desde elecciones 2023"])
            
            for subtab, datos, periodo in zip([subtab1, subtab2, subtab3], 
                                            [comentarios_mayo_2025, comentarios_anio_2025, comentarios_historico],
                                            ["mayo 2025", "año 2025", "histórico"]):
                with subtab:
                    if mostrar_sentimientos and analizador is not None:
                        df_comentarios_analizados, reporte = procesar_comentarios_individuales_con_sentimientos(
                            datos, analizador, top_n=20, filtro_popularidad='impopular'
                        )
                        mostrar_tabla_comentarios_con_sentimientos(
                            df_comentarios_analizados, 
                            f"Comentarios impopulares sobre {partido_comentarios} - {periodo} ({titulo_ubicacion})",
                            mostrar_sentimientos=True,
                            reporte=reporte
                        )
                    else:
                        mostrar_seccion_comentarios_temporal(
                            f"📅 {periodo.title()}",
                            f"Comentarios impopulares sobre {partido_comentarios}",
                            datos,
                            f"{periodo} ({titulo_ubicacion} - {partido_comentarios})",
                            procesar_comentarios_politicos_impopulares,
                            lambda df, titulo, key_suffix, table_height=600: mostrar_tabla_comentarios(df, titulo, es_popular=False, key_suffix=key_suffix, table_height=table_height),
                            f"impopulares_{ubicacion_key}_{partido_comentarios.lower().replace(' ', '_')}_{periodo.replace(' ', '_')}",
                            table_height=300
                        )
    
    elif tipo_analisis_comentarios == "👥 Comentarios sobre Políticos Locales":
        filtros_politicos = {
            "Todos los políticos": ("👥 Políticos Locales", filtrar_comentarios_por_politicos_general),
            "🌹Manuel Pazos": ("🌹 Manuel Pazos", filtrar_comentarios_por_manuel_pazos),
            "🔵María Ramallo": ("🔵 María Ramallo", filtrar_comentarios_por_maria_ramallo),
            "🌀Lucía Santos": ("🌀 Lucía Santos", filtrar_comentarios_por_lucia_santos)
        }
        
        titulo_politico, funcion_filtro = filtros_politicos[politico_comentarios]
        
        st.title(f"💬 {titulo_ubicacion} - {titulo_politico}")
        st.markdown(f"""
        **Análisis de comentarios** {titulo_ubicacion.lower()} que mencionan {politico_comentarios.lower()}
        """)
        
        try:
            with st.spinner("💬 Filtrando comentarios políticos..."):
                datos_filtrados = funcion_filtro(datos_comentarios["filtered_data"])
                
                if len(datos_filtrados) == 0:
                    st.warning(f"⚠️ No se encontraron comentarios sobre {politico_comentarios} en {titulo_ubicacion}")
                    return
                
                st.success(f"✅ Encontrados {len(datos_filtrados)} artículos con comentarios sobre {politico_comentarios}")
        except Exception as e:
            st.error(f"❌ Error filtrando comentarios: {e}")
            return
        
        try:
            comentarios_mayo_2025, comentarios_anio_2025, comentarios_historico = aplicar_filtros_temporales({"filtered_data": datos_filtrados})
        except Exception as e:
            st.error(f"❌ Error aplicando filtros temporales: {e}")
            return
        
        # Usar la misma estructura que partidos pero con políticos
        tab1, tab2, tab3 = st.tabs(["🔥 Artículos polémicos", "👍 Comentarios populares", "👎 Comentarios impopulares"])
        
        with tab1:
            st.subheader(f"🔥 Artículos más polémicos - {titulo_ubicacion} + {politico_comentarios}")
            
            subtab1, subtab2, subtab3 = st.tabs(["📅 Último mes", "📆 Año en curso", "🗳️ Desde elecciones 2023"])
            
            for subtab, datos, periodo in zip([subtab1, subtab2, subtab3], 
                                            [comentarios_mayo_2025, comentarios_anio_2025, comentarios_historico],
                                            ["Mayo 2025", "Año 2025", "Histórico"]):
                with subtab:
                    if mostrar_sentimientos and analizador is not None:
                        # ✅ USAR FUNCIÓN CON SENTIMIENTOS
                        df_resumido, reporte, df_comentarios_originales = procesar_comentarios_con_sentimientos_directo(
                            datos, analizador, top_n=20, filtro_popularidad=None
                        )
                        mostrar_tabla_articulos_agregados_con_sentimientos(
                            df_resumido, 
                            f"Artículos polémicos sobre {politico_comentarios} - {periodo} ({titulo_ubicacion})", 
                            df_comentarios_originales=df_comentarios_originales,
                            reporte=reporte,
                            table_height=300
                        )
                    else:
                        # Versión sin sentimientos
                        mostrar_seccion_comentarios_temporal(
                            f"📅 {periodo}",
                            f"Artículos polémicos con comentarios sobre {politico_comentarios}",
                            datos,
                            f"{periodo.lower()} ({titulo_ubicacion} - {politico_comentarios})",
                            procesar_articulos_politicos_polemicos,
                            mostrar_tabla_articulos_polemicos,
                            f"polemicos_{ubicacion_key}_{politico_comentarios.lower().replace(' ', '_')}_{periodo.lower().replace(' ', '_')}",
                            table_height=300
                        )
        
        with tab2:
            st.subheader(f"👍 Comentarios más populares sobre {politico_comentarios}")
            
            subtab1, subtab2, subtab3 = st.tabs(["📅 Último mes", "📆 Año en curso", "🗳️ Desde elecciones 2023"])
            
            for subtab, datos, periodo in zip([subtab1, subtab2, subtab3], 
                                            [comentarios_mayo_2025, comentarios_anio_2025, comentarios_historico],
                                            ["mayo 2025", "año 2025", "histórico"]):
                with subtab:
                    if mostrar_sentimientos and analizador is not None:
                        df_comentarios_analizados, reporte = procesar_comentarios_individuales_con_sentimientos(
                            datos, analizador, top_n=20, filtro_popularidad='popular'
                        )
                        mostrar_tabla_comentarios_con_sentimientos(
                            df_comentarios_analizados, 
                            f"Comentarios populares sobre {politico_comentarios} - {periodo} ({titulo_ubicacion})",
                            mostrar_sentimientos=True,
                            reporte=reporte
                        )
                    else:
                        mostrar_seccion_comentarios_temporal(
                            f"📅 {periodo.title()}",
                            f"Comentarios populares sobre {politico_comentarios}",
                            datos,
                            f"{periodo} ({titulo_ubicacion} - {politico_comentarios})",
                            procesar_comentarios_politicos_populares,
                            lambda df, titulo, key_suffix, table_height=600: mostrar_tabla_comentarios(df, titulo, es_popular=True, key_suffix=key_suffix, table_height=table_height),
                            f"populares_{ubicacion_key}_{politico_comentarios.lower().replace(' ', '_')}_{periodo.replace(' ', '_')}",
                            table_height=300
                        )
        
        with tab3:
            st.subheader(f"👎 Comentarios más impopulares sobre {politico_comentarios}")
            
            subtab1, subtab2, subtab3 = st.tabs(["📅 Último mes", "📆 Año en curso", "🗳️ Desde elecciones 2023"])
            
            for subtab, datos, periodo in zip([subtab1, subtab2, subtab3], 
                                            [comentarios_mayo_2025, comentarios_anio_2025, comentarios_historico],
                                            ["mayo 2025", "año 2025", "histórico"]):
                with subtab:
                    if mostrar_sentimientos and analizador is not None:
                        df_comentarios_analizados, reporte = procesar_comentarios_individuales_con_sentimientos(
                            datos, analizador, top_n=20, filtro_popularidad='impopular'
                        )
                        mostrar_tabla_comentarios_con_sentimientos(
                            df_comentarios_analizados, 
                            f"Comentarios impopulares sobre {politico_comentarios} - {periodo} ({titulo_ubicacion})",
                            mostrar_sentimientos=True,
                            reporte=reporte
                        )
                    else:
                        mostrar_seccion_comentarios_temporal(
                            f"📅 {periodo.title()}",
                            f"Comentarios impopulares sobre {politico_comentarios}",
                            datos,
                            f"{periodo} ({titulo_ubicacion} - {politico_comentarios})",
                            procesar_comentarios_politicos_impopulares,
                            lambda df, titulo, key_suffix, table_height=600: mostrar_tabla_comentarios(df, titulo, es_popular=False, key_suffix=key_suffix, table_height=table_height),
                            f"impopulares_{ubicacion_key}_{politico_comentarios.lower().replace(' ', '_')}_{periodo.replace(' ', '_')}",
                            table_height=300
                        )

# 🎨 GESTIÓN INTELIGENTE DE FONDOS
# Definir qué páginas tendrán fondos específicos
PAGINAS_CON_FONDO_ORIGINAL = [
    "🏠 Inicio", 
    "🏘️ Visión General del Municipio", 
    "📞 Info. Técnica y Contacto"
]

# 🎨 NUEVA LÓGICA: Aplicar fondos según la página y opciones seleccionadas
if opcion in PAGINAS_CON_FONDO_ORIGINAL:
    # Páginas con fondo original del logotipo
    aplicar_fondo_inicio()

elif opcion == "📊 Análisis de Visualizaciones":
    # 🎨 NUEVA LÓGICA: Fondos específicos para análisis de visualizaciones
    
    fondo_especifico = None
    
    if sub_opcion == "📈 Artículos más Populares":
        fondo_especifico = obtener_fondo_segun_opcion(sub_opcion)
    elif sub_opcion == "🏛️ Artículos sobre Partidos Políticos":
        fondo_especifico = obtener_fondo_segun_opcion(
            sub_opcion, 
            partido_especifico=partido_especifico
        )
    elif sub_opcion == "👥 Artículos sobre Políticos Locales":
        fondo_especifico = obtener_fondo_segun_opcion(
            sub_opcion, 
            politico_especifico=politico_especifico
        )
    
    # Aplicar fondo específico si está definido, sino eliminar fondo
    if fondo_especifico:
        aplicar_fondo_comentarios_especifico(fondo_especifico)
    else:
        eliminar_fondo_inicio()

elif opcion == "💬 Análisis de Comentarios":
    # 🎨 LÓGICA EXISTENTE: Fondos específicos para análisis de comentarios
    
    # Obtener nombre del fondo según las opciones seleccionadas
    fondo_especifico = None
    
    if tipo_analisis_comentarios == "📊 Análisis General":
        fondo_especifico = obtener_fondo_segun_opcion(tipo_analisis_comentarios)
    elif tipo_analisis_comentarios == "🗳️ Comentarios sobre Partidos Políticos":
        fondo_especifico = obtener_fondo_segun_opcion(
            tipo_analisis_comentarios, 
            partido_especifico=partido_comentarios
        )
    elif tipo_analisis_comentarios == "👥 Comentarios sobre Políticos Locales":
        fondo_especifico = obtener_fondo_segun_opcion(
            tipo_analisis_comentarios, 
            politico_especifico=politico_comentarios
        )
    
    # Aplicar fondo específico si está definido, sino eliminar fondo
    if fondo_especifico:
        aplicar_fondo_comentarios_especifico(fondo_especifico)
    else:
        eliminar_fondo_inicio()
        
else:
    # Otras páginas sin fondo especial
    eliminar_fondo_inicio()

# Contenido principal según la opción seleccionada
if opcion == "🏠 Inicio":

    st.markdown("""
    ### ¿Qué es 🏛️**HorizontAI**🏛️?
                
    **HorizontAI** es una herramienta de análisis político centrada en municipios pequeños y medianos
    que utiliza **inteligencia artificial emocional** para analizar visualizaciones y comentarios 
    ciudadanos en medios de comunicación locales. Esto proporciona una visión profunda de la opinión pública
    y ayuda a diseñar campañas efectivas.
                
    **HorizontAI** ha sido **diseñada para** ayudar a los políticos de hoy a ser **los líderes del mañana.**
    """)

    st.divider()
    st.markdown("### 📚 Información Técnica 📚")
    st.info("""
    **Si quieres conocer más detalles técnicos** sobre el funcionamiento del sistema, ve a la pestaña

     **📞 Info. Técnica y Contacto**
    """)  

    st.divider()
        
    # Mostrar estado del analizador
    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown("### 📊 Estado del Sistema 📊")
        if SENTIMENTS_AVAILABLE:
            st.success("""
            ✅ **Sistema Completo Operativo**
            
            🧠 IA Emocional: Activa
            🌍 Detección de Idioma: Activa  
            🎭 Análisis Granular: Activo
            📊 Métricas: Disponibles
            💬 Comentarios: Disponibles
            """)
        else:
            st.warning("⚠️ **Análisis de Sentimientos**: ❌ No disponible")
            st.caption("🔧 Revisa que el archivo advanced_sentiment_analyzer.py esté presente")

    with col2:
        
        if SENTIMENTS_AVAILABLE:
            pass
        else:
            st.warning("""
            ⚠️ **Sistema Parcialmente Operativo**
            
            📊 Métricas: Disponibles
            💬 Comentarios: Disponibles
            🧠 IA Emocional: No disponible
            """)

elif opcion == "🏘️ Visión General del Municipio":

    st.title("⛪Visión General de Marín⛪")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader('Información general')
        st.markdown("""
        **📍 Municipio:** Marín, Pontevedra  
        **👥 Población:** ~25.000 habitantes  
        **🏘️ Comarca:** O Morrazo  
        **🌍 Provincia:** Pontevedra, Galicia  
        **⚓ Características:** Villa marinera con tradición naval
        """)
        
        st.markdown("""
        **Últimas elecciones:** 28 de mayo de 2023  
        **Próximas elecciones:** 2027  
        **Reparto de concejalías en 2023:** 🔵 12 PP / 🔴 5 PSOE / 🌀 4 BNG<br>
        **Reparto de concejalías en 2019:** 🔵 15 PP / 🔴 5 PSOE / 🌀 1 BNG
        """, unsafe_allow_html=True)

    with col2:
        st.subheader("Panorama Político")
        st.markdown("""
        **Principales partidos activos:**
        - 🌹 **PSdeG-PSOE Marín**: Partido Socialista de Galicia - Partido Socialista Obrero Español
        - 🔵 **PP de Marín**: Partido Popular
        - 🌀 **BNG - Marín**: Bloque Nacionalista Galego
        
        **Políticos locales relevantes:**
        - 🔵 **María Ramallo**: Alcaldesa de Marín, PP
        - 🌹 **Manuel Pazos**: Secretario Local PSdeG-PSOE Marín 
        - 🌀 **Lucía Santos**: Secretaria Local BNG Marín
        """)

    st.markdown("""
        <h3 style='text-align: left; color: white;'>
        🗺️ Entorno político de Marín 🗺️
        </h3>
        """, unsafe_allow_html=True)


    st.components.v1.html(
        '''
        <div style="min-height:550px; color-scheme: dark;" id="datawrapper-vis-9YDQ6">
        <script type="text/javascript" defer 
            src="https://datawrapper.dwcdn.net/9YDQ6/embed.js" 
            charset="utf-8" 
            data-target="#datawrapper-vis-9YDQ6"
            data-dark="true">
        </script>
        <noscript><img src="https://datawrapper.dwcdn.net/9YDQ6/full.png" alt="" /></noscript>
        </div>
        ''',
        height=800
    )

    st.components.v1.html(
        '''
        <div style="min-height:559px; color-scheme: dark;" id="datawrapper-vis-Qql67">
        <script type="text/javascript" defer 
            src="https://datawrapper.dwcdn.net/Qql67/embed.js" 
            charset="utf-8"
            data-target="#datawrapper-vis-Qql67"
            data-dark="true">
        </script>
        <noscript><img src="https://datawrapper.dwcdn.net/Qql67/full.png" alt="" /></noscript>
        </div>
        ''',
        height=600
    )

    st.components.v1.html(
        '''
    <div style="min-height:416px; color-scheme: dark;" id="datawrapper-vis-AOYpH">
    <script type="text/javascript" defer 
        src="https://datawrapper.dwcdn.net/AOYpH/embed.js" 
        charset="utf-8" 
        data-target="#datawrapper-vis-AOYpH"
        data-dark="true">
    </script>
    <noscript><img src="https://datawrapper.dwcdn.net/AOYpH/full.png" alt="" /></noscript>
    </div>
        ''',
        height=450
    )

elif opcion == "📊 Análisis de Visualizaciones":
    try:
        with st.spinner("📊 Cargando métricas de visualización..."):
            metricas = cargar_metricas()
    except Exception as e:
        st.error(f"❌ Error cargando métricas: {e}")
        st.stop()
    
    if mostrar_sentimientos:
        st.success("🧠 **Análisis avanzado de sentimientos y emociones activado**")

        st.info("""
        ↖️ **Para visualizar mejor todas las columnas del análisis, cierra el menú principal**.
        """)
            
    if sub_opcion == "📈 Artículos más Populares":
        st.title("📈 Artículos más Populares")
        st.markdown("**Top 20 artículos con mayor número de visualizaciones** (todas las temáticas)")
        
        tab1, tab2, tab3 = st.tabs(["📅 Último mes", "📆 Año en curso", "🗳️ Desde elecciones 2023"])
        
        with tab1:
            mostrar_seccion_temporal(
                "📅 Mayo 2025",
                "Artículos publicados en mayo de 2025",
                metricas["top10_vis"]["mes"],
                "mayo de 2025",
                mostrar_sentimientos,
                analizador,
                es_articulos_populares=True
            )
        
        with tab2:
            mostrar_seccion_temporal(
                "📆 Año 2025",
                "Artículos publicados en 2025",
                metricas["top10_vis"]["anio"],
                "año 2025",
                mostrar_sentimientos,
                analizador,
                es_articulos_populares=True
            )
        
        with tab3:
            mostrar_seccion_temporal(
                "🗳️ Desde las elecciones locales del 28 de mayo de 2023",
                "Todos los artículos históricos ordenados por popularidad",
                metricas["top10_vis"]["total"],
                "período histórico",
                mostrar_sentimientos,
                analizador,
                es_articulos_populares=True
            )

    elif sub_opcion == "🏛️ Artículos sobre Partidos Políticos":
        mapeo_partidos = {
            "Todos los partidos": ("🏛️ Artículos sobre Partidos Políticos 🏛️", "Top 10 artículos que mencionan **PP, PSOE, BNG**", metricas["top10_partidos"]),
            "🌹PSdeG-PSOE de Marín": ("🌹 PSdeG-PSOE Marín 🌹", "Top 10 artículos que mencionan **PSOE o Partido Socialista**", metricas["top10_psoe"]),
            "🔵Partido Popular de Marín": ("🔵 Partido Popular de Marín 🔵", "Top 10 artículos que mencionan **PP o Partido Popular**", metricas["top10_pp"]),
            "🌀BNG - Marín": ("🌀 BNG - Marín 🌀", "Top 10 artículos que mencionan **BNG o Bloque**", metricas["top10_bng"])
        }
        
        titulo, descripcion, datos = mapeo_partidos[partido_especifico]
        st.title(titulo)
        st.markdown(f"{descripcion}\n\n📊 Los artículos se filtran por menciones específicas del partido.")
        
        tab1, tab2, tab3 = st.tabs(["📅 Último mes", "📆 Año en curso", "🗳️ Desde elecciones 2023"])
        
        with tab1:
            mostrar_seccion_temporal("📅 Mayo 2025", f"Artículos sobre {partido_especifico} publicados en mayo de 2025", datos["mes"], "mayo de 2025", mostrar_sentimientos, analizador, es_articulos_populares=False)
        
        with tab2:
            mostrar_seccion_temporal("📆 Año 2025", f"Artículos sobre {partido_especifico} publicados en 2025", datos["anio"], "año 2025", mostrar_sentimientos, analizador, es_articulos_populares=False)
        
        with tab3:
            mostrar_seccion_temporal("🗳️ Desde las elecciones locales del 28 de mayo de 2023", f"Todos los artículos sobre {partido_especifico} históricos", datos["total"], "período histórico", mostrar_sentimientos, analizador, es_articulos_populares=False)

    elif sub_opcion == "👥 Artículos sobre Políticos Locales":
        mapeo_politicos = {
            "Todos los políticos": ("👥 Artículos sobre Políticos Locales 👥", "Top 10 artículos que mencionan **Pazos, Ramallo, Santos**", metricas["top10_politicos"]),
            "🌹Manuel Pazos": ("🌹 Manuel Pazos 🌹", "Top 10 artículos que mencionan **Manuel Pazos**", metricas["top10_manuel"]),
            "🔵María Ramallo": ("🔵 María Ramallo 🔵", "Top 10 artículos que mencionan **María Ramallo o Ramallo**", metricas["top10_maria"]),
            "🌀Lucía Santos": ("🌀 Lucía Santos 🌀", "Top 10 artículos que mencionan **Lucía Santos**", metricas["top10_lucia"])
        }
        
        titulo, descripcion, datos = mapeo_politicos[politico_especifico]
        st.title(titulo)
        st.markdown(f"{descripcion}\n\n📊 Los artículos se filtran por menciones específicas del político.")
        
        tab1, tab2, tab3 = st.tabs(["📅 Último mes", "📆 Año en curso", "🗳️ Desde elecciones 2023"])
        
        with tab1:
            mostrar_seccion_temporal("📅 Mayo 2025", f"Artículos sobre {politico_especifico} publicados en mayo de 2025", datos["mes"], "mayo de 2025", mostrar_sentimientos, analizador, es_articulos_populares=False)
        
        with tab2:
            mostrar_seccion_temporal("📆 Año 2025", f"Artículos sobre {politico_especifico} publicados en 2025", datos["anio"], "año 2025", mostrar_sentimientos, analizador, es_articulos_populares=False)
        
        with tab3:
            mostrar_seccion_temporal("🗳️ Desde las elecciones locales del 28 de mayo de 2023", f"Todos los artículos sobre {politico_especifico} históricos", datos["total"], "período histórico", mostrar_sentimientos, analizador, es_articulos_populares=False)

elif opcion == "💬 Análisis de Comentarios":
    if ubicacion_comentarios == "🌍 Comentarios Globales":
        try:
            datos_comentarios = cargar_datos_comentarios()
            mostrar_analisis_comentarios_con_filtros(datos_comentarios, "Comentarios Globales", "global", mostrar_sentimientos, analizador, tipo_analisis_comentarios, partido_comentarios, politico_comentarios)
        except Exception as e:
            st.error(f"❌ Error cargando datos de comentarios globales: {e}")
            
    elif ubicacion_comentarios == "🏛️ Comentarios de O Morrazo y Pontevedra":
        try:
            datos_comentarios = cargar_datos_comentarios_morrazo()
            mostrar_analisis_comentarios_con_filtros(datos_comentarios, "O Morrazo y Pontevedra", "morrazo", mostrar_sentimientos, analizador, tipo_analisis_comentarios, partido_comentarios, politico_comentarios)
        except Exception as e:
            st.error(f"❌ Error cargando datos de comentarios de O Morrazo: {e}")
            
    elif ubicacion_comentarios == "📍 Comentarios de Marín":
        try:
            datos_comentarios = cargar_datos_comentarios_marin()
            mostrar_analisis_comentarios_con_filtros(datos_comentarios, "Marín", "marin", mostrar_sentimientos, analizador, tipo_analisis_comentarios, partido_comentarios, politico_comentarios)
        except Exception as e:
            st.error(f"❌ Error cargando datos de comentarios de Marín: {e}")

elif opcion == "📞 Info. Técnica y Contacto":
    st.title("📧 Información y Contacto 📧")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🛠️ Información Técnica")
        st.markdown("""
        **Desarrollado con:**
        - 📊 **VisualStudio**: Entorno de desarrollo
        - 🐍 **Python 3.12.9**: Lenguaje principal
        - 🎈 **Streamlit**: Framework de interfaz web
        - 💬 **DataWrapper**: Estadísticas municipales básicas
        - ⚙️ **Sistemas de IA utilizados**: Analizadores BETO y Bertinho, Transformers, NLTK
        """)
            
    with col2:
        st.subheader("📧 Soporte y Contacto")
        st.markdown("""
        **Para consultas y sugerencias:**
        
        - 🌌 **Creador y Desarrollador**: **Jaime Rodríguez**
        - 🌐 **Proyecto original para**: **Evolve Academy** 
        - 📧 **Email**: jairod.programar@gmail.com
        - 📱 **GitHub**: github.com/jairod1  
        - 📋 **LinkedIn**: https://www.linkedin.com/in/jaime-rodríguez-gonzález-a54526205/
        """)

    st.divider()

    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        #### 📊 Funciones Principales:
        
        - **🧠 Análisis Político**: Presentación política básica de tu localidad  
        - **📈 Métricas de Visualización**: Los artículos más leídos y con más impacto sobre ciudadanías locales
        - **📋 Estadísticas de Sentimientos**: Gráficos y estadísticas en funcion de los sentimientos y visualizaciones
        - **🔍 Filtros Avanzados**: Filtros de comentarios por términos políticos específicos (partidos y personas)
        - **🗺️ Análisis Geográfico**: Comentarios globales, de O Morrazo/Pontevedra y específicos de Marín
        - **🔢 Datos de Prueba**: Tomados de la localidad de Marín, Pontevedra, Galicia
        """)

    with col2:      
        if SENTIMENTS_AVAILABLE:
            st.markdown("""
            #### 🧠 Análisis Avanzado con IA Emocional:
            
            - **🌍 Detección de Idioma**: Reconoce gallego y castellano
            - **😊 Tono General**: Clasifica como positivo, negativo o neutral
            - **🎭 Emociones Granulares**: Detecta 10 emociones específicas
            - **🔥 Intensidad Emocional**: Escala del 1 (menos intenso) al 5
            - **📂 Clasificación Temática**: 9 categorías de contenido
            """)

    # 🔧 NUEVA SECCIÓN: Explicación de parámetros del análisis
    st.divider()
    mostrar_explicacion_parametros()

# Footer
st.divider()

footer_col1, footer_col2, footer_col3 = st.columns([2, 1, 1])

with footer_col1:
    if SENTIMENTS_AVAILABLE:
        st.caption("🏛️ **HorizontAI** - Análisis Político Local con IA Emocional | 🧠 Sistema Avanzado Operativo")
    else:
        st.caption("🏛️ **HorizontAI** - Análisis Político Local | ⚠️ Sistema Base Operativo")

with footer_col2:
    st.caption("📊 Datos actualizados automáticamente")

with footer_col3:
    st.caption("🗺️ Gallego + Castellano + Análisis Geográfico")

if SENTIMENTS_AVAILABLE:
    estado_analizador = "🧠 Cargado" if st.session_state.analizador_global is not None else "💤 En espera"
    st.caption(f"✅ **Estado**: Todos los sistemas operativos | 🎭 **Emociones**: 10 tipos | 🌍 **Idiomas**: 2 | 📂 **Temáticas**: 9 | 🗺️ **Análisis**: Global + O Morrazo + Marín | {estado_analizador}")
else:
    st.caption("⚠️ **Estado**: Sistema parcial | 📊 Métricas: Sí | 💬 Comentarios: Sí | 🧠 IA: No | 🗺️ Análisis: Global + O Morrazo + Marín")