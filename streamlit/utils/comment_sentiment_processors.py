"""
Comment Sentiment Processors - HorizontAI (VERSIÓN CORREGIDA)
============================================================

SOLUCIÓN: Cambiar import relativo por parámetro directo
"""

import pandas as pd
import streamlit as st

def extraer_comentarios_para_analisis(df):
    """
    Extrae comentarios individuales de un DataFrame de artículos para análisis de sentimientos
    
    Args:
        df: DataFrame con artículos y comentarios
        
    Returns:
        DataFrame con comentarios individuales preparados para análisis
    """
    comentarios_extraidos = []
    
    for _, row in df.iterrows():
        for i in range(1, 16):  # comment_1 a comment_15
            comment_text = row.get(f'comment_{i}_text', '')
            comment_author = row.get(f'comment_{i}_author', '')
            comment_location = row.get(f'comment_{i}_location', '')
            comment_likes = row.get(f'comment_{i}_likes', 0)
            comment_dislikes = row.get(f'comment_{i}_dislikes', 0)
            
            if pd.notna(comment_text) and str(comment_text).strip():
                comentarios_extraidos.append({
                    'title': comment_text,
                    'texto_completo_preservado': str(comment_text).strip(),  # Backup del texto completo
                    'summary': '',
                    'title_original': row['title'],
                    'date': str(row.get('date', '')).split('T')[0],  # Quitar la parte de tiempo
                    'link': row.get('link', ''),
                    'source': row.get('source', ''),
                    'n_visualizations': row.get('n_visualizations', 0),  # Por si hubiese visualizaciones
                    'comment_author': comment_author,
                    'comment_location': comment_location,
                    'likes': comment_likes,
                    'dislikes': comment_dislikes,
                    'net_score': comment_likes - comment_dislikes,
                    'comment_index': i
                })
    
    return pd.DataFrame(comentarios_extraidos)

def mostrar_comentarios_con_sentimientos(df_comentarios, reporte, titulo_seccion, mostrar_sentimientos=True, es_popular=True):
    """
    SIMPLIFICADO: Redirige a la función que funciona en visualizers
    """
    if len(df_comentarios) == 0:
        tipo = "populares" if es_popular else "impopulares"
        st.info(f"🤷‍♂️ No hay comentarios {tipo} para {titulo_seccion.lower()}")
        return
    
    # Usar directamente la función de visualizers que sabemos que funciona
    try:
        from .visualizers import mostrar_tabla_comentarios_con_sentimientos
        mostrar_tabla_comentarios_con_sentimientos(
            df_comentarios, 
            titulo_seccion, 
            mostrar_sentimientos=mostrar_sentimientos,
            analizador=None,  # Ya está analizado
            es_popular=es_popular,
            reporte=reporte
        )
    except ImportError as e:
        st.error(f"❌ Error importando función de visualización: {e}")
        st.error("💡 Usa la función de visualizers.py directamente")

