"""
Data Loaders - HorizontAI
==========================

Funciones para cargar y procesar datos de métricas y comentarios.
"""

import streamlit as st
import pandas as pd
import os

# === FUNCIÓN ROBUSTA PARA DETECTAR LA RAÍZ DEL PROYECTO ===
def get_project_root():
    """
    Sube directorios hasta encontrar la carpeta raíz del proyecto (la que contiene /data).
    """
    current = os.path.abspath(__file__)
    while current != "/" and current:
        if os.path.isdir(os.path.join(current, "data")):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("No se encontró la carpeta raíz del proyecto (con /data dentro).")

@st.cache_data  # Cache para mejorar rendimiento
def cargar_metricas():
    """
    Carga todos los archivos de métricas y devuelve los top 20 de cada categoría con filtros de fecha correctos
    """
    # Definir rutas base (desde el directorio del script de streamlit)
    # Asumiendo que app.py está en streamlit/ y data/ está en la raíz del proyecto
    vis_path = os.path.join("..", "data", "processed", "metrics-data", "visualizaciones_totales.csv")
    pol_path = os.path.join("..", "data", "processed", "metrics-advanced", "politicos_totales.csv")
    
    try:
        # Rutas de archivos de visualizaciones generales
        vis_total = pd.read_csv(vis_path)
        pol_total = pd.read_csv(pol_path)
        
        # Limpiar títulos: quitar " - Carriola de Marín" del final
        def limpiar_titulo(titulo):
            if pd.isna(titulo):
                return titulo
            # Quitar " - Carriola de Marín" y variaciones similares del final
            titulo_limpio = str(titulo)
            sufijos_a_quitar = [
                " - Carriola de Marín",
                " - Carriola de Marin", 
                " - Carriola de marín",
                " - carriola de marín",
                " - Carriola",
                " -Carriola de Marín"
            ]
            
            for sufijo in sufijos_a_quitar:
                if titulo_limpio.endswith(sufijo):
                    titulo_limpio = titulo_limpio[:-len(sufijo)]
                    break
            
            return titulo_limpio.strip()
        
        # Funciones para filtrar por tipo político
        def contiene_partidos(texto):
            """Busca menciones de partidos políticos"""
            if pd.isna(texto):
                return False
            texto_lower = str(texto).lower()
            partidos = ["pp", "psoe", "bng"]
            return any(partido in texto_lower for partido in partidos)
        
        def contiene_politicos_locales(texto):
            """Busca menciones de políticos locales específicos"""
            if pd.isna(texto):
                return False
            texto_lower = str(texto).lower()
            politicos = ["pazos", "manuel pazos", "ramallo", "maría ramallo", "santos", "lucía santos"]
            return any(politico in texto_lower for politico in politicos)
        
        # Nuevas funciones para filtros específicos de partidos
        def contiene_psoe(texto):
            """Busca menciones específicas de PSOE o Partido Socialista"""
            if pd.isna(texto):
                return False
            texto_lower = str(texto).lower()
            return "psoe" in texto_lower or "partido socialista" in texto_lower
        
        def contiene_pp(texto):
            """Busca menciones específicas de PP o Partido Popular"""
            if pd.isna(texto):
                return False
            texto_str = str(texto)
            return "PP" in texto_str or "partido popular" in texto_str.lower()
        
        def contiene_bng(texto):
            """Busca menciones específicas de BNG o Bloque"""
            if pd.isna(texto):
                return False
            texto_lower = str(texto).lower()
            texto_str = str(texto)
            return "bng" in texto_lower or "Bloque " in texto_str
        
        # Nuevas funciones para filtros específicos de políticos locales
        def contiene_manuel_pazos(texto):
            """Busca menciones específicas de Manuel Pazos"""
            if pd.isna(texto):
                return False
            return "Manuel Pazos" in str(texto)
        
        def contiene_maria_ramallo(texto):
            """Busca menciones específicas de María Ramallo o Ramallo"""
            if pd.isna(texto):
                return False
            texto_str = str(texto)
            return "María Ramallo" in texto_str or "Ramallo" in texto_str
        
        def contiene_lucia_santos(texto):
            """Busca menciones específicas de Lucía Santos"""
            if pd.isna(texto):
                return False
            return "Lucía Santos" in str(texto)
        
        # Aplicar limpieza a títulos
        vis_total['title'] = vis_total['title'].apply(limpiar_titulo)
        pol_total['title'] = pol_total['title'].apply(limpiar_titulo)
        
        # Crear filtros específicos para el contenido político total
        # Filtrar artículos sobre partidos (general)
        mascara_partidos_titulo = pol_total['title'].apply(contiene_partidos)
        mascara_partidos_summary = pol_total['summary'].apply(contiene_partidos)
        pol_partidos = pol_total[mascara_partidos_titulo | mascara_partidos_summary].copy()
        
        # Filtrar artículos sobre políticos locales (general)
        mascara_politicos_titulo = pol_total['title'].apply(contiene_politicos_locales)
        mascara_politicos_summary = pol_total['summary'].apply(contiene_politicos_locales)
        pol_politicos_locales = pol_total[mascara_politicos_titulo | mascara_politicos_summary].copy()
        
        # Filtros específicos por partido
        # PSOE
        mascara_psoe_titulo = pol_total['title'].apply(contiene_psoe)
        mascara_psoe_summary = pol_total['summary'].apply(contiene_psoe)
        pol_psoe = pol_total[mascara_psoe_titulo | mascara_psoe_summary].copy()
        
        # PP
        mascara_pp_titulo = pol_total['title'].apply(contiene_pp)
        mascara_pp_summary = pol_total['summary'].apply(contiene_pp)
        pol_pp = pol_total[mascara_pp_titulo | mascara_pp_summary].copy()
        
        # BNG
        mascara_bng_titulo = pol_total['title'].apply(contiene_bng)
        mascara_bng_summary = pol_total['summary'].apply(contiene_bng)
        pol_bng = pol_total[mascara_bng_titulo | mascara_bng_summary].copy()
        
        # Filtros específicos por político local
        # Manuel Pazos
        mascara_manuel_titulo = pol_total['title'].apply(contiene_manuel_pazos)
        mascara_manuel_summary = pol_total['summary'].apply(contiene_manuel_pazos)
        pol_manuel = pol_total[mascara_manuel_titulo | mascara_manuel_summary].copy()
        
        # María Ramallo
        mascara_maria_titulo = pol_total['title'].apply(contiene_maria_ramallo)
        mascara_maria_summary = pol_total['summary'].apply(contiene_maria_ramallo)
        pol_maria = pol_total[mascara_maria_titulo | mascara_maria_summary].copy()
        
        # Lucía Santos
        mascara_lucia_titulo = pol_total['title'].apply(contiene_lucia_santos)
        mascara_lucia_summary = pol_total['summary'].apply(contiene_lucia_santos)
        pol_lucia = pol_total[mascara_lucia_titulo | mascara_lucia_summary].copy()
        
        # Convertir la columna date a string para filtros
        vis_total['date'] = vis_total['date'].astype(str)
        pol_partidos['date'] = pol_partidos['date'].astype(str)
        pol_politicos_locales['date'] = pol_politicos_locales['date'].astype(str)
        pol_psoe['date'] = pol_psoe['date'].astype(str)
        pol_pp['date'] = pol_pp['date'].astype(str)
        pol_bng['date'] = pol_bng['date'].astype(str)
        pol_manuel['date'] = pol_manuel['date'].astype(str)
        pol_maria['date'] = pol_maria['date'].astype(str)
        pol_lucia['date'] = pol_lucia['date'].astype(str)
        
        # Filtros para artículos generales
        vis_mayo_2025 = vis_total[vis_total['date'].str.startswith('2025-05')].nlargest(20, "n_visualizations")
        vis_anio_2025 = vis_total[vis_total['date'].str.startswith('2025')].nlargest(20, "n_visualizations")
        vis_historico = vis_total.nlargest(20, "n_visualizations")
        
        # Filtros para artículos sobre partidos (general)
        partidos_mayo_2025 = pol_partidos[pol_partidos['date'].str.startswith('2025-05')].nlargest(10, "n_visualizations")
        partidos_anio_2025 = pol_partidos[pol_partidos['date'].str.startswith('2025')].nlargest(10, "n_visualizations")
        partidos_historico = pol_partidos.nlargest(10, "n_visualizations")
        
        # Filtros para artículos sobre políticos locales (general)
        politicos_mayo_2025 = pol_politicos_locales[pol_politicos_locales['date'].str.startswith('2025-05')].nlargest(10, "n_visualizations")
        politicos_anio_2025 = pol_politicos_locales[pol_politicos_locales['date'].str.startswith('2025')].nlargest(10, "n_visualizations")
        politicos_historico = pol_politicos_locales.nlargest(10, "n_visualizations")
        
        # Filtros específicos para PSOE
        psoe_mayo_2025 = pol_psoe[pol_psoe['date'].str.startswith('2025-05')].nlargest(10, "n_visualizations")
        psoe_anio_2025 = pol_psoe[pol_psoe['date'].str.startswith('2025')].nlargest(10, "n_visualizations")
        psoe_historico = pol_psoe.nlargest(10, "n_visualizations")
        
        # Filtros específicos para PP
        pp_mayo_2025 = pol_pp[pol_pp['date'].str.startswith('2025-05')].nlargest(10, "n_visualizations")
        pp_anio_2025 = pol_pp[pol_pp['date'].str.startswith('2025')].nlargest(10, "n_visualizations")
        pp_historico = pol_pp.nlargest(10, "n_visualizations")
        
        # Filtros específicos para BNG
        bng_mayo_2025 = pol_bng[pol_bng['date'].str.startswith('2025-05')].nlargest(10, "n_visualizations")
        bng_anio_2025 = pol_bng[pol_bng['date'].str.startswith('2025')].nlargest(10, "n_visualizations")
        bng_historico = pol_bng.nlargest(10, "n_visualizations")
        
        # Filtros específicos para Manuel Pazos
        manuel_mayo_2025 = pol_manuel[pol_manuel['date'].str.startswith('2025-05')].nlargest(10, "n_visualizations")
        manuel_anio_2025 = pol_manuel[pol_manuel['date'].str.startswith('2025')].nlargest(10, "n_visualizations")
        manuel_historico = pol_manuel.nlargest(10, "n_visualizations")
        
        # Filtros específicos para María Ramallo
        maria_mayo_2025 = pol_maria[pol_maria['date'].str.startswith('2025-05')].nlargest(10, "n_visualizations")
        maria_anio_2025 = pol_maria[pol_maria['date'].str.startswith('2025')].nlargest(10, "n_visualizations")
        maria_historico = pol_maria.nlargest(10, "n_visualizations")
        
        # Filtros específicos para Lucía Santos
        lucia_mayo_2025 = pol_lucia[pol_lucia['date'].str.startswith('2025-05')].nlargest(10, "n_visualizations")
        lucia_anio_2025 = pol_lucia[pol_lucia['date'].str.startswith('2025')].nlargest(10, "n_visualizations")
        lucia_historico = pol_lucia.nlargest(10, "n_visualizations")
        
        return {
            "top10_vis": {
                "mes": vis_mayo_2025.reset_index(drop=True),
                "anio": vis_anio_2025.reset_index(drop=True),
                "total": vis_historico.reset_index(drop=True),
            },
            "top10_partidos": {
                "mes": partidos_mayo_2025.reset_index(drop=True),
                "anio": partidos_anio_2025.reset_index(drop=True),
                "total": partidos_historico.reset_index(drop=True),
            },
            "top10_politicos": {
                "mes": politicos_mayo_2025.reset_index(drop=True),
                "anio": politicos_anio_2025.reset_index(drop=True),
                "total": politicos_historico.reset_index(drop=True),
            },
            "top10_psoe": {
                "mes": psoe_mayo_2025.reset_index(drop=True),
                "anio": psoe_anio_2025.reset_index(drop=True),
                "total": psoe_historico.reset_index(drop=True),
            },
            "top10_pp": {
                "mes": pp_mayo_2025.reset_index(drop=True),
                "anio": pp_anio_2025.reset_index(drop=True),
                "total": pp_historico.reset_index(drop=True),
            },
            "top10_bng": {
                "mes": bng_mayo_2025.reset_index(drop=True),
                "anio": bng_anio_2025.reset_index(drop=True),
                "total": bng_historico.reset_index(drop=True),
            },
            "top10_manuel": {
                "mes": manuel_mayo_2025.reset_index(drop=True),
                "anio": manuel_anio_2025.reset_index(drop=True),
                "total": manuel_historico.reset_index(drop=True),
            },
            "top10_maria": {
                "mes": maria_mayo_2025.reset_index(drop=True),
                "anio": maria_anio_2025.reset_index(drop=True),
                "total": maria_historico.reset_index(drop=True),
            },
            "top10_lucia": {
                "mes": lucia_mayo_2025.reset_index(drop=True),
                "anio": lucia_anio_2025.reset_index(drop=True),
                "total": lucia_historico.reset_index(drop=True),
            }
        }
    
    except FileNotFoundError as e:
        st.error(f"❌ No se encontró el archivo: {e.filename}")
        st.write(f"Ruta buscada: {vis_path} y {pol_path}")
        st.stop()
    except Exception as e:
        st.error(f"❌ Error cargando métricas: {str(e)}")
        st.stop()

