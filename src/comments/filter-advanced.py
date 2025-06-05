import os
import pandas as pd
from datetime import datetime
import re

# Rutas basadas en tu estructura
RUTA_BASE = os.path.abspath(os.path.join("..", "data"))
CARPETA_ENTRADA = os.path.join(RUTA_BASE, "processed", "filtered-data")
CARPETA_SALIDA = os.path.join(RUTA_BASE, "processed", "filtered-data")
os.makedirs(CARPETA_SALIDA, exist_ok=True)

def tiene_texto_valido(texto):
    """Verifica si un comentario tiene texto válido (no solo espacios o nulo)"""
    if pd.isna(texto) or texto is None:
        return False
    texto_limpio = str(texto).strip()
    return len(texto_limpio) > 0

def primer_filtro_localizacion_voz_galicia(df):
    """
    Filtro 1: Para "La Voz de Galicia", LIMPIAR comentarios individuales que:
    1. Su location NO sea MARIN, BUEU, PONTEVEDRA, MOAÑA o nulo
    2. Su texto contenga "desde A CORUÑA"
    Eliminar líneas si no quedan comentarios válidos.
    """
    print("🔍 Aplicando filtro de localización para La Voz de Galicia...")
    
    df_filtrado = df.copy()
    localizaciones_permitidas_a = {'MARIN', 'BUEU', 'PONTEVEDRA', 'MOAÑA', '', 'NAN'}
    filas_eliminadas = []
    comentarios_limpiados_location_a = 0
    comentarios_limpiados_coruna_a = 0
    
    for idx, row in df_filtrado.iterrows():
        if row['source'] == "La Voz de Galicia":
            comentarios_validos = False
            
            # Revisar cada comentario
            for i in range(1, 16):  # comment_1 a comment_15
                texto_col = f'comment_{i}_text'
                location_col = f'comment_{i}_location'
                author_col = f'comment_{i}_author'
                date_col = f'comment_{i}_date'
                likes_col = f'comment_{i}_likes'
                dislikes_col = f'comment_{i}_dislikes'
                
                if texto_col in df_filtrado.columns and location_col in df_filtrado.columns:
                    texto = row[texto_col]
                    location = row[location_col]
                    
                    # Si tiene texto válido, verificar condiciones
                    if tiene_texto_valido(texto):
                        texto_str = str(texto)
                        location_limpia = str(location).strip().upper() if pd.notna(location) else ''
                        
                        # Condición 1: Verificar si contiene "desde A CORUÑA" y similares
                        if (
                            "desde A CORUÑA" in texto_str 
                            or "desde A Coruña" in texto_str 
                            or "desde La Coruña" in texto_str 
                            or "desde UK" in texto_str 
                            or "desde EE.UU." in texto_str
                            or "desde A Gudiña" in texto_str
                            or "desde O PORRIÑO" in texto_str
                            or "desde O GROVE" in texto_str
                            or "desde As Neves" in texto_str
                            or "desde A ESTRADA" in texto_str
                        ):
                            df_filtrado.at[idx, texto_col] = ''
                            df_filtrado.at[idx, author_col] = ''
                            df_filtrado.at[idx, location_col] = ''
                            df_filtrado.at[idx, date_col] = ''
                            if likes_col in df_filtrado.columns:
                                df_filtrado.at[idx, likes_col] = 0
                            if dislikes_col in df_filtrado.columns:
                                df_filtrado.at[idx, dislikes_col] = 0
                            comentarios_limpiados_coruna_a += 1
                            continue  # Ya limpiado, pasar al siguiente
                        
                        # Condición 2: Verificar location si NO contiene "desde A CORUÑA" y similares
                        if location_limpia not in localizaciones_permitidas_a and location_limpia != '':
                            df_filtrado.at[idx, texto_col] = ''
                            df_filtrado.at[idx, author_col] = ''
                            df_filtrado.at[idx, location_col] = ''
                            df_filtrado.at[idx, date_col] = ''
                            if likes_col in df_filtrado.columns:
                                df_filtrado.at[idx, likes_col] = 0
                            if dislikes_col in df_filtrado.columns:
                                df_filtrado.at[idx, dislikes_col] = 0
                            comentarios_limpiados_location_a += 1
                        
                        # Si pasa ambas condiciones, marcar como comentario válido
                        elif location_limpia in localizaciones_permitidas_a or location_limpia == '':
                            comentarios_validos = True
            
            # Si no quedan comentarios válidos para La Voz, eliminar la línea
            if not comentarios_validos:
                filas_eliminadas.append(idx)
    
    # Eliminar filas marcadas
    df_filtrado = df_filtrado.drop(filas_eliminadas)
    
    print(f"   📊 Comentarios limpiados por location no válida: {comentarios_limpiados_location_a}")
    print(f"   📊 Comentarios limpiados por 'desde A CORUÑA y similares': {comentarios_limpiados_coruna_a}")
    print(f"   📊 Filas eliminadas por no tener comentarios válidos: {len(filas_eliminadas)}")
    return df_filtrado.reset_index(drop=True)

