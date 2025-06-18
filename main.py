#!/usr/bin/env python3
"""
MAIN PIPELINE - HorizontAI
===========================

Pipeline completo que ejecuta todos los scrapers y procesamiento de datos
para generar los CSVs finales utilizados por la aplicación Streamlit.

PIPELINE:
1. SCRAPERS → Datos raw individuales
2. COMBINACIÓN → Datos unificados  
3. FILTRADO → Datos procesados para Streamlit
4. MÉTRICAS → Datos de visualizaciones procesados
"""

import os
import sys
import time
import subprocess
import logging
from datetime import datetime
from pathlib import Path

# ========================
# CONFIGURACIÓN PRINCIPAL
# ========================

# Configurar logging detallado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline_execution.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Paths del proyecto
PROJECT_ROOT = Path(__file__).parent
SCRAPING_DIR = PROJECT_ROOT / "src" / "scrapping" / "scrap-clean"
SRC_DIR = PROJECT_ROOT / "src"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Configuración de scrapers
SCRAPERS_CONFIG = [
    {
        "name": "Carriola de Marín",
        "script": "carriola-marin.py",
        "output_dir": "clean-metrics",
        "output_file": "carriola-marin.csv",
        "delay_after": 30  # Segundos de pausa después del scraper
    },
    {
        "name": "Cousas de Carragal", 
        "script": "cousas-carragal.py",
        "output_dir": "clean-csvs",
        "output_file": "cousas-carragal-limpio.csv",
        "delay_after": 30
    },
    {
        "name": "Diario Marín",
        "script": "diario-marin.py", 
        "output_dir": "clean-csvs",
        "output_file": "diario-marin-limpio.csv",
        "delay_after": 30
    },
    {
        "name": "Diario Pontevedra",
        "script": "diario-pontevedra.py",
        "output_dir": "clean-csvs", 
        "output_file": "diario-pontevedra-limpio.csv",
        "delay_after": 60  # Más tiempo por el anti-detección
    },
    {
        "name": "PSOE Marín",
        "script": "psdeg-marin.py",
        "output_dir": "clean-csvs",
        "output_file": "psdeg-marin-limpio.csv", 
        "delay_after": 30
    },
    {
        "name": "Voz de Galicia",
        "script": "voz-galicia.py",
        "output_dir": "clean-csvs",
        "output_file": "voz_galicia-limpio.csv",
        "delay_after": 45  # Selenium requiere más tiempo
    }
]

# Configuración de procesadores
PROCESSORS_CONFIG = [
    {
        "name": "Combinador de Datos",
        "script": "data-combiner.py",
        "directory": "comments",
        "description": "Combina todos los CSVs individuales en combined_data.csv"
    },
    {
        "name": "Filtro Avanzado",
        "script": "filter-advanced.py", 
        "directory": "comments",
        "description": "Genera filtered_data.csv y filtros específicos"
    },
    {
        "name": "Procesador Métricas Avanzadas",
        "script": "filter-advanced-m.py",
        "directory": "metrics", 
        "description": "Procesa métricas políticas (politicos_totales.csv)"
    },
    {
        "name": "Procesador Métricas Básicas", 
        "script": "filter-basic-m.py",
        "directory": "metrics",
        "description": "Procesa métricas de visualizaciones (visualizaciones_totales.csv)"
    }
]

# ========================
# FUNCIONES AUXILIARES
# ========================

