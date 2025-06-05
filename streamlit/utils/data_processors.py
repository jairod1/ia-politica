"""
Data Processors - HorizontAI
=============================

Funciones para procesar datos de comentarios y artículos polémicos.
"""

import pandas as pd

def procesar_articulos_polemicos(df, top_n=20):
    """
    Encuentra los artículos más polémicos basado en número de comentarios
    y longitud de texto de comentarios
    
    Args:
        df: DataFrame con artículos y comentarios
        top_n: Número de artículos top a devolver
        
    Returns:
        DataFrame con los artículos más polémicos
    """
    # Crear una copia del dataframe
    df_processed = df.copy()
    
    # Calcular la longitud total de texto de comentarios por artículo
    df_processed['total_comment_length'] = 0
    
    for i in range(1, 16):  # comment_1 a comment_15
        comment_col = f'comment_{i}_text'
        if comment_col in df.columns:
            df_processed[comment_col] = df_processed[comment_col].fillna('')
            df_processed['total_comment_length'] += df_processed[comment_col].astype(str).str.len()
    
    # Ordenar primero por número de comentarios, luego por longitud total
    df_sorted = df_processed.sort_values(['n_comments', 'total_comment_length'], ascending=[False, False])
    
    return df_sorted.head(top_n)

def procesar_articulos_polemicos_UNIFICADO(df):
    """
    🔧 VERSIÓN UNIFICADA: Usa la misma función base que el análisis con sentimientos
    """
    return obtener_articulos_polemicos_unificado(df, top_n=20)

def procesar_comentarios_populares(df, top_n=20):
    """
    Encuentra los comentarios más populares (más likes que dislikes)
    
    Args:
        df: DataFrame con artículos y comentarios
        top_n: Número de comentarios top a devolver
        
    Returns:
        DataFrame con los comentarios más populares
    """

    comentarios_populares = []
    
    for _, row in df.iterrows():
        for i in range(1, 16):  # comment_1 a comment_15
            comment_text = row.get(f'comment_{i}_text', '')
            comment_likes = row.get(f'comment_{i}_likes', 0)
            comment_dislikes = row.get(f'comment_{i}_dislikes', 0)
            comment_author = row.get(f'comment_{i}_author', '')
            comment_location = row.get(f'comment_{i}_location', '')
            
            if pd.notna(comment_text) and str(comment_text).strip() and comment_likes > comment_dislikes:
                comentarios_populares.append({
                    'article_title': row['title'],
                    'article_date': row['date'],
                    'article_link': row['link'],
                    'article_source': row['source'],
                    'comment_text': comment_text,
                    'comment_author': comment_author,
                    'comment_location': comment_location,
                    'likes': comment_likes,
                    'dislikes': comment_dislikes,
                    'net_score': comment_likes - comment_dislikes
                })
    
    # Convertir a DataFrame y ordenar por net_score
    df_comentarios = pd.DataFrame(comentarios_populares)
    if len(df_comentarios) > 0:
        df_comentarios = df_comentarios.sort_values('net_score', ascending=False)
    
    return df_comentarios.head(top_n)

def procesar_comentarios_impopulares(df, top_n=20):
    """
    Encuentra los comentarios más impopulares (más dislikes que likes)
    
    Args:
        df: DataFrame con artículos y comentarios
        top_n: Número de comentarios top a devolver
        
    Returns:
        DataFrame con los comentarios más impopulares
    """
    comentarios_impopulares = []
    
    for _, row in df.iterrows():
        for i in range(1, 16):  # comment_1 a comment_15
            comment_text = row.get(f'comment_{i}_text', '')
            comment_likes = row.get(f'comment_{i}_likes', 0)
            comment_dislikes = row.get(f'comment_{i}_dislikes', 0)
            comment_author = row.get(f'comment_{i}_author', '')
            comment_location = row.get(f'comment_{i}_location', '')
            
            if pd.notna(comment_text) and str(comment_text).strip() and comment_dislikes > comment_likes:
                comentarios_impopulares.append({
                    'article_title': row['title'],
                    'article_date': row['date'],
                    'article_link': row['link'],
                    'article_source': row['source'],
                    'comment_text': comment_text,
                    'comment_author': comment_author,
                    'comment_location': comment_location,
                    'likes': comment_likes,
                    'dislikes': comment_dislikes,
                    'net_score': comment_likes - comment_dislikes
                })
    
    # Convertir a DataFrame y ordenar por net_score (mayor diferencia negativa)
    df_comentarios = pd.DataFrame(comentarios_impopulares)
    if len(df_comentarios) > 0:
        df_comentarios = df_comentarios.sort_values('net_score', ascending=True)
    
    return df_comentarios.head(top_n)