def segundo_filtro_localizacion_voz_galicia(df):
    """
    Filtro 6: Para "La Voz de Galicia", LIMPIAR comentarios individuales que:
    1. Su location NO sea MARIN
    Eliminar líneas si no quedan comentarios válidos.
    """
    print("🔍 Aplicando filtro de localización para La Voz de Galicia...")
    
    df_filtrado = df.copy()
    localizaciones_permitidas_b = {'MARIN'}
    filas_eliminadas = []
    comentarios_limpiados_location_b = 0
    comentarios_limpiados_coruna_b = 0
    
    for idx, row in df_filtrado.iterrows():
        if row['source'] == "La Voz de Galicia":
            comentarios_validos = False
            
            # Revisar cada comentario
            for i in range(1, 16):  # comment_1 a comment_15
                texto_col = f'comment_{i}_text'
                location_col = f'comment_{i}_location'
                author_col = f'comment_{i}_author'
                date_col = f'comment_{i}_date'
                likes_col = f'comment_{i}_likes'
                dislikes_col = f'comment_{i}_dislikes'
                
                if texto_col in df_filtrado.columns and location_col in df_filtrado.columns:
                    texto = row[texto_col]
                    location = row[location_col]
                    
                    # Si tiene texto válido, verificar condiciones
                    if tiene_texto_valido(texto):
                        texto_str = str(texto)
                        location_limpia = str(location).strip().upper() if pd.notna(location) else ''
                        
                        # Condición 1: Verificar si contiene "desde A CORUÑA" y similares
                        if (
                            "desde A CORUÑA" in texto_str 
                            or "desde A Coruña" in texto_str 
                            or "desde La Coruña" in texto_str 
                            or "desde UK" in texto_str 
                            or "desde EE.UU." in texto_str
                            or "desde A Gudiña" in texto_str
                            or "desde O PORRIÑO" in texto_str
                            or "desde O GROVE" in texto_str
                            or "desde As Neves" in texto_str
                            or "desde A ESTRADA" in texto_str
                            or "desde el mundo" in texto_str
                            or "desde La federación del Jura" in texto_str
                            or "desde la más baja de las Rías Bajas" in texto_str
                            or "desde O mundo" in texto_str
                        ):
                            df_filtrado.at[idx, texto_col] = ''
                            df_filtrado.at[idx, author_col] = ''
                            df_filtrado.at[idx, location_col] = ''
                            df_filtrado.at[idx, date_col] = ''
                            if likes_col in df_filtrado.columns:
                                df_filtrado.at[idx, likes_col] = 0
                            if dislikes_col in df_filtrado.columns:
                                df_filtrado.at[idx, dislikes_col] = 0
                            comentarios_limpiados_coruna_b += 1
                            continue  # Ya limpiado, pasar al siguiente
                        
                        # Condición 2: Verificar location si NO contiene "desde A CORUÑA" y similares
                        if location_limpia not in localizaciones_permitidas_b:
                            df_filtrado.at[idx, texto_col] = ''
                            df_filtrado.at[idx, author_col] = ''
                            df_filtrado.at[idx, location_col] = ''
                            df_filtrado.at[idx, date_col] = ''
                            if likes_col in df_filtrado.columns:
                                df_filtrado.at[idx, likes_col] = 0
                            if dislikes_col in df_filtrado.columns:
                                df_filtrado.at[idx, dislikes_col] = 0
                            comentarios_limpiados_location_b += 1                        
                        
                        # Si pasa ambas condiciones, marcar como comentario válido
                        elif location_limpia in localizaciones_permitidas_b or location_limpia == '':
                            comentarios_validos = True
            
            # Si no quedan comentarios válidos para La Voz, eliminar la línea
            if not comentarios_validos:
                filas_eliminadas.append(idx)
    
    # Eliminar filas marcadas
    df_filtrado = df_filtrado.drop(filas_eliminadas)
    
    print(f"   📊 Comentarios limpiados por location no válida: {comentarios_limpiados_location_b}")
    print(f"   📊 Comentarios limpiados por 'desde A CORUÑA y similares': {comentarios_limpiados_coruna_b}")
    print(f"   📊 Filas eliminadas por no tener comentarios válidos: {len(filas_eliminadas)}")
    return df_filtrado.reset_index(drop=True)