def print_banner():
    """Banner de inicio"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                     🚀 HORIZONTAI PIPELINE 🚀               ║
    ║                                                              ║
    ║  Pipeline completo de scraping y procesamiento de datos      ║
    ║  para análisis político de medios locales                    ║
    ║                                                              ║
    ║   6 Scrapers → Combinación → Filtrado → CSVs finales         ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)
    logger.info("Iniciando pipeline completo HorizontAI")

def create_directories():
    """Crea directorios necesarios si no existen"""
    directories = [
        DATA_RAW_DIR / "clean-csvs",
        DATA_RAW_DIR / "clean-metrics", 
        DATA_PROCESSED_DIR / "combined-data",
        DATA_PROCESSED_DIR / "filtered-data",
        DATA_PROCESSED_DIR / "metrics-data",
        DATA_PROCESSED_DIR / "metrics-advanced"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ Directorio verificado: {directory}")

def check_file_exists(file_path, description="archivo"):
    """Verifica si un archivo existe y reporta su tamaño"""
    if file_path.exists():
        size_mb = file_path.stat().st_size / (1024 * 1024)
        logger.info(f"✅ {description} generado: {file_path.name} ({size_mb:.2f} MB)")
        return True
    else:
        logger.error(f"❌ {description} NO encontrado: {file_path}")
        return False

def run_script(script_path, description, working_dir=None):
    """Ejecuta un script Python y maneja errores"""
    logger.info(f"🔄 Ejecutando: {description}")
    logger.info(f"   Script: {script_path}")
    
    if working_dir:
        logger.info(f"   Directorio: {working_dir}")
    
    try:
        # Cambiar al directorio de trabajo si se especifica
        original_cwd = os.getcwd()
        if working_dir:
            os.chdir(working_dir)
        
        # Ejecutar script
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=3600  # 1 hora máximo por script
        )
        
        # Restaurar directorio original
        os.chdir(original_cwd)
        
        if result.returncode == 0:
            logger.info(f"✅ {description} completado exitosamente")
            if result.stdout:
                logger.info(f"   Output: {result.stdout[-200:]}")  # Últimas 200 chars
            return True
        else:
            logger.error(f"❌ {description} falló (código: {result.returncode})")
            if result.stderr:
                logger.error(f"   Error: {result.stderr}")
            if result.stdout:
                logger.error(f"   Output: {result.stdout}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"⏰ {description} excedió tiempo límite (1 hora)")
        return False
    except Exception as e:
        logger.error(f"💥 Error ejecutando {description}: {e}")
        return False
    finally:
        # Asegurar que volvemos al directorio original
        os.chdir(original_cwd)

def countdown_delay(seconds, message):
    """Cuenta regresiva visual"""
    logger.info(f"⏳ {message}")
    for i in range(seconds, 0, -1):
        print(f"   ⏱️  Esperando {i} segundos...", end='\r', flush=True)
        time.sleep(1)
    print("   ✅ Pausa completada" + " " * 20)  # Limpiar línea

# ========================
# FUNCIONES PRINCIPALES  
# ========================

def step_1_run_scrapers():
    """PASO 1: Ejecutar todos los scrapers"""
    logger.info("=" * 60)
    logger.info("📡 PASO 1: EJECUTANDO SCRAPERS")
    logger.info("=" * 60)
    
    successful_scrapers = 0
    failed_scrapers = 0
    
    for i, scraper in enumerate(SCRAPERS_CONFIG, 1):
        logger.info(f"\n🎯 SCRAPER {i}/{len(SCRAPERS_CONFIG)}: {scraper['name']}")
        logger.info("-" * 50)
        
        # Path del script
        script_path = SCRAPING_DIR / scraper['script']
        
        # Verificar que el script existe
        if not script_path.exists():
            logger.error(f"❌ Script no encontrado: {script_path}")
            failed_scrapers += 1
            continue
        
        # Ejecutar scraper
        success = run_script(
            script_path, 
            f"Scraper {scraper['name']}", 
            working_dir=SCRAPING_DIR
        )
        
        if success:
            # Verificar que se generó el archivo
            output_path = DATA_RAW_DIR / scraper['output_dir'] / scraper['output_file']
            if check_file_exists(output_path, f"CSV de {scraper['name']}"):
                successful_scrapers += 1
            else:
                logger.warning(f"⚠️ {scraper['name']} ejecutó pero no generó archivo esperado")
                failed_scrapers += 1
        else:
            failed_scrapers += 1
        
        # Pausa entre scrapers (excepto el último)
        if i < len(SCRAPERS_CONFIG):
            countdown_delay(
                scraper['delay_after'], 
                f"Pausa anti-sobrecarga entre scrapers ({scraper['delay_after']}s)"
            )
    
    # Resumen del paso
    logger.info("\n" + "=" * 60)
    logger.info(f"📊 RESUMEN PASO 1 - SCRAPERS:")
    logger.info(f"   ✅ Exitosos: {successful_scrapers}")
    logger.info(f"   ❌ Fallidos: {failed_scrapers}")
    logger.info(f"   📈 Tasa éxito: {(successful_scrapers/len(SCRAPERS_CONFIG)*100):.1f}%")
    logger.info("=" * 60)
    
    return successful_scrapers > 0  # Al menos uno debe funcionar

def step_2_combine_data():
    """PASO 2: Combinar datos de todos los scrapers"""
    logger.info("\n" + "=" * 60)
    logger.info("🔗 PASO 2: COMBINANDO DATOS")
    logger.info("=" * 60)
    
    processor = PROCESSORS_CONFIG[0]  # data-combiner.py
    script_path = SRC_DIR / processor['directory'] / processor['script']
    
    logger.info(f"📝 {processor['description']}")
    
    success = run_script(
        script_path,
        processor['name'],
        working_dir=SRC_DIR / processor['directory']
    )
    
    if success:
        # Verificar que se generó combined_data.csv
        combined_path = DATA_PROCESSED_DIR / "combined-data" / "combined_data.csv"
        if check_file_exists(combined_path, "Datos combinados"):
            logger.info("✅ PASO 2 completado exitosamente")
            return True
    
    logger.error("❌ PASO 2 falló")
    return False

def step_3_filter_data():
    """PASO 3: Filtrar y procesar datos de comentarios"""
    logger.info("\n" + "=" * 60)
    logger.info("🔍 PASO 3: FILTRANDO DATOS DE COMENTARIOS")
    logger.info("=" * 60)
    
    processor = PROCESSORS_CONFIG[1]  # filter-advanced.py
    script_path = SRC_DIR / processor['directory'] / processor['script']
    
    logger.info(f"📝 {processor['description']}")
    
    success = run_script(
        script_path,
        processor['name'], 
        working_dir=SRC_DIR / processor['directory']
    )
    
    if success:
        # Verificar archivos generados
        files_to_check = [
            (DATA_PROCESSED_DIR / "filtered-data" / "filtered_data.csv", "Datos filtrados generales"),
            (DATA_PROCESSED_DIR / "filtered-data" / "filtro1_localizacion.csv", "Filtro localización"),
            (DATA_PROCESSED_DIR / "filtered-data" / "filtro6_marin.csv", "Filtro Marín")
        ]
        
        all_files_ok = True
        for file_path, description in files_to_check:
            if not check_file_exists(file_path, description):
                all_files_ok = False
        
        if all_files_ok:
            logger.info("✅ PASO 3 completado exitosamente")
            return True
    
    logger.error("❌ PASO 3 falló")
    return False

def step_4_process_metrics():
    """PASO 4: Procesar métricas de visualizaciones"""
    logger.info("\n" + "=" * 60)
    logger.info("📊 PASO 4: PROCESANDO MÉTRICAS")
    logger.info("=" * 60)
    
    # Procesar métricas avanzadas (políticas)
    logger.info("🏛️ Procesando métricas políticas...")
    metrics_advanced = PROCESSORS_CONFIG[2]  # filter-advanced-m.py
    script_path_advanced = SRC_DIR / metrics_advanced['directory'] / metrics_advanced['script']
    
    success_advanced = run_script(
        script_path_advanced,
        metrics_advanced['name'],
        working_dir=SRC_DIR / metrics_advanced['directory']
    )
    
    # Procesar métricas básicas (visualizaciones)
    logger.info("📈 Procesando métricas de visualizaciones...")
    metrics_basic = PROCESSORS_CONFIG[3]  # filter-basic-m.py  
    script_path_basic = SRC_DIR / metrics_basic['directory'] / metrics_basic['script']
    
    success_basic = run_script(
        script_path_basic,
        metrics_basic['name'],
        working_dir=SRC_DIR / metrics_basic['directory']
    )
    
    # Verificar archivos generados
    if success_advanced and success_basic:
        files_to_check = [
            (DATA_PROCESSED_DIR / "metrics-advanced" / "politicos_totales.csv", "Métricas políticas"),
            (DATA_PROCESSED_DIR / "metrics-data" / "visualizaciones_totales.csv", "Métricas visualizaciones")
        ]
        
        all_files_ok = True
        for file_path, description in files_to_check:
            if not check_file_exists(file_path, description):
                all_files_ok = False
        
        if all_files_ok:
            logger.info("✅ PASO 4 completado exitosamente") 
            return True
    
    logger.error("❌ PASO 4 falló")
    return False

def step_5_final_verification():
    """PASO 5: Verificación final de todos los CSVs necesarios"""
    logger.info("\n" + "=" * 60)
    logger.info("🔍 PASO 5: VERIFICACIÓN FINAL")
    logger.info("=" * 60)
    
    # CSVs críticos que debe usar la aplicación Streamlit
    critical_files = [
        # Métricas
        (DATA_PROCESSED_DIR / "metrics-data" / "visualizaciones_totales.csv", "Métricas de visualizaciones"),
        (DATA_PROCESSED_DIR / "metrics-advanced" / "politicos_totales.csv", "Métricas políticas"),
        
        # Comentarios
        (DATA_PROCESSED_DIR / "filtered-data" / "filtered_data.csv", "Datos filtrados principales"),
        (DATA_PROCESSED_DIR / "filtered-data" / "filtro1_localizacion.csv", "Filtro localización (O Morrazo/Pontevedra)"),
        (DATA_PROCESSED_DIR / "filtered-data" / "filtro6_marin.csv", "Filtro Marín específico")
    ]
    
    logger.info("📋 Verificando CSVs críticos para Streamlit:")
    
    all_critical_ok = True
    for file_path, description in critical_files:
        if check_file_exists(file_path, description):
            # Verificar que el archivo no esté vacío
            try:
                import pandas as pd
                df = pd.read_csv(file_path)
                logger.info(f"   📊 {file_path.name}: {len(df)} filas")
            except Exception as e:
                logger.warning(f"   ⚠️ Error leyendo {file_path.name}: {e}")
        else:
            all_critical_ok = False
    
    # Verificación de CSVs raw (para referencia del usuario)
    logger.info("\n📋 Verificando CSVs raw generados por scrapers:")
    raw_files = [
        (DATA_RAW_DIR / "clean-metrics" / "carriola-marin.csv", "Carriola Marín"),
        (DATA_RAW_DIR / "clean-csvs" / "cousas-carragal-limpio.csv", "Cousas de Carragal"),
        (DATA_RAW_DIR / "clean-csvs" / "diario-marin-limpio.csv", "Diario Marín"),
        (DATA_RAW_DIR / "clean-csvs" / "diario-pontevedra-limpio.csv", "Diario Pontevedra"),
        (DATA_RAW_DIR / "clean-csvs" / "psdeg-marin-limpio.csv", "PSOE Marín"),
        (DATA_RAW_DIR / "clean-csvs" / "voz_galicia-limpio.csv", "Voz de Galicia")
    ]
    
    raw_count = 0
    for file_path, description in raw_files:
        if check_file_exists(file_path, f"Raw {description}"):
            raw_count += 1
    
    logger.info(f"\n📊 RESUMEN VERIFICACIÓN FINAL:")
    logger.info(f"   🎯 CSVs críticos: {'✅ TODOS OK' if all_critical_ok else '❌ ALGUNOS FALLAN'}")
    logger.info(f"   📁 CSVs raw: {raw_count}/{len(raw_files)} generados")
    
    return all_critical_ok

def print_summary():
    """Resumen final del pipeline"""
    end_time = datetime.now()
    
    summary = f"""
    ╔══════════════════════════════════════════════════════════════╗
    ║                    🎉 PIPELINE COMPLETADO 🎉                ║
    ║                                                              ║
    ║  ✅ Scrapers ejecutados                                     ║
    ║  ✅ Datos combinados                                        ║
    ║  ✅ Filtros aplicados                                       ║
    ║  ✅ Métricas procesadas                                     ║
    ║  ✅ Verificación final                                      ║
    ║                                                              ║
    ║  🚀 La aplicación Streamlit está lista para usar            ║
    ║                                                              ║
    ║  Hora finalización: {end_time.strftime('%H:%M:%S')}          ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(summary)
    logger.info("Pipeline HorizontAI completado exitosamente")