@st.cache_data
def cargar_datos_comentarios():
    """
    Carga los archivos CSV con datos de comentarios
    """
    # Definir rutas base (desde el directorio del script de streamlit)
    # Asumiendo que app.py está en streamlit/ y data/ está en la raíz del proyecto
    #ruta_archivo = os.path.join("..", "data", "processed", "filtered-data", "filtered_data.csv")

    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    ruta_archivo = os.path.join(BASE_DIR, "data", "processed", "filtered-data", "filtered_data.csv")

    st.write("🔍 BASE_DIR:", BASE_DIR)
    st.write("🔍 Carpeta esperada:", ruta_archivo)
    st.write("📋 listdir folder:", os.listdir(ruta_archivo) if os.path.exists(ruta_archivo) else "❌ No existe esa carpeta")

    print(f"DEBUG: ruta_archivo = {ruta_archivo}")
    print(f"DEBUG: existe? = {os.path.exists(ruta_archivo)}")
    print(f"DEBUG: es archivo? = {os.path.isfile(ruta_archivo)}")
    print(f"DEBUG: es directorio? = {os.path.isdir(ruta_archivo)}")

    
    try:
        # Cargar solo el archivo principal de datos filtrados
        filtered_data = pd.read_csv(ruta_archivo)
        
        return {
            "filtered_data": filtered_data
        }
    
    except FileNotFoundError as e:
        st.error(f"❌ No se encontró el archivo: {e.filename}")
        st.write(f"Ruta buscada: {ruta_archivo}")
        st.stop()
    except Exception as e:
        st.error(f"❌ Error cargando datos de comentarios: {str(e)}")
        st.stop()