def resumir_sentimientos_por_articulo(df_analizado):
    """
    🔧 VERSIÓN CORREGIDA: Agrupa comentarios por artículo con temática modal
    
    Maneja errores de columnas faltantes de forma más robusta
    """
    
    # Función helper para moda
    def moda_o_neutral(col):
        try:
            conteo = col.dropna().value_counts()
            if len(conteo) == 0:
                return 'neutral'
            return conteo.idxmax()
        except:
            return 'neutral'
    
    # Función helper para temática modal
    def calcular_tematica_modal(col):
        try:
            col_clean = col.dropna()
            if len(col_clean) == 0:
                return '📄 Otra'
            
            conteo = col_clean.value_counts()
            if len(conteo) == 0:
                return '📄 Otra'
            
            tematica_modal = conteo.idxmax()
            
            # Si todas aparecen solo 1 vez, devolver "Variadas"
            if conteo.iloc[0] == 1 and len(conteo) > 1:
                return '📄 Variadas'
            
            return tematica_modal
        except:
            return '📄 Otra'
    
    # 🔧 VERIFICACIÓN BÁSICA SOLO DE COLUMNAS CRÍTICAS
    if 'title_original' not in df_analizado.columns:
        st.error("❌ No se encontró la columna 'title_original'")
        return pd.DataFrame()
    
    if len(df_analizado) == 0:
        st.warning("⚠️ No hay datos para agrupar")
        return pd.DataFrame()
    
    # 🔧 CREAR COLUMNAS FALTANTES CON VALORES POR DEFECTO
    columnas_default = {
        'tono_general': 'neutral',
        'emocion_principal': 'neutral',
        'intensidad_emocional': 1.0,
        'confianza_analisis': 0.5,
        'es_politico': False,
        'idioma': 'castellano',
        'link': '',
        'date': '',
        'n_visualizations': 0,
        'source': ''
    }
    
    # Añadir columnas que falten
    for col, valor_default in columnas_default.items():
        if col not in df_analizado.columns:
            df_analizado[col] = valor_default
    
    # 🆕 VERIFICAR SI EXISTE COLUMNA DE TEMÁTICA
    tiene_tematica = 'tematica' in df_analizado.columns
    
    # 🔧 CONFIGURAR AGREGACIONES BÁSICAS
    agregaciones = {
        'link': 'first',
        'tono_general': moda_o_neutral,
        'emocion_principal': moda_o_neutral,
        'intensidad_emocional': 'mean',
        'confianza_analisis': 'mean',
        'es_politico': lambda x: x.sum() > len(x) / 2,
        'idioma': moda_o_neutral,
        'date': 'first',
        'n_visualizations': 'first',
        'source': 'first'
    }
    
    # 🆕 AÑADIR TEMÁTICA MODAL SI LA COLUMNA EXISTE
    if tiene_tematica:
        agregaciones['tematica'] = calcular_tematica_modal
    
    # 🔧 AGRUPAR CON MANEJO DE ERRORES
    try:
        agrupado = df_analizado.groupby(['title_original']).agg(agregaciones).reset_index()
    except Exception as e:
        st.error(f"❌ Error en agrupación: {e}")
        st.error("💡 Revisa que las columnas necesarias existan en el DataFrame")
        return pd.DataFrame()
    
    # 🔧 RENOMBRAR COLUMNAS CON MANEJO DE ERRORES
    nombres_columnas = {
        'title_original': 'title',
        'tono_general': 'tono_comentarios',
        'emocion_principal': 'emocion_dominante',
        'intensidad_emocional': 'intensidad_media',
        'confianza_analisis': 'confianza_media',
        'es_politico': 'es_politico_por_comentarios',
        'idioma': 'idioma_dominante',
        'link': 'article_link',
        'date': 'article_date'
    }
    
    # 🆕 RENOMBRAR TEMÁTICA SI EXISTE
    if tiene_tematica and 'tematica' in agrupado.columns:
        nombres_columnas['tematica'] = 'tematica_modal'
    
    try:
        agrupado.rename(columns=nombres_columnas, inplace=True)
                
    except Exception as e:
        st.error(f"❌ Error renombrando columnas: {e}")
        return pd.DataFrame()
    
    return agrupado

def procesar_comentarios_politicos_con_sentimientos(df, aplicar_analisis_sentimientos, analizador, top_n=20, filtro_popularidad=None):
    """
    Procesa comentarios políticos aplicando análisis de sentimientos, y resume por artículo

    Args:
        df: DataFrame con artículos y comentarios ya filtrados por política
        aplicar_analisis_sentimientos: función que ejecuta el análisis con el analizador
        analizador: Instancia del analizador de sentimientos
        top_n: Número de artículos top a devolver
        filtro_popularidad: 'popular', 'impopular' o None para todos

    Returns:
        DataFrame resumido por artículo con análisis emocional agregado
    """
    df_comentarios = extraer_comentarios_para_analisis(df)

    if len(df_comentarios) == 0:
        st.warning("⚠️ No se encontraron comentarios para analizar")
        return pd.DataFrame(), None

    # Aplicar filtro de popularidad si se especifica
    if filtro_popularidad == 'popular':
        df_comentarios = df_comentarios[df_comentarios['likes'] > df_comentarios['dislikes']]
        df_comentarios = df_comentarios.sort_values('net_score', ascending=False)
    elif filtro_popularidad == 'impopular':
        df_comentarios = df_comentarios[df_comentarios['dislikes'] > df_comentarios['likes']]
        df_comentarios = df_comentarios.sort_values('net_score', ascending=False)
    else:
        df_comentarios['abs_net_score'] = abs(df_comentarios['net_score'])
        df_comentarios = df_comentarios.sort_values('abs_net_score', ascending=False)

    df_comentarios = df_comentarios.head(top_n * 5)  # Más amplio para agrupación

    if analizador is not None and aplicar_analisis_sentimientos is not None:
        try:
            df_analizado, reporte = aplicar_analisis_sentimientos(df_comentarios, analizador)
            df_resumen = resumir_sentimientos_por_articulo(df_analizado)
            return df_resumen, reporte
        except Exception as e:
            st.error(f"❌ Error aplicando análisis de sentimientos: {e}")
            return df_comentarios, None
    else:
        return df_comentarios, None