# ========================
# FUNCIÓN PRINCIPAL
# ========================

def main():
    """Función principal del pipeline"""
    start_time = datetime.now()
    
    try:
        # Banner inicial
        print_banner()
        
        # Crear directorios necesarios
        logger.info("🏗️ Preparando estructura de directorios...")
        create_directories()
        
        # PASO 1: Scrapers
        if not step_1_run_scrapers():
            logger.error("💥 FALLO CRÍTICO: Ningún scraper funcionó")
            return False
        
        # PASO 2: Combinación 
        if not step_2_combine_data():
            logger.error("💥 FALLO CRÍTICO: No se pudieron combinar datos")
            return False
        
        # PASO 3: Filtrado
        if not step_3_filter_data():
            logger.error("💥 FALLO CRÍTICO: No se pudieron filtrar datos")
            return False
        
        # PASO 4: Métricas
        if not step_4_process_metrics():
            logger.error("💥 FALLO CRÍTICO: No se pudieron procesar métricas")
            return False
        
        # PASO 5: Verificación final
        if not step_5_final_verification():
            logger.error("💥 FALLO CRÍTICO: Verificación final falló")
            return False
        
        # Resumen exitoso
        print_summary()
        
        # Tiempo total
        total_time = datetime.now() - start_time
        logger.info(f"⏱️ Tiempo total de ejecución: {total_time}")
        
        return True
        
    except KeyboardInterrupt:
        logger.error("⚠️ Pipeline interrumpido por el usuario")
        return False
    except Exception as e:
        logger.error(f"💥 Error inesperado en pipeline: {e}")
        return False

if __name__ == "__main__":
    # Verificar Python 3.7+
    if sys.version_info < (3, 7):
        print("❌ Se requiere Python 3.7 o superior")
        sys.exit(1)
    
    # Ejecutar pipeline
    success = main()
    
    # Código de salida
    sys.exit(0 if success else 1)