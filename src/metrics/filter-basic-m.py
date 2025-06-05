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
# 1. VISUALIZACIONES POR MES (ya existía)
# ============================================================================
df_por_mes = df.sort_values(by=["year_month", "n_visualizations"], ascending=[False, False])
archivo_por_mes = os.path.join(carpeta_salida, "visualizaciones_por_mes.csv")
df_por_mes.to_csv(archivo_por_mes, index=False)
print(f"✅ Archivo generado: {archivo_por_mes}")

# ============================================================================
# 2. VISUALIZACIONES POR AÑO
# ============================================================================
# Ordenar TODOS los artículos por año (descendente) y luego por visualizaciones (descendente)
df_por_año = df.sort_values(by=["year", "n_visualizations"], ascending=[False, False])

# Seleccionar columnas relevantes
columnas_importantes = ["source", "title", "link", "date", "n_visualizations", "summary", "year_month", "year"]
df_por_año = df_por_año[columnas_importantes]

# Guardar
archivo_por_año = os.path.join(carpeta_salida, "visualizaciones_por_año.csv")
df_por_año.to_csv(archivo_por_año, index=False)
print(f"✅ Archivo generado: {archivo_por_año}")

# ============================================================================
# 3. VISUALIZACIONES TOTALES (todos los artículos ordenados)
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
print(f"\n📊 RESUMEN DE ARCHIVOS GENERADOS:")
print(f"📁 Carpeta: {carpeta_salida}")
print(f"1️⃣  visualizaciones_por_mes.csv - {len(df_por_mes)} artículos ordenados por mes")
print(f"2️⃣  visualizaciones_por_año.csv - {len(df_por_año)} artículos ordenados por año y visualizaciones")
print(f"3️⃣  visualizaciones_totales.csv - {len(df_totales)} artículos ordenados por popularidad")

# Mostrar preview de artículos más vistos por año
print(f"\n🔥 TOP ARTÍCULOS POR AÑO:")
for year in sorted(df['year'].dropna().unique(), reverse=True):
    top_article = df[df['year'] == year].nlargest(1, 'n_visualizations').iloc[0]
    print(f"   {int(year)}: {top_article['n_visualizations']:,} visualizaciones - {top_article['title'][:50]}...")