def filtro_likes_dislikes(df):
    """
    Filtro 2: Eliminar líneas donde TODOS los likes y dislikes estén a 0.
    """
    print("🔍 Aplicando filtro de likes/dislikes...")
    
    df_filtrado = df.copy()
    filas_eliminadas = []
    
    for idx, row in df_filtrado.iterrows():
        tiene_interaccion = False
        
        # Revisar todos los likes y dislikes
        for i in range(1, 16):  # comment_1 a comment_15
            likes_col = f'comment_{i}_likes'
            dislikes_col = f'comment_{i}_dislikes'
            
            if likes_col in df_filtrado.columns and dislikes_col in df_filtrado.columns:
                likes = row[likes_col]
                dislikes = row[dislikes_col]
                
                # Si encuentra algún like o dislike > 0, marcar como válida
                if (pd.notna(likes) and likes > 0) or (pd.notna(dislikes) and dislikes > 0):
                    tiene_interaccion = True
                    break
        
        # Si no tiene ninguna interacción, marcar para eliminación
        if not tiene_interaccion:
            filas_eliminadas.append(idx)
    
    # Eliminar filas marcadas
    df_filtrado = df_filtrado.drop(filas_eliminadas)
    
    print(f"   📊 Filas eliminadas por filtro de likes/dislikes: {len(filas_eliminadas)}")
    return df_filtrado.reset_index(drop=True)

def filtro_mas_likes_que_dislikes(df):
    """
    Filtro 4: Eliminar comentarios donde dislikes >= likes. 
    Si no quedan comentarios con más likes que dislikes, eliminar la línea.
    """
    print("🔍 Aplicando filtro: mantener solo comentarios con más likes que dislikes...")
    
    df_filtrado = df.copy()
    filas_eliminadas = []
    comentarios_eliminados = 0
    
    for idx, row in df_filtrado.iterrows():
        comentarios_validos = False
        
        # Revisar cada comentario y limpiar los que tienen dislikes >= likes
        for i in range(1, 16):  # comment_1 a comment_15
            likes_col = f'comment_{i}_likes'
            dislikes_col = f'comment_{i}_dislikes'
            text_col = f'comment_{i}_text'
            author_col = f'comment_{i}_author'
            location_col = f'comment_{i}_location'
            date_col = f'comment_{i}_date'
            
            if (likes_col in df_filtrado.columns and dislikes_col in df_filtrado.columns):
                likes = row[likes_col] if pd.notna(row[likes_col]) else 0
                dislikes = row[dislikes_col] if pd.notna(row[dislikes_col]) else 0
                
                # Si tiene texto y dislikes >= likes, limpiar el comentario
                if tiene_texto_valido(row.get(text_col, '')) and dislikes >= likes:
                    df_filtrado.at[idx, text_col] = ''
                    df_filtrado.at[idx, author_col] = ''
                    df_filtrado.at[idx, location_col] = ''
                    df_filtrado.at[idx, date_col] = ''
                    df_filtrado.at[idx, likes_col] = 0
                    df_filtrado.at[idx, dislikes_col] = 0
                    comentarios_eliminados += 1
                
                # Verificar si quedan comentarios válidos (con texto y likes > dislikes)
                elif tiene_texto_valido(row.get(text_col, '')) and likes > dislikes:
                    comentarios_validos = True
        
        # Si no quedan comentarios válidos, marcar línea para eliminación
        if not comentarios_validos:
            filas_eliminadas.append(idx)
    
    # Eliminar filas marcadas
    df_filtrado = df_filtrado.drop(filas_eliminadas)
    
    print(f"   📊 Comentarios individuales eliminados: {comentarios_eliminados}")
    print(f"   📊 Filas eliminadas por no tener comentarios válidos: {len(filas_eliminadas)}")
    return df_filtrado.reset_index(drop=True)

