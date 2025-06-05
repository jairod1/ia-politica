import os
import pandas as pd
from datetime import datetime

# Rutas basadas en tu estructura
RUTA_BASE = os.path.abspath(os.path.join("..", "data"))
CARPETA_ENTRADA = os.path.join(RUTA_BASE, "processed", "combined-data")
CARPETA_SALIDA = os.path.join(RUTA_BASE, "processed", "filtered-data")
os.makedirs(CARPETA_SALIDA, exist_ok=True)

def filtrar_por_comentarios(archivo_entrada="combined_data.csv", 
                           archivo_salida="filtered_data.csv",
                           columna_comentarios="n_comments",
                           minimo_comentarios=1):
    """
    Filtra el CSV combinado para mantener solo filas con comentarios > 0.
    
    Args:
        archivo_entrada (str): Nombre del archivo CSV de entrada
        archivo_salida (str): Nombre del archivo CSV filtrado
        columna_comentarios (str): Nombre de la columna de comentarios
        minimo_comentarios (int): Número mínimo de comentarios (por defecto 1, que es > 0)
    
    Returns:
        str: Ruta del archivo filtrado generado
    """
    
    # Rutas completas
    ruta_entrada = os.path.join(CARPETA_ENTRADA, archivo_entrada)
    ruta_salida = os.path.join(CARPETA_SALIDA, archivo_salida)
    
    print(f"🔍 FILTRADOR DE CSV POR COMENTARIOS")
    print(f"   • Archivo entrada: {ruta_entrada}")
    print(f"   • Archivo salida: {ruta_salida}")
    print(f"   • Filtro: {columna_comentarios} > {minimo_comentarios - 1}")
    
    # Verificar que existe el archivo de entrada
    if not os.path.exists(ruta_entrada):
        raise FileNotFoundError(f"❌ No se encontró el archivo: {ruta_entrada}")
    
    print(f"\n📖 Cargando datos...")
    
    try:
        # Cargar el CSV
        df_original = pd.read_csv(ruta_entrada)
        filas_originales = len(df_original)
        
        print(f"✅ Archivo cargado: {filas_originales:,} filas, {len(df_original.columns)} columnas")
        
        # Verificar que existe la columna de comentarios
        if columna_comentarios not in df_original.columns:
            raise ValueError(f"❌ La columna '{columna_comentarios}' no existe en el archivo")
        
        # Mostrar información sobre la columna de comentarios
        print(f"\n📊 ANÁLISIS DE LA COLUMNA '{columna_comentarios}':")
        comentarios_info = df_original[columna_comentarios].describe()
        print(f"   • Valores no nulos: {df_original[columna_comentarios].count():,}")
        print(f"   • Valores nulos: {df_original[columna_comentarios].isnull().sum():,}")
        print(f"   • Mínimo: {comentarios_info['min']}")
        print(f"   • Máximo: {comentarios_info['max']}")
        print(f"   • Media: {comentarios_info['mean']:.2f}")
        print(f"   • Mediana: {comentarios_info['50%']}")
        
        # Contar cuántas tienen 0 comentarios vs > 0
        sin_comentarios = (df_original[columna_comentarios] == 0).sum()
        con_comentarios = (df_original[columna_comentarios] > 0).sum()
        nulos = df_original[columna_comentarios].isnull().sum()
        
        print(f"\n📈 DISTRIBUCIÓN:")
        print(f"   • Con 0 comentarios: {sin_comentarios:,} ({sin_comentarios/filas_originales*100:.1f}%)")
        print(f"   • Con > 0 comentarios: {con_comentarios:,} ({con_comentarios/filas_originales*100:.1f}%)")
        if nulos > 0:
            print(f"   • Valores nulos: {nulos:,} ({nulos/filas_originales*100:.1f}%)")
        
        # Aplicar el filtro
        print(f"\n🔄 Aplicando filtro: {columna_comentarios} >= {minimo_comentarios}")
        
        # Filtrar (manejar valores nulos como 0)
        df_filtrado = df_original[df_original[columna_comentarios].fillna(0) >= minimo_comentarios].copy()
        filas_filtradas = len(df_filtrado)
        
        # Añadir metadatos del filtrado
        df_filtrado["fecha_filtrado"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        df_filtrado["filtro_aplicado"] = f"{columna_comentarios}>={minimo_comentarios}"
        
        # Guardar el archivo filtrado
        df_filtrado.to_csv(ruta_salida, index=False)
        
        # Estadísticas finales
        filas_eliminadas = filas_originales - filas_filtradas
        porcentaje_mantenido = (filas_filtradas / filas_originales) * 100
        
        print(f"\n✅ FILTRADO COMPLETADO:")
        print(f"   • Filas originales: {filas_originales:,}")
        print(f"   • Filas filtradas: {filas_filtradas:,}")
        print(f"   • Filas eliminadas: {filas_eliminadas:,}")
        print(f"   • Porcentaje mantenido: {porcentaje_mantenido:.1f}%")
        print(f"   • Archivo guardado en: {ruta_salida}")
        
        # Mostrar distribución por archivo origen (si existe)
        if "archivo_origen" in df_filtrado.columns:
            print(f"\n📋 DISTRIBUCIÓN POR ARCHIVO ORIGEN (después del filtro):")
            distribucion = df_filtrado["archivo_origen"].value_counts()
            for archivo, cantidad in distribucion.items():
                print(f"   • {archivo}: {cantidad:,} filas")
        
        # Mostrar distribución por municipio (si existe)
        if "municipio" in df_filtrado.columns:
            print(f"\n🏙️  DISTRIBUCIÓN POR MUNICIPIO (después del filtro):")
            distribucion_municipio = df_filtrado["municipio"].value_counts()
            for municipio, cantidad in distribucion_municipio.items():
                print(f"   • {municipio}: {cantidad:,} filas")
        
        return ruta_salida
        
    except Exception as e:
        raise Exception(f"❌ Error procesando el archivo: {str(e)}")

def verificar_filtro(archivo_filtrado="filtered_data.csv"):
    """
    Función auxiliar para verificar el resultado del filtro.
    """
    ruta_archivo = os.path.join(CARPETA_SALIDA, archivo_filtrado)
    
    if not os.path.exists(ruta_archivo):
        print(f"❌ No existe el archivo filtrado: {ruta_archivo}")
        return
    
    df = pd.read_csv(ruta_archivo)
    
    print(f"\n🔍 VERIFICACIÓN DEL ARCHIVO FILTRADO:")
    print(f"   • Filas totales: {len(df):,}")
    print(f"   • Columnas: {len(df.columns)}")
    
    if "n_comments" in df.columns:
        print(f"   • Mín comentarios: {df['n_comments'].min()}")
        print(f"   • Máx comentarios: {df['n_comments'].max()}")
        print(f"   • Media comentarios: {df['n_comments'].mean():.2f}")
        
        # Verificar que el filtro se aplicó correctamente
        filas_con_cero = (df['n_comments'] == 0).sum()
        if filas_con_cero > 0:
            print(f"⚠️  ADVERTENCIA: {filas_con_cero} filas tienen 0 comentarios")
        else:
            print(f"✅ Filtro correcto: todas las filas tienen > 0 comentarios")

# Ejemplo de uso
if __name__ == "__main__":
    try:
        # Ejecutar el filtro
        archivo_generado = filtrar_por_comentarios(
            archivo_entrada="combined_data.csv",
            archivo_salida="filtered_data.csv",
            columna_comentarios="n_comments",
            minimo_comentarios=1  # > 0 comentarios
        )
        
        # Verificar resultados
        print(f"\n" + "="*60)
        verificar_filtro("filtered_data.csv")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")