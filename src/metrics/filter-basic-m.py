import pandas as pd
import os
import glob

# Definir rutas
ruta_base = os.path.abspath(os.path.join("..", "..", "data"))
carpeta_entrada = os.path.join(ruta_base, "raw", "clean-metrics")
carpeta_salida = os.path.join(ruta_base, "processed", "metrics-data")

# Buscar archivos CSV
archivos_csv = glob.glob(os.path.join(carpeta_entrada, "*.csv"))
if not archivos_csv:
    raise FileNotFoundError("No se encontraron archivos CSV en la carpeta")

# Leer archivo
df = pd.read_csv(archivos_csv[0])

# Validar columnas necesarias
if "date" not in df.columns or "n_visualizations" not in df.columns:
    raise ValueError("Faltan columnas requeridas: 'date' o 'n_visualizations'")

# Convertir fecha
df["date"] = pd.to_datetime(df["date"], errors="coerce")

# Crear columnas de tiempo
df["year_month"] = df["date"].dt.to_period("M").astype(str)
df["year"] = df["date"].dt.year

# Crear carpeta de salida
os.makedirs(carpeta_salida, exist_ok=True)

# ============================================================================
# VISUALIZACIONES TOTALES (todos los artículos ordenados)
# ============================================================================
# Ordenar todos los artículos por visualizaciones descendente
df_totales = df.sort_values("n_visualizations", ascending=False)

# Seleccionar columnas relevantes
columnas_importantes = ["source", "title", "link", "date", "n_visualizations", "summary", "year_month", "year"]
df_totales = df_totales[columnas_importantes]

# Guardar
archivo_totales = os.path.join(carpeta_salida, "visualizaciones_totales.csv")
df_totales.to_csv(archivo_totales, index=False)
print(f"✅ Archivo generado: {archivo_totales}")

# ============================================================================
# RESUMEN
# ============================================================================
print(f"\n📊 RESUMEN DE ARCHIVO GENERADO:")
print(f"📁 Carpeta: {carpeta_salida}")
print(f"📄 visualizaciones_totales.csv - {len(df_totales)} artículos ordenados por popularidad")

# Mostrar preview de artículos más vistos por año
print(f"\n🔥 TOP ARTÍCULOS POR AÑO:")
for year in sorted(df['year'].dropna().unique(), reverse=True):
    top_article = df[df['year'] == year].nlargest(1, 'n_visualizations').iloc[0]
    print(f"   {int(year)}: {top_article['n_visualizations']:,} visualizaciones - {top_article['title'][:50]}...")