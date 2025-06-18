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

def aplicar_filtros_esenciales(archivo_entrada="filtered_data.csv"):
    """
    Aplica SOLO los filtros esenciales que usa la aplicación Streamlit.
    Genera únicamente filtro1_localizacion.csv y filtro6_marin.csv
    """
    ruta_entrada = os.path.join(CARPETA_ENTRADA, archivo_entrada)
    
    print(f"🚀 FILTRADOR ESENCIAL - SOLO CSVs UTILIZADOS")
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
    print("FILTRO 1: LOCALIZACIÓN PARA LA VOZ DE GALICIA (O Morrazo/Pontevedra)")
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
    
    # =================== FILTRO 6: LOCALIZACIÓN: SOLO MARIN ===================
    print(f"\n" + "="*60)
    print("FILTRO 6: LOCALIZACIÓN ESPECÍFICA DE MARÍN")
    print("="*60)
    
    df_filtro6 = segundo_filtro_localizacion_voz_galicia(df_original)
    archivo_filtro6 = "filtro6_marin.csv"
    ruta_filtro6 = os.path.join(CARPETA_SALIDA, archivo_filtro6)
    df_filtro6.to_csv(ruta_filtro6, index=False)
    
    print(f"✅ Filtro 6 completado:")
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
    print(f"   • Filtro 1 (O Morrazo/Pontevedra): {len(df_filtro1):,} filas ({len(df_filtro1)/filas_originales*100:.1f}%)")
    print(f"   • Filtro 6 (Solo Marín): {len(df_filtro6):,} filas ({len(df_filtro6)/filas_originales*100:.1f}%)")
    
    # Mostrar distribución final por fuente para cada filtro
    for i, (df_filtrado, nombre_filtro) in enumerate([
        (df_filtro1, "Filtro 1 (O Morrazo/Pontevedra)"),
        (df_filtro6, "Filtro 6 (Solo Marín)")
    ], 1):
        if 'source' in df_filtrado.columns and len(df_filtrado) > 0:
            print(f"\n📰 DISTRIBUCIÓN {nombre_filtro.upper()}:")
            distribucion = df_filtrado['source'].value_counts()
            for fuente, cantidad in distribucion.items():
                porcentaje = cantidad/len(df_filtrado)*100
                print(f"   • {fuente}: {cantidad:,} filas ({porcentaje:.1f}%)")
    
    return {
        'filtro1': ruta_filtro1,
        'filtro6': ruta_filtro6
    }

def verificar_filtros():
    """
    Función auxiliar para verificar los resultados de los filtros esenciales.
    """
    archivos_verificar = [
        "filtro1_localizacion.csv",
        "filtro6_marin.csv"
    ]
    
    print(f"\n🔍 VERIFICACIÓN DE FILTROS ESENCIALES:")
    
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
        else:
            print(f"❌ {archivo}: No encontrado")

# Ejemplo de uso
if __name__ == "__main__":
    try:
        # Ejecutar los filtros esenciales
        rutas_generadas = aplicar_filtros_esenciales(
            archivo_entrada="filtered_data.csv"
        )
        
        # Verificar resultados
        verificar_filtros()
        
        print(f"\n🎉 ¡PROCESO COMPLETADO!")
        print(f"📁 Archivos generados en: {CARPETA_SALIDA}")
        print(f"📋 Archivos creados (solo los que usa Streamlit):")
        print(f"   • filtro1_localizacion.csv")
        print(f"   • filtro6_marin.csv")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")