def filtro_mas_dislikes_que_likes(df):
    """
    Filtro 5: Eliminar comentarios donde likes >= dislikes.
    Si no quedan comentarios con más dislikes que likes, eliminar la línea.
    """
    print("🔍 Aplicando filtro: mantener solo comentarios con más dislikes que likes...")
    
    df_filtrado = df.copy()
    filas_eliminadas = []
    comentarios_eliminados = 0
    
    for idx, row in df_filtrado.iterrows():
        comentarios_validos = False
        
        # Revisar cada comentario y limpiar los que tienen likes >= dislikes
        for i in range(1, 16):  # comment_1 a comment_15
            likes_col = f'comment_{i}_likes'
            dislikes_col = f'comment_{i}_dislikes'
            text_col = f'comment_{i}_text'
            author_col = f'comment_{i}_author'
            location_col = f'comment_{i}_location'
            date_col = f'comment_{i}_date'
            
            if (likes_col in df_filtrado.columns and dislikes_col in df_filtrado.columns):
                likes = row[likes_col] if pd.notna(row[likes_col]) else 0
                dislikes = row[dislikes_col] if pd.notna(row[dislikes_col]) else 0
                
                # Si tiene texto y likes >= dislikes, limpiar el comentario
                if tiene_texto_valido(row.get(text_col, '')) and likes >= dislikes:
                    df_filtrado.at[idx, text_col] = ''
                    df_filtrado.at[idx, author_col] = ''
                    df_filtrado.at[idx, location_col] = ''
                    df_filtrado.at[idx, date_col] = ''
                    df_filtrado.at[idx, likes_col] = 0
                    df_filtrado.at[idx, dislikes_col] = 0
                    comentarios_eliminados += 1
                
                # Verificar si quedan comentarios válidos (con texto y dislikes > likes)
                elif tiene_texto_valido(row.get(text_col, '')) and dislikes > likes:
                    comentarios_validos = True
        
        # Si no quedan comentarios válidos, marcar línea para eliminación
        if not comentarios_validos:
            filas_eliminadas.append(idx)
    
    # Eliminar filas marcadas
    df_filtrado = df_filtrado.drop(filas_eliminadas)
    
    print(f"   📊 Comentarios individuales eliminados: {comentarios_eliminados}")
    print(f"   📊 Filas eliminadas por no tener comentarios válidos: {len(filas_eliminadas)}")
    return df_filtrado.reset_index(drop=True)

