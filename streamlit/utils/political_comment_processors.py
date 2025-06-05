"""
Political Comment Processors - HorizontAI
==========================================

Funciones para filtrar y procesar comentarios con contenido político específico.
"""

import pandas as pd

def filtrar_comentarios_por_partidos_general(df):
    """
    Filtra artículos que tienen comentarios mencionando cualquier partido político
    
    Args:
        df: DataFrame con artículos y comentarios
        
    Returns:
        DataFrame filtrado con artículos que tienen comentarios sobre partidos
    """
    def contiene_partidos_en_comentarios(row):
        """Busca menciones de partidos en todos los comentarios del artículo"""
        partidos_keywords = ["psoe", "partido socialista", "bloque nacionalista", "bng"]
        
        for i in range(1, 16):  # comment_1 a comment_15
            comment_text = row.get(f'comment_{i}_text', '')
            if pd.notna(comment_text) and str(comment_text).strip():
                texto_str = str(comment_text)
                texto_lower = texto_str.lower()
                
                # Buscar keywords normales
                for keyword in partidos_keywords:
                    if keyword in texto_lower:
                        return True
                
                # Búsqueda especial para "PP" (mayúsculas)
                if (" PP " in texto_str or 
                    texto_str.startswith("PP ") or 
                    texto_str.endswith(" PP") or
                    " PP." in texto_str or
                    " PP," in texto_str):
                    return True
                    
                # Búsqueda especial para "partido popular" 
                if "partido popular" in texto_lower:
                    return True
        return False
    
    mask = df.apply(contiene_partidos_en_comentarios, axis=1)
    return df[mask].reset_index(drop=True)

def filtrar_comentarios_por_psoe(df):
    """
    Filtra artículos que tienen comentarios mencionando PSOE/Partido Socialista
    """
    def contiene_psoe_en_comentarios(row):
        psoe_keywords = ["psoe", "partido socialista", "socialista", "psdeg"]
        
        for i in range(1, 16):
            comment_text = row.get(f'comment_{i}_text', '')
            if pd.notna(comment_text) and str(comment_text).strip():
                texto_lower = str(comment_text).lower()
                for keyword in psoe_keywords:
                    if keyword in texto_lower:
                        return True
        return False
    
    mask = df.apply(contiene_psoe_en_comentarios, axis=1)
    return df[mask].reset_index(drop=True)

def filtrar_comentarios_por_pp(df):
    """
    Filtra artículos que tienen comentarios mencionando PP/Partido Popular
    """
    def contiene_pp_en_comentarios(row):
        for i in range(1, 16):
            comment_text = row.get(f'comment_{i}_text', '')
            if pd.notna(comment_text) and str(comment_text).strip():
                texto_str = str(comment_text)
                texto_lower = texto_str.lower()
                
                # Buscar "PP" con espacios o signos de puntuación
                if (" PP " in texto_str or 
                    texto_str.startswith("PP ") or 
                    texto_str.endswith(" PP") or
                    " PP." in texto_str or
                    " PP," in texto_str or
                    "partido popular" in texto_lower):
                    return True
        return False
    
    mask = df.apply(contiene_pp_en_comentarios, axis=1)
    return df[mask].reset_index(drop=True)

def filtrar_comentarios_por_bng(df):
    """
    Filtra artículos que tienen comentarios mencionando BNG/Bloque
    """
    def contiene_bng_en_comentarios(row):
        bng_keywords = ["bng", "bloque nacionalista", "bloque"]
        
        for i in range(1, 16):
            comment_text = row.get(f'comment_{i}_text', '')
            if pd.notna(comment_text) and str(comment_text).strip():
                texto_lower = str(comment_text).lower()
                for keyword in bng_keywords:
                    if keyword in texto_lower:
                        return True
        return False
    
    mask = df.apply(contiene_bng_en_comentarios, axis=1)
    return df[mask].reset_index(drop=True)

def filtrar_comentarios_por_politicos_general(df):
    """
    Filtra artículos que tienen comentarios mencionando cualquier político local
    """
    def contiene_politicos_en_comentarios(row):
        politicos_keywords = ["pazos", "manuel pazos", "ramallo", "maría ramallo", "maria ramallo", "santos", "lucía santos", "lucia santos"]
        
        for i in range(1, 16):
            comment_text = row.get(f'comment_{i}_text', '')
            if pd.notna(comment_text) and str(comment_text).strip():
                texto_str = str(comment_text)
                texto_lower = texto_str.lower()
                
                for keyword in politicos_keywords:
                    if keyword in texto_lower:
                        return True
                        
                # Búsqueda especial para apellidos con mayúscula
                if ("Pazos" in texto_str or 
                    "Ramallo" in texto_str or 
                    "Santos" in texto_str):
                    return True
        return False
    
    mask = df.apply(contiene_politicos_en_comentarios, axis=1)
    return df[mask].reset_index(drop=True)

