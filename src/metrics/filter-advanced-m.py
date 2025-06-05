import pandas as pd
import os
import re

# Definir rutas
ruta_base = os.path.abspath(os.path.join("..", "..", "data"))
carpeta_entrada = os.path.join(ruta_base, "processed", "metrics-data")
carpeta_salida = os.path.join(ruta_base, "processed", "metrics-advanced")

# Términos de filtrado político
terminos_politicos = [
    "PP", "PSOE", "BNG", 
    "Manuel Pazos", 
    "Ramallo", "María Ramallo", 
    "Lucía Santos"
]

def contiene_terminos_politicos(texto):
    """
    Verifica si el texto contiene alguno de los términos políticos
    """
    if pd.isna(texto):
        return False
    
    texto_lower = str(texto).lower()
    
    for termino in terminos_politicos:
        # Búsqueda case-insensitive
        if termino.lower() in texto_lower:
            return True
    return False

def filtrar_articulos_politicos(df):
    """
    Filtra el DataFrame manteniendo solo artículos que mencionen términos políticos
    """
    # Crear máscara de filtro: buscar en título Y summary
    mascara_titulo = df['title'].apply(contiene_terminos_politicos)
    mascara_summary = df['summary'].apply(contiene_terminos_politicos)
    
    # Mantener artículos que mencionen términos en título O summary
    mascara_final = mascara_titulo | mascara_summary
    
    return df[mascara_final].copy()

# Crear carpeta de salida
os.makedirs(carpeta_salida, exist_ok=True)

# ============================================================================
# PROCESAR LOS 3 ARCHIVOS
# ============================================================================

archivos_config = [
    {"entrada": "visualizaciones_por_mes.csv", "salida": "politicos_por_mes.csv"},
    {"entrada": "visualizaciones_por_año.csv", "salida": "politicos_por_año.csv"},
    {"entrada": "visualizaciones_totales.csv", "salida": "politicos_totales.csv"}
]

resultados = {}

for config in archivos_config:
    archivo_entrada = config["entrada"]
    archivo_salida = config["salida"]
    
    # Leer archivo original
    ruta_entrada = os.path.join(carpeta_entrada, archivo_entrada)
    
    if not os.path.exists(ruta_entrada):
        print(f"⚠️  Archivo no encontrado: {ruta_entrada}")
        continue
    
    print(f"📂 Procesando: {archivo_entrada} → {archivo_salida}")
    
    # Cargar datos
    df = pd.read_csv(ruta_entrada)
    total_original = len(df)
    
    # Aplicar filtro político
    df_filtrado = filtrar_articulos_politicos(df)
    total_filtrado = len(df_filtrado)
    
    # Guardar archivo filtrado con nuevo nombre
    ruta_salida = os.path.join(carpeta_salida, archivo_salida)
    df_filtrado.to_csv(ruta_salida, index=False)
    
    # Almacenar resultados
    resultados[archivo_salida] = {
        'original': total_original,
        'filtrado': total_filtrado,
        'porcentaje': (total_filtrado / total_original * 100) if total_original > 0 else 0
    }
    
    print(f"   ✅ {total_original} → {total_filtrado} artículos ({resultados[archivo_salida]['porcentaje']:.1f}%)")

# ============================================================================
# RESUMEN Y ESTADÍSTICAS
# ============================================================================
print(f"\n🎯 FILTRO POLÍTICO APLICADO")
print(f"📁 Archivos guardados en: {carpeta_salida}")
print(f"🔍 Términos buscados: {', '.join(terminos_politicos)}")

print(f"\n📊 RESUMEN POR ARCHIVO:")
for archivo, stats in resultados.items():
    print(f"   📄 {archivo}")
    print(f"      Original: {stats['original']:,} artículos")
    print(f"      Filtrado: {stats['filtrado']:,} artículos ({stats['porcentaje']:.1f}%)")

# Mostrar muestra de artículos filtrados
if resultados:
    print(f"\n🔥 MUESTRA DE ARTÍCULOS POLÍTICOS ENCONTRADOS:")
    
    # Leer el archivo de totales para mostrar los más vistos
    archivo_totales = os.path.join(carpeta_salida, "politicos_totales.csv")
    if os.path.exists(archivo_totales):
        df_muestra = pd.read_csv(archivo_totales)
        
        for i, (index, row) in enumerate(df_muestra.head(5).iterrows()):
            print(f"   {i+1}. {row['n_visualizations']:,} visualizaciones")
            print(f"      📰 {row['title']}")
            print(f"      📅 {row['date']} | 🏛️ {row['source']}")
            
            # Mostrar qué términos encontró
            terminos_encontrados = []
            titulo_lower = str(row['title']).lower()
            summary_lower = str(row['summary']).lower()
            
            for termino in terminos_politicos:
                if termino.lower() in titulo_lower or termino.lower() in summary_lower:
                    terminos_encontrados.append(termino)
            
            print(f"      🎯 Términos: {', '.join(terminos_encontrados)}")
            print()

print(f"✅ Filtrado político completado exitosamente!")