def aplicar_filtros_triple(archivo_entrada="filtered_data.csv"):
    """
    Aplica los tres filtros y genera tres CSVs diferentes.
    """
    ruta_entrada = os.path.join(CARPETA_ENTRADA, archivo_entrada)
    
    print(f"🚀 FILTRADOR TRIPLE")
    print(f"   • Archivo entrada: {ruta_entrada}")
    print(f"   • Carpeta salida: {CARPETA_SALIDA}")
    
    # Verificar que existe el archivo de entrada
    if not os.path.exists(ruta_entrada):
        raise FileNotFoundError(f"❌ No se encontró el archivo: {ruta_entrada}")
    
    print(f"\n📖 Cargando datos...")
    df_original = pd.read_csv(ruta_entrada)
    filas_originales = len(df_original)
    
    print(f"✅ Archivo cargado: {filas_originales:,} filas, {len(df_original.columns)} columnas")
    
    # Mostrar distribución inicial por fuente
    if 'source' in df_original.columns:
        print(f"\n📰 DISTRIBUCIÓN INICIAL POR FUENTE:")
        distribucion_inicial = df_original['source'].value_counts()
        for fuente, cantidad in distribucion_inicial.items():
            print(f"   • {fuente}: {cantidad:,} filas")
    
    # =================== FILTRO 1: LOCALIZACIÓN VOZ GALICIA ===================
    print(f"\n" + "="*60)
    print("FILTRO 1: LOCALIZACIÓN PARA LA VOZ DE GALICIA")
    print("="*60)
    
    df_filtro1 = primer_filtro_localizacion_voz_galicia(df_original)
    archivo_filtro1 = "filtro1_localizacion.csv"
    ruta_filtro1 = os.path.join(CARPETA_SALIDA, archivo_filtro1)
    df_filtro1.to_csv(ruta_filtro1, index=False)
    
    print(f"✅ Filtro 1 completado:")
    print(f"   • Filas originales: {filas_originales:,}")
    print(f"   • Filas después del filtro: {len(df_filtro1):,}")
    print(f"   • Filas eliminadas: {filas_originales - len(df_filtro1):,}")
    print(f"   • Archivo guardado: {archivo_filtro1}")
    
    # =================== FILTRO 2: LIKES/DISLIKES ===================
    print(f"\n" + "="*60)
    print("FILTRO 2: LIKES/DISLIKES")
    print("="*60)
    
    df_filtro2 = filtro_likes_dislikes(df_original)
    archivo_filtro2 = "filtro2_likes_dislikes.csv"
    ruta_filtro2 = os.path.join(CARPETA_SALIDA, archivo_filtro2)
    df_filtro2.to_csv(ruta_filtro2, index=False)
    
    print(f"✅ Filtro 2 completado:")
    print(f"   • Filas originales: {filas_originales:,}")
    print(f"   • Filas después del filtro: {len(df_filtro2):,}")
    print(f"   • Filas eliminadas: {filas_originales - len(df_filtro2):,}")
    print(f"   • Archivo guardado: {archivo_filtro2}")
    
    # =================== FILTRO 3: COMBINADO ===================
    print(f"\n" + "="*60)
    print("FILTRO 3: COMBINADO (LOCALIZACIÓN + LIKES/DISLIKES)")
    print("="*60)
    
    # Aplicar primero filtro de localización, luego filtro de likes/dislikes
    df_filtro3 = primer_filtro_localizacion_voz_galicia(df_original)
    df_filtro3 = filtro_likes_dislikes(df_filtro3)
    
    archivo_filtro3 = "filtro3_combinado.csv"
    ruta_filtro3 = os.path.join(CARPETA_SALIDA, archivo_filtro3)
    df_filtro3.to_csv(ruta_filtro3, index=False)
    
    print(f"✅ Filtro 3 completado:")
    print(f"   • Filas originales: {filas_originales:,}")
    print(f"   • Filas después del filtro: {len(df_filtro3):,}")
    print(f"   • Filas eliminadas: {filas_originales - len(df_filtro3):,}")
    print(f"   • Archivo guardado: {archivo_filtro3}")
    
    # =================== FILTRO 4: COMBINADO + MÁS LIKES QUE DISLIKES ===================
    print(f"\n" + "="*60)
    print("FILTRO 4: COMBINADO + MÁS LIKES QUE DISLIKES")
    print("="*60)
    
    # Aplicar filtros 1, 2 y luego el nuevo filtro 4
    df_filtro4 = primer_filtro_localizacion_voz_galicia(df_original)
    df_filtro4 = filtro_likes_dislikes(df_filtro4)
    df_filtro4 = filtro_mas_likes_que_dislikes(df_filtro4)
    
    archivo_filtro4 = "filtro4_mas_likes.csv"
    ruta_filtro4 = os.path.join(CARPETA_SALIDA, archivo_filtro4)
    df_filtro4.to_csv(ruta_filtro4, index=False)
    
    print(f"✅ Filtro 4 completado:")
    print(f"   • Filas originales: {filas_originales:,}")
    print(f"   • Filas después del filtro: {len(df_filtro4):,}")
    print(f"   • Filas eliminadas: {filas_originales - len(df_filtro4):,}")
    print(f"   • Archivo guardado: {archivo_filtro4}")
    
    # =================== FILTRO 5: COMBINADO + MÁS DISLIKES QUE LIKES ===================
    print(f"\n" + "="*60)
    print("FILTRO 5: COMBINADO + MÁS DISLIKES QUE LIKES")
    print("="*60)
    
    # Aplicar filtros 1, 2 y luego el nuevo filtro 5
    df_filtro5 = primer_filtro_localizacion_voz_galicia(df_original)
    df_filtro5 = filtro_likes_dislikes(df_filtro5)
    df_filtro5 = filtro_mas_dislikes_que_likes(df_filtro5)
    
    archivo_filtro5 = "filtro5_mas_dislikes.csv"
    ruta_filtro5 = os.path.join(CARPETA_SALIDA, archivo_filtro5)
    df_filtro5.to_csv(ruta_filtro5, index=False)
    
    print(f"✅ Filtro 5 completado:")
    print(f"   • Filas originales: {filas_originales:,}")
    print(f"   • Filas después del filtro: {len(df_filtro5):,}")
    print(f"   • Filas eliminadas: {filas_originales - len(df_filtro5):,}")
    print(f"   • Archivo guardado: {archivo_filtro5}")

    # =================== FILTRO 6: LOCALIZACIÓN: SOLO MARIN ===================
    print(f"\n" + "="*60)
    print("FILTRO 1: LOCALIZACIÓN PARA LA VOZ DE GALICIA")
    print("="*60)
    
    df_filtro6 = segundo_filtro_localizacion_voz_galicia(df_original)
    archivo_filtro6 = "filtro6_marin.csv"
    ruta_filtro6 = os.path.join(CARPETA_SALIDA, archivo_filtro6)
    df_filtro6.to_csv(ruta_filtro6, index=False)
    
    print(f"✅ Filtro 1 completado:")
    print(f"   • Filas originales: {filas_originales:,}")
    print(f"   • Filas después del filtro: {len(df_filtro6):,}")
    print(f"   • Filas eliminadas: {filas_originales - len(df_filtro6):,}")
    print(f"   • Archivo guardado: {archivo_filtro6}")
    
    
    # =================== RESUMEN FINAL ===================
    print(f"\n" + "="*60)
    print("RESUMEN FINAL")
    print("="*60)
    
    print(f"📊 ESTADÍSTICAS FINALES:")
    print(f"   • Archivo original: {filas_originales:,} filas")
    print(f"   • Filtro 1 (Localización): {len(df_filtro1):,} filas ({len(df_filtro1)/filas_originales*100:.1f}%)")
    print(f"   • Filtro 2 (Likes/Dislikes): {len(df_filtro2):,} filas ({len(df_filtro2)/filas_originales*100:.1f}%)")
    print(f"   • Filtro 3 (Combinado): {len(df_filtro3):,} filas ({len(df_filtro3)/filas_originales*100:.1f}%)")
    print(f"   • Filtro 4 (+ Más Likes): {len(df_filtro4):,} filas ({len(df_filtro4)/filas_originales*100:.1f}%)")
    print(f"   • Filtro 5 (+ Más Dislikes): {len(df_filtro5):,} filas ({len(df_filtro5)/filas_originales*100:.1f}%)")
    print(f"   • Filtro 6 (Solo Marin): {len(df_filtro6):,} filas ({len(df_filtro6)/filas_originales*100:.1f}%)")
    
    # Mostrar distribución final por fuente para cada filtro
    for i, (df_filtrado, nombre_filtro) in enumerate([
        (df_filtro1, "Filtro 1 (Localización)"),
        (df_filtro2, "Filtro 2 (Likes/Dislikes)"),
        (df_filtro3, "Filtro 3 (Combinado)"),
        (df_filtro4, "Filtro 4 (+ Más Likes)"),
        (df_filtro5, "Filtro 5 (+ Más Dislikes)"),
        (df_filtro6, "Filtro 6 (Solo Marin)")
    ], 1):
        if 'source' in df_filtrado.columns and len(df_filtrado) > 0:
            print(f"\n📰 DISTRIBUCIÓN {nombre_filtro.upper()}:")
            distribucion = df_filtrado['source'].value_counts()
            for fuente, cantidad in distribucion.items():
                porcentaje = cantidad/len(df_filtrado)*100
                print(f"   • {fuente}: {cantidad:,} filas ({porcentaje:.1f}%)")
    
    return {
        'filtro1': ruta_filtro1,
        'filtro2': ruta_filtro2,
        'filtro3': ruta_filtro3,
        'filtro4': ruta_filtro4,
        'filtro5': ruta_filtro5,
        'filtro6': ruta_filtro6
    }

