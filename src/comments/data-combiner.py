import os
import pandas as pd
from datetime import datetime

# Rutas internas basadas en tu estructura
RUTA_BASE = os.path.abspath(os.path.join("..", "data"))
CARPETA_ENTRADA = os.path.join(RUTA_BASE, "raw", "clean-csvs")
CARPETA_SALIDA = os.path.join(RUTA_BASE, "processed", "combined-data")
os.makedirs(CARPETA_SALIDA, exist_ok=True)

def reordenar_columnas_comentarios(df):
    """
    Reordena las columnas para mantener agrupados los datos de cada comentario.
    Patrón: comment_X_author, comment_X_location, comment_X_date, comment_X_text, comment_X_likes, comment_X_dislikes
    """
    # Identificar columnas base (no de comentarios)
    base_columns = []
    comment_columns = []
    
    for col in df.columns:
        if col.startswith('comment_') and '_' in col:
            comment_columns.append(col)
        else:
            base_columns.append(col)
    
    # Poner "source" al principio, luego ordenar el resto alfabéticamente
    if 'source' in base_columns:
        base_columns.remove('source')
        base_columns.sort()
        base_columns = ['source'] + base_columns
    else:
        base_columns.sort()
    
    # Agrupar columnas de comentarios por número
    comment_groups = {}
    for col in comment_columns:
        # Extraer número de comentario (ej: comment_1_author -> 1)
        parts = col.split('_')
        if len(parts) >= 3:
            try:
                comment_num = int(parts[1])
                if comment_num not in comment_groups:
                    comment_groups[comment_num] = []
                comment_groups[comment_num].append(col)
            except ValueError:
                continue
    
    # Ordenar columnas dentro de cada grupo de comentario
    ordered_comment_columns = []
    for i in sorted(comment_groups.keys()):
        group = comment_groups[i]
        # Orden deseado: author, location, date, text, likes, dislikes
        order_priority = {
            'author': 0,
            'location': 1,
            'date': 2,
            'text': 3,
            'likes': 4,
            'dislikes': 5
        }
        
        def get_priority(col_name):
            for suffix, priority in order_priority.items():
                if col_name.endswith(f'_{suffix}'):
                    return priority
            return 999  # Para sufijos no reconocidos
        
        group.sort(key=get_priority)
        ordered_comment_columns.extend(group)
    
    # Combinar: columnas base + columnas de comentarios ordenadas
    final_order = base_columns + ordered_comment_columns
    
    # Filtrar solo columnas que existen en el DataFrame
    final_order = [col for col in final_order if col in df.columns]
    
    return df[final_order]

def mixer_csvs(columna_texto="title", archivo_salida="combined_data.csv"):
    """
    Combina múltiples CSV desde clean-csvs/ en un solo archivo gigante.

    Args:
        columna_texto (str): Columna principal sobre la que se hará análisis.
        archivo_salida (str): Nombre del archivo CSV combinado.
    
    Returns:
        str: Ruta del archivo generado
    """
    archivos = [f for f in os.listdir(CARPETA_ENTRADA) if f.endswith(".csv")]

    if not archivos:
        raise FileNotFoundError(f"No se encontraron CSVs en {CARPETA_ENTRADA}")

    print(f"📁 Encontrados {len(archivos)} archivos CSV")
    
    dataframes = []
    estadisticas = []

    for archivo in archivos:
        print(f"📖 Procesando: {archivo}")
        ruta_archivo = os.path.join(CARPETA_ENTRADA, archivo)
        
        try:
            df = pd.read_csv(ruta_archivo)
            filas_originales = len(df)
            
            # Verificar que existe la columna principal
            if columna_texto not in df.columns:
                print(f"⚠️  {archivo} no contiene la columna '{columna_texto}'. Saltado.")
                continue

            # Limpiar columna principal
            df[columna_texto] = df[columna_texto].fillna("")
            
            dataframes.append(df)
            estadisticas.append({
                "archivo": archivo,
                "filas": filas_originales
            })
            
            print(f"✅ {archivo}: {filas_originales} filas")
            
        except Exception as e:
            print(f"❌ Error procesando {archivo}: {str(e)}")
            continue

    if not dataframes:
        raise ValueError("No se pudo procesar ningún archivo CSV válido")

    # Combinar todos los DataFrames
    print(f"\n🔄 Combinando {len(dataframes)} DataFrames...")
    df_combinado = pd.concat(dataframes, ignore_index=True, sort=False)
    
    # Reordenar columnas para mantener estructura lógica de comentarios
    print("🔄 Reordenando columnas...")
    df_combinado = reordenar_columnas_comentarios(df_combinado)
    
    # Convertir likes y dislikes a enteros
    print("🔄 Convirtiendo likes/dislikes a enteros...")
    likes_dislikes_columns = [col for col in df_combinado.columns if col.endswith(('_likes', '_dislikes'))]
    for col in likes_dislikes_columns:
        df_combinado[col] = df_combinado[col].fillna(0).astype(int)
    
    # Guardar el archivo combinado
    ruta_salida = os.path.join(CARPETA_SALIDA, archivo_salida)
    df_combinado.to_csv(ruta_salida, index=False)
    
    # Mostrar estadísticas finales
    print(f"\n📊 RESUMEN:")
    print(f"   • Total de filas: {len(df_combinado):,}")
    print(f"   • Total de columnas: {len(df_combinado.columns)}")
    print(f"   • Archivos procesados: {len(estadisticas)}")
    print(f"   • Archivo guardado en: {ruta_salida}")
    
    print(f"\n📋 DESGLOSE POR ARCHIVO:")
    for stat in estadisticas:
        print(f"   • {stat['archivo']}: {stat['filas']:,} filas")
    
    # Mostrar info de las columnas
    print(f"\n🏷️  COLUMNAS EN EL DATASET FINAL:")
    for col in df_combinado.columns:
        print(f"   • {col}")
    
    return ruta_salida

def verificar_datos_combinados(archivo_combinado="combined_data.csv"):
    """
    Función auxiliar para verificar el archivo combinado.
    """
    ruta_archivo = os.path.join(CARPETA_SALIDA, archivo_combinado)
    
    if not os.path.exists(ruta_archivo):
        print(f"❌ No existe el archivo: {ruta_archivo}")
        return
    
    df = pd.read_csv(ruta_archivo)
    
    print(f"🔍 VERIFICACIÓN DEL ARCHIVO COMBINADO:")
    print(f"   • Filas totales: {len(df):,}")
    print(f"   • Columnas: {len(df.columns)}")
    
    # Mostrar información por fuente si existe la columna
    if 'source' in df.columns:
        print(f"   • Fuentes únicas: {df['source'].nunique()}")
        print(f"\n📰 DISTRIBUCIÓN POR FUENTE:")
        print(df['source'].value_counts())

# Ejemplo de uso
if __name__ == "__main__":
    try:
        # Ejecutar el mixer
        archivo_generado = mixer_csvs(
            columna_texto="title",  # Cambia por tu columna principal
            archivo_salida="combined_data.csv"
        )
        
        # Verificar resultados
        print(f"\n" + "="*50)
        verificar_datos_combinados("combined_data.csv")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")