def filtrar_comentarios_por_manuel_pazos(df):
    """
    Filtra artículos que tienen comentarios mencionando Manuel Pazos
    """
    def contiene_manuel_pazos_en_comentarios(row):
        for i in range(1, 16):
            comment_text = row.get(f'comment_{i}_text', '')
            if pd.notna(comment_text) and str(comment_text).strip():
                texto_str = str(comment_text)
                texto_lower = texto_str.lower()
                
                if ("Pazos" in texto_str or 
                    "manuel pazos" in texto_lower or
                    "pazos" in texto_lower):
                    return True
        return False
    
    mask = df.apply(contiene_manuel_pazos_en_comentarios, axis=1)
    return df[mask].reset_index(drop=True)

def filtrar_comentarios_por_maria_ramallo(df):
    """
    Filtra artículos que tienen comentarios mencionando María Ramallo
    """
    def contiene_maria_ramallo_en_comentarios(row):
        for i in range(1, 16):
            comment_text = row.get(f'comment_{i}_text', '')
            if pd.notna(comment_text) and str(comment_text).strip():
                texto_str = str(comment_text)
                texto_lower = texto_str.lower()
                
                if ("Ramallo" in texto_str or 
                    "maría ramallo" in texto_lower or
                    "maria ramallo" in texto_lower or
                    "ramallo" in texto_lower):
                    return True
        return False
    
    mask = df.apply(contiene_maria_ramallo_en_comentarios, axis=1)
    return df[mask].reset_index(drop=True)

def filtrar_comentarios_por_lucia_santos(df):
    """
    Filtra artículos que tienen comentarios mencionando Lucía Santos
    """
    def contiene_lucia_santos_en_comentarios(row):
        for i in range(1, 16):
            comment_text = row.get(f'comment_{i}_text', '')
            if pd.notna(comment_text) and str(comment_text).strip():
                texto_lower = str(comment_text).lower()
                
                if ("lucía santos" in texto_lower or
                    "lucia santos" in texto_lower):
                    return True
        return False
    
    mask = df.apply(contiene_lucia_santos_en_comentarios, axis=1)
    return df[mask].reset_index(drop=True)

def procesar_comentarios_politicos_populares(df, top_n=20):
    """
    Encuentra los comentarios populares que mencionan contenido político
    
    Args:
        df: DataFrame con artículos y comentarios ya filtrados por política
        top_n: Número de comentarios top a devolver
        
    Returns:
        DataFrame con los comentarios políticos más populares
    """
    comentarios_politicos_populares = []
    
    for _, row in df.iterrows():
        for i in range(1, 16):  # comment_1 a comment_15
            comment_text = row.get(f'comment_{i}_text', '')
            comment_likes = row.get(f'comment_{i}_likes', 0)
            comment_dislikes = row.get(f'comment_{i}_dislikes', 0)
            comment_author = row.get(f'comment_{i}_author', '')
            comment_location = row.get(f'comment_{i}_location', '')
            
            if (pd.notna(comment_text) and 
                str(comment_text).strip() and 
                comment_likes > comment_dislikes):
                
                comentarios_politicos_populares.append({
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
    df_comentarios = pd.DataFrame(comentarios_politicos_populares)
    if len(df_comentarios) > 0:
        df_comentarios = df_comentarios.sort_values('net_score', ascending=False)
    
    return df_comentarios.head(top_n)

def procesar_comentarios_politicos_impopulares(df, top_n=20):
    """
    Encuentra los comentarios impopulares que mencionan contenido político
    
    Args:
        df: DataFrame con artículos y comentarios ya filtrados por política
        top_n: Número de comentarios top a devolver
        
    Returns:
        DataFrame con los comentarios políticos más impopulares
    """
    comentarios_politicos_impopulares = []
    
    for _, row in df.iterrows():
        for i in range(1, 16):  # comment_1 a comment_15
            comment_text = row.get(f'comment_{i}_text', '')
            comment_likes = row.get(f'comment_{i}_likes', 0)
            comment_dislikes = row.get(f'comment_{i}_dislikes', 0)
            comment_author = row.get(f'comment_{i}_author', '')
            comment_location = row.get(f'comment_{i}_location', '')
            
            if (pd.notna(comment_text) and 
                str(comment_text).strip() and 
                comment_dislikes > comment_likes):
                
                comentarios_politicos_impopulares.append({
                    'article_title': row['title'],
                    'article_date': row['date'],
                    'article_link': row['link'],
                    'article_source': row['source'],
                    'comment_text': comment_text,
                    'comment_author': comment_author,
                    'comment_location': comment_location,
                    'likes': comment_likes,
                    'dislikes': comment_dislikes,
                    'net_score': comment_dislikes - comment_likes
                })
    
    # Convertir a DataFrame y ordenar por net_score (mayor diferencia negativa)
    df_comentarios = pd.DataFrame(comentarios_politicos_impopulares)
    if len(df_comentarios) > 0:
        df_comentarios = df_comentarios.sort_values('net_score', ascending=True)
    
    return df_comentarios.head(top_n)

def procesar_articulos_politicos_polemicos(df, top_n=20):
    """
    Encuentra los artículos más polémicos que tienen comentarios políticos
    
    Args:
        df: DataFrame con artículos y comentarios ya filtrados por política
        top_n: Número de artículos top a devolver
        
    Returns:
        DataFrame con los artículos políticos más polémicos
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