def verificar_filtros():
    """
    Función auxiliar para verificar los resultados de los filtros.
    """
    archivos_verificar = [
        "filtro1_localizacion.csv",
        "filtro2_likes_dislikes.csv", 
        "filtro3_combinado.csv",
        "filtro4_mas_likes.csv",
        "filtro5_mas_dislikes.csv",
        "filtro6_marin.csv"
    ]
    
    print(f"\n🔍 VERIFICACIÓN DE FILTROS:")
    
    for archivo in archivos_verificar:
        ruta_archivo = os.path.join(CARPETA_SALIDA, archivo)
        
        if os.path.exists(ruta_archivo):
            df = pd.read_csv(ruta_archivo)
            print(f"\n✅ {archivo}:")
            print(f"   • Filas: {len(df):,}")
            print(f"   • Columnas: {len(df.columns)}")
            
            if 'source' in df.columns:
                print(f"   • Fuentes: {df['source'].value_counts().to_dict()}")
                
            if 'n_comments' in df.columns:
                print(f"   • Comentarios (min/max/media): {df['n_comments'].min()}/{df['n_comments'].max()}/{df['n_comments'].mean():.1f}")
                
            # Verificación específica para filtros 4 y 5
            if "mas_likes" in archivo:
                # Contar comentarios con más likes que dislikes
                comentarios_validos = 0
                for i in range(1, 16):
                    likes_col = f'comment_{i}_likes'
                    dislikes_col = f'comment_{i}_dislikes'
                    text_col = f'comment_{i}_text'
                    if all(col in df.columns for col in [likes_col, dislikes_col, text_col]):
                        # Verificar texto válido de forma segura
                        texto_valido = df[text_col].apply(lambda x: tiene_texto_valido(x) if pd.notna(x) else False)
                        likes_mayor = df[likes_col] > df[dislikes_col]
                        mask = texto_valido & likes_mayor
                        comentarios_validos += mask.sum()
                print(f"   • Comentarios con más likes que dislikes: {comentarios_validos}")
                
            elif "mas_dislikes" in archivo:
                # Contar comentarios con más dislikes que likes
                comentarios_validos = 0
                for i in range(1, 16):
                    likes_col = f'comment_{i}_likes'
                    dislikes_col = f'comment_{i}_dislikes'
                    text_col = f'comment_{i}_text'
                    if all(col in df.columns for col in [likes_col, dislikes_col, text_col]):
                        # Verificar texto válido de forma segura
                        texto_valido = df[text_col].apply(lambda x: tiene_texto_valido(x) if pd.notna(x) else False)
                        dislikes_mayor = df[dislikes_col] > df[likes_col]
                        mask = texto_valido & dislikes_mayor
                        comentarios_validos += mask.sum()
                print(f"   • Comentarios con más dislikes que likes: {comentarios_validos}")
        else:
            print(f"❌ {archivo}: No encontrado")

# Ejemplo de uso
if __name__ == "__main__":
    try:
        # Ejecutar los filtros
        rutas_generadas = aplicar_filtros_triple(
            archivo_entrada="filtered_data.csv"
        )
        
        # Verificar resultados
        verificar_filtros()
        
        print(f"\n🎉 ¡PROCESO COMPLETADO!")
        print(f"📁 Archivos generados en: {CARPETA_SALIDA}")
        print(f"📋 Archivos creados:")
        print(f"   • filtro1_localizacion.csv")
        print(f"   • filtro2_likes_dislikes.csv")
        print(f"   • filtro3_combinado.csv")
        print(f"   • filtro4_mas_likes.csv")
        print(f"   • filtro5_mas_dislikes.csv")
        print(f"   • filtro6_marin.csv")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")