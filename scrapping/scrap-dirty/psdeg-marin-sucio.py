import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import pandas as pd
from datetime import datetime
import re
from dateutil.parser import parse as date_parse
import time

HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
DATE_THRESHOLD = datetime(2025, 4, 1)

def scrape_psdegmarin_wordpress_all():
    base_url = "https://psdegmarin.wordpress.com/"
    page = 1
    data = []
    MAX_PAGES = 1000  # Límite de seguridad
    seen_links = set()  # Para evitar duplicados
    consecutive_old_posts = 0  # Contador de posts antiguos consecutivos
    MAX_OLD_POSTS = 3  # Número máximo de posts antiguos consecutivos permitidos

    while page <= MAX_PAGES:
        # En WordPress la paginación suele tener este formato
        current_url = f"{base_url}page/{page}/" if page > 1 else base_url
        print(f"\n🌀 Cargando página {page}: {current_url}")
        
        try:
            response = requests.get(current_url, headers=HEADERS, timeout=15)
            if response.status_code != 200:
                print(f"❌ Error HTTP {response.status_code} al cargar la página.")
                break
                
            soup = BeautifulSoup(response.text, "html.parser")
        except Exception as e:
            print(f"❌ Error al cargar página: {e}")
            break
            
        # En WordPress los artículos suelen tener la clase "post" o "entry"
        articles = soup.select("article") or soup.select(".post") or soup.select(".entry")
        
        if not articles:
            print(f"⚠️ No se encontraron artículos en la página {page}.")
            break
            
        print(f"📄 Artículos encontrados: {len(articles)}")
        valid_articles_this_page = 0
        new_articles_this_page = 0
        
        for article in articles:
            try:
                # Extraer título y enlace - en WordPress suele estar en h2.entry-title o h1.entry-title
                title_tag = article.select_one("h2.entry-title") or article.select_one("h1.entry-title") or article.select_one(".entry-title")
                
                if not title_tag:
                    # Intentar buscar cualquier encabezado
                    for tag in ["h1", "h2", "h3"]:
                        title_tag = article.find(tag)
                        if title_tag:
                            break
                
                if not title_tag:
                    print("⚠️ No se pudo encontrar el título del artículo. Saltando.")
                    continue
                    
                title = title_tag.get_text(strip=True)
                
                # El enlace suele estar en el título
                link_tag = title_tag.find("a") if title_tag else None
                
                # Si no está en el título, intentar buscar en otros lugares
                if not link_tag or not link_tag.get("href"):
                    link_tag = article.find("a", class_="more-link") or article.find("a", class_="read-more")
                    
                    # Si aún no lo encontramos, buscar cualquier enlace que parezca ser el del post
                    if not link_tag or not link_tag.get("href"):
                        link_tag = article.find("a", href=re.compile(r"\/\d{4}\/\d{2}\/"))
                
                if not link_tag or not link_tag.get("href"):
                    print(f"⚠️ No se pudo encontrar el enlace para '{title}'. Saltando.")
                    continue
                    
                link = link_tag["href"]
                
                # Verificar duplicados
                if link in seen_links:
                    print(f"👀 Artículo duplicado: {title}. Saltando.")
                    continue
                    
                seen_links.add(link)
                new_articles_this_page += 1
                
                print(f"🔍 Procesando artículo: {title}")
                
                # Cargar la página completa del artículo
                try:
                    article_response = requests.get(link, headers=HEADERS, timeout=15)
                    if article_response.status_code != 200:
                        print(f"⚠️ Error al cargar artículo '{title}': HTTP {article_response.status_code}")
                        continue
                        
                    article_soup = BeautifulSoup(article_response.text, "html.parser")
                except Exception as e:
                    print(f"⚠️ Error al cargar artículo '{title}': {str(e)[:100]}")
                    continue
                
                # Extraer fecha - WordPress usa diferentes formatos pero suele tener una clase como entry-date
                date = None
                date_tags = [
                    article_soup.select_one("time.entry-date"),
                    article_soup.select_one(".entry-date"),
                    article_soup.select_one(".posted-on time"),
                    article_soup.select_one(".date"),
                    article_soup.select_one(".post-date")
                ]
                
                # Intentar extraer la fecha de los diferentes selectores
                for date_tag in date_tags:
                    if date_tag:
                        # Intentar extraer de atributo datetime primero
                        if date_tag.get("datetime"):
                            try:
                                date = date_parse(date_tag["datetime"]).replace(tzinfo=None)
                                break
                            except:
                                pass
                                
                        # Si no hay atributo datetime, intentar con el texto
                        date_text = date_tag.get_text(strip=True)
                        try:
                            date = date_parse(date_text).replace(tzinfo=None)
                            break
                        except:
                            continue
                
                # Si aún no tenemos fecha, intentar con meta tags
                if not date:
                    meta_tags = [
                        article_soup.find("meta", {"property": "article:published_time"}),
                        article_soup.find("meta", {"name": "article:published_time"}),
                        article_soup.find("meta", {"property": "og:published_time"})
                    ]
                    
                    for tag in meta_tags:
                        if tag and tag.get("content"):
                            try:
                                date = date_parse(tag["content"]).replace(tzinfo=None)
                                break
                            except:
                                continue
                                
                # Si todavía no tenemos fecha, buscar patrones comunes en el HTML
                if not date:
                    # Buscar en todas las clases que contengan "date" o "time"
                    date_elements = article_soup.find_all(class_=lambda c: c and ('date' in c.lower() or 'time' in c.lower()))
                    for el in date_elements:
                        date_text = el.get_text(strip=True)
                        try:
                            date = date_parse(date_text).replace(tzinfo=None)
                            break
                        except:
                            continue
                            
                    # Si aún no tenemos fecha, buscar en las URLs de WordPress (formato: /YYYY/MM/DD/)
                    if not date and link:
                        date_match = re.search(r'\/(\d{4})\/(\d{2})\/(\d{2})\/', link)
                        if date_match:
                            year, month, day = date_match.groups()
                            try:
                                date = datetime(int(year), int(month), int(day))
                            except:
                                pass
                
                if not date:
                    print(f"⚠️ No se pudo determinar la fecha para '{title}'. Saltando.")
                    continue
                
                # Verificar si el artículo cumple con el umbral de fecha
                if date < DATE_THRESHOLD:
                    print(f"🚫 Artículo con fecha {date.isoformat()} anterior al umbral {DATE_THRESHOLD.isoformat()}.")
                    consecutive_old_posts += 1
                    
                    if consecutive_old_posts >= MAX_OLD_POSTS:
                        print(f"🏁 Se alcanzó el límite de {MAX_OLD_POSTS} artículos antiguos consecutivos. Finalizando.")
                        break
                        
                    continue
                else:
                    # Reiniciar contador si encontramos un artículo reciente
                    consecutive_old_posts = 0
                
                # Procesando artículo válido
                valid_articles_this_page += 1
                print(f"✅ [PSOE Marín WordPress] {title} | {date.isoformat()} -> VÁLIDO")
                
                # Extracción de comentarios - WordPress tiene una estructura bastante estándar
                comment_texts = []
                comments_section = article_soup.select_one("#comments")
                
                if comments_section:
                    # En WordPress los comentarios suelen tener estas clases
                    comments = comments_section.select(".comment-content") or comments_section.select(".comment-body")
                    
                    for comment in comments:
                        # Extraer solo el texto del comentario, no metadatos
                        comment_text = comment.get_text(separator=" ", strip=True)
                        
                        # Filtrar comentarios no válidos
                        if comment_text and len(comment_text) > 10:
                            # Ignorar textos específicos que no son comentarios reales
                            if not any(texto in comment_text for texto in ["Deja un comentario", "Cancelar respuesta", "Responder"]):
                                comment_texts.append(comment_text)
                
                # Añadir artículo a los datos
                data.append({
                    "source": "PSOE Marín WordPress",
                    "title": title,
                    "link": link,
                    "date": date.isoformat(),
                    "n_comments": len(comment_texts),
                    "comments_raw": "\n---\n".join(comment_texts) if comment_texts else ""
                })
                
            except Exception as e:
                print(f"⚠️ Error general procesando artículo: {str(e)[:100]}")
                continue
        
        # Verificar si debemos detener el scraping por límite de artículos antiguos
        if consecutive_old_posts >= MAX_OLD_POSTS:
            print(f"🏁 Se alcanzó el límite de {MAX_OLD_POSTS} artículos antiguos consecutivos (antes de {DATE_THRESHOLD.isoformat()}). Finalizando.")
            break
            
        print(f"📊 Página {page}: {valid_articles_this_page} artículos válidos, {new_articles_this_page} nuevos")
        
        # Si no hay artículos nuevos en esta página, finalizar
        if new_articles_this_page == 0:
            print("🏁 No se encontraron nuevos artículos en esta página. Finalizando.")
            break
            
        # Buscar enlace a la siguiente página - WordPress suele tener navegación estándar
        next_page = None
        pagination = soup.select_one(".pagination") or soup.select_one(".nav-links") or soup.select_one(".page-navigation")
        
        if pagination:
            next_link = pagination.find("a", class_="next") or pagination.find("a", string=re.compile(r"Siguiente|Next|»", re.IGNORECASE))
            if next_link and next_link.get("href"):
                next_page = next_link["href"]
                
        # Si no encontramos navegación estándar, intentar otro enfoque (ver si la página actual está en el máximo)
        if not next_page:
            # Ver si hay enlaces numerados de página y si estamos en el último
            page_links = soup.select("a.page-numbers") or soup.select(".pagination a")
            if page_links:
                page_numbers = []
                for pl in page_links:
                    try:
                        num = int(pl.get_text(strip=True))
                        page_numbers.append(num)
                    except:
                        continue
                
                if page_numbers and page >= max(page_numbers):
                    print("🏁 Llegamos a la última página numerada. Finalizando.")
                    break
        
        # Si no encontramos enlace explícito a siguiente página, incrementar manualmente
        page += 1
        
        # Pausa para no sobrecargar el servidor
        time.sleep(2)
    
    print(f"\n✅ PSOE Marín WordPress: {len(data)} artículos válidos (desde {DATE_THRESHOLD.isoformat()}) recopilados de {page-1} páginas")
    print(f"📅 Rango de fechas: {data[0]['date'] if data else 'N/A'} a {data[-1]['date'] if data else 'N/A'}")
    return data

# Ejecutar
data = scrape_psdegmarin_wordpress_all()

# Guardar CSV
df = pd.DataFrame(data)
df.to_csv("psdeg-marin-sucio.csv", index=False)

# Mostrar resumen
print("\n📦 CSV generado con", len(df), "artículos.")
print(df[["source", "title", "date", "n_comments"]])