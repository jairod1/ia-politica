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
    🚨 ARREGLO: Forzar columnas básicas antes de agrupar
    """
    if len(df_analizado) == 0:
        return pd.DataFrame()
    
    # 🚨 FORZAR COLUMNAS NECESARIAS
    df_fixed = df_analizado.copy()
    
    columnas_basicas = {
        'tono_general': 'neutral',
        'emocion_principal': 'neutral', 
        'intensidad_emocional': 1,
        'confianza_analisis': 0.5,
        'es_politico': False,
        'idioma': 'castellano'
    }
    
    for col, valor in columnas_basicas.items():
        if col not in df_fixed.columns:
            df_fixed[col] = valor

    def moda_o_neutral(col):
        """Función auxiliar segura para calcular moda"""
        try:
            conteo = col.value_counts()
            if len(conteo) == 0:
                return 'neutral'
            return conteo.idxmax()
        except:
            return 'neutral'
    
    try:
        # Verificar columnas esenciales con valores por defecto
        columnas_verificacion = {
            'tono_general': 'neutral',
            'emocion_principal': 'neutral', 
            'intensidad_emocional': 1,
            'confianza_analisis': 0.5,
            'es_politico': False,
            'idioma': 'castellano'
        }
        
        # Añadir columnas faltantes con valores por defecto
        for col, valor_default in columnas_verificacion.items():
            if col not in df_fixed.columns:
                st.write(f"🔧 **EMERGENCY**: Añadiendo columna faltante '{col}' con valor '{valor_default}'")
                df_fixed[col] = valor_default
        
        # Verificar columnas de agrupación
        if 'title_original' not in df_fixed.columns:
            if 'title' in df_fixed.columns:
                df_fixed['title_original'] = df_fixed['title']
            else:
                st.error("❌ No se puede agrupar: falta columna de título")
                return pd.DataFrame()
        
        if 'link' not in df_fixed.columns:
            df_fixed['link'] = 'sin_enlace'
        
        # Realizar agrupación
        st.write("🔧 **EMERGENCY**: Realizando agrupación...")
        
        agrupado = df_fixed.groupby(['link', 'title_original']).agg({
            'tono_general': moda_o_neutral,
            'emocion_principal': moda_o_neutral,
            'intensidad_emocional': 'mean',
            'confianza_analisis': 'mean', 
            'es_politico': lambda x: x.sum() > len(x) / 2,
            'idioma': moda_o_neutral,
            'date': 'first',
            'n_visualizations': 'first',
            'source': 'first'
        }).reset_index()
        
        # Renombrar columnas
        agrupado.rename(columns={
            'title_original': 'title',
            'tono_general': 'tono_comentarios',
            'emocion_principal': 'emocion_dominante',
            'intensidad_emocional': 'intensidad_media',
            'confianza_analisis': 'confianza_media',
            'es_politico': 'es_politico_por_comentarios',
            'idioma': 'idioma_dominante',
            'link': 'article_link',
            'date': 'article_date'
        }, inplace=True)
        
        st.write(f"🔧 **EMERGENCY**: Agrupación completada. {len(agrupado)} artículos resumidos")
        st.write(f"🔧 **EMERGENCY**: Columnas finales: {list(agrupado.columns)}")
        
        return agrupado
        
    except Exception as e:
        st.error(f"❌ Error crítico en agrupación: {e}")
        st.write(f"🔧 **EMERGENCY**: Tipo de error: {type(e)}")
        
        # Crear DataFrame mínimo de emergencia
        try:
            # Tomar primer comentario por artículo como representativo
            df_minimo = df_fixed.groupby('title_original' if 'title_original' in df_fixed.columns else 'title').first().reset_index()
            
            # Asegurar columnas necesarias
            df_minimo['tono_comentarios'] = df_minimo.get('tono_general', 'neutral')
            df_minimo['emocion_dominante'] = df_minimo.get('emocion_principal', 'neutral')
            df_minimo['intensidad_media'] = df_minimo.get('intensidad_emocional', 1)
            df_minimo['confianza_media'] = df_minimo.get('confianza_analisis', 0.5)
            df_minimo['es_politico_por_comentarios'] = df_minimo.get('es_politico', False)
            df_minimo['idioma_dominante'] = df_minimo.get('idioma', 'castellano')
            df_minimo['article_link'] = df_minimo.get('link', 'sin_enlace')
            df_minimo['article_date'] = df_minimo.get('date', '2025-01-01')
            
            if 'title_original' in df_minimo.columns:
                df_minimo['title'] = df_minimo['title_original']
            
            st.write("🔧 **EMERGENCY**: DataFrame mínimo creado como fallback")
            return df_minimo
            
        except Exception as e2:
            st.error(f"❌ Error crítico en fallback: {e2}")
            return pd.DataFrame()

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