@st.cache_data
def cargar_datos_comentarios_morrazo():
    """
    Carga los datos de comentarios específicos de O Morrazo y Pontevedra
    """
    # Definir rutas base (desde el directorio del script de streamlit)
    # Asumiendo que app.py está en streamlit/ y el archivo CSV está en el directorio raíz
    #archivo_morrazo = os.path.join("..", "data", "processed", "filtered-data", "filtro1_localizacion.csv")

    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    archivo_morrazo = os.path.join(BASE_DIR, "data", "processed", "filtered-data", "filtro1_localizacion.csv")
    
    archivo_encontrado = None
    
    # Buscar el archivo en las rutas posibles
    for ruta in [archivo_morrazo]:
        if os.path.exists(ruta):
            archivo_encontrado = ruta
            break
    
    if archivo_encontrado is None:
        # Mostrar rutas buscadas para debugging
        st.error("❌ No se encontró el archivo filtro1_localizacion.csv")
        st.write("📂 Rutas buscadas:")
        for ruta in [archivo_morrazo]:
            st.write(f"   - {ruta}")
        st.stop()
    
    try:
        # Cargar el archivo de datos de O Morrazo y Pontevedra
        morrazo_data = pd.read_csv(archivo_encontrado)
        
        # Verificar que el archivo tiene las columnas necesarias
        columnas_necesarias = ['title', 'date', 'n_comments', 'source']
        columnas_faltantes = [col for col in columnas_necesarias if col not in morrazo_data.columns]
        
        if columnas_faltantes:
            st.error(f"❌ El archivo {archivo_encontrado} no tiene las columnas necesarias: {columnas_faltantes}")
            st.write(f"📊 Columnas disponibles: {list(morrazo_data.columns)}")
            st.stop()
                
        return {
            "filtered_data": morrazo_data
        }
    
    except FileNotFoundError as e:
        st.error(f"❌ No se encontró el archivo: {e.filename}")
        st.write(f"Ruta buscada: {archivo_encontrado}")
        st.stop()
        