def obtener_articulos_polemicos_unificado(df, top_n=20):
    """
    🔧 FUNCIÓN UNIFICADA: Determina artículos polémicos usando EXACTAMENTE la misma lógica
    para ambos casos (con y sin analizador)
    
    Args:
        df: DataFrame con artículos y comentarios
        top_n: Número de artículos más polémicos a retornar
        
    Returns:
        DataFrame ordenado por número de comentarios descendente
    """
    
    if len(df) == 0:
        return pd.DataFrame()
    
    # 1. Contar comentarios por artículo (mismo criterio siempre)
    conteo_comentarios = []
    
    for index, row in df.iterrows():
        num_comentarios = 0
        
        # Contar comentarios del 1 al 15
        for i in range(1, 16):
            comment_text = row.get(f'comment_{i}_text', '')
            if pd.notna(comment_text) and str(comment_text).strip():
                num_comentarios += 1
        
        # También verificar columna n_comments si existe
        if 'n_comments' in row and pd.notna(row['n_comments']):
            num_comentarios = max(num_comentarios, int(row['n_comments']))
        
        conteo_comentarios.append({
            'title': row.get('title', ''),
            'date': row.get('date', ''),
            'source': row.get('source', ''),
            'link': row.get('link', ''),
            'n_visualizations': row.get('n_visualizations', 0),
            'summary': row.get('summary', ''),
            'n_comments': num_comentarios,
            'total_comment_length': sum([
                len(str(row.get(f'comment_{i}_text', ''))) 
                for i in range(1, 16) 
                if pd.notna(row.get(f'comment_{i}_text', ''))
            ]),
            # Preservar comentarios originales para análisis
            **{k: v for k, v in row.items() if k.startswith('comment_')}
        })
    
    # 2. Crear DataFrame y ordenar por número de comentarios DESCENDENTE
    df_resultado = pd.DataFrame(conteo_comentarios)
    
    if len(df_resultado) == 0:
        return df_resultado
    
    # 🔧 CRITERIO UNIFICADO: Ordenar siempre por número de comentarios descendente
    df_resultado = df_resultado.sort_values('n_comments', ascending=False)
    
    # 3. Filtrar solo artículos que tengan al menos 1 comentario
    df_resultado = df_resultado[df_resultado['n_comments'] > 0]
    
    # 4. Retornar top N más polémicos
    return df_resultado.head(top_n).reset_index(drop=True)

def aplicar_filtros_temporales(datos_comentarios):
    """
    Aplica filtros temporales con manejo robusto de fechas problemáticas
    """
    try:
        # Convertir de forma segura
        datos_comentarios["filtered_data"]['date'] = datos_comentarios["filtered_data"]['date'].apply(lambda x: str(x) if pd.notna(x) else '')
    except:
        # Si falla, usar valores por defecto
        datos_comentarios["filtered_data"]['date'] = ''
    
    # Aplicar filtros temporales
    comentarios_mayo_2025 = datos_comentarios["filtered_data"][datos_comentarios["filtered_data"]['date'].str.startswith('2025-05')]
    comentarios_anio_2025 = datos_comentarios["filtered_data"][datos_comentarios["filtered_data"]['date'].str.startswith('2025')]
    comentarios_historico = datos_comentarios["filtered_data"]
    
    return comentarios_mayo_2025, comentarios_anio_2025, comentarios_historico