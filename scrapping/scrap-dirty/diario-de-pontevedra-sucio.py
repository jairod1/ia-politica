import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
from datetime import datetime
import os

# Constantes
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def get_comments(article_url):
    """Extrae comentarios directamente del HTML de la página, sin API."""
    try:
        print(f"📄 Cargando artículo: {article_url}")
        response = requests.get(article_url, headers=HEADERS, timeout=20)
        if response.status_code != 200:
            print(f"❌ Error {response.status_code} al cargar la página")
            return []

        soup = BeautifulSoup(response.text, "html.parser")

        # Localizar contenedor de comentarios
        comment_blocks = soup.select(".onm-comment-item")  # clase usada en la web real

        if not comment_blocks:
            print("⚠️ No se encontraron bloques de comentario en el HTML.")
            return []

        comments = []
        for block in comment_blocks:
            user = block.select_one(".onm-comment-user")
            date = block.select_one(".onm-comment-date")
            text = block.select_one(".onm-comment-text")

            comment_text = (
                f"{user.get_text(strip=True)} ({date.get_text(strip=True)}): {text.get_text(strip=True)}"
                if user and date and text else text.get_text(strip=True)
            )
            comments.append(comment_text)

        return comments

    except Exception as e:
        print(f"💥 Error general extrayendo comentarios: {e}")
        return []

def scrape_article(article_url):
    """Simplemente obtiene los comentarios de un artículo específico"""
    comments = get_comments(article_url)
    print(f"\nComentarios encontrados: {len(comments)}")
    
    for i, comment in enumerate(comments):
        print(f"Comentario {i+1}: {comment[:100]}...")
    
    return {
        "url": article_url,
        "n_comments": len(comments),
        "comments": comments
    }

def scrape_morrazo_section(max_pages=3):
    """Versión simplificada del scraper que solo busca artículos y sus comentarios"""
    base_url = "https://www.diariodepontevedra.es/blog/section/o-morrazo/"
    all_articles_data = []
    seen_links = set()
    
    try:
        for page in range(1, max_pages + 1):
            current_url = f"{base_url}?page={page}" if page > 1 else base_url
            print(f"\nCargando página {page}: {current_url}")
            
            response = requests.get(current_url, headers=HEADERS, timeout=15)
            if response.status_code != 200:
                print(f"Error HTTP {response.status_code} al cargar la página.")
                break
                
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Buscar artículos
            articles = soup.select("article") or soup.select(".news-item")
            
            if not articles:
                print(f"No se encontraron artículos en la página {page}.")
                break
                
            print(f"Artículos encontrados: {len(articles)}")
            
            for article in articles:
                try:
                    # Extraer título y enlace
                    title_tag = article.select_one("h2") or article.select_one("h3") or article.select_one(".title")
                    if not title_tag:
                        continue
                        
                    title = title_tag.get_text(strip=True)
                    
                    link_tag = title_tag.find("a") or article.find("a", href=True)
                    if not link_tag or not link_tag.get("href"):
                        continue
                        
                    link = link_tag["href"]
                    
                    # Asegurar que el enlace sea absoluto
                    if not link.startswith(("http://", "https://")):
                        link = "https://www.diariodepontevedra.es" + (link if link.startswith("/") else "/" + link)
                    
                    # Verificar duplicados
                    if link in seen_links:
                        continue
                        
                    seen_links.add(link)
                    print(f"\nProcesando artículo: {title} | {link}")
                    
                    # Obtener comentarios
                    article_data = scrape_article(link)
                    article_data["title"] = title
                    all_articles_data.append(article_data)
                    
                    # Pausa corta entre artículos
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"Error procesando artículo: {e}")
                    continue
            
            # Pausa entre páginas
            time.sleep(2)
    
    except Exception as e:
        print(f"Error en el scraping: {e}")
    
    finally:
        print(f"\nTotal: {len(all_articles_data)} artículos procesados")
    
    return all_articles_data

# Función principal
if __name__ == "__main__":
    print("=== SCRAPER SIMPLIFICADO DEL DIARIO DE PONTEVEDRA - O MORRAZO ===")
    
    # Opción 1: Probar con un artículo específico
    test_url = "https://www.diariodepontevedra.es/articulo/o-morrazo/ceip-ardan-acolle-domingo-dia-das-familias-recadar-fondos/202505172038561391259.html"
    print(f"\nProbando artículo específico: {test_url}")
    test_result = scrape_article(test_url)
    
    if test_result["n_comments"] > 0:
        print(f"\n✅ Prueba exitosa! Se encontraron {test_result['n_comments']} comentarios.")
    else:
        print("\n❌ No se encontraron comentarios en el artículo de prueba.")
    
    # Opción 2: Hacer scraping de la sección completa
    print("\n¿Desea hacer scraping de la sección completa de O Morrazo? (s/n)")
    choice = input().lower().strip()
    
    if choice == 's':
        print("\nIniciando scraping de la sección completa...")
        articles_data = scrape_morrazo_section(max_pages=3)
        
        # Guardar resultados
        if articles_data:
            # Preparar datos para el DataFrame
            df_data = []
            for article in articles_data:
                df_data.append({
                    "title": article["title"],
                    "url": article["url"],
                    "n_comments": article["n_comments"],
                    "comments_raw": "\n---\n".join(article["comments"]) if article["comments"] else ""
                })
            
            # Ruta a nivel superior (subir un nivel desde ialimpia)
            output_dir = os.path.join("..", "data", "csvs-sucios")
            os.makedirs(output_dir, exist_ok=True)  # Crea la estructura si no existe

            # Ruta completa del archivo CSV
            csv_path = os.path.join(output_dir, "diario_pontevedra_sucio.csv")
            
            df = pd.DataFrame(df_data)
            output_file = "diariodepontevedra_comentarios.csv"
            df.to_csv(csv_path, index=False)
            print(f"\n📦 CSV generado en '{csv_path}' con {len(df)} artículos.")
            print(df[["source", "title", "date", "n_comments"]])         

            # Mostrar estadísticas
            total_comments = df['n_comments'].sum()
            articles_with_comments = len(df[df['n_comments'] > 0])
            print(f"Total comentarios encontrados: {total_comments}")
            print(f"Artículos con comentarios: {articles_with_comments}")
        else:
            print("\nNo se recopilaron datos.")
    
    print("\n=== PROCESO DE SCRAPING FINALIZADO ===")