import pandas as pd
import os

def cargar_metricas():
    """
    Carga todos los archivos de métricas y devuelve los top 10 de cada categoría
    """
    # Definir rutas base (desde el directorio raíz del proyecto)
    ruta_base = os.path.abspath("data")
    carpeta_metricas = os.path.join(ruta_base, "processed", "metrics-data")
    carpeta_politicos = os.path.join(ruta_base, "processed", "metrics-advanced")
    
    try:
        # Rutas de archivos de visualizaciones generales
        vis_mes = pd.read_csv(os.path.join(carpeta_metricas, "visualizaciones_por_mes.csv"))
        vis_anio = pd.read_csv(os.path.join(carpeta_metricas, "visualizaciones_por_año.csv"))
        vis_total = pd.read_csv(os.path.join(carpeta_metricas, "visualizaciones_totales.csv"))
        
        # Rutas de archivos políticos
        pol_mes = pd.read_csv(os.path.join(carpeta_politicos, "politicos_por_mes.csv"))
        pol_anio = pd.read_csv(os.path.join(carpeta_politicos, "politicos_por_año.csv"))
        pol_total = pd.read_csv(os.path.join(carpeta_politicos, "politicos_totales.csv"))
        
        return {
            "top10_vis": {
                "mes": vis_mes.nlargest(10, "n_visualizations"),
                "anio": vis_anio.nlargest(10, "n_visualizations"),
                "total": vis_total.nlargest(10, "n_visualizations"),
            },
            "top10_pol": {
                "mes": pol_mes.nlargest(10, "n_visualizations"),
                "anio": pol_anio.nlargest(10, "n_visualizations"),
                "total": pol_total.nlargest(10, "n_visualizations"),
            }
        }
    
    except FileNotFoundError as e:
        raise FileNotFoundError(f"No se encontró el archivo: {e.filename}")
    except Exception as e:
        raise Exception(f"Error cargando métricas: {str(e)}")