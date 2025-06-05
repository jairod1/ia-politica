import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re
from dateutil.parser import parse as date_parse
import time
import os

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}
DATE_THRESHOLD = datetime(2025, 5, 29)

def extract_date_from_text(text):
    """Extrae fecha del formato Carriola.[Sección].DD.MM.YY"""
    try:
        # Patrón más flexible que captura cualquier variante:
        # - Carriola.Redacción.DD.MM.YY
        # - Carriola.Desmarque (Text. y Fot.).DD.MM.YY 
        # - Carriola.Necrológica.DD.MM.YY
        # - Solo DD.MM.YY al final
        date_pattern = r'(?:Carriola\..*?\.?\s*)?(\d{2})\.(\d{2})\.(\d{2})(?:\s|$)'
        match = re.search(date_pattern, text)
        if match:
            day, month, year = match.groups()
            # Convertir año de 2 dígitos a 4 dígitos
            # Años 00-30 son 2000-2030, años 31-99 son 1931-1999
            year_int = int(year)
            if year_int <= 30:
                full_year = f"20{year}"
            else:
                full_year = f"19{year}"
            
            date_str = f"{day}/{month}/{full_year}"
            parsed_date = datetime.strptime(date_str, "%d/%m/%Y")
            print(f"📅 Fecha parseada: {day}.{month}.{year} -> {parsed_date.isoformat()}")
            return parsed_date
    except Exception as e:
        print(f"⚠️ Error al parsear fecha '{text}': {e}")
    return None

def scrape_carriola_article(url):
    """Extrae información de un artículo específico de Carriola"""
    try:
        print(f"🔍 Procesando: {url}")
        response = requests.get(url, headers=HEADERS, timeout=15)
        
        if response.status_code == 404:
            print(f"❌ Error 404 - Artículo no encontrado: {url}")
            return None
        elif response.status_code != 200:
            print(f"❌ Error HTTP {response.status_code}: {url}")
            return None
            
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Extraer título
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else "Sin título"
        
        # Extraer fecha - buscar específicamente párrafos con patrón de fecha
        date = None
        # Buscar párrafos que contengan el patrón de fecha DD.MM.YY
        for p_element in soup.find_all('p'):
            p_text = p_element.get_text(strip=True)
            # Buscar patrón de fecha DD.MM.YY (más específico)
            if re.search(r'\d{2}\.\d{2}\.\d{2}', p_text):
                print(f"🔍 Texto de fecha encontrado: {p_text}")
                date = extract_date_from_text(p_text)
                if date:
                    print(f"✅ Fecha extraída: {date.isoformat()}")
                    break
        
        if not date:
            print(f"⚠️ No se pudo extraer fecha de: {url}")
            return None
            
        # Verificar si el artículo es anterior al threshold
        if date < DATE_THRESHOLD:
            print(f"🚫 Artículo anterior al threshold ({date.isoformat()}): {url}")
            return "OLD_ARTICLE"
            
        # Extraer número de visualizaciones
        visualizations = 0
        try:
            # Buscar meta con UserPageVisits
            meta_tag = soup.find("meta", {"itemprop": "interactionCount"})
            if meta_tag and "content" in meta_tag.attrs:
                content = meta_tag["content"]
                # Extraer número del formato "UserPageVisits:42"
                viz_match = re.search(r'UserPageVisits:(\d+)', content)
                if viz_match:
                    visualizations = int(viz_match.group(1))
        except Exception as e:
            print(f"⚠️ Error al extraer visualizaciones: {e}")
            
        # Extraer resumen (texto en negrita)
        summary = ""
        try:
            # Buscar párrafos con strong tags que sean el resumen
            for p_element in soup.find_all('p'):
                p_text = p_element.get_text(strip=True)
                # Saltear párrafos que son metadatos
                if any(skip in p_text for skip in ["Carriola.Redacción", "julio@carriola.es", "Visto:", "Ver:"]):
                    continue
                
                # Buscar párrafos con strong/b que sean contenido real (más de 50 caracteres)
                strong_tags = p_element.find_all(['strong', 'b'])
                if strong_tags and len(p_text) > 50:
                    summary = p_text
                    print(f"📝 Resumen encontrado: {summary[:100]}...")
                    break
            
            # Si no encontró resumen, buscar después del email
            if not summary:
                # Buscar párrafos que vengan después de julio@carriola.es
                email_found = False
                for p_element in soup.find_all('p'):
                    p_text = p_element.get_text(strip=True)
                    if "julio@carriola.es" in p_text:
                        email_found = True
                        continue
                    
                    if email_found and len(p_text) > 50:
                        strong_tags = p_element.find_all(['strong', 'b'])
                        if strong_tags:
                            summary = p_text
                            print(f"📝 Resumen encontrado después del email: {summary[:100]}...")
                            break
                
        except Exception as e:
            print(f"⚠️ Error al extraer resumen: {e}")
            
        print(f"✅ [Carriola] {title[:50]}... | {date.isoformat()} | {visualizations} vistas -> VÁLIDO")
        
        return {
            "source": "Carriola de Marín",
            "title": title,
            "link": url,
            "date": date.isoformat(),
            "n_visualizations": visualizations,
            "summary": summary
        }
        
    except Exception as e:
        print(f"❌ Error general procesando {url}: {str(e)[:100]}")
        return None