@st.cache_data
def cargar_datos_comentarios_marin():
    """
    Carga los datos de comentarios específicos de Marín
    """
    # Definir rutas base (desde el directorio del script de streamlit)
    # Asumiendo que app.py está en streamlit/ y el archivo CSV está en el directorio raíz
    #archivo_marin = os.path.join("..", "data", "processed", "filtered-data", "filtro6_marin.csv")

    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    archivo_marin = os.path.join(BASE_DIR, "data", "processed", "filtered-data", "filtro6_marin.csv")
 
    archivo_encontrado = None
    
    # Buscar el archivo en las rutas posibles
    for ruta in [archivo_marin]:
        if os.path.exists(ruta):
            archivo_encontrado = ruta
            break
    
    if archivo_encontrado is None:
        # Mostrar rutas buscadas para debugging
        st.error("❌ No se encontró el archivo filtro6_marin.csv")
        st.write("📂 Rutas buscadas:")
        for ruta in [archivo_marin]:
            st.write(f"   - {ruta}")
        st.stop()
    
    try:
        # Cargar el archivo de datos de Marín
        marin_data = pd.read_csv(archivo_encontrado)
        
        # Verificar que el archivo tiene las columnas necesarias
        columnas_necesarias = ['title', 'date', 'n_comments', 'source']
        columnas_faltantes = [col for col in columnas_necesarias if col not in marin_data.columns]
        
        if columnas_faltantes:
            st.error(f"❌ El archivo {archivo_encontrado} no tiene las columnas necesarias: {columnas_faltantes}")
            st.write(f"📊 Columnas disponibles: {list(marin_data.columns)}")
            st.stop()
                
        return {
            "filtered_data": marin_data
        }
    
    except FileNotFoundError as e:
        st.error(f"❌ No se encontró el archivo: {e.filename}")
        st.write(f"Ruta buscada: {archivo_encontrado}")
        st.stop()
    except Exception as e:
        st.error(f"❌ Error cargando datos de comentarios de Marín: {str(e)}")
        st.error(f"Archivo: {archivo_encontrado}")
        st.stop()