def scrape_carriola_all():
    """Scraper principal para Carriola.es"""
    base_url = "https://www.carriola.es/index.php/noticias-de-marin-by-julio-santos/"
    data = []
    
    # Empezar desde la página más reciente (9177) y retroceder
    current_page = 9177
    consecutive_errors = 0  # Contador para errores/artículos sin fecha consecutivos
    consecutive_old_articles = 0
    
    while consecutive_errors < 10 and consecutive_old_articles < 3:  # Parar si hay muchos errores o artículos antiguos
        url = f"{base_url}{current_page}"
        
        result = scrape_carriola_article(url)
        
        if result == "OLD_ARTICLE":
            consecutive_old_articles += 1
            consecutive_errors = 0  # Resetear errores si encontramos artículo antiguo
            print(f"📊 Artículos antiguos consecutivos: {consecutive_old_articles}")
        elif result is None:
            # Error 404, sin fecha, u otro error
            consecutive_errors += 1
            print(f"⚠️ Errores consecutivos: {consecutive_errors}")
        else:
            # Artículo válido encontrado, resetear contadores
            consecutive_old_articles = 0
            consecutive_errors = 0
            data.append(result)
            
        current_page -= 1
        
        # Pausa para no sobrecargar el servidor
        time.sleep(1)
        
        # Verificar que no estemos en números negativos
        if current_page < 1:
            print("🏁 Llegamos al artículo #1, finalizando.")
            break
    
    if consecutive_errors >= 10:
        print(f"🏁 Demasiados errores consecutivos ({consecutive_errors}), finalizando.")
    
    if consecutive_old_articles >= 5:
        print(f"🏁 Encontrados {consecutive_old_articles} artículos antiguos consecutivos, finalizando.")
    
    print(f"\n✅ Carriola de Marín: {len(data)} artículos válidos procesados")
    if data:
        print(f"📅 Rango de fechas: {data[0]['date']} a {data[-1]['date']}")
    
    return data

# Ejecutar
if __name__ == "__main__":
    print("🚀 Iniciando scraping de Carriola de Marín...")
    data = scrape_carriola_all()
    
    # Crear directorio de salida
    output_dir = os.path.join("..", "..", "data", "raw", "dirty-csvs")
    os.makedirs(output_dir, exist_ok=True)
    
    # Ruta completa del archivo CSV
    csv_path = os.path.join(output_dir, "carriola-sucio.csv")
    
    # Guardar CSV
    df = pd.DataFrame(data)
    df.to_csv(csv_path, index=False)
    
    # Mostrar resumen
    print(f"\n📦 CSV generado en '{csv_path}' con {len(df)} artículos.")
    if len(df) > 0:
        print("\n🔍 Muestra de datos:")
        print(df[["source", "title", "date", "n_visualizations"]].head())
        print(f"\n📊 Estadísticas:")
        print(f"Total visualizaciones: {df['n_visualizations'].sum()}")
        print(f"Promedio visualizaciones: {df['n_visualizations'].mean():.1f}")
        print(f"Artículo más visto: {df['n_visualizations'].max()} vistas")